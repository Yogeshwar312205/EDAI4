# AI-Powered Features Guide

## Overview

Two powerful AI features have been added to the EDAI4 P&ID Dashboard using Google Gemini AI:

1. **Natural Language Graph Filtering** - Talk to your graph
2. **Dynamic Maintenance Checklists** - AI-generated equipment maintenance tasks

Both features use the same Gemini API configuration as the existing chatbot and HazOp simulator.

---

## Feature 1: Natural Language Graph Filtering

### What It Does
Allows users to filter and highlight specific parts of the P&ID graph using natural language queries instead of clicking through menus.

### How It Works

**User Experience:**
1. Navigate to the "Graph" tab
2. Find the "Smart Graph Filter" panel in the top-left
3. Type a natural language query like:
   - "Show me all cooling water lines connected to the furnace"
   - "Find all control valves"
   - "Show me all pumps"
4. Click "Filter" or press Enter
5. The graph instantly dims all non-matching nodes and highlights only the requested equipment

**Technical Flow:**
```
User Query → Frontend (GraphFilter.tsx) 
          → Backend API (/api/filter-graph)
          → Gemini AI (graph_filter.py)
          → Returns: matched_node_ids, matched_edge_ids, explanation
          → Frontend applies visual dimming/highlighting
```

**API Endpoint:**
```
POST /api/filter-graph
{
  "query": "Show me all cooling water lines",
  "topology": {
    "nodes": [...],
    "edges": [...]
  }
}

Response:
{
  "matched_node_ids": ["node_5", "node_8", "node_12"],
  "matched_edge_ids": ["edge_3", "edge_9"],
  "explanation": "Found 3 cooling water valves and 2 connecting lines",
  "query": "Show me all cooling water lines"
}
```

### Key Features

- **Natural Language Understanding**: Uses Gemini AI to interpret complex queries
- **Visual Feedback**: Dims non-matching nodes to 20% opacity, keeps matches at 100%
- **Quick Suggestions**: Pre-built filter buttons for common queries
- **Clear Filter**: One-click to restore full graph view
- **Real-time Stats**: Shows count of matched nodes and edges
- **Fallback Mode**: If AI fails, uses keyword-based matching

### Files Created/Modified

**Backend:**
- `src/api/graph_filter.py` - Gemini AI integration for graph filtering
- `src/api/main.py` - Added `/api/filter-graph` endpoint

**Frontend:**
- `frontend/src/components/GraphFilter.tsx` - Filter UI component
- `frontend/src/components/GraphViewer.tsx` - Integrated filter into graph view

---

## Feature 2: Dynamic Maintenance Checklists

### What It Does
Generates equipment-specific preventative maintenance checklists using AI, turning static diagrams into practical maintenance tools.

### How It Works

**User Experience:**
1. Navigate to the "Graph" tab
2. Click on any equipment node (pump, valve, instrument, etc.)
3. Click the "Generate Maintenance Checklist" button
4. AI generates a comprehensive checklist with:
   - 5-10 maintenance tasks
   - Recommended frequencies (Daily, Weekly, Monthly, etc.)
   - Safety notes for each task
   - General safety warnings
   - Estimated time to complete
5. Export checklist as a text file

**Technical Flow:**
```
Node Click → Store Equipment Info
          → User clicks "Generate Maintenance Checklist"
          → Frontend (MaintenanceChecklist.tsx)
          → Backend API (/api/generate-maintenance-checklist)
          → Gemini AI (maintenance_checklist.py)
          → Returns: tasks, safety_warnings, estimated_time
          → Frontend displays in modal
```

**API Endpoint:**
```
POST /api/generate-maintenance-checklist
{
  "equipment_type": "Centrifugal Pump",
  "equipment_tag": "P-101",
  "equipment_description": "Cooling water circulation pump"
}

Response:
{
  "equipment_type": "Centrifugal Pump",
  "equipment_tag": "P-101",
  "checklist_title": "Preventative Maintenance Checklist - Centrifugal Pump",
  "tasks": [
    {
      "step": 1,
      "task": "Inspect pump casing for leaks, cracks, or corrosion",
      "frequency": "Weekly",
      "safety_notes": "Ensure pump is de-energized and isolated before inspection"
    },
    ...
  ],
  "safety_warnings": [
    "Always follow LOTO procedures before maintenance",
    "Wear appropriate PPE (safety glasses, gloves, hearing protection)",
    ...
  ],
  "estimated_time": "45-60 minutes"
}
```

### Key Features

- **Equipment-Specific**: Tailored to the exact equipment type (pump, valve, instrument, etc.)
- **Industry Standards**: Based on API, ASME, ISA standards
- **Safety-Focused**: Includes LOTO procedures and PPE requirements
- **Frequency Color-Coding**:
  - 🔴 Red = Daily
  - 🟠 Orange = Weekly
  - 🟡 Yellow = Monthly
  - 🔵 Blue = Quarterly
  - 🟢 Green = Annual
- **Export Functionality**: Download as text file for printing/sharing
- **Fallback Mode**: Generic checklist if AI unavailable

### Files Created/Modified

**Backend:**
- `src/api/maintenance_checklist.py` - Gemini AI integration for checklist generation
- `src/api/main.py` - Added `/api/generate-maintenance-checklist` endpoint

**Frontend:**
- `frontend/src/components/MaintenanceChecklist.tsx` - Checklist modal component
- `frontend/src/components/GraphViewer.tsx` - Integrated checklist button

---

## Setup & Configuration

### Prerequisites

Both features use the same Gemini API configuration:

1. **Google API Key**: Set in `.env` file
   ```bash
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

2. **Python Package**: Uses `google-generativeai` (already installed for chatbot/HazOp)
   ```bash
   pip install google-generativeai
   ```

3. **Model**: Uses `gemini-1.5-flash` (same as chatbot)

### API Rate Limits

**Free Tier:**
- 15 requests per minute
- 1,500 requests per day

**Behavior on Quota Exceeded:**
- Graph Filter: Falls back to keyword-based matching
- Maintenance Checklist: Falls back to generic checklist

### Testing

**Start Backend:**
```bash
python -m uvicorn src.api.main:app --reload --port 8000
```

**Start Frontend:**
```bash
cd frontend
npm run dev
```

**Test Graph Filter:**
1. Upload a P&ID
2. Go to Graph tab
3. Try queries like:
   - "Show me all valves"
   - "Find all pumps"
   - "Show cooling water lines"

**Test Maintenance Checklist:**
1. Upload a P&ID
2. Go to Graph tab
3. Click any node
4. Click "Generate Maintenance Checklist"
5. Wait for AI to generate (3-5 seconds)
6. Review and export

---

## Architecture

### Backend Architecture

```
src/api/
├── main.py                      # FastAPI app with new endpoints
├── graph_filter.py              # Natural language graph filtering
├── maintenance_checklist.py     # Maintenance checklist generation
├── hazop_simulator.py           # Existing HazOp simulator
└── gemini_analyzer.py           # Existing chatbot analyzer
```

**Shared Components:**
- All use `google.generativeai` package (OLD API)
- All use `gemini-1.5-flash` model
- All have fallback responses when AI unavailable
- All use singleton pattern for model instances

### Frontend Architecture

```
frontend/src/components/
├── GraphViewer.tsx              # Main graph view (integrated both features)
├── GraphFilter.tsx              # Natural language filter UI
├── MaintenanceChecklist.tsx     # Maintenance checklist modal
├── HazOpSimulator.tsx           # Existing HazOp simulator
└── ChatPanel.tsx                # Existing chatbot
```

**Integration Points:**
- GraphFilter: Panel in top-left of graph view
- MaintenanceChecklist: Modal triggered by button in node info panel
- Both use same topology data structure as HazOp simulator

---

## Prompt Engineering

### Graph Filter Prompt Strategy

**System Persona:**
- P&ID expert with deep knowledge of equipment types
- Understands ISA standards and industrial terminology
- Can interpret spatial relationships (connected to, upstream, downstream)

**Prompt Structure:**
1. User query
2. Complete topology (nodes + edges)
3. Matching rules (type, label, tag, connections)
4. JSON response format

**Example Prompt:**
```
You are a P&ID expert. Filter this graph based on the query.

USER QUERY: "Show me all cooling water lines connected to the furnace"

TOPOLOGY:
- node_1: type=valve, label=CV-101, tag=CV-101
- node_2: type=equipment, label=Furnace, tag=F-100
...

TASK: Return node IDs and edge IDs that match the query.
```

### Maintenance Checklist Prompt Strategy

**System Persona:**
- Senior Maintenance Engineer with 25+ years experience
- Expert in PM programs, LOTO, API/ASME/ISA standards
- Safety-focused and practical

**Prompt Structure:**
1. Equipment information (type, tag, description)
2. Requirements (5-10 tasks, frequencies, safety notes)
3. Industry standards reference
4. JSON response format

**Example Prompt:**
```
You are a Senior Maintenance Engineer. Generate a preventative maintenance checklist.

EQUIPMENT:
Type: Centrifugal Pump
Tag: P-101
Description: Cooling water circulation pump

REQUIREMENTS:
- 5-10 practical tasks
- Recommended frequencies
- Safety notes per task
- Follow API/ASME standards

RESPONSE FORMAT: JSON with tasks, safety_warnings, estimated_time
```

---

## Error Handling

### Backend Errors

**503 Service Unavailable:**
- Cause: Gemini API quota exceeded or service down
- Behavior: Returns fallback response
- User Message: "Using fallback analysis (AI unavailable)"

**500 Internal Server Error:**
- Cause: JSON parsing error, invalid response from Gemini
- Behavior: Returns fallback response
- User Message: "Backend error occurred"

**Configuration Error:**
- Cause: GOOGLE_API_KEY not set
- Behavior: Raises ValueError on initialization
- User Message: "Please set GOOGLE_API_KEY in .env file"

### Frontend Errors

**Network Error:**
- Cause: Backend not running
- User Message: "Cannot connect to backend. Make sure it's running on http://localhost:8000"

**Timeout:**
- Cause: Gemini API slow response
- Behavior: Shows loading spinner, waits for response
- No timeout limit (user can cancel)

---

## Performance Considerations

### Graph Filter Performance

**Optimization:**
- Limits topology to first 100 nodes and 100 edges in prompt
- Uses streaming response (not implemented yet, but possible)
- Caches filter results (not implemented yet)

**Response Time:**
- Typical: 2-4 seconds
- With quota exceeded: <100ms (fallback)

### Maintenance Checklist Performance

**Optimization:**
- Generates on-demand (not pre-cached)
- Uses fast model (gemini-1.5-flash)
- Minimal prompt size

**Response Time:**
- Typical: 3-5 seconds
- With quota exceeded: <100ms (fallback)

---

## Future Enhancements

### Graph Filter
- [ ] Cache filter results for repeated queries
- [ ] Add filter history
- [ ] Support complex queries ("Show me all valves NOT connected to pumps")
- [ ] Add visual path highlighting (show flow from A to B)
- [ ] Export filtered subgraph

### Maintenance Checklist
- [ ] Save checklists to database
- [ ] Track completion status
- [ ] Schedule reminders
- [ ] Export to PDF with formatting
- [ ] Multi-equipment checklists
- [ ] Integration with CMMS systems

### General
- [ ] Add usage analytics
- [ ] Implement caching layer
- [ ] Add user feedback mechanism
- [ ] Support custom prompts/templates
- [ ] Multi-language support

---

## Troubleshooting

### Graph Filter Not Working

**Symptom:** Filter button does nothing or shows error

**Solutions:**
1. Check backend is running: `http://localhost:8000/health`
2. Check GOOGLE_API_KEY in `.env`
3. Check browser console for errors
4. Try fallback mode (should work even without AI)

### Maintenance Checklist Not Generating

**Symptom:** Loading spinner forever or error message

**Solutions:**
1. Check backend logs for errors
2. Verify Gemini API quota not exceeded
3. Check equipment type is valid
4. Try with different equipment node

### Nodes Not Dimming After Filter

**Symptom:** Filter runs but graph doesn't change

**Solutions:**
1. Check matched_node_ids in response (browser console)
2. Verify opacity changes in React DevTools
3. Clear filter and try again
4. Refresh page

---

## API Reference

### POST /api/filter-graph

**Request:**
```typescript
{
  query: string;           // Natural language query
  topology: {
    nodes: Array<{
      id: string;
      type: string;
      data: {
        label: string;
        tag: string;
        description: string;
      };
    }>;
    edges: Array<{
      id: string;
      source: string;
      target: string;
      data: {
        label: string;
      };
    }>;
  };
}
```

**Response:**
```typescript
{
  matched_node_ids: string[];      // IDs of matching nodes
  matched_edge_ids: string[];      // IDs of matching edges
  explanation: string;             // Human-readable explanation
  query: string;                   // Original query
}
```

### POST /api/generate-maintenance-checklist

**Request:**
```typescript
{
  equipment_type: string;          // e.g., "Centrifugal Pump"
  equipment_tag: string;           // e.g., "P-101"
  equipment_description?: string;  // Optional details
}
```

**Response:**
```typescript
{
  equipment_type: string;
  equipment_tag: string;
  checklist_title: string;
  tasks: Array<{
    step: number;
    task: string;
    frequency: string;            // "Daily", "Weekly", etc.
    safety_notes: string;
  }>;
  safety_warnings: string[];
  estimated_time: string;         // e.g., "45-60 minutes"
}
```

---

## Credits

**AI Model:** Google Gemini 1.5 Flash
**Framework:** FastAPI + React + TypeScript
**Graph Library:** React Flow
**Styling:** Tailwind CSS

---

## License

Same as EDAI4 project license.
