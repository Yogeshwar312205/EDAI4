"""
EDAI4 - Line/Pipe Detector
Detects black lines connecting instruments using OpenCV
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict
from dataclasses import dataclass


@dataclass
class Line:
    """Detected line segment"""
    x1: float
    y1: float
    x2: float
    y2: float
    length: float
    angle: float
    thickness: float
    
    def midpoint(self) -> Tuple[float, float]:
        """Get midpoint of line"""
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)
    
    def intersects_bbox(self, bbox: Tuple[float, float, float, float], margin: float = 5) -> bool:
        """Check if line intersects with bounding box"""
        x1, y1, x2, y2 = bbox
        # Expand bbox by margin
        x1 -= margin
        y1 -= margin
        x2 += margin
        y2 += margin
        
        # Check if either endpoint is inside bbox
        if (x1 <= self.x1 <= x2 and y1 <= self.y1 <= y2) or \
           (x1 <= self.x2 <= x2 and y1 <= self.y2 <= y2):
            return True
        
        # Check if line crosses bbox edges
        # This is a simplified check - could be more sophisticated
        return False


class LineDetector:
    """Detect lines/pipes in P&ID using OpenCV"""
    
    def __init__(
        self,
        min_line_length: int = 30,
        max_line_gap: int = 10,
        canny_low: int = 50,
        canny_high: int = 150,
        hough_threshold: int = 50,
        thickness_threshold: int = 5,
    ):
        """
        Initialize line detector
        
        Args:
            min_line_length: Minimum line length in pixels
            max_line_gap: Maximum gap between line segments to connect
            canny_low: Lower threshold for Canny edge detection
            canny_high: Upper threshold for Canny edge detection
            hough_threshold: Threshold for Hough line detection
            thickness_threshold: Maximum line thickness to consider
        """
        self.min_line_length = min_line_length
        self.max_line_gap = max_line_gap
        self.canny_low = canny_low
        self.canny_high = canny_high
        self.hough_threshold = hough_threshold
        self.thickness_threshold = thickness_threshold
    
    def detect_lines(self, image: np.ndarray) -> List[Line]:
        """
        Detect lines in image
        
        Args:
            image: Input image (BGR or grayscale)
            
        Returns:
            List of detected lines
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection
        edges = cv2.Canny(blurred, self.canny_low, self.canny_high)
        
        # Detect lines using Probabilistic Hough Transform
        lines_raw = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=self.hough_threshold,
            minLineLength=self.min_line_length,
            maxLineGap=self.max_line_gap
        )
        
        if lines_raw is None:
            return []
        
        # Convert to Line objects
        lines = []
        for line in lines_raw:
            x1, y1, x2, y2 = line[0]
            
            # Calculate line properties
            length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
            
            # Estimate thickness (simplified - could be more sophisticated)
            thickness = self._estimate_thickness(gray, x1, y1, x2, y2)
            
            # Filter out very thick lines (likely not pipes)
            if thickness <= self.thickness_threshold:
                lines.append(Line(
                    x1=float(x1),
                    y1=float(y1),
                    x2=float(x2),
                    y2=float(y2),
                    length=float(length),
                    angle=float(angle),
                    thickness=float(thickness)
                ))
        
        # Merge nearby parallel lines
        lines = self._merge_parallel_lines(lines)
        
        return lines
    
    def _estimate_thickness(
        self,
        gray: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int
    ) -> float:
        """Estimate line thickness by sampling perpendicular to line"""
        # Get line direction
        dx = x2 - x1
        dy = y2 - y1
        length = np.sqrt(dx**2 + dy**2)
        
        if length == 0:
            return 1.0
        
        # Normalize direction
        dx /= length
        dy /= length
        
        # Perpendicular direction
        px = -dy
        py = dx
        
        # Sample at midpoint
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        
        # Sample perpendicular profile
        max_thickness = 20
        thickness = 1.0
        
        for dist in range(1, max_thickness):
            # Check both sides
            x_pos = int(mx + px * dist)
            y_pos = int(my + py * dist)
            x_neg = int(mx - px * dist)
            y_neg = int(my - py * dist)
            
            # Check if still on dark line
            if 0 <= x_pos < gray.shape[1] and 0 <= y_pos < gray.shape[0]:
                if gray[y_pos, x_pos] < 128:  # Dark pixel
                    thickness = dist
                else:
                    break
            
            if 0 <= x_neg < gray.shape[1] and 0 <= y_neg < gray.shape[0]:
                if gray[y_neg, x_neg] < 128:  # Dark pixel
                    thickness = max(thickness, dist)
                else:
                    break
        
        return thickness * 2  # Both sides
    
    def _merge_parallel_lines(self, lines: List[Line], angle_threshold: float = 5.0, distance_threshold: float = 10.0) -> List[Line]:
        """Merge nearby parallel lines"""
        if len(lines) <= 1:
            return lines
        
        merged = []
        used = set()
        
        for i, line1 in enumerate(lines):
            if i in used:
                continue
            
            # Find parallel lines nearby
            group = [line1]
            
            for j, line2 in enumerate(lines):
                if j <= i or j in used:
                    continue
                
                # Check if parallel (similar angle)
                angle_diff = abs(line1.angle - line2.angle)
                if angle_diff > 180:
                    angle_diff = 360 - angle_diff
                
                if angle_diff < angle_threshold:
                    # Check if nearby
                    mid1 = line1.midpoint()
                    mid2 = line2.midpoint()
                    distance = np.sqrt((mid1[0] - mid2[0])**2 + (mid1[1] - mid2[1])**2)
                    
                    if distance < distance_threshold:
                        group.append(line2)
                        used.add(j)
            
            # Merge group into single line
            if len(group) == 1:
                merged.append(line1)
            else:
                # Average the lines
                x1_avg = np.mean([l.x1 for l in group])
                y1_avg = np.mean([l.y1 for l in group])
                x2_avg = np.mean([l.x2 for l in group])
                y2_avg = np.mean([l.y2 for l in group])
                
                length = np.sqrt((x2_avg - x1_avg)**2 + (y2_avg - y1_avg)**2)
                angle = np.arctan2(y2_avg - y1_avg, x2_avg - x1_avg) * 180 / np.pi
                thickness = np.mean([l.thickness for l in group])
                
                merged.append(Line(
                    x1=x1_avg,
                    y1=y1_avg,
                    x2=x2_avg,
                    y2=y2_avg,
                    length=length,
                    angle=angle,
                    thickness=thickness
                ))
        
        return merged
    
    def find_connections(
        self,
        lines: List[Line],
        nodes: List[Dict],
        connection_threshold: float = 20.0
    ) -> List[Tuple[str, str]]:
        """
        Find which nodes are connected by lines
        
        Args:
            lines: Detected lines
            nodes: List of node dictionaries with 'id', 'x1', 'y1', 'x2', 'y2'
            connection_threshold: Maximum distance from line to node to consider connected
            
        Returns:
            List of (node_id1, node_id2) tuples representing connections
        """
        connections = []
        
        for line in lines:
            # Find nodes near this line
            connected_nodes = []
            
            for node in nodes:
                bbox = (node['x1'], node['y1'], node['x2'], node['y2'])
                
                # Check if line intersects or is very close to node
                if line.intersects_bbox(bbox, margin=connection_threshold):
                    connected_nodes.append(node['id'])
                else:
                    # Check distance from line endpoints to node center
                    node_cx = (node['x1'] + node['x2']) / 2
                    node_cy = (node['y1'] + node['y2']) / 2
                    
                    dist1 = np.sqrt((line.x1 - node_cx)**2 + (line.y1 - node_cy)**2)
                    dist2 = np.sqrt((line.x2 - node_cx)**2 + (line.y2 - node_cy)**2)
                    
                    if min(dist1, dist2) < connection_threshold:
                        connected_nodes.append(node['id'])
            
            # Create connections between all nodes on this line
            for i in range(len(connected_nodes)):
                for j in range(i + 1, len(connected_nodes)):
                    connection = (connected_nodes[i], connected_nodes[j])
                    # Avoid duplicates
                    if connection not in connections and (connection[1], connection[0]) not in connections:
                        connections.append(connection)
        
        return connections
    
    def visualize_lines(self, image: np.ndarray, lines: List[Line]) -> np.ndarray:
        """Draw detected lines on image for visualization"""
        vis = image.copy()
        
        for line in lines:
            # Color based on angle (horizontal = blue, vertical = red, diagonal = green)
            angle = abs(line.angle)
            if angle < 30 or angle > 150:
                color = (255, 0, 0)  # Blue - horizontal
            elif 60 < angle < 120:
                color = (0, 0, 255)  # Red - vertical
            else:
                color = (0, 255, 0)  # Green - diagonal
            
            cv2.line(
                vis,
                (int(line.x1), int(line.y1)),
                (int(line.x2), int(line.y2)),
                color,
                2
            )
        
        return vis
