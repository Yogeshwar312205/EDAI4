"""
Design Rule Checker - Automated Quality Control
Validates P&ID against engineering standards
"""
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    """Rule violation severity"""
    CRITICAL = "Critical"
    WARNING = "Warning"
    INFO = "Info"


@dataclass
class RuleViolation:
    """Design rule violation"""
    rule_id: str
    rule_name: str
    severity: Severity
    description: str
    affected_items: List[str]
    recommendation: str
    location: Dict[str, float] = None


class DesignRuleChecker:
    """Check P&ID against engineering design rules"""
    
    def __init__(self):
        self.rules = self._initialize_rules()
    
    def check_all(self, graph) -> List[RuleViolation]:
        """Run all design rule checks"""
        
        violations = []
        
        for rule_func in self.rules:
            rule_violations = rule_func(graph)
            violations.extend(rule_violations)
        
        # Sort by severity
        violations.sort(key=lambda x: (
            0 if x.severity == Severity.CRITICAL else 
            1 if x.severity == Severity.WARNING else 2
        ))
        
        return violations
    
    def _initialize_rules(self) -> List:
        """Initialize all rule checking functions"""
        return [
            self._check_control_valve_isolation,
            self._check_pump_suction_strainer,
            self._check_orphaned_instruments,
            self._check_missing_tags,
            self._check_duplicate_tags,
            self._check_valve_orientation,
            self._check_instrument_connectivity,
            self._check_safety_valve_requirements,
        ]
    
    def _check_control_valve_isolation(self, graph) -> List[RuleViolation]:
        """
        Rule: Control valves must have upstream and downstream isolation valves
        """
        violations = []
        
        # Find all control valves
        control_valves = [
            node for node in graph.get_all_nodes()
            if node.node_type.value == 'valve' and 
            node.tag and 'CV' in node.tag.upper()
        ]
        
        for cv in control_valves:
            # Check for upstream and downstream isolation valves
            upstream_valves = self._find_upstream_valves(cv, graph)
            downstream_valves = self._find_downstream_valves(cv, graph)
            
            issues = []
            if not upstream_valves:
                issues.append("missing upstream isolation valve")
            if not downstream_valves:
                issues.append("missing downstream isolation valve")
            
            if issues:
                violations.append(RuleViolation(
                    rule_id="DRC-001",
                    rule_name="Control Valve Isolation",
                    severity=Severity.WARNING,
                    description=f"Control valve {cv.tag} is {' and '.join(issues)}",
                    affected_items=[cv.tag],
                    recommendation="Add isolation valves upstream and downstream of control valve for maintenance",
                    location={'x': cv.x, 'y': cv.y} if hasattr(cv, 'x') else None
                ))
        
        return violations
    
    def _check_pump_suction_strainer(self, graph) -> List[RuleViolation]:
        """
        Rule: Pump suction lines must have a strainer
        """
        violations = []
        
        # Find all pumps
        pumps = [
            node for node in graph.get_all_nodes()
            if node.node_type.value == 'pump'
        ]
        
        for pump in pumps:
            # Check for strainer on suction line
            has_strainer = self._has_upstream_strainer(pump, graph)
            
            if not has_strainer:
                violations.append(RuleViolation(
                    rule_id="DRC-002",
                    rule_name="Pump Suction Strainer",
                    severity=Severity.CRITICAL,
                    description=f"Pump {pump.tag or 'UNTAGGED'} is missing a suction strainer",
                    affected_items=[pump.tag or pump.id],
                    recommendation="Install a strainer on the pump suction line to protect against debris",
                    location={'x': pump.x, 'y': pump.y} if hasattr(pump, 'x') else None
                ))
        
        return violations
    
    def _check_orphaned_instruments(self, graph) -> List[RuleViolation]:
        """
        Rule: Instruments must be connected to equipment or lines
        """
        violations = []
        
        # Find all instruments
        instruments = [
            node for node in graph.get_all_nodes()
            if node.node_type.value == 'instrument' and node.tag
        ]
        
        for instrument in instruments:
            # Check if connected to anything
            incoming_edges = list(graph.get_edges_to_node(instrument.id))
            outgoing_edges = list(graph.get_edges_from_node(instrument.id))
            
            if not incoming_edges and not outgoing_edges:
                violations.append(RuleViolation(
                    rule_id="DRC-003",
                    rule_name="Orphaned Instrument",
                    severity=Severity.WARNING,
                    description=f"Instrument {instrument.tag} is not connected to any equipment or lines",
                    affected_items=[instrument.tag],
                    recommendation="Connect instrument to the process line or equipment it monitors",
                    location={'x': instrument.x, 'y': instrument.y} if hasattr(instrument, 'x') else None
                ))
        
        return violations
    
    def _check_missing_tags(self, graph) -> List[RuleViolation]:
        """
        Rule: All instruments and equipment should have tags
        """
        violations = []
        
        untagged_items = []
        
        for node in graph.get_all_nodes():
            if node.node_type.value in ['instrument', 'equipment', 'pump', 'valve']:
                if not node.tag or node.tag == 'UNTAGGED':
                    untagged_items.append({
                        'id': node.id,
                        'type': node.node_type.value,
                        'location': {'x': node.x, 'y': node.y} if hasattr(node, 'x') else None
                    })
        
        if untagged_items:
            violations.append(RuleViolation(
                rule_id="DRC-004",
                rule_name="Missing Tags",
                severity=Severity.INFO,
                description=f"Found {len(untagged_items)} untagged items",
                affected_items=[item['id'] for item in untagged_items],
                recommendation="Assign unique tags to all instruments and equipment per ISA S5.1 standard"
            ))
        
        return violations
    
    def _check_duplicate_tags(self, graph) -> List[RuleViolation]:
        """
        Rule: Tags must be unique
        """
        violations = []
        
        tag_counts = {}
        tag_locations = {}
        
        for node in graph.get_all_nodes():
            if node.tag and node.tag != 'UNTAGGED':
                tag = node.tag.upper()
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
                
                if tag not in tag_locations:
                    tag_locations[tag] = []
                tag_locations[tag].append(node.id)
        
        for tag, count in tag_counts.items():
            if count > 1:
                violations.append(RuleViolation(
                    rule_id="DRC-005",
                    rule_name="Duplicate Tags",
                    severity=Severity.CRITICAL,
                    description=f"Tag '{tag}' is used {count} times",
                    affected_items=tag_locations[tag],
                    recommendation="Ensure all tags are unique. Revise duplicate tags per ISA S5.1 standard"
                ))
        
        return violations
    
    def _check_valve_orientation(self, graph) -> List[RuleViolation]:
        """
        Rule: Check valve should be installed in correct flow direction
        """
        violations = []
        
        # Find check valves
        check_valves = [
            node for node in graph.get_all_nodes()
            if node.node_type.value == 'valve' and 
            node.tag and 'CHK' in node.tag.upper()
        ]
        
        for valve in check_valves:
            # This would require flow direction analysis
            # For now, just flag for manual review
            violations.append(RuleViolation(
                rule_id="DRC-006",
                rule_name="Check Valve Orientation",
                severity=Severity.INFO,
                description=f"Check valve {valve.tag} - verify correct flow direction",
                affected_items=[valve.tag],
                recommendation="Verify check valve is installed in correct flow direction",
                location={'x': valve.x, 'y': valve.y} if hasattr(valve, 'x') else None
            ))
        
        return violations
    
    def _check_instrument_connectivity(self, graph) -> List[RuleViolation]:
        """
        Rule: Transmitters should be connected to indicators or controllers
        """
        violations = []
        
        # Find transmitters
        transmitters = [
            node for node in graph.get_all_nodes()
            if node.tag and node.tag.endswith('T') and 
            len(node.tag) > 2 and node.tag[-2] != 'T'
        ]
        
        for transmitter in transmitters:
            # Check if connected to controller or indicator
            has_controller = False
            
            for edge in graph.get_edges_from_node(transmitter.id):
                target = graph.get_node(edge.target_id)
                if target and target.tag:
                    if 'C' in target.tag or 'I' in target.tag:
                        has_controller = True
                        break
            
            if not has_controller:
                violations.append(RuleViolation(
                    rule_id="DRC-007",
                    rule_name="Transmitter Connectivity",
                    severity=Severity.INFO,
                    description=f"Transmitter {transmitter.tag} may not be connected to a controller or indicator",
                    affected_items=[transmitter.tag],
                    recommendation="Verify transmitter signal is connected to control system",
                    location={'x': transmitter.x, 'y': transmitter.y} if hasattr(transmitter, 'x') else None
                ))
        
        return violations
    
    def _check_safety_valve_requirements(self, graph) -> List[RuleViolation]:
        """
        Rule: Pressure vessels should have safety relief valves
        """
        violations = []
        
        # Find vessels
        vessels = [
            node for node in graph.get_all_nodes()
            if node.node_type.value in ['vessel', 'tank']
        ]
        
        for vessel in vessels:
            # Check for safety valve
            has_safety_valve = False
            
            for edge in graph.get_edges_from_node(vessel.id):
                target = graph.get_node(edge.target_id)
                if target and target.tag and ('PSV' in target.tag.upper() or 'PRV' in target.tag.upper()):
                    has_safety_valve = True
                    break
            
            if not has_safety_valve:
                violations.append(RuleViolation(
                    rule_id="DRC-008",
                    rule_name="Safety Valve Requirement",
                    severity=Severity.CRITICAL,
                    description=f"Vessel {vessel.tag or 'UNTAGGED'} may be missing a safety relief valve",
                    affected_items=[vessel.tag or vessel.id],
                    recommendation="Install pressure safety valve (PSV) per ASME code requirements",
                    location={'x': vessel.x, 'y': vessel.y} if hasattr(vessel, 'x') else None
                ))
        
        return violations
    
    # Helper methods
    
    def _find_upstream_valves(self, node, graph) -> List:
        """Find valves upstream of a node"""
        valves = []
        for edge in graph.get_edges_to_node(node.id):
            source = graph.get_node(edge.source_id)
            if source and source.node_type.value == 'valve':
                valves.append(source)
        return valves
    
    def _find_downstream_valves(self, node, graph) -> List:
        """Find valves downstream of a node"""
        valves = []
        for edge in graph.get_edges_from_node(node.id):
            target = graph.get_node(edge.target_id)
            if target and target.node_type.value == 'valve':
                valves.append(target)
        return valves
    
    def _has_upstream_strainer(self, node, graph) -> bool:
        """Check if node has upstream strainer"""
        for edge in graph.get_edges_to_node(node.id):
            source = graph.get_node(edge.source_id)
            if source and source.tag and 'STR' in source.tag.upper():
                return True
        return False
