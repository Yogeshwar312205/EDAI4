# Testing Guide - Bounding Box Fix

## Quick Start

### 1. Start Backend
```bash
python -m uvicorn src.api.main:app --reload --port 8000
```

### 2. Start Frontend
```bash
cd frontend
npm run dev
```

### 3. Access Application
Open browser to: http://localhost:3000

---

## Test Scenarios

### ✅ Scenario 1: Basic Bounding Box Alignment
**Goal**: Verify boxes align with equipment symbols

**Steps**:
1. Upload a P&ID diagram
2. Wait for processing to complete
3. Switch to "Canvas" view
4. Visually inspect bounding boxes

**Expected Result**:
- Boxes should perfectly align with equipment symbols
- No shifting down/right
- No boxes floating outside container

---

### ✅ Scenario 2: Hover Interaction
**Goal**: Verify hover tooltips work correctly

**Steps**:
1. In Canvas view, hover over any bounding box
2. Observe the tooltip

**Expected Result**:
- Tooltip appears next to the box
- Shows: Tag, Class, Confidence
- Box border becomes thicker
- Box has glow effect

---

### ✅ Scenario 3: Click to Select
**Goal**: Verify click interaction and zoom

**Steps**:
1. Click on any bounding box
2. Observe the zoom behavior

**Expected Result**:
- Canvas zooms to 2x
- Selected detection is centered
- Box border becomes thicker
- Smooth animation

---

### ✅ Scenario 4: Pan Functionality
**Goal**: Verify drag-to-pan works

**Steps**:
1. Click and hold on the canvas (not on a box)
2. Drag the mouse
3. Release

**Expected Result**:
- Canvas pans smoothly
- Cursor changes to grabbing hand
- Bounding boxes move with the image

---

### ✅ Scenario 5: Zoom Functionality
**Goal**: Verify scroll-to-zoom works

**Steps**:
1. Hover over the canvas
2. Scroll mouse wheel up (zoom in)
3. Scroll mouse wheel down (zoom out)

**Expected Result**:
- Canvas zooms in/out smoothly
- Zoom centers on mouse position
- Zoom level displayed in controls (bottom-right)
- Min zoom: 50%, Max zoom: 500%

---

### ✅ Scenario 6: Reset View
**Goal**: Verify reset button works

**Steps**:
1. Pan and zoom the canvas
2. Click "Reset View" button (bottom-right)

**Expected Result**:
- Canvas returns to default position
- Zoom resets to 100%
- Smooth animation

---

### ✅ Scenario 7: Window Resize
**Goal**: Verify bounding boxes stay aligned on resize

**Steps**:
1. With P&ID loaded, resize browser window
2. Make window wider, narrower, taller, shorter
3. Observe bounding boxes

**Expected Result**:
- Boxes stay perfectly aligned with equipment
- No manual refresh needed
- Automatic recalculation via ResizeObserver

---

### ✅ Scenario 8: Different Aspect Ratios
**Goal**: Verify letterbox handling

**Steps**:
1. Upload a wide P&ID (landscape)
2. Verify boxes align
3. Upload a tall P&ID (portrait)
4. Verify boxes align
5. Upload a square P&ID
6. Verify boxes align

**Expected Result**:
- All aspect ratios handled correctly
- Letterboxing (black bars) appears as needed
- Boxes always align with equipment

---

### ✅ Scenario 9: Many Detections
**Goal**: Verify performance with 50+ detections

**Steps**:
1. Upload a complex P&ID with many symbols
2. Observe rendering performance
3. Pan and zoom

**Expected Result**:
- Smooth rendering (no lag)
- All boxes visible and aligned
- Pan/zoom remains smooth

---

### ✅ Scenario 10: Data Table Integration
**Goal**: Verify clicking in table zooms to detection

**Steps**:
1. In Canvas view, scroll down the data table (right side)
2. Click on any row in the table
3. Observe the canvas

**Expected Result**:
- Canvas zooms to selected detection
- Detection is centered
- Box is highlighted

---

## Known Issues to Watch For

### ❌ Old Issues (Should be FIXED)
- ~~Boxes shifting down/right~~ ✅ FIXED
- ~~Boxes floating outside container~~ ✅ FIXED
- ~~Manual scale calculation errors~~ ✅ FIXED
- ~~Letterbox not handled correctly~~ ✅ FIXED

### ⚠️ Potential New Issues
- Performance with 100+ detections (not yet tested)
- Very large images (>10MB) (not yet tested)
- Mobile/touch devices (not yet tested)

---

## Debug Information

### Check Console Logs
Open browser DevTools (F12) and check console for:
- Image natural dimensions
- Rendered dimensions
- Offset calculations
- Detection count

### Inspect DOM Elements
1. Right-click on a bounding box
2. Select "Inspect Element"
3. Verify:
   - `position: absolute`
   - `left`, `top`, `width`, `height` values
   - Parent container structure

### Check Network Tab
Verify:
- Image loads successfully
- API calls return detections
- No 404 or 500 errors

---

## Comparison: Old vs New

### Old Implementation (Konva)
- Manual scale calculations
- Canvas-based rendering
- Difficult to debug
- Letterbox issues

### New Implementation (DOM)
- Percentage-based calculations
- DOM-based rendering
- Easy to inspect
- Automatic letterbox handling

---

## Troubleshooting

### Issue: Boxes still misaligned
**Solution**: 
1. Check if old `InteractiveCanvas` is still being used
2. Verify `InteractiveCanvasDOM` is imported in App.tsx
3. Clear browser cache and hard refresh (Ctrl+Shift+R)

### Issue: Boxes don't appear
**Solution**:
1. Check console for errors
2. Verify detections array has data
3. Check if image loaded successfully

### Issue: Pan/zoom not working
**Solution**:
1. Check if event handlers are attached
2. Verify no other elements blocking mouse events
3. Check browser console for errors

### Issue: Performance lag
**Solution**:
1. Check number of detections (50+ may cause lag)
2. Verify browser hardware acceleration is enabled
3. Try in different browser (Chrome recommended)

---

## Success Criteria

The fix is successful if:
- ✅ All bounding boxes align perfectly with equipment symbols
- ✅ No boxes shift or float outside container
- ✅ Hover and click interactions work smoothly
- ✅ Pan and zoom work correctly
- ✅ Window resize maintains alignment
- ✅ Different aspect ratios handled correctly
- ✅ Performance is acceptable (no lag)

---

## Next Steps After Testing

1. **If all tests pass**:
   - Delete old `InteractiveCanvas.tsx` file
   - Update documentation
   - Deploy to production

2. **If issues found**:
   - Document specific issues
   - Create bug reports
   - Iterate on fixes

3. **Optional enhancements**:
   - Add keyboard shortcuts
   - Add minimap
   - Add measurement tools
   - Export annotated image
