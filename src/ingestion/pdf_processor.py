"""
EDAI4 - PDF Processor
Handles PDF to image conversion for P&ID processing
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Generator
import numpy as np
from PIL import Image
import io

from src.utils import get_logger

logger = get_logger(__name__)


class PDFProcessor:
    """
    PDF processor for extracting pages as images.
    Converts PDF pages to high-resolution images suitable for OCR and symbol detection.
    """

    def __init__(self, dpi: int = 300, colorspace: str = "rgb"):
        """
        Initialize PDF processor.

        Args:
            dpi: Resolution for PDF rendering (300-600 recommended)
            colorspace: Color space ('rgb' or 'gray')
        """
        self.dpi = dpi
        self.colorspace = colorspace
        self.zoom = dpi / 72  # PDF points to pixels conversion

        logger.info(f"PDFProcessor initialized (DPI: {dpi}, colorspace: {colorspace})")

    def extract_pages(
        self,
        pdf_path: str | Path,
        page_numbers: list[int] | None = None
    ) -> list[np.ndarray]:
        """
        Extract all pages from PDF as images.

        Args:
            pdf_path: Path to PDF file
            page_numbers: Specific pages to extract (0-indexed). None = all pages.

        Returns:
            List of numpy arrays (images)
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        images = []
        doc = fitz.open(pdf_path)

        try:
            pages_to_process = page_numbers or range(len(doc))

            for page_num in pages_to_process:
                if page_num >= len(doc):
                    logger.warning(f"Page {page_num} does not exist, skipping")
                    continue

                page = doc[page_num]
                image = self._render_page(page)
                images.append(image)

                logger.debug(f"Extracted page {page_num + 1}/{len(doc)}")

            logger.info(f"Extracted {len(images)} pages from {pdf_path.name}")

        finally:
            doc.close()

        return images

    def extract_pages_generator(
        self,
        pdf_path: str | Path,
        page_numbers: list[int] | None = None
    ) -> Generator[tuple[int, np.ndarray], None, None]:
        """
        Extract pages as a generator (memory efficient for large PDFs).

        Args:
            pdf_path: Path to PDF file
            page_numbers: Specific pages to extract (0-indexed)

        Yields:
            Tuple of (page_number, image_array)
        """
        pdf_path = Path(pdf_path)
        doc = fitz.open(pdf_path)

        try:
            pages_to_process = page_numbers or range(len(doc))

            for page_num in pages_to_process:
                if page_num >= len(doc):
                    continue

                page = doc[page_num]
                image = self._render_page(page)
                yield (page_num, image)

        finally:
            doc.close()

    def _render_page(self, page: fitz.Page) -> np.ndarray:
        """
        Render a single PDF page to image.

        Args:
            page: PyMuPDF page object

        Returns:
            Numpy array (image)
        """
        # Create transformation matrix for desired DPI
        mat = fitz.Matrix(self.zoom, self.zoom)

        # Render page to pixmap
        if self.colorspace == "gray":
            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csGRAY)
        else:
            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)

        # Convert to numpy array
        img_data = pix.samples
        width, height = pix.width, pix.height

        if self.colorspace == "gray":
            image = np.frombuffer(img_data, dtype=np.uint8).reshape(height, width)
        else:
            channels = pix.n
            image = np.frombuffer(img_data, dtype=np.uint8).reshape(height, width, channels)

        return image

    def get_metadata(self, pdf_path: str | Path) -> dict:
        """
        Extract PDF metadata.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with metadata
        """
        pdf_path = Path(pdf_path)
        doc = fitz.open(pdf_path)

        try:
            metadata = {
                "filename": pdf_path.name,
                "page_count": len(doc),
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "creator": doc.metadata.get("creator", ""),
                "producer": doc.metadata.get("producer", ""),
                "creation_date": doc.metadata.get("creationDate", ""),
                "modification_date": doc.metadata.get("modDate", ""),
            }

            # Get page dimensions (first page)
            if len(doc) > 0:
                first_page = doc[0]
                rect = first_page.rect
                metadata["page_width_pts"] = rect.width
                metadata["page_height_pts"] = rect.height
                metadata["page_width_px"] = int(rect.width * self.zoom)
                metadata["page_height_px"] = int(rect.height * self.zoom)

        finally:
            doc.close()

        return metadata

    def save_pages_as_images(
        self,
        pdf_path: str | Path,
        output_dir: str | Path,
        format: str = "png",
        page_numbers: list[int] | None = None
    ) -> list[Path]:
        """
        Extract and save PDF pages as image files.

        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save images
            format: Image format (png, jpg, tiff)
            page_numbers: Specific pages to extract

        Returns:
            List of saved image paths
        """
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_paths = []

        for page_num, image in self.extract_pages_generator(pdf_path, page_numbers):
            # Convert to PIL Image
            if len(image.shape) == 2:
                pil_image = Image.fromarray(image, mode="L")
            else:
                pil_image = Image.fromarray(image, mode="RGB")

            # Save image
            filename = f"{pdf_path.stem}_page_{page_num + 1:03d}.{format}"
            output_path = output_dir / filename
            pil_image.save(output_path)
            saved_paths.append(output_path)

            logger.debug(f"Saved: {output_path}")

        logger.info(f"Saved {len(saved_paths)} images to {output_dir}")
        return saved_paths
