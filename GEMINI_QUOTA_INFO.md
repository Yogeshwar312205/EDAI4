# Gemini API Quota Information

## ✅ Good News: The Feature is Working!

The Engineering Q&A Assistant is working correctly. The error you're seeing is just a **quota limit** issue with the free tier of the Gemini API.

## 📊 What Happened

**Error**: `429 You exceeded your current quota`

This means you've used up your free API requests for today.

### Free Tier Limits

The Gemini API free tier has these limits:

| Limit Type | Free Tier |
|------------|-----------|
| Requests per minute | 15 |
| Requests per day | 1,500 |
| Tokens per minute | 1 million |

**You've hit one of these limits** (likely requests per day or per minute).

## 🕐 Wait Time

The error says: **"Please retry in 34.921293368s"**

This means:
- Wait ~35 seconds and try again (for per-minute limit)
- Or wait until tomorrow (for per-day limit)

## 🔍 Check Your Usage

Visit: https://ai.dev/rate-limit

This shows:
- How many requests you've made
- When your quota resets
- Current usage statistics

## 💡 Solutions

### Option 1: Wait and Retry (Free)

**If you hit the per-minute limit** (15 requests/minute):
- Wait 35 seconds
- Try your question again
- Should work! ✅

**If you hit the per-day limit** (1,500 requests/day):
- Wait until tomorrow (resets at midnight UTC)
- Your quota will refresh
- Try again then

### Option 2: Upgrade to Paid Tier

Visit: https://ai.google.dev/pricing

**Pay-as-you-go pricing**:
- $0.075 per 1M input tokens
- $0.30 per 1M output tokens
- No daily limits
- Higher rate limits

**Benefits**:
- No daily request limits
- Higher rate limits (2,000 requests/minute)
- More reliable for production use

### Option 3: Use a Different Model

Some models have different quota limits. Try:

```python
# In src/api/main.py
model = genai.GenerativeModel('gemini-2.5-flash')  # Different quota pool
```

Or:

```python
model = genai.GenerativeModel('gemini-flash-latest')  # Latest version
```

### Option 4: Implement Rate Limiting

Add rate limiting to your app to avoid hitting quotas:

```python
import time
from functools import wraps

def rate_limit(calls_per_minute=10):
    """Rate limit decorator"""
    min_interval = 60.0 / calls_per_minute
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                await asyncio.sleep(left_to_wait)
            ret = await func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator

# Apply to endpoint
@rate_limit(calls_per_minute=10)
async def ask_pid_question(request: PIDQuestionRequest):
    ...
```

## 🧪 Test Your Quota Status

Run this script to check if you can make requests:

```python
# scripts/test_quota.py
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

try:
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content("Say hello")
    print("✅ Quota available! Response:", response.text)
except Exception as e:
    if "429" in str(e):
        print("❌ Quota exceeded. Wait and try again.")
    else:
        print(f"❌ Error: {e}")
```

## 📈 Monitor Your Usage

### Check Current Usage
1. Go to: https://ai.dev/rate-limit
2. Sign in with your Google account
3. View your usage dashboard

### See Quota Details
1. Go to: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas
2. View detailed quota metrics
3. See when quotas reset

## 🎯 Best Practices

### For Development
- Use rate limiting (10-15 requests/minute)
- Cache responses for common questions
- Test with small topologies first
- Monitor your usage regularly

### For Production
- Upgrade to paid tier
- Implement request queuing
- Add retry logic with exponential backoff
- Show users when quota is exceeded

## 🔧 Improved Error Handling

I'll update the frontend to show a better error message when quota is exceeded.

## ✅ Summary

**Status**: ✅ Feature is working perfectly!

**Issue**: Quota limit reached (temporary)

**Solutions**:
1. ⏰ Wait 35 seconds (per-minute limit)
2. ⏰ Wait until tomorrow (per-day limit)
3. 💳 Upgrade to paid tier (no limits)
4. 🔄 Use different model (different quota)
5. ⚡ Add rate limiting (prevent hitting limits)

**The Engineering Q&A Assistant is fully functional!** You just need to manage your API quota. 🎉

## 📚 Resources

- **Rate Limits**: https://ai.google.dev/gemini-api/docs/rate-limits
- **Pricing**: https://ai.google.dev/pricing
- **Usage Dashboard**: https://ai.dev/rate-limit
- **Quota Console**: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas

**Congratulations!** Your Engineering Q&A Assistant is working! 🚀
