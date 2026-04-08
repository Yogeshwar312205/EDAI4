"""
EDAI4 - Image Preprocessor
Handles image preprocessing for optimal OCR and symbol detection
"""

import cv2
import numpy as np
from pathlib import Path
from PIL import Image
from typing import Literal

from src.utils import get_logger

logger = get_logger(__name__)


class ImagePreprocessor:
    """
    Image preprocessor for P&ID images.
    Applies various preprocessing steps to enhance OCR and symbol detection accuracy.
    """

    def __init__(
        self,
        target_dpi: int = 300,
        grayscale: bool = True,
        denoise: bool = True,
        threshold_method: Literal["adaptive", "otsu", "binary", "none"] = "none",
        edge_detection: bool = False,
    ):
        """
        Initialize image preprocessor.

        Args:
            target_dpi: Target DPI for resizing
            grayscale: Convert to grayscale
            denoise: Apply denoising
            threshold_method: Thresholding method
            edge_detection: Apply Canny edge detection
        """
        self.target_dpi = target_dpi
        self.grayscale = grayscale
        self.denoise = denoise
        self.threshold_method = threshold_method
        self.edge_detection = edge_detection

        logger.info(
            f"ImagePreprocessor initialized (grayscale={grayscale}, "
            f"denoise={denoise}, threshold={threshold_method})"
        )

    def load_image(self, image_path: str | Path) -> np.ndarray:
        """
        Load an image from file.

        Args:
            image_path: Path to image file

        Returns:
            Numpy array (BGR format)
        """
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        image = cv2.imread(str(image_path))

        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")

        logger.debug(f"Loaded image: {image_path} ({image.shape})")
        return image

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Apply full preprocessing pipeline.

        Args:
            image: Input image (BGR or grayscale)

        Returns:
            Preprocessed image
        """
        result = image.copy()

        # Step 1: Convert to grayscale (if enabled and needed)
        if self.grayscale and len(result.shape) == 3:
            result = self.to_grayscale(result)

        # Step 2: Denoise (if enabled)
        if self.denoise:
            result = self.apply_denoise(result)

        # Step 3: Apply thresholding (if enabled)
        if self.threshold_method != "none":
            result = self.apply_threshold(result, method=self.threshold_method)

        # Step 4: Edge detection (if enabled)
        if self.edge_detection:
            result = self.detect_edges(result)

        logger.debug(f"Preprocessing complete: {result.shape}")
        return result

    def to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """
        Convert image to grayscale.

        Args:
            image: Input image (BGR)

        Returns:
            Grayscale image
        """
        if len(image.shape) == 2:
            return image  # Already grayscale

        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def apply_denoise(self, image: np.ndarray) -> np.ndarray:
        """
        Apply denoising filter.

        Args:
            image: Input image

        Returns:
            Denoised image
        """
        if len(image.shape) == 2:
            # Grayscale denoising
            return cv2.fastNlMeansDenoising(image, h=10)
        else:
            # Color denoising
            return cv2.fastNlMeansDenoisingColored(image, h=10, hColor=10)

    def apply_threshold(
        self,
        image: np.ndarray,
        method: Literal["adaptive", "otsu", "binary"] = "adaptive"
    ) -> np.ndarray:
        """
        Apply thresholding to binarize the image.

        Args:
            image: Input image (should be grayscale)
            method: Thresholding method

        Returns:
            Thresholded image
        """
        # Ensure grayscale
        if len(image.shape) == 3:
            image = self.to_grayscale(image)

        if method == "adaptive":
            return cv2.adaptiveThreshold(
                image,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11,  # Block size
                2    # Constant subtracted from mean
            )
        elif method == "otsu":
            _, result = cv2.threshold(
                image,
                0,
                255,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
            return result
        elif method == "binary":
            _, result = cv2.threshold(
                image,
                127,
                255,
                cv2.THRESH_BINARY
            )
            return result
        else:
            return image

    def detect_edges(
        self,
        image: np.ndarray,
        low_threshold: int = 50,
        high_threshold: int = 150
    ) -> np.ndarray:
        """
        Apply Canny edge detection.

        Args:
            image: Input image
            low_threshold: Lower threshold for edge detection
            high_threshold: Upper threshold for edge detection

        Returns:
            Edge-detected image
        """
        # Ensure grayscale
        if len(image.shape) == 3:
            image = self.to_grayscale(image)

        return cv2.Canny(image, low_threshold, high_threshold)

    def resize(
        self,
        image: np.ndarray,
        scale: float | None = None,
        width: int | None = None,
        height: int | None = None
    ) -> np.ndarray:
        """
        Resize image.

        Args:
            image: Input image
            scale: Scale factor (e.g., 0.5 for half size)
            width: Target width (maintains aspect ratio if height not specified)
            height: Target height (maintains aspect ratio if width not specified)

        Returns:
            Resized image
        """
        h, w = image.shape[:2]

        if scale:
            new_w = int(w * scale)
            new_h = int(h * scale)
        elif width and height:
            new_w, new_h = width, height
        elif width:
            new_w = width
            new_h = int(h * (width / w))
        elif height:
            new_h = height
            new_w = int(w * (height / h))
        else:
            return image

        return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

    def deskew(self, image: np.ndarray) -> np.ndarray:
        """
        Deskew (straighten) a rotated image.

        Args:
            image: Input image

        Returns:
            Deskewed image
        """
        # Ensure grayscale for angle detection
        if len(image.shape) == 3:
            gray = self.to_grayscale(image)
        else:
            gray = image

        # Detect edges
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Detect lines using Hough transform
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

        if lines is None or len(lines) == 0:
            logger.debug("No lines detected for deskewing")
            return image

        # Calculate average angle
        angles = []
        for line in lines:
            rho, theta = line[0]
            angle = np.degrees(theta) - 90
            if -45 <= angle <= 45:  # Filter reasonable angles
                angles.append(angle)

        if not angles:
            return image

        median_angle = np.median(angles)

        if abs(median_angle) < 0.5:  # Skip if nearly straight
            return image

        # Rotate image
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated = cv2.warpAffine(
            image,
            rotation_matrix,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )

        logger.debug(f"Deskewed image by {median_angle:.2f} degrees")
        return rotated

    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image contrast using CLAHE.

        Args:
            image: Input image

        Returns:
            Contrast-enhanced image
        """
        # Ensure grayscale
        if len(image.shape) == 3:
            # Convert to LAB color space
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l_channel, a, b = cv2.split(lab)

            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced_l = clahe.apply(l_channel)

            # Merge channels back
            enhanced_lab = cv2.merge([enhanced_l, a, b])
            return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        else:
            # Grayscale CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            return clahe.apply(image)

    def remove_borders(
        self,
        image: np.ndarray,
        border_color: int = 255,
        threshold: int = 10
    ) -> np.ndarray:
        """
        Remove white/black borders from image.

        Args:
            image: Input image
            border_color: Expected border color (255=white, 0=black)
            threshold: Color matching threshold

        Returns:
            Cropped image without borders
        """
        # Ensure grayscale
        if len(image.shape) == 3:
            gray = self.to_grayscale(image)
        else:
            gray = image

        # Find non-border region
        if border_color == 255:
            mask = gray < (255 - threshold)
        else:
            mask = gray > threshold

        coords = cv2.findNonZero(mask.astype(np.uint8))

        if coords is None:
            return image

        x, y, w, h = cv2.boundingRect(coords)

        # Add small padding
        padding = 10
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(image.shape[1] - x, w + 2 * padding)
        h = min(image.shape[0] - y, h + 2 * padding)

        return image[y:y+h, x:x+w]

    def save_image(
        self,
        image: np.ndarray,
        output_path: str | Path,
        format: str = "png"
    ) -> Path:
        """
        Save image to file.

        Args:
            image: Image to save
            output_path: Output file path
            format: Image format

        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure correct extension
        if not output_path.suffix:
            output_path = output_path.with_suffix(f".{format}")

        cv2.imwrite(str(output_path), image)
        logger.debug(f"Saved image: {output_path}")

        return output_path

    def get_image_info(self, image: np.ndarray) -> dict:
        """
        Get information about an image.

        Args:
            image: Input image

        Returns:
            Dictionary with image information
        """
        info = {
            "height": image.shape[0],
            "width": image.shape[1],
            "channels": image.shape[2] if len(image.shape) == 3 else 1,
            "dtype": str(image.dtype),
            "size_bytes": image.nbytes,
        }

        # Estimate content density (non-white pixels)
        if len(image.shape) == 3:
            gray = self.to_grayscale(image)
        else:
            gray = image

        non_white = np.sum(gray < 250)
        total = gray.size
        info["content_density"] = non_white / total

        return info
