"""
HazOp Failure Simulator
Predicts cascading effects of equipment failures using Gemini AI
"""

import os
import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import google.generativeai as genai

logger = logging.getLogger(__name__)


# ============================================
# Request/Response Models
# ============================================

class HazOpSimulationRequest(BaseModel):
    """Request model for HazOp simulation"""
    failed_node_id: str = Field(..., description="ID of the failed equipment node")
    failure_mode: str = Field(..., description="Type of failure (e.g., 'Stuck Closed', 'Failed Open')")
    topology: Dict[str, Any] = Field(..., description="Graph topology with nodes and edges")


class HazOpSimulationResponse(BaseModel):
    """Response model for HazOp simulation with structured output"""
    hazard_summary: str = Field(..., description="2-sentence summary of immediate danger")
    cascading_effects: List[str] = Field(..., description="List of cascading failure effects")
    affected_node_ids: List[str] = Field(..., description="List of node IDs in danger zone")
    affected_edge_ids: List[str] = Field(..., description="List of edge IDs that will fail")
    severity_level: str = Field(default="MEDIUM", description="Severity: LOW, MEDIUM, HIGH, CRITICAL")
    recommended_actions: List[str] = Field(default_factory=list, description="Emergency response actions")


# ============================================
# HazOp Simulator Engine
# ============================================

class HazOpSimulator:
    """
    HazOp Failure Simulator using Gemini AI with structured outputs
    """
    
    def __init__(self, api_key: str = None, model: str = "gemini-2.5-flash"):
        """
        Initialize HazOp Simulator
        
        Args:
            api_key: Google Gemini API key
            model: Gemini model to use (default: gemini-2.5-flash, was gemini-1.5-flash but deprecated)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")
        
        # Remove 'models/' prefix if present (OLD API adds it automatically)
        self.model_name = model.replace("models/", "")
        
        # Configure and initialize model (OLD API - deprecated but still works)
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
        
        logger.info(f"HazOp Simulator initialized with model: {self.model_name}")
    
    
    def simulate_failure(
        self,
        failed_node_id: str,
        failure_mode: str,
        topology: Dict[str, Any]
    ) -> HazOpSimulationResponse:
        """
        Simulate equipment failure and predict cascading effects
        
        Args:
            failed_node_id: ID of the failed equipment
            failure_mode: Type of failure
            topology: Graph topology data
            
        Returns:
            HazOpSimulationResponse with structured predictions
        """
        
        # Build system prompt for HazOp analysis
        system_prompt = self._build_system_prompt()
        
        # Build user prompt with topology data
        user_prompt = self._build_user_prompt(failed_node_id, failure_mode, topology)
        
        # Combine system and user prompts
        full_prompt = f"{system_prompt}\n\n{user_prompt}\n\nProvide your analysis as a JSON object with this exact structure:\n{{\n  \"hazard_summary\": \"2-sentence summary\",\n  \"cascading_effects\": [\"effect1\", \"effect2\", \"effect3\"],\n  \"affected_node_ids\": [\"node1\", \"node2\"],\n  \"affected_edge_ids\": [\"edge1\", \"edge2\"],\n  \"severity_level\": \"LOW|MEDIUM|HIGH|CRITICAL\",\n  \"recommended_actions\": [\"action1\", \"action2\", \"action3\"]\n}}"
        
        try:
            # Call Gemini with OLD API (same as working chatbot)
            logger.info(f"Simulating failure: {failed_node_id} - {failure_mode}")
            
            response = self.model.generate_content(full_prompt)
            
            # Parse structured response
            result_text = response.text
            logger.info(f"Gemini response received: {len(result_text)} characters")
            
            # Extract JSON from response (handle markdown code blocks)
            import json
            import re
            
            # Try to find JSON in markdown code block
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(1)
            else:
                # Try to find JSON without code block
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result_text = json_match.group(0)
            
            result_dict = json.loads(result_text)
            
            return HazOpSimulationResponse(**result_dict)
            
        except Exception as e:
            logger.error(f"HazOp simulation failed: {e}")
            # Return fallback response
            return self._generate_fallback_response(failed_node_id, failure_mode, topology)
    
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for HazOp safety engineer persona"""
        return """You are a Senior HazOp Safety Engineer with 20+ years of experience in process safety analysis.

Your expertise includes:
- Hazard and Operability (HazOp) studies
- Process safety management (PSM)
- Failure mode and effects analysis (FMEA)
- Piping and instrumentation diagram (P&ID) analysis
- Consequence modeling and risk assessment

Your task is to analyze equipment failures in P&ID systems and predict:
1. Immediate hazards and dangers
2. Cascading effects through connected equipment
3. Which nodes and pipes will be affected
4. Severity of the incident
5. Emergency response actions

CRITICAL RULES:
- Trace connections through the topology graph carefully
- Consider pressure build-up, cavitation, leaks, and explosions
- Identify all downstream and upstream affected equipment
- Assess severity based on: pressure, temperature, hazardous materials, and population exposure
- Provide actionable emergency response recommendations
- Be conservative in safety assessments (err on the side of caution)

ANALYSIS METHODOLOGY:
1. Identify the failed component and its function
2. Trace immediate upstream and downstream connections
3. Analyze pressure/flow changes in connected pipes
4. Identify equipment that will experience abnormal conditions
5. Predict secondary failures and cascading effects
6. Assess overall severity and recommend actions"""
    
    
    def _build_user_prompt(
        self,
        failed_node_id: str,
        failure_mode: str,
        topology: Dict[str, Any]
    ) -> str:
        """Build user prompt with failure scenario and topology data"""
        
        # Extract topology information
        nodes = topology.get("nodes", [])
        edges = topology.get("edges", [])
        
        # Find the failed node
        failed_node = None
        for node in nodes:
            if node.get("id") == failed_node_id:
                failed_node = node
                break
        
        # Build prompt
        prompt = f"""FAILURE SCENARIO:
Equipment ID: {failed_node_id}
Equipment Type: {failed_node.get('data', {}).get('label', 'Unknown') if failed_node else 'Unknown'}
Failure Mode: {failure_mode}

P&ID TOPOLOGY:
Total Nodes: {len(nodes)}
Total Connections: {len(edges)}

NODES (Equipment):
"""
        
        # Add node details
        for node in nodes[:50]:  # Limit to first 50 nodes to avoid token limits
            node_id = node.get("id", "unknown")
            node_type = node.get("type", "unknown")
            node_label = node.get("data", {}).get("label", "")
            prompt += f"- {node_id}: {node_type} ({node_label})\n"
        
        if len(nodes) > 50:
            prompt += f"... and {len(nodes) - 50} more nodes\n"
        
        prompt += f"\nCONNECTIONS (Pipes/Lines):\n"
        
        # Add edge details
        for edge in edges[:100]:  # Limit to first 100 edges
            edge_id = edge.get("id", "unknown")
            source = edge.get("source", "unknown")
            target = edge.get("target", "unknown")
            edge_label = edge.get("data", {}).get("label", "")
            prompt += f"- {edge_id}: {source} → {target} ({edge_label})\n"
        
        if len(edges) > 100:
            prompt += f"... and {len(edges) - 100} more connections\n"
        
        prompt += f"""

ANALYSIS REQUIRED:
1. Analyze the failure of {failed_node_id} with mode "{failure_mode}"
2. Trace all connections from this node through the topology
3. Identify which equipment (nodes) will be affected
4. Identify which pipes/lines (edges) will experience abnormal conditions
5. Predict cascading failures and their effects
6. Assess severity level: LOW, MEDIUM, HIGH, or CRITICAL
7. Recommend emergency response actions

Provide your analysis in the structured JSON format."""
        
        return prompt
    
    
    
    def _generate_fallback_response(
        self,
        failed_node_id: str,
        failure_mode: str,
        topology: Dict[str, Any]
    ) -> HazOpSimulationResponse:
        """Generate rule-based fallback response when AI fails"""
        
        logger.warning("Using fallback HazOp analysis (AI unavailable)")
        
        # Find connected nodes and edges
        edges = topology.get("edges", [])
        affected_edges = []
        affected_nodes = set()
        
        # Find directly connected edges
        for edge in edges:
            if edge.get("source") == failed_node_id or edge.get("target") == failed_node_id:
                edge_id = edge.get("id")
                if edge_id:  # Only add if not None
                    affected_edges.append(str(edge_id))
                
                source = edge.get("source")
                target = edge.get("target")
                if source:
                    affected_nodes.add(str(source))
                if target:
                    affected_nodes.add(str(target))
        
        # Remove the failed node itself and None values
        affected_nodes.discard(failed_node_id)
        affected_nodes.discard(None)
        
        # Convert to lists and filter out None
        affected_node_list = [n for n in list(affected_nodes)[:10] if n]
        affected_edge_list = [e for e in affected_edges[:10] if e]
        
        # Ensure we have at least some data
        if not affected_node_list:
            affected_node_list = ["No connected nodes detected"]
        if not affected_edge_list:
            affected_edge_list = ["No connected edges detected"]
        
        return HazOpSimulationResponse(
            hazard_summary=f"Equipment {failed_node_id} has failed with mode '{failure_mode}'. Immediate downstream equipment may experience abnormal operating conditions.",
            cascading_effects=[
                f"Loss of flow/pressure control at {failed_node_id}",
                "Potential pressure build-up in connected lines",
                "Downstream equipment may experience abnormal conditions",
                "Process upset and potential safety system activation"
            ],
            affected_node_ids=affected_node_list,
            affected_edge_ids=affected_edge_list,
            severity_level="MEDIUM",
            recommended_actions=[
                "Activate emergency shutdown procedures",
                "Isolate affected section using block valves",
                "Monitor pressure and temperature readings",
                "Notify operations supervisor immediately",
                "Prepare for manual intervention if required"
            ]
        )


# ============================================
# Singleton Instance
# ============================================

_simulator_instance = None

def get_hazop_simulator() -> HazOpSimulator:
    """Get or create HazOp simulator singleton instance"""
    global _simulator_instance
    
    if _simulator_instance is None:
        try:
            _simulator_instance = HazOpSimulator()
            logger.info("HazOp Simulator instance created")
        except Exception as e:
            logger.error(f"Failed to create HazOp Simulator: {e}")
            raise
    
    return _simulator_instance
