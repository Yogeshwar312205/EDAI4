"""
EDAI4 - Graph Builder
Builds a knowledge graph from P&ID symbols and text

Integrates with Layer 2 (Perception) output to create connected topology graphs.
"""

from dataclasses import dataclass, field
from typing import Any, Optional, Union
from enum import Enum
import networkx as nx
import math

from src.utils import get_logger

logger = get_logger(__name__)


class NodeType(Enum):
    """Types of nodes in the P&ID graph."""
    INSTRUMENT = "instrument"
    VALVE = "valve"
    EQUIPMENT = "equipment"
    PUMP = "pump"
    LINE = "line"
    JUNCTION = "junction"
    TEXT = "text"
    UNKNOWN = "unknown"


class EdgeType(Enum):
    """Types of edges in the P&ID graph."""
    CONNECTED_TO = "connected_to"      # Generic spatial connection
    MEASURES = "measures"               # Instrument → Equipment (measurement)
    CONTROLS = "controls"               # Instrument → Valve (control action)
    FLOWS_TO = "flows_to"              # Equipment → Equipment (process flow)
    PART_OF = "part_of"                # Instrument → Equipment (containment)
    LABELED_BY = "labeled_by"          # Symbol → Text (association)
    LEADS_TO = "leads_to"              # Signal flow (transmitter → controller)


@dataclass
class GraphNode:
    """Node in the P&ID graph."""
    id: str
    node_type: NodeType
    label: str

    # Tag information
    tag: Optional[str] = None
    parsed_tag: Any = None  # ParsedTag from Layer 2

    # Spatial information
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    bbox: tuple[float, float, float, float] = field(default_factory=tuple)

    # Detection metadata
    confidence: float = 0.0
    detection_confidence: float = 0.0
    association_confidence: float = 0.0
    detection_class: Optional[str] = None
    
    # Classification (instrument type, tag type, etc.)
    tag_type: Optional[str] = None  # "instrument", "equipment", "line"
    symbol_class: Optional[str] = None

    # Additional attributes
    attributes: dict = field(default_factory=dict)
    description: Optional[str] = None
    additional_text: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        data = {
            "id": self.id,
            "type": self.node_type.value,
            "label": self.label,
            "tag": self.tag,
            "x": self.x,
            "y": self.y,
            "confidence": self.confidence,
            "detection_class": self.detection_class,
            **self.attributes,
        }
        
        if self.description:
            data["description"] = self.description
            
        if self.parsed_tag:
            data["parsed_tag"] = {
                "area": getattr(self.parsed_tag, 'area', None),
                "function": getattr(self.parsed_tag, 'function', None),
                "modifier": getattr(self.parsed_tag, 'modifier', None),
                "loop_number": getattr(self.parsed_tag, 'loop_number', None),
                "suffix": getattr(self.parsed_tag, 'suffix', None),
            }
        
        return data


@dataclass
class GraphEdge:
    """Edge in the P&ID graph."""
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0
    attributes: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "source": self.source_id,
            "target": self.target_id,
            "type": self.edge_type.value,
            "weight": self.weight,
            **self.attributes,
        }


class PIDGraph:
    """
    Knowledge graph representing a P&ID drawing.
    Uses NetworkX for graph operations.
    """

    def __init__(self):
        """Initialize P&ID graph."""
        self.graph = nx.DiGraph()
        self.nodes: dict[str, GraphNode] = {}
        self.edges: list[GraphEdge] = []

    def add_node(self, node: GraphNode) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node
        self.graph.add_node(
            node.id,
            **node.to_dict()
        )

    def add_edge(self, edge: GraphEdge) -> None:
        """Add an edge to the graph."""
        self.edges.append(edge)
        self.graph.add_edge(
            edge.source_id,
            edge.target_id,
            **edge.to_dict()
        )

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_nodes_by_type(self, node_type: NodeType) -> list[GraphNode]:
        """Get all nodes of a specific type."""
        return [n for n in self.nodes.values() if n.node_type == node_type]

    def get_instruments(self) -> list[GraphNode]:
        """Get all instrument nodes."""
        return self.get_nodes_by_type(NodeType.INSTRUMENT)

    def get_valves(self) -> list[GraphNode]:
        """Get all valve nodes."""
        return self.get_nodes_by_type(NodeType.VALVE)

    def get_neighbors(self, node_id: str) -> list[GraphNode]:
        """Get neighboring nodes."""
        if node_id not in self.graph:
            return []
        neighbor_ids = list(self.graph.neighbors(node_id))
        return [self.nodes[nid] for nid in neighbor_ids if nid in self.nodes]

    def get_tagged_nodes(self) -> list[GraphNode]:
        """Get all nodes with tag numbers."""
        return [n for n in self.nodes.values() if n.tag and n.tag != "UNTAGGED"]
    
    def get_node_by_tag(self, tag: str) -> Optional[GraphNode]:
        """Get a node by its tag number."""
        for node in self.nodes.values():
            if node.tag == tag:
                return node
        return None
    
    def get_equipment(self) -> list[GraphNode]:
        """Get all equipment nodes (pumps, vessels, etc.)."""
        return [n for n in self.nodes.values() 
                if n.node_type in (NodeType.EQUIPMENT, NodeType.PUMP)]
    
    def get_edges_by_type(self, edge_type: EdgeType) -> list[GraphEdge]:
        """Get all edges of a specific type."""
        return [e for e in self.edges if e.edge_type == edge_type]
    
    def get_connected_nodes(self, node_id: str, edge_type: Optional[EdgeType] = None) -> list[tuple[GraphNode, GraphEdge]]:
        """
        Get nodes connected to a given node, optionally filtered by edge type.
        
        Returns:
            List of (connected_node, edge) tuples
        """
        results = []
        for edge in self.edges:
            if edge.source_id == node_id:
                if edge_type is None or edge.edge_type == edge_type:
                    target_node = self.nodes.get(edge.target_id)
                    if target_node:
                        results.append((target_node, edge))
            elif edge.target_id == node_id:
                if edge_type is None or edge.edge_type == edge_type:
                    source_node = self.nodes.get(edge.source_id)
                    if source_node:
                        results.append((source_node, edge))
        return results
    
    def find_shortest_path(self, source_tag: str, target_tag: str) -> Optional[list[GraphNode]]:
        """Find shortest path between two tagged nodes."""
        source_node = self.get_node_by_tag(source_tag)
        target_node = self.get_node_by_tag(target_tag)
        
        if not source_node or not target_node:
            return None
        
        try:
            path_ids = nx.shortest_path(self.graph, source_node.id, target_node.id)
            return [self.nodes[nid] for nid in path_ids]
        except nx.NetworkXNoPath:
            return None

    def to_dataframe(self):
        """Convert nodes to pandas DataFrame."""
        import pandas as pd

        data = []
        for node in self.nodes.values():
            row = {
                "id": node.id,
                "type": node.node_type.value,
                "label": node.label,
                "tag": node.tag,
                "tag_type": node.tag_type,
                "x": node.x,
                "y": node.y,
                "confidence": node.confidence,
                "detection_class": node.detection_class,
                "symbol_class": node.symbol_class,
                "description": node.description,
            }

            # Add parsed tag info if available
            if node.parsed_tag:
                row["function"] = getattr(node.parsed_tag, 'function', None)
                row["modifier"] = getattr(node.parsed_tag, 'modifier', None)
                row["loop_number"] = getattr(node.parsed_tag, 'loop_number', None)
                row["area"] = getattr(node.parsed_tag, 'area', None)

            data.append(row)

        return pd.DataFrame(data)
    
    def summary(self) -> str:
        """Generate a summary string of the graph."""
        instruments = len(self.get_instruments())
        valves = len(self.get_valves())
        equipment = len(self.get_equipment())
        tagged = len(self.get_tagged_nodes())
        
        return (
            f"PIDGraph Summary:\n"
            f"  Total Nodes: {self.node_count}\n"
            f"  - Instruments: {instruments} ({tagged} tagged)\n"
            f"  - Valves: {valves}\n"
            f"  - Equipment: {equipment}\n"
            f"  Total Edges: {self.edge_count}\n"
            f"  Edge Types: {len(set(e.edge_type for e in self.edges))}"
        )

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)


class GraphBuilder:
    """
    Builds P&ID knowledge graphs from Layer 2 perception output.
    
    Supports two modes:
    1. From PipelineResult (Layer 2 integration) - PRIMARY
    2. From raw detections/text (legacy)
    """

    # Mapping from symbol class to node type (Layer 2 classes)
    CLASS_TYPE_MAP = {
        # Instruments
        "instrument.bubble": NodeType.INSTRUMENT,
        "instrument.inline": NodeType.INSTRUMENT,
        "transmitter": NodeType.INSTRUMENT,
        "indicator": NodeType.INSTRUMENT,
        "controller": NodeType.INSTRUMENT,
        "switch": NodeType.INSTRUMENT,
        "instrument_general": NodeType.INSTRUMENT,
        
        # Valves
        "valve.gate": NodeType.VALVE,
        "valve.globe": NodeType.VALVE,
        "valve.ball": NodeType.VALVE,
        "valve.butterfly": NodeType.VALVE,
        "valve.check": NodeType.VALVE,
        "valve.plug": NodeType.VALVE,
        "valve.control": NodeType.VALVE,
        "valve.safety_relief": NodeType.VALVE,
        "valve.general": NodeType.VALVE,
        
        # Equipment
        "equipment.pump": NodeType.PUMP,
        "equipment.compressor_blower": NodeType.EQUIPMENT,
        "pump_centrifugal": NodeType.PUMP,
        "pump_positive": NodeType.PUMP,
        "compressor": NodeType.EQUIPMENT,
        "vessel": NodeType.EQUIPMENT,
        "tank": NodeType.EQUIPMENT,
        "heat_exchanger": NodeType.EQUIPMENT,
        "motor": NodeType.EQUIPMENT,
        
        # Fittings
        "fitting.blind": NodeType.JUNCTION,
        "fitting.reducer": NodeType.JUNCTION,
    }

    def __init__(self, proximity_threshold: float = 200.0):
        """
        Initialize graph builder.
        
        Args:
            proximity_threshold: Maximum distance (pixels) for spatial edges
        """
        self._node_counter = 0
        self.proximity_threshold = proximity_threshold

        logger.info(f"GraphBuilder initialized (proximity_threshold={proximity_threshold}px)")

    def build_from_perception(self, perception_result, pid_name: str = "P&ID") -> PIDGraph:
        """
        Build graph from Layer 2 perception pipeline output.
        
        This is the PRIMARY method for Layer 3 integration.
        
        Args:
            perception_result: PipelineResult from Layer 2
            pid_name: Name of the P&ID drawing
        
        Returns:
            PIDGraph object
        """
        graph = PIDGraph()
        self._node_counter = 0

        logger.info(f"Building graph from perception result for '{pid_name}'...")

        # Create nodes from instruments
        for inst_data in perception_result.instruments:
            node = self._create_node_from_instrument_data(inst_data)
            graph.add_node(node)
            logger.debug(f"Added instrument node: {node.tag}")

        # Create nodes from equipment
        for equip_data in perception_result.equipment:
            node = self._create_node_from_instrument_data(equip_data, force_equipment=True)
            graph.add_node(node)
            logger.debug(f"Added equipment node: {node.tag}")

        # Create nodes from lines
        for line_data in perception_result.lines:
            node = self._create_node_from_instrument_data(line_data, force_line=True)
            graph.add_node(node)
            logger.debug(f"Added line node: {node.tag}")

        # Create nodes from unidentified symbols
        for unid in perception_result.unidentified_symbols:
            node = self._create_node_from_instrument_data(unid)
            graph.add_node(node)
            logger.debug(f"Added unidentified node: {node.detection_class}")

        # Create spatial edges
        self._create_spatial_edges(graph)

        logger.info(
            f"Built graph for '{pid_name}': {graph.node_count} nodes, "
            f"{graph.edge_count} edges"
        )
        logger.info(graph.summary())

        return graph

    def _create_node_from_instrument_data(
        self, 
        inst_data, 
        force_equipment: bool = False,
        force_line: bool = False
    ) -> GraphNode:
        """
        Create a GraphNode from InstrumentData (Layer 2 output).
        
        Args:
            inst_data: InstrumentData from perception pipeline
            force_equipment: Force node type to EQUIPMENT
            force_line: Force node type to LINE
        """
        self._node_counter += 1
        node_id = f"node_{self._node_counter:04d}"

        # Determine node type
        if force_line:
            node_type = NodeType.LINE
        elif force_equipment:
            # Check if it's a pump first
            if "pump" in inst_data.symbol_class.lower():
                node_type = NodeType.PUMP
            else:
                node_type = NodeType.EQUIPMENT
        else:
            class_name = inst_data.symbol_class.lower()
            node_type = self.CLASS_TYPE_MAP.get(class_name, NodeType.UNKNOWN)
            
            # Fallback: check tag_type if class not found
            if node_type == NodeType.UNKNOWN and inst_data.tag_type:
                if inst_data.tag_type == "instrument":
                    node_type = NodeType.INSTRUMENT
                elif inst_data.tag_type == "equipment":
                    node_type = NodeType.EQUIPMENT
                elif inst_data.tag_type == "line":
                    node_type = NodeType.LINE

        # Create node
        node = GraphNode(
            id=node_id,
            node_type=node_type,
            label=inst_data.tag_number if inst_data.tag_number != "UNTAGGED" else inst_data.symbol_class,
            tag=inst_data.tag_number if inst_data.tag_number != "UNTAGGED" else None,
            tag_type=inst_data.tag_type,
            parsed_tag=inst_data.parsed_tag,
            x=inst_data.x,
            y=inst_data.y,
            bbox=inst_data.bbox,
            confidence=inst_data.confidence,
            detection_confidence=inst_data.detection_confidence,
            association_confidence=inst_data.association_confidence,
            detection_class=inst_data.symbol_class,
            symbol_class=inst_data.symbol_class,
            description=inst_data.description,
            additional_text=inst_data.additional_text,
        )

        # Calculate width/height from bbox if available
        if inst_data.bbox and len(inst_data.bbox) == 4:
            node.width = inst_data.bbox[2] - inst_data.bbox[0]
            node.height = inst_data.bbox[3] - inst_data.bbox[1]

        return node

    def _create_spatial_edges(self, graph: PIDGraph) -> None:
        """
        Create edges based on spatial proximity between nodes.
        
        Strategy:
        - Connect nodes within proximity_threshold
        - Determine edge type based on node types
        - Weight edges by inverse distance (closer = higher weight)
        """
        nodes = list(graph.nodes.values())
        edge_count = 0

        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                distance = self._calculate_distance(node1, node2)

                if distance <= self.proximity_threshold:
                    # Determine edge type
                    edge_type = self._determine_edge_type(node1, node2)

                    # Calculate weight (closer = higher)
                    weight = 1.0 - (distance / self.proximity_threshold)

                    edge = GraphEdge(
                        source_id=node1.id,
                        target_id=node2.id,
                        edge_type=edge_type,
                        weight=weight,
                        attributes={
                            "distance": distance,
                            "source_tag": node1.tag,
                            "target_tag": node2.tag,
                        },
                    )
                    graph.add_edge(edge)
                    edge_count += 1

        logger.debug(f"Created {edge_count} spatial edges")

    def _calculate_distance(self, node1: GraphNode, node2: GraphNode) -> float:
        """Calculate Euclidean distance between two nodes."""
        return math.sqrt(
            (node1.x - node2.x) ** 2 +
            (node1.y - node2.y) ** 2
        )

    def _determine_edge_type(
        self,
        node1: GraphNode,
        node2: GraphNode
    ) -> EdgeType:
        """
        Determine edge type based on node types.
        
        Rules:
        - Instrument + Valve → CONTROLS
        - Instrument + Equipment/Pump → MEASURES
        - Equipment + Equipment → FLOWS_TO (potential process flow)
        - Pump + Equipment → FLOWS_TO
        - Default → CONNECTED_TO
        """
        types = {node1.node_type, node2.node_type}

        # Instrument controls valve
        if NodeType.INSTRUMENT in types and NodeType.VALVE in types:
            return EdgeType.CONTROLS

        # Instrument measures equipment
        if NodeType.INSTRUMENT in types and (NodeType.EQUIPMENT in types or NodeType.PUMP in types):
            return EdgeType.MEASURES

        # Equipment/pump flow connections
        if (NodeType.EQUIPMENT in types or NodeType.PUMP in types) and len(types & {NodeType.EQUIPMENT, NodeType.PUMP}) == 2:
            return EdgeType.FLOWS_TO

        # Default
        return EdgeType.CONNECTED_TO
