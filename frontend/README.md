# EDAI4 Frontend - Dark Industrial Dashboard

Modern, interactive frontend for the EDAI4 Hybrid Perception Pipeline featuring pan/zoom canvas, cross-linked data tables, and physics-based graph visualization.

## 🎨 Tech Stack

### Core Framework
- **React 18** with TypeScript - Type-safe component architecture
- **Vite** - Lightning-fast build tool and dev server
- **Tailwind CSS** - Utility-first styling with custom dark industrial theme

### Feature Libraries
1. **Interactive Canvas**: React-Konva + Konva.js
   - Hardware-accelerated canvas rendering
   - Smooth pan/zoom with mouse wheel
   - Real-time bounding box overlays
   - Hover tooltips with detection metadata

2. **Data Table**: TanStack Table v8
   - Sorting, filtering, global search
   - Virtual scrolling for large datasets
   - Row selection with canvas synchronization
   - Custom cell renderers

3. **Graph Visualization**: React Flow
   - Physics-based node layout
   - Draggable, interactive nodes
   - Bezier curve edges with animations
   - Mini-map and zoom controls

### State Management
- **Zustand** - Lightweight state management
  - Cross-component state synchronization
  - Table click → Canvas zoom coordination
  - Selected node highlighting across views

### API Integration
- **Axios** - HTTP client for FastAPI backend
- **React Query** - Server state management with caching

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm/yarn/pnpm
- EDAI4 FastAPI backend running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

Opens at `http://localhost:3000` with hot reload enabled.

### Production Build

```bash
npm run build
npm run preview
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── InteractiveCanvas.tsx    # Feature 1: Pan/Zoom Canvas
│   │   ├── DataTable.tsx            # Feature 2: Cross-Linked Table
│   │   ├── GraphViewer.tsx          # Feature 3: Topology Graph
│   │   └── FileUpload.tsx           # Drag & Drop Upload
│   ├── store/
│   │   └── useAppStore.ts           # Zustand State Management
│   ├── lib/
│   │   └── api.ts                   # API Client
│   ├── types/
│   │   └── api.ts                   # TypeScript Definitions
│   ├── App.tsx                      # Main Application
│   ├── main.tsx                     # Entry Point
│   └── index.css                    # Global Styles
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## 🎯 Core Features

### 1. Interactive Canvas (The "Wow" Factor)

**Implementation**: React-Konva with custom pan/zoom logic

**Features**:
- Renders uploaded P&ID image on high-performance canvas
- Draws bounding boxes from backend JSON (`x1, y1, x2, y2`)
- Fluid pan (drag) and zoom (mouse wheel) mechanics
- Hover tooltips showing tag, class, confidence
- Click to select with highlight effect
- Smooth animations for zoom-to-detection

**State Synchronization**:
```typescript
// When table row clicked, canvas auto-zooms to detection
useEffect(() => {
  if (selectedNodeId) {
    const detection = getDetectionById(selectedNodeId);
    // Calculate center point
    const centerX = (bbox.x1 + bbox.x2) / 2;
    const centerY = (bbox.y1 + bbox.y2) / 2;
    // Animate zoom to 2x centered on detection
    stage.to({ x: newX, y: newY, scale: 2, duration: 0.5 });
  }
}, [selectedNodeId]);
```

### 2. Cross-Linked Data Table

**Implementation**: TanStack Table v8 with custom styling

**Features**:
- Displays all detections in sortable, filterable table
- Global search across tags and classes
- Click row → triggers `setSelectedNodeId()` → canvas zooms
- Visual feedback: selected row highlighted with accent border
- Confidence bars with color coding (green/yellow/red)
- Category badges with class-specific colors
- Footer stats (instruments, valves, equipment counts)

**Critical State Management**:
```typescript
const handleRowClick = (rowId: string) => {
  setSelectedNodeId(rowId);  // Updates Zustand store
  setActiveView('canvas');   // Switches to canvas view
  // Canvas component reacts to selectedNodeId change
};
```

### 3. Topology/Knowledge Graph Viewer

**Implementation**: React Flow with custom node styling

**Features**:
- Renders nodes and edges from `/graph` endpoint
- Physics-based layout (draggable nodes)
- Node shapes: circles (instruments/valves), rectangles (equipment)
- Color-coded by type (blue, cyan, green, yellow, purple)
- Animated edges for flow connections
- Mini-map for navigation
- Zoom controls and background grid
- Click node → syncs with table selection

**Node Styling**:
```typescript
const nodeStyle = {
  background: getNodeColor(node.type),
  border: `2px solid ${color}`,
  borderRadius: nodeType === 'instrument' ? '50%' : '8px',
  boxShadow: `0 0 20px ${color}40`,
  // Highlight selected node
  transform: isSelected ? 'scale(1.1)' : 'scale(1)',
};
```

## 🎨 Dark Industrial Theme

Custom Tailwind color palette:

```javascript
colors: {
  industrial: {
    950: '#0a0e14',  // Background
    900: '#0f1419',  // Cards
    800: '#1a1f29',  // Elevated surfaces
    700: '#252b38',  // Borders
    600: '#3d4556',  // Hover states
  },
  accent: {
    blue: '#61afef',    // Instruments
    cyan: '#56b6c2',    // Valves
    green: '#98c379',   // Equipment
    yellow: '#e5c07b',  // Pumps
    orange: '#d19a66',
    red: '#e06c75',
    purple: '#c678dd',  // Other
  },
}
```

## 🔌 API Integration

### Backend Contract

The frontend expects this JSON structure from `/process`:

```typescript
interface ProcessingResult {
  image_name: string;
  processing_time_ms: number;
  layer1_detections: number;
  layer2_instruments: number;
  layer3_nodes: number;
  layer3_edges: number;
  detections: Array<{
    class_name: string;
    confidence: number;
    bbox: { x1: number; y1: number; x2: number; y2: number };
    tag: string | null;
  }>;
  graph_summary: Record<string, any>;
}
```

### API Endpoints Used

- `POST /process` - Upload and process P&ID image
- `GET /graph` - Fetch topology graph data
- `POST /query` - RAG natural language queries
- `GET /health` - Backend health check

### Proxy Configuration

Vite dev server proxies `/api/*` to `http://localhost:8000`:

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, ''),
    },
  },
}
```

## 🧩 State Management Architecture

### Zustand Store (`useAppStore`)

**Centralized State**:
```typescript
interface AppState {
  uploadedImage: string | null;
  processingResult: ProcessingResult | null;
  graphData: GraphData | null;
  selectedNodeId: string | null;  // Critical for cross-linking
  hoveredNodeId: string | null;
  activeView: 'canvas' | 'graph';
}
```

**Cross-Component Flow**:
1. User clicks table row
2. `DataTable` calls `setSelectedNodeId('node_5')`
3. Zustand updates global state
4. `InteractiveCanvas` reacts via `useEffect`
5. Canvas animates zoom to detection #5

## 🎭 Component Interactions

```
┌─────────────────────────────────────────────────┐
│                   App.tsx                        │
│  ┌──────────────┐  ┌──────────────┐             │
│  │ FileUpload   │  │ View Tabs    │             │
│  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼────────┐          ┌───────▼────────┐
│ Canvas View    │          │ Graph View     │
│ ┌────────────┐ │          │ ┌────────────┐ │
│ │ Interactive│ │          │ │ GraphViewer│ │
│ │ Canvas     │ │          │ │            │ │
│ └────────────┘ │          │ └────────────┘ │
│                │          │                │
│ ┌────────────┐ │          │ ┌────────────┐ │
│ │ DataTable  │ │          │ │ DataTable  │ │
│ └────────────┘ │          │ └────────────┘ │
└────────────────┘          └────────────────┘
        │                           │
        └─────────────┬─────────────┘
                      │
              ┌───────▼────────┐
              │  Zustand Store │
              │  selectedNodeId│
              │  hoveredNodeId │
              └────────────────┘
```

## 🔧 Development Tips

### Hot Reload
Vite provides instant HMR. Changes to components reflect immediately without full page reload.

### Type Safety
All API responses are typed. TypeScript will catch mismatches:

```typescript
// ✅ Type-safe
const detection: DetectionResult = processingResult.detections[0];

// ❌ TypeScript error
const invalid = processingResult.nonexistent_field;
```

### Debugging State
Install React DevTools and Zustand DevTools:

```typescript
// Add to useAppStore.ts for debugging
import { devtools } from 'zustand/middleware';

export const useAppStore = create(
  devtools((set, get) => ({ /* ... */ }))
);
```

### Performance
- Canvas uses Konva's layer caching for smooth rendering
- Table uses virtual scrolling for 1000+ rows
- React Flow optimizes node rendering automatically

## 🎨 Customization

### Change Theme Colors

Edit `tailwind.config.js`:

```javascript
colors: {
  industrial: {
    950: '#your-color',  // Background
    // ...
  },
}
```

### Adjust Canvas Zoom Limits

Edit `InteractiveCanvas.tsx`:

```typescript
const clampedScale = Math.max(0.1, Math.min(10, newScale));
//                            ^^^           ^^
//                            min          max
```

### Modify Table Columns

Edit `DataTable.tsx` columns array:

```typescript
columnHelper.accessor('your_field', {
  header: 'Your Header',
  cell: (info) => <YourCustomCell value={info.getValue()} />,
});
```

## 🐛 Troubleshooting

### Canvas Not Rendering
- Check browser console for image load errors
- Verify `uploadedImage` state is set correctly
- Ensure image URL is accessible

### Table-Canvas Sync Not Working
- Verify `selectedNodeId` is updating in Zustand store
- Check `useEffect` dependencies in `InteractiveCanvas`
- Ensure detection IDs match format `node_${index}`

### Graph Not Loading
- Check `/graph` endpoint returns valid data
- Verify `graphData` state is populated
- Check browser console for React Flow errors

### Backend Connection Failed
- Ensure FastAPI server is running on port 8000
- Check Vite proxy configuration
- Verify CORS is enabled in FastAPI

## 📦 Build for Production

```bash
npm run build
```

Output in `dist/` folder. Serve with:

```bash
npm run preview
# or
npx serve dist
```

For deployment, serve `dist/` with Nginx, Apache, or CDN.

## 🚀 Deployment Options

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

### Nginx
```nginx
server {
  listen 80;
  root /var/www/edai4-frontend/dist;
  
  location / {
    try_files $uri $uri/ /index.html;
  }
  
  location /api {
    proxy_pass http://localhost:8000;
  }
}
```

## 📚 Further Reading

- [React-Konva Docs](https://konvajs.org/docs/react/)
- [TanStack Table](https://tanstack.com/table/v8)
- [React Flow](https://reactflow.dev/)
- [Zustand](https://github.com/pmndrs/zustand)
- [Tailwind CSS](https://tailwindcss.com/)

## 🎉 Summary

This frontend delivers:
- ✅ Interactive pan/zoom canvas with bounding boxes
- ✅ Cross-linked data table with canvas synchronization
- ✅ Physics-based topology graph visualization
- ✅ Dark industrial theme with modern UI/UX
- ✅ Type-safe TypeScript architecture
- ✅ Modular, maintainable component structure

**The critical feature** - table click → canvas zoom - is implemented via Zustand state management, ensuring seamless cross-component communication.
