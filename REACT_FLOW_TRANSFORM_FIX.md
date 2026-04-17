# React Flow Transform Bug - FIXED

## The Problem

When clicking on nodes in the minimap or selecting nodes, ALL nodes would suddenly gather/cluster at position (0, 0) instead of staying in their correct positions.

## Root Cause

The issue was in the "Highlight selected node" useEffect that was adding these properties to node styles:

```typescript
transform: isSelected ? 'scale(1.2)' : 'scale(1)',
transition: 'all 0.2s ease',
```

### Why This Broke Everything:

React Flow internally positions nodes using CSS `transform: translate(x, y)`. When we added `transform: 'scale(1)'` to the node's inline style, we **overwrote** React Flow's positioning transform, causing all nodes to lose their position and collapse to (0, 0).

## The Fix

Removed the `transform` and `transition` properties from the node highlighting logic. Now only `boxShadow` and `zIndex` are updated:

```typescript
// Highlight selected node
useEffect(() => {
  if (nodes.length === 0) return;
  
  setNodes((nds) =>
    nds.map((node) => {
      const border = node.style?.border;
      const borderColor = typeof border === 'string' ? border.split(' ')[2] : '#61afef';
      const isSelected = selectedNodeId === node.id;
      
      return {
        ...node,
        style: {
          ...node.style,
          // Only update boxShadow and zIndex
          // ❌ DO NOT USE 'transform' or 'transition' HERE
          // It overrides React Flow's internal position translates!
          boxShadow: isSelected
            ? `0 0 20px ${borderColor}, 0 0 40px ${borderColor}80`
            : `0 2px 6px ${borderColor}40`,
          zIndex: isSelected ? 1000 : 1,
        },
      };
    })
  );
}, [selectedNodeId, setNodes, nodes.length]);
```

## What This Fixes

✅ Nodes stay in their correct positions when selected
✅ Clicking minimap dots navigates to correct locations
✅ Nodes don't gather/cluster at (0, 0)
✅ Minimap accurately reflects node positions
✅ Selection highlighting still works (glowing effect)

## What Changed

**Before:**
- Selected nodes had `transform: scale(1.2)` (scaling animation)
- All nodes had `transition: all 0.2s ease`
- This overwrote React Flow's positioning

**After:**
- Selected nodes only get enhanced `boxShadow` (glowing effect)
- Higher `zIndex` to appear on top
- React Flow's positioning remains intact

## If You Want Scale Animation

If you still want nodes to grow when selected, you need to create a **Custom Node Component** and apply the scale transform to the **inner content**, not the wrapper:

```typescript
// CustomNode.tsx
const CustomNode = ({ data, selected }) => {
  return (
    <div 
      style={{
        // Inner div can have transform without breaking positioning
        transform: selected ? 'scale(1.2)' : 'scale(1)',
        transition: 'transform 0.2s ease',
      }}
    >
      {data.label}
    </div>
  );
};

// Then register it:
const nodeTypes = {
  custom: CustomNode,
};

<ReactFlow nodeTypes={nodeTypes} ... />
```

## Testing

1. **Start the application**
2. **Process a P&ID image**
3. **Click on nodes in the main graph** - they should stay in position
4. **Click on blue dots in minimap** - should navigate to correct positions
5. **Select different nodes** - they should glow but not move

## Key Lesson

**Never use `transform` in React Flow node styles!**

React Flow uses `transform: translate(x, y)` internally for positioning. Any `transform` property you add will override this and break positioning.

**Safe to modify:**
- ✅ `boxShadow`
- ✅ `zIndex`
- ✅ `border`
- ✅ `background`
- ✅ `opacity`

**Dangerous to modify:**
- ❌ `transform` (breaks positioning)
- ❌ `position` (breaks layout)
- ❌ `top`, `left` (conflicts with React Flow)

## Files Modified

- `frontend/src/components/GraphViewer.tsx` - Removed transform and transition from node highlighting

## Related Issues

This fix also resolves:
- Nodes clustering when clicking minimap
- Nodes gathering at origin on selection
- Minimap not matching main view after interaction
- Position desync between minimap and main graph

## Credits

Thanks to the user for identifying this classic React Flow pitfall! The `transform` override is a very common mistake when working with React Flow.
