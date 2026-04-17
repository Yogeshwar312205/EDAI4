# Quick Start Testing Guide - All Features

## 🚀 Start the Application

### 1. Start Backend API
```bash
# In the project root directory
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start Frontend
```bash
# In a new terminal
cd frontend
npm install  # First time only, to install dagre
npm run dev
```

### 3. Open Browser
Navigate to: `http://localhost:5173`

---

## 🧪 Test All Features

### Test 1: Upload and Process P&ID
1. Click the upload area or drag a P&ID image
2. Wait for processing to complete
3. Verify you see the Canvas view with detections

**Expected**: Image loads, detections appear, bounding boxes visible

---

### Test 2: Graph Viewer (NEW HIERARCHICAL LAYOUT)
1. Click the "Graph" tab in the header
2. Observe the graph layout

**Expected**:
- ✅ Nodes arranged in hierarchical left-to-right layout
- ✅ Clear spacing between nodes (no overlapping)
- ✅ Color-coded nodes (blue=instruments, cyan=valves, green=equipment)
- ✅ Animated flow edges with arrows
- ✅ Legend visible in top-right corner
- ✅ Minimap in bottom-right
- ✅ Can pan, zoom, and click nodes

**Before vs After**:
```
Before: Random positions, overlapping, messy
After:  Clean hierarchical flow, easy to understand
```

---

### Test 3: Design Rules Dashboard (FIXED "VIEW ON CANVAS")
1. Click the "Design Rules" tab
2. Wait for rules to load
3. Find any violation card
4. Click "View on Canvas" button

**Expected**:
- ✅ Automatically switches to Canvas view
- ✅ The affected component is highlighted
- ✅ Canvas zooms to show the violation
- ✅ Selected node has glow effect

**Test Different Violations**:
- Try Critical violations (red)
- Try Warning violations (yellow)
- Try Info violations (blue)

---

### Test 4: Flow Simulator - Trace Mode
1. Click the "Flow Sim" tab
2. Ensure "Trace Flow Path" mode is selected
3. Select a start node from dropdown
4. Choose direction (Downstream or Upstream)
5. Click "Trace Flow Path"

**Expected**:
- ✅ Shows loading spinner
- ✅ Displays flow path results
- ✅ Lists all nodes in the path
- ✅ Shows total distance
- ✅ Indicates if flow is blocked

---

### Test 5: Flow Simulator - Valve Simulation (NEW FEATURE)
1. Click the "Flow Sim" tab
2. Click "Simulate Valve" button
3. Select a valve from the dropdown
4. Choose action: "Close Valve" or "Open Valve"
5. Click "Simulate Valve Action"

**Expected**:
- ✅ Dropdown shows only valve nodes
- ✅ Action buttons change color when selected
- ✅ Shows loading spinner during simulation
- ✅ Displays simulation results:
  - Valve ID
  - Action taken
  - Flow status
  - Affected nodes list
- ✅ Color-coded result (red for close, green for open)

**Before vs After**:
```
Before: "Valve simulation coming soon..."
After:  Full valve simulation with results
```

---

### Test 6: Data Table
1. Go to Canvas or Graph view
2. Look at the right panel (Data Table)
3. Click on any row

**Expected**:
- ✅ Clicking a row highlights the node
- ✅ Canvas/Graph zooms to the selected node
- ✅ Can sort by clicking column headers
- ✅ Can filter using search box

---

### Test 7: Deliverables Panel
1. Click the "Deliverables" tab
2. Try downloading different formats

**Expected**:
- ✅ Can download JSON topology
- ✅ Can download CSV data
- ✅ Can download Excel report
- ✅ Can download PDF report

---

### Test 8: Navigation Between Views
1. Start at Canvas view
2. Click "Graph" → verify graph loads
3. Click "Design Rules" → verify rules load
4. Click a violation's "View on Canvas" → verify returns to Canvas
5. Click "Flow Sim" → verify simulator loads
6. Click "Deliverables" → verify panel loads

**Expected**:
- ✅ All tabs are visible
- ✅ Smooth transitions between views
- ✅ State is preserved (selected nodes, etc.)
- ✅ No errors in browser console

---

## 🐛 Common Issues and Solutions

### Issue: Graph nodes are overlapping
**Solution**: This is now fixed with dagre hierarchical layout. If you still see it:
1. Make sure `npm install` was run after updating package.json
2. Check browser console for errors
3. Refresh the page

### Issue: "View on Canvas" doesn't work
**Solution**: This is now fixed. If it still doesn't work:
1. Make sure you processed a P&ID first
2. Check that the Canvas view has data
3. Look for errors in browser console

### Issue: Valve simulation shows "coming soon"
**Solution**: This is now fixed. If you still see it:
1. Clear browser cache
2. Restart the frontend dev server
3. Make sure you're on the latest code

### Issue: Backend API errors
**Solution**:
1. Make sure backend is running on port 8000
2. Check that all Python dependencies are installed
3. Verify the model file exists at `models/yolov8/best.pt`

---

## 📊 Feature Checklist

Use this checklist to verify all features:

### Core Features
- [ ] File upload works
- [ ] Image processing completes
- [ ] Detections appear on canvas
- [ ] Can pan and zoom canvas
- [ ] Can click detections to select

### Advanced Features (All Fixed!)
- [ ] Graph has hierarchical layout (not random)
- [ ] Graph is clearly readable
- [ ] Design Rules loads violations
- [ ] "View on Canvas" navigates correctly
- [ ] "View on Canvas" highlights the right node
- [ ] Flow Simulator trace mode works
- [ ] Flow Simulator valve simulation works
- [ ] Valve dropdown shows valves
- [ ] Simulation shows results
- [ ] All tabs are visible and accessible

### Integration
- [ ] Data Table syncs with Canvas
- [ ] Graph syncs with Data Table
- [ ] State persists across views
- [ ] No console errors
- [ ] Smooth performance

---

## 🎯 Success Criteria

All features are working if:
1. ✅ Graph displays in hierarchical layout (not random)
2. ✅ Design Rules "View on Canvas" navigates and highlights
3. ✅ Flow Simulator valve simulation shows results
4. ✅ All 5 tabs are visible and functional
5. ✅ No errors in browser console
6. ✅ Smooth navigation between views

---

## 📸 Visual Verification

### Graph Viewer Should Look Like:
```
[Equipment] → [Valve] → [Instrument] → [Pump] → [Equipment]
     ↓           ↓           ↓            ↓          ↓
  Clear spacing, left-to-right flow, color-coded
```

### Design Rules Should:
- Show violation cards with severity badges
- Have working "View on Canvas" buttons
- Display affected items
- Show recommendations

### Flow Simulator Should:
- Have two mode buttons at top
- Show appropriate controls for each mode
- Display results in organized cards
- Show affected nodes list

---

## 🎉 All Done!

If all tests pass, your EDAI4 Dashboard is fully functional with:
- ✅ Beautiful hierarchical graph visualization
- ✅ Working design rules navigation
- ✅ Complete valve simulation
- ✅ All advanced features accessible

Enjoy your fully functional P&ID intelligence system! 🚀
