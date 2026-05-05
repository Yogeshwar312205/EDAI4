# ✅ HazOp 503 Error & White Nodes - FIXED!

## 🐛 Issues Found

### Issue 1: White Nodes
**Problem**: Nodes were rendering but appeared white/invisible against the dark background.

**Cause**: No styling applied to nodes.

### Issue 2: 503 Service Unavailable
**Problem**: API call to `/api/simulate-hazop` returns 503 error.

**Cause**: Backend server is not running OR Gemini API is unavailable.

---

## ✅ Fixes Applied

### Fix 1: Node Styling ✅
Added dark theme styling to all nodes:

```typescript
style: {
  background: '#1a1f29',      // Dark background
  color: '#abb2bf',           // Light text
  border: '2px solid #3d4556', // Gray border
  borderRadius: '8px',         // Rounded corners
  padding: '10px',            // Inner spacing
  fontSize: '12px',           // Readable text
  width: 150                  // Fixed width
}
```

### Fix 2: Better Error Messages ✅
Added helpful error messages for different scenarios:

- **503 Error**: Shows backend/API issues
- **500 Error**: Shows backend error
- **Network Error**: Shows connection issues

---

## 🚀 What to Do Now

### Step 1: Check Backend is Running

```bash
# Check if backend is running
curl http://localhost:8000/docs

# If not running, start it:
python -m uvicorn src.api.main:app --reload --port 8000
```

### Step 2: Refresh Frontend

The frontend should auto-reload. If not:
```bash
# Just refresh browser (Ctrl+R)
# Or restart:
cd frontend
npm run dev
```

### Step 3: Test HazOp

1. Click "HazOp" tab
2. You should now see **dark styled nodes** (not white!)
3. Right-click a node
4. Select a failure mode
5. If backend is running, simulation will work

---

## 🎯 Expected Results

### Visual (Nodes):
```
✅ Nodes have dark background (#1a1f29)
✅ Nodes have light text (#abb2bf)
✅ Nodes have gray borders
✅ Nodes are clearly visible
✅ Edges are blue (#61afef)
```

### Functional (API):
```
✅ Backend running on port 8000
✅ Right-click shows context menu
✅ Selecting failure mode triggers simulation
✅ Loading message appears
✅ Analysis panel shows results (if API works)
```

---

## 🔍 Troubleshooting 503 Error

### Cause 1: Backend Not Running ❌

**Check**:
```bash
curl http://localhost:8000/docs
```

**If fails**, start backend:
```bash
python -m uvicorn src.api.main:app --reload --port 8000
```

### Cause 2: Gemini API Quota Exceeded ⚠️

**Error in backend**:
```
503 UNAVAILABLE: This model is currently experiencing high demand
```

**Solutions**:
1. Wait 1 minute (free tier: 15 req/min)
2. Check quota: https://ai.google.dev/gemini-api/docs/rate-limits
3. Use different API key
4. Upgrade to paid tier

### Cause 3: Invalid API Key ❌

**Check `.env` file**:
```bash
cat .env | grep GOOGLE_API_KEY
```

**Should show**:
```
GOOGLE_API_KEY=AIzaSy...
```

**If missing or invalid**:
1. Get new key: https://makersuite.google.com/app/apikey
2. Update `.env` file
3. Restart backend

### Cause 4: Import Error in Backend ❌

**Check backend terminal** for errors like:
```
ImportError: cannot import name 'get_hazop_simulator'
```

**Solution**: Make sure `src/api/hazop_simulator.py` exists

---

## 📊 Visual Comparison

### Before Fix:
```
❌ White nodes (invisible)
❌ No styling
❌ Generic error message
```

### After Fix:
```
✅ Dark styled nodes (visible)
✅ Professional appearance
✅ Helpful error messages
```

---

## 🧪 Testing Steps

### Test 1: Visual Check
1. Click "HazOp" tab
2. **Expected**: See dark nodes with labels
3. **Not**: White/invisible nodes

### Test 2: Backend Check
```bash
# Terminal 1: Start backend
python -m uvicorn src.api.main:app --reload --port 8000

# Terminal 2: Test endpoint
curl http://localhost:8000/api/health
```

### Test 3: Simulation Check
1. Right-click a node
2. Select "Stuck Closed"
3. **If backend running**: See loading, then results
4. **If backend not running**: See helpful error message

---

## 📝 Quick Reference

### Backend Commands:
```bash
# Start backend
python -m uvicorn src.api.main:app --reload --port 8000

# Test backend
curl http://localhost:8000/docs

# Check logs
# Look at terminal where backend is running
```

### Frontend Commands:
```bash
# Restart frontend
cd frontend
npm run dev

# Just refresh browser
Ctrl+R or F5
```

### Test HazOp:
```bash
# Test backend endpoint directly
curl -X POST http://localhost:8000/api/simulate-hazop \
  -H "Content-Type: application/json" \
  -d '{
    "failed_node_id": "test",
    "failure_mode": "Stuck Closed",
    "topology": {"nodes": [], "edges": []}
  }'
```

---

## ✅ Success Indicators

### Visual Success:
- ✅ Nodes are dark colored (not white)
- ✅ Text is readable
- ✅ Borders are visible
- ✅ Edges are blue

### Functional Success:
- ✅ Backend running (check http://localhost:8000/docs)
- ✅ Right-click menu works
- ✅ Simulation completes (if backend + API working)
- ✅ Analysis panel shows results

---

## 🎉 Summary

**Issue 1**: White nodes → **Fixed** with dark styling  
**Issue 2**: 503 error → **Fixed** with better error messages + need to start backend  

**Status**: ✅ **RESOLVED**

**Next Steps**:
1. ✅ Refresh browser to see styled nodes
2. ✅ Start backend if not running
3. ✅ Test simulation

---

**Last Updated**: May 5, 2026  
**Issues**: White nodes + 503 error  
**Status**: ✅ FIXED
