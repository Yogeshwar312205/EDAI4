"""
Unit Tests for TextNormalizer - ISA S5.1 Pattern Recognition
"""

import unittest
from src.perception.text_normalizer import TextNormalizer


class TestInstrumentTagParsing(unittest.TestCase):
    """Test ISA S5.1 instrument tag parsing."""
    
    def setUp(self):
        self.normalizer = TextNormalizer()
    
    def test_basic_instrument_tags(self):
        """Test basic instrument tag patterns."""
        test_cases = [
            ("FIT-1001", True),
            ("PCV-2030", True),
            ("LT-3500", True),
            ("TAHH-4001", True),
            ("PT-0500", True),
        ]
        
        for tag, should_be_valid in test_cases:
            with self.subTest(tag=tag):
                self.assertEqual(
                    self.normalizer.is_valid_instrument_tag(tag),
                    should_be_valid,
                    f"Tag '{tag}' validation failed"
                )
    
    def test_instrument_tags_with_area(self):
        """Test tags with area prefix."""
        test_cases = [
            ("101-FIT-1001", True),
            ("23-PCV-2030", True),
            ("1-LT-3500", True),
        ]
        
        for tag, should_be_valid in test_cases:
            with self.subTest(tag=tag):
                self.assertTrue(self.normalizer.is_valid_instrument_tag(tag))
    
    def test_instrument_tags_with_suffix(self):
        """Test tags with suffix letters."""
        test_cases = [
            ("FIT-1001A", True),
            ("PCV-2030B", True),
            ("LT-3500C", True),
        ]
        
        for tag, should_be_valid in test_cases:
            with self.subTest(tag=tag):
                self.assertTrue(self.normalizer.is_valid_instrument_tag(tag))
    
    def test_case_insensitive_tags(self):
        """Test that tags work with any case."""
        test_cases = [
            "fit-1001",
            "FIT-1001",
            "Fit-1001",
            "FiT-1001",
        ]
        
        for tag in test_cases:
            with self.subTest(tag=tag):
                self.assertTrue(self.normalizer.is_valid_instrument_tag(tag))
                parsed = self.normalizer.parse_instrument_tag(tag)
                self.assertIsNotNone(parsed)
                self.assertEqual(parsed.normalized, "FIT-1001")
    
    def test_parse_instrument_tag_components(self):
        """Test parsing tag into components."""
        tag = "101-FIT-1001A"
        parsed = self.normalizer.parse_instrument_tag(tag)
        
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.area, "101")
        self.assertEqual(parsed.function, "F")
        self.assertEqual(parsed.modifier, "IT")
        self.assertEqual(parsed.loop_number, "1001")
        self.assertEqual(parsed.suffix, "A")
        self.assertEqual(parsed.tag_type, "instrument")
    
    def test_invalid_instrument_tags(self):
        """Test that invalid tags are rejected."""
        invalid_tags = [
            "P-101",           # Equipment tag
            "FIT",             # No loop number
            "1001",            # Just number
            "FIT-1",           # Loop number too short
            "F-1001",          # Function too short
            "NotATag",         # Random text
        ]
        
        for tag in invalid_tags:
            with self.subTest(tag=tag):
                self.assertFalse(self.normalizer.is_valid_instrument_tag(tag))


class TestEquipmentTagParsing(unittest.TestCase):
    """Test equipment tag parsing."""
    
    def setUp(self):
        self.normalizer = TextNormalizer()
    
    def test_basic_equipment_tags(self):
        """Test basic equipment patterns."""
        test_cases = [
            ("P-101", True),
            ("V-201", True),
            ("HX-301", True),
            ("T-401", True),
            ("C-102", True),
        ]
        
        for tag, should_be_valid in test_cases:
            with self.subTest(tag=tag):
                self.assertEqual(
                    self.normalizer.is_valid_equipment_tag(tag),
                    should_be_valid
                )
    
    def test_equipment_tags_with_suffix(self):
        """Test equipment with suffix."""
        test_cases = [
            "P-101A",
            "V-201B",
            "HX-301C",
        ]
        
        for tag in test_cases:
            with self.subTest(tag=tag):
                self.assertTrue(self.normalizer.is_valid_equipment_tag(tag))
    
    def test_parallel_equipment_tags(self):
        """Test parallel equipment notation."""
        tag = "P-101A/B"
        self.assertTrue(self.normalizer.is_valid_equipment_tag(tag))
        
        parsed = self.normalizer.parse_equipment_tag(tag)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.function, "P")
        self.assertEqual(parsed.loop_number, "101")
        self.assertIn("/", parsed.suffix or "")
    
    def test_parse_equipment_tag(self):
        """Test parsing equipment tag components."""
        tag = "HX-301"
        parsed = self.normalizer.parse_equipment_tag(tag)
        
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.function, "HX")
        self.assertEqual(parsed.loop_number, "301")
        self.assertEqual(parsed.tag_type, "equipment")
    
    def test_equipment_type_lookup(self):
        """Test equipment type description lookup."""
        self.assertEqual(self.normalizer.get_equipment_type("P"), "Pump")
        self.assertEqual(self.normalizer.get_equipment_type("HX"), "Heat Exchanger")
        self.assertEqual(self.normalizer.get_equipment_type("V"), "Vessel")


class TestLineNumberParsing(unittest.TestCase):
    """Test line number parsing."""
    
    def setUp(self):
        self.normalizer = TextNormalizer()
    
    def test_basic_line_numbers(self):
        """Test basic line number patterns."""
        test_cases = [
            ('2"-PW-101', True),
            ('4"-STM-001', True),
            ('6-CS-201', True),
            ("8-AIR-305", True),
        ]
        
        for line_num, should_be_valid in test_cases:
            with self.subTest(line_num=line_num):
                self.assertEqual(
                    self.normalizer.is_valid_line_number(line_num),
                    should_be_valid
                )
    
    def test_line_numbers_with_area(self):
        """Test line numbers with area code."""
        line_num = '2"-PW-101-A1A'
        self.assertTrue(self.normalizer.is_valid_line_number(line_num))
        
        parsed = self.normalizer.parse_line_number(line_num)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.modifier, "2")  # Size
        self.assertEqual(parsed.function, "PW")  # Service
        self.assertEqual(parsed.loop_number, "101")  # Sequence
        self.assertEqual(parsed.area, "A1A")
    
    def test_line_numbers_with_insulation(self):
        """Test line numbers with insulation code."""
        line_num = '4"-STM-001-A1A-N'
        self.assertTrue(self.normalizer.is_valid_line_number(line_num))
        
        parsed = self.normalizer.parse_line_number(line_num)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.suffix, "N")  # Insulation
    
    def test_line_service_lookup(self):
        """Test line service description lookup."""
        self.assertEqual(self.normalizer.get_line_service("PW"), "Process Water")
        self.assertEqual(self.normalizer.get_line_service("STM"), "Steam")
        self.assertEqual(self.normalizer.get_line_service("AIR"), "Instrument Air")


class TestOCRCorrection(unittest.TestCase):
    """Test OCR error correction."""
    
    def setUp(self):
        self.normalizer = TextNormalizer()
    
    def test_numeric_to_letter_correction(self):
        """Test correction of numbers to letters."""
        test_cases = [
            ("F1T-1001", "FIT-1001"),  # 1 → I
            ("P0T-2001", "POT-2001"),  # 0 → O (in function)
        ]
        
        for ocr_text, expected in test_cases:
            with self.subTest(ocr=ocr_text):
                normalized = self.normalizer.normalize_tag(ocr_text)
                self.assertEqual(normalized, expected)
    
    def test_letter_to_numeric_correction(self):
        """Test correction of letters to numbers in loop."""
        # Note: This is context-dependent, normalizer attempts smart correction
        ocr_text = "FIT-IOOI"  # I → 1, O → 0
        normalized = self.normalizer.normalize_tag(ocr_text)
        self.assertIn("1001", normalized)
    
    def test_space_removal(self):
        """Test removal of spaces in tags."""
        test_cases = [
            ("FIT - 1001", "FIT-1001"),
            ("F IT-1001", "FIT-1001"),
            ("FIT-1 001", "FIT-1001"),
        ]
        
        for ocr_text, expected in test_cases:
            with self.subTest(ocr=ocr_text):
                normalized = self.normalizer.normalize_tag(ocr_text)
                self.assertEqual(normalized, expected)


class TestTagExtraction(unittest.TestCase):
    """Test extracting tags from mixed text."""
    
    def setUp(self):
        self.normalizer = TextNormalizer()
    
    def test_extract_single_tag(self):
        """Test extracting a single tag."""
        text = "The flow transmitter FIT-1001 is installed"
        tags = self.normalizer.extract_all_tags(text)
        
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0], "FIT-1001")
    
    def test_extract_multiple_tags(self):
        """Test extracting multiple tags."""
        text = "FIT-1001 feeds PCV-2030A and connects to LT-3500"
        tags = self.normalizer.extract_all_tags(text)
        
        self.assertEqual(len(tags), 3)
        self.assertIn("FIT-1001", tags)
        self.assertIn("PCV-2030A", tags)
        self.assertIn("LT-3500", tags)
    
    def test_extract_mixed_tag_types(self):
        """Test extracting different tag types."""
        text = "Pump P-101 feeds valve PCV-2030 through line 2\"-PW-101"
        tags = self.normalizer.extract_all_tags(text)
        
        # Should extract all types
        self.assertGreater(len(tags), 0)
        self.assertTrue(any("P-101" in tag for tag in tags))
        self.assertTrue(any("PCV-2030" in tag for tag in tags))
    
    def test_no_duplicates(self):
        """Test that duplicate tags are not returned."""
        text = "FIT-1001 and FIT-1001 again FIT-1001"
        tags = self.normalizer.extract_all_tags(text)
        
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0], "FIT-1001")


class TestISAFunctionCodes(unittest.TestCase):
    """Test ISA S5.1 function code lookups."""
    
    def setUp(self):
        self.normalizer = TextNormalizer()
    
    def test_common_function_codes(self):
        """Test common ISA function codes."""
        test_cases = [
            ("FIT", "Flow Indicating Transmitter"),
            ("PCV", "Pressure Control Valve"),
            ("LT", "Level Transmitter"),
            ("TIC", "Temperature Indicating Controller"),
            ("LSHH", "Level Switch High High"),
        ]
        
        for code, expected_desc in test_cases:
            with self.subTest(code=code):
                desc = self.normalizer.get_function_description(code)
                self.assertEqual(desc, expected_desc)
    
    def test_case_insensitive_lookup(self):
        """Test that lookups are case-insensitive."""
        desc1 = self.normalizer.get_function_description("FIT")
        desc2 = self.normalizer.get_function_description("fit")
        desc3 = self.normalizer.get_function_description("Fit")
        
        self.assertEqual(desc1, desc2)
        self.assertEqual(desc2, desc3)


class TestTagTypeIdentification(unittest.TestCase):
    """Test automatic tag type identification."""
    
    def setUp(self):
        self.normalizer = TextNormalizer()
    
    def test_identify_instrument_tags(self):
        """Test identifying instrument tags."""
        tags = ["FIT-1001", "PCV-2030A", "101-LT-3500"]
        
        for tag in tags:
            with self.subTest(tag=tag):
                tag_type = self.normalizer.identify_tag_type(tag)
                self.assertEqual(tag_type, "instrument")
    
    def test_identify_equipment_tags(self):
        """Test identifying equipment tags."""
        tags = ["P-101", "V-201A", "HX-301"]
        
        for tag in tags:
            with self.subTest(tag=tag):
                tag_type = self.normalizer.identify_tag_type(tag)
                self.assertEqual(tag_type, "equipment")
    
    def test_identify_line_numbers(self):
        """Test identifying line numbers."""
        tags = ['2"-PW-101', '4"-STM-001']
        
        for tag in tags:
            with self.subTest(tag=tag):
                tag_type = self.normalizer.identify_tag_type(tag)
                self.assertEqual(tag_type, "line")
    
    def test_identify_unknown(self):
        """Test identifying unknown patterns."""
        tags = ["NotATag", "123", "X-Y-Z"]
        
        for tag in tags:
            with self.subTest(tag=tag):
                tag_type = self.normalizer.identify_tag_type(tag)
                self.assertEqual(tag_type, "unknown")


if __name__ == "__main__":
    unittest.main()
