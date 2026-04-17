# Graph Coordinate Debugging Guide

## Issue Summary

The minimap shows nodes clustered in one corner, while the main graph appears spread out (only due to auto-zoom). This indicates the backend is sending coordinates where all nodes are positioned in a small area of the image.

## What I've Done

### 1. Enhanced Frontend Logging

Added detailed coordinate transformation logging in `GraphViewer.tsx`:
- Logs raw node data from backend
- Shows original coordinate bounds (min/max X/Y)
- Displays coordinate ranges
- Shows transformation parameters (scale, offsets)
- Logs final transformed coordinates
- Shows sample transformations for first 3 nodes

### 2. Enhanced Backend Logging

Added coordinate analysis in `src/api/main.py` `/graph` endpoint:
- Logs number of nodes being sent
- Shows X coordinate range and span
- Shows Y coordinate range and span
- Displays sample nodes with their coordinates

### 3. Improved Minimap Visibility

Updated minimap configuration:
- Added stroke width and color for better visibility
- Set explicit size (200x150)
- Maintained color coding by node type

### 4. Better UI Feedback

Updated stats panel to show:
- Node and edge counts
- "Ready" indicator when graph is initialized
- Hint to check browser console for details

## How to Debug

### Step 1: Process a P&ID Image

1. Start backend: `python -m uvicorn src.api.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Upload and process a P&ID image

### Step 2: Check Backend Logs

Look for output like:
```
INFO: Graph API: Sending 69 nodes
INFO: X range: 1850.5 to 1950.3 (span: 99.8)
INFO: Y range: 890.2 to 950.7 (span: 60.5)
INFO: Sample nodes: [{'id': 'node_0', 'x': 1875.3, 'y': 920.1, ...}, ...]
```

**Analysis:**
- ❌ BAD: Span < 200 pixels → Nodes are clustered
- ✅ GOOD: Span > 1000 pixels → Nodes are spread out

### Step 3: Check Frontend Console

Open browser DevTools (F12) and look for:
```
=== GRAPH RENDERING ===
Total nodes: 69
Sample raw nodes: [{id: "node_0", x: 1875.3, y: 920.1, ...}, ...]
Original Bounds: {minX: 1850.5, maxX: 1950.3, minY: 890.2, maxY: 950.7}
Original Ranges: {rangeX: 99.8, rangeY: 60.5}
Uniform Scale: 20.02
Canvas centering: {scaledWidth: 1998, scaledHeight: 1211, offsetX: 1, offsetY: 394}
Final coordinate bounds: {minFinalX: "1.0", maxFinalX: "1999.0", ...}
```

**Analysis:**
- Check "Original Ranges" - should be large (>1000)
- If ranges are small (<200), backend is sending clustered coordinates
- "Final coordinate bounds" should span most of 0-2000 range

### Step 4: Visual Inspection

Look at the minimap (bottom-right):
- ❌ BAD: All blue dots in one corner
- ✅ GOOD: Blue dots spread across minimap

## Common Issues and Solutions

### Issue 1: SAHI Coordinate Transformation

**Symptom:** All nodes have similar coordinates

**Cause:** SAHI might be returning coordinates in slice space instead of full image space

**Solution:** Check `src/perception/sahi_detector.py`:
```python
# Verify this returns full image coordinates
for pred in result.object_prediction_list:
    bbox = pred.bbox  # Should be in original image coordinates
```

### Issue 2: Image Preprocessing

**Symptom:** Coordinates don't match image dimensions

**Cause:** Image might be cropped or resized before detection

**Solution:** Add logging in perception pipeline:
```python
logger.info(f"Image shape: {image.shape}")
logger.info(f"Detection bbox: {bbox.to_tuple()}")
# Bbox coordinates should be within image dimensions
```

### Issue 3: Detection Limited to One Region

**Symptom:** YOLO only detects objects in part of the image

**Cause:** 
- Confidence threshold too high
- Model not trained on full P&IDs
- SAHI slice size too small

**Solution:** Adjust SAHI parameters:
```python
slice_size = 800  # Increase from 640
overlap_ratio = 0.3  # Increase overlap
confidence_threshold = 0.15  # Lower threshold
```

## Verification Test

To verify the frontend is working correctly, you can manually test with known coordinates:

1. Open browser console
2. Paste this code:

```javascript
// Create test graph with nodes spread across 1000x1000 area
const testGraph = {
  nodes: [
    { id: "n1", type: "instrument", tag: "FT-101", label: "FT-101", x: 100, y: 100 },
    { id: "n2", type: "valve", tag: "V-101", label: "V-101", x: 500, y: 100 },
    { id: "n3", type: "equipment", tag: "P-101", label: "P-101", x: 900, y: 100 },
    { id: "n4", type: "instrument", tag: "PT-101", label: "PT-101", x: 100, y: 500 },
    { id: "n5", type: "valve", tag: "V-102", label: "V-102", x: 500, y: 500 },
    { id: "n6", type: "equipment", tag: "T-101", label: "T-101", x: 900, y: 500 },
    { id: "n7", type: "instrument", tag: "LT-101", label: "LT-101", x: 100, y: 900 },
    { id: "n8", type: "valve", tag: "V-103", label: "V-103", x: 500, y: 900 },
    { id: "n9", type: "equipment", tag: "R-101", label: "R-101", x: 900, y: 900 },
  ],
  edges: []
};

// Check console logs - should show wide coordinate ranges
// Check minimap - should show 3x3 grid of dots
```

If the test data shows correctly in the minimap (3x3 grid), then the frontend is working and the issue is in the backend coordinate generation.

## Files Modified

1. `frontend/src/components/GraphViewer.tsx`
   - Enhanced coordinate logging
   - Improved minimap configuration
   - Better UI feedback

2. `src/api/main.py`
   - Added coordinate range logging in `/graph` endpoint

3. Documentation:
   - `MINIMAP_COORDINATE_ISSUE.md` - Detailed analysis
   - `COORDINATE_DEBUGGING_GUIDE.md` - This file

## Next Steps

1. **Run the application** and process a P&ID image
2. **Check backend logs** for coordinate ranges
3. **Check frontend console** for transformation details
4. **Inspect minimap** for node distribution

If coordinates are clustered (span < 200px):
- Check SAHI coordinate transformation
- Verify image preprocessing
- Adjust detection parameters
- Visualize raw YOLO detections on image

If coordinates are spread out (span > 1000px):
- Frontend transformation is working correctly
- Issue might be with specific P&ID image
- Try different images to verify

## Expected Output

### Good Coordinates (Backend)
```
INFO: X range: 150.0 to 1850.0 (span: 1700.0)
INFO: Y range: 200.0 to 1200.0 (span: 1000.0)
```

### Good Coordinates (Frontend)
```
Original Ranges: {rangeX: 1700, rangeY: 1000}
Final coordinate bounds: {rangeX: "1700.0", rangeY: "1000.0"}
```

### Good Minimap
- Blue dots spread across entire minimap area
- Matches main graph layout
- No clustering in corners

## Support

If the issue persists after following this guide:
1. Share backend log output (coordinate ranges)
2. Share frontend console output (transformation logs)
3. Share screenshot of minimap
4. Share sample P&ID image (if possible)

This will help identify whether the issue is in:
- Detection (YOLO/SAHI)
- Coordinate extraction (Perception pipeline)
- Graph building (Topology layer)
- Frontend transformation (React component)
