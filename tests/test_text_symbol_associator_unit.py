"""
Unit Tests for TextSymbolAssociator - Spatial Association Logic
"""

import unittest
import math
from src.perception.text_symbol_associator import (
    TextSymbolAssociator,
    AssociationType,
)
from src.perception.symbol_detector import BoundingBox, Detection, DetectionResult
from src.perception.ocr_engine import TextRegion, TextBlock, OCRResult


class TestSpatialCalculations(unittest.TestCase):
    """Test spatial calculation utilities."""
    
    def setUp(self):
        self.associator = TextSymbolAssociator()
    
    def test_euclidean_distance(self):
        """Test distance calculation."""
        p1 = (0.0, 0.0)
        p2 = (3.0, 4.0)
        
        distance = self.associator._euclidean_distance(p1, p2)
        self.assertAlmostEqual(distance, 5.0)
    
    def test_overlap_calculation_full(self):
        """Test 100% overlap."""
        bbox = BoundingBox(x1=100, y1=100, x2=200, y2=150)
        region = TextRegion(x1=100, y1=100, x2=200, y2=150)
        
        overlap = self.associator._calculate_overlap(bbox, region)
        self.assertAlmostEqual(overlap, 1.0)
    
    def test_overlap_calculation_partial(self):
        """Test partial overlap."""
        bbox = BoundingBox(x1=100, y1=100, x2=200, y2=200)
        region = TextRegion(x1=150, y1=150, x2=250, y2=250)
        
        overlap = self.associator._calculate_overlap(bbox, region)
        self.assertGreater(overlap, 0.0)
        self.assertLess(overlap, 1.0)
    
    def test_overlap_calculation_none(self):
        """Test no overlap."""
        bbox = BoundingBox(x1=100, y1=100, x2=200, y2=200)
        region = TextRegion(x1=300, y1=300, x2=400, y2=400)
        
        overlap = self.associator._calculate_overlap(bbox, region)
        self.assertEqual(overlap, 0.0)


class TestDirectionDetermination(unittest.TestCase):
    """Test spatial direction determination."""
    
    def setUp(self):
        self.associator = TextSymbolAssociator()
    
    def test_direction_right(self):
        """Test text to the right of symbol."""
        symbol_bbox = BoundingBox(x1=100, y1=100, x2=150, y2=150)
        text_region = TextRegion(x1=200, y1=120, x2=250, y2=140)
        
        direction = self.associator._determine_direction(symbol_bbox, text_region)
        self.assertEqual(direction, AssociationType.RIGHT)
    
    def test_direction_left(self):
        """Test text to the left of symbol."""
        symbol_bbox = BoundingBox(x1=200, y1=100, x2=250, y2=150)
        text_region = TextRegion(x1=50, y1=120, x2=100, y2=140)
        
        direction = self.associator._determine_direction(symbol_bbox, text_region)
        self.assertEqual(direction, AssociationType.LEFT)
    
    def test_direction_above(self):
        """Test text above symbol."""
        symbol_bbox = BoundingBox(x1=100, y1=200, x2=150, y2=250)
        text_region = TextRegion(x1=110, y1=50, x2=140, y2=80)
        
        direction = self.associator._determine_direction(symbol_bbox, text_region)
        self.assertEqual(direction, AssociationType.ABOVE)
    
    def test_direction_below(self):
        """Test text below symbol."""
        symbol_bbox = BoundingBox(x1=100, y1=100, x2=150, y2=150)
        text_region = TextRegion(x1=110, y1=200, x2=140, y2=230)
        
        direction = self.associator._determine_direction(symbol_bbox, text_region)
        self.assertEqual(direction, AssociationType.BELOW)


class TestAssociationScoring(unittest.TestCase):
    """Test association confidence scoring."""
    
    def setUp(self):
        self.associator = TextSymbolAssociator()
    
    def test_score_inside_high(self):
        """Test that inside associations score high."""
        prefs = {"prefer_inside": True, "expect_tag": True}
        
        score = self.associator._calculate_score(
            distance=0.0,
            overlap=0.8,
            assoc_type=AssociationType.INSIDE,
            is_tag=True,
            prefs=prefs,
            search_radius=150,
        )
        
        self.assertGreater(score, 0.8)
    
    def test_score_tag_bonus(self):
        """Test that valid tags get bonus."""
        prefs = {"prefer_inside": False, "expect_tag": True}
        
        score_with_tag = self.associator._calculate_score(
            distance=50.0,
            overlap=0.0,
            assoc_type=AssociationType.RIGHT,
            is_tag=True,
            prefs=prefs,
            search_radius=150,
        )
        
        score_without_tag = self.associator._calculate_score(
            distance=50.0,
            overlap=0.0,
            assoc_type=AssociationType.RIGHT,
            is_tag=False,
            prefs=prefs,
            search_radius=150,
        )
        
        self.assertGreater(score_with_tag, score_without_tag)
    
    def test_score_distance_penalty(self):
        """Test that farther text scores lower."""
        prefs = {"prefer_inside": False, "expect_tag": False}
        
        score_near = self.associator._calculate_score(
            distance=20.0,
            overlap=0.0,
            assoc_type=AssociationType.RIGHT,
            is_tag=False,
            prefs=prefs,
            search_radius=150,
        )
        
        score_far = self.associator._calculate_score(
            distance=140.0,
            overlap=0.0,
            assoc_type=AssociationType.RIGHT,
            is_tag=False,
            prefs=prefs,
            search_radius=150,
        )
        
        self.assertGreater(score_near, score_far)


class TestClassPreferences(unittest.TestCase):
    """Test class-specific search preferences."""
    
    def setUp(self):
        self.associator = TextSymbolAssociator()
    
    def test_bubble_preferences(self):
        """Test instrument.bubble preferences."""
        prefs = self.associator._get_class_preferences("instrument.bubble")
        
        self.assertTrue(prefs["prefer_inside"])
        self.assertTrue(prefs["expect_tag"])
        self.assertLess(prefs["search_radius"], 150)  # Smaller radius for bubbles
    
    def test_valve_preferences(self):
        """Test valve preferences."""
        prefs = self.associator._get_class_preferences("valve.control")
        
        self.assertFalse(prefs["prefer_inside"])
        self.assertTrue(prefs["expect_tag"])
    
    def test_equipment_preferences(self):
        """Test equipment preferences."""
        prefs = self.associator._get_class_preferences("equipment.pump")
        
        self.assertFalse(prefs["prefer_inside"])
        self.assertGreater(prefs["search_radius"], 150)  # Larger radius for equipment


class TestBasicAssociation(unittest.TestCase):
    """Test basic association scenarios."""
    
    def setUp(self):
        self.associator = TextSymbolAssociator()
    
    def create_detection(self, x, y, width, height, class_name):
        """Helper to create a detection."""
        return Detection(
            bbox=BoundingBox(x1=x, y1=y, x2=x+width, y2=y+height),
            class_id=0,
            class_name=class_name,
            confidence=0.95,
        )
    
    def create_text_block(self, x, y, width, height, text):
        """Helper to create a text block."""
        return TextBlock(
            text=text,
            region=TextRegion(x1=x, y1=y, x2=x+width, y2=y+height),
            confidence=0.90,
            cleaned_text=text,
        )
    
    def test_simple_association(self):
        """Test simple one-to-one association."""
        # Create a symbol at (100, 100)
        detection = self.create_detection(100, 100, 60, 60, "instrument.bubble")
        detections = DetectionResult(detections=[detection])
        
        # Create text near symbol
        text_block = self.create_text_block(170, 120, 80, 20, "FIT-1001")
        text_block.is_tag = True
        text_block.tag_number = "FIT-1001"
        ocr_result = OCRResult(text_blocks=[text_block])
        
        # Associate
        result = self.associator.associate(detections, ocr_result)
        
        # Should have one association
        self.assertEqual(len(result.associations), 1)
        self.assertEqual(result.associations[0].tag_number, "FIT-1001")
        self.assertGreater(result.associations[0].confidence, 0.3)
    
    def test_inside_bubble_association(self):
        """Test text inside instrument bubble."""
        # Create a bubble
        detection = self.create_detection(100, 100, 80, 80, "instrument.bubble")
        detections = DetectionResult(detections=[detection])
        
        # Create text INSIDE bubble
        text_block = self.create_text_block(120, 120, 40, 20, "FIT-1001")
        text_block.is_tag = True
        text_block.tag_number = "FIT-1001"
        ocr_result = OCRResult(text_blocks=[text_block])
        
        # Associate
        result = self.associator.associate(detections, ocr_result)
        
        # Should have high confidence INSIDE association
        self.assertEqual(len(result.associations), 1)
        assoc = result.associations[0]
        self.assertEqual(assoc.tag_number, "FIT-1001")
        self.assertEqual(assoc.association_type, AssociationType.INSIDE)
        self.assertGreater(assoc.confidence, 0.7)
    
    def test_too_far_no_association(self):
        """Test that distant text is not associated."""
        # Create a symbol
        detection = self.create_detection(100, 100, 60, 60, "instrument.bubble")
        detections = DetectionResult(detections=[detection])
        
        # Create text very far away
        text_block = self.create_text_block(500, 500, 80, 20, "FIT-1001")
        ocr_result = OCRResult(text_blocks=[text_block])
        
        # Associate
        result = self.associator.associate(detections, ocr_result)
        
        # Should have no associations
        self.assertEqual(len(result.associations), 0)
        self.assertEqual(len(result.unassociated_symbols), 1)
        self.assertEqual(len(result.unassociated_texts), 1)
    
    def test_multiple_symbols_multiple_texts(self):
        """Test associating multiple symbols with multiple texts."""
        # Create two symbols
        det1 = self.create_detection(100, 100, 60, 60, "instrument.bubble")
        det2 = self.create_detection(300, 300, 60, 60, "instrument.bubble")
        detections = DetectionResult(detections=[det1, det2])
        
        # Create two texts, each near one symbol
        text1 = self.create_text_block(170, 120, 80, 20, "FIT-1001")
        text1.is_tag = True
        text1.tag_number = "FIT-1001"
        
        text2 = self.create_text_block(370, 320, 80, 20, "PT-2001")
        text2.is_tag = True
        text2.tag_number = "PT-2001"
        
        ocr_result = OCRResult(text_blocks=[text1, text2])
        
        # Associate
        result = self.associator.associate(detections, ocr_result)
        
        # Should have two associations
        self.assertEqual(len(result.associations), 2)
        tags = [a.tag_number for a in result.associations]
        self.assertIn("FIT-1001", tags)
        self.assertIn("PT-2001", tags)
    
    def test_conflict_resolution(self):
        """Test that closest symbol wins when text is equidistant."""
        # Create two symbols relatively close
        det1 = self.create_detection(100, 100, 60, 60, "instrument.bubble")
        det2 = self.create_detection(200, 100, 60, 60, "instrument.bubble")
        detections = DetectionResult(detections=[det1, det2])
        
        # Create one text between them but closer to det1
        text = self.create_text_block(165, 120, 80, 20, "FIT-1001")
        text.is_tag = True
        text.tag_number = "FIT-1001"
        ocr_result = OCRResult(text_blocks=[text])
        
        # Associate
        result = self.associator.associate(detections, ocr_result)
        
        # Should have one association and one unassociated
        self.assertEqual(len(result.associations), 1)
        self.assertEqual(len(result.unassociated_symbols), 1)


class TestFindTextNearPoint(unittest.TestCase):
    """Test finding text near a specific point."""
    
    def setUp(self):
        self.associator = TextSymbolAssociator()
    
    def create_text_block(self, x, y, width, height, text):
        """Helper to create a text block."""
        return TextBlock(
            text=text,
            region=TextRegion(x1=x, y1=y, x2=x+width, y2=y+height),
            confidence=0.90,
        )
    
    def test_find_text_near_point(self):
        """Test finding text blocks near a point."""
        # Create several text blocks at different distances
        text_blocks = [
            self.create_text_block(100, 100, 50, 20, "Text1"),  # Close
            self.create_text_block(200, 200, 50, 20, "Text2"),  # Medium
            self.create_text_block(500, 500, 50, 20, "Text3"),  # Far
        ]
        
        # Find text near (120, 120) within 100px
        found = self.associator.find_text_near_point(
            120, 120, text_blocks, max_distance=100
        )
        
        # Should find Text1 only
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].text, "Text1")
    
    def test_find_text_sorted_by_distance(self):
        """Test that results are sorted by distance."""
        text_blocks = [
            self.create_text_block(150, 150, 50, 20, "Far"),
            self.create_text_block(105, 105, 50, 20, "Close"),
            self.create_text_block(130, 130, 50, 20, "Medium"),
        ]
        
        found = self.associator.find_text_near_point(
            100, 100, text_blocks, max_distance=100
        )
        
        # Should be sorted by distance (closest first)
        self.assertEqual(len(found), 3)
        self.assertEqual(found[0].text, "Close")
        self.assertEqual(found[1].text, "Medium")
        self.assertEqual(found[2].text, "Far")


if __name__ == "__main__":
    unittest.main()
