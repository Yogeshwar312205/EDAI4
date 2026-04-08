"""
================================================================================
EDAI4 - LINE DETECTOR (Phase 4 — Topology)
================================================================================
Detects process pipes and electrical/signal lines in P&ID images.

Pipeline:
  1. detect_lines(image)       → HoughLinesP → List[LineSegment]
  2. classify_line_type(...)   → solid (pipe) vs dashed (signal)
  3. build_graph_edges(...)    → connect nodes via detected lines

Usage:
    from src.topology.line_detector import LineDetector
    detector = LineDetector()
    lines = detector.detect_lines(image)
    edges = detector.build_graph_edges(nodes, lines)
================================================================================
"""

import cv2
import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple, Optional, Dict, Any
import math


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class LineType(Enum):
    """Physical nature of a detected line."""
    SOLID   = "solid"    # Physical pipe / mechanical connection
    DASHED  = "dashed"   # Electrical / pneumatic / software signal
    UNKNOWN = "unknown"  # Could not determine


@dataclass
class LineSegment:
    """A single detected line segment."""
    x1: float
    y1: float
    x2: float
    y2: float
    line_type: LineType = LineType.UNKNOWN
    confidence: float   = 1.0

    @property
    def length(self) -> float:
        return math.sqrt((self.x2 - self.x1) ** 2 + (self.y2 - self.y1) ** 2)

    @property
    def angle_deg(self) -> float:
        """Angle of line in degrees (0 = horizontal right, 90 = downward)."""
        return math.degrees(math.atan2(self.y2 - self.y1, self.x2 - self.x1))

    @property
    def is_horizontal(self, tol: float = 15.0) -> bool:
        return abs(self.angle_deg % 180) < tol or abs(self.angle_deg % 180 - 180) < tol

    @property
    def is_vertical(self, tol: float = 15.0) -> bool:
        return abs(abs(self.angle_deg % 180) - 90) < tol

    @property
    def midpoint(self) -> Tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)

    def start_point(self) -> Tuple[float, float]:
        return (self.x1, self.y1)

    def end_point(self) -> Tuple[float, float]:
        return (self.x2, self.y2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x1": self.x1, "y1": self.y1,
            "x2": self.x2, "y2": self.y2,
            "length": round(self.length, 1),
            "angle_deg": round(self.angle_deg, 1),
            "line_type": self.line_type.value,
            "confidence": round(self.confidence, 3),
        }


@dataclass
class GraphEdge:
    """An edge connecting two P&ID nodes via a detected line."""
    source_id: str
    target_id: str
    line_type: LineType
    line_segment: LineSegment
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "connection_type": self.line_type.value,
            "confidence": round(self.confidence, 3),
            "line": self.line_segment.to_dict(),
        }


# =============================================================================
# LINE DETECTOR
# =============================================================================

class LineDetector:
    """
    Detects process lines (pipes and signals) in P&ID images.

    Strategy
    --------
    1. Preprocess: grayscale → Gaussian blur → Canny edges
    2. HoughLinesP: probabilistic Hough for line segments (fast + accurate)
    3. Filter: remove short segments (<30px) and border/table artifacts
    4. Classify: solid vs dashed by analysing dark-pixel density along the line
    5. Connect: match line endpoints to node bounding boxes → graph edges
    """

    # ── Detection defaults ──────────────────────────────────────────────────
    DEFAULT_CANNY_LOW   = 30
    DEFAULT_CANNY_HIGH  = 100
    DEFAULT_MIN_LENGTH  = 30     # px — ignore micro-lines
    DEFAULT_MAX_GAP     = 15     # px — HoughLinesP maxLineGap
    DEFAULT_THRESHOLD   = 50     # px — HoughLinesP accumulator threshold
    DEFAULT_RHO         = 1      # px
    DEFAULT_THETA       = np.pi / 180  # 1 degree

    # Edge proximity: how far an endpoint can be from a node bbox (px)
    NODE_SNAP_RADIUS = 30

    # Minimum dark-pixel ratio to classify as SOLID
    SOLID_DARK_RATIO   = 0.70
    # Maximum dark-pixel ratio to classify as DASHED
    DASHED_DARK_RATIO  = 0.50

    # Border margin — ignore lines detected within this many px of the image edge
    # (they are usually title-block table borders, not process lines)
    BORDER_MARGIN = 40

    def __init__(
        self,
        min_length: int  = DEFAULT_MIN_LENGTH,
        max_gap:    int  = DEFAULT_MAX_GAP,
        threshold:  int  = DEFAULT_THRESHOLD,
        node_snap_radius: int = NODE_SNAP_RADIUS,
    ):
        self.min_length       = min_length
        self.max_gap          = max_gap
        self.threshold        = threshold
        self.node_snap_radius = node_snap_radius

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 1: Detect Lines
    # ──────────────────────────────────────────────────────────────────────────

    def detect_lines(
        self,
        image:      np.ndarray,
        debug_path: Optional[str] = None,
    ) -> List[LineSegment]:
        """
        Detect all process lines in a P&ID image.

        Args:
            image:      BGR or grayscale image (numpy array)
            debug_path: If set, saves an annotated debug image here

        Returns:
            List[LineSegment] with type classification
        """
        h, w = image.shape[:2]

        # 1. Grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # 2. Blur to reduce noise from text and symbol details
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)

        # 3. Canny edge detection
        edges = cv2.Canny(blurred, self.DEFAULT_CANNY_LOW, self.DEFAULT_CANNY_HIGH)

        # 4. HoughLinesP
        raw_lines = cv2.HoughLinesP(
            edges,
            rho=self.DEFAULT_RHO,
            theta=self.DEFAULT_THETA,
            threshold=self.threshold,
            minLineLength=self.min_length,
            maxLineGap=self.max_gap,
        )

        if raw_lines is None:
            print("[LINES] No lines detected by HoughLinesP")
            return []

        print(f"[LINES] HoughLinesP raw output: {len(raw_lines)} segments")

        # 5. Build LineSegment objects and filter
        segments: List[LineSegment] = []
        for line in raw_lines:
            x1, y1, x2, y2 = line[0]

            seg = LineSegment(
                x1=float(x1), y1=float(y1),
                x2=float(x2), y2=float(y2),
            )

            # Skip segments shorter than threshold
            if seg.length < self.min_length:
                continue

            # Skip segments too close to the image border (table/frame lines)
            if self._is_border_line(seg, w, h):
                continue

            # 6. Classify line type
            seg.line_type = self.classify_line_type(gray, seg)

            segments.append(seg)

        print(f"[LINES] After filtering: {len(segments)} segments")
        solid  = sum(1 for s in segments if s.line_type == LineType.SOLID)
        dashed = sum(1 for s in segments if s.line_type == LineType.DASHED)
        print(f"[LINES]   Solid (pipe):   {solid}")
        print(f"[LINES]   Dashed (signal): {dashed}")
        print(f"[LINES]   Unknown:         {len(segments) - solid - dashed}")

        # 7. Optional debug visualisation
        if debug_path:
            self._save_debug_image(image, segments, debug_path)

        return segments

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 2: Classify Line Type
    # ──────────────────────────────────────────────────────────────────────────

    def classify_line_type(
        self,
        gray_image: np.ndarray,
        segment:    LineSegment,
        samples:    int = 60,
    ) -> LineType:
        """
        Determine if a line is solid (physical pipe) or dashed (signal cable).

        Samples `samples` evenly-spaced points along the line segment and
        counts how many are "dark" (pixel value < 128 on the grayscale image).

        - Dark ratio > 0.70  → SOLID   (continuous ink → pipe)
        - Dark ratio < 0.50  → DASHED  (gaps in ink → signal line)
        - Otherwise          → UNKNOWN

        Args:
            gray_image: Single-channel (grayscale) image
            segment:    The line segment to classify
            samples:    Number of sample points along the line

        Returns:
            LineType enum value
        """
        h, w = gray_image.shape[:2]
        dark_count = 0

        for i in range(samples):
            t = i / max(samples - 1, 1)
            px = int(segment.x1 + t * (segment.x2 - segment.x1))
            py = int(segment.y1 + t * (segment.y2 - segment.y1))

            # Clamp to image bounds
            px = max(0, min(px, w - 1))
            py = max(0, min(py, h - 1))

            if gray_image[py, px] < 128:
                dark_count += 1

        ratio = dark_count / samples

        if ratio >= self.SOLID_DARK_RATIO:
            return LineType.SOLID
        elif ratio <= self.DASHED_DARK_RATIO:
            return LineType.DASHED
        else:
            return LineType.UNKNOWN

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 3: Build Graph Edges
    # ──────────────────────────────────────────────────────────────────────────

    def build_graph_edges(
        self,
        nodes:    List[Dict[str, Any]],
        segments: List[LineSegment],
    ) -> List[GraphEdge]:
        """
        Connect detected line endpoints to P&ID nodes, creating graph edges.

        For each LineSegment, checks if:
          - start_point is within NODE_SNAP_RADIUS of any node's bbox
          - end_point   is within NODE_SNAP_RADIUS of a DIFFERENT node's bbox

        If both endpoints snap to different nodes, a GraphEdge is created.

        Args:
            nodes:    List of node dicts with keys: 'id', 'x1','y1','x2','y2'
                      (Compatible with DetectedNode and GraphNode objects)
            segments: Output of detect_lines()

        Returns:
            List[GraphEdge] representing topology connections
        """
        edges: List[GraphEdge] = []

        for seg in segments:
            start_node = self._snap_point_to_node(seg.start_point(), nodes)
            end_node   = self._snap_point_to_node(seg.end_point(),   nodes)

            # Both endpoints must connect to DIFFERENT nodes
            if start_node is None or end_node is None:
                continue
            if start_node['id'] == end_node['id']:
                continue

            edge = GraphEdge(
                source_id    = start_node['id'],
                target_id    = end_node['id'],
                line_type    = seg.line_type,
                line_segment = seg,
                confidence   = seg.confidence,
            )
            edges.append(edge)

            print(
                f"  [EDGE] {start_node['id']} --[{seg.line_type.value}]--> {end_node['id']}"
                f" (len={seg.length:.0f}px)"
            )

        print(f"[LINES] Built {len(edges)} graph edges from {len(segments)} segments")
        return edges

    # ──────────────────────────────────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────────────────────────────────

    def _snap_point_to_node(
        self,
        point: Tuple[float, float],
        nodes: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Find the node whose bounding box is nearest to `point`.

        Checks if `point` is inside the bbox OR within NODE_SNAP_RADIUS of it.
        Returns the closest match, or None if no node is within range.
        """
        px, py = point
        best_node = None
        best_dist = float('inf')

        for node in nodes:
            # Support both dict and dataclass-style objects
            try:
                x1 = node['x1'] if isinstance(node, dict) else node.x1
                y1 = node['y1'] if isinstance(node, dict) else node.y1
                x2 = node['x2'] if isinstance(node, dict) else node.x2
                y2 = node['y2'] if isinstance(node, dict) else node.y2
                nid = node['id'] if isinstance(node, dict) else node.id
            except (KeyError, AttributeError):
                continue

            # Distance from point to bbox (0 if inside)
            cx = max(x1, min(px, x2))
            cy = max(y1, min(py, y2))
            dist = math.sqrt((px - cx) ** 2 + (py - cy) ** 2)

            if dist <= self.node_snap_radius and dist < best_dist:
                best_dist = dist
                best_node = {'id': nid, 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}

        return best_node

    def _is_border_line(
        self,
        seg: LineSegment,
        img_w: int,
        img_h: int,
    ) -> bool:
        """
        Return True if the segment is likely a title-block or frame border.

        Heuristics:
        - Segment lies entirely within BORDER_MARGIN pixels of any edge
        - Segment spans nearly the full image width or height (table divider)
        """
        m = self.BORDER_MARGIN

        # Near the image border?
        near_left   = seg.x1 < m and seg.x2 < m
        near_right  = seg.x1 > (img_w - m) and seg.x2 > (img_w - m)
        near_top    = seg.y1 < m and seg.y2 < m
        near_bottom = seg.y1 > (img_h - m) and seg.y2 > (img_h - m)

        if near_left or near_right or near_top or near_bottom:
            return True

        # Full-width horizontal line (likely a row separator in a table)
        if seg.is_horizontal and seg.length > img_w * 0.85:
            return True

        # Full-height vertical line
        if seg.is_vertical and seg.length > img_h * 0.85:
            return True

        return False

    def _save_debug_image(
        self,
        image:    np.ndarray,
        segments: List[LineSegment],
        path:     str,
    ) -> None:
        """Draw detected lines on a copy of the image and save."""
        vis = image.copy() if len(image.shape) == 3 else cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        COLOR_MAP = {
            LineType.SOLID:   (0, 200, 0),    # Green  = pipe
            LineType.DASHED:  (0, 150, 255),  # Orange = signal
            LineType.UNKNOWN: (180, 180, 180),# Grey
        }

        for seg in segments:
            color = COLOR_MAP[seg.line_type]
            cv2.line(vis,
                     (int(seg.x1), int(seg.y1)),
                     (int(seg.x2), int(seg.y2)),
                     color, 2)
            # Mark endpoints
            cv2.circle(vis, (int(seg.x1), int(seg.y1)), 4, color, -1)
            cv2.circle(vis, (int(seg.x2), int(seg.y2)), 4, color, -1)

        cv2.imwrite(path, vis)
        print(f"[LINES] Debug image saved → {path}")


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def detect_and_connect(
    image: np.ndarray,
    nodes: List[Dict[str, Any]],
    debug_path: Optional[str] = None,
) -> Tuple[List[LineSegment], List[GraphEdge]]:
    """
    One-shot: detect lines and build graph edges.

    Args:
        image:      BGR P&ID image
        nodes:      List of detected node dicts (with 'id', 'x1','y1','x2','y2')
        debug_path: Optional path for debug visualisation

    Returns:
        (lines, edges) tuple
    """
    detector = LineDetector()
    lines = detector.detect_lines(image, debug_path=debug_path)
    edges = detector.build_graph_edges(nodes, lines)
    return lines, edges
