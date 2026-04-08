"""
EDAI4 - SAHI-Powered Symbol Detector
=====================================
Slicing Aided Hyper Inference for detecting small symbols on large P&ID images.
Falls back to standard YOLO detection if SAHI is not available.
"""

import numpy as np
from typing import List, Tuple, Optional, NamedTuple
from pathlib import Path

class SAHIDetection(NamedTuple):
    """Single detection result."""
    class_name: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float


class SAHISymbolDetector:
    """
    SAHI-wrapped YOLO detector for P&ID symbols.
    Falls back to tiled YOLO if SAHI is not installed.
    """
    
    def __init__(
        self,
        model_path: str,
        confidence_threshold: float = 0.25,
        slice_size: int = 640,
        overlap_ratio: float = 0.2,
    ):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.slice_size = slice_size
        self.overlap_ratio = overlap_ratio
        
        self._sahi_available = False
        self._model = None
        self._sahi_model = None
        
        self._load_model()
    
    def _load_model(self):
        """Load YOLO model with SAHI wrapper if available."""
        try:
            from sahi import AutoDetectionModel
            from sahi.predict import get_sliced_prediction
            
            self._sahi_model = AutoDetectionModel.from_pretrained(
                model_type='yolov8',
                model_path=self.model_path,
                confidence_threshold=self.confidence_threshold,
                device='cuda:0',  # Will fallback to CPU if unavailable
            )
            self._sahi_available = True
            print(f"[SAHI] Loaded YOLO model with SAHI support")
            
        except ImportError:
            print("[SAHI] SAHI not installed, using fallback tiled detection")
            print("       Install with: pip install sahi")
            self._load_fallback_model()
        except Exception as e:
            print(f"[SAHI] Failed to load with SAHI: {e}, using fallback")
            self._load_fallback_model()
    
    def _load_fallback_model(self):
        """Load standard YOLO model for fallback."""
        try:
            from ultralytics import YOLO
            self._model = YOLO(self.model_path)
            print(f"[SAHI] Loaded YOLO model (fallback mode)")
        except Exception as e:
            print(f"[SAHI] Failed to load YOLO model: {e}")
            self._model = None
    
    def detect(self, image: np.ndarray) -> List[SAHIDetection]:
        """
        Run detection on image using SAHI sliced inference.
        
        Args:
            image: BGR image as numpy array
            
        Returns:
            List of SAHIDetection objects
        """
        if self._sahi_available and self._sahi_model is not None:
            return self._detect_with_sahi(image)
        elif self._model is not None:
            return self._detect_with_fallback(image)
        else:
            print("[SAHI] No model loaded, returning empty detections")
            return []
    
    def _detect_with_sahi(self, image: np.ndarray) -> List[SAHIDetection]:
        """Run SAHI sliced inference."""
        from sahi.predict import get_sliced_prediction
        
        h, w = image.shape[:2]
        
        # Adaptive slice size based on image dimensions
        slice_h = min(self.slice_size, h)
        slice_w = min(self.slice_size, w)
        
        result = get_sliced_prediction(
            image=image,
            detection_model=self._sahi_model,
            slice_height=slice_h,
            slice_width=slice_w,
            overlap_height_ratio=self.overlap_ratio,
            overlap_width_ratio=self.overlap_ratio,
            postprocess_type="NMS",
            postprocess_match_metric="IOU",
            postprocess_match_threshold=0.5,
            verbose=0,
        )
        
        detections = []
        for pred in result.object_prediction_list:
            bbox = pred.bbox
            detections.append(SAHIDetection(
                class_name=pred.category.name,
                confidence=pred.score.value,
                x1=bbox.minx,
                y1=bbox.miny,
                x2=bbox.maxx,
                y2=bbox.maxy,
            ))
        
        print(f"[SAHI] Detected {len(detections)} symbols using sliced inference")
        return detections
    
    def _detect_with_fallback(self, image: np.ndarray) -> List[SAHIDetection]:
        """Run tiled YOLO detection as fallback."""
        h, w = image.shape[:2]
        
        # For small images, run directly
        if max(h, w) <= self.slice_size * 1.5:
            return self._run_yolo(image, offset=(0, 0))
        
        # Tiled processing for large images
        overlap = int(self.slice_size * self.overlap_ratio)
        stride = self.slice_size - overlap
        
        all_detections = []
        tile_count = 0
        
        for y in range(0, h, stride):
            for x in range(0, w, stride):
                y2 = min(y + self.slice_size, h)
                x2 = min(x + self.slice_size, w)
                
                tile = image[y:y2, x:x2]
                tile_dets = self._run_yolo(tile, offset=(x, y))
                all_detections.extend(tile_dets)
                tile_count += 1
        
        # Apply NMS to remove duplicates from overlapping tiles
        detections = self._apply_nms(all_detections, iou_threshold=0.5)
        
        print(f"[SAHI] Fallback: {tile_count} tiles, {len(detections)} detections after NMS")
        return detections
    
    def _run_yolo(self, image: np.ndarray, offset: Tuple[int, int]) -> List[SAHIDetection]:
        """Run YOLO on single image/tile."""
        results = self._model(image, conf=self.confidence_threshold, verbose=False)
        
        detections = []
        for r in results:
            if r.boxes is None:
                continue
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                cls_name = self._model.names[cls_id]
                
                detections.append(SAHIDetection(
                    class_name=cls_name,
                    confidence=conf,
                    x1=x1 + offset[0],
                    y1=y1 + offset[1],
                    x2=x2 + offset[0],
                    y2=y2 + offset[1],
                ))
        
        return detections
    
    def _apply_nms(self, detections: List[SAHIDetection], iou_threshold: float) -> List[SAHIDetection]:
        """Apply Non-Maximum Suppression to remove overlapping detections."""
        if not detections:
            return []
        
        boxes = np.array([[d.x1, d.y1, d.x2, d.y2] for d in detections])
        scores = np.array([d.confidence for d in detections])
        
        keep = []
        order = scores.argsort()[::-1]
        
        while len(order) > 0:
            i = order[0]
            keep.append(i)
            
            if len(order) == 1:
                break
            
            xx1 = np.maximum(boxes[i, 0], boxes[order[1:], 0])
            yy1 = np.maximum(boxes[i, 1], boxes[order[1:], 1])
            xx2 = np.minimum(boxes[i, 2], boxes[order[1:], 2])
            yy2 = np.minimum(boxes[i, 3], boxes[order[1:], 3])
            
            inter = np.maximum(0, xx2 - xx1) * np.maximum(0, yy2 - yy1)
            area_i = (boxes[i, 2] - boxes[i, 0]) * (boxes[i, 3] - boxes[i, 1])
            area_j = (boxes[order[1:], 2] - boxes[order[1:], 0]) * (boxes[order[1:], 3] - boxes[order[1:], 1])
            iou = inter / (area_i + area_j - inter + 1e-6)
            
            inds = np.where(iou <= iou_threshold)[0]
            order = order[inds + 1]
        
        return [detections[i] for i in keep]


class PaddleOCREngine:
    """
    PaddleOCR wrapper for text extraction from P&ID images.
    Falls back to EasyOCR if PaddleOCR is not available.
    """
    
    def __init__(self, use_gpu: bool = False):
        self._paddle_available = False
        self._easyocr_available = False
        self._paddle_ocr = None
        self._easyocr_reader = None
        
        self._init_ocr(use_gpu)
    
    def _init_ocr(self, use_gpu: bool):
        """Initialize OCR engine, trying PaddleOCR first."""
        # Try PaddleOCR first
        try:
            from paddleocr import PaddleOCR
            # PaddleOCR 2.7+ API - no show_log or use_gpu params
            self._paddle_ocr = PaddleOCR(
                use_angle_cls=True,
                lang='en',
            )
            self._paddle_available = True
            print("[OCR] PaddleOCR initialized")
            return
        except ImportError:
            print("[OCR] PaddleOCR not installed, trying EasyOCR")
        except Exception as e:
            print(f"[OCR] PaddleOCR failed: {e}, trying EasyOCR")
        
        # Fallback to EasyOCR
        try:
            import easyocr
            self._easyocr_reader = easyocr.Reader(['en'], gpu=use_gpu, verbose=False)
            self._easyocr_available = True
            print("[OCR] EasyOCR initialized (fallback)")
        except ImportError:
            print("[OCR] Neither PaddleOCR nor EasyOCR available!")
            print("       Install with: pip install paddlepaddle paddleocr")
            print("       Or: pip install easyocr")
        except Exception as e:
            print(f"[OCR] EasyOCR failed: {e}")
    
    def extract_text(self, image: np.ndarray) -> List[dict]:
        """
        Extract text from image.
        
        Returns:
            List of dicts with 'text', 'center', 'confidence' keys
        """
        if self._paddle_available:
            return self._extract_with_paddle(image)
        elif self._easyocr_available:
            return self._extract_with_easyocr(image)
        else:
            print("[OCR] No OCR engine available")
            return []
    
    def _extract_with_paddle(self, image: np.ndarray) -> List[dict]:
        """Extract text using PaddleOCR."""
        # PaddleOCR v3+ API - no cls parameter
        results = self._paddle_ocr.ocr(image)
        
        text_blocks = []
        if results and results[0]:
            for line in results[0]:
                if line and len(line) >= 2:
                    bbox, (text, conf) = line[0], line[1]
                    # bbox is [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
                    cx = (bbox[0][0] + bbox[2][0]) / 2
                    cy = (bbox[0][1] + bbox[2][1]) / 2
                    text_blocks.append({
                        'text': text.upper().strip(),
                        'center': (cx, cy),
                        'confidence': conf,
                        'bbox': bbox,
                    })
        
        print(f"[OCR] PaddleOCR found {len(text_blocks)} text blocks")
        return text_blocks
    
    def _extract_with_easyocr(self, image: np.ndarray) -> List[dict]:
        """Extract text using EasyOCR."""
        results = self._easyocr_reader.readtext(image)
        
        text_blocks = []
        for bbox, text, conf in results:
            cx = (bbox[0][0] + bbox[2][0]) / 2
            cy = (bbox[0][1] + bbox[2][1]) / 2
            text_blocks.append({
                'text': text.upper().strip(),
                'center': (cx, cy),
                'confidence': conf,
                'bbox': bbox,
            })
        
        print(f"[OCR] EasyOCR found {len(text_blocks)} text blocks")
        return text_blocks


class SAHIPipeline:
    """
    Combined SAHI detection + OCR pipeline.
    """
    
    # ISA S5.1 instrument tag patterns
    ISA_PREFIXES = [
        'FT', 'PT', 'LT', 'TT', 'AT',  # Transmitters
        'FC', 'PC', 'LC', 'TC', 'AC',  # Controllers
        'FI', 'PI', 'LI', 'TI', 'AI',  # Indicators
        'FV', 'PV', 'LV', 'TV', 'AV',  # Valves
        'FIC', 'PIC', 'LIC', 'TIC',    # Indicating Controllers
        'PSV', 'PRV', 'TSV',            # Safety valves
        'PSH', 'PSL', 'TSH', 'TSL',     # Switches
        'FE', 'TE', 'PE', 'LE',         # Elements
    ]
    
    def __init__(self, model_path: str, confidence_threshold: float = 0.25, use_gpu: bool = False):
        self.detector = SAHISymbolDetector(model_path, confidence_threshold)
        self.ocr = PaddleOCREngine(use_gpu=use_gpu)
    
    def process(self, image: np.ndarray) -> dict:
        """
        Process image with SAHI detection and OCR.
        
        Returns:
            dict with 'detections', 'text_blocks', 'instruments' keys
        """
        import re
        import time
        
        start = time.time()
        
        # Run SAHI detection
        det_start = time.time()
        detections = self.detector.detect(image)
        det_time = (time.time() - det_start) * 1000
        
        # Run OCR
        ocr_start = time.time()
        text_blocks = self.ocr.extract_text(image)
        ocr_time = (time.time() - ocr_start) * 1000
        
        # Find instrument tags from OCR
        instruments = []
        isa_pattern = re.compile(r'^[FPTLAIC][A-Z]{1,3}[-_]?\d+', re.IGNORECASE)
        
        for tb in text_blocks:
            text = tb['text'].strip()
            
            # Check if it's an ISA tag
            is_isa = False
            if isa_pattern.match(text):
                is_isa = True
            else:
                for prefix in self.ISA_PREFIXES:
                    if text.startswith(prefix) and len(text) > len(prefix):
                        is_isa = True
                        break
            
            if is_isa:
                cx, cy = tb['center']
                
                # Check if we already have a detection near this tag
                associated_det = None
                for det in detections:
                    det_cx = (det.x1 + det.x2) / 2
                    det_cy = (det.y1 + det.y2) / 2
                    dist = ((cx - det_cx)**2 + (cy - det_cy)**2)**0.5
                    if dist < 100:  # Within 100px
                        associated_det = det
                        break
                
                instruments.append({
                    'tag': text,
                    'center': (cx, cy),
                    'confidence': tb['confidence'],
                    'associated_detection': associated_det._asdict() if associated_det else None,
                })
        
        total_time = (time.time() - start) * 1000
        
        print(f"[SAHI Pipeline] Detection: {det_time:.1f}ms, OCR: {ocr_time:.1f}ms, Total: {total_time:.1f}ms")
        print(f"[SAHI Pipeline] {len(detections)} symbols, {len(text_blocks)} text, {len(instruments)} instruments")
        
        return {
            'detections': detections,
            'text_blocks': text_blocks,
            'instruments': instruments,
            'timing': {
                'detection_ms': det_time,
                'ocr_ms': ocr_time,
                'total_ms': total_time,
            }
        }
