#!/usr/bin/env pwsh
<#
  BTC AI Platform - Script de déploiement automatise
  Usage:
    .\deploy.ps1              # Deploiement complet (backend + frontend Cloudflare)
    .\deploy.ps1 -Backend     # Backend seulement (Docker)
    .\deploy.ps1 -Frontend    # Frontend seulement (Cloudflare)
    .\deploy.ps1 -Build       # Build seulement (sans deploy)
#>

param(
  [switch]$Backend,
  [switch]$Frontend,
  [switch]$Build,
  [string]$ApiUrl = "",
  [string]$SupabaseUrl = "",
  [string]$SupabaseKey = ""
)

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$FRONTEND = Join-Path $ROOT "frontend"
$BACKEND = Join-Path $ROOT "backend"

function Write-Step($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "  OK: $msg" -ForegroundColor Green }
function Write-Err($msg)  { Write-Host "  ERR: $msg" -ForegroundColor Red }

# ── 1. Verification des pre-requis
Write-Step "Verification des pre-requis"

$missing = @()
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { $missing += "Node.js" }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { $missing += "Python" }
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { $missing += "Docker" }

if ($missing.Count -gt 0) {
  Write-Err "Manquant: $($missing -join ', ')"
  exit 1
}
Write-OK "Node.js, Python, Docker detectes"

# ── 2. Backend (Docker)
if (-not $Frontend -and -not $Build) {
  Write-Step "Demarrage du backend (Docker)"

  Push-Location $ROOT
  docker-compose -f docker-compose.prod.yml down 2>$null
  docker-compose -f docker-compose.prod.yml up -d --build
  if ($LASTEXITCODE -eq 0) {
    Write-OK "Backend demarre sur http://localhost:8000"
  } else {
    Write-Err "Echec du demarrage du backend"
    Pop-Location
    exit 1
  }
  Pop-Location

  # Attendre que le backend reponde
  Write-Host "  Attente du health check..." -NoNewline
  $maxRetries = 15
  $retry = 0
  while ($retry -lt $maxRetries) {
    Start-Sleep -Seconds 2
    try {
      $resp = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 3
      Write-OK "Backend healthy: $($resp.status)"
      break
    } catch {
      $retry++
      Write-Host "." -NoNewline
    }
  }
  if ($retry -eq $maxRetries) {
    Write-Err "Backend ne repond pas apres $maxRetries essais"
  }
}

# ── 3. Frontend (Cloudflare)
if (-not $Backend -and -not $Build) {
  Write-Step "Build + Deploiement frontend (Cloudflare)"

  Push-Location $FRONTEND

  # Installer les dependances
  npm install --silent
  Write-OK "Dependances installees"

  # Variables d'environnement
  if ($ApiUrl) {
    (Get-Content "wrangler.jsonc") -replace '"NEXT_PUBLIC_API_URL": "[^"]*"', "`"NEXT_PUBLIC_API_URL`": `"$ApiUrl`"" | Set-Content "wrangler.jsonc"
    Write-OK "API_URL mis a jour: $ApiUrl"
  }
  if ($SupabaseUrl) {
    (Get-Content "wrangler.jsonc") -replace '"NEXT_PUBLIC_SUPABASE_URL": "[^"]*"', "`"NEXT_PUBLIC_SUPABASE_URL`": `"$SupabaseUrl`"" | Set-Content "wrangler.jsonc"
    Write-OK "SUPABASE_URL mis a jour"
  }
  if ($SupabaseKey) {
    (Get-Content "wrangler.jsonc") -replace '"NEXT_PUBLIC_SUPABASE_ANON_KEY": "[^"]*"', "`"NEXT_PUBLIC_SUPABASE_ANON_KEY`": `"$SupabaseKey`"" | Set-Content "wrangler.jsonc"
    Write-OK "SUPABASE_ANON_KEY mis a jour"
  }

  # Build OpenNext
  npx opennextjs-cloudflare build
  if ($LASTEXITCODE -ne 0) { Write-Err "Echec du build OpenNext"; Pop-Location; exit 1 }
  Write-OK "Build OpenNext reussi"

  # Deploy sur Cloudflare
  npx wrangler deploy
  if ($LASTEXITCODE -eq 0) {
    Write-OK "Frontend deploye sur Cloudflare Workers"
  } else {
    Write-Err "Echec du deploiement Cloudflare"
    Pop-Location
    exit 1
  }

  Pop-Location
}

# ── 4. Build seulement
if ($Build) {
  Write-Step "Build (sans deploiement)"

  Push-Location $FRONTEND
  npm install --silent
  npx next build
  if ($LASTEXITCODE -eq 0) { Write-OK "Frontend build OK" } else { Write-Err "Echec build frontend"; Pop-Location; exit 1 }

  npx opennextjs-cloudflare build
  if ($LASTEXITCODE -eq 0) { Write-OK "OpenNext build OK" } else { Write-Err "Echec build OpenNext"; Pop-Location; exit 1 }
  Pop-Location

  Push-Location $BACKEND
  python -m pytest tests/ -v --tb=short
  if ($LASTEXITCODE -eq 0) { Write-OK "Tests backend OK (77 tests)" } else { Write-Err "Echec tests backend"; Pop-Location; exit 1 }
  Pop-Location
}

# ── 5. Mise a jour CORS automatique
if (-not $Build) {
  Write-Step "Mise a jour CORS"
  $cfUrl = "https://btc-ai-platform.jubilee-israel1.workers.dev"
  $envFile = Join-Path $BACKEND ".env"
  if (Test-Path $envFile) {
    $content = Get-Content $envFile
    $content = $content -replace 'CORS_ORIGINS=.*', "CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,$cfUrl"
    $content | Set-Content $envFile
    Write-OK "CORS mis a jour avec URL Cloudflare"
  }
}

# ── 6. Resume final
Write-Step "Deploiement termine"
Write-Host @"
  Frontend:  https://btc-ai-platform.jubilee-israel1.workers.dev
  Backend:   http://localhost:8000
  Health:    http://localhost:8000/health
  Docs:      http://localhost:8000/docs

  Pour configurer Supabase:
    .\deploy.ps1 -Frontend -ApiUrl "https://votre-api.com" -SupabaseUrl "https://xxx.supabase.co" -SupabaseKey "votre-cle"
"@ -ForegroundColor Yellow
