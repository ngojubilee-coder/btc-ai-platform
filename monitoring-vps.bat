@echo off
chcp 65001 >nul 2>&1
title BTC AI Platform - Monitoring
color 0B

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║     BTC AI PLATFORM - MONITORING SYSTEME              ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

set "ROOT=%~dp0"
cd /d "%ROOT%"

:: ─── Systeme ───
echo  === SYSTEME ===
echo  Date: %date% %time%
echo  OS: %OS%
echo  Architecture: %PROCESSOR_ARCHITECTURE%
echo.

:: ─── Ports ───
echo  === PORTS ===
netstat -ano | findstr ":3000.*LISTENING" >nul 2>&1
if %errorLevel% equ 0 (
    echo  Port 3000 [Frontend]: OCCUPE - en cours d'execution
) else (
    echo  Port 3000 [Frontend]: LIBRE
)
netstat -ano | findstr ":8000.*LISTENING" >nul 2>&1
if %errorLevel% equ 0 (
    echo  Port 8000 [Backend]:  OCCUPE - en cours d'execution
) else (
    echo  Port 8000 [Backend]:  LIBRE
)
echo.

:: ─── Disk ───
echo  === DISQUE ===
for /f "tokens=3" %%a in ('dir /-c "%ROOT%" ^| findstr "bytes free"') do set "FREESPACE=%%a"
echo  Espace libre: %FREESPACE% bytes
echo.

:: ─── Dataset ───
echo  === DATASET ===
if exist "%ROOT%data\btc_enriched_dataset_1m.parquet" (
    for %%F in ("%ROOT%data\btc_enriched_dataset_1m.parquet") do (
        set /a "SIZE_MB=%%~zF / 1048576"
        echo  Fichier: btc_enriched_dataset_1m.parquet
        echo  Taille: !SIZE_MB! MB
    )
) else (
    echo  Dataset: ABSENT
)
echo.

:: ─── Modeles ───
echo  === MODELES ===
if exist "%ROOT%data\models" (
    dir /b "%ROOT%data\models\" 2>nul
) else (
    echo  Aucun modele entraine
)
echo.

:: ─── Resultats ───
echo  === RESULTATS D'ENTRAINEMENT ===
if exist "%ROOT%data\results" (
    dir /b /o-d "%ROOT%data\results\" 2>nul
) else (
    echo  Aucun resultat
)
echo.

:: ─── Python ───
echo  === PYTHON ===
where python >nul 2>&1
if %errorLevel% equ 0 (
    python --version 2>nul
    echo  venv: 
    if exist "%ROOT%backend\.venv\Scripts\activate.bat" (
        echo    Present
    ) else (
        echo    ABSENT - lancez install-vps.bat
    )
) else (
    echo  Python: NON INSTALLE
)
echo.

:: ─── Node.js ───
echo  === NODE.JS ===
where node >nul 2>&1
if %errorLevel% equ 0 (
    node --version 2>nul
    echo  node_modules:
    if exist "%ROOT%frontend\node_modules" (
        echo    Present
    ) else (
        echo    ABSENT - lancez install-vps.bat
    )
) else (
    echo  Node.js: NON INSTALLE
)
echo.

:: ─── Configuration ───
echo  === CONFIGURATION ===
if exist "%ROOT%backend\.env" (
    echo  backend/.env: Present
) else (
    echo  backend/.env: ABSENT
)
if exist "%ROOT%frontend\.env.local" (
    echo  frontend/.env.local: Present
) else (
    echo  frontend/.env.local: ABSENT
)
echo.

echo  ══════════════════════════════════════════════════════
echo  Monitoring termine.
echo  ══════════════════════════════════════════════════════
echo.
pause
