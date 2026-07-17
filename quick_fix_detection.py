"""
Quick Fix for P&ID Detection
Implements Phase 1 improvements for immediate results
"""

import cv2
import numpy as np
from ultralytics import YOLO
import json
import re
from pathlib import Path

# ============================================================================
# Configuration
# ============================================================================

MODEL_PATH = "models/yolov8/best.pt"
IMAGE_PATH = "D:\EDAI4\test_images\Screenshot 2026-04-23 112939.png"  # Update this
OUTPUT_DIR = "detection_results"

# Improved settings
CONFIDENCE_THRESHOLD = 0.2  # Lowered from 0.5
IOU_THRESHOLD = 0.45
IMAGE_SIZE = 1280  # Increased from 640
USE_TTA = True  # Test Time Augmentation

# ============================================================================
# ISA Tag Validation
# ============================================================================

ISA_TAG_PATTERNS = [
    r'^[A-Z]{1,4}[-_]?\d{1,4}[A-Z]?$',  # Standard: FIC-101, TT-201A
    r'^\d{2,3}[-_][A-Z0-9]+$',           # Numeric prefix: 00-8, 12-ABC
    r'^[A-Z]{2,4}[-_]\d{2,3}[-_][A-Z]$', # Extended: LSHH-101-A
]

def validate_isa_tag(text):
    """Check if text matches ISA tag format"""
    if not text:
        return False
    
    text = text.strip().upper()
    
    for pattern in ISA_TAG_PATTERNS:
        if re.match(pattern, text):
            return True
    
    return False

def clean_ocr_text(text):
    """Clean common OCR errors"""
    if not text:
        return ""
    
    text = text.strip().upper()
    
    # Common OCR substitutions
    replacements = {
        'O': '0',  # In numeric contexts
        'l': '1',
        'I': '1',
        '|': '1',
        'S': '5',  # Sometimes
        'Z': '2',  # Sometimes
    }
    
    # Apply smart replacements (only in numeric parts)
    parts = re.split(r'([-_])', text)
    cleaned_parts = []
    
    for part in parts:
        if part in ['-', '_']:
            cleaned_parts.append(part)
        elif part.isdigit() or any(c.isdigit() for c in part):
            # Numeric part - apply replacements
            for old, new in replacements.items():
                part = part.replace(old, new)
            cleaned_parts.append(part)
        else:
            # Alpha part - keep as is
            cleaned_parts.append(part)
    
    cleaned = ''.join(cleaned_parts)
    
    # Remove invalid characters
    cleaned = re.sub(r'[^A-Z0-9-_]', '', cleaned)
    
    return cleaned

# ============================================================================
# Circle Detection for Instruments
# ============================================================================

def detect_instrument_circles(image):
    """
    Detect circular instrument bubbles using Hough Transform
    Returns list of (x, y, radius) tuples
    """
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Preprocessing
    gray = cv2.medianBlur(gray, 5)
    gray = cv2.equalizeHist(gray)
    
    # Detect circles
    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=30,
        param1=50,
        param2=30,
        minRadius=15,
        maxRadius=60
    )
    
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        return [(x, y, r) for x, y, r in circles]
    
    return []

# ============================================================================
# Enhanced YOLO Detection
# ============================================================================

def enhanced_yolo_detection(image_path, model_path):
    """
    Run YOLO detection with improved settings
    """
    print("=" * 70)
    print("Enhanced P&ID Detection")
    print("=" * 70)
    
    # Load model
    print(f"\n1. Loading model: {model_path}")
    model = YOLO(model_path)
    print(f"   ✓ Model loaded ({len(model.names)} classes)")
    
    # Load image
    print(f"\n2. Loading image: {image_path}")
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    h, w = image.shape[:2]
    print(f"   ✓ Image loaded ({w}x{h})")
    
    # Run YOLO detection
    print(f"\n3. Running YOLO detection...")
    print(f"   - Confidence threshold: {CONFIDENCE_THRESHOLD}")
    print(f"   - IOU threshold: {IOU_THRESHOLD}")
    print(f"   - Image size: {IMAGE_SIZE}")
    print(f"   - Test Time Augmentation: {USE_TTA}")
    
    results = model.predict(
        image,
        conf=CONFIDENCE_THRESHOLD,
        iou=IOU_THRESHOLD,
        imgsz=IMAGE_SIZE,
        augment=USE_TTA,
        verbose=False
    )
    
    # Extract detections
    detections = []
    for result in results:
        boxes = result.boxes
        if boxes is None:
            continue
        
        for i in range(len(boxes)):
            xyxy = boxes.xyxy[i].cpu().numpy()
            conf = float(boxes.conf[i].cpu().numpy())
            cls_id = int(boxes.cls[i].cpu().numpy())
            class_name = model.names[cls_id]
            
            detection = {
                'class_name': class_name,
                'confidence': conf,
                'bbox': {
                    'x1': float(xyxy[0]),
                    'y1': float(xyxy[1]),
                    'x2': float(xyxy[2]),
                    'y2': float(xyxy[3])
                }
            }
            detections.append(detection)
    
    print(f"   ✓ YOLO detected {len(detections)} objects")
    
    # Detect circles for instruments
    print(f"\n4. Detecting instrument circles...")
    circles = detect_instrument_circles(image)
    print(f"   ✓ Found {len(circles)} circular objects")
    
    # Add circles as instrument detections
    for x, y, r in circles:
        # Check if circle overlaps with existing detection
        overlaps = False
        for det in detections:
            bbox = det['bbox']
            cx = (bbox['x1'] + bbox['x2']) / 2
            cy = (bbox['y1'] + bbox['y2']) / 2
            dist = np.sqrt((cx - x)**2 + (cy - y)**2)
            if dist < r * 1.5:
                overlaps = True
                break
        
        if not overlaps:
            detection = {
                'class_name': 'instrument.bubble',
                'confidence': 0.85,  # High confidence for circle detection
                'bbox': {
                    'x1': float(x - r),
                    'y1': float(y - r),
                    'x2': float(x + r),
                    'y2': float(y + r)
                },
                'source': 'circle_detection'
            }
            detections.append(detection)
    
    print(f"   ✓ Total detections: {len(detections)}")
    
    return detections, image

# ============================================================================
# Detection Filtering
# ============================================================================

def filter_detections(detections, min_confidence=0.2, min_area=100):
    """
    Filter out low-quality detections
    """
    filtered = []
    
    for det in detections:
        # Skip low confidence
        if det['confidence'] < min_confidence:
            continue
        
        # Calculate area
        bbox = det['bbox']
        width = bbox['x2'] - bbox['x1']
        height = bbox['y2'] - bbox['y1']
        area = width * height
        
        # Skip tiny boxes
        if area < min_area:
            continue
        
        # Skip extreme aspect ratios
        aspect_ratio = width / height if height > 0 else 0
        if aspect_ratio > 10 or aspect_ratio < 0.1:
            continue
        
        filtered.append(det)
    
    return filtered

# ============================================================================
# Visualization
# ============================================================================

def visualize_detections(image, detections, output_path):
    """
    Draw detections on image
    """
    output = image.copy()
    
    # Color map for different classes
    colors = {
        'valve': (0, 255, 0),      # Green
        'equipment': (255, 0, 0),   # Blue
        'instrument': (0, 0, 255),  # Red
        'fitting': (255, 255, 0),   # Cyan
        'line': (255, 0, 255),      # Magenta
    }
    
    for det in detections:
        bbox = det['bbox']
        x1, y1 = int(bbox['x1']), int(bbox['y1'])
        x2, y2 = int(bbox['x2']), int(bbox['y2'])
        
        # Determine color based on class
        class_name = det['class_name']
        color = (128, 128, 128)  # Default gray
        for key, col in colors.items():
            if key in class_name:
                color = col
                break
        
        # Draw box
        cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
        
        # Draw label
        label = f"{class_name} {det['confidence']:.2f}"
        (label_w, label_h), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
        )
        
        cv2.rectangle(
            output,
            (x1, y1 - label_h - 10),
            (x1 + label_w, y1),
            color,
            -1
        )
        cv2.putText(
            output,
            label,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )
    
    # Save
    cv2.imwrite(str(output_path), output)
    print(f"\n✓ Visualization saved: {output_path}")
    
    return output

# ============================================================================
# Statistics
# ============================================================================

def print_statistics(detections):
    """
    Print detection statistics
    """
    print("\n" + "=" * 70)
    print("Detection Statistics")
    print("=" * 70)
    
    # Count by class
    class_counts = {}
    for det in detections:
        class_name = det['class_name']
        class_counts[class_name] = class_counts.get(class_name, 0) + 1
    
    print(f"\nTotal detections: {len(detections)}")
    print(f"\nDetections by class:")
    for class_name, count in sorted(class_counts.items()):
        print(f"  {class_name:30s}: {count:3d}")
    
    # Confidence distribution
    confidences = [det['confidence'] for det in detections]
    print(f"\nConfidence distribution:")
    print(f"  Min:  {min(confidences):.3f}")
    print(f"  Max:  {max(confidences):.3f}")
    print(f"  Mean: {np.mean(confidences):.3f}")
    print(f"  Std:  {np.std(confidences):.3f}")
    
    # Confidence ranges
    ranges = [
        (0.0, 0.3, "Very Low"),
        (0.3, 0.5, "Low"),
        (0.5, 0.7, "Medium"),
        (0.7, 0.9, "High"),
        (0.9, 1.0, "Very High"),
    ]
    
    print(f"\nConfidence ranges:")
    for min_conf, max_conf, label in ranges:
        count = sum(1 for c in confidences if min_conf <= c < max_conf)
        pct = count / len(confidences) * 100 if confidences else 0
        print(f"  {label:12s} ({min_conf:.1f}-{max_conf:.1f}): {count:3d} ({pct:5.1f}%)")

# ============================================================================
# Main
# ============================================================================

def main():
    # Create output directory
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(exist_ok=True)
    
    # Check if image exists
    image_path = Path(IMAGE_PATH)
    if not image_path.exists():
        print(f"❌ Error: Image not found: {image_path}")
        print(f"\nPlease update IMAGE_PATH in the script to point to your image.")
        return
    
    # Run detection
    detections, image = enhanced_yolo_detection(image_path, MODEL_PATH)
    
    # Filter detections
    print(f"\n5. Filtering detections...")
    filtered = filter_detections(detections, min_confidence=0.2, min_area=100)
    print(f"   ✓ Kept {len(filtered)}/{len(detections)} detections")
    
    # Print statistics
    print_statistics(filtered)
    
    # Visualize
    print(f"\n6. Creating visualization...")
    output_path = output_dir / f"{image_path.stem}_enhanced.jpg"
    visualize_detections(image, filtered, output_path)
    
    # Save JSON
    json_path = output_dir / f"{image_path.stem}_enhanced.json"
    with open(json_path, 'w') as f:
        json.dump({
            'image': str(image_path),
            'detections': filtered,
            'total': len(filtered),
            'settings': {
                'confidence_threshold': CONFIDENCE_THRESHOLD,
                'iou_threshold': IOU_THRESHOLD,
                'image_size': IMAGE_SIZE,
                'use_tta': USE_TTA
            }
        }, f, indent=2)
    print(f"✓ JSON saved: {json_path}")
    
    print("\n" + "=" * 70)
    print("✓ Detection complete!")
    print("=" * 70)
    print(f"\nResults saved to: {output_dir}")
    print(f"  - Visualization: {output_path.name}")
    print(f"  - JSON data: {json_path.name}")

if __name__ == "__main__":
    main()
