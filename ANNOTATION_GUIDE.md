# EDAI4 — YOLO Annotation Guide  
**Phase 3: Building a Focused Dataset for Custom Equipment Detection**

---

## The Core Rule

> **Your hybrid pipeline already handles instrument bubbles (circles + OCR + regex).**  
> YOLO's job is ONLY to find what the hybrid pipeline CANNOT: complex equipment shapes.

---

## ✅ What TO Annotate

Draw bounding boxes **only** around these categories:

| Class Label | What It Includes |
|---|---|
| `valve.gate` | Gate valves (diamond/square body) |
| `valve.globe` | Globe valves |
| `valve.ball` | Ball valves (round body) |
| `valve.butterfly` | Butterfly valves |
| `valve.check` | Check / non-return valves |
| `valve.control` | Control valves (with actuator hat) |
| `valve.safety_relief` | PSV / PRV / safety relief valves |
| `equipment.pump` | Centrifugal / reciprocating pumps |
| `equipment.compressor` | Compressors, blowers, fans |
| `equipment.vessel` | Tanks, drums, columns, reactors |
| `equipment.furnace` | Furnaces, fired heaters |
| `fitting.reducer` | Pipe reducers |
| `fitting.blind` | Blind flanges |

---

## ❌ What NOT to Annotate

| Item | Reason |
|---|---|
| **Instrument bubbles (circles with FT-101 etc.)** | Handled by OpenCV HoughCircles + OCR merge |
| **Text / tag numbers** | Handled by PaddleOCR + ISA validator |
| **Pipe lines / arrows** | Handled by LineDetector (Phase 4) |
| **Title blocks, legends, revision tables** | Background noise — skip entirely |

---

## Annotation Tool Setup (Roboflow)

1. Go to [roboflow.com](https://roboflow.com) → **Create New Project** → Object Detection
2. Upload your P&ID PNG/PDF exports
3. Use the **Bounding Box** tool (not polygon)
4. Label classes **exactly** as shown in the table above (lowercase with dots)
5. Export in **YOLOv8 TXT** format

---

## Dataset Rules

| Parameter | Recommendation |
|---|---|
| Images | 100–200 P&ID drawings minimum |
| Annotation density | Every valve / pump / vessel in each image |
| Image resize | Export at **1280×1280** (SAHI slices to 640 anyway) |
| Train / Val split | 80% / 20% |

---

## Retraining Command (after export)

Place Roboflow export at `D:\EDAI4\data\custom_dataset\`. Then run:

```bash
cd D:\EDAI4
python -c "
from ultralytics import YOLO
model = YOLO('yolov8s.pt')
model.train(
    data='data/custom_dataset/data.yaml',
    epochs=100,
    imgsz=640,
    batch=8,
    optimizer='AdamW',
    lr0=0.0005,
    patience=20,
    project='models/yolov8',
    name='custom_v1',
    save=True,
)
"
```

After training, copy `models/yolov8/custom_v1/weights/best.pt` to `models/yolov8/best.pt`  
and restart the pipeline — SAHI will pick it up automatically.

---

## Success Metric

Run `python main.py --image data/sample_pid.png` and check:
- Equipment shapes appear in console as `[YOLO] valve.gate → FV-101`
- No instrument bubbles detected by YOLO (those come from `[HOUGH]` or `[REGEX]`)
