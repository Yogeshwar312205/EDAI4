"""
EDAI4 - Cognitive Layer
Graph-RAG pipeline and semantic analysis for intelligent P&ID reasoning
"""

from src.cognitive.rag_pipeline import RAGPipeline, RAGResponse
from src.cognitive.isa_validator import (
    ISAS51Validator,
    ValidationSeverity,
    ValidationIssue,
    TagValidationResult,
    validate_instrument_tags,
    ISA_FIRST_LETTERS,
    ISA_SUCCEEDING_LETTERS,
)
from src.cognitive.control_classifier import (
    ControlStrategyClassifier,
    ControlStrategy,
    LoopPriority,
    ClassifiedLoop,
    classify_control_strategies,
)
from src.cognitive.semantic_enricher import (
    SemanticEnricher,
    EnrichedNode,
    enrich_pid_graph,
    PROCESS_VARIABLE_INFO,
    INSTRUMENT_DESCRIPTIONS,
)
from src.cognitive.consistency_checker import (
    ConsistencyChecker,
    ConsistencyIssue,
    ConsistencyReport,
    IssueSeverity,
    IssueCategory,
    check_pid_consistency,
)
from src.cognitive.knowledge_base import (
    EngineeringKnowledgeBase,
    KnowledgeEntry,
    KnowledgeCategory,
    get_knowledge_base,
)
from src.cognitive.query_engine import (
    QueryEngine,
    QueryIntent,
    ParsedQuery,
    QueryResult,
    ExtractedEntities,
)
from src.cognitive.vector_store import (
    VectorStore,
    EmbeddedDocument,
    SemanticKnowledgeBase,
    create_semantic_kb,
)

__all__ = [
    # RAG Pipeline
    "RAGPipeline",
    "RAGResponse",
    
    # ISA S5.1 Validator
    "ISAS51Validator",
    "ValidationSeverity",
    "ValidationIssue",
    "TagValidationResult",
    "validate_instrument_tags",
    "ISA_FIRST_LETTERS",
    "ISA_SUCCEEDING_LETTERS",
    
    # Control Strategy Classifier
    "ControlStrategyClassifier",
    "ControlStrategy",
    "LoopPriority",
    "ClassifiedLoop",
    "classify_control_strategies",
    
    # Semantic Enricher
    "SemanticEnricher",
    "EnrichedNode",
    "enrich_pid_graph",
    "PROCESS_VARIABLE_INFO",
    "INSTRUMENT_DESCRIPTIONS",
    
    # Consistency Checker
    "ConsistencyChecker",
    "ConsistencyIssue",
    "ConsistencyReport",
    "IssueSeverity",
    "IssueCategory",
    "check_pid_consistency",
    
    # Knowledge Base
    "EngineeringKnowledgeBase",
    "KnowledgeEntry",
    "KnowledgeCategory",
    "get_knowledge_base",
    
    # Query Engine
    "QueryEngine",
    "QueryIntent",
    "ParsedQuery",
    "QueryResult",
    "ExtractedEntities",
    
    # Vector Store
    "VectorStore",
    "EmbeddedDocument",
    "SemanticKnowledgeBase",
    "create_semantic_kb",
]
