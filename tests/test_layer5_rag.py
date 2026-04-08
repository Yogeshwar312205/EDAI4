"""
Tests for Layer 5 - RAG Intelligence
=====================================
Tests knowledge base, query engine, and RAG pipeline.
"""

import pytest
from src.topology.graph_builder import (
    PIDGraph, GraphNode, GraphEdge, NodeType, EdgeType
)
from src.cognitive.knowledge_base import (
    EngineeringKnowledgeBase, KnowledgeEntry, KnowledgeCategory,
    get_knowledge_base
)
from src.cognitive.query_engine import (
    QueryEngine, QueryIntent, ParsedQuery, QueryResult, ExtractedEntities
)
from src.cognitive.rag_pipeline import RAGPipeline, RAGResponse


def create_test_pid_graph():
    """Create a test P&ID graph."""
    graph = PIDGraph()
    
    # Equipment
    graph.add_node(GraphNode(
        id="tank1", node_type=NodeType.EQUIPMENT, label="Feed Tank",
        tag="TK-100", x=100, y=200
    ))
    graph.add_node(GraphNode(
        id="pump1", node_type=NodeType.PUMP, label="Feed Pump",
        tag="P-101", x=250, y=200
    ))
    
    # Instruments
    graph.add_node(GraphNode(
        id="ft101", node_type=NodeType.INSTRUMENT, label="Flow",
        tag="FT-101", x=200, y=150
    ))
    graph.add_node(GraphNode(
        id="fic101", node_type=NodeType.INSTRUMENT, label="Flow Controller",
        tag="FIC-101", x=200, y=100
    ))
    graph.add_node(GraphNode(
        id="lt100", node_type=NodeType.INSTRUMENT, label="Level",
        tag="LT-100", x=100, y=150
    ))
    graph.add_node(GraphNode(
        id="psh102", node_type=NodeType.INSTRUMENT, label="Pressure High",
        tag="PSH-102", x=300, y=150
    ))
    
    # Valves
    graph.add_node(GraphNode(
        id="fcv101", node_type=NodeType.VALVE, label="Flow Valve",
        tag="FCV-101", x=250, y=200
    ))
    
    # Edges
    graph.add_edge(GraphEdge(source_id="lt100", target_id="tank1", edge_type=EdgeType.MEASURES))
    graph.add_edge(GraphEdge(source_id="ft101", target_id="pump1", edge_type=EdgeType.MEASURES))
    graph.add_edge(GraphEdge(source_id="fic101", target_id="fcv101", edge_type=EdgeType.CONTROLS))
    
    return graph


# =============================================================================
# Knowledge Base Tests
# =============================================================================

class TestKnowledgeBase:
    """Tests for EngineeringKnowledgeBase."""
    
    def test_initialization(self):
        """Test knowledge base loads entries."""
        kb = EngineeringKnowledgeBase()
        assert len(kb.entries) > 0
    
    def test_singleton(self):
        """Test get_knowledge_base returns same instance."""
        kb1 = get_knowledge_base()
        kb2 = get_knowledge_base()
        assert kb1 is kb2
    
    def test_search_isa(self):
        """Test searching for ISA content."""
        kb = EngineeringKnowledgeBase()
        results = kb.search("first letter flow level pressure")
        
        assert len(results) > 0
        # Should find ISA first letters entry
        assert any("ISA" in r[0].title for r in results)
    
    def test_search_sil(self):
        """Test searching for safety content."""
        kb = EngineeringKnowledgeBase()
        results = kb.search("SIL safety integrity level")
        
        assert len(results) > 0
        assert any("SIL" in r[0].title or "Safety" in r[0].title for r in results)
    
    def test_search_control_loop(self):
        """Test searching for control content."""
        kb = EngineeringKnowledgeBase()
        results = kb.search("cascade control ratio feedforward")
        
        assert len(results) > 0
    
    def test_get_by_id(self):
        """Test retrieving by ID."""
        kb = EngineeringKnowledgeBase()
        entry = kb.get_by_id("isa-first-letters")
        
        assert entry is not None
        assert entry.category == KnowledgeCategory.ISA_S51
    
    def test_get_by_category(self):
        """Test filtering by category."""
        kb = EngineeringKnowledgeBase()
        isa_entries = kb.get_by_category(KnowledgeCategory.ISA_S51)
        
        assert len(isa_entries) >= 2
        assert all(e.category == KnowledgeCategory.ISA_S51 for e in isa_entries)
    
    def test_build_context(self):
        """Test context building for LLM."""
        kb = EngineeringKnowledgeBase()
        context = kb.build_context("what is SIL level?")
        
        assert len(context) > 0
        assert "Safety" in context or "SIL" in context
    
    def test_summary(self):
        """Test summary generation."""
        kb = EngineeringKnowledgeBase()
        summary = kb.summary()
        
        assert "Knowledge Base" in summary
        assert "Total Entries" in summary


class TestKnowledgeEntry:
    """Tests for KnowledgeEntry."""
    
    def test_entry_creation(self):
        """Test creating an entry."""
        entry = KnowledgeEntry(
            id="test-1",
            category=KnowledgeCategory.GENERAL,
            title="Test Entry",
            content="This is test content.",
            keywords=["test", "sample"],
        )
        
        assert entry.id == "test-1"
        assert entry.category == KnowledgeCategory.GENERAL
    
    def test_matches_query(self):
        """Test query matching."""
        entry = KnowledgeEntry(
            id="test-1",
            category=KnowledgeCategory.GENERAL,
            title="Flow Measurement",
            content="Flow meters measure fluid flow rate.",
            keywords=["flow", "measurement", "meter"],
        )
        
        # Should match well
        score1 = entry.matches_query("flow measurement")
        assert score1 > 0.3
        
        # Should not match
        score2 = entry.matches_query("pressure temperature")
        assert score2 < score1


# =============================================================================
# Query Engine Tests
# =============================================================================

class TestQueryEngine:
    """Tests for QueryEngine."""
    
    def test_initialization_without_graph(self):
        """Test engine works without graph."""
        engine = QueryEngine()
        assert engine.graph is None
    
    def test_initialization_with_graph(self):
        """Test engine with graph."""
        graph = create_test_pid_graph()
        engine = QueryEngine(graph)
        assert engine.graph is graph
    
    def test_parse_tag_query(self):
        """Test parsing tag lookup query."""
        engine = QueryEngine()
        parsed = engine.parse_query("What is FT-101?")
        
        assert "FT-101" in parsed.entities.tags
        assert parsed.intent == QueryIntent.TAG_LOOKUP
    
    def test_parse_list_query(self):
        """Test parsing list query."""
        engine = QueryEngine()
        parsed = engine.parse_query("List all flow transmitters")
        
        assert parsed.intent == QueryIntent.TAG_LIST
        assert "F" in parsed.entities.variable_types
    
    def test_parse_loop_query(self):
        """Test parsing loop analysis query."""
        engine = QueryEngine()
        parsed = engine.parse_query("Describe control loop 101")
        
        assert "101" in parsed.entities.loop_numbers
        assert parsed.intent == QueryIntent.LOOP_ANALYSIS
    
    def test_parse_count_query(self):
        """Test parsing count query."""
        engine = QueryEngine()
        parsed = engine.parse_query("How many temperature instruments?")
        
        assert parsed.intent == QueryIntent.COUNT
        assert "T" in parsed.entities.variable_types
    
    def test_execute_tag_lookup(self):
        """Test executing tag lookup."""
        graph = create_test_pid_graph()
        engine = QueryEngine(graph)
        
        result = engine.execute_query("What is FT-101?")
        
        assert "FT-101" in result.answer
        assert "Flow" in result.answer
    
    def test_execute_tag_list(self):
        """Test executing tag list."""
        graph = create_test_pid_graph()
        engine = QueryEngine(graph)
        
        result = engine.execute_query("List all flow instruments")
        
        assert result.data.get("tags")
        assert any("F" in tag for tag in result.data["tags"])
    
    def test_execute_loop_analysis(self):
        """Test executing loop analysis."""
        graph = create_test_pid_graph()
        engine = QueryEngine(graph)
        
        result = engine.execute_query("Describe loop 101")
        
        assert "101" in result.answer
    
    def test_execute_knowledge_query(self):
        """Test executing knowledge query."""
        engine = QueryEngine()
        
        result = engine.execute_query("What does SIL mean?")
        
        assert "Safety" in result.answer or "SIL" in result.answer
        assert result.confidence > 0.5


class TestExtractedEntities:
    """Tests for entity extraction."""
    
    def test_tag_extraction(self):
        """Test tag extraction patterns."""
        engine = QueryEngine()
        
        parsed = engine.parse_query("Compare FT-101 and FIC-102")
        
        assert "FT-101" in parsed.entities.tags
        assert "FIC-102" in parsed.entities.tags
    
    def test_loop_extraction(self):
        """Test loop number extraction."""
        engine = QueryEngine()
        
        parsed = engine.parse_query("Loop 200 and loop 300")
        
        assert "200" in parsed.entities.loop_numbers
        assert "300" in parsed.entities.loop_numbers


# =============================================================================
# RAG Pipeline Tests
# =============================================================================

class TestRAGPipeline:
    """Tests for RAGPipeline."""
    
    def test_initialization(self):
        """Test pipeline initialization."""
        pipeline = RAGPipeline(use_llm=False)
        
        assert pipeline.graph is None
        assert not pipeline._llm_initialized
    
    def test_set_graph(self):
        """Test setting graph."""
        pipeline = RAGPipeline(use_llm=False)
        graph = create_test_pid_graph()
        
        pipeline.set_graph(graph)
        
        assert pipeline.graph is graph
        assert pipeline.query_engine.graph is graph
    
    def test_query_without_llm(self):
        """Test querying in local mode."""
        graph = create_test_pid_graph()
        pipeline = RAGPipeline(graph=graph, use_llm=False)
        
        response = pipeline.query("What is FT-101?")
        
        assert isinstance(response, RAGResponse)
        assert "Flow" in response.answer
        assert response.confidence > 0
    
    def test_ask_simple(self):
        """Test simple ask interface."""
        graph = create_test_pid_graph()
        pipeline = RAGPipeline(graph=graph, use_llm=False)
        
        answer = pipeline.ask("What is FT-101?")
        
        assert isinstance(answer, str)
        assert len(answer) > 0
    
    def test_generate_instrument_description(self):
        """Test instrument description generation."""
        graph = create_test_pid_graph()
        pipeline = RAGPipeline(graph=graph, use_llm=False)
        
        desc = pipeline.generate_instrument_description("FIC-101")
        
        assert isinstance(desc, str)
        assert "Flow" in desc or "Controller" in desc
    
    def test_explain_control_loop(self):
        """Test control loop explanation."""
        graph = create_test_pid_graph()
        pipeline = RAGPipeline(graph=graph, use_llm=False)
        
        explanation = pipeline.explain_control_loop("101")
        
        assert isinstance(explanation, str)
    
    def test_get_safety_overview(self):
        """Test safety overview."""
        graph = create_test_pid_graph()
        pipeline = RAGPipeline(graph=graph, use_llm=False)
        
        overview = pipeline.get_safety_overview()
        
        assert isinstance(overview, str)
        # Should find PSH-102
        assert "PSH" in overview or "Safety" in overview
    
    def test_validate_and_explain_tag(self):
        """Test tag validation and explanation."""
        pipeline = RAGPipeline(use_llm=False)
        
        result = pipeline.validate_and_explain_tag("FIC-101")
        
        assert result["tag"] == "FIC-101"
        assert "explanation" in result
        assert "confidence" in result
    
    def test_suggest_improvements(self):
        """Test improvement suggestions."""
        graph = create_test_pid_graph()
        pipeline = RAGPipeline(graph=graph, use_llm=False)
        
        suggestions = pipeline.suggest_improvements()
        
        assert isinstance(suggestions, str)
    
    def test_summary(self):
        """Test pipeline summary."""
        graph = create_test_pid_graph()
        pipeline = RAGPipeline(graph=graph, use_llm=False)
        
        summary = pipeline.summary()
        
        assert "RAG Pipeline Status" in summary
        assert "Graph loaded: Yes" in summary


class TestRAGResponse:
    """Tests for RAGResponse."""
    
    def test_response_creation(self):
        """Test creating a response."""
        response = RAGResponse(
            answer="Test answer",
            sources=["Source 1"],
            confidence=0.9,
            reasoning_steps=["Step 1"],
            intent="tag_lookup",
        )
        
        assert response.answer == "Test answer"
        assert response.confidence == 0.9
    
    def test_response_to_dict(self):
        """Test response serialization."""
        response = RAGResponse(
            answer="Test",
            confidence=0.8,
        )
        
        d = response.to_dict()
        
        assert d["answer"] == "Test"
        assert d["confidence"] == 0.8


# =============================================================================
# Integration Tests
# =============================================================================

class TestLayer5Integration:
    """Integration tests for Layer 5."""
    
    def test_full_query_flow(self):
        """Test complete query flow."""
        graph = create_test_pid_graph()
        pipeline = RAGPipeline(graph=graph, use_llm=False)
        
        # Ask multiple questions
        questions = [
            "What is FT-101?",
            "List all flow instruments",
            "What does SIL mean?",
            "How many temperature instruments?",
        ]
        
        for q in questions:
            response = pipeline.query(q)
            assert response.answer
            assert response.confidence > 0
    
    def test_knowledge_retrieval_chain(self):
        """Test knowledge base → query engine → response."""
        kb = get_knowledge_base()
        engine = QueryEngine()
        
        # Search knowledge
        results = kb.search("ISA first letter")
        assert results
        
        # Parse query
        parsed = engine.parse_query("What is the first letter F?")
        assert parsed.intent in (QueryIntent.TAG_LOOKUP, QueryIntent.KNOWLEDGE)
        
        # Execute
        result = engine.execute_query("What is the first letter F?")
        assert result.answer


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
