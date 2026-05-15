# Requirements: Editor Node Labels Improvement

**Feature ID:** editor-node-labels-improvement  
**Status:** Draft  
**Created:** 2026-05-15  
**Owner:** Development Team

---

## 1. Overview

### 1.1 Problem Statement
Currently, in the EditableGraphViewer component, nodes display minimal identification information (e.g., "Instrument-1", "Valve-2"). Users find it difficult to quickly identify what each node represents without clicking on it or examining detailed properties. This slows down the editing workflow and makes the diagram harder to understand at a glance.

### 1.2 Goals
- **Primary Goal:** Improve node visual identification so users can instantly recognize node types and purposes
- **Secondary Goal:** Maintain consistency with the GraphViewer component's better labeling system
- **Tertiary Goal:** Enhance user experience without cluttering the interface

### 1.3 Success Metrics
- Users can identify node types without clicking (measured by user testing)
- Reduced time to locate specific nodes in complex diagrams
- Positive user feedback on node readability
- No performance degradation with improved labels

---

## 2. User Stories

### 2.1 Core User Stories

**US-1: Visual Node Type Identification**
```
As a P&ID engineer
I want to see clear visual indicators of node types (instrument, valve, pump, equipment)
So that I can quickly identify components without clicking on them
```
**Acceptance Criteria:**
- Each node type has a distinct icon or visual marker
- Icons are visible at default zoom levels (0.5x - 1.5x)
- Color coding matches existing system (instruments: blue, valves: cyan, pumps: yellow, equipment: green)

**US-2: Meaningful Node Labels**
```
As a P&ID engineer
I want to see descriptive labels on nodes (not just numbers)
So that I can understand what each component represents
```
**Acceptance Criteria:**
- Nodes display component type + tag (e.g., "FIC-101" for Flow Indicator Controller)
- Labels are readable at normal zoom levels
- Long labels are truncated with ellipsis but show full text on hover

**US-3: Tag-Based Identification**
```
As a P&ID engineer
I want nodes to show their ISA instrument tags
So that I can follow industry-standard identification conventions
```
**Acceptance Criteria:**
- Nodes support ISA tag format (e.g., FIC-101, PT-205, LT-301)
- Tags are prominently displayed on the node
- Users can edit tags directly from the node info panel

**US-4: Hover Information**
```
As a P&ID engineer
I want to see detailed information when I hover over a node
So that I can get context without clicking
```
**Acceptance Criteria:**
- Hover tooltip shows: full label, type, tag, and ID
- Tooltip appears within 300ms of hover
- Tooltip doesn't obstruct nearby nodes

**US-5: Selected Node Highlighting**
```
As a P&ID engineer
I want selected nodes to be clearly highlighted
So that I know which node I'm currently working with
```
**Acceptance Criteria:**
- Selected nodes have distinct visual treatment (glow, border, or shadow)
- Selection state is visible at all zoom levels
- Only one node can be selected at a time (or multi-select is clearly indicated)

---

## 3. Functional Requirements

### 3.1 Node Label Display

**FR-1.1: Multi-Line Labels**
- Nodes shall display labels on multiple lines:
  - Line 1: Icon + Component Type
  - Line 2: Tag/Identifier
  - Line 3: Node ID (optional, smaller font)

**FR-1.2: Icon System**
- Each node type shall have a unique icon:
  - Instrument: 🎛️ or gauge icon
  - Valve: 🔧 or valve icon
  - Pump: ⚙️ or pump icon
  - Equipment: 📦 or tank icon
  - Other: ⚡ or generic icon

**FR-1.3: Font Hierarchy**
- Primary label (tag): 13px, bold, high contrast
- Secondary label (type): 10px, medium weight
- Tertiary label (ID): 9px, light weight, lower opacity

**FR-1.4: Label Truncation**
- Labels longer than node width shall be truncated with "..."
- Full label shall be visible on hover tooltip

### 3.2 Visual Styling

**FR-2.1: Color Coding**
- Maintain existing color scheme:
  - Instruments: `#61afef` (blue)
  - Valves: `#56b6c2` (cyan)
  - Pumps: `#e5c07b` (yellow)
  - Equipment: `#98c379` (green)
  - Other: `#c678dd` (purple)

**FR-2.2: Node Dimensions**
- Minimum node width: 140px (current)
- Minimum node height: 80px (increased from 70px for multi-line labels)
- Padding: 12px (current)

**FR-2.3: Selection State**
- Selected nodes shall have:
  - Glowing box shadow in node's color
  - Increased z-index (1000)
  - Optional scale transform (1.05x)

### 3.3 Interactive Features

**FR-3.1: Hover Tooltip**
- Tooltip shall display:
  ```
  Tag: FIC-101
  Type: Flow Indicator Controller
  Label: Main Feed Flow
  ID: instrument-1001
  Position: (245, 180)
  ```
- Tooltip shall use dark theme matching UI
- Tooltip shall have 300ms delay before showing

**FR-3.2: Editable Labels**
- Users shall be able to edit node labels from the Node Info Panel
- Label changes shall update immediately in the graph
- Label validation shall prevent empty or duplicate tags

**FR-3.3: Search/Filter by Label**
- Users shall be able to search nodes by label/tag
- Matching nodes shall be highlighted
- Non-matching nodes shall be dimmed

---

## 4. Non-Functional Requirements

### 4.1 Performance

**NFR-1.1: Rendering Performance**
- Node label updates shall render in < 16ms (60 FPS)
- Diagrams with 100+ nodes shall maintain smooth interactions
- No memory leaks from tooltip or label updates

**NFR-1.2: Zoom Performance**
- Labels shall remain readable at zoom levels 0.5x - 1.5x
- Font sizes shall scale appropriately with zoom
- Icons shall remain crisp at all zoom levels

### 4.2 Usability

**NFR-2.1: Accessibility**
- Labels shall have minimum contrast ratio of 4.5:1 (WCAG AA)
- Tooltips shall be keyboard accessible
- Screen readers shall announce node labels

**NFR-2.2: Consistency**
- Editor node labels shall match GraphViewer styling
- Color scheme shall be consistent across all views
- Icon system shall be reusable in other components

### 4.3 Maintainability

**NFR-3.1: Code Quality**
- Label rendering logic shall be extracted to reusable component
- Icon mapping shall be configurable via constants
- Styling shall use Tailwind classes (existing pattern)

**NFR-3.2: Testing**
- Unit tests for label formatting logic
- Visual regression tests for node rendering
- Integration tests for label editing

---

## 5. Technical Constraints

### 5.1 Technology Stack
- React 18+ with TypeScript
- ReactFlow library for graph rendering
- Tailwind CSS for styling
- Lucide React for icons

### 5.2 Browser Support
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

### 5.3 Dependencies
- Must not break existing ReactFlow functionality
- Must maintain compatibility with current node data structure
- Must work with existing drag-and-drop system

---

## 6. Out of Scope

The following are explicitly **NOT** included in this feature:

- ❌ Automatic tag generation from AI/OCR
- ❌ Custom user-defined icons
- ❌ Node grouping or clustering
- ❌ Advanced label animations
- ❌ Multi-language label support
- ❌ Label templates or presets
- ❌ Bulk label editing
- ❌ Label history/versioning

---

## 7. Dependencies

### 7.1 Internal Dependencies
- EditableGraphViewer component (primary target)
- ComponentPalette (may need updates for new node types)
- useAppStore (for selected node state)

### 7.2 External Dependencies
- ReactFlow library (current version)
- Lucide React icons (for node type icons)
- Tailwind CSS (for styling)

---

## 8. Risks and Mitigations

### 8.1 Risk: Performance Degradation
**Impact:** High  
**Probability:** Medium  
**Mitigation:** 
- Use React.memo for node components
- Implement virtual rendering for large diagrams
- Profile performance with 100+ nodes

### 8.2 Risk: Label Clutter
**Impact:** Medium  
**Probability:** Medium  
**Mitigation:**
- Use progressive disclosure (show more info on hover)
- Implement zoom-based label detail levels
- Allow users to toggle label verbosity

### 8.3 Risk: Breaking Existing Functionality
**Impact:** High  
**Probability:** Low  
**Mitigation:**
- Comprehensive testing before deployment
- Feature flag for gradual rollout
- Maintain backward compatibility with old node data

---

## 9. Open Questions

1. **Q:** Should we support custom user-defined labels beyond ISA tags?  
   **A:** TBD - gather user feedback

2. **Q:** Should labels be editable inline (double-click) or only via panel?  
   **A:** TBD - UX research needed

3. **Q:** Should we show connection point labels (inlet/outlet)?  
   **A:** TBD - may be future enhancement

4. **Q:** Should we support label templates for common equipment types?  
   **A:** TBD - out of scope for v1, consider for v2

---

## 10. Approval

**Requirements Review:**
- [ ] Product Owner
- [ ] Engineering Lead
- [ ] UX Designer
- [ ] QA Lead

**Approval Date:** _____________

**Next Steps:**
1. Review and approve requirements
2. Create technical design document
3. Break down into implementation tasks
4. Begin development sprint

---

## Appendix A: Current vs. Proposed

### Current Node Display
```
┌─────────────────┐
│   Instrument    │  ← Generic label
│                 │
└─────────────────┘
```

### Proposed Node Display
```
┌─────────────────┐
│ 🎛️ Instrument   │  ← Icon + Type
│   FIC-101       │  ← ISA Tag (bold)
│   #inst-1001    │  ← ID (small)
└─────────────────┘
```

### Hover Tooltip
```
╔═══════════════════════╗
║ Flow Indicator        ║
║ Controller            ║
║ ─────────────────     ║
║ Tag: FIC-101          ║
║ Type: Instrument      ║
║ ID: instrument-1001   ║
║ Position: (245, 180)  ║
╚═══════════════════════╝
```

---

## Appendix B: ISA Tag Format Reference

Common ISA instrument tag formats:
- **FIC-101**: Flow Indicator Controller
- **PT-205**: Pressure Transmitter
- **LT-301**: Level Transmitter
- **TIC-402**: Temperature Indicator Controller
- **PCV-503**: Pressure Control Valve
- **XV-604**: On/Off Valve

Format: `[Function][Modifier]-[Loop Number]`

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-15  
**Status:** Ready for Review
