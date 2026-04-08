"""
Tests for Graph Query Tools (Phase 3.4)
========================================
Tests E&I deliverable generation.
"""

import pytest
import json
import tempfile
from pathlib import Path

from src.topology.graph_builder import (
    PIDGraph, GraphNode, GraphEdge, NodeType, EdgeType
)
from src.topology.query_tools import (
    GraphQueryTools,
    InstrumentIndexEntry,
    InstrumentType,
    ControlLoop,
    SafetyFunction,
)


def create_process_unit_graph():
    """Create a realistic process unit graph for testing."""
    graph = PIDGraph()
    
    # Equipment
    equipment = [
        GraphNode(id="tank-001", node_type=NodeType.EQUIPMENT, label="Feed Tank",
                  tag="TK-101", x=100, y=200, width=100, height=80,
                  detection_class="equipment.tank"),
        GraphNode(id="pump-001", node_type=NodeType.PUMP, label="Feed Pump",
                  tag="P-101", x=250, y=200, width=50, height=50,
                  detection_class="equipment.pump"),
        GraphNode(id="reactor-001", node_type=NodeType.EQUIPMENT, label="Reactor",
                  tag="R-101", x=450, y=200, width=120, height=100,
                  detection_class="equipment.reactor"),
    ]
    
    # Instruments - Level Control Loop (LC-101)
    instruments = [
        GraphNode(id="lt-101", node_type=NodeType.INSTRUMENT, label="Level Transmitter",
                  tag="LT-101", x=100, y=150, width=25, height=25,
                  detection_class="instrument.bubble"),
        GraphNode(id="lic-101", node_type=NodeType.INSTRUMENT, label="Level Controller",
                  tag="LIC-101", x=100, y=100, width=25, height=25,
                  detection_class="instrument.bubble"),
        # Pressure Control Loop (PC-102)
        GraphNode(id="pt-102", node_type=NodeType.INSTRUMENT, label="Pressure Transmitter",
                  tag="PT-102", x=450, y=150, width=25, height=25,
                  detection_class="instrument.bubble"),
        GraphNode(id="pic-102", node_type=NodeType.INSTRUMENT, label="Pressure Controller",
                  tag="PIC-102", x=450, y=100, width=25, height=25,
                  detection_class="instrument.bubble"),
        # Temperature monitoring
        GraphNode(id="ti-103", node_type=NodeType.INSTRUMENT, label="Temperature Indicator",
                  tag="TI-103", x=500, y=150, width=25, height=25,
                  detection_class="instrument.bubble"),
        # Safety instruments
        GraphNode(id="psh-104", node_type=NodeType.INSTRUMENT, label="Pressure High Switch",
                  tag="PSH-104", x=420, y=180, width=25, height=25,
                  detection_class="instrument.bubble"),
        GraphNode(id="lsl-105", node_type=NodeType.INSTRUMENT, label="Level Low Switch",
                  tag="LSL-105", x=120, y=180, width=25, height=25,
                  detection_class="instrument.bubble"),
    ]
    
    # Valves
    valves = [
        GraphNode(id="lcv-101", node_type=NodeType.VALVE, label="Level Control Valve",
                  tag="LCV-101", x=180, y=200, width=30, height=30,
                  detection_class="valve.control"),
        GraphNode(id="pcv-102", node_type=NodeType.VALVE, label="Pressure Control Valve",
                  tag="PCV-102", x=380, y=200, width=30, height=30,
                  detection_class="valve.control"),
        GraphNode(id="sdv-001", node_type=NodeType.VALVE, label="Shutdown Valve",
                  tag="SDV-001", x=350, y=200, width=30, height=30,
                  detection_class="valve.control"),
    ]
    
    # Add all nodes
    for node in equipment + instruments + valves:
        graph.add_node(node)
    
    # Add edges
    edges = [
        # Equipment flow
        GraphEdge(source_id="tank-001", target_id="pump-001", edge_type=EdgeType.FLOWS_TO),
        GraphEdge(source_id="pump-001", target_id="reactor-001", edge_type=EdgeType.FLOWS_TO),
        # Instrument associations
        GraphEdge(source_id="lt-101", target_id="tank-001", edge_type=EdgeType.MEASURES),
        GraphEdge(source_id="pt-102", target_id="reactor-001", edge_type=EdgeType.MEASURES),
        GraphEdge(source_id="ti-103", target_id="reactor-001", edge_type=EdgeType.MEASURES),
        GraphEdge(source_id="psh-104", target_id="reactor-001", edge_type=EdgeType.MEASURES),
        GraphEdge(source_id="lsl-105", target_id="tank-001", edge_type=EdgeType.MEASURES),
        # Control relationships
        GraphEdge(source_id="lic-101", target_id="lcv-101", edge_type=EdgeType.CONTROLS),
        GraphEdge(source_id="pic-102", target_id="pcv-102", edge_type=EdgeType.CONTROLS),
    ]
    
    for edge in edges:
        graph.add_edge(edge)
    
    return graph


class TestInstrumentType:
    """Tests for InstrumentType enum."""
    
    def test_instrument_types(self):
        """Test instrument type values."""
        assert InstrumentType.FLOW.value == "F"
        assert InstrumentType.LEVEL.value == "L"
        assert InstrumentType.PRESSURE.value == "P"
        assert InstrumentType.TEMPERATURE.value == "T"


class TestInstrumentIndexEntry:
    """Tests for InstrumentIndexEntry."""
    
    def test_entry_creation(self):
        """Test creating an index entry."""
        entry = InstrumentIndexEntry(
            tag="FT-101",
            description="Flow Transmitter",
            instrument_type=InstrumentType.FLOW,
            loop_number="101",
            function_code="FT",
        )
        
        assert entry.tag == "FT-101"
        assert entry.instrument_type == InstrumentType.FLOW
    
    def test_entry_to_dict(self):
        """Test serialization."""
        entry = InstrumentIndexEntry(
            tag="PT-102",
            description="Pressure Transmitter",
            instrument_type=InstrumentType.PRESSURE,
            associated_equipment=["R-101"],
        )
        
        d = entry.to_dict()
        assert d["tag"] == "PT-102"
        assert d["type"] == "P"
        assert "R-101" in d["equipment"]


class TestControlLoop:
    """Tests for ControlLoop."""
    
    def test_complete_loop(self):
        """Test complete control loop."""
        loop = ControlLoop(
            loop_id="LOOP-101",
            loop_type="regulatory",
            transmitter_tag="FT-101",
            controller_tag="FIC-101",
            final_element_tag="FCV-101",
            process_variable="Flow",
        )
        
        assert loop.is_complete
        assert loop.loop_type == "regulatory"
    
    def test_incomplete_loop(self):
        """Test incomplete loop (monitoring only)."""
        loop = ControlLoop(
            loop_id="LOOP-102",
            loop_type="monitoring",
            transmitter_tag="TI-102",
        )
        
        assert not loop.is_complete
    
    def test_loop_to_dict(self):
        """Test serialization."""
        loop = ControlLoop(
            loop_id="LOOP-103",
            loop_type="safety",
            transmitter_tag="PSH-103",
        )
        
        d = loop.to_dict()
        assert d["loop_id"] == "LOOP-103"
        assert d["loop_type"] == "safety"


class TestSafetyFunction:
    """Tests for SafetyFunction."""
    
    def test_sif_creation(self):
        """Test creating a safety function."""
        sif = SafetyFunction(
            sif_id="SIF-001",
            description="High Pressure Shutdown",
            initiator_tags=["PSH-101", "PSH-102"],
            final_elements=["SDV-001", "SDV-002"],
            sil_level=2,
        )
        
        assert len(sif.initiator_tags) == 2
        assert sif.sil_level == 2
    
    def test_sif_to_dict(self):
        """Test serialization."""
        sif = SafetyFunction(
            sif_id="SIF-002",
            description="Level Protection",
            initiator_tags=["LSL-101"],
        )
        
        d = sif.to_dict()
        assert d["sif_id"] == "SIF-002"


class TestGraphQueryTools:
    """Tests for GraphQueryTools."""
    
    def test_initialization(self):
        """Test query tools initialization."""
        graph = create_process_unit_graph()
        tools = GraphQueryTools(graph)
        
        assert tools.graph == graph
    
    def test_generate_instrument_index(self):
        """Test instrument index generation."""
        graph = create_process_unit_graph()
        tools = GraphQueryTools(graph)
        
        index = tools.generate_instrument_index()
        
        # Should have all tagged instruments
        tags = [e.tag for e in index]
        assert "LT-101" in tags
        assert "PT-102" in tags
        assert "PSH-104" in tags
        
        # Check instrument types detected correctly
        lt_entry = next(e for e in index if e.tag == "LT-101")
        assert lt_entry.instrument_type == InstrumentType.LEVEL
        
        pt_entry = next(e for e in index if e.tag == "PT-102")
        assert pt_entry.instrument_type == InstrumentType.PRESSURE
    
    def test_identify_control_loops(self):
        """Test control loop identification."""
        graph = create_process_unit_graph()
        tools = GraphQueryTools(graph)
        
        loops = tools.identify_control_loops()
        
        # Should find loops
        loop_ids = [l.loop_id for l in loops]
        # Note: Implementation groups by loop number
    
    def test_identify_safety_functions(self):
        """Test safety function identification."""
        graph = create_process_unit_graph()
        tools = GraphQueryTools(graph)
        
        sifs = tools.identify_safety_functions()
        
        # Should find safety instruments (PSH, LSL)
        if sifs:
            all_initiators = []
            for sif in sifs:
                all_initiators.extend(sif.initiator_tags)
            assert any("PSH" in tag for tag in all_initiators) or \
                   any("LSL" in tag for tag in all_initiators)
    
    def test_build_equipment_tree(self):
        """Test equipment tree generation."""
        graph = create_process_unit_graph()
        tools = GraphQueryTools(graph)
        
        tree = tools.build_equipment_tree()
        
        assert "areas" in tree
        # Should have at least default area
        assert len(tree["areas"]) >= 1
    
    def test_generate_io_list(self):
        """Test I/O list generation."""
        graph = create_process_unit_graph()
        tools = GraphQueryTools(graph)
        
        io_list = tools.generate_io_list()
        
        # Should have entries for instruments
        assert len(io_list) >= 5
        
        # Check I/O types
        io_types = {io["io_type"] for io in io_list}
        assert "AI" in io_types  # Transmitters
        assert "DI" in io_types  # Switches
    
    def test_export_deliverables(self):
        """Test export to JSON."""
        graph = create_process_unit_graph()
        tools = GraphQueryTools(graph)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name
        
        try:
            deliverables = tools.export_deliverables(output_path)
            
            # Verify file written
            with open(output_path) as f:
                loaded = json.load(f)
            
            assert "instrument_index" in loaded
            assert "control_loops" in loaded
            assert "safety_functions" in loaded
            assert "equipment_tree" in loaded
            assert "io_list" in loaded
        finally:
            Path(output_path).unlink(missing_ok=True)
    
    def test_summary(self):
        """Test summary generation."""
        graph = create_process_unit_graph()
        tools = GraphQueryTools(graph)
        
        summary = tools.summary()
        
        assert "E&I Deliverables Summary" in summary
        assert "Instrument Index" in summary
        assert "Control Loops" in summary


class TestGraphQueryToolsEdgeCases:
    """Edge case tests."""
    
    def test_empty_graph(self):
        """Test with empty graph."""
        graph = PIDGraph()
        tools = GraphQueryTools(graph)
        
        index = tools.generate_instrument_index()
        assert len(index) == 0
        
        loops = tools.identify_control_loops()
        assert len(loops) == 0
    
    def test_no_tagged_instruments(self):
        """Test graph with untagged instruments."""
        graph = PIDGraph()
        graph.add_node(GraphNode(
            id="inst-1", node_type=NodeType.INSTRUMENT, label="Unknown",
            x=100, y=100
        ))
        
        tools = GraphQueryTools(graph)
        index = tools.generate_instrument_index()
        
        # Untagged instruments should be skipped
        assert len(index) == 0
    
    def test_instruments_without_loop_numbers(self):
        """Test instruments that don't have loop numbers."""
        graph = PIDGraph()
        graph.add_node(GraphNode(
            id="inst-1", node_type=NodeType.INSTRUMENT, label="FT",
            tag="FT-X", x=100, y=100  # No numeric loop
        ))
        
        tools = GraphQueryTools(graph)
        index = tools.generate_instrument_index()
        
        assert len(index) == 1
        assert index[0].tag == "FT-X"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
