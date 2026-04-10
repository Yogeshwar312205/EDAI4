# 🚀 EDAI4 Quick Start Guide

## ⚡ Fastest Way to Run

### Windows Users

1. **Start Backend** (in terminal 1):
   ```bash
   START_BACKEND.bat
   ```
   Or manually:
   ```bash
   python -m uvicorn src.api.main:app --reload --port 8000
   ```

2. **Start Frontend** (in terminal 2):
   ```bash
   START_FRONTEND.bat
   ```
   Or manually:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open Browser**:
   ```
   http://localhost:3000
   ```

---

## 📋 Prerequisites

### Backend
- Python 3.8+
- All dependencies installed:
  ```bash
  pip install -r requirements.txt
  ```

### Frontend
- Node.js 16+
- Dependencies installed:
  ```bash
  cd frontend
  npm install
  ```

---

## 🎯 What You'll See

### 1. Upload Screen
- Drag & drop P&ID image
- Or click to browse

### 2. After Upload - 5 Tabs
- **Canvas** - Interactive image viewer
- **Graph** - Topology visualization
- **Deliverables** ⭐ - Generate Excel reports
- **Design Rules** ⭐ - Quality control
- **Flow Sim** ⭐ - Flow path analysis

---

## 🧪 Quick Test

1. Upload a P&ID image
2. Wait for processing (shows spinner)
3. Click **"Deliverables"** tab
4. Click **"Generate Excel Deliverables"**
5. Download and open Excel file
6. Verify 3 tabs: Instrument Index, IO List, Alarm List

---

## 🔧 Troubleshooting

### Backend won't start?
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Install missing dependencies
pip install -r requirements.txt
```

### Frontend won't start?
```bash
# Install dependencies
cd frontend
npm install

# Clear cache and restart
npm run dev
```

### "No graph loaded" error?
- Upload a P&ID image first
- Advanced features require processed data

---

## 📚 Full Documentation

- **SYSTEM_STATUS.md** - Complete system status
- **FINAL_TESTING_GUIDE.md** - Detailed testing
- **IMPLEMENTATION_COMPLETE.md** - Feature overview

---

## ✅ Success Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Can upload P&ID image
- [ ] All 5 tabs visible
- [ ] Can generate Excel deliverables
- [ ] No console errors

---

**Status**: 🟢 Ready to Run
**Version**: 1.0.0

🎉 **Your P&ID intelligence platform is ready!**
