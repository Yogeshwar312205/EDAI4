# EDAI4 - Complete Project Guide

## 🎯 Project Overview

EDAI4 is a complete AI-powered system for digitizing P&ID (Piping & Instrumentation Diagrams) with a modern, interactive web interface.

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EDAI4 Full Stack                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Frontend (React + TypeScript)          │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │    │
│  │  │ Interactive  │  │  Data Table  │  │  Graph   │ │    │
│  │  │   Canvas     │  │  (TanStack)  │  │  Viewer  │ │    │
│  │  │ (React-Konva)│  │              │  │ (React   │ │    │
│  │  │              │  │              │  │  Flow)   │ │    │
│  │  └──────────────┘  └──────────────┘  └──────────┘ │    │
│  │         │                  │                │       │    │
│  │         └──────────────────┼────────────────┘       │    │
│  │                            │                        │    │
│  │                   ┌────────▼────────┐               │    │
│  │                   │  Zustand Store  │               │    │
│  │                   └────────┬────────┘               │    │
│  └────────────────────────────┼────────────────────────┘    │
│                                │ HTTP/JSON                   │
│  ┌────────────────────────────▼────────────────────────┐    │
│  │              Backend (FastAPI + Python)              │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │    │
│  │  │ Layer 1  │  │ Layer 2  │  │ Layer 3  │          │    │
│  │  │  YOLO    │→ │   OCR    │→ │  Graph   │          │    │
│  │  │ Detection│  │ Parsing  │  │ Builder  │          │    │
│  │  └──────────┘  └──────────┘  └──────────┘          │    │
│  │       ↓             ↓             ↓                 │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │    │
│  │  │ Layer 4  │  │ Layer 5  │  │   API    │          │    │
│  │  │ Semantic │  │   RAG    │  │ Endpoints│          │    │
│  │  │ Enricher │  │ Pipeline │  │          │          │    │
│  │  └──────────┘  └──────────┘  └──────────┘          │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start (Both Frontend & Backend)

### Prerequisites
- Python 3.11+
- Node.js 18+
- YOLO model (`best.pt`)

### 1. Setup Backend

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env and add GOOGLE_API_KEY if using LLM features

# Start FastAPI server
python -m uvicorn src.api.main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000`

### 2. Setup Frontend

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at `http://localhost:3000`

### 3. Test the System

1. Open `http://localhost:3000` in browser
2. Upload a P&ID image
3. Wait for processing
4. Explore the interactive features:
   - Pan/zoom canvas
   - Click table rows to zoom
   - View topology graph

## 📦 Project Structure

```
EDAI4/
├── frontend/                      # React Frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── InteractiveCanvas.tsx
│   │   │   ├── DataTable.tsx
│   │   │   ├── GraphViewer.tsx
│   │   │   └── FileUpload.tsx
│   │   ├── store/
│   │   │   └── useAppStore.ts
│   │   ├── lib/
│   │   │   └── api.ts
│   │   ├── types/
│   │   │   └── api.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── src/                           # Python Backend
│   ├── api/
│   │   └── main.py               # FastAPI endpoints
│   ├── perception/               # Layer 1 & 2
│   │   ├── symbol_detector.py
│   │   ├── ocr_engine.py
│   │   ├── hybrid_pipeline.py
│   │   └── perception_pipeline.py
│   ├── topology/                 # Layer 3
│   │   ├── graph_builder.py
│   │   ├── spatial_analyzer.py
│   │   └── flow_analyzer.py
│   ├── cognitive/                # Layer 4 & 5
│   │   ├── isa_validator.py
│   │   ├── semantic_enricher.py
│   │   ├── knowledge_base.py
│   │   └── rag_pipeline.py
│   └── utils/
│       ├── logger.py
│       └── helpers.py
│
├── models/
│   └── yolov8/
│       └── best.pt               # YOLO model
│
├── config/
│   ├── settings.yaml
│   ├── instrument_rules.yaml
│   └── safety_rules.yaml
│
├── tests/                        # Test suite
│   ├── test_layer2_*.py
│   ├── test_layer3_*.py
│   ├── test_layer4_*.py
│   └── test_layer5_*.py
│
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
│
└── Documentation/
    ├── FRONTEND_QUICK_START.md
    ├── FRONTEND_SETUP_GUIDE.md
    ├── FRONTEND_ARCHITECTURE.md
    ├── FRONTEND_IMPLEMENTATION_SUMMARY.md
    ├── LAYER2_COMPLETE.md
    ├── LAYER3_COMPLETE.md
    ├── LAYER4_COMPLETE.md
    └── LAYER5_COMPLETE.md
```

## 🎨 Frontend Features

### 1. Interactive Pan/Zoom Canvas
- **Library**: React-Konva
- **Features**:
  - Smooth pan (drag) and zoom (mouse wheel)
  - Bounding boxes with hover tooltips
  - Click to select with highlight
  - Auto-zoom to detection on table click

### 2. Cross-Linked Data Table
- **Library**: TanStack Table v8
- **Features**:
  - Sortable columns
  - Global search/filter
  - Click row → canvas zooms to detection
  - Confidence bars and category badges

### 3. Topology Graph Viewer
- **Library**: React Flow
- **Features**:
  - Physics-based layout
  - Draggable nodes
  - Color-coded by type
  - Animated edges

## 🔧 Backend Features

### Layer 1: Visual Perception
- YOLOv8s with 88.1% mAP50
- 16 E&I super-classes
- SAHI for large images

### Layer 2: Text Extraction
- EasyOCR / PaddleOCR
- ISA S5.1 tag parsing
- Text-symbol association

### Layer 3: Topology & Graph
- NetworkX graph construction
- Spatial analysis
- Flow path detection

### Layer 4: Semantic Interpretation
- ISA tag validation
- Control strategy classification
- Consistency checking

### Layer 5: RAG Intelligence
- Knowledge base
- Natural language queries
- Optional LLM enhancement

## 📊 API Endpoints

### Core Endpoints

#### POST /process
Upload and process P&ID image

**Request**:
```bash
curl -X POST http://localhost:8000/process \
  -F "file=@pid_image.jpg"
```

**Response**:
```json
{
  "image_name": "pid_image.jpg",
  "processing_time_ms": 1234.5,
  "layer1_detections": 25,
  "layer2_instruments": 12,
  "layer3_nodes": 30,
  "layer3_edges": 15,
  "detections": [
    {
      "class_name": "instrument.bubble",
      "confidence": 0.98,
      "bbox": { "x1": 100, "y1": 150, "x2": 150, "y2": 200 },
      "tag": "FIC-101"
    }
  ],
  "graph_summary": { "mode": "hybrid", ... }
}
```

#### GET /graph
Get topology graph data

**Response**:
```json
{
  "nodes": [
    {
      "id": "node_1",
      "type": "instrument",
      "tag": "FT-101",
      "label": "Flow Transmitter",
      "x": 100,
      "y": 150
    }
  ],
  "edges": [
    {
      "source": "node_1",
      "target": "node_2",
      "type": "signal"
    }
  ]
}
```

#### POST /query
Natural language query

**Request**:
```json
{
  "question": "What instruments measure flow?",
  "use_llm": false
}
```

**Response**:
```json
{
  "answer": "Found 5 flow instruments: FT-101, FT-102, ...",
  "confidence": 0.95,
  "sources": ["graph_analysis", "knowledge_base"],
  "intent": "tag_list"
}
```

#### GET /health
Health check

**Response**:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "layers_ready": {
    "layer1_yolo": true,
    "layer2_ocr": true,
    "layer3_graph": true,
    "layer4_semantic": true,
    "layer5_rag": true
  },
  "timestamp": "2026-04-10T12:00:00"
}
```

## 🔄 Data Flow

### Complete Processing Pipeline

```
1. User uploads P&ID image
   ↓
2. Frontend sends to POST /process
   ↓
3. Backend Layer 1: YOLO detects symbols
   ↓
4. Backend Layer 2: OCR extracts text, parses tags
   ↓
5. Backend Layer 3: Builds topology graph
   ↓
6. Backend Layer 4: Validates and enriches
   ↓
7. Backend Layer 5: Prepares for RAG queries
   ↓
8. Backend returns JSON with detections
   ↓
9. Frontend displays in canvas and table
   ↓
10. User clicks table row
   ↓
11. Zustand updates selectedNodeId
   ↓
12. Canvas zooms to detection
```

## 🎯 Key Features

### Cross-Component Synchronization

The critical feature - table click → canvas zoom - works via Zustand:

```typescript
// DataTable.tsx
const handleRowClick = (rowId: string) => {
  setSelectedNodeId(rowId);  // Update global state
  setActiveView('canvas');   // Switch to canvas view
};

// InteractiveCanvas.tsx
useEffect(() => {
  if (selectedNodeId) {
    // Calculate center and zoom
    const centerX = (bbox.x1 + bbox.x2) / 2;
    const centerY = (bbox.y1 + bbox.y2) / 2;
    
    // Animate zoom
    stage.to({
      x: stageSize.width / 2 - centerX * 2,
      y: stageSize.height / 2 - centerY * 2,
      scaleX: 2,
      scaleY: 2,
      duration: 0.5,
    });
  }
}, [selectedNodeId]);
```

## 🐛 Troubleshooting

### Backend Issues

**YOLO model not found**:
```bash
# Download or place best.pt in models/yolov8/
# Or set environment variable
export YOLO_MODEL_PATH=/path/to/best.pt
```

**Import errors**:
```bash
pip install -r requirements.txt
```

**Port already in use**:
```bash
# Change port
python -m uvicorn src.api.main:app --port 8001
```

### Frontend Issues

**Canvas not rendering**:
- Check browser console for errors
- Verify image uploaded successfully
- Ensure backend is running

**Table-Canvas sync not working**:
- Click a table row
- Check Zustand store in React DevTools
- Verify selectedNodeId is updating

**Backend connection failed**:
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check Vite proxy config
# Edit frontend/vite.config.ts if needed
```

## 📚 Documentation

### Frontend
- **Quick Start**: `FRONTEND_QUICK_START.md`
- **Setup Guide**: `FRONTEND_SETUP_GUIDE.md`
- **Architecture**: `FRONTEND_ARCHITECTURE.md`
- **Summary**: `FRONTEND_IMPLEMENTATION_SUMMARY.md`
- **Component Docs**: `frontend/README.md`

### Backend
- **Layer 2**: `LAYER2_COMPLETE.md`
- **Layer 3**: `LAYER3_COMPLETE.md`
- **Layer 4**: `LAYER4_COMPLETE.md`
- **Layer 5**: `LAYER5_COMPLETE.md`
- **Current Status**: `CURRENT_STATUS_AND_OPTIONS.md`

## 🚀 Deployment

### Development
```bash
# Terminal 1: Backend
python -m uvicorn src.api.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Production

#### Backend
```bash
# Build and run with Gunicorn
gunicorn src.api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

#### Frontend
```bash
cd frontend
npm run build
# Serve dist/ folder with Nginx or CDN
```

#### Docker Compose
```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - YOLO_MODEL_PATH=/app/models/yolov8/best.pt
  
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
```

## 📊 Performance

### Backend
- YOLO inference: ~7ms per image
- OCR processing: ~200ms per image
- Graph building: ~50ms
- Total processing: ~300ms typical

### Frontend
- Initial load: ~1.5s
- Canvas pan/zoom: 60 FPS
- Table render (100 rows): ~50ms
- Table search: ~20ms
- Graph render (50 nodes): ~150ms
- Table → Canvas zoom: ~500ms

## 🎉 Success Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Can upload P&ID image
- [ ] Canvas displays with bounding boxes
- [ ] Can pan and zoom smoothly
- [ ] Hover shows tooltips
- [ ] Table displays all detections
- [ ] Can search and sort table
- [ ] **Clicking table row zooms canvas** ✨
- [ ] Graph view displays topology
- [ ] Can drag nodes in graph
- [ ] Health check returns OK

## 🔮 Future Enhancements

1. **RAG Query Interface**: Add search panel for natural language queries
2. **Export Features**: Download results as JSON/Excel/PDF
3. **Annotation Tools**: Draw on canvas, add notes
4. **Multi-Image Support**: Process multiple P&IDs
5. **Real-time Collaboration**: WebSocket updates
6. **Mobile Responsive**: Touch gestures
7. **Accessibility**: ARIA labels, keyboard navigation

## 📞 Support

For issues or questions:
1. Check relevant documentation files
2. Review troubleshooting sections
3. Inspect browser/server console logs
4. Verify all dependencies are installed
5. Test with sample P&ID images

---

**EDAI4 is now complete with a modern, interactive frontend and powerful AI backend!**
