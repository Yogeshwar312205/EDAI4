"""
Tests for Layer 4 - Semantic Interpretation
============================================
Tests ISA validation, control classification, enrichment, and consistency.
"""

import pytest
from src.topology.graph_builder import (
    PIDGraph, GraphNode, GraphEdge, NodeType, EdgeType
)
from src.cognitive.isa_validator import (
    ISAS51Validator, ValidationSeverity, TagValidationResult,
    validate_instrument_tags, ISA_FIRST_LETTERS
)
from src.cognitive.control_classifier import (
    ControlStrategyClassifier, ControlStrategy, LoopPriority,
    ClassifiedLoop, classify_control_strategies
)
from src.cognitive.semantic_enricher import (
    SemanticEnricher, EnrichedNode, enrich_pid_graph,
    PROCESS_VARIABLE_INFO, INSTRUMENT_DESCRIPTIONS
)
from src.cognitive.consistency_checker import (
    ConsistencyChecker, ConsistencyReport, IssueSeverity, IssueCategory,
    check_pid_consistency
)


# =============================================================================
# ISA S5.1 Validator Tests
# =============================================================================

class TestISAS51Validator:
    """Tests for ISA S5.1 validation."""
    
    def test_valid_transmitter_tags(self):
        """Test valid transmitter tags."""
        validator = ISAS51Validator()
        
        valid_tags = ["FT-101", "LT-200", "PT-300", "TT-400", "AT-500"]
        for tag in valid_tags:
            result = validator.validate_tag(tag)
            assert result.is_valid, f"{tag} should be valid"
            assert result.parsed_first_letter is not None
    
    def test_valid_controller_tags(self):
        """Test valid controller tags."""
        validator = ISAS51Validator()
        
        valid_tags = ["FIC-101", "LIC-200", "PIC-300", "TIC-400"]
        for tag in valid_tags:
            result = validator.validate_tag(tag)
            assert result.is_valid, f"{tag} should be valid"
            assert "C" in result.parsed_succeeding_letters
    
    def test_valid_safety_tags(self):
        """Test valid safety instrument tags."""
        validator = ISAS51Validator()
        
        valid_tags = ["PSH-101", "PSL-102", "PSHH-103", "TSH-201", "LSL-301"]
        for tag in valid_tags:
            result = validator.validate_tag(tag)
            assert result.is_valid, f"{tag} should be valid"
    
    def test_invalid_first_letter(self):
        """Test invalid first letter detection."""
        validator = ISAS51Validator()
        
        # X is valid but uncommon, numbers are invalid
        result = validator.validate_tag("1T-101")
        assert not result.is_valid
    
    def test_empty_tag(self):
        """Test empty tag handling."""
        validator = ISAS51Validator()
        
        result = validator.validate_tag("")
        assert not result.is_valid
        assert result.compliance_score == 0.0
    
    def test_tag_parsing(self):
        """Test tag component parsing."""
        validator = ISAS51Validator()
        
        result = validator.validate_tag("100-FIT-201A")
        assert result.parsed_first_letter == "F"
        assert result.parsed_succeeding_letters == "IT"
        assert result.parsed_loop_number == "201"
        assert result.parsed_suffix == "A"
    
    def test_common_combinations(self):
        """Test that common combinations are recognized."""
        validator = ISAS51Validator()
        
        common = ["FT", "LT", "PT", "TT", "FIC", "LIC", "PSV", "SDV"]
        for combo in common:
            result = validator.validate_tag(f"{combo}-101")
            # Should not have UNCOMMON_COMBINATION info
            uncommon_issues = [i for i in result.issues 
                             if i.code == "UNCOMMON_COMBINATION"]
            assert len(uncommon_issues) == 0, f"{combo} should be common"
    
    def test_batch_validation(self):
        """Test validating multiple tags."""
        tags = ["FT-101", "LT-102", "INVALID", "PT-103"]
        result = validate_instrument_tags(tags)
        
        assert result["total_tags"] == 4
        assert result["valid_tags"] == 3
        assert result["invalid_tags"] == 1
    
    def test_letter_description(self):
        """Test getting letter descriptions."""
        validator = ISAS51Validator()
        
        desc = validator.get_letter_description("FIC-101")
        assert desc["measured_variable"]["name"] == "Flow Rate"
        assert len(desc["functions"]) >= 2


# =============================================================================
# Control Strategy Classifier Tests
# =============================================================================

def create_test_control_graph():
    """Create a test graph with various control loops."""
    graph = PIDGraph()
    
    # Regulatory loop 101
    graph.add_node(GraphNode(id="ft101", node_type=NodeType.INSTRUMENT, 
                             label="Flow", tag="FT-101"))
    graph.add_node(GraphNode(id="fic101", node_type=NodeType.INSTRUMENT,
                             label="Controller", tag="FIC-101"))
    graph.add_node(GraphNode(id="fcv101", node_type=NodeType.VALVE,
                             label="Valve", tag="FCV-101"))
    
    # Safety instruments loop 102
    graph.add_node(GraphNode(id="psh102", node_type=NodeType.INSTRUMENT,
                             label="High Switch", tag="PSH-102"))
    graph.add_node(GraphNode(id="psl102", node_type=NodeType.INSTRUMENT,
                             label="Low Switch", tag="PSL-102"))
    
    # Monitoring only loop 103
    graph.add_node(GraphNode(id="ti103", node_type=NodeType.INSTRUMENT,
                             label="Indicator", tag="TI-103"))
    
    # Add edges
    graph.add_edge(GraphEdge(source_id="fic101", target_id="fcv101",
                             edge_type=EdgeType.CONTROLS))
    
    return graph


class TestControlStrategyClassifier:
    """Tests for control strategy classification."""
    
    def test_initialization(self):
        """Test classifier initialization."""
        graph = create_test_control_graph()
        classifier = ControlStrategyClassifier(graph)
        assert classifier.graph == graph
    
    def test_regulatory_loop_detection(self):
        """Test regulatory loop identification."""
        graph = create_test_control_graph()
        classifier = ControlStrategyClassifier(graph)
        
        result = classifier.classify_loop("101")
        assert result.strategy == ControlStrategy.REGULATORY
        assert "FT-101" in result.transmitters
        assert "FIC-101" in result.controllers
    
    def test_safety_loop_detection(self):
        """Test safety loop identification."""
        graph = create_test_control_graph()
        classifier = ControlStrategyClassifier(graph)
        
        result = classifier.classify_loop("102")
        assert result.strategy == ControlStrategy.SAFETY
        assert result.priority == LoopPriority.SAFETY_CRITICAL
    
    def test_monitoring_loop_detection(self):
        """Test monitoring-only loop identification."""
        graph = create_test_control_graph()
        classifier = ControlStrategyClassifier(graph)
        
        result = classifier.classify_loop("103")
        assert result.strategy == ControlStrategy.MONITORING
        assert result.priority == LoopPriority.LOW
    
    def test_classify_all(self):
        """Test classifying all loops."""
        graph = create_test_control_graph()
        classifier = ControlStrategyClassifier(graph)
        
        results = classifier.classify_all_loops()
        assert len(results) >= 3
    
    def test_get_loops_by_strategy(self):
        """Test filtering by strategy."""
        graph = create_test_control_graph()
        classifier = ControlStrategyClassifier(graph)
        
        safety_loops = classifier.get_loops_by_strategy(ControlStrategy.SAFETY)
        assert len(safety_loops) >= 1
    
    def test_summary(self):
        """Test summary generation."""
        graph = create_test_control_graph()
        classifier = ControlStrategyClassifier(graph)
        
        summary = classifier.summary()
        assert "Control Strategy Classification" in summary
        assert "Total Loops" in summary


# =============================================================================
# Semantic Enricher Tests
# =============================================================================

class TestSemanticEnricher:
    """Tests for semantic enrichment."""
    
    def test_initialization(self):
        """Test enricher initialization."""
        graph = create_test_control_graph()
        enricher = SemanticEnricher(graph)
        assert enricher.graph == graph
    
    def test_enrich_flow_transmitter(self):
        """Test enriching a flow transmitter."""
        graph = create_test_control_graph()
        enricher = SemanticEnricher(graph)
        
        enriched = enricher.enrich_by_tag("FT-101")
        assert enriched is not None
        assert enriched.process_variable == "Flow"
        assert "GPM" in enriched.typical_units or "m³/h" in enriched.typical_units
    
    def test_enrich_all(self):
        """Test enriching all nodes."""
        graph = create_test_control_graph()
        enricher = SemanticEnricher(graph)
        
        results = enricher.enrich_all()
        assert len(results) >= 4  # At least the instruments
    
    def test_process_variable_summary(self):
        """Test process variable summary."""
        graph = create_test_control_graph()
        enricher = SemanticEnricher(graph)
        
        summary = enricher.get_process_variable_summary()
        assert "F" in summary  # Flow
        assert "P" in summary  # Pressure
    
    def test_engineering_report(self):
        """Test engineering report generation."""
        graph = create_test_control_graph()
        enricher = SemanticEnricher(graph)
        
        report = enricher.to_engineering_report()
        assert "P&ID Semantic Analysis Report" in report
        assert "Process Variables" in report


class TestProcessVariableInfo:
    """Tests for process variable information."""
    
    def test_all_common_variables_defined(self):
        """Test that common variables have info."""
        common = ["F", "L", "P", "T", "A"]
        for var in common:
            assert var in PROCESS_VARIABLE_INFO
            assert "name" in PROCESS_VARIABLE_INFO[var]
            assert "units" in PROCESS_VARIABLE_INFO[var]
    
    def test_instrument_descriptions(self):
        """Test instrument descriptions exist."""
        common_funcs = ["FT", "LT", "PT", "TT", "FIC", "LIC", "PSV"]
        for func in common_funcs:
            assert func in INSTRUMENT_DESCRIPTIONS


# =============================================================================
# Consistency Checker Tests
# =============================================================================

def create_inconsistent_graph():
    """Create a graph with various inconsistencies."""
    graph = PIDGraph()
    
    # Duplicate tags
    graph.add_node(GraphNode(id="dup1", node_type=NodeType.INSTRUMENT,
                             label="Dup1", tag="FT-101"))
    graph.add_node(GraphNode(id="dup2", node_type=NodeType.INSTRUMENT,
                             label="Dup2", tag="FT-101"))  # Duplicate!
    
    # Orphan instrument
    graph.add_node(GraphNode(id="orphan", node_type=NodeType.INSTRUMENT,
                             label="Orphan", tag="LT-200"))
    
    # Equipment with no instruments
    graph.add_node(GraphNode(id="tank", node_type=NodeType.EQUIPMENT,
                             label="Tank", tag="TK-100"))
    
    # Control valve with no controller
    graph.add_node(GraphNode(id="valve", node_type=NodeType.VALVE,
                             label="Valve", tag="FCV-300"))
    
    return graph


class TestConsistencyChecker:
    """Tests for consistency checking."""
    
    def test_initialization(self):
        """Test checker initialization."""
        graph = create_inconsistent_graph()
        checker = ConsistencyChecker(graph)
        assert checker.graph == graph
    
    def test_duplicate_tag_detection(self):
        """Test duplicate tag detection."""
        graph = create_inconsistent_graph()
        checker = ConsistencyChecker(graph)
        
        issues = checker.check_duplicate_tags()
        assert len(issues) >= 1
        assert issues[0].severity == IssueSeverity.CRITICAL
        assert "FT-101" in issues[0].affected_tags
    
    def test_orphan_instrument_detection(self):
        """Test orphan instrument detection."""
        graph = create_inconsistent_graph()
        checker = ConsistencyChecker(graph)
        
        issues = checker.check_orphan_instruments()
        # All instruments are orphans in this graph
        assert len(issues) >= 1
    
    def test_orphan_equipment_detection(self):
        """Test orphan equipment detection."""
        graph = create_inconsistent_graph()
        checker = ConsistencyChecker(graph)
        
        issues = checker.check_orphan_equipment()
        assert len(issues) >= 1
    
    def test_run_all_checks(self):
        """Test running all checks."""
        graph = create_inconsistent_graph()
        checker = ConsistencyChecker(graph)
        
        report = checker.run_all_checks()
        
        assert isinstance(report, ConsistencyReport)
        assert report.total_issues > 0
        assert report.has_critical_issues  # Duplicate tags
    
    def test_summary(self):
        """Test summary generation."""
        graph = create_inconsistent_graph()
        checker = ConsistencyChecker(graph)
        
        summary = checker.summary()
        assert "Consistency Check Report" in summary
        assert "CRITICAL" in summary


class TestConsistencyReport:
    """Tests for ConsistencyReport."""
    
    def test_report_to_dict(self):
        """Test report serialization."""
        report = ConsistencyReport(
            total_issues=5,
            critical_count=1,
            warning_count=3,
            info_count=1,
            issues=[],
            checks_performed=["Test Check"],
        )
        
        d = report.to_dict()
        assert d["summary"]["total"] == 5
        assert d["has_critical"] == True
    
    def test_has_critical_property(self):
        """Test has_critical_issues property."""
        report_with = ConsistencyReport(
            total_issues=1, critical_count=1, warning_count=0, info_count=0,
            issues=[], checks_performed=[],
        )
        assert report_with.has_critical_issues
        
        report_without = ConsistencyReport(
            total_issues=1, critical_count=0, warning_count=1, info_count=0,
            issues=[], checks_performed=[],
        )
        assert not report_without.has_critical_issues


# =============================================================================
# Integration Tests
# =============================================================================

class TestLayer4Integration:
    """Integration tests for Layer 4 components."""
    
    def test_full_analysis_pipeline(self):
        """Test running full semantic analysis."""
        graph = create_test_control_graph()
        
        # Validate tags
        tags = [n.tag for n in graph.nodes.values() if n.tag]
        validation = validate_instrument_tags(tags)
        assert validation["total_tags"] > 0
        
        # Classify loops
        loops = classify_control_strategies(graph)
        assert len(loops) > 0
        
        # Enrich nodes
        enriched = enrich_pid_graph(graph)
        assert len(enriched) > 0
        
        # Check consistency
        report = check_pid_consistency(graph)
        assert isinstance(report, ConsistencyReport)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
