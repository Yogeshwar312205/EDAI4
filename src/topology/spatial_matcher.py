"""
EDAI4 - Spatial Matcher
Associates text labels with detected symbols based on proximity
"""

from dataclasses import dataclass
from typing import Optional
import math

from src.utils import get_logger
from src.perception import Detection, TextBlock, BoundingBox, TextRegion

logger = get_logger(__name__)


@dataclass
class SpatialMatch:
    """Match between a symbol and its associated text."""
    symbol: Detection
    text_block: TextBlock
    distance: float
    confidence: float
    match_type: str  # "overlap", "proximity", "nearest"


class SpatialMatcher:
    """
    Matches text blocks to symbols based on spatial proximity.
    Uses geometric relationships to associate labels with P&ID symbols.
    """

    def __init__(
        self,
        max_distance: float = 100.0,
        overlap_threshold: float = 0.3,
    ):
        """
        Initialize spatial matcher.

        Args:
            max_distance: Maximum pixel distance for text-symbol association
            overlap_threshold: Minimum overlap ratio for direct association
        """
        self.max_distance = max_distance
        self.overlap_threshold = overlap_threshold

        logger.info(
            f"SpatialMatcher initialized (max_dist={max_distance}, "
            f"overlap={overlap_threshold})"
        )

    def match_text_to_symbols(
        self,
        text_blocks: list[TextBlock],
        detections: list[Detection],
    ) -> list[SpatialMatch]:
        """
        Match text blocks to detected symbols.

        Args:
            text_blocks: List of OCR text blocks
            detections: List of symbol detections

        Returns:
            List of spatial matches
        """
        matches = []
        matched_texts = set()

        # First pass: Direct overlaps
        for detection in detections:
            for i, text_block in enumerate(text_blocks):
                if i in matched_texts:
                    continue

                overlap = self._calculate_overlap(
                    text_block.region, detection.bbox
                )

                if overlap >= self.overlap_threshold:
                    match = SpatialMatch(
                        symbol=detection,
                        text_block=text_block,
                        distance=0,
                        confidence=min(overlap * 2, 1.0),
                        match_type="overlap",
                    )
                    matches.append(match)
                    matched_texts.add(i)

                    # Update detection with text info
                    if text_block.is_tag:
                        detection.tag_number = text_block.tag_number
                    detection.associated_text = text_block.cleaned_text or text_block.text

        # Second pass: Proximity matching
        for detection in detections:
            # Skip if already has associated text
            if detection.associated_text:
                continue

            best_match = None
            best_distance = self.max_distance

            for i, text_block in enumerate(text_blocks):
                if i in matched_texts:
                    continue

                distance = self._calculate_distance(
                    text_block.region, detection.bbox
                )

                if distance < best_distance:
                    best_distance = distance
                    best_match = (i, text_block)

            if best_match:
                i, text_block = best_match
                confidence = 1.0 - (best_distance / self.max_distance)

                match = SpatialMatch(
                    symbol=detection,
                    text_block=text_block,
                    distance=best_distance,
                    confidence=confidence,
                    match_type="proximity",
                )
                matches.append(match)
                matched_texts.add(i)

                if text_block.is_tag:
                    detection.tag_number = text_block.tag_number
                detection.associated_text = text_block.cleaned_text or text_block.text

        logger.info(f"Created {len(matches)} spatial matches")
        return matches

    def find_nearest_symbol(
        self,
        text_block: TextBlock,
        detections: list[Detection],
    ) -> Optional[Detection]:
        """
        Find the nearest symbol to a text block.

        Args:
            text_block: Text block to match
            detections: Available symbol detections

        Returns:
            Nearest detection or None
        """
        if not detections:
            return None

        nearest = None
        min_distance = float("inf")

        for detection in detections:
            distance = self._calculate_distance(text_block.region, detection.bbox)
            if distance < min_distance:
                min_distance = distance
                nearest = detection

        return nearest if min_distance <= self.max_distance else None

    def find_text_for_symbol(
        self,
        detection: Detection,
        text_blocks: list[TextBlock],
        prefer_tags: bool = True,
    ) -> Optional[TextBlock]:
        """
        Find the best text block for a symbol.

        Args:
            detection: Symbol detection
            text_blocks: Available text blocks
            prefer_tags: Prefer tag numbers over other text

        Returns:
            Best matching text block or None
        """
        if not text_blocks:
            return None

        candidates = []

        for text_block in text_blocks:
            distance = self._calculate_distance(text_block.region, detection.bbox)
            if distance <= self.max_distance:
                candidates.append((text_block, distance))

        if not candidates:
            return None

        # Sort by distance
        candidates.sort(key=lambda x: x[1])

        # Prefer tags if requested
        if prefer_tags:
            for text_block, _ in candidates:
                if text_block.is_tag:
                    return text_block

        return candidates[0][0]

    def _calculate_distance(
        self,
        region: TextRegion,
        bbox: BoundingBox,
    ) -> float:
        """Calculate distance between region center and bbox center."""
        text_cx, text_cy = region.center
        symbol_cx, symbol_cy = bbox.center

        return math.sqrt(
            (text_cx - symbol_cx) ** 2 + (text_cy - symbol_cy) ** 2
        )

    def _calculate_overlap(
        self,
        region: TextRegion,
        bbox: BoundingBox,
    ) -> float:
        """Calculate overlap ratio between region and bbox."""
        # Calculate intersection
        x1 = max(region.x1, bbox.x1)
        y1 = max(region.y1, bbox.y1)
        x2 = min(region.x2, bbox.x2)
        y2 = min(region.y2, bbox.y2)

        if x2 <= x1 or y2 <= y1:
            return 0.0

        intersection = (x2 - x1) * (y2 - y1)
        region_area = region.width * region.height
        bbox_area = bbox.area

        # IoU-like calculation
        union = region_area + bbox_area - intersection
        if union <= 0:
            return 0.0

        return intersection / union

    def get_unmatched_texts(
        self,
        text_blocks: list[TextBlock],
        matches: list[SpatialMatch],
    ) -> list[TextBlock]:
        """Get text blocks that weren't matched to any symbol."""
        matched_texts = {id(m.text_block) for m in matches}
        return [tb for tb in text_blocks if id(tb) not in matched_texts]

    def get_unmatched_symbols(
        self,
        detections: list[Detection],
        matches: list[SpatialMatch],
    ) -> list[Detection]:
        """Get symbols that weren't matched to any text."""
        matched_symbols = {id(m.symbol) for m in matches}
        return [d for d in detections if id(d) not in matched_symbols]
