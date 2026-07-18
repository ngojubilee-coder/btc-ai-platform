@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title BTC AI Platform - Demarrage VPS
color 0B

echo.
echo  === BTC AI PLATFORM - DEMARRAGE LOCAL VPS ===
echo.

set "ROOT=%~dp0"
cd /d "%ROOT%"

:: Tuer les processus existants sur les ports 3000 et 8000
echo  [i] Nettoyage des ports 3000 et 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000.*LISTENING" 2^>nul') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING" 2^>nul') do taskkill /PID %%a /F >nul 2>&1

:: --- Demarrer le Backend ---
echo  [1/2] Demarrage du Backend - FastAPI...
start "BTC-AI-Backend" /d "%ROOT%backend" cmd /k "call .venv\Scripts\activate.bat && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

:: Attendre que le backend demarre
echo      Attente du backend...
timeout /t 5 /nobreak >nul

:: --- Demarrer le Frontend ---
echo  [2/2] Demarrage du Frontend - Next.js...
start "BTC-AI-Frontend" /d "%ROOT%frontend" cmd /k "npm run dev"

:: Attendre que le frontend demarre
echo      Attente du frontend...
timeout /t 8 /nobreak >nul

:: --- Verification ---
echo.
echo  [i] Verification des services...
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8000/health' -TimeoutSec 5 -UseBasicParsing; Write-Host '  Backend:  OK (' $r.StatusCode ')' -ForegroundColor Green } catch { Write-Host '  Backend:  EN COURS DE DEMARRAGE...' -ForegroundColor Yellow }"
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:3000' -TimeoutSec 5 -UseBasicParsing; Write-Host '  Frontend: OK (' $r.StatusCode ')' -ForegroundColor Green } catch { Write-Host '  Frontend: EN COURS DE DEMARRAGE...' -ForegroundColor Yellow }"

echo.
echo  ========================================
echo  === PLATFORME DEMARREE ===
echo  ========================================
echo.
echo  Frontend:  http://localhost:3000
echo  Backend:   http://localhost:8000
echo  API Docs:  http://localhost:8000/docs
echo  Health:    http://localhost:8000/health
echo.
echo  Pour arreter: fermez les 2 fenetres ou lancez stop-vps.bat
echo.

:: Ouvrir le navigateur
echo  [i] Ouverture du navigateur...
timeout /t 3 /nobreak >nul
start http://localhost:3000

pause
