# Spec: Editor Node Labels Improvement

**Feature ID:** editor-node-labels-improvement  
**Type:** Feature  
**Status:** requirements  
**Priority:** High  
**Created:** 2026-05-15

---

## Quick Summary

Improve node identification in the EditableGraphViewer by adding clear visual indicators, ISA instrument tags, icons, and better labeling. Currently, nodes only show generic labels like "Instrument-1" which makes it difficult for users to quickly identify components in complex P&ID diagrams.

---

## Problem

Users struggle to identify nodes in the editor because:
- Nodes only show generic labels (e.g., "Instrument-1", "Valve-2")
- No visual icons to distinguish component types
- No ISA standard tags for professional identification
- Limited information visible without clicking

This slows down the editing workflow and makes diagrams harder to understand.

---

## Solution

Enhance node display with:
1. **Type Icons** - Visual indicators for each component type (🎛️ instruments, 🔧 valves, ⚙️ pumps, 📦 equipment)
2. **ISA Tags** - Industry-standard identifiers (FIC-101, PT-205, etc.)
3. **Multi-line Labels** - Hierarchical information display
4. **Hover Tooltips** - Detailed information on hover
5. **Better Selection** - Clear visual feedback for selected nodes

---

## Documents

- [Requirements](./REQUIREMENTS.md) - Detailed functional and non-functional requirements
- [Design](./DESIGN.md) - Technical design (to be created)
- [Tasks](./TASKS.md) - Implementation tasks (to be created)

---

## Key Features

### 1. Enhanced Node Labels
- Multi-line display: Icon + Type, Tag, ID
- Font hierarchy for readability
- Truncation with ellipsis for long labels

### 2. Icon System
- Unique icon for each node type
- Color-coded to match existing scheme
- Scalable at all zoom levels

### 3. ISA Tag Support
- Standard instrument tag format
- Editable from node info panel
- Validation to prevent duplicates

### 4. Interactive Tooltips
- Show full details on hover
- 300ms delay for smooth UX
- Dark theme matching UI

### 5. Selection Highlighting
- Glowing effect for selected nodes
- Increased z-index
- Clear visual feedback

---

## Success Criteria

- ✅ Users can identify node types without clicking
- ✅ ISA tags are clearly visible on all nodes
- ✅ No performance degradation with 100+ nodes
- ✅ Consistent styling with GraphViewer
- ✅ Positive user feedback on readability

---

## Timeline

- **Requirements:** 1 day (CURRENT)
- **Design:** 1 day
- **Implementation:** 3-5 days
- **Testing:** 2 days
- **Total:** ~1-2 weeks

---

## Next Steps

1. ✅ Complete requirements document
2. ⏳ Review and approve requirements
3. ⏳ Create technical design document
4. ⏳ Break down into implementation tasks
5. ⏳ Begin development

---

**Owner:** Development Team  
**Reviewers:** Product Owner, UX Designer, Engineering Lead  
**Status:** Ready for Review
