# 🔍 Debug Gemini Issue - Step by Step

## 🎯 Current Situation

You're still getting fallback mode, which means:
- ✅ Fallback is working (good!)
- ❌ Gemini API is still failing (need to fix)

---

## 🚀 STEP-BY-STEP FIX

### Step 1: Test Your API Key

Run this test script:
```bash
python test_gemini_model.py
```

**What to look for**:
```
✓ API Key found: AIzaSyB3Y8xvKuC8RPbT...DRI
✓ google-generativeai package installed
✓ API configured

Testing: gemini-1.5-flash
----------------------------------------------------------------------
✅ SUCCESS!
   Response: Hello there, how are you?
```

**If you see SUCCESS** → Your API key works! Go to Step 2.

**If you see QUOTA ERROR** → Your API key might be restricted. Go to Step 3.

---

### Step 2: Restart Backend (CRITICAL!)

**You MUST restart the backend for code changes to take effect!**

```bash
# 1. Stop current backend
#    Press Ctrl+C in the terminal running the backend

# 2. Start backend again
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Look for this in startup logs**:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Then test the chatbot again.**

---

### Step 3: Check API Key Restrictions

Your API key might have restrictions. Let's check:

#### 3.1 Visit Google AI Studio
https://makersuite.google.com/app/apikey

#### 3.2 Check Your API Key
- Click on your API key
- Look for "API restrictions"
- Make sure "Generative Language API" is enabled

#### 3.3 Create New API Key (If Needed)
1. Click "Create API Key"
2. Select "Create API key in new project"
3. Copy the new key
4. Update `.env` file:
   ```
   GOOGLE_API_KEY=YOUR_NEW_KEY_HERE
   ```
5. Restart backend

---

### Step 4: Check Backend Logs

When you ask a question, look at the backend terminal for these messages:

**Good (Working)**:
```
[INFO] Asking Gemini about P&ID: List all instruments
[INFO] Gemini response length: 1234 characters
```

**Bad (Still Failing)**:
```
[WARNING] Gemini API quota exceeded, using fallback analysis
```

If you see the WARNING, the API is still failing.

---

### Step 5: Manual API Test

Open Python and test directly:

```python
import google.generativeai as genai

# Use YOUR API key
genai.configure(api_key="AIzaSyB3Y8xvKuC8RPbTg10yaLPpMTtELzxVDRI")

# Test gemini-1.5-flash
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content("Say hello")
print(response.text)
```

**Expected**: Should print "Hello!" or similar

**If you get error**: Copy the FULL error message and we'll debug it.

---

## 🐛 Common Issues & Solutions

### Issue 1: "Did you restart backend?"

**Symptom**: Still seeing fallback mode

**Solution**: 
```bash
# Stop backend (Ctrl+C)
# Start again
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Verify**: Look for "Application startup complete" in logs

---

### Issue 2: "API key not working"

**Symptom**: 
```
google.api_core.exceptions.PermissionDenied: 403 API key not valid
```

**Solution**:
1. Go to https://makersuite.google.com/app/apikey
2. Create NEW API key
3. Update `.env` file
4. Restart backend

---

### Issue 3: "Model not available"

**Symptom**:
```
Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, 
limit: 0, model: gemini-1.5-flash
```

**Solution**: This means even gemini-1.5-flash is not available. Try:

1. **Check if Gemini API is enabled**:
   - Visit: https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com
   - Click "Enable"

2. **Try gemini-1.0-pro instead**:
   Edit `src/api/main.py`:
   ```python
   model = genai.GenerativeModel('gemini-1.0-pro')
   ```

3. **Create API key in NEW project**:
   - Go to https://makersuite.google.com/app/apikey
   - Click "Create API key in new project"
   - Use that key

---

### Issue 4: "Package not installed"

**Symptom**:
```
ModuleNotFoundError: No module named 'google.generativeai'
```

**Solution**:
```bash
pip install google-generativeai
```

---

### Issue 5: "Backend not picking up changes"

**Symptom**: Code changed but still using old model

**Solution**:
1. Make sure you saved the file
2. Stop backend completely (Ctrl+C)
3. Start fresh (don't use --reload flag first time):
   ```bash
   python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
   ```

---

## 🧪 Verification Checklist

Run through this checklist:

- [ ] **Step 1**: Run `python test_gemini_model.py`
  - [ ] See "✅ SUCCESS" for at least one model
  
- [ ] **Step 2**: Restart backend
  - [ ] See "Application startup complete"
  
- [ ] **Step 3**: Upload P&ID in frontend
  
- [ ] **Step 4**: Ask question: "List all instruments"
  
- [ ] **Step 5**: Check response
  - [ ] Should NOT see "Rule-Based Mode"
  - [ ] Should see actual AI analysis
  
- [ ] **Step 6**: Check backend logs
  - [ ] Should see "[INFO] Gemini response length: XXX"
  - [ ] Should NOT see "[WARNING] quota exceeded"

---

## 📊 Expected vs Actual

### Expected (Working)
```
User: "List all instruments"

Backend logs:
[INFO] Asking Gemini about P&ID: List all instruments
[INFO] Topology: 25 nodes, 30 edges
[INFO] Gemini response length: 1234 characters

Response:
Based on the P&ID topology analysis, here are the instruments:

**Flow Instruments:**
- FT-101: Flow Transmitter
- FT-102: Flow Transmitter
...
```

### Actual (Your Current)
```
User: "List all instruments"

Backend logs:
[WARNING] Gemini API quota exceeded, using fallback analysis

Response:
**P&ID Analysis (Rule-Based Mode)**
*Note: Gemini API quota exceeded. Using fallback analysis.*
...
```

---

## 🎯 Quick Debug Commands

### 1. Test API Key
```bash
python test_gemini_model.py
```

### 2. Check Backend Process
```bash
# Windows
tasklist | findstr python

# Should show python.exe running
```

### 3. Check Backend Logs
Look at the terminal where backend is running.

### 4. Test API Directly
```python
import google.generativeai as genai
genai.configure(api_key="YOUR_KEY")
model = genai.GenerativeModel('gemini-1.5-flash')
print(model.generate_content("test").text)
```

---

## 💡 Most Likely Issues

Based on your situation, the most likely issues are:

### 1. Backend Not Restarted (90% chance)
**Solution**: Stop and restart backend

### 2. API Key Restrictions (5% chance)
**Solution**: Create new API key in new project

### 3. Model Still Not Available (5% chance)
**Solution**: Try gemini-1.0-pro instead

---

## 🚀 Action Plan

**Do this RIGHT NOW**:

1. **Run test script**:
   ```bash
   python test_gemini_model.py
   ```
   
2. **Copy the output** and send it to me

3. **Restart backend**:
   ```bash
   python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Test chatbot** and tell me:
   - Do you still see "Rule-Based Mode"?
   - What do the backend logs say?

---

## 📞 Send Me This Info

To help you further, send me:

1. **Output of test script**:
   ```bash
   python test_gemini_model.py
   ```

2. **Backend startup logs** (first 20 lines)

3. **Backend logs when you ask a question**

4. **The exact response** you get from chatbot

With this info, I can pinpoint the exact issue!

---

**Run the test script NOW and send me the output!** 🚀
