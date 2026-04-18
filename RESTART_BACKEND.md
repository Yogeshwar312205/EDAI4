# Restart Backend to Enable Gemini AI

## What Changed

The backend now recognizes your existing `GOOGLE_API_KEY` environment variable.

## Steps to Enable AI Analysis

### 1. Stop Current Backend

Press `Ctrl+C` in the terminal running the backend.

### 2. Restart Backend

```bash
python -m uvicorn src.api.main:app --reload
```

### 3. Verify Gemini is Enabled

Look for this log message when backend starts:
```
INFO: Gemini AI initialized successfully
```

If you see:
```
WARNING: GEMINI_API_KEY or GOOGLE_API_KEY not set. Gemini features will be disabled.
```

Then check your .env file has:
```
GOOGLE_API_KEY=your_key_here
```

### 4. Test in Frontend

1. Refresh browser (Ctrl+Shift+R)
2. Click on an instrument node
3. You should now see AI-powered definitions instead of:
   ```
   "Unable to determine specific function. Configure GEMINI_API_KEY..."
   ```

## Expected Result

**Before (Simulated Mode):**
```
Tag: instrument.bubble
Definition: Instrument tag - Unable to determine specific function. 
Configure GEMINI_API_KEY for AI-powered analysis.
```

**After (AI Mode):**
```
Tag: FIC-101
Definition: Flow Indicator Controller - Measures flow rate and 
provides automatic control to maintain desired flow setpoint 
in the process line.
```

## Troubleshooting

### Issue: Still showing "Unable to determine"

**Solution:**
1. Check .env file has `GOOGLE_API_KEY=...`
2. Restart backend completely (stop and start again)
3. Check backend logs for "Gemini AI initialized successfully"

### Issue: "API key invalid"

**Solution:**
1. Verify API key is correct
2. Get new key from: https://makersuite.google.com/app/apikey
3. Update .env file
4. Restart backend

### Issue: "Rate limit exceeded"

**Solution:**
- Free tier: 15 requests/minute
- Wait 1 minute and try again
- Or upgrade to paid tier

## Quick Test

```bash
# Test the endpoint directly
curl -X POST http://localhost:8000/api/api/analyze-tag \
  -F "tag_text=FIC-101"

# Should return AI-powered definition
{
  "tag": "FIC-101",
  "definition": "Flow Indicator Controller - Measures flow rate..."
}
```

## Summary

✅ Backend updated to use `GOOGLE_API_KEY`
✅ Just restart backend to enable AI
✅ No need to change .env file (already has the key)

**Next:** Restart backend and test!
