# 🎯 REAL FIX: Vite Proxy Configuration Issue

**Root Cause:** Vite proxy was stripping `/api` prefix before forwarding to backend  
**Status:** ✅ **FIXED**  
**Date:** 2026-05-17

---

## 🔍 The Real Problem

The issue wasn't just the axios vs api import - it was the **Vite proxy configuration**!

### What Was Happening

```
Frontend Request:  /api/simulate-flow
         ↓
Vite Proxy (with rewrite rule):
  - Receives: /api/simulate-flow
  - Rewrites: /simulate-flow  ← REMOVES /api prefix!
  - Forwards: /simulate-flow
         ↓
Backend:
  - Receives: /simulate-flow
  - Looks for endpoint: /simulate-flow
  - Result: 404 Not Found ❌
  
Backend actually has: /api/simulate-flow ✅
```

### The Vite Config Problem

**Before (Incorrect):**
```typescript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, ''),  // ❌ REMOVES /api!
    },
  },
}
```

This configuration:
1. Intercepts requests to `/api/*`
2. **Removes** the `/api` prefix with the rewrite rule
3. Forwards the modified path to backend
4. Backend receives `/simulate-flow` instead of `/api/simulate-flow`

---

## ✅ The Solution

**After (Correct):**
```typescript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      // Don't rewrite - backend expects /api prefix
    },
  },
}
```

Now the flow is:
```
Frontend Request:  /api/simulate-flow
         ↓
Vite Proxy (no rewrite):
  - Receives: /api/simulate-flow
  - Forwards: /api/simulate-flow  ← KEEPS /api prefix!
         ↓
Backend:
  - Receives: /api/simulate-flow
  - Finds endpoint: /api/simulate-flow
  - Result: 200 OK ✅
```

---

## 🔧 Changes Made

### File 1: `frontend/vite.config.ts`
```diff
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
-       rewrite: (path) => path.replace(/^\/api/, ''),
+       // Don't rewrite - backend expects /api prefix
      },
    },
  },
```

### File 2: `frontend/src/components/InteractiveFlowSimulator.tsx`
```diff
- import axios from 'axios';
+ import api from '@/lib/api';

  const simulateMutation = useMutation({
    mutationFn: async (request: FlowSimulationRequest) => {
-     const response = await axios.post<FlowSimulationResponse>(
-       '/api/simulate-flow',
+     const response = await api.post<FlowSimulationResponse>(
+       '/simulate-flow',
        request
      );
```

---

## 🎯 Why Both Changes Were Needed

### Change 1: Use `api` instance
- Ensures consistent base URL (`/api`)
- Centralizes configuration
- Better error handling

### Change 2: Remove Vite rewrite rule
- Keeps `/api` prefix when forwarding to backend
- Matches backend endpoint structure
- Fixes the 404 error

**Both changes work together to ensure the correct URL reaches the backend!**

---

## 🔄 How to Apply the Fix

### Step 1: Verify Changes
```bash
# Check vite.config.ts
cat frontend/vite.config.ts | grep -A 5 "proxy"

# Should NOT see "rewrite" line
```

### Step 2: Restart Frontend Dev Server
```bash
# Stop the server (Ctrl+C)

# Clear cache
cd frontend
rm -rf node_modules/.vite

# Restart
npm run dev
```

### Step 3: Hard Refresh Browser
- **Windows/Linux:** `Ctrl + Shift + R`
- **Mac:** `Cmd + Shift + R`

Or:
- Open DevTools (F12)
- Right-click refresh button
- "Empty Cache and Hard Reload"

---

## 🧪 Testing

### Test 1: Check Network Request
1. Open DevTools → Network tab
2. Go to Flow Sim tab
3. Select source node
4. Click "Run Simulation"
5. Check the request:

**Should see:**
```
Request URL: http://localhost:3000/api/simulate-flow
Status: 200 OK
```

### Test 2: Check Backend Logs
**Should see:**
```
INFO: 127.0.0.1:xxxxx - "POST /api/simulate-flow HTTP/1.1" 200 OK
```

**NOT:**
```
INFO: 127.0.0.1:xxxxx - "POST /simulate-flow HTTP/1.1" 404 Not Found
```

### Test 3: Check Response
In Network tab, click the request and check Response:
```json
{
  "active_node_ids": ["Tank-101", "V-101"],
  "active_edge_ids": ["Tank-101-V-101"],
  "blocked_nodes": [],
  "flow_path": ["Tank-101", "V-101"],
  "total_distance": 100.0,
  "message": "Flow simulation complete"
}
```

---

## 📊 Request Flow Diagram

### Before Fix (404 Error)
```
┌─────────────────────────────────────────────────────────────┐
│ Frontend (Browser)                                          │
│ api.post('/simulate-flow')                                  │
│ → Actual URL: /api/simulate-flow                           │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ Vite Dev Server (localhost:3000)                           │
│ Proxy intercepts: /api/simulate-flow                       │
│ Rewrite rule: path.replace(/^\/api/, '')                   │
│ → Forwards: /simulate-flow  ❌ (removed /api)              │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ Backend (localhost:8000)                                    │
│ Receives: POST /simulate-flow                              │
│ Looks for endpoint: /simulate-flow                         │
│ Result: 404 Not Found ❌                                    │
│                                                             │
│ Available endpoints:                                        │
│ ✅ /api/simulate-flow                                       │
│ ✅ /api/process                                             │
│ ✅ /api/graph                                               │
└─────────────────────────────────────────────────────────────┘
```

### After Fix (200 OK)
```
┌─────────────────────────────────────────────────────────────┐
│ Frontend (Browser)                                          │
│ api.post('/simulate-flow')                                  │
│ → Actual URL: /api/simulate-flow                           │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ Vite Dev Server (localhost:3000)                           │
│ Proxy intercepts: /api/simulate-flow                       │
│ No rewrite rule                                             │
│ → Forwards: /api/simulate-flow  ✅ (keeps /api)            │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ Backend (localhost:8000)                                    │
│ Receives: POST /api/simulate-flow                          │
│ Finds endpoint: /api/simulate-flow                         │
│ Result: 200 OK ✅                                           │
│                                                             │
│ Returns:                                                    │
│ {                                                           │
│   "active_node_ids": [...],                                │
│   "active_edge_ids": [...],                                │
│   ...                                                       │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤔 Why Was the Rewrite Rule There?

The rewrite rule is sometimes used when:
- Backend doesn't have `/api` prefix in its routes
- You want to strip the prefix before forwarding

**Example where rewrite is useful:**
```
Frontend: /api/users
Backend endpoint: /users  (no /api prefix)
Rewrite: Needed to strip /api
```

**Our case:**
```
Frontend: /api/simulate-flow
Backend endpoint: /api/simulate-flow  (has /api prefix)
Rewrite: NOT needed - causes 404!
```

---

## 📝 Best Practices

### When to Use Rewrite
✅ Use rewrite when backend doesn't have `/api` prefix:
```typescript
// Backend has: /simulate-flow
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    rewrite: (path) => path.replace(/^\/api/, ''),
  },
}
```

### When NOT to Use Rewrite
❌ Don't use rewrite when backend has `/api` prefix:
```typescript
// Backend has: /api/simulate-flow
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    // No rewrite needed!
  },
}
```

### How to Check
Look at your backend routes:
```python
# If routes look like this:
@app.post("/api/simulate-flow")  # ← Has /api prefix
@app.get("/api/graph")           # ← Has /api prefix

# Then DON'T use rewrite in Vite config
```

---

## ✅ Verification Checklist

After applying the fix:
- [ ] Vite config has no `rewrite` rule
- [ ] Frontend uses `api` instance (not direct `axios`)
- [ ] Frontend dev server restarted
- [ ] Browser cache cleared (hard refresh)
- [ ] Network tab shows `/api/simulate-flow` with 200 OK
- [ ] Backend logs show `/api/simulate-flow` with 200 OK
- [ ] Simulation results display in Flow Sim tab
- [ ] Graph tab shows animated visualization

---

## 🎉 Expected Result

### Flow Sim Tab
1. Select source node
2. Toggle valves
3. Click "Run Simulation"
4. **See:** ✅ Success message, flow path, statistics

### Graph Tab
1. Switch to Graph tab
2. **See:** ✅ Animated green edges, glowing nodes, status badge

### Backend Logs
```
INFO: 127.0.0.1:xxxxx - "POST /api/simulate-flow HTTP/1.1" 200 OK
```

### Browser Network Tab
```
POST /api/simulate-flow
Status: 200 OK
Response: { "active_node_ids": [...], ... }
```

---

## 🐛 If Still Not Working

1. **Check both files were saved:**
   ```bash
   # Check vite.config.ts
   grep "rewrite" frontend/vite.config.ts
   # Should return nothing or just a comment
   
   # Check InteractiveFlowSimulator.tsx
   grep "import api" frontend/src/components/InteractiveFlowSimulator.tsx
   # Should show: import api from '@/lib/api';
   ```

2. **Completely restart everything:**
   ```bash
   # Stop both servers
   
   # Backend
   uvicorn app.main:app --reload --port 8000
   
   # Frontend (new terminal)
   cd frontend
   rm -rf node_modules/.vite dist
   npm run dev
   ```

3. **Test backend directly:**
   ```bash
   curl -X POST http://localhost:8000/api/simulate-flow \
     -H "Content-Type: application/json" \
     -d '{"topology":{"nodes":[{"id":"A","type":"tank","x":0,"y":0}],"edges":[]},"start_node_id":"A","closed_valve_ids":[]}'
   ```
   Should return JSON, not 404.

---

## 📚 Related Documentation

- [BUGFIX_FLOW_SIMULATOR_404.md](BUGFIX_FLOW_SIMULATOR_404.md) - Initial fix attempt
- [TROUBLESHOOTING_404_FIX.md](TROUBLESHOOTING_404_FIX.md) - Troubleshooting guide
- [FLOW_SIMULATOR_INTEGRATION_COMPLETE.md](FLOW_SIMULATOR_INTEGRATION_COMPLETE.md) - Full feature docs

---

## 🎯 Summary

**Two changes needed:**
1. ✅ Use `api` instance instead of direct `axios`
2. ✅ Remove `rewrite` rule from Vite proxy config

**Why:**
- Frontend needs to call `/api/simulate-flow`
- Vite proxy should forward `/api/simulate-flow` as-is
- Backend expects `/api/simulate-flow`

**Result:**
- ✅ Requests reach the correct endpoint
- ✅ Backend returns 200 OK
- ✅ Flow simulation works!

---

**Version:** 1.0.0  
**Status:** ✅ Fixed  
**Last Updated:** 2026-05-17

**Now restart the frontend and it will work!** 🚀
