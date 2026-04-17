# Expected Errors and Warnings

This document explains errors and warnings that are NORMAL and EXPECTED during application operation.

## 400 Bad Request: /design-rules/check

### Error Message in Logs:
```
INFO:     127.0.0.1:59127 - "GET /design-rules/check HTTP/1.1" 400 Bad Request
```

### What It Means:
The frontend tried to load the Design Rules dashboard before a P&ID image was processed.

### Why It Happens:
- User navigates to the "Rules" tab before uploading an image
- Frontend automatically tries to fetch design rule violations
- Backend responds with 400 because there's no graph to check

### Is This a Problem?
**NO** - This is completely normal and expected behavior.

### How It's Handled:
The frontend displays a user-friendly message:
```
Error loading design rules. Process a P&ID first.
```

### How to Avoid:
1. Upload and process a P&ID image first
2. Then navigate to the Rules tab
3. The endpoint will return successfully

---

## Other Expected Warnings

### Coordinate Clustering Warning

```
⚠️ WARNING: Coordinates appear clustered!
   Range: 100 x 80 pixels
   This indicates a backend detection issue.
```

**What it means:** Backend is sending coordinates where all nodes are in a small area.

**Is this a problem?** YES - indicates SAHI/YOLO detection needs adjustment.

**How to fix:** See `FINAL_MINIMAP_FIX.md` for backend fixes.

---

### No Graph Loaded

```
INFO: No graph loaded. Process an image first.
```

**What it means:** User tried to access graph-dependent features before processing an image.

**Is this a problem?** NO - expected behavior.

**How to fix:** Upload and process a P&ID image.

---

## Summary

Not all errors in logs are problems! Some are expected responses to normal user behavior:

✅ **Expected (OK):**
- 400 on /design-rules/check before image processed
- "No graph loaded" messages
- Empty graph warnings

❌ **Actual Problems:**
- 500 Internal Server Error
- Coordinate clustering warnings
- Model loading failures
- Database connection errors

## When to Worry

You should investigate if you see:
- Repeated 500 errors
- Stack traces in logs
- Application crashes
- Features not working after processing image
- Persistent coordinate clustering after backend fixes

## When NOT to Worry

These are fine:
- Single 400 errors on first page load
- "No graph loaded" before processing
- Expected validation errors
- User-triggered errors (like clicking before ready)
