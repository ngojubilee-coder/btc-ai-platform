@echo off
chcp 65001 >nul 2>&1
title BTC AI Platform - Arret
color 0C

echo.
echo  Arret de la BTC AI Platform...
echo.

:: Tuer les processus sur les ports 3000 et 8000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000.*LISTENING" 2^>nul') do (
    echo  Arret du processus frontend (PID: %%a)
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING" 2^>nul') do (
    echo  Arret du processus backend (PID: %%a)
    taskkill /PID %%a /F >nul 2>&1
)

:: Fermer les fenetres
taskkill /FI "WINDOWTITLE eq BTC-AI-Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq BTC-AI-Frontend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq BTC-AI-Training*" /F >nul 2>&1

echo.
echo  Platforme arretee.
pause
