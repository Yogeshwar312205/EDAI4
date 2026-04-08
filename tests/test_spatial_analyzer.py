"""
Unit tests for Spatial Analyzer (Phase 3.2).

Tests containment detection, alignment detection, clustering, and KNN.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataclasses import dataclass
from src.topology.graph_builder import GraphNode, NodeType
from src.topology.spatial_analyzer import (
    SpatialAnalyzer,
    SpatialRelationType,
    print_spatial_analysis_summary
)


def create_test_node(
    node_id: str,
    x: float,
    y: float,
    node_type: NodeType = NodeType.INSTRUMENT,
    width: float = 20.0,
    height: float = 20.0,
    tag: str = None
) -> GraphNode:
    """Helper to create test nodes."""
    return GraphNode(
        id=node_id,
        node_type=node_type,
        label=tag or node_id,
        tag=tag,
        x=x,
        y=y,
        width=width,
        height=height,
        confidence=0.9
    )


def test_containment_detection():
    """Test detection of instruments inside equipment."""
    print("=" * 70)
    print("TEST: Containment Detection")
    print("=" * 70)
    
    # Create a large equipment vessel
    vessel = create_test_node(
        "vessel1",
        x=300.0,
        y=300.0,
        node_type=NodeType.EQUIPMENT,
        width=200.0,
        height=150.0,
        tag="V-101"
    )
    
    # Create instruments
    # Inside the vessel
    inside_inst1 = create_test_node("inst1", x=300.0, y=300.0, tag="LIT-101")  # Center
    inside_inst2 = create_test_node("inst2", x=350.0, y=320.0, tag="TIT-101")  # Inside
    
    # Outside the vessel
    outside_inst = create_test_node("inst3", x=500.0, y=300.0, tag="PIT-201")  # Far away
    
    # On the edge (should not be contained)
    edge_inst = create_test_node("inst4", x=400.0, y=300.0, tag="FIT-301")  # Right edge
    
    nodes = [vessel, inside_inst1, inside_inst2, outside_inst, edge_inst]
    
    # Run analysis
    analyzer = SpatialAnalyzer(containment_threshold=0.5)
    containment = analyzer.detect_containment(nodes)
    
    # Verify
    print(f"\n✓ Detected {len(containment)} container nodes")
    assert vessel in containment, "Vessel should be a container"
    
    contained = containment[vessel]
    print(f"✓ Vessel contains {len(contained)} instruments")
    
    # Check correct containment
    contained_ids = {n.id for n in contained}
    assert "inst1" in contained_ids, "inst1 should be inside"
    assert "inst2" in contained_ids, "inst2 should be inside"
    assert "inst3" not in contained_ids, "inst3 should NOT be inside (too far)"
    
    print(f"  Contained instruments: {[n.tag for n in contained]}")
    
    print("\n✅ TEST PASSED: Containment detection works correctly")
    print("=" * 70)


def test_horizontal_alignment():
    """Test detection of horizontally aligned nodes."""
    print("\n" + "=" * 70)
    print("TEST: Horizontal Alignment Detection")
    print("=" * 70)
    
    # Create nodes on same horizontal line (y=100)
    aligned_nodes = [
        create_test_node("h1", x=100.0, y=100.0, tag="FIT-101"),
        create_test_node("h2", x=200.0, y=102.0, tag="PIT-101"),  # Slightly off (within tolerance)
        create_test_node("h3", x=300.0, y=99.0, tag="TIT-101"),   # Slightly off (within tolerance)
    ]
    
    # Create node NOT aligned
    unaligned = create_test_node("h4", x=150.0, y=200.0, tag="LIT-201")
    
    nodes = aligned_nodes + [unaligned]
    
    # Run analysis
    analyzer = SpatialAnalyzer(alignment_tolerance=5.0)
    alignment_groups = analyzer.detect_alignment(nodes, min_group_size=2)
    
    # Verify
    print(f"\n✓ Detected {len(alignment_groups)} alignment groups")
    assert len(alignment_groups) >= 1, "Should detect at least 1 horizontal group"
    
    # Find horizontal group
    h_groups = [g for g in alignment_groups if g.orientation == "horizontal"]
    assert len(h_groups) >= 1, "Should have horizontal alignment group"
    
    h_group = h_groups[0]
    print(f"✓ Horizontal group has {h_group.node_count} nodes")
    print(f"  Axis value: {h_group.axis_value:.1f}")
    print(f"  Tags: {h_group.tags}")
    
    assert h_group.node_count == 3, "Should have 3 aligned nodes"
    assert "FIT-101" in h_group.tags
    assert "PIT-101" in h_group.tags
    assert "TIT-101" in h_group.tags
    assert "LIT-201" not in h_group.tags, "Unaligned node should NOT be in group"
    
    print("\n✅ TEST PASSED: Horizontal alignment detection works")
    print("=" * 70)


def test_vertical_alignment():
    """Test detection of vertically aligned nodes."""
    print("\n" + "=" * 70)
    print("TEST: Vertical Alignment Detection")
    print("=" * 70)
    
    # Create nodes on same vertical line (x=150)
    aligned_nodes = [
        create_test_node("v1", x=150.0, y=100.0, tag="PCV-101"),
        create_test_node("v2", x=152.0, y=200.0, tag="PCV-102"),  # Slightly off
        create_test_node("v3", x=148.0, y=300.0, tag="PCV-103"),  # Slightly off
    ]
    
    nodes = aligned_nodes
    
    # Run analysis
    analyzer = SpatialAnalyzer(alignment_tolerance=5.0)
    alignment_groups = analyzer.detect_alignment(nodes, min_group_size=2)
    
    # Verify
    v_groups = [g for g in alignment_groups if g.orientation == "vertical"]
    print(f"\n✓ Detected {len(v_groups)} vertical alignment groups")
    assert len(v_groups) >= 1, "Should detect vertical group"
    
    v_group = v_groups[0]
    print(f"✓ Vertical group has {v_group.node_count} nodes")
    print(f"  Axis value: {v_group.axis_value:.1f}")
    print(f"  Tags: {v_group.tags}")
    
    assert v_group.node_count == 3, "Should have 3 aligned nodes"
    
    print("\n✅ TEST PASSED: Vertical alignment detection works")
    print("=" * 70)


def test_spatial_clustering():
    """Test spatial clustering of nodes."""
    print("\n" + "=" * 70)
    print("TEST: Spatial Clustering")
    print("=" * 70)
    
    try:
        import scipy
        SCIPY_OK = True
    except ImportError:
        SCIPY_OK = False
        print("⚠️ Scipy not available - skipping clustering test")
        return
    
    # Create two distinct clusters
    # Cluster 1: around (100, 100)
    cluster1 = [
        create_test_node("c1_1", x=100.0, y=100.0, tag="FIT-101"),
        create_test_node("c1_2", x=110.0, y=105.0, tag="PIT-101"),
        create_test_node("c1_3", x=95.0, y=110.0, tag="TIT-101"),
        create_test_node("c1_4", x=105.0, y=95.0, tag="LIT-101"),
    ]
    
    # Cluster 2: around (400, 400)
    cluster2 = [
        create_test_node("c2_1", x=400.0, y=400.0, tag="FIT-201"),
        create_test_node("c2_2", x=410.0, y=405.0, tag="PIT-201"),
        create_test_node("c2_3", x=395.0, y=410.0, tag="TIT-201"),
        create_test_node("c2_4", x=405.0, y=395.0, tag="LIT-201"),
    ]
    
    nodes = cluster1 + cluster2
    
    # Run analysis
    analyzer = SpatialAnalyzer(cluster_distance=100.0)
    clusters = analyzer.detect_clusters(nodes, min_cluster_size=3)
    
    # Verify
    print(f"\n✓ Detected {len(clusters)} spatial clusters")
    assert len(clusters) == 2, f"Should detect 2 clusters, got {len(clusters)}"
    
    for i, cluster in enumerate(clusters):
        print(f"\n  Cluster {cluster.cluster_id}:")
        print(f"    Nodes: {cluster.node_count}")
        print(f"    Centroid: ({cluster.centroid[0]:.1f}, {cluster.centroid[1]:.1f})")
        print(f"    Radius: {cluster.radius:.1f}px")
        print(f"    Tags: {[n.tag for n in cluster.nodes]}")
        
        assert cluster.node_count == 4, f"Each cluster should have 4 nodes"
    
    print("\n✅ TEST PASSED: Spatial clustering works")
    print("=" * 70)


def test_nearest_neighbors():
    """Test K-nearest neighbors search."""
    print("\n" + "=" * 70)
    print("TEST: K-Nearest Neighbors")
    print("=" * 70)
    
    # Create target node
    target = create_test_node("target", x=200.0, y=200.0, tag="FIT-101")
    
    # Create other nodes at various distances
    neighbors = [
        create_test_node("n1", x=210.0, y=200.0, tag="PIT-101"),  # 10px away
        create_test_node("n2", x=200.0, y=230.0, tag="TIT-101"),  # 30px away
        create_test_node("n3", x=250.0, y=200.0, tag="LIT-101"),  # 50px away
        create_test_node("n4", x=300.0, y=200.0, tag="FIT-201"),  # 100px away
        create_test_node("n5", x=400.0, y=400.0, tag="PIT-201"),  # ~283px away
    ]
    
    all_nodes = [target] + neighbors
    
    # Run analysis
    analyzer = SpatialAnalyzer()
    knn = analyzer.find_nearest_neighbors(target, all_nodes, k=3)
    
    # Verify
    print(f"\n✓ Found {len(knn)} nearest neighbors")
    assert len(knn) == 3, "Should return 3 neighbors"
    
    for i, (node, dist) in enumerate(knn):
        print(f"  {i+1}. {node.tag}: {dist:.1f}px away")
    
    # Check order (should be sorted by distance)
    assert knn[0][0].tag == "PIT-101", "Closest should be PIT-101 (10px)"
    assert knn[1][0].tag == "TIT-101", "Second should be TIT-101 (30px)"
    assert knn[2][0].tag == "LIT-101", "Third should be LIT-101 (50px)"
    
    # Check distances
    assert knn[0][1] < knn[1][1] < knn[2][1], "Distances should be ascending"
    
    print("\n✅ TEST PASSED: K-nearest neighbors works correctly")
    print("=" * 70)


def test_full_spatial_analysis():
    """Test complete spatial analysis pipeline."""
    print("\n" + "=" * 70)
    print("TEST: Full Spatial Analysis Pipeline")
    print("=" * 70)
    
    # Create a realistic P&ID scenario
    # Equipment vessel
    vessel = create_test_node(
        "V-101",
        x=300.0,
        y=300.0,
        node_type=NodeType.EQUIPMENT,
        width=200.0,
        height=150.0,
        tag="V-101"
    )
    
    # Instruments inside vessel
    inside_instruments = [
        create_test_node("LIT-101", x=280.0, y=300.0, tag="LIT-101"),
        create_test_node("TIT-101", x=320.0, y=300.0, tag="TIT-101"),
    ]
    
    # Instruments aligned horizontally (y=200)
    h_aligned = [
        create_test_node("FIT-201", x=100.0, y=200.0, tag="FIT-201"),
        create_test_node("PIT-201", x=200.0, y=201.0, tag="PIT-201"),
        create_test_node("TIT-201", x=300.0, y=199.0, tag="TIT-201"),
    ]
    
    # Pump and related instruments (cluster)
    pump_cluster = [
        create_test_node("P-101", x=500.0, y=500.0, node_type=NodeType.PUMP, tag="P-101"),
        create_test_node("FIT-301", x=510.0, y=510.0, tag="FIT-301"),
        create_test_node("PIT-301", x=490.0, y=505.0, tag="PIT-301"),
    ]
    
    all_nodes = [vessel] + inside_instruments + h_aligned + pump_cluster
    
    # Run full analysis
    analyzer = SpatialAnalyzer(
        containment_threshold=0.5,
        alignment_tolerance=5.0,
        cluster_distance=50.0
    )
    
    results = analyzer.analyze_all(all_nodes)
    
    # Verify results
    print(f"\n✓ Analysis complete")
    print(f"  Containments: {len(results['containment'])}")
    print(f"  Alignment groups: {len(results['alignment'])}")
    print(f"  Clusters: {len(results['clusters'])}")
    print(f"  Relationships: {len(results['relationships'])}")
    
    # Check containment
    assert len(results['containment']) >= 1, "Should detect vessel containment"
    
    # Check alignment
    assert len(results['alignment']) >= 1, "Should detect horizontal alignment"
    
    # Check relationships
    assert len(results['relationships']) > 0, "Should create spatial relationships"
    
    # Print summary
    print("\n" + print_spatial_analysis_summary(results))
    
    print("\n✅ TEST PASSED: Full spatial analysis pipeline works")
    print("=" * 70)


if __name__ == "__main__":
    try:
        test_containment_detection()
        test_horizontal_alignment()
        test_vertical_alignment()
        test_spatial_clustering()
        test_nearest_neighbors()
        test_full_spatial_analysis()
        
        print("\n" + "🎉" * 30)
        print("ALL SPATIAL ANALYZER TESTS PASSED!")
        print("🎉" * 30)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
