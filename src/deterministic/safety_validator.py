"""
EDAI4 - Safety Validator
IEC 61511 compliant safety instrumented system validation
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from src.utils import get_logger, config
from src.deterministic.tag_parser import TagInfo

logger = get_logger(__name__)


class SILLevel(Enum):
    """Safety Integrity Level enumeration."""
    NONE = 0
    SIL1 = 1
    SIL2 = 2
    SIL3 = 3
    SIL4 = 4


class SafetyFunctionType(Enum):
    """Type of safety function."""
    ESD = "Emergency Shutdown"
    HIPPS = "High Integrity Pressure Protection"
    BMS = "Burner Management System"
    F_AND_G = "Fire and Gas"
    PROCESS = "Process Interlock"
    NONE = "Not a Safety Function"


@dataclass
class SafetyValidationResult:
    """Results of safety validation."""
    is_safety_instrument: bool = False
    safety_function: SafetyFunctionType = SafetyFunctionType.NONE

    # SIL information
    sil_level: Optional[SILLevel] = None
    sil_capable: bool = False

    # Trip/Alarm classification
    is_trip_initiator: bool = False
    is_final_element: bool = False
    trip_type: Optional[str] = None  # High-High, Low-Low, etc.

    # Validation messages
    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    # Cause & Effect data
    cause_or_effect: Optional[str] = None  # "Cause" or "Effect"
    typical_actions: list[str] = field(default_factory=list)


class SafetyValidator:
    """
    Validates instruments for IEC 61511 compliance.
    Identifies safety-related instruments and their roles in SIS.
    """

    # Patterns that indicate safety instruments (trip initiators)
    TRIP_PATTERNS = [
        (r".*SHH$", "High-High"),
        (r".*SLL$", "Low-Low"),
        (r".*PSHH.*", "Pressure High-High"),
        (r".*PSLL.*", "Pressure Low-Low"),
        (r".*LSHH.*", "Level High-High"),
        (r".*LSLL.*", "Level Low-Low"),
        (r".*TSHH.*", "Temperature High-High"),
        (r".*TSLL.*", "Temperature Low-Low"),
        (r".*FSHH.*", "Flow High-High"),
        (r".*FSLL.*", "Flow Low-Low"),
    ]

    # Patterns for final elements (actuated devices)
    FINAL_ELEMENT_PATTERNS = [
        (r"SDV-?\d+", "Shutdown Valve"),
        (r"BDV-?\d+", "Blowdown Valve"),
        (r"XV-?\d+", "On/Off Valve"),
        (r"ESV-?\d+", "Emergency Shutoff Valve"),
        (r"PSV-?\d+", "Pressure Safety Valve"),
    ]

    # Tags that indicate non-safety instruments
    NON_SAFETY_PATTERNS = [
        r".*I$",    # Indicators only
        r".*G$",    # Gauges
        r".*R$",    # Recorders
        r"P[ITGR]-\d+$",  # Simple pressure instruments
        r"T[ITGR]-\d+$",  # Simple temperature instruments
    ]

    def __init__(self):
        """Initialize safety validator."""
        self.rules = config.get_safety_rules()
        if not self.rules:
            logger.warning("No safety rules loaded, using defaults")
            self.rules = self._load_default_rules()

        # Compile patterns
        self.trip_patterns = [(re.compile(p, re.IGNORECASE), t) for p, t in self.TRIP_PATTERNS]
        self.final_element_patterns = [(re.compile(p, re.IGNORECASE), t) for p, t in self.FINAL_ELEMENT_PATTERNS]
        self.non_safety_patterns = [re.compile(p, re.IGNORECASE) for p in self.NON_SAFETY_PATTERNS]

        logger.info("SafetyValidator initialized")

    def _load_default_rules(self) -> dict:
        """Load default safety rules."""
        return {
            "sil_levels": {
                "SIL1": {"risk_reduction_factor": "10-100"},
                "SIL2": {"risk_reduction_factor": "100-1000"},
                "SIL3": {"risk_reduction_factor": "1000-10000"},
            },
            "trip_logic": {
                "patterns": {
                    "1oo1": {"fault_tolerant": False},
                    "1oo2": {"fault_tolerant": True},
                    "2oo3": {"fault_tolerant": True},
                }
            }
        }

    def validate(self, tag_info: TagInfo) -> SafetyValidationResult:
        """
        Validate an instrument for safety compliance.

        Args:
            tag_info: Parsed tag information

        Returns:
            SafetyValidationResult with validation details
        """
        result = SafetyValidationResult()
        tag = tag_info.raw_tag.upper()

        # Check if explicitly marked as safety
        if tag_info.is_safety:
            result.is_safety_instrument = True

        # Check for trip initiator patterns
        for pattern, trip_type in self.trip_patterns:
            if pattern.match(tag):
                result.is_safety_instrument = True
                result.is_trip_initiator = True
                result.trip_type = trip_type
                result.cause_or_effect = "Cause"
                result.safety_function = SafetyFunctionType.ESD
                break

        # Check for final element patterns
        for pattern, element_type in self.final_element_patterns:
            if pattern.match(tag):
                result.is_safety_instrument = True
                result.is_final_element = True
                result.cause_or_effect = "Effect"
                result.typical_actions.append(element_type)

                # Determine safety function
                if "SDV" in tag or "ESV" in tag:
                    result.safety_function = SafetyFunctionType.ESD
                elif "BDV" in tag:
                    result.safety_function = SafetyFunctionType.ESD
                elif "PSV" in tag:
                    result.safety_function = SafetyFunctionType.HIPPS
                break

        # Check if explicitly non-safety
        if not result.is_safety_instrument:
            for pattern in self.non_safety_patterns:
                if pattern.match(tag):
                    result.safety_function = SafetyFunctionType.NONE
                    break

        # Determine SIL capability
        if result.is_safety_instrument:
            result.sil_capable = True
            result.sil_level = self._estimate_sil_level(tag_info, result)

        # Generate recommendations
        self._generate_recommendations(tag_info, result)

        return result

    def _estimate_sil_level(
        self,
        tag_info: TagInfo,
        validation: SafetyValidationResult
    ) -> SILLevel:
        """
        Estimate SIL level based on instrument characteristics.
        Note: Actual SIL determination requires full SIF analysis.
        """
        # High-High/Low-Low typically indicate SIL 2 or higher
        if validation.trip_type and ("High-High" in validation.trip_type or "Low-Low" in validation.trip_type):
            return SILLevel.SIL2

        # Basic safety switches typically SIL 1
        if validation.is_trip_initiator:
            return SILLevel.SIL1

        # Final elements depend on application
        if validation.is_final_element:
            if "HIPPS" in tag_info.raw_tag.upper():
                return SILLevel.SIL3
            return SILLevel.SIL2

        return SILLevel.SIL1

    def _generate_recommendations(
        self,
        tag_info: TagInfo,
        result: SafetyValidationResult
    ) -> None:
        """Generate safety recommendations."""
        if not result.is_safety_instrument:
            return

        # Trip initiator recommendations
        if result.is_trip_initiator:
            result.recommendations.append(
                "Verify SIL rating with SIF analysis"
            )
            result.recommendations.append(
                "Document proof test interval"
            )
            result.recommendations.append(
                "Include in Cause & Effect matrix"
            )

        # Final element recommendations
        if result.is_final_element:
            result.recommendations.append(
                "Document fail-safe position (FC/FO)"
            )
            result.recommendations.append(
                "Verify actuator spring return"
            )

        # SIL-specific recommendations
        if result.sil_level and result.sil_level.value >= 2:
            result.recommendations.append(
                f"Consider redundancy for {result.sil_level.name}"
            )

    def is_sis_instrument(self, tag: str) -> bool:
        """
        Quick check if tag represents a SIS instrument.

        Args:
            tag: Instrument tag string

        Returns:
            True if likely a SIS instrument
        """
        tag = tag.upper()

        # Check trip patterns
        for pattern, _ in self.trip_patterns:
            if pattern.match(tag):
                return True

        # Check final element patterns
        for pattern, _ in self.final_element_patterns:
            if pattern.match(tag):
                return True

        return False

    def get_trip_type(self, tag: str) -> Optional[str]:
        """
        Get trip type for a tag.

        Args:
            tag: Instrument tag string

        Returns:
            Trip type string or None
        """
        tag = tag.upper()

        for pattern, trip_type in self.trip_patterns:
            if pattern.match(tag):
                return trip_type

        return None

    def get_cause_effect_role(self, tag: str) -> Optional[str]:
        """
        Determine if tag is a Cause or Effect in C&E matrix.

        Args:
            tag: Instrument tag string

        Returns:
            "Cause", "Effect", or None
        """
        tag = tag.upper()

        # Trip initiators are causes
        for pattern, _ in self.trip_patterns:
            if pattern.match(tag):
                return "Cause"

        # Final elements are effects
        for pattern, _ in self.final_element_patterns:
            if pattern.match(tag):
                return "Effect"

        return None

    def validate_trip_logic(self, initiators: list[str], voting: str) -> dict:
        """
        Validate trip logic configuration.

        Args:
            initiators: List of initiator tags
            voting: Voting logic (e.g., "1oo2", "2oo3")

        Returns:
            Validation result dictionary
        """
        result = {
            "voting": voting,
            "initiator_count": len(initiators),
            "is_valid": False,
            "warnings": [],
            "sil_achievable": None,
        }

        # Parse voting logic
        match = re.match(r"(\d)oo(\d)", voting)
        if not match:
            result["warnings"].append(f"Invalid voting pattern: {voting}")
            return result

        required = int(match.group(1))
        total = int(match.group(2))

        if len(initiators) != total:
            result["warnings"].append(
                f"Voting {voting} requires {total} initiators, found {len(initiators)}"
            )
        else:
            result["is_valid"] = True

        # Estimate achievable SIL
        trip_rules = self.rules.get("trip_logic", {}).get("patterns", {})
        if voting in trip_rules:
            rule = trip_rules[voting]
            result["fault_tolerant"] = rule.get("fault_tolerant", False)
            result["sil_achievable"] = rule.get("typical_sil", "SIL1")

        return result
