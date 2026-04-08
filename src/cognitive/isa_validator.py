"""
EDAI4 - ISA S5.1 Validator
===========================
Validates instrument tags against ISA S5.1/ISA-5.1-2009 standard.

Features:
- First letter validation (measured variable)
- Succeeding letters validation (function/modifier)
- Tag format validation
- Loop number validation
- Complete compliance scoring
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import re

from src.utils import get_logger

logger = get_logger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"       # Violates standard
    WARNING = "warning"   # Unusual but allowed
    INFO = "info"         # Informational note


@dataclass
class ValidationIssue:
    """A validation issue found in a tag."""
    tag: str
    severity: ValidationSeverity
    code: str
    message: str
    suggestion: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "tag": self.tag,
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "suggestion": self.suggestion,
        }


@dataclass
class TagValidationResult:
    """Result of validating a single tag."""
    tag: str
    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    parsed_first_letter: Optional[str] = None
    parsed_succeeding_letters: Optional[str] = None
    parsed_loop_number: Optional[str] = None
    parsed_suffix: Optional[str] = None
    compliance_score: float = 1.0  # 0.0 to 1.0
    
    def to_dict(self) -> dict:
        return {
            "tag": self.tag,
            "valid": self.is_valid,
            "score": self.compliance_score,
            "first_letter": self.parsed_first_letter,
            "succeeding_letters": self.parsed_succeeding_letters,
            "loop_number": self.parsed_loop_number,
            "suffix": self.parsed_suffix,
            "issues": [i.to_dict() for i in self.issues],
        }


# ISA S5.1 First Letter Definitions (Measured/Initiating Variable)
ISA_FIRST_LETTERS = {
    "A": {"name": "Analysis", "description": "Composition, concentration"},
    "B": {"name": "Burner/Combustion", "description": "Flame, combustion"},
    "C": {"name": "User Choice", "description": "Conductivity (common)"},
    "D": {"name": "User Choice", "description": "Density, specific gravity (common)"},
    "E": {"name": "Voltage", "description": "Electrical potential"},
    "F": {"name": "Flow Rate", "description": "Volume or mass flow"},
    "G": {"name": "User Choice", "description": "Gauging, dimensional (common)"},
    "H": {"name": "Hand/Manual", "description": "Manual actuation"},
    "I": {"name": "Current", "description": "Electrical current"},
    "J": {"name": "Power", "description": "Electrical power"},
    "K": {"name": "Time/Schedule", "description": "Time-based control"},
    "L": {"name": "Level", "description": "Liquid or solid level"},
    "M": {"name": "User Choice", "description": "Moisture, humidity (common)"},
    "N": {"name": "User Choice", "description": "User defined"},
    "O": {"name": "User Choice", "description": "User defined"},
    "P": {"name": "Pressure", "description": "Pressure, vacuum"},
    "Q": {"name": "Quantity", "description": "Totalized flow, count"},
    "R": {"name": "Radiation", "description": "Nuclear radiation"},
    "S": {"name": "Speed/Frequency", "description": "Rotational speed"},
    "T": {"name": "Temperature", "description": "Temperature"},
    "U": {"name": "Multivariable", "description": "Multiple measured variables"},
    "V": {"name": "Vibration", "description": "Mechanical vibration"},
    "W": {"name": "Weight/Force", "description": "Weight, force, torque"},
    "X": {"name": "Unclassified", "description": "Special/unclassified"},
    "Y": {"name": "Event/State", "description": "Presence, sequence"},
    "Z": {"name": "Position/Dimension", "description": "Position, length"},
}

# ISA S5.1 Succeeding Letters (Function/Modifier)
ISA_SUCCEEDING_LETTERS = {
    # Readout/Passive Functions
    "A": {"name": "Alarm", "type": "readout"},
    "G": {"name": "Glass/Gauge", "type": "readout"},
    "I": {"name": "Indicating", "type": "readout"},
    "R": {"name": "Recording", "type": "readout"},
    
    # Output/Control Functions
    "C": {"name": "Control", "type": "output"},
    "K": {"name": "Control Station", "type": "output"},
    "S": {"name": "Switch", "type": "output"},
    "T": {"name": "Transmit", "type": "output"},
    "V": {"name": "Valve/Damper", "type": "output"},
    "Y": {"name": "Relay/Compute", "type": "output"},
    "Z": {"name": "Actuator/Driver", "type": "output"},
    
    # Modifiers (used with other letters)
    "D": {"name": "Differential", "type": "modifier"},
    "E": {"name": "Element/Sensor", "type": "modifier"},
    "F": {"name": "Ratio/Fraction", "type": "modifier"},
    "H": {"name": "High", "type": "modifier"},
    "L": {"name": "Low", "type": "modifier"},
    "M": {"name": "Middle/Intermediate", "type": "modifier"},
    "N": {"name": "User Choice", "type": "modifier"},
    "O": {"name": "Orifice/Restriction", "type": "modifier"},
    "P": {"name": "Point/Test", "type": "modifier"},
    "Q": {"name": "Integrate/Totalize", "type": "modifier"},
    "U": {"name": "Multifunction", "type": "modifier"},
    "W": {"name": "Well/Probe", "type": "modifier"},
    "X": {"name": "Unclassified", "type": "modifier"},
    
    # Special combinations
    "J": {"name": "Scan", "type": "special"},
    "B": {"name": "Burner", "type": "special"},
}

# Common valid letter combinations
COMMON_VALID_COMBINATIONS = {
    # Transmitters
    "FT", "LT", "PT", "TT", "AT", "FIT", "LIT", "PIT", "TIT",
    # Controllers
    "FC", "LC", "PC", "TC", "AC", "FIC", "LIC", "PIC", "TIC",
    # Indicators
    "FI", "LI", "PI", "TI", "AI",
    # Switches
    "FS", "LS", "PS", "TS", "FSH", "FSL", "LSH", "LSL", "PSH", "PSL", "TSH", "TSL",
    # High-High / Low-Low
    "FSHH", "FSLL", "LSHH", "LSLL", "PSHH", "PSLL", "TSHH", "TSLL",
    # Alarms
    "FAH", "FAL", "LAH", "LAL", "PAH", "PAL", "TAH", "TAL",
    # Valves
    "FV", "LV", "PV", "TV", "FCV", "LCV", "PCV", "TCV",
    # Control Valves with indicators
    "FICV", "LICV", "PICV", "TICV",
    # Recording
    "FR", "LR", "PR", "TR", "FIR", "LIR", "PIR", "TIR",
    # Elements/Wells
    "TE", "PE", "FE", "TW",
    # Safety
    "PSV", "TSV", "SDV", "BDV", "XV",
    # Analyzers
    "AIT", "AIC", "AE",
    # Level gauges
    "LG", "LGI",
    # Flow elements
    "FO", "FE",
    # Hand/Manual
    "HC", "HV", "HS", "HIC",
    # Position
    "ZI", "ZS", "ZT", "ZSH", "ZSL", "ZIC",
}


class ISAS51Validator:
    """
    Validates instrument tags against ISA S5.1 standard.
    
    The ISA S5.1 standard defines:
    - First letter: Measured variable (F=Flow, L=Level, P=Pressure, T=Temperature)
    - Succeeding letters: Functions (T=Transmit, I=Indicate, C=Control, etc.)
    - Loop number: Numeric identifier
    - Suffix: Optional qualifiers (A, B, C for redundant instruments)
    """
    
    # Tag parsing regex
    # Pattern: [Area-]FirstLetter(SucceedingLetters)LoopNumber[Suffix]
    TAG_PATTERN = re.compile(
        r'^(?:(\d{1,3})-)?'           # Optional area prefix (e.g., "100-")
        r'([A-Z])'                     # First letter (required)
        r'([A-Z]*)'                    # Succeeding letters (optional)
        r'[-]?'                        # Optional separator
        r'(\d{2,5})?'                  # Loop number (optional for some)
        r'([A-Z])?$',                  # Suffix (optional, A/B/C/etc.)
        re.IGNORECASE
    )
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize validator.
        
        Args:
            strict_mode: If True, applies stricter validation rules
        """
        self.strict_mode = strict_mode
    
    def validate_tag(self, tag: str) -> TagValidationResult:
        """
        Validate a single instrument tag.
        
        Args:
            tag: Instrument tag string (e.g., "FT-101", "LIC-200A")
            
        Returns:
            TagValidationResult with parsing and issues
        """
        issues = []
        result = TagValidationResult(tag=tag, is_valid=True)
        
        if not tag:
            issues.append(ValidationIssue(
                tag=tag,
                severity=ValidationSeverity.ERROR,
                code="EMPTY_TAG",
                message="Tag is empty",
            ))
            result.is_valid = False
            result.issues = issues
            result.compliance_score = 0.0
            return result
        
        # Normalize tag
        normalized = tag.upper().strip()
        
        # Parse tag components
        match = self.TAG_PATTERN.match(normalized)
        
        if not match:
            issues.append(ValidationIssue(
                tag=tag,
                severity=ValidationSeverity.ERROR,
                code="INVALID_FORMAT",
                message=f"Tag '{tag}' does not match ISA S5.1 format",
                suggestion="Use format: [Area-]FirstLetter[SucceedingLetters]-LoopNumber[Suffix]",
            ))
            result.is_valid = False
            result.issues = issues
            result.compliance_score = 0.0
            return result
        
        area, first_letter, succeeding, loop_num, suffix = match.groups()
        
        result.parsed_first_letter = first_letter
        result.parsed_succeeding_letters = succeeding or ""
        result.parsed_loop_number = loop_num
        result.parsed_suffix = suffix
        
        # Validate first letter
        first_issues = self._validate_first_letter(tag, first_letter)
        issues.extend(first_issues)
        
        # Validate succeeding letters
        if succeeding:
            succ_issues = self._validate_succeeding_letters(tag, first_letter, succeeding)
            issues.extend(succ_issues)
        
        # Validate loop number
        if loop_num:
            loop_issues = self._validate_loop_number(tag, loop_num)
            issues.extend(loop_issues)
        elif self.strict_mode:
            issues.append(ValidationIssue(
                tag=tag,
                severity=ValidationSeverity.WARNING,
                code="MISSING_LOOP",
                message="Loop number is missing",
            ))
        
        # Validate suffix
        if suffix:
            suffix_issues = self._validate_suffix(tag, suffix)
            issues.extend(suffix_issues)
        
        # Check for common valid combinations
        func_letters = first_letter + (succeeding or "")
        if func_letters not in COMMON_VALID_COMBINATIONS:
            issues.append(ValidationIssue(
                tag=tag,
                severity=ValidationSeverity.INFO,
                code="UNCOMMON_COMBINATION",
                message=f"'{func_letters}' is not a commonly used combination",
                suggestion="Verify this is intentional per project standards",
            ))
        
        # Calculate compliance score
        error_count = len([i for i in issues if i.severity == ValidationSeverity.ERROR])
        warning_count = len([i for i in issues if i.severity == ValidationSeverity.WARNING])
        
        if error_count > 0:
            result.is_valid = False
            result.compliance_score = 0.0
        else:
            result.compliance_score = max(0.0, 1.0 - (warning_count * 0.1))
        
        result.issues = issues
        return result
    
    def _validate_first_letter(self, tag: str, letter: str) -> list[ValidationIssue]:
        """Validate first letter against ISA standard."""
        issues = []
        
        if letter not in ISA_FIRST_LETTERS:
            issues.append(ValidationIssue(
                tag=tag,
                severity=ValidationSeverity.ERROR,
                code="INVALID_FIRST_LETTER",
                message=f"'{letter}' is not a valid ISA S5.1 first letter",
                suggestion=f"Valid letters: {', '.join(sorted(ISA_FIRST_LETTERS.keys()))}",
            ))
        elif letter in ("C", "D", "G", "M", "N", "O"):
            # User-defined letters
            issues.append(ValidationIssue(
                tag=tag,
                severity=ValidationSeverity.INFO,
                code="USER_DEFINED_LETTER",
                message=f"'{letter}' is a user-defined letter in ISA S5.1",
                suggestion="Ensure project documentation defines this letter's meaning",
            ))
        
        return issues
    
    def _validate_succeeding_letters(self, tag: str, first: str, succeeding: str) -> list[ValidationIssue]:
        """Validate succeeding letters."""
        issues = []
        
        for i, letter in enumerate(succeeding):
            if letter not in ISA_SUCCEEDING_LETTERS:
                issues.append(ValidationIssue(
                    tag=tag,
                    severity=ValidationSeverity.WARNING,
                    code="INVALID_SUCCEEDING_LETTER",
                    message=f"'{letter}' at position {i+2} is not standard ISA S5.1",
                ))
            else:
                letter_info = ISA_SUCCEEDING_LETTERS[letter]
                
                # Check for common mistakes
                if letter == first and letter not in ("U", "X"):
                    issues.append(ValidationIssue(
                        tag=tag,
                        severity=ValidationSeverity.WARNING,
                        code="DUPLICATE_LETTER",
                        message=f"First letter '{first}' repeated as succeeding letter",
                    ))
        
        # Check letter ordering (modifiers before functions)
        has_output_func = False
        for letter in succeeding:
            info = ISA_SUCCEEDING_LETTERS.get(letter, {})
            if info.get("type") == "output":
                has_output_func = True
            elif info.get("type") == "modifier" and has_output_func:
                issues.append(ValidationIssue(
                    tag=tag,
                    severity=ValidationSeverity.WARNING,
                    code="LETTER_ORDER",
                    message="Modifiers should precede output functions",
                ))
                break
        
        return issues
    
    def _validate_loop_number(self, tag: str, loop_num: str) -> list[ValidationIssue]:
        """Validate loop number."""
        issues = []
        
        try:
            num = int(loop_num)
            if num <= 0:
                issues.append(ValidationIssue(
                    tag=tag,
                    severity=ValidationSeverity.ERROR,
                    code="INVALID_LOOP_NUMBER",
                    message="Loop number must be positive",
                ))
            elif num > 99999:
                issues.append(ValidationIssue(
                    tag=tag,
                    severity=ValidationSeverity.WARNING,
                    code="LARGE_LOOP_NUMBER",
                    message="Loop number exceeds typical range",
                ))
        except ValueError:
            issues.append(ValidationIssue(
                tag=tag,
                severity=ValidationSeverity.ERROR,
                code="INVALID_LOOP_NUMBER",
                message=f"'{loop_num}' is not a valid loop number",
            ))
        
        return issues
    
    def _validate_suffix(self, tag: str, suffix: str) -> list[ValidationIssue]:
        """Validate tag suffix."""
        issues = []
        
        # Typical suffixes: A, B, C (redundancy), or numbers
        valid_suffixes = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        
        if suffix not in valid_suffixes:
            issues.append(ValidationIssue(
                tag=tag,
                severity=ValidationSeverity.WARNING,
                code="INVALID_SUFFIX",
                message=f"Suffix '{suffix}' is unusual",
            ))
        
        return issues
    
    def validate_tags(self, tags: list[str]) -> dict:
        """
        Validate multiple tags.
        
        Args:
            tags: List of tag strings
            
        Returns:
            Dictionary with validation results and summary
        """
        results = [self.validate_tag(tag) for tag in tags]
        
        valid_count = len([r for r in results if r.is_valid])
        avg_score = sum(r.compliance_score for r in results) / len(results) if results else 0
        
        # Group issues by code
        issue_summary = {}
        for result in results:
            for issue in result.issues:
                if issue.code not in issue_summary:
                    issue_summary[issue.code] = {
                        "count": 0,
                        "severity": issue.severity.value,
                        "message": issue.message,
                    }
                issue_summary[issue.code]["count"] += 1
        
        return {
            "total_tags": len(tags),
            "valid_tags": valid_count,
            "invalid_tags": len(tags) - valid_count,
            "compliance_score": avg_score,
            "results": [r.to_dict() for r in results],
            "issue_summary": issue_summary,
        }
    
    def get_letter_description(self, tag: str) -> dict:
        """
        Get human-readable description of tag letters.
        
        Args:
            tag: Instrument tag
            
        Returns:
            Dictionary with letter meanings
        """
        result = self.validate_tag(tag)
        
        description = {
            "tag": tag,
            "measured_variable": None,
            "functions": [],
        }
        
        if result.parsed_first_letter:
            first_info = ISA_FIRST_LETTERS.get(result.parsed_first_letter, {})
            description["measured_variable"] = {
                "letter": result.parsed_first_letter,
                "name": first_info.get("name", "Unknown"),
                "description": first_info.get("description", ""),
            }
        
        if result.parsed_succeeding_letters:
            for letter in result.parsed_succeeding_letters:
                info = ISA_SUCCEEDING_LETTERS.get(letter, {})
                description["functions"].append({
                    "letter": letter,
                    "name": info.get("name", "Unknown"),
                    "type": info.get("type", "unknown"),
                })
        
        return description


def validate_instrument_tags(tags: list[str], strict: bool = False) -> dict:
    """Convenience function to validate tags."""
    validator = ISAS51Validator(strict_mode=strict)
    return validator.validate_tags(tags)
