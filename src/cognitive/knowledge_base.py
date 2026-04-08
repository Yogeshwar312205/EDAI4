"""
EDAI4 - Engineering Knowledge Base
===================================
Knowledge base of engineering standards, P&ID conventions, and best practices.

Contains:
- ISA S5.1 instrument standards
- IEC 61511 safety requirements
- P&ID symbol conventions
- Engineering best practices
- Common Q&A patterns
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from src.utils import get_logger

logger = get_logger(__name__)


class KnowledgeCategory(Enum):
    """Categories of engineering knowledge."""
    ISA_S51 = "isa_s51"           # Instrument tagging
    IEC_61511 = "iec_61511"       # Safety instrumented systems
    PID_SYMBOLS = "pid_symbols"   # P&ID symbology
    CONTROL = "control"           # Control system design
    PROCESS = "process"           # Process engineering
    EQUIPMENT = "equipment"       # Equipment types
    GENERAL = "general"           # General knowledge


@dataclass
class KnowledgeEntry:
    """A single knowledge entry."""
    id: str
    category: KnowledgeCategory
    title: str
    content: str
    keywords: list[str] = field(default_factory=list)
    related_entries: list[str] = field(default_factory=list)
    source: str = ""
    
    def matches_query(self, query: str) -> float:
        """Calculate relevance score for a query."""
        query_lower = query.lower()
        score = 0.0
        
        # Title match
        if any(word in self.title.lower() for word in query_lower.split()):
            score += 0.3
        
        # Keyword match
        for keyword in self.keywords:
            if keyword.lower() in query_lower:
                score += 0.2
        
        # Content match
        query_words = set(query_lower.split())
        content_lower = self.content.lower()
        matches = sum(1 for word in query_words if word in content_lower)
        score += matches * 0.05
        
        return min(score, 1.0)


class EngineeringKnowledgeBase:
    """
    Knowledge base for P&ID and instrumentation engineering.
    
    Provides structured knowledge for:
    - Tag interpretation
    - Safety system requirements
    - Control loop design
    - Equipment specifications
    """
    
    def __init__(self):
        """Initialize knowledge base with built-in content."""
        self.entries: dict[str, KnowledgeEntry] = {}
        self._load_builtin_knowledge()
    
    def _load_builtin_knowledge(self):
        """Load built-in engineering knowledge."""
        
        # ISA S5.1 Knowledge
        self._add_entry(KnowledgeEntry(
            id="isa-first-letters",
            category=KnowledgeCategory.ISA_S51,
            title="ISA S5.1 First Letters (Measured Variables)",
            content="""
ISA S5.1 defines first letters for instrument tags indicating the measured/initiating variable:

| Letter | Variable | Description |
|--------|----------|-------------|
| A | Analysis | Composition, pH, conductivity |
| B | Burner/Combustion | Flame detection |
| C | User Choice | Often conductivity |
| D | User Choice | Often density |
| E | Voltage | Electrical voltage |
| F | Flow | Volume or mass flow rate |
| G | User Choice | Often gauging/dimension |
| H | Hand | Manual actuation |
| I | Current | Electrical current |
| J | Power | Electrical power |
| K | Time | Time-based control |
| L | Level | Liquid or solid level |
| M | User Choice | Often moisture |
| P | Pressure | Process pressure |
| Q | Quantity | Totalized flow |
| R | Radiation | Nuclear radiation |
| S | Speed/Frequency | Rotational speed |
| T | Temperature | Process temperature |
| U | Multivariable | Multiple variables |
| V | Vibration | Mechanical vibration |
| W | Weight/Force | Weight or force |
| X | Unclassified | Special applications |
| Y | Event/State | Presence, sequence |
| Z | Position | Valve/actuator position |
""",
            keywords=["first letter", "measured variable", "ISA", "tag", "instrument"],
            source="ISA-5.1-2009",
        ))
        
        self._add_entry(KnowledgeEntry(
            id="isa-succeeding-letters",
            category=KnowledgeCategory.ISA_S51,
            title="ISA S5.1 Succeeding Letters (Functions)",
            content="""
Succeeding letters in ISA S5.1 tags indicate instrument functions:

**Readout/Passive Functions:**
- A: Alarm
- G: Glass/Gauge (local viewing)
- I: Indicating (local display)
- R: Recording

**Output/Control Functions:**
- C: Control
- K: Control Station
- S: Switch (discrete output)
- T: Transmit (to control system)
- V: Valve/Damper (final element)
- Y: Relay/Compute
- Z: Actuator/Driver

**Modifiers:**
- D: Differential
- E: Element/Sensor (primary)
- F: Ratio/Fraction
- H: High
- L: Low
- M: Middle/Intermediate
- O: Orifice/Restriction
- Q: Integrate/Totalize
- W: Well/Probe

**Common combinations:**
- FT: Flow Transmitter
- LIC: Level Indicating Controller
- PSH: Pressure Switch High
- TCV: Temperature Control Valve
""",
            keywords=["function", "succeeding letter", "transmitter", "controller", "switch"],
            source="ISA-5.1-2009",
        ))
        
        self._add_entry(KnowledgeEntry(
            id="isa-tag-format",
            category=KnowledgeCategory.ISA_S51,
            title="ISA S5.1 Tag Number Format",
            content="""
Standard ISA S5.1 tag format:

**Format:** [Area-]FirstLetter[SucceedingLetters]-LoopNumber[Suffix]

**Examples:**
- FT-101: Flow Transmitter, Loop 101
- 100-LIC-201A: Area 100, Level Indicating Controller, Loop 201, Unit A
- PSH-300: Pressure Switch High, Loop 300

**Components:**
1. Area prefix (optional): Plant area/unit number (e.g., "100-")
2. First letter: Measured variable (F, L, P, T, etc.)
3. Succeeding letters: Functions (I, C, T, S, V, etc.)
4. Hyphen: Optional separator
5. Loop number: Numeric identifier (typically 3-5 digits)
6. Suffix: Redundancy indicator (A, B, C) or qualifier

**Best Practices:**
- Use consistent loop numbering across a project
- Match transmitter and controller loop numbers
- Use suffixes for redundant instruments
""",
            keywords=["tag format", "loop number", "area", "suffix"],
            source="ISA-5.1-2009",
        ))
        
        # IEC 61511 Safety Knowledge
        self._add_entry(KnowledgeEntry(
            id="iec61511-sil",
            category=KnowledgeCategory.IEC_61511,
            title="Safety Integrity Levels (SIL)",
            content="""
IEC 61511 defines Safety Integrity Levels for Safety Instrumented Systems:

**SIL Levels:**
| SIL | PFDavg (Low Demand) | RRF | Description |
|-----|---------------------|-----|-------------|
| 1 | 0.1 to 0.01 | 10-100 | Basic safety |
| 2 | 0.01 to 0.001 | 100-1000 | Standard industrial |
| 3 | 0.001 to 0.0001 | 1000-10000 | High hazard |
| 4 | 0.0001 to 0.00001 | 10000-100000 | Rarely used |

**Key Terms:**
- PFDavg: Average Probability of Failure on Demand
- RRF: Risk Reduction Factor

**Architecture Requirements:**
- SIL 1: Single channel may be acceptable
- SIL 2: Usually 1oo2 (1 out of 2) or redundant
- SIL 3: Typically 2oo3 (2 out of 3) voting

**Proof Test Intervals:**
- Based on sensor/final element technology
- Typically annual or semi-annual
- More frequent for higher SIL
""",
            keywords=["SIL", "safety", "PFD", "integrity", "IEC 61511", "SIS"],
            source="IEC 61511-1:2016",
        ))
        
        self._add_entry(KnowledgeEntry(
            id="iec61511-sis-architecture",
            category=KnowledgeCategory.IEC_61511,
            title="SIS Architecture and Voting",
            content="""
Safety Instrumented System (SIS) voting architectures:

**Common Architectures:**
- 1oo1 (1 out of 1): Single channel, no redundancy
- 1oo2 (1 out of 2): Either channel trips (safe, less available)
- 2oo2 (2 out of 2): Both channels must trip (available, less safe)
- 2oo3 (2 out of 3): Two of three channels trip (balanced)

**Selection Criteria:**
- Safety vs. Availability trade-off
- Process consequences of spurious trips
- Required SIL level
- Diagnostic coverage available

**1oo2 vs 2oo3:**
- 1oo2: Higher spurious trip rate, better for safety
- 2oo3: Better availability, still achieves high safety
- 2oo3 preferred for high SIL with availability needs

**SIS Components:**
1. Initiator (sensor): PSH, TSH, LSL, etc.
2. Logic Solver: Safety PLC/SIS controller
3. Final Element: SDV, BDV, XV, etc.
""",
            keywords=["voting", "1oo2", "2oo3", "redundancy", "architecture", "SIS"],
            source="IEC 61511-1:2016",
        ))
        
        # Control System Knowledge
        self._add_entry(KnowledgeEntry(
            id="control-loops",
            category=KnowledgeCategory.CONTROL,
            title="Control Loop Types",
            content="""
Common control loop configurations in process control:

**Regulatory Control:**
Basic feedback loop: Transmitter → Controller → Final Element
Example: FIC-101 (flow controller) adjusts FCV-101 based on FT-101

**Cascade Control:**
Master controller output sets setpoint of slave controller
Example: TIC-100 (temperature) → FIC-101 (flow) → FCV-101
Use when: Inner loop is faster than outer loop

**Ratio Control:**
Maintains ratio between two flows
Example: FFC-100 keeps Feed B flow proportional to Feed A
Use when: Mixing, blending, stoichiometric reactions

**Feedforward Control:**
Anticipates disturbances before they affect process
Example: Feed rate change triggers immediate heating adjustment
Use when: Measurable disturbances with known effects

**Split-Range Control:**
One controller drives multiple final elements
Example: PIC-100 → PCV-100A (0-50%) + PCV-100B (50-100%)
Use when: Different responses needed at different ranges

**Override/Select Control:**
High or low selector between controllers
Example: MIN(FIC-101, LIC-102) → FCV-100
Use when: Protection limits needed
""",
            keywords=["control loop", "cascade", "ratio", "feedforward", "split-range", "PID"],
            source="Engineering Best Practices",
        ))
        
        self._add_entry(KnowledgeEntry(
            id="pid-tuning",
            category=KnowledgeCategory.CONTROL,
            title="PID Controller Tuning",
            content="""
PID (Proportional-Integral-Derivative) controller tuning guidelines:

**PID Equation:**
Output = Kp × e(t) + Ki × ∫e(t)dt + Kd × de(t)/dt

**Typical Tuning by Loop Type:**

| Loop Type | Kp | Ti (min) | Td (min) |
|-----------|-----|----------|----------|
| Flow | 0.5-1.0 | 0.1-0.5 | 0 |
| Level | 1-5 | 1-5 | 0 |
| Pressure (gas) | 1-2 | 0.5-2 | 0 |
| Pressure (liquid) | 0.5-1 | 0.1-0.5 | 0 |
| Temperature | 1-5 | 2-10 | 0.5-2 |

**Tuning Methods:**
1. Ziegler-Nichols (ultimate gain method)
2. Cohen-Coon (process reaction curve)
3. Lambda tuning (desired closed-loop response)
4. Internal Model Control (IMC)

**General Guidelines:**
- Start with P-only, then add I, then D
- Flow loops rarely need derivative
- Temperature loops often benefit from derivative
- Avoid aggressive tuning in safety systems
""",
            keywords=["PID", "tuning", "proportional", "integral", "derivative", "Kp", "Ti", "Td"],
            source="Engineering Best Practices",
        ))
        
        # Equipment Knowledge
        self._add_entry(KnowledgeEntry(
            id="equipment-types",
            category=KnowledgeCategory.EQUIPMENT,
            title="Common P&ID Equipment",
            content="""
Common equipment types in P&IDs and their typical instrumentation:

**Vessels/Tanks (TK, V):**
- Level: LT, LIC, LAH, LAL, LG
- Pressure: PT, PI, PSV
- Temperature: TT, TI

**Pumps (P):**
- Flow: FT, FIC (discharge)
- Pressure: PI (suction/discharge)
- Level: LSL (suction tank low)

**Compressors (C):**
- Pressure: PIC (discharge)
- Temperature: TI (discharge)
- Vibration: VT, VAH
- Speed: ST

**Heat Exchangers (E):**
- Temperature: TIC (outlet)
- Flow: FT (both sides)
- Differential Pressure: PDT

**Reactors (R):**
- Temperature: TIC (multiple zones)
- Pressure: PIC
- Level: LIC
- Analysis: AIC (composition)

**Distillation Columns:**
- Pressure: PIC (top)
- Level: LIC (bottom, reflux drum)
- Temperature: TI (multiple trays)
- Flow: FIC (reflux, feed)
""",
            keywords=["equipment", "tank", "pump", "compressor", "heat exchanger", "reactor", "column"],
            source="Engineering Best Practices",
        ))
        
        # P&ID Symbols
        self._add_entry(KnowledgeEntry(
            id="pid-instrument-symbols",
            category=KnowledgeCategory.PID_SYMBOLS,
            title="P&ID Instrument Symbols",
            content="""
Standard P&ID instrument symbols per ISA S5.1:

**Location Symbols (Shape):**
- Circle: Field mounted
- Circle with horizontal line: Panel mounted
- Square: DCS/Computer function
- Hexagon: PLC function
- Diamond: Shared display

**Connection to Process:**
- Solid line: Process connection
- Dashed line: Signal (pneumatic/electric)
- Double line: Data link

**Instrument Bubbles:**
- Single circle: Discrete instrument
- Bubble with leader: Tag number location
- Shared bubble: Multi-function instrument

**Valve Symbols:**
- Globe valve: ⊗ (general)
- Ball valve: Filled circle in line
- Gate valve: Zigzag through line
- Check valve: Arrow through line
- Control valve: Globe with diaphragm

**Line Symbols:**
- Solid: Process line
- Dashed: Instrument signal
- Double: Major process line
- Arrow: Flow direction
""",
            keywords=["symbol", "circle", "square", "bubble", "valve", "line"],
            source="ISA-5.1-2009",
        ))
        
        # Common Questions
        self._add_entry(KnowledgeEntry(
            id="faq-tag-meaning",
            category=KnowledgeCategory.GENERAL,
            title="How to Read Instrument Tags",
            content="""
**Question:** How do I read an instrument tag like "FIC-101"?

**Answer:**
Break down the tag into components:

FIC-101:
- F = Flow (measured variable)
- I = Indicating (has local display)
- C = Controller (controls the process)
- 101 = Loop number

So FIC-101 is a "Flow Indicating Controller for Loop 101"

**More Examples:**

| Tag | Meaning |
|-----|---------|
| LT-200 | Level Transmitter, Loop 200 |
| PSH-301 | Pressure Switch High, Loop 301 |
| TCV-102 | Temperature Control Valve, Loop 102 |
| AIT-401 | Analyzer Indicating Transmitter, Loop 401 |
| SDV-001 | Shutdown Valve, Loop 001 |

**Tips:**
1. First letter = what's being measured
2. Middle letters = functions performed
3. Number = loop identifier
4. Letter suffix (A, B) = redundant units
""",
            keywords=["read tag", "understand tag", "meaning", "how to"],
            source="Training Material",
        ))
        
        self._add_entry(KnowledgeEntry(
            id="faq-control-valve-sizing",
            category=KnowledgeCategory.GENERAL,
            title="Control Valve Selection",
            content="""
**Question:** How is a control valve selected and sized?

**Answer:**

**Selection Criteria:**
1. **Service conditions:**
   - Fluid type (liquid, gas, two-phase)
   - Temperature and pressure
   - Corrosive/erosive properties

2. **Control requirements:**
   - Required Cv (flow coefficient)
   - Rangeability needed
   - Inherent characteristic (linear, equal %)

3. **Fail-safe action:**
   - Fail-closed (FC): Valve closes on air/signal loss
   - Fail-open (FO): Valve opens on air/signal loss
   - Fail-last (FL): Stays in last position

**Sizing:**
Cv = Q × √(SG / ΔP)

Where:
- Q = Flow rate (GPM for liquids)
- SG = Specific gravity
- ΔP = Pressure drop (psi)

**Best Practices:**
- Size for 60-80% open at normal conditions
- Ensure adequate rangeability (typically 50:1)
- Consider noise and cavitation limits
""",
            keywords=["control valve", "sizing", "Cv", "fail-safe", "selection"],
            source="Engineering Best Practices",
        ))
        
        logger.info(f"Loaded {len(self.entries)} knowledge entries")
    
    def _add_entry(self, entry: KnowledgeEntry):
        """Add an entry to the knowledge base."""
        self.entries[entry.id] = entry
    
    def search(self, query: str, top_k: int = 5) -> list[tuple[KnowledgeEntry, float]]:
        """
        Search knowledge base for relevant entries.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of (entry, score) tuples sorted by relevance
        """
        results = []
        
        for entry in self.entries.values():
            score = entry.matches_query(query)
            if score > 0:
                results.append((entry, score))
        
        # Sort by score descending
        results.sort(key=lambda x: -x[1])
        
        return results[:top_k]
    
    def get_by_id(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Get entry by ID."""
        return self.entries.get(entry_id)
    
    def get_by_category(self, category: KnowledgeCategory) -> list[KnowledgeEntry]:
        """Get all entries in a category."""
        return [e for e in self.entries.values() if e.category == category]
    
    def build_context(self, query: str, max_tokens: int = 2000) -> str:
        """
        Build context string for LLM from relevant knowledge.
        
        Args:
            query: User query
            max_tokens: Approximate max context length
            
        Returns:
            Formatted context string
        """
        results = self.search(query, top_k=3)
        
        if not results:
            return ""
        
        context_parts = ["## Relevant Engineering Knowledge\n"]
        
        for entry, score in results:
            section = f"\n### {entry.title}\n{entry.content}\n"
            
            # Simple token estimation (4 chars per token)
            if len("".join(context_parts)) + len(section) > max_tokens * 4:
                break
            
            context_parts.append(section)
        
        return "".join(context_parts)
    
    def summary(self) -> str:
        """Get summary of knowledge base contents."""
        category_counts = {}
        for entry in self.entries.values():
            cat = entry.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        lines = [
            "Engineering Knowledge Base",
            "=" * 40,
            f"Total Entries: {len(self.entries)}",
            "",
            "By Category:",
        ]
        
        for cat, count in sorted(category_counts.items()):
            lines.append(f"  {cat}: {count}")
        
        return "\n".join(lines)


# Singleton instance for convenience
_knowledge_base: Optional[EngineeringKnowledgeBase] = None

def get_knowledge_base() -> EngineeringKnowledgeBase:
    """Get or create the singleton knowledge base."""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = EngineeringKnowledgeBase()
    return _knowledge_base
