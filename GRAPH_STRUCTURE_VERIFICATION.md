# Graph Structure Verification Guide

## Issue

You mentioned the Graph structure changed and you want it back to the original structure.

## Original Backend Structure (Correct)

When data comes from the backend `/api/graph` endpoint:

```typescript
{
  nodes: [
    {
      id: "node_0",
      type: "instrument",
      tag: "FIC-101",
      label: "FIC-101",
      x: 250.5,        // ← x at root level
      y: 180.3         // ← y at root level
    }
  ],
  edges: [
    {
      source: "node_0",
      target: "node_1",
      type: "connected_to"
    }
  ]
}
```

## React Flow Structure (Internal to Editor)

When displayed in React Flow (Editor or Graph viewer):

```typescript
{
  nodes: [
    {
      id: "node_0",
      type: "default",
      position: {      // ← position object
        x: 250.5,
        y: 180.3
      },
      data: {
        label: "FIC-101",
        type: "instrument"
      }
    }
  ]
}
```

## What the "Update Graph & HazOp" Does

1. **Takes React Flow format** from Editor (with `position: {x, y}`)
2. **Converts to Backend format** (with `x, y` at root)
3. **Updates the store** with backend format
4. **GraphViewer receives** backend format
5. **GraphViewer transforms** to React Flow format (same as always)

## Verification Steps

### Step 1: Check Console Logs

After clicking "Update Graph & HazOp", check the browser console for:

```
=== UPDATING GRAPH DATA ===
Nodes: 5
Edges: 4
Sample backend node: {id: "valve-1001", type: "valve", tag: "Valve-1", label: "Valve-1", x: 250, y: 150}
Backend format check:
  - Has x/y at root? true true
  - Has position object? false
  - Has type? true
  - Has label? true
```

**Expected:**
- ✅ `Has x/y at root? true true`
- ✅ `Has position object? false`

**If you see:**
- ❌ `Has x/y at root? false false`
- ❌ `Has position object? true`

Then the conversion is wrong.

### Step 2: Check Graph View

1. Click "Update Graph & HazOp" in Editor
2. Switch to "Graph" tab
3. Check console for:

```
=== GRAPH RENDERING ===
Total nodes: 5
Total edges: 4
Sample raw nodes: [{id: "valve-1001", type: "valve", x: 250, y: 150, ...}]
```

**Expected:**
- ✅ Nodes have `x` and `y` at root level
- ✅ GraphViewer transforms them to React Flow format
- ✅ Graph displays correctly

### Step 3: Compare with Original

**Original flow (from backend):**
```
Backend /api/graph
  ↓ (returns backend format)
Store (graphData)
  ↓ (backend format)
GraphViewer
  ↓ (transforms to React Flow)
Display
```

**New flow (from Editor):**
```
Editor (React Flow format)
  ↓ (converts to backend format)
Store (graphData)
  ↓ (backend format - SAME AS ORIGINAL)
GraphViewer
  ↓ (transforms to React Flow - SAME AS ORIGINAL)
Display
```

## What Should NOT Change

The GraphViewer component should work **exactly the same** whether data comes from:
- Backend API (`/api/graph`)
- Editor ("Update Graph & HazOp")

Both provide the **same backend format** to the store.

## If Graph View Looks Different

### Possible Issue 1: Coordinates

**Problem:** Nodes from Editor have different coordinate ranges than backend

**Solution:** This is expected! Editor creates nodes at different positions than backend detection.

**Example:**
- Backend: x=1500, y=800 (from P&ID image pixels)
- Editor: x=250, y=150 (from canvas drop position)

**This is normal!** The Editor creates a new diagram, not the same as the uploaded P&ID.

### Possible Issue 2: Node Styling

**Problem:** Nodes look different (colors, sizes, shapes)

**Check:** Are the node `type` values correct?

```javascript
// Editor creates:
type: "valve"  // ← lowercase

// Backend might return:
type: "Valve"  // ← capitalized
```

**Solution:** Ensure type matching is case-insensitive in GraphViewer.

### Possible Issue 3: Missing Properties

**Problem:** Some nodes don't display

**Check:** Do all nodes have required properties?

Required:
- `id` ✅
- `x` ✅
- `y` ✅
- `type` ✅
- `label` ✅

Optional:
- `tag`

## Testing Checklist

- [ ] Upload P&ID → Process → View in Graph tab
  - Note the structure and appearance
- [ ] Go to Editor tab
- [ ] Create 3 new nodes (Valve, Pump, Instrument)
- [ ] Connect them
- [ ] Click "Update Graph & HazOp"
- [ ] Check console logs (verify backend format)
- [ ] Switch to Graph tab
- [ ] Verify nodes display correctly
- [ ] Compare with original Graph view

## Expected Behavior

### Original Graph (from backend)
- Shows detected equipment from P&ID
- Positions match P&ID layout
- Many nodes (50+)
- Complex connections

### Updated Graph (from Editor)
- Shows custom-created equipment
- Positions from Editor canvas
- Few nodes (3-10)
- Simple connections

**Both should display correctly in Graph view!**

## If You Want Original Graph Back

If you want to see the original P&ID graph again:

1. **Option A:** Reload the page
   - This clears the store
   - Upload P&ID again
   - Original graph returns

2. **Option B:** Add a "Reset" button
   - Fetches original graph from backend
   - Restores original view

3. **Option C:** Keep both
   - Store original graph separately
   - Allow switching between original and edited

## Summary

The Graph view structure **has not changed**. It still:
1. Receives backend format (x, y at root)
2. Transforms to React Flow format
3. Displays the same way

What **has changed**:
- You can now update the graph data from the Editor
- The data comes from a different source (Editor vs Backend)
- The content is different (custom vs detected)

The **structure and rendering** remain the same!

---

**If you're still seeing issues, please:**
1. Share the console logs after clicking "Update Graph & HazOp"
2. Describe what looks different in the Graph view
3. Share a screenshot if possible

I'll help fix any remaining issues!
