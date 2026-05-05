# HazOp Simulator - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Verify Installation (30 seconds)

```bash
# Test the backend
python test_hazop_simulator.py
```

Expected output:
```
✓ API Key found
✓ HazOp Simulator module imported successfully
✓ Simulation completed successfully!
✓ ALL TESTS PASSED!
```

### Step 2: Start the Servers (1 minute)

**Terminal 1 - Backend:**
```bash
python -m uvicorn src.api.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Step 3: Use the Simulator (3 minutes)

1. **Open browser**: http://localhost:5173
2. **Upload a P&ID** and process it
3. **Click "HazOp" tab** in the navigation
4. **Right-click any node** on the canvas
5. **Select a failure mode** (e.g., "Stuck Closed")
6. **Wait 2-5 seconds** for AI analysis
7. **Review results** in the sliding panel

## 🎯 What You'll See

### Context Menu (Right-click on node)
```
┌─────────────────────────┐
│ ⚡ Simulate Failure      │
│ Node: V-101             │
├─────────────────────────┤
│ 🔒 Stuck Closed         │
│ 🔓 Failed Open          │
│ 💧 Leaking              │
│ 🚫 Blocked              │
└─────────────────────────┘
```

### Analysis Panel (After simulation)
```
┌──────────────────────────────────┐
│ ⚠️  HazOp Analysis Report        │
│ V-101 - Stuck Closed             │
├──────────────────────────────────┤
│ 🛡️ SEVERITY: HIGH                │
├──────────────────────────────────┤
│ ⚠️  Immediate Hazard             │
│ Control valve V-101 failure      │
│ causes pressure buildup...       │
├──────────────────────────────────┤
│ 📊 Cascading Effects             │
│ ▸ Pressure buildup in feed line  │
│ ▸ Pump P-101 may cavitate        │
│ ▸ Tank T-101 overpressure risk   │
├──────────────────────────────────┤
│ 🎯 Affected Equipment            │
│ Nodes: P-101, T-101, V-102       │
│ Edges: e1, e2, e3                │
├──────────────────────────────────┤
│ 🛡️ Emergency Response            │
│ 1. Activate emergency shutdown   │
│ 2. Isolate affected section      │
│ 3. Monitor pressure readings     │
└──────────────────────────────────┘
```

### Visual Effects
- **Failed Node**: 🔴 Red pulsing glow
- **Affected Nodes**: 🟠 Orange border
- **Affected Edges**: 🔴 Animated red lines

## 🔧 Troubleshooting

### Problem: Test script fails
```bash
# Install missing package
pip install google-genai

# Verify .env file has API key
cat .env | grep GOOGLE_API_KEY
```

### Problem: Backend won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Use different port
python -m uvicorn src.api.main:app --reload --port 8001
```

### Problem: Frontend won't start
```bash
# Reinstall dependencies
cd frontend
rm -rf node_modules
npm install
npm run dev
```

### Problem: Context menu doesn't appear
- Make sure you're **right-clicking on a NODE** (not empty space)
- Check browser console for errors (F12)
- Verify you're on the "HazOp" tab

### Problem: "API quota exceeded"
- Free tier: 15 requests/minute
- Wait 1 minute and try again
- Or upgrade at: https://ai.google.dev/pricing

## 📊 Example Scenarios to Try

### Scenario 1: Valve Failure
- **Node**: Any valve (V-xxx)
- **Mode**: "Stuck Closed"
- **Expected**: Pressure buildup, flow blockage

### Scenario 2: Pump Failure
- **Node**: Any pump (P-xxx)
- **Mode**: "Failed Open"
- **Expected**: Loss of pressure, flow disruption

### Scenario 3: Tank Leak
- **Node**: Any tank (T-xxx)
- **Mode**: "Leaking"
- **Expected**: Material loss, environmental hazard

### Scenario 4: Pipe Blockage
- **Node**: Any pipe connection
- **Mode**: "Blocked"
- **Expected**: Flow restriction, pressure changes

## 🎓 Understanding the Results

### Severity Levels
- 🟢 **LOW**: Minor impact, easy to control
- 🟡 **MEDIUM**: Moderate impact, requires attention
- 🟠 **HIGH**: Serious impact, immediate action needed
- 🔴 **CRITICAL**: Catastrophic impact, emergency response

### Cascading Effects
Shows how the failure propagates through the system:
1. **Immediate**: Direct impact on connected equipment
2. **Secondary**: Effects on downstream processes
3. **Tertiary**: System-wide consequences

### Affected Equipment
- **Nodes**: Equipment that will experience abnormal conditions
- **Edges**: Pipes/lines with flow/pressure changes

### Emergency Actions
Prioritized list of response steps:
1. **Immediate**: Stop the hazard
2. **Containment**: Prevent spread
3. **Monitoring**: Track conditions
4. **Recovery**: Return to normal

## 🎉 Success Checklist

- ✅ Test script passes
- ✅ Backend server running (port 8000)
- ✅ Frontend server running (port 5173)
- ✅ Can upload and process P&ID
- ✅ Can see graph in "HazOp" tab
- ✅ Context menu appears on right-click
- ✅ Simulation completes in 2-5 seconds
- ✅ Analysis panel shows results
- ✅ Visual effects appear on canvas
- ✅ Can clear simulation and reset

## 📚 Next Steps

1. **Read the full guide**: `HAZOP_SIMULATOR_GUIDE.md`
2. **Customize failure modes**: Edit `HazOpSimulator.tsx`
3. **Adjust AI behavior**: Edit `hazop_simulator.py`
4. **Test with real data**: Use your actual P&IDs
5. **Train your team**: Share this guide

## 🆘 Need Help?

### Check These Files
- `HAZOP_SIMULATOR_GUIDE.md` - Complete documentation
- `test_hazop_simulator.py` - Backend test script
- `src/api/hazop_simulator.py` - Backend implementation
- `frontend/src/components/HazOpSimulator.tsx` - Frontend component

### Common Issues
1. **Import errors**: Run `pip install google-genai`
2. **API errors**: Check `.env` has valid `GOOGLE_API_KEY`
3. **UI errors**: Check browser console (F12)
4. **Network errors**: Verify backend is running on port 8000

### Still Stuck?
1. Check the troubleshooting section in `HAZOP_SIMULATOR_GUIDE.md`
2. Review the code comments for detailed explanations
3. Test with the sample data in `test_hazop_simulator.py`

---

**You're all set! Start simulating failures and exploring safety scenarios! 🚀**
