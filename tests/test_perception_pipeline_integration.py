"""
Integration Tests for PerceptionPipeline
Tests the complete Layer 2 pipeline with mock data
"""

import unittest
import numpy as np
from unittest.mock import Mock, MagicMock, patch

from src.perception.perception_pipeline import (
    PerceptionPipeline,
    PipelineResult,
    InstrumentData,
)
from src.perception.symbol_detector import Detection, DetectionResult, BoundingBox
from src.perception.ocr_engine import OCRResult, TextBlock, TextRegion


class TestPipelineInitialization(unittest.TestCase):
    """Test pipeline initialization."""
    
    def test_pipeline_creates_components(self):
        """Test that pipeline initializes all components."""
        pipeline = PerceptionPipeline()
        
        self.assertIsNotNone(pipeline.symbol_detector)
        self.assertIsNotNone(pipeline.ocr)
        self.assertIsNotNone(pipeline.associator)
        self.assertIsNotNone(pipeline.normalizer)
    
    def test_pipeline_with_custom_config(self):
        """Test pipeline with custom configuration."""
        pipeline = PerceptionPipeline(
            ocr_engine="tesseract",
            confidence_threshold=0.7,
            association_search_radius=200,
        )
        
        self.assertEqual(pipeline.ocr_engine_type, "tesseract")
        self.assertEqual(pipeline.confidence_threshold, 0.7)
        self.assertEqual(pipeline.association_search_radius, 200)


class TestPipelineWithMockData(unittest.TestCase):
    """Test pipeline with mocked detector and OCR."""
    
    def setUp(self):
        """Set up pipeline with mocks."""
        self.pipeline = PerceptionPipeline()
        
        # Mock the detector
        self.pipeline.symbol_detector.detect = Mock()
        
        # Mock the OCR
        self.pipeline.ocr.extract_all_text = Mock()
    
    def test_pipeline_processes_mock_data(self):
        """Test pipeline with mock detection and OCR results."""
        # Create mock image
        image = np.zeros((1000, 1000, 3), dtype=np.uint8)
        
        # Mock detection result
        detection = Detection(
            bbox=BoundingBox(x1=100, y1=100, x2=160, y2=160),
            class_id=0,
            class_name="instrument.bubble",
            confidence=0.95,
        )
        mock_detections = DetectionResult(
            detections=[detection],
            image_width=1000,
            image_height=1000,
        )
        self.pipeline.symbol_detector.detect.return_value = mock_detections
        
        # Mock OCR result
        text_block = TextBlock(
            text="FIT-1001",
            region=TextRegion(x1=170, y1=120, x2=250, y2=140),
            confidence=0.90,
            cleaned_text="FIT-1001",
            is_tag=True,
            tag_number="FIT-1001",
        )
        mock_ocr = OCRResult(
            text_blocks=[text_block],
            image_width=1000,
            image_height=1000,
        )
        self.pipeline.ocr.extract_all_text.return_value = mock_ocr
        
        # Process
        result = self.pipeline.process_image(image)
        
        # Verify calls
        self.pipeline.symbol_detector.detect.assert_called_once()
        self.pipeline.ocr.extract_all_text.assert_called_once()
        
        # Verify result structure
        self.assertIsInstance(result, PipelineResult)
        self.assertEqual(len(result.detections.detections), 1)
        self.assertEqual(len(result.ocr_result.text_blocks), 1)
        self.assertGreater(len(result.associations.associations), 0)
    
    def test_pipeline_selective_processing(self):
        """Test running only specific pipeline stages."""
        image = np.zeros((1000, 1000, 3), dtype=np.uint8)
        
        # Mock returns
        self.pipeline.symbol_detector.detect.return_value = DetectionResult()
        self.pipeline.ocr.extract_all_text.return_value = OCRResult()
        
        # Run detection only
        result = self.pipeline.process_image(
            image,
            run_detection=True,
            run_ocr=False,
            run_association=False,
        )
        
        self.pipeline.symbol_detector.detect.assert_called_once()
        self.pipeline.ocr.extract_all_text.assert_not_called()
    
    def test_pipeline_extracts_instruments(self):
        """Test that pipeline correctly extracts instrument data."""
        image = np.zeros((1000, 1000, 3), dtype=np.uint8)
        
        # Mock detection
        detection = Detection(
            bbox=BoundingBox(x1=100, y1=100, x2=160, y2=160),
            class_id=0,
            class_name="instrument.bubble",
            confidence=0.95,
        )
        mock_detections = DetectionResult(detections=[detection])
        self.pipeline.symbol_detector.detect.return_value = mock_detections
        
        # Mock OCR with instrument tag
        text_block = TextBlock(
            text="FIT-1001",
            region=TextRegion(x1=120, y1=120, x2=150, y2=140),
            confidence=0.90,
            cleaned_text="FIT-1001",
            is_tag=True,
            tag_number="FIT-1001",
        )
        mock_ocr = OCRResult(text_blocks=[text_block])
        self.pipeline.ocr.extract_all_text.return_value = mock_ocr
        
        # Process
        result = self.pipeline.process_image(image)
        
        # Should extract as instrument
        self.assertGreater(len(result.instruments), 0)
        
        inst = result.instruments[0]
        self.assertEqual(inst.tag_number, "FIT-1001")
        self.assertEqual(inst.tag_type, "instrument")
        self.assertIsNotNone(inst.parsed_tag)
        self.assertEqual(inst.parsed_tag.function, "F")
        self.assertEqual(inst.parsed_tag.modifier, "IT")


class TestPipelineDataExtraction(unittest.TestCase):
    """Test structured data extraction from pipeline results."""
    
    def create_mock_result(self):
        """Create a mock pipeline result."""
        # Detection
        detection = Detection(
            bbox=BoundingBox(x1=100, y1=100, x2=160, y2=160),
            class_id=0,
            class_name="instrument.bubble",
            confidence=0.95,
        )
        
        # Text block
        text_block = TextBlock(
            text="FIT-1001",
            region=TextRegion(x1=120, y1=120, x2=150, y2=140),
            confidence=0.90,
            cleaned_text="FIT-1001",
            is_tag=True,
            tag_number="FIT-1001",
        )
        
        # Create result
        result = PipelineResult(
            detections=DetectionResult(detections=[detection]),
            ocr_result=OCRResult(text_blocks=[text_block]),
            associations=Mock(),
        )
        
        # Add instrument data
        from src.perception.text_normalizer import ParsedTag
        result.instruments.append(InstrumentData(
            tag_number="FIT-1001",
            tag_type="instrument",
            symbol_class="instrument.bubble",
            confidence=0.90,
            x=130.0,
            y=130.0,
            bbox=(100, 100, 160, 160),
            parsed_tag=ParsedTag(
                raw_text="FIT-1001",
                normalized="FIT-1001",
                function="F",
                modifier="IT",
                loop_number="1001",
                tag_type="instrument",
            ),
        ))
        
        return result
    
    def test_get_all_tags(self):
        """Test extracting all tag numbers."""
        result = self.create_mock_result()
        
        tags = result.get_all_tags()
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0], "FIT-1001")
    
    def test_get_by_class(self):
        """Test filtering by symbol class."""
        result = self.create_mock_result()
        
        bubbles = result.get_by_class("instrument.bubble")
        self.assertEqual(len(bubbles), 1)
        self.assertEqual(bubbles[0].symbol_class, "instrument.bubble")
    
    def test_summary_generation(self):
        """Test result summary generation."""
        result = self.create_mock_result()
        
        summary = result.summary()
        self.assertIn("Instruments:", summary)
        self.assertIn("Processing Time:", summary)


class TestPipelineExport(unittest.TestCase):
    """Test pipeline data export functionality."""
    
    def setUp(self):
        self.pipeline = PerceptionPipeline()
    
    def create_mock_result(self):
        """Create a mock result for export testing."""
        from src.perception.text_normalizer import ParsedTag
        
        result = PipelineResult(
            detections=DetectionResult(),
            ocr_result=OCRResult(),
            associations=Mock(),
            processing_time_ms=1500.0,
        )
        
        result.instruments.append(InstrumentData(
            tag_number="FIT-1001",
            tag_type="instrument",
            symbol_class="instrument.bubble",
            confidence=0.90,
            x=130.0,
            y=130.0,
            bbox=(100, 100, 160, 160),
            detection_confidence=0.95,
            association_confidence=0.90,
            parsed_tag=ParsedTag(
                raw_text="FIT-1001",
                normalized="FIT-1001",
                area=None,
                function="F",
                modifier="IT",
                loop_number="1001",
                suffix=None,
                tag_type="instrument",
            ),
        ))
        
        return result
    
    def test_export_to_dict_structure(self):
        """Test export to dictionary format."""
        result = self.create_mock_result()
        data = self.pipeline.export_to_dict(result)
        
        # Verify structure
        self.assertIn("summary", data)
        self.assertIn("instruments", data)
        self.assertIn("equipment", data)
        self.assertIn("lines", data)
        
        # Verify summary
        self.assertEqual(data["summary"]["total_instruments"], 1)
        self.assertEqual(data["summary"]["processing_time_ms"], 1500.0)
        
        # Verify instrument data
        self.assertEqual(len(data["instruments"]), 1)
        inst = data["instruments"][0]
        self.assertEqual(inst["tag_number"], "FIT-1001")
        self.assertEqual(inst["type"], "instrument")
        self.assertIn("position", inst)
        self.assertIn("parsed", inst)
    
    def test_export_parsed_tag_data(self):
        """Test that parsed tag data is exported correctly."""
        result = self.create_mock_result()
        data = self.pipeline.export_to_dict(result)
        
        inst = data["instruments"][0]
        parsed = inst["parsed"]
        
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["function"], "F")
        self.assertEqual(parsed["modifier"], "IT")
        self.assertEqual(parsed["loop_number"], "1001")
    
    def test_export_confidence_scores(self):
        """Test that confidence scores are exported."""
        result = self.create_mock_result()
        data = self.pipeline.export_to_dict(result)
        
        inst = data["instruments"][0]
        confidence = inst["confidence"]
        
        self.assertEqual(confidence["detection"], 0.95)
        self.assertEqual(confidence["association"], 0.90)


class TestBatchProcessing(unittest.TestCase):
    """Test batch processing functionality."""
    
    def setUp(self):
        self.pipeline = PerceptionPipeline()
        
        # Mock the process_image method
        self.pipeline.process_image = Mock(return_value=PipelineResult(
            detections=DetectionResult(),
            ocr_result=OCRResult(),
            associations=Mock(),
        ))
    
    def test_process_batch(self):
        """Test processing multiple images."""
        images = [
            np.zeros((1000, 1000, 3), dtype=np.uint8),
            np.zeros((1200, 800, 3), dtype=np.uint8),
            np.zeros((800, 1200, 3), dtype=np.uint8),
        ]
        
        results = self.pipeline.process_batch(images)
        
        self.assertEqual(len(results), 3)
        self.assertEqual(self.pipeline.process_image.call_count, 3)


if __name__ == "__main__":
    unittest.main()
