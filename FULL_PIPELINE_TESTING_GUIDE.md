# 🧪 EDAI4 Full Pipeline Testing Guide

## Overview
This guide shows how to test the complete **Layer 1 → Layer 2 → Layer 3** pipeline on real P&ID images.

## Testing Options

### Option 1: Kaggle Notebook (RECOMMENDED) ✅
**Why**: Has all dependencies, trained model, and validation images.

#### Step-by-Step Instructions:

1. **Upload EDAI4 Code to Kaggle**
   ```python
   # In Kaggle notebook, create these directories and upload files:
   !mkdir -p /kaggle/working/src/perception
   !mkdir -p /kaggle/working/src/topology
   !mkdir -p /kaggle/working/src/utils
   
   # Upload all .py files from your local:
   # - src/perception/*.py
   # - src/topology/*.py
   # - src/utils/*.py
   ```

2. **Run the Full Pipeline Test**
   ```python
   # Copy-paste the contents of KAGGLE_FULL_PIPELINE_TEST.py
   # OR upload the file and run:
   !python /kaggle/working/KAGGLE_FULL_PIPELINE_TEST.py
   ```

3. **View Results**
   - 3 visualizations will be displayed inline
   - 2 data exports (JSON + CSV)
   - All saved to `/kaggle/working/`

#### Expected Output:
```
🎲 Selected test image: pid_sample_042.jpg
📁 Model: /kaggle/working/runs/detect/edai4_layer1_v2/weights/best.pt

===============================================================
⚙️ LAYER 1: YOLO Symbol Detection
===============================================================
✓ Image loaded: 1024x768 pixels
✓ Detected 47 symbols

📊 Class Distribution:
  instrument.bubble: 23
  valve.control: 12
  equipment.pump: 8
  valve.check: 4
  ...

===============================================================
⚙️ LAYER 2: OCR + Text-Symbol Association
===============================================================
✓ Instruments: 23
✓ Equipment: 8
✓ Lines: 3
✓ Unidentified: 12

📋 Tagged Instruments (21):
  FIT-101         (instrument.bubble) - Flow Indicator Transmitter
  PCV-201         (instrument.bubble) - Pressure Control Valve
  TIT-301         (instrument.bubble) - Temperature Indicator Transm
  ...

===============================================================
⚙️ LAYER 3: Topology Graph Construction
===============================================================
✓ Graph built: 46 nodes, 138 edges

PIDGraph Summary:
  Total Nodes: 46
  - Instruments: 23 (21 tagged)
  - Valves: 12
  - Equipment: 8
  Total Edges: 138
  Edge Types: 3

📊 Edge Type Distribution:
  MEASURES       : 31
  CONTROLS       : 24
  CONNECTED_TO   : 83

===============================================================
✅ FULL PIPELINE TEST COMPLETE!
===============================================================
```

### Option 2: Local Testing (Advanced)
**Requirements**:
- All dependencies installed
- Trained YOLO model (best.pt)
- P&ID images

```bash
# Install dependencies
pip install ultralytics opencv-python easyocr matplotlib pandas networkx

# Run test
python tests/test_full_pipeline_e2e.py --image path/to/pid.jpg --output results/

# Or use random validation image (if available)
python tests/test_full_pipeline_e2e.py
```

## Output Files

After running the pipeline, you'll get:

### 1. Visualizations (PNG)
- **layer1_detections.png** - YOLO bounding boxes with class labels
- **layer2_associations.png** - OCR text matched to symbols (tagged in green)
- **layer3_graph.png** - NetworkX graph visualization with edge types

### 2. Data Exports

#### perception_result.json
```json
{
  "instruments": [
    {
      "tag_number": "FIT-101",
      "tag_type": "instrument",
      "symbol_class": "instrument.bubble",
      "x": 245.5,
      "y": 123.7,
      "bbox": [240, 118, 251, 129],
      "confidence": 0.95,
      "description": "Flow Indicator Transmitter",
      "parsed_tag": {
        "function": "FI",
        "modifier": "T",
        "loop_number": "101",
        ...
      }
    },
    ...
  ],
  "equipment": [...],
  "lines": [...],
  "unidentified_symbols": [...]
}
```

#### graph_nodes.csv
```csv
tag,type,tag_type,symbol_class,x,y,confidence,description,function,modifier,loop_number
FIT-101,instrument,instrument,instrument.bubble,245.5,123.7,0.95,Flow Indicator Transmitter,FI,T,101
PCV-201,instrument,instrument,instrument.bubble,456.2,234.1,0.92,Pressure Control Valve,PC,V,201
P-101,equipment,equipment,equipment.pump,123.4,567.8,0.88,Centrifugal Pump,,,
...
```

## Interpreting Results

### Layer 1 Metrics
- **Detection Count**: Should match expected symbols in P&ID
- **Class Distribution**: Check for class imbalance
- **Confidence Scores**: High (>0.8) indicates good model performance

### Layer 2 Metrics
- **Tagged vs Untagged**: Higher tagged % = better OCR/association
- **Tag Format**: Should follow ISA S5.1 patterns (e.g., FIT-101)
- **Description Quality**: Auto-generated from function codes

### Layer 3 Metrics
- **Node Count**: Should equal Layer 2 total symbols
- **Edge Count**: Depends on proximity threshold and drawing density
- **Edge Types**:
  - **CONTROLS**: Instrument → Valve (control loops)
  - **MEASURES**: Instrument → Equipment (measurement)
  - **FLOWS_TO**: Equipment → Equipment (process flow)
  - **CONNECTED_TO**: Generic proximity

## Troubleshooting

### Issue: "No module named 'src'"
**Solution**: Check sys.path setup
```python
import sys
sys.path.insert(0, '/kaggle/working')  # Adjust to your root
```

### Issue: "Could not find YOLO model"
**Solution**: Verify model path
```python
from pathlib import Path
model_path = "/kaggle/working/runs/detect/edai4_layer1_v2/weights/best.pt"
print(f"Model exists: {Path(model_path).exists()}")
```

### Issue: "No images found in validation directory"
**Solution**: Check validation images
```python
from pathlib import Path
val_dir = Path("/kaggle/working/pid_dataset/images/val/")
images = list(val_dir.glob("*.jpg")) + list(val_dir.glob("*.png"))
print(f"Found {len(images)} images")
```

### Issue: Low tagging rate (<50%)
**Possible causes**:
- OCR failing (poor image quality, small text)
- Association radius too small (increase from 100 to 150)
- Non-standard tag formats

**Solution**: Adjust parameters
```python
pipeline = PerceptionPipeline(
    model_path=model_path,
    ocr_languages=['en'],
    association_radius=150,  # Increased
    min_confidence=0.4        # Lower threshold
)
```

### Issue: Too many/few edges in graph
**Solution**: Adjust proximity threshold
```python
# Tighter connections (fewer edges)
builder = GraphBuilder(proximity_threshold=100.0)

# Looser connections (more edges)
builder = GraphBuilder(proximity_threshold=300.0)
```

## Performance Benchmarks

### Expected Processing Times (Kaggle Tesla T4)
- **Layer 1 (YOLO)**: ~10-20ms per image
- **Layer 2 (OCR)**: ~2-5s per image (dominated by EasyOCR)
- **Layer 3 (Graph)**: ~1-5ms per graph (50 nodes)
- **Total Pipeline**: ~3-7s per P&ID

### Typical Accuracy (Validation Set)
- **Symbol Detection (Layer 1)**: 88.1% mAP50
- **Tag Recognition (Layer 2)**: 75-85% (depends on image quality)
- **Graph Connectivity (Layer 3)**: 90%+ (if proximity threshold tuned)

## Next Steps After Testing

Once you've verified the pipeline works:

1. **Batch Processing**: Process all validation images
   ```python
   for img_path in val_dir.glob("*.jpg"):
       result = pipeline.process_image(cv2.imread(str(img_path)))
       graph = builder.build_from_perception(result)
       # Save results...
   ```

2. **Continue Layer 3 Development**:
   - Phase 3.2: Spatial relationship analysis
   - Phase 3.3: Flow path detection
   - Phase 3.4: Graph query tools

3. **Generate Deliverables**:
   - Instrument Index (from tagged instruments)
   - I/O List (from control loops)
   - Alarm List (from safety instruments)

## Quick Test Checklist

- [ ] YOLO model loaded successfully
- [ ] Detections visualized with correct classes
- [ ] OCR text extracted and visible
- [ ] Instruments tagged with ISA S5.1 format
- [ ] Graph nodes created from all symbols
- [ ] Graph edges created based on proximity
- [ ] Edge types (CONTROLS, MEASURES) present
- [ ] JSON and CSV exports created
- [ ] No errors in console output

✅ If all checked, your pipeline is working correctly!
