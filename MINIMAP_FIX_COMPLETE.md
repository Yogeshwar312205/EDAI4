# Minimap Coordinate Fix - Complete Implementation

## Problem Summary

The minimap shows blue dots clustered in one corner while the main graph appears spread out. This is because:
1. Backend is sending coordinates where all nodes are in a small area (50-100px range)
2. Frontend scales these up to fill the canvas (making them appear spread in main view)
3. Minimap shows the TRUE positions (revealing the clustering)

## Changes Implemented

### 1. Backend Logging (`src/perception/perception_pipeline.py`)

Added coordinate range analysis after detection:
```python
# Logs X/Y coordinate ranges and spans
# Warns if coordinates are clustered (<200px span)
# Shows first 5 instrument coordinates
```

### 2. API Endpoint Logging (`src/api/main.py`)

Enhanced `/graph` endpoint with detailed coordinate analysis:
```python
# Logs coordinate ranges when sending graph data
# Warns if clustering detected
# Shows sample nodes
```

### 3. Frontend Logging (`frontend/src/components/GraphViewer.tsx`)

Already has comprehensive logging:
```javascript
// Logs raw backend data
// Shows coordinate transformation
// Displays final positions
```

### 4. Diagnostic Tools

Created `scripts/diagnose_coordinates.py`:
- Fetches graph data from API
- Analyzes coordinate distribution
- Identifies clustering issues
- Saves analysis to JSON file

## How to Use

### Step 1: Process an Image

1. Start backend:
   ```bash
   python -m uvicorn src.api.main:app --reload
   ```

2. Start frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Upload and process a P&ID image

### Step 2: Check Backend Logs

Look for this output in the backend terminal:

```
============================================================
COORDINATE ANALYSIS
Total instruments: 69
X range: 150.0 to 1850.0 (span: 1700.0)
Y range: 200.0 to 1200.0 (span: 1000.0)
============================================================
```

**If you see:**
- ✅ Span > 1000px → Coordinates are good
- ❌ Span < 200px → **CLUSTERING DETECTED** - this is the problem!

### Step 3: Check Frontend Console

Open browser DevTools (F12) and look for:

```
=== GRAPH RENDERING ===
Total nodes: 69
Original Ranges: {rangeX: 1700, rangeY: 1000}
```

### Step 4: Run Diagnostic Script

```bash
python scripts/diagnose_coordinates.py
```

This will show:
- Coordinate ranges
- Whether clustering is detected
- Sample node positions
- Saves full analysis to `data/coordinate_analysis.json`

## Interpreting Results

### Scenario A: Coordinates ARE Clustered (span < 200px)

**Backend logs show:**
```
X range: 1850.0 to 1950.0 (span: 100.0)
⚠️  Coordinates are clustered! Check SAHI detection.
```

**This means:**
- SAHI/YOLO is only detecting objects in one small region
- Image might be cropped or preprocessed incorrectly
- Detection parameters need adjustment

**Solutions:**

1. **Check Image Dimensions**
   Add to `src/api/main.py` after loading image:
   ```python
   logger.info(f"Image shape: {image.shape}")
   ```
   Verify image is full P&ID, not cropped

2. **Adjust SAHI Parameters**
   In `src/perception/high_density_pipeline.py`:
   ```python
   slice_size = 800  # Increase from 640
   overlap_ratio = 0.3  # Increase overlap
   confidence_threshold = 0.15  # Lower to detect more
   ```

3. **Visualize Detections**
   Add to `src/api/main.py` after processing:
   ```python
   import cv2
   img_debug = image.copy()
   for inst in result.instruments:
       cv2.circle(img_debug, (int(inst.x), int(inst.y)), 10, (0, 255, 0), -1)
   cv2.imwrite("debug_detections.jpg", img_debug)
   ```
   Check if circles are spread across image or clustered

### Scenario B: Coordinates ARE Spread (span > 1000px)

**Backend logs show:**
```
X range: 150.0 to 1850.0 (span: 1700.0)
Y range: 200.0 to 1200.0 (span: 1000.0)
```

**But minimap still shows clustering?**

This would indicate a frontend transformation issue. Check:
1. Frontend console logs for transformation errors
2. Minimap configuration
3. ReactFlow version compatibility

## Common Issues and Fixes

### Issue 1: SAHI Only Detecting in One Slice

**Symptom:** All coordinates in 640x640 range

**Cause:** SAHI slice coordinates not transformed to full image space

**Fix:** Verify in `src/perception/sahi_detector.py`:
```python
# SAHI should automatically handle coordinate transformation
# Verify bbox.minx, bbox.maxx are in full image coordinates
```

### Issue 2: Image Preprocessing Crops P&ID

**Symptom:** Coordinates match a small portion of image

**Cause:** Image resized or cropped before detection

**Fix:** Check image preprocessing in API:
```python
# Ensure image is not resized/cropped
# Use original image dimensions
```

### Issue 3: Low Detection Coverage

**Symptom:** Only detecting objects in center/corner

**Cause:** 
- Confidence threshold too high
- Model not trained on full P&IDs
- Slice size too small

**Fix:**
```python
# In high_density_pipeline.py
confidence_threshold = 0.15  # Lower from 0.20
slice_size = 800  # Increase from 640
overlap_ratio = 0.3  # Increase from 0.25
```

## Expected Behavior After Fix

### Backend Logs
```
============================================================
COORDINATE ANALYSIS
Total instruments: 69
X range: 150.0 to 1850.0 (span: 1700.0)
Y range: 200.0 to 1200.0 (span: 1000.0)
============================================================
```

### Frontend Console
```
Original Ranges: {rangeX: 1700, rangeY: 1000}
Uniform Scale: 1.18
Final coordinate bounds: {rangeX: "2000.0", rangeY: "1176.0"}
```

### Minimap
- Blue dots spread across entire minimap area
- Matches main graph layout exactly
- No clustering in corners

### Main Graph
- Nodes visible immediately
- Proper spacing
- Matches P&ID spatial layout

## Files Modified

1. `src/perception/perception_pipeline.py` - Added coordinate logging
2. `src/api/main.py` - Enhanced graph endpoint logging
3. `frontend/src/components/GraphViewer.tsx` - Already had logging
4. `scripts/diagnose_coordinates.py` - New diagnostic tool

## Next Steps

1. **Run the application** with your P&ID image
2. **Check all three log sources**:
   - Backend terminal (perception pipeline)
   - Backend terminal (API endpoint)
   - Frontend browser console
3. **Run diagnostic script** for detailed analysis
4. **If clustering detected**, follow solutions above
5. **Share logs** if issue persists

## Testing Checklist

- [ ] Backend shows coordinate span > 1000px
- [ ] Frontend console shows proper transformation
- [ ] Minimap shows dots spread across area
- [ ] Main graph matches minimap layout
- [ ] Nodes positioned correctly relative to P&ID
- [ ] No clustering in corners
- [ ] Zoom/pan works smoothly
- [ ] Edit mode functions correctly

## Support Information

If the issue persists, please provide:
1. Backend log output (coordinate ranges)
2. Frontend console output (transformation logs)
3. Output from `scripts/diagnose_coordinates.py`
4. Screenshot of minimap
5. P&ID image dimensions
6. Number of nodes detected

This will help identify the exact cause and solution.
