"""
EDAI4 - Semantic Enricher
==========================
Enriches P&ID data with engineering context and knowledge.

Features:
- Process descriptions from tag analysis
- Typical ranges for measured variables
- Function meanings in plain English
- Equipment relationships
- Operating context inference
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum

from src.topology.graph_builder import PIDGraph, GraphNode, NodeType, EdgeType
from src.cognitive.isa_validator import (
    ISAS51Validator, ISA_FIRST_LETTERS, ISA_SUCCEEDING_LETTERS
)
from src.utils import get_logger

logger = get_logger(__name__)


# Typical ranges and units for process variables
PROCESS_VARIABLE_INFO = {
    "F": {
        "name": "Flow",
        "units": ["GPM", "m³/h", "kg/h", "SCFH", "lb/h"],
        "typical_ranges": {
            "liquid": (0, 1000, "GPM"),
            "gas": (0, 10000, "SCFH"),
            "steam": (0, 50000, "lb/h"),
        },
        "description": "Volume or mass flow rate through piping",
    },
    "L": {
        "name": "Level",
        "units": ["%", "ft", "m", "inches"],
        "typical_ranges": {
            "tank": (0, 100, "%"),
            "vessel": (0, 100, "%"),
            "drum": (0, 100, "%"),
        },
        "description": "Liquid or solid level in vessels/tanks",
    },
    "P": {
        "name": "Pressure",
        "units": ["psig", "barg", "kPa", "inH2O", "mmHg"],
        "typical_ranges": {
            "process": (0, 500, "psig"),
            "vacuum": (-14.7, 0, "psig"),
            "atmospheric": (14.5, 15.0, "psia"),
        },
        "description": "Process pressure or vacuum",
    },
    "T": {
        "name": "Temperature",
        "units": ["°F", "°C", "K"],
        "typical_ranges": {
            "ambient": (60, 100, "°F"),
            "process": (100, 500, "°F"),
            "cryogenic": (-300, -100, "°F"),
            "high_temp": (500, 2000, "°F"),
        },
        "description": "Process temperature",
    },
    "A": {
        "name": "Analysis",
        "units": ["%", "ppm", "pH", "conductivity"],
        "typical_ranges": {
            "composition": (0, 100, "%"),
            "trace": (0, 1000, "ppm"),
            "pH": (0, 14, "pH"),
        },
        "description": "Chemical composition or quality analysis",
    },
    "D": {
        "name": "Density",
        "units": ["SG", "kg/m³", "lb/ft³"],
        "typical_ranges": {
            "liquid": (0.5, 2.0, "SG"),
            "gas": (0.001, 0.1, "SG"),
        },
        "description": "Fluid density or specific gravity",
    },
    "W": {
        "name": "Weight",
        "units": ["lb", "kg", "tons"],
        "typical_ranges": {
            "batch": (0, 10000, "lb"),
            "hopper": (0, 50000, "lb"),
        },
        "description": "Weight or force measurement",
    },
    "S": {
        "name": "Speed",
        "units": ["RPM", "Hz", "m/s"],
        "typical_ranges": {
            "pump": (1000, 3600, "RPM"),
            "compressor": (3000, 15000, "RPM"),
            "conveyor": (10, 100, "m/min"),
        },
        "description": "Rotational speed or frequency",
    },
    "V": {
        "name": "Vibration",
        "units": ["mil", "mm/s", "g"],
        "typical_ranges": {
            "acceptable": (0, 0.5, "in/s"),
            "warning": (0.5, 1.0, "in/s"),
            "alarm": (1.0, 2.0, "in/s"),
        },
        "description": "Mechanical vibration amplitude",
    },
    "Z": {
        "name": "Position",
        "units": ["%", "mm", "degrees"],
        "typical_ranges": {
            "valve": (0, 100, "%"),
            "actuator": (0, 100, "%"),
        },
        "description": "Position or stroke measurement",
    },
}

# Function descriptions for common instruments
INSTRUMENT_DESCRIPTIONS = {
    "FT": "Flow Transmitter - Measures flow rate and transmits signal to control system",
    "FI": "Flow Indicator - Local display of flow rate",
    "FIC": "Flow Indicating Controller - Displays and controls flow rate",
    "FCV": "Flow Control Valve - Modulates flow based on controller output",
    "LT": "Level Transmitter - Measures level and transmits signal to control system",
    "LI": "Level Indicator - Local display of level",
    "LIC": "Level Indicating Controller - Displays and controls level",
    "LCV": "Level Control Valve - Modulates flow to control level",
    "LG": "Level Gauge/Glass - Visual level indication",
    "PT": "Pressure Transmitter - Measures pressure and transmits signal",
    "PI": "Pressure Indicator - Local pressure display",
    "PIC": "Pressure Indicating Controller - Displays and controls pressure",
    "PCV": "Pressure Control Valve - Modulates flow to control pressure",
    "PSV": "Pressure Safety Valve - Relieves excess pressure for safety",
    "PSH": "Pressure Switch High - Activates on high pressure",
    "PSL": "Pressure Switch Low - Activates on low pressure",
    "TT": "Temperature Transmitter - Measures temperature and transmits signal",
    "TI": "Temperature Indicator - Local temperature display",
    "TIC": "Temperature Indicating Controller - Displays and controls temperature",
    "TCV": "Temperature Control Valve - Modulates flow to control temperature",
    "TE": "Temperature Element - Primary sensor (thermocouple, RTD)",
    "TW": "Temperature Well - Thermowell for sensor protection",
    "AT": "Analyzer Transmitter - Measures composition and transmits signal",
    "AIC": "Analyzer Indicating Controller - Displays and controls composition",
    "SDV": "Shutdown Valve - Automatically closes for safety",
    "BDV": "Blowdown Valve - Emergency pressure relief",
    "XV": "On/Off Valve - Binary open/close valve",
    "HV": "Hand Valve - Manually operated valve",
    "HC": "Hand Controller - Manual control station",
}


@dataclass
class EnrichedNode:
    """A graph node enriched with semantic information."""
    node: GraphNode
    description: str
    process_variable: Optional[str] = None
    typical_units: list[str] = field(default_factory=list)
    typical_range: Optional[tuple] = None
    function_description: str = ""
    engineering_context: list[str] = field(default_factory=list)
    related_equipment: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "id": self.node.id,
            "tag": self.node.tag,
            "description": self.description,
            "process_variable": self.process_variable,
            "units": self.typical_units,
            "typical_range": self.typical_range,
            "function": self.function_description,
            "context": self.engineering_context,
            "related_equipment": self.related_equipment,
        }


class SemanticEnricher:
    """
    Enriches P&ID graph data with engineering semantics.
    
    Adds:
    - Human-readable descriptions
    - Typical ranges and units
    - Function explanations
    - Equipment relationships
    - Operating context
    """
    
    def __init__(self, graph: PIDGraph):
        """
        Initialize enricher.
        
        Args:
            graph: PIDGraph to enrich
        """
        self.graph = graph
        self.validator = ISAS51Validator()
    
    def _get_function_letters(self, tag: str) -> str:
        """Extract function letter combination from tag."""
        result = self.validator.validate_tag(tag)
        first = result.parsed_first_letter or ""
        succ = result.parsed_succeeding_letters or ""
        return first + succ
    
    def _generate_description(self, node: GraphNode) -> str:
        """Generate human-readable description for a node."""
        if not node.tag:
            return node.label or f"Unknown {node.node_type.value}"
        
        func = self._get_function_letters(node.tag)
        
        # Check for known instrument type
        if func in INSTRUMENT_DESCRIPTIONS:
            return INSTRUMENT_DESCRIPTIONS[func]
        
        # Build description from letter meanings
        result = self.validator.validate_tag(node.tag)
        
        parts = []
        
        # First letter - measured variable
        if result.parsed_first_letter:
            first_info = ISA_FIRST_LETTERS.get(result.parsed_first_letter, {})
            parts.append(first_info.get("name", result.parsed_first_letter))
        
        # Succeeding letters - functions
        if result.parsed_succeeding_letters:
            for letter in result.parsed_succeeding_letters:
                info = ISA_SUCCEEDING_LETTERS.get(letter, {})
                name = info.get("name")
                if name:
                    parts.append(name)
        
        if parts:
            return " ".join(parts)
        
        return node.label or node.tag
    
    def _get_process_variable_info(self, tag: str) -> dict:
        """Get process variable information from tag."""
        result = self.validator.validate_tag(tag)
        first_letter = result.parsed_first_letter
        
        if first_letter and first_letter in PROCESS_VARIABLE_INFO:
            return PROCESS_VARIABLE_INFO[first_letter]
        
        return {}
    
    def _find_related_equipment(self, node: GraphNode) -> list[str]:
        """Find equipment related to this node."""
        related = []
        
        # Check MEASURES edges
        for connected, edge in self.graph.get_connected_nodes(node.id, EdgeType.MEASURES):
            if connected.node_type in (NodeType.EQUIPMENT, NodeType.PUMP):
                related.append(connected.tag or connected.id)
        
        # Check PART_OF edges (containment)
        for connected, edge in self.graph.get_connected_nodes(node.id, EdgeType.PART_OF):
            related.append(connected.tag or connected.id)
        
        # Check generic connections to equipment
        for connected, edge in self.graph.get_connected_nodes(node.id):
            if connected.node_type in (NodeType.EQUIPMENT, NodeType.PUMP):
                if connected.tag and connected.tag not in related:
                    related.append(connected.tag)
        
        return related
    
    def _generate_engineering_context(self, node: GraphNode, pv_info: dict) -> list[str]:
        """Generate engineering context notes."""
        context = []
        
        if not node.tag:
            return context
        
        result = self.validator.validate_tag(node.tag)
        func = self._get_function_letters(node.tag)
        
        # Safety instruments
        if any(p in func for p in ["SH", "SL", "AH", "AL"]):
            context.append("Safety-critical instrument - requires regular testing")
        
        if any(p in func for p in ["HH", "LL"]):
            context.append("High-high or Low-low alarm - typically initiates shutdown")
        
        # Transmitters
        if "T" in result.parsed_succeeding_letters:
            context.append("Transmitter output typically 4-20mA or digital (HART/Foundation)")
        
        # Controllers
        if "IC" in func or "C" in result.parsed_succeeding_letters:
            context.append("Controller requires tuning (PID parameters)")
        
        # Analyzers
        if result.parsed_first_letter == "A":
            context.append("Analyzer requires regular calibration and maintenance")
        
        # Temperature elements
        if "TE" in func or "TW" in func:
            context.append("Primary sensor - check thermowell material compatibility")
        
        # Flow elements
        if "FE" in func or "FO" in func:
            context.append("Primary flow element - consider beta ratio and straight run requirements")
        
        return context
    
    def enrich_node(self, node: GraphNode) -> EnrichedNode:
        """
        Enrich a single node with semantic information.
        
        Args:
            node: GraphNode to enrich
            
        Returns:
            EnrichedNode with added context
        """
        description = self._generate_description(node)
        pv_info = self._get_process_variable_info(node.tag or "")
        related = self._find_related_equipment(node)
        context = self._generate_engineering_context(node, pv_info)
        
        # Extract function description
        func = self._get_function_letters(node.tag or "")
        func_desc = INSTRUMENT_DESCRIPTIONS.get(func, "")
        
        # Get typical range
        typical_range = None
        if pv_info:
            ranges = pv_info.get("typical_ranges", {})
            if ranges:
                # Use first available range as default
                first_key = next(iter(ranges.keys()), None)
                if first_key:
                    typical_range = ranges[first_key]
        
        return EnrichedNode(
            node=node,
            description=description,
            process_variable=pv_info.get("name"),
            typical_units=pv_info.get("units", []),
            typical_range=typical_range,
            function_description=func_desc,
            engineering_context=context,
            related_equipment=related,
        )
    
    def enrich_all(self) -> list[EnrichedNode]:
        """
        Enrich all nodes in the graph.
        
        Returns:
            List of EnrichedNode objects
        """
        enriched = []
        
        for node in self.graph.nodes.values():
            if node.node_type == NodeType.INSTRUMENT:
                enriched.append(self.enrich_node(node))
        
        logger.info(f"Enriched {len(enriched)} instrument nodes")
        return enriched
    
    def enrich_by_tag(self, tag: str) -> Optional[EnrichedNode]:
        """Get enriched information for a specific tag."""
        node = self.graph.get_node_by_tag(tag)
        if node:
            return self.enrich_node(node)
        return None
    
    def get_process_variable_summary(self) -> dict:
        """Get summary of process variables in the graph."""
        summary = {}
        
        for node in self.graph.get_instruments():
            if not node.tag:
                continue
            
            result = self.validator.validate_tag(node.tag)
            first = result.parsed_first_letter
            
            if first:
                if first not in summary:
                    info = PROCESS_VARIABLE_INFO.get(first, {})
                    summary[first] = {
                        "name": info.get("name", first),
                        "count": 0,
                        "tags": [],
                    }
                summary[first]["count"] += 1
                summary[first]["tags"].append(node.tag)
        
        return summary
    
    def to_engineering_report(self) -> str:
        """Generate an engineering-focused report."""
        enriched = self.enrich_all()
        pv_summary = self.get_process_variable_summary()
        
        lines = [
            "P&ID Semantic Analysis Report",
            "=" * 50,
            "",
            "Process Variables:",
        ]
        
        for pv, info in sorted(pv_summary.items()):
            lines.append(f"  {pv} ({info['name']}): {info['count']} instruments")
        
        lines.append("")
        lines.append("Instrument Details:")
        lines.append("-" * 50)
        
        for e in sorted(enriched, key=lambda x: x.node.tag or ""):
            lines.append(f"\n{e.node.tag}:")
            lines.append(f"  Description: {e.description}")
            if e.process_variable:
                lines.append(f"  Measures: {e.process_variable}")
            if e.typical_units:
                lines.append(f"  Typical Units: {', '.join(e.typical_units[:3])}")
            if e.related_equipment:
                lines.append(f"  Equipment: {', '.join(e.related_equipment)}")
            for ctx in e.engineering_context:
                lines.append(f"  Note: {ctx}")
        
        return "\n".join(lines)


def enrich_pid_graph(graph: PIDGraph) -> list[EnrichedNode]:
    """Convenience function to enrich a graph."""
    enricher = SemanticEnricher(graph)
    return enricher.enrich_all()
