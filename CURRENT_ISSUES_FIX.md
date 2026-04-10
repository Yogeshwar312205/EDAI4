# 🔧 Current Issues & Fixes

## 🚨 Issues Reported

1. ❌ Graph section not working
2. ❌ Deliverables showing 500 error
3. ❌ Design Rules showing "Process a P&ID first" even after processing
4. ❌ Flow Simulator not working

---

## ✅ Fixes Applied

### Fix 1: Graph Endpoint Fixed
**File:** `src/api/main.py`

**Problem:**
- Edge objects not properly formatted
- Trying to access `.value` on string

**Solution:**
```python
# Added proper edge handling
for edge in state.current_graph.get_all_edges():
    if hasattr(edge, 'source_id'):
        source = edge.source_id
        target = edge.target_id
        edge_type = edge.edge_type.value if hasattr(edge.edge_type, 'value') else edge.edge_type
    else:
        # Handle dict format
        source = edge['source_id']
        target = edge['target_id']
        edge_type = edge['edge_type']
```

### Fix 2: SimpleGraph Class Fixed
**File:** `src/api/main.py`

**Problem:**
- Edges returned as dicts, not objects
- Missing attributes

**Solution:**
```python
# Create proper edge objects
edge_obj = type('Edge', (), {
    'source_id': source,
    'target_id': target,
    'edge_type': edge_data.get('edge_type', 'connected_to')
})()
self.edges.append(edge_obj)
```

---

## 🧪 How to Test the Fixes

### Step 1: Restart Backend

```bash
# Stop current backend (Ctrl+C)
# Start fresh
python -m uvicorn src.api.main:app --reload --port 8000
```

**Look for:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Step 2: Clear Browser Cache

```
1. Open browser (http://localhost:3000)
2. Press Ctrl+Shift+R (hard refresh)
3. Or clear cache in DevTools
```

### Step 3: Upload P&ID Again

```
1. Upload a P&ID image
2. Wait for processing
3. Check backend console for:
   [API] Building graph from hybrid pipeline results...
   [API] Detected X lines/pipes
   [API] Found Y connections
   [API] Graph built: X nodes, Y edges
```

### Step 4: Test Each Feature

**Test Graph:**
```
1. Click "Graph" tab
2. Should see topology visualization
3. Nodes should be draggable
4. Edges should connect nodes
```

**Test Deliverables:**
```
1. Click "Deliverables" tab
2. Enter P&ID reference
3. Click "Generate Excel Deliverables"
4. Should download Excel file (not 500 error)
```

**Test Design Rules:**
```
1. Click "Design Rules" tab
2. Should show summary cards
3. Should show violations or "No violations"
4. NOT "Process a P&ID first" error
```

**Test Flow Simulator:**
```
1. Click "Flow Sim" tab
2. Dropdown should have nodes
3. Select a node
4. Click "Trace Flow Path"
5. Should show results
```

---

## 🐛 If Still Not Working

### Check 1: Backend Console Errors

**Look for:**
```python
# Good signs:
[API] Building graph from hybrid pipeline results...
[API] Detected 156 lines/pipes
[API] Found 87 connections
[API] Graph built: 42 nodes, 87 edges

# Bad signs:
Traceback (most recent call last):
  File "...", line X, in ...
    ...
AttributeError: ...
```

**If you see errors:**
1. Copy the full error message
2. Check which line is failing
3. The error will tell you what's wrong

### Check 2: Frontend Console Errors

**Open DevTools (F12):**
```
1. Go to Console tab
2. Look for red errors
3. Common errors:
   - "Failed to fetch" → Backend not running
   - "500 Internal Server Error" → Backend crash
   - "400 Bad Request" → Graph not loaded
```

### Check 3: Network Tab

**Check API calls:**
```
1. Open DevTools (F12)
2. Go to Network tab
3. Upload P&ID
4. Look for:
   - POST /process → Should be 200 OK
   - GET /graph → Should be 200 OK
   - GET /design-rules/check → Should be 200 OK
   - POST /deliverables/generate → Should be 200 OK
```

---

## 🔍 Detailed Debugging

### Debug Deliverables 500 Error

**Check backend console when you click "Generate":**

**If you see:**
```python
AttributeError: 'SimpleGraph' object has no attribute 'X'
```

**Solution:**
The graph object is missing a method. Check if `state.current_graph` has:
- `nodes` (dict)
- `get_all_nodes()` (method)
- `get_all_edges()` (method)
- `node_count` (property)
- `edge_count` (property)

**If you see:**
```python
KeyError: 'tag'
```

**Solution:**
Some nodes don't have tags. The deliverables generator needs to handle this:
```python
# In deliverables code, use:
tag = node.tag if node.tag else f"UNTAGGED_{node.id}"
```

### Debug Design Rules Error

**If still showing "Process a P&ID first":**

**Check:**
```python
# In backend console after upload:
print(f"Graph loaded: {state.current_graph is not None}")
print(f"Node count: {state.current_graph.node_count if state.current_graph else 0}")
```

**If graph is None:**
- Graph building failed
- Check for errors in graph building section
- Verify line detector ran successfully

**If graph exists but features fail:**
- Graph format might be wrong
- Check if nodes have required attributes
- Verify edges are properly formatted

### Debug Flow Simulator

**If dropdown is empty:**

**Check:**
```python
# In frontend console:
console.log('Processing result:', processingResult);
console.log('Detections:', processingResult?.detections);
```

**If detections is empty:**
- Processing failed
- Check backend console for errors
- Verify image was uploaded correctly

**If dropdown has nodes but trace fails:**

**Check backend console when clicking "Trace":**
```python
# Should see:
[FlowSimulator] Tracing from node_X in direction downstream
[FlowSimulator] Found path with Y nodes
```

**If you see errors:**
- Graph might not have edges
- Nodes might not be connected
- Check graph viewer to verify connections

---

## 📋 Verification Checklist

After applying fixes, verify:

- [ ] Backend starts without errors
- [ ] Upload P&ID successfully
- [ ] See graph building messages in console
- [ ] Graph tab shows visualization
- [ ] Deliverables generates Excel (no 500 error)
- [ ] Design Rules shows results (no "Process P&ID" error)
- [ ] Flow Sim dropdown has nodes
- [ ] Flow Sim traces paths successfully
- [ ] No errors in backend console
- [ ] No errors in browser console

---

## 🆘 Emergency Debugging

### If Everything Fails

**1. Check if graph is actually built:**
```bash
# In backend console after upload, add this temporarily:
print("=" * 80)
print("GRAPH DEBUG")
print(f"Graph exists: {state.current_graph is not None}")
if state.current_graph:
    print(f"Nodes: {state.current_graph.node_count}")
    print(f"Edges: {state.current_graph.edge_count}")
    print(f"Node IDs: {list(state.current_graph.nodes.keys())[:5]}")
print("=" * 80)
```

**2. Test graph endpoint directly:**
```bash
# After uploading P&ID:
curl http://localhost:8000/graph
```

**Should return:**
```json
{
  "nodes": [
    {"id": "node_0", "type": "instrument", "tag": "FT-101", ...},
    ...
  ],
  "edges": [
    {"source": "node_0", "target": "node_1", "type": "connected_to"},
    ...
  ]
}
```

**3. Test deliverables endpoint directly:**
```bash
curl -X POST http://localhost:8000/deliverables/generate \
  -F "pid_reference=TEST-001" \
  -F "plc_name=PLC-001" \
  --output test.xlsx
```

**Should:**
- Return 200 OK
- Download Excel file
- NOT return 500 error

---

## 📞 What to Report

If still not working, provide:

**1. Backend Console Output:**
```
Copy everything from:
- "HYBRID PIPELINE COMPLETE" section
- "[API] Building graph..." section
- Any error messages
```

**2. Browser Console Errors:**
```
Press F12 → Console tab
Copy any red error messages
```

**3. Network Tab:**
```
Press F12 → Network tab
Click failing feature
Copy the failed request details
```

**4. What You Tried:**
```
- Restarted backend? Yes/No
- Cleared browser cache? Yes/No
- Re-uploaded P&ID? Yes/No
- Checked console for errors? Yes/No
```

---

## ✅ Expected Behavior After Fixes

### Graph Tab
```
✅ Shows topology visualization
✅ Nodes are draggable
✅ Edges connect nodes
✅ Can zoom and pan
✅ No errors
```

### Deliverables Tab
```
✅ Form appears
✅ Can enter P&ID reference
✅ Click "Generate" → Excel downloads
✅ Excel has 3 tabs with data
✅ No 500 error
```

### Design Rules Tab
```
✅ Summary cards show counts
✅ Shows violations or "No violations"
✅ Can filter by severity
✅ NOT "Process a P&ID first" error
```

### Flow Simulator Tab
```
✅ Dropdown has nodes
✅ Can select node
✅ Can choose direction
✅ Click "Trace" → Shows results
✅ Path nodes list appears
```

---

**Status**: 🔧 Fixes Applied
**Next Step**: Restart backend and test
**Expected**: All features working

🎯 **Follow the testing steps above to verify fixes!**
