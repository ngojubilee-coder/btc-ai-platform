@echo off
chcp 65001 >nul 2>&1
title BTC AI Platform - Backup
color 0D

echo.
echo  === BTC AI PLATFORM - BACKUP ===
echo.

set "ROOT=%~dp0"
cd /d "%ROOT%"

set "BACKUP_DIR=%ROOT%backups"
set "TIMESTAMP=%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"
set "BACKUP_PATH=%BACKUP_DIR%\%TIMESTAMP%"

if not exist "%BACKUP_PATH%" mkdir "%BACKUP_PATH%"

echo  [i] Backup vers: %BACKUP_PATH%
echo.

if exist "%ROOT%backend\.env" (
    copy "%ROOT%backend\.env" "%BACKUP_PATH%\backend.env" >nul
    echo  [OK] backend/.env
)

if exist "%ROOT%frontend\.env.local" (
    copy "%ROOT%frontend\.env.local" "%BACKUP_PATH%\frontend.env.local" >nul
    echo  [OK] frontend/.env.local
)

if exist "%ROOT%data\models" (
    xcopy "%ROOT%data\models" "%BACKUP_PATH%\models\" /E /I /Q >nul
    echo  [OK] data/models/
)

if exist "%ROOT%data\results" (
    xcopy "%ROOT%data\results" "%BACKUP_PATH%\results\" /E /I /Q >nul
    echo  [OK] data/results/
)

if exist "%ROOT%data\btc_enriched_dataset_1m.parquet" (
    copy "%ROOT%data\btc_enriched_dataset_1m.parquet" "%BACKUP_PATH%\" >nul
    echo  [OK] data/btc_enriched_dataset_1m.parquet
)

if exist "%ROOT%frontend\wrangler.jsonc" (
    copy "%ROOT%frontend\wrangler.jsonc" "%BACKUP_PATH%\" >nul
    echo  [OK] frontend/wrangler.jsonc
)

if exist "%ROOT%render.yaml" (
    copy "%ROOT%render.yaml" "%BACKUP_PATH%\" >nul
    echo  [OK] render.yaml
)

echo.
echo  [i] Compression...
powershell -Command "Compress-Archive -Path '%BACKUP_PATH%\*' -DestinationPath '%BACKUP_DIR%\backup_%TIMESTAMP%.zip' -Force"
if %errorLevel% equ 0 (
    rmdir /s /q "%BACKUP_PATH%"
    echo  [OK] Backup cree: backups\backup_%TIMESTAMP%.zip
)

echo.
echo  === Backup termine ===
echo  Fichier: backups\backup_%TIMESTAMP%.zip
echo.
pause
