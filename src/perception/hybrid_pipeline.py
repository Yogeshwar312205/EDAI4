"""
================================================================================
EDAI4 - HYBRID PERCEPTION PIPELINE
================================================================================
Solves the "YOLO Domain Shift" problem by combining:
  1. YOLO/SAHI detection (valves, equipment, fittings)
  2. OpenCV HoughCircles (instrument bubbles that YOLO misses)
  3. Regex ISA S5.1 validation (OCR text → Instrument promotion)

This is a FALLBACK-FIRST architecture:
  - If YOLO catches an instrument bubble → great
  - If YOLO misses but HoughCircles finds a circle with ISA text → create node
  - If both miss but OCR text matches ISA pattern → forcefully promote to node

Dependencies:
  pip install sahi ultralytics paddlepaddle paddleocr opencv-python numpy

Author: EDAI4 Project
================================================================================
"""

import os
import re
import time
import warnings
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

# CRITICAL: Disable OneDNN BEFORE any paddle imports to avoid Windows issues
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["MKLDNN_CACHE_CAPACITY"] = "0"
os.environ["FLAGS_enable_pir_api"] = "0"

import numpy as np
import cv2

warnings.filterwarnings("ignore")
os.environ["CUDA_MODULE_LOADING"] = "LAZY"


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class DetectionSource(Enum):
    """Origin of a detection."""
    YOLO = "yolo"                    # SAHI/YOLO detected
    HOUGH_CIRCLE = "hough_circle"    # OpenCV circle detection
    ISA_REGEX = "isa_regex"          # Regex-validated OCR text
    COMBINED = "combined"            # Multiple sources confirmed


@dataclass
class DetectedNode:
    """
    A unified node detected by any method.
    Can represent valves, instruments, equipment, etc.
    """
    class_name: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float
    source: DetectionSource
    tag: Optional[str] = None
    is_instrument: bool = False
    
    @property
    def center(self) -> Tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)
    
    @property
    def width(self) -> float:
        return self.x2 - self.x1
    
    @property
    def height(self) -> float:
        return self.y2 - self.y1
    
    @property
    def area(self) -> float:
        return self.width * self.height


@dataclass
class OCRText:
    """Text extracted by PaddleOCR."""
    text: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float
    is_isa_tag: bool = False
    matched_to_node: bool = False
    
    @property
    def center(self) -> Tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)


@dataclass
class CircleDetection:
    """A circle detected by HoughCircles."""
    cx: float  # Center X
    cy: float  # Center Y
    radius: float
    matched_text: Optional[str] = None
    
    @property
    def x1(self) -> float:
        return self.cx - self.radius
    
    @property
    def y1(self) -> float:
        return self.cy - self.radius
    
    @property
    def x2(self) -> float:
        return self.cx + self.radius
    
    @property
    def y2(self) -> float:
        return self.cy + self.radius


@dataclass 
class HybridPipelineResult:
    """Complete result from hybrid pipeline."""
    nodes: List[DetectedNode]
    text_blocks: List[OCRText]
    circles: List[CircleDetection]
    discarded_text: List[OCRText]
    timing: Dict[str, float]
    stats: Dict[str, int]
    image_size: Tuple[int, int]


# =============================================================================
# ISA S5.1 REGEX VALIDATOR
# =============================================================================

class ISATagValidator:
    """
    Validates instrument tags against ISA S5.1 standard.
    
    ISA S5.1 defines instrument tag format as:
      - First letter: Measured variable (F=Flow, T=Temp, P=Pressure, L=Level, A=Analysis)
      - Second letter: Function (I=Indicator, C=Controller, T=Transmitter, V=Valve, etc.)
      - Optional third letter: Modifier (H=High, L=Low, etc.)
      - Followed by loop number (e.g., 101, 202A)
    
    Examples: FT-101, PIC-202, TT-303A, LSH-401, PSV-001
    """
    
    # Comprehensive ISA S5.1 prefixes
    # Format: [Measured Variable][Readout/Function][Modifier]
    
    MEASURED_VARIABLES = {
        'A': 'Analysis',
        'B': 'Burner/Combustion', 
        'C': 'Conductivity',
        'D': 'Density/Specific Gravity',
        'E': 'Voltage',
        'F': 'Flow',
        'G': 'Gauging/Position',
        'H': 'Hand',
        'I': 'Current',
        'J': 'Power',
        'K': 'Time/Schedule',
        'L': 'Level',
        'M': 'Moisture/Humidity',
        'N': 'User Choice',
        'O': 'User Choice',
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
    
    FUNCTIONS = {
        'A': 'Alarm',
        'C': 'Controller',
        'D': 'Differential',
        'E': 'Element/Sensor',
        'G': 'Glass/Gauge',
        'H': 'High',
        'I': 'Indicator',
        'K': 'Control Station',
        'L': 'Low',
        'M': 'Middle/Intermediate',
        'N': 'User Choice',
        'O': 'Orifice',
        'P': 'Point',
        'Q': 'Integrate/Totalize',
        'R': 'Recorder',
        'S': 'Switch',
        'T': 'Transmitter',
        'U': 'Multifunction',
        'V': 'Valve',
        'W': 'Well',
        'X': 'Unclassified',
        'Y': 'Relay/Compute',
        'Z': 'Driver/Actuator',
    }
    
    # Common two-letter and three-letter prefixes
    COMMON_PREFIXES = [
        # Transmitters
        'FT', 'PT', 'LT', 'TT', 'AT', 'WT', 'DT', 'ST', 'VT',
        # Controllers
        'FC', 'PC', 'LC', 'TC', 'AC', 'WC', 'DC', 'SC',
        # Indicators
        'FI', 'PI', 'LI', 'TI', 'AI', 'WI', 'DI', 'SI',
        # Valves (Control/Hand)
        'FV', 'PV', 'LV', 'TV', 'AV', 'HV',
        # Indicating Controllers
        'FIC', 'PIC', 'LIC', 'TIC', 'AIC',
        # Recording Controllers
        'FRC', 'PRC', 'LRC', 'TRC', 'ARC',
        # Safety Valves
        'PSV', 'PRV', 'TSV', 'PSE',
        # High/Low Switches and Alarms
        'PSH', 'PSL', 'PSHH', 'PSLL',
        'TSH', 'TSL', 'TSHH', 'TSLL',
        'LSH', 'LSL', 'LSHH', 'LSLL',
        'FSH', 'FSL', 'FSHH', 'FSLL',
        'ASH', 'ASL',
        # High/Low Alarms
        'PAH', 'PAL', 'PAHH', 'PALL',
        'TAH', 'TAL', 'TAHH', 'TALL',
        'LAH', 'LAL', 'LAHH', 'LALL',
        'FAH', 'FAL', 'FAHH', 'FALL',
        'AAH', 'AAL',
        # Elements
        'FE', 'TE', 'PE', 'LE', 'AE', 'SE', 'DE',
        # Differential
        'PDT', 'PDI', 'PDC', 'PDIC',
        # Flow Elements and Orifices
        'FO', 'FQ', 'FQI', 'FQC',
        # Level Gauges
        'LG', 'LGD',
        # General Switches
        'FS', 'PS', 'LS', 'TS', 'AS',
        # Analyzers
        'AIT', 'AIC', 'AT', 'AC', 'AR',
        # Hand Controls
        'HC', 'HIC', 'HS',
        # Other common
        'XV', 'ZV', 'ZIC', 'ZT',
    ]
    
    def __init__(self):
        """Initialize regex patterns."""
        # Build comprehensive prefix pattern
        prefix_pattern = '|'.join(sorted(self.COMMON_PREFIXES, key=len, reverse=True))
        
        # Pattern 1: Standard format PREFIX-NUMBER or PREFIX_NUMBER
        # Examples: FT-101, PIC-202A, TT_303, PSV-001
        self.pattern_standard = re.compile(
            rf'^({prefix_pattern})[-_]?(\d{{2,4}}[A-Z]?)$',
            re.IGNORECASE
        )
        
        # Pattern 2: Prefix only (for bubble text that's just "FIC" or "TT")
        self.pattern_prefix_only = re.compile(
            rf'^({prefix_pattern})$',
            re.IGNORECASE
        )
        
        # Pattern 3: Dynamic pattern for any valid ISA combination
        # First letter must be measured variable, second must be function
        mv_pattern = ''.join(self.MEASURED_VARIABLES.keys())
        fn_pattern = ''.join(self.FUNCTIONS.keys())
        self.pattern_dynamic = re.compile(
            rf'^([{mv_pattern}])([{fn_pattern}]{{1,3}})[-_]?(\d{{2,4}}[A-Z]?)?$',
            re.IGNORECASE
        )
        
        # Pre-compile set for fast lookup
        self._prefix_set = set(p.upper() for p in self.COMMON_PREFIXES)
    
    # =========================================================================
    # COMPREHENSIVE BAN LIST - Common P&ID words that are NOT instruments
    # =========================================================================
    BAN_LIST = {
        # Equipment labels
        'PUMP', 'TANK', 'VALVE', 'FILTER', 'BURNER', 'BLOWER', 'FAN', 'MOTOR',
        'HEATER', 'COOLER', 'EXCHANGER', 'REACTOR', 'VESSEL', 'DRUM', 'COLUMN',
        'COMPRESSOR', 'TURBINE', 'MIXER', 'AGITATOR', 'SEPARATOR', 'SCRUBBER',
        
        # Process words
        'FEED', 'FLOW', 'INLET', 'OUTLET', 'VENT', 'DRAIN', 'BYPASS', 'RETURN',
        'SUPPLY', 'SUCTION', 'DISCHARGE', 'OVERFLOW', 'RECYCLE', 'BLOWDOWN',
        
        # Substances
        'AIR', 'GAS', 'WATER', 'STEAM', 'OIL', 'FUEL', 'ACID', 'CAUSTIC',
        'NITROGEN', 'OXYGEN', 'HYDROGEN', 'AMMONIA', 'METHANE', 'PROPANE',
        'SLUDGE', 'SLURRY', 'CONDENSATE', 'BRINE', 'COOLANT',
        
        # Directions and locations  
        'TO', 'FROM', 'OFF', 'ON', 'IN', 'OUT', 'UP', 'DOWN',
        'NORTH', 'SOUTH', 'EAST', 'WEST', 'TOP', 'BOTTOM', 'SIDE',
        'LEFT', 'RIGHT', 'FRONT', 'BACK', 'UPPER', 'LOWER',
        
        # Drawing notations
        'LINE', 'PIPE', 'NOTE', 'REV', 'DATE', 'BY', 'DWG', 'SHEET', 'PAGE',
        'TYPICAL', 'TYP', 'SEE', 'REF', 'DETAIL', 'SECTION', 'VIEW', 'AREA',
        'ZONE', 'TAG', 'SIZE', 'SPEC', 'CLASS', 'RATING', 'SCHEDULE',
        
        # Common fragments and noise
        'THE', 'AND', 'FOR', 'WITH', 'THIS', 'THAT', 'NOT', 'ALL', 'NEW', 'OLD',
        'MIN', 'MAX', 'LOW', 'HIGH', 'HOT', 'COLD', 'OPEN', 'CLOSE', 'CLOSED',
        'ING', 'ION', 'ARH', 'ALR', 'ERR', 'END', 'ALM',  # Common OCR fragments
        'ASH', 'ARM', 'COOL', 'JANK',  # Additional 3-4 letter false positives
        
        # Misspellings we've seen
        'COMBUSTION', 'COMBUSTIOM', 'INCINERATOR', 'INCINERATOP',
    }
    
    # Valid ISA S5.1 first letters (measured variables)
    VALID_FIRST_LETTERS = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    
    # Valid ISA S5.1 succeeding letters (functions/modifiers)
    VALID_FUNCTION_LETTERS = set('ACDEGHIKLMNOPQRSTUVWXYZ')
    
    def is_valid_isa_tag(self, text: str) -> bool:
        """
        Check if text matches ISA S5.1 instrument tag pattern.
        RELAXED validation - more permissive to avoid dropping valid tags.
        """
        if not text or len(text) < 2:
            return False
        
        # Normalize
        normalized = text.upper().strip().replace(' ', '').replace('.', '')
        
        # Remove leading/trailing special chars
        normalized = normalized.strip('-_')
        
        if not normalized:
            return False
        
        # =================================================================
        # RULE 0: STRICT BAN LIST CHECK (before anything else!)
        # Extract alpha-only portion and check against ban list
        # =================================================================
        alpha_only = ''.join(c for c in normalized if c.isalpha())
        if alpha_only in self.BAN_LIST or normalized in self.BAN_LIST:
            return False
        
        # =================================================================
        # RULE 1: Must start with a letter
        # =================================================================
        if not normalized[0].isalpha():
            return False
        
        # =================================================================
        # RULE 2: Reject very long strings without numbers (likely words)
        # =================================================================
        has_number = any(c.isdigit() for c in normalized)
        
        # If no numbers AND length > 5, might be a word - BUT still allow 2-4 letter codes
        if not has_number and len(normalized) > 5:
            return False
        
        # =================================================================
        # RULE 3: Check against known ISA patterns (RELAXED)
        # =================================================================
        if self.pattern_standard.match(normalized):
            return True
        
        # Prefix-only valid for 2-4 char codes (FT, TIC, PDIC)
        if len(normalized) >= 2 and len(normalized) <= 4:
            if self.pattern_prefix_only.match(normalized):
                return True
        
        # Dynamic pattern with number
        if self.pattern_dynamic.match(normalized):
            return True
        
        # =================================================================
        # RULE 4: Accept anything that looks like CODE-NUMBER
        # =================================================================
        # Pattern: 2-4 letters + optional dash + 1-4 digits + optional letter
        simple_isa = re.match(r'^[A-Z]{2,4}[-_]?\d{1,4}[A-Z]?$', normalized)
        if simple_isa:
            return True

        # =================================================================
        # RULE 5: FALLBACK - Any short string with letters AND numbers
        # =================================================================
        # OCR often reads FI-101 as F1-101. This catches those edge cases.
        has_letter = any(c.isalpha() for c in normalized)
        if has_letter and has_number and 2 <= len(normalized) <= 12:
            return True
            
        return False
    
    def is_strict_isa_tag(self, text: str) -> bool:
        """
        BULLETPROOF ISA tag validation for floating text (no spatial anchor).
        
        REQUIREMENTS:
        1. Must have 2-4 valid ISA letters at start
        2. MUST contain numbers (loop number)
        3. NOT in ban list
        4. Maximum 10 characters total
        5. First letter must be valid measured variable
        6. Pattern: [A-Z]{2,4}[-_]?[0-9]{2,4}[A-Z]?
        
        PASS: FT-101, PIC202, PSV-001, TT303A, PDIC-400, FIC, TT, PT
        FAIL: FEED, AIR, SLUDGE, BURNER, ING, ALR, COMBUSTIOM
        """
        if not text:
            return False
        
        # =================================================================
        # SANITIZE INPUT: Strip, uppercase, remove special chars except dash
        # =================================================================
        sanitized = text.upper().strip()
        # Remove everything except A-Z, 0-9, and dash
        sanitized = ''.join(c for c in sanitized if c.isalnum() or c == '-')
        
        # =================================================================
        # RULE 1: Strict length constraint
        # =================================================================
        if len(sanitized) < 2:   # Minimum: FT
            return False
        if len(sanitized) > 8:   # Maximum: PDIC-101A (8 chars) - reject anything longer
            return False
        
        # =================================================================
        # RULE 2: Must start with valid letter
        # =================================================================
        if not sanitized[0].isalpha():
            return False
        
        # =================================================================
        # RULE 3: Ban list check - IMMEDIATE REJECTION
        # =================================================================
        # Extract only alphabetic part for ban check
        alpha_only = ''.join(c for c in sanitized if c.isalpha())
        
        if alpha_only in self.BAN_LIST:
            return False
        if sanitized in self.BAN_LIST:
            return False
        
        # =================================================================
        # RULE 4: Strict regex using FULLMATCH (not search!)
        # =================================================================
        # Pattern: 2-4 capital letters, optional dash, optional 1-4 digits
        # This matches: FIC, TT, PT, FT-101, PIC202, PSV-001, TT303A
        strict_pattern = re.compile(r'^[A-Z]{2,4}(?:-?\d{1,4}[A-Z]?)?$')
        
        if not strict_pattern.fullmatch(sanitized):
            return False
        
        # =================================================================
        # RULE 5: If has digits, must have at least 2 letters at start
        # =================================================================
        has_digits = any(c.isdigit() for c in sanitized)
        letter_count = sum(1 for c in sanitized if c.isalpha())
        
        if has_digits and letter_count < 2:
            return False
        
        # =================================================================
        # RULE 6: First letter must be valid ISA measured variable
        # =================================================================
        if sanitized[0] not in self.VALID_FIRST_LETTERS:
            return False
        
        # =================================================================
        # RULE 7: Validate prefix is known or follows ISA structure
        # =================================================================
        # Extract prefix (letters before any digits)
        prefix_match = re.match(r'^([A-Z]+)', sanitized)
        if prefix_match:
            prefix = prefix_match.group(1)
            
            # =============================================================
            # RULE 7b: NO-DIGIT strings MUST be a KNOWN ISA prefix.
            # This is the iron gate that kills "ASH", "ARM", "FEED", etc.
            # Even if they pass all regex checks, if they have NO numbers
            # they are only valid when they are an exact known prefix.
            # =============================================================
            if not has_digits:
                if prefix not in self._prefix_set:
                    print(f"[ISA REJECT] '{sanitized}' has no digits and is not a known ISA prefix")
                    return False
                return True  # Known prefix, no digits (e.g. 'FT', 'TIC', 'PSV')
            
            # Known prefix with digits is always valid
            if prefix in self._prefix_set:
                return True
            
            # Unknown prefix with digits: check ISA structure
            if len(prefix) >= 2:
                # First letter = measured variable, rest = functions
                if prefix[0] in self.VALID_FIRST_LETTERS:
                    if all(c in self.VALID_FUNCTION_LETTERS for c in prefix[1:]):
                        return True
        
        return False
    
    def get_tag_info(self, text: str) -> Dict:
        """
        Parse ISA tag and return component information.
        
        Args:
            text: Valid ISA tag
            
        Returns:
            Dict with measured_variable, function, loop_number
        """
        normalized = text.upper().strip().replace(' ', '')
        
        match = self.pattern_standard.match(normalized)
        if match:
            prefix, number = match.groups()
            return {
                'prefix': prefix,
                'loop_number': number,
                'measured_variable': self.MEASURED_VARIABLES.get(prefix[0], 'Unknown'),
                'function': self.FUNCTIONS.get(prefix[1] if len(prefix) > 1 else '', 'Unknown'),
            }
        
        return {'prefix': normalized, 'loop_number': None}


# =============================================================================
# CONTOUR-BASED CIRCLE DETECTOR (Replaces brittle HoughCircles)
# =============================================================================

class CircleDetector:
    """
    Detects instrument bubbles using CONTOUR CIRCULARITY analysis.
    
    This approach is MORE ROBUST than HoughCircles for scanned P&IDs because:
    - HoughCircles fails on jagged/aliased edges from scanning
    - Contour circularity tolerates imperfect circles
    - Works better with thresholded binary images
    
    CIRCULARITY FORMULA:
        circularity = 4 * π * (area / perimeter²)
        Perfect circle = 1.0
        Rough circle ≥ 0.7
        Rectangle ≈ 0.78
        Triangle ≈ 0.60
    
    For P&ID instrument bubbles:
    - Accept circularity > 0.82 (stricter to avoid letters/curves)
    - Area between 400-5000 px² (radius ~12-40px)
    - Fill ratio > 75% (contour fills its enclosing circle)
    """
    
    # Area bounds for instrument bubbles (in pixels²)
    # radius 15px → area ~706, radius 45px → area ~6361
    # P&ID instrument bubbles are typically 18-40px radius
    MIN_AREA = 700      # ~15px radius minimum (rejects letters/small curves)
    MAX_AREA = 6500     # ~45px radius maximum
    
    # Circularity threshold (1.0 = perfect circle)
    # VERY STRICT: 0.85 rejects nearly all letters/curves
    MIN_CIRCULARITY = 0.85  # Was 0.82 - still too loose
    
    # Aspect ratio bounds (width/height should be near 1.0 for circles)
    MIN_ASPECT_RATIO = 0.85  # Was 0.8 - tighter
    MAX_ASPECT_RATIO = 1.18  # Was 1.25 - tighter
    
    # Fill ratio: contour area / enclosing circle area
    # Real instrument bubbles fill 80%+ of their enclosing circle
    MIN_FILL_RATIO = 0.78  # Was 0.75
    
    # Minimum enclosing circle radius (pixels)
    MIN_RADIUS = 15  # Instrument bubbles are at least 15px radius
    MAX_RADIUS = 50  # Not more than 50px
    
    def __init__(
        self,
        min_area: int = MIN_AREA,
        max_area: int = MAX_AREA,
        min_circularity: float = MIN_CIRCULARITY,
        min_fill_ratio: float = MIN_FILL_RATIO,
        min_radius: float = MIN_RADIUS,
        max_radius: float = MAX_RADIUS,
    ):
        """
        Initialize contour-based circle detector.
        
        Args:
            min_area: Minimum contour area in pixels²
            max_area: Maximum contour area in pixels²
            min_circularity: Minimum circularity score (0-1)
            min_fill_ratio: Minimum fill ratio (contour area / enclosing circle area)
            min_radius: Minimum enclosing circle radius
            max_radius: Maximum enclosing circle radius
        """
        self.min_area = min_area
        self.max_area = max_area
        self.min_circularity = min_circularity
        self.MIN_FILL_RATIO = min_fill_ratio
        self.MIN_RADIUS = min_radius
        self.MAX_RADIUS = max_radius
    
    def detect(self, image: np.ndarray, debug_output_path: str = None) -> List[CircleDetection]:
        """
        Detect circular contours (instrument bubbles) in image.
        
        Args:
            image: BGR or grayscale image
            debug_output_path: If set, saves the binary threshold image here for inspection.
            
        Returns:
            List of CircleDetection objects
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 1)
        
        # Adaptive threshold works better for scanned drawings with uneven lighting
        binary = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            blockSize=11,
            C=2
        )
        
        # Also try Otsu threshold and combine results
        _, otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Combine both threshold results
        combined = cv2.bitwise_or(binary, otsu)
        
        # ── DEBUG: Save the threshold image so you can inspect circle outlines ──
        # If the circles appear as solid blobs instead of outlines, adjust
        # blockSize (increase) or switch to a fixed cv2.threshold value (e.g. 150).
        _debug_path = debug_output_path or "debug_threshold.jpg"
        try:
            cv2.imwrite(_debug_path, combined)
            print(f"[CIRCLE DEBUG] Threshold image saved → {_debug_path}")
        except Exception as _e:
            print(f"[CIRCLE DEBUG] Could not save debug image: {_e}")
        # ─────────────────────────────────────────────────────────────────────
        
        # Morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        cleaned = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel, iterations=1)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Find contours
        contours, _ = cv2.findContours(cleaned, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        
        detections = []
        
        for contour in contours:
            # Calculate area
            area = cv2.contourArea(contour)
            if area < self.min_area or area > self.max_area:
                continue
            
            # Calculate perimeter
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue
            
            # Calculate circularity: 4π(A/P²)
            circularity = 4 * np.pi * (area / (perimeter ** 2))
            
            if circularity < self.min_circularity:
                continue
            
            # Get bounding rectangle for aspect ratio check
            x, y, w, h = cv2.boundingRect(contour)
            if h == 0:
                continue
            
            aspect_ratio = w / h
            if aspect_ratio < self.MIN_ASPECT_RATIO or aspect_ratio > self.MAX_ASPECT_RATIO:
                continue
            
            # Get minimum enclosing circle
            (cx, cy), radius = cv2.minEnclosingCircle(contour)
            
            # RADIUS CHECK: Must be within expected instrument bubble size
            if radius < self.MIN_RADIUS or radius > self.MAX_RADIUS:
                continue
            
            # Additional check: the contour area should be close to the enclosing circle area
            enclosing_area = np.pi * radius ** 2
            fill_ratio = area / enclosing_area if enclosing_area > 0 else 0
            
            # A real instrument bubble fills 78%+ of its enclosing circle
            if fill_ratio < self.MIN_FILL_RATIO:
                continue
            
            detections.append(CircleDetection(
                cx=float(cx),
                cy=float(cy),
                radius=float(radius),
            ))
        
        # Deduplicate overlapping detections
        return self._deduplicate_circles(detections)
    
    def detect_multiscale(self, image: np.ndarray) -> List[CircleDetection]:
        """
        Detect circles using a single, highly-tuned HoughCircles pass.
        
        Optimized for dense P&ID scans where instrument bubbles are well-defined
        but surrounded by noisy text edges and intersecting lines.
        
        Args:
            image: BGR or grayscale image
            
        Returns:
            List of CircleDetection objects (deduplicated)
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 1.5)
        
        # =====================================================================
        # SINGLE HIGHLY-TUNED HOUGH PASS
        # - param1=150: VERY HIGH Canny threshold ignores faint text edges
        # - param2=28:  The sweet spot for vote accumulation
        # - minDist=40: Instrument bubbles rarely overlap on P&IDs
        # =====================================================================
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=40,         # INCREASED: Forces spatial separation
            param1=150,         # VERY HIGH: Ignores noisy text edges
            param2=28,          # Sweet spot for vote accumulation
            minRadius=10,
            maxRadius=35,
        )
        
        all_circles = []
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for c in circles[0, :]:
                all_circles.append(CircleDetection(
                    cx=float(c[0]),
                    cy=float(c[1]),
                    radius=float(c[2]),
                ))
            print(f"[HOUGH] Found {len(circles[0])} circles (param1=150, minDist=40)")
        else:
            print("[HOUGH] Found 0 circles")
        
        return self._deduplicate_circles(all_circles)
    
    def _deduplicate_circles(
        self, 
        circles: List[CircleDetection], 
        distance_threshold: float = 15.0
    ) -> List[CircleDetection]:
        """Remove overlapping circle detections."""
        if not circles:
            return []
        
        # Sort by radius (larger circles first - more likely to be real)
        circles = sorted(circles, key=lambda c: c.radius, reverse=True)
        
        kept = []
        for circle in circles:
            is_duplicate = False
            for existing in kept:
                # Check center distance
                dist = np.sqrt(
                    (circle.cx - existing.cx)**2 + 
                    (circle.cy - existing.cy)**2
                )
                # If centers are close, it's a duplicate
                if dist < distance_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                kept.append(circle)
        
        return kept


# =============================================================================
# SAHI DETECTOR (from previous implementation)
# =============================================================================

class SAHIDetector:
    """SAHI-powered YOLO detector."""
    
    def __init__(
        self,
        model_path: str,
        slice_size: int = 640,
        overlap_ratio: float = 0.25,
        confidence_threshold: float = 0.20,
        device: str = "auto",
    ):
        self.model_path = model_path
        self.slice_size = slice_size
        self.overlap_ratio = overlap_ratio
        self.confidence_threshold = confidence_threshold
        
        if device == "auto":
            import torch
            self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        self._sahi_model = None
        self._yolo_model = None
        self._sahi_available = False
        
        self._load_model()
    
    def _load_model(self):
        """Load model with SAHI or fallback."""
        try:
            from sahi import AutoDetectionModel
            self._sahi_model = AutoDetectionModel.from_pretrained(
                model_type="yolov8",
                model_path=self.model_path,
                confidence_threshold=self.confidence_threshold,
                device=self.device,
            )
            self._sahi_available = True
            print(f"[SAHI] ✓ Model loaded on {self.device}")
        except ImportError:
            print("[SAHI] ✗ SAHI not installed, using fallback")
            self._load_fallback()
        except Exception as e:
            print(f"[SAHI] ✗ Failed: {e}")
            self._load_fallback()
    
    def _load_fallback(self):
        """Load vanilla YOLO."""
        try:
            from ultralytics import YOLO
            self._yolo_model = YOLO(self.model_path)
            print("[SAHI] ✓ Fallback YOLO loaded")
        except Exception as e:
            raise RuntimeError(f"YOLO load failed: {e}")
    
    def detect(self, image: np.ndarray) -> List[DetectedNode]:
        """Run detection and return DetectedNode list."""
        if self._sahi_available:
            return self._detect_sahi(image)
        return self._detect_fallback(image)
    
    def _detect_sahi(self, image: np.ndarray) -> List[DetectedNode]:
        from sahi.predict import get_sliced_prediction
        
        h, w = image.shape[:2]
        
        result = get_sliced_prediction(
            image=image,
            detection_model=self._sahi_model,
            slice_height=min(self.slice_size, h),
            slice_width=min(self.slice_size, w),
            overlap_height_ratio=self.overlap_ratio,
            overlap_width_ratio=self.overlap_ratio,
            postprocess_type="NMS",
            postprocess_match_threshold=0.45,
            verbose=0,
        )
        
        nodes = []
        for pred in result.object_prediction_list:
            bbox = pred.bbox
            nodes.append(DetectedNode(
                class_name=pred.category.name,
                confidence=pred.score.value,
                x1=bbox.minx,
                y1=bbox.miny,
                x2=bbox.maxx,
                y2=bbox.maxy,
                source=DetectionSource.YOLO,
                is_instrument="instrument" in pred.category.name.lower(),
            ))
        
        return nodes
    
    def _detect_fallback(self, image: np.ndarray) -> List[DetectedNode]:
        results = self._yolo_model(image, conf=self.confidence_threshold, verbose=False)
        
        nodes = []
        for r in results:
            if r.boxes is None:
                continue
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                cls_name = self._yolo_model.names[cls_id]
                
                nodes.append(DetectedNode(
                    class_name=cls_name,
                    confidence=conf,
                    x1=x1, y1=y1, x2=x2, y2=y2,
                    source=DetectionSource.YOLO,
                    is_instrument="instrument" in cls_name.lower(),
                ))
        
        return nodes


# =============================================================================
# PADDLEOCR ENGINE (from previous implementation)
# =============================================================================

class PaddleOCREngine:
    """PaddleOCR text extractor."""
    
    def __init__(self, use_gpu: bool = True):
        self._ocr = None
        self._easyocr = None
        
        try:
            # Disable OneDNN to avoid Windows compatibility issues
            import os
            os.environ["FLAGS_use_mkldnn"] = "0"
            os.environ["MKLDNN_CACHE_CAPACITY"] = "0"
            os.environ["FLAGS_enable_pir_api"] = "0"
            os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"  # Skip connectivity check
            
            from paddleocr import PaddleOCR
            
            # SPEED-OPTIMIZED PaddleOCR - using MOBILE models (10x faster than server models)
            self._ocr = PaddleOCR(
                lang="en",
                use_angle_cls=False,         # CRITICAL: Disable angle classification (slow)
                enable_mkldnn=False,         # Disable MKLDNN (Windows bug)
                # DETECTION MODEL: Use mobile (fast) instead of server (slow)
                det_model_dir=None,          # Let it use default mobile model
                det_limit_side_len=960,      # Default size (don't upscale internally)
                det_db_thresh=0.3,           # Standard threshold
                det_db_box_thresh=0.5,       # Standard box threshold
                # RECOGNITION MODEL: Use mobile (fast)
                rec_model_dir=None,          # Let it use default mobile model
                rec_batch_num=6,             # Batch size
            )
            print("[OCR] ✓ PaddleOCR initialized (mobile models - FAST)")
        except ImportError:
            print("[OCR] ✗ PaddleOCR not found, trying EasyOCR")
            self._init_easyocr(use_gpu)
        except Exception as e:
            print(f"[OCR] ✗ PaddleOCR failed: {e}")
            self._init_easyocr(use_gpu)
    
    def _init_easyocr(self, use_gpu: bool):
        try:
            import easyocr
            self._easyocr = easyocr.Reader(['en'], gpu=use_gpu, verbose=False)
            print("[OCR] ✓ EasyOCR initialized (fallback)")
        except:
            print("[OCR] ✗ No OCR engine available!")
    
    def extract(self, image: np.ndarray) -> List[OCRText]:
        if self._ocr:
            try:
                return self._extract_paddle(image)
            except Exception as e:
                print(f"[OCR] PaddleOCR extraction failed: {e}")
                # Fall back to EasyOCR if PaddleOCR fails at runtime
                if not self._easyocr:
                    self._init_easyocr(False)
                if self._easyocr:
                    return self._extract_easyocr(image)
        elif self._easyocr:
            return self._extract_easyocr(image)
        return []
    
    def _extract_paddle(self, image: np.ndarray) -> List[OCRText]:
        """Safely extract text - handles PaddleOCR v2.x AND v3.x/PaddleX formats."""
        h, w = image.shape[:2]
        print(f"[OCR] Processing {w}x{h} image at original resolution (fast mode)")
        
        # 1. Run OCR safely - try both APIs (v3/PaddleX uses predict, v2 uses ocr)
        raw_results = None
        try:
            # Try .ocr() first (PaddleOCR v2.x style)
            raw_results = self._ocr.ocr(image) 
            print("[OCR] ✓ PaddleOCR completed (ocr API)")
        except Exception as e:
            print(f"[OCR DEBUG] ocr() API failed: {e}, trying predict()...")
            try:
                # Try .predict() (PaddleX/v3 style)
                raw_results = self._ocr.predict(image)
                print("[OCR] ✓ PaddleOCR completed (predict API)")
            except Exception as e2:
                print(f"[OCR] ✗ PaddleOCR failed with both APIs: ocr={e}, predict={e2}")
                return []
            
        texts = []
        if not raw_results:
            print("[OCR DEBUG] raw_results is None or empty")
            return texts
        
        # DEBUG: Print the structure of raw_results
        print(f"[OCR DEBUG] raw_results type: {type(raw_results)}")
        
        # =====================================================================
        # FORMAT 0: PaddleX v3 returns a LIST of result objects.
        # Each element in the list has singular .dt_polys and .rec_text attrs.
        # This is the MOST COMMON failure point - check this FIRST.
        # Example: raw_results = [<OCRResult dt_polys=[...] rec_text='FIC'>]
        # =====================================================================
        if isinstance(raw_results, list) and len(raw_results) > 0:
            first = raw_results[0]
            # Check if it's a PaddleX result object (has singular rec_text)
            if hasattr(first, 'dt_polys') or hasattr(first, 'rec_text'):
                print("[OCR DEBUG] FORMAT 0: PaddleX list-of-result-objects detected")
                for page_obj in raw_results:
                    try:
                        # Extract fields - use both singular and plural names
                        rec_texts = (
                            getattr(page_obj, 'rec_texts', None) or
                            [getattr(page_obj, 'rec_text', None)]
                        )
                        rec_scores = (
                            getattr(page_obj, 'rec_scores', None) or
                            getattr(page_obj, 'rec_score', None) or
                            [0.9] * len(rec_texts)
                        )
                        dt_polys = (
                            getattr(page_obj, 'dt_polys', None) or []
                        )
                        
                        # Normalise to lists
                        if not isinstance(rec_texts, (list, tuple)):
                            rec_texts = [rec_texts]
                        if not isinstance(rec_scores, (list, tuple)):
                            rec_scores = [rec_scores]
                        if not isinstance(dt_polys, (list, tuple)):
                            dt_polys = [dt_polys]
                        
                        print(f"[OCR DEBUG] FORMAT 0: {len(rec_texts)} texts in this page object")
                        
                        for i, (text, score) in enumerate(zip(rec_texts, rec_scores)):
                            if not text:
                                continue
                            text = str(text).strip()
                            score = float(score) if score is not None else 0.9
                            print(f"[OCR RAW] '{text}' (conf={score:.2f})")
                            
                            if i < len(dt_polys) and dt_polys[i] is not None:
                                poly = dt_polys[i]
                                try:
                                    xs = [float(p[0]) for p in poly]
                                    ys = [float(p[1]) for p in poly]
                                    texts.append(OCRText(
                                        text=text,
                                        confidence=score,
                                        x1=min(xs), y1=min(ys),
                                        x2=max(xs), y2=max(ys)
                                    ))
                                except Exception as poly_err:
                                    print(f"[OCR DEBUG] FORMAT 0 poly error: {poly_err}")
                                    texts.append(OCRText(text=text, confidence=score,
                                                         x1=0, y1=0, x2=100, y2=20))
                            else:
                                texts.append(OCRText(text=text, confidence=score,
                                                     x1=0, y1=0, x2=100, y2=20))
                    except Exception as e:
                        print(f"[OCR DEBUG] FORMAT 0 page parse error: {e}")
                        continue
                
                if texts:
                    print(f"[OCR DEBUG] FORMAT 0: Parsed {len(texts)} text blocks successfully")
                    return texts
                print("[OCR DEBUG] FORMAT 0 returned no texts, falling through to other formats")
        
        # =====================================================================
        # FORMAT 1: PaddleX top-level object (has .rec_texts plural + .dt_polys)
        # Older / single-image PaddleX API style.
        # =====================================================================
        if hasattr(raw_results, 'rec_texts') and hasattr(raw_results, 'dt_polys'):
            print("[OCR DEBUG] FORMAT 1: PaddleX top-level result object")
            try:
                rec_texts = raw_results.rec_texts if hasattr(raw_results, 'rec_texts') else []
                rec_scores = raw_results.rec_scores if hasattr(raw_results, 'rec_scores') else [0.9]*len(rec_texts)
                dt_polys = raw_results.dt_polys if hasattr(raw_results, 'dt_polys') else []
                
                print(f"[OCR DEBUG] FORMAT 1: {len(rec_texts)} text items")
                
                for i, (text, score) in enumerate(zip(rec_texts, rec_scores)):
                    if not text:
                        continue
                    print(f"[OCR RAW] '{text}' (conf={score:.2f})")
                    
                    if i < len(dt_polys):
                        poly = dt_polys[i]
                        xs = [p[0] for p in poly]
                        ys = [p[1] for p in poly]
                        texts.append(OCRText(
                            text=str(text).strip(),
                            confidence=float(score),
                            x1=min(xs), y1=min(ys),
                            x2=max(xs), y2=max(ys)
                        ))
                    else:
                        texts.append(OCRText(
                            text=str(text).strip(),
                            confidence=float(score),
                            x1=0, y1=0, x2=100, y2=20
                        ))
                        
                print(f"[OCR DEBUG] FORMAT 1: Parsed {len(texts)} text blocks")
                return texts
            except Exception as e:
                print(f"[OCR DEBUG] FORMAT 1 parsing failed: {e}")
        
        # =====================================================================
        # FORMAT 2: PaddleOCR v2 style - list of pages, each a list of items.
        # Each item: [[bbox_poly], ('text', conf)]
        # =====================================================================
        if hasattr(raw_results, '__len__'):
            print(f"[OCR DEBUG] raw_results length: {len(raw_results)}")
        else:
            print(f"[OCR DEBUG] raw_results is not iterable, type: {type(raw_results)}")
            if hasattr(raw_results, '__dict__'):
                print(f"[OCR DEBUG] raw_results attributes: {list(raw_results.__dict__.keys())}")
            return texts
            
        # Get the first page results safely
        page_result = raw_results[0] if isinstance(raw_results, list) and len(raw_results) > 0 else raw_results
        if not page_result:
            print("[OCR DEBUG] page_result is None or empty")
            return texts
        
        page_type_name = type(page_result).__name__
        page_len = len(page_result) if hasattr(page_result, '__len__') else 'N/A'
        print(f"[OCR DEBUG] FORMAT 2: page_result type={page_type_name}, len={page_len}")
        
        # =====================================================================
        # FORMAT 2-PADDLEX: Check if page_result is a PaddleX OCRResult object
        # OCRResult SUBCLASSES dict - so use .get() not getattr()!
        # =====================================================================
        if 'OCRResult' in page_type_name or 'Result' in page_type_name or isinstance(page_result, dict):
            print(f"[OCR DEBUG] FORMAT 2-PADDLEX: Detected {page_type_name} (dict-like)")
            
            # Print available keys for debugging
            if isinstance(page_result, dict):
                print(f"[OCR DEBUG] FORMAT 2-PADDLEX keys: {list(page_result.keys())[:15]}")
            
            try:
                # PaddleX OCRResult is a dict subclass - use .get() NOT getattr()!
                rec_texts = page_result.get('rec_texts') or page_result.get('rec_text')
                rec_scores = page_result.get('rec_scores') or page_result.get('rec_score')
                dt_polys = page_result.get('dt_polys') or page_result.get('boxes') or page_result.get('text_region')
                
                # Convert single values to lists
                if rec_texts is not None and not isinstance(rec_texts, (list, tuple)):
                    rec_texts = [rec_texts]
                if rec_scores is not None and not isinstance(rec_scores, (list, tuple)):
                    rec_scores = [rec_scores]
                if dt_polys is not None and not isinstance(dt_polys, (list, tuple)):
                    dt_polys = [dt_polys]
                
                print(f"[OCR DEBUG] FORMAT 2-PADDLEX: rec_texts={type(rec_texts)}, count={len(rec_texts) if rec_texts else 0}")
                print(f"[OCR DEBUG] FORMAT 2-PADDLEX: dt_polys={type(dt_polys)}, count={len(dt_polys) if dt_polys else 0}")
                
                if rec_texts:
                    if rec_scores is None:
                        rec_scores = [0.9] * len(rec_texts)
                    if dt_polys is None:
                        dt_polys = [None] * len(rec_texts)
                    
                    for i, text in enumerate(rec_texts):
                        if not text:
                            continue
                        text = str(text).strip()
                        score = float(rec_scores[i]) if i < len(rec_scores) and rec_scores[i] is not None else 0.9
                        
                        print(f"[OCR RAW] '{text}' (conf={score:.2f})")
                        
                        poly = dt_polys[i] if i < len(dt_polys) else None
                        if poly is not None and len(poly) >= 4:
                            try:
                                xs = [float(p[0]) for p in poly]
                                ys = [float(p[1]) for p in poly]
                                texts.append(OCRText(
                                    text=text,
                                    confidence=score,
                                    x1=min(xs), y1=min(ys),
                                    x2=max(xs), y2=max(ys)
                                ))
                            except Exception as poly_err:
                                print(f"[OCR DEBUG] Poly parse error for '{text}': {poly_err}")
                                texts.append(OCRText(text=text, confidence=score,
                                                     x1=0, y1=0, x2=100, y2=20))
                        else:
                            texts.append(OCRText(text=text, confidence=score,
                                                 x1=0, y1=0, x2=100, y2=20))
                    
                    print(f"[OCR DEBUG] FORMAT 2-PADDLEX: Parsed {len(texts)} text blocks")
                    return texts
                else:
                    print("[OCR DEBUG] FORMAT 2-PADDLEX: No rec_texts found, trying iteration")
                    
            except Exception as e:
                print(f"[OCR DEBUG] FORMAT 2-PADDLEX parse failed: {e}, trying iteration")
        
        # =====================================================================
        # FORMAT 2-LIST: page_result is a list of [bbox, (text, conf)] items
        # =====================================================================
        if not hasattr(page_result, '__iter__'):
            print("[OCR DEBUG] page_result is not iterable, skipping FORMAT 2-LIST")
            return texts
            
        # Try to get first item safely for debugging
        try:
            if hasattr(page_result, '__getitem__'):
                first_item = page_result[0]
                print(f"[OCR DEBUG] FORMAT 2-LIST: First item type: {type(first_item)}")
                print(f"[OCR DEBUG] FORMAT 2-LIST: First item: {str(first_item)[:200]}")
        except Exception as e:
            print(f"[OCR DEBUG] FORMAT 2-LIST: Could not get first item: {e}")
            
        # Only iterate if it's a true list/tuple, not a PaddleX result object
        if not isinstance(page_result, (list, tuple)):
            print(f"[OCR DEBUG] FORMAT 2-LIST: page_result is {type(page_result)}, not list/tuple - skipping iteration")
            return texts
            
        for idx, item in enumerate(page_result):
            try:
                bbox_points = None
                text = None
                conf = 0.9
                
                # FORMAT 2a: Dictionary
                if isinstance(item, dict):
                    text = item.get('text', item.get('rec_text', ''))
                    conf = item.get('confidence', item.get('rec_score', item.get('score', 0.9)))
                    bbox_points = item.get('text_region', item.get('dt_polys', item.get('points', [])))
                    print(f"[OCR DEBUG] FORMAT 2a (dict): text='{text}'")
                
                # FORMAT 2b: [bbox, (text, conf)]
                elif isinstance(item, (list, tuple)) and len(item) == 2:
                    bbox_points = item[0]
                    text_info = item[1]
                    
                    if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                        text = str(text_info[0]).strip()
                        conf = float(text_info[1])
                    elif isinstance(text_info, str):
                        text = text_info
                        conf = 0.9
                    print(f"[OCR DEBUG] FORMAT 2b (list len=2): text='{text}'")
                
                # FORMAT 2c: More elements
                elif isinstance(item, (list, tuple)) and len(item) > 2:
                    for sub_item in item:
                        if isinstance(sub_item, str) and len(sub_item) > 0:
                            text = sub_item
                        elif isinstance(sub_item, (int, float)) and 0 <= sub_item <= 1:
                            conf = float(sub_item)
                        elif isinstance(sub_item, list) and len(sub_item) >= 4:
                            bbox_points = sub_item
                    print(f"[OCR DEBUG] FORMAT 2c (list len>2): text='{text}'")
                
                # FORMAT 2d: Object with attributes
                elif hasattr(item, 'text') or hasattr(item, 'rec_text'):
                    text = getattr(item, 'text', None) or getattr(item, 'rec_text', '')
                    conf = getattr(item, 'confidence', None) or getattr(item, 'score', 0.9)
                    bbox_points = getattr(item, 'text_region', None) or getattr(item, 'dt_polys', [])
                    print(f"[OCR DEBUG] FORMAT 2d (object): text='{text}'")
                
                else:
                    print(f"[OCR DEBUG] Unknown format for item {idx}: type={type(item)}, content={str(item)[:100]}")
                    continue
                
                if not text:
                    continue
                    
                if bbox_points and len(bbox_points) >= 4:
                    try:
                        xs = [float(p[0]) for p in bbox_points]
                        ys = [float(p[1]) for p in bbox_points]
                        
                        print(f"[OCR RAW] '{text}' (conf={conf:.2f})")
                        
                        texts.append(OCRText(
                            text=str(text).strip(),
                            confidence=float(conf),
                            x1=min(xs),
                            y1=min(ys),
                            x2=max(xs),
                            y2=max(ys)
                        ))
                    except Exception as bbox_err:
                        print(f"[OCR DEBUG] Bbox parse error for '{text}': {bbox_err}")
                else:
                    print(f"[OCR RAW] '{text}' (conf={conf:.2f}) - NO BBOX")
                    texts.append(OCRText(
                        text=str(text).strip(),
                        confidence=float(conf),
                        x1=0, y1=0, x2=100, y2=20
                    ))
                    
            except Exception as e:
                print(f"[OCR DEBUG] Skipped item {idx} due to parsing error: {e}")
                
        print(f"[OCR DEBUG] FORMAT 2: Parsed {len(texts)} text blocks successfully")
        return texts
    
    def _extract_easyocr(self, image: np.ndarray) -> List[OCRText]:
        """Extract text using EasyOCR with upscaling for small text."""
        # Conditional upscaling for small images
        h, w = image.shape[:2]
        megapixels = (w * h) / 1_000_000
        
        if megapixels < 2.0:
            scale_factor = 1.5  # Upscale small images
            upscaled_image = cv2.resize(image, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
            print(f"[OCR] Upscaled {w}x{h} ({megapixels:.1f}MP) → {upscaled_image.shape[1]}x{upscaled_image.shape[0]} ({scale_factor}x)")
        else:
            scale_factor = 1.0
            upscaled_image = image
        
        results = self._easyocr.readtext(upscaled_image)
        
        texts = []
        for bbox, text, conf in results:
            xs = [p[0] / scale_factor for p in bbox]
            ys = [p[1] / scale_factor for p in bbox]
            texts.append(OCRText(
                text=text.strip(),
                confidence=conf,
                x1=min(xs), y1=min(ys),
                x2=max(xs), y2=max(ys),
            ))
        return texts


# =============================================================================
# HYBRID PERCEPTION PIPELINE (MAIN CLASS)
# =============================================================================

class HybridPerceptionPipeline:
    """
    Hybrid Perception Pipeline combining YOLO + Hough Circles + Regex.
    
    Detection Strategy:
    ┌─────────────────────────────────────────────────────────────────┐
    │                     DETECTION SOURCES                           │
    ├─────────────────────────────────────────────────────────────────┤
    │  1. YOLO/SAHI → Valves, Equipment, Fittings, (some Instruments)│
    │  2. HoughCircles → Instrument Bubbles (catches YOLO blind spots)│
    │  3. ISA Regex → OCR text validation → Force-promote to Node    │
    └─────────────────────────────────────────────────────────────────┘
    
    Merging Strategy:
    ┌─────────────────────────────────────────────────────────────────┐
    │ For each OCR text block:                                        │
    │  1. Is it inside/near a YOLO detection? → Assign as tag        │
    │  2. Is it inside/near a Hough Circle? → Create Instrument Node │
    │  3. Does it match ISA Regex? → Force-create Instrument Node    │
    │  4. None of the above? → Discard as floating text              │
    └─────────────────────────────────────────────────────────────────┘
    """
    
    # Text-to-symbol proximity thresholds (pixels)
    YOLO_PROXIMITY_THRESHOLD = 80.0    # Relaxed from 60px
    CIRCLE_PROXIMITY_THRESHOLD = 30.0  # Text should be inside or very close to circle
    
    def __init__(
        self,
        model_path: str,
        # SAHI parameters
        slice_size: int = 640,
        overlap_ratio: float = 0.25,
        confidence_threshold: float = 0.20,
        # Circle detection parameters
        # min_radius reduced from 15→8 to catch small instrument bubbles on
        # scanned P&IDs (radius 8px → area ~200px²)
        circle_min_radius: int = 8,
        circle_max_radius: int = 60,
        # Hardware
        use_gpu: bool = True,
    ):
        """
        Initialize Hybrid Perception Pipeline.
        
        Args:
            model_path: Path to YOLOv8 model (best.pt)
            slice_size: SAHI tile size
            overlap_ratio: SAHI tile overlap
            confidence_threshold: YOLO confidence threshold
            circle_min_radius: Min radius for HoughCircles
            circle_max_radius: Max radius for HoughCircles
            use_gpu: Use GPU acceleration
        """
        print("=" * 70)
        print("EDAI4 HYBRID PERCEPTION PIPELINE")
        print("  YOLO/SAHI + HoughCircles + ISA Regex")
        print("=" * 70)
        
        # Validate model path
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        # Initialize components
        print("\n[INIT] Loading SAHI/YOLO detector...")
        self.yolo_detector = SAHIDetector(
            model_path=model_path,
            slice_size=slice_size,
            overlap_ratio=overlap_ratio,
            confidence_threshold=confidence_threshold,
        )
        
        print("[INIT] Loading PaddleOCR...")
        self.ocr_engine = PaddleOCREngine(use_gpu=use_gpu)
        
        print("[INIT] Initializing CircleDetector (contour-based)...")
        # Convert radius to area (area = π * r²)
        # min_radius=15 → min_area ≈ 706
        # max_radius=60 → max_area ≈ 11309
        import math
        min_area = int(math.pi * circle_min_radius ** 2)
        max_area = int(math.pi * circle_max_radius ** 2)
        
        self.circle_detector = CircleDetector(
            min_area=min_area,
            max_area=max_area,
            min_circularity=0.82,      # STRICTER: was 0.70, rejects 'C', 'D', 'O' letters
            min_fill_ratio=0.75,       # Contour must fill 75%+ of enclosing circle
        )
        
        print("[INIT] Initializing ISA tag validator...")
        self.isa_validator = ISATagValidator()
        
        print("=" * 70)
        print("✓ Hybrid Pipeline Ready!")
        print("=" * 70)
    
    def process(self, image_path_or_array) -> HybridPipelineResult:
        """
        Process P&ID image through hybrid detection pipeline.
        
        Args:
            image_path_or_array: Path to image or numpy array (BGR)
            
        Returns:
            HybridPipelineResult with all detections and statistics
        """
        timing = {}
        stats = {}
        
        # Load image
        if isinstance(image_path_or_array, str):
            print(f"\n[PIPELINE] Loading: {image_path_or_array}")
            image = cv2.imread(image_path_or_array)
            if image is None:
                raise ValueError(f"Failed to load: {image_path_or_array}")
        else:
            image = image_path_or_array
        
        h, w = image.shape[:2]
        print(f"[PIPELINE] Image size: {w}x{h}")
        
        # =====================================================================
        # STAGE 1: YOLO/SAHI Detection
        # =====================================================================
        print("\n" + "=" * 50)
        print("STAGE 1: YOLO/SAHI Detection")
        print("=" * 50)
        
        t0 = time.time()
        yolo_nodes = self.yolo_detector.detect(image)
        timing["yolo_ms"] = (time.time() - t0) * 1000
        
        stats["yolo_detections"] = len(yolo_nodes)
        print(f"[YOLO] Found {len(yolo_nodes)} detections")
        
        # =====================================================================
        # STAGE 2: PaddleOCR Text Extraction
        # =====================================================================
        print("\n" + "=" * 50)
        print("STAGE 2: PaddleOCR Text Extraction")
        print("=" * 50)
        
        t0 = time.time()
        text_blocks = self.ocr_engine.extract(image)
        timing["ocr_ms"] = (time.time() - t0) * 1000
        
        # Mark ISA tags (RELAXED validation - don't be too strict!)
        for text in text_blocks:
            text.is_isa_tag = self.isa_validator.is_valid_isa_tag(text.text)
            # Log what ISA validator thinks
            if text.is_isa_tag:
                print(f"[ISA ✓] '{text.text}' recognized as ISA tag")
            else:
                print(f"[ISA ✗] '{text.text}' rejected by ISA validator")
        
        isa_count = sum(1 for t in text_blocks if t.is_isa_tag)
        stats["ocr_total"] = len(text_blocks)
        stats["isa_tags_found"] = isa_count
        print(f"[OCR] Found {len(text_blocks)} text blocks ({isa_count} ISA tags)")
        
        # =====================================================================
        # STAGE 3: HoughCircle Detection
        # =====================================================================
        print("\n" + "=" * 50)
        print("STAGE 3: HoughCircle Detection (Instrument Bubbles)")
        print("=" * 50)
        
        t0 = time.time()
        circles = self.circle_detector.detect_multiscale(image)
        timing["circle_ms"] = (time.time() - t0) * 1000
        
        stats["circles_detected"] = len(circles)
        print(f"[HOUGH] Found {len(circles)} circles")
        
        # =====================================================================
        # STAGE 4: Hybrid Merging Logic
        # =====================================================================
        print("\n" + "=" * 50)
        print("STAGE 4: Hybrid Merging")
        print("=" * 50)
        
        t0 = time.time()
        
        # ── STEP 4.5: Merge split OCR fragments inside the same circle ──────
        # PaddleOCR often reads "FIC" and "101" as two blocks inside one bubble.
        # This groups them by circle and concatenates top-to-bottom before ISA
        # validation so "FIC" + "101" → "FIC-101" which passes is_strict_isa_tag.
        text_blocks = self._merge_split_text_in_circles(text_blocks, circles)
        # Re-stamp ISA tags after merge
        for text in text_blocks:
            text.is_isa_tag = self.isa_validator.is_valid_isa_tag(text.text)
        # ─────────────────────────────────────────────────────────────────────
        
        # Start with YOLO detections
        all_nodes = list(yolo_nodes)
        discarded_text = []
        
        # Process each text block
        for text in text_blocks:
            matched = False
            
            # -----------------------------------------------------------------
            # Step 1: Try to match to YOLO detection
            # -----------------------------------------------------------------
            for node in yolo_nodes:
                if self._is_text_near_bbox(text, node):
                    if node.tag is None:  # Don't overwrite existing tags
                        node.tag = text.text.upper()
                        text.matched_to_node = True
                        matched = True
                        print(f"  [YOLO] '{text.text}' → {node.class_name}")
                    break
            
            if matched:
                continue
            
            # -----------------------------------------------------------------
            # Step 2: Try to match to Hough Circle
            # IRON GATE: Text inside circle must ALSO pass ISA validation
            # -----------------------------------------------------------------
            for circle in circles:
                if self._is_text_strictly_inside_circle(text, circle):
                    # Only create instrument if text is a valid ISA tag
                    if not text.is_isa_tag:
                        # Text inside circle but not ISA - just associate, don't create node
                        circle.matched_text = text.text.upper()
                        text.matched_to_node = True  # Mark as processed
                        print(f"  [CIRCLE] '{text.text}' inside circle but NOT ISA - skipped")
                        matched = True
                        break
                    
                    circle.matched_text = text.text.upper()
                    text.matched_to_node = True
                    matched = True
                    
                    # Create instrument node from circle
                    new_node = DetectedNode(
                        class_name="instrument.bubble",
                        confidence=0.85,  # Heuristic confidence
                        x1=circle.x1,
                        y1=circle.y1,
                        x2=circle.x2,
                        y2=circle.y2,
                        source=DetectionSource.HOUGH_CIRCLE,
                        tag=text.text.upper(),
                        is_instrument=True,
                    )
                    
                    # Check for duplicate (don't add if YOLO already found it)
                    if not self._is_duplicate_node(new_node, all_nodes):
                        all_nodes.append(new_node)
                        print(f"  [CIRCLE] '{text.text}' → instrument.bubble")
                    break
            
            if matched:
                continue
            
            # -----------------------------------------------------------------
            # Step 3: ISA Regex Bypass - ONLY for STRICT ISA tags
            # Uses is_strict_isa_tag() which requires numbers (e.g., FT-101)
            # This prevents dictionary words like "SLUDGE" from becoming nodes
            # -----------------------------------------------------------------
            if self.isa_validator.is_strict_isa_tag(text.text):
                text.matched_to_node = True
                
                # Create instrument node centered on text
                cx, cy = text.center
                radius = 25  # Default radius for text-only instrument
                
                new_node = DetectedNode(
                    class_name="instrument.bubble",
                    confidence=0.70,  # Lower confidence for regex-only
                    x1=cx - radius,
                    y1=cy - radius,
                    x2=cx + radius,
                    y2=cy + radius,
                    source=DetectionSource.ISA_REGEX,
                    tag=text.text.upper(),
                    is_instrument=True,
                )
                
                if not self._is_duplicate_node(new_node, all_nodes):
                    all_nodes.append(new_node)
                    print(f"  [REGEX] '{text.text}' → instrument.bubble (strict ISA match)")
                
                continue
            
            # -----------------------------------------------------------------
            # Step 4: Not matched anywhere → Discard as floating text
            # -----------------------------------------------------------------
            discarded_text.append(text)
        
        # =====================================================================
        # CRITICAL FIX: Add unmatched circles as nodes (don't discard them!)
        # =====================================================================
        for circle in circles:
            # If circle doesn't have matched text, add it anyway as an instrument bubble
            if not hasattr(circle, 'matched_text') or not circle.matched_text:
                new_node = DetectedNode(
                    class_name="instrument.bubble",
                    confidence=0.80,  # Good confidence from contour detection
                    x1=circle.x1,
                    y1=circle.y1,
                    x2=circle.x2,
                    y2=circle.y2,
                    source=DetectionSource.HOUGH_CIRCLE,
                    tag=None,  # No tag yet
                    is_instrument=True,
                )
                
                # Check for duplicate (don't add if already exists)
                if not self._is_duplicate_node(new_node, all_nodes):
                    all_nodes.append(new_node)
                    print(f"  [CIRCLE] Unmatched circle added as instrument.bubble (no tag yet)")
        
        timing["merge_ms"] = (time.time() - t0) * 1000
        timing["total_ms"] = sum(timing.values())
        
        # Calculate final stats
        stats["final_nodes"] = len(all_nodes)
        stats["instruments"] = sum(1 for n in all_nodes if n.is_instrument)
        stats["valves"] = sum(1 for n in all_nodes if "valve" in n.class_name.lower())
        stats["equipment"] = sum(1 for n in all_nodes 
                                  if any(x in n.class_name.lower() 
                                        for x in ["pump", "compressor", "equipment"]))
        stats["discarded_text"] = len(discarded_text)
        stats["nodes_from_yolo"] = sum(1 for n in all_nodes if n.source == DetectionSource.YOLO)
        stats["nodes_from_circles"] = sum(1 for n in all_nodes if n.source == DetectionSource.HOUGH_CIRCLE)
        stats["nodes_from_regex"] = sum(1 for n in all_nodes if n.source == DetectionSource.ISA_REGEX)
        
        # =====================================================================
        # Summary
        # =====================================================================
        print("\n" + "=" * 70)
        print("HYBRID PIPELINE COMPLETE")
        print("=" * 70)
        print(f"  YOLO detections:        {stats['yolo_detections']}")
        print(f"  OCR text blocks:        {stats['ocr_total']} ({stats['isa_tags_found']} ISA tags)")
        print(f"  Hough circles:          {stats['circles_detected']}")
        print(f"  ")
        print(f"  FINAL NODE COUNT:       {stats['final_nodes']}")
        print(f"    → From YOLO:          {stats['nodes_from_yolo']}")
        print(f"    → From HoughCircles:  {stats['nodes_from_circles']}")
        print(f"    → From ISA Regex:     {stats['nodes_from_regex']}")
        print(f"  ")
        print(f"  Instruments:            {stats['instruments']}")
        print(f"  Valves:                 {stats['valves']}")
        print(f"  Equipment:              {stats['equipment']}")
        print(f"  Discarded text:         {stats['discarded_text']}")
        print(f"  ")
        print(f"  Total time:             {timing['total_ms']:.0f}ms")
        print(f"    → YOLO:               {timing['yolo_ms']:.0f}ms")
        print(f"    → OCR:                {timing['ocr_ms']:.0f}ms")
        print(f"    → Circles:            {timing['circle_ms']:.0f}ms")
        print(f"    → Merging:            {timing['merge_ms']:.0f}ms")
        
        return HybridPipelineResult(
            nodes=all_nodes,
            text_blocks=text_blocks,
            circles=circles,
            discarded_text=discarded_text,
            timing=timing,
            stats=stats,
            image_size=(w, h),
        )
    
    def _is_text_near_bbox(self, text: OCRText, node: DetectedNode) -> bool:
        """Check if text is inside or near a node's bounding box."""
        tx, ty = text.center
        
        # Inside bbox
        if node.x1 <= tx <= node.x2 and node.y1 <= ty <= node.y2:
            return True
        
        # Near bbox (within threshold)
        cx = max(node.x1, min(tx, node.x2))
        cy = max(node.y1, min(ty, node.y2))
        dist = np.sqrt((tx - cx)**2 + (ty - cy)**2)
        
        return dist <= self.YOLO_PROXIMITY_THRESHOLD
    
    def _is_text_strictly_inside_bbox(self, text: OCRText, node: DetectedNode) -> bool:
        """
        STRICT check: Text center must be INSIDE the bounding box.
        No proximity threshold - pure geometric containment.
        """
        tx, ty = text.center
        return node.x1 <= tx <= node.x2 and node.y1 <= ty <= node.y2
    
    def _is_text_inside_circle(self, text: OCRText, circle: CircleDetection) -> bool:
        """Check if text center is inside or very close to circle."""
        tx, ty = text.center
        dist = np.sqrt((tx - circle.cx)**2 + (ty - circle.cy)**2)
        
        # Inside circle or within tight threshold
        return dist <= circle.radius + self.CIRCLE_PROXIMITY_THRESHOLD
    
    def _is_text_strictly_inside_circle(self, text: OCRText, circle: CircleDetection) -> bool:
        """
        Forgiving check: Does the text bounding box intersect or sit close to the circle?
        
        Uses closest-point-on-bbox to circle-center distance check.
        This is more tolerant of OCR bboxes that partially overlap the circle.
        """
        # Get the closest point on the text bounding box to the circle's center
        closest_x = max(text.x1, min(circle.cx, text.x2))
        closest_y = max(text.y1, min(circle.cy, text.y2))
        
        # Calculate distance from the closest bounding box point to the circle center
        dist = np.sqrt((closest_x - circle.cx)**2 + (closest_y - circle.cy)**2)
        
        # If the bounding box touches the circle (plus 5px leeway), it's inside!
        return dist <= circle.radius + 5.0
    
    def _merge_split_text_in_circles(
        self,
        text_blocks: List[OCRText],
        circles: List[CircleDetection],
    ) -> List[OCRText]:
        """
        Merge vertically-stacked OCR fragments inside the same circle.

        PaddleOCR often splits a bubble tag into two lines:
          - Top block:    "FIC"  (y=300)
          - Bottom block: "101"  (y=320)
        Both are inside the same Hough circle but neither passes ISA strict
        validation alone. This method concatenates them top-to-bottom:
            "FIC" + "-" + "101" = "FIC-101"  which passes is_strict_isa_tag.

        RULES:
        - Only merge if EXACTLY 2-3 text blocks share the same circle (not 5+).
        - Combined text must be ≤12 characters (ISA tags are short).
        - Sort by Y (top → bottom), join alpha prefix + digit suffix with "-".
        - The merged block inherits the highest confidence of its fragments.
        """
        if not circles or not text_blocks:
            return text_blocks

        used_ids: Set = set()
        merged_blocks: List[OCRText] = []

        for circle in circles:
            inside = [
                t for t in text_blocks
                if id(t) not in used_ids and self._is_text_strictly_inside_circle(t, circle)
            ]

            # THE FIX: Only merge if there are exactly 2 or 3 items
            # An ISA tag is never 5 separate words - that's a paragraph
            if not (2 <= len(inside) <= 3):
                continue

            # Sort top → bottom
            inside.sort(key=lambda t: t.y1)

            parts = [t.text.strip() for t in inside if t.text.strip()]

            # Smart join: alpha-prefix + digit-suffix → "FIC-101"
            if len(parts) >= 2 and parts[0].isalpha() and parts[-1].isdigit():
                combined_text = parts[0] + "-" + "-".join(parts[1:])
            else:
                combined_text = "-".join(parts)

            # THE FIX: ISA tags are rarely longer than 10-12 characters
            # If it's 30 characters long, it's a paragraph, not a tag
            if len(combined_text) > 12:
                print(f"  [MERGE SKIP] '{combined_text}' too long ({len(combined_text)} chars > 12)")
                continue

            best_conf = max(t.confidence for t in inside)

            merged = OCRText(
                text=combined_text,
                confidence=best_conf,
                x1=min(t.x1 for t in inside),
                y1=min(t.y1 for t in inside),
                x2=max(t.x2 for t in inside),
                y2=max(t.y2 for t in inside),
            )

            print(f"  [MERGE] {[t.text for t in inside]} → '{combined_text}' (conf={best_conf:.2f})")

            merged_blocks.append(merged)
            for t in inside:
                used_ids.add(id(t))

        # Keep all blocks not consumed by merging
        remaining = [t for t in text_blocks if id(t) not in used_ids]
        return merged_blocks + remaining

    def _is_duplicate_node(self, new_node: DetectedNode, existing_nodes: List[DetectedNode]) -> bool:
        """Check if new node overlaps significantly with existing nodes."""
        for existing in existing_nodes:
            # Calculate center distance
            new_cx, new_cy = new_node.center
            ex_cx, ex_cy = existing.center
            dist = np.sqrt((new_cx - ex_cx)**2 + (new_cy - ex_cy)**2)
            
            # If centers are within 50px and tags match (or one is None), it's duplicate
            if dist < 50:
                if existing.tag == new_node.tag or existing.tag is None or new_node.tag is None:
                    # Update existing node's tag if new one has it
                    if new_node.tag and not existing.tag:
                        existing.tag = new_node.tag
                    return True
        
        return False
    
    def visualize(
        self,
        image: np.ndarray,
        result: HybridPipelineResult,
        output_path: Optional[str] = None,
        show_circles: bool = True,
        show_discarded: bool = False,
    ) -> np.ndarray:
        """
        Visualize pipeline results on image.
        
        Args:
            image: Original BGR image
            result: HybridPipelineResult
            output_path: Optional path to save
            show_circles: Draw detected circles
            show_discarded: Show discarded text (faded)
            
        Returns:
            Annotated image
        """
        vis = image.copy()
        
        # Color scheme by source
        SOURCE_COLORS = {
            DetectionSource.YOLO: (0, 255, 0),         # Green
            DetectionSource.HOUGH_CIRCLE: (255, 165, 0),  # Orange
            DetectionSource.ISA_REGEX: (255, 0, 255),   # Magenta
            DetectionSource.COMBINED: (255, 255, 0),    # Cyan
        }
        
        # Draw all detected nodes
        for node in result.nodes:
            color = SOURCE_COLORS.get(node.source, (255, 255, 255))
            
            x1, y1 = int(node.x1), int(node.y1)
            x2, y2 = int(node.x2), int(node.y2)
            
            # Draw rectangle
            cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = node.class_name
            if node.tag:
                label = f"{node.tag}"
            label += f" [{node.source.value}]"
            
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
            cv2.rectangle(vis, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
            cv2.putText(vis, label, (x1 + 2, y1 - 3), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
        
        # Draw raw circles (optional)
        if show_circles:
            for circle in result.circles:
                if circle.matched_text is None:
                    # Unmatched circles in gray
                    cv2.circle(vis, (int(circle.cx), int(circle.cy)), 
                              int(circle.radius), (128, 128, 128), 1)
        
        # Draw discarded text (optional)
        if show_discarded:
            for text in result.discarded_text:
                cv2.rectangle(vis, 
                             (int(text.x1), int(text.y1)), 
                             (int(text.x2), int(text.y2)), 
                             (0, 0, 128), 1)
        
        # Add legend
        legend_y = 30
        for source, color in SOURCE_COLORS.items():
            cv2.putText(vis, f"● {source.value}", (10, legend_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            legend_y += 25
        
        if output_path:
            cv2.imwrite(output_path, vis)
            print(f"[VIS] Saved: {output_path}")
        
        return vis


# =============================================================================
# MAIN (KAGGLE ENTRY POINT)
# =============================================================================

def main():
    """Example usage for Kaggle notebook."""
    
    # Paths (adjust for your environment)
    if os.path.exists("/kaggle/working"):
        # Kaggle environment
        MODEL_PATH = "/kaggle/input/edai4-golden-model/best.pt"
        IMAGE_PATH = "/kaggle/input/pid-test/incinerator_pid.png"
        OUTPUT_PATH = "/kaggle/working/hybrid_output.png"
    else:
        # Local development
        MODEL_PATH = "D:/EDAI4/models/yolov8/best.pt"
        IMAGE_PATH = "D:/EDAI4/data/test_images/complex_pid.png"
        OUTPUT_PATH = "D:/EDAI4/output/hybrid_output.png"
    
    # Check model exists
    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: Model not found at {MODEL_PATH}")
        return
    
    # Initialize pipeline
    pipeline = HybridPerceptionPipeline(
        model_path=MODEL_PATH,
        slice_size=640,
        overlap_ratio=0.25,
        confidence_threshold=0.20,
        circle_min_radius=15,
        circle_max_radius=60,
        use_gpu=True,
    )
    
    # Process image
    if os.path.exists(IMAGE_PATH):
        result = pipeline.process(IMAGE_PATH)
        
        # Load image for visualization
        image = cv2.imread(IMAGE_PATH)
        pipeline.visualize(image, result, OUTPUT_PATH)
        
        # Print instruments
        print("\n" + "=" * 50)
        print("DETECTED INSTRUMENTS")
        print("=" * 50)
        for node in result.nodes:
            if node.is_instrument:
                print(f"  {node.tag or 'UNTAGGED'} ({node.class_name}) "
                      f"[{node.source.value}] conf={node.confidence:.0%}")
    else:
        print(f"Image not found: {IMAGE_PATH}")


if __name__ == "__main__":
    main()
