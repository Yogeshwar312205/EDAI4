#!/usr/bin/env python3
"""
Visualize node positions on the P&ID image to debug coordinate issues.
This script reads the current graph and draws circles at each node position.
"""
import sys
import cv2
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def visualize_graph_on_image(image_path: str, graph, output_path: str = None):
    """
    Draw node positions on the P&ID image.
    
    Args:
        image_path: Path to the original P&ID image
        graph: PIDGraph object with nodes
        output_path: Where to save the visualization (optional)
    """
    # Read image
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not read image from {image_path}")
        return
    
    print(f"Image size: {img.shape[1]}x{img.shape[0]}")
    
    # Get all nodes
    nodes = list(graph.get_all_nodes())
    print(f"Total nodes: {len(nodes)}")
    
    if len(nodes) == 0:
        print("No nodes to visualize!")
        return
    
    # Calculate coordinate statistics
    x_coords = [n.x for n in nodes]
    y_coords = [n.y for n in nodes]
    
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)
    
    print("\nCoordinate Statistics:")
    print(f"X range: {min_x:.1f} to {max_x:.1f} (span: {max_x - min_x:.1f})")
    print(f"Y range: {min_y:.1f} to {max_y:.1f} (span: {max_y - min_y:.1f})")
    
    # Check if coordinates are within image bounds
    img_height, img_width = img.shape[:2]
    out_of_bounds = 0
    
    for node in nodes:
        if not (0 <= node.x < img_width and 0 <= node.y < img_height):
            out_of_bounds += 1
    
    if out_of_bounds > 0:
        print(f"\n⚠️  WARNING: {out_of_bounds} nodes are outside image bounds!")
        print(f"   Image size: {img_width}x{img_height}")
    
    # Draw nodes
    for i, node in enumerate(nodes):
        x, y = int(node.x), int(node.y)
        
        # Skip if out of bounds
        if not (0 <= x < img_width and 0 <= y < img_height):
            continue
        
        # Color based on node type
        if 'instrument' in node.node_type.value.lower():
            color = (255, 175, 97)  # Blue
        elif 'valve' in node.node_type.value.lower():
            color = (194, 182, 86)  # Cyan
        elif 'equipment' in node.node_type.value.lower():
            color = (121, 195, 152)  # Green
        else:
            color = (221, 120, 198)  # Purple
        
        # Draw circle at node position
        cv2.circle(img, (x, y), 15, color, -1)
        cv2.circle(img, (x, y), 17, (255, 255, 255), 2)
        
        # Draw tag/label
        label = node.tag or node.label or f"node_{i}"
        cv2.putText(img, label, (x + 20, y + 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        cv2.putText(img, label, (x + 20, y + 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    # Draw bounding box around all nodes
    if len(nodes) > 0:
        cv2.rectangle(img, (int(min_x), int(min_y)), (int(max_x), int(max_y)), 
                     (0, 255, 0), 3)
        
        # Add text showing coordinate range
        text = f"Nodes: {len(nodes)} | X: {min_x:.0f}-{max_x:.0f} | Y: {min_y:.0f}-{max_y:.0f}"
        cv2.putText(img, text, (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 3)
        cv2.putText(img, text, (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    
    # Save or display
    if output_path:
        cv2.imwrite(output_path, img)
        print(f"\n✓ Saved visualization to: {output_path}")
    else:
        output_path = "data/output/node_positions_debug.jpg"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(output_path, img)
        print(f"\n✓ Saved visualization to: {output_path}")
    
    return img


if __name__ == "__main__":
    print("="*70)
    print("Node Position Visualizer")
    print("="*70)
    
    # This script needs to be run after processing an image
    # It will use the current graph state
    
    print("\nTo use this script:")
    print("1. Process a P&ID image through the API")
    print("2. The graph will be stored in the application state")
    print("3. Run this script to visualize node positions")
    print("\nAlternatively, you can import this function and call it directly:")
    print("  from scripts.visualize_node_positions import visualize_graph_on_image")
    print("  visualize_graph_on_image('path/to/image.jpg', graph)")
    print("\n" + "="*70)
