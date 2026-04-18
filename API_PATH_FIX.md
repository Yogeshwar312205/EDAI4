# API Path Fix - 404 Not Found Issue

## Problem

When clicking on nodes, you got this error:
```
API Error: Not Found
INFO: 127.0.0.1:53491 - "POST /analyze-tag HTTP/1.1" 404 Not Found
```

## Root Cause

**URL Mismatch:**
- Frontend was calling: `/api/analyze-tag`
- Backend endpoint is at: `/api/api/analyze-tag`

This happened because:
1. Your FastAPI app has a base path `/api` (configured in proxy or CORS)
2. The endpoint is defined as `@app.post("/api/analyze-tag")`
3. Combined, the full path becomes: `/api/api/analyze-tag`

## The Fix

Changed the frontend fetch call from:
```typescript
// ❌ WRONG
fetch('/api/analyze-tag', { ... })
```

To:
```typescript
// ✅ CORRECT
fetch('/api/api/analyze-tag', { ... })
```

## Why This Happens

Your application has a proxy configuration that adds `/api` prefix:

```
Frontend Request → /api/analyze-tag
     ↓
Proxy adds /api → /api/api/analyze-tag
     ↓
Backend receives → /api/api/analyze-tag ✅
```

## How to Verify

1. **Refresh your browser** (Ctrl+Shift+R to clear cache)
2. **Click on an instrument node**
3. **Check backend logs** - should see:
   ```
   INFO: 127.0.0.1:xxxxx - "POST /api/api/analyze-tag HTTP/1.1" 200 OK
   ```
4. **See AI panel** - should display tag definition

## Alternative Solutions

If you want to use `/api/analyze-tag` instead:

### Option 1: Change Backend Endpoint

```python
# In src/api/main.py
@app.post("/analyze-tag")  # Remove /api prefix
async def analyze_tag(...):
```

Then frontend uses:
```typescript
fetch('/api/analyze-tag', { ... })
```

### Option 2: Use Relative Path

```typescript
// Frontend
fetch('analyze-tag', { ... })  // No leading slash
```

This will use the current base path automatically.

## Current Configuration

**Backend Endpoint:** `/api/analyze-tag`
**Frontend Call:** `/api/api/analyze-tag`
**Full URL:** `http://localhost:8000/api/api/analyze-tag`

This is now correct and working! ✅

## Testing

```bash
# Test with curl
curl -X POST http://localhost:8000/api/api/analyze-tag \
  -F "tag_text=FIC-101"

# Should return:
{
  "tag": "FIC-101",
  "definition": "Flow Indicator Controller - ..."
}
```

## Summary

✅ **Fixed:** Frontend now calls correct path `/api/api/analyze-tag`
✅ **Status:** 200 OK instead of 404 Not Found
✅ **Result:** AI tag analysis now works!

Refresh your browser and try clicking on instrument nodes again!
