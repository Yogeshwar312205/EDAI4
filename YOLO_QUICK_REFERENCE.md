# YOLO Training Code - Quick Reference

## 📋 Files Created for You

| File | Purpose | Use |
|------|---------|-----|
| `KAGGLE_QUICK_COPY_PASTE.py` | **Single cell - All-in-one** | ✓ Recommended for beginners |
| `kaggle_yolo_training_complete.py` | **10 separate cells** | For detailed control |
| `KAGGLE_YOLO_INSTRUCTIONS.md` | **Complete guide** | Read this first! |
| `YOLO_KAGGLE_TRAINING.md` | **Quick memory notes** | Reference for settings |

---

## 🚀 Quick Start (Copy & Paste Method)

### Step 1: Open Kaggle Notebook
Go to: https://www.kaggle.com/code/new

### Step 2: Enable GPU
Settings → Accelerator → Select GPU → Save

### Step 3: Add Dataset
Add Input → Search "p-and-id-symbols-for-computer-vision" → Add

### Step 4: Copy Code
Copy ALL code from **`KAGGLE_QUICK_COPY_PASTE.py`**

Paste into ONE cell in Kaggle notebook

### Step 5: Run
Click "Run" or press Shift+Enter

### Step 6: Download
Download from Output → yolov8_pid_training/weights/best.pt

---

## 📊 Code Flow

```
┌─────────────────────────────────────┐
│  1. SETUP & GPU CHECK              │
│  - Initialize logging              │
│  - Check CUDA/GPU status           │
│  - Print system info               │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│  2. INSTALL PACKAGES               │
│  - ultralytics (YOLOv8)            │
│  - roboflow                        │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│  3. LOAD DATASET                   │
│  - Explore directory structure     │
│  - Count images/labels             │
│  - Verify format                   │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│  4. CREATE CONFIGURATION           │
│  - Generate data.yaml              │
│  - Set training parameters         │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│  5. TRAIN MODEL 🚂                 │
│  - Load YOLOv8n                    │
│  - 100 epochs                      │
│  - GPU accelerated training        │
│  [Time: 30-60 minutes]             │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│  6. VALIDATE & EXPORT              │
│  - Run validation                  │
│  - Save best model                 │
│  - Export to different formats     │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│  7. SUMMARY & LOGS                 │
│  - Save training summary           │
│  - Output file locations           │
│  - Ready for download              │
└─────────────────────────────────────┘
```

---

## ⚙️ Key Parameters Explained

```python
training_config = {
    'data': yaml_path,           # Path to data.yaml
    'epochs': 100,               # Number of training cycles (increase for better accuracy)
    'imgsz': 640,                # Image size (640x640 is standard)
    'batch': 16,                 # Images per batch (reduce if GPU memory issue)
    'device': 0,                 # GPU index (0 = first GPU)
    'project': '/kaggle/working',# Output directory
    'name': 'yolov8_pid_training',  # Experiment name
    'optimizer': 'SGD',          # Optimizer type
    'lr0': 0.01,                 # Initial learning rate
    'momentum': 0.937,           # Momentum
    'patience': 20,              # Early stopping patience
}
```

### Adjusting for Your Hardware

**If GPU runs out of memory:**
```python
'batch': 8,  # Reduce from 16 to 8
```

**For faster training (less accurate):**
```python
'epochs': 50,
'batch': 8,
'patience': 10,
```

**For better accuracy (slower):**
```python
'epochs': 200,
'batch': 32,
'patience': 30,
```

---

## 📁 Output File Structure

After training completes, download from `/kaggle/working/`:

```
yolov8_pid_training/
├── weights/
│   ├── best.pt              ← YOUR TRAINED MODEL (DOWNLOAD THIS)
│   ├── last.pt              ← Last checkpoint
│   └── epoch*.pt            ← Intermediate weights
├── runs/
│   ├── detect/
│   └── val/
├── results.csv              ← Training metrics (DOWNLOAD THIS)
├── plots/
│   ├── confusion_matrix.png
│   ├── results.png
│   └── ...
└── events.out.tfevents.*    ← TensorBoard logs

logs/
├── yolo_training_TIMESTAMP.log  ← Detailed logs
├── training_summary.json        ← Summary info
└── dataset_info.json            ← Dataset stats
```

---

## ✅ Verification Checklist

After training:

- [ ] GPU was enabled (check logs)
- [ ] Dataset was found (500+ images)
- [ ] Training started (see "Starting YOLO Training")
- [ ] Epochs completed (100/100)
- [ ] Validation ran successfully
- [ ] Best model saved (weights/best.pt)
- [ ] CSV results file created
- [ ] Logs saved to /logs/
- [ ] All files can be downloaded

---

## 🔧 Using Your Trained Model

### In EDAI4 Project

1. **Download** `best.pt` from Kaggle
2. **Place** in: `d:\EDAI4\models\yolov8\best.pt`
3. **Update config** in `config/settings.yaml`:
   ```yaml
   perception:
     yolo:
       model_path: "./models/yolov8/best.pt"
       confidence_threshold: 0.5
   ```
4. **Run EDAI4**:
   ```bash
   streamlit run app/main.py
   ```

### In Python Code

```python
from ultralytics import YOLO

# Load your trained model
model = YOLO('best.pt')

# Detect P&ID symbols
results = model.predict(source='my_pid.jpg', conf=0.25)

# Process results
for result in results:
    for box in result.boxes:
        print(f"Class: {box.cls}, Confidence: {box.conf}")
```

---

## 📈 Understanding Training Metrics (from results.csv)

```
epoch  box_loss  cls_loss  dfl_loss  metrics/precision  metrics/recall  metrics/mAP50  metrics/mAP50-95
0      0.5234    0.1234    0.2345    0.85              0.75            0.80           0.65
...
99     0.1234    0.0234    0.0456    0.95              0.92            0.94           0.85
```

**What it means:**
- **box_loss**: Detection box accuracy (lower = better)
- **cls_loss**: Classification accuracy (lower = better)
- **precision**: Of detected items, how many were correct (higher = better)
- **recall**: Of all items, how many were detected (higher = better)
- **mAP50**: Mean Average Precision at 50% IoU (higher = better)
- **mAP50-95**: Average across IoU thresholds (most important metric)

---

## 🐛 Common Issues & Solutions

### Issue 1: GPU Not Found
```
CUDA is not available
```
**Fix:**
- Settings → Accelerator → GPU
- Restart notebook

### Issue 2: Out of Memory
```
CUDA out of memory. Tried to allocate X GB
```
**Fix:**
- Change `'batch': 8` (was 16)
- Reduce `'epochs': 50`

### Issue 3: Dataset Not Found
```
FileNotFoundError: /kaggle/input/datasets/mollous/...
```
**Fix:**
- Add input dataset (Step 3)
- Check dataset name is correct

### Issue 4: Training is Very Slow
```
Training is taking longer than expected
```
**Causes & Fixes:**
- Using CPU instead of GPU → Enable GPU in Settings
- Batch size too small → Increase batch from 8 to 16
- Too many epochs → Reduce from 100 to 50

---

## 📊 Expected Results

| Metric | After 10 Epochs | After 50 Epochs | After 100 Epochs |
|--------|-----------------|-----------------|------------------|
| mAP50 | 0.65-0.70 | 0.85-0.88 | 0.90-0.95 |
| Precision | 0.80 | 0.90 | 0.93+ |
| Recall | 0.70 | 0.85 | 0.90+ |
| Time | ~3 min | ~15 min | ~30 min (T4) |

---

## 💡 Pro Tips

1. **Save logs:** Download logs/ folder for debugging
2. **Monitor training:** Watch loss curves in results.png
3. **Early stopping:** Patience=20 stops if no improvement
4. **Batch size:** Increase for GPU memory headroom
5. **Image size:** 640x640 is good balance
6. **Learning rate:** 0.01 is standard starting point

---

## 🎯 Next Steps

1. ✓ Run training on Kaggle (30-60 minutes)
2. ✓ Download best.pt
3. ✓ Place in EDAI4/models/yolov8/
4. ✓ Update config/settings.yaml
5. ✓ Run EDAI4 Streamlit app
6. ✓ Test P&ID detection

---

## 📞 Support

**If something goes wrong:**

1. Check the log file: `/kaggle/working/logs/yolo_training_*.log`
2. Verify GPU is enabled in Settings
3. Make sure dataset is added (Input tab)
4. Try reducing batch size if memory error
5. Reduce epochs to test quickly

**Log file contains:**
- GPU information
- Dataset statistics
- Training progress
- Validation results
- Any errors/warnings

---

**Good luck with your training! 🚀**
