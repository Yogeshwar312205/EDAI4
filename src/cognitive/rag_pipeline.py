"""
EDAI4 - RAG Pipeline
=====================
Graph-RAG pipeline for intelligent P&ID reasoning using LLM.

Integrates:
- Knowledge base (engineering standards)
- Query engine (intent parsing, entity extraction)
- Graph data (topology, connections)
- Semantic enrichment (descriptions, context)
- LLM for natural language generation
"""

from typing import Optional, Any
from dataclasses import dataclass, field
import json

from src.topology.graph_builder import PIDGraph
from src.cognitive.knowledge_base import get_knowledge_base, EngineeringKnowledgeBase
from src.cognitive.query_engine import QueryEngine, ParsedQuery, QueryResult, QueryIntent
from src.utils import get_logger

logger = get_logger(__name__)


@dataclass
class RAGResponse:
    """Response from RAG pipeline."""
    answer: str
    sources: list[str] = field(default_factory=list)
    confidence: float = 0.0
    reasoning_steps: list[str] = field(default_factory=list)
    data: dict = field(default_factory=dict)
    intent: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "answer": self.answer,
            "sources": self.sources,
            "confidence": self.confidence,
            "reasoning_steps": self.reasoning_steps,
            "data": self.data,
            "intent": self.intent,
        }


class RAGPipeline:
    """
    Graph-RAG pipeline for P&ID reasoning.

    Combines structured data queries with LLM generation for
    intelligent, contextual answers about P&ID content.
    
    Can operate in two modes:
    1. Local mode (no LLM): Uses query engine + knowledge base
    2. LLM mode: Enhances with Gemini for natural language
    """

    def __init__(
        self,
        graph: Optional[PIDGraph] = None,
        api_key: Optional[str] = None,
        model: str = "gemini-1.5-flash",
        use_llm: bool = True,
    ):
        """
        Initialize RAG pipeline.

        Args:
            graph: Optional PIDGraph for data queries
            api_key: Google Gemini API key (optional)
            model: Model to use (gemini-1.5-flash, gemini-1.5-pro)
            use_llm: Whether to use LLM for response generation
        """
        self.graph = graph
        self.api_key = api_key
        self.model_name = model
        self.use_llm = use_llm
        
        self.llm = None
        self._llm_initialized = False
        
        # Initialize components
        self.knowledge_base = get_knowledge_base()
        self.query_engine = QueryEngine(graph)

        # Try loading API key from environment
        import os
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")

        logger.info(f"RAGPipeline initialized (model={model}, use_llm={use_llm})")

    def set_graph(self, graph: PIDGraph):
        """Set or update the P&ID graph."""
        self.graph = graph
        self.query_engine.set_graph(graph)
    
    def initialize_llm(self) -> bool:
        """
        Initialize LLM connection.

        Returns:
            True if initialized successfully
        """
        if not self.api_key:
            logger.warning("Google API key not configured - running in local mode")
            return False

        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            self.llm = genai.GenerativeModel(self.model_name)

            self._llm_initialized = True
            logger.info("LLM initialized with Gemini")
            return True

        except ImportError:
            logger.warning(
                "google-generativeai not installed. "
                "Running in local mode. Install with: pip install google-generativeai"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            return False

    def query(
        self,
        query: str,
        use_llm_enhancement: Optional[bool] = None,
    ) -> RAGResponse:
        """
        Query the RAG pipeline.

        Args:
            query: Natural language query
            use_llm_enhancement: Override default LLM usage

        Returns:
            RAGResponse with answer
        """
        # Step 1: Parse and execute structured query
        result = self.query_engine.execute_query(query)
        
        reasoning_steps = [
            f"Parsed intent: {result.query.intent.value}",
            f"Entities found: tags={result.query.entities.tags}, loops={result.query.entities.loop_numbers}",
        ]
        
        # Step 2: Decide if LLM enhancement is needed
        should_use_llm = use_llm_enhancement if use_llm_enhancement is not None else self.use_llm
        
        # Don't use LLM for simple lookups with good answers
        if result.confidence > 0.8 and result.query.intent in (
            QueryIntent.TAG_LOOKUP, QueryIntent.TAG_LIST, QueryIntent.COUNT
        ):
            should_use_llm = False
            reasoning_steps.append("High-confidence structured answer - no LLM needed")
        
        # Step 3: Optionally enhance with LLM
        if should_use_llm and self.use_llm:
            if not self._llm_initialized:
                self.initialize_llm()
            
            if self._llm_initialized:
                enhanced = self._enhance_with_llm(query, result)
                reasoning_steps.append("Enhanced with LLM")
                return RAGResponse(
                    answer=enhanced,
                    sources=result.sources + ["LLM (Gemini)"],
                    confidence=min(result.confidence + 0.1, 1.0),
                    reasoning_steps=reasoning_steps,
                    data=result.data,
                    intent=result.query.intent.value,
                )
        
        # Return structured answer
        return RAGResponse(
            answer=result.answer,
            sources=result.sources,
            confidence=result.confidence,
            reasoning_steps=reasoning_steps,
            data=result.data,
            intent=result.query.intent.value,
        )

    def _enhance_with_llm(self, query: str, result: QueryResult) -> str:
        """Enhance structured answer with LLM."""
        try:
            # Build context for LLM
            context_parts = []
            
            # Add structured data
            if result.data:
                context_parts.append(f"Data from P&ID:\n{json.dumps(result.data, indent=2)}")
            
            # Add knowledge base context
            kb_context = self.knowledge_base.build_context(query)
            if kb_context:
                context_parts.append(f"\nEngineering Knowledge:\n{kb_context}")
            
            # Add the structured answer
            context_parts.append(f"\nStructured Answer:\n{result.answer}")
            
            prompt = self._build_enhancement_prompt(query, "\n".join(context_parts))
            
            response = self.llm.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"LLM enhancement failed: {e}")
            return result.answer  # Fall back to structured answer
    
    def _build_enhancement_prompt(self, query: str, context: str) -> str:
        """Build prompt for LLM enhancement."""
        return f"""You are an expert in P&ID (Piping and Instrumentation Diagrams) and industrial instrumentation.

Use the following context to answer the user's question. Be concise but thorough.
Reference ISA-5.1 and IEC 61511 standards where relevant.

{context}

User Question: {query}

Provide a clear, professional answer:"""

    def ask(self, question: str) -> str:
        """
        Simple interface for asking questions.
        
        Args:
            question: Natural language question
            
        Returns:
            Answer string
        """
        response = self.query(question)
        return response.answer
    
    def generate_instrument_description(self, tag: str) -> str:
        """Generate description for an instrument tag."""
        response = self.query(f"Describe instrument {tag}")
        return response.answer

    def explain_control_loop(self, loop_number: str) -> str:
        """Explain a control loop."""
        response = self.query(f"Describe control loop {loop_number}")
        return response.answer
    
    def get_safety_overview(self) -> str:
        """Get overview of safety instrumentation."""
        response = self.query("What safety instruments are in this P&ID?")
        return response.answer
    
    def validate_and_explain_tag(self, tag: str) -> dict:
        """Validate and explain a tag format."""
        response = self.query(f"What is {tag}?")
        return {
            "tag": tag,
            "explanation": response.answer,
            "confidence": response.confidence,
            "data": response.data,
        }

    def suggest_improvements(self) -> str:
        """Suggest improvements based on P&ID analysis."""
        if not self.graph:
            return "No P&ID data loaded."
        
        # Run consistency checks
        from src.cognitive.consistency_checker import ConsistencyChecker
        checker = ConsistencyChecker(self.graph)
        report = checker.run_all_checks()
        
        if report.total_issues == 0:
            return "No issues detected in the P&ID. Design appears consistent."
        
        parts = ["**Improvement Suggestions:**\n"]
        
        for issue in report.issues[:5]:  # Top 5 issues
            parts.append(f"- {issue.message}")
            if issue.suggestion:
                parts.append(f"  *Suggestion: {issue.suggestion}*")
        
        if report.total_issues > 5:
            parts.append(f"\n...and {report.total_issues - 5} more issues.")
        
        return "\n".join(parts)
    
    def interactive_session(self):
        """
        Run an interactive Q&A session (for CLI use).
        """
        print("EDAI4 P&ID Assistant")
        print("=" * 40)
        print("Ask questions about the P&ID. Type 'quit' to exit.\n")
        
        while True:
            try:
                question = input("You: ").strip()
                
                if question.lower() in ('quit', 'exit', 'q'):
                    print("Goodbye!")
                    break
                
                if not question:
                    continue
                
                response = self.query(question)
                print(f"\nAssistant: {response.answer}")
                print(f"[Confidence: {response.confidence:.0%}]\n")
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}\n")
    
    def summary(self) -> str:
        """Get summary of RAG pipeline status."""
        lines = [
            "RAG Pipeline Status",
            "=" * 40,
            f"Graph loaded: {'Yes' if self.graph else 'No'}",
            f"LLM enabled: {self.use_llm}",
            f"LLM initialized: {self._llm_initialized}",
            f"Model: {self.model_name}",
            "",
            self.knowledge_base.summary(),
        ]
        
        if self.graph:
            lines.append("")
            lines.append(f"Graph nodes: {self.graph.node_count}")
            lines.append(f"Graph edges: {self.graph.edge_count}")
        
        return "\n".join(lines)
