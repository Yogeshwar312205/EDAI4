# YOLO P&ID Training on Kaggle - Complete Instructions

## Prerequisites
- Kaggle account
- Access to dataset: "p-and-id-symbols-for-computer-vision" (already available)
- GPU accelerator enabled

---

## Step 1: Create a New Kaggle Notebook

1. Go to https://www.kaggle.com/code
2. Click **"New Notebook"**
3. Name it: `YOLO-PID-Training`
4. Make sure the notebook is set to **Python** language

---

## Step 2: Enable GPU Accelerator (CRITICAL!)

1. Click **Settings** (top right of notebook, gear icon)
2. Under **"Accelerator"**, select **GPU** (P100 or T4)
3. Click **"Save"**
4. Wait for the kernel to restart (usually takes 1-2 minutes)

**Verify GPU is enabled:**
```python
import torch
print(f"GPU Available: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
```

If output shows `True` and a GPU name, you're good to go!

---

## Step 3: Add the Dataset

1. Click **"+ Add Input"** button on the right panel
2. Search for: `p-and-id-symbols-for-computer-vision`
3. Select the dataset by mollous
4. Click **"Add"**

The dataset will be available at:
```
/kaggle/input/datasets/mollous/p-and-id-symbols-for-computer-vision
```

---

## Step 4: Copy and Run the Training Code

### Option A: QUICK METHOD (All-in-One Cell)

1. Create a new cell
2. Copy the ENTIRE code from: **`KAGGLE_QUICK_COPY_PASTE.py`**
3. Paste it into the cell
4. Click **"Run"** or press Shift+Enter
5. Wait for training to complete (usually 30-60 minutes)

### Option B: DETAILED METHOD (Multiple Cells)

Create separate cells for each section from **`kaggle_yolo_training_complete.py`**:

- Cell 1: Environment Setup
- Cell 2: Install Dependencies
- Cell 3: Explore Dataset
- Cell 4: Create YOLO Config
- Cell 5: Verify Dataset
- Cell 6: Train Model
- Cell 7: Validate Model
- Cell 8: Export Model
- Cell 9: Summary
- Cell 10: Test Model

---

## What the Code Does

### 1. **GPU Verification**
   - Checks if GPU is available
   - Prints GPU name and memory
   - Logs all information

### 2. **Dataset Exploration**
   - Verifies dataset integrity
   - Counts images and labels
   - Checks image formats

### 3. **Configuration Setup**
   - Creates `data.yaml` (YOLO format)
   - Configures training parameters
   - Sets up logging system

### 4. **Model Training**
   - Loads YOLOv8n (nano model - fastest)
   - Trains for 100 epochs
   - Uses 16 batch size (adjust if GPU runs out of memory)
   - Saves metrics and best model

### 5. **Validation & Export**
   - Validates on validation set
   - Exports model to different formats
   - Generates comprehensive logs

### 6. **Summary & Logs**
   - Creates detailed logs
   - Saves training summary
   - Shows location of outputs

---

## Expected Output

During training, you should see:
```
100%|████████████| 100/100 [XX:XX<00:00, XX.XXs/it]
  Class     Images  Instances      Box(P          R      mAP50  mAP50-95):
    all         XX        XXX       0.XX       0.XX      0.XX      0.XX
```

### Key Files Generated

**Location:** `/kaggle/working/`

```
/kaggle/working/
├── yolov8_pid_training/
│   ├── weights/
│   │   ├── best.pt          ← BEST TRAINED MODEL
│   │   └── last.pt
│   ├── results.csv          ← TRAINING METRICS
│   ├── plots/               ← VISUALIZATION PLOTS
│   └── runs/
├── logs/
│   ├── yolo_training_*.log  ← DETAILED LOGS
│   ├── training_summary.json
│   └── dataset_info.json
└── data.yaml                ← YOLO CONFIG
```

---

## Troubleshooting

### **Error: GPU not found**
```
Error: CUDA not available
```
**Solution:**
- Go to Settings → Accelerator → Select GPU
- Restart the notebook

### **Error: Out of memory**
```
CUDA out of memory. Tried to allocate XX GB
```
**Solution:**
- Reduce batch size in the code:
```python
'batch': 8,  # Change from 16 to 8
```

### **Error: Dataset not found**
```
FileNotFoundError: /kaggle/input/datasets/mollous/p-and-id-symbols-for-computer-vision
```
**Solution:**
- Make sure dataset is added (Step 3)
- Check dataset name spelling

### **Error: Takes too long**
**Solution:**
- Use YOLOv8n (nano) - faster training
- Reduce epochs to 50
- Increase batch size (if GPU allows)

---

## Download Your Trained Model

After training completes:

1. **Go to Output tab** (right panel)
2. **Expand "yolov8_pid_training"**
3. **Download files:**
   - `weights/best.pt` ← **YOUR TRAINED MODEL**
   - `results.csv` ← Training metrics

---

## Using Your Trained Model

After downloading `best.pt`:

```python
from ultralytics import YOLO

# Load your trained model
model = YOLO('best.pt')

# Detect P&ID symbols
results = model.predict(source='path/to/pid/image.jpg', conf=0.25)

# Access predictions
for r in results:
    print(r.boxes)  # Detections
```

---

## GPU Memory Tips

| GPU | Max Batch Size | Recommended |
|-----|-------|--------------|
| T4 (16GB) | 32 | 16 |
| P100 (16GB) | 32 | 16 |
| V100 (16GB) | 64 | 32 |
| K80 (12GB) | 16 | 8 |
| CPU | 1-4 | DON'T USE |

---

## Log Files Explanation

**Log files are saved to:** `/kaggle/working/logs/`

### `yolo_training_TIMESTAMP.log`
Contains:
- GPU information
- Dataset structure
- Training progress
- Validation results
- Errors and warnings

### `training_summary.json`
Contains:
```json
{
  "timestamp": "20240115_143022",
  "model": "YOLOv8n",
  "epochs": 100,
  "gpu": "Tesla T4",
  "best_model": "/kaggle/working/yolov8_pid_training/weights/best.pt"
}
```

### `dataset_info.json`
Contains dataset statistics:
```json
{
  "train": {"images": 500, "labels": 500},
  "val": {"images": 100, "labels": 100},
  "test": {"images": 100, "labels": 100}
}
```

---

## Parameter Tuning Guide

### For Better Accuracy (Slower)
```python
'epochs': 200,
'batch': 32,
'imgsz': 1024,
'patience': 30,
```

### For Faster Training (Less Accurate)
```python
'epochs': 50,
'batch': 8,
'imgsz': 416,
'patience': 10,
```

### Balanced (Recommended)
```python
'epochs': 100,
'batch': 16,
'imgsz': 640,
'patience': 20,
```

---

## Expected Training Time

| GPU | Model | Time |
|-----|-------|------|
| P100 | YOLOv8n | 20-30 min |
| T4 | YOLOv8n | 30-50 min |
| P100 | YOLOv8s | 40-60 min |
| CPU | YOLOv8n | 2-4 hours |

---

## Success Checklist

- [x] GPU enabled in Settings
- [x] Dataset added from Kaggle
- [x] Code copied into notebook
- [x] Training started and completed
- [x] Best model saved
- [x] Logs downloaded
- [x] Model downloaded locally

---

## Next Steps After Training

1. **Download** `best.pt` to your local machine
2. **Integrate** into EDAI4 project:
   ```
   d:\EDAI4\models\yolov8\best.pt
   ```

3. **Update** `config/settings.yaml`:
   ```yaml
   perception:
     yolo:
       model_path: "./models/yolov8/best.pt"
   ```

4. **Test** with EDAI4 Streamlit app:
   ```bash
   streamlit run app/main.py
   ```

---

## Support & Issues

If you encounter issues:

1. **Check logs:** `/kaggle/working/logs/yolo_training_*.log`
2. **Verify GPU:** Run cell 1 to check GPU status
3. **Restart kernel:** Sometimes helps with memory issues
4. **Reduce batch size:** If out of memory
5. **Check dataset:** Verify images and labels are valid

---

**Happy training! 🚀**
