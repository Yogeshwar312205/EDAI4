"""
EDAI4 - Graph Query Tools
==========================
Query tools for extracting E&I deliverables from P&ID graphs.

Generates:
- Instrument Index
- Control Loop Mapping
- Safety System Analysis
- Equipment Tree
- I/O List
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum
import json

from src.topology.graph_builder import PIDGraph, GraphNode, NodeType, EdgeType
from src.topology.spatial_analyzer import SpatialAnalyzer
from src.topology.flow_analyzer import FlowAnalyzer, FlowDirection
from src.utils import get_logger

logger = get_logger(__name__)


class InstrumentType(Enum):
    """ISA S5.1 instrument types by first letter."""
    ANALYZER = "A"          # Analysis
    BURNER = "B"            # Burner/Combustion
    CONDUCTIVITY = "C"      # User choice
    DENSITY = "D"           # Density
    VOLTAGE = "E"           # Voltage
    FLOW = "F"              # Flow
    GAUGING = "G"           # Gauging/Length
    HAND = "H"              # Hand/Manual
    CURRENT = "I"           # Current
    POWER = "J"             # Power
    TIME = "K"              # Time
    LEVEL = "L"             # Level
    MOISTURE = "M"          # Moisture
    PRESSURE = "P"          # Pressure
    QUANTITY = "Q"          # Quantity
    RADIATION = "R"         # Radiation
    SPEED = "S"             # Speed/Frequency
    TEMPERATURE = "T"       # Temperature
    MULTIVARIABLE = "U"     # Multivariable
    VIBRATION = "V"         # Vibration
    WEIGHT = "W"            # Weight/Force
    POSITION = "Z"          # Position
    UNKNOWN = "?"


@dataclass
class InstrumentIndexEntry:
    """Entry in the Instrument Index."""
    tag: str
    description: str
    instrument_type: InstrumentType
    loop_number: Optional[str] = None
    function_code: Optional[str] = None
    modifier: Optional[str] = None
    service: Optional[str] = None
    location: Optional[str] = None  # Area/Unit
    associated_equipment: list[str] = field(default_factory=list)
    io_type: Optional[str] = None  # AI, AO, DI, DO
    pid_reference: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "tag": self.tag,
            "description": self.description,
            "type": self.instrument_type.value,
            "loop_number": self.loop_number,
            "function": self.function_code,
            "modifier": self.modifier,
            "service": self.service,
            "location": self.location,
            "equipment": self.associated_equipment,
            "io_type": self.io_type,
            "pid_ref": self.pid_reference,
        }


@dataclass
class ControlLoop:
    """A control loop identified in the P&ID."""
    loop_id: str
    loop_type: str  # "regulatory", "safety", "monitoring"
    transmitter_tag: Optional[str] = None
    controller_tag: Optional[str] = None
    final_element_tag: Optional[str] = None  # Usually a control valve
    process_variable: Optional[str] = None   # What is being measured
    controlled_equipment: list[str] = field(default_factory=list)
    
    @property
    def is_complete(self) -> bool:
        """Check if loop has all required elements."""
        return all([
            self.transmitter_tag,
            self.controller_tag or self.final_element_tag
        ])
    
    def to_dict(self) -> dict:
        return {
            "loop_id": self.loop_id,
            "loop_type": self.loop_type,
            "transmitter": self.transmitter_tag,
            "controller": self.controller_tag,
            "final_element": self.final_element_tag,
            "process_variable": self.process_variable,
            "equipment": self.controlled_equipment,
            "complete": self.is_complete,
        }


@dataclass 
class SafetyFunction:
    """A safety instrumented function (SIF)."""
    sif_id: str
    description: str
    initiator_tags: list[str] = field(default_factory=list)  # Sensors
    logic_solver: Optional[str] = None  # SIS/ESD controller
    final_elements: list[str] = field(default_factory=list)  # Valves, shutdown
    protected_equipment: list[str] = field(default_factory=list)
    sil_level: Optional[int] = None  # 1, 2, or 3
    
    def to_dict(self) -> dict:
        return {
            "sif_id": self.sif_id,
            "description": self.description,
            "initiators": self.initiator_tags,
            "logic_solver": self.logic_solver,
            "final_elements": self.final_elements,
            "protected_equipment": self.protected_equipment,
            "sil": self.sil_level,
        }


class GraphQueryTools:
    """
    Query tools for extracting deliverables from P&ID graphs.
    
    Provides methods for generating:
    - Instrument Index
    - Control Loop Mapping
    - Safety System Analysis
    - Equipment Hierarchy
    """
    
    def __init__(self, graph: PIDGraph):
        """
        Initialize query tools.
        
        Args:
            graph: PIDGraph to query
        """
        self.graph = graph
        self._spatial_analyzer: Optional[SpatialAnalyzer] = None
        self._flow_analyzer: Optional[FlowAnalyzer] = None
    
    @property
    def spatial(self) -> SpatialAnalyzer:
        """Lazy-load spatial analyzer."""
        if self._spatial_analyzer is None:
            self._spatial_analyzer = SpatialAnalyzer(self.graph)
        return self._spatial_analyzer
    
    @property
    def flow(self) -> FlowAnalyzer:
        """Lazy-load flow analyzer."""
        if self._flow_analyzer is None:
            self._flow_analyzer = FlowAnalyzer(self.graph)
        return self._flow_analyzer
    
    def _parse_instrument_type(self, tag: str) -> InstrumentType:
        """Extract instrument type from tag's first letter."""
        if not tag:
            return InstrumentType.UNKNOWN
        
        # Extract first letter (skip prefixes like area codes)
        clean_tag = ''.join(c for c in tag if c.isalpha())
        if not clean_tag:
            return InstrumentType.UNKNOWN
        
        first_letter = clean_tag[0].upper()
        
        for itype in InstrumentType:
            if itype.value == first_letter:
                return itype
        
        return InstrumentType.UNKNOWN
    
    def _get_function_description(self, function_code: str) -> str:
        """Get description for ISA function code."""
        descriptions = {
            "A": "Analyzer", "B": "Burner", "C": "Controller",
            "D": "Differential", "E": "Element/Sensor",
            "F": "Flow", "G": "Gauge/Glass", "H": "High",
            "I": "Indicating", "J": "Scan", "K": "Station",
            "L": "Level/Low", "M": "Middle/Momentary",
            "N": "User Choice", "O": "Orifice",
            "P": "Pressure/Point", "Q": "Quantity",
            "R": "Recording", "S": "Switch/Safety",
            "T": "Temperature/Transmitter", "U": "Multifunction",
            "V": "Valve", "W": "Well/Weight", "X": "Unclassified",
            "Y": "Relay/Compute", "Z": "Position/Actuator",
        }
        
        result = []
        for letter in function_code.upper():
            if letter in descriptions:
                result.append(descriptions[letter])
        
        return " ".join(result) if result else "Unknown"
    
    def generate_instrument_index(self) -> list[InstrumentIndexEntry]:
        """
        Generate Instrument Index from graph.
        
        Returns:
            List of InstrumentIndexEntry objects
        """
        entries = []
        instruments = self.graph.get_instruments()
        
        # Get containment info for equipment associations
        containment = self.spatial.detect_containment()
        
        # Build reverse lookup: instrument → container
        inst_to_equipment = {}
        for relation in containment:
            for contained_id in relation.contained_ids:
                inst_to_equipment[contained_id] = relation.container_id
        
        for inst in instruments:
            if not inst.tag:
                continue
            
            # Parse tag information
            parsed = inst.parsed_tag
            itype = self._parse_instrument_type(inst.tag)
            
            # Build function code from tag
            func_code = ""
            if parsed:
                func_code = getattr(parsed, 'function', '') or ""
            else:
                # Extract letters from tag
                func_code = ''.join(c for c in inst.tag if c.isalpha())
            
            # Get associated equipment
            assoc_equipment = []
            if inst.id in inst_to_equipment:
                container = self.graph.nodes.get(inst_to_equipment[inst.id])
                if container and container.tag:
                    assoc_equipment.append(container.tag)
            
            # Also check MEASURES edges
            for node, edge in self.graph.get_connected_nodes(inst.id, EdgeType.MEASURES):
                if node.tag and node.tag not in assoc_equipment:
                    assoc_equipment.append(node.tag)
            
            # Determine I/O type from function code
            io_type = None
            if func_code:
                if 'T' in func_code.upper():  # Transmitter
                    io_type = "AI"  # Analog Input
                elif 'S' in func_code.upper():  # Switch
                    io_type = "DI"  # Digital Input
                elif 'V' in func_code.upper():  # Valve
                    io_type = "AO"  # Analog Output
                elif 'Y' in func_code.upper():  # Relay
                    io_type = "DO"  # Digital Output
            
            entry = InstrumentIndexEntry(
                tag=inst.tag,
                description=self._get_function_description(func_code),
                instrument_type=itype,
                loop_number=getattr(parsed, 'loop_number', None) if parsed else None,
                function_code=func_code,
                modifier=getattr(parsed, 'modifier', None) if parsed else None,
                service=inst.description,
                location=getattr(parsed, 'area', None) if parsed else None,
                associated_equipment=assoc_equipment,
                io_type=io_type,
            )
            entries.append(entry)
        
        # Sort by tag
        entries.sort(key=lambda e: e.tag)
        
        logger.info(f"Generated instrument index with {len(entries)} entries")
        return entries
    
    def identify_control_loops(self) -> list[ControlLoop]:
        """
        Identify control loops in the graph.
        
        A control loop typically consists of:
        - Transmitter (xT): Measures process variable
        - Controller (xC): Processes signal
        - Final Element (xV): Usually a control valve
        
        Returns:
            List of identified control loops
        """
        loops = []
        instruments = self.graph.get_instruments()
        valves = self.graph.get_valves()
        
        # Group instruments by loop number
        loop_groups: dict[str, list[GraphNode]] = {}
        for inst in instruments:
            loop_num = None
            if inst.parsed_tag:
                loop_num = getattr(inst.parsed_tag, 'loop_number', None)
            
            if loop_num:
                if loop_num not in loop_groups:
                    loop_groups[loop_num] = []
                loop_groups[loop_num].append(inst)
        
        # Also check valves for control valves (xCV, FV, etc.)
        control_valve_tags = {}
        for valve in valves:
            if valve.tag and valve.detection_class:
                if 'control' in valve.detection_class.lower():
                    # Extract loop number from valve tag
                    loop_num = ''.join(c for c in valve.tag if c.isdigit())
                    if loop_num:
                        control_valve_tags[loop_num] = valve.tag
        
        # Build control loops from groups
        for loop_num, members in loop_groups.items():
            transmitter = None
            controller = None
            
            for inst in members:
                func = inst.tag.upper() if inst.tag else ""
                if 'T' in func:  # Transmitter
                    transmitter = inst.tag
                elif 'C' in func or 'IC' in func:  # Controller
                    controller = inst.tag
            
            # Look for associated final element
            final_element = control_valve_tags.get(loop_num)
            
            # Determine loop type
            loop_type = "regulatory"
            if transmitter and any(s in transmitter.upper() for s in ['PSH', 'LSH', 'TSH', 'PSL', 'LSL', 'TSL']):
                loop_type = "safety"
            elif not controller and not final_element:
                loop_type = "monitoring"
            
            # Determine process variable from first letter
            pv = None
            if transmitter:
                first_letter = ''.join(c for c in transmitter if c.isalpha())[0:1]
                pv_map = {'F': 'Flow', 'L': 'Level', 'P': 'Pressure', 'T': 'Temperature'}
                pv = pv_map.get(first_letter.upper())
            
            loop = ControlLoop(
                loop_id=f"LOOP-{loop_num}",
                loop_type=loop_type,
                transmitter_tag=transmitter,
                controller_tag=controller,
                final_element_tag=final_element,
                process_variable=pv,
            )
            loops.append(loop)
        
        logger.info(f"Identified {len(loops)} control loops")
        return loops
    
    def identify_safety_functions(self) -> list[SafetyFunction]:
        """
        Identify Safety Instrumented Functions (SIFs).
        
        Looks for:
        - High/Low switches (xSH, xSL, xSHH, xSLL)
        - Safety valves (SDV, BDV)
        - Emergency shutdown elements
        
        Returns:
            List of identified safety functions
        """
        sifs = []
        instruments = self.graph.get_instruments()
        valves = self.graph.get_valves()
        
        # Find safety initiators (switches with H/L modifiers)
        initiators = []
        for inst in instruments:
            if not inst.tag:
                continue
            tag_upper = inst.tag.upper()
            
            # Look for safety switches
            if any(pattern in tag_upper for pattern in ['SH', 'SL', 'AH', 'AL', 'HH', 'LL']):
                initiators.append(inst)
        
        # Find safety final elements
        final_elements = []
        for valve in valves:
            if not valve.tag:
                continue
            tag_upper = valve.tag.upper()
            
            # Safety/shutdown valves
            if any(pattern in tag_upper for pattern in ['SDV', 'BDV', 'XV', 'ESV']):
                final_elements.append(valve)
        
        # Group by protected equipment using spatial analysis
        # For now, create one SIF per initiator-final element pair in proximity
        
        if initiators:
            # Create a general safety function
            sif = SafetyFunction(
                sif_id="SIF-001",
                description="Process Safety Shutdown",
                initiator_tags=[i.tag for i in initiators if i.tag],
                final_elements=[v.tag for v in final_elements if v.tag],
                sil_level=1,  # Default, would need LOPA analysis
            )
            sifs.append(sif)
        
        logger.info(f"Identified {len(sifs)} safety functions")
        return sifs
    
    def build_equipment_tree(self) -> dict:
        """
        Build hierarchical equipment tree.
        
        Groups equipment by area/unit and includes associated instruments.
        
        Returns:
            Hierarchical dictionary of equipment
        """
        tree = {"areas": {}}
        equipment = self.graph.get_equipment()
        
        # Get containment relationships
        containment = self.spatial.detect_containment()
        
        # Build equipment -> instruments map
        eq_instruments = {}
        for rel in containment:
            container = self.graph.nodes.get(rel.container_id)
            if container:
                eq_tag = container.tag or container.id
                eq_instruments[eq_tag] = []
                for cid in rel.contained_ids:
                    contained = self.graph.nodes.get(cid)
                    if contained and contained.tag:
                        eq_instruments[eq_tag].append(contained.tag)
        
        # Organize by area (from parsed tags or default)
        for eq in equipment:
            area = "AREA-00"  # Default
            if eq.parsed_tag:
                area = getattr(eq.parsed_tag, 'area', None) or area
            
            if area not in tree["areas"]:
                tree["areas"][area] = {"equipment": []}
            
            eq_entry = {
                "tag": eq.tag or eq.id,
                "type": eq.detection_class or "equipment",
                "description": eq.description or eq.label,
                "instruments": eq_instruments.get(eq.tag or eq.id, []),
            }
            tree["areas"][area]["equipment"].append(eq_entry)
        
        return tree
    
    def generate_io_list(self) -> list[dict]:
        """
        Generate I/O List for DCS/PLC configuration.
        
        Returns:
            List of I/O point dictionaries
        """
        io_list = []
        instruments = self.graph.get_instruments()
        
        for inst in instruments:
            if not inst.tag:
                continue
            
            func = inst.tag.upper()
            
            # Determine I/O type
            io_type = "AI"  # Default analog input
            
            if any(s in func for s in ['SH', 'SL', 'AH', 'AL', 'SW']):
                io_type = "DI"  # Digital input (switches/alarms)
            elif 'Y' in func or 'SOL' in func:
                io_type = "DO"  # Digital output (solenoids)
            elif 'CV' in func or 'V' in func:
                if inst.node_type == NodeType.VALVE:
                    io_type = "AO"  # Analog output (control valves)
            elif 'T' in func:  # Transmitters
                io_type = "AI"
            
            io_entry = {
                "tag": inst.tag,
                "io_type": io_type,
                "description": inst.description or self._get_function_description(func),
                "signal_type": "4-20mA" if io_type.startswith('A') else "24VDC",
                "range": "0-100%" if io_type == "AI" else None,
                "alarm_high": None,
                "alarm_low": None,
                "interlock": "SH" in func or "SL" in func or "HH" in func or "LL" in func,
            }
            io_list.append(io_entry)
        
        # Sort by tag
        io_list.sort(key=lambda x: x["tag"])
        
        logger.info(f"Generated I/O list with {len(io_list)} points")
        return io_list
    
    def export_deliverables(self, output_path: str):
        """
        Export all deliverables to JSON file.
        
        Args:
            output_path: Path to output JSON file
        """
        deliverables = {
            "instrument_index": [e.to_dict() for e in self.generate_instrument_index()],
            "control_loops": [l.to_dict() for l in self.identify_control_loops()],
            "safety_functions": [s.to_dict() for s in self.identify_safety_functions()],
            "equipment_tree": self.build_equipment_tree(),
            "io_list": self.generate_io_list(),
        }
        
        with open(output_path, 'w') as f:
            json.dump(deliverables, f, indent=2)
        
        logger.info(f"Exported deliverables to {output_path}")
        return deliverables
    
    def summary(self) -> str:
        """Generate summary of extractable deliverables."""
        inst_index = self.generate_instrument_index()
        loops = self.identify_control_loops()
        sifs = self.identify_safety_functions()
        io_list = self.generate_io_list()
        
        lines = [
            "E&I Deliverables Summary",
            "=" * 40,
            f"Instrument Index: {len(inst_index)} instruments",
            f"Control Loops: {len(loops)} loops",
            f"  - Regulatory: {len([l for l in loops if l.loop_type == 'regulatory'])}",
            f"  - Safety: {len([l for l in loops if l.loop_type == 'safety'])}",
            f"  - Monitoring: {len([l for l in loops if l.loop_type == 'monitoring'])}",
            f"Safety Functions: {len(sifs)} SIFs",
            f"I/O Points: {len(io_list)}",
            f"  - AI: {len([i for i in io_list if i['io_type'] == 'AI'])}",
            f"  - AO: {len([i for i in io_list if i['io_type'] == 'AO'])}",
            f"  - DI: {len([i for i in io_list if i['io_type'] == 'DI'])}",
            f"  - DO: {len([i for i in io_list if i['io_type'] == 'DO'])}",
        ]
        
        return "\n".join(lines)


def print_deliverables_summary(graph: PIDGraph):
    """Convenience function to print deliverables summary."""
    tools = GraphQueryTools(graph)
    print(tools.summary())
    return tools
