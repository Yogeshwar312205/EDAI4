"""
EDAI4 - Control Strategy Classifier
=====================================
Classifies control loops into strategy types.

Strategies:
- Regulatory: Basic feedback control (PID)
- Cascade: Master-slave controller pairs
- Ratio: Maintains ratio between two flows
- Feedforward: Anticipatory control
- Split-range: Multiple valves, one controller
- Override/Select: High/low selection
- Safety: SIS/ESD/Trip systems
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from src.topology.graph_builder import PIDGraph, GraphNode, NodeType, EdgeType
from src.cognitive.isa_validator import ISAS51Validator, ISA_FIRST_LETTERS
from src.utils import get_logger

logger = get_logger(__name__)


class ControlStrategy(Enum):
    """Types of control strategies."""
    REGULATORY = "regulatory"        # Basic PID loop
    CASCADE = "cascade"              # Master-slave (PIC→FIC)
    RATIO = "ratio"                  # Ratio control (FFC)
    FEEDFORWARD = "feedforward"      # Anticipatory control
    SPLIT_RANGE = "split_range"      # One controller, multiple valves
    OVERRIDE = "override"            # High/low select
    SAFETY = "safety"                # SIS/ESD systems
    MONITORING = "monitoring"        # No control action
    UNKNOWN = "unknown"


class LoopPriority(Enum):
    """Control loop priority classification."""
    SAFETY_CRITICAL = "safety_critical"   # SIL-rated, trip systems
    HIGH = "high"                          # Product quality, major equipment
    MEDIUM = "medium"                      # Normal process control
    LOW = "low"                            # Monitoring, non-critical
    UNKNOWN = "unknown"


@dataclass
class ClassifiedLoop:
    """A control loop with strategy classification."""
    loop_id: str
    strategy: ControlStrategy
    priority: LoopPriority
    confidence: float
    
    # Loop components
    transmitters: list[str] = field(default_factory=list)
    controllers: list[str] = field(default_factory=list)
    final_elements: list[str] = field(default_factory=list)
    
    # Strategy-specific info
    master_controller: Optional[str] = None  # For cascade
    slave_controller: Optional[str] = None   # For cascade
    ratio_tag: Optional[str] = None          # For ratio
    
    # Classification reasons
    reasons: list[str] = field(default_factory=list)
    
    @property
    def is_complete(self) -> bool:
        """Check if loop has minimum required elements."""
        has_measurement = len(self.transmitters) > 0
        has_control = len(self.controllers) > 0 or len(self.final_elements) > 0
        return has_measurement and has_control
    
    def to_dict(self) -> dict:
        return {
            "loop_id": self.loop_id,
            "strategy": self.strategy.value,
            "priority": self.priority.value,
            "confidence": self.confidence,
            "transmitters": self.transmitters,
            "controllers": self.controllers,
            "final_elements": self.final_elements,
            "master_controller": self.master_controller,
            "slave_controller": self.slave_controller,
            "ratio_tag": self.ratio_tag,
            "complete": self.is_complete,
            "reasons": self.reasons,
        }


class ControlStrategyClassifier:
    """
    Classifies control loops into strategy types.
    
    Uses tag analysis and graph topology to identify:
    - Loop type (regulatory, cascade, ratio, etc.)
    - Priority level
    - Control relationships
    """
    
    # Safety-related tag patterns
    SAFETY_PATTERNS = [
        "SH", "SL", "SHH", "SLL",  # High/low switches
        "AH", "AL", "AHH", "ALL",  # High/low alarms
        "SDV", "BDV", "XV",        # Safety valves
        "ESD", "SIS",              # Emergency shutdown
        "PSV", "TSV",              # Pressure/temperature safety valves
    ]
    
    # Override/select patterns
    OVERRIDE_PATTERNS = [
        "HSL", "LSL",  # High/low select
        "SEL",         # Select
        ">", "<",      # High/low select symbols in tag
    ]
    
    def __init__(self, graph: PIDGraph):
        """
        Initialize classifier.
        
        Args:
            graph: PIDGraph to analyze
        """
        self.graph = graph
        self.validator = ISAS51Validator()
        self._loop_cache: dict[str, list[GraphNode]] = {}
    
    def _group_by_loop_number(self) -> dict[str, list[GraphNode]]:
        """Group instruments by loop number."""
        if self._loop_cache:
            return self._loop_cache
        
        loops = {}
        
        for node in self.graph.nodes.values():
            if node.node_type != NodeType.INSTRUMENT:
                continue
            
            if not node.tag:
                continue
            
            # Extract loop number from tag
            result = self.validator.validate_tag(node.tag)
            loop_num = result.parsed_loop_number
            
            if loop_num:
                if loop_num not in loops:
                    loops[loop_num] = []
                loops[loop_num].append(node)
        
        self._loop_cache = loops
        return loops
    
    def _extract_function_letters(self, tag: str) -> tuple[str, str]:
        """Extract first letter and succeeding letters from tag."""
        result = self.validator.validate_tag(tag)
        return (
            result.parsed_first_letter or "",
            result.parsed_succeeding_letters or "",
        )
    
    def _is_safety_related(self, tag: str) -> bool:
        """Check if tag indicates safety function."""
        tag_upper = tag.upper()
        return any(pattern in tag_upper for pattern in self.SAFETY_PATTERNS)
    
    def _is_transmitter(self, tag: str) -> bool:
        """Check if tag is a transmitter."""
        _, succeeding = self._extract_function_letters(tag)
        return "T" in succeeding and "C" not in succeeding
    
    def _is_controller(self, tag: str) -> bool:
        """Check if tag is a controller."""
        _, succeeding = self._extract_function_letters(tag)
        return "C" in succeeding or "IC" in succeeding
    
    def _is_indicator_only(self, tag: str) -> bool:
        """Check if tag is indicator only (no control)."""
        _, succeeding = self._extract_function_letters(tag)
        return succeeding in ("I", "IR", "R") and "C" not in succeeding
    
    def _is_final_element(self, node: GraphNode) -> bool:
        """Check if node is a final control element."""
        if node.node_type == NodeType.VALVE:
            return True
        
        if node.tag:
            _, succeeding = self._extract_function_letters(node.tag)
            return "V" in succeeding or "Y" in succeeding or "Z" in succeeding
        
        return False
    
    def _detect_cascade(self, loop_nodes: list[GraphNode]) -> Optional[tuple[str, str]]:
        """
        Detect cascade control configuration.
        
        Cascade: Two controllers where output of one (master) sets
        setpoint of another (slave).
        
        Returns:
            (master_tag, slave_tag) if cascade found, None otherwise
        """
        controllers = [n for n in loop_nodes if n.tag and self._is_controller(n.tag)]
        
        if len(controllers) < 2:
            return None
        
        # Look for typical cascade patterns
        # e.g., TIC (master) → FIC (slave), LIC (master) → FIC (slave)
        for c1 in controllers:
            for c2 in controllers:
                if c1.id == c2.id:
                    continue
                
                first1, _ = self._extract_function_letters(c1.tag)
                first2, _ = self._extract_function_letters(c2.tag)
                
                # Common cascade: slow variable (T, L, A) controls fast (F, P)
                slow_vars = {"T", "L", "A", "C"}
                fast_vars = {"F", "P"}
                
                if first1 in slow_vars and first2 in fast_vars:
                    # Check if they're connected
                    for connected, edge in self.graph.get_connected_nodes(c1.id):
                        if connected.id == c2.id:
                            return (c1.tag, c2.tag)
                    
                    # Or if they share similar loop number
                    return (c1.tag, c2.tag)
        
        return None
    
    def _detect_ratio(self, loop_nodes: list[GraphNode]) -> Optional[str]:
        """
        Detect ratio control configuration.
        
        Ratio: Maintains ratio between two flows.
        Look for FFC (flow fraction controller) or ratio stations.
        
        Returns:
            Ratio tag if found
        """
        for node in loop_nodes:
            if not node.tag:
                continue
            
            tag_upper = node.tag.upper()
            _, succeeding = self._extract_function_letters(node.tag)
            
            # FFC = Flow Fraction Controller
            if "FF" in tag_upper or "F" in succeeding and "F" in succeeding:
                return node.tag
            
            # FK = Ratio station
            if "FK" in tag_upper:
                return node.tag
        
        return None
    
    def _detect_split_range(self, loop_num: str) -> bool:
        """
        Detect split-range control.
        
        Split-range: One controller drives multiple valves.
        """
        loop_nodes = self._loop_cache.get(loop_num, [])
        
        controllers = [n for n in loop_nodes if n.tag and self._is_controller(n.tag)]
        valves = [n for n in loop_nodes if self._is_final_element(n)]
        
        # Also check graph for connected valves
        connected_valves = 0
        for ctrl in controllers:
            for node, edge in self.graph.get_connected_nodes(ctrl.id, EdgeType.CONTROLS):
                if self._is_final_element(node):
                    connected_valves += 1
        
        total_valves = len(valves) + connected_valves
        
        # Split-range typically has 2+ valves per controller
        return len(controllers) > 0 and total_valves >= 2
    
    def _determine_priority(self, loop_nodes: list[GraphNode], strategy: ControlStrategy) -> LoopPriority:
        """Determine loop priority based on tags and strategy."""
        
        # Safety loops are always safety-critical
        if strategy == ControlStrategy.SAFETY:
            return LoopPriority.SAFETY_CRITICAL
        
        # Check for safety-related tags in any loop member
        for node in loop_nodes:
            if node.tag and self._is_safety_related(node.tag):
                return LoopPriority.SAFETY_CRITICAL
        
        # Monitoring loops are low priority
        if strategy == ControlStrategy.MONITORING:
            return LoopPriority.LOW
        
        # Check measured variable for priority hints
        for node in loop_nodes:
            if not node.tag:
                continue
            
            first, _ = self._extract_function_letters(node.tag)
            
            # Critical process variables
            if first in ("T", "P"):  # Temperature, Pressure
                return LoopPriority.HIGH
            
            # Quality-related
            if first in ("A", "C"):  # Analysis, Conductivity
                return LoopPriority.HIGH
        
        return LoopPriority.MEDIUM
    
    def classify_loop(self, loop_num: str) -> ClassifiedLoop:
        """
        Classify a single control loop.
        
        Args:
            loop_num: Loop number to classify
            
        Returns:
            ClassifiedLoop with strategy and details
        """
        loop_nodes = self._group_by_loop_number().get(loop_num, [])
        
        result = ClassifiedLoop(
            loop_id=f"LOOP-{loop_num}",
            strategy=ControlStrategy.UNKNOWN,
            priority=LoopPriority.UNKNOWN,
            confidence=0.0,
        )
        
        if not loop_nodes:
            result.reasons.append(f"No instruments found for loop {loop_num}")
            return result
        
        # Categorize nodes
        for node in loop_nodes:
            if not node.tag:
                continue
            
            if self._is_transmitter(node.tag):
                result.transmitters.append(node.tag)
            elif self._is_controller(node.tag):
                result.controllers.append(node.tag)
            elif self._is_final_element(node):
                result.final_elements.append(node.tag)
        
        # Also check valves in the graph
        for valve in self.graph.get_valves():
            if not valve.tag:
                continue
            
            # Check if valve tag contains this loop number
            v_result = self.validator.validate_tag(valve.tag)
            if v_result.parsed_loop_number == loop_num:
                if valve.tag not in result.final_elements:
                    result.final_elements.append(valve.tag)
        
        # Classify strategy
        strategy = ControlStrategy.UNKNOWN
        confidence = 0.5
        reasons = []
        
        # Check for safety first (highest priority classification)
        has_safety = any(self._is_safety_related(n.tag) for n in loop_nodes if n.tag)
        if has_safety:
            strategy = ControlStrategy.SAFETY
            confidence = 0.9
            reasons.append("Contains safety-related instruments (SH/SL/AH/AL)")
        
        # Check for cascade
        elif (cascade := self._detect_cascade(loop_nodes)):
            strategy = ControlStrategy.CASCADE
            result.master_controller = cascade[0]
            result.slave_controller = cascade[1]
            confidence = 0.8
            reasons.append(f"Cascade: {cascade[0]} (master) → {cascade[1]} (slave)")
        
        # Check for ratio
        elif (ratio_tag := self._detect_ratio(loop_nodes)):
            strategy = ControlStrategy.RATIO
            result.ratio_tag = ratio_tag
            confidence = 0.85
            reasons.append(f"Ratio control via {ratio_tag}")
        
        # Check for split-range
        elif self._detect_split_range(loop_num):
            strategy = ControlStrategy.SPLIT_RANGE
            confidence = 0.75
            reasons.append("Multiple final elements for single controller")
        
        # Check for monitoring only
        elif not result.controllers and not result.final_elements:
            strategy = ControlStrategy.MONITORING
            confidence = 0.9
            reasons.append("No controllers or final elements - monitoring only")
        
        # Default to regulatory
        elif result.controllers or result.final_elements:
            strategy = ControlStrategy.REGULATORY
            confidence = 0.7
            reasons.append("Standard feedback control loop")
        
        result.strategy = strategy
        result.confidence = confidence
        result.reasons = reasons
        result.priority = self._determine_priority(loop_nodes, strategy)
        
        return result
    
    def classify_all_loops(self) -> list[ClassifiedLoop]:
        """
        Classify all control loops in the graph.
        
        Returns:
            List of ClassifiedLoop objects
        """
        loops = self._group_by_loop_number()
        results = []
        
        for loop_num in sorted(loops.keys()):
            classified = self.classify_loop(loop_num)
            results.append(classified)
        
        logger.info(f"Classified {len(results)} control loops")
        return results
    
    def get_loops_by_strategy(self, strategy: ControlStrategy) -> list[ClassifiedLoop]:
        """Get all loops of a specific strategy type."""
        all_loops = self.classify_all_loops()
        return [l for l in all_loops if l.strategy == strategy]
    
    def get_loops_by_priority(self, priority: LoopPriority) -> list[ClassifiedLoop]:
        """Get all loops of a specific priority."""
        all_loops = self.classify_all_loops()
        return [l for l in all_loops if l.priority == priority]
    
    def summary(self) -> str:
        """Generate classification summary."""
        all_loops = self.classify_all_loops()
        
        # Count by strategy
        strategy_counts = {}
        for strategy in ControlStrategy:
            count = len([l for l in all_loops if l.strategy == strategy])
            if count > 0:
                strategy_counts[strategy.value] = count
        
        # Count by priority
        priority_counts = {}
        for priority in LoopPriority:
            count = len([l for l in all_loops if l.priority == priority])
            if count > 0:
                priority_counts[priority.value] = count
        
        lines = [
            "Control Strategy Classification",
            "=" * 40,
            f"Total Loops: {len(all_loops)}",
            "",
            "By Strategy:",
        ]
        
        for strategy, count in sorted(strategy_counts.items()):
            lines.append(f"  {strategy}: {count}")
        
        lines.append("")
        lines.append("By Priority:")
        
        for priority, count in sorted(priority_counts.items()):
            lines.append(f"  {priority}: {count}")
        
        # Completeness
        complete = len([l for l in all_loops if l.is_complete])
        lines.append("")
        lines.append(f"Complete Loops: {complete}/{len(all_loops)}")
        
        return "\n".join(lines)


def classify_control_strategies(graph: PIDGraph) -> list[ClassifiedLoop]:
    """Convenience function to classify all loops."""
    classifier = ControlStrategyClassifier(graph)
    return classifier.classify_all_loops()
