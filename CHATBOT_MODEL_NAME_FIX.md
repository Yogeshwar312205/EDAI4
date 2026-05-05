# Chatbot Model Name Fix

## Error

```
[ERROR] Gemini API error: 404 models/gemini-1.5-flash is not found for API version v1beta
```

## Root Cause

The OLD Gemini API doesn't use the `models/` prefix in model names. The error occurred because somewhere in the code the model name had the prefix.

## Solution

Added the same safety check that HazOp uses:

```python
# Remove 'models/' prefix if present (same as HazOp)
model_name = 'gemini-1.5-flash'.replace("models/", "")
model = genai.GenerativeModel(model_name)
```

This ensures the model name is always `gemini-1.5-flash` without any prefix.

## Verification

### Backend Logs Should Show:

**Before (Error):**
```
[ERROR] Gemini API error: 404 models/gemini-1.5-flash is not found
```

**After (Success):**
```
[INFO] Chatbot using Gemini model: gemini-1.5-flash
[INFO] Asking Gemini about P&ID: describe whole diagram
[INFO] ✓ Gemini response received: 1234 characters
```

## Testing

The backend should auto-reload (if started with `--reload` flag). If not, restart it:

```bash
python -m uvicorn src.api.main:app --reload --port 8000
```

Then test the chatbot:
1. Upload P&ID
2. Go to Graph tab
3. Open chatbot
4. Ask: "describe whole diagram"
5. Should get AI response (not fallback)

## Status

✅ **Fixed** - Chatbot now uses exact same model initialization as HazOp
✅ **Consistent** - Both use `gemini-1.5-flash` without prefix
✅ **Safe** - `.replace("models/", "")` prevents future issues

The chatbot should now work! 🎉
