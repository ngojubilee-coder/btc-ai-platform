@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title BTC AI Platform - Preparation Donnees
color 0D

echo.
echo  === BTC AI PLATFORM - PREPARATION DES DONNEES ===
echo.

set "ROOT=%~dp0"
cd /d "%ROOT%backend"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo  [!] Environnement virtuel non trouve. Lancez install-vps.bat.
    pause
    exit /b 1
)

echo  [i] Generation du dataset BTC synthetique - 100k lignes...
echo.
python download_data.py --rows 100000

echo.
pause
