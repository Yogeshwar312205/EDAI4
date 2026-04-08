# ============================================================================
# EDAI4 - COMPLETE 5-LAYER PIPELINE TEST FOR KAGGLE
# ============================================================================
# Copy this entire cell into a Kaggle notebook and run it.
# 
# PREREQUISITES:
# 1. Attach the Golden Model dataset: yogeshwarvshinde/edai4-golden-model
# 2. Attach a P&ID image dataset (or upload your own P&ID images)
# 3. Enable GPU for faster processing
#
# This script tests ALL 5 layers of the EDAI4 pipeline:
#   Layer 1: YOLO Symbol Detection (88.1% mAP50)
#   Layer 2: OCR Text Extraction + ISA S5.1 Parsing
#   Layer 3: Graph Construction + Spatial Analysis
#   Layer 4: Semantic Interpretation + Validation
#   Layer 5: RAG Intelligence (Natural Language Queries)
# ============================================================================

print("=" * 70)
print("EDAI4 - COMPLETE 5-LAYER P&ID INTELLIGENCE PIPELINE")
print("=" * 70)

# ============================================================================
# 0. INSTALL DEPENDENCIES
# ============================================================================
print("\n[1/6] Installing dependencies...")
import subprocess
subprocess.run(["pip", "install", "-q", "ultralytics", "easyocr", "networkx", "scipy"])

import sys
import os
import glob
import random
import math
import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from collections import defaultdict

import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ML imports
from ultralytics import YOLO
import easyocr
import networkx as nx

print("   Dependencies installed!")

# ============================================================================
# 1. CONFIGURATION
# ============================================================================
print("\n[2/6] Configuring paths...")

# Golden Model Path (from attached dataset)
MODEL_PATHS = [
    "/kaggle/input/edai4-golden-model/best.pt",
    "/kaggle/input/datasets/yogeshwarvshinde/edai4-golden-model/best.pt",
]
YOLO_MODEL_PATH = None
for p in MODEL_PATHS:
    if os.path.exists(p):
        YOLO_MODEL_PATH = p
        break

if not YOLO_MODEL_PATH:
    print("   ERROR: Golden model not found! Attach: yogeshwarvshinde/edai4-golden-model")
    raise FileNotFoundError("Golden model not found")

print(f"   Model: {YOLO_MODEL_PATH}")

# Find test image
IMAGE_SEARCH_PATHS = [
    "/kaggle/input/**/images/**/*.jpg",
    "/kaggle/input/**/images/**/*.png",
    "/kaggle/working/**/*.jpg",
    "/kaggle/working/**/*.png",
]

test_images = []
for pattern in IMAGE_SEARCH_PATHS:
    test_images.extend(glob.glob(pattern, recursive=True))

if not test_images:
    print("   WARNING: No test images found. Using demo mode.")
    TEST_IMAGE_PATH = None
else:
    TEST_IMAGE_PATH = random.choice(test_images)
    print(f"   Test Image: {os.path.basename(TEST_IMAGE_PATH)}")

# ============================================================================
# 2. CORE DATA CLASSES
# ============================================================================

@dataclass
class BoundingBox:
    x1: float
    y1: float
    x2: float
    y2: float
    
    @property
    def center(self) -> Tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)
    
    @property
    def width(self) -> float:
        return self.x2 - self.x1
    
    @property
    def height(self) -> float:
        return self.y2 - self.y1
    
    @property
    def area(self) -> float:
        return self.width * self.height


@dataclass
class Detection:
    class_name: str
    confidence: float
    bbox: BoundingBox
    tag_number: Optional[str] = None
    functions: List[str] = field(default_factory=list)
    loop_number: Optional[str] = None


class NodeType(Enum):
    INSTRUMENT = "instrument"
    VALVE = "valve"
    EQUIPMENT = "equipment"
    PUMP = "pump"
    LINE = "line"
    UNKNOWN = "unknown"


class EdgeType(Enum):
    CONTROLS = "controls"
    MEASURES = "measures"
    FLOWS_TO = "flows_to"
    CONNECTED_TO = "connected_to"
    CONTAINS = "contains"


# Class to NodeType mapping
CLASS_TYPE_MAP = {
    "instrument.bubble": NodeType.INSTRUMENT,
    "instrument.inline": NodeType.INSTRUMENT,
    "valve.control": NodeType.VALVE,
    "valve.general": NodeType.VALVE,
    "valve.ball": NodeType.VALVE,
    "valve.gate": NodeType.VALVE,
    "valve.globe": NodeType.VALVE,
    "valve.butterfly": NodeType.VALVE,
    "valve.check": NodeType.VALVE,
    "valve.plug": NodeType.VALVE,
    "valve.safety_relief": NodeType.VALVE,
    "equipment.pump": NodeType.PUMP,
    "equipment.compressor_blower": NodeType.EQUIPMENT,
    "fitting.blind": NodeType.EQUIPMENT,
    "fitting.reducer": NodeType.EQUIPMENT,
    "line.flow_arrow": NodeType.LINE,
}

# ISA S5.1 First Letters
ISA_FIRST_LETTERS = {
    'A': 'Analysis', 'B': 'Burner/Combustion', 'C': 'Conductivity',
    'D': 'Density/Specific Gravity', 'E': 'Voltage', 'F': 'Flow Rate',
    'G': 'Gauging/Position', 'H': 'Hand/Manual', 'I': 'Current',
    'J': 'Power', 'K': 'Time/Schedule', 'L': 'Level',
    'M': 'Moisture/Humidity', 'N': 'User Defined', 'O': 'User Defined',
    'P': 'Pressure', 'Q': 'Quantity', 'R': 'Radiation',
    'S': 'Speed/Frequency', 'T': 'Temperature', 'U': 'Multivariable',
    'V': 'Vibration', 'W': 'Weight/Force', 'X': 'Unclassified',
    'Y': 'Event/State', 'Z': 'Position/Dimension',
}

# ISA S5.1 Succeeding Letters
ISA_SUCCEEDING_LETTERS = {
    'A': 'Alarm', 'C': 'Controller', 'E': 'Element',
    'G': 'Glass/Gauge', 'H': 'High', 'I': 'Indicator',
    'K': 'Control Station', 'L': 'Low', 'R': 'Recorder',
    'S': 'Switch', 'T': 'Transmitter', 'V': 'Valve',
    'Y': 'Relay/Compute', 'Z': 'Driver/Actuator',
}

# ============================================================================
# 3. LAYER 1: YOLO SYMBOL DETECTION
# ============================================================================

def run_layer1(image: np.ndarray, model_path: str) -> List[Detection]:
    """Layer 1: YOLO-based symbol detection."""
    model = YOLO(model_path)
    results = model(image, conf=0.4, verbose=False)
    
    detections = []
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            detections.append(Detection(
                class_name=model.names[int(box.cls[0])],
                confidence=float(box.conf[0]),
                bbox=BoundingBox(float(x1), float(y1), float(x2), float(y2))
            ))
    
    return detections


# ============================================================================
# 4. LAYER 2: OCR + TEXT-SYMBOL ASSOCIATION
# ============================================================================

def parse_isa_tag(text: str) -> Optional[Dict[str, Any]]:
    """Parse ISA S5.1 tag format."""
    text = text.strip().upper()
    
    # Pattern: [Area-]FirstLetter[SucceedingLetters]-LoopNumber[Suffix]
    pattern = r'^(?:(\d+)-)?([A-Z])([A-Z]*)-?(\d+)([A-Z]?)$'
    match = re.match(pattern, text)
    
    if not match:
        return None
    
    area, first_letter, succeeding, loop_num, suffix = match.groups()
    
    if first_letter not in ISA_FIRST_LETTERS:
        return None
    
    functions = []
    for letter in succeeding:
        if letter in ISA_SUCCEEDING_LETTERS:
            functions.append(ISA_SUCCEEDING_LETTERS[letter])
    
    return {
        'area': area,
        'first_letter': first_letter,
        'measured_variable': ISA_FIRST_LETTERS[first_letter],
        'succeeding_letters': succeeding,
        'functions': functions,
        'loop_number': loop_num,
        'suffix': suffix,
        'tag': text,
    }


def run_layer2(image: np.ndarray, detections: List[Detection]) -> List[Detection]:
    """Layer 2: OCR and text-symbol association."""
    reader = easyocr.Reader(['en'], gpu=True, verbose=False)
    ocr_results = reader.readtext(image)
    
    # Parse and associate
    for det in detections:
        cx, cy = det.bbox.center
        
        best_match = None
        best_distance = float('inf')
        
        for bbox, text, conf in ocr_results:
            tx, ty = np.mean(bbox, axis=0)
            distance = math.sqrt((cx - tx)**2 + (cy - ty)**2)
            
            # Check if within association radius
            radius = max(det.bbox.width, det.bbox.height) * 1.5
            if distance < radius and distance < best_distance:
                parsed = parse_isa_tag(text)
                if parsed:
                    best_match = parsed
                    best_distance = distance
        
        if best_match:
            det.tag_number = best_match['tag']
            det.functions = best_match['functions']
            det.loop_number = best_match['loop_number']
    
    return detections


# ============================================================================
# 5. LAYER 3: GRAPH CONSTRUCTION + SPATIAL ANALYSIS
# ============================================================================

@dataclass
class GraphNode:
    id: str
    node_type: NodeType
    label: str
    tag: Optional[str] = None
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0


class PIDGraph:
    """P&ID Knowledge Graph."""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
    
    def add_node(self, node: GraphNode):
        self.nodes[node.id] = node
        self.graph.add_node(node.id, **{
            'type': node.node_type.value,
            'label': node.label,
            'tag': node.tag,
            'x': node.x,
            'y': node.y,
        })
    
    def add_edge(self, edge: GraphEdge):
        self.edges.append(edge)
        self.graph.add_edge(
            edge.source_id,
            edge.target_id,
            type=edge.edge_type.value,
            weight=edge.weight,
        )
    
    @property
    def node_count(self) -> int:
        return len(self.nodes)
    
    @property
    def edge_count(self) -> int:
        return len(self.edges)
    
    def get_nodes_by_type(self, node_type: NodeType) -> List[GraphNode]:
        return [n for n in self.nodes.values() if n.node_type == node_type]
    
    def get_node_by_tag(self, tag: str) -> Optional[GraphNode]:
        for node in self.nodes.values():
            if node.tag == tag:
                return node
        return None


def run_layer3(detections: List[Detection], proximity_threshold: float = 100) -> PIDGraph:
    """Layer 3: Build graph and analyze spatial relationships."""
    graph = PIDGraph()
    
    # Create nodes from detections
    for i, det in enumerate(detections):
        node_type = CLASS_TYPE_MAP.get(det.class_name, NodeType.UNKNOWN)
        
        node = GraphNode(
            id=f"n{i}",
            node_type=node_type,
            label=det.tag_number or det.class_name,
            tag=det.tag_number,
            x=det.bbox.center[0],
            y=det.bbox.center[1],
            width=det.bbox.width,
            height=det.bbox.height,
            metadata={
                'class_name': det.class_name,
                'confidence': det.confidence,
                'functions': det.functions,
                'loop_number': det.loop_number,
            }
        )
        graph.add_node(node)
    
    # Create proximity edges
    nodes_list = list(graph.nodes.values())
    for i, n1 in enumerate(nodes_list):
        for n2 in nodes_list[i+1:]:
            distance = math.sqrt((n1.x - n2.x)**2 + (n1.y - n2.y)**2)
            
            if distance < proximity_threshold:
                # Determine edge type
                if n1.node_type == NodeType.INSTRUMENT and n2.node_type == NodeType.VALVE:
                    edge_type = EdgeType.CONTROLS
                elif n1.node_type == NodeType.INSTRUMENT and n2.node_type in (NodeType.EQUIPMENT, NodeType.PUMP):
                    edge_type = EdgeType.MEASURES
                elif n1.node_type == NodeType.LINE:
                    edge_type = EdgeType.FLOWS_TO
                else:
                    edge_type = EdgeType.CONNECTED_TO
                
                graph.add_edge(GraphEdge(
                    source_id=n1.id,
                    target_id=n2.id,
                    edge_type=edge_type,
                    weight=1.0 / (distance + 1)
                ))
    
    # Containment analysis
    containers = [n for n in nodes_list if n.node_type in (NodeType.EQUIPMENT, NodeType.PUMP)]
    instruments = [n for n in nodes_list if n.node_type == NodeType.INSTRUMENT]
    
    for container in containers:
        cx1 = container.x - container.width / 2
        cy1 = container.y - container.height / 2
        cx2 = container.x + container.width / 2
        cy2 = container.y + container.height / 2
        
        for inst in instruments:
            if cx1 <= inst.x <= cx2 and cy1 <= inst.y <= cy2:
                graph.add_edge(GraphEdge(
                    source_id=container.id,
                    target_id=inst.id,
                    edge_type=EdgeType.CONTAINS,
                ))
    
    return graph


# ============================================================================
# 6. LAYER 4: SEMANTIC INTERPRETATION
# ============================================================================

class ControlStrategy(Enum):
    REGULATORY = "regulatory"
    CASCADE = "cascade"
    RATIO = "ratio"
    FEEDFORWARD = "feedforward"
    SAFETY = "safety"
    MONITORING = "monitoring"


def run_layer4(graph: PIDGraph) -> Dict[str, Any]:
    """Layer 4: Semantic interpretation and validation."""
    results = {
        'valid_tags': [],
        'invalid_tags': [],
        'control_loops': [],
        'safety_functions': [],
        'issues': [],
    }
    
    for node in graph.nodes.values():
        if not node.tag:
            continue
        
        parsed = parse_isa_tag(node.tag)
        if parsed:
            results['valid_tags'].append({
                'tag': node.tag,
                'type': parsed['measured_variable'],
                'functions': parsed['functions'],
            })
        else:
            results['invalid_tags'].append(node.tag)
    
    # Detect control loops (same loop number)
    loop_instruments = defaultdict(list)
    for node in graph.nodes.values():
        loop_num = node.metadata.get('loop_number')
        if loop_num:
            loop_instruments[loop_num].append(node)
    
    for loop_num, instruments in loop_instruments.items():
        strategy = ControlStrategy.REGULATORY
        
        # Check for safety instruments (PSH, TSH, LSH, etc.)
        has_safety = any(
            node.tag and ('SH' in node.tag or 'SL' in node.tag or 'SD' in node.tag)
            for node in instruments
        )
        if has_safety:
            strategy = ControlStrategy.SAFETY
            results['safety_functions'].append({
                'loop': loop_num,
                'instruments': [n.tag for n in instruments if n.tag],
            })
        else:
            results['control_loops'].append({
                'loop': loop_num,
                'strategy': strategy.value,
                'instruments': [n.tag for n in instruments if n.tag],
            })
    
    return results


# ============================================================================
# 7. LAYER 5: RAG INTELLIGENCE
# ============================================================================

# Engineering Knowledge Base
KNOWLEDGE_BASE = {
    "isa_first_letters": """
ISA S5.1 First Letters define the measured variable:
- F = Flow Rate (volume or mass flow)
- L = Level (liquid level in vessels)
- P = Pressure (process pressure)
- T = Temperature (process temperature)
- A = Analysis (composition, pH, conductivity)
""",
    "isa_succeeding_letters": """
ISA S5.1 Succeeding Letters define functions:
- T = Transmitter (sends signal to control system)
- I = Indicator (local display)
- C = Controller (PID control action)
- V = Valve (final control element)
- S = Switch (discrete on/off)
- H = High (alarm level)
- L = Low (alarm level)
- A = Alarm (alert operator)
""",
    "sil_levels": """
Safety Integrity Levels (IEC 61511):
- SIL 1: Risk reduction 10-100x, PFD 0.1-0.01
- SIL 2: Risk reduction 100-1000x, PFD 0.01-0.001
- SIL 3: Risk reduction 1000-10000x, PFD 0.001-0.0001
- SIL 4: Risk reduction 10000-100000x, PFD 0.0001-0.00001
""",
}


class RAGPipeline:
    """Layer 5: RAG-powered Q&A."""
    
    def __init__(self, graph: PIDGraph = None):
        self.graph = graph
        self.knowledge = KNOWLEDGE_BASE
    
    def query(self, question: str) -> Dict[str, Any]:
        """Answer a question about the P&ID."""
        question_lower = question.lower()
        
        # Tag lookup
        tag_match = re.search(r'([A-Z]{2,4}-?\d+[A-Z]?)', question.upper())
        if tag_match and self.graph:
            tag = tag_match.group(1)
            node = self.graph.get_node_by_tag(tag)
            if node:
                parsed = parse_isa_tag(tag)
                return {
                    'answer': f"**{tag}**\n- Type: {parsed['measured_variable'] if parsed else 'Unknown'}\n- Functions: {', '.join(parsed['functions']) if parsed else 'N/A'}",
                    'confidence': 1.0,
                    'source': 'graph',
                }
        
        # List queries
        if 'list' in question_lower and 'instrument' in question_lower:
            if self.graph:
                instruments = self.graph.get_nodes_by_type(NodeType.INSTRUMENT)
                tags = [n.tag for n in instruments if n.tag]
                return {
                    'answer': f"Found {len(tags)} instruments:\n" + ", ".join(tags[:20]),
                    'confidence': 0.9,
                    'source': 'graph',
                }
        
        # Safety queries
        if 'safety' in question_lower or 'sil' in question_lower:
            if self.graph:
                safety_nodes = [n for n in self.graph.nodes.values() 
                              if n.tag and ('SH' in n.tag or 'SL' in n.tag or 'SD' in n.tag)]
                if safety_nodes:
                    tags = [n.tag for n in safety_nodes]
                    return {
                        'answer': f"Safety instruments found: {', '.join(tags)}\n\n{self.knowledge['sil_levels']}",
                        'confidence': 0.9,
                        'source': 'graph+knowledge',
                    }
            return {
                'answer': self.knowledge['sil_levels'],
                'confidence': 0.8,
                'source': 'knowledge',
            }
        
        # Knowledge queries
        if 'first letter' in question_lower or 'what does' in question_lower:
            return {
                'answer': self.knowledge['isa_first_letters'],
                'confidence': 0.8,
                'source': 'knowledge',
            }
        
        if 'function' in question_lower or 'succeeding' in question_lower:
            return {
                'answer': self.knowledge['isa_succeeding_letters'],
                'confidence': 0.8,
                'source': 'knowledge',
            }
        
        # Default response
        return {
            'answer': "I can answer questions about:\n- Specific tags (e.g., 'What is FT-101?')\n- Instrument lists (e.g., 'List all instruments')\n- Safety systems (e.g., 'What safety instruments?')\n- ISA standards (e.g., 'What does F mean?')",
            'confidence': 0.5,
            'source': 'help',
        }


# ============================================================================
# 8. RUN THE COMPLETE PIPELINE
# ============================================================================

print("\n[3/6] Loading YOLO model...")
model = YOLO(YOLO_MODEL_PATH)
print(f"   Model loaded: {model.model.names}")

if TEST_IMAGE_PATH:
    print(f"\n[4/6] Processing image: {os.path.basename(TEST_IMAGE_PATH)}")
    image = cv2.imread(TEST_IMAGE_PATH)
    
    # Layer 1
    print("   Layer 1: Detecting symbols...")
    detections = run_layer1(image, YOLO_MODEL_PATH)
    print(f"   -> {len(detections)} symbols detected")
    
    # Layer 2
    print("   Layer 2: Extracting text...")
    detections = run_layer2(image, detections)
    tagged = sum(1 for d in detections if d.tag_number)
    print(f"   -> {tagged}/{len(detections)} symbols tagged")
    
    # Layer 3
    print("   Layer 3: Building graph...")
    graph = run_layer3(detections)
    print(f"   -> {graph.node_count} nodes, {graph.edge_count} edges")
    
    # Layer 4
    print("   Layer 4: Semantic analysis...")
    semantics = run_layer4(graph)
    print(f"   -> {len(semantics['valid_tags'])} valid tags, {len(semantics['control_loops'])} loops")
    
    # Layer 5
    print("   Layer 5: RAG initialized")
    rag = RAGPipeline(graph)
else:
    print("\n[4/6] No test image - running demo mode")
    detections = []
    graph = PIDGraph()
    semantics = {'valid_tags': [], 'control_loops': [], 'safety_functions': []}
    rag = RAGPipeline()

# ============================================================================
# 9. VISUALIZATION
# ============================================================================

print("\n[5/6] Generating visualizations...")

fig, axes = plt.subplots(1, 3, figsize=(24, 8))

# Panel 1: Detections
if TEST_IMAGE_PATH:
    axes[0].imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    for det in detections:
        color = 'red' if det.node_type == NodeType.INSTRUMENT else 'blue' if det.node_type == NodeType.VALVE else 'green'
        rect = patches.Rectangle(
            (det.bbox.x1, det.bbox.y1), det.bbox.width, det.bbox.height,
            linewidth=2, edgecolor=color, facecolor='none'
        )
        axes[0].add_patch(rect)
        if det.tag_number:
            axes[0].text(det.bbox.x1, det.bbox.y1 - 5, det.tag_number,
                        fontsize=8, color='white', backgroundcolor='green')
else:
    axes[0].text(0.5, 0.5, "No Image\n(Demo Mode)", ha='center', va='center', fontsize=20)
axes[0].set_title(f"Layer 1+2: Detection & OCR ({len(detections)} symbols)", fontsize=14)
axes[0].axis('off')

# Panel 2: Graph
if graph.node_count > 0:
    pos = {n.id: (n.x, -n.y) for n in graph.nodes.values()}  # Flip Y for display
    colors = []
    for node in graph.nodes.values():
        if node.node_type == NodeType.INSTRUMENT:
            colors.append('#4CAF50')  # Green
        elif node.node_type == NodeType.VALVE:
            colors.append('#2196F3')  # Blue
        elif node.node_type in (NodeType.EQUIPMENT, NodeType.PUMP):
            colors.append('#FF9800')  # Orange
        else:
            colors.append('#9E9E9E')  # Gray
    
    nx.draw(graph.graph, pos, ax=axes[1], node_color=colors, node_size=100,
           with_labels=False, edge_color='#CCCCCC', arrows=True)
else:
    axes[1].text(0.5, 0.5, "No Graph Data", ha='center', va='center', fontsize=20)
axes[1].set_title(f"Layer 3: Topology Graph ({graph.node_count} nodes)", fontsize=14)

# Panel 3: Summary
summary_text = f"""
EDAI4 Pipeline Results
======================

Layer 1 (YOLO Detection):
  Symbols: {len(detections)}
  
Layer 2 (OCR + Association):
  Tagged: {sum(1 for d in detections if d.tag_number)}
  
Layer 3 (Graph):
  Nodes: {graph.node_count}
  Edges: {graph.edge_count}
  
Layer 4 (Semantics):
  Valid Tags: {len(semantics['valid_tags'])}
  Control Loops: {len(semantics['control_loops'])}
  Safety Functions: {len(semantics['safety_functions'])}
  
Layer 5 (RAG):
  Ready for queries!
"""
axes[2].text(0.1, 0.9, summary_text, transform=axes[2].transAxes,
            fontsize=12, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
axes[2].axis('off')
axes[2].set_title("Pipeline Summary", fontsize=14)

plt.tight_layout()
plt.savefig('/kaggle/working/edai4_pipeline_results.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================================
# 10. INTERACTIVE RAG DEMO
# ============================================================================

print("\n[6/6] RAG Query Demo")
print("=" * 50)

demo_questions = [
    "What does FT mean in ISA S5.1?",
    "List all instruments",
    "What safety systems are present?",
]

for q in demo_questions:
    print(f"\nQ: {q}")
    result = rag.query(q)
    print(f"A: {result['answer'][:200]}...")
    print(f"   (Confidence: {result['confidence']:.0%}, Source: {result['source']})")

print("\n" + "=" * 70)
print("EDAI4 PIPELINE TEST COMPLETE!")
print("=" * 70)
print("\nOutput saved to: /kaggle/working/edai4_pipeline_results.png")
print("\nTo ask more questions, use: rag.query('your question here')")
