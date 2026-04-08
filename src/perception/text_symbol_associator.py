"""
EDAI4 - Text-Symbol Associator
Spatial association engine linking OCR text to detected P&ID symbols

This module implements the core intelligence for Layer 2, connecting
visual symbol detections (from YOLO) with semantic text (from OCR).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import math

from src.perception.symbol_detector import Detection, DetectionResult, BoundingBox
from src.perception.ocr_engine import OCRResult, TextBlock, TextRegion
from src.perception.text_normalizer import TextNormalizer
from src.utils import get_logger

logger = get_logger(__name__)


class AssociationType(Enum):
    """How text is spatially related to a symbol."""
    INSIDE = "inside"           # Text overlaps symbol bbox (common for bubbles)
    ABOVE = "above"             # Text positioned above symbol
    BELOW = "below"             # Text positioned below symbol
    LEFT = "left"               # Text positioned to left
    RIGHT = "right"             # Text positioned to right
    LEADER_LINE = "leader"      # Text connected via leader line (callout)
    UNKNOWN = "unknown"


@dataclass
class AssociationCandidate:
    """A potential text-symbol association with scoring."""
    text_block: TextBlock
    detection: Detection
    association_type: AssociationType
    distance: float                     # Pixel distance between centers
    score: float = 0.0                  # Association confidence score
    is_tag_format: bool = False         # Text matches tag pattern
    overlap_ratio: float = 0.0          # How much text overlaps symbol


@dataclass
class SymbolTextAssociation:
    """Final association between a symbol and its text."""
    detection: Detection
    tag_number: Optional[str] = None
    description: Optional[str] = None
    associated_texts: list[TextBlock] = field(default_factory=list)
    confidence: float = 0.0
    association_type: AssociationType = AssociationType.UNKNOWN


@dataclass
class AssociationResult:
    """Result of text-symbol association for an image."""
    associations: list[SymbolTextAssociation] = field(default_factory=list)
    unassociated_symbols: list[Detection] = field(default_factory=list)
    unassociated_texts: list[TextBlock] = field(default_factory=list)
    processing_time_ms: float = 0.0

    def get_instruments(self) -> list[SymbolTextAssociation]:
        """Get associations for instrument symbols."""
        instrument_classes = [
            "instrument.bubble", "instrument.inline",
            "transmitter", "indicator", "controller", "switch"
        ]
        return [a for a in self.associations
                if any(ic in a.detection.class_name.lower() for ic in instrument_classes)]

    def get_valves(self) -> list[SymbolTextAssociation]:
        """Get associations for valve symbols."""
        return [a for a in self.associations
                if "valve" in a.detection.class_name.lower()]

    def get_equipment(self) -> list[SymbolTextAssociation]:
        """Get associations for equipment symbols."""
        equipment_classes = ["pump", "compressor", "blower", "equipment"]
        return [a for a in self.associations
                if any(ec in a.detection.class_name.lower() for ec in equipment_classes)]


class TextSymbolAssociator:
    """
    Associates OCR text with detected P&ID symbols using spatial analysis.

    Strategy:
    1. For each symbol, define search regions (inside, cardinal directions)
    2. Find candidate text blocks in each region
    3. Score candidates based on distance, format match, position preference
    4. Resolve conflicts (one text → one symbol, closest wins)
    5. Apply class-specific rules (bubbles expect internal text)
    """

    # Search region configuration (pixels)
    DEFAULT_SEARCH_RADIUS = 150
    INSIDE_OVERLAP_THRESHOLD = 0.3      # 30% overlap = inside
    MIN_ASSOCIATION_SCORE = 0.3

    # Position preference weights (engineering convention)
    POSITION_WEIGHTS = {
        AssociationType.INSIDE: 1.0,     # Highest priority for bubbles
        AssociationType.RIGHT: 0.9,      # Tags often to the right
        AssociationType.BELOW: 0.85,     # Or below
        AssociationType.ABOVE: 0.7,
        AssociationType.LEFT: 0.6,
        AssociationType.LEADER_LINE: 0.95,
        AssociationType.UNKNOWN: 0.3,
    }

    # Class-specific search preferences
    CLASS_PREFERENCES = {
        "instrument.bubble": {
            "prefer_inside": True,
            "search_radius": 80,
            "expect_tag": True,
        },
        "instrument.inline": {
            "prefer_inside": False,
            "search_radius": 120,
            "expect_tag": True,
        },
        "valve": {
            "prefer_inside": False,
            "search_radius": 100,
            "expect_tag": True,
        },
        "equipment": {
            "prefer_inside": False,
            "search_radius": 200,
            "expect_tag": True,
        },
        "default": {
            "prefer_inside": False,
            "search_radius": 150,
            "expect_tag": False,
        }
    }

    def __init__(
        self,
        search_radius: float = DEFAULT_SEARCH_RADIUS,
        min_score: float = MIN_ASSOCIATION_SCORE,
    ):
        """
        Initialize the associator.

        Args:
            search_radius: Default search radius in pixels
            min_score: Minimum score for valid association
        """
        self.search_radius = search_radius
        self.min_score = min_score
        self.normalizer = TextNormalizer()

        logger.info(f"TextSymbolAssociator initialized (radius={search_radius}px)")

    def associate(
        self,
        detections: DetectionResult,
        ocr_result: OCRResult,
    ) -> AssociationResult:
        """
        Associate text blocks with detected symbols.

        Args:
            detections: YOLO detection results
            ocr_result: OCR extraction results

        Returns:
            AssociationResult with matched pairs
        """
        import time
        start_time = time.time()

        result = AssociationResult()

        # Track which texts have been assigned
        assigned_texts: set[int] = set()

        # Process each detection
        for detection in detections.detections:
            candidates = self._find_candidates(
                detection,
                ocr_result.text_blocks,
                assigned_texts,
            )

            if candidates:
                # Pick best candidate(s)
                best = self._select_best_candidates(candidates, detection)

                association = SymbolTextAssociation(
                    detection=detection,
                    confidence=best[0].score if best else 0.0,
                    association_type=best[0].association_type if best else AssociationType.UNKNOWN,
                )

                for candidate in best:
                    text_idx = ocr_result.text_blocks.index(candidate.text_block)
                    assigned_texts.add(text_idx)
                    association.associated_texts.append(candidate.text_block)

                    # Extract tag if present
                    if candidate.is_tag_format and not association.tag_number:
                        association.tag_number = candidate.text_block.tag_number
                        detection.tag_number = association.tag_number

                result.associations.append(association)
            else:
                result.unassociated_symbols.append(detection)

        # Collect unassociated texts
        for i, text_block in enumerate(ocr_result.text_blocks):
            if i not in assigned_texts:
                result.unassociated_texts.append(text_block)

        result.processing_time_ms = (time.time() - start_time) * 1000

        logger.info(
            f"Associated {len(result.associations)} symbols, "
            f"{len(result.unassociated_symbols)} orphan symbols, "
            f"{len(result.unassociated_texts)} orphan texts "
            f"in {result.processing_time_ms:.1f}ms"
        )

        return result

    def _find_candidates(
        self,
        detection: Detection,
        text_blocks: list[TextBlock],
        assigned: set[int],
    ) -> list[AssociationCandidate]:
        """Find candidate text blocks for a detection."""
        candidates = []
        prefs = self._get_class_preferences(detection.class_name)
        search_radius = prefs["search_radius"]

        symbol_center = detection.bbox.center

        for i, text_block in enumerate(text_blocks):
            if i in assigned:
                continue

            text_center = text_block.region.center
            distance = self._euclidean_distance(symbol_center, text_center)

            # Check overlap first (for inside association)
            overlap = self._calculate_overlap(detection.bbox, text_block.region)

            if overlap >= self.INSIDE_OVERLAP_THRESHOLD:
                assoc_type = AssociationType.INSIDE
            elif distance <= search_radius:
                assoc_type = self._determine_direction(detection.bbox, text_block.region)
            else:
                continue  # Too far

            # Check if text matches tag format
            is_tag = self.normalizer.is_valid_tag(
                text_block.cleaned_text or text_block.text
            )

            # Calculate score
            score = self._calculate_score(
                distance=distance,
                overlap=overlap,
                assoc_type=assoc_type,
                is_tag=is_tag,
                prefs=prefs,
                search_radius=search_radius,
            )

            if score >= self.min_score:
                candidates.append(AssociationCandidate(
                    text_block=text_block,
                    detection=detection,
                    association_type=assoc_type,
                    distance=distance,
                    score=score,
                    is_tag_format=is_tag,
                    overlap_ratio=overlap,
                ))

        return candidates

    def _calculate_score(
        self,
        distance: float,
        overlap: float,
        assoc_type: AssociationType,
        is_tag: bool,
        prefs: dict,
        search_radius: float,
    ) -> float:
        """Calculate association confidence score."""
        # Base score from distance (closer = better)
        if overlap > 0:
            distance_score = 1.0  # Inside symbol
        else:
            distance_score = max(0, 1 - (distance / search_radius))

        # Position preference
        position_weight = self.POSITION_WEIGHTS.get(assoc_type, 0.5)

        # Tag format bonus
        tag_bonus = 0.3 if is_tag and prefs.get("expect_tag", False) else 0.0

        # Inside bonus for bubble-type symbols
        inside_bonus = 0.2 if (
            assoc_type == AssociationType.INSIDE and
            prefs.get("prefer_inside", False)
        ) else 0.0

        # Combined score
        score = (distance_score * 0.4) + (position_weight * 0.3) + tag_bonus + inside_bonus

        return min(1.0, score)

    def _select_best_candidates(
        self,
        candidates: list[AssociationCandidate],
        detection: Detection,
    ) -> list[AssociationCandidate]:
        """Select best candidate(s) from the list."""
        if not candidates:
            return []

        # Sort by score descending
        sorted_candidates = sorted(candidates, key=lambda c: c.score, reverse=True)

        # For instruments, prefer tag-format text
        prefs = self._get_class_preferences(detection.class_name)
        if prefs.get("expect_tag", False):
            tag_candidates = [c for c in sorted_candidates if c.is_tag_format]
            if tag_candidates:
                return [tag_candidates[0]]

        # Return best single match
        return [sorted_candidates[0]]

    def _get_class_preferences(self, class_name: str) -> dict:
        """Get search preferences for a class."""
        class_lower = class_name.lower()

        for key, prefs in self.CLASS_PREFERENCES.items():
            if key in class_lower:
                return prefs

        return self.CLASS_PREFERENCES["default"]

    def _determine_direction(
        self,
        symbol_bbox: BoundingBox,
        text_region: TextRegion,
    ) -> AssociationType:
        """Determine spatial relationship between symbol and text."""
        sx, sy = symbol_bbox.center
        tx, ty = text_region.center

        dx = tx - sx
        dy = ty - sy

        # Use angle to determine primary direction
        angle = math.atan2(dy, dx) * 180 / math.pi

        if -45 <= angle < 45:
            return AssociationType.RIGHT
        elif 45 <= angle < 135:
            return AssociationType.BELOW
        elif -135 <= angle < -45:
            return AssociationType.ABOVE
        else:
            return AssociationType.LEFT

    def _calculate_overlap(
        self,
        bbox: BoundingBox,
        region: TextRegion,
    ) -> float:
        """Calculate overlap ratio between bounding box and text region."""
        # Intersection coordinates
        x1 = max(bbox.x1, region.x1)
        y1 = max(bbox.y1, region.y1)
        x2 = min(bbox.x2, region.x2)
        y2 = min(bbox.y2, region.y2)

        if x1 >= x2 or y1 >= y2:
            return 0.0

        intersection = (x2 - x1) * (y2 - y1)
        text_area = region.width * region.height

        if text_area <= 0:
            return 0.0

        return intersection / text_area

    @staticmethod
    def _euclidean_distance(p1: tuple[float, float], p2: tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points."""
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def associate_single(
        self,
        detection: Detection,
        text_blocks: list[TextBlock],
    ) -> Optional[SymbolTextAssociation]:
        """
        Associate text with a single detection.

        Args:
            detection: Single detection
            text_blocks: Available text blocks

        Returns:
            Association or None
        """
        candidates = self._find_candidates(detection, text_blocks, set())

        if not candidates:
            return None

        best = self._select_best_candidates(candidates, detection)

        if not best:
            return None

        association = SymbolTextAssociation(
            detection=detection,
            confidence=best[0].score,
            association_type=best[0].association_type,
            associated_texts=[c.text_block for c in best],
        )

        if best[0].is_tag_format:
            association.tag_number = best[0].text_block.tag_number

        return association

    def find_text_near_point(
        self,
        x: float,
        y: float,
        text_blocks: list[TextBlock],
        max_distance: float = None,
    ) -> list[TextBlock]:
        """Find text blocks near a point."""
        max_dist = max_distance or self.search_radius
        results = []

        for tb in text_blocks:
            dist = self._euclidean_distance((x, y), tb.region.center)
            if dist <= max_dist:
                results.append((tb, dist))

        # Sort by distance
        results.sort(key=lambda x: x[1])
        return [tb for tb, _ in results]

    def visualize(
        self,
        image,
        result: AssociationResult,
        show_lines: bool = True,
    ):
        """
        Visualize associations on image.

        Args:
            image: Input image (numpy array)
            result: Association result
            show_lines: Draw lines connecting symbols and text

        Returns:
            Annotated image
        """
        import cv2

        output = image.copy()

        # Colors
        COLOR_ASSOCIATED = (0, 255, 0)      # Green
        COLOR_UNASSOCIATED = (0, 0, 255)    # Red
        COLOR_TAG = (255, 255, 0)           # Cyan
        COLOR_LINE = (255, 165, 0)          # Orange

        # Draw associated pairs
        for assoc in result.associations:
            bbox = assoc.detection.bbox
            x1, y1, x2, y2 = int(bbox.x1), int(bbox.y1), int(bbox.x2), int(bbox.y2)

            # Symbol box
            color = COLOR_TAG if assoc.tag_number else COLOR_ASSOCIATED
            cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)

            # Draw tag label
            if assoc.tag_number:
                cv2.putText(
                    output, assoc.tag_number,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
                )

            # Draw lines to associated text
            if show_lines:
                sx, sy = int(bbox.center[0]), int(bbox.center[1])
                for tb in assoc.associated_texts:
                    tx, ty = int(tb.region.center[0]), int(tb.region.center[1])
                    cv2.line(output, (sx, sy), (tx, ty), COLOR_LINE, 1)

        # Draw unassociated symbols
        for det in result.unassociated_symbols:
            bbox = det.bbox
            x1, y1, x2, y2 = int(bbox.x1), int(bbox.y1), int(bbox.x2), int(bbox.y2)
            cv2.rectangle(output, (x1, y1), (x2, y2), COLOR_UNASSOCIATED, 2)

        return output
