# P&ID Editor - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Access the Editor

1. **Upload a P&ID** (or skip to start from scratch)
2. **Click "Editor" tab** in the header
3. **Click "Edit Mode"** button (top center)

### Step 2: Add Components

1. **See the palette** on the left side
2. **Drag a component** (e.g., Valve) onto the canvas
3. **Drop it** where you want it
4. **Repeat** to add more components

### Step 3: Connect Components

1. **Hover over a node** - you'll see small circles (handles)
2. **Click and drag** from one handle
3. **Drop on another node's handle**
4. **See the animated connection** appear

### Step 4: Save Your Work

1. **Click "Save Topology"** button (top center)
2. **JSON file downloads** automatically
3. **Done!** Your diagram is saved

---

## 🎯 Quick Actions

### Add Equipment
```
Drag from palette → Drop on canvas
```

### Connect Nodes
```
Click handle → Drag → Drop on another handle
```

### Delete
```
Click to select → Press Backspace or Delete
```

### Save
```
Click "Save Topology" button
```

### Load
```
Click "Load" button → Select JSON file
```

---

## 📦 Available Components

| Icon | Component | Use For |
|------|-----------|---------|
| 💧 | **Valve** | Control or isolation valves |
| 🌪️ | **Pump** | Pumps and compressors |
| 📊 | **Instrument** | Sensors and controllers |
| 📦 | **Tank** | Storage tanks |
| ⭕ | **Vessel** | Pressure vessels, reactors |
| ⚡ | **Equipment** | Generic equipment |

---

## ⌨️ Keyboard Shortcuts

- **Delete**: `Backspace` or `Delete` key
- **Select**: Click on node or edge
- **Pan**: Click and drag canvas
- **Zoom**: Mouse wheel

---

## 💡 Pro Tips

1. **Collapse Palette**: Click chevron to get more canvas space
2. **View Mode**: Switch to view mode to prevent accidental edits
3. **Save Often**: Click save button frequently
4. **Clear All**: Use "Clear" button to start fresh

---

## 🎨 Visual Guide

### Edit Mode ON:
```
┌─────────────────────────────────────────┐
│ [Edit Mode] [Save] [Load] [Clear]      │
│                                         │
│ [Palette]                               │
│ ┌─────┐                                 │
│ │Valve│    [Your Diagram Here]          │
│ │Pump │                                 │
│ │Tank │                                 │
│ └─────┘                                 │
│                                         │
│ Drag → Drop → Connect → Save            │
└─────────────────────────────────────────┘
```

### Connecting Nodes:
```
[Node A] ──drag──> [Node B]
   ○                  ○
   └──────────────────┘
        (creates edge)
```

---

## 🔧 Troubleshooting

**Can't drag components?**
→ Make sure "Edit Mode" is ON

**Can't connect nodes?**
→ Drag from handle (small circle) to another handle

**Save not working?**
→ File downloads to your Downloads folder

**Want to start over?**
→ Click "Clear" button

---

## 📝 Example Workflow

### Building a Simple Process:

1. **Add Tank**
   - Drag "Tank" from palette
   - Drop at top of canvas

2. **Add Valve**
   - Drag "Valve" from palette
   - Drop below tank

3. **Add Pump**
   - Drag "Pump" from palette
   - Drop below valve

4. **Connect Them**
   - Tank → Valve (drag handle to handle)
   - Valve → Pump (drag handle to handle)

5. **Save**
   - Click "Save Topology"
   - File: `pid-topology-{timestamp}.json`

**Done! You've created your first P&ID!** 🎉

---

## 🎓 Next Steps

- **Read Full Guide**: `PID_EDITOR_GUIDE.md`
- **Try HazOp**: Switch to HazOp tab to simulate failures
- **Use Graph Filter**: Filter your custom diagram
- **Generate Checklists**: Click nodes for maintenance tasks

---

## ✅ Checklist

- [ ] Opened Editor tab
- [ ] Enabled Edit Mode
- [ ] Dragged a component
- [ ] Connected two nodes
- [ ] Deleted something
- [ ] Saved topology
- [ ] Loaded topology

**All checked? You're a P&ID Editor pro!** 🚀
