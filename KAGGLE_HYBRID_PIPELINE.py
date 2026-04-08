"""
================================================================================
KAGGLE NOTEBOOK: HYBRID P&ID PERCEPTION PIPELINE
================================================================================
Copy-paste this entire script into a Kaggle notebook cell.

Solves the "YOLO Domain Shift" problem by combining:
  1. YOLO/SAHI detection (valves, equipment)
  2. OpenCV HoughCircles (instrument bubbles YOLO misses)
  3. ISA S5.1 Regex validation (force-promote OCR text to instruments)

INSTRUCTIONS:
  1. Run Cell 1 to install dependencies
  2. Upload your best.pt model as a Kaggle dataset
  3. Upload your P&ID images
  4. Run the remaining cells

================================================================================
"""

# =============================================================================
# CELL 1: INSTALL DEPENDENCIES (Run this first!)
# =============================================================================

# !pip install -q sahi ultralytics paddlepaddle paddleocr opencv-python-headless

# =============================================================================
# CELL 2: CONFIGURATION
# =============================================================================

import os
import re
import time
import warnings
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

import numpy as np
import cv2

warnings.filterwarnings("ignore")
os.environ["CUDA_MODULE_LOADING"] = "LAZY"

# ===================== PATHS =====================
MODEL_PATH = "/kaggle/input/edai4-golden-model/best.pt"
IMAGE_PATH = "/kaggle/input/pid-images/incinerator_pid.png"
OUTPUT_PATH = "/kaggle/working/hybrid_result.png"

# ===================== PARAMETERS =====================
SLICE_SIZE = 640           # SAHI tile size
OVERLAP_RATIO = 0.25       # Tile overlap
CONFIDENCE = 0.20          # YOLO confidence
CIRCLE_MIN_R = 15          # Min instrument bubble radius
CIRCLE_MAX_R = 60          # Max instrument bubble radius
YOLO_PROXIMITY = 80.0      # Text-to-YOLO distance
CIRCLE_PROXIMITY = 30.0    # Text-to-circle distance


# =============================================================================
# CELL 3: DATA STRUCTURES
# =============================================================================

class DetectionSource(Enum):
    YOLO = "yolo"
    HOUGH_CIRCLE = "hough"
    ISA_REGEX = "regex"


@dataclass
class DetectedNode:
    class_name: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float
    source: DetectionSource
    tag: Optional[str] = None
    is_instrument: bool = False
    
    @property
    def center(self):
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)


@dataclass
class OCRText:
    text: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float
    is_isa: bool = False
    matched: bool = False
    
    @property
    def center(self):
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)


@dataclass
class Circle:
    cx: float
    cy: float
    radius: float
    text: Optional[str] = None


# =============================================================================
# CELL 4: ISA S5.1 TAG VALIDATOR
# =============================================================================

class ISAValidator:
    """Validates instrument tags against ISA S5.1 standard."""
    
    PREFIXES = [
        'FT', 'PT', 'LT', 'TT', 'AT', 'WT',
        'FC', 'PC', 'LC', 'TC', 'AC',
        'FI', 'PI', 'LI', 'TI', 'AI',
        'FV', 'PV', 'LV', 'TV', 'AV', 'HV',
        'FIC', 'PIC', 'LIC', 'TIC', 'AIC',
        'FRC', 'PRC', 'LRC', 'TRC', 'ARC',
        'PSV', 'PRV', 'TSV', 'PSE',
        'PSH', 'PSL', 'PSHH', 'PSLL',
        'TSH', 'TSL', 'TSHH', 'TSLL',
        'LSH', 'LSL', 'LSHH', 'LSLL',
        'FSH', 'FSL', 'FSHH', 'FSLL',
        'PAH', 'PAL', 'PAHH', 'PALL',
        'TAH', 'TAL', 'TAHH', 'TALL',
        'LAH', 'LAL', 'LAHH', 'LALL',
        'FAH', 'FAL', 'FAHH', 'FALL',
        'FE', 'TE', 'PE', 'LE', 'AE',
        'FS', 'PS', 'LS', 'TS', 'AS',
        'PDT', 'PDI', 'PDC', 'PDIC',
        'XV', 'ZV', 'ZIC', 'ZT',
    ]
    
    def __init__(self):
        prefix_pattern = '|'.join(sorted(self.PREFIXES, key=len, reverse=True))
        self.pattern = re.compile(
            rf'^({prefix_pattern})[-_]?(\d{{2,4}}[A-Z]?)?$',
            re.IGNORECASE
        )
        self._set = set(p.upper() for p in self.PREFIXES)
    
    def is_valid(self, text: str) -> bool:
        if not text or len(text) < 2:
            return False
        normalized = text.upper().strip().replace(' ', '').replace('.', '')
        
        if self.pattern.match(normalized):
            return True
        
        for prefix in self._set:
            if normalized.startswith(prefix) and len(normalized) <= len(prefix) + 5:
                return True
        
        return False


# =============================================================================
# CELL 5: CIRCLE DETECTOR (HoughTransform)
# =============================================================================

class CircleDetector:
    """Detects instrument bubbles using OpenCV HoughCircles."""
    
    def __init__(self, min_r=15, max_r=60, min_dist=30, param1=50, param2=25):
        self.min_r = min_r
        self.max_r = max_r
        self.min_dist = min_dist
        self.param1 = param1
        self.param2 = param2
    
    def detect(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Try multiple param2 values for robustness
        all_circles = []
        for p2 in [20, 25, 30]:
            circles = cv2.HoughCircles(
                blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=self.min_dist,
                param1=self.param1, param2=p2,
                minRadius=self.min_r, maxRadius=self.max_r
            )
            if circles is not None:
                for c in circles[0]:
                    all_circles.append(Circle(float(c[0]), float(c[1]), float(c[2])))
        
        # Deduplicate
        return self._dedupe(all_circles)
    
    def _dedupe(self, circles, threshold=0.5):
        if not circles:
            return []
        circles = sorted(circles, key=lambda c: c.radius, reverse=True)
        kept = []
        for c in circles:
            dup = False
            for k in kept:
                dist = np.sqrt((c.cx - k.cx)**2 + (c.cy - k.cy)**2)
                if dist < max(c.radius, k.radius) * threshold:
                    dup = True
                    break
            if not dup:
                kept.append(c)
        return kept


# =============================================================================
# CELL 6: SAHI DETECTOR
# =============================================================================

class SAHIDetector:
    """SAHI-powered YOLO detector."""
    
    def __init__(self, model_path, slice_size=640, overlap=0.25, conf=0.20):
        from sahi import AutoDetectionModel
        import torch
        
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        print(f"[SAHI] Loading model on {device}...")
        
        self.model = AutoDetectionModel.from_pretrained(
            model_type="yolov8",
            model_path=model_path,
            confidence_threshold=conf,
            device=device,
        )
        self.slice_size = slice_size
        self.overlap = overlap
        print("[SAHI] ✓ Model loaded!")
    
    def detect(self, image):
        from sahi.predict import get_sliced_prediction
        
        h, w = image.shape[:2]
        result = get_sliced_prediction(
            image=image,
            detection_model=self.model,
            slice_height=min(self.slice_size, h),
            slice_width=min(self.slice_size, w),
            overlap_height_ratio=self.overlap,
            overlap_width_ratio=self.overlap,
            postprocess_type="NMS",
            postprocess_match_threshold=0.45,
            verbose=0,
        )
        
        nodes = []
        for pred in result.object_prediction_list:
            bbox = pred.bbox
            nodes.append(DetectedNode(
                class_name=pred.category.name,
                confidence=pred.score.value,
                x1=bbox.minx, y1=bbox.miny,
                x2=bbox.maxx, y2=bbox.maxy,
                source=DetectionSource.YOLO,
                is_instrument="instrument" in pred.category.name.lower(),
            ))
        return nodes


# =============================================================================
# CELL 7: PADDLEOCR
# =============================================================================

class OCREngine:
    """PaddleOCR text extractor."""
    
    def __init__(self, use_gpu=True):
        try:
            from paddleocr import PaddleOCR
            # PaddleOCR v3+ API - minimal params
            self.ocr = PaddleOCR(lang="en")
            print("[OCR] ✓ PaddleOCR initialized")
        except:
            self.ocr = None
            print("[OCR] ✗ PaddleOCR not available")
    
    def extract(self, image):
        if not self.ocr:
            return []
        
        # PaddleOCR v3+ - no cls param
        results = self.ocr.ocr(image)
        texts = []
        if results and results[0]:
            for line in results[0]:
                if line and len(line) >= 2:
                    bbox, (text, conf) = line[0], line[1]
                    xs = [p[0] for p in bbox]
                    ys = [p[1] for p in bbox]
                    texts.append(OCRText(
                        text=text.strip(), confidence=conf,
                        x1=min(xs), y1=min(ys),
                        x2=max(xs), y2=max(ys),
                    ))
        return texts


# =============================================================================
# CELL 8: HYBRID PIPELINE
# =============================================================================

class HybridPipeline:
    """
    Combines YOLO + HoughCircles + ISA Regex.
    
    Strategy:
      1. YOLO catches valves/equipment
      2. HoughCircles catches instrument bubbles YOLO missed
      3. ISA Regex force-promotes valid instrument tags
    """
    
    def __init__(self, model_path, slice_size=640, overlap=0.25, conf=0.20,
                 min_r=15, max_r=60, use_gpu=True):
        
        print("=" * 60)
        print("HYBRID P&ID PERCEPTION PIPELINE")
        print("=" * 60)
        
        self.yolo = SAHIDetector(model_path, slice_size, overlap, conf)
        self.ocr = OCREngine(use_gpu)
        self.circles = CircleDetector(min_r, max_r)
        self.isa = ISAValidator()
        
        print("=" * 60)
        print("✓ Pipeline ready!")
        print("=" * 60)
    
    def process(self, image):
        """Process P&ID image."""
        h, w = image.shape[:2]
        print(f"\n[PIPELINE] Processing {w}x{h} image...")
        
        timing = {}
        
        # Stage 1: YOLO
        print("\n[STAGE 1] YOLO/SAHI Detection...")
        t0 = time.time()
        yolo_nodes = self.yolo.detect(image)
        timing["yolo"] = time.time() - t0
        print(f"  Found {len(yolo_nodes)} YOLO detections")
        
        # Stage 2: OCR
        print("\n[STAGE 2] PaddleOCR Extraction...")
        t0 = time.time()
        texts = self.ocr.extract(image)
        timing["ocr"] = time.time() - t0
        
        # Mark ISA tags
        for t in texts:
            t.is_isa = self.isa.is_valid(t.text)
        isa_count = sum(1 for t in texts if t.is_isa)
        print(f"  Found {len(texts)} text blocks ({isa_count} ISA tags)")
        
        # Stage 3: HoughCircles
        print("\n[STAGE 3] HoughCircle Detection...")
        t0 = time.time()
        circles = self.circles.detect(image)
        timing["circles"] = time.time() - t0
        print(f"  Found {len(circles)} circles")
        
        # Stage 4: Merge
        print("\n[STAGE 4] Hybrid Merging...")
        t0 = time.time()
        
        all_nodes = list(yolo_nodes)
        discarded = []
        
        for text in texts:
            matched = False
            
            # Try YOLO match
            for node in yolo_nodes:
                if self._near_bbox(text, node):
                    if node.tag is None:
                        node.tag = text.text.upper()
                        text.matched = True
                        matched = True
                    break
            
            if matched:
                continue
            
            # Try circle match
            for circle in circles:
                if self._inside_circle(text, circle):
                    circle.text = text.text.upper()
                    text.matched = True
                    matched = True
                    
                    new_node = DetectedNode(
                        class_name="instrument.bubble",
                        confidence=0.85,
                        x1=circle.cx - circle.radius,
                        y1=circle.cy - circle.radius,
                        x2=circle.cx + circle.radius,
                        y2=circle.cy + circle.radius,
                        source=DetectionSource.HOUGH_CIRCLE,
                        tag=text.text.upper(),
                        is_instrument=True,
                    )
                    
                    if not self._is_dup(new_node, all_nodes):
                        all_nodes.append(new_node)
                        print(f"  [CIRCLE] '{text.text}' → instrument")
                    break
            
            if matched:
                continue
            
            # ISA Regex bypass
            if text.is_isa:
                text.matched = True
                cx, cy = text.center
                r = 25
                
                new_node = DetectedNode(
                    class_name="instrument.bubble",
                    confidence=0.75,
                    x1=cx - r, y1=cy - r, x2=cx + r, y2=cy + r,
                    source=DetectionSource.ISA_REGEX,
                    tag=text.text.upper(),
                    is_instrument=True,
                )
                
                if not self._is_dup(new_node, all_nodes):
                    all_nodes.append(new_node)
                    print(f"  [REGEX] '{text.text}' → instrument (ISA bypass)")
                continue
            
            discarded.append(text)
        
        timing["merge"] = time.time() - t0
        timing["total"] = sum(timing.values())
        
        # Stats
        stats = {
            "total_nodes": len(all_nodes),
            "instruments": sum(1 for n in all_nodes if n.is_instrument),
            "valves": sum(1 for n in all_nodes if "valve" in n.class_name.lower()),
            "from_yolo": sum(1 for n in all_nodes if n.source == DetectionSource.YOLO),
            "from_circles": sum(1 for n in all_nodes if n.source == DetectionSource.HOUGH_CIRCLE),
            "from_regex": sum(1 for n in all_nodes if n.source == DetectionSource.ISA_REGEX),
            "discarded": len(discarded),
        }
        
        print("\n" + "=" * 60)
        print("COMPLETE")
        print("=" * 60)
        print(f"  Total nodes:      {stats['total_nodes']}")
        print(f"  → From YOLO:      {stats['from_yolo']}")
        print(f"  → From Circles:   {stats['from_circles']}")
        print(f"  → From Regex:     {stats['from_regex']}")
        print(f"  Instruments:      {stats['instruments']}")
        print(f"  Valves:           {stats['valves']}")
        print(f"  Discarded text:   {stats['discarded']}")
        print(f"  Total time:       {timing['total']:.1f}s")
        
        return {
            "nodes": all_nodes,
            "texts": texts,
            "circles": circles,
            "discarded": discarded,
            "stats": stats,
            "timing": timing,
        }
    
    def _near_bbox(self, text, node):
        tx, ty = text.center
        if node.x1 <= tx <= node.x2 and node.y1 <= ty <= node.y2:
            return True
        cx = max(node.x1, min(tx, node.x2))
        cy = max(node.y1, min(ty, node.y2))
        return np.sqrt((tx-cx)**2 + (ty-cy)**2) <= YOLO_PROXIMITY
    
    def _inside_circle(self, text, circle):
        tx, ty = text.center
        dist = np.sqrt((tx - circle.cx)**2 + (ty - circle.cy)**2)
        return dist <= circle.radius + CIRCLE_PROXIMITY
    
    def _is_dup(self, new, existing):
        ncx, ncy = new.center
        for e in existing:
            ecx, ecy = e.center
            if np.sqrt((ncx-ecx)**2 + (ncy-ecy)**2) < 50:
                if new.tag and not e.tag:
                    e.tag = new.tag
                return True
        return False
    
    def visualize(self, image, result, output_path=None):
        """Visualize results."""
        vis = image.copy()
        
        COLORS = {
            DetectionSource.YOLO: (0, 255, 0),
            DetectionSource.HOUGH_CIRCLE: (255, 165, 0),
            DetectionSource.ISA_REGEX: (255, 0, 255),
        }
        
        for node in result["nodes"]:
            color = COLORS.get(node.source, (255, 255, 255))
            x1, y1 = int(node.x1), int(node.y1)
            x2, y2 = int(node.x2), int(node.y2)
            
            cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)
            
            label = node.tag or node.class_name
            cv2.putText(vis, label, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        if output_path:
            cv2.imwrite(output_path, vis)
            print(f"\n✓ Saved: {output_path}")
        
        return vis


# =============================================================================
# CELL 9: RUN THE PIPELINE
# =============================================================================

def run():
    """Execute the hybrid pipeline."""
    
    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: Model not found: {MODEL_PATH}")
        return None
    
    if not os.path.exists(IMAGE_PATH):
        print(f"ERROR: Image not found: {IMAGE_PATH}")
        return None
    
    # Initialize
    pipeline = HybridPipeline(
        model_path=MODEL_PATH,
        slice_size=SLICE_SIZE,
        overlap=OVERLAP_RATIO,
        conf=CONFIDENCE,
        min_r=CIRCLE_MIN_R,
        max_r=CIRCLE_MAX_R,
        use_gpu=True,
    )
    
    # Process
    image = cv2.imread(IMAGE_PATH)
    result = pipeline.process(image)
    
    # Visualize
    pipeline.visualize(image, result, OUTPUT_PATH)
    
    # Print instruments
    print("\n" + "=" * 50)
    print("DETECTED INSTRUMENTS")
    print("=" * 50)
    for node in result["nodes"]:
        if node.is_instrument:
            print(f"  {node.tag or 'UNTAGGED'} ({node.source.value})")
    
    return result


# Run it!
if __name__ == "__main__":
    result = run()
