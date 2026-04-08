"""
EDAI4 - Topology Layer
Graph construction and spatial analysis for P&ID
"""

from src.topology.spatial_matcher import SpatialMatcher, SpatialMatch
from src.topology.graph_builder import (
    GraphBuilder,
    PIDGraph,
    GraphNode,
    GraphEdge,
    NodeType,
    EdgeType,
)
from src.topology.spatial_analyzer import (
    SpatialAnalyzer,
    SpatialRelationType,
    SpatialRelationship,
    AlignmentGroup,
    SpatialCluster,
    print_spatial_analysis_summary,
)
from src.topology.flow_analyzer import (
    FlowAnalyzer,
    FlowDirection,
    FlowSegment,
    FlowPath,
    FlowArrowInfo,
    print_flow_analysis_summary,
)
from src.topology.query_tools import (
    GraphQueryTools,
    InstrumentIndexEntry,
    InstrumentType,
    ControlLoop,
    SafetyFunction,
    print_deliverables_summary,
)
from src.topology.neo4j_client import Neo4jClient
from src.topology.line_detector import (
    LineDetector,
    LineSegment,
    LineType,
    GraphEdge as LineGraphEdge,
    detect_and_connect,
)

__all__ = [
    # Spatial Matcher (legacy)
    "SpatialMatcher",
    "SpatialMatch",

    # Graph Builder
    "GraphBuilder",
    "PIDGraph",
    "GraphNode",
    "GraphEdge",
    "NodeType",
    "EdgeType",
    
    # Spatial Analyzer (Phase 3.2)
    "SpatialAnalyzer",
    "SpatialRelationType",
    "SpatialRelationship",
    "AlignmentGroup",
    "SpatialCluster",
    "print_spatial_analysis_summary",
    
    # Flow Analyzer (Phase 3.3)
    "FlowAnalyzer",
    "FlowDirection",
    "FlowSegment",
    "FlowPath",
    "FlowArrowInfo",
    "print_flow_analysis_summary",
    
    # Query Tools (Phase 3.4)
    "GraphQueryTools",
    "InstrumentIndexEntry",
    "InstrumentType",
    "ControlLoop",
    "SafetyFunction",
    "print_deliverables_summary",

    # Neo4j Client
    "Neo4jClient",

    # Line Detector (Phase 4)
    "LineDetector",
    "LineSegment",
    "LineType",
    "LineGraphEdge",
    "detect_and_connect",
]
