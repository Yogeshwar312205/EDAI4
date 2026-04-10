"""
P&ID Diff Engine - Automated Redlining & Revision Control
Compares two P&ID versions and highlights changes
"""
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class DiffResult:
    """Result of P&ID comparison"""
    added_items: List[Dict[str, Any]]
    deleted_items: List[Dict[str, Any]]
    modified_items: List[Dict[str, Any]]
    unchanged_items: List[Dict[str, Any]]
    summary: Dict[str, int]


class PIDDiffEngine:
    """Compare two P&ID versions and identify changes"""
    
    def __init__(self, position_tolerance: float = 50.0, tag_match_threshold: float = 0.8):
        """
        Args:
            position_tolerance: Max distance (pixels) to consider items as same position
            tag_match_threshold: Similarity threshold for tag matching
        """
        self.position_tolerance = position_tolerance
        self.tag_match_threshold = tag_match_threshold
    
    def compare(
        self,
        old_result: Dict[str, Any],
        new_result: Dict[str, Any]
    ) -> DiffResult:
        """
        Compare two P&ID processing results
        
        Args:
            old_result: ProcessingResult from old P&ID
            new_result: ProcessingResult from new P&ID
            
        Returns:
            DiffResult with categorized changes
        """
        
        old_detections = old_result.get('detections', [])
        new_detections = new_result.get('detections', [])
        
        # Match detections between old and new
        matches, added, deleted = self._match_detections(old_detections, new_detections)
        
        # Identify modified items
        modified = []
        unchanged = []
        
        for old_idx, new_idx in matches:
            old_item = old_detections[old_idx]
            new_item = new_detections[new_idx]
            
            if self._is_modified(old_item, new_item):
                modified.append({
                    'old': old_item,
                    'new': new_item,
                    'changes': self._get_changes(old_item, new_item)
                })
            else:
                unchanged.append(new_item)
        
        # Prepare added/deleted items
        added_items = [new_detections[idx] for idx in added]
        deleted_items = [old_detections[idx] for idx in deleted]
        
        # Create summary
        summary = {
            'total_old': len(old_detections),
            'total_new': len(new_detections),
            'added': len(added_items),
            'deleted': len(deleted_items),
            'modified': len(modified),
            'unchanged': len(unchanged)
        }
        
        return DiffResult(
            added_items=added_items,
            deleted_items=deleted_items,
            modified_items=modified,
            unchanged_items=unchanged,
            summary=summary
        )
    
    def _match_detections(
        self,
        old_detections: List[Dict],
        new_detections: List[Dict]
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """
        Match detections between old and new P&IDs
        
        Returns:
            (matches, added_indices, deleted_indices)
        """
        
        matches = []
        used_new = set()
        used_old = set()
        
        # First pass: Match by tag (if available)
        for old_idx, old_item in enumerate(old_detections):
            if old_item.get('tag'):
                for new_idx, new_item in enumerate(new_detections):
                    if new_idx in used_new:
                        continue
                    
                    if new_item.get('tag') == old_item.get('tag'):
                        matches.append((old_idx, new_idx))
                        used_old.add(old_idx)
                        used_new.add(new_idx)
                        break
        
        # Second pass: Match by position and class
        for old_idx, old_item in enumerate(old_detections):
            if old_idx in used_old:
                continue
            
            old_center = self._get_center(old_item['bbox'])
            
            best_match = None
            best_distance = float('inf')
            
            for new_idx, new_item in enumerate(new_detections):
                if new_idx in used_new:
                    continue
                
                # Check if same class
                if old_item['class_name'] != new_item['class_name']:
                    continue
                
                new_center = self._get_center(new_item['bbox'])
                distance = self._euclidean_distance(old_center, new_center)
                
                if distance < self.position_tolerance and distance < best_distance:
                    best_match = new_idx
                    best_distance = distance
            
            if best_match is not None:
                matches.append((old_idx, best_match))
                used_old.add(old_idx)
                used_new.add(best_match)
        
        # Identify added and deleted
        added = [i for i in range(len(new_detections)) if i not in used_new]
        deleted = [i for i in range(len(old_detections)) if i not in used_old]
        
        return matches, added, deleted
    
    def _is_modified(self, old_item: Dict, new_item: Dict) -> bool:
        """Check if item has been modified"""
        
        # Check tag change
        if old_item.get('tag') != new_item.get('tag'):
            return True
        
        # Check class change
        if old_item['class_name'] != new_item['class_name']:
            return True
        
        # Check significant position change
        old_center = self._get_center(old_item['bbox'])
        new_center = self._get_center(new_item['bbox'])
        distance = self._euclidean_distance(old_center, new_center)
        
        if distance > self.position_tolerance / 2:
            return True
        
        # Check size change
        old_size = self._get_size(old_item['bbox'])
        new_size = self._get_size(new_item['bbox'])
        
        size_change = abs(old_size - new_size) / old_size if old_size > 0 else 0
        if size_change > 0.2:  # 20% size change
            return True
        
        return False
    
    def _get_changes(self, old_item: Dict, new_item: Dict) -> List[str]:
        """Get list of changes between items"""
        
        changes = []
        
        if old_item.get('tag') != new_item.get('tag'):
            changes.append(f"Tag changed: {old_item.get('tag')} → {new_item.get('tag')}")
        
        if old_item['class_name'] != new_item['class_name']:
            changes.append(f"Class changed: {old_item['class_name']} → {new_item['class_name']}")
        
        old_center = self._get_center(old_item['bbox'])
        new_center = self._get_center(new_item['bbox'])
        distance = self._euclidean_distance(old_center, new_center)
        
        if distance > self.position_tolerance / 2:
            changes.append(f"Position moved: {distance:.1f} pixels")
        
        return changes
    
    def _get_center(self, bbox: Dict) -> Tuple[float, float]:
        """Get center point of bounding box"""
        return (
            (bbox['x1'] + bbox['x2']) / 2,
            (bbox['y1'] + bbox['y2']) / 2
        )
    
    def _get_size(self, bbox: Dict) -> float:
        """Get size (area) of bounding box"""
        width = bbox['x2'] - bbox['x1']
        height = bbox['y2'] - bbox['y1']
        return width * height
    
    def _euclidean_distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points"""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
