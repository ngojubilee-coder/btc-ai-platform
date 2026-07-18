@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title BTC AI Platform - VPS Windows Setup
color 0A

echo.
echo  === BTC AI PLATFORM - VPS WINDOWS INSTALLATION ===
echo  === Tout inclus - Installation 100%% automatique ===
echo.

:: Verifier les privileges admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo  [!] Lancement avec privileges administrateur...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Detecter le repertoire
set "ROOT=%~dp0"
cd /d "%ROOT%"

:: --- 1. Verification Python ---
echo  [1/10] Verification de Python...
where python >nul 2>&1
if %errorLevel% neq 0 (
    echo      Python non trouve. Installation...
    powershell -Command "winget install Python.Python.3.11 --accept-source-agreements --accept-package-agreements"
    set "PATH=%PATH%;C:\Program Files\Python311\;C:\Program Files\Python311\Scripts\"
    for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "SYS_PATH=%%b"
    set "PATH=%SYS_PATH%;%PATH%"
)
python --version 2>nul
if %errorLevel% neq 0 (
    echo  [ERREUR] Python n est pas accessible. Redemarrez le terminal et relancez ce script.
    pause
    exit /b 1
)
echo      Python OK

:: --- 2. Verification Node.js ---
echo  [2/10] Verification de Node.js...
where node >nul 2>&1
if %errorLevel% neq 0 (
    echo      Node.js non trouve. Installation...
    powershell -Command "winget install OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements"
    set "PATH=%PATH%;C:\Program Files\nodejs\"
    for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "SYS_PATH=%%b"
    set "PATH=%SYS_PATH%;%PATH%"
)
node --version 2>nul
if %errorLevel% neq 0 (
    echo  [ERREUR] Node.js n est pas accessible. Redemarrez le terminal et relancez ce script.
    pause
    exit /b 1
)
echo      Node.js OK

:: --- 3. Environnement virtuel Python ---
echo  [3/10] Creation de l environnement virtuel Python...
cd /d "%ROOT%backend"
if not exist ".venv" (
    python -m venv .venv
    echo      Environnement virtuel cree
) else (
    echo      Environnement virtuel existe deja
)
call .venv\Scripts\activate.bat
echo      Environnement virtuel active

:: --- 4. Installation des dependances Python ---
echo  [4/10] Installation des dependances Python...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt --quiet
if %errorLevel% neq 0 (
    echo  [!] Erreur lors de l installation pip. Nouvel essai...
    pip install -r requirements.txt
)
echo      Dependances Python installees

:: --- 5. Dependances d entrainement ---
echo  [5/10] Installation des dependances d entrainement...
pip install xgboost scikit-learn --quiet 2>nul
python -c "import tensorflow" 2>nul
if %errorLevel% neq 0 (
    echo      TensorFlow non installe. Installation...
    pip install tensorflow --quiet
)
echo      xgboost + scikit-learn + tensorflow installes

:: --- 6. Installation des dependances Node.js ---
echo  [6/10] Installation des dependances Node.js - frontend...
cd /d "%ROOT%frontend"
if not exist "node_modules" (
    npm install --silent
    echo      Dependances Node.js installees
) else (
    echo      node_modules existe deja
)

:: --- 7. Configuration .env ---
echo  [7/10] Configuration de l environnement...
cd /d "%ROOT%backend"
if not exist ".env" (
    copy ".env.example" ".env" >nul 2>&1
    if not exist ".env.example" (
        echo # === SUPABASE === > .env
        echo SUPABASE_URL= >> .env
        echo SUPABASE_KEY= >> .env
        echo SUPABASE_SERVICE_KEY= >> .env
        echo. >> .env
        echo # === LLM API KEYS === >> .env
        echo GEMINI_API_KEY= >> .env
        echo ANTHROPIC_API_KEY= >> .env
        echo OPENAI_API_KEY= >> .env
        echo. >> .env
        echo # === OLLAMA - local === >> .env
        echo OLLAMA_BASE_URL=http://localhost:11434 >> .env
        echo. >> .env
        echo # === DATA PATHS === >> .env
        echo DATA_DIR=../data >> .env
        echo PARQUET_PATH=../data/btc_enriched_dataset_1m.parquet >> .env
        echo. >> .env
        echo # === AUTH === >> .env
        echo JWT_SECRET=change-this-secret >> .env
        echo JWT_ALGORITHM=HS256 >> .env
        echo JWT_EXPIRE_HOURS=24 >> .env
        echo. >> .env
        echo # === SERVER === >> .env
        echo HOST=0.0.0.0 >> .env
        echo PORT=8000 >> .env
        echo CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000 >> .env
    )
    echo      Fichier .env cree - a configurer
) else (
    echo      .env existe deja
)

:: --- 8. Frontend .env.local ---
echo  [8/10] Configuration frontend...
cd /d "%ROOT%frontend"
if not exist ".env.local" (
    echo NEXT_PUBLIC_API_URL=http://localhost:8000 > .env.local
    echo NEXT_PUBLIC_SUPABASE_URL= >> .env.local
    echo NEXT_PUBLIC_SUPABASE_ANON_KEY= >> .env.local
    echo      .env.local cree
) else (
    echo      .env.local existe deja
)

:: --- 9. Tests backend ---
echo  [9/10] Verification des tests backend...
cd /d "%ROOT%backend"
call .venv\Scripts\activate.bat
python -m pytest tests/ -v --tb=short 2>&1 | findstr /C:"passed" /C:"failed" /C:"error"

:: --- 10. Verification finale ---
echo  [10/10] Verification finale...
python -c "import fastapi; import uvicorn; import duckdb; import pandas; import xgboost; import sklearn; print('  Imports OK')" 2>nul
if %errorLevel% neq 0 (
    echo  [!] Certains imports ont echoue. Verifiez l installation.
)
if exist "%ROOT%data\btc_enriched_dataset_1m.parquet" (
    echo      Dataset present
) else (
    echo      Dataset absent - lancez prepare-data.bat
)

:: --- Resume ---
echo.
echo  ========================================
echo  === INSTALLATION TERMINEE AVEC SUCCES ===
echo  ========================================
echo.
echo  Pour demarrer la platforme:
echo    1. start-vps.bat
echo.
echo  Pour lancer l entrainement:
echo    2. train-vps.bat
echo.
echo  URLs locales:
echo    Frontend: http://localhost:3000
echo    Backend:  http://localhost:8000
echo    API Docs: http://localhost:8000/docs
echo.
echo  Configurez .env dans backend/ avec vos cles API
echo.
echo  Scripts disponibles:
echo    health-check-vps.bat  - Verification systeme
echo    monitoring-vps.bat    - Monitoring complet
echo    backup-vps.bat        - Backup ZIP
echo    update-vps.bat        - Mise a jour
echo    auto-train-vps.bat    - Entrainement auto
echo.
pause
