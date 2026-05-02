# ⚡ FIX GEMINI NOW - 2 Steps

## 🎯 The Problem

**gemini-2.0-flash has limit=0 for free tier** (it's paid-only now)

Your code was using the wrong model!

---

## ✅ The Fix (Already Applied)

Changed from:
```python
❌ gemini-2.0-flash  (limit: 0)
```

To:
```python
✅ gemini-1.5-flash  (limit: 1,500/day)
```

---

## 🚀 What You Do Now

### Step 1: Restart Backend
```bash
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 2: Test
- Upload P&ID
- Ask: "List all instruments"
- ✅ Should work!

---

## 📊 Quick Facts

| Model | Free? | Limit |
|-------|-------|-------|
| gemini-2.0-flash | ❌ NO | 0 |
| gemini-1.5-flash | ✅ YES | 1,500/day |

---

## ✅ Status

**Fixed**: ✅ Code updated to use gemini-1.5-flash  
**Action**: Restart backend and test  
**Expected**: No more 429 errors!  

---

**RESTART BACKEND NOW!** 🚀
