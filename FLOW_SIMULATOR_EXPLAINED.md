# 🌊 Flow Simulator - Complete Explanation

## 🎯 What is Flow Simulator?

**Flow Simulator** is a digital twin feature that traces the path of fluids (water, oil, gas, chemicals) through your P&ID piping system.

### Real-World Use Case

Imagine you're a maintenance engineer and you need to:
- **Isolate a pump for maintenance** - Which valves do you need to close?
- **Trace contamination** - If there's contamination at point A, what equipment is affected?
- **Plan shutdown** - If you close valve V-101, what equipment loses flow?
- **Troubleshoot** - Why is Tank T-102 not filling? Trace the flow path backwards.

**Flow Simulator answers these questions instantly!**

---

## 🔍 How It Works

### Example P&ID System

```
Tank-101 → Pump-201 → Valve-301 → Heat Exchanger-401 → Tank-501
    ↓                      ↓                ↓
  Drain              Bypass Line      Pressure Relief
```

### Flow Tracing

**Downstream Trace (Forward):**
```
Start: Tank-101
Direction: Downstream (where does fluid go?)

Result:
Tank-101 → Pump-201 → Valve-301 → Heat Exchanger-401 → Tank-501

Affected Equipment:
- Pump-201 (will pump fluid from Tank-101)
- Valve-301 (controls flow)
- Heat Exchanger-401 (receives fluid)
- Tank-501 (receives final fluid)
```

**Upstream Trace (Backward):**
```
Start: Tank-501
Direction: Upstream (where does fluid come from?)

Result:
Tank-501 ← Heat Exchanger-401 ← Valve-301 ← Pump-201 ← Tank-101

Source Equipment:
- Tank-101 (original source)
- Pump-201 (provides pressure)
- Valve-301 (controls flow)
- Heat Exchanger-401 (processes fluid)
```

---

## 🎨 Features

### 1. Flow Path Tracing

**What it does:**
- Traces fluid flow from any starting point
- Shows complete path through piping system
- Identifies all equipment in the flow path

**Use Cases:**
- **Maintenance Planning:** "If I isolate Pump P-101, what's affected?"
- **Troubleshooting:** "Why isn't Tank T-202 filling?"
- **Safety Analysis:** "If there's a leak at Valve V-303, what's downstream?"

### 2. Upstream Analysis

**What it does:**
- Traces backwards to find source
- Identifies all feeding equipment
- Shows supply chain

**Use Cases:**
- **Source Identification:** "Where does this tank get its fluid?"
- **Contamination Tracing:** "If Tank T-101 is contaminated, what fed it?"
- **Pressure Analysis:** "What pumps supply this line?"

### 3. Downstream Analysis

**What it does:**
- Traces forward to find destination
- Identifies all receiving equipment
- Shows distribution network

**Use Cases:**
- **Impact Analysis:** "If this pump fails, what equipment loses supply?"
- **Distribution Mapping:** "Where does this tank discharge to?"
- **Shutdown Planning:** "What's affected if I close this valve?"

### 4. Valve Closure Simulation

**What it does:**
- Simulates closing a valve
- Shows blocked paths
- Identifies isolated equipment

**Use Cases:**
- **Maintenance Isolation:** "Which valves isolate this pump?"
- **Emergency Shutdown:** "What happens if I close emergency valve EV-101?"
- **Bypass Verification:** "Does the bypass work if I close the main valve?"

---

## 📊 Real-World Examples

### Example 1: Pump Maintenance

**Scenario:** You need to maintain Pump P-201

**Steps:**
1. Select Pump P-201 as start node
2. Choose "Upstream" direction
3. Click "Trace Flow Path"

**Result:**
```
Upstream Path:
Tank T-101 → Valve V-101 → Pump P-201

Action Required:
1. Close Valve V-101 (isolates pump from tank)
2. Drain pump
3. Perform maintenance
4. Open Valve V-101 when done
```

### Example 2: Contamination Investigation

**Scenario:** Tank T-501 has contaminated fluid

**Steps:**
1. Select Tank T-501 as start node
2. Choose "Upstream" direction
3. Click "Trace Flow Path"

**Result:**
```
Upstream Path:
Tank T-501 ← Heat Exchanger HE-401 ← Valve V-301 ← Pump P-201 ← Tank T-101

Possible Contamination Sources:
1. Tank T-101 (original source)
2. Pump P-201 (seal leak?)
3. Heat Exchanger HE-401 (tube leak?)

Investigation Plan:
- Sample Tank T-101
- Check Pump P-201 seals
- Inspect Heat Exchanger HE-401
```

### Example 3: Emergency Shutdown

**Scenario:** Emergency valve EV-101 needs to be closed

**Steps:**
1. Select Valve EV-101 as start node
2. Choose "Downstream" direction
3. Click "Trace Flow Path"

**Result:**
```
Downstream Path:
Valve EV-101 → Reactor R-301 → Separator S-401 → Tank T-501

Affected Equipment (will lose flow):
- Reactor R-301 (process stops)
- Separator S-401 (no feed)
- Tank T-501 (no filling)

Emergency Actions:
1. Close EV-101
2. Monitor Reactor R-301 pressure
3. Activate backup cooling
4. Notify operations team
```

---

## 🎯 How to Use in EDAI4

### Step 1: Upload P&ID
```
1. Open http://localhost:3000
2. Upload your P&ID image
3. Wait for processing
4. See 5 tabs appear
```

### Step 2: Open Flow Simulator
```
1. Click "Flow Sim" tab
2. You'll see:
   - Start Node dropdown
   - Direction selector (Upstream/Downstream)
   - Trace Flow Path button
```

### Step 3: Select Start Node
```
1. Click "Start Node" dropdown
2. Select equipment/instrument
   Example: "FT-101 - instrument.bubble"
   Example: "Pump P-201 - equipment.pump"
```

### Step 4: Choose Direction
```
Upstream (←):
- Traces backwards
- Finds sources
- Shows what feeds this node

Downstream (→):
- Traces forward
- Finds destinations
- Shows what this node feeds
```

### Step 5: Trace Path
```
1. Click "Trace Flow Path" button
2. Wait for results (1-2 seconds)
3. View results:
   - Start Node
   - End Node
   - Path Nodes (all nodes in path)
   - Total Distance
   - Blocked Paths (if any)
```

---

## 📈 Understanding Results

### Result Display

```
Flow Path Results
─────────────────
Start Node:    FT-101
End Node:      Tank-501
Total Nodes:   5
Distance:      1250.5px

Path Nodes (5):
1. FT-101 (instrument.bubble)
   ↓
2. Pump-201 (equipment.pump)
   ↓
3. Valve-301 (valve.gate)
   ↓
4. HE-401 (equipment.heat_exchanger)
   ↓
5. Tank-501 (equipment.tank)
```

### What Each Field Means

**Start Node:**
- Where you started tracing from
- The equipment/instrument you selected

**End Node:**
- Where the path ends
- Last equipment in the flow path
- Could be a dead-end or boundary

**Total Nodes:**
- Number of equipment/instruments in path
- Includes start and end nodes

**Distance:**
- Total distance traveled (in pixels)
- Approximate pipe length
- Useful for material calculations

**Path Nodes:**
- Complete list of equipment in order
- Shows flow direction with arrows
- Includes equipment type

**Blocked By:**
- Shows if path is blocked
- Indicates closed valves
- Helps identify isolation points

---

## 🔧 Technical Details

### Algorithm: Breadth-First Search (BFS)

**Why BFS?**
- Finds shortest path
- Explores all connections
- Handles complex networks
- Detects cycles

**How it works:**
```python
1. Start at selected node
2. Add to queue
3. While queue not empty:
   a. Get next node
   b. Mark as visited
   c. Check all neighbors
   d. Add unvisited neighbors to queue
   e. Record path
4. Return complete path
```

### Distance Calculation

```python
# Euclidean distance between nodes
distance = sqrt((x2 - x1)² + (y2 - y1)²)

# Total path distance
total = sum(distance between each consecutive pair)
```

### Blocked Path Detection

```python
# Check if valve is closed
if node.type == "valve" and node.state == "closed":
    path_blocked = True
    blocked_by = node.tag
```

---

## 🎨 Use Cases by Industry

### Oil & Gas
- **Pipeline Tracing:** Track oil/gas flow through complex networks
- **Isolation Planning:** Identify valves for maintenance
- **Emergency Response:** Quick shutdown planning

### Chemical Processing
- **Batch Tracing:** Track chemical batches through process
- **Contamination Control:** Identify affected equipment
- **Process Optimization:** Analyze flow paths

### Water Treatment
- **Distribution Analysis:** Track water flow
- **Valve Management:** Identify isolation points
- **Maintenance Planning:** Plan shutdowns

### Power Generation
- **Steam Tracing:** Track steam distribution
- **Cooling Water:** Analyze cooling circuits
- **Fuel Systems:** Trace fuel flow

---

## 💡 Pro Tips

### Tip 1: Start from Key Equipment
```
Good starting points:
- Pumps (show what they feed)
- Tanks (show sources/destinations)
- Critical valves (show isolation zones)
```

### Tip 2: Use Both Directions
```
Upstream:   Find sources
Downstream: Find destinations
Both:       Complete picture
```

### Tip 3: Check for Bypasses
```
If main path blocked:
1. Trace from bypass valve
2. Verify alternate path exists
3. Confirm bypass capacity
```

### Tip 4: Document Results
```
For maintenance:
1. Trace flow path
2. Screenshot results
3. Add to work permit
4. Verify isolation
```

---

## 🐛 Troubleshooting

### Issue: Dropdown is Empty

**Cause:** No P&ID processed yet

**Solution:**
```
1. Upload P&ID image first
2. Wait for processing
3. Dropdown will populate with nodes
```

### Issue: No Path Found

**Cause:** Nodes not connected or isolated

**Solution:**
```
1. Check if nodes are actually connected
2. Try different start node
3. Check graph viewer for connections
```

### Issue: Path Seems Wrong

**Cause:** Line detection missed connections

**Solution:**
```
1. Check graph viewer
2. Verify connections are correct
3. May need to adjust line detection parameters
```

---

## 📚 Related Features

### Graph Viewer
- Visualizes topology
- Shows all connections
- Helps verify flow paths

### Design Rules
- Checks for orphaned equipment
- Verifies connectivity
- Ensures proper isolation

### Deliverables
- Generates I/O lists
- Documents connections
- Creates system diagrams

---

## ✅ Summary

**Flow Simulator is:**
- Digital twin of your piping system
- Traces fluid flow paths
- Identifies affected equipment
- Plans maintenance isolation
- Analyzes impact of changes

**Use it for:**
- Maintenance planning
- Troubleshooting
- Safety analysis
- Emergency response
- Process optimization

**Benefits:**
- Instant analysis (1-2 seconds)
- Visual path display
- Complete equipment list
- Distance calculations
- Blocked path detection

---

**Status**: ✅ Fully Functional
**Algorithm**: Breadth-First Search (BFS)
**Performance**: <1 second per trace
**Accuracy**: Depends on line detection quality

🌊 **Flow Simulator - Your Digital Twin for P&ID Analysis!**
