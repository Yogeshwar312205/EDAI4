"""
EDAI4 - SELF-CONTAINED Kaggle Pipeline Test
============================================
This script includes ALL necessary code inline - no module uploads needed!

Just copy-paste this entire script into a Kaggle notebook cell and run.

Requirements:
- Trained YOLO model at: /kaggle/working/runs/detect/edai4_layer1_v2/weights/best.pt
- Validation images at: /kaggle/working/pid_dataset/images/val/
"""

# ============================================================================
# CELL 1: IMPORTS & SETUP
# ============================================================================

import sys
import os
import random
import math
import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Any, Union
from enum import Enum
from collections import defaultdict

import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from ultralytics import YOLO
import easyocr
import networkx as nx

print("✓ All imports successful")

# ============================================================================
# CONFIGURATION
# ============================================================================

YOLO_MODEL_PATH = "/kaggle/working/runs/detect/edai4_layer1_v2/weights/best.pt"
VAL_IMAGES_DIR = "/kaggle/working/pid_dataset/images/val/"

# Verify paths
assert Path(YOLO_MODEL_PATH).exists(), f"Model not found: {YOLO_MODEL_PATH}"
assert Path(VAL_IMAGES_DIR).exists(), f"Val dir not found: {VAL_IMAGES_DIR}"

# Select random validation image
val_dir = Path(VAL_IMAGES_DIR)
all_images = list(val_dir.glob("*.jpg")) + list(val_dir.glob("*.png"))
assert len(all_images) > 0, "No images found in validation directory"
test_image_path = random.choice(all_images)

print(f"🎲 Selected: {test_image_path.name}")
print(f"📁 Model: {YOLO_MODEL_PATH}")

# ============================================================================
# INLINE: Detection Classes
# ============================================================================

@dataclass
class BoundingBox:
    """Bounding box representation."""
    x1: float
    y1: float
    x2: float
    y2: float
    
    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)
    
    @property
    def width(self) -> float:
        return self.x2 - self.x1
    
    @property
    def height(self) -> float:
        return self.y2 - self.y1
    
    def __iter__(self):
        return iter([self.x1, self.y1, self.x2, self.y2])

@dataclass
class Detection:
    """Symbol detection result."""
    class_name: str
    confidence: float
    bbox: BoundingBox
    tag_number: Optional[str] = None
    associated_text: Optional[str] = None

# ============================================================================
# INLINE: Symbol Detector (Layer 1)
# ============================================================================

class SymbolDetector:
    """YOLO-based symbol detector."""
    
    def __init__(self, model_path: str, confidence_threshold: float = 0.4):
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        print(f"✓ YOLO model loaded: {model_path}")
    
    def detect(self, image: np.ndarray) -> list[Detection]:
        """Run detection on image."""
        results = self.model(image, conf=self.confidence_threshold, verbose=False)
        
        detections = []
        for result in results:
            boxes = result.boxes
            for i in range(len(boxes)):
                box = boxes[i]
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                cls_name = self.model.names[cls_id]
                
                detections.append(Detection(
                    class_name=cls_name,
                    confidence=conf,
                    bbox=BoundingBox(x1, y1, x2, y2)
                ))
        
        return detections

# ============================================================================
# INLINE: OCR Engine (Layer 2)
# ============================================================================

@dataclass
class TextRegion:
    """OCR text region."""
    x1: float
    y1: float
    x2: float
    y2: float
    
    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)

@dataclass
class OCRResult:
    """OCR result with text and position."""
    text: str
    confidence: float
    region: TextRegion

class OCREngine:
    """EasyOCR wrapper."""
    
    def __init__(self, languages: list[str] = None):
        languages = languages or ['en']
        self.reader = easyocr.Reader(languages, gpu=True, verbose=False)
        print(f"✓ EasyOCR initialized")
    
    def extract(self, image: np.ndarray) -> list[OCRResult]:
        """Extract text from image."""
        results = self.reader.readtext(image)
        
        ocr_results = []
        for bbox, text, conf in results:
            x1 = min(p[0] for p in bbox)
            y1 = min(p[1] for p in bbox)
            x2 = max(p[0] for p in bbox)
            y2 = max(p[1] for p in bbox)
            
            ocr_results.append(OCRResult(
                text=text,
                confidence=conf,
                region=TextRegion(x1, y1, x2, y2)
            ))
        
        return ocr_results

# ============================================================================
# INLINE: Text Normalizer (ISA S5.1)
# ============================================================================

# ISA function codes
ISA_FUNCTION_CODES = {
    'A': 'Analysis', 'B': 'Burner/Flame', 'C': 'Conductivity',
    'D': 'Density', 'E': 'Voltage', 'F': 'Flow', 'G': 'Gaging',
    'H': 'Hand', 'I': 'Current', 'J': 'Power', 'K': 'Time',
    'L': 'Level', 'M': 'Moisture', 'N': 'User Choice',
    'O': 'User Choice', 'P': 'Pressure', 'Q': 'Quantity',
    'R': 'Radiation', 'S': 'Speed', 'T': 'Temperature',
    'U': 'Multivariable', 'V': 'Vibration', 'W': 'Weight',
    'X': 'Unclassified', 'Y': 'Event', 'Z': 'Position',
}

ISA_MODIFIER_CODES = {
    'I': 'Indicator', 'R': 'Recorder', 'C': 'Controller',
    'T': 'Transmitter', 'S': 'Switch', 'A': 'Alarm',
    'E': 'Element', 'V': 'Valve', 'Y': 'Relay',
    'H': 'High', 'L': 'Low', 'HH': 'High-High', 'LL': 'Low-Low',
}

# Tag patterns
INSTRUMENT_TAG_PATTERN = re.compile(
    r'^(?:(\d{1,3})-)?'  # Optional area prefix
    r'([A-Z]{1,4})'      # Function letters (F, FI, FIT, etc.)
    r'[-_]?'             # Optional separator
    r'(\d{3,5})'         # Loop number
    r'([A-Z])?$',        # Optional suffix
    re.IGNORECASE
)

EQUIPMENT_TAG_PATTERN = re.compile(
    r'^([A-Z]{1,3})'     # Equipment type (P, V, HX, etc.)
    r'[-_]?'
    r'(\d{2,4})'         # Number
    r'([A-Z])?'          # Suffix
    r'(?:/([A-Z]))?$',   # Parallel indicator
    re.IGNORECASE
)

def parse_instrument_tag(text: str) -> Optional[dict]:
    """Parse ISA S5.1 instrument tag."""
    text = text.strip().upper()
    match = INSTRUMENT_TAG_PATTERN.match(text)
    
    if not match:
        return None
    
    area, func, loop, suffix = match.groups()
    
    # Parse function letters
    first_letter = func[0] if func else ''
    modifiers = func[1:] if len(func) > 1 else ''
    
    measured_var = ISA_FUNCTION_CODES.get(first_letter, 'Unknown')
    
    # Build description
    desc_parts = [measured_var]
    for m in modifiers:
        if m in ISA_MODIFIER_CODES:
            desc_parts.append(ISA_MODIFIER_CODES[m])
    
    return {
        'tag': text,
        'area': area,
        'function': func,
        'first_letter': first_letter,
        'modifiers': modifiers,
        'loop_number': loop,
        'suffix': suffix,
        'measured_variable': measured_var,
        'description': ' '.join(desc_parts),
    }

def is_likely_tag(text: str) -> bool:
    """Check if text looks like a tag."""
    text = text.strip().upper()
    if len(text) < 4 or len(text) > 20:
        return False
    if INSTRUMENT_TAG_PATTERN.match(text):
        return True
    if EQUIPMENT_TAG_PATTERN.match(text):
        return True
    return False

# ============================================================================
# INLINE: Text-Symbol Associator
# ============================================================================

def associate_text_to_detections(
    detections: list[Detection],
    ocr_results: list[OCRResult],
    max_distance: float = 100.0
) -> list[Detection]:
    """Associate OCR text with detected symbols."""
    
    used_ocr = set()
    
    for det in detections:
        det_cx, det_cy = det.bbox.center
        best_ocr = None
        best_dist = max_distance
        best_idx = -1
        
        for i, ocr in enumerate(ocr_results):
            if i in used_ocr:
                continue
            
            ocr_cx, ocr_cy = ocr.region.center
            dist = math.sqrt((det_cx - ocr_cx)**2 + (det_cy - ocr_cy)**2)
            
            if dist < best_dist:
                best_dist = dist
                best_ocr = ocr
                best_idx = i
        
        if best_ocr:
            used_ocr.add(best_idx)
            det.associated_text = best_ocr.text
            
            if is_likely_tag(best_ocr.text):
                det.tag_number = best_ocr.text.upper()
    
    return detections

# ============================================================================
# INLINE: InstrumentData for Layer 2 Output
# ============================================================================

@dataclass
class InstrumentData:
    """Structured instrument data from Layer 2."""
    tag_number: str
    tag_type: str  # "instrument", "equipment", "line"
    symbol_class: str
    x: float
    y: float
    bbox: tuple
    confidence: float
    detection_confidence: float
    association_confidence: float
    parsed_tag: Optional[dict] = None
    description: Optional[str] = None
    additional_text: list = field(default_factory=list)

@dataclass
class PipelineResult:
    """Complete Layer 2 output."""
    instruments: list[InstrumentData]
    equipment: list[InstrumentData]
    lines: list[InstrumentData]
    unidentified_symbols: list[InstrumentData]
    
    def to_dict(self) -> dict:
        return {
            'instruments': [vars(i) for i in self.instruments],
            'equipment': [vars(e) for e in self.equipment],
            'lines': [vars(l) for l in self.lines],
            'unidentified_symbols': [vars(u) for u in self.unidentified_symbols],
        }

# ============================================================================
# INLINE: Perception Pipeline (Layer 2 Orchestration)
# ============================================================================

def run_perception_pipeline(
    image: np.ndarray,
    model_path: str,
    association_radius: float = 100.0
) -> PipelineResult:
    """Run complete Layer 2 perception pipeline."""
    
    # Step 1: Symbol Detection
    detector = SymbolDetector(model_path)
    detections = detector.detect(image)
    print(f"  → Detected {len(detections)} symbols")
    
    # Step 2: OCR
    ocr = OCREngine()
    ocr_results = ocr.extract(image)
    print(f"  → Extracted {len(ocr_results)} text regions")
    
    # Step 3: Associate text to symbols
    detections = associate_text_to_detections(detections, ocr_results, association_radius)
    
    # Step 4: Classify and structure output
    instruments = []
    equipment = []
    lines = []
    unidentified = []
    
    for det in detections:
        cx, cy = det.bbox.center
        
        # Parse tag if available
        parsed = None
        desc = None
        tag_type = "unknown"
        
        if det.tag_number:
            parsed = parse_instrument_tag(det.tag_number)
            if parsed:
                desc = parsed.get('description')
                tag_type = "instrument"
        
        inst_data = InstrumentData(
            tag_number=det.tag_number or "UNTAGGED",
            tag_type=tag_type,
            symbol_class=det.class_name,
            x=cx,
            y=cy,
            bbox=(det.bbox.x1, det.bbox.y1, det.bbox.x2, det.bbox.y2),
            confidence=det.confidence,
            detection_confidence=det.confidence,
            association_confidence=0.8 if det.tag_number else 0.0,
            parsed_tag=parsed,
            description=desc,
        )
        
        # Classify by symbol class
        cls_lower = det.class_name.lower()
        if 'instrument' in cls_lower:
            instruments.append(inst_data)
        elif 'equipment' in cls_lower or 'pump' in cls_lower:
            equipment.append(inst_data)
            inst_data.tag_type = "equipment"
        elif 'line' in cls_lower or 'flow' in cls_lower:
            lines.append(inst_data)
            inst_data.tag_type = "line"
        elif 'valve' in cls_lower:
            instruments.append(inst_data)
        else:
            unidentified.append(inst_data)
    
    return PipelineResult(
        instruments=instruments,
        equipment=equipment,
        lines=lines,
        unidentified_symbols=unidentified
    )

# ============================================================================
# INLINE: Graph Types (Layer 3)
# ============================================================================

class NodeType(Enum):
    INSTRUMENT = "instrument"
    VALVE = "valve"
    EQUIPMENT = "equipment"
    PUMP = "pump"
    LINE = "line"
    JUNCTION = "junction"
    UNKNOWN = "unknown"

class EdgeType(Enum):
    CONNECTED_TO = "connected_to"
    MEASURES = "measures"
    CONTROLS = "controls"
    FLOWS_TO = "flows_to"

@dataclass
class GraphNode:
    """Node in P&ID graph."""
    id: str
    node_type: NodeType
    label: str
    tag: Optional[str] = None
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    confidence: float = 0.0
    symbol_class: Optional[str] = None
    description: Optional[str] = None

@dataclass
class GraphEdge:
    """Edge in P&ID graph."""
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0
    attributes: dict = field(default_factory=dict)

# ============================================================================
# INLINE: Graph Builder (Layer 3.1)
# ============================================================================

CLASS_TYPE_MAP = {
    "instrument.bubble": NodeType.INSTRUMENT,
    "instrument.inline": NodeType.INSTRUMENT,
    "valve.gate": NodeType.VALVE,
    "valve.globe": NodeType.VALVE,
    "valve.ball": NodeType.VALVE,
    "valve.butterfly": NodeType.VALVE,
    "valve.check": NodeType.VALVE,
    "valve.plug": NodeType.VALVE,
    "valve.control": NodeType.VALVE,
    "valve.safety_relief": NodeType.VALVE,
    "valve.general": NodeType.VALVE,
    "equipment.pump": NodeType.PUMP,
    "equipment.compressor_blower": NodeType.EQUIPMENT,
    "fitting.blind": NodeType.JUNCTION,
    "fitting.reducer": NodeType.JUNCTION,
}

class PIDGraph:
    """P&ID knowledge graph."""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes: dict[str, GraphNode] = {}
        self.edges: list[GraphEdge] = []
    
    def add_node(self, node: GraphNode):
        self.nodes[node.id] = node
        self.graph.add_node(node.id, **vars(node))
    
    def add_edge(self, edge: GraphEdge):
        self.edges.append(edge)
        self.graph.add_edge(edge.source_id, edge.target_id, **vars(edge))
    
    @property
    def node_count(self) -> int:
        return len(self.nodes)
    
    @property
    def edge_count(self) -> int:
        return len(self.edges)
    
    def get_edges_by_type(self, edge_type: EdgeType) -> list[GraphEdge]:
        return [e for e in self.edges if e.edge_type == edge_type]
    
    def get_node_by_tag(self, tag: str) -> Optional[GraphNode]:
        for n in self.nodes.values():
            if n.tag == tag:
                return n
        return None
    
    def summary(self) -> str:
        instruments = sum(1 for n in self.nodes.values() if n.node_type == NodeType.INSTRUMENT)
        valves = sum(1 for n in self.nodes.values() if n.node_type == NodeType.VALVE)
        equipment = sum(1 for n in self.nodes.values() if n.node_type in (NodeType.EQUIPMENT, NodeType.PUMP))
        tagged = sum(1 for n in self.nodes.values() if n.tag and n.tag != "UNTAGGED")
        
        return (
            f"PIDGraph Summary:\n"
            f"  Total Nodes: {self.node_count}\n"
            f"  - Instruments: {instruments} ({tagged} tagged)\n"
            f"  - Valves: {valves}\n"
            f"  - Equipment: {equipment}\n"
            f"  Total Edges: {self.edge_count}"
        )
    
    def to_dataframe(self):
        import pandas as pd
        data = []
        for node in self.nodes.values():
            data.append({
                'id': node.id,
                'tag': node.tag,
                'type': node.node_type.value,
                'symbol_class': node.symbol_class,
                'x': node.x,
                'y': node.y,
                'confidence': node.confidence,
                'description': node.description,
            })
        return pd.DataFrame(data)

def build_graph(perception_result: PipelineResult, proximity_threshold: float = 200.0) -> PIDGraph:
    """Build graph from Layer 2 output."""
    graph = PIDGraph()
    node_counter = 0
    
    # Combine all items
    all_items = (
        perception_result.instruments +
        perception_result.equipment +
        perception_result.lines +
        perception_result.unidentified_symbols
    )
    
    # Create nodes
    for item in all_items:
        node_counter += 1
        node_id = f"node_{node_counter:04d}"
        
        # Determine node type
        cls_lower = item.symbol_class.lower()
        node_type = CLASS_TYPE_MAP.get(cls_lower, NodeType.UNKNOWN)
        
        if node_type == NodeType.UNKNOWN:
            if 'instrument' in cls_lower:
                node_type = NodeType.INSTRUMENT
            elif 'valve' in cls_lower:
                node_type = NodeType.VALVE
            elif 'pump' in cls_lower:
                node_type = NodeType.PUMP
            elif 'equipment' in cls_lower:
                node_type = NodeType.EQUIPMENT
        
        node = GraphNode(
            id=node_id,
            node_type=node_type,
            label=item.tag_number if item.tag_number != "UNTAGGED" else item.symbol_class,
            tag=item.tag_number if item.tag_number != "UNTAGGED" else None,
            x=item.x,
            y=item.y,
            width=item.bbox[2] - item.bbox[0],
            height=item.bbox[3] - item.bbox[1],
            confidence=item.confidence,
            symbol_class=item.symbol_class,
            description=item.description,
        )
        graph.add_node(node)
    
    # Create edges based on proximity
    nodes_list = list(graph.nodes.values())
    for i, n1 in enumerate(nodes_list):
        for n2 in nodes_list[i+1:]:
            dist = math.sqrt((n1.x - n2.x)**2 + (n1.y - n2.y)**2)
            
            if dist <= proximity_threshold:
                # Determine edge type
                types = {n1.node_type, n2.node_type}
                
                if NodeType.INSTRUMENT in types and NodeType.VALVE in types:
                    edge_type = EdgeType.CONTROLS
                elif NodeType.INSTRUMENT in types and (NodeType.EQUIPMENT in types or NodeType.PUMP in types):
                    edge_type = EdgeType.MEASURES
                elif (NodeType.EQUIPMENT in types or NodeType.PUMP in types) and len(types & {NodeType.EQUIPMENT, NodeType.PUMP}) >= 1:
                    edge_type = EdgeType.FLOWS_TO
                else:
                    edge_type = EdgeType.CONNECTED_TO
                
                edge = GraphEdge(
                    source_id=n1.id,
                    target_id=n2.id,
                    edge_type=edge_type,
                    weight=1.0 - (dist / proximity_threshold),
                )
                graph.add_edge(edge)
    
    return graph

# ============================================================================
# INLINE: Spatial Analyzer (Layer 3.2)
# ============================================================================

@dataclass
class AlignmentGroup:
    """Group of aligned nodes."""
    orientation: str  # "horizontal" or "vertical"
    nodes: list[GraphNode]
    axis_value: float

@dataclass
class SpatialCluster:
    """Spatial cluster of nodes."""
    cluster_id: int
    nodes: list[GraphNode]
    centroid: tuple[float, float]
    radius: float
    
    @property
    def node_count(self) -> int:
        return len(self.nodes)
    
    @property
    def node_types(self) -> dict:
        counts = defaultdict(int)
        for n in self.nodes:
            counts[n.node_type] += 1
        return dict(counts)

def detect_containment(
    nodes: list[GraphNode],
    threshold: float = 0.5
) -> dict[GraphNode, list[GraphNode]]:
    """Detect containment relationships."""
    containment = {}
    
    # Get potential containers (large equipment)
    containers = [n for n in nodes if n.node_type in (NodeType.EQUIPMENT, NodeType.PUMP) and n.width > 50]
    containees = [n for n in nodes if n.node_type in (NodeType.INSTRUMENT, NodeType.VALVE)]
    
    for container in containers:
        contained = []
        c_x1 = container.x - container.width/2
        c_y1 = container.y - container.height/2
        c_x2 = container.x + container.width/2
        c_y2 = container.y + container.height/2
        
        for inst in containees:
            if c_x1 <= inst.x <= c_x2 and c_y1 <= inst.y <= c_y2:
                contained.append(inst)
        
        if contained:
            containment[container] = contained
    
    return containment

def detect_alignment(
    nodes: list[GraphNode],
    tolerance: float = 10.0,
    min_group_size: int = 2
) -> list[AlignmentGroup]:
    """Detect horizontal and vertical alignment."""
    groups = []
    
    # Horizontal alignment (same y)
    h_groups = defaultdict(list)
    for n in nodes:
        # Round to tolerance
        key = round(n.y / tolerance) * tolerance
        h_groups[key].append(n)
    
    for y_val, group_nodes in h_groups.items():
        if len(group_nodes) >= min_group_size:
            groups.append(AlignmentGroup(
                orientation="horizontal",
                nodes=group_nodes,
                axis_value=y_val
            ))
    
    # Vertical alignment (same x)
    v_groups = defaultdict(list)
    for n in nodes:
        key = round(n.x / tolerance) * tolerance
        v_groups[key].append(n)
    
    for x_val, group_nodes in v_groups.items():
        if len(group_nodes) >= min_group_size:
            groups.append(AlignmentGroup(
                orientation="vertical",
                nodes=group_nodes,
                axis_value=x_val
            ))
    
    return groups

def detect_clusters(
    nodes: list[GraphNode],
    distance_threshold: float = 150.0,
    min_cluster_size: int = 3
) -> list[SpatialCluster]:
    """Detect spatial clusters using simple distance-based grouping."""
    if len(nodes) < min_cluster_size:
        return []
    
    # Simple clustering: group by distance
    clusters = []
    assigned = set()
    cluster_id = 0
    
    for i, seed in enumerate(nodes):
        if i in assigned:
            continue
        
        # Find nearby nodes
        cluster_nodes = [seed]
        assigned.add(i)
        
        for j, other in enumerate(nodes):
            if j in assigned:
                continue
            
            # Check distance to any node in cluster
            for cn in cluster_nodes:
                dist = math.sqrt((cn.x - other.x)**2 + (cn.y - other.y)**2)
                if dist <= distance_threshold:
                    cluster_nodes.append(other)
                    assigned.add(j)
                    break
        
        if len(cluster_nodes) >= min_cluster_size:
            # Calculate centroid and radius
            cx = sum(n.x for n in cluster_nodes) / len(cluster_nodes)
            cy = sum(n.y for n in cluster_nodes) / len(cluster_nodes)
            radius = max(
                math.sqrt((n.x - cx)**2 + (n.y - cy)**2)
                for n in cluster_nodes
            )
            
            clusters.append(SpatialCluster(
                cluster_id=cluster_id,
                nodes=cluster_nodes,
                centroid=(cx, cy),
                radius=radius
            ))
            cluster_id += 1
    
    return clusters

def run_spatial_analysis(nodes: list[GraphNode]) -> dict:
    """Run all spatial analyses."""
    return {
        'containment': detect_containment(nodes),
        'alignment': detect_alignment(nodes),
        'clusters': detect_clusters(nodes),
    }

# ============================================================================
# MAIN PIPELINE EXECUTION
# ============================================================================

print("\n" + "=" * 70)
print("🚀 EDAI4 FULL PIPELINE TEST")
print("=" * 70)

# Load image
image = cv2.imread(str(test_image_path))
print(f"\n✓ Loaded image: {image.shape[1]}x{image.shape[0]} pixels")

# ============================================================================
# LAYER 1: YOLO Detection
# ============================================================================

print("\n" + "-" * 70)
print("⚙️ LAYER 1: YOLO Symbol Detection")
print("-" * 70)

detector = SymbolDetector(YOLO_MODEL_PATH)
detections = detector.detect(image)
print(f"✓ Detected {len(detections)} symbols")

# Class distribution
class_counts = defaultdict(int)
for d in detections:
    class_counts[d.class_name] += 1

print("\n📊 Class Distribution:")
for cls, cnt in sorted(class_counts.items(), key=lambda x: -x[1])[:10]:
    print(f"  {cls}: {cnt}")

# Visualize Layer 1
fig, ax = plt.subplots(1, figsize=(20, 15))
ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
ax.set_title("Layer 1: YOLO Symbol Detection", fontsize=18, fontweight='bold')

for det in detections:
    x1, y1, x2, y2 = det.bbox
    w, h = x2 - x1, y2 - y1
    color = 'red' if 'instrument' in det.class_name else 'blue' if 'valve' in det.class_name else 'green'
    rect = patches.Rectangle((x1, y1), w, h, linewidth=2, edgecolor=color, facecolor='none')
    ax.add_patch(rect)

ax.axis('off')
plt.tight_layout()
plt.savefig('/kaggle/working/layer1_detections.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================================
# LAYER 2: OCR + Text-Symbol Association
# ============================================================================

print("\n" + "-" * 70)
print("⚙️ LAYER 2: OCR + Text-Symbol Association")
print("-" * 70)

perception_result = run_perception_pipeline(image, YOLO_MODEL_PATH, association_radius=100)

print(f"\n✓ Instruments: {len(perception_result.instruments)}")
print(f"✓ Equipment: {len(perception_result.equipment)}")
print(f"✓ Lines: {len(perception_result.lines)}")
print(f"✓ Unidentified: {len(perception_result.unidentified_symbols)}")

# Show tagged
tagged = [i for i in perception_result.instruments if i.tag_number != "UNTAGGED"]
print(f"\n📋 Tagged Instruments ({len(tagged)}):")
for inst in tagged[:10]:
    desc = inst.description[:25] if inst.description else "N/A"
    print(f"  {inst.tag_number:15s} - {desc}")

# Visualize Layer 2
fig, ax = plt.subplots(1, figsize=(20, 15))
ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
ax.set_title("Layer 2: OCR + Text-Symbol Association", fontsize=18, fontweight='bold')

for inst in perception_result.instruments:
    x1, y1, x2, y2 = inst.bbox
    color = 'green' if inst.tag_number != "UNTAGGED" else 'yellow'
    rect = patches.Rectangle((x1, y1), x2-x1, y2-y1, linewidth=2, edgecolor=color, facecolor='none')
    ax.add_patch(rect)
    label = inst.tag_number if inst.tag_number != "UNTAGGED" else inst.symbol_class[:15]
    ax.text(x1, y1-5, label, fontsize=8, color='white', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.9))

ax.axis('off')
plt.tight_layout()
plt.savefig('/kaggle/working/layer2_associations.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================================
# LAYER 3.1: Graph Construction
# ============================================================================

print("\n" + "-" * 70)
print("⚙️ LAYER 3.1: Topology Graph Construction")
print("-" * 70)

graph = build_graph(perception_result, proximity_threshold=200.0)
print(f"✓ Built graph: {graph.node_count} nodes, {graph.edge_count} edges")
print("\n" + graph.summary())

# Edge breakdown
print("\n📊 Edge Type Distribution:")
for et in EdgeType:
    edges = graph.get_edges_by_type(et)
    if edges:
        print(f"  {et.value}: {len(edges)}")

# Visualize Layer 3
fig, ax = plt.subplots(1, figsize=(20, 15))

pos = {n.id: (n.x, -n.y) for n in graph.nodes.values()}
color_map = {
    NodeType.INSTRUMENT: '#FF6B6B',
    NodeType.VALVE: '#4ECDC4',
    NodeType.EQUIPMENT: '#45B7D1',
    NodeType.PUMP: '#96CEB4',
    NodeType.UNKNOWN: '#B2BEC3',
}
node_colors = [color_map.get(graph.nodes[n].node_type, '#B2BEC3') for n in graph.graph.nodes()]

nx.draw_networkx_nodes(graph.graph, pos, node_color=node_colors, node_size=300, alpha=0.9, ax=ax)
nx.draw_networkx_edges(graph.graph, pos, edge_color='gray', width=1, alpha=0.5, ax=ax)

labels = {n.id: n.tag if n.tag else '' for n in graph.nodes.values()}
nx.draw_networkx_labels(graph.graph, pos, labels, font_size=7, ax=ax)

ax.set_title("Layer 3.1: P&ID Topology Graph", fontsize=18, fontweight='bold')
ax.axis('off')
plt.tight_layout()
plt.savefig('/kaggle/working/layer3_graph.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================================
# LAYER 3.2: Spatial Analysis
# ============================================================================

print("\n" + "-" * 70)
print("⚙️ LAYER 3.2: Spatial Relationship Analysis")
print("-" * 70)

nodes_list = list(graph.nodes.values())
spatial_results = run_spatial_analysis(nodes_list)

containment = spatial_results['containment']
alignment = spatial_results['alignment']
clusters = spatial_results['clusters']

print(f"\n📦 Containment: {len(containment)} containers")
for container, contained in list(containment.items())[:3]:
    tags = [n.tag or n.label for n in contained]
    print(f"  {container.tag or container.label} contains: {', '.join(tags[:3])}")

print(f"\n📏 Alignment Groups: {len(alignment)}")
h_count = len([g for g in alignment if g.orientation == 'horizontal'])
v_count = len([g for g in alignment if g.orientation == 'vertical'])
print(f"  Horizontal: {h_count}, Vertical: {v_count}")

print(f"\n🌐 Clusters: {len(clusters)}")
for c in clusters[:3]:
    types = c.node_types
    type_str = ', '.join(f"{k.value}:{v}" for k, v in types.items())
    print(f"  Cluster {c.cluster_id}: {c.node_count} nodes ({type_str})")

# Visualize Spatial Analysis
fig, axes = plt.subplots(2, 2, figsize=(20, 16))
fig.suptitle("Layer 3.2: Spatial Relationship Analysis", fontsize=18, fontweight='bold')

# Containment
ax = axes[0, 0]
ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
ax.set_title("Containment", fontsize=14)
for container, contained_list in containment.items():
    x1 = container.x - container.width/2
    y1 = container.y - container.height/2
    rect = patches.Rectangle((x1, y1), container.width, container.height,
                             linewidth=3, edgecolor='blue', facecolor='none')
    ax.add_patch(rect)
    for inst in contained_list:
        ax.plot(inst.x, inst.y, 'ro', markersize=8)
ax.axis('off')

# Alignment
ax = axes[0, 1]
ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
ax.set_title("Alignment Groups", fontsize=14)
for group in alignment[:10]:
    color = 'red' if group.orientation == 'horizontal' else 'blue'
    for node in group.nodes:
        ax.plot(node.x, node.y, 'o', color=color, markersize=6)
    if group.orientation == 'horizontal' and len(group.nodes) > 1:
        xs = [n.x for n in group.nodes]
        ax.plot([min(xs)-30, max(xs)+30], [group.axis_value, group.axis_value], 
                color=color, linestyle='--', alpha=0.7)
ax.axis('off')

# Clusters
ax = axes[1, 0]
ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
ax.set_title("Spatial Clusters", fontsize=14)
colors = plt.cm.Set3(np.linspace(0, 1, max(len(clusters), 1)))
for cluster, col in zip(clusters, colors):
    circle = patches.Circle(cluster.centroid, cluster.radius,
                           edgecolor=col, facecolor=col, alpha=0.2, linewidth=3)
    ax.add_patch(circle)
    for node in cluster.nodes:
        ax.plot(node.x, node.y, 'o', color=col, markersize=8)
ax.axis('off')

# Summary
ax = axes[1, 1]
ax.axis('off')
summary = f"""
SPATIAL ANALYSIS SUMMARY

Nodes Analyzed: {len(nodes_list)}

📦 CONTAINMENT
   Containers: {len(containment)}
   Total Contained: {sum(len(v) for v in containment.values())}

📏 ALIGNMENT
   Horizontal Groups: {h_count}
   Vertical Groups: {v_count}

🌐 CLUSTERS
   Total Clusters: {len(clusters)}
   Clustered Nodes: {sum(c.node_count for c in clusters)}
"""
ax.text(0.1, 0.9, summary, transform=ax.transAxes, fontsize=12,
        verticalalignment='top', fontfamily='monospace',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()
plt.savefig('/kaggle/working/layer3_spatial.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================================
# EXPORT RESULTS
# ============================================================================

print("\n" + "-" * 70)
print("💾 Exporting Results")
print("-" * 70)

# Export JSON
with open('/kaggle/working/perception_result.json', 'w') as f:
    json.dump(perception_result.to_dict(), f, indent=2)
print("✓ Saved: perception_result.json")

# Export CSV
df = graph.to_dataframe()
df.to_csv('/kaggle/working/graph_nodes.csv', index=False)
print("✓ Saved: graph_nodes.csv")

# Export spatial
spatial_export = {
    'containment': {
        (c.tag or c.id): [n.tag or n.id for n in contained]
        for c, contained in containment.items()
    },
    'alignment_count': len(alignment),
    'cluster_count': len(clusters),
}
with open('/kaggle/working/spatial_results.json', 'w') as f:
    json.dump(spatial_export, f, indent=2)
print("✓ Saved: spatial_results.json")

print("\n" + "=" * 70)
print("✅ FULL PIPELINE TEST COMPLETE!")
print("=" * 70)
print("\n📁 Output Files:")
print("  - layer1_detections.png")
print("  - layer2_associations.png")
print("  - layer3_graph.png")
print("  - layer3_spatial.png")
print("  - perception_result.json")
print("  - graph_nodes.csv")
print("  - spatial_results.json")
