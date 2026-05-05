# HazOp Simulator - Architecture Diagram

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                              │
│                    (React + TypeScript)                             │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ User Actions
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FRONTEND COMPONENTS                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  HazOpSimulator.tsx                                      │     │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────┐ │     │
│  │  │ Context Menu   │  │ Analysis Panel │  │ React Flow │ │     │
│  │  │ - Right-click  │  │ - Hazard Info  │  │ - Canvas   │ │     │
│  │  │ - 4 Modes      │  │ - Severity     │  │ - Nodes    │ │     │
│  │  │ - Node Select  │  │ - Effects      │  │ - Edges    │ │     │
│  │  └────────────────┘  └────────────────┘  └────────────┘ │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                     │
│  State Management: Zustand (useAppStore)                           │
│  Styling: Tailwind CSS + Custom Animations                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ HTTP POST
                                  │ /api/simulate-hazop
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKEND API                                    │
│                    (FastAPI + Python)                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  main.py                                                 │     │
│  │  ┌────────────────────────────────────────────────────┐  │     │
│  │  │  POST /api/simulate-hazop                          │  │     │
│  │  │  - Validate request (Pydantic)                     │  │     │
│  │  │  - Get simulator instance                          │  │     │
│  │  │  - Call simulate_failure()                         │  │     │
│  │  │  - Return structured response                      │  │     │
│  │  └────────────────────────────────────────────────────┘  │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Call Simulator
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   HAZOP SIMULATOR ENGINE                            │
│                  (hazop_simulator.py)                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  HazOpSimulator Class                                    │     │
│  │  ┌────────────────────────────────────────────────────┐  │     │
│  │  │  1. Build System Prompt                            │  │     │
│  │  │     - Senior HazOp Engineer persona                │  │     │
│  │  │     - Safety analysis methodology                  │  │     │
│  │  │     - Conservative approach                        │  │     │
│  │  │                                                     │  │     │
│  │  │  2. Build User Prompt                              │  │     │
│  │  │     - Failure scenario details                     │  │     │
│  │  │     - Topology data (nodes + edges)                │  │     │
│  │  │     - Analysis requirements                        │  │     │
│  │  │                                                     │  │     │
│  │  │  3. Define Response Schema                         │  │     │
│  │  │     - hazard_summary: string                       │  │     │
│  │  │     - cascading_effects: string[]                  │  │     │
│  │  │     - affected_node_ids: string[]                  │  │     │
│  │  │     - affected_edge_ids: string[]                  │  │     │
│  │  │     - severity_level: enum                         │  │     │
│  │  │     - recommended_actions: string[]                │  │     │
│  │  │                                                     │  │     │
│  │  │  4. Call Gemini API                                │  │     │
│  │  │     - Structured output mode                       │  │     │
│  │  │     - Temperature: 0.3                             │  │     │
│  │  │     - JSON response guaranteed                     │  │     │
│  │  │                                                     │  │     │
│  │  │  5. Fallback Analysis (if AI fails)                │  │     │
│  │  │     - Rule-based topology traversal               │  │     │
│  │  │     - Basic safety recommendations                 │  │     │
│  │  └────────────────────────────────────────────────────┘  │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ API Call
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      GOOGLE GEMINI AI                               │
│                   (google-genai SDK)                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Model: gemini-2.5-flash                                           │
│  Features:                                                          │
│  - Fast inference (2-5 seconds)                                    │
│  - Structured output with schema validation                        │
│  - Free tier: 15 req/min, 1500 req/day                            │
│  - Context window: 1M tokens                                       │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  AI Processing Pipeline                                  │     │
│  │  1. Parse system + user prompts                          │     │
│  │  2. Analyze topology graph structure                     │     │
│  │  3. Trace failure propagation paths                      │     │
│  │  4. Assess severity and consequences                     │     │
│  │  5. Generate emergency recommendations                   │     │
│  │  6. Format as structured JSON                            │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Structured JSON Response
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    RESPONSE PROCESSING                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Backend: Parse JSON → Validate → Return to Frontend               │
│  Frontend: Receive → Update State → Apply Visual Effects           │
│                                                                     │
│  Visual Effects Applied:                                            │
│  ┌────────────────────────────────────────────────────────┐        │
│  │  Failed Node:     🔴 Red pulsing glow                  │        │
│  │  Affected Nodes:  🟠 Orange border + shadow            │        │
│  │  Affected Edges:  🔴 Animated red lines                │        │
│  │  Analysis Panel:  📊 Sliding panel with results        │        │
│  └────────────────────────────────────────────────────────┘        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 📊 Data Flow Diagram

```
User Action (Right-click Node)
        │
        ▼
Context Menu Opens
        │
        ▼
User Selects Failure Mode
        │
        ▼
Frontend Collects Data:
  - failed_node_id: "V-101"
  - failure_mode: "Stuck Closed"
  - topology: { nodes: [...], edges: [...] }
        │
        ▼
HTTP POST to Backend
  URL: http://localhost:8000/api/simulate-hazop
  Body: { failed_node_id, failure_mode, topology }
        │
        ▼
FastAPI Endpoint Receives Request
        │
        ▼
Pydantic Validates Request
        │
        ▼
Get HazOpSimulator Instance (Singleton)
        │
        ▼
Build AI Prompts:
  - System: "You are a Senior HazOp Engineer..."
  - User: "Analyze failure of V-101 (Stuck Closed)..."
        │
        ▼
Call Gemini API with Structured Output
  - Model: gemini-2.5-flash
  - Config: response_schema, temperature=0.3
        │
        ▼
Gemini AI Processes:
  1. Parse topology graph
  2. Trace connections from V-101
  3. Identify affected equipment
  4. Assess severity
  5. Generate recommendations
        │
        ▼
Gemini Returns Structured JSON:
{
  "hazard_summary": "...",
  "cascading_effects": [...],
  "affected_node_ids": [...],
  "affected_edge_ids": [...],
  "severity_level": "HIGH",
  "recommended_actions": [...]
}
        │
        ▼
Backend Validates Response (Pydantic)
        │
        ▼
Backend Returns to Frontend
        │
        ▼
Frontend Receives Response
        │
        ▼
Update React State:
  - setSimulationResult(response)
  - setIsSimulating(false)
        │
        ▼
Apply Visual Effects:
  - Update node styles (red pulsing)
  - Update edge styles (animated red)
  - Show analysis panel
        │
        ▼
User Sees Results:
  - Canvas shows danger zones
  - Panel shows analysis
  - Can clear and reset
```

## 🔄 Component Interaction Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         App.tsx                                 │
│  - Main application container                                   │
│  - Manages active view state                                    │
│  - Renders HazOpSimulator when activeView === 'hazop'          │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ Renders
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   HazOpSimulator.tsx                            │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  State Management (React Hooks)                           │ │
│  │  - nodes, edges (useNodesState, useEdgesState)            │ │
│  │  - contextMenu (useState)                                 │ │
│  │  - simulationResult (useState)                            │ │
│  │  - isSimulating (useState)                                │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Event Handlers                                           │ │
│  │  - onNodeContextMenu: Show context menu                   │ │
│  │  - simulateFailure: Call API + update state               │ │
│  │  - applyVisualEffects: Update node/edge styles            │ │
│  │  - clearSimulation: Reset to default                      │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Child Components                                         │ │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │ │
│  │  │ ReactFlow   │  │ ContextMenu  │  │ AnalysisPanel  │  │ │
│  │  │ - Canvas    │  │ - Failure    │  │ - Results      │  │ │
│  │  │ - Controls  │  │   Modes      │  │ - Actions      │  │ │
│  │  │ - MiniMap   │  │ - Position   │  │ - Severity     │  │ │
│  │  └─────────────┘  └──────────────┘  └────────────────┘  │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🎨 Visual Effects Pipeline

```
Simulation Complete
        │
        ▼
applyVisualEffects(result)
        │
        ├─────────────────────────────────────────┐
        │                                         │
        ▼                                         ▼
Update Nodes                              Update Edges
        │                                         │
        ▼                                         ▼
For each node:                           For each edge:
  - Is failed node?                        - Is affected edge?
    → Red pulsing glow                       → Animated red line
    → 3px border                             → 3px stroke width
    → Box shadow                             → Drop shadow filter
    → Pulse animation                        → animated: true
        │                                         │
  - Is affected node?                            │
    → Orange border                              │
    → 2px border                                 │
    → Box shadow                                 │
        │                                         │
        └─────────────────┬───────────────────────┘
                          │
                          ▼
                  React Flow Re-renders
                          │
                          ▼
                  User Sees Visual Effects
```

## 🔐 Security & Error Handling

```
┌─────────────────────────────────────────────────────────────────┐
│                    Error Handling Layers                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer 1: Frontend Validation                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  - Check node exists                                      │ │
│  │  - Validate failure mode                                  │ │
│  │  - Ensure topology has data                               │ │
│  │  - Show loading state                                     │ │
│  └───────────────────────────────────────────────────────────┘ │
│                          │                                      │
│                          ▼                                      │
│  Layer 2: API Request Handling                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  - Try/catch around axios call                            │ │
│  │  - Handle network errors                                  │ │
│  │  - Handle timeout errors                                  │ │
│  │  - Show user-friendly error messages                      │ │
│  └───────────────────────────────────────────────────────────┘ │
│                          │                                      │
│                          ▼                                      │
│  Layer 3: Backend Validation                                    │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  - Pydantic model validation                              │ │
│  │  - Check API key exists                                   │ │
│  │  - Validate topology structure                            │ │
│  │  - Return 400/503 on errors                               │ │
│  └───────────────────────────────────────────────────────────┘ │
│                          │                                      │
│                          ▼                                      │
│  Layer 4: AI API Handling                                       │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  - Try/catch around Gemini call                           │ │
│  │  - Handle quota exceeded (503)                            │ │
│  │  - Handle high demand errors                              │ │
│  │  - Automatic fallback to rule-based                       │ │
│  └───────────────────────────────────────────────────────────┘ │
│                          │                                      │
│                          ▼                                      │
│  Layer 5: Response Validation                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  - Validate JSON structure                                │ │
│  │  - Check required fields                                  │ │
│  │  - Validate enum values                                   │ │
│  │  - Parse into Pydantic model                              │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 📈 Performance Optimization

```
┌─────────────────────────────────────────────────────────────────┐
│                  Performance Strategies                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Singleton Pattern                                           │
│     - Single HazOpSimulator instance                            │
│     - Reuse Gemini client connection                            │
│     - Avoid repeated initialization                             │
│                                                                 │
│  2. Topology Optimization                                       │
│     - Limit to 50 nodes, 100 edges                              │
│     - Truncate large topologies                                 │
│     - Send only relevant data                                   │
│                                                                 │
│  3. React Optimization                                          │
│     - useCallback for event handlers                            │
│     - Memoized components where needed                          │
│     - Efficient state updates                                   │
│                                                                 │
│  4. Visual Effects                                              │
│     - CSS animations (GPU accelerated)                          │
│     - Batch style updates                                       │
│     - Smooth transitions                                        │
│                                                                 │
│  5. API Efficiency                                              │
│     - Low temperature (0.3) for faster inference                │
│     - Structured output (no parsing overhead)                   │
│     - Fallback for quota management                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🎯 Key Design Decisions

### Why gemini-2.5-flash?
- ✅ Fast inference (2-5 seconds)
- ✅ Free tier available
- ✅ Structured output support
- ✅ Good balance of speed and accuracy
- ✅ Large context window (1M tokens)

### Why Structured Output?
- ✅ Guaranteed valid JSON
- ✅ No parsing errors
- ✅ Type-safe responses
- ✅ Consistent format
- ✅ Easy validation

### Why React Flow?
- ✅ Built for graph visualization
- ✅ Excellent performance
- ✅ Easy node/edge styling
- ✅ Built-in controls and minimap
- ✅ TypeScript support

### Why Fallback Analysis?
- ✅ Graceful degradation
- ✅ Always provides results
- ✅ Handles API quota limits
- ✅ Handles high demand periods
- ✅ Better user experience

---

**This architecture provides:**
- 🚀 Fast performance (2-5 second response)
- 🔒 Robust error handling (5 layers)
- 🎨 Beautiful UI (dark industrial theme)
- 🤖 AI-powered analysis (Gemini 2.5 Flash)
- 📊 Structured outputs (guaranteed JSON)
- 🔄 Graceful fallback (rule-based backup)
- ✅ Production ready (tested and documented)
