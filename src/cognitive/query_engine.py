"""
EDAI4 - Natural Language Query Engine
======================================
Parses user questions and routes to appropriate data sources.

Capabilities:
- Intent classification (tag lookup, loop analysis, equipment query)
- Entity extraction (tags, equipment names, loop numbers)
- Query routing to graph/semantic/knowledge sources
- Multi-source aggregation
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum
import re

from src.topology.graph_builder import PIDGraph, GraphNode, NodeType, EdgeType
from src.cognitive.isa_validator import ISAS51Validator
from src.cognitive.knowledge_base import get_knowledge_base, EngineeringKnowledgeBase
from src.utils import get_logger

logger = get_logger(__name__)


class QueryIntent(Enum):
    """Types of user query intents."""
    TAG_LOOKUP = "tag_lookup"           # "What is FT-101?"
    TAG_LIST = "tag_list"               # "List all flow transmitters"
    LOOP_ANALYSIS = "loop_analysis"     # "Describe control loop 101"
    EQUIPMENT_QUERY = "equipment_query" # "What instruments are on TK-100?"
    SAFETY_QUERY = "safety_query"       # "What safety instruments protect R-101?"
    FLOW_PATH = "flow_path"             # "What is the flow path from TK-101 to R-102?"
    KNOWLEDGE = "knowledge"             # "What does SIL mean?"
    COMPARISON = "comparison"           # "Compare FIC-101 and FIC-102"
    COUNT = "count"                     # "How many temperature transmitters?"
    GENERAL = "general"                 # Fallback for unclear queries


@dataclass
class ExtractedEntities:
    """Entities extracted from a query."""
    tags: list[str] = field(default_factory=list)
    equipment: list[str] = field(default_factory=list)
    loop_numbers: list[str] = field(default_factory=list)
    variable_types: list[str] = field(default_factory=list)  # F, L, P, T
    keywords: list[str] = field(default_factory=list)


@dataclass
class ParsedQuery:
    """Result of parsing a natural language query."""
    original_query: str
    intent: QueryIntent
    entities: ExtractedEntities
    confidence: float
    sub_queries: list[str] = field(default_factory=list)


@dataclass
class QueryResult:
    """Result from executing a query."""
    query: ParsedQuery
    answer: str
    sources: list[str] = field(default_factory=list)
    data: dict = field(default_factory=dict)
    confidence: float = 1.0


class QueryEngine:
    """
    Natural language query engine for P&ID data.
    
    Parses questions and retrieves answers from:
    - Graph database (topology, connections)
    - Semantic layer (enriched descriptions)
    - Knowledge base (engineering standards)
    """
    
    # Patterns for entity extraction
    TAG_PATTERN = re.compile(r'\b([A-Z]{1,4}-?\d{2,5}[A-Z]?)\b', re.IGNORECASE)
    LOOP_PATTERN = re.compile(r'\b(?:loop\s*)?(\d{2,5})\b', re.IGNORECASE)
    EQUIPMENT_PATTERN = re.compile(
        r'\b(TK|V|P|C|R|E|D|T|F|H|M)-?\d{2,4}\b',
        re.IGNORECASE
    )
    
    # Intent keywords
    INTENT_KEYWORDS = {
        QueryIntent.TAG_LOOKUP: ["what is", "describe", "explain", "tell me about"],
        QueryIntent.TAG_LIST: ["list", "show all", "find all", "get all"],
        QueryIntent.LOOP_ANALYSIS: ["loop", "control loop", "analyze loop"],
        QueryIntent.EQUIPMENT_QUERY: ["on", "connected to", "instruments on", "equipment"],
        QueryIntent.SAFETY_QUERY: ["safety", "sil", "trip", "interlock", "protect"],
        QueryIntent.FLOW_PATH: ["flow path", "path from", "connected", "upstream", "downstream"],
        QueryIntent.KNOWLEDGE: ["what does", "how to", "define", "meaning of", "standard"],
        QueryIntent.COMPARISON: ["compare", "difference between", "versus", "vs"],
        QueryIntent.COUNT: ["how many", "count", "number of", "total"],
    }
    
    def __init__(self, graph: Optional[PIDGraph] = None):
        """
        Initialize query engine.
        
        Args:
            graph: Optional PIDGraph for data queries
        """
        self.graph = graph
        self.validator = ISAS51Validator()
        self.knowledge_base = get_knowledge_base()
    
    def set_graph(self, graph: PIDGraph):
        """Set or update the graph."""
        self.graph = graph
    
    def parse_query(self, query: str) -> ParsedQuery:
        """
        Parse a natural language query.
        
        Args:
            query: User's question
            
        Returns:
            ParsedQuery with intent and entities
        """
        query_lower = query.lower()
        
        # Extract entities
        entities = self._extract_entities(query)
        
        # Classify intent
        intent, confidence = self._classify_intent(query_lower, entities)
        
        return ParsedQuery(
            original_query=query,
            intent=intent,
            entities=entities,
            confidence=confidence,
        )
    
    def _extract_entities(self, query: str) -> ExtractedEntities:
        """Extract named entities from query."""
        entities = ExtractedEntities()
        
        # Extract instrument tags
        tags = self.TAG_PATTERN.findall(query.upper())
        entities.tags = [t.replace("-", "-") for t in tags]
        
        # Extract equipment tags
        equipment = self.EQUIPMENT_PATTERN.findall(query.upper())
        entities.equipment = equipment
        
        # Extract loop numbers
        loops = self.LOOP_PATTERN.findall(query)
        entities.loop_numbers = loops
        
        # Extract variable types
        var_keywords = {
            "flow": "F", "level": "L", "pressure": "P", "temperature": "T",
            "analyzer": "A", "vibration": "V", "position": "Z",
        }
        for keyword, var_type in var_keywords.items():
            if keyword in query.lower():
                entities.variable_types.append(var_type)
        
        # Extract general keywords
        important_words = ["safety", "control", "valve", "transmitter", "controller"]
        entities.keywords = [w for w in important_words if w in query.lower()]
        
        return entities
    
    def _classify_intent(self, query_lower: str, entities: ExtractedEntities) -> tuple[QueryIntent, float]:
        """Classify query intent."""
        best_intent = QueryIntent.GENERAL
        best_score = 0.0
        
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in query_lower) / len(keywords)
            if score > best_score:
                best_score = score
                best_intent = intent
        
        # Boost score based on entities
        if entities.tags:
            if best_intent == QueryIntent.GENERAL:
                best_intent = QueryIntent.TAG_LOOKUP
                best_score = 0.7
        
        if entities.loop_numbers and "loop" in query_lower:
            best_intent = QueryIntent.LOOP_ANALYSIS
            best_score = max(best_score, 0.8)
        
        return best_intent, min(best_score + 0.3, 1.0)  # Baseline confidence
    
    def execute_query(self, query: str) -> QueryResult:
        """
        Execute a natural language query.
        
        Args:
            query: User's question
            
        Returns:
            QueryResult with answer and sources
        """
        parsed = self.parse_query(query)
        
        # Route to appropriate handler
        handlers = {
            QueryIntent.TAG_LOOKUP: self._handle_tag_lookup,
            QueryIntent.TAG_LIST: self._handle_tag_list,
            QueryIntent.LOOP_ANALYSIS: self._handle_loop_analysis,
            QueryIntent.EQUIPMENT_QUERY: self._handle_equipment_query,
            QueryIntent.SAFETY_QUERY: self._handle_safety_query,
            QueryIntent.KNOWLEDGE: self._handle_knowledge_query,
            QueryIntent.COUNT: self._handle_count_query,
            QueryIntent.GENERAL: self._handle_general_query,
        }
        
        handler = handlers.get(parsed.intent, self._handle_general_query)
        return handler(parsed)
    
    def _handle_tag_lookup(self, parsed: ParsedQuery) -> QueryResult:
        """Handle tag lookup queries."""
        if not parsed.entities.tags:
            return QueryResult(
                query=parsed,
                answer="No instrument tag found in query. Please specify a tag like FT-101.",
                confidence=0.5,
            )
        
        tag = parsed.entities.tags[0]
        sources = []
        data = {}
        
        # Validate and describe tag
        validation = self.validator.validate_tag(tag)
        description = self.validator.get_letter_description(tag)
        
        parts = [f"**{tag}**"]
        
        if description.get("measured_variable"):
            mv = description["measured_variable"]
            parts.append(f"- Measured Variable: {mv['name']} ({mv['description']})")
        
        if description.get("functions"):
            funcs = ", ".join(f["name"] for f in description["functions"])
            parts.append(f"- Functions: {funcs}")
        
        if validation.parsed_loop_number:
            parts.append(f"- Loop Number: {validation.parsed_loop_number}")
        
        # Check graph for additional info
        if self.graph:
            node = self.graph.get_node_by_tag(tag)
            if node:
                sources.append(f"Graph node: {node.id}")
                if node.description:
                    parts.append(f"- Description: {node.description}")
                
                # Get connected equipment
                for connected, edge in self.graph.get_connected_nodes(node.id):
                    if connected.node_type in (NodeType.EQUIPMENT, NodeType.PUMP):
                        parts.append(f"- Connected to: {connected.tag or connected.label}")
        
        data["validation"] = validation.to_dict()
        data["description"] = description
        
        return QueryResult(
            query=parsed,
            answer="\n".join(parts),
            sources=sources,
            data=data,
            confidence=validation.compliance_score,
        )
    
    def _handle_tag_list(self, parsed: ParsedQuery) -> QueryResult:
        """Handle list/find all queries."""
        if not self.graph:
            return QueryResult(
                query=parsed,
                answer="No P&ID data loaded. Please load a P&ID first.",
                confidence=0.3,
            )
        
        # Filter by variable type if specified
        var_types = parsed.entities.variable_types
        
        matching_tags = []
        for node in self.graph.get_instruments():
            if not node.tag:
                continue
            
            result = self.validator.validate_tag(node.tag)
            first = result.parsed_first_letter
            
            if var_types and first not in var_types:
                continue
            
            matching_tags.append(node.tag)
        
        if not matching_tags:
            return QueryResult(
                query=parsed,
                answer="No matching instruments found.",
                confidence=0.7,
            )
        
        # Format answer
        type_name = ""
        if var_types:
            from src.cognitive.isa_validator import ISA_FIRST_LETTERS
            type_name = ISA_FIRST_LETTERS.get(var_types[0], {}).get("name", "")
        
        header = f"Found {len(matching_tags)} {type_name} instruments:" if type_name else f"Found {len(matching_tags)} instruments:"
        tag_list = ", ".join(sorted(matching_tags)[:20])
        
        if len(matching_tags) > 20:
            tag_list += f"... and {len(matching_tags) - 20} more"
        
        return QueryResult(
            query=parsed,
            answer=f"{header}\n{tag_list}",
            data={"tags": matching_tags},
            confidence=0.9,
        )
    
    def _handle_loop_analysis(self, parsed: ParsedQuery) -> QueryResult:
        """Handle control loop analysis queries."""
        if not parsed.entities.loop_numbers:
            return QueryResult(
                query=parsed,
                answer="No loop number specified. Please include a loop number like 'loop 101'.",
                confidence=0.5,
            )
        
        loop_num = parsed.entities.loop_numbers[0]
        
        if not self.graph:
            # Provide general knowledge
            kb_context = self.knowledge_base.build_context(f"control loop {loop_num}")
            return QueryResult(
                query=parsed,
                answer=f"No P&ID data loaded. Here's general information about control loops:\n\n{kb_context}",
                confidence=0.6,
            )
        
        # Find instruments in this loop
        loop_instruments = []
        for node in self.graph.get_instruments():
            if not node.tag:
                continue
            result = self.validator.validate_tag(node.tag)
            if result.parsed_loop_number == loop_num:
                loop_instruments.append(node)
        
        if not loop_instruments:
            return QueryResult(
                query=parsed,
                answer=f"No instruments found for loop {loop_num}.",
                confidence=0.7,
            )
        
        # Categorize instruments
        transmitters = []
        controllers = []
        final_elements = []
        others = []
        
        for node in loop_instruments:
            result = self.validator.validate_tag(node.tag)
            succ = result.parsed_succeeding_letters or ""
            
            if "T" in succ and "C" not in succ:
                transmitters.append(node.tag)
            elif "C" in succ:
                controllers.append(node.tag)
            elif "V" in succ:
                final_elements.append(node.tag)
            else:
                others.append(node.tag)
        
        parts = [f"**Control Loop {loop_num}**", ""]
        
        if transmitters:
            parts.append(f"- Transmitters: {', '.join(transmitters)}")
        if controllers:
            parts.append(f"- Controllers: {', '.join(controllers)}")
        if final_elements:
            parts.append(f"- Final Elements: {', '.join(final_elements)}")
        if others:
            parts.append(f"- Other: {', '.join(others)}")
        
        return QueryResult(
            query=parsed,
            answer="\n".join(parts),
            data={
                "loop": loop_num,
                "transmitters": transmitters,
                "controllers": controllers,
                "final_elements": final_elements,
            },
            confidence=0.85,
        )
    
    def _handle_equipment_query(self, parsed: ParsedQuery) -> QueryResult:
        """Handle equipment-related queries."""
        if not self.graph:
            return QueryResult(
                query=parsed,
                answer="No P&ID data loaded.",
                confidence=0.3,
            )
        
        equipment_tag = None
        if parsed.entities.equipment:
            equipment_tag = parsed.entities.equipment[0]
        elif parsed.entities.tags:
            # Check if it's equipment
            for tag in parsed.entities.tags:
                node = self.graph.get_node_by_tag(tag)
                if node and node.node_type in (NodeType.EQUIPMENT, NodeType.PUMP):
                    equipment_tag = tag
                    break
        
        if not equipment_tag:
            return QueryResult(
                query=parsed,
                answer="No equipment specified. Please include an equipment tag like TK-100.",
                confidence=0.5,
            )
        
        node = self.graph.get_node_by_tag(equipment_tag)
        if not node:
            return QueryResult(
                query=parsed,
                answer=f"Equipment {equipment_tag} not found in P&ID.",
                confidence=0.7,
            )
        
        # Get connected instruments
        connected_instruments = []
        for connected, edge in self.graph.get_connected_nodes(node.id):
            if connected.node_type == NodeType.INSTRUMENT and connected.tag:
                connected_instruments.append(connected.tag)
        
        parts = [f"**Equipment: {equipment_tag}**"]
        parts.append(f"- Type: {node.label or node.detection_class}")
        
        if connected_instruments:
            parts.append(f"- Instruments ({len(connected_instruments)}): {', '.join(sorted(connected_instruments))}")
        else:
            parts.append("- No instruments connected")
        
        return QueryResult(
            query=parsed,
            answer="\n".join(parts),
            data={"equipment": equipment_tag, "instruments": connected_instruments},
            confidence=0.85,
        )
    
    def _handle_safety_query(self, parsed: ParsedQuery) -> QueryResult:
        """Handle safety-related queries."""
        # Get knowledge base context
        kb_context = self.knowledge_base.build_context(parsed.original_query)
        
        if not self.graph:
            return QueryResult(
                query=parsed,
                answer=f"Here's safety information:\n\n{kb_context}",
                sources=["Knowledge Base"],
                confidence=0.7,
            )
        
        # Find safety instruments
        safety_patterns = ["SH", "SL", "AH", "AL", "HH", "LL", "SDV", "BDV", "XV", "PSV"]
        safety_instruments = []
        
        for node in self.graph.nodes.values():
            if not node.tag:
                continue
            if any(p in node.tag.upper() for p in safety_patterns):
                safety_instruments.append(node.tag)
        
        parts = ["**Safety Instruments Found:**"]
        if safety_instruments:
            parts.append(", ".join(sorted(safety_instruments)))
        else:
            parts.append("No safety instruments detected.")
        
        if kb_context:
            parts.append("\n**Reference:**")
            parts.append(kb_context[:500])  # Limit context length
        
        return QueryResult(
            query=parsed,
            answer="\n".join(parts),
            data={"safety_instruments": safety_instruments},
            sources=["Graph", "Knowledge Base"],
            confidence=0.8,
        )
    
    def _handle_knowledge_query(self, parsed: ParsedQuery) -> QueryResult:
        """Handle knowledge/definition queries."""
        context = self.knowledge_base.build_context(parsed.original_query)
        
        if not context:
            return QueryResult(
                query=parsed,
                answer="I don't have specific information about that. Try asking about ISA S5.1, control loops, or safety systems.",
                confidence=0.4,
            )
        
        return QueryResult(
            query=parsed,
            answer=context,
            sources=["Engineering Knowledge Base"],
            confidence=0.85,
        )
    
    def _handle_count_query(self, parsed: ParsedQuery) -> QueryResult:
        """Handle counting queries."""
        if not self.graph:
            return QueryResult(
                query=parsed,
                answer="No P&ID data loaded.",
                confidence=0.3,
            )
        
        var_types = parsed.entities.variable_types
        
        count = 0
        for node in self.graph.get_instruments():
            if not node.tag:
                continue
            
            if var_types:
                result = self.validator.validate_tag(node.tag)
                if result.parsed_first_letter in var_types:
                    count += 1
            else:
                count += 1
        
        type_name = ""
        if var_types:
            from src.cognitive.isa_validator import ISA_FIRST_LETTERS
            type_name = ISA_FIRST_LETTERS.get(var_types[0], {}).get("name", "") + " "
        
        return QueryResult(
            query=parsed,
            answer=f"There are **{count}** {type_name}instruments in the P&ID.",
            data={"count": count, "type": type_name.strip()},
            confidence=0.95,
        )
    
    def _handle_general_query(self, parsed: ParsedQuery) -> QueryResult:
        """Handle general/unclear queries."""
        # Try knowledge base first
        context = self.knowledge_base.build_context(parsed.original_query)
        
        if context:
            return QueryResult(
                query=parsed,
                answer=context,
                sources=["Knowledge Base"],
                confidence=0.6,
            )
        
        return QueryResult(
            query=parsed,
            answer=(
                "I'm not sure how to answer that. Try asking:\n"
                "- 'What is FT-101?' (tag lookup)\n"
                "- 'List all flow transmitters' (tag list)\n"
                "- 'Describe control loop 101' (loop analysis)\n"
                "- 'What does SIL mean?' (knowledge)"
            ),
            confidence=0.3,
        )
