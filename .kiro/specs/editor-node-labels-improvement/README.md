# Editor Node Labels Improvement - Spec Overview

**Feature ID:** `editor-node-labels-improvement`  
**Status:** 📝 Requirements Phase  
**Priority:** 🔥 High  
**Estimated Timeline:** 1-2 weeks

---

## 🎯 What This Feature Does

Improves node identification in the P&ID Editor by adding:
- **Visual Icons** for each component type (🎛️ instruments, 🔧 valves, ⚙️ pumps, 📦 equipment)
- **ISA Standard Tags** (FIC-101, PT-205, etc.) for professional identification
- **Multi-line Labels** with clear hierarchy (Type → Tag → ID)
- **Hover Tooltips** showing detailed information
- **Better Selection** with glowing effects

---

## 📋 Current Problem

**Before:**
```
┌──────────────────┐
│   Instrument     │  ← Generic, hard to identify
│                  │
└──────────────────┘
```

Users can't quickly identify what nodes represent without clicking on them.

---

## ✨ Proposed Solution

**After:**
```
┌──────────────────┐
│ 🎛️ Instrument    │  ← Icon + Type
│   FIC-101        │  ← ISA Tag (bold)
│   #inst-1001     │  ← System ID
└──────────────────┘
```

Clear, professional, industry-standard identification at a glance!

---

## 📚 Documentation

| Document | Description | Status |
|----------|-------------|--------|
| [SPEC.md](./SPEC.md) | High-level overview and summary | ✅ Complete |
| [REQUIREMENTS.md](./REQUIREMENTS.md) | Detailed functional requirements | ✅ Complete |
| [MOCKUPS.md](./MOCKUPS.md) | Visual designs and mockups | ✅ Complete |
| [DESIGN.md](./DESIGN.md) | Technical design document | ⏳ Pending |
| [TASKS.md](./TASKS.md) | Implementation task breakdown | ⏳ Pending |

---

## 🎨 Key Features

### 1. Enhanced Node Labels
- **Multi-line display:** Icon + Type, Tag, ID
- **Font hierarchy:** Bold tags, lighter IDs
- **Smart truncation:** Ellipsis for long labels

### 2. Icon System
- **Unique icons** for each component type
- **Color-coded** to match existing scheme
- **Scalable** at all zoom levels

### 3. ISA Tag Support
- **Standard format:** FIC-101, PT-205, LT-301
- **Editable** from node info panel
- **Validation** to prevent duplicates

### 4. Interactive Tooltips
- **Full details** on hover (300ms delay)
- **Dark theme** matching UI
- **Comprehensive info:** Tag, Type, ID, Position, Connections

### 5. Selection Highlighting
- **Glowing effect** in node's color
- **Increased z-index** for visibility
- **Clear feedback** for user actions

---

## 📊 User Stories

### US-1: Visual Node Type Identification
> As a P&ID engineer, I want to see clear visual indicators of node types so that I can quickly identify components without clicking on them.

**Acceptance Criteria:**
- ✅ Each node type has a distinct icon
- ✅ Icons visible at default zoom levels
- ✅ Color coding matches existing system

### US-2: Meaningful Node Labels
> As a P&ID engineer, I want to see descriptive labels on nodes so that I can understand what each component represents.

**Acceptance Criteria:**
- ✅ Nodes display component type + tag
- ✅ Labels readable at normal zoom
- ✅ Long labels truncated with ellipsis

### US-3: Tag-Based Identification
> As a P&ID engineer, I want nodes to show their ISA instrument tags so that I can follow industry-standard identification conventions.

**Acceptance Criteria:**
- ✅ Nodes support ISA tag format
- ✅ Tags prominently displayed
- ✅ Users can edit tags from panel

### US-4: Hover Information
> As a P&ID engineer, I want to see detailed information when I hover over a node so that I can get context without clicking.

**Acceptance Criteria:**
- ✅ Tooltip shows full details
- ✅ Appears within 300ms
- ✅ Doesn't obstruct nearby nodes

### US-5: Selected Node Highlighting
> As a P&ID engineer, I want selected nodes to be clearly highlighted so that I know which node I'm currently working with.

**Acceptance Criteria:**
- ✅ Distinct visual treatment (glow)
- ✅ Visible at all zoom levels
- ✅ Clear selection state

---

## 🎯 Success Metrics

- ✅ Users can identify node types without clicking
- ✅ Reduced time to locate specific nodes
- ✅ No performance degradation with 100+ nodes
- ✅ Consistent styling with GraphViewer
- ✅ Positive user feedback on readability

---

## 🛠️ Technical Stack

- **Frontend:** React 18+ with TypeScript
- **Graph Library:** ReactFlow
- **Styling:** Tailwind CSS
- **Icons:** Lucide React
- **State:** Zustand (useAppStore)

---

## 📅 Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| **Requirements** | 1 day | ✅ Complete |
| **Design** | 1 day | Create technical design doc |
| **Implementation** | 3-5 days | Build features |
| **Testing** | 2 days | Unit + integration tests |
| **Total** | **1-2 weeks** | |

---

## 🚀 Next Steps

### For You to Review:

1. **Read [REQUIREMENTS.md](./REQUIREMENTS.md)** - Detailed functional requirements
2. **Check [MOCKUPS.md](./MOCKUPS.md)** - Visual designs and examples
3. **Review [SPEC.md](./SPEC.md)** - High-level summary

### Questions to Answer:

1. ✅ Do the proposed node labels meet your needs?
2. ✅ Are the ISA tag formats correct for your use case?
3. ✅ Should we support custom user-defined labels?
4. ✅ Should labels be editable inline (double-click)?
5. ✅ Any additional information to display on nodes?

### After Approval:

1. ⏳ Create technical design document (DESIGN.md)
2. ⏳ Break down into implementation tasks (TASKS.md)
3. ⏳ Begin development sprint
4. ⏳ Implement and test features

---

## 🎨 Visual Preview

### Current vs. Proposed

**BEFORE (Current):**
```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   Instrument     │  │      Valve       │  │      Pump        │
│                  │  │                  │  │                  │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

**AFTER (Proposed):**
```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ 🎛️ Instrument    │  │ 🔧 Valve         │  │ ⚙️ Pump          │
│   FIC-101        │  │   XV-205         │  │   P-301          │
│   #inst-1001     │  │   #valve-1002    │  │   #pump-1003     │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

**With Selection:**
```
    ░░░░╔══════════════════╗░░░░
  ░░░░░░║ 🎛️ Instrument    ║░░░░░░
░░░░░░░░║   FIC-101        ║░░░░░░░░  ← Glowing effect
  ░░░░░░║   #inst-1001     ║░░░░░░
    ░░░░╚══════════════════╝░░░░
```

**With Hover Tooltip:**
```
                    ┌──────────────────┐
                    │ 🎛️ Instrument    │
                    │   FIC-101        │
                    └──────────────────┘
                            │
                            ▼
        ╔═══════════════════════════════════╗
        ║  Flow Indicator Controller        ║
        ║  ─────────────────────────────    ║
        ║  📋 Tag: FIC-101                  ║
        ║  🏷️  Type: Instrument             ║
        ║  🆔 ID: instrument-1001           ║
        ║  📍 Position: (245, 180)          ║
        ║  🔗 Connections: 2 in, 1 out      ║
        ╚═══════════════════════════════════╝
```

---

## ❓ FAQ

### Q: Will this break existing diagrams?
**A:** No! The feature is backward compatible. Existing nodes will automatically get the new labels.

### Q: Can users customize the icons?
**A:** Not in v1. This is out of scope but could be added in v2 based on feedback.

### Q: Will this slow down the editor?
**A:** No. We'll use React.memo and optimize rendering to maintain 60 FPS even with 100+ nodes.

### Q: Can I turn off the new labels?
**A:** Not planned for v1, but we can add a toggle if users request it.

### Q: Will this work on mobile?
**A:** Yes! The labels are responsive and will adapt to smaller screens.

---

## 📞 Contact

**Questions or feedback?**
- Review the detailed docs in this folder
- Approve the requirements to proceed to design phase
- Request changes or additions as needed

---

## ✅ Approval Checklist

Before proceeding to design phase:

- [ ] Requirements reviewed and approved
- [ ] Visual mockups meet expectations
- [ ] User stories cover all use cases
- [ ] Success metrics are clear
- [ ] Timeline is acceptable
- [ ] No major concerns or blockers

**Once approved, we'll create the technical design and start implementation!**

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-15  
**Status:** 📝 Ready for Review
