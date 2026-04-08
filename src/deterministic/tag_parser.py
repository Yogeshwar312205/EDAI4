"""
EDAI4 - Tag Parser
ISA-5.1 compliant instrument tag parsing
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

from src.utils import get_logger, config

logger = get_logger(__name__)


@dataclass
class TagInfo:
    """Parsed instrument tag information."""
    raw_tag: str
    is_valid: bool = False

    # Tag components
    area_prefix: Optional[str] = None
    first_letter: Optional[str] = None
    succeeding_letters: Optional[str] = None
    loop_number: Optional[str] = None
    suffix: Optional[str] = None

    # Interpreted information
    measured_variable: Optional[str] = None
    measured_variable_name: Optional[str] = None
    instrument_type: Optional[str] = None
    function: Optional[str] = None
    signal_type: Optional[str] = None

    # Alarm/Safety information
    has_alarm: bool = False
    alarm_type: Optional[str] = None  # High, Low, High-High, Low-Low
    is_safety: bool = False

    # Additional metadata
    unit: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None

    # Confidence score (0-1)
    confidence: float = 0.0


class TagParser:
    """
    ISA-5.1 compliant instrument tag parser.
    Parses tag numbers and extracts engineering information.
    """

    # Standard tag pattern: [Area]-[FirstLetter][SucceedingLetters]-[LoopNumber][Suffix]
    # Examples: PT-1001, 10-FIC-2001A, LSHH-3001
    TAG_PATTERNS = [
        # With area prefix and hyphen
        r"^(?P<area>\d{1,3}|[A-Z]+\d*)-(?P<first>[A-Z])(?P<succeed>[A-Z]{1,5})-?(?P<loop>\d{3,5})(?P<suffix>[A-Z])?$",
        # Standard with hyphen
        r"^(?P<first>[A-Z])(?P<succeed>[A-Z]{1,5})-(?P<loop>\d{3,5})(?P<suffix>[A-Z])?$",
        # Without hyphen
        r"^(?P<first>[A-Z])(?P<succeed>[A-Z]{1,5})(?P<loop>\d{3,5})(?P<suffix>[A-Z])?$",
        # Short form (e.g., PT1001)
        r"^(?P<first>[A-Z])(?P<succeed>[A-Z]{1,2})(?P<loop>\d{3,5})$",
    ]

    def __init__(self, rules_path: Optional[str | Path] = None):
        """
        Initialize tag parser with instrument rules.

        Args:
            rules_path: Path to instrument rules YAML file
        """
        # Load rules from config
        self.rules = config.get_instrument_rules()

        if not self.rules:
            # Try loading from file
            if rules_path:
                from src.utils import load_config
                self.rules = load_config(rules_path)
            else:
                logger.warning("No instrument rules loaded, using defaults")
                self._load_default_rules()

        # Compile regex patterns
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.TAG_PATTERNS]

        logger.info("TagParser initialized")

    def _load_default_rules(self):
        """Load minimal default rules."""
        self.rules = {
            "first_letter": {
                "P": {"name": "Pressure", "unit": "bar"},
                "F": {"name": "Flow", "unit": "m3/h"},
                "L": {"name": "Level", "unit": "%"},
                "T": {"name": "Temperature", "unit": "degC"},
                "A": {"name": "Analysis", "unit": "varies"},
            },
            "succeeding_letters": {
                "T": {"name": "Transmitter", "signal_type": "AI"},
                "I": {"name": "Indicator", "signal_type": "Local"},
                "C": {"name": "Controller", "signal_type": "AO"},
                "V": {"name": "Valve", "signal_type": "AO"},
                "S": {"name": "Switch", "signal_type": "DI"},
            },
            "modifiers": {
                "H": {"name": "High", "alarm_type": "Alarm"},
                "L": {"name": "Low", "alarm_type": "Alarm"},
                "HH": {"name": "High-High", "alarm_type": "Trip", "is_safety": True},
                "LL": {"name": "Low-Low", "alarm_type": "Trip", "is_safety": True},
            },
        }

    def parse(self, tag: str) -> TagInfo:
        """
        Parse an instrument tag and extract information.

        Args:
            tag: Instrument tag string (e.g., "PT-1001", "LSHH-3001")

        Returns:
            TagInfo object with parsed information
        """
        tag = tag.strip().upper()
        tag_info = TagInfo(raw_tag=tag)

        # Try each pattern
        match = None
        for pattern in self.patterns:
            match = pattern.match(tag)
            if match:
                break

        if not match:
            logger.debug(f"Tag '{tag}' did not match any pattern")
            return tag_info

        # Extract components
        groups = match.groupdict()
        tag_info.area_prefix = groups.get("area")
        tag_info.first_letter = groups.get("first", "").upper()
        tag_info.succeeding_letters = groups.get("succeed", "").upper()
        tag_info.loop_number = groups.get("loop")
        tag_info.suffix = groups.get("suffix", "").upper() if groups.get("suffix") else None
        tag_info.is_valid = True

        # Interpret first letter (measured variable)
        self._interpret_first_letter(tag_info)

        # Interpret succeeding letters (function)
        self._interpret_succeeding_letters(tag_info)

        # Check for alarm/safety modifiers
        self._check_modifiers(tag_info)

        # Determine overall instrument type
        self._determine_instrument_type(tag_info)

        # Calculate confidence
        tag_info.confidence = self._calculate_confidence(tag_info)

        logger.debug(f"Parsed tag '{tag}': {tag_info.instrument_type}, signal={tag_info.signal_type}")

        return tag_info

    def _interpret_first_letter(self, tag_info: TagInfo) -> None:
        """Interpret the first letter (measured variable)."""
        first_letter = tag_info.first_letter

        if not first_letter:
            return

        first_rules = self.rules.get("first_letter", {})
        if first_letter in first_rules:
            rule = first_rules[first_letter]
            tag_info.measured_variable = first_letter
            tag_info.measured_variable_name = rule.get("name")
            tag_info.unit = rule.get("unit")

    def _interpret_succeeding_letters(self, tag_info: TagInfo) -> None:
        """Interpret succeeding letters (function)."""
        succeed = tag_info.succeeding_letters

        if not succeed:
            return

        succeed_rules = self.rules.get("succeeding_letters", {})
        combined_rules = self.rules.get("combined_functions", {})
        type_rules = self.rules.get("type_inference", {})

        # First check combined functions (e.g., SHH, IC)
        if succeed in combined_rules:
            rule = combined_rules[succeed]
            tag_info.function = rule.get("name")
            tag_info.signal_type = rule.get("signal_type")
            if rule.get("alarm_type"):
                tag_info.has_alarm = True
                tag_info.alarm_type = rule.get("alarm_type")
            if rule.get("is_safety"):
                tag_info.is_safety = True
            return

        # Check type inference rules
        full_letters = tag_info.first_letter + succeed
        if full_letters in type_rules:
            rule = type_rules[full_letters]
            tag_info.instrument_type = rule.get("type")
            tag_info.signal_type = rule.get("signal")
            tag_info.category = rule.get("category")
            if rule.get("alarm"):
                tag_info.has_alarm = True
                tag_info.alarm_type = rule.get("alarm")
            if rule.get("is_safety"):
                tag_info.is_safety = True
            return

        # Parse individual letters
        functions = []
        signal_types = []

        for letter in succeed:
            if letter in succeed_rules:
                rule = succeed_rules[letter]
                functions.append(rule.get("name", letter))
                if rule.get("signal_type"):
                    signal_types.append(rule.get("signal_type"))

        if functions:
            tag_info.function = " ".join(functions)

        if signal_types:
            # Combine signal types (e.g., AI + AO for IC)
            unique_signals = list(dict.fromkeys(signal_types))
            tag_info.signal_type = "+".join(unique_signals) if len(unique_signals) > 1 else unique_signals[0]

    def _check_modifiers(self, tag_info: TagInfo) -> None:
        """Check for alarm/safety modifiers in succeeding letters."""
        succeed = tag_info.succeeding_letters or ""
        modifiers = self.rules.get("modifiers", {})

        # Check for HH, LL, H, L patterns
        for modifier in ["HH", "LL", "H", "L"]:
            if modifier in succeed:
                if modifier in modifiers:
                    rule = modifiers[modifier]
                    tag_info.has_alarm = True
                    tag_info.alarm_type = rule.get("name")
                    if rule.get("is_safety"):
                        tag_info.is_safety = True
                break

    def _determine_instrument_type(self, tag_info: TagInfo) -> None:
        """Determine the overall instrument type."""
        if tag_info.instrument_type:
            return  # Already set by type inference

        parts = []

        if tag_info.measured_variable_name:
            parts.append(tag_info.measured_variable_name)

        if tag_info.function:
            parts.append(tag_info.function)

        if parts:
            tag_info.instrument_type = " ".join(parts)

        # Generate description
        desc_parts = []
        if tag_info.measured_variable_name:
            desc_parts.append(tag_info.measured_variable_name)
        if tag_info.function:
            desc_parts.append(tag_info.function.lower())
        if tag_info.alarm_type:
            desc_parts.append(f"({tag_info.alarm_type})")

        tag_info.description = " ".join(desc_parts) if desc_parts else None

    def _calculate_confidence(self, tag_info: TagInfo) -> float:
        """Calculate confidence score for the parsing."""
        score = 0.0

        if tag_info.is_valid:
            score += 0.3

        if tag_info.first_letter and tag_info.measured_variable_name:
            score += 0.2

        if tag_info.succeeding_letters and tag_info.function:
            score += 0.2

        if tag_info.loop_number:
            score += 0.2

        if tag_info.signal_type:
            score += 0.1

        return min(score, 1.0)

    def is_valid_tag(self, tag: str) -> bool:
        """
        Check if a string is a valid instrument tag.

        Args:
            tag: String to check

        Returns:
            True if valid tag format
        """
        tag = tag.strip().upper()

        for pattern in self.patterns:
            if pattern.match(tag):
                return True

        return False

    def extract_tags_from_text(self, text: str) -> list[str]:
        """
        Extract potential instrument tags from a text string.

        Args:
            text: Text containing potential tags

        Returns:
            List of found tags
        """
        tags = []

        # Pattern to find potential tags in text
        potential_pattern = r'\b([A-Z]{1,2}[A-Z]{1,5}-?\d{3,5}[A-Z]?)\b'
        matches = re.findall(potential_pattern, text.upper())

        for match in matches:
            if self.is_valid_tag(match):
                tags.append(match)

        return tags

    def batch_parse(self, tags: list[str]) -> list[TagInfo]:
        """
        Parse multiple tags.

        Args:
            tags: List of tag strings

        Returns:
            List of TagInfo objects
        """
        return [self.parse(tag) for tag in tags]
