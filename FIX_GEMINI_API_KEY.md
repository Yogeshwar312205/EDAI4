# Fix Gemini API Key - Complete Guide

## Issues Found

### Issue 1: API Key Not Loading ❌
The `.env` file had `GOOGLE_API_KEY` but the value wasn't being read properly.

### Issue 2: Wrong Key Format ⚠️
The key `AQ.Ab8RN6L...` is not a valid Gemini API key. Gemini keys start with `AIza`.

## Solution: Get a Real Gemini API Key

### Step 1: Get Your API Key (2 minutes)

1. **Go to Google AI Studio:**
   ```
   https://makersuite.google.com/app/apikey
   ```

2. **Sign in with your Google account**

3. **Click "Create API Key"**

4. **Copy the key** - It should look like:
   ```
   AIzaSyC1234567890abcdefghijklmnopqrstuvwxyz
   ```
   (Starts with `AIza`)

### Step 2: Update .env File

Open `.env` file and replace the dummy key:

```bash
# Find this line:
GOOGLE_API_KEY=AIzaSyDummy_Replace_With_Your_Real_Key_From_MakerSuite

# Replace with your real key:
GOOGLE_API_KEY=AIzaSyC1234567890abcdefghijklmnopqrstuvwxyz
```

**Important:** 
- No spaces around the `=`
- No quotes around the key
- Key should be on the same line

### Step 3: Test the Key

```bash
python scripts/test_gemini_key.py
```

**Expected output:**
```
✅ API key found: AIzaSyC12...xyz
✅ Key format looks correct (starts with 'AIza')
✅ SUCCESS! Gemini API is working!
```

### Step 4: Restart Backend

```bash
# Stop current backend (Ctrl+C)
# Then restart:
python -m uvicorn src.api.main:app --reload
```

**Look for this log:**
```
✅ Gemini AI initialized successfully with API key
```

### Step 5: Test in Frontend

1. Refresh browser (Ctrl+Shift+R)
2. Click on an instrument node
3. You should see AI-powered definition!

## Common Issues

### Issue: "API key not found"

**Cause:** .env file not loaded or key is empty

**Solution:**
```bash
# Check if key is set
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('GOOGLE_API_KEY'))"

# Should print your key, not empty
```

### Issue: "Invalid API key"

**Cause:** Wrong key format or expired key

**Solution:**
1. Verify key starts with `AIza`
2. Get new key from MakerSuite
3. Make sure you copied the entire key

### Issue: "Rate limit exceeded"

**Cause:** Too many requests

**Solution:**
- Free tier: 15 requests/minute
- Wait 1 minute and try again
- Or upgrade to paid tier

### Issue: Still showing simulated mode

**Cause:** Backend not restarted or key not loaded

**Solution:**
1. Stop backend completely (Ctrl+C)
2. Verify .env has correct key
3. Restart backend
4. Check logs for "✅ Gemini AI initialized"

## What the Old Key Was

The key `AQ.Ab8RN6L...` appears to be:
- A Google Cloud API key (not for Gemini)
- An OAuth token
- Or a different Google service key

**Gemini API keys are different** and must be obtained from:
https://makersuite.google.com/app/apikey

## Verification Checklist

- [ ] Got API key from https://makersuite.google.com/app/apikey
- [ ] Key starts with `AIza`
- [ ] Updated .env file with real key
- [ ] No spaces or quotes around key
- [ ] Ran test script successfully
- [ ] Restarted backend
- [ ] Saw "✅ Gemini AI initialized" in logs
- [ ] Tested in frontend - got AI definitions

## Example .env Format

```bash
# ✅ CORRECT
GOOGLE_API_KEY=AIzaSyC1234567890abcdefghijklmnopqrstuvwxyz

# ❌ WRONG - has quotes
GOOGLE_API_KEY="AIzaSyC1234567890abcdefghijklmnopqrstuvwxyz"

# ❌ WRONG - has spaces
GOOGLE_API_KEY = AIzaSyC1234567890abcdefghijklmnopqrstuvwxyz

# ❌ WRONG - wrong key format
GOOGLE_API_KEY=AQ.Ab8RN6LXixrWFBeMadhjLLu8OZAUQOVhhnvFAvGtjWuGNvHAGw
```

## Quick Test Command

```bash
# Test if key works
curl -X POST http://localhost:8000/api/api/analyze-tag \
  -F "tag_text=FIC-101"

# Should return AI definition, not:
# "Unable to determine specific function. Configure GEMINI_API_KEY..."
```

## Summary

1. ❌ Old key `AQ.Ab8RN6L...` is not a Gemini API key
2. ✅ Get real key from https://makersuite.google.com/app/apikey
3. ✅ Update .env with key starting with `AIza`
4. ✅ Restart backend
5. ✅ Test and enjoy AI-powered analysis!

The key is free (1,500 requests/day) and takes 2 minutes to get! 🚀
