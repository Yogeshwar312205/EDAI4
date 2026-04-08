# =============================================================================
# EDAI4 QUICK FIX - SAHI + PaddleOCR (No VLM Required)
# =============================================================================
# 
# This is the MINIMAL upgrade that solves the immediate problems:
# 1. SAHI for small object detection (fixes "0 instruments" issue)
# 2. PaddleOCR as reliable OCR fallback (fixes "OCR failed" issue)
#
# This script can run on ANY GPU (even 4GB) and is much faster than
# the full Florence-2 multimodal approach.
#
# Target: Kaggle T4 GPU or local development
# =============================================================================

"""
INSTALLATION (run first):
!pip install -q ultralytics sahi paddlepaddle paddleocr
"""

import os
import re
import cv2
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class QuickFixConfig:
    """Minimal configuration for quick fix."""
    # YOLO Model
    yolo_model_path: str = "/kaggle/input/edai4-golden-model/best.pt"
    
    # SAHI Settings
    slice_height: int = 640
    slice_width: int = 640
    overlap_ratio: float = 0.25
    confidence_threshold: float = 0.2  # Lower for better recall
    
    # OCR Settings
    ocr_lang: str = "en"
    tag_search_radius: int = 100  # Pixels to search for tag near detection
    
    # ISA Pattern
    isa_pattern: str = r'[FPTLACIS][IRTCASVHE][-_]?\d{2,4}[A-Z]?'


# =============================================================================
# SAHI DETECTOR (Simplified)
# =============================================================================

class QuickSAHIDetector:
    """Simplified SAHI detector for immediate use."""
    
    def __init__(self, config: QuickFixConfig):
        self.config = config
        self.model = None
        self.sahi_model = None
        self._load()
    
    def _load(self):
        """Load SAHI-wrapped YOLO model."""
        try:
            from sahi import AutoDetectionModel
            
            self.sahi_model = AutoDetectionModel.from_pretrained(
                model_type="yolov8",
                model_path=self.config.yolo_model_path,
                confidence_threshold=self.config.confidence_threshold,
                device="cuda:0",  # Use GPU
            )
            print(f"✅ SAHI + YOLO loaded")
        except Exception as e:
            print(f"⚠️ SAHI failed: {e}, using standard YOLO")
            from ultralytics import YOLO
            self.model = YOLO(self.config.yolo_model_path)
    
    def detect(self, image: np.ndarray) -> List[Dict]:
        """Run detection with SAHI slicing."""
        if self.sahi_model:
            return self._detect_sahi(image)
        return self._detect_standard(image)
    
    def _detect_sahi(self, image: np.ndarray) -> List[Dict]:
        """SAHI sliced detection."""
        from sahi.predict import get_sliced_prediction
        
        # SAHI expects RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        result = get_sliced_prediction(
            image=image_rgb,
            detection_model=self.sahi_model,
            slice_height=self.config.slice_height,
            slice_width=self.config.slice_width,
            overlap_height_ratio=self.config.overlap_ratio,
            overlap_width_ratio=self.config.overlap_ratio,
            postprocess_type="NMS",
            postprocess_match_threshold=0.5,
            verbose=0,
        )
        
        detections = []
        for pred in result.object_prediction_list:
            bbox = pred.bbox
            detections.append({
                "class_name": pred.category.name,
                "confidence": pred.score.value,
                "bbox": {"x1": bbox.minx, "y1": bbox.miny, "x2": bbox.maxx, "y2": bbox.maxy},
                "center": ((bbox.minx + bbox.maxx) / 2, (bbox.miny + bbox.maxy) / 2),
            })
        
        return detections
    
    def _detect_standard(self, image: np.ndarray) -> List[Dict]:
        """Fallback standard YOLO."""
        results = self.model(image, conf=self.config.confidence_threshold, verbose=False)
        
        detections = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                detections.append({
                    "class_name": self.model.names[int(box.cls[0])],
                    "confidence": float(box.conf[0]),
                    "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    "center": ((x1 + x2) / 2, (y1 + y2) / 2),
                })
        
        return detections


# =============================================================================
# PADDLEOCR WRAPPER
# =============================================================================

class QuickOCR:
    """PaddleOCR wrapper with ISA tag extraction."""
    
    def __init__(self, config: QuickFixConfig):
        self.config = config
        self.ocr = None
        self._load()
    
    def _load(self):
        """Load PaddleOCR."""
        try:
            from paddleocr import PaddleOCR
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang=self.config.ocr_lang,
                show_log=False,
                use_gpu=True,
            )
            print("✅ PaddleOCR loaded")
        except Exception as e:
            print(f"⚠️ PaddleOCR failed: {e}")
            self.ocr = None
    
    def extract_all_text(self, image: np.ndarray) -> List[Dict]:
        """Extract all text with positions."""
        if self.ocr is None:
            return []
        
        try:
            result = self.ocr.ocr(image, cls=True)
            
            texts = []
            if result and result[0]:
                for line in result[0]:
                    bbox = line[0]
                    text = line[1][0]
                    conf = line[1][1]
                    
                    # Calculate center
                    cx = (bbox[0][0] + bbox[2][0]) / 2
                    cy = (bbox[0][1] + bbox[2][1]) / 2
                    
                    texts.append({
                        "text": text,
                        "confidence": conf,
                        "center": (cx, cy),
                        "bbox": bbox,
                    })
            
            return texts
        except Exception as e:
            print(f"OCR error: {e}")
            return []
    
    def extract_isa_tags(self, image: np.ndarray) -> List[str]:
        """Extract ISA S5.1 tags from image."""
        texts = self.extract_all_text(image)
        
        pattern = re.compile(self.config.isa_pattern, re.IGNORECASE)
        tags = []
        
        for text_info in texts:
            found = pattern.findall(text_info["text"].upper())
            tags.extend(found)
        
        # Normalize tags (add hyphen if missing)
        normalized = []
        for tag in set(tags):
            tag = tag.upper().strip()
            match = re.match(r'^([A-Z]{2,3})(\d+)([A-Z]?)$', tag)
            if match:
                normalized.append(f"{match.group(1)}-{match.group(2)}{match.group(3)}")
            else:
                normalized.append(tag)
        
        return normalized


# =============================================================================
# TEXT-DETECTION ASSOCIATION
# =============================================================================

def associate_tags_with_detections(
    detections: List[Dict],
    ocr_texts: List[Dict],
    search_radius: int = 100,
    isa_pattern: str = r'[FPTLACIS][IRTCASVHE][-_]?\d{2,4}[A-Z]?'
) -> List[Dict]:
    """
    Associate OCR text with nearby detections.
    
    For each detection, find the closest ISA tag within search_radius.
    """
    pattern = re.compile(isa_pattern, re.IGNORECASE)
    
    for det in detections:
        det["tag"] = None
        det["tag_confidence"] = 0.0
        
        cx, cy = det["center"]
        best_tag = None
        best_dist = search_radius
        
        for text_info in ocr_texts:
            # Check if text looks like an ISA tag
            text = text_info["text"].upper()
            if not pattern.match(text):
                continue
            
            # Calculate distance
            tx, ty = text_info["center"]
            dist = ((cx - tx)**2 + (cy - ty)**2)**0.5
            
            if dist < best_dist:
                best_dist = dist
                best_tag = text
                det["tag_confidence"] = text_info["confidence"]
        
        if best_tag:
            # Normalize tag
            match = re.match(r'^([A-Z]{2,3})(\d+)([A-Z]?)$', best_tag)
            if match:
                best_tag = f"{match.group(1)}-{match.group(2)}{match.group(3)}"
            det["tag"] = best_tag
    
    return detections


# =============================================================================
# UNIFIED QUICK FIX PIPELINE
# =============================================================================

class QuickFixPipeline:
    """
    Minimal pipeline that fixes the immediate issues:
    - Uses SAHI for small object detection
    - Uses PaddleOCR for reliable text extraction
    - Associates tags with detections
    """
    
    def __init__(self, config: Optional[QuickFixConfig] = None):
        self.config = config or QuickFixConfig()
        
        print("=" * 50)
        print("🔧 EDAI4 QUICK FIX PIPELINE")
        print("=" * 50)
        
        self.detector = QuickSAHIDetector(self.config)
        self.ocr = QuickOCR(self.config)
        
        print("=" * 50)
    
    def process(self, image_path: str) -> Dict:
        """
        Process a P&ID image.
        
        Returns:
            Dict with detections, tags, and statistics
        """
        import time
        start = time.time()
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load: {image_path}")
        
        h, w = image.shape[:2]
        print(f"📄 Image: {w}x{h}")
        
        # Step 1: SAHI Detection
        print("🔍 Running SAHI detection...")
        detections = self.detector.detect(image)
        print(f"   Found {len(detections)} objects")
        
        # Count by type
        type_counts = {}
        for d in detections:
            cls = d["class_name"]
            type_counts[cls] = type_counts.get(cls, 0) + 1
        
        for cls, count in sorted(type_counts.items(), key=lambda x: -x[1])[:5]:
            print(f"   - {cls}: {count}")
        
        # Step 2: OCR
        print("📝 Running OCR...")
        ocr_texts = self.ocr.extract_all_text(image)
        print(f"   Found {len(ocr_texts)} text blocks")
        
        # Step 3: Extract ISA tags
        isa_tags = self.ocr.extract_isa_tags(image)
        print(f"   ISA tags: {len(isa_tags)}")
        
        # Step 4: Associate tags with detections
        print("🔗 Associating tags...")
        detections = associate_tags_with_detections(
            detections, 
            ocr_texts,
            search_radius=self.config.tag_search_radius,
            isa_pattern=self.config.isa_pattern,
        )
        
        tagged_count = sum(1 for d in detections if d.get("tag"))
        print(f"   Tagged detections: {tagged_count}")
        
        # Calculate instruments
        instrument_dets = [d for d in detections if "instrument" in d["class_name"].lower()]
        
        elapsed = (time.time() - start) * 1000
        
        result = {
            "image_path": image_path,
            "image_size": (w, h),
            "processing_time_ms": elapsed,
            "detection_count": len(detections),
            "instrument_count": len(instrument_dets),
            "ocr_text_count": len(ocr_texts),
            "isa_tag_count": len(isa_tags),
            "tagged_detection_count": tagged_count,
            "detections": detections,
            "isa_tags": isa_tags,
            "type_counts": type_counts,
        }
        
        print(f"\n✅ Done in {elapsed:.0f}ms")
        return result
    
    def visualize(self, image_path: str, result: Dict, output_path: str = None):
        """Draw detections and tags on image."""
        image = cv2.imread(image_path)
        
        for det in result["detections"]:
            bbox = det["bbox"]
            x1, y1 = int(bbox["x1"]), int(bbox["y1"])
            x2, y2 = int(bbox["x2"]), int(bbox["y2"])
            
            # Color by type
            if "instrument" in det["class_name"].lower():
                color = (0, 255, 0)  # Green
            elif "valve" in det["class_name"].lower():
                color = (255, 0, 0)  # Blue
            else:
                color = (0, 165, 255)  # Orange
            
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            
            # Draw tag if present
            tag = det.get("tag")
            if tag:
                cv2.putText(image, tag, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.5, (0, 255, 0), 2)
            else:
                cv2.putText(image, det["class_name"][:10], (x1, y1-5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        if output_path:
            cv2.imwrite(output_path, image)
            print(f"💾 Saved: {output_path}")
        
        return image


# =============================================================================
# MAIN
# =============================================================================

def run_quick_fix(image_path: str, model_path: str = None):
    """
    Run the quick fix pipeline on an image.
    
    Args:
        image_path: Path to P&ID image
        model_path: Path to YOLO model (optional)
    """
    config = QuickFixConfig()
    if model_path:
        config.yolo_model_path = model_path
    
    pipeline = QuickFixPipeline(config)
    result = pipeline.process(image_path)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 RESULTS SUMMARY")
    print("=" * 50)
    print(f"Detections: {result['detection_count']}")
    print(f"Instruments: {result['instrument_count']}")
    print(f"ISA Tags Found: {result['isa_tag_count']}")
    print(f"Tagged Detections: {result['tagged_detection_count']}")
    print(f"\nISA Tags: {result['isa_tags']}")
    
    # Save visualization
    output_path = image_path.replace(".jpg", "_detected.jpg").replace(".png", "_detected.png")
    pipeline.visualize(image_path, result, output_path)
    
    return result


# =============================================================================
# KAGGLE EXECUTION
# =============================================================================

if __name__ == "__main__":
    import glob
    
    # Find image
    search_paths = [
        "/kaggle/input/**/images/**/*.jpg",
        "/kaggle/input/**/*.png",
        "/kaggle/working/*.jpg",
    ]
    
    image_path = None
    for pattern in search_paths:
        found = glob.glob(pattern, recursive=True)
        if found:
            image_path = found[0]
            break
    
    if image_path:
        print(f"📄 Found image: {image_path}")
        
        # Find model
        model_paths = [
            "/kaggle/input/edai4-golden-model/best.pt",
            "/kaggle/input/**/best.pt",
        ]
        
        model_path = None
        for pattern in model_paths:
            found = glob.glob(pattern, recursive=True)
            if found:
                model_path = found[0]
                break
        
        if model_path:
            run_quick_fix(image_path, model_path)
        else:
            print("⚠️ YOLO model not found")
    else:
        print("⚠️ No image found")
