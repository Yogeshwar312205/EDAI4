# Coordinate Analysis - Next Steps

## Issue Fixed

Fixed `NameError: name 'logger' is not defined` in `/graph` endpoint by adding:
```python
import logging
logger = logging.getLogger(__name__)
```

## What to Do Now

### 1. Restart the Backend

The backend needs to be restarted to pick up the logger fix:

```bash
# Stop the current backend (Ctrl+C)
# Then restart:
python -m uvicorn src.api.main:app --reload
```

### 2. Process Your P&ID Image Again

1. Upload your P&ID image in the frontend
2. Click "Process Image"
3. Wait for processing to complete
4. Navigate to the "Graph" view

### 3. Check Backend Logs

After clicking on the Graph view, you should now see logs like:

```
INFO: Graph API: Sending 69 nodes
INFO: X range: XXX.X to YYY.Y (span: ZZZ.Z)
INFO: Y range: XXX.X to YYY.Y (span: ZZZ.Z)
INFO: Sample nodes: [{'id': 'node_0', 'x': ..., 'y': ..., ...}, ...]
```

### 4. Analyze the Coordinate Ranges

**Look at the "span" values:**

#### If span is SMALL (< 200 pixels):
```
INFO: X range: 1850.5 to 1950.3 (span: 99.8)  ← BAD: Nodes clustered
INFO: Y range: 890.2 to 950.7 (span: 60.5)    ← BAD: Nodes clustered
```

This means all nodes are detected in a small area. Possible causes:
- SAHI coordinate transformation issue
- Detection only working in one region
- Image preprocessing problem

#### If span is LARGE (> 1000 pixels):
```
INFO: X range: 150.0 to 1550.0 (span: 1400.0)  ← GOOD: Nodes spread out
INFO: Y range: 100.0 to 950.0 (span: 850.0)    ← GOOD: Nodes spread out
```

This means nodes are properly distributed across the image. The minimap should show them spread out.

### 5. Check Frontend Console

Open browser DevTools (F12) and look for:

```
=== GRAPH RENDERING ===
Total nodes: 69
Sample raw nodes: [...]
Original Bounds: { minX: ..., maxX: ..., minY: ..., maxY: ... }
Original Ranges: { rangeX: ..., rangeY: ... }
```

The ranges should match what the backend reported.

### 6. Inspect the Minimap

Look at the minimap in the bottom-right corner:

- **If dots are clustered in one corner**: Backend is sending clustered coordinates
- **If dots are spread across minimap**: Coordinates are correct, frontend is working

## Understanding Your Current Logs

From your logs, I can see:

```
[YOLO] Found 26 detections
[OCR] Found 104 text blocks (29 ISA tags)
[HOUGH] Found 68 circles
FINAL NODE COUNT: 69
```

This is good - the detection is working. The question is: **Are these 69 nodes spread across the P&ID image, or clustered in one area?**

The coordinate logging will tell us this.

## Expected Behavior

### For a typical P&ID (1607x1001 pixels):

**Good coordinates:**
- X range: 50 to 1550 (span: 1500)
- Y range: 50 to 950 (span: 900)
- Nodes distributed across most of the image

**Bad coordinates (clustered):**
- X range: 1400 to 1500 (span: 100)
- Y range: 800 to 850 (span: 50)
- All nodes in small area (top-right corner)

## What the Minimap Shows

The minimap in your screenshot shows blue dots clustered in the top-right corner. This suggests:

1. **Backend is sending coordinates** where all nodes are in the range:
   - X: ~1400-1600 (right side of image)
   - Y: ~0-200 (top of image)

2. **Main graph looks OK** only because `fitView` zooms in on the clustered nodes

3. **The real issue** is in the detection/coordinate extraction, not the frontend

## Next Actions Based on Logs

### If coordinates are clustered:

1. **Check SAHI coordinate handling** in `src/perception/sahi_detector.py`
2. **Verify HoughCircles coordinates** are in full image space
3. **Add visualization** to see where objects are detected:

```python
# In src/api/main.py, after processing
import cv2
img = cv2.imread(image_path)
for node in state.current_graph.get_all_nodes():
    x, y = int(node.x), int(node.y)
    cv2.circle(img, (x, y), 10, (0, 255, 0), -1)
    cv2.putText(img, node.tag or node.id, (x+15, y), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
cv2.imwrite("data/output/debug_node_positions.jpg", img)
print(f"Saved debug visualization to data/output/debug_node_positions.jpg")
```

This will create an image showing where each node is positioned.

### If coordinates are spread out:

The frontend is working correctly! The minimap should show nodes distributed properly.

## Files Modified

- `src/api/main.py` - Added logging import and logger initialization

## Summary

The logger error is now fixed. Restart the backend, process your image again, and check the coordinate ranges in the logs. This will tell us exactly where the problem is:

- **Small ranges** → Backend detection/coordinate issue
- **Large ranges** → Frontend working correctly

Share the coordinate range logs and I can help diagnose further!
