# HazOp Simulator - Deployment Checklist

## ✅ Pre-Deployment Checklist

### 1. Environment Setup
- [ ] `.env` file exists in project root
- [ ] `GOOGLE_API_KEY` is set in `.env`
- [ ] API key is valid (starts with `AIza`)
- [ ] Python 3.8+ installed
- [ ] Node.js 16+ installed

### 2. Backend Dependencies
```bash
# Check if installed
pip list | grep google-genai
pip list | grep fastapi
pip list | grep pydantic
pip list | grep uvicorn
```

- [ ] `google-genai` installed
- [ ] `fastapi` installed
- [ ] `pydantic` installed
- [ ] `uvicorn` installed
- [ ] `python-dotenv` installed

**If missing, install:**
```bash
pip install google-genai fastapi pydantic uvicorn python-dotenv
```

### 3. Frontend Dependencies
```bash
cd frontend
npm list reactflow
npm list axios
npm list lucide-react
npm list tailwindcss
```

- [ ] `reactflow` installed
- [ ] `axios` installed
- [ ] `lucide-react` installed
- [ ] `tailwindcss` installed
- [ ] `zustand` installed

**If missing, install:**
```bash
cd frontend
npm install
```

### 4. File Verification
- [ ] `src/api/hazop_simulator.py` exists
- [ ] `src/api/main.py` has `/api/simulate-hazop` endpoint
- [ ] `frontend/src/components/HazOpSimulator.tsx` exists
- [ ] `frontend/src/App.tsx` has HazOp tab
- [ ] `frontend/src/store/useAppStore.ts` has 'hazop' view
- [ ] `frontend/tailwind.config.js` has slide-in animation
- [ ] `frontend/src/index.css` has pulse animation

### 5. Backend Testing
```bash
# Run test script
python test_hazop_simulator.py
```

Expected output:
- [ ] ✓ API Key found
- [ ] ✓ HazOp Simulator module imported
- [ ] ✓ HazOp Simulator initialized
- [ ] ✓ TEST SCENARIO 1: PASSED
- [ ] ✓ TEST SCENARIO 2: PASSED
- [ ] ✓ ALL TESTS PASSED!

### 6. Start Backend Server
```bash
# Terminal 1
python -m uvicorn src.api.main:app --reload --port 8000
```

Verify:
- [ ] Server starts without errors
- [ ] Listening on `http://0.0.0.0:8000`
- [ ] Can access `http://localhost:8000/docs`
- [ ] `/api/simulate-hazop` endpoint visible in docs

### 7. Start Frontend Server
```bash
# Terminal 2
cd frontend
npm run dev
```

Verify:
- [ ] Server starts without errors
- [ ] Listening on `http://localhost:5173`
- [ ] No TypeScript errors
- [ ] No build errors

### 8. Browser Testing
Open `http://localhost:5173`

- [ ] Page loads without errors
- [ ] No console errors (F12)
- [ ] Can see upload interface
- [ ] Dark industrial theme applied

## 🧪 Functional Testing

### Test 1: Upload and Process P&ID
- [ ] Click upload button
- [ ] Select a P&ID file (PDF or image)
- [ ] File uploads successfully
- [ ] Processing completes
- [ ] Graph data generated
- [ ] Can see tabs: Canvas, Graph, Deliverables, Rules, Flow Sim, **HazOp**

### Test 2: Navigate to HazOp View
- [ ] Click "HazOp" tab
- [ ] React Flow canvas appears
- [ ] Nodes are visible
- [ ] Edges are visible
- [ ] Controls (zoom, pan) work
- [ ] MiniMap appears

### Test 3: Context Menu
- [ ] Right-click on a node
- [ ] Context menu appears
- [ ] Shows 4 failure modes:
  - [ ] 🔒 Stuck Closed
  - [ ] 🔓 Failed Open
  - [ ] 💧 Leaking
  - [ ] 🚫 Blocked
- [ ] Shows node ID
- [ ] Click outside to close menu

### Test 4: Simulate Failure
- [ ] Right-click a node
- [ ] Select "Stuck Closed"
- [ ] Loading message appears: "Running HazOp Simulation..."
- [ ] Wait 2-5 seconds
- [ ] Loading message disappears
- [ ] Analysis panel slides in from right

### Test 5: Analysis Panel
- [ ] Panel has red border
- [ ] Header shows "HazOp Analysis Report"
- [ ] Shows failed node ID and failure mode
- [ ] Severity badge visible (LOW/MEDIUM/HIGH/CRITICAL)
- [ ] Hazard summary displayed (2 sentences)
- [ ] Cascading effects listed (3-5 items)
- [ ] Affected nodes listed
- [ ] Affected edges listed
- [ ] Recommended actions listed (3-5 items)
- [ ] "Clear Simulation" button visible

### Test 6: Visual Effects
- [ ] Failed node has red pulsing border
- [ ] Failed node has glowing shadow
- [ ] Affected nodes have orange border
- [ ] Affected edges are red and animated
- [ ] Effects are smooth and visible

### Test 7: Clear Simulation
- [ ] Click "Clear Simulation" button
- [ ] Analysis panel disappears
- [ ] Node styles reset to default
- [ ] Edge styles reset to default
- [ ] No red/orange colors remain
- [ ] Can run another simulation

### Test 8: Multiple Simulations
- [ ] Run simulation on Node A
- [ ] Clear simulation
- [ ] Run simulation on Node B
- [ ] Results are different
- [ ] Visual effects update correctly
- [ ] No leftover effects from previous simulation

## 🔍 Edge Case Testing

### Test 9: API Errors
- [ ] Temporarily set invalid API key in `.env`
- [ ] Restart backend
- [ ] Try simulation
- [ ] Error message appears
- [ ] Fallback analysis works (if implemented)
- [ ] Restore valid API key

### Test 10: Network Errors
- [ ] Stop backend server
- [ ] Try simulation
- [ ] Error message appears
- [ ] Frontend doesn't crash
- [ ] Can retry after restarting backend

### Test 11: Large Topology
- [ ] Test with P&ID having 50+ nodes
- [ ] Simulation completes (may be slower)
- [ ] Results are reasonable
- [ ] No timeout errors

### Test 12: Empty Topology
- [ ] Test with minimal topology (1-2 nodes)
- [ ] Simulation completes
- [ ] Results make sense
- [ ] No errors

## 📊 Performance Testing

### Test 13: Response Time
- [ ] Run simulation
- [ ] Measure time from click to results
- [ ] Should be 2-5 seconds
- [ ] Visual effects appear immediately after response

### Test 14: Multiple Rapid Simulations
- [ ] Run 5 simulations in quick succession
- [ ] All complete successfully
- [ ] No rate limit errors (within 15/minute)
- [ ] UI remains responsive

### Test 15: Browser Compatibility
Test in multiple browsers:
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (if on Mac)
- [ ] All features work in each browser

## 🎨 UI/UX Testing

### Test 16: Responsive Design
- [ ] Resize browser window
- [ ] Canvas adjusts properly
- [ ] Analysis panel remains visible
- [ ] Context menu positions correctly
- [ ] No layout breaks

### Test 17: Animations
- [ ] Pulse animation is smooth
- [ ] Panel slide-in is smooth
- [ ] Edge animations are smooth
- [ ] No janky or stuttering animations

### Test 18: Accessibility
- [ ] Can navigate with keyboard (Tab key)
- [ ] Focus indicators visible
- [ ] Colors have good contrast
- [ ] Text is readable

## 🔒 Security Testing

### Test 19: API Key Protection
- [ ] API key not visible in frontend code
- [ ] API key not in browser network tab
- [ ] API key only in backend `.env`
- [ ] `.env` in `.gitignore`

### Test 20: Input Validation
- [ ] Try invalid node ID
- [ ] Try empty failure mode
- [ ] Try malformed topology
- [ ] Backend rejects invalid requests
- [ ] Frontend handles errors gracefully

## 📝 Documentation Testing

### Test 21: Documentation Completeness
- [ ] `HAZOP_SIMULATOR_GUIDE.md` exists and is complete
- [ ] `HAZOP_QUICKSTART.md` exists and is accurate
- [ ] `HAZOP_IMPLEMENTATION_SUMMARY.md` exists
- [ ] `HAZOP_ARCHITECTURE.md` exists
- [ ] `test_hazop_simulator.py` works
- [ ] All code has comments

### Test 22: Follow Quick Start Guide
- [ ] Follow `HAZOP_QUICKSTART.md` step by step
- [ ] All steps work as described
- [ ] Can complete in 5 minutes
- [ ] No missing steps

## 🚀 Production Readiness

### Test 23: Error Handling
- [ ] All errors show user-friendly messages
- [ ] No stack traces visible to users
- [ ] Errors logged to console/logs
- [ ] Application doesn't crash on errors

### Test 24: Logging
- [ ] Backend logs API calls
- [ ] Backend logs errors
- [ ] Frontend logs errors to console
- [ ] Logs are informative

### Test 25: Configuration
- [ ] Can change AI model in code
- [ ] Can adjust temperature
- [ ] Can add custom failure modes
- [ ] Can customize colors/styles

## 📋 Final Checklist

### Before Going Live
- [ ] All tests above passed
- [ ] Documentation reviewed
- [ ] Team trained on usage
- [ ] Backup plan if API fails
- [ ] Monitoring in place
- [ ] Support process defined

### Production Environment
- [ ] Environment variables set
- [ ] API key secured
- [ ] HTTPS enabled (if public)
- [ ] CORS configured correctly
- [ ] Rate limiting considered
- [ ] Backup/recovery plan

### User Training
- [ ] Quick start guide shared
- [ ] Demo session conducted
- [ ] FAQ document created
- [ ] Support contact provided
- [ ] Feedback mechanism in place

## 🎉 Deployment Complete!

Once all items are checked:
- ✅ System is fully tested
- ✅ Documentation is complete
- ✅ Team is trained
- ✅ Ready for production use

## 📞 Support Contacts

### Technical Issues
- Check `HAZOP_SIMULATOR_GUIDE.md` troubleshooting section
- Review code comments
- Check browser console (F12)
- Check backend logs

### API Issues
- Verify API key: https://ai.google.dev/
- Check quota: https://ai.google.dev/gemini-api/docs/rate-limits
- Review API docs: https://ai.google.dev/gemini-api/docs

### Feature Requests
- Document in project issues
- Discuss with team
- Prioritize and plan

---

## 📊 Test Results Summary

| Category | Tests | Passed | Failed | Notes |
|----------|-------|--------|--------|-------|
| Setup | 7 | __ | __ | |
| Functional | 8 | __ | __ | |
| Edge Cases | 4 | __ | __ | |
| Performance | 3 | __ | __ | |
| UI/UX | 3 | __ | __ | |
| Security | 2 | __ | __ | |
| Documentation | 2 | __ | __ | |
| Production | 3 | __ | __ | |
| **TOTAL** | **32** | **__** | **__** | |

**Target**: 100% pass rate before production deployment

---

**Last Updated**: May 5, 2026
**Version**: 1.0.0
**Status**: Ready for Testing
