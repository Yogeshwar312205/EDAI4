# Gemini Model Update - gemini-1.5-flash → gemini-2.5-flash

## Problem

All AI features were failing with:
```
404 models/gemini-1.5-flash is not found for API version v1beta
```

## Root Cause

The `google.generativeai` package (OLD API) is **deprecated** and `gemini-1.5-flash` is **no longer available**.

### Package Status
```
FutureWarning: All support for the `google.generativeai` package has ended.
It will no longer be receiving updates or bug fixes.
Please switch to the `google.genai` package as soon as possible.
```

### Available Models
When we list available models, `gemini-1.5-flash` is NOT in the list:
- ✅ `models/gemini-2.5-flash` (latest)
- ✅ `models/gemini-2.0-flash`
- ✅ `models/gemini-flash-latest`
- ❌ `models/gemini-1.5-flash` (REMOVED)

## Solution

Updated all AI features to use `gemini-2.5-flash`:

### Files Updated:
1. ✅ `src/api/main.py` - Chatbot
2. ✅ `src/api/hazop_simulator.py` - HazOp Simulator
3. ✅ `src/api/maintenance_checklist.py` - Maintenance Checklist
4. ✅ `src/api/graph_filter.py` - Graph Filter

### Change:
```python
# Before
model: str = "gemini-1.5-flash"

# After
model: str = "gemini-2.5-flash"
```

## Benefits of gemini-2.5-flash

1. **Latest Model:** Most recent Gemini model
2. **Better Performance:** Improved accuracy and speed
3. **Available:** Actually exists in the API
4. **Same API:** Works with OLD package (for now)

## Testing

### Restart Backend:
```bash
# Stop current backend (Ctrl+C)
python -m uvicorn src.api.main:app --reload --port 8000
```

### Test All Features:

**1. Chatbot:**
- Upload P&ID → Graph tab → Chatbot
- Ask: "describe whole diagram"
- Should get AI response

**2. HazOp Simulator:**
- Graph tab → Right-click node → Simulate failure
- Should get hazard analysis

**3. Graph Filter:**
- Graph tab → Click "Smart Filter"
- Type: "all valves"
- Should highlight matching nodes

**4. Maintenance Checklist:**
- Graph tab → Click node → "Generate Maintenance Checklist"
- Should get equipment-specific tasks

### Expected Logs:
```
[INFO] Chatbot using Gemini model: gemini-2.5-flash
[INFO] HazOp Simulator initialized with model: gemini-2.5-flash
[INFO] Maintenance Checklist Generator initialized with model: gemini-2.5-flash
[INFO] Graph Filter initialized with model: gemini-2.5-flash
```

## Future Migration

The OLD `google.generativeai` package is deprecated. We should eventually migrate to the NEW `google-genai` package:

### NEW Package:
```python
from google import genai

client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model='models/gemini-2.5-flash',
    contents=prompt
)
```

### Why Not Now?
- OLD package still works
- NEW package has different API
- Would require rewriting all AI features
- Can do later when OLD package stops working

## Rate Limits

### gemini-2.5-flash (Free Tier):
- **Requests:** 15 per minute, 1,500 per day
- **Tokens:** 1 million per minute
- **Same as before:** No change in limits

## Summary

✅ **Updated:** All AI features now use `gemini-2.5-flash`
✅ **Working:** Model is available and supported
✅ **Consistent:** All features use same model
✅ **Future-proof:** Latest Gemini model

**All AI features should now work!** 🎉

---

## Quick Test Checklist

- [ ] Backend restarted
- [ ] Chatbot works (no fallback message)
- [ ] HazOp simulator works
- [ ] Graph filter works
- [ ] Maintenance checklist works
- [ ] Logs show `gemini-2.5-flash`

If all checked, the update is successful! ✅
