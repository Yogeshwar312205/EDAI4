# 🔧 Troubleshooting: Flow Simulator Still Getting 404

**Issue:** After fixing the code, still seeing `POST /simulate-flow HTTP/1.1 404 Not Found`  
**Status:** ⚠️ **NEEDS FRONTEND RESTART**

---

## ✅ Code is Fixed

The code has been correctly updated:
- ✅ Import changed from `axios` to `api`
- ✅ API call changed to use `api.post()`
- ✅ Backend endpoint exists at `/api/simulate-flow`

**But the browser is still using the old cached code!**

---

## 🔄 Solution: Restart Frontend Dev Server

### Step 1: Stop Frontend Server
Press `Ctrl+C` in the terminal running the frontend

### Step 2: Clear Node Cache (Optional but Recommended)
```bash
cd frontend
rm -rf node_modules/.vite
```

### Step 3: Restart Frontend Server
```bash
cd frontend
npm run dev
```

### Step 4: Hard Refresh Browser
- **Windows/Linux:** `Ctrl + Shift + R` or `Ctrl + F5`
- **Mac:** `Cmd + Shift + R`

Or:
- Open DevTools (F12)
- Right-click the refresh button
- Select "Empty Cache and Hard Reload"

---

## 🧪 Verify the Fix

### 1. Check Browser Network Tab
1. Open DevTools (F12)
2. Go to Network tab
3. Click "Run Simulation" in Flow Sim tab
4. Look for the request

**Before Fix:**
```
POST /simulate-flow HTTP/1.1
Status: 404 Not Found
```

**After Fix:**
```
POST /api/simulate-flow HTTP/1.1
Status: 200 OK
```

### 2. Check Request URL
In the Network tab, click on the request and check:
- **Request URL:** Should be `http://localhost:5173/api/simulate-flow`
- **Status Code:** Should be `200 OK`
- **Response:** Should contain JSON with `active_node_ids`, etc.

### 3. Check Backend Logs
Should see:
```
INFO: 127.0.0.1:xxxxx - "POST /api/simulate-flow HTTP/1.1" 200 OK
```

---

## 🐛 If Still Not Working

### Check 1: Verify File Changes
```bash
# Check the import
grep "import api from" frontend/src/components/InteractiveFlowSimulator.tsx

# Should output:
# import api from '@/lib/api';
```

```bash
# Check the API call
grep "api.post" frontend/src/components/InteractiveFlowSimulator.tsx

# Should output:
# const response = await api.post<FlowSimulationResponse>(
```

### Check 2: Verify Backend is Running
```bash
# Test the endpoint directly
curl -X POST http://localhost:8000/api/simulate-flow \
  -H "Content-Type: application/json" \
  -d '{
    "topology": {
      "nodes": [
        {"id": "A", "type": "tank", "x": 0, "y": 0}
      ],
      "edges": []
    },
    "start_node_id": "A",
    "closed_valve_ids": []
  }'
```

Should return JSON response, not 404.

### Check 3: Check Vite Config
Verify proxy is configured in `frontend/vite.config.ts`:

```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

### Check 4: Clear All Caches
```bash
# Stop frontend
# Ctrl+C

# Clear all caches
cd frontend
rm -rf node_modules/.vite
rm -rf dist

# Restart
npm run dev
```

### Check 5: Check Browser Console
Open browser console (F12 → Console tab) and look for errors:
- CORS errors
- Network errors
- TypeScript errors

---

## 📋 Complete Restart Procedure

If nothing else works, do a complete restart:

```bash
# 1. Stop both servers
# Press Ctrl+C in both terminals

# 2. Backend restart
cd /path/to/EDAI4
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload --port 8000

# 3. Frontend restart (in new terminal)
cd /path/to/EDAI4/frontend
rm -rf node_modules/.vite
npm run dev

# 4. Hard refresh browser
# Ctrl+Shift+R or Cmd+Shift+R
```

---

## 🎯 Expected Behavior After Fix

### Flow Sim Tab
1. Select source node: "Tank-101"
2. Toggle valve: Click V-101 → CLOSED
3. Click "Run Simulation"
4. **Should see:**
   - ✅ Success message
   - ✅ Flow path displayed
   - ✅ Statistics updated
   - ✅ No errors in console

### Graph Tab
1. Switch to Graph tab
2. **Should see:**
   - ✅ "Flow Simulation Active" badge
   - ✅ Green animated edges
   - ✅ Green glowing nodes
   - ✅ Red glowing blocked valves
   - ✅ Dimmed inactive elements

### Backend Logs
```
INFO: 127.0.0.1:xxxxx - "POST /api/simulate-flow HTTP/1.1" 200 OK
```

### Browser Network Tab
```
Request URL: http://localhost:5173/api/simulate-flow
Status: 200 OK
Response: {
  "active_node_ids": [...],
  "active_edge_ids": [...],
  "blocked_nodes": [...],
  ...
}
```

---

## 🔍 Why This Happens

### Vite Dev Server Caching
Vite (the frontend build tool) caches compiled modules for faster reloads. Sometimes it doesn't detect changes properly, especially with:
- Import statement changes
- Dependency changes
- Configuration changes

### Browser Caching
Browsers cache JavaScript files aggressively. Even with hot module replacement (HMR), sometimes the old code persists.

### Solution
A hard restart clears all caches and forces recompilation.

---

## ✅ Checklist

Before reporting the issue:
- [ ] Stopped frontend dev server
- [ ] Cleared Vite cache (`rm -rf node_modules/.vite`)
- [ ] Restarted frontend dev server
- [ ] Hard refreshed browser (Ctrl+Shift+R)
- [ ] Checked Network tab for correct URL
- [ ] Checked backend logs for 200 OK
- [ ] Verified file changes are saved
- [ ] Checked browser console for errors

---

## 📞 Still Having Issues?

If you've tried everything above and it still doesn't work:

1. **Check the file was saved:**
   ```bash
   cat frontend/src/components/InteractiveFlowSimulator.tsx | grep "import api"
   ```
   Should show: `import api from '@/lib/api';`

2. **Check for TypeScript errors:**
   ```bash
   cd frontend
   npm run build
   ```
   Look for any compilation errors

3. **Check backend endpoint exists:**
   ```bash
   curl http://localhost:8000/docs
   ```
   Look for `/api/simulate-flow` in the API docs

4. **Try a different browser:**
   Sometimes browser extensions or settings cause issues

5. **Check firewall/antivirus:**
   Make sure they're not blocking the requests

---

## 🎉 Success Indicators

You'll know it's working when:
- ✅ Network tab shows `POST /api/simulate-flow` with `200 OK`
- ✅ Backend logs show `POST /api/simulate-flow HTTP/1.1 200 OK`
- ✅ Flow Sim tab shows simulation results
- ✅ Graph tab shows animated flow visualization
- ✅ No errors in browser console

---

**TL;DR: Restart the frontend dev server and hard refresh your browser!** 🔄

---

**Version:** 1.0.0  
**Last Updated:** 2026-05-17

**Restart and it will work!** 🚀
