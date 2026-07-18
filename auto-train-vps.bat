@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title BTC AI Platform - Entrainement Automatique
color 0C

echo.
echo  === BTC AI PLATFORM - ENTRAINEMENT AUTOMATIQUE ===
echo.

set "ROOT=%~dp0"
cd /d "%ROOT%backend"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo  [!] venv absent. Lancez install-vps.bat d abord.
    exit /b 1
)

:: Argument: modele (xgboost, random_forest, lstm, ou compare)
set "MODEL=%1"
if "%MODEL%"=="" set "MODEL=xgboost"

set "LOGFILE=%ROOT%data\training_log.txt"
if not exist "%ROOT%data" mkdir "%ROOT%data"

echo  [i] Modele: %MODEL%
echo  [i] Heure de debut: %time%
echo  [i] Log: %LOGFILE%
echo.

echo [%date% %time%] === DEBUT entrainement %MODEL% === >> "%LOGFILE%"

if "%MODEL%"=="compare" (
    python train.py --compare --backtest
) else (
    python train.py --model %MODEL% --backtest
)

if %errorLevel% neq 0 (
    echo [%date% %time%] [ECHEC] Entrainement %MODEL% - code erreur %errorLevel% >> "%LOGFILE%"
    echo  [!] Erreur lors de l entrainement %MODEL%
    exit /b 1
)

echo [%date% %time%] [OK] Entrainement %MODEL% termine avec succes >> "%LOGFILE%"
echo.
echo  [i] Entrainement termine avec succes.
echo  [i] Heure de fin: %time%
echo.
echo  ========================================
echo  Entrainement automatique termine.
echo  Log: data\training_log.txt
echo  ========================================
echo.
