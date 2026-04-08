"""
EDAI4 - Perception Layer
Symbol detection and text extraction for P&ID images
"""

from src.perception.symbol_detector import (
    SymbolDetector,
    Detection,
    DetectionResult,
    BoundingBox,
)
from src.perception.ocr_engine import (
    OCREngine,
    OCRResult,
    TextBlock,
    TextRegion,
)
from src.perception.text_normalizer import TextNormalizer, ParsedTag
from src.perception.text_symbol_associator import (
    TextSymbolAssociator,
    AssociationResult,
    SymbolTextAssociation,
    AssociationType,
)
from src.perception.perception_pipeline import (
    PerceptionPipeline,
    PipelineResult,
    InstrumentData,
)

# Optional SAHI support (imports may fail if sahi not installed)
try:
    from src.perception.sahi_detector import (
        SAHISymbolDetector,
        SAHIDetection,
        PaddleOCREngine,
        SAHIPipeline,
    )
    SAHI_AVAILABLE = True
except ImportError:
    SAHI_AVAILABLE = False

__all__ = [
    # Symbol Detector
    "SymbolDetector",
    "Detection",
    "DetectionResult",
    "BoundingBox",

    # OCR Engine
    "OCREngine",
    "OCRResult",
    "TextBlock",
    "TextRegion",

    # Text Normalizer
    "TextNormalizer",
    "ParsedTag",

    # Text-Symbol Associator
    "TextSymbolAssociator",
    "AssociationResult",
    "SymbolTextAssociation",
    "AssociationType",

    # Perception Pipeline
    "PerceptionPipeline",
    "PipelineResult",
    "InstrumentData",
    
    # SAHI (if available)
    "SAHISymbolDetector",
    "SAHIDetection",
    "PaddleOCREngine",
    "SAHIPipeline",
    "SAHI_AVAILABLE",
]
