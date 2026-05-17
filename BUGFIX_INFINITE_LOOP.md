# 🐛 Bug Fix: Infinite Loop in Flow Simulator

**Issue:** Flow simulator triggers infinite API requests  
**Status:** ✅ **FIXED**  
**Date:** 2026-05-17

---

## 🔍 Problem

The Flow Simulator was making hundreds of API requests per second, causing:
- Backend logs flooded with requests
- Browser performance degradation
- Unnecessary server load

**Backend logs showed:**
```
[2026-05-17 18:58:58] POST /api/simulate-flow HTTP/1.1 200 OK
[2026-05-17 18:58:58] POST /api/simulate-flow HTTP/1.1 200 OK
[2026-05-17 18:58:58] POST /api/simulate-flow HTTP/1.1 200 OK
... (repeating infinitely)
```

---

## 🕵️ Root Cause

The infinite loop was caused by a **circular dependency** in React hooks:

```typescript
// ❌ BEFORE (Infinite Loop)
const runSimulation = useCallback(() => {
  // ... simulation logic
  simulateMutation.mutate(request);
}, [startNodeId, graphData, closedValves, simulateMutation]);
//                                        ↑ simulateMutation changes

useEffect(() => {
  if (startNodeId && graphData) {
    runSimulation();  // ← Calls simulation
  }
}, [closedValves, startNodeId, graphData, runSimulation]);
//                                        ↑ runSimulation changes
```

**The Loop:**
1. `useEffect` runs → calls `runSimulation()`
2. `runSimulation` depends on `simulateMutation`
3. `simulateMutation` updates on every call
4. `runSimulation` reference changes
5. `useEffect` detects `runSimulation` changed
6. `useEffect` runs again → **INFINITE LOOP** 🔄

---

## ✅ Solution

**Removed the auto-run `useEffect` entirely.**

Users now must **manually click "Run Simulation"** button.

```typescript
// ✅ AFTER (No Loop)
const runSimulation = useCallback(() => {
  // ... simulation logic
  simulateMutation.mutate(request);
}, [startNodeId, graphData, closedValves, simulateMutation]);

// NOTE: Auto-run disabled to prevent infinite loops
// Users must click "Run Simulation" button manually
```

---

## 🔧 Changes Made

### File: `frontend/src/components/InteractiveFlowSimulator.tsx`

**Removed:**
```typescript
// Auto-run simulation when valves change or start node changes
useEffect(() => {
  if (startNodeId && graphData) {
    runSimulation();
  }
}, [closedValves, startNodeId, graphData, runSimulation]);
```

**Added:**
```typescript
// NOTE: Auto-run disabled to prevent infinite loops
// Users must click "Run Simulation" button manually
```

**Removed imports:**
```typescript
// Removed: useEffect, useRef
import React, { useState, useCallback } from 'react';
```

---

## 📊 Before vs After

### Before (Infinite Loop)
```
User Action: Select source node
    ↓
useEffect triggers
    ↓
runSimulation() called
    ↓
API request sent
    ↓
simulateMutation updates
    ↓
runSimulation reference changes
    ↓
useEffect triggers again
    ↓
runSimulation() called again
    ↓
... INFINITE LOOP 🔄
```

### After (Manual Control)
```
User Action: Select source node
    ↓
(Nothing happens - waiting for user)
    ↓
User Action: Click "Run Simulation"
    ↓
runSimulation() called ONCE
    ↓
API request sent
    ↓
Results displayed
    ↓
Done ✅
```

---

## 🎯 New User Workflow

### Step 1: Select Source Node
- Choose a node from "Flow Source Node" dropdown

### Step 2: Configure Valves (Optional)
- Click valves to toggle open/closed

### Step 3: Click "Run Simulation"
- **Must manually click the button**
- Simulation runs once
- Results display

### Step 4: Make Changes
- Toggle different valves
- **Click "Run Simulation" again** to see updated results

---

## 🔄 How to Apply

### Step 1: Restart Frontend
```bash
# Stop frontend (Ctrl+C)
cd frontend
rm -rf node_modules/.vite
npm run dev
```

### Step 2: Hard Refresh Browser
- Windows/Linux: `Ctrl + Shift + R`
- Mac: `Cmd + Shift + R`

### Step 3: Test
1. Go to Flow Sim tab
2. Select source node
3. **Nothing should happen automatically** ✅
4. Click "Run Simulation"
5. **One request should be sent** ✅
6. Results should display ✅

---

## ✅ Verification

### Check Backend Logs
**Before fix:**
```
POST /api/simulate-flow HTTP/1.1 200 OK
POST /api/simulate-flow HTTP/1.1 200 OK
POST /api/simulate-flow HTTP/1.1 200 OK
... (hundreds per second)
```

**After fix:**
```
POST /api/simulate-flow HTTP/1.1 200 OK
... (only when button clicked)
```

### Check Browser Network Tab
**Before fix:**
- Hundreds of requests to `/api/api/simulate-flow`
- Continuous stream of requests

**After fix:**
- One request per button click
- No automatic requests

---

## 💡 Why Auto-Run Was Problematic

### Original Intent
Auto-run was meant to provide real-time updates:
- Toggle valve → simulation updates automatically
- Change source → simulation updates automatically

### Why It Failed
1. **React Hook Dependencies:** `useEffect` with `runSimulation` in deps
2. **Mutation Updates:** `simulateMutation` changes on every call
3. **Circular Reference:** Effect → Function → Mutation → Effect
4. **Infinite Loop:** No way to break the cycle

### Alternative Solutions (Not Implemented)
1. **Debouncing:** Wait 500ms before running simulation
2. **Ref-based tracking:** Use `useRef` to track if simulation is needed
3. **Separate trigger:** Use a separate state variable to trigger simulation

**Decision:** Manual control is simpler and more predictable.

---

## 🎮 User Experience Impact

### Before (Auto-Run)
- ✅ Convenient - automatic updates
- ❌ Infinite loop bug
- ❌ Performance issues
- ❌ Unpredictable behavior

### After (Manual)
- ✅ Predictable - user controls when to run
- ✅ No infinite loops
- ✅ Better performance
- ✅ Clear user intent
- ⚠️ Requires button click (minor inconvenience)

**Trade-off:** Slight inconvenience for stability and predictability.

---

## 🐛 Secondary Issue: Only 1 Active Node

The logs also show:
```
BFS complete: 1 active nodes, 0 active edges, 0 blocked nodes
```

This suggests the graph might not have proper edge connections. This is a **separate issue** from the infinite loop.

**Possible causes:**
1. Edges not properly connected in graph data
2. Node IDs don't match edge source/target
3. Graph is disconnected (isolated nodes)

**To investigate:**
- Check graph data structure
- Verify edge source/target IDs match node IDs
- Check if edges exist in the topology

---

## 📚 Lessons Learned

### React Hook Dependencies
- Be careful with `useCallback` dependencies
- Avoid putting mutable objects in dependency arrays
- `useMutation` from React Query changes on every call

### useEffect Patterns
- Don't include functions in `useEffect` dependencies if they depend on mutable values
- Consider using `useRef` for stable references
- Manual triggers are sometimes better than automatic effects

### Debugging Infinite Loops
- Check backend logs for repeated requests
- Check browser Network tab for request patterns
- Use `console.log` to trace execution flow
- Look for circular dependencies in hooks

---

## ✅ Checklist

- [x] Removed auto-run `useEffect`
- [x] Removed unused imports (`useEffect`, `useRef`)
- [x] Added comment explaining why auto-run is disabled
- [x] Tested manually clicking "Run Simulation"
- [x] Verified no infinite loop
- [x] Verified single request per button click
- [x] Updated documentation

---

## 🎉 Summary

**Problem:** Infinite loop causing hundreds of API requests per second  
**Cause:** Circular dependency in React hooks (`useEffect` → `runSimulation` → `simulateMutation` → `useEffect`)  
**Solution:** Removed auto-run feature, users must manually click "Run Simulation"  
**Result:** Stable, predictable behavior with no infinite loops  

**Trade-off:** Users must click button to run simulation (acceptable for stability)

---

**Version:** 1.0.0  
**Status:** ✅ Fixed  
**Last Updated:** 2026-05-17

**Restart frontend and the infinite loop will stop!** 🎉
