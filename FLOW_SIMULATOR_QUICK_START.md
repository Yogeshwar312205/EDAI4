# 🚀 Flow Simulator - Quick Start Guide

**Get started with the Interactive Flow Simulator in 5 minutes!**

---

## 📋 Prerequisites

- ✅ Backend running on `http://localhost:8000`
- ✅ Frontend running on `http://localhost:5173`
- ✅ P&ID image uploaded and processed

---

## 🎯 Quick Start (3 Steps)

### Step 1: Upload P&ID
1. Open the application
2. Click "Upload P&ID Image"
3. Wait for processing to complete
4. You should see the Canvas view with detected components

### Step 2: Configure Flow Simulation
1. Click the **"Flow Sim"** tab at the top
2. Select a **source node** from the dropdown (e.g., "Tank-101")
3. Toggle valves by clicking them:
   - **Green = OPEN** ✅
   - **Red = CLOSED** 🔴
4. Simulation runs automatically!

### Step 3: View Animated Flow
1. Click the **"Graph"** tab at the top
2. See the magic happen:
   - 🟢 **Green animated edges** = Active flow
   - 🟢 **Green glowing nodes** = Nodes in flow path
   - 🔴 **Red glowing nodes** = Blocked valves
   - ⚫ **Dimmed nodes/edges** = Inactive (no flow)
3. Look for the **"Flow Simulation Active"** badge at the top

---

## 🎨 Visual Guide

### Flow Sim Tab
```
┌─────────────────────────────────────────────────────┐
│ 🌊 Interactive Flow Simulator              [Reset] │
├─────────────────────────────────────────────────────┤
│ Flow Source Node                                    │
│ [Tank-101                                       ▼]  │
│                                                     │
│ Valve Controls (3 valves)                          │
│ ┌─────────────────────────────────────────────┐   │
│ │ ⚡ V-101 - Gate Valve            [OPEN]     │   │
│ │ ⭕ V-102 - Ball Valve            [CLOSED]   │   │
│ │ ⚡ V-103 - Globe Valve           [OPEN]     │   │
│ └─────────────────────────────────────────────┘   │
│                                                     │
│ [▶ Run Simulation]                                 │
│                                                     │
│ ✅ Flow simulation from Tank-101: 5 nodes reached │
│                                                     │
│ Flow Path (5 nodes)                                │
│ 1  Tank-101                                        │
│ 2  V-101                                           │
│ 3  Pump-201                                        │
│ 4  V-102                          🔴 BLOCKED       │
│ 5  Tank-201                                        │
└─────────────────────────────────────────────────────┘
```

### Graph Tab (Animated View)
```
┌─────────────────────────────────────────────────────┐
│ [Nodes: 10] [Edges: 15] [✅ Ready]                 │
│ [🟢 Flow Simulation Active - 5 nodes]              │
├─────────────────────────────────────────────────────┤
│                                                     │
│     🟢 Tank-101                                     │
│         ║ (animated green flow)                    │
│         ║                                           │
│     🟢 V-101 (OPEN)                                 │
│         ║ (animated green flow)                    │
│         ║                                           │
│     🟢 Pump-201                                     │
│         ║ (animated green flow)                    │
│         ║                                           │
│     🔴 V-102 (CLOSED - BLOCKED!)                    │
│         ┆ (dimmed, no animation)                   │
│         ┆                                           │
│     ⚫ Tank-201 (dimmed - not reached)              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 🎮 Interactive Controls

### Valve Toggle
- **Click any valve** to toggle between OPEN/CLOSED
- **Green badge** = Valve is OPEN ✅
- **Red badge** = Valve is CLOSED 🔴
- Simulation updates **automatically** on toggle

### Source Node Selection
- **Dropdown menu** shows all nodes in the topology
- Select the **starting point** for flow simulation
- Common choices: Tanks, Feed lines, Pumps

### Reset Button
- Clears all valve states (all valves OPEN)
- Clears source node selection
- Clears simulation results

---

## 💡 Use Cases

### 1. Maintenance Planning
**Goal:** Isolate equipment for maintenance

**Steps:**
1. Select equipment as source
2. Close upstream and downstream valves
3. Verify equipment is isolated (dimmed in Graph view)
4. Safe to perform maintenance ✅

### 2. Troubleshooting
**Goal:** Find why tank is not filling

**Steps:**
1. Select tank as source
2. Check flow path in Flow Sim tab
3. Identify closed valves blocking flow
4. Open necessary valves
5. Verify flow reaches tank ✅

### 3. Emergency Shutdown
**Goal:** Quickly isolate a section

**Steps:**
1. Select emergency valve
2. Close valve
3. Check affected equipment in Graph view
4. Verify isolation ✅

---

## 🔍 Understanding the Visualization

### Edge Colors & Animation

| Visual | Meaning |
|--------|---------|
| **═══>** (Green, animated) | Active flow path |
| **───>** (Gray, static) | No simulation running |
| **···>** (Dimmed, static) | Inactive (simulation running, no flow) |

### Node Colors & Glow

| Visual | Meaning |
|--------|---------|
| **🟢 Green glow** | Node in active flow path |
| **🔴 Red glow** | Blocked node (closed valve) |
| **⚫ Dimmed** | Inactive node (no flow reaching) |
| **Normal** | No simulation running |

### Status Indicators

| Badge | Meaning |
|-------|---------|
| **🟢 Flow Simulation Active** | Simulation is running |
| **Nodes: 10** | Total nodes in graph |
| **Edges: 15** | Total edges in graph |
| **✅ Ready** | Graph is loaded and ready |

---

## 🐛 Troubleshooting

### Problem: No valves showing in Flow Sim tab

**Solution:**
- Ensure P&ID has valve symbols
- Check that valves were detected (look in Canvas view)
- Verify graph data is loaded (check Graph tab)

### Problem: Simulation not running

**Solution:**
- Select a source node first
- Check browser console for errors
- Verify backend is running (`http://localhost:8000/docs`)

### Problem: Graph not showing animation

**Solution:**
- Switch to Graph tab (animation only shows there)
- Ensure simulation ran successfully in Flow Sim tab
- Check for "Flow Simulation Active" badge

### Problem: All nodes dimmed

**Solution:**
- Check if source node is valid
- Verify at least one valve is open
- Try resetting simulation and running again

---

## 🎓 Tips & Tricks

### Tip 1: Use Multiple Tabs
- Keep **Flow Sim** tab open in one window
- Keep **Graph** tab open in another window
- Toggle valves and see real-time updates!

### Tip 2: Start Simple
- Begin with all valves OPEN
- Close one valve at a time
- Observe how flow changes

### Tip 3: Follow the Flow Path
- Check the **Flow Path** section in Flow Sim tab
- Numbers show the order of traversal
- Red highlights show where flow stops

### Tip 4: Use Reset Often
- Click **Reset** to start fresh
- Helps when testing different scenarios
- Clears all previous states

### Tip 5: Check Statistics
- **Total Distance** shows flow path length
- **Blocked Nodes** shows how many valves are blocking
- **Active Nodes** shows reachable equipment

---

## 📊 Example Scenario

### Scenario: Test Pump Isolation

**Initial State:**
```
Source: Tank-101
Valves: All OPEN
Result: Flow reaches Pump-201 ✓
```

**Close Upstream Valve:**
```
Action: Click V-101 → CLOSED
Result: Flow stops at V-101 🔴
        Pump-201 is dimmed ⚫
```

**Close Downstream Valve:**
```
Action: Click V-102 → CLOSED
Result: Pump-201 is fully isolated ✓
        Safe for maintenance ✅
```

**Verification in Graph Tab:**
```
Tank-101:  🟢 (green glow)
V-101:     🔴 (red glow - blocked)
Pump-201:  ⚫ (dimmed - isolated)
V-102:     ⚫ (dimmed - not reached)
```

**Conclusion:** Pump successfully isolated! ✅

---

## 🚀 Next Steps

### Learn More
- Read [FLOW_SIMULATOR_INTEGRATION_COMPLETE.md](FLOW_SIMULATOR_INTEGRATION_COMPLETE.md) for full documentation
- Check [INTERACTIVE_FLOW_SIMULATOR_COMPLETE.md](INTERACTIVE_FLOW_SIMULATOR_COMPLETE.md) for implementation details
- Visit `http://localhost:8000/docs` for API documentation

### Advanced Features (Coming Soon)
- Flow rate calculations
- Pressure drop simulation
- Multiple source nodes
- Time-based animation
- 3D visualization

### Get Help
- Check browser console for errors
- Review backend logs
- Open an issue on GitHub
- Contact support team

---

## ✅ Quick Checklist

Before using Flow Simulator:
- [ ] Backend is running
- [ ] Frontend is running
- [ ] P&ID image uploaded
- [ ] Graph data loaded
- [ ] At least one valve detected

To run a simulation:
- [ ] Go to Flow Sim tab
- [ ] Select source node
- [ ] Configure valve states
- [ ] Check results in Flow Sim tab
- [ ] Switch to Graph tab for animation

---

## 🎉 You're Ready!

You now know how to:
- ✅ Configure flow simulations
- ✅ Toggle valve states
- ✅ View animated flow visualization
- ✅ Interpret visual indicators
- ✅ Troubleshoot common issues

**Start simulating flows now!** 🌊

---

**Version:** 1.0.0  
**Last Updated:** 2026-05-17  
**Status:** ✅ Production Ready

**Happy Simulating!** 🚀
