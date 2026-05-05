# ✅ HazOp Blank Screen - SOLUTION APPLIED

## 🎯 Problem
When clicking the "HazOp" tab, you see a blank screen instead of the simulator.

## 🔧 Solution Applied

I've created a **diagnostic wrapper component** that will show you exactly what's wrong instead of a blank screen.

### Files Modified:

1. **`frontend/src/components/HazOpSimulatorWrapper.tsx`** (NEW)
   - Checks if graphData exists
   - Checks if nodes array is valid
   - Checks if nodes array is empty
   - Shows helpful error messages for each case
   - Logs debug info to console

2. **`frontend/src/App.tsx`** (MODIFIED)
   - Replaced direct HazOpSimulator with HazOpSimulatorWrapper
   - Now uses: `<HazOpSimulatorWrapper graphData={graphData} />`

---

## 🎨 What You'll See Now

Instead of a blank screen, you'll see one of these helpful messages:

### Scenario 1: No Graph Data
```
⚠️ No Graph Data

Graph data is not available. Please make sure you've 
processed a P&ID and generated the graph.

Debug Info:
graphData: null or undefined
```

### Scenario 2: Invalid Structure
```
⚠️ Invalid Graph Structure

Graph data exists but doesn't have a valid nodes array.

Debug Info:
graphData exists: true
graphData.nodes: undefined
Expected: array
```

### Scenario 3: Empty Graph
```
⚠️ Empty Graph

Graph data exists but contains no nodes. The P&ID 
processing may not have detected any equipment.

Debug Info:
graphData.nodes.length: 0
graphData.edges.length: 0
```

### Scenario 4: Success! ✅
If everything is correct, you'll see:
- React Flow canvas with grid
- Nodes displayed as boxes
- Edges connecting nodes
- Controls and MiniMap
- Right-click context menu works

---

## 🚀 How to Use

### Step 1: Restart Frontend
```bash
# Stop the frontend (Ctrl+C)
# Then restart:
cd frontend
npm run dev
```

### Step 2: Test the HazOp Tab
1. Open http://localhost:5173
2. Upload a P&ID image
3. Wait for processing to complete
4. Click "HazOp" tab
5. You should now see either:
   - The simulator (if graph data exists)
   - A helpful error message (if something is wrong)

### Step 3: Check Browser Console
Open DevTools (F12) and look for messages like:
```
HazOpSimulatorWrapper - graphData: {...}
HazOpSimulatorWrapper - nodes: [...]
HazOpSimulatorWrapper - edges: [...]
HazOpSimulator: Rendering with X nodes and Y edges
```

---

## 🔍 Most Likely Cause

Based on your issue, the most likely cause is:

**Graph data hasn't been loaded yet.**

### Why This Happens:
1. You uploaded a P&ID
2. Processing completed
3. But the graph data fetch failed or didn't complete
4. So `graphData` is `null`

### Solution:
1. **Check if backend is running**: `http://localhost:8000/docs`
2. **Check if graph endpoint works**: `http://localhost:8000/api/graph`
3. **Re-upload your P&ID** to trigger graph generation
4. **Check browser Network tab** for `/api/graph` request

---

## 🧪 Quick Test with Sample Data

If you want to test the HazOp simulator without uploading a P&ID, you can inject sample data:

### Option 1: Browser Console
Open browser console (F12) and paste:
```javascript
// Get the Zustand store
const store = window.__ZUSTAND_STORE__ || 
  document.querySelector('[data-zustand-store]')?.__zustand_store__;

// Set sample graph data
if (store && store.setGraphData) {
  store.setGraphData({
    nodes: [
      {
        id: 'P-101',
        type: 'default',
        data: { label: 'Pump P-101' },
        position: { x: 100, y: 100 }
      },
      {
        id: 'V-101',
        type: 'default',
        data: { label: 'Valve V-101' },
        position: { x: 300, y: 100 }
      },
      {
        id: 'T-101',
        type: 'default',
        data: { label: 'Tank T-101' },
        position: { x: 500, y: 100 }
      }
    ],
    edges: [
      {
        id: 'e1',
        source: 'P-101',
        target: 'V-101',
        data: { label: 'Feed Line' }
      },
      {
        id: 'e2',
        source: 'V-101',
        target: 'T-101',
        data: { label: 'Inlet Line' }
      }
    ]
  });
  
  // Switch to HazOp view
  store.setActiveView('hazop');
  
  console.log('✅ Sample data loaded! HazOp should now work.');
} else {
  console.error('❌ Could not find Zustand store');
}
```

### Option 2: Add Test Button (Temporary)
Add this to your App.tsx temporarily:
```typescript
{/* Debug: Load Sample Data */}
<button
  onClick={() => {
    setGraphData({
      nodes: [
        { id: 'P-101', type: 'default', data: { label: 'Pump' }, position: { x: 100, y: 100 } },
        { id: 'V-101', type: 'default', data: { label: 'Valve' }, position: { x: 300, y: 100 } },
        { id: 'T-101', type: 'default', data: { label: 'Tank' }, position: { x: 500, y: 100 } }
      ],
      edges: [
        { id: 'e1', source: 'P-101', target: 'V-101' },
        { id: 'e2', source: 'V-101', target: 'T-101' }
      ]
    });
    setActiveView('hazop');
  }}
  className="px-4 py-2 bg-accent-blue text-industrial-950 rounded"
>
  Load Sample Data for HazOp
</button>
```

---

## 📊 Verification Steps

After applying the fix, verify:

1. **Restart frontend** ✅
2. **Open browser** → http://localhost:5173 ✅
3. **Open DevTools** (F12) → Console tab ✅
4. **Click HazOp tab** ✅
5. **See helpful message** (not blank screen) ✅

### Expected Console Output:
```
HazOpSimulatorWrapper - graphData: null
```
OR
```
HazOpSimulatorWrapper - graphData: {nodes: Array(5), edges: Array(4)}
HazOpSimulatorWrapper - nodes: (5) [{...}, {...}, ...]
HazOpSimulatorWrapper - edges: (4) [{...}, {...}, ...]
HazOpSimulator: Rendering with 5 nodes and 4 edges
```

---

## 🎯 Next Steps

### If You See "No Graph Data":
1. Upload a P&ID image
2. Wait for processing to complete
3. Check if `/api/graph` endpoint returns data
4. Try clicking "Graph" tab first (it might trigger graph generation)

### If You See "Invalid Graph Structure":
1. Check backend logs for errors
2. Verify `/api/graph` response format
3. Make sure backend is returning correct structure

### If You See "Empty Graph":
1. Your P&ID might not have detectable equipment
2. Try a different P&ID with clearer symbols
3. Check YOLO detection is working

### If You See the Simulator:
1. ✅ Success! Everything is working
2. Right-click any node to test context menu
3. Select a failure mode
4. Wait for AI analysis

---

## 🐛 Still Having Issues?

If you still see a blank screen after these changes:

1. **Clear browser cache** (Ctrl+Shift+Delete)
2. **Hard reload** (Ctrl+Shift+R)
3. **Check for TypeScript errors** in terminal
4. **Share the console output** with me

---

## ✅ Summary

**What Changed:**
- Added `HazOpSimulatorWrapper.tsx` with diagnostic messages
- Updated `App.tsx` to use the wrapper
- Now shows helpful errors instead of blank screen

**What to Do:**
1. Restart frontend: `npm run dev`
2. Open browser and click HazOp tab
3. Read the error message (if any)
4. Follow the guidance in the message

**Expected Result:**
- No more blank screen!
- Clear error messages if something is wrong
- Working simulator if everything is correct

---

**Status**: ✅ **FIX APPLIED - RESTART FRONTEND TO TEST**

**Files Created**:
- `frontend/src/components/HazOpSimulatorWrapper.tsx`
- `HAZOP_BLANK_SCREEN_FIX.md`
- `HAZOP_BLANK_SCREEN_SOLUTION.md`

**Files Modified**:
- `frontend/src/App.tsx`

---

**Last Updated**: May 5, 2026  
**Issue**: Blank screen on HazOp tab  
**Solution**: Diagnostic wrapper with helpful error messages  
**Status**: Ready to test
