@echo off
echo ========================================
echo EDAI4 Backend Server
echo ========================================
echo.
echo Starting FastAPI server on port 8000...
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn src.api.main:app --reload --port 8000
