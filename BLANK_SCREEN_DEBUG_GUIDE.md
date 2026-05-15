# 🐛 Blank Screen After Processing - Debug Guide

## Problem
Frontend shows a blank screen after uploading and processing a P&ID image.

## Possible Causes

### 1. Frontend JavaScript Error
The most likely cause is a JavaScript error in the React components that's breaking the rendering.

**How to Check:**
1. Open browser DevTools (F12)
2. Go to **Console** tab
3. Look for red error messages
4. Take a screenshot and share the error

### 2. Backend Response Format Issue
The backend might be returning data in an unexpected format.

**How to Check:**
1. Open browser DevTools (F12)
2. Go to **Network** tab
3. Find the `/process` request (should be at the bottom)
4. Click on it
5. Go to **Response** tab
6. Check if the response looks like this:

```json
{
  "image_name": "...",
  "processing_time_ms": 1234,
  "layer1_detections": 25,
  "layer2_instruments": 10,
  "layer3_nodes": 25,
  "layer3_edges": 15,
  "detections": [
    {
      "class_name": "instrument.bubble",
      "confidence": 0.95,
      "pct_x": 0.1234,
      "pct_y": 0.5678,
      "pct_width": 0.0456,
      "pct_height": 0.0789,
      "tag": "FT-101"
    }
  ],
  "graph_summary": {...}
}
```

### 3. State Management Issue
The state might not be updating correctly.

**How to Check:**
1. Open browser DevTools (F12)
2. Install React DevTools extension if not already installed
3. Go to **Components** tab
4. Find `AppContent` component
5. Check the state values:
   - `uploadedImage` - should be a data URL string
   - `processingResult` - should be an object with detections array
   - `hasData` - should be `true`

### 4. Backend Crashed During Processing
The backend might have crashed while processing the image.

**How to Check:**
Look at the backend terminal output for errors.

## Quick Fixes to Try

### Fix 1: Hard Refresh Browser
```
Windows: Ctrl + Shift + R
Mac: Cmd + Shift + R
```

### Fix 2: Clear Browser Cache
1. Open DevTools (F12)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"

### Fix 3: Restart Frontend
```bash
# Stop frontend (Ctrl+C in terminal)
cd frontend
npm run dev
```

### Fix 4: Check Backend Logs
Look at Terminal ID: 6 for any errors during processing.

## Debug Steps

### Step 1: Check Console Errors
```
1. Open browser (http://localhost:5173)
2. Press F12 to open DevTools
3. Go to Console tab
4. Upload an image
5. Look for RED error messages
6. Copy the error message
```

### Step 2: Check Network Response
```
1. In DevTools, go to Network tab
2. Upload an image
3. Find the "process" request
4. Click on it
5. Check Response tab
6. Verify the format matches expected format above
```

### Step 3: Check React State
```
1. Install React DevTools browser extension
2. Open DevTools, go to Components tab
3. Find AppContent component
4. Check state values
```

## Common Errors and Solutions

### Error: "Cannot read property 'pct_x' of undefined"
**Cause:** Backend is not returning detections in the expected format.
**Solution:** Check backend response format in Network tab.

### Error: "detections.map is not a function"
**Cause:** `detections` is not an array.
**Solution:** Check if backend is returning `detections` as an array.

### Error: "Cannot read property 'detections' of null"
**Cause:** `processingResult` is null.
**Solution:** Check if backend request succeeded in Network tab.

### Blank screen with no errors
**Cause:** CSS issue or component not rendering.
**Solution:** Check if `hasData` is true in React DevTools.

## Temporary Workaround

If you need to test the coordinate fix without fixing the blank screen issue, you can:

1. **Test backend directly:**
   ```bash
   python test_backend_coordinate_fix.py
   ```

2. **Use curl to test:**
   ```bash
   curl -X POST http://localhost:8000/process \
     -F "file=@path/to/image.jpg" \
     | python -m json.tool
   ```

## What to Report

Please provide:
1. **Console errors** (screenshot or copy-paste)
2. **Network response** (from /process request)
3. **React state** (from React DevTools)
4. **Backend logs** (any errors during processing)

This will help diagnose the exact cause of the blank screen.

## Backend Status

**Current Status:** ✅ Running
- Terminal ID: 6
- URL: http://localhost:8000
- Status: Application startup complete

## Next Steps

1. Open browser DevTools (F12)
2. Check Console tab for errors
3. Upload an image
4. Report what you see in the console
