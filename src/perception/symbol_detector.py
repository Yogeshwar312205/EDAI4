"""
EDAI4 - Symbol Detector
YOLOv8-based P&ID symbol detection
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import numpy as np

from src.utils import get_logger, config

logger = get_logger(__name__)


@dataclass
class BoundingBox:
    """Bounding box for detected object."""
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

    @property
    def area(self) -> float:
        return self.width * self.height

    def to_tuple(self) -> tuple[float, float, float, float]:
        return (self.x1, self.y1, self.x2, self.y2)

    def to_xywh(self) -> tuple[float, float, float, float]:
        """Convert to x, y, width, height format."""
        return (self.x1, self.y1, self.width, self.height)


@dataclass
class Detection:
    """Single detection result."""
    bbox: BoundingBox
    class_id: int
    class_name: str
    confidence: float
    metadata: dict = field(default_factory=dict)

    # Associated text (from OCR)
    associated_text: Optional[str] = None
    tag_number: Optional[str] = None


@dataclass
class DetectionResult:
    """Collection of detections from an image."""
    detections: list[Detection] = field(default_factory=list)
    image_width: int = 0
    image_height: int = 0
    processing_time_ms: float = 0.0

    def filter_by_confidence(self, min_confidence: float) -> list[Detection]:
        """Filter detections by minimum confidence."""
        return [d for d in self.detections if d.confidence >= min_confidence]

    def filter_by_class(self, class_names: list[str]) -> list[Detection]:
        """Filter detections by class name."""
        return [d for d in self.detections if d.class_name in class_names]

    def get_by_class(self, class_name: str) -> list[Detection]:
        """Get all detections of a specific class."""
        return [d for d in self.detections if d.class_name == class_name]


class SymbolDetector:
    """
    YOLOv8-based symbol detector for P&ID drawings.
    Detects valves, instruments, equipment, and other symbols.
    """

    # Default P&ID symbol classes
    DEFAULT_CLASSES = {
        0: "valve_gate",
        1: "valve_globe",
        2: "valve_ball",
        3: "valve_check",
        4: "valve_control",
        5: "valve_safety",
        6: "pump_centrifugal",
        7: "pump_positive",
        8: "compressor",
        9: "vessel",
        10: "tank",
        11: "heat_exchanger",
        12: "transmitter",
        13: "indicator",
        14: "controller",
        15: "switch",
        16: "instrument_general",
        17: "motor",
        18: "reducer",
        19: "junction",
    }

    def __init__(
        self,
        model_path: Optional[str | Path] = None,
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        device: str = "auto",
    ):
        """
        Initialize symbol detector.

        Args:
            model_path: Path to YOLOv8 weights file
            confidence_threshold: Minimum confidence for detections
            iou_threshold: IoU threshold for NMS
            device: Device to use (auto, cpu, cuda:0)
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        self.model = None
        self.classes = self.DEFAULT_CLASSES.copy()

        # Try to load configuration
        settings = config.get_settings()
        if settings:
            perception_config = settings.get("perception", {}).get("yolo", {})
            if not model_path:
                self.model_path = perception_config.get("model_path")
            self.confidence_threshold = perception_config.get(
                "confidence_threshold", self.confidence_threshold
            )
            self.iou_threshold = perception_config.get(
                "iou_threshold", self.iou_threshold
            )

        logger.info(
            f"SymbolDetector initialized (conf={self.confidence_threshold}, "
            f"iou={self.iou_threshold})"
        )

    def load_model(self, model_path: Optional[str | Path] = None) -> bool:
        """
        Load YOLOv8 model.

        Args:
            model_path: Path to model weights (optional, uses configured path)

        Returns:
            True if model loaded successfully
        """
        path = model_path or self.model_path

        if not path:
            logger.warning("No model path specified, using pretrained YOLOv8n")
            path = "yolov8n.pt"  # Default pretrained model

        try:
            from ultralytics import YOLO

            self.model = YOLO(str(path))

            # Update classes from model if available
            if hasattr(self.model, "names") and self.model.names:
                self.classes = self.model.names

            logger.info(f"Model loaded: {path}")
            logger.info(f"Classes: {len(self.classes)}")
            return True

        except ImportError:
            logger.error("ultralytics not installed. Run: pip install ultralytics")
            return False
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def detect(self, image: np.ndarray) -> DetectionResult:
        """
        Detect symbols in an image.

        Args:
            image: Input image (numpy array, BGR or RGB)

        Returns:
            DetectionResult with all detections
        """
        import time
        start_time = time.time()

        result = DetectionResult(
            image_height=image.shape[0],
            image_width=image.shape[1],
        )

        # Ensure model is loaded
        if self.model is None:
            if not self.load_model():
                logger.error("Model not available, returning empty result")
                return result

        try:
            # Run inference
            predictions = self.model(
                image,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                device=self.device if self.device != "auto" else None,
                verbose=False,
            )

            # Process results
            for pred in predictions:
                boxes = pred.boxes

                if boxes is None:
                    continue

                for i in range(len(boxes)):
                    # Extract box coordinates
                    xyxy = boxes.xyxy[i].cpu().numpy()
                    conf = float(boxes.conf[i].cpu().numpy())
                    cls_id = int(boxes.cls[i].cpu().numpy())

                    # Get class name
                    class_name = self.classes.get(cls_id, f"class_{cls_id}")

                    # Create detection
                    detection = Detection(
                        bbox=BoundingBox(
                            x1=float(xyxy[0]),
                            y1=float(xyxy[1]),
                            x2=float(xyxy[2]),
                            y2=float(xyxy[3]),
                        ),
                        class_id=cls_id,
                        class_name=class_name,
                        confidence=conf,
                    )

                    result.detections.append(detection)

        except Exception as e:
            logger.error(f"Detection failed: {e}")

        # Calculate processing time
        result.processing_time_ms = (time.time() - start_time) * 1000

        logger.info(
            f"Detected {len(result.detections)} symbols in "
            f"{result.processing_time_ms:.1f}ms"
        )

        return result

    def detect_batch(
        self,
        images: list[np.ndarray],
        batch_size: int = 8
    ) -> list[DetectionResult]:
        """
        Detect symbols in multiple images.

        Args:
            images: List of input images
            batch_size: Processing batch size

        Returns:
            List of DetectionResult objects
        """
        results = []

        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]

            for image in batch:
                result = self.detect(image)
                results.append(result)

            logger.debug(f"Processed batch {i//batch_size + 1}/{(len(images)-1)//batch_size + 1}")

        return results

    def get_bounding_boxes(self, result: DetectionResult) -> list[BoundingBox]:
        """Extract just bounding boxes from detection result."""
        return [d.bbox for d in result.detections]

    def visualize(
        self,
        image: np.ndarray,
        result: DetectionResult,
        show_labels: bool = True,
        show_confidence: bool = True,
    ) -> np.ndarray:
        """
        Draw detection results on image.

        Args:
            image: Original image
            result: Detection result
            show_labels: Show class labels
            show_confidence: Show confidence scores

        Returns:
            Image with drawn detections
        """
        import cv2

        output = image.copy()

        for detection in result.detections:
            bbox = detection.bbox
            x1, y1, x2, y2 = int(bbox.x1), int(bbox.y1), int(bbox.x2), int(bbox.y2)

            # Draw box
            color = (0, 255, 0)  # Green
            cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)

            # Draw label
            if show_labels or show_confidence:
                label_parts = []
                if show_labels:
                    label_parts.append(detection.class_name)
                if show_confidence:
                    label_parts.append(f"{detection.confidence:.2f}")

                label = " ".join(label_parts)

                # Label background
                (label_w, label_h), _ = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
                )
                cv2.rectangle(
                    output, (x1, y1 - label_h - 10), (x1 + label_w, y1), color, -1
                )
                cv2.putText(
                    output, label, (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1
                )

        return output

    def set_classes(self, classes: dict[int, str]) -> None:
        """Update class mapping."""
        self.classes = classes
        logger.info(f"Updated classes: {len(classes)} classes")

    def get_class_counts(self, result: DetectionResult) -> dict[str, int]:
        """
        Count detections by class.

        Args:
            result: Detection result

        Returns:
            Dictionary of class_name: count
        """
        counts = {}
        for detection in result.detections:
            name = detection.class_name
            counts[name] = counts.get(name, 0) + 1
        return counts
