"""
EDAI4 - Text Normalizer
Cleans and normalizes OCR output for P&ID drawings

Supports:
- ISA S5.1 Instrument Tag Numbers
- Equipment Tag Numbers
- Line Numbers (ASME/ISO standards)
- Engineering abbreviations and units
"""

import re
from typing import Optional, Literal
from dataclasses import dataclass

from src.utils import get_logger

logger = get_logger(__name__)


@dataclass
class ParsedTag:
    """Parsed instrument tag components."""
    raw_text: str
    normalized: str
    area: Optional[str] = None           # Plant area/unit (e.g., "101")
    function: Optional[str] = None       # First letter (F, P, L, T, etc.)
    modifier: Optional[str] = None       # Modifier letters (I, C, V, etc.)
    loop_number: Optional[str] = None    # Loop number (1001, 2030, etc.)
    suffix: Optional[str] = None         # Suffix letter (A, B, C, etc.)
    tag_type: Literal["instrument", "equipment", "line", "unknown"] = "unknown"


class TextNormalizer:
    """
    Normalizes and cleans OCR output from P&ID drawings.
    Implements ISA S5.1 standard for instrument identification.
    """

    # Common OCR character substitutions
    OCR_CORRECTIONS = {
        "0": "O",  # Zero to O (context-dependent)
        "1": "I",  # One to I (context-dependent)
        "|": "I",  # Pipe to I
        "l": "I",  # Lowercase L to I (in tags)
        "!": "I",  # Exclamation to I
        "$": "S",  # Dollar to S
        "@": "A",  # At to A
        "¢": "C",  # Cent to C
        "€": "E",  # Euro to E
    }

    # ========================================
    # ISA S5.1 Instrument Tag Patterns
    # ========================================
    
    # Comprehensive instrument tag pattern
    # Format: [Area-]FunctionModifier-LoopNumber[Suffix]
    # Examples: FIT-1001, 101-PCV-2030A, LT-3500, TAHH-4001
    INSTRUMENT_TAG_PATTERN = re.compile(
        r"^(?:(\d{1,3})-)?([A-Z]{2,6})-?(\d{3,5})([A-Z])?$",
        re.IGNORECASE
    )

    # Looser extraction pattern for finding tags in text
    INSTRUMENT_TAG_EXTRACTION = re.compile(
        r"(?:\d{1,3}-)?[A-Z]{2,6}-?\d{3,5}[A-Z]?",
        re.IGNORECASE
    )

    # ========================================
    # Equipment Tag Patterns
    # ========================================
    
    # Equipment tags: P-101, V-201A, HX-301, T-401A/B
    EQUIPMENT_TAG_PATTERN = re.compile(
        r"^([A-Z]{1,3})-(\d{2,4})([A-Z])?(?:/([A-Z]))?$",
        re.IGNORECASE
    )

    # Equipment extraction pattern
    EQUIPMENT_TAG_EXTRACTION = re.compile(
        r"[A-Z]{1,3}-\d{2,4}[A-Z]?(?:/[A-Z])?",
        re.IGNORECASE
    )

    # ========================================
    # Line Number Patterns (ASME/ISO)
    # ========================================
    
    # Line numbers: 2"-PW-101-A1A-N, 4"-STM-001, 6-CS-201-P
    LINE_NUMBER_PATTERN = re.compile(
        r'^(?:(\d{1,2}(?:\.\d)?)["\']?-)?'        # Size (2", 4", 6.5")
        r'([A-Z]{2,4})-'                          # Service code (PW, STM, CS)
        r'(\d{2,4})'                              # Sequence number
        r'(?:-([A-Z0-9]{1,4}))?'                  # Area/section
        r'(?:-([A-Z]))?$',                        # Insulation code
        re.IGNORECASE
    )

    # Line extraction pattern
    LINE_NUMBER_EXTRACTION = re.compile(
        r'\d{1,2}(?:\.\d)?["\']?-[A-Z]{2,4}-\d{2,4}(?:-[A-Z0-9]{1,4})?(?:-[A-Z])?',
        re.IGNORECASE
    )

    # ========================================
    # ISA S5.1 Function Letters
    # ========================================
    
    # First letter (measured variable)
    ISA_FIRST_LETTERS = {
        'A': 'Analysis',
        'B': 'Burner/Combustion',
        'C': 'Conductivity',
        'D': 'Density/Specific Gravity',
        'E': 'Voltage',
        'F': 'Flow',
        'G': 'Gauging',
        'H': 'Hand (Manual)',
        'I': 'Current',
        'J': 'Power',
        'K': 'Time/Schedule',
        'L': 'Level',
        'M': 'Moisture',
        'N': 'User Defined',
        'O': 'User Defined',
        'P': 'Pressure',
        'Q': 'Quantity',
        'R': 'Radiation',
        'S': 'Speed/Frequency',
        'T': 'Temperature',
        'U': 'Multivariable',
        'V': 'Vibration',
        'W': 'Weight/Force',
        'X': 'Unclassified',
        'Y': 'Event/State',
        'Z': 'Position/Dimension',
    }

    # Common function code combinations
    ISA_FUNCTION_CODES = {
        'FIT': 'Flow Indicating Transmitter',
        'FT': 'Flow Transmitter',
        'FI': 'Flow Indicator',
        'FIC': 'Flow Indicating Controller',
        'FCV': 'Flow Control Valve',
        'PIT': 'Pressure Indicating Transmitter',
        'PT': 'Pressure Transmitter',
        'PI': 'Pressure Indicator',
        'PIC': 'Pressure Indicating Controller',
        'PCV': 'Pressure Control Valve',
        'PSV': 'Pressure Safety Valve',
        'PSVH': 'Pressure Safety Valve High',
        'LIT': 'Level Indicating Transmitter',
        'LT': 'Level Transmitter',
        'LI': 'Level Indicator',
        'LIC': 'Level Indicating Controller',
        'LCV': 'Level Control Valve',
        'LSH': 'Level Switch High',
        'LSL': 'Level Switch Low',
        'LSHH': 'Level Switch High High',
        'LSLL': 'Level Switch Low Low',
        'TIT': 'Temperature Indicating Transmitter',
        'TT': 'Temperature Transmitter',
        'TI': 'Temperature Indicator',
        'TIC': 'Temperature Indicating Controller',
        'TCV': 'Temperature Control Valve',
        'TSH': 'Temperature Switch High',
        'TSL': 'Temperature Switch Low',
        'TAH': 'Temperature Alarm High',
        'TAL': 'Temperature Alarm Low',
        'TAHH': 'Temperature Alarm High High',
        'TALL': 'Temperature Alarm Low Low',
        'AIT': 'Analysis Indicating Transmitter',
        'AT': 'Analysis Transmitter',
        'AI': 'Analysis Indicator',
        'HS': 'Hand Switch',
        'HV': 'Hand Valve',
        'XV': 'Solenoid Valve',
        'ZSC': 'Position Switch Closed',
        'ZSO': 'Position Switch Open',
    }

    # Equipment type codes
    EQUIPMENT_TYPE_CODES = {
        'P': 'Pump',
        'C': 'Compressor',
        'V': 'Vessel',
        'T': 'Tank',
        'R': 'Reactor',
        'HX': 'Heat Exchanger',
        'E': 'Heat Exchanger',
        'K': 'Package Unit',
        'M': 'Motor',
        'G': 'Generator',
        'TK': 'Tank',
        'F': 'Filter',
        'S': 'Separator',
        'D': 'Dryer',
    }

    # Line service codes
    LINE_SERVICE_CODES = {
        'PW': 'Process Water',
        'CW': 'Cooling Water',
        'STM': 'Steam',
        'CS': 'Condensate',
        'AIR': 'Instrument Air',
        'PA': 'Plant Air',
        'NG': 'Natural Gas',
        'FG': 'Fuel Gas',
        'FO': 'Fuel Oil',
        'WW': 'Waste Water',
        'N2': 'Nitrogen',
        'SW': 'Sea Water',
    }

    def __init__(self):
        """Initialize text normalizer."""
        logger.debug("TextNormalizer initialized")

    def clean_ocr_output(self, text: str) -> str:
        """
        Clean and normalize OCR output.

        Args:
            text: Raw OCR text

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Strip whitespace
        text = text.strip()

        # Remove non-printable characters
        text = "".join(c for c in text if c.isprintable())

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove common OCR artifacts
        text = text.replace("'", "")
        text = text.replace('"', "")
        text = text.replace("`", "")

        # Fix common dash issues
        text = re.sub(r"[–—−]", "-", text)  # Various dashes to hyphen

        return text

    def normalize_tag(self, text: str) -> str:
        """
        Normalize a potential instrument tag.

        Args:
            text: Text that might be a tag

        Returns:
            Normalized tag or original text
        """
        if not text:
            return ""

        # Uppercase
        normalized = text.upper().strip()

        # Remove spaces
        normalized = normalized.replace(" ", "")

        # Fix common OCR errors in tag context
        # Numbers should stay as numbers, letters as letters based on position

        # If it looks like a tag pattern, apply smart corrections
        if re.match(r"^[A-Z0-9\-]+$", normalized):
            # The first few characters should be letters
            parts = re.split(r"[-]", normalized)
            corrected_parts = []

            for i, part in enumerate(parts):
                if i == 0 or (len(parts) > 2 and i == 1):
                    # This should be letters (tag prefix or area)
                    corrected = self._correct_to_letters(part)
                else:
                    # This could be numbers (loop number)
                    if part.isdigit() or re.match(r"^\d+[A-Z]?$", part):
                        corrected = part
                    else:
                        corrected = self._correct_to_numbers(part)

                corrected_parts.append(corrected)

            normalized = "-".join(corrected_parts)

        return normalized

    def _correct_to_letters(self, text: str) -> str:
        """Correct text that should be letters."""
        corrections = {
            "0": "O",
            "1": "I",
            "5": "S",
            "8": "B",
        }
        result = ""
        for c in text:
            result += corrections.get(c, c.upper())
        return result

    def _correct_to_numbers(self, text: str) -> str:
        """Correct text that should be numbers (with optional suffix letter)."""
        corrections = {
            "O": "0",
            "I": "1",
            "l": "1",
            "S": "5",
            "B": "8",
            "Z": "2",
        }
        result = ""
        for i, c in enumerate(text):
            # Last character might be a suffix letter
            if i == len(text) - 1 and c.isalpha():
                result += c.upper()
            else:
                result += corrections.get(c, c)
        return result

    # ========================================
    # Numeric and Unit Extraction
    # ========================================

    def extract_numeric_value(self, text: str) -> Optional[float]:
        """
        Extract numeric value from text (e.g., setpoints).

        Args:
            text: Text containing a number

        Returns:
            Extracted number or None
        """
        if not text:
            return None

        # Pattern for numbers with optional decimal and units
        pattern = r"[-+]?\d*\.?\d+"
        match = re.search(pattern, text)

        if match:
            try:
                return float(match.group())
            except ValueError:
                pass

        return None

    def extract_unit(self, text: str) -> Optional[str]:
        """
        Extract engineering unit from text.

        Args:
            text: Text containing unit

        Returns:
            Extracted unit or None
        """
        # Common engineering units
        unit_patterns = [
            r"(bar[g]?)",
            r"(psi[ga]?)",
            r"(kPa)",
            r"(MPa)",
            r"(°[CF])",
            r"(deg[CF])",
            r"(m3/h)",
            r"(m³/h)",
            r"(kg/h)",
            r"(l/min)",
            r"(gpm)",
            r"(%)",
            r"(mm)",
            r"(m)",
            r"(mA)",
            r"(VDC)",
            r"(VAC)",
        ]

        for pattern in unit_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def normalize_engineering_text(self, text: str) -> str:
        """
        Normalize engineering-specific text (descriptions, notes).

        Args:
            text: Engineering text

        Returns:
            Normalized text
        """
        # Clean basic OCR issues
        text = self.clean_ocr_output(text)

        # Standardize common abbreviations
        abbreviations = {
            r"\bPRESS\b": "PRESSURE",
            r"\bTEMP\b": "TEMPERATURE",
            r"\bLVL\b": "LEVEL",
            r"\bFLW\b": "FLOW",
            r"\bXMTR\b": "TRANSMITTER",
            r"\bINDIC\b": "INDICATOR",
            r"\bCTRL\b": "CONTROLLER",
            r"\bVLV\b": "VALVE",
        }

        for pattern, replacement in abbreviations.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text

    def split_combined_text(self, text: str) -> list[str]:
        """
        Split text that may contain multiple items.

        Args:
            text: Text with multiple items

        Returns:
            List of individual items
        """
        if not text:
            return []

        # Split on common delimiters
        parts = re.split(r"[,;/|]|\s{2,}", text)

        return [p.strip() for p in parts if p.strip()]

    # ========================================
    # Enhanced Pattern Recognition (ISA S5.1)
    # ========================================

    def parse_instrument_tag(self, text: str) -> Optional[ParsedTag]:
        """
        Parse instrument tag into components per ISA S5.1.

        Args:
            text: Tag text (e.g., "101-FIT-1001A")

        Returns:
            ParsedTag with components or None
        """
        normalized = self.normalize_tag(text)
        match = self.INSTRUMENT_TAG_PATTERN.match(normalized)

        if not match:
            return None

        area, function_code, loop_num, suffix = match.groups()

        # Parse function code into first letter + modifiers
        function = function_code[0] if function_code else None
        modifier = function_code[1:] if len(function_code) > 1 else None

        return ParsedTag(
            raw_text=text,
            normalized=normalized,
            area=area,
            function=function,
            modifier=modifier,
            loop_number=loop_num,
            suffix=suffix,
            tag_type="instrument"
        )

    def parse_equipment_tag(self, text: str) -> Optional[ParsedTag]:
        """
        Parse equipment tag (e.g., "P-101A", "HX-301").

        Args:
            text: Equipment tag text

        Returns:
            ParsedTag with components or None
        """
        normalized = text.upper().strip().replace(" ", "")
        match = self.EQUIPMENT_TAG_PATTERN.match(normalized)

        if not match:
            return None

        equip_type, number, suffix, parallel_suffix = match.groups()

        full_suffix = suffix
        if parallel_suffix:
            full_suffix = f"{suffix or ''}/{parallel_suffix}"

        return ParsedTag(
            raw_text=text,
            normalized=normalized,
            function=equip_type,
            loop_number=number,
            suffix=full_suffix,
            tag_type="equipment"
        )

    def parse_line_number(self, text: str) -> Optional[ParsedTag]:
        """
        Parse line number (e.g., '2"-PW-101-A1A-N').

        Args:
            text: Line number text

        Returns:
            ParsedTag with components or None
        """
        normalized = text.upper().strip()
        match = self.LINE_NUMBER_PATTERN.match(normalized)

        if not match:
            return None

        size, service, seq, area, insulation = match.groups()

        return ParsedTag(
            raw_text=text,
            normalized=normalized,
            area=area,
            function=service,  # Service code
            loop_number=seq,
            modifier=size,     # Line size
            suffix=insulation,
            tag_type="line"
        )

    def identify_tag_type(self, text: str) -> Literal["instrument", "equipment", "line", "unknown"]:
        """
        Identify what type of tag this is.

        Args:
            text: Tag text

        Returns:
            Tag type classification
        """
        if self.INSTRUMENT_TAG_PATTERN.match(self.normalize_tag(text)):
            return "instrument"
        
        normalized = text.upper().strip()
        if self.EQUIPMENT_TAG_PATTERN.match(normalized):
            return "equipment"
        
        if self.LINE_NUMBER_PATTERN.match(normalized):
            return "line"
        
        return "unknown"

    def is_valid_instrument_tag(self, text: str) -> bool:
        """Check if text is a valid ISA S5.1 instrument tag."""
        if not text:
            return False
        normalized = self.normalize_tag(text)
        return bool(self.INSTRUMENT_TAG_PATTERN.match(normalized))

    def is_valid_equipment_tag(self, text: str) -> bool:
        """Check if text is a valid equipment tag."""
        if not text:
            return False
        normalized = text.upper().strip()
        return bool(self.EQUIPMENT_TAG_PATTERN.match(normalized))

    def is_valid_line_number(self, text: str) -> bool:
        """Check if text is a valid line number."""
        if not text:
            return False
        normalized = text.upper().strip()
        return bool(self.LINE_NUMBER_PATTERN.match(normalized))

    def is_valid_tag(self, text: str) -> bool:
        """
        Check if text is ANY valid tag (instrument, equipment, or line).
        
        Override of original method to support all tag types.
        """
        return (
            self.is_valid_instrument_tag(text) or
            self.is_valid_equipment_tag(text) or
            self.is_valid_line_number(text)
        )

    def extract_tag_number(self, text: str) -> Optional[str]:
        """
        Extract ANY tag number from text (instrument, equipment, or line).

        Override of original method to support all tag types.

        Args:
            text: Text that might contain a tag

        Returns:
            Extracted tag or None
        """
        if not text:
            return None

        # Try instrument tag first (most common)
        normalized = self.normalize_tag(text)
        if self.INSTRUMENT_TAG_PATTERN.match(normalized):
            return normalized

        # Try equipment tag
        normalized_upper = text.upper().strip().replace(" ", "")
        if self.EQUIPMENT_TAG_PATTERN.match(normalized_upper):
            return normalized_upper

        # Try line number
        if self.LINE_NUMBER_PATTERN.match(normalized_upper):
            return normalized_upper

        # Try extraction patterns
        # Instrument tags
        matches = self.INSTRUMENT_TAG_EXTRACTION.findall(text)
        for match in matches:
            normalized_match = self.normalize_tag(match)
            if self.INSTRUMENT_TAG_PATTERN.match(normalized_match):
                return normalized_match

        # Equipment tags
        matches = self.EQUIPMENT_TAG_EXTRACTION.findall(text)
        for match in matches:
            normalized_match = match.upper().strip()
            if self.EQUIPMENT_TAG_PATTERN.match(normalized_match):
                return normalized_match

        # Line numbers
        matches = self.LINE_NUMBER_EXTRACTION.findall(text)
        for match in matches:
            normalized_match = match.upper().strip()
            if self.LINE_NUMBER_PATTERN.match(normalized_match):
                return normalized_match

        return None

    def extract_all_tags(self, text: str) -> list[str]:
        """
        Extract all tags from text (instrument, equipment, and line).

        Override of original method to support all tag types.

        Args:
            text: Text containing potential tags

        Returns:
            List of extracted tags
        """
        if not text:
            return []

        tags = []

        # Extract instrument tags
        matches = self.INSTRUMENT_TAG_EXTRACTION.findall(text)
        for match in matches:
            normalized = self.normalize_tag(match)
            if self.INSTRUMENT_TAG_PATTERN.match(normalized) and normalized not in tags:
                tags.append(normalized)

        # Extract equipment tags
        matches = self.EQUIPMENT_TAG_EXTRACTION.findall(text)
        for match in matches:
            normalized = match.upper().strip()
            if self.EQUIPMENT_TAG_PATTERN.match(normalized) and normalized not in tags:
                tags.append(normalized)

        # Extract line numbers
        matches = self.LINE_NUMBER_EXTRACTION.findall(text)
        for match in matches:
            normalized = match.upper().strip()
            if self.LINE_NUMBER_PATTERN.match(normalized) and normalized not in tags:
                tags.append(normalized)

        return tags

    def get_function_description(self, function_code: str) -> Optional[str]:
        """
        Get description for an ISA function code.

        Args:
            function_code: Function letters (e.g., "FIT", "PCV")

        Returns:
            Description or None
        """
        return self.ISA_FUNCTION_CODES.get(function_code.upper())

    def get_equipment_type(self, equipment_code: str) -> Optional[str]:
        """
        Get equipment type from code.

        Args:
            equipment_code: Equipment letter(s) (e.g., "P", "HX")

        Returns:
            Equipment type or None
        """
        return self.EQUIPMENT_TYPE_CODES.get(equipment_code.upper())

    def get_line_service(self, service_code: str) -> Optional[str]:
        """
        Get line service description from code.

        Args:
            service_code: Service letters (e.g., "PW", "STM")

        Returns:
            Service description or None
        """
        return self.LINE_SERVICE_CODES.get(service_code.upper())

