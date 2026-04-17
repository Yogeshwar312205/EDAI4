# Clustered Nodes Issue - Complete Fix

## Problem Description

When you click on blue dots in the minimap, all nodes appear gathered/clustered together in the main view instead of being spread out.

## Root Cause

The backend is sending coordinates where ALL nodes are positioned in a very small area (typically 50-200 pixels). This happens because:

1. **SAHI/YOLO is only detecting objects in one small region of the P&ID**
2. **Coordinate transformation error in detection pipeline**
3. **Image preprocessing is cropping the P&ID**

## How to Verify

### Step 1: Run the diagnostic script

```bash
# Make sure backend is running and you've processed a P&ID
python scripts/check_backend_coordinates.py
```

### Expected Output if Clustered:

```
❌ PROBLEM: Coordinates are SEVERELY CLUSTERED!
   All 69 nodes are within a 85x62 pixel area

This is why:
  • Minimap shows dots clustered in one spot
  • Clicking minimap shows nodes gathered together
  • Initial view looks spread out (due to extreme zoom)
```

### Step 2: Check browser console

Open DevTools (F12) and look for:

```
Original Ranges: {rangeX: 85, rangeY: 62}
⚠️ WARNING: Coordinates appear clustered!
```

## The Fix - Backend Detection

The problem is in the backend detection, NOT the frontend. Here's how to fix it:

### Fix 1: Adjust SAHI Parameters

Edit `src/perception/high_density_pipeline.py`:

```python
class HighDensityPipeline:
    def __init__(
        self,
        model_path: str,
        slice_size: int = 800,  # ← INCREASE from 640
        overlap_ratio: float = 0.3,  # ← INCREASE from 0.25
        confidence_threshold: float = 0.15,  # ← DECREASE from 0.20
        use_gpu: bool = True
    ):
```

**Why this helps:**
- Larger slice_size: Covers more of the image per slice
- Higher overlap: Ensures objects at slice boundaries are detected
- Lower confidence: Detects more objects (including faint ones)

### Fix 2: Verify Image Dimensions

Add logging to `src/api/main.py` in the `/process` endpoint:

```python
@app.post("/process")
async def process_image(file: UploadFile = File(...)):
    # ... existing code ...
    
    # Add this logging
    logger.info(f"Image dimensions: {image.shape}")
    logger.info(f"Image size: {image.shape[1]}x{image.shape[0]} pixels")
    
    # Continue with processing...
```

**Check:** Image dimensions should match your original P&ID (e.g., 2000x1500 pixels)

If dimensions are small (e.g., 640x480), the image is being resized/cropped!

### Fix 3: Check SAHI Coordinate Transformation

Edit `src/perception/sahi_detector.py` and add logging:

```python
def detect(self, image: np.ndarray) -> List[SAHIDetection]:
    h, w = image.shape[:2]
    logger.info(f"SAHI input image: {w}x{h}")
    
    # ... existing SAHI code ...
    
    detections = []
    for pred in result.object_prediction_list:
        bbox = pred.bbox
        logger.debug(f"Detection bbox: ({bbox.minx}, {bbox.miny}) to ({bbox.maxx}, {bbox.maxy})")
        # ... rest of code ...
```

**Check:** Bounding boxes should span across the full image dimensions, not just 0-200 range.

### Fix 4: Visualize Detections

Add this to `src/api/main.py` after processing:

```python
# After: result = pipeline.process_image(image)

# Visualize detections for debugging
import cv2
img_debug = image.copy()
for inst in result.instruments + result.equipment:
    x, y = int(inst.x), int(inst.y)
    cv2.circle(img_debug, (x, y), 15, (0, 255, 0), 3)
    cv2.putText(img_debug, inst.tag_number[:10], (x+20, y), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

# Save debug image
debug_path = "data/output/debug_detections.jpg"
cv2.imwrite(debug_path, img_debug)
logger.info(f"Debug visualization saved to: {debug_path}")
```

**Check:** Open `data/output/debug_detections.jpg` - green circles should be spread across the entire P&ID, not clustered in one corner.

## Testing the Fix

### Step 1: Apply Backend Changes

1. Edit `src/perception/high_density_pipeline.py` with new parameters
2. Restart backend: `python -m uvicorn src.api.main:app --reload`

### Step 2: Process Image Again

1. Upload your P&ID image
2. Process it
3. Check backend logs for coordinate ranges

### Step 3: Verify in Frontend

1. Navigate to Graph view
2. Check browser console for coordinate ranges
3. Look at minimap - dots should be spread out
4. Click on minimap dots - nodes should stay in their positions

### Expected Results After Fix:

**Backend logs:**
```
============================================================
COORDINATE ANALYSIS
Total instruments: 69
X range: 150.0 to 1850.0 (span: 1700.0)  ← GOOD!
Y range: 200.0 to 1200.0 (span: 1000.0)  ← GOOD!
============================================================
```

**Frontend console:**
```
Original Ranges: {rangeX: 1700, rangeY: 1000}  ← GOOD!
✓ No clustering warning
```

**Minimap:**
- Blue dots spread across entire minimap area
- Clicking dots navigates to correct positions
- Nodes stay spread out (not gathered)

## If Fix Doesn't Work

### Check 1: Image Quality

- Is your P&ID image clear and high resolution?
- Are symbols visible and not too faint?
- Try with a different P&ID image to test

### Check 2: Model Performance

- Is the YOLO model trained on similar P&IDs?
- Check model confidence scores in logs
- May need to retrain model with better data

### Check 3: SAHI Installation

```bash
pip install sahi --upgrade
```

Ensure SAHI is properly installed and up to date.

### Check 4: GPU Memory

If using GPU, check if there's enough memory:

```python
# In high_density_pipeline.py
use_gpu = False  # Try with CPU to test
```

## Alternative Workaround (Not Recommended)

If you can't fix the backend immediately, you can artificially spread nodes in the frontend, but this will NOT match the actual P&ID layout:

```typescript
// In GraphViewer.tsx - NOT RECOMMENDED
// This spreads nodes in a grid pattern
const gridSize = Math.ceil(Math.sqrt(coords.length));
coords.forEach((coord, index) => {
  const row = Math.floor(index / gridSize);
  const col = index % gridSize;
  const finalX = col * 200;  // Artificial spacing
  const finalY = row * 200;
  positions.set(coord.id, { x: finalX, y: finalY });
});
```

**Why not recommended:** This destroys the spatial relationships from the P&ID!

## Summary

The issue is **100% a backend detection problem**, not a frontend rendering issue. The backend is only detecting objects in a small region of the P&ID image.

**Fix priority:**
1. ✅ Adjust SAHI parameters (easiest, try first)
2. ✅ Verify image dimensions (check for resizing)
3. ✅ Visualize detections (see where objects are detected)
4. ✅ Check SAHI coordinate transformation
5. ⚠️ Consider model retraining (if above don't work)

**Do NOT:**
- ❌ Try to "fix" this in the frontend by spreading nodes artificially
- ❌ Scale up clustered coordinates (hides the real problem)
- ❌ Ignore the clustering warnings

The frontend is working correctly - it's honestly showing you that the backend is sending clustered coordinates!

## Files to Check/Modify

1. `src/perception/high_density_pipeline.py` - SAHI parameters
2. `src/perception/sahi_detector.py` - Coordinate transformation
3. `src/api/main.py` - Image dimensions and debug visualization
4. `scripts/check_backend_coordinates.py` - Diagnostic tool

## Need Help?

Run these commands and share the output:

```bash
# 1. Check coordinates
python scripts/check_backend_coordinates.py

# 2. Check image in debug output
ls -la data/output/debug_detections.jpg

# 3. Check backend logs
# Look for "COORDINATE ANALYSIS" section
```

This will help identify exactly where the problem is occurring.
