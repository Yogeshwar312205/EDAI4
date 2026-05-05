# HazOp Blank Screen - Troubleshooting Guide

## 🐛 Issue: Blank Screen When Clicking HazOp Tab

If you see a blank screen when clicking the HazOp tab, follow these steps:

---

## ✅ Quick Fix Steps

### Step 1: Check Browser Console (F12)
1. Open browser developer tools (Press **F12**)
2. Go to **Console** tab
3. Look for messages starting with `HazOpSimulatorWrapper`
4. You should see one of these messages:

#### Message 1: "graphData: null or undefined"
**Problem**: Graph data hasn't been loaded yet.

**Solution**:
- Upload a P&ID image first
- Wait for processing to complete
- The graph data loads automatically after upload

#### Message 2: "graphData.nodes: undefined" or "graphData.nodes: object"
**Problem**: Graph data structure is invalid.

**Solution**:
- Re-upload your P&ID
- Check backend logs for errors
- Verify `/api/graph` endpoint is working

#### Message 3: "graphData.nodes.length: 0"
**Problem**: Graph has no nodes (empty).

**Solution**:
- Your P&ID may not have detectable equipment
- Try a different P&ID with clearer symbols
- Check if YOLO detection is working

#### Message 4: "Rendering with X nodes and Y edges"
**Problem**: Component is rendering but still blank.

**Solution**:
- Check for React errors in console
- Verify React Flow CSS is loaded
- Check for conflicting styles

---

## 🔍 Detailed Debugging

### Check 1: Verify Graph Data Exists
Open browser console and type:
```javascript
// Check if graph data is in the store
const store = window.__ZUSTAND_STORE__ || {};
console.log('Graph Data:', store.graphData);
```

### Check 2: Verify API Response
1. Open **Network** tab in DevTools (F12)
2. Look for request to `/api/graph`
3. Check the response:
   - Should have `nodes` array
   - Should have `edges` array
   - Nodes should have `id`, `type`, `data`, `position`

### Check 3: Verify React Flow CSS
Check if this file is loaded:
```
node_modules/reactflow/dist/style.css
```

If not, add to your main CSS file:
```typescript
import 'reactflow/dist/style.css';
```

---

## 🛠️ Manual Fixes

### Fix 1: Force Reload Graph Data
Add this button to your UI temporarily:

```typescript
<button onClick={async () => {
  const graphData = await edaiAPI.getGraph();
  useAppStore.getState().setGraphData(graphData);
  console.log('Graph reloaded:', graphData);
}}>
  Reload Graph
</button>
```

### Fix 2: Use Sample Data
If you don't have a P&ID, use sample data:

```typescript
// In App.tsx or HazOpSimulatorWrapper.tsx
const sampleGraphData = {
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
};

// Use this in HazOpSimulatorWrapper if graphData is null
const dataToUse = graphData || sampleGraphData;
```

### Fix 3: Check Backend is Running
```bash
# Test if backend is running
curl http://localhost:8000/api/health

# Test graph endpoint
curl http://localhost:8000/api/graph
```

---

## 📋 Checklist

Before reporting an issue, verify:

- [ ] Backend server is running (port 8000)
- [ ] Frontend server is running (port 5173)
- [ ] You've uploaded a P&ID image
- [ ] Processing completed successfully
- [ ] Browser console shows no errors
- [ ] Network tab shows `/api/graph` request succeeded
- [ ] Graph data has nodes array with length > 0
- [ ] React Flow CSS is loaded
- [ ] No conflicting CSS styles

---

## 🎯 Expected Behavior

### After Upload:
1. Upload P&ID image
2. Processing completes (shows green checkmark)
3. Graph data loads automatically
4. Click "HazOp" tab
5. See React Flow canvas with nodes and edges
6. Right-click any node to see context menu

### Debug Messages in Console:
```
HazOpSimulatorWrapper - graphData: {nodes: Array(5), edges: Array(4)}
HazOpSimulatorWrapper - nodes: Array(5)
HazOpSimulatorWrapper - edges: Array(4)
HazOpSimulator: Rendering with 5 nodes and 4 edges
```

---

## 🚨 Common Issues

### Issue 1: "Cannot read property 'nodes' of null"
**Cause**: Graph data not loaded
**Fix**: Upload a P&ID first

### Issue 2: "React Flow: Seems like you have not used zustand provider"
**Cause**: Missing ReactFlowProvider wrapper
**Fix**: Already fixed in HazOpSimulatorWrapper.tsx

### Issue 3: Blank white screen, no errors
**Cause**: CSS not loaded or conflicting styles
**Fix**: Check if `reactflow/dist/style.css` is imported

### Issue 4: Nodes appear but can't interact
**Cause**: Event handlers not working
**Fix**: Check if React Flow version is compatible (v11+)

---

## 🔧 Quick Test

Run this in browser console to test the component:
```javascript
// Get the store
const store = window.__ZUSTAND_STORE__;

// Set sample data
store.setGraphData({
  nodes: [
    { id: '1', type: 'default', data: { label: 'Node 1' }, position: { x: 100, y: 100 } },
    { id: '2', type: 'default', data: { label: 'Node 2' }, position: { x: 300, y: 100 } }
  ],
  edges: [
    { id: 'e1', source: '1', target: '2' }
  ]
});

// Switch to HazOp view
store.setActiveView('hazop');
```

---

## 📞 Still Not Working?

If you've tried everything above and it's still blank:

1. **Check the wrapper component output**:
   - You should see a helpful error message
   - It will tell you exactly what's wrong

2. **Share these details**:
   - Browser console output
   - Network tab showing `/api/graph` response
   - Screenshot of the blank screen
   - Output of: `console.log(useAppStore.getState())`

3. **Try the Graph tab first**:
   - Click "Graph" tab
   - If that works, HazOp should work too
   - If Graph tab is also blank, it's a graph data issue

---

## ✅ Solution Applied

I've created `HazOpSimulatorWrapper.tsx` which:
- ✅ Shows helpful error messages instead of blank screen
- ✅ Logs debug info to console
- ✅ Checks all possible failure points
- ✅ Provides clear guidance on what's wrong

**The blank screen should now show a helpful error message!**

---

## 🎉 Success Indicators

You'll know it's working when you see:
1. ✅ React Flow canvas with grid background
2. ✅ Nodes displayed as boxes with labels
3. ✅ Edges connecting nodes
4. ✅ Controls (zoom, pan) in bottom-left
5. ✅ MiniMap in bottom-right
6. ✅ Right-click on node shows context menu

---

**Last Updated**: May 5, 2026  
**Status**: Wrapper component added to diagnose issues
