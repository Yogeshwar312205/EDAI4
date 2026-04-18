# Why You're Seeing "Unable to determine specific function"

## The Message You're Seeing

```
🤖 AI Tag Explainer

Tag: instrument.bubble

Definition: Instrument tag - Unable to determine specific function. 
Configure GEMINI_API_KEY for AI-powered analysis.
```

## Two Problems

### Problem 1: No Real Gemini API Key ❌

**Current situation:**
- Your `.env` file has `GOOGLE_API_KEY` but it's not a valid Gemini API key
- The system is running in **simulated mode** (fallback mode)
- Simulated mode only recognizes standard ISA tags like "FIC-101", "PT-205"

**Solution:**
1. Get real API key from: https://makersuite.google.com/app/apikey
2. Update `.env` file with key starting with `AIza`
3. Restart backend

### Problem 2: Wrong Tag Being Analyzed ❌

**Current situation:**
- The node label is "instrument.bubble" (the class name)
- This is NOT an actual instrument tag
- Real tags look like: "FIC-101", "PT-205", "TIC-301"

**Why this happens:**
- Your P&ID nodes don't have actual instrument tags assigned
- The system falls back to showing the detection class name
- The backend can't analyze a class name

## What Should Happen

### With Proper Tags

If your nodes had real tags, you'd see:

```
🤖 AI Tag Explainer

Tag: FIC-101

Definition: Flow Indicator Controller - Measures flow rate 
and provides automatic control to maintain desired flow 
setpoint in the process line.

Powered by Google Gemini AI
```

### How to Get Proper Tags

Your P&ID processing needs to:
1. **Detect instrument symbols** ✅ (Working - you have "instrument.bubble")
2. **Read text near symbols** ✅ (OCR is working)
3. **Associate text with symbols** ❌ (Not working or no text found)
4. **Extract ISA tags** ❌ (Tags not being extracted)

## Quick Fixes

### Fix 1: Enable Gemini AI (2 minutes)

Even without proper tags, Gemini can analyze class names better:

```bash
# 1. Get API key
https://makersuite.google.com/app/apikey

# 2. Update .env
GOOGLE_API_KEY=AIzaSyYourRealKeyHere

# 3. Restart backend
python -m uvicorn src.api.main:app --reload
```

### Fix 2: Check Your P&ID Image

**Does your P&ID have text labels?**
- ✅ Yes → OCR should extract them
- ❌ No → You need to add tags manually or use a different P&ID

**Example P&ID with tags:**
```
    FIC-101
      ⭕  ← Instrument bubble with tag above/inside
      
    PT-205
      ⭕  ← Another instrument with tag
```

### Fix 3: Test with a Sample Tag

Even in simulated mode, you can test with a proper tag format:

```bash
# Test the API directly
curl -X POST http://localhost:8000/api/api/analyze-tag \
  -F "tag_text=FIC-101"

# Should return definition even in simulated mode
{
  "tag": "FIC-101",
  "definition": "Flow Indicator Controller - Measures flow rate and provides automatic control (Simulated response - Gemini API not configured)"
}
```

## Understanding the System Modes

### Mode 1: Simulated Mode (Current)

**When:** No Gemini API key configured

**What it does:**
- Uses built-in ISA tag dictionary (30+ common tags)
- Only recognizes standard formats: FIC, PT, TIC, LIC, etc.
- Cannot analyze unusual tags or class names

**Limitations:**
- ❌ Can't analyze "instrument.bubble"
- ❌ Can't handle custom tags
- ❌ Limited to predefined dictionary

### Mode 2: AI Mode (With Gemini)

**When:** Valid Gemini API key configured

**What it does:**
- Uses Google Gemini AI for analysis
- Can understand any tag format
- Provides detailed engineering explanations
- Can even analyze class names intelligently

**Benefits:**
- ✅ Analyzes any tag format
- ✅ Understands context
- ✅ Detailed explanations
- ✅ Handles unusual cases

## What Your Backend Logs Show

```
WARNING: GOOGLE_API_KEY not found - LLM features disabled
```

This confirms:
1. The API key is not being loaded
2. System is in simulated mode
3. Only basic ISA tags will work

## Complete Solution

### Step 1: Fix API Key

```bash
# Get key from MakerSuite
https://makersuite.google.com/app/apikey

# Update .env
GOOGLE_API_KEY=AIzaSyYourRealKeyHere

# Test it
python scripts/test_gemini_key.py
```

### Step 2: Restart Backend

```bash
python -m uvicorn src.api.main:app --reload
```

**Look for:**
```
✅ Gemini AI initialized successfully with API key
```

### Step 3: Process P&ID with Tags

Use a P&ID image that has:
- Instrument symbols (circles, squares)
- Text labels near symbols (FIC-101, PT-205, etc.)
- Clear, readable text

### Step 4: Test

1. Refresh browser
2. Click instrument node
3. Should see AI-powered analysis

## Why "instrument.bubble" Appears

This is the **YOLO detection class name**, not an instrument tag:

```python
# What YOLO detects:
class_name = "instrument.bubble"  # Detection class
tag = None  # No tag extracted

# What gets displayed:
label = tag or class_name  # Falls back to class name
# Result: "instrument.bubble"
```

**To fix:** Your P&ID needs text labels that OCR can read and associate with the symbols.

## Summary

**Current State:**
- ❌ No valid Gemini API key → Simulated mode
- ❌ No instrument tags → Shows class name "instrument.bubble"
- ❌ Simulated mode can't analyze class names

**Solution:**
1. ✅ Get Gemini API key (2 minutes, free)
2. ✅ Update .env file
3. ✅ Restart backend
4. ✅ Use P&ID with text labels
5. ✅ Enjoy AI-powered analysis!

**Quick Win:**
Even without fixing tags, getting the Gemini API key will make the system smarter at analyzing whatever text it receives!

Get your free API key now: https://makersuite.google.com/app/apikey 🚀
