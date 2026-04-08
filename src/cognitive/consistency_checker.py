"""
EDAI4 - Consistency Checker
============================
Detects inconsistencies and potential issues in P&ID data.

Checks:
- Orphan instruments (no equipment association)
- Duplicate loop numbers
- Missing loop elements
- Tag format violations
- Unreferenced equipment
- Control loop completeness
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from collections import defaultdict

from src.topology.graph_builder import PIDGraph, GraphNode, NodeType, EdgeType
from src.cognitive.isa_validator import ISAS51Validator, ValidationSeverity
from src.utils import get_logger

logger = get_logger(__name__)


class IssueSeverity(Enum):
    """Severity of detected issues."""
    CRITICAL = "critical"  # Must be fixed
    WARNING = "warning"    # Should be reviewed
    INFO = "info"          # For awareness


class IssueCategory(Enum):
    """Categories of issues."""
    ORPHAN = "orphan"                    # Unconnected elements
    DUPLICATE = "duplicate"              # Duplicate identifiers
    MISSING = "missing"                  # Missing required elements
    FORMAT = "format"                    # Format/naming violations
    INCONSISTENT = "inconsistent"        # Logical inconsistencies
    INCOMPLETE = "incomplete"            # Incomplete information


@dataclass
class ConsistencyIssue:
    """A detected consistency issue."""
    issue_id: str
    severity: IssueSeverity
    category: IssueCategory
    message: str
    affected_tags: list[str] = field(default_factory=list)
    affected_nodes: list[str] = field(default_factory=list)
    suggestion: Optional[str] = None
    details: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.issue_id,
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "affected_tags": self.affected_tags,
            "affected_nodes": self.affected_nodes,
            "suggestion": self.suggestion,
            "details": self.details,
        }


@dataclass
class ConsistencyReport:
    """Complete consistency check report."""
    total_issues: int
    critical_count: int
    warning_count: int
    info_count: int
    issues: list[ConsistencyIssue]
    checks_performed: list[str]
    
    @property
    def has_critical_issues(self) -> bool:
        return self.critical_count > 0
    
    def to_dict(self) -> dict:
        return {
            "summary": {
                "total": self.total_issues,
                "critical": self.critical_count,
                "warnings": self.warning_count,
                "info": self.info_count,
            },
            "has_critical": self.has_critical_issues,
            "checks": self.checks_performed,
            "issues": [i.to_dict() for i in self.issues],
        }


class ConsistencyChecker:
    """
    Checks P&ID data for consistency issues.
    
    Performs multiple validation checks and generates
    a comprehensive report of detected issues.
    """
    
    def __init__(self, graph: PIDGraph):
        """
        Initialize checker.
        
        Args:
            graph: PIDGraph to check
        """
        self.graph = graph
        self.validator = ISAS51Validator()
        self._issue_counter = 0
    
    def _generate_issue_id(self) -> str:
        """Generate unique issue ID."""
        self._issue_counter += 1
        return f"ISSUE-{self._issue_counter:04d}"
    
    def check_orphan_instruments(self) -> list[ConsistencyIssue]:
        """
        Find instruments not connected to any equipment.
        
        Returns:
            List of issues for orphan instruments
        """
        issues = []
        
        for node in self.graph.get_instruments():
            if not node.tag:
                continue
            
            # Check for connections to equipment
            has_equipment = False
            for connected, edge in self.graph.get_connected_nodes(node.id):
                if connected.node_type in (NodeType.EQUIPMENT, NodeType.PUMP):
                    has_equipment = True
                    break
            
            if not has_equipment:
                issues.append(ConsistencyIssue(
                    issue_id=self._generate_issue_id(),
                    severity=IssueSeverity.WARNING,
                    category=IssueCategory.ORPHAN,
                    message=f"Instrument {node.tag} has no associated equipment",
                    affected_tags=[node.tag],
                    affected_nodes=[node.id],
                    suggestion="Review P&ID to identify which equipment this instrument monitors",
                ))
        
        return issues
    
    def check_orphan_equipment(self) -> list[ConsistencyIssue]:
        """
        Find equipment with no connected instruments.
        
        Returns:
            List of issues for equipment without instrumentation
        """
        issues = []
        
        for node in self.graph.get_equipment():
            if not node.tag:
                continue
            
            # Check for connected instruments
            has_instruments = False
            for connected, edge in self.graph.get_connected_nodes(node.id):
                if connected.node_type == NodeType.INSTRUMENT:
                    has_instruments = True
                    break
            
            if not has_instruments:
                issues.append(ConsistencyIssue(
                    issue_id=self._generate_issue_id(),
                    severity=IssueSeverity.INFO,
                    category=IssueCategory.ORPHAN,
                    message=f"Equipment {node.tag} has no connected instruments",
                    affected_tags=[node.tag],
                    affected_nodes=[node.id],
                    suggestion="Verify if this equipment requires instrumentation",
                ))
        
        return issues
    
    def check_duplicate_tags(self) -> list[ConsistencyIssue]:
        """
        Find duplicate instrument tags.
        
        Returns:
            List of issues for duplicate tags
        """
        issues = []
        tag_nodes = defaultdict(list)
        
        for node in self.graph.nodes.values():
            if node.tag:
                tag_nodes[node.tag].append(node)
        
        for tag, nodes in tag_nodes.items():
            if len(nodes) > 1:
                issues.append(ConsistencyIssue(
                    issue_id=self._generate_issue_id(),
                    severity=IssueSeverity.CRITICAL,
                    category=IssueCategory.DUPLICATE,
                    message=f"Duplicate tag '{tag}' found {len(nodes)} times",
                    affected_tags=[tag],
                    affected_nodes=[n.id for n in nodes],
                    suggestion="Each instrument tag must be unique",
                    details={"count": len(nodes)},
                ))
        
        return issues
    
    def check_duplicate_loop_numbers(self) -> list[ConsistencyIssue]:
        """
        Check for conflicting loop numbers across different variables.
        
        E.g., FT-101 and LT-101 is usually fine (same loop),
        but FIC-101 and LIC-101 might indicate an issue.
        """
        issues = []
        loop_controllers = defaultdict(list)
        
        for node in self.graph.get_instruments():
            if not node.tag:
                continue
            
            result = self.validator.validate_tag(node.tag)
            loop_num = result.parsed_loop_number
            succeeding = result.parsed_succeeding_letters or ""
            
            # Only check controllers
            if loop_num and "C" in succeeding:
                loop_controllers[loop_num].append(node)
        
        for loop_num, controllers in loop_controllers.items():
            if len(controllers) > 1:
                # Check if they're different types (might be cascade, might be error)
                first_letters = set()
                for c in controllers:
                    result = self.validator.validate_tag(c.tag)
                    first_letters.add(result.parsed_first_letter)
                
                if len(first_letters) > 2:  # More than 2 different variables
                    issues.append(ConsistencyIssue(
                        issue_id=self._generate_issue_id(),
                        severity=IssueSeverity.WARNING,
                        category=IssueCategory.DUPLICATE,
                        message=f"Loop {loop_num} has controllers for {len(first_letters)} different variables",
                        affected_tags=[c.tag for c in controllers],
                        affected_nodes=[c.id for c in controllers],
                        suggestion="Verify this is intentional (cascade) or needs correction",
                        details={"variables": list(first_letters)},
                    ))
        
        return issues
    
    def check_tag_format(self) -> list[ConsistencyIssue]:
        """
        Validate all tags against ISA S5.1 format.
        
        Returns:
            List of format violation issues
        """
        issues = []
        
        for node in self.graph.nodes.values():
            if not node.tag:
                continue
            
            result = self.validator.validate_tag(node.tag)
            
            if not result.is_valid:
                error_issues = [i for i in result.issues 
                              if i.severity == ValidationSeverity.ERROR]
                
                if error_issues:
                    issues.append(ConsistencyIssue(
                        issue_id=self._generate_issue_id(),
                        severity=IssueSeverity.WARNING,
                        category=IssueCategory.FORMAT,
                        message=f"Tag '{node.tag}' has format violations",
                        affected_tags=[node.tag],
                        affected_nodes=[node.id],
                        suggestion=error_issues[0].suggestion if error_issues else None,
                        details={"validation_issues": [i.to_dict() for i in result.issues]},
                    ))
        
        return issues
    
    def check_incomplete_loops(self) -> list[ConsistencyIssue]:
        """
        Find control loops missing required elements.
        
        A complete regulatory loop typically needs:
        - Transmitter (xT)
        - Controller (xC/xIC)
        - Final element (xV/xCV)
        """
        issues = []
        
        # Group by loop number
        loops = defaultdict(lambda: {"T": [], "C": [], "V": []})
        
        for node in self.graph.get_instruments():
            if not node.tag:
                continue
            
            result = self.validator.validate_tag(node.tag)
            loop_num = result.parsed_loop_number
            succeeding = result.parsed_succeeding_letters or ""
            
            if not loop_num:
                continue
            
            if "T" in succeeding and "C" not in succeeding:
                loops[loop_num]["T"].append(node.tag)
            if "C" in succeeding:
                loops[loop_num]["C"].append(node.tag)
            if "V" in succeeding:
                loops[loop_num]["V"].append(node.tag)
        
        # Also check valves
        for node in self.graph.get_valves():
            if not node.tag:
                continue
            
            result = self.validator.validate_tag(node.tag)
            loop_num = result.parsed_loop_number
            
            if loop_num:
                loops[loop_num]["V"].append(node.tag)
        
        # Check completeness
        for loop_num, elements in loops.items():
            missing = []
            
            if not elements["T"]:
                missing.append("transmitter")
            if not elements["C"]:
                missing.append("controller")
            if not elements["V"]:
                missing.append("final element")
            
            # Only report if partially complete (has some but not all)
            has_some = any(elements[k] for k in ["T", "C", "V"])
            has_all = all(elements[k] for k in ["T", "C", "V"])
            
            if has_some and not has_all and len(missing) < 3:
                all_tags = elements["T"] + elements["C"] + elements["V"]
                
                issues.append(ConsistencyIssue(
                    issue_id=self._generate_issue_id(),
                    severity=IssueSeverity.INFO,
                    category=IssueCategory.INCOMPLETE,
                    message=f"Loop {loop_num} may be missing: {', '.join(missing)}",
                    affected_tags=all_tags,
                    suggestion="Verify if this is a monitoring loop or has missing instruments",
                    details={"missing": missing, "has": elements},
                ))
        
        return issues
    
    def check_safety_instrument_isolation(self) -> list[ConsistencyIssue]:
        """
        Check that safety instruments are properly isolated.
        
        Safety instruments should have dedicated connections.
        """
        issues = []
        
        safety_patterns = ["SH", "SL", "AH", "AL", "HH", "LL", "SDV", "BDV", "XV"]
        
        for node in self.graph.nodes.values():
            if not node.tag:
                continue
            
            tag_upper = node.tag.upper()
            is_safety = any(p in tag_upper for p in safety_patterns)
            
            if not is_safety:
                continue
            
            # Check if safety instrument is connected to non-safety elements
            # (This is a simplified check - real SIS verification is complex)
            connections = self.graph.get_connected_nodes(node.id)
            
            for connected, edge in connections:
                if connected.tag:
                    conn_upper = connected.tag.upper()
                    conn_is_safety = any(p in conn_upper for p in safety_patterns)
                    
                    # Control connections to non-safety elements might be an issue
                    if not conn_is_safety and edge.edge_type == EdgeType.CONTROLS:
                        issues.append(ConsistencyIssue(
                            issue_id=self._generate_issue_id(),
                            severity=IssueSeverity.INFO,
                            category=IssueCategory.INCONSISTENT,
                            message=f"Safety instrument {node.tag} connected to non-safety element {connected.tag}",
                            affected_tags=[node.tag, connected.tag],
                            affected_nodes=[node.id, connected.id],
                            suggestion="Verify safety system segregation requirements",
                        ))
        
        return issues
    
    def check_unconnected_valves(self) -> list[ConsistencyIssue]:
        """
        Find control valves with no controller connection.
        """
        issues = []
        
        for node in self.graph.get_valves():
            if not node.tag:
                continue
            
            # Only check control valves (CV in tag)
            if "CV" not in node.tag.upper():
                continue
            
            has_controller = False
            for connected, edge in self.graph.get_connected_nodes(node.id):
                if edge.edge_type == EdgeType.CONTROLS:
                    has_controller = True
                    break
                # Also check if connected to an instrument
                if connected.node_type == NodeType.INSTRUMENT:
                    result = self.validator.validate_tag(connected.tag or "")
                    if "C" in (result.parsed_succeeding_letters or ""):
                        has_controller = True
                        break
            
            if not has_controller:
                issues.append(ConsistencyIssue(
                    issue_id=self._generate_issue_id(),
                    severity=IssueSeverity.WARNING,
                    category=IssueCategory.ORPHAN,
                    message=f"Control valve {node.tag} has no connected controller",
                    affected_tags=[node.tag],
                    affected_nodes=[node.id],
                    suggestion="Verify controller-valve relationship",
                ))
        
        return issues
    
    def run_all_checks(self) -> ConsistencyReport:
        """
        Run all consistency checks.
        
        Returns:
            ConsistencyReport with all detected issues
        """
        self._issue_counter = 0
        all_issues = []
        checks = []
        
        # Run each check
        check_methods = [
            ("Orphan Instruments", self.check_orphan_instruments),
            ("Orphan Equipment", self.check_orphan_equipment),
            ("Duplicate Tags", self.check_duplicate_tags),
            ("Duplicate Loop Numbers", self.check_duplicate_loop_numbers),
            ("Tag Format", self.check_tag_format),
            ("Incomplete Loops", self.check_incomplete_loops),
            ("Safety Isolation", self.check_safety_instrument_isolation),
            ("Unconnected Valves", self.check_unconnected_valves),
        ]
        
        for name, method in check_methods:
            checks.append(name)
            try:
                issues = method()
                all_issues.extend(issues)
            except Exception as e:
                logger.error(f"Error in check '{name}': {e}")
        
        # Count by severity
        critical = len([i for i in all_issues if i.severity == IssueSeverity.CRITICAL])
        warning = len([i for i in all_issues if i.severity == IssueSeverity.WARNING])
        info = len([i for i in all_issues if i.severity == IssueSeverity.INFO])
        
        report = ConsistencyReport(
            total_issues=len(all_issues),
            critical_count=critical,
            warning_count=warning,
            info_count=info,
            issues=all_issues,
            checks_performed=checks,
        )
        
        logger.info(f"Consistency check complete: {len(all_issues)} issues found")
        return report
    
    def get_issues_by_category(self, category: IssueCategory) -> list[ConsistencyIssue]:
        """Get issues of a specific category."""
        report = self.run_all_checks()
        return [i for i in report.issues if i.category == category]
    
    def get_issues_by_severity(self, severity: IssueSeverity) -> list[ConsistencyIssue]:
        """Get issues of a specific severity."""
        report = self.run_all_checks()
        return [i for i in report.issues if i.severity == severity]
    
    def summary(self) -> str:
        """Generate summary of consistency check."""
        report = self.run_all_checks()
        
        lines = [
            "P&ID Consistency Check Report",
            "=" * 50,
            "",
            f"Total Issues: {report.total_issues}",
            f"  Critical: {report.critical_count}",
            f"  Warnings: {report.warning_count}",
            f"  Info: {report.info_count}",
            "",
            "Checks Performed:",
        ]
        
        for check in report.checks_performed:
            lines.append(f"  ✓ {check}")
        
        if report.has_critical_issues:
            lines.append("")
            lines.append("⚠️ CRITICAL ISSUES REQUIRE ATTENTION:")
            for issue in report.issues:
                if issue.severity == IssueSeverity.CRITICAL:
                    lines.append(f"  • {issue.message}")
        
        return "\n".join(lines)


def check_pid_consistency(graph: PIDGraph) -> ConsistencyReport:
    """Convenience function to run all checks."""
    checker = ConsistencyChecker(graph)
    return checker.run_all_checks()
