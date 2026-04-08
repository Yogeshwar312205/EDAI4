"""
EDAI4 - Perception Pipeline
Unified orchestration of Layer 2: Visual Detection + OCR + Text-Symbol Association

This module provides the complete Layer 2 pipeline that:
1. Detects P&ID symbols using YOLOv8 (Layer 1 output)
2. Extracts text using OCR (Tesseract/EasyOCR)
3. Associates text with symbols spatially
4. Validates and normalizes tags (ISA S5.1)
5. Outputs structured data for downstream layers
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union, Literal
import time
import numpy as np

from src.perception.symbol_detector import (
    SymbolDetector,
    DetectionResult,
    Detection,
)
from src.perception.ocr_engine import (
    OCREngine,
    OCRResult,
    TextBlock,
)
from src.perception.text_symbol_associator import (
    TextSymbolAssociator,
    AssociationResult,
    SymbolTextAssociation,
)
from src.perception.text_normalizer import TextNormalizer, ParsedTag
from src.utils import get_logger, config

logger = get_logger(__name__)


@dataclass
class InstrumentData:
    """Structured instrument data extracted from P&ID."""
    tag_number: str
    tag_type: Literal["instrument", "equipment", "line", "unknown"]
    symbol_class: str
    confidence: float
    
    # Parsed tag components (if available)
    parsed_tag: Optional[ParsedTag] = None
    
    # Spatial information
    x: float = 0.0
    y: float = 0.0
    bbox: tuple[float, float, float, float] = field(default_factory=tuple)
    
    # Associated text
    description: Optional[str] = None
    additional_text: list[str] = field(default_factory=list)
    
    # Metadata
    detection_confidence: float = 0.0
    association_confidence: float = 0.0


@dataclass
class PipelineResult:
    """Complete result from perception pipeline."""
    # Raw detection and OCR results
    detections: DetectionResult
    ocr_result: OCRResult
    associations: AssociationResult
    
    # Structured extracted data
    instruments: list[InstrumentData] = field(default_factory=list)
    equipment: list[InstrumentData] = field(default_factory=list)
    lines: list[InstrumentData] = field(default_factory=list)
    unidentified_symbols: list[Detection] = field(default_factory=list)
    
    # Performance metrics
    processing_time_ms: float = 0.0
    detection_time_ms: float = 0.0
    ocr_time_ms: float = 0.0
    association_time_ms: float = 0.0
    
    # Image metadata
    image_width: int = 0
    image_height: int = 0
    
    def get_all_tags(self) -> list[str]:
        """Get all extracted tag numbers."""
        tags = []
        for item in self.instruments + self.equipment + self.lines:
            if item.tag_number:
                tags.append(item.tag_number)
        return tags
    
    def get_by_class(self, class_name: str) -> list[InstrumentData]:
        """Get all items matching a symbol class."""
        all_items = self.instruments + self.equipment + self.lines + self.unidentified_symbols
        return [item for item in all_items 
                if hasattr(item, 'symbol_class') and class_name in item.symbol_class.lower()]
    
    def summary(self) -> str:
        """Generate summary string."""
        return (
            f"Pipeline Result:\n"
            f"  Instruments: {len(self.instruments)} tagged, {len(self.unidentified_symbols)} untagged\n"
            f"  Equipment: {len(self.equipment)}\n"
            f"  Lines: {len(self.lines)}\n"
            f"  Processing Time: {self.processing_time_ms:.1f}ms\n"
            f"    - Detection: {self.detection_time_ms:.1f}ms\n"
            f"    - OCR: {self.ocr_time_ms:.1f}ms\n"
            f"    - Association: {self.association_time_ms:.1f}ms"
        )


class PerceptionPipeline:
    """
    Complete Layer 2 perception pipeline for P&ID analysis.
    
    Orchestrates symbol detection, OCR, and text-symbol association
    to produce structured instrument/equipment data.
    """
    
    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        ocr_engine: Literal["tesseract", "easyocr"] = "easyocr",
        confidence_threshold: float = 0.5,
        association_search_radius: float = 150,
    ):
        """
        Initialize perception pipeline.
        
        Args:
            model_path: Path to YOLO model weights
            ocr_engine: OCR backend to use
            confidence_threshold: Minimum confidence for symbol detection
            association_search_radius: Search radius for text-symbol association (pixels)
        """
        self.model_path = model_path
        self.ocr_engine_type = ocr_engine
        self.confidence_threshold = confidence_threshold
        self.association_search_radius = association_search_radius
        
        # Initialize components
        logger.info("Initializing Perception Pipeline...")
        
        self.symbol_detector = SymbolDetector(
            model_path=model_path,
            confidence_threshold=confidence_threshold,
        )
        
        self.ocr = OCREngine(
            engine=ocr_engine,
        )
        
        self.associator = TextSymbolAssociator(
            search_radius=association_search_radius,
        )
        
        self.normalizer = TextNormalizer()
        
        logger.info("Perception Pipeline initialized")
    
    def process_image(
        self,
        image: np.ndarray,
        run_detection: bool = True,
        run_ocr: bool = True,
        run_association: bool = True,
    ) -> PipelineResult:
        """
        Process a P&ID image through the complete pipeline.
        
        Args:
            image: Input image (numpy array, BGR or RGB)
            run_detection: Run symbol detection
            run_ocr: Run OCR text extraction
            run_association: Run text-symbol association
        
        Returns:
            PipelineResult with structured data
        """
        start_time = time.time()
        
        result = PipelineResult(
            detections=DetectionResult(),
            ocr_result=OCRResult(),
            associations=AssociationResult(),
            image_width=image.shape[1],
            image_height=image.shape[0],
        )
        
        # Step 1: Symbol Detection
        if run_detection:
            logger.info("Running symbol detection...")
            result.detections = self.symbol_detector.detect(image)
            result.detection_time_ms = result.detections.processing_time_ms
            logger.info(f"Detected {len(result.detections.detections)} symbols")
        
        # Step 2: OCR Text Extraction
        if run_ocr:
            logger.info("Running OCR...")
            result.ocr_result = self.ocr.extract_all_text(image)
            result.ocr_time_ms = result.ocr_result.processing_time_ms
            logger.info(f"Extracted {len(result.ocr_result.text_blocks)} text blocks")
        
        # Step 3: Text-Symbol Association
        if run_association and run_detection and run_ocr:
            logger.info("Associating text with symbols...")
            result.associations = self.associator.associate(
                result.detections,
                result.ocr_result,
            )
            result.association_time_ms = result.associations.processing_time_ms
            logger.info(f"Created {len(result.associations.associations)} associations")
        
        # Step 4: Structure extraction
        self._extract_structured_data(result)
        
        result.processing_time_ms = (time.time() - start_time) * 1000
        
        logger.info(f"Pipeline completed in {result.processing_time_ms:.1f}ms")
        logger.info(result.summary())
        
        return result
    
    def _extract_structured_data(self, result: PipelineResult) -> None:
        """
        Extract and structure instrument/equipment data from associations.
        
        Populates result.instruments, result.equipment, result.lines.
        """
        for assoc in result.associations.associations:
            # Extract tag number
            tag_number = assoc.tag_number
            
            if not tag_number and assoc.associated_texts:
                # Try to extract from associated text
                for text_block in assoc.associated_texts:
                    potential_tag = self.normalizer.extract_tag_number(
                        text_block.cleaned_text or text_block.text
                    )
                    if potential_tag:
                        tag_number = potential_tag
                        break
            
            # Determine tag type
            tag_type = "unknown"
            parsed_tag = None
            
            if tag_number:
                tag_type = self.normalizer.identify_tag_type(tag_number)
                
                # Parse tag based on type
                if tag_type == "instrument":
                    parsed_tag = self.normalizer.parse_instrument_tag(tag_number)
                elif tag_type == "equipment":
                    parsed_tag = self.normalizer.parse_equipment_tag(tag_number)
                elif tag_type == "line":
                    parsed_tag = self.normalizer.parse_line_number(tag_number)
            
            # Collect additional text (descriptions, notes)
            additional_text = []
            description = None
            
            for text_block in assoc.associated_texts:
                text = text_block.cleaned_text or text_block.text
                if text and text != tag_number:
                    if not description:
                        description = text
                    else:
                        additional_text.append(text)
            
            # Create structured data
            bbox = assoc.detection.bbox
            instrument_data = InstrumentData(
                tag_number=tag_number or "UNTAGGED",
                tag_type=tag_type,
                symbol_class=assoc.detection.class_name,
                confidence=assoc.confidence,
                parsed_tag=parsed_tag,
                x=bbox.center[0],
                y=bbox.center[1],
                bbox=bbox.to_tuple(),
                description=description,
                additional_text=additional_text,
                detection_confidence=assoc.detection.confidence,
                association_confidence=assoc.confidence,
            )
            
            # Categorize by type
            if tag_type == "instrument" or "instrument" in assoc.detection.class_name.lower():
                result.instruments.append(instrument_data)
            elif tag_type == "equipment" or any(
                kw in assoc.detection.class_name.lower() 
                for kw in ["pump", "compressor", "equipment", "vessel", "tank"]
            ):
                result.equipment.append(instrument_data)
            elif tag_type == "line":
                result.lines.append(instrument_data)
            else:
                # Check if it has a valid tag but unclear category
                if tag_number and tag_number != "UNTAGGED":
                    result.instruments.append(instrument_data)
        
        # Collect unidentified symbols (no association)
        for detection in result.associations.unassociated_symbols:
            bbox = detection.bbox
            unidentified = InstrumentData(
                tag_number="UNTAGGED",
                tag_type="unknown",
                symbol_class=detection.class_name,
                confidence=0.0,
                x=bbox.center[0],
                y=bbox.center[1],
                bbox=bbox.to_tuple(),
                detection_confidence=detection.confidence,
            )
            result.unidentified_symbols.append(unidentified)
    
    def process_batch(
        self,
        images: list[np.ndarray],
    ) -> list[PipelineResult]:
        """
        Process multiple images.
        
        Args:
            images: List of input images
        
        Returns:
            List of PipelineResult objects
        """
        results = []
        
        for i, image in enumerate(images):
            logger.info(f"Processing image {i+1}/{len(images)}")
            result = self.process_image(image)
            results.append(result)
        
        return results
    
    def export_to_dict(self, result: PipelineResult) -> dict:
        """
        Export pipeline result to dictionary format.
        
        Args:
            result: Pipeline result
        
        Returns:
            Dictionary with structured data
        """
        return {
            "summary": {
                "total_instruments": len(result.instruments),
                "total_equipment": len(result.equipment),
                "total_lines": len(result.lines),
                "untagged_symbols": len(result.unidentified_symbols),
                "processing_time_ms": result.processing_time_ms,
            },
            "instruments": [
                {
                    "tag_number": inst.tag_number,
                    "type": inst.tag_type,
                    "symbol_class": inst.symbol_class,
                    "position": {"x": inst.x, "y": inst.y},
                    "bbox": inst.bbox,
                    "description": inst.description,
                    "confidence": {
                        "detection": inst.detection_confidence,
                        "association": inst.association_confidence,
                    },
                    "parsed": {
                        "area": inst.parsed_tag.area if inst.parsed_tag else None,
                        "function": inst.parsed_tag.function if inst.parsed_tag else None,
                        "modifier": inst.parsed_tag.modifier if inst.parsed_tag else None,
                        "loop_number": inst.parsed_tag.loop_number if inst.parsed_tag else None,
                        "suffix": inst.parsed_tag.suffix if inst.parsed_tag else None,
                    } if inst.parsed_tag else None,
                }
                for inst in result.instruments
            ],
            "equipment": [
                {
                    "tag_number": equip.tag_number,
                    "type": equip.tag_type,
                    "symbol_class": equip.symbol_class,
                    "position": {"x": equip.x, "y": equip.y},
                    "bbox": equip.bbox,
                    "description": equip.description,
                    "confidence": {
                        "detection": equip.detection_confidence,
                        "association": equip.association_confidence,
                    },
                }
                for equip in result.equipment
            ],
            "lines": [
                {
                    "line_number": line.tag_number,
                    "type": line.tag_type,
                    "position": {"x": line.x, "y": line.y},
                    "parsed": {
                        "size": line.parsed_tag.modifier if line.parsed_tag else None,
                        "service": line.parsed_tag.function if line.parsed_tag else None,
                        "sequence": line.parsed_tag.loop_number if line.parsed_tag else None,
                    } if line.parsed_tag else None,
                }
                for line in result.lines
            ],
        }
    
    def visualize(
        self,
        image: np.ndarray,
        result: PipelineResult,
        show_detections: bool = True,
        show_ocr: bool = True,
        show_associations: bool = True,
    ) -> np.ndarray:
        """
        Visualize pipeline results on image.
        
        Args:
            image: Original image
            result: Pipeline result
            show_detections: Draw detection boxes
            show_ocr: Draw OCR text boxes
            show_associations: Draw association lines
        
        Returns:
            Annotated image
        """
        import cv2
        
        output = image.copy()
        
        # Draw OCR results (first, so overlaid by others)
        if show_ocr:
            output = self.ocr.visualize(
                output,
                result.ocr_result,
                show_text=False,
                highlight_tags=True,
            )
        
        # Draw associations
        if show_associations:
            output = self.associator.visualize(
                output,
                result.associations,
                show_lines=True,
            )
        
        # Draw legend
        cv2.putText(
            output,
            f"Instruments: {len(result.instruments)} | Equipment: {len(result.equipment)}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )
        
        return output
    
    def load_model(self, model_path: Optional[Union[str, Path]] = None) -> bool:
        """
        Load or reload YOLO model.
        
        Args:
            model_path: Path to model weights (optional, uses configured path)
        
        Returns:
            True if successful
        """
        if model_path:
            self.model_path = model_path
        
        return self.symbol_detector.load_model(self.model_path)
