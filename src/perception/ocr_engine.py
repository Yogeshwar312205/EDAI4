"""
EDAI4 - OCR Engine
Text extraction from P&ID images using Tesseract/EasyOCR
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional
import numpy as np

from src.utils import get_logger, config

logger = get_logger(__name__)


@dataclass
class TextRegion:
    """Detected text region."""
    x1: float  # Top-left X
    y1: float  # Top-left Y
    x2: float  # Bottom-right X
    y2: float  # Bottom-right Y

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)

    def to_tuple(self) -> tuple[float, float, float, float]:
        return (self.x1, self.y1, self.x2, self.y2)


@dataclass
class TextBlock:
    """Extracted text block with metadata."""
    text: str
    region: TextRegion
    confidence: float

    # Normalized/cleaned text
    cleaned_text: Optional[str] = None

    # Potential tag number (if detected)
    is_tag: bool = False
    tag_number: Optional[str] = None

    # OCR metadata
    language: str = "en"
    font_size: Optional[float] = None


@dataclass
class OCRResult:
    """OCR extraction result."""
    text_blocks: list[TextBlock] = field(default_factory=list)
    full_text: str = ""
    image_width: int = 0
    image_height: int = 0
    processing_time_ms: float = 0.0

    def get_tags(self) -> list[TextBlock]:
        """Get only text blocks identified as tags."""
        return [tb for tb in self.text_blocks if tb.is_tag]

    def get_text_near(
        self,
        x: float,
        y: float,
        max_distance: float = 100
    ) -> list[TextBlock]:
        """Get text blocks near a point."""
        result = []
        for tb in self.text_blocks:
            cx, cy = tb.region.center
            distance = ((cx - x) ** 2 + (cy - y) ** 2) ** 0.5
            if distance <= max_distance:
                result.append(tb)
        return result


class OCREngine:
    """
    OCR engine for extracting text from P&ID images.
    Supports Tesseract and EasyOCR backends.
    """

    def __init__(
        self,
        engine: Literal["tesseract", "easyocr"] = "easyocr",
        languages: list[str] = None,
        confidence_threshold: float = 0.5,
    ):
        """
        Initialize OCR engine.

        Args:
            engine: OCR backend to use
            languages: Languages to detect
            confidence_threshold: Minimum confidence for text extraction
        """
        self.engine_type = engine
        self.languages = languages or ["en"]
        self.confidence_threshold = confidence_threshold
        self.engine = None

        # Load config
        settings = config.get_settings()
        if settings:
            ocr_config = settings.get("perception", {}).get("ocr", {})
            self.engine_type = ocr_config.get("engine", self.engine_type)
            self.languages = ocr_config.get("languages", self.languages)
            self.confidence_threshold = ocr_config.get(
                "confidence_threshold", self.confidence_threshold
            )

        logger.info(f"OCREngine initialized (engine={self.engine_type})")

    def _initialize_engine(self) -> bool:
        """Initialize the OCR engine."""
        if self.engine is not None:
            return True

        try:
            if self.engine_type == "easyocr":
                import easyocr
                self.engine = easyocr.Reader(
                    self.languages,
                    gpu=True,  # Use GPU if available
                    verbose=False,
                )
                logger.info("EasyOCR engine initialized")
                return True

            elif self.engine_type == "tesseract":
                import pytesseract
                # Test tesseract availability
                pytesseract.get_tesseract_version()
                self.engine = pytesseract
                logger.info("Tesseract engine initialized")
                return True

        except ImportError as e:
            logger.error(f"OCR engine not available: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize OCR engine: {e}")
            return False

        return False

    def extract_all_text(self, image: np.ndarray) -> OCRResult:
        """
        Extract all text from an image.

        Args:
            image: Input image (numpy array)

        Returns:
            OCRResult with all extracted text
        """
        import time
        start_time = time.time()

        result = OCRResult(
            image_height=image.shape[0],
            image_width=image.shape[1],
        )

        if not self._initialize_engine():
            return result

        try:
            if self.engine_type == "easyocr":
                result = self._extract_easyocr(image)
            elif self.engine_type == "tesseract":
                result = self._extract_tesseract(image)

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")

        result.processing_time_ms = (time.time() - start_time) * 1000
        result.image_height = image.shape[0]
        result.image_width = image.shape[1]

        logger.info(
            f"Extracted {len(result.text_blocks)} text blocks in "
            f"{result.processing_time_ms:.1f}ms"
        )

        return result

    def _extract_easyocr(self, image: np.ndarray) -> OCRResult:
        """Extract text using EasyOCR."""
        result = OCRResult()

        # Run OCR
        detections = self.engine.readtext(image)

        full_text_parts = []

        for detection in detections:
            bbox, text, confidence = detection

            if confidence < self.confidence_threshold:
                continue

            # Convert bbox to region
            # EasyOCR returns [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
            x_coords = [p[0] for p in bbox]
            y_coords = [p[1] for p in bbox]

            region = TextRegion(
                x1=min(x_coords),
                y1=min(y_coords),
                x2=max(x_coords),
                y2=max(y_coords),
            )

            text_block = TextBlock(
                text=text,
                region=region,
                confidence=confidence,
            )

            # Clean and analyze text
            self._process_text_block(text_block)

            result.text_blocks.append(text_block)
            full_text_parts.append(text)

        result.full_text = " ".join(full_text_parts)

        return result

    def _extract_tesseract(self, image: np.ndarray) -> OCRResult:
        """Extract text using Tesseract."""
        import cv2

        result = OCRResult()

        # Convert to RGB if needed
        if len(image.shape) == 2:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 4:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        else:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Get detailed data
        data = self.engine.image_to_data(
            rgb_image,
            output_type=self.engine.Output.DICT,
        )

        full_text_parts = []
        n_boxes = len(data["text"])

        for i in range(n_boxes):
            text = data["text"][i].strip()
            conf = int(data["conf"][i])

            if not text or conf < self.confidence_threshold * 100:
                continue

            region = TextRegion(
                x1=data["left"][i],
                y1=data["top"][i],
                x2=data["left"][i] + data["width"][i],
                y2=data["top"][i] + data["height"][i],
            )

            text_block = TextBlock(
                text=text,
                region=region,
                confidence=conf / 100.0,
            )

            self._process_text_block(text_block)

            result.text_blocks.append(text_block)
            full_text_parts.append(text)

        result.full_text = " ".join(full_text_parts)

        return result

    def _process_text_block(self, text_block: TextBlock) -> None:
        """Process and analyze a text block."""
        from src.perception.text_normalizer import TextNormalizer

        normalizer = TextNormalizer()

        # Clean text
        text_block.cleaned_text = normalizer.clean_ocr_output(text_block.text)

        # Check if it's a tag number
        tag = normalizer.extract_tag_number(text_block.cleaned_text)
        if tag:
            text_block.is_tag = True
            text_block.tag_number = tag

    def extract_region(
        self,
        image: np.ndarray,
        region: TextRegion
    ) -> str:
        """
        Extract text from a specific region.

        Args:
            image: Input image
            region: Region to extract from

        Returns:
            Extracted text
        """
        # Crop region
        x1, y1, x2, y2 = int(region.x1), int(region.y1), int(region.x2), int(region.y2)
        cropped = image[y1:y2, x1:x2]

        if cropped.size == 0:
            return ""

        # Extract text
        result = self.extract_all_text(cropped)

        return result.full_text

    def detect_text_regions(self, image: np.ndarray) -> list[TextRegion]:
        """
        Detect text regions without full OCR.

        Args:
            image: Input image

        Returns:
            List of text regions
        """
        result = self.extract_all_text(image)
        return [tb.region for tb in result.text_blocks]

    def visualize(
        self,
        image: np.ndarray,
        result: OCRResult,
        show_text: bool = True,
        highlight_tags: bool = True,
    ) -> np.ndarray:
        """
        Draw OCR results on image.

        Args:
            image: Original image
            result: OCR result
            show_text: Show extracted text
            highlight_tags: Highlight detected tag numbers

        Returns:
            Image with drawn text regions
        """
        import cv2

        output = image.copy()

        for text_block in result.text_blocks:
            region = text_block.region
            x1, y1, x2, y2 = int(region.x1), int(region.y1), int(region.x2), int(region.y2)

            # Color based on type
            if text_block.is_tag and highlight_tags:
                color = (0, 0, 255)  # Red for tags
            else:
                color = (255, 0, 0)  # Blue for regular text

            # Draw box
            cv2.rectangle(output, (x1, y1), (x2, y2), color, 1)

            # Draw text
            if show_text:
                label = text_block.cleaned_text or text_block.text
                cv2.putText(
                    output, label[:20], (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1
                )

        return output
