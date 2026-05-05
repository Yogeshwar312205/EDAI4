# AI Features Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Backend running on port 8000
- Frontend running on port 5173 (or 3000)
- GOOGLE_API_KEY set in `.env` file
- P&ID image uploaded and processed

---

## Feature 1: Natural Language Graph Filtering

### Try It Now!

1. **Navigate to Graph Tab**
   - Upload a P&ID image
   - Click "Graph" tab in the header

2. **Find the Filter Panel**
   - Look for "Smart Graph Filter" in the top-left corner
   - It has a blue filter icon 🔵

3. **Try These Queries:**
   ```
   Show me all valves
   Find all pumps
   Show cooling water lines
   Find all instruments
   Show control valves
   ```

4. **See the Magic!**
   - Non-matching nodes dim to 20% opacity
   - Matching nodes stay bright
   - Count shows in the result panel

5. **Clear Filter**
   - Click the red "Clear" button
   - Graph returns to normal

### Quick Tips
- Use natural language (no special syntax needed)
- Be specific: "cooling water valves" vs "valves"
- Click quick suggestion buttons for common filters
- Works even if AI quota exceeded (fallback mode)

---

## Feature 2: Dynamic Maintenance Checklists

### Try It Now!

1. **Navigate to Graph Tab**
   - Upload a P&ID image
   - Click "Graph" tab in the header

2. **Click Any Equipment Node**
   - Click on a pump, valve, or instrument
   - Node info panel appears on the right

3. **Generate Checklist**
   - Scroll down in the node info panel
   - Click "Generate Maintenance Checklist" button (cyan color)
   - Wait 3-5 seconds for AI to generate

4. **Review Checklist**
   - See 5-10 maintenance tasks
   - Each task has:
     - Step number
     - Task description
     - Frequency (color-coded)
     - Safety notes
   - General safety warnings at top
   - Estimated time at top

5. **Export Checklist**
   - Click "Export" button at bottom
   - Downloads as `.txt` file
   - Ready to print or share

### Quick Tips
- Works for any equipment type (pump, valve, instrument, etc.)
- AI generates industry-standard tasks
- Safety warnings follow LOTO procedures
- Frequency color-coded: Red=Daily, Orange=Weekly, Yellow=Monthly
- Export includes all details in readable format

---

## Example Workflow

### Scenario: Inspect Cooling Water System

1. **Upload P&ID**
   - Drag and drop your P&ID image
   - Wait for processing (10-30 seconds)

2. **Filter for Cooling Water**
   ```
   Query: "Show me all cooling water lines"
   ```
   - Graph highlights only cooling water equipment
   - See 5 valves, 2 pumps, 3 instruments

3. **Check Pump Maintenance**
   - Click on pump node "P-101"
   - Click "Generate Maintenance Checklist"
   - Review 7 tasks:
     1. Inspect casing for leaks (Weekly)
     2. Check bearing temperature (Daily)
     3. Verify seal condition (Weekly)
     4. Lubricate bearings (Monthly)
     5. Test vibration levels (Weekly)
     6. Check alignment (Quarterly)
     7. Inspect impeller (Annual)

4. **Export and Use**
   - Click "Export"
   - Print checklist
   - Give to maintenance team

5. **Clear Filter**
   - Click "Clear" to see full graph again
   - Repeat for other systems

---

## Troubleshooting

### "Backend service unavailable"
**Solution:** Start backend
```bash
python -m uvicorn src.api.main:app --reload --port 8000
```

### "Cannot connect to backend"
**Solution:** Check backend is running
```bash
curl http://localhost:8000/health
```

### "Using fallback analysis"
**Solution:** Gemini API quota exceeded
- Wait 1 minute (15 req/min limit)
- Or use fallback mode (still works!)

### Filter not working
**Solution:** Check browser console
- Press F12
- Look for errors in Console tab
- Check Network tab for API calls

### Checklist not generating
**Solution:** Check backend logs
- Look at terminal running backend
- Check for Gemini API errors
- Verify GOOGLE_API_KEY is set

---

## Video Tutorial (Coming Soon)

1. Upload P&ID
2. Use Graph Filter
3. Generate Maintenance Checklist
4. Export and Use

---

## Next Steps

- Read full guide: `AI_FEATURES_GUIDE.md`
- Try HazOp Simulator (similar AI features)
- Explore chatbot for Q&A
- Check out design rules dashboard

---

## Support

**Issues?**
- Check `AI_FEATURES_GUIDE.md` for detailed troubleshooting
- Check backend logs for errors
- Verify GOOGLE_API_KEY is set correctly
- Try fallback mode (works without AI)

**Questions?**
- Read the full documentation
- Check API reference in guide
- Review prompt engineering section

---

## Key Shortcuts

| Action | Shortcut |
|--------|----------|
| Filter graph | Type query + Enter |
| Clear filter | Click "Clear" button |
| Generate checklist | Click node + Click button |
| Export checklist | Click "Export" in modal |
| Close checklist | Click "Close" or X |

---

## Pro Tips

### Graph Filter
- Be specific: "cooling water valves" > "valves"
- Use connections: "connected to furnace"
- Use locations: "inlet valves"
- Use functions: "flow control instruments"

### Maintenance Checklist
- Click different equipment types to see variety
- Export multiple checklists for comparison
- Review safety warnings carefully
- Adjust frequencies based on your plant
- Use as template, not final checklist

---

## What's Next?

After mastering these features, try:

1. **HazOp Simulator**
   - Right-click nodes to simulate failures
   - See cascading effects
   - Get emergency response actions

2. **Chatbot Q&A**
   - Ask questions about the P&ID
   - Get instant answers
   - Powered by same Gemini AI

3. **Design Rules**
   - Check compliance
   - Validate instrument tags
   - Review safety systems

---

## Feedback

Love these features? Have suggestions?
- Add issues to the project
- Contribute improvements
- Share your use cases

---

**Happy Filtering and Maintaining! 🎉**
