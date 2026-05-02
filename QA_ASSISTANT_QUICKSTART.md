# Engineering Q&A Assistant - Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Verify Gemini API Key

```bash
# Check your .env file
cat .env | grep GOOGLE_API_KEY

# Should show: GOOGLE_API_KEY=AIzaSy...
```

If missing, add it:
```bash
echo "GOOGLE_API_KEY=AIzaSyYourKeyHere" >> .env
```

Get your free API key: https://makersuite.google.com/app/apikey

### Step 2: Restart Backend

```bash
# Stop current backend (Ctrl+C)
# Then restart:
python -m uvicorn src.api.main:app --reload --port 8000
```

Look for this in the logs:
```
✅ Gemini AI initialized successfully
```

### Step 3: Test It!

**Option A: Use the Frontend**
1. Open your browser to the frontend
2. Load a P&ID (process an image)
3. Look for the floating "Ask about P&ID" button in bottom-right
4. Click it and ask a question!

**Option B: Test with Script**
```bash
python scripts/test_qa_assistant.py
```

**Option C: Test with curl**
```bash
curl -X POST http://localhost:8000/api/api/ask-pid \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What instruments are in this P&ID?",
    "topology": {
      "nodes": [
        {"id": "node_1", "type": "instrument", "tag": "FE", "label": "FE", "x": 100, "y": 200}
      ],
      "edges": []
    }
  }'
```

## 🎯 What You'll See

### In the Frontend

**Closed State**:
```
[💬 Ask about P&ID] ← Floating button in bottom-right
```

**Open State**:
```
┌────────────────────────────────────┐
│ 🤖 Engineering Q&A                 │
│    Powered by Gemini AI      [_][X]│
├────────────────────────────────────┤
│ Ask me anything about this P&ID!   │
│                                    │
│ 💡 Try asking:                     │
│ • What instruments measure flow?   │
│ • Trace flow path from inlet...    │
│ • What control loops are present?  │
├────────────────────────────────────┤
│ [Type your question...........] [→]│
│ 69 nodes • 12 edges loaded         │
└────────────────────────────────────┘
```

### Example Conversation

**You**: "What instruments are measuring flow?"

**AI**: 
```
Based on the topology analysis, I found 3 flow instruments:

1. **FE (Flow Element)** - node_5
   - Primary flow sensing element
   - Connected to FT-101 via signal edge

2. **FT-101 (Flow Transmitter)** - node_12
   - Measures and transmits flow rate signal
   - Connected to FIC-101

3. **FIC-101 (Flow Indicator Controller)** - node_18
   - Displays flow rate and provides automatic control
   - Connected to control valve CV-101

These instruments form a complete flow control loop.
```

## 💡 Example Questions to Try

### Basic Questions
- "What instruments are in this P&ID?"
- "How many valves are there?"
- "List all the equipment"

### Flow Analysis
- "Trace the flow path from inlet to outlet"
- "What is connected to node_5?"
- "Show me the flow through the pump"

### Control Systems
- "What control loops are present?"
- "Explain the FIC-101 control loop"
- "What instruments control temperature?"

### Safety Systems
- "List all safety instruments"
- "What pressure relief valves are installed?"
- "Identify all high/low alarms"

### Connections
- "What is connected to the pump?"
- "Show all instruments connected to FT-101"
- "Trace signals from PT-205"

## 🎨 UI Features

### Controls
- **Send**: Press Enter or click → button
- **Clear**: Click "Clear conversation" to start fresh
- **Minimize**: Click [-] to minimize to header only
- **Close**: Click [X] to close (reopens with floating button)

### Visual Feedback
- **Loading**: Spinner with "Analyzing topology..." message
- **User messages**: Blue bubbles on right
- **AI messages**: Dark bubbles on left with 🤖 icon
- **Timestamps**: Small text below each message
- **Node/edge count**: Shows at bottom of input area

## 🔧 Troubleshooting

### Issue: Button doesn't appear

**Check**:
1. Is the graph loaded? (Process a P&ID first)
2. Open browser console - any errors?
3. Refresh the page (Ctrl+Shift+R)

### Issue: "Gemini API not configured"

**Solution**:
```bash
# Check if key is set
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('GOOGLE_API_KEY'))"

# Should print your key, not None

# If None, add to .env:
echo "GOOGLE_API_KEY=AIzaSy..." >> .env

# Restart backend
```

### Issue: AI gives generic answers

**Possible causes**:
1. Topology not being sent (check Network tab in browser)
2. Nodes don't have proper tags
3. Graph is empty or has no edges

**Solution**:
- Ensure P&ID is processed and graph is loaded
- Check that nodes have tags and types
- Try a more specific question

### Issue: Slow responses

**Normal**: AI takes 2-5 seconds to analyze topology

**Too slow** (>10 seconds):
1. Check internet connection
2. Verify Gemini API quota not exceeded
3. Try with smaller topology (fewer nodes)

## 📊 What Gets Sent to AI

The frontend sends:
```json
{
  "question": "Your question here",
  "topology": {
    "nodes": [
      {
        "id": "node_1",
        "type": "instrument",
        "tag": "FE",
        "label": "FE",
        "x": 100.5,
        "y": 200.3
      }
    ],
    "edges": [
      {
        "source": "node_1",
        "target": "node_2",
        "type": "connected_to"
      }
    ]
  }
}
```

The AI receives:
- All node IDs, types, tags, labels, and positions
- All edge connections (source, target, type)
- Summary statistics (node counts by type)
- Expert system prompt for chemical engineering

## 🎓 Tips for Best Results

### Write Clear Questions
✅ **Good**: "What instruments measure flow in this P&ID?"
❌ **Bad**: "flow stuff?"

### Be Specific
✅ **Good**: "Trace flow from node_5 to node_12"
❌ **Bad**: "show me stuff"

### Use Engineering Terms
✅ **Good**: "Explain the control loop for FIC-101"
❌ **Bad**: "what does that thing do?"

### Ask About Topology
✅ **Good**: "What is connected to the pump?"
❌ **Bad**: "Is this a good design?" (too subjective)

### Follow Up
✅ **Good**: Ask follow-up questions to dig deeper
✅ **Good**: Reference previous answers in new questions

## 🎉 You're Ready!

The Engineering Q&A Assistant is now fully functional. Just:

1. ✅ Verify API key is set
2. ✅ Restart backend
3. ✅ Load a P&ID in the frontend
4. ✅ Click the floating chat button
5. ✅ Ask your first question!

**Need help?** Check `ENGINEERING_QA_ASSISTANT.md` for detailed documentation.

**Happy analyzing!** 🚀
