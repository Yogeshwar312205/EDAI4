# Quick Start - Smart OCR Tag Explainer

## 3-Minute Setup

### Step 1: Install Dependency (30 seconds)

```bash
pip install google-generativeai
```

### Step 2: Get API Key (1 minute)

1. Visit: https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key

### Step 3: Configure (30 seconds)

```bash
# Run setup script
python scripts/setup_gemini.py

# Or manually add to .env:
echo "GEMINI_API_KEY=your_key_here" >> .env
```

### Step 4: Restart Backend (30 seconds)

```bash
python -m uvicorn src.api.main:app --reload
```

### Step 5: Test (30 seconds)

1. Open frontend
2. Process a P&ID image
3. Click any instrument node (blue circle)
4. See AI-powered definition! 🎉

## That's It!

You now have AI-powered tag analysis in your P&ID viewer.

## What You Get

- **Instant Definitions** - Click any instrument, get explanation
- **ISA Standard** - Based on industry standards
- **Fast** - <1 second response time
- **Free** - 1,500 requests/day free tier

## Example

Click on "FIC-101" node:

```
🤖 AI Tag Explainer

Tag: FIC-101

Definition: Flow Indicator Controller - Measures flow rate 
and provides automatic control to maintain desired flow 
setpoint in the process line.

Powered by Google Gemini AI
```

## Need Help?

See full documentation: `SMART_OCR_TAG_EXPLAINER.md`
