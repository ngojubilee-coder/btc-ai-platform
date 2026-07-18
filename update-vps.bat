@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title BTC AI Platform - Mise a jour
color 0E

echo.
echo  === BTC AI PLATFORM - MISE A JOUR ===
echo.

set "ROOT=%~dp0"
cd /d "%ROOT%"

echo  [1/5] Git pull...
git pull origin master 2>nul
if %errorLevel% neq 0 (
    echo  [!] Erreur git pull. Verifiez votre connexion.
    pause
    exit /b 1
)
echo      Code a jour

echo  [2/5] Mise a jour des dependances Python...
cd /d "%ROOT%backend"
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip >nul 2>&1
    pip install -r requirements.txt --quiet
    pip install xgboost scikit-learn --quiet 2>nul
    echo      Dependances Python OK
) else (
    echo  [!] venv absent - lancez install-vps.bat
)

echo  [3/5] Mise a jour des dependances Node.js...
cd /d "%ROOT%frontend"
if exist "node_modules" (
    npm update --silent 2>nul
    echo      Dependances Node.js OK
) else (
    echo  [!] node_modules absent - lancez install-vps.bat
)

echo  [4/5] Verification des tests...
cd /d "%ROOT%backend"
call .venv\Scripts\activate.bat
python -m pytest tests/ -v --tb=short 2>&1 | findstr /C:"passed" /C:"failed" /C:"error"

echo  [5/5] Verification du dataset...
if exist "%ROOT%data\btc_enriched_dataset_1m.parquet" (
    echo      Dataset present
) else (
    echo      Dataset absent - lancez prepare-data.bat
)

echo.
echo  ========================================
echo  Mise a jour terminee.
echo  Relancez start-vps.bat pour appliquer.
echo  ========================================
echo.
pause
