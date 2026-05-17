"""
Text-to-Topology Generator - AI-Powered P&ID Drafting
======================================================
Uses Gemini AI to generate P&ID topology from natural language descriptions.
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from google import genai
import os
from dotenv import load_dotenv

# Ensure .env is loaded (safe to call multiple times)
load_dotenv()

logger = logging.getLogger(__name__)


# =============================================================================
# Pydantic Models
# =============================================================================

class TextToTopologyRequest(BaseModel):
    """Request for text-to-topology generation."""
    prompt: str
    existing_nodes: Optional[List[Dict[str, Any]]] = []
    existing_edges: Optional[List[Dict[str, Any]]] = []
    start_position: Optional[Dict[str, float]] = {"x": 100, "y": 100}


class GeneratedNode(BaseModel):
    """Generated node in the topology."""
    id: str
    type: str
    label: str
    tag: str
    x: float
    y: float
    description: Optional[str] = None


class GeneratedEdge(BaseModel):
    """Generated edge in the topology."""
    source: str
    target: str
    type: str = "pipe"
    label: Optional[str] = None


class TextToTopologyResponse(BaseModel):
    """Response from text-to-topology generation."""
    nodes: List[GeneratedNode]
    edges: List[GeneratedEdge]
    description: str
    prompt: str
    success: bool
    error: Optional[str] = None


# =============================================================================
# Text-to-Topology Generator
# =============================================================================

class TextToTopologyGenerator:
    """
    Generates P&ID topology from natural language using Gemini AI.
    """
    
    def __init__(self):
        self.client = None
        self.model_name = "gemini-2.5-flash"
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Gemini AI client (google.genai SDK)."""
        try:
            # Try GEMINI_API_KEY first, then fall back to GOOGLE_API_KEY
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                logger.error("Neither GEMINI_API_KEY nor GOOGLE_API_KEY found in environment")
                return
            
            key_source = "GEMINI_API_KEY" if os.getenv("GEMINI_API_KEY") else "GOOGLE_API_KEY"
            logger.info(f"Using API key from {key_source}")
            
            # New google.genai SDK
            self.client = genai.Client(api_key=api_key)
            logger.info(f"✅ Gemini AI initialized for text-to-topology (model: {self.model_name})")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.client = None
    
    def reinitialize(self):
        """Retry Gemini initialization (e.g., after env vars are loaded)."""
        if self.client is None:
            logger.info("Retrying Gemini AI initialization...")
            self._initialize_gemini()
    
    def generate_topology(
        self,
        prompt: str,
        existing_nodes: List[Dict[str, Any]] = None,
        existing_edges: List[Dict[str, Any]] = None,
        start_position: Dict[str, float] = None
    ) -> TextToTopologyResponse:
        """
        Generate P&ID topology from natural language prompt.
        
        Args:
            prompt: Natural language description of the subsystem
            existing_nodes: Existing nodes in the canvas (for context)
            existing_edges: Existing edges in the canvas (for context)
            start_position: Starting position for new nodes
        
        Returns:
            TextToTopologyResponse with generated nodes and edges
        """
        if not self.client:
            return TextToTopologyResponse(
                nodes=[],
                edges=[],
                description="",
                prompt=prompt,
                success=False,
                error="Gemini AI not initialized. Check GEMINI_API_KEY or GOOGLE_API_KEY."
            )
        
        try:
            # Set defaults
            existing_nodes = existing_nodes or []
            existing_edges = existing_edges or []
            start_position = start_position or {"x": 100, "y": 100}
            
            # Build the AI prompt
            ai_prompt = self._build_ai_prompt(
                prompt,
                existing_nodes,
                existing_edges,
                start_position
            )
            
            logger.info(f"Generating topology for: {prompt}")
            
            # Call Gemini AI (new google.genai SDK)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=ai_prompt
            )
            response_text = response.text
            
            logger.debug(f"Gemini response: {response_text[:500]}...")
            
            # Parse the response
            topology_data = self._parse_gemini_response(response_text)
            
            if not topology_data:
                return TextToTopologyResponse(
                    nodes=[],
                    edges=[],
                    description="",
                    prompt=prompt,
                    success=False,
                    error="Failed to parse Gemini response"
                )
            
            # Create response
            return TextToTopologyResponse(
                nodes=topology_data["nodes"],
                edges=topology_data["edges"],
                description=topology_data.get("description", "Generated topology"),
                prompt=prompt,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Text-to-topology generation error: {e}")
            return TextToTopologyResponse(
                nodes=[],
                edges=[],
                description="",
                prompt=prompt,
                success=False,
                error=str(e)
            )
    
    def _build_ai_prompt(
        self,
        user_prompt: str,
        existing_nodes: List[Dict[str, Any]],
        existing_edges: List[Dict[str, Any]],
        start_position: Dict[str, float]
    ) -> str:
        """Build the prompt for Gemini AI."""
        
        prompt = f"""You are an expert P&ID (Piping and Instrumentation Diagram) engineer. 
Your task is to generate a complete P&ID subsystem topology based on the user's description.

USER REQUEST:
{user_prompt}

INSTRUCTIONS:
1. Generate nodes (equipment, instruments, valves) and edges (pipes, connections)
2. Use standard P&ID conventions and ISA instrument tags
3. Position nodes in a logical left-to-right or top-to-bottom flow
4. Start positioning from: x={start_position['x']}, y={start_position['y']}
5. Space nodes appropriately (150-200 pixels apart)
6. Use proper equipment types and instrument tags

EQUIPMENT TYPES:
- equipment.tank (storage tanks)
- equipment.pump (centrifugal, positive displacement)
- equipment.vessel (pressure vessels, reactors)
- equipment.heat_exchanger (shell & tube, plate)
- equipment.compressor
- valve.gate (isolation)
- valve.globe (throttling)
- valve.check (one-way flow)
- valve.ball (quick shutoff)
- valve.control (automated control)
- instrument.flow (FT, FIC, FE)
- instrument.pressure (PT, PIC, PE)
- instrument.temperature (TT, TIC, TE)
- instrument.level (LT, LIC, LE)

ISA TAG FORMAT:
- First letter: Measured variable (F=Flow, P=Pressure, T=Temperature, L=Level)
- Second letter: Function (I=Indicator, C=Controller, T=Transmitter, E=Element)
- Number: Loop identifier (e.g., 101, 201)
- Example: FIC-101 (Flow Indicator Controller, loop 101)

OUTPUT FORMAT (JSON):
{{
  "description": "Brief description of the generated subsystem",
  "nodes": [
    {{
      "id": "unique_id",
      "type": "equipment_type",
      "label": "Display Name",
      "tag": "ISA_TAG or Equipment_ID",
      "x": 100,
      "y": 100,
      "description": "Optional description"
    }}
  ],
  "edges": [
    {{
      "source": "node_id_1",
      "target": "node_id_2",
      "type": "pipe",
      "label": "Optional label"
    }}
  ]
}}

EXAMPLE:
User: "Draft a cooling water loop with pump and control valve"
Output:
{{
  "description": "Cooling water circulation loop with centrifugal pump and flow control",
  "nodes": [
    {{"id": "tank_cw_001", "type": "equipment.tank", "label": "CW Tank", "tag": "TK-101", "x": 100, "y": 100}},
    {{"id": "pump_cw_001", "type": "equipment.pump", "label": "CW Pump", "tag": "P-101", "x": 300, "y": 100}},
    {{"id": "valve_cv_001", "type": "valve.control", "label": "Flow Control", "tag": "FCV-101", "x": 500, "y": 100}},
    {{"id": "flow_meter_001", "type": "instrument.flow", "label": "Flow Meter", "tag": "FT-101", "x": 650, "y": 100}}
  ],
  "edges": [
    {{"source": "tank_cw_001", "target": "pump_cw_001", "type": "pipe"}},
    {{"source": "pump_cw_001", "target": "valve_cv_001", "type": "pipe"}},
    {{"source": "valve_cv_001", "target": "flow_meter_001", "type": "pipe"}}
  ]
}}

IMPORTANT:
- Return ONLY valid JSON (no markdown, no code blocks)
- Ensure all node IDs are unique
- Ensure all edge source/target IDs reference existing nodes
- Use realistic spacing (150-200px between nodes)
- Follow process flow direction (left-to-right or top-to-bottom)

Now generate the topology for the user's request above.
"""
        
        return prompt
    
    def _parse_gemini_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse Gemini's JSON response."""
        try:
            # Remove markdown code blocks if present
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON
            data = json.loads(response_text)
            
            # Validate structure
            if "nodes" not in data or "edges" not in data:
                logger.error("Invalid response structure: missing nodes or edges")
                return None
            
            # Convert to Pydantic models for validation
            nodes = [GeneratedNode(**node) for node in data["nodes"]]
            edges = [GeneratedEdge(**edge) for edge in data["edges"]]
            
            return {
                "nodes": nodes,
                "edges": edges,
                "description": data.get("description", "Generated topology")
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            return None
        except Exception as e:
            logger.error(f"Failed to parse response: {e}")
            return None


# =============================================================================
# Singleton Instance
# =============================================================================

_generator = None


def get_text_to_topology_generator() -> TextToTopologyGenerator:
    """Get or create text-to-topology generator instance."""
    global _generator
    if _generator is None:
        _generator = TextToTopologyGenerator()
        logger.info("✅ Text-to-Topology Generator initialized")
    elif _generator.client is None:
        # Singleton exists but Gemini failed to init — retry now that env may be loaded
        _generator.reinitialize()
    return _generator
