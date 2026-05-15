# 🏭 EDAI4 - P&ID Intelligence Platform

**AI-Powered P&ID Analysis with YOLOv8, OCR, and Graph Intelligence**

---

## 🚀 Quick Start

**New to EDAI4?** Start here:
1. **[00_START_HERE.md](00_START_HERE.md)** - Main entry point and overview
2. **[QUICK_START.md](QUICK_START.md)** - Get up and running in 5 minutes
3. **[PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)** - Complete project documentation

---

## 📚 Documentation Index

### 🎯 Core Documentation

| Document | Description |
|----------|-------------|
| **[00_START_HERE.md](00_START_HERE.md)** | Main entry point - Start here! |
| **[PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)** | Complete project overview and architecture |
| **[FRONTEND_ARCHITECTURE.md](FRONTEND_ARCHITECTURE.md)** | Frontend structure and components |
| **[QUICK_START.md](QUICK_START.md)** | Quick start guide for developers |
| **[TESTING_GUIDE.md](TESTING_GUIDE.md)** | Testing instructions and procedures |
| **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | Common issues and solutions |

### 🤖 Model & Detection

| Document | Description |
|----------|-------------|
| **[KAGGLE_YOLO_INSTRUCTIONS.md](KAGGLE_YOLO_INSTRUCTIONS.md)** | YOLO model setup and training |
| **[YOLO_QUICK_REFERENCE.md](YOLO_QUICK_REFERENCE.md)** | YOLO commands and reference |
| **[DETECTION_IMPROVEMENT_PLAN.md](DETECTION_IMPROVEMENT_PLAN.md)** | Detection optimization guide |
| **[LINE_DETECTOR_GUIDE.md](LINE_DETECTOR_GUIDE.md)** | Line and pipe detection |

### 🎨 Recent Features & Fixes

| Document | Description |
|----------|-------------|
| **[FINAL_COORDINATE_FIX_SUMMARY.md](FINAL_COORDINATE_FIX_SUMMARY.md)** | Latest coordinate mapping fix |
| **[XYXYN_FOOLPROOF_FIX.md](XYXYN_FOOLPROOF_FIX.md)** | Foolproof coordinate method using xyxyn |
| **[HISTORY_IMPLEMENTATION_COMPLETE.md](HISTORY_IMPLEMENTATION_COMPLETE.md)** | History feature documentation |
| **[EDITOR_NODE_LABELS_IMPROVED.md](EDITOR_NODE_LABELS_IMPROVED.md)** | Editor improvements and node labels |

### 🛠️ Feature Guides

| Document | Description |
|----------|-------------|
| **[HAZOP_QUICKSTART.md](HAZOP_QUICKSTART.md)** | HazOp simulator quick start |
| **[PID_EDITOR_GUIDE.md](PID_EDITOR_GUIDE.md)** | P&ID editor usage guide |
| **[QA_ASSISTANT_QUICKSTART.md](QA_ASSISTANT_QUICKSTART.md)** | Q&A assistant guide |
| **[FLOW_SIMULATOR_EXPLAINED.md](FLOW_SIMULATOR_EXPLAINED.md)** | Flow simulator documentation |

---

## 🎯 Key Features

### 1. **Interactive Canvas** 🖼️
- Pan, zoom, and explore P&ID diagrams
- Real-time bounding box overlays
- Click to select and inspect detections
- Percentage-based coordinate system (resolution-independent)

### 2. **Smart Detection** 🤖
- YOLOv8-based symbol detection (88.1% mAP50)
- SAHI for high-density diagrams
- Hybrid pipeline with multiple detection strategies
- ISA S5.1 tag recognition

### 3. **Graph Visualization** 🕸️
- Interactive topology graph
- Physics-based layout
- Node filtering and search
- Connection analysis

### 4. **P&ID Editor** ✏️
- Drag-and-drop component palette
- Visual node editing
- Connection management
- Export/import topology

### 5. **HazOp Simulator** ⚠️
- Scenario-based risk analysis
- AI-powered hazard identification
- Interactive failure simulation
- Safety recommendations

### 6. **Flow Simulator** 🌊
- Process flow simulation
- Pressure and flow calculations
- Visual flow animation
- Real-time parameter adjustment

### 7. **Q&A Assistant** 💬
- Natural language queries
- RAG-based knowledge retrieval
- Gemini AI integration
- Context-aware responses

### 8. **Processing History** 📜
- Track all processed P&IDs
- Quick reload of previous sessions
- Thumbnail previews
- Search and filter

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     EDAI4 Platform                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Layer 1    │  │   Layer 2    │  │   Layer 3    │    │
│  │   Detection  │→ │     OCR      │→ │    Graph     │    │
│  │   (YOLOv8)   │  │  (PaddleOCR) │  │   Builder    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│         ↓                  ↓                  ↓            │
│  ┌──────────────────────────────────────────────────┐     │
│  │            Layer 4: Semantic Analysis            │     │
│  │         (RAG + Knowledge Base + Gemini)          │     │
│  └──────────────────────────────────────────────────┘     │
│         ↓                                                  │
│  ┌──────────────────────────────────────────────────┐     │
│  │     Layer 5: Advanced Features & Simulation      │     │
│  │  (HazOp, Flow Sim, Editor, Q&A, Deliverables)   │     │
│  └──────────────────────────────────────────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- CUDA (optional, for GPU acceleration)

### Installation

**1. Clone the repository**
```bash
git clone <repository-url>
cd EDAI4
```

**2. Install backend dependencies**
```bash
pip install -r requirements.txt
```

**3. Install frontend dependencies**
```bash
cd frontend
npm install
```

**4. Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys
```

**5. Start the backend**
```bash
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**6. Start the frontend**
```bash
cd frontend
npm run dev
```

**7. Open browser**
```
http://localhost:5173
```

---

## 📖 Usage

### Basic Workflow

1. **Upload P&ID** - Drag and drop or click to upload
2. **Processing** - Automatic detection, OCR, and graph analysis
3. **Explore** - Use Canvas, Graph, or other views
4. **Analyze** - Run HazOp, Flow Sim, or Q&A
5. **Edit** - Modify topology in Editor
6. **Export** - Generate deliverables

### Views

- **Canvas** - Interactive P&ID with bounding boxes
- **Graph** - Topology visualization
- **Deliverables** - Generate reports and exports
- **Design Rules** - Validation and compliance
- **Flow Sim** - Process flow simulation
- **Editor** - Visual topology editing
- **HazOp** - Hazard analysis
- **History** - Previous processing sessions

---

## 🧪 Testing

Run the test suite:
```bash
pytest tests/
```

See **[TESTING_GUIDE.md](TESTING_GUIDE.md)** for detailed testing instructions.

---

## 🐛 Troubleshooting

Common issues and solutions are documented in **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**.

Quick fixes:
- **Backend not starting?** Check Python dependencies
- **Frontend blank?** Clear browser cache (Ctrl+Shift+R)
- **Detections misaligned?** See coordinate fix documentation
- **API errors?** Check .env file and API keys

---

## 📊 Performance

- **Detection Speed:** ~1-3 seconds per P&ID
- **Accuracy:** 88.1% mAP50 on validation set
- **Supported Formats:** JPG, PNG, TIFF
- **Max Image Size:** 4096x4096 pixels
- **Concurrent Users:** 10+ (depends on hardware)

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📝 License

[Your License Here]

---

## 🙏 Acknowledgments

- **YOLOv8** - Ultralytics
- **PaddleOCR** - PaddlePaddle
- **React Flow** - React Flow Team
- **Gemini AI** - Google

---

## 📞 Support

- **Documentation:** See files listed above
- **Issues:** [GitHub Issues]
- **Email:** [Your Email]

---

## 🗺️ Roadmap

### Completed ✅
- [x] YOLOv8 detection pipeline
- [x] OCR and tag extraction
- [x] Graph topology analysis
- [x] Interactive canvas
- [x] HazOp simulator
- [x] Flow simulator
- [x] P&ID editor
- [x] Q&A assistant
- [x] Processing history
- [x] Coordinate fix (xyxyn method)
- [x] Editor node labels

### Planned 🚧
- [ ] Multi-page P&ID support
- [ ] 3D visualization
- [ ] Real-time collaboration
- [ ] Mobile app
- [ ] Cloud deployment
- [ ] Advanced analytics dashboard

---

**Last Updated:** 2026-05-15

**Version:** 1.0.0

**Status:** ✅ Production Ready
