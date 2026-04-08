"""
EDAI4 - Kaggle Full Pipeline Test with Spatial Analysis
Copy-paste this into a Kaggle notebook cell to test the complete pipeline.

Tests: Layer 1 (YOLO) → Layer 2 (OCR + Association) → Layer 3 (Graph + Spatial Analysis)
"""

# ============================================================================
# SETUP: Import and Path Configuration
# ============================================================================

import sys
from pathlib import Path
import random
import cv2
import numpy as np
from IPython.display import Image as IPImage, display
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Add EDAI4 code to path (adjust if needed)
sys.path.insert(0, '/kaggle/working')

from src.perception import PerceptionPipeline
from src.topology import GraphBuilder, SpatialAnalyzer, print_spatial_analysis_summary, NodeType, EdgeType

# ============================================================================
# CONFIGURATION
# ============================================================================

YOLO_MODEL_PATH = "/kaggle/working/runs/detect/edai4_layer1_v2/weights/best.pt"
VAL_IMAGES_DIR = "/kaggle/working/pid_dataset/images/val/"

# Select random validation image
val_dir = Path(VAL_IMAGES_DIR)
all_images = list(val_dir.glob("*.jpg")) + list(val_dir.glob("*.png"))
test_image_path = random.choice(all_images)

print(f"🎲 Selected test image: {test_image_path.name}")
print(f"📁 Model: {YOLO_MODEL_PATH}")

# ============================================================================
# LAYER 1: YOLO SYMBOL DETECTION
# ============================================================================

print("\n" + "=" * 70)
print("⚙️ LAYER 1: YOLO Symbol Detection")
print("=" * 70)

# Load image
image = cv2.imread(str(test_image_path))
print(f"✓ Image loaded: {image.shape[1]}x{image.shape[0]} pixels")

# Run YOLO detection
from src.perception import SymbolDetector
detector = SymbolDetector(model_path=YOLO_MODEL_PATH)
detections = detector.detect(image)

print(f"✓ Detected {len(detections)} symbols")

# Class distribution
class_counts = {}
for det in detections:
    class_counts[det.class_name] = class_counts.get(det.class_name, 0) + 1

print("\n📊 Class Distribution:")
for cls, count in sorted(class_counts.items(), key=lambda x: -x[1])[:10]:
    print(f"  {cls}: {count}")

# Visualize Layer 1
fig, ax = plt.subplots(1, figsize=(20, 15))
ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
ax.set_title("Layer 1: YOLO Symbol Detection", fontsize=18, fontweight='bold')

for det in detections:
    x1, y1, x2, y2 = det.bbox
    w, h = x2 - x1, y2 - y1
    color = 'red' if 'instrument' in det.class_name else 'blue' if 'valve' in det.class_name else 'green'
    rect = patches.Rectangle((x1, y1), w, h, linewidth=2, edgecolor=color, facecolor='none')
    ax.add_patch(rect)
    ax.text(x1, y1-5, f"{det.class_name}\n{det.confidence:.2f}", 
            fontsize=7, color='white', bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.7))

ax.axis('off')
plt.tight_layout()
plt.savefig('/kaggle/working/layer1_detections.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================================
# LAYER 2: OCR + TEXT-SYMBOL ASSOCIATION
# ============================================================================

print("\n" + "=" * 70)
print("⚙️ LAYER 2: OCR + Text-Symbol Association")
print("=" * 70)

# Initialize perception pipeline
pipeline = PerceptionPipeline(
    model_path=YOLO_MODEL_PATH,
    ocr_languages=['en'],
    association_radius=100
)

# Process image
perception_result = pipeline.process_image(image)

print(f"✓ Instruments: {len(perception_result.instruments)}")
print(f"✓ Equipment: {len(perception_result.equipment)}")
print(f"✓ Lines: {len(perception_result.lines)}")
print(f"✓ Unidentified: {len(perception_result.unidentified_symbols)}")

# Show tagged instruments
tagged_instruments = [i for i in perception_result.instruments if i.tag_number != "UNTAGGED"]
print(f"\n📋 Tagged Instruments ({len(tagged_instruments)}):")
for inst in tagged_instruments[:10]:
    desc = inst.description[:30] if inst.description else "N/A"
    print(f"  {inst.tag_number:15s} ({inst.symbol_class:25s}) - {desc}")

# Visualize Layer 2
fig, ax = plt.subplots(1, figsize=(20, 15))
ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
ax.set_title("Layer 2: OCR + Text-Symbol Association", fontsize=18, fontweight='bold')

# Draw instruments
for inst in perception_result.instruments:
    x1, y1, x2, y2 = inst.bbox
    w, h = x2 - x1, y2 - y1
    color = 'green' if inst.tag_number != "UNTAGGED" else 'yellow'
    rect = patches.Rectangle((x1, y1), w, h, linewidth=2.5, edgecolor=color, facecolor='none')
    ax.add_patch(rect)
    label = inst.tag_number if inst.tag_number != "UNTAGGED" else inst.symbol_class
    ax.text(x1, y1-5, label, fontsize=9, color='white', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.4', facecolor=color, alpha=0.9))

# Draw equipment
for equip in perception_result.equipment:
    x1, y1, x2, y2 = equip.bbox
    w, h = x2 - x1, y2 - y1
    rect = patches.Rectangle((x1, y1), w, h, linewidth=2.5, edgecolor='blue', facecolor='none')
    ax.add_patch(rect)
    label = equip.tag_number if equip.tag_number != "UNTAGGED" else equip.symbol_class
    ax.text(x1, y1-5, label, fontsize=9, color='white', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='blue', alpha=0.9))

ax.axis('off')
plt.tight_layout()
plt.savefig('/kaggle/working/layer2_associations.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================================
# LAYER 3.1: GRAPH CONSTRUCTION
# ============================================================================

print("\n" + "=" * 70)
print("⚙️ LAYER 3.1: Topology Graph Construction")
print("=" * 70)

# Build graph
builder = GraphBuilder(proximity_threshold=200.0)
graph = builder.build_from_perception(perception_result, pid_name=test_image_path.stem)

print(f"✓ Graph built: {graph.node_count} nodes, {graph.edge_count} edges")
print("\n" + graph.summary())

# Edge type breakdown
print("\n📊 Edge Type Distribution:")
for edge_type in EdgeType:
    edges = graph.get_edges_by_type(edge_type)
    if edges:
        print(f"  {edge_type.value:15s}: {len(edges)}")

# Visualize Layer 3.1
import networkx as nx

fig, ax = plt.subplots(1, figsize=(20, 15))

# Node positions from actual coordinates
pos = {node.id: (node.x, -node.y) for node in graph.nodes.values()}

# Node colors by type
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
            graph.graph, pos, edgelist=edges,
            edge_color=edge_color_map.get(edge_type, 'gray'),
            width=2, alpha=0.6, arrows=True, arrowsize=15, ax=ax,
            label=edge_type.value
        )

# Draw nodes
nx.draw_networkx_nodes(graph.graph, pos, node_color=node_colors, node_size=400, alpha=0.9, ax=ax)

# Draw labels
labels = {node.id: node.tag if node.tag else node.label[:10] for node in graph.nodes.values()}
nx.draw_networkx_labels(graph.graph, pos, labels, font_size=8, font_weight='bold', ax=ax)

ax.set_title("Layer 3.1: P&ID Topology Graph", fontsize=18, fontweight='bold')
ax.legend(loc='upper right', fontsize=12)
ax.axis('off')
plt.tight_layout()
plt.savefig('/kaggle/working/layer3_graph.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================================
# LAYER 3.2: SPATIAL RELATIONSHIP ANALYSIS ⭐ NEW!
# ============================================================================

print("\n" + "=" * 70)
print("⚙️ LAYER 3.2: Spatial Relationship Analysis")
print("=" * 70)

# Initialize spatial analyzer
spatial_analyzer = SpatialAnalyzer(
    containment_threshold=0.5,
    alignment_tolerance=10.0,
    cluster_distance=150.0
)

# Run spatial analysis
nodes_list = list(graph.nodes.values())
spatial_results = spatial_analyzer.analyze_all(nodes_list)

# Print summary
print("\n" + print_spatial_analysis_summary(spatial_results))

# ============================================================================
# VISUALIZE SPATIAL RELATIONSHIPS
# ============================================================================

print("\n" + "=" * 70)
print("📊 VISUALIZING SPATIAL RELATIONSHIPS")
print("=" * 70)

fig, axes = plt.subplots(2, 2, figsize=(24, 18))
fig.suptitle("Layer 3.2: Spatial Relationship Analysis", fontsize=20, fontweight='bold')

# -------- SUBPLOT 1: Containment --------
ax = axes[0, 0]
ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
ax.set_title("Containment Relationships", fontsize=14, fontweight='bold')

containment = spatial_results.get("containment", {})
for container, contained_list in containment.items():
    # Draw container in blue
    x1 = container.x - container.width/2
    y1 = container.y - container.height/2
    rect = patches.Rectangle(
        (x1, y1), container.width, container.height,
        linewidth=3, edgecolor='blue', facecolor='none'
    )
    ax.add_patch(rect)
    ax.text(x1, y1-10, f"Container: {container.tag or container.label}", 
            fontsize=10, color='white', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='blue', alpha=0.9))
    
    # Draw contained instruments in red
    for inst in contained_list:
        x1_i = inst.x - inst.width/2
        y1_i = inst.y - inst.height/2
        rect_i = patches.Rectangle(
            (x1_i, y1_i), inst.width, inst.height,
            linewidth=2, edgecolor='red', facecolor='none'
        )
        ax.add_patch(rect_i)
        ax.text(x1_i, y1_i-5, inst.tag or inst.label, 
                fontsize=8, color='white',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.8))

ax.axis('off')

# -------- SUBPLOT 2: Alignment --------
ax = axes[0, 1]
ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
ax.set_title("Alignment Groups (H: Red, V: Blue)", fontsize=14, fontweight='bold')

alignment_groups = spatial_results.get("alignment", [])
for group in alignment_groups:
    color = 'red' if group.orientation == 'horizontal' else 'blue'
    
    # Draw alignment line
    if group.orientation == 'horizontal':
        x_min = min(n.x for n in group.nodes) - 50
        x_max = max(n.x for n in group.nodes) + 50
        ax.plot([x_min, x_max], [group.axis_value, group.axis_value], 
                color=color, linewidth=3, alpha=0.7, linestyle='--')
    else:
        y_min = min(n.y for n in group.nodes) - 50
        y_max = max(n.y for n in group.nodes) + 50
        ax.plot([group.axis_value, group.axis_value], [y_min, y_max],
                color=color, linewidth=3, alpha=0.7, linestyle='--')
    
    # Draw nodes
    for node in group.nodes:
        circle = patches.Circle((node.x, node.y), radius=15, 
                                edgecolor=color, facecolor='none', linewidth=2)
        ax.add_patch(circle)
        ax.text(node.x, node.y-20, node.tag or node.label[:10], 
                fontsize=8, color='white', ha='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.8))

ax.axis('off')

# -------- SUBPLOT 3: Clusters --------
ax = axes[1, 0]
ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
ax.set_title("Spatial Clusters", fontsize=14, fontweight='bold')

clusters = spatial_results.get("clusters", [])
cluster_colors = plt.cm.Set3(np.linspace(0, 1, len(clusters)))

for cluster, color in zip(clusters, cluster_colors):
    # Draw cluster circle
    circle = patches.Circle(
        cluster.centroid, cluster.radius,
        edgecolor=color, facecolor=color, alpha=0.2, linewidth=3
    )
    ax.add_patch(circle)
    
    # Draw centroid
    ax.plot(cluster.centroid[0], cluster.centroid[1], 'o', 
            color=color, markersize=15, markeredgecolor='black', markeredgewidth=2)
    
    # Draw cluster nodes
    for node in cluster.nodes:
        circle_node = patches.Circle((node.x, node.y), radius=10,
                                    edgecolor=color, facecolor='none', linewidth=2)
        ax.add_patch(circle_node)
        ax.text(node.x, node.y-15, node.tag or node.label[:10],
                fontsize=7, color='white', ha='center',
                bbox=dict(boxstyle='round,pad=0.2', facecolor=color, alpha=0.9))
    
    # Label cluster
    ax.text(cluster.centroid[0], cluster.centroid[1] + cluster.radius + 20,
            f"Cluster {cluster.cluster_id}\n{cluster.node_count} nodes",
            fontsize=10, color='white', ha='center', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor=color, alpha=0.9))

ax.axis('off')

# -------- SUBPLOT 4: Summary Statistics --------
ax = axes[1, 1]
ax.axis('off')

# Create text summary
summary_text = f"""
SPATIAL ANALYSIS RESULTS

Total Nodes Analyzed: {len(nodes_list)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 CONTAINMENT
   Containers: {len(containment)}
   Total Contained: {sum(len(v) for v in containment.values())}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📏 ALIGNMENT
   Total Groups: {len(alignment_groups)}
   Horizontal: {len([g for g in alignment_groups if g.orientation == 'horizontal'])}
   Vertical: {len([g for g in alignment_groups if g.orientation == 'vertical'])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌐 CLUSTERS
   Total Clusters: {len(clusters)}
   Total Clustered Nodes: {sum(c.node_count for c in clusters)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 RELATIONSHIPS
   Total: {len(spatial_results.get('relationships', []))}
"""

# Add containment details
if containment:
    summary_text += "\n📋 CONTAINMENT DETAILS:\n"
    for i, (container, contained) in enumerate(list(containment.items())[:3]):
        tags = [n.tag or n.label for n in contained]
        summary_text += f"   • {container.tag or container.label} contains:\n"
        summary_text += f"     {', '.join(tags[:5])}\n"
        if len(contained) > 5:
            summary_text += f"     ... and {len(contained)-5} more\n"

# Add alignment details
if alignment_groups:
    summary_text += "\n📋 ALIGNMENT DETAILS:\n"
    for group in alignment_groups[:3]:
        tags = [n.tag or n.label[:10] for n in group.nodes]
        summary_text += f"   • {group.orientation} @ {group.axis_value:.1f}px:\n"
        summary_text += f"     {', '.join(tags[:5])}\n"

# Add cluster details
if clusters:
    summary_text += "\n📋 CLUSTER DETAILS:\n"
    for cluster in clusters[:3]:
        types = cluster.node_types
        type_str = ', '.join(f"{k.value}:{v}" for k, v in types.items())
        summary_text += f"   • Cluster {cluster.cluster_id}: {cluster.node_count} nodes\n"
        summary_text += f"     Types: {type_str}\n"

ax.text(0.05, 0.95, summary_text, transform=ax.transAxes,
        fontsize=11, verticalalignment='top', fontfamily='monospace',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()
plt.savefig('/kaggle/working/layer3_spatial_analysis.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================================
# EXPORT RESULTS
# ============================================================================

print("\n" + "=" * 70)
print("💾 Exporting Results")
print("=" * 70)

# Export perception result as JSON
import json
with open('/kaggle/working/perception_result.json', 'w') as f:
    json.dump(perception_result.to_dict(), f, indent=2)
print("✓ Saved: perception_result.json")

# Export graph as CSV
df = graph.to_dataframe()
df.to_csv('/kaggle/working/graph_nodes.csv', index=False)
print("✓ Saved: graph_nodes.csv")

# Export spatial relationships as JSON
spatial_export = {
    "containment": {
        (container.tag or container.id): [n.tag or n.id for n in contained]
        for container, contained in containment.items()
    },
    "alignment_groups": [
        {
            "orientation": g.orientation,
            "axis_value": g.axis_value,
            "node_count": g.node_count,
            "tags": g.tags
        }
        for g in alignment_groups
    ],
    "clusters": [
        {
            "cluster_id": c.cluster_id,
            "node_count": c.node_count,
            "centroid": c.centroid,
            "radius": c.radius,
            "node_types": {k.value: v for k, v in c.node_types.items()}
        }
        for c in clusters
    ],
    "relationships": [
        rel.to_dict() for rel in spatial_results.get("relationships", [])
    ]
}

with open('/kaggle/working/spatial_relationships.json', 'w') as f:
    json.dump(spatial_export, f, indent=2)
print("✓ Saved: spatial_relationships.json")

# Show sample data
print("\n📊 Sample Graph Nodes (first 10):")
print(df[['tag', 'type', 'tag_type', 'symbol_class', 'confidence', 'description']].head(10))

print("\n" + "=" * 70)
print("✅ FULL PIPELINE TEST COMPLETE (WITH SPATIAL ANALYSIS)!")
print("=" * 70)
print("\n📁 Output Files:")
print("  - /kaggle/working/layer1_detections.png")
print("  - /kaggle/working/layer2_associations.png")
print("  - /kaggle/working/layer3_graph.png")
print("  - /kaggle/working/layer3_spatial_analysis.png  ⭐ NEW!")
print("  - /kaggle/working/perception_result.json")
print("  - /kaggle/working/graph_nodes.csv")
print("  - /kaggle/working/spatial_relationships.json  ⭐ NEW!")

