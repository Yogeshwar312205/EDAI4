"""
EDAI4 - Signal Classifier
Classifies instrument signals based on ISA-5.1 standards
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from src.utils import get_logger, config
from src.deterministic.tag_parser import TagInfo

logger = get_logger(__name__)


class SignalType(Enum):
    """Signal type enumeration."""
    AI = "Analog Input"
    AO = "Analog Output"
    DI = "Digital Input"
    DO = "Digital Output"
    LOCAL = "Local (No Signal)"
    UNKNOWN = "Unknown"


@dataclass
class SignalInfo:
    """Signal classification information."""
    signal_type: SignalType
    signal_code: str  # AI, AO, DI, DO
    description: str

    # Electrical characteristics
    range: Optional[str] = None  # e.g., "4-20mA", "24VDC"
    voltage: Optional[str] = None
    current: Optional[str] = None

    # I/O classification
    io_type: Optional[str] = None  # Input or Output
    is_analog: bool = False
    is_digital: bool = False

    # Safety information
    is_safety: bool = False
    fail_safe_action: Optional[str] = None

    # Module assignment hints
    suggested_module: Optional[str] = None


class SignalClassifier:
    """
    Classifies instrument signals based on instrument type and function.
    Uses ISA-5.1 rules to determine signal types (AI, AO, DI, DO).
    """

    # Signal type mapping based on function
    FUNCTION_SIGNAL_MAP = {
        # Transmitters -> Analog Input
        "T": SignalType.AI,
        "TRANSMITTER": SignalType.AI,

        # Controllers -> Analog Output (output side)
        "C": SignalType.AO,
        "CONTROLLER": SignalType.AO,

        # Indicators (local) -> No signal
        "I": SignalType.LOCAL,
        "G": SignalType.LOCAL,  # Gauge

        # Switches -> Digital Input
        "S": SignalType.DI,
        "SWITCH": SignalType.DI,

        # Valves
        "V": SignalType.AO,  # Control valve
        "VALVE": SignalType.AO,

        # Actuators/Drivers -> Digital Output
        "Z": SignalType.DO,
        "Y": SignalType.DO,  # Relay/Solenoid
    }

    # Combined function signal mapping
    COMBINED_SIGNAL_MAP = {
        # Transmitter combinations
        "PT": SignalType.AI,
        "FT": SignalType.AI,
        "LT": SignalType.AI,
        "TT": SignalType.AI,
        "AT": SignalType.AI,
        "PDT": SignalType.AI,
        "FDT": SignalType.AI,

        # Controller combinations (have both AI and AO)
        "PIC": SignalType.AI,  # Primary signal is input
        "FIC": SignalType.AI,
        "LIC": SignalType.AI,
        "TIC": SignalType.AI,
        "AIC": SignalType.AI,

        # Control valves
        "PCV": SignalType.AO,
        "FCV": SignalType.AO,
        "LCV": SignalType.AO,
        "TCV": SignalType.AO,

        # Switches (High/Low)
        "PSH": SignalType.DI,
        "PSL": SignalType.DI,
        "PSHH": SignalType.DI,
        "PSLL": SignalType.DI,
        "LSH": SignalType.DI,
        "LSL": SignalType.DI,
        "LSHH": SignalType.DI,
        "LSLL": SignalType.DI,
        "TSH": SignalType.DI,
        "TSL": SignalType.DI,
        "TSHH": SignalType.DI,
        "TSLL": SignalType.DI,
        "FSH": SignalType.DI,
        "FSL": SignalType.DI,
        "FSHH": SignalType.DI,
        "FSLL": SignalType.DI,

        # On/Off valves -> Digital Output
        "XV": SignalType.DO,
        "SDV": SignalType.DO,
        "BDV": SignalType.DO,

        # Local indicators
        "PI": SignalType.LOCAL,
        "TI": SignalType.LOCAL,
        "LI": SignalType.LOCAL,
        "FI": SignalType.LOCAL,
        "PG": SignalType.LOCAL,
        "LG": SignalType.LOCAL,
    }

    def __init__(self):
        """Initialize signal classifier."""
        self.rules = config.get_instrument_rules()
        self.signal_rules = self.rules.get("signal_types", {}) if self.rules else {}

        logger.info("SignalClassifier initialized")

    def classify(self, tag_info: TagInfo) -> SignalInfo:
        """
        Classify the signal type for an instrument.

        Args:
            tag_info: Parsed tag information

        Returns:
            SignalInfo object with signal classification
        """
        # Get signal type from tag info if already parsed
        if tag_info.signal_type:
            return self._create_signal_info(tag_info.signal_type, tag_info)

        # Try combined type lookup
        if tag_info.first_letter and tag_info.succeeding_letters:
            combined = tag_info.first_letter + tag_info.succeeding_letters
            if combined in self.COMBINED_SIGNAL_MAP:
                signal_type = self.COMBINED_SIGNAL_MAP[combined]
                return self._create_signal_info(signal_type.name, tag_info)

        # Try function-based lookup
        if tag_info.succeeding_letters:
            # Check first succeeding letter
            first_func = tag_info.succeeding_letters[0]
            if first_func in self.FUNCTION_SIGNAL_MAP:
                signal_type = self.FUNCTION_SIGNAL_MAP[first_func]
                return self._create_signal_info(signal_type.name, tag_info)

        # Default to unknown
        return SignalInfo(
            signal_type=SignalType.UNKNOWN,
            signal_code="UNKNOWN",
            description="Signal type could not be determined",
        )

    def _create_signal_info(self, signal_code: str, tag_info: TagInfo) -> SignalInfo:
        """Create SignalInfo from signal code."""
        # Handle combined signals (e.g., "AI+AO")
        if "+" in signal_code:
            primary_code = signal_code.split("+")[0]
        else:
            primary_code = signal_code

        # Map to enum
        signal_type_map = {
            "AI": SignalType.AI,
            "AO": SignalType.AO,
            "DI": SignalType.DI,
            "DO": SignalType.DO,
            "LOCAL": SignalType.LOCAL,
        }

        signal_type = signal_type_map.get(primary_code, SignalType.UNKNOWN)

        # Get signal characteristics
        range_str = None
        voltage = None
        current = None
        suggested_module = None

        if primary_code == "AI":
            range_str = "4-20mA"
            current = "4-20mA"
            suggested_module = "AI Module"
        elif primary_code == "AO":
            range_str = "4-20mA"
            current = "4-20mA"
            suggested_module = "AO Module"
        elif primary_code == "DI":
            range_str = "24VDC"
            voltage = "24VDC"
            suggested_module = "DI Module"
        elif primary_code == "DO":
            range_str = "24VDC"
            voltage = "24VDC"
            suggested_module = "DO Module"

        # Determine fail-safe action for outputs
        fail_safe = None
        if primary_code in ["AO", "DO"]:
            if tag_info.is_safety:
                # Safety valves typically fail closed
                if "BDV" in tag_info.raw_tag.upper():
                    fail_safe = "Fail Open (FO)"
                else:
                    fail_safe = "Fail Close (FC)"

        return SignalInfo(
            signal_type=signal_type,
            signal_code=signal_code,
            description=signal_type.value,
            range=range_str,
            voltage=voltage,
            current=current,
            io_type="Input" if primary_code in ["AI", "DI"] else "Output" if primary_code in ["AO", "DO"] else "Local",
            is_analog=primary_code in ["AI", "AO"],
            is_digital=primary_code in ["DI", "DO"],
            is_safety=tag_info.is_safety,
            fail_safe_action=fail_safe,
            suggested_module=suggested_module,
        )

    def classify_from_tag(self, tag: str) -> SignalInfo:
        """
        Classify signal directly from tag string.

        Args:
            tag: Instrument tag string

        Returns:
            SignalInfo object
        """
        from src.deterministic.tag_parser import TagParser
        parser = TagParser()
        tag_info = parser.parse(tag)
        return self.classify(tag_info)

    def get_signal_range(self, signal_type: SignalType) -> str:
        """
        Get typical signal range for a signal type.

        Args:
            signal_type: Signal type enum

        Returns:
            Signal range string
        """
        ranges = {
            SignalType.AI: "4-20mA DC",
            SignalType.AO: "4-20mA DC",
            SignalType.DI: "24VDC",
            SignalType.DO: "24VDC",
            SignalType.LOCAL: "N/A",
            SignalType.UNKNOWN: "Unknown",
        }
        return ranges.get(signal_type, "Unknown")

    def is_input_signal(self, signal_info: SignalInfo) -> bool:
        """Check if signal is an input type."""
        return signal_info.signal_type in [SignalType.AI, SignalType.DI]

    def is_output_signal(self, signal_info: SignalInfo) -> bool:
        """Check if signal is an output type."""
        return signal_info.signal_type in [SignalType.AO, SignalType.DO]

    def count_io_by_type(self, signals: list[SignalInfo]) -> dict:
        """
        Count I/O points by type.

        Args:
            signals: List of SignalInfo objects

        Returns:
            Dictionary with counts per signal type
        """
        counts = {
            "AI": 0,
            "AO": 0,
            "DI": 0,
            "DO": 0,
            "LOCAL": 0,
            "UNKNOWN": 0,
            "TOTAL": 0,
        }

        for signal in signals:
            code = signal.signal_code.split("+")[0]  # Handle combined types
            if code in counts:
                counts[code] += 1
            else:
                counts["UNKNOWN"] += 1
            counts["TOTAL"] += 1

        return counts
