# Visual Mockups: Editor Node Labels Improvement

**Feature ID:** editor-node-labels-improvement  
**Created:** 2026-05-15

---

## Current State vs. Proposed State

### 🔴 BEFORE (Current Implementation)

```
Current Node Display - Hard to Identify
═══════════════════════════════════════

┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   Instrument     │  │      Valve       │  │      Pump        │
│                  │  │                  │  │                  │
└──────────────────┘  └──────────────────┘  └──────────────────┘
   (Blue gradient)       (Cyan gradient)       (Yellow gradient)

Problems:
❌ Generic labels don't tell you what the component does
❌ No visual icons to quickly identify type
❌ No industry-standard tags
❌ All nodes look similar except for color
❌ Must click to see details
```

### 🟢 AFTER (Proposed Implementation)

```
Proposed Node Display - Clear Identification
═══════════════════════════════════════════

┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ 🎛️ Instrument    │  │ 🔧 Valve         │  │ ⚙️ Pump          │
│   FIC-101        │  │   XV-205         │  │   P-301          │
│   #inst-1001     │  │   #valve-1002    │  │   #pump-1003     │
└──────────────────┘  └──────────────────┘  └──────────────────┘
   (Blue gradient)       (Cyan gradient)       (Yellow gradient)

Benefits:
✅ Icon instantly shows component type
✅ ISA tag (FIC-101) follows industry standards
✅ Clear hierarchy: Type → Tag → ID
✅ Professional appearance
✅ Quick identification without clicking
```

---

## Detailed Node Anatomy

### Standard Node (Instrument Example)

```
┌─────────────────────────────────┐
│  🎛️  Flow Indicator Controller  │  ← Line 1: Icon + Full Type Name
│      ─────────────────          │     (13px, semi-bold, white)
│         FIC-101                  │  ← Line 2: ISA Tag (PROMINENT)
│                                  │     (14px, bold, bright cyan)
│      #instrument-1001            │  ← Line 3: System ID (optional)
│                                  │     (9px, light, 60% opacity)
└─────────────────────────────────┘
     140px wide × 80px tall
     12px padding, rounded corners
     Gradient background with glow
```

### Compact Node (When Space is Limited)

```
┌──────────────────┐
│ 🎛️ FIC-101      │  ← Icon + Tag only
│   Instrument     │  ← Type below
└──────────────────┘
   120px × 60px
```

### Selected Node (With Glow Effect)

```
        ╔═══════════════════════════════╗
    ░░░░║  🎛️  Flow Indicator Controller ║░░░░
  ░░░░░░║      ─────────────────         ║░░░░░░
░░░░░░░░║         FIC-101                 ║░░░░░░░░  ← Glowing aura
  ░░░░░░║      #instrument-1001           ║░░░░░░     in node color
    ░░░░╚═══════════════════════════════╝░░░░
         
         Box shadow: 0 0 20px #61afef
         Border: 3px solid #61afef
         Z-index: 1000
         Optional: scale(1.05)
```

---

## Node Types with Icons

### All Component Types

```
INSTRUMENTS (Blue #61afef)
┌──────────────────┐
│ 🎛️ Instrument    │
│   FIC-101        │
│   Flow Control   │
└──────────────────┘

VALVES (Cyan #56b6c2)
┌──────────────────┐
│ 🔧 Valve         │
│   XV-205         │
│   Shutoff Valve  │
└──────────────────┘

PUMPS (Yellow #e5c07b)
┌──────────────────┐
│ ⚙️ Pump          │
│   P-301          │
│   Centrifugal    │
└──────────────────┘

EQUIPMENT (Green #98c379)
┌──────────────────┐
│ 📦 Equipment     │
│   T-401          │
│   Storage Tank   │
└──────────────────┘

OTHER (Purple #c678dd)
┌──────────────────┐
│ ⚡ Component     │
│   MISC-501       │
│   Generic        │
└──────────────────┘
```

---

## Hover Tooltip Design

### Tooltip Appearance

```
User hovers over node for 300ms...

                    ┌──────────────────┐
                    │ 🎛️ Instrument    │  ← Node
                    │   FIC-101        │
                    │   #inst-1001     │
                    └──────────────────┘
                            │
                            ▼
        ╔═══════════════════════════════════╗
        ║  Flow Indicator Controller        ║  ← Full name
        ║  ─────────────────────────────    ║
        ║  📋 Tag: FIC-101                  ║  ← ISA Tag
        ║  🏷️  Type: Instrument             ║  ← Component type
        ║  🆔 ID: instrument-1001           ║  ← System ID
        ║  📍 Position: (245, 180)          ║  ← Canvas position
        ║  🔗 Connections: 2 in, 1 out      ║  ← Edge count
        ╚═══════════════════════════════════╝
        
        Background: rgba(26, 31, 41, 0.95)
        Border: 1px solid #3d4556
        Padding: 12px
        Border-radius: 8px
        Box-shadow: 0 4px 12px rgba(0,0,0,0.3)
        Font: 11px, monospace
```

---

## Node Info Panel (Right Side)

### When Node is Selected

```
╔═══════════════════════════════════════════╗
║  🎛️  FIC-101                              ║  ← Header with icon + tag
║  Flow Indicator Controller                ║  ← Full name
║  ─────────────────────────────────────    ║
║                                           ║
║  📋 Details                               ║
║  ┌─────────────────────────────────────┐ ║
║  │ Type:     Instrument                │ ║
║  │ Tag:      FIC-101                   │ ║  ← Editable field
║  │ ID:       instrument-1001           │ ║
║  │ Position: (245, 180)                │ ║
║  │ Created:  2026-05-15                │ ║
║  └─────────────────────────────────────┘ ║
║                                           ║
║  🔗 Connections (3)                       ║
║  ┌─────────────────────────────────────┐ ║
║  │ ← From: P-301 (Pump)                │ ║
║  │ → To: XV-205 (Valve)                │ ║
║  │ → To: T-401 (Tank)                  │ ║
║  └─────────────────────────────────────┘ ║
║                                           ║
║  [Edit Label]  [Delete Node]             ║
╚═══════════════════════════════════════════╝
```

---

## Zoom Level Behavior

### Zoom Out (0.5x) - Simplified Labels

```
┌────────┐  ┌────────┐  ┌────────┐
│🎛️ FIC  │  │🔧 XV   │  │⚙️ P    │  ← Show icon + abbreviated tag
│  101   │  │  205   │  │  301   │
└────────┘  └────────┘  └────────┘
   60px        60px        60px
```

### Normal Zoom (1.0x) - Full Labels

```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ 🎛️ Instrument    │  │ 🔧 Valve         │  │ ⚙️ Pump          │
│   FIC-101        │  │   XV-205         │  │   P-301          │
│   #inst-1001     │  │   #valve-1002    │  │   #pump-1003     │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

### Zoom In (1.5x) - Maximum Detail

```
┌─────────────────────────────────┐
│  🎛️  Flow Indicator Controller  │  ← Full type name
│      ─────────────────          │
│         FIC-101                  │  ← ISA Tag
│    Main Feed Flow Control        │  ← Description
│      #instrument-1001            │  ← System ID
│                                  │
│  Status: ● Active                │  ← Additional info
└─────────────────────────────────┘
```

---

## Color Scheme Reference

### Node Colors (Existing - Maintained)

```
INSTRUMENTS
Background: linear-gradient(135deg, #61afef 0%, #61afefdd 100%)
Border: 2px solid #61afef
Shadow: 0 4px 6px #61afef40

VALVES
Background: linear-gradient(135deg, #56b6c2 0%, #56b6c2dd 100%)
Border: 2px solid #56b6c2
Shadow: 0 4px 6px #56b6c240

PUMPS
Background: linear-gradient(135deg, #e5c07b 0%, #e5c07bdd 100%)
Border: 2px solid #e5c07b
Shadow: 0 4px 6px #e5c07b40

EQUIPMENT
Background: linear-gradient(135deg, #98c379 0%, #98c379dd 100%)
Border: 2px solid #98c379
Shadow: 0 4px 6px #98c37940

OTHER
Background: linear-gradient(135deg, #c678dd 0%, #c678dddd 100%)
Border: 2px solid #c678dd
Shadow: 0 4px 6px #c678dd40
```

### Selection Glow

```
Selected Node:
Box-shadow: 0 0 20px [node-color], 0 0 40px [node-color]80
Border-width: 3px
Z-index: 1000
Transform: scale(1.05) (optional)
```

---

## Typography Hierarchy

```
PRIMARY LABEL (ISA Tag)
Font: 14px
Weight: 700 (bold)
Color: #ffffff
Line-height: 1.2
Letter-spacing: 0.5px
Example: FIC-101

SECONDARY LABEL (Type)
Font: 11px
Weight: 600 (semi-bold)
Color: #ffffff
Opacity: 0.9
Example: Flow Indicator Controller

TERTIARY LABEL (ID)
Font: 9px
Weight: 400 (regular)
Color: #ffffff
Opacity: 0.6
Example: #instrument-1001

ICON
Size: 16px × 16px
Color: #ffffff
Opacity: 1.0
```

---

## Responsive Behavior

### Small Nodes (< 100px width)

```
┌────────┐
│ 🎛️     │  ← Icon only
│ FIC    │  ← Abbreviated tag
│ 101    │
└────────┘
```

### Medium Nodes (100-140px width)

```
┌──────────────┐
│ 🎛️ Inst.    │  ← Icon + abbreviated type
│   FIC-101    │  ← Full tag
└──────────────┘
```

### Large Nodes (> 140px width)

```
┌──────────────────┐
│ 🎛️ Instrument    │  ← Icon + full type
│   FIC-101        │  ← Full tag
│   #inst-1001     │  ← System ID
└──────────────────┘
```

---

## Edge Cases

### Long Labels

```
BEFORE TRUNCATION:
┌──────────────────┐
│ 🎛️ Very Long Flo │  ← Text overflow
│   w Indicator Co │
│   ntroller Name  │
└──────────────────┘

AFTER TRUNCATION:
┌──────────────────┐
│ 🎛️ Very Long...  │  ← Ellipsis
│   FIC-101        │  ← Tag always visible
│   #inst-1001     │
└──────────────────┘
     ↓ Hover to see full text
```

### Untagged Nodes

```
┌──────────────────┐
│ 🎛️ Instrument    │
│   UNTAGGED       │  ← Placeholder in red/orange
│   #inst-1001     │
└──────────────────┘
```

### Duplicate Tags (Validation Error)

```
┌──────────────────┐
│ 🎛️ Instrument    │
│   FIC-101 ⚠️     │  ← Warning icon
│   Duplicate!     │  ← Error message
└──────────────────┘
     Red border
```

---

## Animation & Transitions

### Selection Animation

```
Frame 1 (0ms):     Frame 2 (100ms):   Frame 3 (200ms):
┌────────┐         ┌────────┐         ┌────────┐
│ Node   │   →     │ Node   │   →     │ Node   │
└────────┘         └────────┘         └────────┘
Normal             Glow starts        Full glow
                   Scale 1.02         Scale 1.05
```

### Hover Tooltip Animation

```
Frame 1 (0ms):     Frame 2 (300ms):   Frame 3 (400ms):
                   ╔═══════╗          ╔═══════════╗
Hover starts  →    ║ Fade  ║    →     ║ Full Info ║
                   ╚═══════╝          ╚═══════════╝
                   Opacity 0          Opacity 1
                                      Slide down 5px
```

---

## Accessibility Features

### High Contrast Mode

```
┌──────────────────┐
│ 🎛️ Instrument    │  ← White text on dark background
│   FIC-101        │     Contrast ratio: 7:1 (AAA)
│   #inst-1001     │
└──────────────────┘
     Thicker borders (3px)
     Higher contrast colors
```

### Screen Reader Announcement

```
When node is selected:
"Instrument node, tag FIC-101, Flow Indicator Controller, 
 ID instrument-1001, position 245 by 180, 
 2 incoming connections, 1 outgoing connection"
```

### Keyboard Navigation

```
Tab:        Select next node
Shift+Tab:  Select previous node
Enter:      Open node details panel
Delete:     Delete selected node
Escape:     Deselect node
Arrow keys: Move selected node (in edit mode)
```

---

## Implementation Priority

### Phase 1: Core Labels (Week 1)
✅ Multi-line label layout
✅ Icon system
✅ ISA tag display
✅ Font hierarchy

### Phase 2: Interactivity (Week 1)
✅ Hover tooltips
✅ Selection highlighting
✅ Label editing

### Phase 3: Polish (Week 2)
✅ Animations
✅ Zoom-based detail levels
✅ Accessibility features
✅ Edge case handling

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-15  
**Status:** Ready for Review
