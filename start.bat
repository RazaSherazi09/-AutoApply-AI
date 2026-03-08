@echo off
echo ===================================================
echo       Starting AutoApply AI (Clean Restart)
echo ===================================================
echo.
echo [1/3] Terminating any stuck background processes...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1
echo Done.
echo.

echo [2/3] Launching FastAPI Backend...
start "AutoApply AI - Backend" cmd /k "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
echo Backend starting in a new window...
echo.

echo [3/3] Launching Next.js Frontend...
start "AutoApply AI - Frontend" cmd /k "cd frontend && npm run dev"
echo Frontend starting in a new window...
echo.

echo ===================================================
echo   System is booting up natively! 
echo   Frontend will be available at: http://localhost:3000
echo   Backend is running at: http://localhost:8000
echo ===================================================
pause
