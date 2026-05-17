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
import logging
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

# Setup logger
logger = logging.getLogger(__name__)

# EDAI4 imports will be done lazily to avoid import errors if deps missing
# Gemini analyzer import
from src.api.gemini_analyzer import get_analyzer
# HazOp simulator import
from src.api.hazop_simulator import get_hazop_simulator, HazOpSimulationRequest, HazOpSimulationResponse
# Flow simulator import
from src.api.flow_simulator import (
    get_flow_simulator,
    FlowSimulationRequest,
    FlowSimulationResponse
)


# =============================================================================
# Pydantic Models
# =============================================================================

class DetectionResult(BaseModel):
    """Single detection result with percentage-based coordinates."""
    class_name: str
    confidence: float
    # Percentage coordinates (0.0 to 1.0) - Backend does all the math!
    pct_x: float  # Top-left X as percentage
    pct_y: float  # Top-left Y as percentage
    pct_width: float  # Width as percentage
    pct_height: float  # Height as percentage
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


class GraphTopology(BaseModel):
    """Graph topology for Q&A."""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class PIDQuestionRequest(BaseModel):
    """P&ID Q&A request."""
    question: str
    topology: GraphTopology


class PIDQuestionResponse(BaseModel):
    """P&ID Q&A response."""
    answer: str
    question: str
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


# =============================================================================
# Helper Functions for Coordinate Conversion
# =============================================================================

def yolo_to_percentages(box) -> dict:
    """
    Convert YOLO bounding box to top-left percentages using xyxyn.
    
    FOOLPROOF METHOD: Uses YOLOv8's built-in normalized coordinates (xyxyn)
    which gives perfect percentages (0.0 to 1.0) with NO manual math needed!
    
    Args:
        box: YOLO box object with xyxyn attribute
    
    Returns:
        Dictionary with pct_x, pct_y, pct_width, pct_height (0.0 to 1.0)
    """
    # xyxyn gives [x_min, y_min, x_max, y_max] as perfect percentages (0.0 to 1.0)
    # This is ALREADY normalized to the original image dimensions!
    x1_pct, y1_pct, x2_pct, y2_pct = box.xyxyn[0].cpu().tolist()
    
    # Calculate width and height as percentages
    pct_width = x2_pct - x1_pct
    pct_height = y2_pct - y1_pct
    
    # Clamp to valid range [0.0, 1.0] (should already be valid, but just in case)
    pct_x = max(0.0, min(1.0, x1_pct))
    pct_y = max(0.0, min(1.0, y1_pct))
    pct_width = max(0.0, min(1.0 - pct_x, pct_width))
    pct_height = max(0.0, min(1.0 - pct_y, pct_height))
    
    return {
        "pct_x": pct_x,
        "pct_y": pct_y,
        "pct_width": pct_width,
        "pct_height": pct_height,
    }


def bbox_to_percentages(x1: float, y1: float, x2: float, y2: float, 
                        orig_width: int, orig_height: int) -> dict:
    """
    Convert pixel bounding box (x1, y1, x2, y2) to percentages.
    
    Args:
        x1, y1: Top-left corner in pixels
        x2, y2: Bottom-right corner in pixels
        orig_width: Original image width
        orig_height: Original image height
    
    Returns:
        Dictionary with pct_x, pct_y, pct_width, pct_height (0.0 to 1.0)
    """
    width = x2 - x1
    height = y2 - y1
    
    # Convert to percentages
    pct_x = float(x1 / orig_width)
    pct_y = float(y1 / orig_height)
    pct_width = float(width / orig_width)
    pct_height = float(height / orig_height)
    
    # Clamp to valid range
    pct_x = max(0.0, min(1.0, pct_x))
    pct_y = max(0.0, min(1.0, pct_y))
    pct_width = max(0.0, min(1.0 - pct_x, pct_width))
    pct_height = max(0.0, min(1.0 - pct_y, pct_height))
    
    return {
        "pct_x": pct_x,
        "pct_y": pct_y,
        "pct_width": pct_width,
        "pct_height": pct_height,
    }


# =============================================================================
# API Endpoints
# =============================================================================

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
        
        # Helper function to validate and clamp bounding boxes
        def validate_bbox(bbox_dict, img_width, img_height, min_size=10):
            """
            Validate and clamp bounding box coordinates to image dimensions.
            Returns None if bbox is invalid (outside image or too small).
            """
            x1 = max(0, min(bbox_dict["x1"], img_width))
            y1 = max(0, min(bbox_dict["y1"], img_height))
            x2 = max(0, min(bbox_dict["x2"], img_width))
            y2 = max(0, min(bbox_dict["y2"], img_height))
            
            # Check if bbox is valid
            width = x2 - x1
            height = y2 - y1
            
            # Filter out invalid boxes
            if width < min_size or height < min_size:
                return None
            
            # Filter out boxes that are mostly outside the image
            if x1 >= img_width * 0.95 or y1 >= img_height * 0.95:
                return None
            
            # Filter out boxes with invalid coordinates
            if x1 >= x2 or y1 >= y2:
                return None
            
            return {"x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2)}
        
        # Helper function to check if bbox is in valid content area
        def is_in_content_area(bbox_dict, img_width, img_height):
            """
            Check if bounding box is in a valid content area (not in margins/blank areas).
            """
            x1, y1, x2, y2 = bbox_dict["x1"], bbox_dict["y1"], bbox_dict["x2"], bbox_dict["y2"]
            
            # Calculate center
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            
            # Check if center is within reasonable bounds (not in extreme margins)
            margin_x = img_width * 0.05  # 5% margin
            margin_y = img_height * 0.05
            
            if cx < margin_x or cx > img_width - margin_x:
                return False
            if cy < margin_y or cy > img_height - margin_y:
                return False
            
            return True
        
        # Priority 1: Hybrid Pipeline (YOLO + HoughCircles + ISA Regex)
        if state.hybrid_pipeline:
            print("[API] Using Hybrid Pipeline (YOLO + HoughCircles + ISA Regex)")
            result = state.hybrid_pipeline.process(image)
            
            # Convert hybrid results to API format with percentage coordinates
            for node in result.nodes:
                # Convert pixel coordinates to percentages
                coords = bbox_to_percentages(node.x1, node.y1, node.x2, node.y2, w, h)
                
                # Basic validation: skip if box is too small or invalid
                if coords["pct_width"] < 0.005 or coords["pct_height"] < 0.005:
                    continue
                
                detections.append(DetectionResult(
                    class_name=node.class_name,
                    confidence=node.confidence,
                    pct_x=coords["pct_x"],
                    pct_y=coords["pct_y"],
                    pct_width=coords["pct_width"],
                    pct_height=coords["pct_height"],
                    tag=node.tag,
                ))
            
            instruments_count = result.stats.get("instruments", 0)
            nodes_count = len(detections)  # Use filtered count
            
            # BUILD GRAPH FROM HYBRID RESULTS
            if state.graph_builder:
                print("[API] Building graph from hybrid pipeline results...")
                try:
                    # Detect lines/pipes connecting instruments
                    from src.perception.line_detector import LineDetector
                    line_detector = LineDetector(
                        min_line_length=30,
                        max_line_gap=10,
                        hough_threshold=50
                    )
                    
                    # Detect lines
                    lines = line_detector.detect_lines(image)
                    print(f"[API] Detected {len(lines)} lines/pipes")
                    
                    # Prepare nodes for connection detection
                    nodes_for_connection = []
                    for i, node in enumerate(result.nodes):
                        nodes_for_connection.append({
                            'id': f'node_{i}',
                            'x1': node.x1,
                            'y1': node.y1,
                            'x2': node.x2,
                            'y2': node.y2,
                            'tag': node.tag,
                            'class': node.class_name
                        })
                    
                    # Find connections
                    connections = line_detector.find_connections(lines, nodes_for_connection, connection_threshold=30.0)
                    print(f"[API] Found {len(connections)} connections")
                    
                    # Build graph manually
                    from src.topology.graph_builder import GraphBuilder, GraphNode, NodeType, EdgeType
                    import networkx as nx
                    
                    graph = nx.DiGraph()
                    
                    # Add nodes
                    for i, node in enumerate(result.nodes):
                        node_id = f'node_{i}'
                        
                        # Determine node type
                        if 'instrument' in node.class_name.lower():
                            node_type = NodeType.INSTRUMENT
                        elif 'valve' in node.class_name.lower():
                            node_type = NodeType.VALVE
                        elif 'equipment' in node.class_name.lower() or 'pump' in node.class_name.lower():
                            node_type = NodeType.EQUIPMENT
                        else:
                            node_type = NodeType.UNKNOWN
                        
                        graph_node = GraphNode(
                            id=node_id,
                            node_type=node_type,
                            label=node.tag or node.class_name,
                            tag=node.tag,
                            x=(node.x1 + node.x2) / 2,
                            y=(node.y1 + node.y2) / 2,
                            width=node.x2 - node.x1,
                            height=node.y2 - node.y1,
                            bbox=(node.x1, node.y1, node.x2, node.y2),
                            confidence=node.confidence,
                            detection_class=node.class_name,
                            symbol_class=node.class_name
                        )
                        
                        graph.add_node(node_id, data=graph_node)
                    
                    # Add edges from connections
                    for source_id, target_id in connections:
                        graph.add_edge(source_id, target_id, edge_type=EdgeType.CONNECTED_TO.value)
                    
                    # Create a simple graph object
                    class SimpleGraph:
                        def __init__(self, nx_graph):
                            self.graph = nx_graph
                            self.nodes = {}
                            self.edges = []
                            
                            # Convert nodes
                            for node_id, node_data in nx_graph.nodes(data=True):
                                if 'data' in node_data:
                                    self.nodes[node_id] = node_data['data']
                            
                            # Convert edges
                            for source, target, edge_data in nx_graph.edges(data=True):
                                # Create edge object with attributes
                                edge_obj = type('Edge', (), {
                                    'source_id': source,
                                    'target_id': target,
                                    'edge_type': edge_data.get('edge_type', 'connected_to')
                                })()
                                self.edges.append(edge_obj)
                        
                        @property
                        def node_count(self):
                            return len(self.nodes)
                        
                        @property
                        def edge_count(self):
                            return len(self.edges)
                        
                        def get_all_nodes(self):
                            return list(self.nodes.values())
                        
                        def get_all_edges(self):
                            return self.edges
                        
                        def get_node(self, node_id):
                            """Get a node by ID"""
                            return self.nodes.get(node_id)
                        
                        def get_edges_from_node(self, node_id):
                            """Get all edges originating from a node"""
                            return [e for e in self.edges if e.source_id == node_id]
                        
                        def get_edges_to_node(self, node_id):
                            """Get all edges pointing to a node"""
                            return [e for e in self.edges if e.target_id == node_id]
                        
                        def get_neighbors(self, node_id):
                            """Get all neighboring nodes"""
                            neighbors = []
                            for edge in self.edges:
                                if edge.source_id == node_id:
                                    neighbors.append(edge.target_id)
                                elif edge.target_id == node_id:
                                    neighbors.append(edge.source_id)
                            return neighbors
                        
                        def get_predecessors(self, node_id):
                            """Get nodes that point to this node"""
                            return [e.source_id for e in self.edges if e.target_id == node_id]
                        
                        def get_successors(self, node_id):
                            """Get nodes that this node points to"""
                            return [e.target_id for e in self.edges if e.source_id == node_id]
                    
                    state.current_graph = SimpleGraph(graph)
                    nodes_count = state.current_graph.node_count
                    edges_count = state.current_graph.edge_count
                    
                    print(f"[API] Graph built: {nodes_count} nodes, {edges_count} edges")
                    
                    # Update RAG pipeline
                    if state.rag_pipeline:
                        state.rag_pipeline.set_graph(state.current_graph)
                    
                except Exception as e:
                    print(f"[API] Error building graph: {e}")
                    import traceback
                    traceback.print_exc()
            
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
                "nodes": nodes_count,
                "edges": edges_count,
            }
        
        # Priority 2: High-Density Pipeline (SAHI + PaddleOCR)
        elif state.high_density_pipeline:
            print("[API] Using High-Density Pipeline (SAHI + PaddleOCR)")
            result = state.high_density_pipeline.process(image)
            
            # Convert high-density results to API format with percentage coordinates
            for idx, symbol in enumerate(result.symbols):
                # Convert pixel coordinates to percentages
                coords = bbox_to_percentages(symbol.x1, symbol.y1, symbol.x2, symbol.y2, w, h)
                
                # Basic validation: skip if box is too small
                if coords["pct_width"] < 0.005 or coords["pct_height"] < 0.005:
                    continue
                
                detections.append(DetectionResult(
                    class_name=symbol.class_name,
                    confidence=symbol.confidence,
                    pct_x=coords["pct_x"],
                    pct_y=coords["pct_y"],
                    pct_width=coords["pct_width"],
                    pct_height=coords["pct_height"],
                        tag=symbol.tag,
                    ))
            
            instruments_count = len(result.associated_tags)
            nodes_count = len(detections)  # Use filtered count
            
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
            
            # Convert SAHI detections to API format with percentage coordinates
            for det in result['detections']:
                # Convert pixel coordinates to percentages
                coords = bbox_to_percentages(det.x1, det.y1, det.x2, det.y2, w, h)
                
                # Basic validation: skip if box is too small
                if coords["pct_width"] < 0.005 or coords["pct_height"] < 0.005:
                    continue
                
                detections.append(DetectionResult(
                    class_name=det.class_name,
                    confidence=det.confidence,
                    pct_x=coords["pct_x"],
                    pct_y=coords["pct_y"],
                    pct_width=coords["pct_width"],
                    pct_height=coords["pct_height"],
                    tag=None,
                ))
            
            # Add instrument detections from ISA tags with percentage coordinates
            for inst in result['instruments']:
                cx, cy = inst['center']
                radius = 25  # Typical instrument bubble size
                
                x1 = float(cx - radius)
                y1 = float(cy - radius)
                x2 = float(cx + radius)
                y2 = float(cy + radius)
                
                # Convert to percentages
                coords = bbox_to_percentages(x1, y1, x2, y2, w, h)
                
                # Skip if too small
                if coords["pct_width"] < 0.005 or coords["pct_height"] < 0.005:
                    continue
                
                # Check if already detected (check against existing detections)
                is_duplicate = False
                for det in detections:
                    # Calculate center from percentage coordinates
                    det_cx = (det.pct_x + det.pct_width / 2) * w
                    det_cy = (det.pct_y + det.pct_height / 2) * h
                    if ((cx - det_cx)**2 + (cy - det_cy)**2)**0.5 < 50:
                        det.tag = inst['tag']  # Assign tag to existing detection
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    detections.append(DetectionResult(
                        class_name="instrument.bubble",
                        confidence=inst['confidence'],
                        pct_x=coords["pct_x"],
                        pct_y=coords["pct_y"],
                        pct_width=coords["pct_width"],
                        pct_height=coords["pct_height"],
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
            
            # Build detections list - include all detected objects with percentage coordinates
            all_items = (
                list(result.instruments) + 
                list(result.equipment) + 
                list(result.lines) +
                list(result.unidentified_symbols)
            )
            
            for inst in all_items:
                # bbox is a tuple (x1, y1, x2, y2)
                bbox_coords = inst.bbox if isinstance(inst.bbox, tuple) and len(inst.bbox) == 4 else (0, 0, 0, 0)
                
                # Convert to percentages
                coords = bbox_to_percentages(
                    bbox_coords[0], bbox_coords[1], 
                    bbox_coords[2], bbox_coords[3], 
                    w, h
                )
                
                # Skip if too small
                if coords["pct_width"] < 0.005 or coords["pct_height"] < 0.005:
                    continue
                
                # Use detection_confidence if confidence is 0 (for unidentified symbols)
                conf = inst.confidence if inst.confidence > 0 else inst.detection_confidence
                detections.append(DetectionResult(
                    class_name=inst.symbol_class,
                    confidence=conf,
                    pct_x=coords["pct_x"],
                    pct_y=coords["pct_y"],
                    pct_width=coords["pct_width"],
                    pct_height=coords["pct_height"],
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
                    
                    radius = 25
                    x1 = float(tx - radius)
                    y1 = float(ty - radius)
                    x2 = float(tx + radius)
                    y2 = float(ty + radius)
                    
                    # Convert to percentages
                    coords = bbox_to_percentages(x1, y1, x2, y2, w, h)
                    
                    # Skip if too small
                    if coords["pct_width"] < 0.005 or coords["pct_height"] < 0.005:
                        continue
                    
                    # Check if overlaps with existing detections
                    is_duplicate = False
                    for det in detections:
                        det_cx = (det.pct_x + det.pct_width / 2) * w
                        det_cy = (det.pct_y + det.pct_height / 2) * h
                        if ((tx - det_cx)**2 + (ty - det_cy)**2)**0.5 < 50:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        detections.append(DetectionResult(
                            class_name="instrument.bubble",
                            confidence=0.8,
                            pct_x=coords["pct_x"],
                            pct_y=coords["pct_y"],
                            pct_width=coords["pct_width"],
                            pct_height=coords["pct_height"],
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
            # Demo mode without model - use percentage coordinates
            detections = [
                DetectionResult(
                    class_name="instrument.bubble",
                    confidence=0.95,
                    pct_x=0.1,  # 10% from left
                    pct_y=0.1,  # 10% from top
                    pct_width=0.05,  # 5% width
                    pct_height=0.05,  # 5% height
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
    
    # Debug logging for coordinate analysis
    if nodes:
        x_coords = [n["x"] for n in nodes]
        y_coords = [n["y"] for n in nodes]
        logger.info("="*60)
        logger.info(f"GRAPH API COORDINATE ANALYSIS")
        logger.info("="*60)
        logger.info(f"Total nodes: {len(nodes)}")
        logger.info(f"X coordinates: min={min(x_coords):.1f}, max={max(x_coords):.1f}, span={max(x_coords)-min(x_coords):.1f}")
        logger.info(f"Y coordinates: min={min(y_coords):.1f}, max={max(y_coords):.1f}, span={max(y_coords)-min(y_coords):.1f}")
        logger.info(f"First 5 nodes:")
        for i, node in enumerate(nodes[:5]):
            logger.info(f"  {node['id']}: ({node['x']:.1f}, {node['y']:.1f}) - {node['tag']}")
        logger.info("="*60)
        
        # Check if coordinates are clustered
        x_span = max(x_coords) - min(x_coords)
        y_span = max(y_coords) - min(y_coords)
        if x_span < 200 or y_span < 200:
            logger.warning("⚠️  COORDINATES ARE CLUSTERED! This will cause minimap issues.")
            logger.warning(f"   X span: {x_span:.1f}px, Y span: {y_span:.1f}px")
            logger.warning("   Expected: >1000px for proper distribution")
    
    edges = []
    for edge in state.current_graph.get_all_edges():
        # Handle both object and dict formats
        if hasattr(edge, 'source_id'):
            source = edge.source_id
            target = edge.target_id
            edge_type = edge.edge_type.value if hasattr(edge.edge_type, 'value') else edge.edge_type
        else:
            source = edge.source_id if hasattr(edge, 'source_id') else edge['source_id']
            target = edge.target_id if hasattr(edge, 'target_id') else edge['target_id']
            edge_type = edge.edge_type if hasattr(edge, 'edge_type') else edge['edge_type']
        
        edges.append({
            "source": source,
            "target": target,
            "type": edge_type,
        })
    
    return {"nodes": nodes, "edges": edges}


# =============================================================================
# Advanced Features Endpoints
# =============================================================================

@app.post("/api/analyze-tag")
async def analyze_tag(
    file: Optional[UploadFile] = File(None),
    tag_text: Optional[str] = Form(None)
):
    """
    Analyze P&ID instrument tag using Gemini AI
    
    Args:
        file: Optional uploaded image of instrument bubble
        tag_text: Optional tag text (used if no image provided)
        
    Returns:
        JSON with 'tag' and 'definition' keys
    """
    try:
        analyzer = get_analyzer()
        
        # If image provided, analyze from image
        if file:
            logger.info(f"Analyzing tag from image: {file.filename}")
            result = await analyzer.analyze_tag_from_image(file)
        # Otherwise, analyze from text
        elif tag_text:
            logger.info(f"Analyzing tag from text: {tag_text}")
            result = analyzer.analyze_tag_from_text(tag_text)
        else:
            raise HTTPException(400, "Either 'file' or 'tag_text' must be provided")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze_tag endpoint: {e}")
        raise HTTPException(500, f"Failed to analyze tag: {str(e)}")


def generate_fallback_answer(question: str, topology_json: dict) -> str:
    """
    Generate a rule-based answer when Gemini API is unavailable.
    This provides basic analysis without requiring LLM.
    """
    question_lower = question.lower()
    nodes = topology_json.get("nodes", [])
    edges = topology_json.get("edges", [])
    summary = topology_json.get("summary", {})
    
    # Extract useful info
    total_nodes = summary.get("total_nodes", len(nodes))
    total_edges = summary.get("total_edges", len(edges))
    node_types = summary.get("node_types", {})
    
    # Get all tags
    tags = [n.get("tag") or n.get("label") for n in nodes if n.get("tag") or n.get("label")]
    
    # Categorize by instrument type
    instruments = {}
    for node in nodes:
        tag = node.get("tag") or node.get("label", "")
        if tag and len(tag) >= 2:
            prefix = tag[:2].upper()
            if prefix not in instruments:
                instruments[prefix] = []
            instruments[prefix].append(tag)
    
    # Build answer based on question type
    answer_parts = []
    
    # Header
    answer_parts.append("**P&ID Analysis (Rule-Based Mode)**\n")
    answer_parts.append("*Note: Gemini API quota exceeded. Using fallback analysis.*\n")
    
    # Question-specific analysis
    if any(word in question_lower for word in ["list", "show", "what", "which", "all"]):
        if "instrument" in question_lower or "tag" in question_lower:
            answer_parts.append(f"\n**Instruments Found ({len(tags)} total):**\n")
            for prefix, tag_list in sorted(instruments.items()):
                answer_parts.append(f"- **{prefix}**: {', '.join(sorted(tag_list))}")
        
        elif "flow" in question_lower:
            flow_instruments = instruments.get("FT", []) + instruments.get("FI", []) + instruments.get("FC", [])
            if flow_instruments:
                answer_parts.append(f"\n**Flow Instruments ({len(flow_instruments)}):**\n")
                answer_parts.append(", ".join(sorted(flow_instruments)))
            else:
                answer_parts.append("\nNo flow instruments detected.")
        
        elif "pressure" in question_lower:
            pressure_instruments = instruments.get("PT", []) + instruments.get("PI", []) + instruments.get("PC", [])
            if pressure_instruments:
                answer_parts.append(f"\n**Pressure Instruments ({len(pressure_instruments)}):**\n")
                answer_parts.append(", ".join(sorted(pressure_instruments)))
            else:
                answer_parts.append("\nNo pressure instruments detected.")
        
        elif "temperature" in question_lower or "temp" in question_lower:
            temp_instruments = instruments.get("TT", []) + instruments.get("TI", []) + instruments.get("TC", [])
            if temp_instruments:
                answer_parts.append(f"\n**Temperature Instruments ({len(temp_instruments)}):**\n")
                answer_parts.append(", ".join(sorted(temp_instruments)))
            else:
                answer_parts.append("\nNo temperature instruments detected.")
        
        elif "level" in question_lower:
            level_instruments = instruments.get("LT", []) + instruments.get("LI", []) + instruments.get("LC", [])
            if level_instruments:
                answer_parts.append(f"\n**Level Instruments ({len(level_instruments)}):**\n")
                answer_parts.append(", ".join(sorted(level_instruments)))
            else:
                answer_parts.append("\nNo level instruments detected.")
        
        elif "valve" in question_lower:
            valves = [n.get("tag") or n.get("label") for n in nodes 
                     if "valve" in (n.get("type", "").lower())]
            if valves:
                answer_parts.append(f"\n**Valves ({len(valves)}):**\n")
                answer_parts.append(", ".join(sorted(valves)))
            else:
                answer_parts.append("\nNo valves detected.")
    
    elif "how many" in question_lower or "count" in question_lower:
        answer_parts.append(f"\n**Topology Summary:**\n")
        answer_parts.append(f"- Total Nodes: {total_nodes}")
        answer_parts.append(f"- Total Connections: {total_edges}")
        answer_parts.append(f"- Total Instruments: {len(tags)}")
        
        if node_types:
            answer_parts.append(f"\n**By Type:**")
            for node_type, count in sorted(node_types.items()):
                answer_parts.append(f"- {node_type}: {count}")
    
    elif "connect" in question_lower or "path" in question_lower or "flow" in question_lower:
        answer_parts.append(f"\n**Connectivity Analysis:**\n")
        answer_parts.append(f"- Total Connections: {total_edges}")
        answer_parts.append(f"- Average Connections per Node: {total_edges / max(total_nodes, 1):.1f}")
        
        # Find most connected nodes
        connection_count = {}
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            connection_count[source] = connection_count.get(source, 0) + 1
            connection_count[target] = connection_count.get(target, 0) + 1
        
        if connection_count:
            top_connected = sorted(connection_count.items(), key=lambda x: x[1], reverse=True)[:5]
            answer_parts.append(f"\n**Most Connected Nodes:**")
            for node_id, count in top_connected:
                # Find node label
                node_label = next((n.get("tag") or n.get("label") for n in nodes if n.get("id") == node_id), node_id)
                answer_parts.append(f"- {node_label}: {count} connections")
    
    else:
        # Generic answer
        answer_parts.append(f"\n**P&ID Overview:**\n")
        answer_parts.append(f"- Nodes: {total_nodes}")
        answer_parts.append(f"- Connections: {total_edges}")
        answer_parts.append(f"- Instruments: {len(tags)}")
        
        if instruments:
            answer_parts.append(f"\n**Instrument Types:**")
            for prefix, tag_list in sorted(instruments.items()):
                answer_parts.append(f"- {prefix}: {len(tag_list)} instruments")
    
    # Footer
    answer_parts.append(f"\n\n**Tip:** For more detailed AI-powered analysis, please check your Gemini API quota at https://ai.google.dev/gemini-api/docs/rate-limits")
    
    return "\n".join(answer_parts)


@app.post("/api/ask-pid", response_model=PIDQuestionResponse)
async def ask_pid_question(request: PIDQuestionRequest):
    """
    Engineering Q&A Assistant - Ask questions about P&ID topology
    
    Uses Gemini AI to analyze the graph topology and answer engineering questions
    about how pipes, equipment, and instruments are connected.
    
    Args:
        request: Question and graph topology (nodes and edges)
        
    Returns:
        AI-generated answer based on topology analysis
    """
    try:
        # Check if Gemini is available
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise HTTPException(
                503, 
                "Gemini API not configured. Please set GOOGLE_API_KEY in .env file."
            )
        
        # Validate API key format
        if not api_key.startswith("AIza"):
            raise HTTPException(
                503,
                "Invalid Gemini API key format. Get a valid key from https://makersuite.google.com/app/apikey"
            )
        
        # Import OLD Gemini SDK (deprecated but still works)
        try:
            import google.generativeai as genai
        except ImportError:
            raise HTTPException(
                503,
                "google-generativeai package not installed. Run: pip install google-generativeai"
            )
        
        # Configure Gemini with OLD API
        genai.configure(api_key=api_key)
        
        # Use gemini-2.5-flash (gemini-1.5-flash is no longer available)
        # Note: The OLD package automatically adds 'models/' prefix
        model_name = 'gemini-2.5-flash'
        model = genai.GenerativeModel(model_name)
        
        logger.info(f"Chatbot using Gemini model: {model_name} (will become models/{model_name})")
        
        # Prepare topology data
        topology_json = {
            "nodes": request.topology.nodes,
            "edges": request.topology.edges,
            "summary": {
                "total_nodes": len(request.topology.nodes),
                "total_edges": len(request.topology.edges),
                "node_types": {}
            }
        }
        
        # Count node types
        for node in request.topology.nodes:
            node_type = node.get("type", "unknown")
            topology_json["summary"]["node_types"][node_type] = \
                topology_json["summary"]["node_types"].get(node_type, 0) + 1
        
        # Create system prompt
        system_prompt = """You are an expert chemical and process engineer with deep knowledge of P&ID (Piping & Instrumentation Diagrams) and process control systems.

Your role is to analyze the provided P&ID graph topology and answer engineering questions about:
- How pipes, equipment, and instruments are connected
- Flow paths through the system
- Control loops and instrumentation
- Safety systems and interlocks
- Equipment relationships and dependencies

The topology is provided as JSON with:
- **nodes**: Each node has an id, type (instrument/valve/equipment), tag, label, and position (x, y)
- **edges**: Each edge has source, target, and type (connected_to/flow/signal/control)

When answering:
1. **Trace connections** by following edges between nodes
2. **Identify flow paths** from source to destination
3. **Explain control loops** by finding instruments and their connections
4. **Use proper engineering terminology** (ISA S5.1 standards)
5. **Be specific** - reference actual node IDs and tags from the topology
6. **If information is missing**, clearly state what cannot be determined from the topology

Format your answers clearly with:
- Direct answer to the question
- Supporting evidence from the topology
- Relevant node IDs and tags
- Any assumptions or limitations

Be concise but thorough. Focus on engineering accuracy."""

        # Create user prompt with topology
        user_prompt = f"""**P&ID Topology Data:**
```json
{json.dumps(topology_json, indent=2)}
```

**User Question:**
{request.question}

Please analyze the topology and provide a detailed engineering answer."""

        # Combine prompts
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        # Generate response with error handling
        logger.info(f"Asking Gemini about P&ID: {request.question}")
        logger.info(f"Topology: {len(request.topology.nodes)} nodes, {len(request.topology.edges)} edges")
        
        try:
            # Use OLD API format (same as HazOp)
            response = model.generate_content(full_prompt)
            
            answer = response.text
            logger.info(f"✓ Gemini response received: {len(answer)} characters")
            
        except Exception as gemini_error:
            # Check if it's a quota error
            error_str = str(gemini_error)
            logger.error(f"Gemini API error: {error_str}")
            
            if "429" in error_str or "quota" in error_str.lower() or "ResourceExhausted" in error_str or "503" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                logger.warning(f"⚠ Gemini API quota exceeded, using fallback analysis")
                # Use fallback rule-based analysis
                answer = generate_fallback_answer(request.question, topology_json)
            else:
                # For other errors, try fallback as well
                logger.warning(f"⚠ Gemini API error, attempting fallback: {error_str}")
                try:
                    answer = generate_fallback_answer(request.question, topology_json)
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
                    raise HTTPException(500, f"Both Gemini and fallback failed: {str(gemini_error)}")
        
        return PIDQuestionResponse(
            answer=answer,
            question=request.question,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in ask_pid_question endpoint: {e}")
        import traceback
        traceback.print_exc()
        
        # Try fallback one more time
        try:
            logger.info("Attempting fallback analysis after error")
            answer = generate_fallback_answer(request.question, topology_json)
            return PIDQuestionResponse(
                answer=answer,
                question=request.question,
                timestamp=datetime.now().isoformat()
            )
        except:
            raise HTTPException(500, f"Failed to process question: {str(e)}")


@app.post("/deliverables/generate")
async def generate_deliverables(
    pid_reference: str = Form(...),
    plc_name: str = Form("PLC-001")
):
    """Generate professional Excel deliverables"""
    
    if not state.current_graph:
        raise HTTPException(400, "No graph loaded. Process an image first.")
    
    # VALIDATION: Check if graph has nodes
    all_nodes = state.current_graph.get_all_nodes()
    if not all_nodes or len(all_nodes) == 0:
        print("[Deliverables] Graph is empty, generating demo data")
        return await generate_demo_deliverables(pid_reference, plc_name)
    
    # VALIDATION: Check if graph has tagged instruments
    tagged_nodes = [n for n in all_nodes if hasattr(n, 'tag') and n.tag]
    print(f"[Deliverables] Generating from {len(all_nodes)} nodes, {len(tagged_nodes)} tagged")
    
    try:
        # Import deliverable generators
        from src.deliverables import (
            InstrumentIndexGenerator,
            IOListGenerator,
            AlarmListGenerator,
            ExcelFormatter
        )
        
        # Create Excel formatter
        formatter = ExcelFormatter()
        
        # Generate Instrument Index
        inst_gen = InstrumentIndexGenerator()
        inst_df = inst_gen.generate(state.current_graph, pid_reference)
        
        # Check if DataFrame is empty
        if inst_df.empty:
            print("[Deliverables] Instrument Index is empty, adding demo data")
            inst_df = create_demo_instrument_index(pid_reference)
        
        formatter.create_formatted_sheet(
            "Instrument Index",
            inst_df,
            f"Instrument Index - {pid_reference}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
        # Generate I/O List
        io_gen = IOListGenerator()
        io_df = io_gen.generate(state.current_graph, pid_reference, plc_name)
        
        if io_df.empty:
            print("[Deliverables] I/O List is empty, adding demo data")
            io_df = create_demo_io_list(pid_reference, plc_name)
        
        formatter.create_formatted_sheet(
            "IO List",
            io_df,
            f"I/O List - {pid_reference}",
            f"PLC/DCS: {plc_name}"
        )
        
        # Generate Alarm List
        alarm_gen = AlarmListGenerator()
        alarm_df = alarm_gen.generate(state.current_graph, pid_reference)
        
        if alarm_df.empty:
            print("[Deliverables] Alarm List is empty, adding demo data")
            alarm_df = create_demo_alarm_list(pid_reference)
        
        formatter.create_formatted_sheet(
            "Alarm List",
            alarm_df,
            f"Alarm & Trip List - {pid_reference}",
            "Safety Critical Items Highlighted"
        )
        
        # Save to temp file
        output_dir = tempfile.gettempdir()
        output_path = os.path.join(output_dir, f"{pid_reference}_deliverables.xlsx")
        formatter.save(output_path)
        
        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"{pid_reference}_deliverables.xlsx"
        )
        
    except Exception as e:
        import traceback
        print(f"Error generating deliverables: {e}")
        print(traceback.format_exc())
        raise HTTPException(500, f"Failed to generate deliverables: {str(e)}")


def create_demo_instrument_index(pid_reference: str):
    """Create demo instrument index data"""
    import pandas as pd
    
    demo_data = [
        {
            'Tag Number': 'FT-101',
            'Instrument Type': 'Flow Transmitter',
            'Measured Variable': 'Flow',
            'Function': 'Transmitter',
            'Service Description': 'Feed flow measurement',
            'P&ID Drawing': pid_reference,
            'Location': 'Field',
            'Connected Equipment': 'P-101',
            'Line Number': 'L-101',
            'Remarks': 'Demo data - no instruments detected in P&ID'
        },
        {
            'Tag Number': 'PT-201',
            'Instrument Type': 'Pressure Transmitter',
            'Measured Variable': 'Pressure',
            'Function': 'Transmitter',
            'Service Description': 'Discharge pressure measurement',
            'P&ID Drawing': pid_reference,
            'Location': 'Field',
            'Connected Equipment': 'V-201',
            'Line Number': 'L-201',
            'Remarks': 'Demo data - no instruments detected in P&ID'
        },
        {
            'Tag Number': 'LT-301',
            'Instrument Type': 'Level Transmitter',
            'Measured Variable': 'Level',
            'Function': 'Transmitter',
            'Service Description': 'Tank level measurement',
            'P&ID Drawing': pid_reference,
            'Location': 'Field',
            'Connected Equipment': 'T-301',
            'Line Number': '',
            'Remarks': 'Demo data - no instruments detected in P&ID'
        }
    ]
    
    return pd.DataFrame(demo_data)


def create_demo_io_list(pid_reference: str, plc_name: str):
    """Create demo I/O list data"""
    import pandas as pd
    
    demo_data = [
        {
            'Tag Number': 'FT-101',
            'Signal Type': 'AI',
            'Description': 'Feed flow measurement',
            'PLC/DCS': plc_name,
            'Card/Slot': 'AI-01',
            'Channel': '01',
            'Range': '0-100 m³/h',
            'Units': 'm³/h',
            'P&ID Drawing': pid_reference,
            'Remarks': 'Demo data - no instruments detected in P&ID'
        },
        {
            'Tag Number': 'PT-201',
            'Signal Type': 'AI',
            'Description': 'Discharge pressure measurement',
            'PLC/DCS': plc_name,
            'Card/Slot': 'AI-01',
            'Channel': '02',
            'Range': '0-10 bar',
            'Units': 'bar',
            'P&ID Drawing': pid_reference,
            'Remarks': 'Demo data - no instruments detected in P&ID'
        },
        {
            'Tag Number': 'FV-101',
            'Signal Type': 'AO',
            'Description': 'Feed flow control valve',
            'PLC/DCS': plc_name,
            'Card/Slot': 'AO-01',
            'Channel': '01',
            'Range': '0-100%',
            'Units': '%',
            'P&ID Drawing': pid_reference,
            'Remarks': 'Demo data - no instruments detected in P&ID'
        }
    ]
    
    return pd.DataFrame(demo_data)


def create_demo_alarm_list(pid_reference: str):
    """Create demo alarm list data"""
    import pandas as pd
    
    demo_data = [
        {
            'Tag Number': 'PAH-201',
            'Alarm Type': 'High Pressure',
            'Priority': 'Critical',
            'Setpoint': '9.5 bar',
            'Action': 'Shutdown pump P-201',
            'P&ID Drawing': pid_reference,
            'Remarks': 'Demo data - no alarms detected in P&ID'
        },
        {
            'Tag Number': 'LAL-301',
            'Alarm Type': 'Low Level',
            'Priority': 'High',
            'Setpoint': '10%',
            'Action': 'Close inlet valve',
            'P&ID Drawing': pid_reference,
            'Remarks': 'Demo data - no alarms detected in P&ID'
        },
        {
            'Tag Number': 'TAH-401',
            'Alarm Type': 'High Temperature',
            'Priority': 'Medium',
            'Setpoint': '80°C',
            'Action': 'Operator notification',
            'P&ID Drawing': pid_reference,
            'Remarks': 'Demo data - no alarms detected in P&ID'
        }
    ]
    
    return pd.DataFrame(demo_data)


async def generate_demo_deliverables(pid_reference: str, plc_name: str):
    """Generate deliverables with demo data when graph is empty"""
    from src.deliverables import ExcelFormatter
    
    formatter = ExcelFormatter()
    
    # Add demo sheets
    formatter.create_formatted_sheet(
        "Instrument Index",
        create_demo_instrument_index(pid_reference),
        f"Instrument Index - {pid_reference}",
        f"Demo Data - No instruments detected in P&ID"
    )
    
    formatter.create_formatted_sheet(
        "IO List",
        create_demo_io_list(pid_reference, plc_name),
        f"I/O List - {pid_reference}",
        f"Demo Data - PLC/DCS: {plc_name}"
    )
    
    formatter.create_formatted_sheet(
        "Alarm List",
        create_demo_alarm_list(pid_reference),
        f"Alarm & Trip List - {pid_reference}",
        "Demo Data - No alarms detected in P&ID"
    )
    
    # Save to temp file
    output_dir = tempfile.gettempdir()
    output_path = os.path.join(output_dir, f"{pid_reference}_deliverables_demo.xlsx")
    formatter.save(output_path)
    
    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"{pid_reference}_deliverables_demo.xlsx"
    )


@app.get("/design-rules/check")
async def check_design_rules():
    """Run automated design rule checks"""
    
    if not state.current_graph:
        raise HTTPException(400, "No graph loaded. Process an image first.")
    
    try:
        from src.advanced import DesignRuleChecker
        
        checker = DesignRuleChecker()
        violations = checker.check_all(state.current_graph)
        
        return {
            "total_violations": len(violations),
            "critical": len([v for v in violations if v.severity.value == "Critical"]),
            "warnings": len([v for v in violations if v.severity.value == "Warning"]),
            "info": len([v for v in violations if v.severity.value == "Info"]),
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "rule_name": v.rule_name,
                    "severity": v.severity.value,
                    "description": v.description,
                    "affected_items": v.affected_items,
                    "recommendation": v.recommendation,
                    "location": v.location
                }
                for v in violations
            ]
        }
        
    except Exception as e:
        import traceback
        print(f"Error checking design rules: {e}")
        print(traceback.format_exc())
        raise HTTPException(500, f"Design rule check failed: {str(e)}")


@app.post("/flow/trace")
async def trace_flow(
    start_node: str = Form(...),
    direction: str = Form("downstream")
):
    """Trace flow path from a starting node"""
    
    if not state.current_graph:
        raise HTTPException(400, "No graph loaded. Process an image first.")
    
    try:
        from src.advanced import FlowSimulator
        
        simulator = FlowSimulator()
        flow_path = simulator.trace_flow_path(
            state.current_graph,
            start_node,
            direction
        )
        
        return {
            "start_node": flow_path.start_node,
            "end_node": flow_path.end_node,
            "path_nodes": flow_path.path_nodes,
            "path_edges": flow_path.path_edges,
            "total_distance": flow_path.total_distance,
            "blocked_by": flow_path.blocked_by
        }
        
    except Exception as e:
        import traceback
        print(f"Error tracing flow: {e}")
        print(traceback.format_exc())
        raise HTTPException(500, f"Flow trace failed: {str(e)}")


@app.post("/flow/simulate-valve")
async def simulate_valve_closure(
    valve_tag: str = Form(...),
    source_node: str = Form(...),
    state_open: bool = Form(False)
):
    """Simulate valve closure and show affected equipment"""
    
    if not state.current_graph:
        raise HTTPException(400, "No graph loaded. Process an image first.")
    
    try:
        from src.advanced import FlowSimulator
        
        simulator = FlowSimulator()
        result = simulator.simulate_valve_closure(
            state.current_graph,
            valve_tag,
            source_node
        )
        
        return result
        
    except Exception as e:
        import traceback
        print(f"Error simulating valve: {e}")
        print(traceback.format_exc())
        raise HTTPException(500, f"Valve simulation failed: {str(e)}")


@app.post("/diff/compare")
async def compare_pids(
    old_image: UploadFile = File(...),
    new_image: UploadFile = File(...)
):
    """Compare two P&ID versions and identify changes"""
    
    try:
        from src.advanced import PIDDiffEngine
        import cv2
        import numpy as np
        
        # Process old image
        old_contents = await old_image.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(old_contents)
            old_path = tmp.name
        
        # Process new image
        new_contents = await new_image.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(new_contents)
            new_path = tmp.name
        
        # TODO: Process both images through perception pipeline
        # For now, return placeholder
        old_result = {"detections": []}
        new_result = {"detections": []}
        
        # Run diff engine
        diff_engine = PIDDiffEngine()
        diff_result = diff_engine.compare(old_result, new_result)
        
        # Cleanup
        os.unlink(old_path)
        os.unlink(new_path)
        
        return {
            "summary": diff_result.summary,
            "added": diff_result.added_items,
            "deleted": diff_result.deleted_items,
            "modified": diff_result.modified_items
        }
        
    except Exception as e:
        import traceback
        print(f"Error comparing P&IDs: {e}")
        print(traceback.format_exc())
        raise HTTPException(500, f"Diff comparison failed: {str(e)}")


# =============================================================================
# HazOp Failure Simulator
# =============================================================================

@app.post("/api/simulate-hazop", response_model=HazOpSimulationResponse)
async def simulate_hazop(request: HazOpSimulationRequest):
    """
    Simulate equipment failure and predict cascading effects using HazOp analysis.
    
    This endpoint uses Gemini AI to act as a senior HazOp safety engineer,
    analyzing the P&ID topology to predict:
    - Immediate hazards and dangers
    - Cascading effects through connected equipment
    - Affected nodes and edges
    - Severity level
    - Emergency response actions
    
    Args:
        request: HazOpSimulationRequest with failed_node_id, failure_mode, and topology
        
    Returns:
        HazOpSimulationResponse with structured predictions
        
    Example:
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
    """
    try:
        logger.info(f"HazOp simulation request: {request.failed_node_id} - {request.failure_mode}")
        
        # Get HazOp simulator instance
        simulator = get_hazop_simulator()
        
        # Run simulation
        result = simulator.simulate_failure(
            failed_node_id=request.failed_node_id,
            failure_mode=request.failure_mode,
            topology=request.topology
        )
        
        logger.info(f"HazOp simulation complete: {result.severity_level} severity")
        
        return result
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"HazOp Simulator not configured: {str(e)}. Please set GOOGLE_API_KEY in .env file."
        )
    except Exception as e:
        logger.error(f"HazOp simulation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"HazOp simulation failed: {str(e)}"
        )


# =============================================================================
# Flow Simulator
# =============================================================================

@app.post("/api/simulate-flow", response_model=FlowSimulationResponse)
async def simulate_flow(request: FlowSimulationRequest):
    """
    Simulate fluid flow through P&ID topology with valve control.
    
    This endpoint performs a directed graph traversal (BFS) starting from a source node,
    respecting closed valves as barriers. It returns the active flow path, showing which
    pipes and equipment have fluid flowing through them.
    
    **Use Cases:**
    - Maintenance planning: "If I close valve V-101, what equipment loses flow?"
    - Troubleshooting: "Why isn't Tank T-202 filling?"
    - Emergency response: "If I close emergency valve EV-101, what's affected?"
    - Process optimization: "What's the flow path from Tank-101 to Tank-501?"
    
    **Algorithm:**
    - Uses Breadth-First Search (BFS) for shortest path
    - Stops traversal at closed valves (does not explore downstream)
    - Calculates total flow distance
    - Identifies blocked nodes
    
    Args:
        request: FlowSimulationRequest containing:
            - topology: Full graph (nodes and edges)
            - start_node_id: Starting node for flow simulation
            - closed_valve_ids: List of valve node IDs that are closed
    
    Returns:
        FlowSimulationResponse with:
            - active_node_ids: Nodes with fluid flow
            - active_edge_ids: Pipes with fluid flow
            - blocked_nodes: Nodes blocked by closed valves
            - flow_path: Complete flow path from start to end
            - total_distance: Total distance of flow path
            - message: Human-readable summary
    
    Example Request:
        ```json
        {
            "topology": {
                "nodes": [
                    {"id": "Tank-101", "type": "equipment.tank", "x": 100, "y": 200},
                    {"id": "V-101", "type": "valve.gate", "x": 200, "y": 200},
                    {"id": "Pump-201", "type": "equipment.pump", "x": 300, "y": 200}
                ],
                "edges": [
                    {"source": "Tank-101", "target": "V-101"},
                    {"source": "V-101", "target": "Pump-201"}
                ]
            },
            "start_node_id": "Tank-101",
            "closed_valve_ids": ["V-101"]
        }
        ```
    
    Example Response:
        ```json
        {
            "active_node_ids": ["Tank-101", "V-101"],
            "active_edge_ids": ["Tank-101-V-101"],
            "blocked_nodes": ["V-101"],
            "flow_path": ["Tank-101", "V-101"],
            "total_distance": 100.0,
            "message": "Flow simulation from Tank-101: 2 nodes reached, 1 connections active. 1 nodes blocked by 1 closed valve(s)."
        }
        ```
    """
    try:
        logger.info(
            f"Flow simulation request: start={request.start_node_id}, "
            f"closed_valves={len(request.closed_valve_ids)}"
        )
        
        # Get flow simulator instance
        simulator = get_flow_simulator()
        
        # Run simulation
        result = simulator.simulate_flow(
            topology=request.topology,
            start_node_id=request.start_node_id,
            closed_valve_ids=request.closed_valve_ids
        )
        
        logger.info(
            f"Flow simulation complete: {len(result.active_node_ids)} active nodes, "
            f"{len(result.active_edge_ids)} active edges"
        )
        
        return result
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Flow simulation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Flow simulation failed: {str(e)}"
        )


@app.post("/api/filter-graph", response_model=Any)
async def filter_graph(request: Dict[str, Any]):
    """
    Filter graph nodes based on natural language query.
    
    Uses Gemini AI to understand the query and return matching node/edge IDs.
    
    Args:
        request: Dict with 'query' (str) and 'topology' (dict)
        
    Returns:
        GraphFilterResponse with matched_node_ids, matched_edge_ids, and explanation
        
    Example:
        ```json
        {
            "query": "Show me all cooling water lines connected to the furnace",
            "topology": {
                "nodes": [...],
                "edges": [...]
            }
        }
        ```
    """
    try:
        from src.api.graph_filter import get_graph_filter, GraphFilterRequest
        
        query = request.get("query", "")
        topology = request.get("topology", {})
        
        logger.info(f"Graph filter request: {query}")
        
        # Get graph filter instance
        graph_filter = get_graph_filter()
        
        # Filter graph
        result = graph_filter.filter_graph(
            query=query,
            topology=topology
        )
        
        logger.info(f"Graph filter complete: {len(result.matched_node_ids)} nodes matched")
        
        return result.dict()
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Graph Filter not configured: {str(e)}. Please set GOOGLE_API_KEY in .env file."
        )
    except Exception as e:
        logger.error(f"Graph filtering failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Graph filtering failed: {str(e)}"
        )


@app.post("/api/generate-maintenance-checklist", response_model=Any)
async def generate_maintenance_checklist(request: Dict[str, Any]):
    """
    Generate equipment-specific maintenance checklist.
    
    Uses Gemini AI to generate preventative maintenance tasks based on equipment type.
    
    Args:
        request: Dict with 'equipment_type', 'equipment_tag', and optional 'equipment_description'
        
    Returns:
        MaintenanceChecklistResponse with tasks, safety warnings, and estimated time
        
    Example:
        ```json
        {
            "equipment_type": "Centrifugal Pump",
            "equipment_tag": "P-101",
            "equipment_description": "Cooling water circulation pump"
        }
        ```
    """
    try:
        from src.api.maintenance_checklist import get_maintenance_generator, MaintenanceChecklistRequest
        
        equipment_type = request.get("equipment_type", "")
        equipment_tag = request.get("equipment_tag", "")
        equipment_description = request.get("equipment_description", "")
        
        logger.info(f"Maintenance checklist request: {equipment_type} ({equipment_tag})")
        
        # Get maintenance generator instance
        generator = get_maintenance_generator()
        
        # Generate checklist
        result = generator.generate_checklist(
            equipment_type=equipment_type,
            equipment_tag=equipment_tag,
            equipment_description=equipment_description
        )
        
        logger.info(f"Maintenance checklist generated: {len(result.tasks)} tasks")
        
        return result.dict()
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Maintenance Checklist Generator not configured: {str(e)}. Please set GOOGLE_API_KEY in .env file."
        )
    except Exception as e:
        logger.error(f"Maintenance checklist generation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Maintenance checklist generation failed: {str(e)}"
        )


@app.post("/api/save-topology")
async def save_topology(topology: Dict[str, Any]):
    """
    Save P&ID topology to file
    
    Saves the edited topology (nodes and edges) to a JSON file
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = Path("data/output/topologies")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"topology_{timestamp}.json"
        filepath = output_dir / filename
        
        # Add metadata
        topology_with_metadata = {
            **topology,
            "metadata": {
                "savedAt": datetime.now().isoformat(),
                "nodeCount": len(topology.get("nodes", [])),
                "edgeCount": len(topology.get("edges", [])),
                "version": "1.0.0"
            }
        }
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(topology_with_metadata, f, indent=2)
        
        logger.info(f"Topology saved to {filepath}")
        
        return {
            "success": True,
            "message": "Topology saved successfully",
            "filename": filename,
            "filepath": str(filepath),
            "nodeCount": len(topology.get("nodes", [])),
            "edgeCount": len(topology.get("edges", []))
        }
        
    except Exception as e:
        logger.error(f"Failed to save topology: {e}")
        raise HTTPException(500, f"Failed to save topology: {str(e)}")


@app.get("/api/load-topology/{filename}")
async def load_topology(filename: str):
    """
    Load P&ID topology from file
    
    Loads a previously saved topology JSON file
    """
    try:
        filepath = Path("data/output/topologies") / filename
        
        if not filepath.exists():
            raise HTTPException(404, f"Topology file not found: {filename}")
        
        with open(filepath, 'r') as f:
            topology = json.load(f)
        
        logger.info(f"Topology loaded from {filepath}")
        
        return topology
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load topology: {e}")
        raise HTTPException(500, f"Failed to load topology: {str(e)}")


@app.get("/api/list-topologies")
async def list_topologies():
    """
    List all saved topologies
    
    Returns a list of all saved topology files with metadata
    """
    try:
        output_dir = Path("data/output/topologies")
        
        if not output_dir.exists():
            return {"topologies": []}
        
        topologies = []
        for filepath in output_dir.glob("topology_*.json"):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                topologies.append({
                    "filename": filepath.name,
                    "savedAt": data.get("metadata", {}).get("savedAt"),
                    "nodeCount": data.get("metadata", {}).get("nodeCount", 0),
                    "edgeCount": data.get("metadata", {}).get("edgeCount", 0),
                })
            except Exception as e:
                logger.warning(f"Failed to read topology file {filepath}: {e}")
                continue
        
        # Sort by saved date (newest first)
        topologies.sort(key=lambda x: x.get("savedAt", ""), reverse=True)
        
        return {"topologies": topologies}
        
    except Exception as e:
        logger.error(f"Failed to list topologies: {e}")
        raise HTTPException(500, f"Failed to list topologies: {str(e)}")


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
