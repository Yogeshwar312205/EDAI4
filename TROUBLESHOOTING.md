# 🔧 EDAI4 Troubleshooting Guide

## 🚨 Features Not Working? Follow These Steps

### Step 1: Run Diagnostic Test

```bash
python test_features.py
```

This will check:
- ✅ All modules can be imported
- ✅ All classes can be instantiated
- ✅ All dependencies are installed
- ✅ All API endpoints exist

---

## 🔍 Common Issues & Solutions

### Issue 1: "Module not found" errors

**Symptoms:**
- Backend crashes on startup
- Import errors in console
- "No module named 'src.deliverables'" or "No module named 'src.advanced'"

**Solution:**
```bash
# Make sure you're in the EDAI4 root directory
cd D:/EDAI4  # or your project path

# Run the diagnostic
python test_features.py

# If modules are missing, check file structure
dir src\deliverables
dir src\advanced
```

**Expected files:**
```
src/deliverables/
├── __init__.py
├── excel_formatter.py
├── instrument_index.py
├── io_list.py
└── alarm_list.py

src/advanced/
├── __init__.py
├── design_rules.py
├── flow_simulator.py
└── pid_diff.py
```

---

### Issue 2: "No module named 'openpyxl'" or "No module named 'pandas'"

**Symptoms:**
- Backend starts but crashes when generating deliverables
- Error: "ModuleNotFoundError: No module named 'openpyxl'"

**Solution:**
```bash
# Install missing dependencies
pip install openpyxl pandas xlsxwriter

# Or install all requirements
pip install -r requirements.txt
```

---

### Issue 3: Backend starts but features return errors

**Symptoms:**
- Backend runs without errors
- Frontend loads but features don't work
- API calls return 500 errors

**Diagnosis:**
1. Check backend console for errors
2. Check browser console (F12) for errors
3. Test API endpoints directly

**Test API endpoints:**
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test design rules (after uploading P&ID)
curl http://localhost:8000/design-rules/check

# Test deliverables (after uploading P&ID)
curl -X POST http://localhost:8000/deliverables/generate \
  -F "pid_reference=TEST-001" \
  -F "plc_name=PLC-001"
```

---

### Issue 4: "No graph loaded" error

**Symptoms:**
- Features return "No graph loaded. Process an image first."
- Deliverables, Design Rules, Flow Sim don't work

**Solution:**
1. Upload a P&ID image first
2. Wait for processing to complete
3. Verify you see 5 tabs (Canvas, Graph, Deliverables, Design Rules, Flow Sim)
4. Then try the features

**The features require a processed P&ID to work!**

---

### Issue 5: Frontend shows blank screen or errors

**Symptoms:**
- Frontend loads but shows errors
- Console shows "Failed to fetch" or network errors
- Features don't load

**Solution:**
```bash
# Check if backend is running
# Should see: "Uvicorn running on http://127.0.0.1:8000"

# Check if frontend proxy is configured
cd frontend
cat vite.config.ts

# Should see:
# proxy: {
#   '/api': {
#     target: 'http://localhost:8000',
#     ...
#   }
# }

# Restart frontend
npm run dev
```

---

### Issue 6: Excel file doesn't download

**Symptoms:**
- Click "Generate Excel Deliverables"
- Button shows "Generating..." but nothing downloads
- Error in console

**Solution:**

**Check 1: Backend is running**
```bash
# Backend must be running on port 8000
netstat -ano | findstr :8000
```

**Check 2: Dependencies installed**
```bash
pip install openpyxl pandas
```

**Check 3: Graph is loaded**
- Upload a P&ID image first
- Wait for processing to complete
- Then try generating deliverables

**Check 4: Browser console**
- Press F12 to open developer tools
- Check Console tab for errors
- Check Network tab for failed requests

---

### Issue 7: Design Rules shows no violations

**This is NORMAL if your P&ID is clean!**

The design rule checker looks for:
1. Control valves without isolation
2. Pumps without suction strainers
3. Orphaned instruments
4. Missing or duplicate tags
5. Check valve orientation issues
6. Transmitter connectivity problems
7. Safety valve requirements

If your P&ID follows all standards, you'll see:
✅ "No violations found! Your P&ID meets all design rule requirements."

---

### Issue 8: Flow Simulator dropdown is empty

**Symptoms:**
- Flow Simulator tab loads
- Start node dropdown is empty
- Can't select any nodes

**Solution:**
1. Upload a P&ID image first
2. Wait for processing to complete
3. The dropdown populates from detected nodes
4. If still empty, check backend console for processing errors

---

## 📋 Step-by-Step Verification

### Step 1: Verify File Structure

```bash
# Check if all files exist
dir src\deliverables
dir src\advanced
python test_features.py
```

**Expected output:**
```
✅ SUCCESS: All deliverables classes imported
✅ SUCCESS: All advanced classes imported
✅ SUCCESS: All deliverable generators instantiated
✅ SUCCESS: All advanced feature classes instantiated
```

### Step 2: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Specifically for advanced features
pip install openpyxl pandas xlsxwriter networkx

# Install frontend dependencies
cd frontend
npm install
```

### Step 3: Start Backend

```bash
# From EDAI4 root directory
python -m uvicorn src.api.main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Check for errors:**
- No "ModuleNotFoundError"
- No "ImportError"
- No crashes

### Step 4: Test Backend Health

```bash
# In a new terminal
curl http://localhost:8000/health
```

**Expected output:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "layers_ready": {
    "layer1_yolo": true,
    "layer2_ocr": true,
    ...
  }
}
```

### Step 5: Start Frontend

```bash
cd frontend
npm run dev
```

**Expected output:**
```
VITE v5.0.11  ready in 1234 ms
➜  Local:   http://localhost:3000/
```

### Step 6: Test in Browser

1. Open http://localhost:3000
2. Upload a P&ID image
3. Wait for processing (shows spinner)
4. Verify 5 tabs appear
5. Click each tab to verify it loads

### Step 7: Test Each Feature

**Deliverables:**
1. Click "Deliverables" tab
2. Enter P&ID reference
3. Click "Generate Excel Deliverables"
4. Excel file should download
5. Open Excel - should have 3 tabs

**Design Rules:**
1. Click "Design Rules" tab
2. Should show summary cards
3. Should show violations or "No violations"
4. Filter buttons should work

**Flow Simulator:**
1. Click "Flow Sim" tab
2. Dropdown should have nodes
3. Select a node
4. Click "Trace Flow Path"
5. Should show results

---

## 🐛 Debug Mode

### Enable Verbose Logging

**Backend:**
```python
# In src/api/main.py, add at the top:
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Frontend:**
```typescript
// In frontend/src/lib/api.ts, add:
api.interceptors.request.use(request => {
  console.log('API Request:', request);
  return request;
});

api.interceptors.response.use(
  response => {
    console.log('API Response:', response);
    return response;
  },
  error => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);
```

---

## 📞 Still Not Working?

### Collect Diagnostic Information

1. **Run diagnostic test:**
   ```bash
   python test_features.py > diagnostic.txt
   ```

2. **Check backend logs:**
   - Copy all output from backend terminal

3. **Check frontend console:**
   - Press F12 in browser
   - Copy all errors from Console tab

4. **Check network requests:**
   - Press F12 in browser
   - Go to Network tab
   - Try the feature
   - Check for failed requests (red)
   - Click on failed request to see details

5. **Verify file structure:**
   ```bash
   dir /s src\deliverables
   dir /s src\advanced
   ```

---

## ✅ Success Checklist

Use this to verify everything is working:

- [ ] `python test_features.py` passes all tests
- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Can access http://localhost:3000
- [ ] Can upload P&ID image
- [ ] Processing completes successfully
- [ ] All 5 tabs appear
- [ ] Deliverables tab loads
- [ ] Can generate Excel file
- [ ] Excel file downloads and opens
- [ ] Design Rules tab loads
- [ ] Shows violations or "No violations"
- [ ] Flow Sim tab loads
- [ ] Dropdown has nodes
- [ ] Can trace flow path
- [ ] No errors in browser console
- [ ] No errors in backend console

---

## 🎯 Quick Fix Commands

```bash
# Fix 1: Reinstall dependencies
pip install -r requirements.txt
cd frontend && npm install

# Fix 2: Clear cache and restart
# Backend: Ctrl+C then restart
python -m uvicorn src.api.main:app --reload --port 8000

# Frontend: Ctrl+C then restart
cd frontend
npm run dev

# Fix 3: Check ports
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# Fix 4: Run diagnostic
python test_features.py

# Fix 5: Test API directly
curl http://localhost:8000/health
```

---

**Need more help?** Check these files:
- `QUICK_START.md` - Fast startup guide
- `FINAL_TESTING_GUIDE.md` - Detailed testing
- `SYSTEM_STATUS.md` - Complete system overview

---

**Status**: 🔧 Troubleshooting Guide
**Version**: 1.0.0
**Last Updated**: 2026-04-10
