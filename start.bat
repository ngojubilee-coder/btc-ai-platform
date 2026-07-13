@echo off
echo Starting BTC AI Platform...
echo.

echo Starting backend (port 8000)...
start "BTC AI Backend" cmd /k "cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo Starting frontend (port 3000)...
start "BTC AI Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Backend: http://localhost:8000/docs
echo Frontend: http://localhost:3000
echo.
