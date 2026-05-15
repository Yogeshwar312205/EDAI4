# Model Retraining Guide - Detect Missing Equipment

## 🎯 Goal
Add missing equipment classes to your YOLO model so it can detect:
- Storage tanks
- Vessels
- Heat exchangers
- Compressors
- Motors
- Filters
- Separators

## 📋 Current Status

### ✅ What's Working (After Quick Fix)
- Valves: 10 detected
- Instruments: 79 detected (circle detection)
- Pumps: 1 detected
- **Total: 89 detections (+345% improvement!)**

### ❌ What's Still Missing
- Storage tanks: 0 detected
- Vessels: 0 detected
- Heat exchangers: 0 detected
- Compressors: 0 detected
- Motors: 0 detected

**Reason:** These classes don't exist in your model.

## 🔧 Retraining Process

### Step 1: Collect Training Data (10-20 hours)

**Target:** 200-500 images with missing equipment

**Sources:**
1. **Public datasets:**
   - Roboflow Universe: https://universe.roboflow.com/
   - Search for "P&ID", "piping", "instrumentation"
   - Download datasets with equipment

2. **Create your own:**
   - Scan engineering drawings
   - Screenshot from CAD software
   - Request from engineering firms
   - Use your existing P&ID library

3. **Data augmentation:**
   - Rotate images (±5°)
   - Scale (0.8-1.2x)
   - Adjust brightness/contrast
   - Add noise

**Minimum requirements:**
- 50 images with storage tanks
- 50 images with vessels
- 50 images with heat exchangers
- 50 images with compressors
- 50 images with motors

### Step 2: Annotate Images (20-40 hours)

**Tool options:**

1. **LabelImg** (Recommended for beginners)
   ```bash
   pip install labelImg
   labelImg
   ```
   - Simple interface
   - YOLO format export
   - Free and open source

2. **CVAT** (Advanced)
   - Web-based
   - Team collaboration
   - Auto-annotation features
   - https://www.cvat.ai/

3. **Roboflow** (Cloud-based)
   - Automatic preprocessing
   - Version control
   - Export to YOLO format
   - https://roboflow.com/

**Annotation guidelines:**

```yaml
# New classes to add:
16: equipment.tank
17: equipment.vessel
18: equipment.heat_exchanger
19: equipment.motor
20: equipment.filter
21: equipment.separator
22: equipment.reactor
23: equipment.column
24: instrument.transmitter
25: instrument.controller
26: instrument.indicator
27: instrument.switch
```

**Tips:**
- Draw tight bounding boxes
- Include all visible equipment
- Be consistent with class names
- Annotate partially visible objects
- Include different scales and orientations

### Step 3: Prepare Dataset (2 hours)

**Directory structure:**
```
pid_dataset/
├── images/
│   ├── train/
│   │   ├── image001.jpg
│   │   ├── image002.jpg
│   │   └── ...
│   ├── val/
│   │   ├── image101.jpg
│   │   └── ...
│   └── test/
│       ├── image201.jpg
│       └── ...
└── labels/
    ├── train/
    │   ├── image001.txt
    │   ├── image002.txt
    │   └── ...
    ├── val/
    │   ├── image101.txt
    │   └── ...
    └── test/
        ├── image201.txt
        └── ...
```

**Split ratios:**
- Training: 70% (350 images)
- Validation: 20% (100 images)
- Test: 10% (50 images)

**Create dataset.yaml:**
```yaml
# pid_dataset.yaml
path: ./pid_dataset
train: images/train
val: images/val
test: images/test

# Classes (16 existing + 12 new = 28 total)
names:
  0: valve.ball
  1: valve.gate
  2: valve.globe
  3: valve.butterfly
  4: valve.check
  5: valve.plug
  6: valve.control
  7: valve.safety_relief
  8: valve.general
  9: equipment.pump
  10: equipment.compressor_blower
  11: fitting.blind
  12: fitting.reducer
  13: instrument.bubble
  14: instrument.inline
  15: line.flow_arrow
  # New classes:
  16: equipment.tank
  17: equipment.vessel
  18: equipment.heat_exchanger
  19: equipment.motor
  20: equipment.filter
  21: equipment.separator
  22: equipment.reactor
  23: equipment.column
  24: instrument.transmitter
  25: instrument.controller
  26: instrument.indicator
  27: instrument.switch
```

### Step 4: Train Model (4-8 hours GPU time)

**Training script:**
```python
# train_improved_model.py
from ultralytics import YOLO

# Load your existing model (transfer learning)
model = YOLO('models/yolov8/best.pt')

# Train with new data
results = model.train(
    data='pid_dataset.yaml',
    epochs=100,              # More epochs for better learning
    imgsz=1280,              # Larger images for detail
    batch=16,                # Adjust based on GPU memory
    patience=20,             # Early stopping
    save=True,
    project='runs/train',
    name='pid_v2',
    
    # Augmentation
    augment=True,
    hsv_h=0.015,            # Hue augmentation
    hsv_s=0.7,              # Saturation
    hsv_v=0.4,              # Value
    degrees=5.0,            # Rotation
    translate=0.1,          # Translation
    scale=0.2,              # Scaling
    flipud=0.0,             # No vertical flip (P&IDs have orientation)
    fliplr=0.5,             # Horizontal flip OK
    mosaic=1.0,             # Mosaic augmentation
    mixup=0.1,              # Mixup augmentation
    
    # Optimization
    optimizer='AdamW',
    lr0=0.001,              # Initial learning rate
    lrf=0.01,               # Final learning rate
    momentum=0.937,
    weight_decay=0.0005,
    warmup_epochs=3,
    
    # Hardware
    device=0,               # GPU 0 (or 'cpu' for CPU)
    workers=8,              # Data loading workers
    
    # Validation
    val=True,
    plots=True,
    save_period=10,         # Save checkpoint every 10 epochs
)

# Evaluate on test set
metrics = model.val(data='pid_dataset.yaml', split='test')

print("\n" + "="*70)
print("Training Complete!")
print("="*70)
print(f"Best model saved to: {results.save_dir}/weights/best.pt")
print(f"\nMetrics:")
print(f"  mAP@0.5: {metrics.box.map50:.3f}")
print(f"  mAP@0.5:0.95: {metrics.box.map:.3f}")
print(f"  Precision: {metrics.box.mp:.3f}")
print(f"  Recall: {metrics.box.mr:.3f}")
```

**Run training:**
```bash
python train_improved_model.py
```

**Expected training time:**
- RTX 3070: 4-6 hours
- RTX 3090: 2-3 hours
- RTX 4090: 1-2 hours
- CPU: 40-80 hours (not recommended)

**Monitor training:**
```bash
# View training progress
tensorboard --logdir runs/train/pid_v2
```

### Step 5: Evaluate Results (1 hour)

**Validation script:**
```python
# validate_model.py
from ultralytics import YOLO
import cv2
import json

# Load new model
model = YOLO('runs/train/pid_v2/weights/best.pt')

# Test on your P&ID
image_path = 'test_images/Screenshot 2026-04-23 112939.png'
image = cv2.imread(image_path)

# Run detection
results = model.predict(
    image,
    conf=0.2,
    iou=0.45,
    imgsz=1280,
    augment=True,
    verbose=True
)

# Count detections by class
detections = {}
for result in results:
    boxes = result.boxes
    if boxes is None:
        continue
    
    for i in range(len(boxes)):
        cls_id = int(boxes.cls[i].cpu().numpy())
        class_name = model.names[cls_id]
        detections[class_name] = detections.get(class_name, 0) + 1

print("\n" + "="*70)
print("Detection Results")
print("="*70)
for class_name, count in sorted(detections.items()):
    print(f"  {class_name:30s}: {count:3d}")

print(f"\nTotal detections: {sum(detections.values())}")

# Check for missing equipment
expected_equipment = [
    'equipment.tank',
    'equipment.vessel',
    'equipment.heat_exchanger',
    'equipment.compressor_blower',
    'equipment.motor'
]

print("\n" + "="*70)
print("Expected Equipment Check")
print("="*70)
for equip in expected_equipment:
    status = "✓" if equip in detections else "✗"
    count = detections.get(equip, 0)
    print(f"  {status} {equip:30s}: {count}")
```

**Expected improvements:**
- Equipment detection: 14% → 85%
- Total detections: 89 → 120+
- New classes detected: tanks, vessels, heat exchangers, motors

### Step 6: Deploy New Model (10 minutes)

**Replace old model:**
```bash
# Backup old model
cp models/yolov8/best.pt models/yolov8/best_old.pt

# Copy new model
cp runs/train/pid_v2/weights/best.pt models/yolov8/best.pt
```

**Update quick_fix_detection.py:**
```python
# No changes needed - it will automatically use the new model
python quick_fix_detection.py
```

## 📊 Expected Results After Retraining

### Before Retraining (Current):
```
Valves: 10
Instruments: 79 (circle detection)
Equipment: 1 (pump only)
Total: 89
Missing: tanks, vessels, heat exchangers, motors
```

### After Retraining (Target):
```
Valves: 15
Instruments: 85 (YOLO + circle detection)
Equipment: 7 (pump, tank, vessel, heat exchanger, compressor, motor, filter)
Total: 120+
Missing: None (all major equipment detected)
```

### Metrics Comparison:

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Equipment Detection | 14% | 85% | 85% |
| Valve Detection | 87% | 95% | 90% |
| Instrument Detection | 89% | 95% | 90% |
| mAP@0.5 | 0.60 | 0.82 | 0.85 |
| Average Confidence | 0.82 | 0.85 | 0.85 |

## 💰 Cost Estimate

### Time Investment:
- Data collection: 10-20 hours
- Annotation: 20-40 hours
- Training: 4-8 hours (GPU time)
- Evaluation: 2-4 hours
- **Total: 36-72 hours**

### Financial Cost:
- **Free option:**
  - Use your own GPU
  - Free annotation tools (LabelImg)
  - Free datasets (Roboflow Universe)
  - **Cost: $0**

- **Cloud GPU option:**
  - Google Colab Pro: $10/month
  - AWS EC2 g4dn.xlarge: $0.50/hour × 8 hours = $4
  - Paperspace: $0.45/hour × 8 hours = $3.60
  - **Cost: $10-20**

- **Annotation service option:**
  - Professional annotation: $0.10-0.50 per image
  - 500 images × $0.20 = $100
  - **Cost: $100-250**

## 🚀 Quick Start Commands

```bash
# 1. Install annotation tool
pip install labelImg

# 2. Start annotating
labelImg

# 3. Train model (after annotation)
python train_improved_model.py

# 4. Validate results
python validate_model.py

# 5. Deploy new model
cp runs/train/pid_v2/weights/best.pt models/yolov8/best.pt

# 6. Test with quick fix script
python quick_fix_detection.py
```

## 📚 Resources

### Tutorials:
- YOLOv8 Training: https://docs.ultralytics.com/modes/train/
- Custom Dataset: https://docs.ultralytics.com/datasets/
- Transfer Learning: https://docs.ultralytics.com/guides/transfer-learning/

### Datasets:
- Roboflow Universe: https://universe.roboflow.com/
- Kaggle P&ID: https://www.kaggle.com/search?q=P%26ID
- Academic datasets: Search Google Scholar

### Tools:
- LabelImg: https://github.com/heartexlabs/labelImg
- CVAT: https://www.cvat.ai/
- Roboflow: https://roboflow.com/

## ❓ FAQ

**Q: Can I skip retraining?**
A: No. Your model can't detect classes it wasn't trained on. It's like asking someone who only learned English to read Chinese.

**Q: How many images do I need?**
A: Minimum 50 per new class, ideally 200-500 for good performance.

**Q: Can I use pretrained models?**
A: Generic YOLO models don't know P&ID symbols. You need domain-specific training.

**Q: How long does training take?**
A: 2-8 hours on a good GPU (RTX 3070+), 40-80 hours on CPU.

**Q: Will I lose my current detections?**
A: No. Transfer learning keeps existing knowledge and adds new classes.

**Q: What if I don't have a GPU?**
A: Use Google Colab (free GPU) or cloud services ($3-10 for training).

## ✅ Success Criteria

You'll know retraining was successful when:
- ✅ Storage tank detected with >0.7 confidence
- ✅ Vessel V-102 detected with >0.7 confidence
- ✅ Heat exchanger detected with >0.7 confidence
- ✅ Compressor detected with >0.7 confidence
- ✅ Motor detected with >0.7 confidence
- ✅ mAP@0.5 > 0.80
- ✅ Total equipment detection > 85%

## 🎯 Next Steps

1. **Today:** Start collecting P&ID images
2. **This week:** Annotate 100-200 images
3. **Next week:** Train model
4. **Week 3:** Evaluate and iterate
5. **Week 4:** Deploy and celebrate! 🎉

---

**Ready to start? Begin with data collection!**
