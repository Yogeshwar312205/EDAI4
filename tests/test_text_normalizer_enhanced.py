"""
Test script for enhanced TextNormalizer with ISA S5.1 patterns
"""

from src.perception.text_normalizer import TextNormalizer

def test_instrument_tags():
    """Test instrument tag recognition."""
    normalizer = TextNormalizer()
    
    test_cases = [
        # (input, expected_valid, expected_normalized)
        ("FIT-1001", True, "FIT-1001"),
        ("101-PCV-2030A", True, "101-PCV-2030A"),
        ("LT-3500", True, "LT-3500"),
        ("TAHH-4001", True, "TAHH-4001"),
        ("fit-1001", True, "FIT-1001"),  # Lowercase
        ("F1T-IO01", True, "FIT-1001"),  # OCR errors
        ("PSV-0500", True, "PSV-0500"),
        ("LSHH-2001", True, "LSHH-2001"),
        ("NotATag", False, None),
        ("P-101", False, None),  # Equipment tag, not instrument
    ]
    
    print("🔍 Testing Instrument Tags (ISA S5.1)")
    print("=" * 60)
    
    for text, should_be_valid, expected in test_cases:
        is_valid = normalizer.is_valid_instrument_tag(text)
        parsed = normalizer.parse_instrument_tag(text)
        
        status = "✅" if is_valid == should_be_valid else "❌"
        print(f"{status} '{text}' -> Valid: {is_valid}")
        
        if parsed:
            print(f"   Area: {parsed.area}, Function: {parsed.function}, "
                  f"Modifier: {parsed.modifier}, Loop: {parsed.loop_number}, Suffix: {parsed.suffix}")
            desc = normalizer.get_function_description(f"{parsed.function}{parsed.modifier or ''}")
            if desc:
                print(f"   Description: {desc}")
    
    print()

def test_equipment_tags():
    """Test equipment tag recognition."""
    normalizer = TextNormalizer()
    
    test_cases = [
        ("P-101", True),
        ("V-201A", True),
        ("HX-301", True),
        ("T-401A/B", True),
        ("C-102", True),
        ("p-101", True),  # Lowercase
        ("FIT-1001", False),  # Instrument tag
    ]
    
    print("🏭 Testing Equipment Tags")
    print("=" * 60)
    
    for text, should_be_valid in test_cases:
        is_valid = normalizer.is_valid_equipment_tag(text)
        parsed = normalizer.parse_equipment_tag(text)
        
        status = "✅" if is_valid == should_be_valid else "❌"
        print(f"{status} '{text}' -> Valid: {is_valid}")
        
        if parsed:
            print(f"   Type: {parsed.function}, Number: {parsed.loop_number}, Suffix: {parsed.suffix}")
            equip_type = normalizer.get_equipment_type(parsed.function)
            if equip_type:
                print(f"   Equipment: {equip_type}")
    
    print()

def test_line_numbers():
    """Test line number recognition."""
    normalizer = TextNormalizer()
    
    test_cases = [
        ('2"-PW-101-A1A-N', True),
        ('4"-STM-001', True),
        ('6-CS-201-P', True),
        ("8-AIR-305", True),
        ("NotALine", False),
    ]
    
    print("🔧 Testing Line Numbers")
    print("=" * 60)
    
    for text, should_be_valid in test_cases:
        is_valid = normalizer.is_valid_line_number(text)
        parsed = normalizer.parse_line_number(text)
        
        status = "✅" if is_valid == should_be_valid else "❌"
        print(f"{status} '{text}' -> Valid: {is_valid}")
        
        if parsed:
            print(f"   Size: {parsed.modifier}, Service: {parsed.function}, "
                  f"Seq: {parsed.loop_number}, Area: {parsed.area}, Insulation: {parsed.suffix}")
            service = normalizer.get_line_service(parsed.function)
            if service:
                print(f"   Service: {service}")
    
    print()

def test_tag_extraction():
    """Test extracting tags from mixed text."""
    normalizer = TextNormalizer()
    
    test_texts = [
        "The flow transmitter FIT-1001 is connected to valve PCV-2030A",
        "Pump P-101 feeds tank V-201A through line 2\"-PW-101",
        "Temperature LT-3500 and pressure PT-3501",
        "LSHH-2001 LSLL-2002",
    ]
    
    print("📝 Testing Tag Extraction from Text")
    print("=" * 60)
    
    for text in test_texts:
        tags = normalizer.extract_all_tags(text)
        print(f"Text: {text}")
        print(f"Found: {tags}")
        print()

def test_ocr_corrections():
    """Test OCR error corrections."""
    normalizer = TextNormalizer()
    
    test_cases = [
        ("F1T-IO01", "FIT-1001"),  # 1→I, O→0
        ("PlT-2OO1", "PIT-2001"),  # l→I, O→0
        ("LT- 3500", "LT-3500"),   # Space removal
    ]
    
    print("🔧 Testing OCR Corrections")
    print("=" * 60)
    
    for ocr_text, expected in test_cases:
        normalized = normalizer.normalize_tag(ocr_text)
        status = "✅" if normalized == expected else "❌"
        print(f"{status} '{ocr_text}' -> '{normalized}' (expected: '{expected}')")
    
    print()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  EDAI4 - TextNormalizer Test Suite")
    print("  ISA S5.1 Pattern Recognition")
    print("=" * 60 + "\n")
    
    test_instrument_tags()
    test_equipment_tags()
    test_line_numbers()
    test_tag_extraction()
    test_ocr_corrections()
    
    print("=" * 60)
    print("✅ Test suite completed!")
    print("=" * 60)
