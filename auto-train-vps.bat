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

echo  [i] Demarrage de l entrainement automatique...
echo  [i] Modele: XGBoost + Backtest
echo  [i] Heure de debut: %time%
echo.

:: Entrainement XGBoost avec backtest
python train.py --model xgboost --backtest
if %errorLevel% neq 0 (
    echo  [!] Erreur lors de l entrainement XGBoost
    exit /b 1
)

echo.
echo  [i] Entrainement termine avec succes.
echo  [i] Heure de fin: %time%
echo.

:: Log dans un fichier
echo [%date% %time%] Entrainement XGBoost OK >> "%ROOT%data\training_log.txt"

echo  ========================================
echo  Entrainement automatique termine.
echo  Log: data\training_log.txt
echo  ========================================
echo.
