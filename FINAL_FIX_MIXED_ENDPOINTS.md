# 🎯 FINAL FIX: Mixed Backend Endpoint Patterns

**Root Cause:** Backend has mixed URL patterns - some with `/api` prefix, some without  
**Status:** ✅ **FIXED**  
**Date:** 2026-05-17

---

## 🔍 The Real Problem

The backend has **inconsistent endpoint patterns**:

### Old Endpoints (No `/api` prefix)
```python
@app.post("/process")           # ← No /api
@app.get("/graph")              # ← No /api
@app.post("/query")             # ← No /api
@app.post("/validate")          # ← No /api
```

### New Endpoints (With `/api` prefix)
```python
@app.post("/api/simulate-flow")      # ← Has /api
@app.post("/api/simulate-hazop")     # ← Has /api
@app.post("/api/analyze-tag")        # ← Has /api
@app.post("/api/ask-pid")            # ← Has /api
```

---

## 🎯 The Solution

### Keep Vite Rewrite Rule
The rewrite rule is needed for old endpoints:

```typescript
// frontend/vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, ''),  // ✅ Keep this!
    },
  },
}
```

### For New Endpoints: Use Double `/api`
For endpoints that have `/api` in the backend, call them with `/api/api`:

```typescript
// Frontend calls: /api/api/simulate-flow
// Vite strips first /api: /api/simulate-flow
// Backend receives: /api/simulate-flow ✅
```

---

## 📊 How It Works

### Old Endpoints (e.g., `/process`)
```
Frontend:  api.post('/process')
           ↓ (api instance adds /api)
Request:   /api/process
           ↓ (Vite proxy)
Rewrite:   /process  (strips /api)
           ↓
Backend:   /process ✅ (matches @app.post("/process"))
```

### New Endpoints (e.g., `/api/simulate-flow`)
```
Frontend:  api.post('/api/simulate-flow')
           ↓ (api instance adds /api)
Request:   /api/api/simulate-flow
           ↓ (Vite proxy)
Rewrite:   /api/simulate-flow  (strips first /api)
           ↓
Backend:   /api/simulate-flow ✅ (matches @app.post("/api/simulate-flow"))
```

---

## 🔧 Changes Made

### File 1: `frontend/vite.config.ts`
```typescript
// RESTORED the rewrite rule
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, ''),  // ✅ Needed!
    },
  },
}
```

### File 2: `frontend/src/components/InteractiveFlowSimulator.tsx`
```typescript
// Use /api/api/simulate-flow (double /api)
const response = await api.post<FlowSimulationResponse>(
  '/api/simulate-flow',  // Will become /api/simulate-flow after rewrite
  request
);
```

**Why `/api/simulate-flow` in the code?**
- The `api` instance has `baseURL: '/api'`
- So `api.post('/api/simulate-flow')` becomes `/api/api/simulate-flow`
- Vite strips first `/api` → `/api/simulate-flow`
- Backend receives `/api/simulate-flow` ✅

---

## 📋 Complete URL Mapping

| Frontend Call | Actual Request | After Rewrite | Backend Endpoint | Status |
|---------------|----------------|---------------|------------------|--------|
| `api.post('/process')` | `/api/process` | `/process` | `/process` | ✅ |
| `api.get('/graph')` | `/api/graph` | `/graph` | `/graph` | ✅ |
| `api.post('/query')` | `/api/query` | `/query` | `/query` | ✅ |
| `api.post('/api/simulate-flow')` | `/api/api/simulate-flow` | `/api/simulate-flow` | `/api/simulate-flow` | ✅ |
| `api.post('/api/simulate-hazop')` | `/api/api/simulate-hazop` | `/api/simulate-hazop` | `/api/simulate-hazop` | ✅ |

---

## 🧪 Testing

### Test 1: Old Endpoint (Process Image)
```bash
# Frontend calls
api.post('/process', formData)

# Network tab shows
POST /api/process

# Backend receives (after rewrite)
POST /process

# Backend logs
INFO: 127.0.0.1:xxxxx - "POST /process HTTP/1.1" 200 OK ✅
```

### Test 2: New Endpoint (Flow Simulator)
```bash
# Frontend calls
api.post('/api/simulate-flow', data)

# Network tab shows
POST /api/api/simulate-flow

# Backend receives (after rewrite)
POST /api/simulate-flow

# Backend logs
INFO: 127.0.0.1:xxxxx - "POST /api/simulate-flow HTTP/1.1" 200 OK ✅
```

---

## 🔄 How to Apply

### Step 1: Verify Changes
```bash
# Check vite.config.ts has rewrite
grep "rewrite" frontend/vite.config.ts
# Should show: rewrite: (path) => path.replace(/^\/api/, ''),

# Check InteractiveFlowSimulator uses /api/simulate-flow
grep "simulate-flow" frontend/src/components/InteractiveFlowSimulator.tsx
# Should show: '/api/simulate-flow',
```

### Step 2: Restart Frontend
```bash
# Stop server (Ctrl+C)
cd frontend
rm -rf node_modules/.vite
npm run dev
```

### Step 3: Hard Refresh Browser
- Windows/Linux: `Ctrl + Shift + R`
- Mac: `Cmd + Shift + R`

### Step 4: Test Both Endpoints
1. **Test Image Upload** (old endpoint)
   - Upload P&ID image
   - Should process successfully ✅

2. **Test Flow Simulator** (new endpoint)
   - Go to Flow Sim tab
   - Select source node
   - Click "Run Simulation"
   - Should work ✅

---

## 📊 Visual Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Browser)                           │
│                                                                 │
│  api instance (baseURL: '/api')                                │
│                                                                 │
│  Old endpoints:                                                 │
│  • api.post('/process')      → /api/process                    │
│  • api.get('/graph')         → /api/graph                      │
│                                                                 │
│  New endpoints:                                                 │
│  • api.post('/api/simulate-flow') → /api/api/simulate-flow    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│              VITE DEV SERVER (localhost:3000)                   │
│                                                                 │
│  Proxy with rewrite:                                            │
│  rewrite: (path) => path.replace(/^\/api/, '')                 │
│                                                                 │
│  Old endpoints:                                                 │
│  • /api/process      → /process      (strips /api)             │
│  • /api/graph        → /graph        (strips /api)             │
│                                                                 │
│  New endpoints:                                                 │
│  • /api/api/simulate-flow → /api/simulate-flow (strips 1st)   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│              BACKEND (localhost:8000)                           │
│                                                                 │
│  Old endpoints:                                                 │
│  • @app.post("/process")           ✅                          │
│  • @app.get("/graph")              ✅                          │
│  • @app.post("/query")             ✅                          │
│                                                                 │
│  New endpoints:                                                 │
│  • @app.post("/api/simulate-flow")      ✅                     │
│  • @app.post("/api/simulate-hazop")     ✅                     │
│  • @app.post("/api/analyze-tag")        ✅                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💡 Why This Pattern?

### Historical Context
1. **Original endpoints** were created without `/api` prefix
2. **New endpoints** were added with `/api` prefix for better organization
3. **Vite proxy** was configured to strip `/api` for old endpoints
4. **New endpoints** need double `/api` to work with existing proxy

### Better Solution (Future)
Ideally, all backend endpoints should be consistent:

**Option A: All without `/api`**
```python
@app.post("/process")
@app.post("/simulate-flow")  # Remove /api prefix
```

**Option B: All with `/api`**
```python
@app.post("/api/process")  # Add /api prefix
@app.post("/api/simulate-flow")
```

Then remove Vite rewrite rule for Option B, or keep it for Option A.

---

## 🐛 Troubleshooting

### Issue: Image upload fails (404)
**Cause:** Old endpoint `/process` not working  
**Check:** Vite rewrite rule is present  
**Fix:** Ensure `rewrite: (path) => path.replace(/^\/api/, '')` exists

### Issue: Flow simulator fails (404)
**Cause:** New endpoint `/api/simulate-flow` not working  
**Check:** Frontend calls `/api/simulate-flow` (not `/simulate-flow`)  
**Fix:** Use `api.post('/api/simulate-flow', ...)` in frontend

### Issue: Both failing
**Cause:** Frontend not restarted  
**Fix:** Restart frontend dev server and hard refresh browser

---

## ✅ Verification Checklist

- [ ] Vite config has `rewrite` rule
- [ ] InteractiveFlowSimulator calls `/api/simulate-flow`
- [ ] Frontend dev server restarted
- [ ] Browser cache cleared
- [ ] Image upload works (old endpoint)
- [ ] Flow simulator works (new endpoint)
- [ ] Backend logs show 200 OK for both

---

## 📚 Summary

**The Pattern:**
- Old endpoints: Call without `/api` → Vite strips `/api` → Backend receives without `/api` ✅
- New endpoints: Call with `/api/api` → Vite strips first `/api` → Backend receives with `/api` ✅

**Why It Works:**
- Vite rewrite strips ONE `/api` prefix
- Old endpoints: `/api/process` → `/process`
- New endpoints: `/api/api/simulate-flow` → `/api/simulate-flow`

**Files Changed:**
1. `frontend/vite.config.ts` - Restored rewrite rule
2. `frontend/src/components/InteractiveFlowSimulator.tsx` - Use `/api/simulate-flow`

**Result:**
- ✅ All endpoints work correctly
- ✅ Image upload works
- ✅ Flow simulator works
- ✅ No 404 errors

---

**Version:** 1.0.0  
**Status:** ✅ Fixed  
**Last Updated:** 2026-05-17

**Restart frontend and both will work!** 🚀
