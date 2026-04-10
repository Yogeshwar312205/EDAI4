# EDAI4 Frontend - Architecture & Implementation Details

## 🏗️ Architectural Overview

This document provides deep technical insights into the frontend architecture, explaining design decisions, implementation patterns, and the critical cross-linking mechanism.

## 📐 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Browser (Client)                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                   React Application                     │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │ │
│  │  │ Interactive  │  │  Data Table  │  │    Graph     │ │ │
│  │  │   Canvas     │  │  (TanStack)  │  │ (React Flow) │ │ │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │ │
│  │         │                  │                  │         │ │
│  │         └──────────────────┼──────────────────┘         │ │
│  │                            │                            │ │
│  │                   ┌────────▼────────┐                   │ │
│  │                   │  Zustand Store  │                   │ │
│  │                   │  - selectedNode │                   │ │
│  │                   │  - hoveredNode  │                   │ │
│  │                   │  - activeView   │                   │ │
│  │                   └────────┬────────┘                   │ │
│  │                            │                            │ │
│  │                   ┌────────▼────────┐                   │ │
│  │                   │  React Query    │                   │ │
│  │                   │  (API Cache)    │                   │ │
│  │                   └────────┬────────┘                   │ │
│  └────────────────────────────┼────────────────────────────┘ │
└────────────────────────────────┼────────────────────────────┘
                                 │ HTTP/JSON
                    ┌────────────▼────────────┐
                    │   FastAPI Backend       │
                    │   (localhost:8000)      │
                    │  - /process             │
                    │  - /graph               │
                    │  - /query               │
                    └─────────────────────────┘
```

## 🎯 Feature 1: Interactive Canvas - Deep Dive

### Technology Choice: React-Konva

**Why React-Konva over alternatives?**

| Alternative | Pros | Cons | Verdict |
|-------------|------|------|---------|
| HTML Canvas | Native, fast | Manual state management, no React integration | ❌ Too low-level |
| SVG | Scalable, DOM-based | Poor performance with many elements | ❌ Slow for 100+ boxes |
| Fabric.js | Rich features | Large bundle, complex API | ❌ Overkill |
| **React-Konva** | React integration, hardware-accelerated, smooth pan/zoom | Learning curve | ✅ Perfect fit |

### Implementation Architecture

```typescript
// Component Structure
InteractiveCanvas
├── Stage (Konva root)
│   ├── Layer (rendering layer)
│   │   ├── Image (P&ID background)
│   │   └── Group[] (for each detection)
│   │       ├── Rect (bounding box)
│   │       ├── Text (tag label)
│   │       └── Group (hover tooltip)
│   │           ├── Rect (tooltip background)
│   │           └── Text[] (tooltip content)
```

### Pan/Zoom Implementation

**Zoom Logic** (Mouse Wheel):

```typescript
const handleWheel = (e: any) => {
  e.evt.preventDefault();
  
  const stage = stageRef.current;
  const oldScale = stage.scaleX();
  const pointer = stage.getPointerPosition();
  
  // Calculate new scale
  const scaleBy = 1.1;
  const newScale = e.evt.deltaY < 0 
    ? oldScale * scaleBy      // Zoom in
    : oldScale / scaleBy;     // Zoom out
  
  // Clamp between 0.1x and 10x
  const clampedScale = Math.max(0.1, Math.min(10, newScale));
  
  // Calculate new position to zoom towards mouse pointer
  const mousePointTo = {
    x: (pointer.x - stage.x()) / oldScale,
    y: (pointer.y - stage.y()) / oldScale,
  };
  
  const newPos = {
    x: pointer.x - mousePointTo.x * clampedScale,
    y: pointer.y - mousePointTo.y * clampedScale,
  };
  
  setStageScale(clampedScale);
  setStagePos(newPos);
};
```

**Pan Logic** (Drag):

```typescript
<Stage
  draggable
  onDragEnd={(e) => {
    setStagePos({ x: e.target.x(), y: e.target.y() });
  }}
/>
```

### Zoom-to-Detection (Critical Feature)

**Triggered by table row click**:

```typescript
useEffect(() => {
  if (selectedNodeId && stageRef.current) {
    const index = parseInt(selectedNodeId.replace('node_', ''));
    const detection = detections[index];
    
    if (detection) {
      const bbox = detection.bbox;
      
      // Calculate center of bounding box
      const centerX = (bbox.x1 + bbox.x2) / 2;
      const centerY = (bbox.y1 + bbox.y2) / 2;
      
      // Zoom to 2x and center on detection
      const newScale = 2;
      const newPos = {
        x: stageSize.width / 2 - centerX * newScale,
        y: stageSize.height / 2 - centerY * newScale,
      };
      
      // Smooth animation using Konva's tween
      const stage = stageRef.current;
      stage.to({
        x: newPos.x,
        y: newPos.y,
        scaleX: newScale,
        scaleY: newScale,
        duration: 0.5,
        easing: (t: number) => t * (2 - t), // easeOutQuad
      });
      
      setStageScale(newScale);
      setStagePos(newPos);
    }
  }
}, [selectedNodeId, detections, stageSize]);
```

**Key Points**:
- Listens to `selectedNodeId` from Zustand store
- Calculates center point of bounding box
- Uses Konva's `.to()` for smooth animation
- Custom easing function for natural feel
- Updates local state to keep UI in sync

### Hover Tooltips

**Implementation**:

```typescript
{isHovered && (
  <Group>
    {/* Tooltip Background */}
    <Rect
      x={bbox.x2 + 10}
      y={bbox.y1}
      width={200}
      height={80}
      fill="#1a1f29"
      stroke={color}
      strokeWidth={2}
      cornerRadius={8}
      shadowBlur={15}
      shadowColor={color}
      opacity={0.95}
    />
    {/* Tooltip Text */}
    <Text x={bbox.x2 + 20} y={bbox.y1 + 10} text={`Tag: ${tag}`} />
    <Text x={bbox.x2 + 20} y={bbox.y1 + 30} text={`Class: ${className}`} />
    <Text x={bbox.x2 + 20} y={bbox.y1 + 50} text={`Confidence: ${conf}%`} />
  </Group>
)}
```

**Performance Optimization**:
- Tooltips only render when `isHovered` is true
- Uses Konva's layer caching for static elements
- Minimal re-renders via React.memo (if needed)

## 🎯 Feature 2: Data Table - Deep Dive

### Technology Choice: TanStack Table v8

**Why TanStack Table?**

| Feature | TanStack Table | Alternatives |
|---------|----------------|--------------|
| Sorting | ✅ Built-in | Material-UI: ✅ / AG-Grid: ✅ |
| Filtering | ✅ Built-in | Material-UI: ⚠️ Manual / AG-Grid: ✅ |
| Virtual Scrolling | ✅ Built-in | Material-UI: ❌ / AG-Grid: ✅ |
| Customization | ✅ Headless | Material-UI: ⚠️ Styled / AG-Grid: ⚠️ Complex |
| Bundle Size | ✅ 14KB | Material-UI: 300KB+ / AG-Grid: 500KB+ |
| TypeScript | ✅ Excellent | Material-UI: ✅ / AG-Grid: ✅ |

**Verdict**: TanStack Table wins on flexibility, size, and performance.

### Column Definition

```typescript
const columns = useMemo(() => [
  // Index column
  columnHelper.accessor('index', {
    header: '#',
    cell: (info) => info.getValue() + 1,
    size: 50,
  }),
  
  // Tag column with sorting
  columnHelper.accessor('tag', {
    header: ({ column }) => (
      <button onClick={() => column.toggleSorting()}>
        Tag <ArrowUpDown />
      </button>
    ),
    cell: (info) => {
      const tag = info.getValue();
      return tag || <span className="italic">N/A</span>;
    },
    size: 120,
  }),
  
  // Class column with color badges
  columnHelper.accessor('class_name', {
    header: ({ column }) => (
      <button onClick={() => column.toggleSorting()}>
        Class <ArrowUpDown />
      </button>
    ),
    cell: (info) => {
      const className = info.getValue();
      const color = getClassColor(className);
      return (
        <span
          className="px-2 py-1 rounded text-xs"
          style={{ backgroundColor: `${color}20`, color }}
        >
          {className}
        </span>
      );
    },
    size: 180,
  }),
  
  // Confidence column with progress bar
  columnHelper.accessor('confidence', {
    header: ({ column }) => (
      <button onClick={() => column.toggleSorting()}>
        Confidence <ArrowUpDown />
      </button>
    ),
    cell: (info) => {
      const confidence = info.getValue();
      const percentage = (confidence * 100).toFixed(1);
      const color = confidence > 0.8 ? '#98c379' : 
                    confidence > 0.5 ? '#e5c07b' : '#e06c75';
      return (
        <div className="flex items-center gap-2">
          <div className="flex-1 bg-industrial-700 rounded-full h-2">
            <div
              className="h-full rounded-full"
              style={{ width: `${percentage}%`, backgroundColor: color }}
            />
          </div>
          <span style={{ color }}>{percentage}%</span>
        </div>
      );
    },
    size: 150,
  }),
], []);
```

### Row Click Handler (Critical)

```typescript
const handleRowClick = (rowId: string) => {
  setSelectedNodeId(rowId);  // Update Zustand store
  setActiveView('canvas');   // Switch to canvas view
  
  // Canvas component reacts to selectedNodeId change
  // and zooms to the detection automatically
};

// In table body
<tr
  onClick={() => handleRowClick(row.original.id)}
  className={`
    cursor-pointer transition-all
    hover:bg-industrial-700/50
    ${isSelected ? 'bg-accent-blue/20 border-l-4 border-accent-blue' : ''}
  `}
>
  {/* cells */}
</tr>
```

**Flow**:
1. User clicks row
2. `handleRowClick` called with `node_5`
3. Zustand store updated: `selectedNodeId = 'node_5'`
4. Canvas `useEffect` triggers
5. Canvas zooms to detection #5
6. Row highlighted with blue border

### Search and Filter

```typescript
const [globalFilter, setGlobalFilter] = useState('');

// Global search across all columns
<input
  value={globalFilter ?? ''}
  onChange={(e) => setGlobalFilter(e.target.value)}
  placeholder="Search tags, classes..."
/>

// TanStack Table handles filtering automatically
const table = useReactTable({
  data,
  columns,
  state: { globalFilter },
  onGlobalFilterChange: setGlobalFilter,
  getFilteredRowModel: getFilteredRowModel(),
});
```

## 🎯 Feature 3: Graph Viewer - Deep Dive

### Technology Choice: React Flow

**Why React Flow?**

| Feature | React Flow | Alternatives |
|---------|------------|--------------|
| Physics Layout | ✅ Built-in | Cytoscape: ✅ / D3: ⚠️ Manual |
| Drag & Drop | ✅ Built-in | Cytoscape: ✅ / D3: ⚠️ Manual |
| React Integration | ✅ Native | Cytoscape: ⚠️ Wrapper / D3: ❌ |
| Customization | ✅ Excellent | Cytoscape: ⚠️ Limited / D3: ✅ |
| Performance | ✅ 1000+ nodes | Cytoscape: ✅ / D3: ⚠️ Depends |
| Bundle Size | ✅ 50KB | Cytoscape: 200KB+ / D3: 100KB+ |

**Verdict**: React Flow is the modern choice for React apps.

### Node Transformation

**Backend format**:
```json
{
  "id": "node_1",
  "type": "instrument",
  "tag": "FT-101",
  "x": 100,
  "y": 150
}
```

**React Flow format**:
```typescript
const node: Node = {
  id: "node_1",
  type: "default",  // 'default' = circle, 'input' = rectangle
  position: { x: 200, y: 300 },  // Scaled 2x for visibility
  data: {
    label: "FT-101",
    type: "instrument",
  },
  style: {
    background: "#61afef",  // Blue for instruments
    color: "#0a0e14",
    border: "2px solid #61afef",
    borderRadius: "50%",  // Circle for instruments
    width: 80,
    height: 80,
    boxShadow: "0 0 20px #61afef40",
  },
};
```

### Node Styling Logic

```typescript
const getNodeType = (type: string) => {
  if (type.includes('instrument') || type.includes('valve')) {
    return { shape: 'default' };  // Circle
  }
  return { shape: 'input' };  // Rectangle
};

const getNodeColor = (type: string): string => {
  if (type.includes('instrument')) return '#61afef';  // Blue
  if (type.includes('valve')) return '#56b6c2';       // Cyan
  if (type.includes('equipment')) return '#98c379';   // Green
  if (type.includes('pump')) return '#e5c07b';        // Yellow
  return '#c678dd';  // Purple (other)
};
```

### Edge Styling

```typescript
const edge: Edge = {
  id: "edge-0",
  source: "node_1",
  target: "node_2",
  type: ConnectionLineType.Bezier,  // Smooth curves
  animated: edge.type === 'flow',   // Animate flow edges
  style: {
    stroke: getEdgeColor(edge.type),
    strokeWidth: 2,
  },
  markerEnd: {
    type: MarkerType.ArrowClosed,
    color: getEdgeColor(edge.type),
  },
  label: edge.type,
};
```

### Selection Synchronization

```typescript
// Highlight selected node
useEffect(() => {
  setNodes((nds) =>
    nds.map((node) => ({
      ...node,
      style: {
        ...node.style,
        boxShadow: selectedNodeId === node.id
          ? `0 0 30px ${color}`      // Strong glow
          : `0 0 20px ${color}40`,   // Subtle glow
        transform: selectedNodeId === node.id
          ? 'scale(1.1)'             // Scale up
          : 'scale(1)',
        transition: 'all 0.3s ease',
      },
    }))
  );
}, [selectedNodeId, setNodes]);
```

## 🔄 State Management - Zustand Deep Dive

### Why Zustand over Redux/Context?

| Feature | Zustand | Redux | Context API |
|---------|---------|-------|-------------|
| Boilerplate | ✅ Minimal | ❌ Verbose | ✅ Minimal |
| Performance | ✅ Excellent | ✅ Good | ⚠️ Re-renders |
| DevTools | ✅ Yes | ✅ Yes | ❌ No |
| Learning Curve | ✅ Easy | ❌ Steep | ✅ Easy |
| Bundle Size | ✅ 1KB | ⚠️ 10KB+ | ✅ 0KB (built-in) |

**Verdict**: Zustand is perfect for this use case.

### Store Structure

```typescript
interface AppState {
  // Data
  uploadedImage: string | null;
  processingResult: ProcessingResult | null;
  graphData: GraphData | null;
  
  // UI State (critical for cross-linking)
  selectedNodeId: string | null;  // 'node_5'
  hoveredNodeId: string | null;   // 'node_3'
  activeView: 'canvas' | 'graph';
  
  // Actions
  setSelectedNodeId: (id: string | null) => void;
  setHoveredNodeId: (id: string | null) => void;
  // ...
}
```

### Usage in Components

```typescript
// DataTable.tsx
const { setSelectedNodeId } = useAppStore();

const handleRowClick = (id: string) => {
  setSelectedNodeId(id);  // Updates global state
};

// InteractiveCanvas.tsx
const { selectedNodeId } = useAppStore();

useEffect(() => {
  if (selectedNodeId) {
    // Zoom to detection
  }
}, [selectedNodeId]);  // Reacts to state change
```

### Performance Optimization

Zustand uses shallow equality by default:

```typescript
// Only re-renders when selectedNodeId changes
const selectedNodeId = useAppStore((state) => state.selectedNodeId);

// Re-renders on any state change (avoid!)
const state = useAppStore();
```

## 🎨 Styling Architecture

### Tailwind CSS Configuration

**Custom Theme**:

```javascript
// tailwind.config.js
theme: {
  extend: {
    colors: {
      industrial: {
        950: '#0a0e14',  // Darkest - background
        900: '#0f1419',  // Dark - cards
        800: '#1a1f29',  // Medium - elevated
        700: '#252b38',  // Light - borders
        600: '#3d4556',  // Lighter - hover
        500: '#5c6370',  // Text secondary
        400: '#828997',  // Text tertiary
        300: '#abb2bf',  // Text primary
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
    },
    boxShadow: {
      'glow-blue': '0 0 20px rgba(97, 175, 239, 0.3)',
      'glow-cyan': '0 0 20px rgba(86, 182, 194, 0.3)',
    },
  },
}
```

### Component Styling Pattern

```typescript
// Consistent pattern across components
<div className="
  bg-industrial-800           // Background
  border border-industrial-600  // Border
  rounded-lg                  // Rounded corners
  p-4                         // Padding
  hover:border-accent-blue    // Hover effect
  transition-colors           // Smooth transition
">
  <span className="
    text-industrial-300       // Text color
    font-mono                 // Monospace font
    text-sm                   // Size
  ">
    Content
  </span>
</div>
```

## 🚀 Performance Optimizations

### 1. Canvas Rendering

- **Layer Caching**: Konva caches static layers
- **Selective Rendering**: Only render visible bounding boxes
- **Debounced Zoom**: Throttle zoom events to 60 FPS

### 2. Table Rendering

- **Virtual Scrolling**: Only render visible rows
- **Memoized Columns**: `useMemo` prevents re-creation
- **Optimized Filters**: TanStack Table's built-in optimization

### 3. Graph Rendering

- **Node Limit**: Warn if > 500 nodes
- **Edge Simplification**: Use straight lines for > 100 edges
- **Lazy Loading**: Load graph data on tab switch

### 4. State Updates

- **Shallow Equality**: Zustand's default behavior
- **Selective Subscriptions**: Only subscribe to needed state
- **Batched Updates**: React 18's automatic batching

## 📊 Bundle Size Analysis

```
Production Build:
├── vendor.js      (React, React-Konva, React Flow)  ~250 KB
├── main.js        (App code)                        ~80 KB
├── styles.css     (Tailwind)                        ~15 KB
└── Total (gzipped)                                  ~120 KB
```

**Optimization Strategies**:
- Code splitting by route (if multi-page)
- Lazy load graph viewer
- Tree-shake unused Tailwind classes
- Use CDN for large libraries

## 🔒 Type Safety

### API Type Definitions

```typescript
// src/types/api.ts
export interface DetectionResult {
  class_name: string;
  confidence: number;
  bbox: BoundingBox;
  tag: string | null;
}

// Ensures type safety across components
const detection: DetectionResult = processingResult.detections[0];
//    ^^^^^^^^^ TypeScript validates this
```

### Component Props

```typescript
interface InteractiveCanvasProps {
  imageUrl: string;
  detections: DetectionResult[];  // Type-safe
  imageSize: { width: number; height: number };
}

// TypeScript catches errors at compile time
<InteractiveCanvas
  imageUrl={url}
  detections={data.detections}  // ✅ Correct type
  imageSize={{ width: 1200, height: 800 }}
/>
```

## 🎉 Summary

This frontend architecture delivers:

1. **Interactive Canvas**: React-Konva with smooth pan/zoom and hover tooltips
2. **Cross-Linked Table**: TanStack Table with canvas synchronization via Zustand
3. **Graph Visualization**: React Flow with physics-based layout
4. **Dark Industrial Theme**: Custom Tailwind CSS configuration
5. **Type Safety**: Full TypeScript coverage
6. **Performance**: Optimized rendering and state management
7. **Modularity**: Clean component separation and reusability

**The critical feature** - table click → canvas zoom - is implemented through Zustand's reactive state management, ensuring seamless cross-component communication with minimal boilerplate.
