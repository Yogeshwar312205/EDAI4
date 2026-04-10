"""
EDAI4 - FastAPI Web Interface
==============================
REST API for the P&ID extraction pipeline.
"""

import os
import io
import base64
import tempfile
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# Load environment variables FIRST (before any other imports that might need them)
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Form
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# EDAI4 imports will be done lazily to avoid import errors if deps missing


# =============================================================================
# Pydantic Models
# =============================================================================

class DetectionResult(BaseModel):
    """Single detection result."""
    class_name: str
    confidence: float
    bbox: Dict[str, float]
    tag: Optional[str] = None


class ProcessingResult(BaseModel):
    """Full processing result."""
    image_name: str
    processing_time_ms: float
    layer1_detections: int
    layer2_instruments: int
    layer3_nodes: int
    layer3_edges: int
    detections: List[DetectionResult]
    graph_summary: Dict[str, Any]


class QueryRequest(BaseModel):
    """RAG query request."""
    question: str
    use_llm: bool = False


class QueryResponse(BaseModel):
    """RAG query response."""
    answer: str
    confidence: float
    sources: List[str]
    intent: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    layers_ready: Dict[str, bool]
    timestamp: str


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="EDAI4 - P&ID Intelligence API",
    description="""
    AI-powered P&ID (Piping & Instrumentation Diagram) analysis pipeline.
    
    ## Features
    - **Layer 1**: YOLO-based symbol detection (88.1% mAP50)
    - **Layer 2**: OCR text extraction with ISA S5.1 parsing
    - **Layer 3**: Graph-based topology analysis
    - **Layer 4**: Semantic interpretation and validation
    - **Layer 5**: RAG-powered natural language queries
    
    ## Endpoints
    - `/process` - Process a P&ID image through all layers
    - `/query` - Ask questions about processed P&IDs
    - `/validate` - Validate instrument tags
    - `/health` - API health check
    """,
    version="1.0.0",
)

# CORS for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Global State
# =============================================================================

class PipelineState:
    """Manages pipeline components."""
    
    def __init__(self):
        self.perception_pipeline = None
        self.sahi_pipeline = None
        self.high_density_pipeline = None
        self.hybrid_pipeline = None  # NEW: YOLO + HoughCircles + ISA Regex
        self.graph_builder = None
        self.rag_pipeline = None
        self.current_graph = None
        self.model_path = None
        self._initialized = False
    
    def initialize(self, model_path: str = None):
        """Initialize pipeline components."""
        if self._initialized:
            return
        
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            
            from src.perception import PerceptionPipeline
            from src.topology import GraphBuilder
            from src.cognitive import RAGPipeline
            
            # Search multiple paths for the model
            model_search_paths = [
                model_path,
                os.environ.get("YOLO_MODEL_PATH"),
                # Kaggle paths
                "/kaggle/input/edai4-golden-model/best.pt",
                "/kaggle/input/datasets/yogeshwarvshinde/edai4-golden-model/best.pt",
                # Local paths - including subdirectories
                str(Path(__file__).parent.parent.parent / "models" / "yolov8" / "best.pt"),
                str(Path(__file__).parent.parent.parent / "models" / "best.pt"),
                str(Path(__file__).parent.parent.parent / "best.pt"),
                "D:/EDAI4/models/yolov8/best.pt",
                "D:/EDAI4/models/best.pt",
                "./models/yolov8/best.pt",
                "./models/best.pt",
                "./best.pt",
            ]
            
            self.model_path = None
            for p in model_search_paths:
                if p and os.path.exists(p):
                    self.model_path = p
                    break
            
            # Initialize if model exists
            if self.model_path:
                print(f"Loading YOLO model from: {self.model_path}")
                
                # Priority 1: Hybrid Pipeline (YOLO + HoughCircles + ISA Regex)
                try:
                    from src.perception.hybrid_pipeline import HybridPerceptionPipeline
                    self.hybrid_pipeline = HybridPerceptionPipeline(
                        model_path=self.model_path,
                        slice_size=640,
                        overlap_ratio=0.25,
                        confidence_threshold=0.20,
                        circle_min_radius=15,
                        circle_max_radius=60,
                        use_gpu=False,  # Windows compatibility
                    )
                    print("Hybrid Pipeline (YOLO + HoughCircles + ISA Regex) initialized!")
                except Exception as e:
                    print(f"Hybrid Pipeline failed: {e}")
                    self.hybrid_pipeline = None
                
                # Priority 2: High-Density Pipeline (SAHI + PaddleOCR)
                if self.hybrid_pipeline is None:
                    try:
                        from src.perception.high_density_pipeline import HighDensityPipeline
                        self.high_density_pipeline = HighDensityPipeline(
                            model_path=self.model_path,
                            slice_size=640,
                            overlap_ratio=0.25,
                            confidence_threshold=0.20,
                            max_proximity_px=60.0,
                            use_gpu=False,
                        )
                        print("High-Density Pipeline initialized (fallback 1)")
                    except Exception as e:
                        print(f"High-Density Pipeline failed: {e}")
                        self.high_density_pipeline = None
                
                # Priority 3: Basic SAHI pipeline
                if self.hybrid_pipeline is None and self.high_density_pipeline is None:
                    try:
                        from src.perception.sahi_detector import SAHIPipeline
                        self.sahi_pipeline = SAHIPipeline(
                            model_path=self.model_path,
                            confidence_threshold=0.25,
                            use_gpu=False,
                        )
                        print("SAHI Pipeline initialized (fallback 2)")
                    except Exception as e:
                        print(f"SAHI Pipeline failed: {e}")
                        self.sahi_pipeline = None
                
                # Priority 4: Standard pipeline (last resort)
                self.perception_pipeline = PerceptionPipeline(
                    model_path=self.model_path,
                    confidence_threshold=0.25,
                    association_search_radius=200,
                )
            else:
                print("WARNING: YOLO model not found. Running in demo mode.")
                print("Set YOLO_MODEL_PATH environment variable or place best.pt in models/")
            
            self.graph_builder = GraphBuilder()
            
            # Initialize RAG with LLM enabled if API key is available
            api_key = os.getenv("GOOGLE_API_KEY")
            use_llm = bool(api_key)
            if api_key:
                print(f"GOOGLE_API_KEY found: {api_key[:10]}...{api_key[-4:]}")
            else:
                print("WARNING: GOOGLE_API_KEY not found - LLM features disabled")
            self.rag_pipeline = RAGPipeline(use_llm=use_llm)
            self._initialized = True
            
        except ImportError as e:
            print(f"Warning: Could not import pipeline components: {e}")
    
    def is_ready(self) -> Dict[str, bool]:
        """Check which components are ready."""
        has_detector = (
            self.hybrid_pipeline is not None or
            self.high_density_pipeline is not None or
            self.sahi_pipeline is not None or
            self.perception_pipeline is not None
        )
        return {
            "layer1_yolo": has_detector,
            "layer2_ocr": has_detector,
            "hybrid_enabled": self.hybrid_pipeline is not None,
            "high_density_enabled": self.high_density_pipeline is not None,
            "sahi_enabled": self.sahi_pipeline is not None,
            "layer3_graph": self.graph_builder is not None,
            "layer4_semantic": True,  # Always available (pure Python)
            "layer5_rag": self.rag_pipeline is not None,
        }


state = PipelineState()


# =============================================================================
# API Endpoints
# =============================================================================

@app.on_event("startup")
async def startup():
    """Initialize on startup."""
    state.initialize()


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web interface."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>EDAI4 - P&ID Intelligence</title>
        <style>
            * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
            body { margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 { color: #333; margin-bottom: 5px; }
            .subtitle { color: #666; margin-bottom: 30px; }
            .card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .card h2 { margin-top: 0; color: #444; }
            .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; cursor: pointer; border-radius: 8px; transition: all 0.3s; }
            .upload-area:hover { border-color: #007bff; background: #f8f9ff; }
            .upload-area.dragover { border-color: #007bff; background: #e8f0ff; }
            input[type="file"] { display: none; }
            .btn { background: #007bff; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-size: 16px; }
            .btn:hover { background: #0056b3; }
            .btn:disabled { background: #ccc; cursor: not-allowed; }
            .query-box { display: flex; gap: 10px; }
            .query-box input { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 16px; }
            #results { margin-top: 20px; }
            .result-item { background: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 10px; }
            .result-item h4 { margin: 0 0 10px 0; }
            .tag { display: inline-block; background: #e9ecef; padding: 4px 8px; border-radius: 4px; margin: 2px; font-size: 14px; }
            .tag.instrument { background: #d4edda; color: #155724; }
            .tag.valve { background: #cce5ff; color: #004085; }
            .tag.equipment { background: #fff3cd; color: #856404; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 20px; }
            .stat { text-align: center; }
            .stat-value { font-size: 32px; font-weight: bold; color: #007bff; }
            .stat-label { color: #666; }
            .loading { text-align: center; padding: 20px; }
            .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #007bff; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            .preview-img { max-width: 100%; max-height: 400px; border-radius: 8px; margin-top: 15px; }
            .answer-box { background: #e8f5e9; padding: 15px; border-radius: 8px; border-left: 4px solid #4caf50; }
            .confidence { color: #666; font-size: 14px; margin-top: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>EDAI4 - P&ID Intelligence</h1>
            <p class="subtitle">AI-powered extraction of E&I deliverables from P&ID diagrams</p>
            
            <div class="card">
                <h2>Upload P&ID Image</h2>
                <div class="upload-area" id="dropZone" onclick="document.getElementById('fileInput').click()">
                    <p>Drop P&ID image here or click to browse</p>
                    <p style="color: #999; font-size: 14px;">Supports: JPG, PNG, TIFF</p>
                </div>
                <input type="file" id="fileInput" accept="image/*" onchange="handleFile(this.files[0])">
                <img id="preview" class="preview-img" style="display: none;">
                <div id="uploadStatus"></div>
            </div>
            
            <div class="card" id="resultsCard" style="display: none;">
                <h2>Analysis Results</h2>
                <div class="stats" id="stats"></div>
                <div id="detections"></div>
            </div>
            
            <div class="card">
                <h2>Ask a Question</h2>
                <div class="query-box">
                    <input type="text" id="queryInput" placeholder="e.g., What instruments measure flow?" onkeypress="if(event.key==='Enter')askQuestion()">
                    <button class="btn" onclick="askQuestion()">Ask</button>
                </div>
                <div id="answer"></div>
            </div>
            
            <div class="card">
                <h2>Quick Actions</h2>
                <button class="btn" onclick="askQuestion('List all instruments')" style="margin: 5px;">List Instruments</button>
                <button class="btn" onclick="askQuestion('What safety systems are present?')" style="margin: 5px;">Safety Systems</button>
                <button class="btn" onclick="askQuestion('Describe the control loops')" style="margin: 5px;">Control Loops</button>
                <button class="btn" onclick="checkHealth()" style="margin: 5px; background: #28a745;">Check Health</button>
            </div>
        </div>
        
        <script>
            const dropZone = document.getElementById('dropZone');
            
            dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
            dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
            dropZone.addEventListener('drop', (e) => { e.preventDefault(); dropZone.classList.remove('dragover'); handleFile(e.dataTransfer.files[0]); });
            
            async function handleFile(file) {
                if (!file) return;
                
                // Show preview
                const preview = document.getElementById('preview');
                preview.src = URL.createObjectURL(file);
                preview.style.display = 'block';
                
                // Upload and process
                document.getElementById('uploadStatus').innerHTML = '<div class="loading"><div class="spinner"></div><p>Processing...</p></div>';
                
                const formData = new FormData();
                formData.append('file', file);
                
                try {
                    const response = await fetch('/process', { method: 'POST', body: formData });
                    const data = await response.json();
                    
                    if (response.ok) {
                        showResults(data);
                    } else {
                        document.getElementById('uploadStatus').innerHTML = '<p style="color: red;">Error: ' + (data.detail || 'Processing failed') + '</p>';
                    }
                } catch (err) {
                    document.getElementById('uploadStatus').innerHTML = '<p style="color: red;">Error: ' + err.message + '</p>';
                }
            }
            
            function showResults(data) {
                document.getElementById('uploadStatus').innerHTML = '<p style="color: green;">Processed in ' + data.processing_time_ms.toFixed(0) + 'ms</p>';
                document.getElementById('resultsCard').style.display = 'block';
                
                // Stats
                document.getElementById('stats').innerHTML = `
                    <div class="stat"><div class="stat-value">${data.layer1_detections}</div><div class="stat-label">Symbols Detected</div></div>
                    <div class="stat"><div class="stat-value">${data.layer2_instruments}</div><div class="stat-label">Instruments</div></div>
                    <div class="stat"><div class="stat-value">${data.layer3_nodes}</div><div class="stat-label">Graph Nodes</div></div>
                    <div class="stat"><div class="stat-value">${data.layer3_edges}</div><div class="stat-label">Connections</div></div>
                `;
                
                // Detections
                const detHtml = data.detections.slice(0, 20).map(d => {
                    const tagClass = d.class_name.startsWith('instrument') ? 'instrument' : 
                                    d.class_name.startsWith('valve') ? 'valve' : 'equipment';
                    return `<span class="tag ${tagClass}">${d.tag || d.class_name} (${(d.confidence*100).toFixed(0)}%)</span>`;
                }).join('');
                document.getElementById('detections').innerHTML = detHtml;
            }
            
            async function askQuestion(q) {
                const question = q || document.getElementById('queryInput').value;
                if (!question) return;
                
                document.getElementById('answer').innerHTML = '<div class="loading"><div class="spinner"></div></div>';
                
                try {
                    const response = await fetch('/query', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({question: question})
                    });
                    const data = await response.json();
                    
                    document.getElementById('answer').innerHTML = `
                        <div class="answer-box">
                            <p>${data.answer.replace(/\\n/g, '<br>')}</p>
                            <div class="confidence">Confidence: ${(data.confidence*100).toFixed(0)}% | Intent: ${data.intent}</div>
                        </div>
                    `;
                } catch (err) {
                    document.getElementById('answer').innerHTML = '<p style="color: red;">Error: ' + err.message + '</p>';
                }
            }
            
            async function checkHealth() {
                const response = await fetch('/health');
                const data = await response.json();
                alert(JSON.stringify(data, null, 2));
            }
        </script>
    </body>
    </html>
    """


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        layers_ready=state.is_ready(),
        timestamp=datetime.now().isoformat(),
    )


@app.post("/process", response_model=ProcessingResult)
async def process_image(file: UploadFile = File(...)):
    """
    Process a P&ID image through all layers.
    Uses SAHI pipeline for better detection on large images.
    """
    import time
    start_time = time.time()
    
    # Read image
    contents = await file.read()
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    
    try:
        detections = []
        instruments_count = 0
        nodes_count = 0
        edges_count = 0
        graph_summary = {}
        
        import cv2
        import numpy as np
        
        # Decode image
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        h, w = image.shape[:2]
        print(f"Image size: {w}x{h}")
        
        # Priority 1: Hybrid Pipeline (YOLO + HoughCircles + ISA Regex)
        if state.hybrid_pipeline:
            print("[API] Using Hybrid Pipeline (YOLO + HoughCircles + ISA Regex)")
            result = state.hybrid_pipeline.process(image)
            
            # Convert hybrid results to API format
            for node in result.nodes:
                detections.append(DetectionResult(
                    class_name=node.class_name,
                    confidence=node.confidence,
                    bbox={"x1": node.x1, "y1": node.y1, "x2": node.x2, "y2": node.y2},
                    tag=node.tag,
                ))
            
            instruments_count = result.stats.get("instruments", 0)
            nodes_count = len(result.nodes)
            
            graph_summary = {
                "mode": "hybrid",
                "yolo_ms": result.timing.get("yolo_ms", 0),
                "ocr_ms": result.timing.get("ocr_ms", 0),
                "circle_ms": result.timing.get("circle_ms", 0),
                "merge_ms": result.timing.get("merge_ms", 0),
                "total_ms": result.timing.get("total_ms", 0),
                "yolo_detections": result.stats.get("yolo_detections", 0),
                "circles_detected": result.stats.get("circles_detected", 0),
                "isa_tags_found": result.stats.get("isa_tags_found", 0),
                "nodes_from_yolo": result.stats.get("nodes_from_yolo", 0),
                "nodes_from_circles": result.stats.get("nodes_from_circles", 0),
                "nodes_from_regex": result.stats.get("nodes_from_regex", 0),
                "instruments": instruments_count,
                "valves": result.stats.get("valves", 0),
                "equipment": result.stats.get("equipment", 0),
                "discarded_text": result.stats.get("discarded_text", 0),
            }
        
        # Priority 2: High-Density Pipeline (SAHI + PaddleOCR)
        elif state.high_density_pipeline:
            print("[API] Using High-Density Pipeline (SAHI + PaddleOCR)")
            result = state.high_density_pipeline.process(image)
            
            # Convert high-density results to API format
            for idx, symbol in enumerate(result.symbols):
                detections.append(DetectionResult(
                    class_name=symbol.class_name,
                    confidence=symbol.confidence,
                    bbox={"x1": symbol.x1, "y1": symbol.y1, "x2": symbol.x2, "y2": symbol.y2},
                    tag=symbol.tag,
                ))
            
            instruments_count = len(result.associated_tags)
            nodes_count = len(result.symbols)
            
            graph_summary = {
                "mode": "high_density",
                "detection_ms": result.timing.get("detection_ms", 0),
                "ocr_ms": result.timing.get("ocr_ms", 0),
                "association_ms": result.timing.get("association_ms", 0),
                "symbols_detected": len(result.symbols),
                "text_blocks": len(result.text_blocks),
                "tags_associated": len(result.associated_tags),
                "floating_text_discarded": len(result.discarded_text),
                "instruments": instruments_count,
            }
        
        # Priority 3: SAHI Pipeline (basic)
        elif state.sahi_pipeline:
            print("[API] Using SAHI Pipeline for processing")
            result = state.sahi_pipeline.process(image)
            
            # Convert SAHI detections to API format
            for det in result['detections']:
                detections.append(DetectionResult(
                    class_name=det.class_name,
                    confidence=det.confidence,
                    bbox={"x1": det.x1, "y1": det.y1, "x2": det.x2, "y2": det.y2},
                    tag=None,
                ))
            
            # Add instrument detections from ISA tags
            for inst in result['instruments']:
                cx, cy = inst['center']
                radius = 25  # Typical instrument bubble size
                
                # Check if already detected
                is_duplicate = False
                for det in detections:
                    det_cx = (det.bbox["x1"] + det.bbox["x2"]) / 2
                    det_cy = (det.bbox["y1"] + det.bbox["y2"]) / 2
                    if ((cx - det_cx)**2 + (cy - det_cy)**2)**0.5 < 50:
                        det.tag = inst['tag']  # Assign tag to existing detection
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    detections.append(DetectionResult(
                        class_name="instrument.bubble",
                        confidence=inst['confidence'],
                        bbox={
                            "x1": float(cx - radius),
                            "y1": float(cy - radius),
                            "x2": float(cx + radius),
                            "y2": float(cy + radius),
                        },
                        tag=inst['tag'],
                    ))
            
            instruments_count = len(result['instruments'])
            nodes_count = len(detections)
            
            graph_summary = {
                "mode": "sahi",
                "detection_ms": result['timing']['detection_ms'],
                "ocr_ms": result['timing']['ocr_ms'],
                "symbols_detected": len(result['detections']),
                "text_blocks": len(result['text_blocks']),
                "instruments": instruments_count,
            }
            
        # Fallback: Standard perception pipeline
        elif state.perception_pipeline:
            print("[API] Using standard perception pipeline (fallback)")
            result = state.perception_pipeline.process_image(image)
            
            instruments_count = len(result.instruments)
            
            # Build detections list - include all detected objects
            all_items = (
                list(result.instruments) + 
                list(result.equipment) + 
                list(result.lines) +
                list(result.unidentified_symbols)
            )
            
            for inst in all_items:
                # bbox is a tuple (x1, y1, x2, y2)
                bbox_coords = inst.bbox if isinstance(inst.bbox, tuple) and len(inst.bbox) == 4 else (0, 0, 0, 0)
                # Use detection_confidence if confidence is 0 (for unidentified symbols)
                conf = inst.confidence if inst.confidence > 0 else inst.detection_confidence
                detections.append(DetectionResult(
                    class_name=inst.symbol_class,
                    confidence=conf,
                    bbox={
                        "x1": bbox_coords[0],
                        "y1": bbox_coords[1],
                        "x2": bbox_coords[2],
                        "y2": bbox_coords[3],
                    },
                    tag=inst.tag_number if inst.tag_number != "UNTAGGED" else None,
                ))
            
            # Run OCR directly if pipeline OCR failed
            ocr_texts = []
            if len(result.ocr_result.text_blocks) == 0:
                print("OCR from pipeline is empty, running direct EasyOCR...")
                try:
                    import easyocr
                    reader = easyocr.Reader(['en'], gpu=False, verbose=False)
                    ocr_raw = reader.readtext(image)
                    for bbox, text, conf in ocr_raw:
                        cx = (bbox[0][0] + bbox[2][0]) / 2
                        cy = (bbox[0][1] + bbox[2][1]) / 2
                        ocr_texts.append({'text': text.upper(), 'center': (cx, cy), 'conf': conf})
                    print(f"Direct EasyOCR found {len(ocr_texts)} text blocks")
                except Exception as e:
                    print(f"EasyOCR failed: {e}")
            else:
                for tb in result.ocr_result.text_blocks:
                    ocr_texts.append({'text': tb.text.upper(), 'center': tb.region.center, 'conf': tb.confidence})
            
            # Fallback: Find instruments by looking for OCR tags that match ISA patterns
            import re
            isa_pattern = re.compile(r'^[FPTLAIC][IRTCASV][-_]?\d+', re.IGNORECASE)
            
            circle_count = 0
            print(f"Found {len(ocr_texts)} OCR text blocks, checking for ISA tags...")
            
            for txt_info in ocr_texts:
                tag_text = txt_info['text'].strip()
                
                # Check if it looks like an ISA instrument tag
                if isa_pattern.match(tag_text) or len(tag_text) >= 2 and tag_text[:2] in ['FT', 'PT', 'LT', 'TT', 'AT', 'FC', 'PC', 'LC', 'TC', 'FI', 'PI', 'LI', 'TI']:
                    tx, ty = txt_info['center']
                    
                    # Check if overlaps with existing detections
                    is_duplicate = False
                    for det in detections:
                        det_cx = (det.bbox["x1"] + det.bbox["x2"]) / 2
                        det_cy = (det.bbox["y1"] + det.bbox["y2"]) / 2
                        if ((tx - det_cx)**2 + (ty - det_cy)**2)**0.5 < 50:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        radius = 25
                        detections.append(DetectionResult(
                            class_name="instrument.bubble",
                            confidence=0.8,
                            bbox={
                                "x1": float(tx - radius),
                                "y1": float(ty - radius),
                                "x2": float(tx + radius),
                                "y2": float(ty + radius),
                            },
                            tag=tag_text,
                        ))
                        circle_count += 1
                        instruments_count += 1
                        print(f"  Found ISA tag: {tag_text} at ({tx:.0f}, {ty:.0f})")
            
            print(f"ISA tag detection found {circle_count} instrument bubbles")
            
            # Layer 3: Build graph
            if state.graph_builder:
                state.current_graph = state.graph_builder.build_from_perception(result)
                nodes_count = state.current_graph.node_count
                edges_count = state.current_graph.edge_count
                
                if state.rag_pipeline:
                    state.rag_pipeline.set_graph(state.current_graph)
                
                graph_summary = {
                    "mode": "standard",
                    "nodes": nodes_count,
                    "edges": edges_count,
                    "instruments": instruments_count,
                    "valves": len([n for n in state.current_graph.nodes.values() 
                                  if n.node_type.value == "valve"]),
                    "equipment": len([n for n in state.current_graph.nodes.values() 
                                     if n.node_type.value in ("equipment", "pump")]),
                }
        else:
            # Demo mode without model
            detections = [
                DetectionResult(
                    class_name="instrument.bubble",
                    confidence=0.95,
                    bbox={"x1": 100, "y1": 100, "x2": 150, "y2": 150},
                    tag="FT-101",
                )
            ]
            instruments_count = 1
            graph_summary = {"message": "Demo mode - model not loaded"}
        
        processing_time = (time.time() - start_time) * 1000
        
        return ProcessingResult(
            image_name=file.filename,
            processing_time_ms=processing_time,
            layer1_detections=len(detections),
            layer2_instruments=instruments_count,
            layer3_nodes=nodes_count,
            layer3_edges=edges_count,
            detections=detections,
            graph_summary=graph_summary,
        )
        
    finally:
        # Cleanup temp file
        os.unlink(tmp_path)


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Ask a natural language question about the P&ID.
    
    Requires an image to be processed first, or uses general knowledge.
    """
    if not state.rag_pipeline:
        # Initialize RAG pipeline if not done
        try:
            from src.cognitive import RAGPipeline
            state.rag_pipeline = RAGPipeline(use_llm=request.use_llm)
        except ImportError:
            raise HTTPException(500, "RAG pipeline not available")
    
    # Query the pipeline
    response = state.rag_pipeline.query(request.question)
    
    return QueryResponse(
        answer=response.answer,
        confidence=response.confidence,
        sources=response.sources,
        intent=response.intent or "general",
    )


@app.post("/validate")
async def validate_tag(tag: str = Form(...)):
    """
    Validate an ISA S5.1 instrument tag.
    """
    try:
        from src.cognitive import ISAS51Validator
        
        validator = ISAS51Validator()
        result = validator.validate_tag(tag)
        
        return {
            "tag": tag,
            "valid": result.is_valid,
            "score": result.compliance_score,
            "parsed": {
                "first_letter": result.parsed_tag.first_letter if result.parsed_tag else None,
                "succeeding_letters": result.parsed_tag.succeeding_letters if result.parsed_tag else None,
                "loop_number": result.parsed_tag.loop_number if result.parsed_tag else None,
            },
            "issues": [{"message": i.message, "severity": i.severity.value} for i in result.issues],
        }
    except ImportError:
        raise HTTPException(500, "Validator not available")


@app.get("/graph")
async def get_graph():
    """
    Get the current P&ID graph as JSON.
    """
    if not state.current_graph:
        return {"message": "No graph loaded. Process an image first."}
    
    nodes = []
    for node in state.current_graph.get_all_nodes():
        nodes.append({
            "id": node.id,
            "type": node.node_type.value,
            "tag": node.tag,
            "label": node.label,
            "x": node.x,
            "y": node.y,
        })
    
    edges = []
    for edge in state.current_graph.get_all_edges():
        edges.append({
            "source": edge.source_id,
            "target": edge.target_id,
            "type": edge.edge_type.value,
        })
    
    return {"nodes": nodes, "edges": edges}


# =============================================================================
# Run Server
# =============================================================================

def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the FastAPI server."""
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    run_server(port=8000, reload=True)
