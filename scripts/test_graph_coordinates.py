#!/usr/bin/env python3
"""
Test script to verify graph coordinate generation
"""
import sys
import json
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Now import with correct path
from topology.graph_builder import PIDGraph, GraphNode, NodeType

def create_test_graph():
    """Create a test graph with known coordinates"""
    graph = PIDGraph()
    
    # Add nodes with specific coordinates spread across the image
    test_nodes = [
        ("node_1", 100, 100, "instrument"),
        ("node_2", 500, 100, "valve"),
        ("node_3", 900, 100, "equipment"),
        ("node_4", 100, 500, "instrument"),
        ("node_5", 500, 500, "valve"),
        ("node_6", 900, 500, "equipment"),
        ("node_7", 100, 900, "instrument"),
        ("node_8", 500, 900, "valve"),
        ("node_9", 900, 900, "equipment"),
    ]
    
    for node_id, x, y, node_type in test_nodes:
        node = GraphNode(
            id=node_id,
            node_type=NodeType.INSTRUMENT if node_type == "instrument" 
                     else NodeType.VALVE if node_type == "valve"
                     else NodeType.EQUIPMENT,
            label=node_id,
            tag=node_id.upper(),
            x=float(x),
            y=float(y),
            width=50.0,
            height=50.0
        )
        graph.add_node(node)
    
    return graph

def export_graph_json(graph):
    """Export graph in the same format as the API"""
    nodes = []
    for node in graph.get_all_nodes():
        nodes.append({
            "id": node.id,
            "type": node.node_type.value,
            "tag": node.tag,
            "label": node.label,
            "x": node.x,
            "y": node.y,
        })
    
    edges = []
    for edge in graph.get_all_edges():
        edges.append({
            "source": edge.source_id,
            "target": edge.target_id,
            "type": edge.edge_type.value,
        })
    
    return {"nodes": nodes, "edges": edges}

if __name__ == "__main__":
    print("Creating test graph with known coordinates...")
    graph = create_test_graph()
    
    print(f"\nCreated {len(graph.get_all_nodes())} nodes")
    print("\nNode coordinates:")
    for node in graph.get_all_nodes():
        print(f"  {node.id}: ({node.x}, {node.y})")
    
    # Export to JSON
    graph_data = export_graph_json(graph)
    
    print("\n" + "="*60)
    print("JSON Output (copy to test in frontend):")
    print("="*60)
    print(json.dumps(graph_data, indent=2))
    
    # Calculate bounds
    x_coords = [n["x"] for n in graph_data["nodes"]]
    y_coords = [n["y"] for n in graph_data["nodes"]]
    
    print("\n" + "="*60)
    print("Coordinate Statistics:")
    print("="*60)
    print(f"X range: {min(x_coords)} to {max(x_coords)} (range: {max(x_coords) - min(x_coords)})")
    print(f"Y range: {min(y_coords)} to {max(y_coords)} (range: {max(y_coords) - min(y_coords)})")
    
    # Save to file
    output_file = Path(__file__).parent.parent / "data" / "test_graph.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(graph_data, f, indent=2)
    
    print(f"\nSaved to: {output_file}")
