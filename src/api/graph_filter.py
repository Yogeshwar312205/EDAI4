"""
Natural Language Graph Filtering
Filters graph nodes based on natural language queries using Gemini AI
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

class GraphFilterRequest(BaseModel):
    """Request model for graph filtering"""
    query: str = Field(..., description="Natural language query (e.g., 'Show me all cooling water lines')")
    topology: Dict[str, Any] = Field(..., description="Graph topology with nodes and edges")


class GraphFilterResponse(BaseModel):
    """Response model for graph filtering"""
    matched_node_ids: List[str] = Field(..., description="List of node IDs that match the query")
    matched_edge_ids: List[str] = Field(default_factory=list, description="List of edge IDs that match the query")
    explanation: str = Field(..., description="Brief explanation of what was found")
    query: str = Field(..., description="Original query")


# ============================================
# Graph Filter Engine
# ============================================

class GraphFilter:
    """
    Natural Language Graph Filter using Gemini AI
    """
    
    def __init__(self, api_key: str = None, model: str = "gemini-2.5-flash"):
        """
        Initialize Graph Filter
        
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
        
        logger.info(f"Graph Filter initialized with model: {self.model_name}")
    
    
    def filter_graph(
        self,
        query: str,
        topology: Dict[str, Any]
    ) -> GraphFilterResponse:
        """
        Filter graph based on natural language query
        
        Args:
            query: Natural language query
            topology: Graph topology data
            
        Returns:
            GraphFilterResponse with matched node/edge IDs
        """
        
        # Build prompt
        prompt = self._build_prompt(query, topology)
        
        try:
            logger.info(f"Filtering graph with query: {query}")
            
            # Call Gemini
            response = self.model.generate_content(prompt)
            result_text = response.text
            
            logger.info(f"Gemini response received: {len(result_text)} characters")
            
            # Parse JSON response
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
            
            return GraphFilterResponse(**result_dict, query=query)
            
        except Exception as e:
            logger.error(f"Graph filtering failed: {e}")
            # Return fallback response
            return self._generate_fallback_response(query, topology)
    
    
    def _build_prompt(self, query: str, topology: Dict[str, Any]) -> str:
        """Build prompt for graph filtering"""
        
        nodes = topology.get("nodes", [])
        edges = topology.get("edges", [])
        
        prompt = f"""You are a P&ID (Piping & Instrumentation Diagram) expert. Your task is to filter a graph topology based on a natural language query.

USER QUERY: "{query}"

P&ID TOPOLOGY:
Total Nodes: {len(nodes)}
Total Connections: {len(edges)}

NODES (Equipment):
"""
        
        # Add node details
        for node in nodes[:100]:  # Limit to avoid token limits
            node_id = node.get("id", "unknown")
            node_type = node.get("type", "unknown")
            node_data = node.get("data", {})
            node_label = node_data.get("label", "")
            node_tag = node_data.get("tag", "")
            node_desc = node_data.get("description", "")
            
            prompt += f"- {node_id}: type={node_type}, label={node_label}, tag={node_tag}, desc={node_desc}\n"
        
        if len(nodes) > 100:
            prompt += f"... and {len(nodes) - 100} more nodes\n"
        
        prompt += f"\nCONNECTIONS (Pipes/Lines):\n"
        
        # Add edge details
        for edge in edges[:100]:
            edge_id = edge.get("id", "unknown")
            source = edge.get("source", "unknown")
            target = edge.get("target", "unknown")
            edge_data = edge.get("data", {})
            edge_label = edge_data.get("label", "")
            
            prompt += f"- {edge_id}: {source} → {target} (label={edge_label})\n"
        
        if len(edges) > 100:
            prompt += f"... and {len(edges) - 100} more connections\n"
        
        prompt += """

TASK:
Analyze the user's query and return ONLY the node IDs and edge IDs that match the query.

MATCHING RULES:
1. Match based on equipment type, label, tag, description
2. Match based on connections (e.g., "connected to furnace")
3. Match based on function (e.g., "cooling water", "flow control")
4. Match based on location or system (e.g., "inlet", "outlet")
5. Be inclusive - if unsure, include the node
6. For queries about connections/lines/pipes, include relevant edges

RESPONSE FORMAT (JSON):
{
  "matched_node_ids": ["node_1", "node_5", "node_8"],
  "matched_edge_ids": ["edge_2", "edge_7"],
  "explanation": "Found 3 cooling water valves connected to the furnace inlet"
}

Provide your response as a JSON object with this exact structure."""
        
        return prompt
    
    
    def _generate_fallback_response(
        self,
        query: str,
        topology: Dict[str, Any]
    ) -> GraphFilterResponse:
        """Generate rule-based fallback response when AI fails"""
        
        logger.warning("Using fallback graph filtering (AI unavailable)")
        
        nodes = topology.get("nodes", [])
        edges = topology.get("edges", [])
        
        # Simple keyword matching
        query_lower = query.lower()
        keywords = query_lower.split()
        
        matched_nodes = []
        matched_edges = []
        
        # Match nodes
        for node in nodes:
            node_id = node.get("id", "")
            node_data = node.get("data", {})
            node_text = f"{node.get('type', '')} {node_data.get('label', '')} {node_data.get('tag', '')} {node_data.get('description', '')}".lower()
            
            # Check if any keyword matches
            if any(keyword in node_text for keyword in keywords):
                matched_nodes.append(node_id)
        
        # Match edges
        for edge in edges:
            edge_id = edge.get("id", "")
            edge_data = edge.get("data", {})
            edge_text = f"{edge_data.get('label', '')}".lower()
            
            if any(keyword in edge_text for keyword in keywords):
                matched_edges.append(edge_id)
        
        # If no matches, return all nodes
        if not matched_nodes:
            matched_nodes = [node.get("id") for node in nodes[:20]]
            explanation = f"No specific matches found for '{query}'. Showing first 20 nodes."
        else:
            explanation = f"Found {len(matched_nodes)} nodes matching '{query}' using keyword search."
        
        return GraphFilterResponse(
            matched_node_ids=matched_nodes,
            matched_edge_ids=matched_edges,
            explanation=explanation,
            query=query
        )


# ============================================
# Singleton Instance
# ============================================

_filter_instance = None

def get_graph_filter() -> GraphFilter:
    """Get or create graph filter singleton instance"""
    global _filter_instance
    
    if _filter_instance is None:
        try:
            _filter_instance = GraphFilter()
            logger.info("Graph Filter instance created")
        except Exception as e:
            logger.error(f"Failed to create Graph Filter: {e}")
            raise
    
    return _filter_instance
