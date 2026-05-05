# 🚨 HazOp Failure Simulator

> AI-powered safety analysis tool for P&ID systems using Google Gemini

[![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.8+-blue)]()
[![React](https://img.shields.io/badge/react-18.2-blue)]()
[![Gemini](https://img.shields.io/badge/gemini-2.5--flash-orange)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

## 🎯 What is This?

The **HazOp Failure Simulator** allows engineers to simulate equipment failures in P&ID systems and instantly see:
- 🔴 **Cascading effects** through connected equipment
- ⚠️ **Danger zones** highlighted on the canvas
- 📊 **Severity assessment** (LOW/MEDIUM/HIGH/CRITICAL)
- 🛡️ **Emergency response** recommendations

**Powered by Google Gemini AI** acting as a senior HazOp safety engineer.

## ✨ Features

### 🖱️ Interactive Simulation
- Right-click any equipment node
- Select from 4 failure modes
- Get AI analysis in 2-5 seconds

### 🎨 Visual Feedback
- **Red pulsing glow** on failed equipment
- **Orange borders** on affected nodes
- **Animated red lines** on affected pipes
- **Sliding analysis panel** with detailed results

### 🤖 AI-Powered Analysis
- Traces connections through topology
- Predicts pressure build-up, cavitation, leaks
- Assesses severity and consequences
- Generates emergency action plans

### 🔒 Safety-First Design
- Conservative AI prompts
- Structured, validated outputs
- Fallback analysis when AI unavailable
- Professional industrial UI

## 🚀 Quick Start (5 Minutes)

### 1. Test Backend
```bash
python test_hazop_simulator.py
```

### 2. Start Servers
```bash
# Terminal 1 - Backend
python -m uvicorn src.api.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 3. Use Simulator
1. Open http://localhost:5173
2. Upload and process a P&ID
3. Click **"HazOp"** tab
4. Right-click any node → Select failure mode
5. Review AI analysis in sliding panel

## 📸 Screenshots

### Context Menu
```
┌─────────────────────────┐
│ ⚡ Simulate Failure      │
│ V-101                   │
├─────────────────────────┤
│ 🔒 Stuck Closed         │
│ 🔓 Failed Open          │
│ 💧 Leaking              │
│ 🚫 Blocked              │
└─────────────────────────┘
```

### Analysis Panel
```
┌──────────────────────────────────┐
│ ⚠️  HazOp Analysis Report        │
│ V-101 - Stuck Closed             │
├──────────────────────────────────┤
│ 🛡️ SEVERITY: HIGH                │
├──────────────────────────────────┤
│ ⚠️  Immediate Hazard             │
│ Valve failure causes pressure    │
│ buildup in upstream equipment... │
├──────────────────────────────────┤
│ 📊 Cascading Effects             │
│ ▸ Pressure buildup in feed line  │
│ ▸ Pump may cavitate              │
│ ▸ Tank overpressure risk         │
├──────────────────────────────────┤
│ 🎯 Affected Equipment            │
│ Nodes: P-101, T-101, V-102       │
│ Edges: e1, e2, e3                │
├──────────────────────────────────┤
│ 🛡️ Emergency Response            │
│ 1. Activate emergency shutdown   │
│ 2. Isolate affected section      │
│ 3. Monitor pressure readings     │
└──────────────────────────────────┘
```

## 🏗️ Architecture

```
User → React Frontend → FastAPI Backend → Gemini AI
         (React Flow)    (Python)         (2.5-flash)
              ↓               ↓                ↓
        Visual Effects   Structured      Safety Analysis
        Context Menu     Output          HazOp Expertise
```

**Tech Stack:**
- **Frontend**: React 18 + TypeScript + React Flow + Tailwind CSS
- **Backend**: FastAPI + Python + Pydantic
- **AI**: Google Gemini 2.5 Flash (via `google-genai` SDK)
- **State**: Zustand
- **Styling**: Dark industrial theme with red accents

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[HAZOP_QUICKSTART.md](HAZOP_QUICKSTART.md)** | 5-minute quick start guide |
| **[HAZOP_SIMULATOR_GUIDE.md](HAZOP_SIMULATOR_GUIDE.md)** | Complete implementation guide |
| **[HAZOP_ARCHITECTURE.md](HAZOP_ARCHITECTURE.md)** | System architecture diagrams |
| **[HAZOP_IMPLEMENTATION_SUMMARY.md](HAZOP_IMPLEMENTATION_SUMMARY.md)** | Implementation details |
| **[HAZOP_DEPLOYMENT_CHECKLIST.md](HAZOP_DEPLOYMENT_CHECKLIST.md)** | Pre-deployment testing |

## 🔧 Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- Google Gemini API key (free tier available)

### Backend Setup
```bash
# Install dependencies
pip install google-genai fastapi uvicorn pydantic python-dotenv

# Configure API key
echo "GOOGLE_API_KEY=your_key_here" > .env

# Test installation
python test_hazop_simulator.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 🎮 Usage Examples

### Example 1: Valve Failure
```
Node: V-101 (Control Valve)
Mode: Stuck Closed
Result: HIGH severity
- Pressure buildup in upstream line
- Pump P-101 may cavitate
- Tank T-101 overpressure risk
Actions: Isolate section, activate ESD
```

### Example 2: Pump Failure
```
Node: P-101 (Feed Pump)
Mode: Failed Open
Result: CRITICAL severity
- Uncontrolled flow into system
- Tank T-101 rapid overfilling
- Potential tank rupture/overflow
Actions: Trip pump, close valves, evacuate
```

## 🔌 API Reference

### POST /api/simulate-hazop

**Request:**
```json
{
  "failed_node_id": "V-101",
  "failure_mode": "Stuck Closed",
  "topology": {
    "nodes": [...],
    "edges": [...]
  }
}
```

**Response:**
```json
{
  "hazard_summary": "...",
  "cascading_effects": ["...", "..."],
  "affected_node_ids": ["...", "..."],
  "affected_edge_ids": ["...", "..."],
  "severity_level": "HIGH",
  "recommended_actions": ["...", "..."]
}
```

## 🎨 Customization

### Change AI Model
```python
# In src/api/hazop_simulator.py
simulator = HazOpSimulator(model="models/gemini-2.5-pro")
```

### Add Failure Modes
```typescript
// In frontend/src/components/HazOpSimulator.tsx
const failureModes = [
  { label: 'Stuck Closed', icon: '🔒', color: 'text-red-400' },
  { label: 'Your Custom Mode', icon: '💥', color: 'text-purple-400' },
];
```

### Adjust Visual Effects
```typescript
// In applyVisualEffects function
style: {
  border: '3px solid #your-color',
  boxShadow: '0 0 20px #your-color',
}
```

## 🧪 Testing

### Run Backend Tests
```bash
python test_hazop_simulator.py
```

### Manual Testing
1. Start both servers
2. Upload a P&ID
3. Navigate to HazOp tab
4. Right-click nodes and test all failure modes
5. Verify visual effects appear
6. Check analysis panel content
7. Test clear simulation

### Expected Results
- ✅ Simulation completes in 2-5 seconds
- ✅ Visual effects appear immediately
- ✅ Analysis panel shows detailed results
- ✅ Can clear and run multiple simulations

## 🐛 Troubleshooting

### "google-genai not installed"
```bash
pip install google-genai
```

### "API key not found"
```bash
# Check .env file
cat .env | grep GOOGLE_API_KEY

# Should show: GOOGLE_API_KEY=AIza...
```

### "Context menu not appearing"
- Make sure you're right-clicking on a **node** (not empty space)
- Check browser console (F12) for errors
- Verify you're on the "HazOp" tab

### "API quota exceeded"
- Free tier: 15 requests/minute, 1500/day
- Wait 1 minute and retry
- Or upgrade at https://ai.google.dev/pricing

## 📊 Performance

- **Response Time**: 2-5 seconds
- **Visual Update**: <100ms
- **API Quota**: 15 req/min (free tier)
- **Topology Limit**: 50 nodes, 100 edges (optimized)

## 🔒 Safety Disclaimer

⚠️ **Important**: This is a simulation tool for training and preliminary analysis.

**✅ Use for:**
- Training and education
- Preliminary hazard identification
- Design review support
- "What-if" scenario exploration

**❌ Not for:**
- Final safety certification
- Regulatory compliance
- Replacing professional HazOp studies
- Critical safety decisions without expert review

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional failure modes
- Enhanced visual effects
- Export to PDF reports
- Integration with safety management systems
- Multi-language support

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- **Google Gemini AI** for powerful language models
- **React Flow** for excellent graph visualization
- **FastAPI** for modern Python web framework
- **Tailwind CSS** for beautiful styling

## 📞 Support

### Documentation
- Read the [Quick Start Guide](HAZOP_QUICKSTART.md)
- Check the [Complete Guide](HAZOP_SIMULATOR_GUIDE.md)
- Review the [Architecture](HAZOP_ARCHITECTURE.md)

### Issues
- Check [Troubleshooting](#-troubleshooting) section
- Review code comments
- Check browser console (F12)
- Verify API key and quota

### Resources
- [Gemini API Docs](https://ai.google.dev/gemini-api/docs)
- [React Flow Docs](https://reactflow.dev/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)

---

## 🎉 Ready to Simulate!

```bash
# Start the system
python -m uvicorn src.api.main:app --reload --port 8000
cd frontend && npm run dev

# Open browser
http://localhost:5173

# Start simulating failures! 🚀
```

---

**Built with ❤️ for process safety engineers**

**Version**: 1.0.0  
**Status**: ✅ Production Ready  
**Last Updated**: May 5, 2026
