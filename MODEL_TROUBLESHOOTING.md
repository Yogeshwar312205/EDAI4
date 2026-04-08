# 🔧 EDAI4 - Model Detection Issues & Solutions

## Problem Summary

You're experiencing two issues:

### Issue 1: Web UI Shows "Demo Mode" (1 detection, FT-101)
**Cause**: The YOLO model file (`best.pt`) is not found on your local machine.

**Solution**:
1. Download the model from Kaggle
2. Place it in `D:\EDAI4\models\best.pt`
3. OR set environment variable: `YOLO_MODEL_PATH=path/to/best.pt`

### Issue 2: Model Detects Valves But Misses Instrument Bubbles
**Cause**: The model was trained on **isolated symbol cutouts**, not full P&ID drawings. This is called "domain shift" - the model learned to recognize symbols in isolation but struggles when they're surrounded by lines, text, and other symbols.

---

## Quick Fixes (Apply Now)

### Fix 1: Lower Confidence Threshold

Change from `conf=0.4` to `conf=0.25`:

```python
# OLD (misses many symbols)
results = model(image, conf=0.4, verbose=False)

# NEW (detects more symbols)
results = model(image, conf=0.25, verbose=False, imgsz=1280)
```

### Fix 2: Use Higher Resolution

```python
# Use 1280 or higher for full P&ID sheets
results = model(image, conf=0.25, imgsz=1280, verbose=False)
```

### Fix 3: Image Preprocessing

```python
import cv2

# Enhance contrast before detection
lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
l, a, b = cv2.split(lab)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
l = clahe.apply(l)
enhanced = cv2.merge([l, a, b])
enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

results = model(enhanced, conf=0.25, imgsz=1280)
```

---

## Long-Term Solution: Retrain the Model

The model needs to be fine-tuned on **full P&ID drawings** (not isolated symbols).

### Option A: Fine-tune with 20-50 labeled P&IDs

1. **Collect 20-50 full P&ID drawings**
2. **Label them** using Roboflow, CVAT, or Label Studio
3. **Fine-tune** from the current model:

```python
from ultralytics import YOLO

# Load current model
model = YOLO("/path/to/best.pt")

# Fine-tune on new data
model.train(
    data="path/to/new_dataset/data.yaml",
    epochs=30,
    imgsz=1280,
    batch=8,
    lr0=0.001,  # Lower learning rate for fine-tuning
    freeze=10,  # Freeze first 10 layers
)
```

### Option B: Use Test-Time Augmentation (TTA)

```python
# Enable TTA for better detection (slower but more accurate)
results = model(image, conf=0.25, augment=True)
```

### Option C: Multi-Scale Detection

For large P&IDs, detect on tiles and combine:

```python
def tiled_detection(image, model, tile_size=800, overlap=200, conf=0.25):
    """Detect on tiles for large images."""
    h, w = image.shape[:2]
    all_boxes = []
    
    for y in range(0, h - overlap, tile_size - overlap):
        for x in range(0, w - overlap, tile_size - overlap):
            tile = image[y:y+tile_size, x:x+tile_size]
            results = model(tile, conf=conf, verbose=False)
            
            for r in results:
                for box in r.boxes:
                    # Adjust coordinates to full image
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    all_boxes.append({
                        'bbox': (x1+x, y1+y, x2+x, y2+y),
                        'class': model.names[int(box.cls[0])],
                        'conf': float(box.conf[0]),
                    })
    
    # Apply NMS to remove duplicates
    return non_max_suppression(all_boxes)
```

---

## For Local Web UI

To run the Web UI locally with the model:

### Step 1: Download the model
```bash
# From Kaggle, download best.pt from yogeshwarvshinde/edai4-golden-model
# Place it in D:\EDAI4\models\best.pt
```

### Step 2: Create models folder
```bash
mkdir D:\EDAI4\models
# Copy best.pt to this folder
```

### Step 3: Run the API
```bash
cd D:\EDAI4
set YOLO_MODEL_PATH=D:\EDAI4\models\best.pt
python -m src.api.main
```

### Step 4: Open browser
Navigate to `http://localhost:8000`

---

## Diagnostic Script

Run `KAGGLE_MODEL_DIAGNOSTIC.py` in Kaggle to:
1. Compare original vs improved detection
2. See class distribution
3. Get specific recommendations

---

## Why This Happens

| Training Data | Real P&ID |
|---------------|-----------|
| Single symbols on white background | Symbols surrounded by lines, text |
| High contrast | Variable contrast |
| Standard sizes | Various scales |
| Clean images | Noise, annotations |

The model learned "symbol in isolation" not "symbol in context". This is fixable with:
1. Data augmentation during training (background noise, lines)
2. Fine-tuning on real P&ID images
3. Adjusting confidence thresholds

---

## Contact

If the quick fixes don't work, the best solution is to:
1. Label 20-50 real P&ID images
2. Fine-tune the model for 30 epochs
3. This typically improves accuracy from ~30% to ~80% on full P&IDs
