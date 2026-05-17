# 🐛 Debug: Flow Simulator Not Running

**Issue:** Clicking "Run Simulation" does nothing  
**Status:** 🔍 **DEBUGGING**

---

## 🔍 Debugging Steps

### Step 1: Check Browser Console

1. Open DevTools (F12)
2. Go to Console tab
3. Click "Run Simulation"
4. Look for console logs:

**Expected logs:**
```
Starting simulation... { startNodeId: 'Tank-101', closedValves: ['V-102'] }
Simulation request: { topology: {...}, start_node_id: 'Tank-101', ... }
Simulation success: { active_node_ids: [...], ... }
```

**If you see:**
```
Cannot run simulation: { startNodeId: null, hasGraphData: true }
```
→ **Problem:** No source node selected

**If you see:**
```
Cannot run simulation: { startNodeId: 'Tank-101', hasGraphData: false }
```
→ **Problem:** No graph data loaded

**If you see:**
```
Flow simulation error: ...
```
→ **Problem:** API error (check error message)

---

### Step 2: Check Network Tab

1. Open DevTools (F12)
2. Go to Network tab
3. Click "Run Simulation"
4. Look for request to `/api/api/simulate-flow`

**If no request appears:**
- Button might be disabled
- JavaScript error preventing execution
- Check console for errors

**If request shows 404:**
- Backend endpoint not found
- Check backend is running
- Check endpoint exists at `/api/simulate-flow`

**If request shows 500:**
- Backend error
- Check backend logs
- Check request payload is valid

**If request shows 200:**
- Success! Check response data
- If response is empty, check backend logic

---

### Step 3: Check Button State

**Is the button disabled?**

The button is disabled if:
- No source node selected (`!startNodeId`)
- Simulation is running (`isSimulating`)

**Check:**
1. Have you selected a source node from the dropdown?
2. Is the dropdown showing any nodes?
3. Is the button grayed out?

---

### Step 4: Check Graph Data

**Open React DevTools:**
1. Install React DevTools extension
2. Open DevTools → Components tab
3. Find `InteractiveFlowSimulator` component
4. Check props/state:
   - `graphData`: Should have `nodes` and `edges` arrays
   - `startNodeId`: Should be a string (node ID)
   - `closedValves`: Should be a Set
   - `isSimulating`: Should be false when idle

---

### Step 5: Check Backend

**Is the backend running?**
```bash
# Check if backend is responding
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","timestamp":"..."}
```

**Does the endpoint exist?**
```bash
# Check API docs
open http://localhost:8000/docs

# Look for: POST /api/simulate-flow
```

**Test endpoint directly:**
```bash
curl -X POST http://localhost:8000/api/simulate-flow \
  -H "Content-Type: application/json" \
  -d '{
    "topology": {
      "nodes": [{"id": "A", "type": "tank", "x": 0, "y": 0}],
      "edges": []
    },
    "start_node_id": "A",
    "closed_valve_ids": []
  }'

# Should return JSON with active_node_ids, etc.
```

---

## 🔧 Common Issues & Fixes

### Issue 1: Button is Disabled

**Symptoms:**
- Button is grayed out
- Can't click it

**Causes:**
1. No source node selected
2. No graph data loaded
3. Simulation already running

**Fix:**
1. Select a source node from dropdown
2. Ensure P&ID image was processed
3. Wait for previous simulation to complete

---

### Issue 2: No Nodes in Dropdown

**Symptoms:**
- Source node dropdown is empty
- Shows "Select source node..." but no options

**Causes:**
- Graph data not loaded
- No nodes detected in P&ID

**Fix:**
1. Upload and process a P&ID image first
2. Check Canvas or Graph tab to see if nodes exist
3. Check browser console for errors

---

### Issue 3: Silent Failure

**Symptoms:**
- Button clicks but nothing happens
- No console logs
- No network requests

**Causes:**
- JavaScript error preventing execution
- Event handler not attached
- React component not rendering

**Fix:**
1. Check browser console for errors
2. Hard refresh browser (Ctrl+Shift+R)
3. Restart frontend dev server

---

### Issue 4: API Error

**Symptoms:**
- Console shows "Flow simulation error"
- Network tab shows 400/500 error

**Causes:**
- Invalid request payload
- Backend validation error
- Backend crash

**Fix:**
1. Check error message in console
2. Check backend logs
3. Verify request payload format

---

## 📋 Checklist

Before reporting issue:
- [ ] P&ID image uploaded and processed
- [ ] Graph data loaded (check Graph tab)
- [ ] Source node selected from dropdown
- [ ] Button is not disabled (not grayed out)
- [ ] Browser console checked for errors
- [ ] Network tab checked for requests
- [ ] Backend is running (check health endpoint)
- [ ] Frontend dev server restarted
- [ ] Browser cache cleared (hard refresh)

---

## 🧪 Test Procedure

### Minimal Test

1. **Upload P&ID:**
   - Go to home page
   - Upload a P&ID image
   - Wait for processing to complete

2. **Check Graph:**
   - Click "Graph" tab
   - Verify nodes and edges are visible
   - Note down a node ID (e.g., "Tank-101")

3. **Go to Flow Sim:**
   - Click "Flow Sim" tab
   - Check if dropdown has nodes

4. **Select Source:**
   - Open "Flow Source Node" dropdown
   - Select any node (e.g., "Tank-101")

5. **Run Simulation:**
   - Click "Run Simulation" button
   - Check console for logs
   - Check Network tab for request
   - Check for results display

---

## 🔍 Expected Behavior

### When Working Correctly

**Console logs:**
```
Starting simulation... { startNodeId: 'Tank-101', closedValves: [] }
Simulation request: { topology: { nodes: [...], edges: [...] }, ... }
Simulation success: { active_node_ids: [...], active_edge_ids: [...], ... }
```

**Network tab:**
```
POST /api/api/simulate-flow
Status: 200 OK
Response: { "active_node_ids": [...], ... }
```

**UI:**
- Button shows "Simulating..." briefly
- Results section shows flow path
- Statistics cards update
- No errors displayed

---

## 🆘 Still Not Working?

### Collect Debug Info

1. **Browser Console Output:**
   - Copy all console logs
   - Include errors and warnings

2. **Network Request:**
   - Copy request URL
   - Copy request payload
   - Copy response (if any)

3. **Backend Logs:**
   - Copy relevant backend logs
   - Include any errors or stack traces

4. **Component State:**
   - Use React DevTools
   - Copy `graphData`, `startNodeId`, `closedValves`

5. **Environment:**
   - Browser version
   - Frontend dev server running?
   - Backend server running?
   - Any proxy/firewall?

---

## 🎯 Quick Fixes to Try

### Fix 1: Complete Restart
```bash
# Stop both servers (Ctrl+C)

# Backend
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
rm -rf node_modules/.vite dist
npm run dev

# Hard refresh browser
# Ctrl+Shift+R
```

### Fix 2: Check File Changes
```bash
# Verify InteractiveFlowSimulator has console.log statements
grep "console.log" frontend/src/components/InteractiveFlowSimulator.tsx

# Should show multiple console.log lines
```

### Fix 3: Test Backend Directly
```bash
# Test the endpoint
curl -X POST http://localhost:8000/api/simulate-flow \
  -H "Content-Type: application/json" \
  -d '{"topology":{"nodes":[{"id":"A","type":"tank","x":0,"y":0}],"edges":[]},"start_node_id":"A","closed_valve_ids":[]}'

# Should return JSON, not 404
```

---

**Version:** 1.0.0  
**Last Updated:** 2026-05-17

**Check console logs first!** 🔍
