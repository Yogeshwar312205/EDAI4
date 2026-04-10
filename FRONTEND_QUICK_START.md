# EDAI4 Frontend - Quick Start Guide

## ⚡ 5-Minute Setup

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Start Backend
```bash
# In another terminal, from EDAI4 root
python -m uvicorn src.api.main:app --reload --port 8000
```

### 3. Start Frontend
```bash
npm run dev
```

### 4. Open Browser
Navigate to `http://localhost:3000`

## 🎯 Test the Features

### Upload P&ID
1. Drag & drop an image or click to browse
2. Wait for processing (~2-5 seconds)
3. View results in canvas and table

### Interactive Canvas
- **Pan**: Click and drag
- **Zoom**: Mouse wheel
- **Hover**: See tooltips
- **Select**: Click bounding box

### Cross-Linked Table
- **Search**: Type in search box
- **Sort**: Click column headers
- **Filter**: Use search to filter rows
- **Zoom**: Click any row → canvas zooms to detection ✨

### Graph View
- Click "Graph" tab in header
- **Drag**: Move nodes around
- **Zoom**: Mouse wheel
- **Select**: Click node

## 📦 Tech Stack Summary

| Feature | Library | Why |
|---------|---------|-----|
| Canvas | React-Konva | Hardware-accelerated, smooth pan/zoom |
| Table | TanStack Table | Powerful, flexible, 14KB |
| Graph | React Flow | Modern, physics-based, draggable |
| State | Zustand | Lightweight, 1KB, perfect for cross-linking |
| Styling | Tailwind CSS | Utility-first, custom dark theme |

## 🔧 Common Commands

```bash
# Development
npm run dev          # Start dev server (port 3000)

# Production
npm run build        # Build for production
npm run preview      # Preview production build

# Linting
npm run lint         # Check code quality
```

## 🐛 Quick Troubleshooting

### Canvas not showing?
- Check browser console for errors
- Verify image uploaded successfully
- Ensure backend is running

### Table-Canvas sync not working?
- Click a table row
- Canvas should zoom to that detection
- Check Zustand store in React DevTools

### Backend connection failed?
- Verify backend is running: `curl http://localhost:8000/health`
- Check Vite proxy config in `vite.config.ts`

## 📚 Documentation

- **Full Setup**: `FRONTEND_SETUP_GUIDE.md`
- **Architecture**: `FRONTEND_ARCHITECTURE.md`
- **Component Docs**: `frontend/README.md`

## 🎉 Success Checklist

- [ ] Frontend runs on `http://localhost:3000`
- [ ] Can upload P&ID image
- [ ] Canvas displays with bounding boxes
- [ ] Can pan and zoom smoothly
- [ ] Table displays all detections
- [ ] **Clicking table row zooms canvas** ✨
- [ ] Graph view shows topology

## 🚀 Next Steps

1. Customize theme colors in `tailwind.config.js`
2. Add more features (RAG queries, export, etc.)
3. Deploy to production

---

**You're ready to go!** Upload a P&ID and explore the interactive features.
