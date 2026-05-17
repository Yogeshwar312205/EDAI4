"""
Flow Simulator - Interactive Flow Path Simulation
==================================================
Simulates fluid flow through P&ID topology with valve control.
"""

import logging
from typing import List, Dict, Any, Set, Optional
from collections import deque
import networkx as nx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# =============================================================================
# Pydantic Models
# =============================================================================

class FlowNode(BaseModel):
    """Node in the topology graph."""
    id: str
    type: str
    label: Optional[str] = None
    x: float
    y: float


class FlowEdge(BaseModel):
    """Edge in the topology graph."""
    source: str
    target: str
    type: Optional[str] = "connected_to"


class FlowTopology(BaseModel):
    """Complete topology for flow simulation."""
    nodes: List[FlowNode]
    edges: List[FlowEdge]


class FlowSimulationRequest(BaseModel):
    """Request for flow simulation."""
    topology: FlowTopology
    start_node_id: str
    closed_valve_ids: List[str] = []


class FlowSimulationResponse(BaseModel):
    """Response from flow simulation."""
    active_node_ids: List[str]
    active_edge_ids: List[str]
    blocked_nodes: List[str]
    flow_path: List[str]
    total_distance: float
    message: str


# =============================================================================
# Flow Simulator
# =============================================================================

class FlowSimulator:
    """
    Simulates fluid flow through P&ID topology.
    
    Uses BFS (Breadth-First Search) to traverse the graph from a starting node,
    respecting closed valves as barriers.
    """
    
    def __init__(self):
        self.graph = None
        self.node_positions = {}
    
    def simulate_flow(
        self,
        topology: FlowTopology,
        start_node_id: str,
        closed_valve_ids: List[str]
    ) -> FlowSimulationResponse:
        """
        Simulate fluid flow from a starting node.
        
        Args:
            topology: Graph topology (nodes and edges)
            start_node_id: ID of the starting node
            closed_valve_ids: List of valve node IDs that are closed
        
        Returns:
            FlowSimulationResponse with active nodes and edges
        """
        try:
            # Build NetworkX directed graph
            self.graph = self._build_graph(topology)
            
            # Validate start node exists
            if start_node_id not in self.graph:
                raise ValueError(f"Start node '{start_node_id}' not found in topology")
            
            # Convert closed valves to set for O(1) lookup
            closed_valves = set(closed_valve_ids)
            
            # Perform BFS traversal with valve blocking
            active_nodes, active_edges, blocked_nodes, flow_path = self._bfs_with_valves(
                start_node_id,
                closed_valves
            )
            
            # Calculate total flow distance
            total_distance = self._calculate_flow_distance(active_edges)
            
            # Generate message
            message = self._generate_message(
                start_node_id,
                len(active_nodes),
                len(active_edges),
                len(blocked_nodes),
                len(closed_valves)
            )
            
            return FlowSimulationResponse(
                active_node_ids=list(active_nodes),
                active_edge_ids=active_edges,
                blocked_nodes=list(blocked_nodes),
                flow_path=flow_path,
                total_distance=total_distance,
                message=message
            )
            
        except Exception as e:
            logger.error(f"Flow simulation error: {e}")
            raise
    
    def _build_graph(self, topology: FlowTopology) -> nx.DiGraph:
        """Build NetworkX directed graph from topology."""
        G = nx.DiGraph()
        
        # Add nodes with attributes
        for node in topology.nodes:
            G.add_node(
                node.id,
                type=node.type,
                label=node.label or node.id,
                x=node.x,
                y=node.y
            )
            self.node_positions[node.id] = (node.x, node.y)
        
        # Add edges
        for edge in topology.edges:
            if edge.source in G and edge.target in G:
                G.add_edge(
                    edge.source,
                    edge.target,
                    type=edge.type or "connected_to"
                )
        
        logger.info(f"Built graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        return G
    
    def _bfs_with_valves(
        self,
        start_node_id: str,
        closed_valves: Set[str]
    ) -> tuple[Set[str], List[str], Set[str], List[str]]:
        """
        Perform BFS traversal, stopping at closed valves.
        
        Returns:
            (active_nodes, active_edge_ids, blocked_nodes, flow_path)
        """
        active_nodes = set()
        active_edges = []
        blocked_nodes = set()
        flow_path = []
        
        # BFS queue: (current_node, path_to_node)
        queue = deque([(start_node_id, [start_node_id])])
        visited = set()
        
        while queue:
            current_node, path = queue.popleft()
            
            # Skip if already visited
            if current_node in visited:
                continue
            
            visited.add(current_node)
            active_nodes.add(current_node)
            
            # Update flow path (keep longest path)
            if len(path) > len(flow_path):
                flow_path = path.copy()
            
            # Check if current node is a closed valve
            if current_node in closed_valves:
                blocked_nodes.add(current_node)
                logger.debug(f"Flow blocked at closed valve: {current_node}")
                continue  # Stop traversal at this branch
            
            # Get all downstream neighbors
            neighbors = list(self.graph.successors(current_node))
            
            for neighbor in neighbors:
                if neighbor not in visited:
                    # Add edge to active edges
                    edge_id = f"{current_node}-{neighbor}"
                    active_edges.append(edge_id)
                    
                    # Add to queue with updated path
                    new_path = path + [neighbor]
                    queue.append((neighbor, new_path))
        
        logger.info(
            f"BFS complete: {len(active_nodes)} active nodes, "
            f"{len(active_edges)} active edges, "
            f"{len(blocked_nodes)} blocked nodes"
        )
        
        return active_nodes, active_edges, blocked_nodes, flow_path
    
    def _calculate_flow_distance(self, active_edges: List[str]) -> float:
        """Calculate total distance of flow path."""
        total_distance = 0.0
        
        for edge_id in active_edges:
            try:
                source, target = edge_id.split('-', 1)
                if source in self.node_positions and target in self.node_positions:
                    x1, y1 = self.node_positions[source]
                    x2, y2 = self.node_positions[target]
                    distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                    total_distance += distance
            except Exception as e:
                logger.warning(f"Error calculating distance for edge {edge_id}: {e}")
        
        return round(total_distance, 2)
    
    def _generate_message(
        self,
        start_node: str,
        active_nodes: int,
        active_edges: int,
        blocked_nodes: int,
        closed_valves: int
    ) -> str:
        """Generate human-readable message about simulation."""
        if closed_valves == 0:
            return (
                f"Flow simulation from {start_node}: "
                f"{active_nodes} nodes reached, {active_edges} connections active. "
                f"All valves open."
            )
        elif blocked_nodes > 0:
            return (
                f"Flow simulation from {start_node}: "
                f"{active_nodes} nodes reached, {active_edges} connections active. "
                f"{blocked_nodes} nodes blocked by {closed_valves} closed valve(s)."
            )
        else:
            return (
                f"Flow simulation from {start_node}: "
                f"{active_nodes} nodes reached, {active_edges} connections active. "
                f"{closed_valves} valve(s) closed but not in flow path."
            )


# =============================================================================
# Singleton Instance
# =============================================================================

_flow_simulator = None


def get_flow_simulator() -> FlowSimulator:
    """Get or create flow simulator instance."""
    global _flow_simulator
    if _flow_simulator is None:
        _flow_simulator = FlowSimulator()
        logger.info("✅ Flow Simulator initialized")
    return _flow_simulator
