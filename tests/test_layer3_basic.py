"""
Basic test for Layer 3 Graph Builder integration with Layer 2.

This test demonstrates how to build a P&ID graph from Layer 2 output.
Uses mocks to avoid dependencies on YOLO/OCR.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataclasses import dataclass
from typing import Optional
from src.topology.graph_builder import GraphBuilder, NodeType, EdgeType


# Mock Layer 2 output structures
@dataclass
class MockInstrumentData:
    """Mock InstrumentData from Layer 2."""
    tag_number: str
    tag_type: str
    symbol_class: str
    x: float
    y: float
    bbox: tuple
    confidence: float
    detection_confidence: float
    association_confidence: float
    parsed_tag: Optional[object] = None
    description: Optional[str] = None
    additional_text: list = None


@dataclass
class MockPipelineResult:
    """Mock PipelineResult from Layer 2."""
    instruments: list
    equipment: list
    lines: list
    unidentified_symbols: list


def test_basic_graph_construction():
    """Test basic graph construction from Layer 2 output."""
    print("=" * 60)
    print("TEST: Basic Graph Construction from Layer 2")
    print("=" * 60)

    # Create mock Layer 2 output
    instruments = [
        MockInstrumentData(
            tag_number="FIT-101",
            tag_type="instrument",
            symbol_class="instrument.bubble",
            x=100.0,
            y=100.0,
            bbox=(90, 90, 110, 110),
            confidence=0.95,
            detection_confidence=0.93,
            association_confidence=0.90,
            description="Flow Indicator Transmitter",
        ),
        MockInstrumentData(
            tag_number="PCV-201",
            tag_type="instrument",
            symbol_class="instrument.bubble",
            x=300.0,
            y=100.0,
            bbox=(290, 90, 310, 110),
            confidence=0.92,
            detection_confidence=0.90,
            association_confidence=0.88,
            description="Pressure Control Valve",
        ),
    ]

    equipment = [
        MockInstrumentData(
            tag_number="P-101",
            tag_type="equipment",
            symbol_class="equipment.pump",
            x=200.0,
            y=200.0,
            bbox=(180, 180, 220, 220),
            confidence=0.88,
            detection_confidence=0.88,
            association_confidence=0.85,
            description="Centrifugal Pump",
        ),
    ]

    valves = [
        MockInstrumentData(
            tag_number="XV-301",
            tag_type="instrument",
            symbol_class="valve.control",
            x=100.0,
            y=200.0,
            bbox=(90, 190, 110, 210),
            confidence=0.90,
            detection_confidence=0.89,
            association_confidence=0.87,
            description="Control Valve",
        ),
    ]

    perception_result = MockPipelineResult(
        instruments=instruments,
        equipment=equipment,
        lines=[],
        unidentified_symbols=valves,  # Treat valve as unidentified for this test
    )

    # Build graph
    builder = GraphBuilder(proximity_threshold=150.0)
    graph = builder.build_from_perception(perception_result, pid_name="Test-P&ID-001")

    # Assertions
    print(f"\n✓ Graph created with {graph.node_count} nodes")
    assert graph.node_count == 4, f"Expected 4 nodes, got {graph.node_count}"

    print(f"✓ Graph has {graph.edge_count} edges")
    assert graph.edge_count > 0, "Expected at least some edges"

    # Check instruments
    instruments_found = graph.get_instruments()
    print(f"✓ Found {len(instruments_found)} instruments")
    assert len(instruments_found) == 2, f"Expected 2 instruments, got {len(instruments_found)}"

    # Check equipment
    equipment_found = graph.get_equipment()
    print(f"✓ Found {len(equipment_found)} equipment")
    assert len(equipment_found) == 1, f"Expected 1 equipment, got {len(equipment_found)}"

    # Check tagged nodes
    tagged_nodes = graph.get_tagged_nodes()
    print(f"✓ Found {len(tagged_nodes)} tagged nodes")
    assert len(tagged_nodes) == 4, f"Expected 4 tagged nodes, got {len(tagged_nodes)}"

    # Check node lookup by tag
    fit_node = graph.get_node_by_tag("FIT-101")
    assert fit_node is not None, "Could not find FIT-101"
    assert fit_node.node_type == NodeType.INSTRUMENT
    assert fit_node.x == 100.0
    print(f"✓ Successfully retrieved node FIT-101: {fit_node.label}")

    # Check edges
    measures_edges = graph.get_edges_by_type(EdgeType.MEASURES)
    print(f"✓ Found {len(measures_edges)} MEASURES edges")

    controls_edges = graph.get_edges_by_type(EdgeType.CONTROLS)
    print(f"✓ Found {len(controls_edges)} CONTROLS edges")

    # Print summary
    print("\n" + graph.summary())

    print("\n" + "=" * 60)
    print("✅ TEST PASSED: Basic graph construction successful")
    print("=" * 60)


def test_spatial_edge_creation():
    """Test that spatial edges are created based on proximity."""
    print("\n" + "=" * 60)
    print("TEST: Spatial Edge Creation")
    print("=" * 60)

    # Create two close nodes
    close_instruments = [
        MockInstrumentData(
            tag_number="TIT-101",
            tag_type="instrument",
            symbol_class="instrument.bubble",
            x=100.0,
            y=100.0,
            bbox=(90, 90, 110, 110),
            confidence=0.95,
            detection_confidence=0.95,
            association_confidence=0.90,
        ),
        MockInstrumentData(
            tag_number="TIT-102",
            tag_type="instrument",
            symbol_class="instrument.bubble",
            x=150.0,  # 50 pixels away (within threshold)
            y=100.0,
            bbox=(140, 90, 160, 110),
            confidence=0.93,
            detection_confidence=0.93,
            association_confidence=0.88,
        ),
    ]

    # Create one far node
    far_instrument = [
        MockInstrumentData(
            tag_number="TIT-201",
            tag_type="instrument",
            symbol_class="instrument.bubble",
            x=500.0,  # 400 pixels away (outside threshold)
            y=100.0,
            bbox=(490, 90, 510, 110),
            confidence=0.91,
            detection_confidence=0.91,
            association_confidence=0.85,
        ),
    ]

    perception_result = MockPipelineResult(
        instruments=close_instruments + far_instrument,
        equipment=[],
        lines=[],
        unidentified_symbols=[],
    )

    # Build graph with 200px threshold
    builder = GraphBuilder(proximity_threshold=200.0)
    graph = builder.build_from_perception(perception_result)

    print(f"\n✓ Graph created with {graph.node_count} nodes")
    print(f"✓ Graph has {graph.edge_count} edges")

    # Should have edge between close nodes, but not to far node
    assert graph.node_count == 3
    assert graph.edge_count == 1, f"Expected 1 edge (close pair), got {graph.edge_count}"

    # Check connected nodes
    tit101 = graph.get_node_by_tag("TIT-101")
    connected = graph.get_connected_nodes(tit101.id)
    print(f"✓ TIT-101 is connected to {len(connected)} nodes")
    assert len(connected) == 1, "TIT-101 should be connected to 1 node"
    assert connected[0][0].tag == "TIT-102", "Should be connected to TIT-102"

    print("\n✅ TEST PASSED: Spatial edges created correctly")
    print("=" * 60)


def test_edge_type_determination():
    """Test that edge types are determined correctly based on node types."""
    print("\n" + "=" * 60)
    print("TEST: Edge Type Determination")
    print("=" * 60)

    # Create instrument and valve (should create CONTROLS edge)
    instruments = [
        MockInstrumentData(
            tag_number="FIC-101",
            tag_type="instrument",
            symbol_class="instrument.bubble",
            x=100.0,
            y=100.0,
            bbox=(90, 90, 110, 110),
            confidence=0.95,
            detection_confidence=0.95,
            association_confidence=0.90,
        ),
    ]

    valves = [
        MockInstrumentData(
            tag_number="FV-101",
            tag_type="valve",
            symbol_class="valve.control",
            x=150.0,  # Close enough for edge
            y=100.0,
            bbox=(140, 90, 160, 110),
            confidence=0.92,
            detection_confidence=0.92,
            association_confidence=0.88,
        ),
    ]

    equipment = [
        MockInstrumentData(
            tag_number="P-101",
            tag_type="equipment",
            symbol_class="equipment.pump",
            x=100.0,
            y=200.0,  # Close to instrument
            bbox=(90, 190, 110, 210),
            confidence=0.90,
            detection_confidence=0.90,
            association_confidence=0.85,
        ),
    ]

    perception_result = MockPipelineResult(
        instruments=instruments,
        equipment=equipment,
        lines=[],
        unidentified_symbols=valves,
    )

    builder = GraphBuilder(proximity_threshold=150.0)
    graph = builder.build_from_perception(perception_result)

    # Check CONTROLS edge (instrument → valve)
    controls_edges = graph.get_edges_by_type(EdgeType.CONTROLS)
    print(f"✓ Found {len(controls_edges)} CONTROLS edges")
    assert len(controls_edges) >= 1, "Should have at least 1 CONTROLS edge"

    # Check MEASURES edge (instrument → equipment)
    measures_edges = graph.get_edges_by_type(EdgeType.MEASURES)
    print(f"✓ Found {len(measures_edges)} MEASURES edges")
    assert len(measures_edges) >= 1, "Should have at least 1 MEASURES edge"

    print("\n✅ TEST PASSED: Edge types determined correctly")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_basic_graph_construction()
        test_spatial_edge_creation()
        test_edge_type_determination()
        
        print("\n" + "🎉" * 30)
        print("ALL LAYER 3 BASIC TESTS PASSED!")
        print("🎉" * 30)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
