"""
================================================================================
KAGGLE NOTEBOOK: HIGH-DENSITY P&ID VISION PIPELINE
================================================================================
Copy this entire script into a Kaggle notebook cell.

Solves three critical failures on complex P&ID drawings:
  1. Resolution Collapse → SAHI sliced inference
  2. Poor OCR accuracy  → PaddleOCR
  3. Text as Node Bug   → Strict BBox proximity constraints

INSTRUCTIONS:
  1. Upload your best.pt model to Kaggle as a dataset
  2. Upload your P&ID images to process
  3. Run the cells below in order

================================================================================
"""

# =============================================================================
# CELL 1: INSTALL DEPENDENCIES
# =============================================================================
# Run this first!

# !pip install -q sahi ultralytics
# !pip install -q paddlepaddle paddleocr
# !pip install -q opencv-python-headless

# =============================================================================
# CELL 2: IMPORTS AND CONFIGURATION
# =============================================================================

import os
import sys
import time
import warnings
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

import numpy as np
import cv2

# Suppress warnings
warnings.filterwarnings("ignore")
os.environ["CUDA_MODULE_LOADING"] = "LAZY"

# ===================== CONFIGURATION =====================
# Adjust these paths for your Kaggle environment

MODEL_PATH = "/kaggle/input/edai4-golden-model/best.pt"  # Your YOLO model
IMAGE_PATH = "/kaggle/input/pid-images/incinerator_pid.png"  # P&ID to process
OUTPUT_PATH = "/kaggle/working/output_annotated.png"  # Where to save results

# Detection parameters (tune these for your drawings)
SLICE_SIZE = 640           # SAHI tile size
OVERLAP_RATIO = 0.25       # Tile overlap (25%)
CONFIDENCE_THRESHOLD = 0.20  # YOLO confidence (lower = more detections)
MAX_PROXIMITY_PX = 60.0    # Max distance for text-symbol association


# =============================================================================
# CELL 3: DATA STRUCTURES
# =============================================================================

@dataclass
class DetectedSymbol:
    """A symbol detected by YOLO/SAHI."""
    class_name: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float
    tag: Optional[str] = None
    
    @property
    def center(self) -> Tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)
    
    @property
    def area(self) -> float:
        return (self.x2 - self.x1) * (self.y2 - self.y1)


@dataclass
class OCRText:
    """Text extracted by PaddleOCR."""
    text: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float
    
    @property
    def center(self) -> Tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)


# =============================================================================
# CELL 4: SAHI DETECTOR CLASS
# =============================================================================

class SAHIDetector:
    """SAHI-powered YOLO detector for high-resolution P&IDs."""
    
    def __init__(self, model_path: str, slice_size: int = 640,
                 overlap_ratio: float = 0.25, confidence: float = 0.20):
        self.slice_size = slice_size
        self.overlap_ratio = overlap_ratio
        self.confidence = confidence
        
        # Load model with SAHI
        from sahi import AutoDetectionModel
        import torch
        
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        print(f"[SAHI] Loading model on {device}...")
        
        self.model = AutoDetectionModel.from_pretrained(
            model_type="yolov8",
            model_path=model_path,
            confidence_threshold=confidence,
            device=device,
        )
        print("[SAHI] ✓ Model loaded!")
    
    def detect(self, image: np.ndarray) -> List[DetectedSymbol]:
        """Run SAHI sliced inference."""
        from sahi.predict import get_sliced_prediction
        
        h, w = image.shape[:2]
        print(f"[SAHI] Processing {w}x{h} image...")
        
        start = time.time()
        
        result = get_sliced_prediction(
            image=image,
            detection_model=self.model,
            slice_height=min(self.slice_size, h),
            slice_width=min(self.slice_size, w),
            overlap_height_ratio=self.overlap_ratio,
            overlap_width_ratio=self.overlap_ratio,
            postprocess_type="NMS",
            postprocess_match_metric="IOU",
            postprocess_match_threshold=0.45,
            verbose=0,
        )
        
        detections = []
        for pred in result.object_prediction_list:
            bbox = pred.bbox
            detections.append(DetectedSymbol(
                class_name=pred.category.name,
                confidence=pred.score.value,
                x1=bbox.minx, y1=bbox.miny,
                x2=bbox.maxx, y2=bbox.maxy,
            ))
        
        elapsed = time.time() - start
        print(f"[SAHI] ✓ Found {len(detections)} symbols in {elapsed:.1f}s")
        
        return detections


# =============================================================================
# CELL 5: PADDLEOCR ENGINE CLASS
# =============================================================================

class PaddleOCREngine:
    """PaddleOCR for engineering text extraction."""
    
    def __init__(self, use_gpu: bool = True):
        from paddleocr import PaddleOCR
        
        print("[OCR] Initializing PaddleOCR...")
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang="en",
            use_gpu=use_gpu,
            show_log=False,
        )
        print("[OCR] ✓ PaddleOCR ready!")
    
    def extract(self, image: np.ndarray) -> List[OCRText]:
        """Extract text from image."""
        print(f"[OCR] Extracting text...")
        start = time.time()
        
        results = self.ocr.ocr(image, cls=True)
        
        text_blocks = []
        if results and results[0]:
            for line in results[0]:
                if line and len(line) >= 2:
                    bbox_points, (text, conf) = line[0], line[1]
                    xs = [p[0] for p in bbox_points]
                    ys = [p[1] for p in bbox_points]
                    
                    text_blocks.append(OCRText(
                        text=text.strip(),
                        confidence=conf,
                        x1=min(xs), y1=min(ys),
                        x2=max(xs), y2=max(ys),
                    ))
        
        elapsed = time.time() - start
        print(f"[OCR] ✓ Found {len(text_blocks)} text blocks in {elapsed:.1f}s")
        
        return text_blocks


# =============================================================================
# CELL 6: SPATIAL CONSTRAINT ENGINE (FIXES TEXT-AS-NODE BUG)
# =============================================================================

class SpatialConstraintEngine:
    """Enforces strict spatial constraints for text-symbol association."""
    
    # ISA S5.1 instrument tag prefixes
    ISA_PREFIXES = [
        "FT", "PT", "LT", "TT", "AT", "WT",
        "FC", "PC", "LC", "TC", "AC",
        "FI", "PI", "LI", "TI", "AI",
        "FV", "PV", "LV", "TV", "AV",
        "FIC", "PIC", "LIC", "TIC",
        "PSV", "PRV", "TSV",
        "PSH", "PSL", "TSH", "TSL", "LSH", "LSL",
        "FE", "TE", "PE", "LE",
        "FAH", "FAL", "PAH", "PAL", "LAH", "LAL", "TAH", "TAL",
    ]
    
    def __init__(self, max_proximity_px: float = 60.0):
        self.max_proximity_px = max_proximity_px
        
        import re
        prefix_pattern = "|".join(self.ISA_PREFIXES)
        self.isa_pattern = re.compile(
            rf"^({prefix_pattern})[-_]?(\d{{2,4}}[A-Z]?)$",
            re.IGNORECASE
        )
    
    def associate(self, symbols: List[DetectedSymbol], 
                  texts: List[OCRText]) -> Tuple[Dict[int, str], List[OCRText]]:
        """Associate text with symbols, discard floating text."""
        print(f"[SPATIAL] Associating {len(texts)} texts with {len(symbols)} symbols...")
        
        associations = {}
        discarded = []
        symbol_scores = {}  # Track best match per symbol
        
        for text in texts:
            if len(text.text) < 2:
                discarded.append(text)
                continue
            
            is_isa = self._is_isa_tag(text.text)
            best_idx = None
            best_score = 0
            
            for idx, symbol in enumerate(symbols):
                score = self._compute_score(text, symbol, is_isa)
                if score > best_score:
                    best_score = score
                    best_idx = idx
            
            if best_idx is not None and best_score > 0:
                existing = symbol_scores.get(best_idx)
                if existing is None or best_score > existing[0]:
                    symbol_scores[best_idx] = (best_score, text.text)
            else:
                discarded.append(text)
        
        # Build final associations
        for idx, (score, tag) in symbol_scores.items():
            tag_upper = tag.upper()
            associations[idx] = tag_upper
            symbols[idx].tag = tag_upper
        
        print(f"[SPATIAL] ✓ Associated {len(associations)} tags, discarded {len(discarded)} floating text")
        return associations, discarded
    
    def _compute_score(self, text: OCRText, symbol: DetectedSymbol, is_isa: bool) -> float:
        """Compute association score."""
        tx, ty = text.center
        
        # Check if inside symbol bbox
        if symbol.x1 <= tx <= symbol.x2 and symbol.y1 <= ty <= symbol.y2:
            score = 0.8
        else:
            # Calculate distance to bbox edge
            cx = max(symbol.x1, min(tx, symbol.x2))
            cy = max(symbol.y1, min(ty, symbol.y2))
            dist = np.sqrt((tx - cx)**2 + (ty - cy)**2)
            
            if dist > self.max_proximity_px:
                return 0.0
            
            score = 0.3 * (1 - dist / self.max_proximity_px)
        
        # Boost for instrument symbols
        if "instrument" in symbol.class_name.lower():
            score *= 1.5
        
        # Boost for ISA tags
        if is_isa:
            score *= 1.3
        
        return min(score, 1.0)
    
    def _is_isa_tag(self, text: str) -> bool:
        normalized = text.upper().strip().replace(" ", "")
        return bool(self.isa_pattern.match(normalized))


# =============================================================================
# CELL 7: MAIN PIPELINE CLASS
# =============================================================================

class HighDensityPipeline:
    """Complete high-density vision pipeline."""
    
    def __init__(self, model_path: str, slice_size: int = 640,
                 overlap_ratio: float = 0.25, confidence: float = 0.20,
                 max_proximity_px: float = 60.0, use_gpu: bool = True):
        
        print("=" * 60)
        print("EDAI4 HIGH-DENSITY P&ID VISION PIPELINE")
        print("=" * 60)
        
        self.detector = SAHIDetector(model_path, slice_size, overlap_ratio, confidence)
        self.ocr = PaddleOCREngine(use_gpu)
        self.spatial = SpatialConstraintEngine(max_proximity_px)
        
        print("=" * 60)
        print("✓ Pipeline ready!")
        print("=" * 60)
    
    def process(self, image_path: str) -> dict:
        """Process P&ID image."""
        print(f"\n[PIPELINE] Processing: {image_path}")
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Failed to load: {image_path}")
        
        h, w = image.shape[:2]
        print(f"[PIPELINE] Image size: {w}x{h}")
        
        timing = {}
        
        # Stage 1: SAHI Detection
        print("\n" + "-" * 40)
        print("STAGE 1: SAHI Symbol Detection")
        print("-" * 40)
        t0 = time.time()
        symbols = self.detector.detect(image)
        timing["detection"] = time.time() - t0
        
        # Stage 2: PaddleOCR
        print("\n" + "-" * 40)
        print("STAGE 2: PaddleOCR Text Extraction")
        print("-" * 40)
        t0 = time.time()
        texts = self.ocr.extract(image)
        timing["ocr"] = time.time() - t0
        
        # Stage 3: Spatial Association
        print("\n" + "-" * 40)
        print("STAGE 3: Spatial Constraint Association")
        print("-" * 40)
        t0 = time.time()
        associations, discarded = self.spatial.associate(symbols, texts)
        timing["association"] = time.time() - t0
        
        timing["total"] = sum(timing.values())
        
        # Summary
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETE")
        print("=" * 60)
        print(f"  Symbols detected:    {len(symbols)}")
        print(f"  Text blocks found:   {len(texts)}")
        print(f"  Tags associated:     {len(associations)}")
        print(f"  Floating text:       {len(discarded)}")
        print(f"  Total time:          {timing['total']:.1f}s")
        
        return {
            "symbols": symbols,
            "texts": texts,
            "associations": associations,
            "discarded": discarded,
            "timing": timing,
            "image": image,
        }
    
    def visualize(self, result: dict, output_path: str = None):
        """Visualize results."""
        image = result["image"].copy()
        symbols = result["symbols"]
        
        # Colors
        COLORS = {
            "instrument": (0, 255, 0),
            "valve": (255, 0, 0),
            "equipment": (0, 165, 255),
            "default": (255, 0, 255),
        }
        
        for symbol in symbols:
            color = COLORS["default"]
            for key in COLORS:
                if key in symbol.class_name.lower():
                    color = COLORS[key]
                    break
            
            x1, y1 = int(symbol.x1), int(symbol.y1)
            x2, y2 = int(symbol.x2), int(symbol.y2)
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            
            label = symbol.class_name
            if symbol.tag:
                label += f": {symbol.tag}"
            
            cv2.putText(image, label, (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        if output_path:
            cv2.imwrite(output_path, image)
            print(f"\n✓ Saved visualization: {output_path}")
        
        return image


# =============================================================================
# CELL 8: RUN THE PIPELINE
# =============================================================================

def run_pipeline():
    """Run the complete pipeline."""
    
    # Check if model exists
    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: Model not found at {MODEL_PATH}")
        print("Please upload your best.pt model to Kaggle as a dataset.")
        return
    
    # Check if image exists
    if not os.path.exists(IMAGE_PATH):
        print(f"ERROR: Image not found at {IMAGE_PATH}")
        print("Please upload your P&ID image to Kaggle as a dataset.")
        return
    
    # Initialize pipeline
    pipeline = HighDensityPipeline(
        model_path=MODEL_PATH,
        slice_size=SLICE_SIZE,
        overlap_ratio=OVERLAP_RATIO,
        confidence=CONFIDENCE_THRESHOLD,
        max_proximity_px=MAX_PROXIMITY_PX,
        use_gpu=True,
    )
    
    # Process image
    result = pipeline.process(IMAGE_PATH)
    
    # Visualize and save
    pipeline.visualize(result, OUTPUT_PATH)
    
    # Print detected instruments with tags
    print("\n" + "=" * 60)
    print("DETECTED INSTRUMENTS WITH TAGS")
    print("=" * 60)
    
    for idx, tag in sorted(result["associations"].items()):
        symbol = result["symbols"][idx]
        print(f"  [{symbol.class_name}] {tag} (confidence: {symbol.confidence:.0%})")
    
    return result


# Run it!
if __name__ == "__main__":
    result = run_pipeline()
