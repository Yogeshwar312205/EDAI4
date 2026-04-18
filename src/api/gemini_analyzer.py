"""
Gemini AI Tag Analyzer
Uses Google Gemini API to analyze P&ID instrument tags
"""
import os
import logging
from typing import Optional

# Try new google.genai package first, fall back to deprecated one
GENAI_AVAILABLE = False
USING_NEW_SDK = False

try:
    import google.genai as genai
    from google.genai import types
    GENAI_AVAILABLE = True
    USING_NEW_SDK = True
    logger = logging.getLogger(__name__)
    logger.info("✅ Using new google.genai SDK (recommended)")
except ImportError:
    try:
        import google.generativeai as genai
        GENAI_AVAILABLE = True
        USING_NEW_SDK = False
        logger = logging.getLogger(__name__)
        logger.warning("⚠️  Using deprecated google.generativeai package. Consider upgrading to google.genai")
    except ImportError:
        GENAI_AVAILABLE = False
        logger = logging.getLogger(__name__)
        logger.warning("❌ Neither google.genai nor google.generativeai package found")

from fastapi import UploadFile
import base64

if not logger:
    logger = logging.getLogger(__name__)


class GeminiTagAnalyzer:
    """Analyzes P&ID instrument tags using Gemini AI"""
    
    def __init__(self):
        """Initialize Gemini API"""
        if not GENAI_AVAILABLE:
            logger.warning("❌ google-generativeai package not installed. Gemini features will be disabled.")
            logger.info("💡 Install with: pip install google-genai")
            self.enabled = False
            return
            
        # Try both GEMINI_API_KEY and GOOGLE_API_KEY
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("❌ GEMINI_API_KEY or GOOGLE_API_KEY not set. Gemini features will be disabled.")
            logger.info("💡 Get your free API key from: https://makersuite.google.com/app/apikey")
            logger.info("💡 Then add to .env: GOOGLE_API_KEY=AIzaSy...")
            self.enabled = False
            return
        
        # Validate key format
        if not api_key.startswith("AIza"):
            logger.error(f"❌ Invalid API key format. Gemini keys should start with 'AIza', got: {api_key[:10]}...")
            logger.info("💡 Get a valid key from: https://makersuite.google.com/app/apikey")
            self.enabled = False
            return
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.enabled = True
            logger.info(f"✅ Gemini AI initialized successfully (key: {api_key[:10]}...{api_key[-4:]})")
            if USING_NEW_SDK:
                logger.info("✅ Using latest google.genai SDK")
            else:
                logger.warning("⚠️  Using deprecated google.generativeai - consider upgrading")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini: {e}")
            logger.info("💡 Check your API key at: https://makersuite.google.com/app/apikey")
            self.enabled = False
    
    async def analyze_tag_from_image(self, image_file: UploadFile) -> dict:
        """
        Analyze instrument tag from uploaded image
        
        Args:
            image_file: Uploaded image file containing P&ID instrument bubble
            
        Returns:
            dict with 'tag' and 'definition' keys
        """
        if not self.enabled:
            return {
                "tag": "N/A",
                "definition": "Gemini API not configured. Please set GEMINI_API_KEY environment variable."
            }
        
        try:
            # Read image bytes
            image_bytes = await image_file.read()
            
            # Prepare prompt
            prompt = """
You are an expert in Process & Instrumentation Diagrams (P&IDs) and industrial instrumentation.

Analyze this image of an instrument tag/bubble from a P&ID diagram.

Tasks:
1. Read and extract the instrument tag text (e.g., "FIC-101", "PT-205", "LT-301")
2. Provide a clear, concise engineering definition of what this instrument does

Format your response EXACTLY as:
TAG: [extracted tag]
DEFINITION: [brief engineering explanation in 1-2 sentences]

Example:
TAG: FIC-101
DEFINITION: Flow Indicator Controller - Measures flow rate and provides automatic control to maintain desired flow setpoint in the process line.

If you cannot read the tag clearly, respond with:
TAG: UNREADABLE
DEFINITION: Unable to extract tag from image. Please provide a clearer image.
"""
            
            # Create image part for Gemini
            image_part = {
                "mime_type": image_file.content_type or "image/jpeg",
                "data": image_bytes
            }
            
            # Generate response
            response = self.model.generate_content([prompt, image_part])
            
            # Parse response
            return self._parse_gemini_response(response.text)
            
        except Exception as e:
            logger.error(f"Error analyzing tag from image: {e}")
            return {
                "tag": "ERROR",
                "definition": f"Failed to analyze image: {str(e)}"
            }
    
    def analyze_tag_from_text(self, tag_text: str) -> dict:
        """
        Analyze instrument tag from text (fallback when no image)
        
        Args:
            tag_text: Instrument tag text (e.g., "FIC-101")
            
        Returns:
            dict with 'tag' and 'definition' keys
        """
        if not self.enabled:
            return self._get_simulated_response(tag_text)
        
        try:
            prompt = f"""
You are an expert in Process & Instrumentation Diagrams (P&IDs) and industrial instrumentation.

Analyze this instrument tag: {tag_text}

Provide a clear, concise engineering definition of what this instrument does based on the ISA standard abbreviations.

Format your response EXACTLY as:
TAG: {tag_text}
DEFINITION: [brief engineering explanation in 1-2 sentences]

Common abbreviations:
- F = Flow
- P = Pressure  
- T = Temperature
- L = Level
- A = Analysis
- I = Indicator
- C = Controller
- T = Transmitter
- V = Valve
- S = Switch

Example:
TAG: FIC-101
DEFINITION: Flow Indicator Controller - Measures flow rate and provides automatic control to maintain desired flow setpoint in the process line.
"""
            
            response = self.model.generate_content(prompt)
            return self._parse_gemini_response(response.text)
            
        except Exception as e:
            logger.error(f"Error analyzing tag from text: {e}")
            return self._get_simulated_response(tag_text)
    
    def _parse_gemini_response(self, response_text: str) -> dict:
        """Parse Gemini response into structured format"""
        try:
            lines = response_text.strip().split('\n')
            tag = None
            definition = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('TAG:'):
                    tag = line.replace('TAG:', '').strip()
                elif line.startswith('DEFINITION:'):
                    definition = line.replace('DEFINITION:', '').strip()
            
            if not tag or not definition:
                # Fallback: use entire response as definition
                return {
                    "tag": tag or "UNKNOWN",
                    "definition": response_text.strip()
                }
            
            return {
                "tag": tag,
                "definition": definition
            }
            
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            return {
                "tag": "PARSE_ERROR",
                "definition": response_text
            }
    
    def _get_simulated_response(self, tag_text: str) -> dict:
        """
        Generate simulated response when Gemini is not available
        Uses basic ISA tag parsing
        """
        # Check if this is a class name (contains dots) rather than a tag
        if '.' in tag_text or tag_text.lower() in ['instrument', 'valve', 'equipment', 'untagged']:
            return {
                "tag": tag_text,
                "definition": "⚠️ No instrument tag detected. This node shows a class name instead of an ISA tag. The P&ID processing needs improvement to extract actual tags like FIC-101, PT-205, etc. from instrument bubbles."
            }
        
        # Parse ISA tag format: [Variable][Function][Loop Number]
        # Example: FIC-101 = Flow Indicator Controller, Loop 101
        
        definitions = {
            # Flow instruments
            "FI": "Flow Indicator - Displays flow rate measurement",
            "FT": "Flow Transmitter - Measures and transmits flow rate signal",
            "FC": "Flow Controller - Automatically controls flow rate",
            "FIC": "Flow Indicator Controller - Measures flow rate and provides automatic control",
            "FE": "Flow Element - Primary flow sensing element (orifice, venturi, etc.)",
            "FV": "Flow Control Valve - Valve that regulates flow rate",
            "FS": "Flow Switch - Detects flow/no-flow condition",
            "FY": "Flow Relay/Converter - Converts or relays flow signal",
            
            # Pressure instruments
            "PI": "Pressure Indicator - Displays pressure measurement",
            "PT": "Pressure Transmitter - Measures and transmits pressure signal",
            "PC": "Pressure Controller - Automatically controls pressure",
            "PIC": "Pressure Indicator Controller - Measures pressure and provides automatic control",
            "PSV": "Pressure Safety Valve - Protects equipment from overpressure",
            "PV": "Pressure Control Valve - Valve that regulates pressure",
            "PS": "Pressure Switch - Detects high/low pressure conditions",
            "PY": "Pressure Relay/Converter - Converts or relays pressure signal",
            
            # Temperature instruments
            "TI": "Temperature Indicator - Displays temperature measurement",
            "TT": "Temperature Transmitter - Measures and transmits temperature signal",
            "TC": "Temperature Controller - Automatically controls temperature",
            "TIC": "Temperature Indicator Controller - Measures temperature and provides automatic control",
            "TE": "Temperature Element - Temperature sensor (thermocouple, RTD, etc.)",
            "TV": "Temperature Control Valve - Valve that regulates temperature",
            "TS": "Temperature Switch - Detects high/low temperature conditions",
            "TY": "Temperature Relay/Converter - Converts or relays temperature signal",
            
            # Level instruments
            "LI": "Level Indicator - Displays level measurement",
            "LT": "Level Transmitter - Measures and transmits level signal",
            "LC": "Level Controller - Automatically controls level",
            "LIC": "Level Indicator Controller - Measures level and provides automatic control",
            "LSH": "Level Switch High - Alarm/shutdown on high level",
            "LSL": "Level Switch Low - Alarm/shutdown on low level",
            "LV": "Level Control Valve - Valve that regulates level",
            "LS": "Level Switch - Detects high/low level conditions",
            "LY": "Level Relay/Converter - Converts or relays level signal",
            
            # Analysis instruments
            "AI": "Analysis Indicator - Displays analytical measurement (pH, conductivity, etc.)",
            "AT": "Analysis Transmitter - Measures and transmits analytical signal",
            "AC": "Analysis Controller - Automatically controls analytical parameter",
            "AIC": "Analysis Indicator Controller - Measures analytical parameter and provides control",
            "AE": "Analysis Element - Analytical sensor or probe",
            
            # Speed/Frequency
            "SI": "Speed Indicator - Displays rotational speed",
            "ST": "Speed Transmitter - Measures and transmits speed signal",
            "SC": "Speed Controller - Controls rotational speed",
            "SS": "Speed Switch - Detects high/low speed conditions",
            
            # Setpoint/Signal
            "SP": "Setpoint - Desired value or target for control system",
            "SY": "Signal Relay/Converter - Converts or relays control signal",
            
            # Weight/Force
            "WI": "Weight Indicator - Displays weight measurement",
            "WT": "Weight Transmitter - Measures and transmits weight signal",
            "WC": "Weight Controller - Controls weight or force",
            
            # Position
            "ZI": "Position Indicator - Displays position measurement",
            "ZT": "Position Transmitter - Measures and transmits position signal",
            "ZC": "Position Controller - Controls position",
            "ZS": "Position Switch - Detects position limits",
            
            # Vibration
            "VI": "Vibration Indicator - Displays vibration measurement",
            "VT": "Vibration Transmitter - Measures and transmits vibration signal",
            "VS": "Vibration Switch - Detects high vibration conditions",
            
            # Hand/Manual
            "HIC": "Hand Indicator Controller - Manual control station",
            "HS": "Hand Switch - Manual selector switch",
            
            # Alarms
            "AH": "Alarm High - High level alarm",
            "AL": "Alarm Low - Low level alarm",
            "AHL": "Alarm High-Low - Combined high and low alarm",
        }
        
        # Extract instrument type (first 2-3 characters)
        tag_upper = tag_text.upper()
        
        # Try 3-character match first (e.g., FIC, PIC)
        for key, desc in definitions.items():
            if tag_upper.startswith(key):
                return {
                    "tag": tag_text,
                    "definition": f"{desc}"
                }
        
        # Fallback - try to provide basic info based on first letters
        tag_upper = tag_text.upper()
        
        # Extract first letter (measured variable)
        first_letter_meanings = {
            "F": "Flow",
            "P": "Pressure",
            "T": "Temperature",
            "L": "Level",
            "A": "Analysis (pH, conductivity, etc.)",
            "S": "Speed/Frequency",
            "W": "Weight",
            "Z": "Position",
            "V": "Vibration",
            "H": "Hand/Manual",
        }
        
        # Extract second letter (function)
        second_letter_meanings = {
            "I": "Indicator",
            "T": "Transmitter",
            "C": "Controller",
            "V": "Valve",
            "S": "Switch",
            "E": "Element/Sensor",
            "Y": "Relay/Converter",
            "A": "Alarm",
        }
        
        # Try to parse
        if len(tag_upper) >= 2:
            first = tag_upper[0]
            second = tag_upper[1]
            
            var_type = first_letter_meanings.get(first, "Unknown variable")
            func_type = second_letter_meanings.get(second, "Unknown function")
            
            return {
                "tag": tag_text,
                "definition": f"{var_type} {func_type} - ISA instrument tag. For detailed AI-powered analysis, ensure GEMINI_API_KEY is configured."
            }
        
        # Ultimate fallback
        return {
            "tag": tag_text,
            "definition": "Instrument tag - Unable to parse. Format should be [Variable][Function]-[Number] (e.g., FIC-101). Configure GEMINI_API_KEY for AI-powered analysis."
        }


# Global instance
_analyzer: Optional[GeminiTagAnalyzer] = None


def get_analyzer() -> GeminiTagAnalyzer:
    """Get or create global analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = GeminiTagAnalyzer()
    return _analyzer
