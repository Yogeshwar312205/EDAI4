"""
Flow Simulator - Digital Twin Topology Simulation
Traces flow paths through P&ID using graph algorithms
"""
from typing import List, Dict, Any, Set, Optional
from collections import deque
from dataclasses import dataclass


@dataclass
class FlowPath:
    """Represents a flow path through the P&ID"""
    start_node: str
    end_node: str
    path_nodes: List[str]
    path_edges: List[str]
    total_distance: float
    blocked_by: Optional[str] = None


class FlowSimulator:
    """Simulate fluid flow through P&ID topology"""
    
    def __init__(self):
        self.valve_states = {}  # Track valve open/closed states
    
    def trace_flow_path(
        self,
        graph,
        start_node_id: str,
        direction: str = 'downstream',
        max_depth: int = 50
    ) -> FlowPath:
        """
        Trace flow path from a starting point
        
        Args:
            graph: P&ID graph
            start_node_id: Starting node ID
            direction: 'downstream' or 'upstream'
            max_depth: Maximum path length to prevent infinite loops
            
        Returns:
            FlowPath object with traced path
        """
        
        start_node = graph.get_node(start_node_id)
        if not start_node:
            raise ValueError(f"Start node {start_node_id} not found")
        
        # BFS to trace flow path
        visited = set()
        queue = deque([(start_node_id, [start_node_id], [], 0.0)])
        
        path_nodes = [start_node_id]
        path_edges = []
        total_distance = 0.0
        blocked_by = None
        end_node_id = start_node_id
        
        while queue and len(path_nodes) < max_depth:
            current_id, current_path, current_edges, current_dist = queue.popleft()
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            current_node = graph.get_node(current_id)
            
            if not current_node:
                continue
            
            # Check if blocked by closed valve
            if self._is_valve_closed(current_node):
                blocked_by = current_node.tag or current_id
                path_nodes = current_path
                path_edges = current_edges
                total_distance = current_dist
                end_node_id = current_id
                break
            
            # Get next nodes based on direction
            if direction == 'downstream':
                edges = list(graph.get_edges_from_node(current_id))
            else:
                edges = list(graph.get_edges_to_node(current_id))
            
            if not edges:
                # Reached end of path
                path_nodes = current_path
                path_edges = current_edges
                total_distance = current_dist
                end_node_id = current_id
                break
            
            for edge in edges:
                next_id = edge.target_id if direction == 'downstream' else edge.source_id
                
                if next_id not in visited:
                    next_node = graph.get_node(next_id)
                    if next_node:
                        # Calculate distance
                        dist = self._calculate_distance(current_node, next_node)
                        
                        new_path = current_path + [next_id]
                        new_edges = current_edges + [edge.id if hasattr(edge, 'id') else f"{current_id}-{next_id}"]
                        new_dist = current_dist + dist
                        
                        queue.append((next_id, new_path, new_edges, new_dist))
                        
                        # Update longest path found
                        if len(new_path) > len(path_nodes):
                            path_nodes = new_path
                            path_edges = new_edges
                            total_distance = new_dist
                            end_node_id = next_id
        
        return FlowPath(
            start_node=start_node_id,
            end_node=end_node_id,
            path_nodes=path_nodes,
            path_edges=path_edges,
            total_distance=total_distance,
            blocked_by=blocked_by
        )
    
    def find_all_paths(
        self,
        graph,
        start_node_id: str,
        end_node_id: str,
        max_paths: int = 10
    ) -> List[FlowPath]:
        """
        Find all possible flow paths between two nodes
        
        Args:
            graph: P&ID graph
            start_node_id: Starting node ID
            end_node_id: Target node ID
            max_paths: Maximum number of paths to find
            
        Returns:
            List of FlowPath objects
        """
        
        paths = []
        
        def dfs(current_id: str, target_id: str, visited: Set[str], path: List[str], edges: List[str], dist: float):
            if len(paths) >= max_paths:
                return
            
            if current_id == target_id:
                paths.append(FlowPath(
                    start_node=start_node_id,
                    end_node=end_node_id,
                    path_nodes=path.copy(),
                    path_edges=edges.copy(),
                    total_distance=dist
                ))
                return
            
            visited.add(current_id)
            current_node = graph.get_node(current_id)
            
            if not current_node:
                return
            
            # Check if blocked
            if self._is_valve_closed(current_node):
                return
            
            for edge in graph.get_edges_from_node(current_id):
                next_id = edge.target_id
                
                if next_id not in visited:
                    next_node = graph.get_node(next_id)
                    if next_node:
                        edge_dist = self._calculate_distance(current_node, next_node)
                        
                        path.append(next_id)
                        edges.append(edge.id if hasattr(edge, 'id') else f"{current_id}-{next_id}")
                        
                        dfs(next_id, target_id, visited.copy(), path, edges, dist + edge_dist)
                        
                        path.pop()
                        edges.pop()
        
        dfs(start_node_id, end_node_id, set(), [start_node_id], [], 0.0)
        
        # Sort by distance
        paths.sort(key=lambda p: p.total_distance)
        
        return paths
    
    def set_valve_state(self, valve_tag: str, is_open: bool):
        """Set valve state (open/closed)"""
        self.valve_states[valve_tag] = is_open
    
    def get_valve_state(self, valve_tag: str) -> bool:
        """Get valve state (default: open)"""
        return self.valve_states.get(valve_tag, True)
    
    def simulate_valve_closure(
        self,
        graph,
        valve_tag: str,
        source_node_id: str
    ) -> Dict[str, Any]:
        """
        Simulate closing a valve and show affected downstream equipment
        
        Args:
            graph: P&ID graph
            valve_tag: Valve to close
            source_node_id: Source node (e.g., tank or pump)
            
        Returns:
            Simulation results with affected equipment
        """
        
        # Find valve node
        valve_node = None
        for node in graph.get_all_nodes():
            if node.tag == valve_tag:
                valve_node = node
                break
        
        if not valve_node:
            return {'error': f'Valve {valve_tag} not found'}
        
        # Trace flow with valve open
        self.set_valve_state(valve_tag, True)
        path_open = self.trace_flow_path(graph, source_node_id, 'downstream')
        
        # Trace flow with valve closed
        self.set_valve_state(valve_tag, False)
        path_closed = self.trace_flow_path(graph, source_node_id, 'downstream')
        
        # Find affected equipment
        affected_nodes = set(path_open.path_nodes) - set(path_closed.path_nodes)
        
        affected_equipment = []
        for node_id in affected_nodes:
            node = graph.get_node(node_id)
            if node and node.node_type.value in ['equipment', 'pump', 'instrument']:
                affected_equipment.append({
                    'id': node_id,
                    'tag': node.tag,
                    'type': node.node_type.value
                })
        
        return {
            'valve': valve_tag,
            'valve_state': 'closed',
            'flow_blocked_at': path_closed.blocked_by,
            'affected_equipment': affected_equipment,
            'path_before': path_open.path_nodes,
            'path_after': path_closed.path_nodes
        }
    
    def _is_valve_closed(self, node) -> bool:
        """Check if node is a closed valve"""
        if node.node_type.value != 'valve':
            return False
        
        if not node.tag:
            return False
        
        return not self.get_valve_state(node.tag)
    
    def _calculate_distance(self, node1, node2) -> float:
        """Calculate distance between two nodes"""
        if hasattr(node1, 'x') and hasattr(node2, 'x'):
            dx = node2.x - node1.x
            dy = node2.y - node1.y
            return (dx**2 + dy**2)**0.5
        return 1.0  # Default unit distance
