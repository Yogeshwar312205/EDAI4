"""
EDAI4 - Spatial Relationship Analyzer
Advanced spatial analysis for P&ID topology detection.

Phase 3.2: Detects containment, alignment, intersections, and clusters.
"""

from dataclasses import dataclass, field
from typing import Optional, Union
from enum import Enum
import math
from collections import defaultdict

import numpy as np
try:
    from scipy.spatial import KDTree
    from scipy.cluster.hierarchy import fclusterdata
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    
try:
    from shapely.geometry import box, Point, LineString, Polygon
    from shapely.ops import unary_union
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False

from src.utils import get_logger
from src.topology.graph_builder import GraphNode, NodeType

logger = get_logger(__name__)


class SpatialRelationType(Enum):
    """Types of spatial relationships between nodes."""
    CONTAINS = "contains"                  # Equipment contains instrument
    CONTAINED_IN = "contained_in"          # Instrument inside equipment
    ALIGNED_HORIZONTAL = "aligned_h"       # Same horizontal line
    ALIGNED_VERTICAL = "aligned_v"         # Same vertical line
    INTERSECTS_LINE = "intersects_line"    # Symbol intersects flow line
    CLUSTERED = "clustered"                # Spatially clustered nodes
    ADJACENT = "adjacent"                  # Next to each other


@dataclass
class SpatialRelationship:
    """A detected spatial relationship between nodes."""
    node1_id: str
    node2_id: str
    relation_type: SpatialRelationType
    confidence: float
    distance: float = 0.0
    attributes: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "node1_id": self.node1_id,
            "node2_id": self.node2_id,
            "relation_type": self.relation_type.value,
            "confidence": self.confidence,
            "distance": self.distance,
            **self.attributes
        }


@dataclass
class AlignmentGroup:
    """A group of nodes aligned horizontally or vertically."""
    orientation: str  # "horizontal" or "vertical"
    nodes: list[GraphNode]
    axis_value: float  # y-coordinate for horizontal, x for vertical
    tolerance: float
    
    @property
    def node_count(self) -> int:
        return len(self.nodes)
    
    @property
    def tags(self) -> list[str]:
        return [n.tag for n in self.nodes if n.tag]


@dataclass
class SpatialCluster:
    """A cluster of spatially grouped nodes."""
    cluster_id: int
    nodes: list[GraphNode]
    centroid: tuple[float, float]
    radius: float
    
    @property
    def node_count(self) -> int:
        return len(self.nodes)
    
    @property
    def node_types(self) -> dict:
        """Count nodes by type."""
        counts = defaultdict(int)
        for node in self.nodes:
            counts[node.node_type] += 1
        return dict(counts)


class SpatialAnalyzer:
    """
    Advanced spatial relationship analysis for P&ID graphs.
    
    Detects:
    1. Containment (instruments inside equipment boundaries)
    2. Alignment (instruments on same horizontal/vertical line)
    3. Line intersections (symbols touching flow lines)
    4. Spatial clustering (grouped nodes)
    """
    
    def __init__(
        self,
        containment_threshold: float = 0.5,
        alignment_tolerance: float = 10.0,
        cluster_distance: float = 150.0,
    ):
        """
        Initialize spatial analyzer.
        
        Args:
            containment_threshold: Minimum overlap for containment (0-1)
            alignment_tolerance: Max pixel deviation for alignment
            cluster_distance: Max distance for clustering
        """
        self.containment_threshold = containment_threshold
        self.alignment_tolerance = alignment_tolerance
        self.cluster_distance = cluster_distance
        
        if not SCIPY_AVAILABLE:
            logger.warning("scipy not available - clustering features disabled")
        if not SHAPELY_AVAILABLE:
            logger.warning("shapely not available - advanced geometry disabled")
        
        logger.info(
            f"SpatialAnalyzer initialized "
            f"(containment={containment_threshold}, "
            f"alignment_tol={alignment_tolerance}px, "
            f"cluster_dist={cluster_distance}px)"
        )
    
    def analyze_all(
        self,
        nodes: list[GraphNode]
    ) -> dict:
        """
        Run all spatial analyses on a set of nodes.
        
        Returns:
            Dictionary with all analysis results
        """
        logger.info(f"Running spatial analysis on {len(nodes)} nodes...")
        
        results = {
            "containment": self.detect_containment(nodes),
            "alignment": self.detect_alignment(nodes),
            "clusters": self.detect_clusters(nodes) if SCIPY_AVAILABLE else [],
            "relationships": [],
        }
        
        # Compile all relationships
        relationships = []
        
        # Add containment relationships
        for container, contained_list in results["containment"].items():
            for contained in contained_list:
                rel = SpatialRelationship(
                    node1_id=container.id,
                    node2_id=contained.id,
                    relation_type=SpatialRelationType.CONTAINS,
                    confidence=0.9,
                    attributes={"container_tag": container.tag, "contained_tag": contained.tag}
                )
                relationships.append(rel)
        
        # Add alignment relationships
        for group in results["alignment"]:
            # Create pairwise relationships within group
            for i, node1 in enumerate(group.nodes):
                for node2 in group.nodes[i+1:]:
                    rel_type = (SpatialRelationType.ALIGNED_HORIZONTAL 
                               if group.orientation == "horizontal" 
                               else SpatialRelationType.ALIGNED_VERTICAL)
                    rel = SpatialRelationship(
                        node1_id=node1.id,
                        node2_id=node2.id,
                        relation_type=rel_type,
                        confidence=0.85,
                        distance=abs(node1.x - node2.x) if group.orientation == "vertical" else abs(node1.y - node2.y),
                        attributes={"axis": group.axis_value, "orientation": group.orientation}
                    )
                    relationships.append(rel)
        
        results["relationships"] = relationships
        
        logger.info(
            f"Spatial analysis complete: "
            f"{len(results['containment'])} containments, "
            f"{len(results['alignment'])} alignment groups, "
            f"{len(results['clusters'])} clusters, "
            f"{len(relationships)} relationships"
        )
        
        return results
    
    def detect_containment(
        self,
        nodes: list[GraphNode]
    ) -> dict[GraphNode, list[GraphNode]]:
        """
        Detect containment relationships (instruments inside equipment).
        
        Returns:
            Dictionary mapping container nodes to list of contained nodes
        """
        containment = {}
        
        # Get potential containers (equipment, vessels, etc.)
        containers = [
            n for n in nodes 
            if n.node_type in (NodeType.EQUIPMENT, NodeType.PUMP)
            and n.width > 0 and n.height > 0
        ]
        
        # Get potential contained items (instruments, small valves)
        containees = [
            n for n in nodes 
            if n.node_type in (NodeType.INSTRUMENT, NodeType.VALVE)
        ]
        
        logger.debug(f"Checking containment: {len(containers)} containers, {len(containees)} potential contained")
        
        for container in containers:
            contained_nodes = []
            
            for containee in containees:
                if containee.id == container.id:
                    continue
                
                # Check if containee center is inside container bbox
                if self._is_contained(containee, container):
                    overlap_ratio = self._calculate_containment_overlap(containee, container)
                    
                    if overlap_ratio >= self.containment_threshold:
                        contained_nodes.append(containee)
                        logger.debug(
                            f"Containment: {container.tag or container.id} contains "
                            f"{containee.tag or containee.id} (overlap={overlap_ratio:.2f})"
                        )
            
            if contained_nodes:
                containment[container] = contained_nodes
        
        return containment
    
    def detect_alignment(
        self,
        nodes: list[GraphNode],
        min_group_size: int = 2
    ) -> list[AlignmentGroup]:
        """
        Detect horizontal and vertical alignment groups.
        
        Args:
            nodes: List of nodes to analyze
            min_group_size: Minimum nodes to form a group
        
        Returns:
            List of alignment groups
        """
        groups = []
        
        # Detect horizontal alignment (same y-coordinate)
        h_groups = self._detect_alignment_axis(
            nodes, 
            axis='y', 
            min_group_size=min_group_size
        )
        for y_value, group_nodes in h_groups.items():
            groups.append(AlignmentGroup(
                orientation="horizontal",
                nodes=group_nodes,
                axis_value=y_value,
                tolerance=self.alignment_tolerance
            ))
        
        # Detect vertical alignment (same x-coordinate)
        v_groups = self._detect_alignment_axis(
            nodes, 
            axis='x', 
            min_group_size=min_group_size
        )
        for x_value, group_nodes in v_groups.items():
            groups.append(AlignmentGroup(
                orientation="vertical",
                nodes=group_nodes,
                axis_value=x_value,
                tolerance=self.alignment_tolerance
            ))
        
        logger.debug(f"Detected {len(groups)} alignment groups")
        return groups
    
    def detect_clusters(
        self,
        nodes: list[GraphNode],
        min_cluster_size: int = 3
    ) -> list[SpatialCluster]:
        """
        Detect spatial clusters using hierarchical clustering.
        
        Args:
            nodes: List of nodes to cluster
            min_cluster_size: Minimum nodes per cluster
        
        Returns:
            List of spatial clusters
        """
        if not SCIPY_AVAILABLE:
            logger.warning("Clustering requires scipy - returning empty list")
            return []
        
        if len(nodes) < min_cluster_size:
            return []
        
        # Extract coordinates
        coords = np.array([[n.x, n.y] for n in nodes])
        
        try:
            # Hierarchical clustering
            cluster_labels = fclusterdata(
                coords,
                t=self.cluster_distance,
                criterion='distance',
                method='complete'
            )
            
            # Group nodes by cluster
            cluster_dict = defaultdict(list)
            for node, label in zip(nodes, cluster_labels):
                cluster_dict[label].append(node)
            
            # Create cluster objects
            clusters = []
            for cluster_id, cluster_nodes in cluster_dict.items():
                if len(cluster_nodes) >= min_cluster_size:
                    # Calculate centroid
                    centroid_x = np.mean([n.x for n in cluster_nodes])
                    centroid_y = np.mean([n.y for n in cluster_nodes])
                    
                    # Calculate radius (max distance from centroid)
                    radius = max(
                        math.sqrt((n.x - centroid_x)**2 + (n.y - centroid_y)**2)
                        for n in cluster_nodes
                    )
                    
                    clusters.append(SpatialCluster(
                        cluster_id=cluster_id,
                        nodes=cluster_nodes,
                        centroid=(centroid_x, centroid_y),
                        radius=radius
                    ))
            
            logger.debug(f"Detected {len(clusters)} clusters")
            return clusters
            
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            return []
    
    def find_nearest_neighbors(
        self,
        target_node: GraphNode,
        nodes: list[GraphNode],
        k: int = 5,
        max_distance: Optional[float] = None
    ) -> list[tuple[GraphNode, float]]:
        """
        Find k nearest neighbors to a target node.
        
        Args:
            target_node: Node to find neighbors for
            nodes: List of candidate nodes
            k: Number of neighbors
            max_distance: Maximum distance threshold
        
        Returns:
            List of (node, distance) tuples
        """
        if SCIPY_AVAILABLE and len(nodes) > 10:
            return self._knn_scipy(target_node, nodes, k, max_distance)
        else:
            return self._knn_simple(target_node, nodes, k, max_distance)
    
    def _is_contained(self, inner: GraphNode, outer: GraphNode) -> bool:
        """Check if inner node center is inside outer node bbox."""
        return (outer.x - outer.width/2 <= inner.x <= outer.x + outer.width/2 and
                outer.y - outer.height/2 <= inner.y <= outer.y + outer.height/2)
    
    def _calculate_containment_overlap(
        self, 
        inner: GraphNode, 
        outer: GraphNode
    ) -> float:
        """
        Calculate overlap ratio for containment.
        
        Returns value between 0 and 1 indicating how much of inner is inside outer.
        """
        # Get bboxes
        inner_x1 = inner.x - inner.width/2
        inner_y1 = inner.y - inner.height/2
        inner_x2 = inner.x + inner.width/2
        inner_y2 = inner.y + inner.height/2
        
        outer_x1 = outer.x - outer.width/2
        outer_y1 = outer.y - outer.height/2
        outer_x2 = outer.x + outer.width/2
        outer_y2 = outer.y + outer.height/2
        
        # Calculate intersection
        x1 = max(inner_x1, outer_x1)
        y1 = max(inner_y1, outer_y1)
        x2 = min(inner_x2, outer_x2)
        y2 = min(inner_y2, outer_y2)
        
        if x2 <= x1 or y2 <= y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        inner_area = inner.width * inner.height
        
        if inner_area <= 0:
            return 0.0
        
        return intersection / inner_area
    
    def _detect_alignment_axis(
        self,
        nodes: list[GraphNode],
        axis: str,
        min_group_size: int
    ) -> dict[float, list[GraphNode]]:
        """
        Detect alignment along a specific axis.
        
        Args:
            nodes: Nodes to analyze
            axis: 'x' or 'y'
            min_group_size: Minimum nodes per group
        
        Returns:
            Dictionary mapping axis values to node groups
        """
        # Get axis values
        axis_values = [getattr(n, axis) for n in nodes]
        
        # Group nodes by similar axis values
        groups = defaultdict(list)
        for node, value in zip(nodes, axis_values):
            # Find existing group within tolerance
            matched = False
            for group_value in list(groups.keys()):
                if abs(value - group_value) <= self.alignment_tolerance:
                    groups[group_value].append(node)
                    matched = True
                    break
            
            if not matched:
                groups[value].append(node)
        
        # Filter by minimum size
        return {
            k: v for k, v in groups.items() 
            if len(v) >= min_group_size
        }
    
    def _knn_scipy(
        self,
        target_node: GraphNode,
        nodes: list[GraphNode],
        k: int,
        max_distance: Optional[float]
    ) -> list[tuple[GraphNode, float]]:
        """KNN using scipy KDTree (fast for large datasets)."""
        coords = np.array([[n.x, n.y] for n in nodes])
        tree = KDTree(coords)
        
        target_coords = np.array([[target_node.x, target_node.y]])
        distances, indices = tree.query(target_coords, k=min(k+1, len(nodes)))
        
        # Filter out the target node itself and apply max_distance
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if nodes[idx].id != target_node.id:
                if max_distance is None or dist <= max_distance:
                    results.append((nodes[idx], dist))
        
        return results[:k]
    
    def _knn_simple(
        self,
        target_node: GraphNode,
        nodes: list[GraphNode],
        k: int,
        max_distance: Optional[float]
    ) -> list[tuple[GraphNode, float]]:
        """Simple KNN using brute force (for small datasets)."""
        distances = []
        for node in nodes:
            if node.id == target_node.id:
                continue
            
            dist = math.sqrt(
                (node.x - target_node.x)**2 + 
                (node.y - target_node.y)**2
            )
            
            if max_distance is None or dist <= max_distance:
                distances.append((node, dist))
        
        # Sort by distance and return top k
        distances.sort(key=lambda x: x[1])
        return distances[:k]


def print_spatial_analysis_summary(results: dict) -> str:
    """
    Generate a human-readable summary of spatial analysis results.
    
    Args:
        results: Output from SpatialAnalyzer.analyze_all()
    
    Returns:
        Formatted summary string
    """
    lines = []
    lines.append("=" * 70)
    lines.append("SPATIAL ANALYSIS SUMMARY")
    lines.append("=" * 70)
    
    # Containment
    containment = results.get("containment", {})
    lines.append(f"\n📦 Containment Relationships: {len(containment)}")
    for container, contained_list in list(containment.items())[:5]:
        container_label = container.tag or container.label
        contained_tags = [n.tag or n.label for n in contained_list]
        lines.append(f"  {container_label} contains: {', '.join(contained_tags[:3])}")
        if len(contained_list) > 3:
            lines.append(f"    ... and {len(contained_list) - 3} more")
    
    # Alignment
    alignment = results.get("alignment", [])
    h_groups = [g for g in alignment if g.orientation == "horizontal"]
    v_groups = [g for g in alignment if g.orientation == "vertical"]
    lines.append(f"\n📏 Alignment Groups: {len(alignment)}")
    lines.append(f"  Horizontal: {len(h_groups)} groups")
    lines.append(f"  Vertical: {len(v_groups)} groups")
    
    for group in alignment[:3]:
        tags = [n.tag or n.label[:10] for n in group.nodes]
        lines.append(f"  {group.orientation} @ {group.axis_value:.1f}: {', '.join(tags[:5])}")
    
    # Clusters
    clusters = results.get("clusters", [])
    lines.append(f"\n🌐 Spatial Clusters: {len(clusters)}")
    for cluster in clusters[:5]:
        types = cluster.node_types
        type_str = ", ".join(f"{k.value}:{v}" for k, v in types.items())
        lines.append(f"  Cluster {cluster.cluster_id}: {cluster.node_count} nodes ({type_str})")
    
    # Relationships
    relationships = results.get("relationships", [])
    lines.append(f"\n🔗 Total Relationships: {len(relationships)}")
    rel_counts = defaultdict(int)
    for rel in relationships:
        rel_counts[rel.relation_type] += 1
    for rel_type, count in rel_counts.items():
        lines.append(f"  {rel_type.value}: {count}")
    
    lines.append("=" * 70)
    return "\n".join(lines)
