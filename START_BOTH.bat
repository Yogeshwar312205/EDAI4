@echo off
echo ========================================
echo Starting EDAI4 - Frontend and Backend
echo ========================================
echo.

REM Start Backend in new window
echo Starting Backend on port 8000...
start "EDAI4 Backend" cmd /k "cd /d %~dp0 && python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait 3 seconds for backend to start
timeout /t 3 /nobreak >nul

REM Start Frontend in new window
echo Starting Frontend on port 3000...
start "EDAI4 Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo Both services starting...
echo ========================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to close this window...
pause >nul
