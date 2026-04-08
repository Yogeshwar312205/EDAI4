# ============================================================================
# EDAI4 - MODEL DIAGNOSTIC AND FIX SCRIPT
# ============================================================================
# This script diagnoses why the model isn't working well on full P&IDs
# and provides fixes.
#
# PROBLEM: Model trained on isolated symbol cutouts, not full P&ID sheets
# SOLUTION: Lower confidence, use multi-scale detection, improve preprocessing
# ============================================================================

print("=" * 70)
print("EDAI4 MODEL DIAGNOSTIC & IMPROVED DETECTION")
print("=" * 70)

# Install dependencies
import subprocess
subprocess.run(["pip", "install", "-q", "ultralytics", "easyocr", "opencv-python-headless"])

import os
import glob
import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from collections import Counter

# ============================================================================
# 1. FIND THE MODEL
# ============================================================================
print("\n[1/5] Locating model...")

MODEL_PATHS = [
    "/kaggle/input/edai4-golden-model/best.pt",
    "/kaggle/input/datasets/yogeshwarvshinde/edai4-golden-model/best.pt",
    # Add local paths if needed
    "D:/EDAI4/models/best.pt",
    "./best.pt",
]

YOLO_MODEL_PATH = None
for p in MODEL_PATHS:
    if os.path.exists(p):
        YOLO_MODEL_PATH = p
        print(f"   ✓ Found: {p}")
        break

if not YOLO_MODEL_PATH:
    print("   ✗ Model not found!")
    print("   Please ensure 'yogeshwarvshinde/edai4-golden-model' is attached")
    raise FileNotFoundError("Model not found")

# ============================================================================
# 2. FIND TEST IMAGE
# ============================================================================
print("\n[2/5] Finding test image...")

IMAGE_PATHS = glob.glob("/kaggle/input/**/*.png", recursive=True) + \
              glob.glob("/kaggle/input/**/*.jpg", recursive=True) + \
              glob.glob("/kaggle/working/**/*.png", recursive=True)

# Filter for likely P&ID images (larger files)
pid_images = []
for img_path in IMAGE_PATHS:
    try:
        size = os.path.getsize(img_path)
        if size > 50000:  # > 50KB likely a full P&ID
            pid_images.append((img_path, size))
    except:
        pass

if pid_images:
    # Sort by size descending (larger = more likely full P&ID)
    pid_images.sort(key=lambda x: -x[1])
    TEST_IMAGE = pid_images[0][0]
    print(f"   ✓ Selected: {os.path.basename(TEST_IMAGE)} ({pid_images[0][1]//1024}KB)")
else:
    print("   ✗ No suitable test images found")
    TEST_IMAGE = None

# ============================================================================
# 3. LOAD MODEL AND ANALYZE
# ============================================================================
print("\n[3/5] Loading and analyzing model...")

from ultralytics import YOLO
model = YOLO(YOLO_MODEL_PATH)

print(f"   Model classes ({len(model.names)}):")
for idx, name in model.names.items():
    print(f"      {idx}: {name}")

# ============================================================================
# 4. IMPROVED DETECTION FUNCTION
# ============================================================================

def detect_with_improvements(image_path, model, conf_threshold=0.25):
    """
    Improved detection with:
    1. Lower confidence threshold (0.25 instead of 0.4)
    2. Multi-scale detection (sliding window for large images)
    3. Image preprocessing
    """
    
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        print(f"   ✗ Could not load image: {image_path}")
        return None, []
    
    h, w = img.shape[:2]
    print(f"   Image size: {w}x{h}")
    
    # Preprocessing: enhance contrast
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    enhanced = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    
    all_detections = []
    
    # Method 1: Full image detection at multiple confidence levels
    print(f"   Running detection at conf={conf_threshold}...")
    
    # Use the enhanced image
    results = model(enhanced, conf=conf_threshold, verbose=False, imgsz=1280)
    
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            
            all_detections.append({
                'bbox': (float(x1), float(y1), float(x2), float(y2)),
                'class': model.names[cls_id],
                'confidence': conf,
            })
    
    # Method 2: If image is large, also try tiled detection
    if w > 1500 or h > 1500:
        print("   Large image - running tiled detection...")
        
        tile_size = 800
        overlap = 200
        
        for y_start in range(0, h - overlap, tile_size - overlap):
            for x_start in range(0, w - overlap, tile_size - overlap):
                x_end = min(x_start + tile_size, w)
                y_end = min(y_start + tile_size, h)
                
                tile = enhanced[y_start:y_end, x_start:x_end]
                
                tile_results = model(tile, conf=conf_threshold, verbose=False)
                
                for r in tile_results:
                    for box in r.boxes:
                        tx1, ty1, tx2, ty2 = box.xyxy[0].cpu().numpy()
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        
                        # Adjust coordinates to full image
                        all_detections.append({
                            'bbox': (
                                float(tx1 + x_start),
                                float(ty1 + y_start),
                                float(tx2 + x_start),
                                float(ty2 + y_start)
                            ),
                            'class': model.names[cls_id],
                            'confidence': conf,
                        })
    
    # Remove duplicates (NMS)
    all_detections = non_max_suppression(all_detections, iou_threshold=0.5)
    
    return img, all_detections


def non_max_suppression(detections, iou_threshold=0.5):
    """Simple NMS to remove duplicate detections."""
    if not detections:
        return []
    
    # Sort by confidence
    detections = sorted(detections, key=lambda x: -x['confidence'])
    
    keep = []
    for det in detections:
        is_duplicate = False
        for kept in keep:
            if det['class'] == kept['class']:
                iou = compute_iou(det['bbox'], kept['bbox'])
                if iou > iou_threshold:
                    is_duplicate = True
                    break
        if not is_duplicate:
            keep.append(det)
    
    return keep


def compute_iou(box1, box2):
    """Compute IoU between two boxes."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    if x2 < x1 or y2 < y1:
        return 0.0
    
    intersection = (x2 - x1) * (y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    
    return intersection / (area1 + area2 - intersection + 1e-6)


# ============================================================================
# 5. RUN IMPROVED DETECTION
# ============================================================================

if TEST_IMAGE:
    print("\n[4/5] Running improved detection...")
    
    # Compare original vs improved
    print("\n--- ORIGINAL (conf=0.4) ---")
    img_orig = cv2.imread(TEST_IMAGE)
    results_orig = model(img_orig, conf=0.4, verbose=False)
    orig_count = sum(len(r.boxes) for r in results_orig)
    print(f"   Detections: {orig_count}")
    
    print("\n--- IMPROVED (conf=0.25 + preprocessing + tiling) ---")
    img, improved_dets = detect_with_improvements(TEST_IMAGE, model, conf_threshold=0.25)
    print(f"   Detections: {len(improved_dets)}")
    
    # Class distribution
    class_counts = Counter(d['class'] for d in improved_dets)
    print("\n   Detection breakdown:")
    for cls, count in class_counts.most_common():
        print(f"      {cls}: {count}")
    
    # ============================================================================
    # 6. VISUALIZATION
    # ============================================================================
    print("\n[5/5] Creating visualization...")
    
    fig, axes = plt.subplots(1, 2, figsize=(20, 10))
    
    # Original detection
    axes[0].imshow(cv2.cvtColor(img_orig, cv2.COLOR_BGR2RGB))
    axes[0].set_title(f"Original Detection (conf=0.4)\n{orig_count} detections", fontsize=14)
    for r in results_orig:
        for box in r.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            rect = patches.Rectangle((x1, y1), x2-x1, y2-y1,
                                     linewidth=2, edgecolor='red', facecolor='none')
            axes[0].add_patch(rect)
    axes[0].axis('off')
    
    # Improved detection
    axes[1].imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    axes[1].set_title(f"Improved Detection (conf=0.25 + preprocessing)\n{len(improved_dets)} detections", fontsize=14)
    
    colors = {
        'instrument.bubble': 'lime',
        'instrument.inline': 'green',
        'valve.control': 'blue',
        'valve.general': 'cyan',
        'equipment.pump': 'orange',
        'equipment.compressor_blower': 'yellow',
    }
    
    for det in improved_dets:
        x1, y1, x2, y2 = det['bbox']
        color = colors.get(det['class'], 'red')
        rect = patches.Rectangle((x1, y1), x2-x1, y2-y1,
                                 linewidth=2, edgecolor=color, facecolor='none')
        axes[1].add_patch(rect)
        axes[1].text(x1, y1-5, f"{det['class'].split('.')[-1][:4]}",
                    fontsize=6, color='white', backgroundcolor=color)
    axes[1].axis('off')
    
    plt.tight_layout()
    plt.savefig('/kaggle/working/detection_comparison.png', dpi=150)
    plt.show()
    
    # ============================================================================
    # SUMMARY & RECOMMENDATIONS
    # ============================================================================
    print("\n" + "=" * 70)
    print("DIAGNOSIS COMPLETE")
    print("=" * 70)
    
    improvement = len(improved_dets) - orig_count
    print(f"\nImprovement: {orig_count} → {len(improved_dets)} detections (+{improvement})")
    
    print("\n📋 RECOMMENDATIONS:")
    print("-" * 50)
    
    if len(improved_dets) < 20:
        print("""
⚠️  LOW DETECTION COUNT - The model needs retraining!

The model was trained on ISOLATED SYMBOL CUTOUTS, not full P&ID sheets.
To fix this properly, you need to:

1. RETRAIN with full P&ID images:
   - Annotate 20-50 full P&ID drawings
   - Use tools like Roboflow, CVAT, or Label Studio
   - Fine-tune from the current model (transfer learning)

2. USE a different dataset:
   - Search for "P&ID object detection dataset" on Roboflow
   - Look for datasets with full drawings, not cutouts

3. QUICK FIX (may help):
   - Lower confidence to 0.15-0.20
   - Use higher resolution (imgsz=1920)
   - Try test-time augmentation (TTA)
""")
    else:
        print("""
✅ DETECTION IMPROVED!

The lower confidence threshold helped find more symbols.
To further improve:

1. Fine-tune OCR association radius
2. Add more ISA tag patterns
3. Consider training on full P&ID sheets for best results
""")
    
    print("\n💡 QUICK FIX FOR YOUR SCRIPTS:")
    print("-" * 50)
    print("""
Change confidence from 0.4 to 0.25:

# OLD:
results = model(image, conf=0.4, verbose=False)

# NEW:
results = model(image, conf=0.25, verbose=False, imgsz=1280)
""")

else:
    print("\n⚠️  No test image found. Upload a P&ID image to /kaggle/working/")
