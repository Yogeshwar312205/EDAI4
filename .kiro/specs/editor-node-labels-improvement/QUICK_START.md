# Quick Start Guide: Editor Node Labels Improvement

**Feature:** Enhanced node identification in P&ID Editor  
**Status:** ✅ Ready to Test

---

## 🚀 How to Test

### 1. Start the Frontend

```bash
cd frontend
npm run dev
```

The app will open at `http://localhost:5173` (or similar)

### 2. Navigate to Editor

1. Upload a P&ID image (or use existing processed image)
2. Click on the **"Editor"** tab
3. Enable **Edit Mode** (toggle button at top)

### 3. Test New Features

#### ✅ Create New Nodes
1. Drag components from the left palette:
   - Instrument
   - Valve
   - Pump
   - Equipment
2. Drop them on the canvas
3. **Observe:** Each node now shows:
   - Icon (🎛️, 🔧, ⚙️, 📦)
   - Component type
   - ISA tag (e.g., FIC-101, XV-205)
   - System ID

#### ✅ Hover Tooltips
1. Hover over any node
2. Wait 300ms
3. **Observe:** Tooltip appears showing:
   - Full description
   - Tag, Type, ID
   - Position coordinates
   - Connection count

#### ✅ Selection Highlighting
1. Click on any node
2. **Observe:** 
   - Node glows in its color
   - Border becomes thicker
   - Pulsing animation
   - Info panel appears on left

#### ✅ Edit ISA Tags
1. Select a node
2. Look at the info panel on the left
3. Click **"Edit ISA Tag"** button
4. Enter new tag (e.g., "PT-205")
5. **Observe:** Node label updates immediately

#### ✅ Multiple Node Types
1. Create one of each type:
   - Instrument → Blue with 🎛️ icon, tag FIC-101
   - Valve → Cyan with 🔧 icon, tag XV-201
   - Pump → Yellow with ⚙️ icon, tag P-301
   - Equipment → Green with 📦 icon, tag T-401
2. **Observe:** Each has distinct color and icon

---

## 🎨 What You Should See

### Before (Old Nodes)
```
┌──────────────────┐
│   Instrument     │  ← Generic label
│                  │
└──────────────────┘
```

### After (New Nodes)
```
┌──────────────────┐
│ 🎛️ Instrument    │  ← Icon + Type
│   FIC-101        │  ← ISA Tag (bold)
│   #1001          │  ← System ID
└──────────────────┘
```

### With Hover
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
        ╚═══════════════════════════════════╝
```

---

## 🧪 Test Scenarios

### Scenario 1: Create a Simple Flow Control Loop
1. Drag an **Instrument** → Should show FIC-101
2. Drag a **Valve** → Should show XV-201
3. Connect them with an edge
4. Hover over each → Should see full details
5. Select instrument → Edit tag to "FIC-100"

**Expected:** All features work smoothly, labels are clear

### Scenario 2: Build a Complex Diagram
1. Create 10+ nodes of different types
2. Connect them with edges
3. Zoom in and out
4. Pan around the canvas
5. Select different nodes

**Expected:** Performance is smooth, no lag, labels remain readable

### Scenario 3: Edit Multiple Tags
1. Create 5 instruments
2. Edit each tag to follow a sequence:
   - FIC-101, FIC-102, FIC-103, FIC-104, FIC-105
3. Verify each updates correctly

**Expected:** Tags update immediately, no conflicts

---

## 🐛 What to Look For

### ✅ Good Signs
- Icons display correctly for each type
- ISA tags are bold and prominent
- Tooltips appear after 300ms hover
- Selection glow is visible
- Colors match node types
- Info panel shows correct data
- Edit button works

### ❌ Issues to Report
- Icons not showing
- Tooltips not appearing
- Selection not highlighting
- Tags not updating
- Performance lag
- Layout issues
- Missing information

---

## 📊 ISA Tag Examples

### Valid Tags
- **FIC-101** - Flow Indicator Controller #101
- **PT-205** - Pressure Transmitter #205
- **TIC-301** - Temperature Indicator Controller #301
- **LT-402** - Level Transmitter #402
- **XV-503** - On/Off Valve #503
- **P-601** - Pump #601

### Tag Format
```
[Variable][Modifiers]-[Number][Suffix]

F = Flow
P = Pressure
T = Temperature
L = Level

I = Indicator
C = Controller
T = Transmitter
V = Valve
```

---

## 🎯 Success Criteria

The feature is working correctly if:

1. ✅ All new nodes show icons, type, tag, and ID
2. ✅ Tooltips appear on hover with full details
3. ✅ Selected nodes have glowing effect
4. ✅ ISA tags can be edited from info panel
5. ✅ Different node types have different colors/icons
6. ✅ Performance is smooth with 10+ nodes
7. ✅ No console errors
8. ✅ Layout is clean and professional

---

## 🔧 Troubleshooting

### Issue: Icons not showing
**Solution:** Check that Lucide React is installed
```bash
npm install lucide-react
```

### Issue: Tooltips not appearing
**Solution:** Check browser console for errors, verify NodeTooltip component is imported

### Issue: Styles not applied
**Solution:** Restart dev server
```bash
npm run dev
```

### Issue: TypeScript errors
**Solution:** Check that all imports are correct, run:
```bash
npm run build
```

---

## 📝 Feedback

After testing, please provide feedback on:

1. **Visual Clarity:** Are nodes easy to identify?
2. **ISA Tags:** Are they prominent enough?
3. **Tooltips:** Is the information useful?
4. **Performance:** Any lag or slowness?
5. **Usability:** Is editing tags intuitive?
6. **Suggestions:** Any improvements or additions?

---

## 🎉 Next Steps

Once testing is complete:

1. ✅ Gather feedback
2. ✅ Make any necessary adjustments
3. ✅ Update documentation
4. ✅ Deploy to production
5. ✅ Train users on new features

---

**Happy Testing!** 🚀

If you encounter any issues or have questions, refer to:
- [REQUIREMENTS.md](./REQUIREMENTS.md) - Detailed requirements
- [MOCKUPS.md](./MOCKUPS.md) - Visual examples
- [TASKS.md](./TASKS.md) - Implementation details
