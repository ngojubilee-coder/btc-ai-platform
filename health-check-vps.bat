@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title BTC AI Platform - Health Check
color 0A

echo.
echo  === BTC AI PLATFORM - VERIFICATION SYSTEME ===
echo.

set "ROOT=%~dp0"
cd /d "%ROOT%"

echo  [1/5] Backend API...
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8000/health' -TimeoutSec 5 -UseBasicParsing; $j = $r.Content | ConvertFrom-Json; Write-Host '      Status:' $j.status -ForegroundColor Green; foreach ($k in $j.components.PSObject.Properties) { $v = $k.Value; if ($v.status) { Write-Host '      '$k.Name':' $v.status } elseif ($v.gemini) { Write-Host '      '$k.Name': gemini=' $v.gemini 'anthropic=' $v.anthropic 'openai=' $v.openai } } } catch { Write-Host '      ERREUR: Backend non accessible' -ForegroundColor Red }"

echo  [2/5] Frontend...
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:3000' -TimeoutSec 5 -UseBasicParsing; Write-Host '      Status:' $r.StatusCode '- OK' -ForegroundColor Green } catch { Write-Host '      ERREUR: Frontend non accessible' -ForegroundColor Red }"

echo  [3/5] Endpoints API...
powershell -Command "$eps = @('/api/whales/stats', '/api/data/stats', '/api/data/schema', '/api/news/search'); foreach ($ep in $eps) { try { $r = Invoke-WebRequest -Uri ('http://localhost:8000' + $ep) -TimeoutSec 5 -UseBasicParsing; Write-Host '      ' $ep '->' $r.StatusCode -ForegroundColor Green } catch { Write-Host '      ' $ep '-> ERR' -ForegroundColor Red } }"

echo  [4/5] Dataset...
if exist "%ROOT%data\btc_enriched_dataset_1m.parquet" (
    for %%F in ("%ROOT%data\btc_enriched_dataset_1m.parquet") do echo      Present - %%~zF bytes
) else (
    echo      Absent - lancez prepare-data.bat
)

echo  [5/5] Modeles entraines...
if exist "%ROOT%data\models" (
    for /f %%c in ('dir /b "%ROOT%data\models\*.json" 2^>nul ^| find /c /v ""') do echo      %%c modele(s) disponible(s)
    dir /b "%ROOT%data\models\" 2>nul
) else (
    echo      Aucun modele - lancez train-vps.bat
)

echo.
echo  [i] Derniers resultats d entrainement...
if exist "%ROOT%data\results" (
    dir /b /o-d "%ROOT%data\results\*.json" 2>nul | findstr /n "." | findstr "^[1-3]:" 2>nul
) else (
    echo      Aucun resultat - lancez train-vps.bat
)

echo.
echo  ========================================
echo  Verification terminee.
echo  ========================================
echo.
pause
