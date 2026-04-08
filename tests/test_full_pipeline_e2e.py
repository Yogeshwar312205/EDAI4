"""
EDAI4 - End-to-End Pipeline Test
Tests the complete Layer 1 → Layer 2 → Layer 3 pipeline on real P&ID images.

This script is designed to run in Kaggle environment where:
- YOLO model is at: /kaggle/working/runs/detect/edai4_layer1_v2/weights/best.pt
- Validation images: /kaggle/working/pid_dataset/images/val/
- All dependencies are installed

Usage in Kaggle:
    !python tests/test_full_pipeline_e2e.py

Usage locally (with all dependencies):
    python tests/test_full_pipeline_e2e.py --image path/to/pid.jpg
"""

import sys
import argparse
from pathlib import Path
import random
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import cv2
    import numpy as np
    from PIL import Image
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from ultralytics import YOLO
    import easyocr
except ImportError as e:
    print(f"⚠️ Missing dependency: {e}")
    print("This script requires: ultralytics, opencv-python, easyocr, matplotlib")
    print("Install with: pip install ultralytics opencv-python easyocr matplotlib")
    sys.exit(1)

from src.perception import (
    SymbolDetector,
    OCREngine,
    TextSymbolAssociator,
    PerceptionPipeline,
)
from src.topology import GraphBuilder, NodeType, EdgeType


def find_yolo_model():
    """Find the trained YOLO model."""
    # Kaggle paths
    kaggle_paths = [
        "/kaggle/working/runs/detect/edai4_layer1_v2/weights/best.pt",
        "/kaggle/working/runs/detect/train/weights/best.pt",
    ]
    
    # Local paths
    local_paths = [
        "models/best.pt",
        "runs/detect/edai4_layer1_v2/weights/best.pt",
    ]
    
    for path in kaggle_paths + local_paths:
        if Path(path).exists():
            return path
    
    return None


def find_validation_images():
    """Find validation images directory."""
    paths = [
        "/kaggle/working/pid_dataset/images/val/",
        "/kaggle/input/p-and-id-symbols-for-computer-vision/images/val/",
        "data/val/",
    ]
    
    for path in paths:
        p = Path(path)
        if p.exists() and p.is_dir():
            images = list(p.glob("*.jpg")) + list(p.glob("*.png"))
            if images:
                return p
    
    return None


def select_random_image(val_dir: Path) -> Optional[Path]:
    """Select a random image from validation directory."""
    images = list(val_dir.glob("*.jpg")) + list(val_dir.glob("*.png"))
    if not images:
        return None
    return random.choice(images)


def visualize_layer1_results(image, detections, save_path: Optional[str] = None):
    """Visualize Layer 1 YOLO detections."""
    fig, ax = plt.subplots(1, figsize=(16, 12))
    ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    ax.set_title("Layer 1: YOLO Symbol Detection", fontsize=16, fontweight='bold')
    
    # Draw bounding boxes
    for det in detections:
        x1, y1, x2, y2 = det.bbox
        w, h = x2 - x1, y2 - y1
        
        # Color by class
        color = 'red' if 'instrument' in det.class_name else 'blue' if 'valve' in det.class_name else 'green'
        
        rect = patches.Rectangle(
            (x1, y1), w, h,
            linewidth=2,
            edgecolor=color,
            facecolor='none'
        )
        ax.add_patch(rect)
        
        # Label
        label = f"{det.class_name}\n{det.confidence:.2f}"
        ax.text(
            x1, y1 - 5,
            label,
            fontsize=8,
            color='white',
            bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.7)
        )
    
    ax.axis('off')
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ Saved Layer 1 visualization: {save_path}")
    
    plt.show()
    plt.close()


def visualize_layer2_results(image, perception_result, save_path: Optional[str] = None):
    """Visualize Layer 2 text-symbol associations."""
    fig, ax = plt.subplots(1, figsize=(16, 12))
    ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    ax.set_title("Layer 2: OCR + Text-Symbol Association", fontsize=16, fontweight='bold')
    
    # Draw instruments with tags
    for inst in perception_result.instruments:
        x1, y1, x2, y2 = inst.bbox
        w, h = x2 - x1, y2 - y1
        
        # Green for tagged, yellow for untagged
        color = 'green' if inst.tag_number != "UNTAGGED" else 'yellow'
        
        rect = patches.Rectangle(
            (x1, y1), w, h,
            linewidth=2,
            edgecolor=color,
            facecolor='none'
        )
        ax.add_patch(rect)
        
        # Label with tag
        label = inst.tag_number if inst.tag_number != "UNTAGGED" else inst.symbol_class
        if inst.description:
            label += f"\n{inst.description[:20]}"
        
        ax.text(
            x1, y1 - 5,
            label,
            fontsize=9,
            color='white',
            fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.8)
        )
    
    # Draw equipment
    for equip in perception_result.equipment:
        x1, y1, x2, y2 = equip.bbox
        w, h = x2 - x1, y2 - y1
        
        rect = patches.Rectangle(
            (x1, y1), w, h,
            linewidth=2,
            edgecolor='blue',
            facecolor='none'
        )
        ax.add_patch(rect)
        
        label = equip.tag_number if equip.tag_number != "UNTAGGED" else equip.symbol_class
        ax.text(
            x1, y1 - 5,
            label,
            fontsize=9,
            color='white',
            fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='blue', alpha=0.8)
        )
    
    ax.axis('off')
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ Saved Layer 2 visualization: {save_path}")
    
    plt.show()
    plt.close()


def visualize_layer3_graph(graph, save_path: Optional[str] = None):
    """Visualize Layer 3 graph structure."""
    import networkx as nx
    
    fig, ax = plt.subplots(1, figsize=(16, 12))
    
    # Create layout based on actual positions
    pos = {node.id: (node.x, -node.y) for node in graph.nodes.values()}
    
    # Color nodes by type
    color_map = {
        NodeType.INSTRUMENT: '#FF6B6B',
        NodeType.VALVE: '#4ECDC4',
        NodeType.EQUIPMENT: '#45B7D1',
        NodeType.PUMP: '#96CEB4',
        NodeType.LINE: '#FFEAA7',
        NodeType.JUNCTION: '#DFE6E9',
        NodeType.UNKNOWN: '#B2BEC3',
    }
    
    node_colors = [color_map.get(graph.nodes[n].node_type, '#B2BEC3') for n in graph.graph.nodes()]
    
    # Edge colors by type
    edge_color_map = {
        EdgeType.CONTROLS: 'red',
        EdgeType.MEASURES: 'blue',
        EdgeType.FLOWS_TO: 'green',
        EdgeType.CONNECTED_TO: 'gray',
    }
    
    # Draw edges by type
    for edge_type in EdgeType:
        edges = [(e.source_id, e.target_id) for e in graph.get_edges_by_type(edge_type)]
        if edges:
            nx.draw_networkx_edges(
                graph.graph,
                pos,
                edgelist=edges,
                edge_color=edge_color_map.get(edge_type, 'gray'),
                width=2,
                alpha=0.6,
                arrows=True,
                arrowsize=15,
                ax=ax,
                label=edge_type.value
            )
    
    # Draw nodes
    nx.draw_networkx_nodes(
        graph.graph,
        pos,
        node_color=node_colors,
        node_size=300,
        alpha=0.9,
        ax=ax
    )
    
    # Draw labels (tags only)
    labels = {
        node.id: node.tag if node.tag else node.label[:10]
        for node in graph.nodes.values()
    }
    nx.draw_networkx_labels(
        graph.graph,
        pos,
        labels,
        font_size=7,
        font_weight='bold',
        ax=ax
    )
    
    ax.set_title("Layer 3: P&ID Topology Graph", fontsize=16, fontweight='bold')
    ax.legend(loc='upper right')
    ax.axis('off')
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ Saved Layer 3 visualization: {save_path}")
    
    plt.show()
    plt.close()


def print_statistics(perception_result, graph):
    """Print pipeline statistics."""
    print("\n" + "=" * 70)
    print("📊 PIPELINE STATISTICS")
    print("=" * 70)
    
    # Layer 2 stats
    print("\n🔍 Layer 2 (Perception):")
    print(f"  Instruments detected: {len(perception_result.instruments)}")
    print(f"  - Tagged: {sum(1 for i in perception_result.instruments if i.tag_number != 'UNTAGGED')}")
    print(f"  - Untagged: {sum(1 for i in perception_result.instruments if i.tag_number == 'UNTAGGED')}")
    print(f"  Equipment detected: {len(perception_result.equipment)}")
    print(f"  Lines detected: {len(perception_result.lines)}")
    print(f"  Unidentified symbols: {len(perception_result.unidentified_symbols)}")
    
    # Layer 3 stats
    print(f"\n🕸️ Layer 3 (Topology):")
    print(graph.summary())
    
    # Edge breakdown
    for edge_type in EdgeType:
        edges = graph.get_edges_by_type(edge_type)
        if edges:
            print(f"  - {edge_type.value}: {len(edges)}")
    
    print("\n" + "=" * 70)


def run_full_pipeline(image_path: Path, output_dir: Optional[Path] = None):
    """Run the complete Layer 1 → 2 → 3 pipeline."""
    print("=" * 70)
    print("🚀 EDAI4 - Full Pipeline Test")
    print("=" * 70)
    print(f"📁 Image: {image_path}")
    
    # Find YOLO model
    model_path = find_yolo_model()
    if not model_path:
        print("❌ Error: Could not find YOLO model (best.pt)")
        print("Expected locations:")
        print("  - /kaggle/working/runs/detect/edai4_layer1_v2/weights/best.pt")
        print("  - models/best.pt")
        return False
    
    print(f"✓ Found YOLO model: {model_path}")
    
    # Load image
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"❌ Error: Could not load image: {image_path}")
        return False
    
    print(f"✓ Loaded image: {image.shape[1]}x{image.shape[0]} pixels")
    
    # Create output directory
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # ========================================
    # LAYER 1: YOLO Symbol Detection
    # ========================================
    print("\n" + "-" * 70)
    print("⚙️ LAYER 1: YOLO Symbol Detection")
    print("-" * 70)
    
    detector = SymbolDetector(model_path=model_path)
    detections = detector.detect(image)
    
    print(f"✓ Detected {len(detections)} symbols")
    
    # Show class distribution
    class_counts = {}
    for det in detections:
        class_counts[det.class_name] = class_counts.get(det.class_name, 0) + 1
    
    print("  Class distribution:")
    for cls, count in sorted(class_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"    {cls}: {count}")
    
    # Visualize Layer 1
    if output_dir:
        visualize_layer1_results(
            image, 
            detections, 
            save_path=output_dir / "layer1_detections.png"
        )
    else:
        visualize_layer1_results(image, detections)
    
    # ========================================
    # LAYER 2: OCR + Text-Symbol Association
    # ========================================
    print("\n" + "-" * 70)
    print("⚙️ LAYER 2: OCR + Text-Symbol Association")
    print("-" * 70)
    
    pipeline = PerceptionPipeline(
        model_path=model_path,
        ocr_languages=['en'],
        association_radius=100
    )
    
    perception_result = pipeline.process_image(image)
    
    print(f"✓ Processed {len(perception_result.instruments)} instruments")
    print(f"✓ Processed {len(perception_result.equipment)} equipment")
    print(f"✓ Processed {len(perception_result.lines)} lines")
    
    # Show some tagged instruments
    tagged_instruments = [i for i in perception_result.instruments if i.tag_number != "UNTAGGED"]
    if tagged_instruments:
        print(f"\n  Sample tagged instruments:")
        for inst in tagged_instruments[:5]:
            print(f"    {inst.tag_number} ({inst.symbol_class}) - {inst.description or 'N/A'}")
    
    # Visualize Layer 2
    if output_dir:
        visualize_layer2_results(
            image, 
            perception_result, 
            save_path=output_dir / "layer2_associations.png"
        )
    else:
        visualize_layer2_results(image, perception_result)
    
    # ========================================
    # LAYER 3: Graph Construction
    # ========================================
    print("\n" + "-" * 70)
    print("⚙️ LAYER 3: Graph Construction")
    print("-" * 70)
    
    builder = GraphBuilder(proximity_threshold=200.0)
    graph = builder.build_from_perception(
        perception_result,
        pid_name=image_path.stem
    )
    
    print(f"✓ Built graph with {graph.node_count} nodes and {graph.edge_count} edges")
    
    # Visualize Layer 3
    if output_dir:
        visualize_layer3_graph(
            graph, 
            save_path=output_dir / "layer3_graph.png"
        )
    else:
        visualize_layer3_graph(graph)
    
    # ========================================
    # Statistics & Export
    # ========================================
    print_statistics(perception_result, graph)
    
    # Export results
    if output_dir:
        # Export perception result as JSON
        import json
        json_path = output_dir / "perception_result.json"
        with open(json_path, 'w') as f:
            json.dump(perception_result.to_dict(), f, indent=2)
        print(f"\n✓ Exported perception result: {json_path}")
        
        # Export graph as DataFrame
        df = graph.to_dataframe()
        csv_path = output_dir / "graph_nodes.csv"
        df.to_csv(csv_path, index=False)
        print(f"✓ Exported graph nodes: {csv_path}")
    
    print("\n" + "=" * 70)
    print("✅ FULL PIPELINE TEST COMPLETE")
    print("=" * 70)
    
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="EDAI4 Full Pipeline Test")
    parser.add_argument(
        '--image',
        type=str,
        help='Path to P&ID image (if not provided, will use random validation image)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='output/pipeline_test',
        help='Output directory for results (default: output/pipeline_test)'
    )
    
    args = parser.parse_args()
    
    # Find image
    if args.image:
        image_path = Path(args.image)
        if not image_path.exists():
            print(f"❌ Error: Image not found: {image_path}")
            return 1
    else:
        # Find validation directory
        val_dir = find_validation_images()
        if not val_dir:
            print("❌ Error: Could not find validation images")
            print("Expected locations:")
            print("  - /kaggle/working/pid_dataset/images/val/")
            print("  - /kaggle/input/p-and-id-symbols-for-computer-vision/images/val/")
            return 1
        
        # Select random image
        image_path = select_random_image(val_dir)
        if not image_path:
            print(f"❌ Error: No images found in {val_dir}")
            return 1
        
        print(f"🎲 Selected random validation image: {image_path.name}")
    
    # Run pipeline
    output_dir = Path(args.output) if args.output else None
    success = run_full_pipeline(image_path, output_dir)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
