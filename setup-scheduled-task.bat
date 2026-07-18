@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title BTC AI Platform - Planification Tache
color 0D

echo.
echo  === BTC AI PLATFORM - PLANIFICATION ENTRAINEMENT ===
echo.

set "ROOT=%~dp0"
set "SCRIPT=%ROOT%auto-train-vps.bat"

echo  Selectionnez la frequence d entrainement:
echo    1. Quotidien - 06h00
echo    2. Quotidien - 12h00
echo    3. Quotidien - 00h00 (minuit)
echo    4. Hebdomadaire - Dimanche 02h00
echo    5. Toutes les 6 heures
echo    6. Supprimer la tache planifiee
echo.

set /p choice="Votre choix (1-6): "

if "%choice%"=="1" (
    schtasks /create /tn "BTC_AI_Train_Daily" /tr "%SCRIPT% xgboost" /sc daily /st 06:00 /f
    echo  [OK] Tache creee: quotidienne 06h00
) else if "%choice%"=="2" (
    schtasks /create /tn "BTC_AI_Train_Daily" /tr "%SCRIPT% xgboost" /sc daily /st 12:00 /f
    echo  [OK] Tache creee: quotidienne 12h00
) else if "%choice%"=="3" (
    schtasks /create /tn "BTC_AI_Train_Daily" /tr "%SCRIPT% xgboost" /sc daily /st 00:00 /f
    echo  [OK] Tache creee: quotidienne 00h00
) else if "%choice%"=="4" (
    schtasks /create /tn "BTC_AI_Train_Weekly" /tr "%SCRIPT% compare" /sc weekly /d SUN /st 02:00 /f
    echo  [OK] Tache creee: hebdomadaire dimanche 02h00
) else if "%choice%"=="5" (
    schtasks /create /tn "BTC_AI_Train_6h" /tr "%SCRIPT% xgboost" /sc hourly /mo 6 /f
    echo  [OK] Tache creee: toutes les 6 heures
) else if "%choice%"=="6" (
    schtasks /delete /tn "BTC_AI_Train_Daily" /f 2>nul
    schtasks /delete /tn "BTC_AI_Train_Weekly" /f 2>nul
    schtasks /delete /tn "BTC_AI_Train_6h" /f 2>nul
    echo  [OK] Taches supprimees
) else (
    echo  Choix invalide.
)

echo.
echo  ========================================
echo  Pour verifier: schtasks /query /tn BTC_AI_Train_*
echo  ========================================
echo.
pause
