"""
================================================================================
EDAI4 - HIGH-DENSITY VISION PIPELINE
================================================================================
Solves three critical failures on complex P&ID drawings:
  1. Resolution Collapse → SAHI sliced inference
  2. Poor OCR accuracy  → PaddleOCR  
  3. Text as Node Bug   → Strict BBox proximity constraints

Dependencies (run these first):
  pip install sahi ultralytics paddlepaddle paddleocr opencv-python numpy

For Kaggle T4 GPU:
  pip install paddlepaddle-gpu  # Use GPU version on Kaggle

Author: EDAI4 Project
================================================================================
"""

import os
import sys
import re
import time
import warnings
from pathlib import Path
from typing import List, Dict, Tuple, Optional, NamedTuple
from dataclasses import dataclass, field

# CRITICAL: Disable OneDNN BEFORE any paddle imports to avoid Windows issues
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["MKLDNN_CACHE_CAPACITY"] = "0"
os.environ["FLAGS_enable_pir_api"] = "0"

import numpy as np
import cv2

# Suppress verbose warnings
warnings.filterwarnings("ignore", category=UserWarning)
os.environ["CUDA_MODULE_LOADING"] = "LAZY"  # Faster GPU init


# =============================================================================
# CONTOUR-BASED CIRCLE DETECTOR (Bypasses YOLO for instrument bubbles)
# =============================================================================

def detect_circular_instruments(
    image: np.ndarray,
    min_area: int = 200,
    max_area: int = 6000,
    min_circularity: float = 0.70,
) -> List['DetectedSymbol']:
    """
    Detect circular instrument bubbles using OpenCV contour analysis.
    
    This bypasses YOLO entirely for instrument detection, solving the
    "YOLO blindness" problem where the model misses 40+ bubbles.
    
    Uses circularity formula: 4 * π * (area / perimeter²)
    Perfect circle = 1.0, rough circle ≥ 0.7
    
    Args:
        image: BGR or grayscale image
        min_area: Minimum contour area (px²) - ~8px radius
        max_area: Maximum contour area (px²) - ~44px radius
        min_circularity: Minimum circularity score (0-1)
        
    Returns:
        List of DetectedSymbol objects for each detected bubble
    """
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(gray, (5, 5), 1)
    
    detections = []
    
    # Try multiple threshold strategies for robustness
    threshold_strategies = []
    
    # Strategy 1: Adaptive threshold
    adaptive = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=11, C=2
    )
    threshold_strategies.append(adaptive)
    
    # Strategy 2: Otsu threshold
    _, otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    threshold_strategies.append(otsu)
    
    # Strategy 3: Fixed thresholds
    for thresh_val in [127, 150, 180]:
        _, fixed = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY_INV)
        threshold_strategies.append(fixed)
    
    seen_centers = set()  # For deduplication
    
    for binary in threshold_strategies:
        # Morphological cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Find contours
        contours, _ = cv2.findContours(cleaned, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            # Area check
            area = cv2.contourArea(contour)
            if area < min_area or area > max_area:
                continue
            
            # Perimeter and circularity
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue
            
            circularity = 4 * np.pi * (area / (perimeter ** 2))
            if circularity < min_circularity:
                continue
            
            # Aspect ratio check (circles should be roughly square)
            x, y, w, h = cv2.boundingRect(contour)
            if h == 0:
                continue
            aspect_ratio = w / h
            if aspect_ratio < 0.7 or aspect_ratio > 1.4:
                continue
            
            # Get enclosing circle
            (cx, cy), radius = cv2.minEnclosingCircle(contour)
            
            # Fill ratio check
            enclosing_area = np.pi * radius ** 2
            if enclosing_area > 0 and (area / enclosing_area) < 0.65:
                continue
            
            # Deduplication by center proximity
            center_key = (int(cx) // 15, int(cy) // 15)  # Grid-based dedup
            if center_key in seen_centers:
                continue
            seen_centers.add(center_key)
            
            # Create DetectedSymbol
            detections.append(DetectedSymbol(
                class_name="instrument.bubble",
                confidence=circularity,  # Use circularity as confidence
                x1=float(cx - radius),
                y1=float(cy - radius),
                x2=float(cx + radius),
                y2=float(cy + radius),
                tag=None,
            ))
    
    return detections


# =============================================================================
# DATA STRUCTURES
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
    tag: Optional[str] = None  # Assigned after OCR association
    
    @property
    def center(self) -> Tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)
    
    @property
    def width(self) -> float:
        return self.x2 - self.x1
    
    @property
    def height(self) -> float:
        return self.y2 - self.y1
    
    @property
    def area(self) -> float:
        return self.width * self.height


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


@dataclass
class PipelineResult:
    """Complete result from high-density pipeline."""
    symbols: List[DetectedSymbol]
    text_blocks: List[OCRText]
    associated_tags: Dict[int, str]  # symbol_index -> tag
    discarded_text: List[OCRText]    # Floating text (not near any symbol)
    timing: Dict[str, float]
    image_size: Tuple[int, int]


# =============================================================================
# SAHI SYMBOL DETECTOR
# =============================================================================

class SAHIDetector:
    """
    SAHI-powered YOLO detector for high-resolution P&ID images.
    
    SAHI (Slicing Aided Hyper Inference) solves the "resolution collapse" problem
    by slicing large images into overlapping tiles, running inference on each,
    and merging results with NMS.
    """
    
    # Default SAHI parameters tuned for P&ID drawings
    DEFAULT_SLICE_SIZE = 640      # Each tile is 640x640 (YOLO's native resolution)
    DEFAULT_OVERLAP_RATIO = 0.25  # 25% overlap between tiles
    DEFAULT_CONFIDENCE = 0.20     # Lower threshold for better recall
    DEFAULT_IOU_THRESHOLD = 0.45  # NMS threshold for merging duplicates
    
    def __init__(
        self,
        model_path: str,
        slice_size: int = DEFAULT_SLICE_SIZE,
        overlap_ratio: float = DEFAULT_OVERLAP_RATIO,
        confidence_threshold: float = DEFAULT_CONFIDENCE,
        iou_threshold: float = DEFAULT_IOU_THRESHOLD,
        device: str = "auto",
    ):
        """
        Initialize SAHI detector.
        
        Args:
            model_path: Path to YOLOv8 weights (best.pt)
            slice_size: Size of each tile (default 640 for YOLOv8)
            overlap_ratio: Overlap between tiles (0.25 = 25%)
            confidence_threshold: Min confidence for detections
            iou_threshold: NMS IoU threshold for merging
            device: "cuda:0", "cpu", or "auto"
        """
        self.model_path = model_path
        self.slice_size = slice_size
        self.overlap_ratio = overlap_ratio
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        
        # Auto-detect device
        if device == "auto":
            import torch
            self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        self._sahi_model = None
        self._yolo_model = None
        self._sahi_available = False
        
        self._load_model()
    
    def _load_model(self):
        """Load YOLO model with SAHI wrapper."""
        print(f"[SAHI] Loading model from: {self.model_path}")
        print(f"[SAHI] Device: {self.device}")
        
        # Try SAHI first (preferred)
        try:
            from sahi import AutoDetectionModel
            
            self._sahi_model = AutoDetectionModel.from_pretrained(
                model_type="yolov8",
                model_path=self.model_path,
                confidence_threshold=self.confidence_threshold,
                device=self.device,
            )
            self._sahi_available = True
            print(f"[SAHI] ✓ Model loaded with SAHI support")
            print(f"[SAHI]   Slice size: {self.slice_size}x{self.slice_size}")
            print(f"[SAHI]   Overlap: {self.overlap_ratio*100:.0f}%")
            
        except ImportError:
            print("[SAHI] ✗ SAHI not installed, using fallback tiled inference")
            print("[SAHI]   Install with: pip install sahi")
            self._load_fallback()
        except Exception as e:
            print(f"[SAHI] ✗ SAHI load failed: {e}")
            self._load_fallback()
    
    def _load_fallback(self):
        """Load vanilla YOLO as fallback."""
        try:
            from ultralytics import YOLO
            self._yolo_model = YOLO(self.model_path)
            print("[SAHI] ✓ Fallback YOLO model loaded")
        except Exception as e:
            raise RuntimeError(f"Failed to load YOLO model: {e}")
    
    def detect(self, image: np.ndarray) -> List[DetectedSymbol]:
        """
        Run sliced inference on image.
        
        Args:
            image: BGR image as numpy array
            
        Returns:
            List of DetectedSymbol objects
        """
        h, w = image.shape[:2]
        print(f"[SAHI] Processing image: {w}x{h} pixels")
        
        if self._sahi_available:
            return self._detect_with_sahi(image)
        else:
            return self._detect_with_fallback(image)
    
    def _detect_with_sahi(self, image: np.ndarray) -> List[DetectedSymbol]:
        """Run SAHI sliced prediction."""
        from sahi.predict import get_sliced_prediction
        
        h, w = image.shape[:2]
        
        # Adaptive slice size (don't slice if image is small)
        slice_h = min(self.slice_size, h)
        slice_w = min(self.slice_size, w)
        
        start = time.time()
        
        result = get_sliced_prediction(
            image=image,
            detection_model=self._sahi_model,
            slice_height=slice_h,
            slice_width=slice_w,
            overlap_height_ratio=self.overlap_ratio,
            overlap_width_ratio=self.overlap_ratio,
            postprocess_type="NMS",
            postprocess_match_metric="IOU",
            postprocess_match_threshold=self.iou_threshold,
            verbose=0,  # Suppress SAHI logs
        )
        
        elapsed = time.time() - start
        
        # Convert SAHI results to our format
        detections = []
        for pred in result.object_prediction_list:
            bbox = pred.bbox
            detections.append(DetectedSymbol(
                class_name=pred.category.name,
                confidence=pred.score.value,
                x1=bbox.minx,
                y1=bbox.miny,
                x2=bbox.maxx,
                y2=bbox.maxy,
            ))
        
        # Calculate tile count
        tiles_x = max(1, int(np.ceil((w - slice_w) / (slice_w * (1 - self.overlap_ratio))) + 1))
        tiles_y = max(1, int(np.ceil((h - slice_h) / (slice_h * (1 - self.overlap_ratio))) + 1))
        
        print(f"[SAHI] ✓ Processed {tiles_x}x{tiles_y}={tiles_x*tiles_y} tiles in {elapsed:.2f}s")
        print(f"[SAHI] ✓ Found {len(detections)} symbols")
        
        return detections
    
    def _detect_with_fallback(self, image: np.ndarray) -> List[DetectedSymbol]:
        """Manual tiled inference (when SAHI unavailable)."""
        h, w = image.shape[:2]
        
        # Small images: run directly
        if max(h, w) <= self.slice_size * 1.2:
            return self._run_yolo_single(image, offset=(0, 0))
        
        # Large images: tile manually
        stride = int(self.slice_size * (1 - self.overlap_ratio))
        all_detections = []
        tile_count = 0
        
        start = time.time()
        
        for y in range(0, h, stride):
            for x in range(0, w, stride):
                y2 = min(y + self.slice_size, h)
                x2 = min(x + self.slice_size, w)
                
                tile = image[y:y2, x:x2]
                tile_dets = self._run_yolo_single(tile, offset=(x, y))
                all_detections.extend(tile_dets)
                tile_count += 1
        
        # Apply NMS to merged detections
        detections = self._apply_nms(all_detections)
        
        elapsed = time.time() - start
        print(f"[SAHI] ✓ Fallback: {tile_count} tiles in {elapsed:.2f}s")
        print(f"[SAHI] ✓ Found {len(detections)} symbols (after NMS)")
        
        return detections
    
    def _run_yolo_single(self, image: np.ndarray, offset: Tuple[int, int]) -> List[DetectedSymbol]:
        """Run YOLO on single image/tile."""
        results = self._yolo_model(image, conf=self.confidence_threshold, verbose=False)
        
        detections = []
        for r in results:
            if r.boxes is None:
                continue
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                cls_name = self._yolo_model.names[cls_id]
                
                detections.append(DetectedSymbol(
                    class_name=cls_name,
                    confidence=conf,
                    x1=x1 + offset[0],
                    y1=y1 + offset[1],
                    x2=x2 + offset[0],
                    y2=y2 + offset[1],
                ))
        
        return detections
    
    def _apply_nms(self, detections: List[DetectedSymbol]) -> List[DetectedSymbol]:
        """Apply Non-Maximum Suppression."""
        if not detections:
            return []
        
        boxes = np.array([[d.x1, d.y1, d.x2, d.y2] for d in detections])
        scores = np.array([d.confidence for d in detections])
        
        # Sort by confidence (descending)
        order = scores.argsort()[::-1]
        keep = []
        
        while len(order) > 0:
            i = order[0]
            keep.append(i)
            
            if len(order) == 1:
                break
            
            # Calculate IoU with remaining boxes
            xx1 = np.maximum(boxes[i, 0], boxes[order[1:], 0])
            yy1 = np.maximum(boxes[i, 1], boxes[order[1:], 1])
            xx2 = np.minimum(boxes[i, 2], boxes[order[1:], 2])
            yy2 = np.minimum(boxes[i, 3], boxes[order[1:], 3])
            
            inter = np.maximum(0, xx2 - xx1) * np.maximum(0, yy2 - yy1)
            area_i = (boxes[i, 2] - boxes[i, 0]) * (boxes[i, 3] - boxes[i, 1])
            area_j = (boxes[order[1:], 2] - boxes[order[1:], 0]) * (boxes[order[1:], 3] - boxes[order[1:], 1])
            iou = inter / (area_i + area_j - inter + 1e-6)
            
            # Keep boxes with IoU below threshold
            inds = np.where(iou <= self.iou_threshold)[0]
            order = order[inds + 1]
        
        return [detections[i] for i in keep]


# =============================================================================
# PADDLEOCR ENGINE
# =============================================================================

class PaddleOCREngine:
    """
    PaddleOCR-based text extractor optimized for P&ID drawings.
    
    PaddleOCR significantly outperforms EasyOCR on:
      - Dense, cluttered text
      - Rotated text (common in P&IDs)
      - Technical engineering notation (FT-101, PSV-202)
    """
    
    def __init__(self, use_gpu: bool = True, lang: str = "en"):
        """
        Initialize PaddleOCR.
        
        Args:
            use_gpu: Use GPU acceleration (recommended on Kaggle T4)
            lang: Language code ("en" for English)
        """
        self._ocr = None
        self._easyocr_reader = None
        self._paddle_available = False
        
        self._init_ocr(use_gpu, lang)
    
    def _init_ocr(self, use_gpu: bool, lang: str):
        """Initialize OCR engine - PaddleOCR with MOBILE models for speed."""
        try:
            # Ensure OneDNN/MKLDNN is disabled before import
            import os
            os.environ["FLAGS_use_mkldnn"] = "0"
            os.environ["MKLDNN_CACHE_CAPACITY"] = "0" 
            os.environ["FLAGS_enable_pir_api"] = "0"
            os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
            os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"  # Skip connectivity check
            
            from paddleocr import PaddleOCR
            
            # SPEED-OPTIMIZED PaddleOCR - using MOBILE models (10x faster than server models)
            self._ocr = PaddleOCR(
                lang=lang,
                use_angle_cls=False,         # CRITICAL: Disable angle classification (slow)
                enable_mkldnn=False,         # Disable MKLDNN (Windows bug)
                # DETECTION MODEL: Use mobile (fast) instead of server (slow)
                det_model_dir=None,          # Let it use default mobile model
                det_limit_side_len=960,      # Default size (don't upscale internally)
                det_db_thresh=0.3,           # Standard threshold
                det_db_box_thresh=0.5,       # Standard box threshold
                # RECOGNITION MODEL: Use mobile (fast)
                rec_model_dir=None,          # Let it use default mobile model
                rec_batch_num=6,             # Batch size
            )
            self._paddle_available = True
            print(f"[OCR] ✓ PaddleOCR initialized (mobile models - FAST)")
            
        except ImportError:
            print("[OCR] ✗ PaddleOCR not installed, trying EasyOCR...")
            print("[OCR]   Install with: pip install paddlepaddle paddleocr")
            self._init_fallback(use_gpu)
            
        except Exception as e:
            print(f"[OCR] ✗ PaddleOCR failed: {e}")
            self._init_fallback(use_gpu)
            print(f"[OCR] ✗ PaddleOCR failed: {e}")
            self._init_fallback(use_gpu)
    
    def _init_fallback(self, use_gpu: bool):
        """Initialize EasyOCR as fallback."""
        try:
            import easyocr
            self._easyocr_reader = easyocr.Reader(
                ["en"],
                gpu=use_gpu,
                verbose=False,
            )
            print("[OCR] ✓ EasyOCR initialized (fallback)")
        except ImportError:
            print("[OCR] ✗ Neither PaddleOCR nor EasyOCR available!")
            print("[OCR]   Install with: pip install paddleocr")
        except Exception as e:
            print(f"[OCR] ✗ EasyOCR failed: {e}")
    
    def extract(self, image: np.ndarray) -> List[OCRText]:
        """
        Extract text from image.
        
        Args:
            image: BGR image as numpy array
            
        Returns:
            List of OCRText objects
        """
        h, w = image.shape[:2]
        print(f"[OCR] Processing image: {w}x{h} pixels")
        
        start = time.time()
        
        if self._paddle_available:
            try:
                results = self._extract_paddle(image)
            except Exception as e:
                print(f"[OCR] PaddleOCR runtime error: {e}")
                print("[OCR] Falling back to EasyOCR...")
                if self._easyocr_reader is None:
                    self._init_fallback(False)
                if self._easyocr_reader is not None:
                    results = self._extract_easyocr(image)
                else:
                    results = []
        elif self._easyocr_reader is not None:
            results = self._extract_easyocr(image)
        else:
            print("[OCR] ✗ No OCR engine available")
            return []
        
        elapsed = time.time() - start
        print(f"[OCR] ✓ Extracted {len(results)} text blocks in {elapsed:.2f}s")
        
        return results
    
    def _extract_paddle(self, image: np.ndarray) -> List[OCRText]:
        """Safely extract text without crashing on debug prints."""
        h, w = image.shape[:2]
        print(f"[OCR] Processing {w}x{h} image at original resolution (fast mode)")
        
        # 1. Run OCR safely
        try:
            raw_results = self._ocr.ocr(image) 
            print("[OCR] ✓ PaddleOCR completed")
        except Exception as e:
            print(f"[OCR] ✗ PaddleOCR failed to run: {e}")
            return []
            
        text_blocks = []
        if not raw_results:
            return text_blocks
            
        # 2. Get the first page results safely
        page_result = raw_results[0] if isinstance(raw_results, list) else raw_results
        if not page_result:
            return text_blocks
            
        # 3. Parse the nested output
        for idx, item in enumerate(page_result):
            try:
                # Standard format: [[[x1,y1], [x2,y2], [x3,y3], [x4,y4]], ('Text', conf)]
                if isinstance(item, (list, tuple)) and len(item) == 2:
                    bbox_points = item[0]
                    text_info = item[1]
                    
                    text = str(text_info[0]).strip()
                    conf = float(text_info[1])
                    
                    print(f"[OCR RAW] '{text}' (conf={conf:.2f})")
                    
                    xs = [float(p[0]) for p in bbox_points]
                    ys = [float(p[1]) for p in bbox_points]
                    
                    text_blocks.append(OCRText(
                        text=text,
                        confidence=conf,
                        x1=min(xs),
                        y1=min(ys),
                        x2=max(xs),
                        y2=max(ys)
                    ))
            except Exception as e:
                print(f"[OCR DEBUG] Skipped item {idx} due to parsing error: {e}")
                
        print(f"[OCR DEBUG] Parsed {len(text_blocks)} text blocks successfully")
        return text_blocks
    
    def _extract_easyocr(self, image: np.ndarray) -> List[OCRText]:
        """Extract text using EasyOCR."""
        results = self._easyocr_reader.readtext(image)
        
        text_blocks = []
        for bbox, text, conf in results:
            # bbox: [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
            xs = [p[0] for p in bbox]
            ys = [p[1] for p in bbox]
            
            text_blocks.append(OCRText(
                text=text.strip(),
                confidence=conf,
                x1=min(xs),
                y1=min(ys),
                x2=max(xs),
                y2=max(ys),
            ))
        
        return text_blocks


# =============================================================================
# SPATIAL CONSTRAINT ENGINE (Fixes "Text as Node" Bug)
# =============================================================================

class SpatialConstraintEngine:
    """
    Enforces strict spatial AND semantic constraints between OCR text and symbols.
    
    CRITICAL FIX: Text is ONLY assigned to instrument.bubble symbols if it 
    passes STRICT ISA S5.1 regex validation. This prevents garbage text like 
    "FURNACE", "FEED", "CONTROLLER" from being assigned as instrument tags.
    
    Association Rules:
      1. Spatial: Text center must be inside or near (<60px) symbol bbox
      2. Semantic: For instrument.bubble, text MUST match ISA pattern
      3. Priority: ISA-valid text gets higher association score
    """
    
    # Comprehensive BAN LIST - common P&ID words that are NOT instrument tags
    BAN_LIST = {
        # Equipment
        'PUMP', 'TANK', 'VALVE', 'FILTER', 'BURNER', 'BLOWER', 'FAN', 'MOTOR',
        'HEATER', 'COOLER', 'EXCHANGER', 'REACTOR', 'VESSEL', 'DRUM', 'COLUMN',
        'COMPRESSOR', 'TURBINE', 'MIXER', 'AGITATOR', 'SEPARATOR', 'SCRUBBER',
        'FURNACE', 'INCINERATOR', 'BOILER', 'CONDENSER', 'EVAPORATOR',
        
        # Process labels
        'FEED', 'FLOW', 'INLET', 'OUTLET', 'VENT', 'DRAIN', 'BYPASS', 'RETURN',
        'SUPPLY', 'SUCTION', 'DISCHARGE', 'OVERFLOW', 'RECYCLE', 'BLOWDOWN',
        'PRESSURE', 'TEMPERATURE', 'LEVEL', 'CONTROLLER', 'CONTROL',
        
        # Substances
        'AIR', 'GAS', 'WATER', 'STEAM', 'OIL', 'FUEL', 'ACID', 'NITROGEN',
        'SLUDGE', 'SLURRY', 'COOLANT', 'CONDENSATE', 'BRINE',
        
        # Directions
        'TO', 'FROM', 'OFF', 'ON', 'IN', 'OUT', 'UP', 'DOWN', 'TOP', 'BOTTOM',
        'NORTH', 'SOUTH', 'EAST', 'WEST', 'LEFT', 'RIGHT', 'UPPER', 'LOWER',
        
        # Drawing labels
        'LINE', 'PIPE', 'NOTE', 'REV', 'DATE', 'DWG', 'SHEET', 'FIGURE',
        'TYPICAL', 'TYP', 'SEE', 'REF', 'DETAIL', 'SECTION', 'VIEW',
        'STACK', 'HANDLING', 'HAMDLING', 'VACUUM', 'VACUUH', 'COOL',
        
        # Fragments
        'ALR', 'ING', 'ION', 'ERR', 'END', 'THE', 'AND', 'FOR', 'WITH',
    }
    
    # ISA S5.1 instrument tag prefixes
    ISA_TAG_PREFIXES = [
        "FT", "PT", "LT", "TT", "AT", "WT", "DT", "ST",
        "FC", "PC", "LC", "TC", "AC", "WC", "DC", "SC",
        "FI", "PI", "LI", "TI", "AI", "WI", "DI", "SI",
        "FV", "PV", "LV", "TV", "AV", "WV", "DV", "SV",
        "FIC", "PIC", "LIC", "TIC", "AIC", "WIC",
        "FRC", "PRC", "LRC", "TRC", "ARC",
        "PSV", "PRV", "TSV", "PSH", "PSL", "TSH", "TSL", "LSH", "LSL",
        "PSHH", "PSLL", "TSHH", "TSLL", "LSHH", "LSLL",
        "FE", "TE", "PE", "LE", "AE", "SE", "DE",
        "FAH", "FAL", "PAH", "PAL", "LAH", "LAL", "TAH", "TAL",
        "FS", "PS", "LS", "TS", "AS", "XV", "ZV", "HV",
        "PDT", "PDI", "PDC", "PDIC", "HC", "HIC", "HS",
    ]
    
    def __init__(
        self,
        max_proximity_px: float = 60.0,
        min_iou: float = 0.05,
        prefer_instrument_class: bool = True,
    ):
        self.max_proximity_px = max_proximity_px
        self.min_iou = min_iou
        self.prefer_instrument_class = prefer_instrument_class
        
        # Compile strict ISA pattern
        import re
        self._prefix_set = set(p.upper() for p in self.ISA_TAG_PREFIXES)
        
        # Pattern: 2-4 letters, optional dash, optional 1-4 digits, optional suffix
        self.strict_isa_pattern = re.compile(r'^[A-Z]{2,4}(?:-?\d{1,4}[A-Z]?)?$')
    
    def _sanitize_text(self, text: str) -> str:
        """
        Sanitize OCR text for ISA tag validation.
        Removes spaces, special chars (except dash), converts to uppercase.
        """
        # Uppercase and strip
        sanitized = text.upper().strip()
        # Remove spaces (OCR sometimes adds them: "F I C" -> "FIC")
        sanitized = sanitized.replace(' ', '')
        # Remove all chars except A-Z, 0-9, dash
        sanitized = ''.join(c for c in sanitized if c.isalnum() or c == '-')
        return sanitized
    
    def _is_strict_isa_tag(self, text: str) -> bool:
        """
        STRICT ISA tag validation using re.fullmatch().
        
        Returns True for: FIC, TT, PT, FT-101, PIC202, PSV-001
        Returns False for: FURNACE, FEED, CONTROLLER, STACK, Figure, ALR
        """
        sanitized = self._sanitize_text(text)
        
        # Reject if too short or too long
        if len(sanitized) < 2 or len(sanitized) > 8:
            return False
        
        # Reject if in ban list
        alpha_only = ''.join(c for c in sanitized if c.isalpha())
        if alpha_only in self.BAN_LIST:
            return False
        if sanitized in self.BAN_LIST:
            return False
        
        # Must match strict pattern (using fullmatch, not search!)
        if not self.strict_isa_pattern.fullmatch(sanitized):
            return False
        
        # Extract prefix (letters before any digits)
        prefix_match = re.match(r'^([A-Z]+)', sanitized)
        if prefix_match:
            prefix = prefix_match.group(1)
            # Must be a known ISA prefix
            if prefix in self._prefix_set:
                return True
            # Or a valid 2-letter ISA combination (first letter = measured var)
            if len(prefix) >= 2 and prefix[0] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                return True
        
        return False
    
    def is_isa_tag(self, text: str) -> bool:
        """Check if text matches ISA S5.1 pattern (for scoring)."""
        return self._is_strict_isa_tag(text)
    
    def associate(
        self,
        symbols: List[DetectedSymbol],
        text_blocks: List[OCRText],
    ) -> Tuple[Dict[int, str], List[OCRText]]:
        """
        Associate OCR text with symbols using STRICT spatial + semantic constraints.
        
        CRITICAL: For instrument.bubble symbols, text MUST pass _is_strict_isa_tag().
        """
        print(f"[SPATIAL] Associating {len(text_blocks)} text blocks with {len(symbols)} symbols")
        
        associations: Dict[int, str] = {}
        discarded: List[OCRText] = []
        
        # Track best match per symbol
        symbol_scores: Dict[int, Tuple[float, str]] = {}
        
        for text in text_blocks:
            # Skip very short text (noise)
            if len(text.text.strip()) < 2:
                discarded.append(text)
                continue
            
            # Pre-check if this text could be an ISA tag
            is_isa_tag = self._is_strict_isa_tag(text.text)
            sanitized = self._sanitize_text(text.text)
            
            # Find best matching symbol
            best_symbol_idx = None
            best_score = 0.0
            
            for idx, symbol in enumerate(symbols):
                # CRITICAL: For instrument bubbles, REQUIRE valid ISA tag
                if 'instrument' in symbol.class_name.lower() or 'bubble' in symbol.class_name.lower():
                    if not is_isa_tag:
                        # Skip this symbol - text is not a valid ISA tag
                        continue
                
                score = self._compute_association_score(text, symbol, is_isa_tag)
                
                if score > best_score:
                    best_score = score
                    best_symbol_idx = idx
            
            # Apply association threshold
            if best_symbol_idx is not None and best_score > 0:
                existing = symbol_scores.get(best_symbol_idx)
                if existing is None or best_score > existing[0]:
                    symbol_scores[best_symbol_idx] = (best_score, sanitized if is_isa_tag else text.text.upper())
                    print(f"[SPATIAL]   '{text.text}' -> symbol[{best_symbol_idx}] ({symbols[best_symbol_idx].class_name}) score={best_score:.2f}")
                else:
                    discarded.append(text)
            else:
                discarded.append(text)
        
        # Build final associations
        for idx, (score, tag) in symbol_scores.items():
            associations[idx] = tag
            symbols[idx].tag = tag
        
        print(f"[SPATIAL] ✓ Associated {len(associations)} tags")
        print(f"[SPATIAL] ✓ Discarded {len(discarded)} floating text blocks")
        
        if discarded:
            examples = [t.text for t in discarded[:5]]
            print(f"[SPATIAL]   Discarded examples: {examples}")
        
        return associations, discarded
    
    def _compute_association_score(
        self,
        text: OCRText,
        symbol: DetectedSymbol,
        is_isa_tag: bool,
    ) -> float:
        """
        Compute association score between text and symbol.
        Higher score = better match.
        
        Scoring factors:
          - IoU overlap (0-1)
          - Proximity to bbox edge (inverse distance)
          - Symbol class boost (instruments get priority)
          - ISA tag boost (recognized instrument tags)
        """
        # Calculate IoU
        iou = self._compute_iou(text, symbol)
        
        # Calculate proximity (distance from text center to symbol bbox edge)
        distance = self._distance_to_bbox(text.center, symbol)
        
        # Check if text center is inside symbol bbox
        inside = self._is_inside(text.center, symbol)
        
        # Base score
        score = 0.0
        
        # Method 1: IoU overlap
        if iou >= self.min_iou:
            score = max(score, 0.5 + iou * 0.5)  # 0.5 to 1.0
        
        # Method 2: Inside bbox
        if inside:
            score = max(score, 0.8)
        
        # Method 3: Proximity (only if within threshold)
        if distance <= self.max_proximity_px:
            # Linear decay: closer = higher score
            prox_score = 0.3 * (1 - distance / self.max_proximity_px)
            score = max(score, prox_score)
        
        # Boost for instrument symbols
        if self.prefer_instrument_class and "instrument" in symbol.class_name.lower():
            score *= 1.5
        
        # Boost for ISA tags
        if is_isa_tag:
            score *= 1.3
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _compute_iou(self, text: OCRText, symbol: DetectedSymbol) -> float:
        """Compute Intersection over Union."""
        # Intersection
        xi1 = max(text.x1, symbol.x1)
        yi1 = max(text.y1, symbol.y1)
        xi2 = min(text.x2, symbol.x2)
        yi2 = min(text.y2, symbol.y2)
        
        inter_width = max(0, xi2 - xi1)
        inter_height = max(0, yi2 - yi1)
        inter_area = inter_width * inter_height
        
        if inter_area == 0:
            return 0.0
        
        # Union
        text_area = (text.x2 - text.x1) * (text.y2 - text.y1)
        symbol_area = symbol.area
        union_area = text_area + symbol_area - inter_area
        
        return inter_area / union_area if union_area > 0 else 0.0
    
    def _distance_to_bbox(self, point: Tuple[float, float], symbol: DetectedSymbol) -> float:
        """Calculate minimum distance from point to bbox edge."""
        px, py = point
        
        # Clamp point to bbox
        cx = max(symbol.x1, min(px, symbol.x2))
        cy = max(symbol.y1, min(py, symbol.y2))
        
        # Distance from point to clamped point
        return np.sqrt((px - cx)**2 + (py - cy)**2)
    
    def _is_inside(self, point: Tuple[float, float], symbol: DetectedSymbol) -> bool:
        """Check if point is inside symbol bbox."""
        px, py = point
        return symbol.x1 <= px <= symbol.x2 and symbol.y1 <= py <= symbol.y2
    
    def is_isa_tag(self, text: str) -> bool:
        """Check if text matches ISA S5.1 instrument tag pattern."""
        normalized = text.upper().strip().replace(" ", "")
        return bool(self.isa_pattern.match(normalized))


# =============================================================================
# HIGH-DENSITY PIPELINE (MAIN CLASS)
# =============================================================================

class HighDensityPipeline:
    """
    Complete High-Density Vision Pipeline for complex P&ID drawings.
    
    Combines:
      1. SAHI sliced inference (fixes resolution collapse)
      2. PaddleOCR (better accuracy than EasyOCR)
      3. Spatial constraints (fixes "text as node" bug)
    
    Usage:
        pipeline = HighDensityPipeline("path/to/best.pt")
        result = pipeline.process("path/to/pid_drawing.png")
        
        # Access results
        print(f"Found {len(result.symbols)} symbols")
        for idx, tag in result.associated_tags.items():
            symbol = result.symbols[idx]
            print(f"  {symbol.class_name}: {tag}")
    """
    
    def __init__(
        self,
        model_path: str,
        # SAHI parameters
        slice_size: int = 640,
        overlap_ratio: float = 0.25,
        confidence_threshold: float = 0.20,
        # Spatial constraint parameters
        max_proximity_px: float = 60.0,
        min_iou: float = 0.05,
        # Hardware
        use_gpu: bool = True,
    ):
        """
        Initialize High-Density Pipeline.
        
        Args:
            model_path: Path to YOLOv8 model (best.pt)
            slice_size: SAHI tile size (default 640)
            overlap_ratio: SAHI tile overlap (default 0.25)
            confidence_threshold: YOLO confidence threshold
            max_proximity_px: Max distance for text-symbol association
            min_iou: Min IoU for overlap association
            use_gpu: Use GPU acceleration
        """
        print("=" * 60)
        print("EDAI4 HIGH-DENSITY VISION PIPELINE")
        print("=" * 60)
        
        # Validate model path
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        # Initialize components
        self.detector = SAHIDetector(
            model_path=model_path,
            slice_size=slice_size,
            overlap_ratio=overlap_ratio,
            confidence_threshold=confidence_threshold,
        )
        
        self.ocr = PaddleOCREngine(use_gpu=use_gpu)
        
        self.spatial = SpatialConstraintEngine(
            max_proximity_px=max_proximity_px,
            min_iou=min_iou,
        )
        
        print("=" * 60)
        print("Pipeline initialized successfully!")
        print("=" * 60)
    
    def process(self, image_path_or_array) -> PipelineResult:
        """
        Process a P&ID image through the full pipeline.
        
        Args:
            image_path_or_array: Path to image file OR numpy array (BGR)
            
        Returns:
            PipelineResult with all detections, text, and associations
        """
        timing = {}
        
        # Load image
        if isinstance(image_path_or_array, str):
            print(f"\n[PIPELINE] Loading image: {image_path_or_array}")
            image = cv2.imread(image_path_or_array)
            if image is None:
                raise ValueError(f"Failed to load image: {image_path_or_array}")
        else:
            image = image_path_or_array
        
        h, w = image.shape[:2]
        print(f"[PIPELINE] Image size: {w}x{h} pixels ({w*h/1e6:.1f} megapixels)")
        
        # Stage 1a: SAHI/YOLO Detection
        print("\n" + "-" * 40)
        print("STAGE 1a: SAHI/YOLO Symbol Detection")
        print("-" * 40)
        t0 = time.time()
        yolo_symbols = self.detector.detect(image)
        yolo_ms = (time.time() - t0) * 1000
        print(f"[YOLO] Found {len(yolo_symbols)} symbols")
        
        # Stage 1b: OpenCV Contour Circle Detection (bypasses YOLO blindness)
        print("\n" + "-" * 40)
        print("STAGE 1b: OpenCV Contour Circle Detection")
        print("-" * 40)
        t0 = time.time()
        circle_symbols = detect_circular_instruments(image)
        circle_ms = (time.time() - t0) * 1000
        print(f"[CONTOUR] Found {len(circle_symbols)} circular instruments")
        
        # Merge YOLO + Contour results (deduplicate by center proximity)
        symbols = self._merge_detections(yolo_symbols, circle_symbols)
        timing["detection_ms"] = yolo_ms + circle_ms
        print(f"[MERGED] Total symbols: {len(symbols)} (YOLO: {len(yolo_symbols)}, Contour: {len(circle_symbols)})")
        
        # Stage 2: OCR
        print("\n" + "-" * 40)
        print("STAGE 2: OCR Text Extraction")
        print("-" * 40)
        t0 = time.time()
        text_blocks = self.ocr.extract(image)
        timing["ocr_ms"] = (time.time() - t0) * 1000
        
        # Stage 3: Spatial Association
        print("\n" + "-" * 40)
        print("STAGE 3: Spatial Constraint Association")
        print("-" * 40)
        t0 = time.time()
        associations, discarded = self.spatial.associate(symbols, text_blocks)
        timing["association_ms"] = (time.time() - t0) * 1000
        
        timing["total_ms"] = sum(timing.values())
        
        # Summary
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETE")
        print("=" * 60)
        print(f"  YOLO symbols:        {len(yolo_symbols)}")
        print(f"  Contour circles:     {len(circle_symbols)}")
        print(f"  Total symbols:       {len(symbols)}")
        print(f"  Text blocks found:   {len(text_blocks)}")
        print(f"  Tags associated:     {len(associations)}")
        print(f"  Floating text:       {len(discarded)}")
        print(f"  Total time:          {timing['total_ms']:.0f}ms")
        print(f"    - YOLO:            {yolo_ms:.0f}ms")
        print(f"    - Contour:         {circle_ms:.0f}ms")
        print(f"    - OCR:             {timing['ocr_ms']:.0f}ms")
        print(f"    - Association:     {timing['association_ms']:.0f}ms")
        
        return PipelineResult(
            symbols=symbols,
            text_blocks=text_blocks,
            associated_tags=associations,
            discarded_text=discarded,
            timing=timing,
            image_size=(w, h),
        )
    
    def _merge_detections(
        self,
        yolo_symbols: List[DetectedSymbol],
        circle_symbols: List[DetectedSymbol],
        distance_threshold: float = 30.0,
    ) -> List[DetectedSymbol]:
        """
        Merge YOLO and contour-based detections, removing duplicates.
        
        Args:
            yolo_symbols: Detections from YOLO/SAHI
            circle_symbols: Detections from contour analysis
            distance_threshold: Max center distance to consider duplicate
            
        Returns:
            Merged list with duplicates removed
        """
        # Start with all YOLO detections (higher priority)
        merged = list(yolo_symbols)
        
        # Add contour detections that don't overlap with YOLO
        for circle in circle_symbols:
            cx, cy = circle.center
            is_duplicate = False
            
            for existing in merged:
                ex, ey = existing.center
                dist = np.sqrt((cx - ex)**2 + (cy - ey)**2)
                
                if dist < distance_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                merged.append(circle)
        
        return merged
    
    def visualize(
        self,
        image: np.ndarray,
        result: PipelineResult,
        output_path: Optional[str] = None,
    ) -> np.ndarray:
        """
        Visualize pipeline results on image.
        
        Args:
            image: Original BGR image
            result: PipelineResult from process()
            output_path: Optional path to save visualization
            
        Returns:
            Annotated image
        """
        vis = image.copy()
        
        # Color scheme
        COLORS = {
            "instrument": (0, 255, 0),    # Green
            "valve": (255, 0, 0),          # Blue
            "equipment": (0, 165, 255),    # Orange
            "fitting": (255, 255, 0),      # Cyan
            "line": (128, 128, 128),       # Gray
            "default": (255, 0, 255),      # Magenta
        }
        
        # Draw symbols
        for idx, symbol in enumerate(result.symbols):
            # Choose color based on class
            color = COLORS["default"]
            for key in COLORS:
                if key in symbol.class_name.lower():
                    color = COLORS[key]
                    break
            
            # Draw bounding box
            x1, y1, x2, y2 = int(symbol.x1), int(symbol.y1), int(symbol.x2), int(symbol.y2)
            cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{symbol.class_name}"
            if symbol.tag:
                label += f": {symbol.tag}"
            else:
                label += f" ({symbol.confidence:.0%})"
            
            # Background for text
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(vis, (x1, y1 - th - 4), (x1 + tw, y1), color, -1)
            cv2.putText(vis, label, (x1, y1 - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Draw discarded text (faded red)
        for text in result.discarded_text:
            x1, y1 = int(text.x1), int(text.y1)
            x2, y2 = int(text.x2), int(text.y2)
            cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 0, 128), 1)
        
        if output_path:
            cv2.imwrite(output_path, vis)
            print(f"[VIS] Saved visualization to: {output_path}")
        
        return vis


# =============================================================================
# MAIN (KAGGLE NOTEBOOK ENTRY POINT)
# =============================================================================

def main():
    """
    Example usage for Kaggle notebook.
    
    Run this in a Kaggle notebook cell:
    
        !pip install sahi paddlepaddle paddleocr -q
        
        from high_density_pipeline import HighDensityPipeline
        
        pipeline = HighDensityPipeline("/kaggle/working/best.pt")
        result = pipeline.process("/kaggle/input/your-pid/drawing.png")
        
        # Show results
        for idx, tag in result.associated_tags.items():
            sym = result.symbols[idx]
            print(f"{sym.class_name}: {tag}")
    """
    # Example paths (adjust for your environment)
    MODEL_PATH = "/kaggle/working/best.pt"
    IMAGE_PATH = "/kaggle/input/pid-test/incinerator_pid.png"
    
    # Check if running on Kaggle
    if os.path.exists("/kaggle/working"):
        print("Running on Kaggle environment")
    else:
        # Local development paths
        MODEL_PATH = "D:/EDAI4/models/yolov8/best.pt"
        IMAGE_PATH = "D:/EDAI4/data/test_images/complex_pid.png"
    
    # Initialize pipeline
    pipeline = HighDensityPipeline(
        model_path=MODEL_PATH,
        slice_size=640,
        overlap_ratio=0.25,
        confidence_threshold=0.20,
        max_proximity_px=60.0,
        use_gpu=True,
    )
    
    # Process image
    if os.path.exists(IMAGE_PATH):
        result = pipeline.process(IMAGE_PATH)
        
        # Print detected instruments with tags
        print("\n" + "=" * 60)
        print("DETECTED INSTRUMENTS WITH TAGS")
        print("=" * 60)
        
        for idx, tag in sorted(result.associated_tags.items()):
            symbol = result.symbols[idx]
            print(f"  [{symbol.class_name}] {tag} (conf: {symbol.confidence:.0%})")
    else:
        print(f"Test image not found: {IMAGE_PATH}")
        print("Please provide a valid image path.")


if __name__ == "__main__":
    main()
