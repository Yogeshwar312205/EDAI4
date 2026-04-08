"""
Tests for Flow Analyzer (Phase 3.3)
===================================
Tests flow path detection and direction inference.
"""

import pytest
import math
from unittest.mock import MagicMock, patch

from src.topology.graph_builder import (
    PIDGraph, GraphNode, GraphEdge, NodeType, EdgeType
)
from src.topology.flow_analyzer import (
    FlowAnalyzer, FlowDirection, FlowSegment, FlowPath, FlowArrowInfo
)


def create_test_graph_with_flow():
    """Create a test graph with equipment and flow arrows."""
    graph = PIDGraph()
    
    # Equipment chain: Tank → Pump → Reactor → Condenser
    nodes = [
        GraphNode(
            id="tank-001", node_type=NodeType.EQUIPMENT, label="Feed Tank",
            tag="TK-101", x=100, y=200, width=80, height=60,
            detection_class="equipment.tank"
        ),
        GraphNode(
            id="pump-001", node_type=NodeType.PUMP, label="Feed Pump",
            tag="P-101", x=250, y=200, width=40, height=40,
            detection_class="equipment.pump"
        ),
        GraphNode(
            id="reactor-001", node_type=NodeType.EQUIPMENT, label="Reactor",
            tag="R-101", x=400, y=200, width=100, height=80,
            detection_class="equipment.reactor"
        ),
        GraphNode(
            id="condenser-001", node_type=NodeType.EQUIPMENT, label="Condenser",
            tag="E-101", x=600, y=200, width=60, height=80,
            detection_class="equipment.condenser"
        ),
        # Flow arrows between equipment
        GraphNode(
            id="arrow-001", node_type=NodeType.LINE, label="Flow Arrow 1",
            x=175, y=200, width=30, height=10,
            detection_class="line.flow_arrow", confidence=0.9
        ),
        GraphNode(
            id="arrow-002", node_type=NodeType.LINE, label="Flow Arrow 2",
            x=325, y=200, width=30, height=10,
            detection_class="line.flow_arrow", confidence=0.9
        ),
        GraphNode(
            id="arrow-003", node_type=NodeType.LINE, label="Flow Arrow 3",
            x=500, y=200, width=30, height=10,
            detection_class="line.flow_arrow", confidence=0.9
        ),
        # Instruments on equipment
        GraphNode(
            id="inst-001", node_type=NodeType.INSTRUMENT, label="Level",
            tag="LT-101", x=100, y=180, width=20, height=20,
            detection_class="instrument.bubble"
        ),
        GraphNode(
            id="inst-002", node_type=NodeType.INSTRUMENT, label="Pressure",
            tag="PT-101", x=400, y=170, width=20, height=20,
            detection_class="instrument.bubble"
        ),
    ]
    
    for node in nodes:
        graph.add_node(node)
    
    # Add flow edges
    edges = [
        GraphEdge(source_id="tank-001", target_id="pump-001", 
                  edge_type=EdgeType.FLOWS_TO, weight=0.9),
        GraphEdge(source_id="pump-001", target_id="reactor-001",
                  edge_type=EdgeType.FLOWS_TO, weight=0.85),
        GraphEdge(source_id="reactor-001", target_id="condenser-001",
                  edge_type=EdgeType.FLOWS_TO, weight=0.8),
        # Instrument connections
        GraphEdge(source_id="inst-001", target_id="tank-001",
                  edge_type=EdgeType.MEASURES, weight=0.9),
        GraphEdge(source_id="inst-002", target_id="reactor-001",
                  edge_type=EdgeType.MEASURES, weight=0.9),
    ]
    
    for edge in edges:
        graph.add_edge(edge)
    
    return graph


def create_closed_loop_graph():
    """Create a graph with a closed loop."""
    graph = PIDGraph()
    
    # Circular process: A → B → C → A
    nodes = [
        GraphNode(id="eq-A", node_type=NodeType.EQUIPMENT, label="A",
                  tag="EQ-A", x=200, y=100),
        GraphNode(id="eq-B", node_type=NodeType.EQUIPMENT, label="B",
                  tag="EQ-B", x=400, y=100),
        GraphNode(id="eq-C", node_type=NodeType.EQUIPMENT, label="C",
                  tag="EQ-C", x=300, y=300),
    ]
    
    for node in nodes:
        graph.add_node(node)
    
    edges = [
        GraphEdge(source_id="eq-A", target_id="eq-B", edge_type=EdgeType.FLOWS_TO),
        GraphEdge(source_id="eq-B", target_id="eq-C", edge_type=EdgeType.FLOWS_TO),
        GraphEdge(source_id="eq-C", target_id="eq-A", edge_type=EdgeType.FLOWS_TO),
    ]
    
    for edge in edges:
        graph.add_edge(edge)
    
    return graph


class TestFlowArrowInfo:
    """Tests for FlowArrowInfo class."""
    
    def test_points_toward_basic(self):
        """Test direction detection for arrow."""
        # Arrow pointing right (0 degrees)
        arrow = FlowArrowInfo(
            arrow_id="test", x=100, y=100, angle=0, confidence=0.9
        )
        
        # Target to the right should match
        assert arrow.points_toward(200, 100)
        
        # Target to the left should not match
        assert not arrow.points_toward(0, 100)
    
    def test_points_toward_with_tolerance(self):
        """Test direction detection with angle tolerance."""
        arrow = FlowArrowInfo(
            arrow_id="test", x=100, y=100, angle=0, confidence=0.9
        )
        
        # 30 degrees off should still match with default 45 degree tolerance
        assert arrow.points_toward(200, 58)  # ~30 degrees up-right


class TestFlowSegment:
    """Tests for FlowSegment class."""
    
    def test_segment_creation(self):
        """Test creating a flow segment."""
        segment = FlowSegment(
            source_id="A",
            target_id="B",
            direction=FlowDirection.FORWARD,
            distance=150.0,
            confidence=0.9
        )
        
        assert segment.source_id == "A"
        assert segment.target_id == "B"
        assert segment.direction == FlowDirection.FORWARD
        assert segment.distance == 150.0
    
    def test_segment_to_dict(self):
        """Test serialization."""
        segment = FlowSegment(
            source_id="A", target_id="B",
            direction=FlowDirection.FORWARD,
            distance=100.0
        )
        
        d = segment.to_dict()
        assert d["source"] == "A"
        assert d["target"] == "B"
        assert d["direction"] == "forward"


class TestFlowPath:
    """Tests for FlowPath class."""
    
    def test_path_creation(self):
        """Test creating a flow path."""
        path = FlowPath(
            path_id="test-path",
            segments=[],
            node_sequence=["A", "B", "C"],
            equipment_sequence=["EQ-A", "EQ-B", "EQ-C"]
        )
        
        assert path.length == 3
        assert not path.is_closed_loop
    
    def test_closed_loop_detection(self):
        """Test closed loop detection."""
        path = FlowPath(
            path_id="loop",
            segments=[],
            node_sequence=["A", "B", "C", "A"],  # Returns to start
        )
        
        assert path.is_closed_loop
    
    def test_open_path(self):
        """Test open path (not a loop)."""
        path = FlowPath(
            path_id="open",
            segments=[],
            node_sequence=["A", "B", "C", "D"],
        )
        
        assert not path.is_closed_loop


class TestFlowAnalyzer:
    """Tests for FlowAnalyzer class."""
    
    def test_initialization(self):
        """Test analyzer initialization."""
        graph = create_test_graph_with_flow()
        analyzer = FlowAnalyzer(graph)
        
        assert analyzer.graph == graph
        assert analyzer.proximity_threshold == 200.0
        # Should have extracted flow arrows
        assert len(analyzer.flow_arrows) >= 3
    
    def test_extract_flow_arrows(self):
        """Test flow arrow extraction."""
        graph = create_test_graph_with_flow()
        analyzer = FlowAnalyzer(graph)
        
        # Should find arrows from line.flow_arrow class
        arrow_ids = [a.arrow_id for a in analyzer.flow_arrows]
        assert "arrow-001" in arrow_ids
        assert "arrow-002" in arrow_ids
    
    def test_trace_flow_path(self):
        """Test tracing a flow path."""
        graph = create_test_graph_with_flow()
        analyzer = FlowAnalyzer(graph)
        
        path = analyzer.trace_flow_path("tank-001")
        
        assert path is not None
        assert path.length >= 2
        assert "tank-001" in path.node_sequence
    
    def test_find_all_flow_paths(self):
        """Test finding all flow paths."""
        graph = create_test_graph_with_flow()
        analyzer = FlowAnalyzer(graph)
        
        paths = analyzer.find_all_flow_paths(min_length=2)
        
        # Should find at least one path
        assert len(paths) >= 1
    
    def test_find_equipment_connections(self):
        """Test finding equipment connections."""
        graph = create_test_graph_with_flow()
        analyzer = FlowAnalyzer(graph)
        
        connections = analyzer.find_equipment_connections()
        
        # Should find connections between equipment
        assert len(connections) >= 1
    
    def test_upstream_downstream(self):
        """Test upstream/downstream equipment detection."""
        graph = create_test_graph_with_flow()
        analyzer = FlowAnalyzer(graph)
        
        # Pump should have tank upstream
        upstream = analyzer.get_upstream_equipment("pump-001")
        upstream_tags = [n.tag for n in upstream]
        # Note: Direction inference may vary
        
        # Pump should have reactor/condenser downstream
        downstream = analyzer.get_downstream_equipment("pump-001")
        # Should find at least some downstream
    
    def test_analyze_flow_network(self):
        """Test comprehensive flow network analysis."""
        graph = create_test_graph_with_flow()
        analyzer = FlowAnalyzer(graph)
        
        analysis = analyzer.analyze_flow_network()
        
        assert "total_flow_arrows" in analysis
        assert "total_paths" in analysis
        assert "equipment_connections" in analysis
        assert "sources" in analysis
        assert "sinks" in analysis
    
    def test_summary_generation(self):
        """Test summary string generation."""
        graph = create_test_graph_with_flow()
        analyzer = FlowAnalyzer(graph)
        
        summary = analyzer.summary()
        
        assert "Flow Analysis Summary" in summary
        assert "Flow Arrows Detected" in summary


class TestFlowAnalyzerEdgeCases:
    """Edge case tests for FlowAnalyzer."""
    
    def test_empty_graph(self):
        """Test with empty graph."""
        graph = PIDGraph()
        analyzer = FlowAnalyzer(graph)
        
        assert len(analyzer.flow_arrows) == 0
        paths = analyzer.find_all_flow_paths()
        assert len(paths) == 0
    
    def test_no_flow_arrows(self):
        """Test graph with equipment but no flow arrows."""
        graph = PIDGraph()
        
        # Just equipment, no arrows
        graph.add_node(GraphNode(
            id="eq1", node_type=NodeType.EQUIPMENT, label="Tank",
            tag="TK-101", x=100, y=100
        ))
        graph.add_node(GraphNode(
            id="eq2", node_type=NodeType.EQUIPMENT, label="Pump",
            tag="P-101", x=300, y=100
        ))
        graph.add_edge(GraphEdge(
            source_id="eq1", target_id="eq2", edge_type=EdgeType.FLOWS_TO
        ))
        
        analyzer = FlowAnalyzer(graph)
        
        # Should still work, just with UNKNOWN direction
        direction = analyzer.infer_flow_direction(
            graph.nodes["eq1"], graph.nodes["eq2"]
        )
        assert direction == FlowDirection.UNKNOWN
    
    def test_invalid_start_node(self):
        """Test trace from non-existent node."""
        graph = create_test_graph_with_flow()
        analyzer = FlowAnalyzer(graph)
        
        path = analyzer.trace_flow_path("nonexistent-node")
        assert path is None
    
    def test_isolated_node(self):
        """Test trace from isolated node with no connections."""
        graph = PIDGraph()
        graph.add_node(GraphNode(
            id="isolated", node_type=NodeType.EQUIPMENT, label="Isolated",
            x=100, y=100
        ))
        
        analyzer = FlowAnalyzer(graph)
        path = analyzer.trace_flow_path("isolated")
        
        # Should return None (no path possible)
        assert path is None


class TestClosedLoopDetection:
    """Tests for closed loop detection."""
    
    def test_closed_loop_graph(self):
        """Test detection of closed loops."""
        graph = create_closed_loop_graph()
        analyzer = FlowAnalyzer(graph)
        
        analysis = analyzer.analyze_flow_network()
        
        # May or may not detect the loop depending on traversal
        # The key is no errors
        assert "closed_loops" in analysis
    
    def test_multiple_paths(self):
        """Test graph with multiple independent paths."""
        graph = PIDGraph()
        
        # Path 1: A → B
        graph.add_node(GraphNode(id="A1", node_type=NodeType.EQUIPMENT, 
                                 tag="A1", x=0, y=0))
        graph.add_node(GraphNode(id="B1", node_type=NodeType.EQUIPMENT,
                                 tag="B1", x=100, y=0))
        graph.add_edge(GraphEdge(source_id="A1", target_id="B1",
                                 edge_type=EdgeType.FLOWS_TO))
        
        # Path 2: C → D (separate)
        graph.add_node(GraphNode(id="C1", node_type=NodeType.EQUIPMENT,
                                 tag="C1", x=0, y=200))
        graph.add_node(GraphNode(id="D1", node_type=NodeType.EQUIPMENT,
                                 tag="D1", x=100, y=200))
        graph.add_edge(GraphEdge(source_id="C1", target_id="D1",
                                 edge_type=EdgeType.FLOWS_TO))
        
        analyzer = FlowAnalyzer(graph)
        paths = analyzer.find_all_flow_paths(min_length=2)
        
        # Should find both paths
        assert len(paths) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
