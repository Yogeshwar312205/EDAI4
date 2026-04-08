"""
EDAI4 - Flow Path Analyzer
===========================
Analyzes process flow paths through P&ID graphs.

Features:
- Flow path detection following line.flow_arrow symbols
- Direction inference from arrow positions
- Process line tracing through equipment
- Critical path identification
- Flow network analysis
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum
import math

from src.topology.graph_builder import PIDGraph, GraphNode, NodeType, EdgeType
from src.utils import get_logger

logger = get_logger(__name__)


class FlowDirection(Enum):
    """Direction of process flow."""
    FORWARD = "forward"
    REVERSE = "reverse"
    BIDIRECTIONAL = "bidirectional"
    UNKNOWN = "unknown"


@dataclass
class FlowSegment:
    """A segment of a flow path between two nodes."""
    source_id: str
    target_id: str
    direction: FlowDirection
    distance: float
    intermediate_nodes: list[str] = field(default_factory=list)
    confidence: float = 1.0
    
    def to_dict(self) -> dict:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "direction": self.direction.value,
            "distance": self.distance,
            "intermediate_nodes": self.intermediate_nodes,
            "confidence": self.confidence,
        }


@dataclass
class FlowPath:
    """A complete flow path through the P&ID."""
    path_id: str
    segments: list[FlowSegment]
    total_distance: float = 0.0
    node_sequence: list[str] = field(default_factory=list)
    equipment_sequence: list[str] = field(default_factory=list)
    
    @property
    def length(self) -> int:
        """Number of nodes in path."""
        return len(self.node_sequence)
    
    @property
    def is_closed_loop(self) -> bool:
        """Check if path forms a closed loop."""
        return len(self.node_sequence) > 2 and self.node_sequence[0] == self.node_sequence[-1]
    
    def to_dict(self) -> dict:
        return {
            "path_id": self.path_id,
            "length": self.length,
            "total_distance": self.total_distance,
            "is_closed_loop": self.is_closed_loop,
            "node_sequence": self.node_sequence,
            "equipment_sequence": self.equipment_sequence,
            "segments": [s.to_dict() for s in self.segments],
        }


@dataclass
class FlowArrowInfo:
    """Information about a flow arrow and its direction."""
    arrow_id: str
    x: float
    y: float
    angle: float  # Direction angle in degrees (0=right, 90=down)
    confidence: float
    
    def points_toward(self, target_x: float, target_y: float, tolerance: float = 45.0) -> bool:
        """Check if arrow points toward a target location."""
        dx = target_x - self.x
        dy = target_y - self.y
        target_angle = math.degrees(math.atan2(dy, dx))
        
        # Normalize angles to 0-360
        target_angle = target_angle % 360
        arrow_angle = self.angle % 360
        
        # Check if angles are within tolerance
        diff = abs(target_angle - arrow_angle)
        return diff <= tolerance or diff >= (360 - tolerance)


class FlowAnalyzer:
    """
    Analyzes process flow paths in P&ID graphs.
    
    Uses flow arrow symbols to determine direction and traces
    connected paths through equipment and instruments.
    """
    
    def __init__(self, graph: PIDGraph, proximity_threshold: float = 200.0):
        """
        Initialize flow analyzer.
        
        Args:
            graph: PIDGraph to analyze
            proximity_threshold: Maximum distance for flow connectivity
        """
        self.graph = graph
        self.proximity_threshold = proximity_threshold
        self.flow_arrows: list[FlowArrowInfo] = []
        self._extract_flow_arrows()
    
    def _extract_flow_arrows(self):
        """Extract flow arrow information from graph nodes."""
        for node in self.graph.nodes.values():
            if node.node_type == NodeType.LINE or (
                node.detection_class and 'flow_arrow' in node.detection_class.lower()
            ):
                # Estimate arrow direction from bbox aspect ratio and position
                angle = self._estimate_arrow_direction(node)
                self.flow_arrows.append(FlowArrowInfo(
                    arrow_id=node.id,
                    x=node.x,
                    y=node.y,
                    angle=angle,
                    confidence=node.confidence,
                ))
    
    def _estimate_arrow_direction(self, node: GraphNode) -> float:
        """
        Estimate arrow direction from node properties.
        
        Uses bbox aspect ratio and nearby nodes to infer direction.
        """
        # If bbox is wider than tall, likely horizontal flow
        if node.width > node.height * 1.5:
            # Default to right-pointing (0 degrees)
            return 0.0
        elif node.height > node.width * 1.5:
            # Vertical flow - default to down (90 degrees)
            return 90.0
        else:
            # Square-ish - use context from nearby equipment
            nearby = self._find_nearby_equipment(node, radius=150)
            if len(nearby) >= 2:
                # Point from first to second nearby equipment
                dx = nearby[1].x - nearby[0].x
                dy = nearby[1].y - nearby[0].y
                return math.degrees(math.atan2(dy, dx))
            return 0.0  # Default
    
    def _find_nearby_equipment(self, node: GraphNode, radius: float) -> list[GraphNode]:
        """Find equipment nodes within radius of a node."""
        equipment = []
        for eq in self.graph.get_equipment():
            dist = math.sqrt((eq.x - node.x)**2 + (eq.y - node.y)**2)
            if dist <= radius:
                equipment.append((dist, eq))
        
        # Sort by distance and return just the nodes
        equipment.sort(key=lambda x: x[0])
        return [eq for _, eq in equipment]
    
    def infer_flow_direction(self, source: GraphNode, target: GraphNode) -> FlowDirection:
        """
        Infer flow direction between two nodes using flow arrows.
        
        Args:
            source: Source node
            target: Target node
            
        Returns:
            Inferred flow direction
        """
        # Find flow arrows between source and target
        mid_x = (source.x + target.x) / 2
        mid_y = (source.y + target.y) / 2
        
        relevant_arrows = []
        for arrow in self.flow_arrows:
            # Check if arrow is between the two nodes
            arrow_dist = math.sqrt((arrow.x - mid_x)**2 + (arrow.y - mid_y)**2)
            node_dist = math.sqrt((source.x - target.x)**2 + (source.y - target.y)**2)
            
            if arrow_dist <= node_dist / 2 + 50:  # Within the region between nodes
                relevant_arrows.append(arrow)
        
        if not relevant_arrows:
            return FlowDirection.UNKNOWN
        
        # Check if arrows point from source to target
        forward_count = 0
        reverse_count = 0
        
        for arrow in relevant_arrows:
            if arrow.points_toward(target.x, target.y):
                forward_count += 1
            elif arrow.points_toward(source.x, source.y):
                reverse_count += 1
        
        if forward_count > reverse_count:
            return FlowDirection.FORWARD
        elif reverse_count > forward_count:
            return FlowDirection.REVERSE
        elif forward_count > 0 and reverse_count > 0:
            return FlowDirection.BIDIRECTIONAL
        else:
            return FlowDirection.UNKNOWN
    
    def trace_flow_path(self, start_node_id: str, max_hops: int = 20) -> Optional[FlowPath]:
        """
        Trace a flow path starting from a given node.
        
        Follows FLOWS_TO edges and infers direction from flow arrows.
        
        Args:
            start_node_id: Node ID to start tracing from
            max_hops: Maximum number of hops to trace
            
        Returns:
            FlowPath if found, None otherwise
        """
        if start_node_id not in self.graph.nodes:
            logger.warning(f"Node {start_node_id} not found in graph")
            return None
        
        visited = set()
        path_nodes = [start_node_id]
        segments = []
        total_distance = 0.0
        equipment_seq = []
        
        current_id = start_node_id
        visited.add(current_id)
        
        # Track equipment in sequence
        current_node = self.graph.nodes[current_id]
        if current_node.node_type in (NodeType.EQUIPMENT, NodeType.PUMP):
            equipment_seq.append(current_node.tag or current_id)
        
        for _ in range(max_hops):
            # Find connected nodes via FLOWS_TO edges
            connections = self.graph.get_connected_nodes(current_id, EdgeType.FLOWS_TO)
            
            if not connections:
                # Try generic connections
                connections = self.graph.get_connected_nodes(current_id, EdgeType.CONNECTED_TO)
            
            if not connections:
                break
            
            # Pick the best next node (not visited, equipment preferred)
            next_node = None
            next_edge = None
            
            for node, edge in connections:
                if node.id not in visited:
                    if node.node_type in (NodeType.EQUIPMENT, NodeType.PUMP):
                        next_node = node
                        next_edge = edge
                        break
                    elif next_node is None:
                        next_node = node
                        next_edge = edge
            
            if next_node is None:
                break
            
            # Add segment
            current_node = self.graph.nodes[current_id]
            direction = self.infer_flow_direction(current_node, next_node)
            distance = math.sqrt((next_node.x - current_node.x)**2 + 
                                (next_node.y - current_node.y)**2)
            
            segments.append(FlowSegment(
                source_id=current_id,
                target_id=next_node.id,
                direction=direction,
                distance=distance,
                confidence=next_edge.weight if next_edge else 1.0,
            ))
            
            total_distance += distance
            path_nodes.append(next_node.id)
            visited.add(next_node.id)
            
            if next_node.node_type in (NodeType.EQUIPMENT, NodeType.PUMP):
                equipment_seq.append(next_node.tag or next_node.id)
            
            current_id = next_node.id
        
        if len(segments) == 0:
            return None
        
        return FlowPath(
            path_id=f"flow_{start_node_id}",
            segments=segments,
            total_distance=total_distance,
            node_sequence=path_nodes,
            equipment_sequence=equipment_seq,
        )
    
    def find_all_flow_paths(self, min_length: int = 2) -> list[FlowPath]:
        """
        Find all flow paths in the graph.
        
        Starts from equipment nodes and traces forward.
        
        Args:
            min_length: Minimum path length to include
            
        Returns:
            List of discovered flow paths
        """
        paths = []
        traced_starts = set()
        
        # Start from all equipment nodes
        for node in self.graph.get_equipment():
            if node.id in traced_starts:
                continue
            
            path = self.trace_flow_path(node.id)
            if path and path.length >= min_length:
                paths.append(path)
                # Mark all nodes in path as traced
                for nid in path.node_sequence:
                    traced_starts.add(nid)
        
        logger.info(f"Found {len(paths)} flow paths")
        return paths
    
    def find_equipment_connections(self) -> list[tuple[str, str, FlowDirection]]:
        """
        Find all direct connections between equipment nodes.
        
        Returns:
            List of (source_equipment, target_equipment, direction) tuples
        """
        connections = []
        equipment = self.graph.get_equipment()
        
        for i, eq1 in enumerate(equipment):
            for eq2 in equipment[i+1:]:
                # Check if connected
                path = self.graph.find_shortest_path(
                    eq1.tag or eq1.id, 
                    eq2.tag or eq2.id
                )
                
                if path and len(path) <= 5:  # Direct-ish connection
                    direction = self.infer_flow_direction(eq1, eq2)
                    connections.append((
                        eq1.tag or eq1.id,
                        eq2.tag or eq2.id,
                        direction
                    ))
        
        return connections
    
    def get_upstream_equipment(self, node_id: str, max_depth: int = 10) -> list[GraphNode]:
        """
        Find equipment upstream of a node (based on flow direction).
        
        Args:
            node_id: Starting node
            max_depth: Maximum search depth
            
        Returns:
            List of upstream equipment nodes
        """
        if node_id not in self.graph.nodes:
            return []
        
        upstream = []
        visited = {node_id}
        queue = [(node_id, 0)]
        
        while queue:
            current_id, depth = queue.pop(0)
            if depth >= max_depth:
                continue
            
            current_node = self.graph.nodes.get(current_id)
            if not current_node:
                continue
            
            # Get all connected nodes
            for node, edge in self.graph.get_connected_nodes(current_id):
                if node.id in visited:
                    continue
                
                # Check flow direction - we want reverse flow (upstream)
                direction = self.infer_flow_direction(node, current_node)
                if direction in (FlowDirection.FORWARD, FlowDirection.UNKNOWN):
                    # This node flows TO current, so it's upstream
                    visited.add(node.id)
                    if node.node_type in (NodeType.EQUIPMENT, NodeType.PUMP):
                        upstream.append(node)
                    queue.append((node.id, depth + 1))
        
        return upstream
    
    def get_downstream_equipment(self, node_id: str, max_depth: int = 10) -> list[GraphNode]:
        """
        Find equipment downstream of a node (based on flow direction).
        
        Args:
            node_id: Starting node
            max_depth: Maximum search depth
            
        Returns:
            List of downstream equipment nodes
        """
        if node_id not in self.graph.nodes:
            return []
        
        downstream = []
        visited = {node_id}
        queue = [(node_id, 0)]
        
        while queue:
            current_id, depth = queue.pop(0)
            if depth >= max_depth:
                continue
            
            current_node = self.graph.nodes.get(current_id)
            if not current_node:
                continue
            
            # Get all connected nodes
            for node, edge in self.graph.get_connected_nodes(current_id):
                if node.id in visited:
                    continue
                
                # Check flow direction - we want forward flow (downstream)
                direction = self.infer_flow_direction(current_node, node)
                if direction in (FlowDirection.FORWARD, FlowDirection.UNKNOWN):
                    # Current flows TO this node, so it's downstream
                    visited.add(node.id)
                    if node.node_type in (NodeType.EQUIPMENT, NodeType.PUMP):
                        downstream.append(node)
                    queue.append((node.id, depth + 1))
        
        return downstream
    
    def analyze_flow_network(self) -> dict:
        """
        Comprehensive flow network analysis.
        
        Returns:
            Dictionary with flow network statistics and paths
        """
        paths = self.find_all_flow_paths()
        connections = self.find_equipment_connections()
        
        # Find sources (equipment with only outgoing flow)
        # Find sinks (equipment with only incoming flow)
        sources = []
        sinks = []
        
        for eq in self.graph.get_equipment():
            upstream = self.get_upstream_equipment(eq.id, max_depth=3)
            downstream = self.get_downstream_equipment(eq.id, max_depth=3)
            
            if not upstream and downstream:
                sources.append(eq.tag or eq.id)
            elif upstream and not downstream:
                sinks.append(eq.tag or eq.id)
        
        return {
            "total_flow_arrows": len(self.flow_arrows),
            "total_paths": len(paths),
            "paths": [p.to_dict() for p in paths],
            "equipment_connections": [
                {"source": s, "target": t, "direction": d.value}
                for s, t, d in connections
            ],
            "sources": sources,  # Starting points of flow
            "sinks": sinks,      # Ending points of flow
            "closed_loops": [p.path_id for p in paths if p.is_closed_loop],
        }
    
    def summary(self) -> str:
        """Generate human-readable summary of flow analysis."""
        analysis = self.analyze_flow_network()
        
        lines = [
            "Flow Analysis Summary",
            "=" * 40,
            f"Flow Arrows Detected: {analysis['total_flow_arrows']}",
            f"Flow Paths Found: {analysis['total_paths']}",
            f"Equipment Connections: {len(analysis['equipment_connections'])}",
            f"Process Sources: {len(analysis['sources'])}",
            f"Process Sinks: {len(analysis['sinks'])}",
            f"Closed Loops: {len(analysis['closed_loops'])}",
        ]
        
        if analysis['sources']:
            lines.append(f"\nSources: {', '.join(analysis['sources'][:5])}")
        if analysis['sinks']:
            lines.append(f"Sinks: {', '.join(analysis['sinks'][:5])}")
        
        return "\n".join(lines)


def print_flow_analysis_summary(graph: PIDGraph):
    """Convenience function to print flow analysis summary."""
    analyzer = FlowAnalyzer(graph)
    print(analyzer.summary())
    return analyzer.analyze_flow_network()
