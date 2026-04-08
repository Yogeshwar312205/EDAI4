# ============================================================================
# EDAI4 - IMPROVED DETECTION (Fixes Low Detection on Full P&IDs)
# ============================================================================
# This script uses optimized settings for detecting symbols on FULL P&ID sheets
# 
# CHANGES FROM ORIGINAL:
# 1. Lower confidence threshold (0.25 instead of 0.4)
# 2. Higher resolution (1280px)
# 3. Image preprocessing (contrast enhancement)
# 4. Tiled detection for large images
# ============================================================================

print("=" * 70)
print("EDAI4 - IMPROVED FULL P&ID DETECTION")
print("=" * 70)

# Install dependencies
import subprocess
subprocess.run(["pip", "install", "-q", "ultralytics", "easyocr", "networkx"])

import os
import sys
import glob
import math
import re
import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple, Any
from enum import Enum

from ultralytics import YOLO
import easyocr

# ============================================================================
# CONFIGURATION - OPTIMIZED FOR FULL P&IDs
# ============================================================================

CONFIG = {
    'confidence': 0.25,      # Lower than default 0.4
    'image_size': 1280,      # Higher resolution
    'use_tiles': True,       # Tile large images
    'tile_size': 800,
    'tile_overlap': 200,
    'enhance_contrast': True,
    'ocr_radius_multiplier': 2.0,  # Larger search radius for tags
}

# Find model
MODEL_PATHS = [
    "/kaggle/input/edai4-golden-model/best.pt",
    "/kaggle/input/datasets/yogeshwarvshinde/edai4-golden-model/best.pt",
]
MODEL_PATH = next((p for p in MODEL_PATHS if os.path.exists(p)), None)

if not MODEL_PATH:
    raise FileNotFoundError("Model not found! Attach yogeshwarvshinde/edai4-golden-model")

print(f"✓ Model: {MODEL_PATH}")

# Find test images
IMAGE_PATTERNS = [
    "/kaggle/working/**/*.png",
    "/kaggle/working/**/*.jpg",
    "/kaggle/input/**/*.png",
    "/kaggle/input/**/*.jpg",
]

all_images = []
for pattern in IMAGE_PATTERNS:
    all_images.extend(glob.glob(pattern, recursive=True))

# Filter for full P&IDs (larger files)
full_pids = [(p, os.path.getsize(p)) for p in all_images if os.path.getsize(p) > 100000]
full_pids.sort(key=lambda x: -x[1])

if full_pids:
    TEST_IMAGE = full_pids[0][0]
    print(f"✓ Test Image: {os.path.basename(TEST_IMAGE)} ({full_pids[0][1]//1024}KB)")
else:
    print("⚠ No large images found - using first available")
    TEST_IMAGE = all_images[0] if all_images else None

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class BoundingBox:
    x1: float; y1: float; x2: float; y2: float
    @property
    def center(self): return ((self.x1+self.x2)/2, (self.y1+self.y2)/2)
    @property
    def width(self): return self.x2 - self.x1
    @property
    def height(self): return self.y2 - self.y1

@dataclass
class Detection:
    class_name: str
    confidence: float
    bbox: BoundingBox
    tag: Optional[str] = None
    functions: List[str] = field(default_factory=list)

class NodeType(Enum):
    INSTRUMENT = "instrument"
    VALVE = "valve"
    EQUIPMENT = "equipment"
    PUMP = "pump"
    LINE = "line"
    UNKNOWN = "unknown"

CLASS_TYPE_MAP = {
    "instrument.bubble": NodeType.INSTRUMENT,
    "instrument.inline": NodeType.INSTRUMENT,
    "valve.control": NodeType.VALVE,
    "valve.general": NodeType.VALVE,
    "valve.ball": NodeType.VALVE,
    "valve.gate": NodeType.VALVE,
    "valve.globe": NodeType.VALVE,
    "valve.butterfly": NodeType.VALVE,
    "valve.check": NodeType.VALVE,
    "valve.plug": NodeType.VALVE,
    "valve.safety_relief": NodeType.VALVE,
    "equipment.pump": NodeType.PUMP,
    "equipment.compressor_blower": NodeType.EQUIPMENT,
    "line.flow_arrow": NodeType.LINE,
}

ISA_FIRST_LETTERS = {
    'A': 'Analysis', 'B': 'Burner', 'C': 'Conductivity',
    'D': 'Density', 'E': 'Voltage', 'F': 'Flow',
    'G': 'Gauging', 'H': 'Hand', 'I': 'Current',
    'J': 'Power', 'K': 'Time', 'L': 'Level',
    'M': 'Moisture', 'N': 'User', 'O': 'User',
    'P': 'Pressure', 'Q': 'Quantity', 'R': 'Radiation',
    'S': 'Speed', 'T': 'Temperature', 'U': 'Multi',
    'V': 'Vibration', 'W': 'Weight', 'X': 'Unclassified',
    'Y': 'Event', 'Z': 'Position',
}

ISA_FUNCTIONS = {
    'A': 'Alarm', 'C': 'Controller', 'E': 'Element',
    'G': 'Gauge', 'H': 'High', 'I': 'Indicator',
    'L': 'Low', 'R': 'Recorder', 'S': 'Switch',
    'T': 'Transmitter', 'V': 'Valve', 'Y': 'Relay',
}

# ============================================================================
# IMPROVED DETECTION FUNCTIONS
# ============================================================================

def enhance_image(img):
    """Enhance contrast for better detection."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    enhanced = cv2.merge([l, a, b])
    return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)


def compute_iou(box1, box2):
    """Compute IoU between two boxes."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    if x2 < x1 or y2 < y1:
        return 0.0
    
    inter = (x2-x1) * (y2-y1)
    area1 = (box1[2]-box1[0]) * (box1[3]-box1[1])
    area2 = (box2[2]-box2[0]) * (box2[3]-box2[1])
    
    return inter / (area1 + area2 - inter + 1e-6)


def nms(detections, iou_thresh=0.5):
    """Non-max suppression."""
    if not detections:
        return []
    
    dets = sorted(detections, key=lambda x: -x.confidence)
    keep = []
    
    for det in dets:
        is_dup = False
        for kept in keep:
            if det.class_name == kept.class_name:
                b1 = (det.bbox.x1, det.bbox.y1, det.bbox.x2, det.bbox.y2)
                b2 = (kept.bbox.x1, kept.bbox.y1, kept.bbox.x2, kept.bbox.y2)
                if compute_iou(b1, b2) > iou_thresh:
                    is_dup = True
                    break
        if not is_dup:
            keep.append(det)
    
    return keep


def detect_improved(img, model, config):
    """Improved detection with preprocessing and tiling."""
    h, w = img.shape[:2]
    
    # Enhance image
    if config['enhance_contrast']:
        img = enhance_image(img)
    
    all_dets = []
    
    # Full image detection
    results = model(img, conf=config['confidence'], imgsz=config['image_size'], verbose=False)
    
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            all_dets.append(Detection(
                class_name=model.names[int(box.cls[0])],
                confidence=float(box.conf[0]),
                bbox=BoundingBox(float(x1), float(y1), float(x2), float(y2))
            ))
    
    # Tiled detection for large images
    if config['use_tiles'] and (w > 1500 or h > 1500):
        ts = config['tile_size']
        ov = config['tile_overlap']
        
        for y0 in range(0, h - ov, ts - ov):
            for x0 in range(0, w - ov, ts - ov):
                tile = img[y0:y0+ts, x0:x0+ts]
                
                tile_results = model(tile, conf=config['confidence'], verbose=False)
                
                for r in tile_results:
                    for box in r.boxes:
                        tx1, ty1, tx2, ty2 = box.xyxy[0].cpu().numpy()
                        all_dets.append(Detection(
                            class_name=model.names[int(box.cls[0])],
                            confidence=float(box.conf[0]),
                            bbox=BoundingBox(
                                float(tx1 + x0), float(ty1 + y0),
                                float(tx2 + x0), float(ty2 + y0)
                            )
                        ))
    
    # Remove duplicates
    return nms(all_dets)


def parse_tag(text):
    """Parse ISA S5.1 tag."""
    text = text.strip().upper()
    pattern = r'^(?:(\d+)-)?([A-Z])([A-Z]*)-?(\d+)([A-Z]?)$'
    match = re.match(pattern, text)
    
    if not match:
        return None
    
    area, first, succ, loop, suffix = match.groups()
    
    if first not in ISA_FIRST_LETTERS:
        return None
    
    funcs = [ISA_FUNCTIONS[l] for l in succ if l in ISA_FUNCTIONS]
    
    return {
        'tag': text,
        'variable': ISA_FIRST_LETTERS[first],
        'functions': funcs,
        'loop': loop,
    }


def associate_tags(img, detections, config):
    """Associate OCR text with detections."""
    reader = easyocr.Reader(['en'], gpu=True, verbose=False)
    ocr_results = reader.readtext(img)
    
    for det in detections:
        cx, cy = det.bbox.center
        radius = max(det.bbox.width, det.bbox.height) * config['ocr_radius_multiplier']
        
        best_match = None
        best_dist = float('inf')
        
        for bbox, text, conf in ocr_results:
            tx, ty = np.mean(bbox, axis=0)
            dist = math.sqrt((cx - tx)**2 + (cy - ty)**2)
            
            if dist < radius and dist < best_dist:
                parsed = parse_tag(text)
                if parsed:
                    best_match = parsed
                    best_dist = dist
        
        if best_match:
            det.tag = best_match['tag']
            det.functions = best_match['functions']
    
    return detections


# ============================================================================
# MAIN PIPELINE
# ============================================================================

print("\n" + "=" * 70)
print("RUNNING IMPROVED PIPELINE")
print("=" * 70)

# Load model
model = YOLO(MODEL_PATH)
print(f"✓ Model loaded ({len(model.names)} classes)")

if TEST_IMAGE:
    # Load image
    img = cv2.imread(TEST_IMAGE)
    h, w = img.shape[:2]
    print(f"✓ Image loaded: {w}x{h}")
    
    # Run improved detection
    print("\n⚙️ Layer 1: Running improved detection...")
    detections = detect_improved(img, model, CONFIG)
    print(f"   → {len(detections)} symbols detected")
    
    # Class breakdown
    class_counts = Counter(d.class_name for d in detections)
    print("   Class breakdown:")
    for cls, cnt in class_counts.most_common(10):
        print(f"      {cls}: {cnt}")
    
    # OCR and tag association
    print("\n⚙️ Layer 2: OCR and tag association...")
    detections = associate_tags(img, detections, CONFIG)
    tagged = sum(1 for d in detections if d.tag)
    print(f"   → {tagged}/{len(detections)} symbols tagged")
    
    # Show tagged instruments
    if tagged > 0:
        print("   Tagged instruments:")
        for d in detections:
            if d.tag:
                print(f"      {d.tag} ({d.class_name}) - {', '.join(d.functions) or 'N/A'}")
    
    # Visualization
    print("\n⚙️ Creating visualization...")
    
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    
    colors = {
        NodeType.INSTRUMENT: 'lime',
        NodeType.VALVE: 'blue',
        NodeType.PUMP: 'orange',
        NodeType.EQUIPMENT: 'yellow',
        NodeType.LINE: 'cyan',
        NodeType.UNKNOWN: 'red',
    }
    
    for det in detections:
        node_type = CLASS_TYPE_MAP.get(det.class_name, NodeType.UNKNOWN)
        color = colors[node_type]
        
        rect = patches.Rectangle(
            (det.bbox.x1, det.bbox.y1), det.bbox.width, det.bbox.height,
            linewidth=2, edgecolor=color, facecolor='none'
        )
        ax.add_patch(rect)
        
        label = det.tag or det.class_name.split('.')[-1][:6]
        ax.text(det.bbox.x1, det.bbox.y1 - 5, label,
               fontsize=7, color='white', backgroundcolor=color,
               fontweight='bold')
    
    ax.set_title(f"EDAI4 Improved Detection: {len(detections)} symbols, {tagged} tagged", fontsize=14)
    ax.axis('off')
    
    # Legend
    legend_elements = [patches.Patch(facecolor=c, label=t.value) for t, c in colors.items()]
    ax.legend(handles=legend_elements, loc='upper right')
    
    plt.tight_layout()
    plt.savefig('/kaggle/working/improved_detection.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total detections: {len(detections)}")
    print(f"Tagged instruments: {tagged}")
    print(f"Detection types:")
    for node_type in NodeType:
        count = sum(1 for d in detections if CLASS_TYPE_MAP.get(d.class_name, NodeType.UNKNOWN) == node_type)
        if count > 0:
            print(f"   {node_type.value}: {count}")
    
    print(f"\nOutput saved: /kaggle/working/improved_detection.png")
    
else:
    print("⚠ No test image found!")

print("\n✅ Done!")
