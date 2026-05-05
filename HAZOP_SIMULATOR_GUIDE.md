# HazOp Failure Simulator - Complete Implementation Guide

## 🎯 Overview

The **HazOp Failure Simulator** is an AI-powered safety analysis tool that predicts cascading effects of equipment failures in P&ID systems. It uses Google Gemini AI to act as a senior HazOp safety engineer, analyzing topology connections to identify danger zones and recommend emergency responses.

## 🏗️ Architecture

### Backend (Python + FastAPI)
- **File**: `src/api/hazop_simulator.py`
- **Endpoint**: `POST /api/simulate-hazop`
- **AI Model**: `gemini-2.5-flash` (fast, accurate, free tier)
- **SDK**: `google-genai` (NEW SDK, not deprecated `google.generativeai`)

### Frontend (React + TypeScript)
- **Component**: `frontend/src/components/HazOpSimulator.tsx`
- **UI Framework**: React Flow for graph visualization
- **Styling**: Tailwind CSS with dark industrial theme
- **State**: Zustand for global state management

## 📋 Features

### 1. **Context Menu Interaction**
- Right-click any equipment node on the canvas
- Select from 4 failure modes:
  - 🔒 **Stuck Closed** - Valve fails in closed position
  - 🔓 **Failed Open** - Valve fails in open position
  - 💧 **Leaking** - Equipment develops leak
  - 🚫 **Blocked** - Pipe or equipment becomes blocked

### 2. **AI-Powered Analysis**
The Gemini AI acts as a senior HazOp engineer and provides:
- **Hazard Summary**: 2-sentence immediate danger assessment
- **Cascading Effects**: 3-5 predicted downstream failures
- **Affected Equipment**: List of nodes in danger zone
- **Affected Connections**: List of pipes with abnormal conditions
- **Severity Level**: LOW, MEDIUM, HIGH, or CRITICAL
- **Emergency Actions**: 3-5 recommended response steps

### 3. **Visual Feedback**
- **Failed Node**: Red pulsing border with glow effect
- **Affected Nodes**: Orange border with glow
- **Affected Edges**: Animated red lines with glow
- **Analysis Panel**: Sliding panel with color-coded severity

### 4. **Structured Output**
Uses Gemini's `response_schema` feature to guarantee valid JSON:
```json
{
  "hazard_summary": "string",
  "cascading_effects": ["string"],
  "affected_node_ids": ["string"],
  "affected_edge_ids": ["string"],
  "severity_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "recommended_actions": ["string"]
}
```

## 🚀 Installation & Setup

### 1. Backend Dependencies

The required packages should already be installed, but verify:

```bash
pip install google-genai fastapi uvicorn pydantic python-dotenv
```

### 2. Environment Configuration

Your `.env` file already has the required API key:
```env
GOOGLE_API_KEY=AIzaSyB3Y8xvKuC8RPbTg10yaLPpMTtELzxVDRI
```

### 3. Frontend Dependencies

Already installed in your project:
```bash
cd frontend
npm install
# Dependencies: reactflow, axios, lucide-react, tailwindcss
```

## 🎮 Usage

### Step 1: Start Backend Server
```bash
# From project root
python -m uvicorn src.api.main:app --reload --port 8000
```

### Step 2: Start Frontend Dev Server
```bash
# From frontend directory
cd frontend
npm run dev
```

### Step 3: Use the Simulator

1. **Upload a P&ID** and process it to generate the graph
2. **Click the "HazOp" tab** in the navigation
3. **Right-click any equipment node** on the canvas
4. **Select a failure mode** from the context menu
5. **Wait for AI analysis** (2-5 seconds)
6. **Review the results** in the analysis panel
7. **Click "Clear Simulation"** to reset

## 🔧 API Reference

### POST /api/simulate-hazop

**Request Body:**
```typescript
{
  failed_node_id: string;      // ID of failed equipment
  failure_mode: string;         // Type of failure
  topology: {
    nodes: Array<{
      id: string;
      type: string;
      data: any;
      position: { x: number; y: number };
    }>;
    edges: Array<{
      id: string;
      source: string;
      target: string;
      data?: any;
    }>;
  };
}
```

**Response:**
```typescript
{
  hazard_summary: string;
  cascading_effects: string[];
  affected_node_ids: string[];
  affected_edge_ids: string[];
  severity_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  recommended_actions: string[];
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/simulate-hazop \
  -H "Content-Type: application/json" \
  -d '{
    "failed_node_id": "V-101",
    "failure_mode": "Stuck Closed",
    "topology": {
      "nodes": [...],
      "edges": [...]
    }
  }'
```

## 🎨 Customization

### Change AI Model

Edit `src/api/hazop_simulator.py`:
```python
# Use a different model
simulator = HazOpSimulator(model="models/gemini-2.5-pro")  # More powerful
# or
simulator = HazOpSimulator(model="models/gemini-2.0-flash")  # Faster
```

### Adjust Temperature

Lower temperature = more deterministic, higher = more creative:
```python
config=types.GenerateContentConfig(
    temperature=0.1,  # Very conservative (default: 0.3)
)
```

### Add More Failure Modes

Edit `frontend/src/components/HazOpSimulator.tsx`:
```typescript
const failureModes = [
  { label: 'Stuck Closed', icon: '🔒', color: 'text-red-400' },
  { label: 'Failed Open', icon: '🔓', color: 'text-orange-400' },
  { label: 'Leaking', icon: '💧', color: 'text-blue-400' },
  { label: 'Blocked', icon: '🚫', color: 'text-yellow-400' },
  // Add your custom modes here
  { label: 'Overpressure', icon: '💥', color: 'text-purple-400' },
];
```

### Customize Visual Effects

Edit the `applyVisualEffects` function:
```typescript
// Change colors, shadows, animations
style: {
  border: '3px solid #your-color',
  boxShadow: '0 0 20px #your-color',
  animation: 'pulse 1.5s ease-in-out infinite',
}
```

## 🧪 Testing

### Test Backend Endpoint
```bash
# Test with sample data
python -c "
import requests
response = requests.post('http://localhost:8000/api/simulate-hazop', json={
    'failed_node_id': 'V-101',
    'failure_mode': 'Stuck Closed',
    'topology': {
        'nodes': [
            {'id': 'V-101', 'type': 'valve', 'data': {'label': 'Control Valve'}},
            {'id': 'P-101', 'type': 'pump', 'data': {'label': 'Feed Pump'}}
        ],
        'edges': [
            {'id': 'e1', 'source': 'P-101', 'target': 'V-101'}
        ]
    }
})
print(response.json())
"
```

### Test Frontend Component
```bash
# Run in development mode with hot reload
cd frontend
npm run dev
```

## 🐛 Troubleshooting

### Issue: "google-genai package not installed"
**Solution:**
```bash
pip install google-genai
```

### Issue: "GOOGLE_API_KEY not found"
**Solution:**
Check your `.env` file has:
```env
GOOGLE_API_KEY=your_actual_key_here
```

### Issue: "API quota exceeded"
**Solution:**
- Check your quota at: https://ai.google.dev/gemini-api/docs/rate-limits
- Free tier: 15 requests/minute, 1500 requests/day
- Wait or upgrade to paid tier

### Issue: "Context menu not appearing"
**Solution:**
- Ensure you're right-clicking on a **node**, not empty space
- Check browser console for errors
- Verify React Flow is properly initialized

### Issue: "Visual effects not showing"
**Solution:**
- Check that `affected_node_ids` and `affected_edge_ids` match actual node/edge IDs
- Verify CSS animations are loaded (check `frontend/src/index.css`)
- Clear browser cache and reload

## 📊 Performance

### Response Times
- **AI Analysis**: 2-5 seconds (depends on topology size)
- **Visual Update**: <100ms
- **Total User Wait**: 2-5 seconds

### Optimization Tips
1. **Limit topology size**: Send only relevant nodes/edges (max 50 nodes, 100 edges)
2. **Use caching**: Cache results for identical scenarios
3. **Batch requests**: If simulating multiple failures, batch them
4. **Use faster model**: Switch to `gemini-2.0-flash-lite` for speed

## 🔒 Safety Considerations

### Important Notes
1. **This is a simulation tool** - Not a replacement for professional HazOp studies
2. **AI predictions may not be 100% accurate** - Always verify with domain experts
3. **Use for training and preliminary analysis** - Not for final safety decisions
4. **Conservative by design** - AI is instructed to err on the side of caution

### Recommended Use Cases
✅ Training and education  
✅ Preliminary hazard identification  
✅ Design review support  
✅ "What-if" scenario exploration  
✅ Emergency response planning  

❌ Final safety certification  
❌ Regulatory compliance documentation  
❌ Replacing professional HazOp studies  

## 📚 Additional Resources

### HazOp Methodology
- [IEC 61882:2016 - HazOp Studies](https://webstore.iec.ch/publication/24239)
- [CCPS Guidelines for HazOp](https://www.aiche.org/ccps)

### Gemini API Documentation
- [Gemini API Docs](https://ai.google.dev/gemini-api/docs)
- [Structured Output Guide](https://ai.google.dev/gemini-api/docs/structured-output)
- [Rate Limits](https://ai.google.dev/gemini-api/docs/rate-limits)

### React Flow Documentation
- [React Flow Docs](https://reactflow.dev/)
- [Custom Nodes](https://reactflow.dev/learn/customization/custom-nodes)
- [Styling](https://reactflow.dev/learn/customization/theming)

## 🎉 Success!

You now have a fully functional HazOp Failure Simulator! The system combines:
- ✅ AI-powered safety analysis
- ✅ Interactive visual feedback
- ✅ Structured, reliable outputs
- ✅ Professional industrial UI
- ✅ Real-time simulation

**Next Steps:**
1. Test with your actual P&ID data
2. Customize failure modes for your industry
3. Integrate with your safety management system
4. Train your team on the tool
5. Collect feedback and iterate

---

**Built with:**
- 🤖 Google Gemini AI (gemini-2.5-flash)
- ⚡ FastAPI + Python
- ⚛️ React + TypeScript
- 🎨 Tailwind CSS
- 📊 React Flow

**Questions or Issues?**
Check the troubleshooting section or review the code comments for detailed explanations.
