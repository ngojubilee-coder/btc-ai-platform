@echo off
chcp 65001 >nul 2>&1
title BTC AI Platform - Entrainement
color 0E

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║     BTC AI PLATFORM - PIPELINE D'ENTRAINEMENT         ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

set "ROOT=%~dp0"
cd /d "%ROOT%backend"

:: Activer l'environnement virtuel
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo  [!] Environnement virtuel non trouve. Lancez install-vps.bat d'abord.
    pause
    exit /b 1
)

:: Installer les dependances d'entrainement
echo  [i] Verification des dependances d'entrainement...
pip install xgboost scikit-learn --quiet 2>nul
python -c "import tensorflow" 2>nul
if %errorLevel% neq 0 (
    echo  [i] TensorFlow non installe. Installation (peut prendre quelques minutes)...
    pip install tensorflow --quiet
)

:: Menu de selection
echo  Selectionnez le modele a entrainer:
echo    1. XGBoost (recommande - rapide et performant)
echo    2. Random Forest (robuste)
echo    3. LSTM Deep Learning (TensorFlow - lent)
echo    4. Comparaison tous modeles + CSV
echo    5. Lister les modeles disponibles
echo    6. Verifier le dataset
echo.

set /p choice="Votre choix (1-6): "

if "%choice%"=="1" (
    echo.
    python train.py --model xgboost --backtest
) else if "%choice%"=="2" (
    echo.
    python train.py --model random_forest --backtest
) else if "%choice%"=="3" (
    echo.
    python train.py --model lstm --backtest
) else if "%choice%"=="4" (
    echo.
    python train.py --compare --backtest
) else if "%choice%"=="5" (
    python train.py --list
) else if "%choice%"=="6" (
    echo.
    python download_data.py --rows 100000
) else (
    echo  Choix invalide.
)

echo.
pause
