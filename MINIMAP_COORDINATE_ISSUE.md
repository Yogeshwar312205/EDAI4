# Minimap Coordinate Issue - Diagnosis and Solution

## Problem Description

Based on the user's screenshot and description:
- **Minimap**: Shows blue dots clustered in top-right corner
- **Main Graph**: Shows nodes spread out (but only because of auto-fit zoom)
- **Issue**: The actual node coordinates are clustered together, not spread across the P&ID

## Root Cause Analysis

The minimap is showing the TRUE positions of the nodes. The main graph appears correct only because `fitView` zooms in on the clustered nodes. The real problem is that the backend is sending coordinates where all nodes are in a small area.

### Coordinate Flow

1. **YOLO Detection** → Bounding boxes in pixel coordinates
2. **Perception Pipeline** → Calculates center: `(x1+x2)/2, (y1+y2)/2`
3. **Graph Builder** → Uses `inst_data.x, inst_data.y`
4. **API Endpoint** → Sends raw coordinates to frontend
5. **Frontend** → Transforms coordinates for display
6. **Minimap** → Shows actual positions (reveals clustering)

## Possible Causes

### 1. SAHI Slicing Issue (Most Likely)
SAHI divides the image into overlapping slices. If coordinate transformation is incorrect, all detections might be mapped to the same slice's coordinate space.

**Check**: Look at SAHI detector coordinate handling

### 2. Detection Limited to One Area
YOLO might only be detecting objects in one region of the P&ID.

**Check**: Visualize raw YOLO detections on original image

### 3. Coordinate System Mismatch
Different coordinate systems between detection and graph building.

**Check**: Verify bbox coordinates match image dimensions

## Debugging Steps

### Step 1: Check Raw Backend Data

Open browser console when viewing the graph. Look for logs:
```
=== GRAPH RENDERING ===
Total nodes: 69
Sample raw nodes: [...]
Original Bounds: { minX: ..., maxX: ..., minY: ..., maxY: ... }
```

**What to look for:**
- Are minX and maxX very close? (indicates clustering)
- Are coordinates spread across a wide range?
- Example GOOD: minX=100, maxX=1800 (range=1700)
- Example BAD: minX=1850, maxX=1950 (range=100)

### Step 2: Check Backend Logs

When processing an image, check the backend console for:
```python
# In perception_pipeline.py
print(f"Detection bbox: {bbox.to_tuple()}")
print(f"Center: ({bbox.center[0]}, {bbox.center[1]})")
```

### Step 3: Visualize Detections

Add visualization to see where YOLO is detecting objects:

```python
# In src/api/main.py, after processing
import cv2
import numpy as np

# Draw detections on image
img = cv2.imread(image_path)
for inst in result.instruments:
    x, y = int(inst.x), int(inst.y)
    cv2.circle(img, (x, y), 10, (0, 255, 0), -1)
    cv2.putText(img, inst.tag_number, (x+15, y), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

cv2.imwrite("debug_detections.jpg", img)
```

## Solutions

### Solution 1: Fix SAHI Coordinate Transformation

If SAHI is the issue, check `src/perception/sahi_detector.py`:

```python
# Ensure coordinates are in full image space, not slice space
# SAHI should handle this automatically, but verify:
for pred in result.object_prediction_list:
    bbox = pred.bbox  # Should be in full image coordinates
    # NOT in slice coordinates
```

### Solution 2: Increase Detection Coverage

If detections are limited to one area:

```python
# In high_density_pipeline.py or sahi_detector.py
# Adjust SAHI parameters:
slice_size = 640  # Try different sizes
overlap_ratio = 0.3  # Increase overlap
confidence_threshold = 0.15  # Lower threshold to detect more
```

### Solution 3: Verify Image Preprocessing

Check if image is being cropped or resized incorrectly:

```python
# In perception pipeline
print(f"Original image shape: {image.shape}")
print(f"Processed image shape: {processed_image.shape}")
# Coordinates should match original image dimensions
```

## Quick Fix for Testing

To verify the frontend is working correctly, you can test with known coordinates:

1. Open browser console
2. Manually create test graph data:

```javascript
const testGraph = {
  nodes: [
    { id: "n1", type: "instrument", tag: "FT-101", label: "FT-101", x: 100, y: 100 },
    { id: "n2", type: "valve", tag: "V-101", label: "V-101", x: 500, y: 100 },
    { id: "n3", type: "equipment", tag: "P-101", label: "P-101", x: 900, y: 100 },
    { id: "n4", type: "instrument", tag: "PT-101", label: "PT-101", x: 100, y: 500 },
    { id: "n5", type: "valve", tag: "V-102", label: "V-102", x: 500, y: 500 },
    { id: "n6", type: "equipment", tag: "T-101", label: "T-101", x: 900, y: 500 },
  ],
  edges: []
};

// This should show nodes spread across the graph
// If minimap shows them spread out, frontend is working correctly
```

## Expected Behavior After Fix

### Minimap
- Blue dots should be spread across the minimap
- Positions should match the main graph layout
- Dots should not be clustered in one corner

### Main Graph
- Nodes visible immediately on load
- Proper spacing between nodes
- Matches P&ID spatial layout

## Files to Check

1. `src/perception/sahi_detector.py` - SAHI coordinate handling
2. `src/perception/high_density_pipeline.py` - Detection pipeline
3. `src/perception/perception_pipeline.py` - Coordinate extraction
4. `src/topology/graph_builder.py` - Graph node creation
5. `src/api/main.py` - API endpoint data formatting

## Next Steps

1. **Check browser console** - Look at coordinate ranges in logs
2. **Add backend logging** - Print bbox coordinates during processing
3. **Visualize detections** - Draw circles on image to see where objects are detected
4. **Test with simple image** - Use a P&ID with objects clearly spread out
5. **Verify SAHI** - Ensure slice coordinates are transformed to full image space

## Contact Points

If the issue persists:
- Check if YOLO model is trained on full P&IDs or cropped regions
- Verify training data had objects spread across images
- Consider retraining with better spatial distribution
- Test with different SAHI slice sizes and overlap ratios
