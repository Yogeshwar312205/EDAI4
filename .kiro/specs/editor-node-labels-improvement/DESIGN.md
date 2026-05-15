# Technical Design: Editor Node Labels Improvement

**Feature ID:** editor-node-labels-improvement  
**Status:** Implementation  
**Created:** 2026-05-15

---

## 1. Architecture Overview

### 1.1 Component Structure

```
EditableGraphViewer (existing)
├─ ComponentPalette (existing)
├─ ReactFlow (existing)
│  ├─ EnhancedNode (NEW - custom node component)
│  │  ├─ NodeIcon (NEW)
│  │  ├─ NodeLabel (NEW)
│  │  └─ NodeTooltip (NEW)
│  ├─ Background
│  ├─ Controls
│  └─ MiniMap
└─ Node Info Panel (enhanced)
```

### 1.2 New Components

1. **EnhancedNode.tsx** - Custom ReactFlow node with improved labels
2. **NodeIcon.tsx** - Icon component for node types
3. **NodeLabel.tsx** - Multi-line label component
4. **NodeTooltip.tsx** - Hover tooltip component
5. **nodeUtils.ts** - Utility functions for ISA tags and node styling

---

## 2. Implementation Plan

### Phase 1: Core Components (Day 1-2)
- Create EnhancedNode component
- Create NodeIcon component
- Create NodeLabel component
- Add icon mapping utilities

### Phase 2: Interactivity (Day 3)
- Add NodeTooltip component
- Implement hover behavior
- Enhance selection highlighting

### Phase 3: Integration (Day 4)
- Update EditableGraphViewer to use EnhancedNode
- Update node creation logic
- Add ISA tag validation

### Phase 4: Polish (Day 5)
- Add animations
- Optimize performance
- Test with 100+ nodes

---

## 3. Data Structures

### Node Data Interface
```typescript
interface EnhancedNodeData {
  label: string;           // Display label
  type: string;            // Component type (instrument, valve, pump, equipment)
  tag?: string;            // ISA tag (FIC-101, PT-205, etc.)
  description?: string;    // Optional description
  status?: 'normal' | 'warning' | 'danger' | 'critical';
}
```

### Icon Mapping
```typescript
const NODE_ICONS = {
  instrument: Gauge,
  valve: Wrench,
  pump: Cog,
  equipment: Package,
  other: Zap,
};
```

---

## 4. Styling System

### Color Scheme (Existing)
```typescript
const NODE_COLORS = {
  instrument: '#61afef',
  valve: '#56b6c2',
  pump: '#e5c07b',
  equipment: '#98c379',
  other: '#c678dd',
};
```

### Node Dimensions
```typescript
const NODE_DIMENSIONS = {
  minWidth: 140,
  minHeight: 80,
  padding: 12,
  borderRadius: 8,
  borderWidth: 2,
};
```

---

## 5. File Changes

### New Files
- `frontend/src/components/nodes/EnhancedNode.tsx`
- `frontend/src/components/nodes/NodeIcon.tsx`
- `frontend/src/components/nodes/NodeLabel.tsx`
- `frontend/src/components/nodes/NodeTooltip.tsx`
- `frontend/src/utils/nodeUtils.ts`

### Modified Files
- `frontend/src/components/EditableGraphViewer.tsx`

---

**Status:** Ready for Implementation
