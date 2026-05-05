# 🔧 Fix: Frontend Can't Connect to Backend

## 🐛 Error

```
http proxy error: /process
AggregateError [ECONNREFUSED]
```

## 🎯 Problem

Your **frontend is running** on port 3000 ✅  
But your **backend is NOT running** on port 8000 ❌

The frontend is trying to connect to `http://localhost:8000` but nothing is there!

---

## ✅ Solution: Start Backend

### Open a NEW Terminal (Keep frontend running!)

**Terminal 1** (Already running):
```
Frontend on http://localhost:3000 ✅
```

**Terminal 2** (Start this NOW):
```bash
cd D:\EDAI4
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🚀 Quick Fix (2 Terminals)

### Terminal 1: Frontend (Already Running)
```bash
cd D:\EDAI4\frontend
npm run dev
```
**Status**: ✅ Running on http://localhost:3000

### Terminal 2: Backend (Start This!)
```bash
cd D:\EDAI4
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```
**Status**: Should show "Application startup complete"

---

## 📊 How to Verify

### Backend Started Successfully
You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Frontend Can Connect
1. Go to http://localhost:3000
2. Upload a P&ID
3. Should process without proxy error!

---

## 🐛 Troubleshooting

### Issue: Backend won't start

**Error: "Address already in use"**
```bash
# Kill process on port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Then start backend again
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Error: "Module not found"**
```bash
# Install dependencies
pip install -r requirements.txt

# Then start backend
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Issue: Still getting proxy error

**Check 1**: Is backend running?
```bash
# Open http://localhost:8000/health in browser
# Should show: {"status":"ok",...}
```

**Check 2**: Is backend on correct port?
```bash
# Backend should show:
INFO:     Uvicorn running on http://0.0.0.0:8000
                                              ^^^^
                                         Port 8000!
```

**Check 3**: Restart frontend
```bash
# In frontend terminal, press Ctrl+C
# Then start again:
npm run dev
```

---

## 📝 Summary

**Problem**: Frontend running, backend NOT running  
**Solution**: Start backend in separate terminal  
**Command**: `python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000`

---

## 🎯 Quick Commands

### Start Backend (Terminal 2)
```bash
cd D:\EDAI4
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Check Backend Health
```bash
curl http://localhost:8000/health
```

Or open in browser: http://localhost:8000/health

---

**START BACKEND NOW!** 🚀
