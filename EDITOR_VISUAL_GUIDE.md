# P&ID Editor - Visual Guide 🎨

## What You Should See

### 1. Main Navigation Bar
```
┌─────────────────────────────────────────────────────────────────┐
│ EDAI4 Dashboard                                                 │
│                                                                 │
│ [Canvas] [Graph] [Deliverables] [Rules] [Flow] [Editor] [HazOp]│
└─────────────────────────────────────────────────────────────────┘
```

### 2. Editor Tab - View Mode (Default)
```
┌─────────────────────────────────────────────────────────────────┐
│                    [👁 View Mode]                                │
│                                                                 │
│                                                                 │
│                                                                 │
│                    Your P&ID Graph                              │
│                    (Read-Only)                                  │
│                                                                 │
│                                                                 │
│                                                                 │
│                                                                 │
│  [Zoom Controls]                        [Minimap]              │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Editor Tab - Edit Mode (Active)
```
┌─────────────────────────────────────────────────────────────────┐
│         [✏ Edit Mode] [💾 Save] [📤 Load] [🗑 Clear]            │
│                                                                 │
│  ┌──────────┐                                                  │
│  │ 🔧 Comp  │                                                  │
│  │ Library  │                                                  │
│  │          │                                                  │
│  │ 💧 Valve │         Your Editable Canvas                    │
│  │ 🌀 Pump  │                                                  │
│  │ 📊 Instr │         (Drag components here)                  │
│  │ 📦 Tank  │                                                  │
│  │ ⭕ Vessel│                                                  │
│  │ ⚡ Equip │                                                  │
│  │          │                                                  │
│  │ [<] Hide │                                                  │
│  └──────────┘                                                  │
│                                                                 │
│  [Zoom Controls]                        [Minimap]              │
│                                                                 │
│  ℹ Drag components | Connect handles | Delete: Backspace       │
└─────────────────────────────────────────────────────────────────┘
```

### 4. Component Palette (Expanded)
```
┌─────────────────────────────┐
│ 🔧 Component Library        │
│    Drag to canvas           │
├─────────────────────────────┤
│                             │
│ ┌─────────────────────────┐ │
│ │ 💧  Valve               │ │
│ │     Control or isolation│ │
│ └─────────────────────────┘ │
│                             │
│ ┌─────────────────────────┐ │
│ │ 🌀  Pump                │ │
│ │     Centrifugal pump    │ │
│ └─────────────────────────┘ │
│                             │
│ ┌─────────────────────────┐ │
│ │ 📊  Instrument          │ │
│ │     Measurement device  │ │
│ └─────────────────────────┘ │
│                             │
│ ┌─────────────────────────┐ │
│ │ 📦  Tank                │ │
│ │     Storage tank        │ │
│ └─────────────────────────┘ │
│                             │
│ ┌─────────────────────────┐ │
│ │ ⭕  Vessel              │ │
│ │     Pressure vessel     │ │
│ └─────────────────────────┘ │
│                             │
│ ┌─────────────────────────┐ │
│ │ ⚡  Equipment           │ │
│ │     Generic equipment   │ │
│ └─────────────────────────┘ │
│                             │
├─────────────────────────────┤
│ • Drag components to canvas │
│ • Connect nodes with handles│
│ • Delete: Select + Backspace│
└─────────────────────────────┘
```

### 5. Component Palette (Collapsed)
```
┌────┐
│ 🔧 │
├────┤
│ 💧 │
│ 🌀 │
│ 📊 │
│ 📦 │
│ ⭕ │
│ ⚡ │
│    │
│ [>]│
└────┘
```

### 6. Node on Canvas (After Dragging)
```
┌─────────────────┐
│   Valve-1       │  ← Label with auto-incrementing number
│                 │
│   (Cyan color)  │  ← Color based on component type
└─────────────────┘
     ○       ○        ← Connection handles (visible on hover)
```

### 7. Connected Nodes
```
┌─────────────┐              ┌─────────────┐
│   Valve-1   │──────────────│   Pump-2    │
└─────────────┘              └─────────────┘
                  ↑
            Animated edge
         (smooth step style)
```

### 8. Stats Badge (Top Right)
```
┌──────────────────────────────┐
│ • Nodes: 5  |  • Edges: 4   │
└──────────────────────────────┘
```

### 9. Instructions Panel (Bottom Center)
```
┌────────────────────────────────────────────────────────────┐
│ ℹ Drag components from left | Connect by dragging handles │
│   Delete: Select + Backspace                              │
└────────────────────────────────────────────────────────────┘
```

### 10. Minimap (Bottom Right)
```
┌──────────┐
│ ┌──┐     │  ← Miniature view of entire canvas
│ │  │ ┌─┐ │
│ └──┘ └─┘ │  ← Color-coded nodes
│          │
│  [View]  │  ← Current viewport indicator
└──────────┘
```

---

## Color Scheme

### Component Colors
- **Valve**: `#56b6c2` (Cyan)
- **Pump**: `#e5c07b` (Yellow)
- **Instrument**: `#61afef` (Blue)
- **Tank**: `#98c379` (Green)
- **Vessel**: `#98c379` (Green)
- **Equipment**: `#c678dd` (Purple)

### UI Colors
- **Background**: `#0a0e14` (Dark industrial)
- **Panels**: `#1a1f29` (Industrial 800)
- **Borders**: `#3d4556` (Industrial 600)
- **Text**: `#abb2bf` (Industrial 200)
- **Accent Blue**: `#61afef`
- **Accent Cyan**: `#56b6c2`
- **Accent Green**: `#98c379`

---

## Interaction Flow

### Adding a Component
```
1. Click "Edit Mode" button
   ↓
2. Component Palette appears on left
   ↓
3. Click and drag a component (e.g., Valve)
   ↓
4. Drop it on the canvas
   ↓
5. Node appears with auto-generated ID (valve-1001)
   ↓
6. Node is styled with cyan color and label
```

### Connecting Nodes
```
1. Hover over a node
   ↓
2. Connection handles appear (small circles)
   ↓
3. Click and drag from one handle
   ↓
4. Drag to another node's handle
   ↓
5. Release mouse button
   ↓
6. Animated edge is created
```

### Deleting Items
```
1. Click to select a node or edge
   ↓
2. Selected item gets highlighted border
   ↓
3. Press Backspace or Delete key
   ↓
4. Item is removed from canvas
   ↓
5. (If node) Connected edges are also removed
```

### Saving Topology
```
1. Click "Save Topology" button
   ↓
2. Browser download dialog appears
   ↓
3. File is saved as: pid-topology-{timestamp}.json
   ↓
4. File contains nodes, edges, and metadata
```

### Loading Topology
```
1. Click "Load" button
   ↓
2. File picker dialog appears
   ↓
3. Select a .json file
   ↓
4. Topology is loaded onto canvas
   ↓
5. All nodes and edges are restored
```

---

## Button States

### Edit Mode Button
- **View Mode**: Gray background, eye icon
- **Edit Mode**: Blue gradient, edit icon

### Save Button
- **Normal**: Blue gradient
- **Hover**: Slightly larger (scale 1.05)

### Load Button
- **Normal**: Gray with border
- **Hover**: Blue border

### Clear Button
- **Normal**: Gray with red border
- **Hover**: Red background (10% opacity)

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **Backspace** | Delete selected item |
| **Delete** | Delete selected item |
| **Mouse Wheel** | Zoom in/out |
| **Click + Drag** | Pan canvas |
| **Ctrl + Scroll** | Zoom (alternative) |

---

## Mouse Interactions

| Action | Result |
|--------|--------|
| **Click node** | Select node |
| **Click edge** | Select edge |
| **Click canvas** | Deselect all |
| **Drag node** | Move node (edit mode only) |
| **Drag handle** | Create edge (edit mode only) |
| **Drag canvas** | Pan view |
| **Scroll** | Zoom in/out |

---

## Expected Behavior

### ✅ What Should Work
- Dragging components from palette to canvas
- Connecting nodes by dragging handles
- Deleting nodes with Backspace/Delete
- Deleting edges with Backspace/Delete
- Saving topology to JSON file
- Loading topology from JSON file
- Clearing all nodes and edges
- Zooming and panning
- Minimap navigation
- Stats display updates
- Edit mode toggle

### ❌ What Won't Work (By Design)
- Undo/Redo (not implemented)
- Multi-select (not implemented)
- Copy/Paste (not implemented)
- Snap to grid (not implemented)
- Alignment tools (not implemented)
- Node property editing (not implemented)
- Edge label editing (not implemented)

---

## Troubleshooting

### Component Palette Not Showing
- **Check**: Is Edit Mode enabled?
- **Solution**: Click the "Edit Mode" button

### Can't Drag Components
- **Check**: Is Edit Mode enabled?
- **Solution**: Click the "Edit Mode" button

### Can't Connect Nodes
- **Check**: Is Edit Mode enabled?
- **Check**: Are you dragging from a handle?
- **Solution**: Hover over node to see handles

### Delete Key Not Working
- **Check**: Is an item selected?
- **Check**: Is Edit Mode enabled?
- **Solution**: Click item first, then press Delete

### Save Button Not Working
- **Check**: Browser console for errors
- **Solution**: Check if download is blocked by browser

### Load Button Not Working
- **Check**: Is the file a valid JSON?
- **Solution**: Use a file saved by the editor

---

## File Format Example

```json
{
  "nodes": [
    {
      "id": "valve-1001",
      "type": "default",
      "position": {
        "x": 250,
        "y": 150
      },
      "data": {
        "label": "Valve-1",
        "type": "valve"
      },
      "style": {
        "background": "linear-gradient(135deg, #56b6c2 0%, #56b6c2dd 100%)",
        "color": "#ffffff",
        "border": "2px solid #56b6c2",
        "borderRadius": "8px",
        "padding": 10,
        "fontSize": 12,
        "fontWeight": 600,
        "width": 120,
        "height": 60,
        "boxShadow": "0 4px 6px #56b6c240"
      }
    }
  ],
  "edges": [
    {
      "id": "edge-1234567890",
      "source": "valve-1001",
      "target": "pump-1002",
      "type": "smoothstep",
      "animated": true,
      "style": {
        "stroke": "#61afef",
        "strokeWidth": 2
      },
      "markerEnd": {
        "type": "arrowclosed",
        "color": "#61afef"
      }
    }
  ],
  "metadata": {
    "savedAt": "2026-05-05T22:09:15.123Z",
    "nodeCount": 2,
    "edgeCount": 1,
    "version": "1.0.0"
  }
}
```

---

## Performance Notes

- **Recommended**: Up to 100 nodes for smooth performance
- **Maximum**: 500 nodes (may experience lag)
- **Edge Limit**: 1000 edges
- **Canvas Size**: Infinite (virtual canvas)
- **Zoom Range**: 0.1x to 2x

---

## Browser Compatibility

✅ **Supported Browsers**
- Chrome 90+
- Firefox 88+
- Edge 90+
- Safari 14+

❌ **Not Supported**
- Internet Explorer (any version)
- Opera Mini
- Old mobile browsers

---

## Tips & Tricks

1. **Organize Your Diagram**: Use the minimap to navigate large diagrams
2. **Quick Delete**: Select multiple items by clicking them while holding Shift (if multi-select is added)
3. **Zoom to Fit**: Use the fit view button in controls panel
4. **Save Often**: Save your work frequently to avoid data loss
5. **Use Descriptive Names**: Edit node labels to make diagrams clearer (if property editing is added)
6. **Color Coding**: Use component colors to identify equipment types quickly
7. **Edge Routing**: Edges automatically route around nodes
8. **Handle Positioning**: Handles appear on all four sides of nodes

---

## Next Steps

1. **Try It Out**: Open http://localhost:3000 and click the Editor tab
2. **Create a Diagram**: Drag some components and connect them
3. **Save Your Work**: Click Save Topology to download
4. **Load It Back**: Click Load to restore your diagram
5. **Experiment**: Try different component types and connections

---

*Happy Editing! 🎨*
