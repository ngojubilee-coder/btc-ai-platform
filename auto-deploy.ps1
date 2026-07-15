#!/usr/bin/env pwsh
<#
  BTC AI Platform - Deploiement 100% Autopilote
  Frontend -> Cloudflare Workers
  Backend  -> Railway.app
  
  Usage: .\auto-deploy.ps1
  
  Preconditions:
    - Railway CLI installe (npm install -g @railway/cli)
    - Railway login effectue (railway login)
    - Cloudflare login effectue (npx wrangler login)
#>

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$FRONTEND = Join-Path $ROOT "frontend"
$BACKEND = Join-Path $ROOT "backend"

function Write-Step($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Err($msg)  { Write-Host "  [ERR] $msg" -ForegroundColor Red }
function Write-Info($msg) { Write-Host "  [i] $msg" -ForegroundColor Yellow }

# ── 1. Verifications
Write-Step "Verification des outils"

$tools = @(
  @{ Name = "node"; Cmd = "node --version" },
  @{ Name = "python"; Cmd = "python --version" },
  @{ Name = "railway"; Cmd = "railway --help" },
  @{ Name = "wrangler"; Cmd = "npx wrangler --version" }
)

foreach ($t in $tools) {
  try { Invoke-Expression $t.Cmd 2>&1 | Out-Null; Write-OK "$($t.Name) detecte" }
  catch { Write-Err "$($t.Name) manquant"; exit 1 }
}

# ── 2. Backend -> Railway
Write-Step "Deploiement Backend sur Railway"

Push-Location $BACKEND

# Lier au projet Railway existant ou en creer un nouveau
$linked = railway status 2>&1
if ($LASTEXITCODE -ne 0) {
  Write-Info "Creation d'un nouveau projet Railway..."
  railway init --name "btc-ai-platform" 2>&1 | Out-Null
  if ($LASTEXITCODE -eq 0) { Write-OK "Projet Railway cree" }
  else { Write-Err "Echec creation projet Railway"; Pop-Location; exit 1 }
} else {
  Write-OK "Projet Railway deja lie"
}

# Ajouter les variables d'environnement
Write-Info "Configuration des variables d'environnement..."

$envVars = @(
  @{ Name = "CORS_ORIGINS"; Value = "https://btc-ai-platform.jubilee-israel1.workers.dev" },
  @{ Name = "DATA_DIR"; Value = "./data" },
  @{ Name = "PARQUET_PATH"; Value = "./data/btc_enriched_dataset_1m.parquet" },
  @{ Name = "HOST"; Value = "0.0.0.0" },
  @{ Name = "PYTHON_VERSION"; Value = "3.11" }
)

foreach ($v in $envVars) {
  railway variables --set "$($v.Name)=$($v.Value)" 2>&1 | Out-Null
}
Write-OK "Variables de base configurees"

# Variables secretes (recuperer depuis .env local si disponible)
if (Test-Path ".env") {
  $envContent = Get-Content ".env"
  $secretVars = @("GEMINI_API_KEY", "SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_SERVICE_KEY", "JWT_SECRET", "ANTHROPIC_API_KEY", "OPENAI_API_KEY")
  foreach ($line in $envContent) {
    if ($line -match "^([^#=]+)=(.+)$") {
      $key = $matches[1].Trim()
      $val = $matches[2].Trim()
      if ($secretVars -contains $key -and $val -notmatch "your-|change-this|placeholder") {
        railway variables --set "$key=$val" 2>&1 | Out-Null
        Write-OK "Variable $key importee depuis .env"
      }
    }
  }
}

# Deployer
Write-Info "Deploiement du code backend sur Railway..."
railway up --detach 2>&1 | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }

if ($LASTEXITCODE -eq 0) {
  Write-OK "Backend deploye sur Railway"
} else {
  Write-Err "Echec du deploiement Railway"
  Pop-Location
  exit 1
}

# Recuperer l'URL du backend
Start-Sleep -Seconds 5
$backendUrl = railway domain 2>&1 | Select-Object -First 1
if ($backendUrl) {
  $backendUrl = $backendUrl.Trim()
  if ($backendUrl -notmatch "^https?://") { $backendUrl = "https://$backendUrl" }
  Write-OK "URL Backend: $backendUrl"
} else {
  Write-Info "URL non disponible immediatement, utilisation du pattern Railway"
  $backendUrl = "https://btc-ai-platform.up.railway.app"
  Write-Info "URL estimee: $backendUrl"
}

Pop-Location

# ── 3. Frontend -> Cloudflare
Write-Step "Mise a jour + Deploiement Frontend sur Cloudflare"

Push-Location $FRONTEND

# Mettre a jour l'URL du backend dans wrangler.jsonc
$wranglerFile = "wrangler.jsonc"
if (Test-Path $wranglerFile) {
  $content = Get-Content $wranglerFile -Raw
  $content = $content -replace '"NEXT_PUBLIC_API_URL": "[^"]*"', "`"NEXT_PUBLIC_API_URL`": `"$backendUrl`""
  $content | Set-Content $wranglerFile -NoNewline
  Write-OK "wrangler.jsonc mis a jour avec API_URL=$backendUrl"
}

# Build OpenNext
Write-Info "Build OpenNext..."
npx opennextjs-cloudflare build 2>&1 | Select-Object -Last 3 | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
if ($LASTEXITCODE -ne 0) { Write-Err "Echec build OpenNext"; Pop-Location; exit 1 }
Write-OK "Build OpenNext reussi"

# Deploy sur Cloudflare
Write-Info "Deploiement sur Cloudflare Workers..."
npx wrangler deploy 2>&1 | Select-Object -Last 8 | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
if ($LASTEXITCODE -eq 0) {
  Write-OK "Frontend deploye sur Cloudflare"
} else {
  Write-Err "Echec deploiement Cloudflare"
  Pop-Location
  exit 1
}

Pop-Location

# ── 4. Mise a jour CORS sur le backend
Write-Step "Mise a jour CORS sur Railway"
Push-Location $BACKEND
railway variables --set "CORS_ORIGINS=https://btc-ai-platform.jubilee-israel1.workers.dev,$backendUrl" 2>&1 | Out-Null
Write-OK "CORS mis a jour"
Pop-Location

# ── 5. Verification
Write-Step "Verification des endpoints"

$frontendUrl = "https://btc-ai-platform.jubilee-israel1.workers.dev"

Write-Info "Test Frontend..."
try {
  $r = Invoke-WebRequest -Uri $frontendUrl -TimeoutSec 15 -UseBasicParsing
  Write-OK "Frontend: $($r.StatusCode) OK"
} catch { Write-Err "Frontend: $($_.Exception.Message)" }

Write-Info "Test Backend (peut prendre 1-2 min pour le premier deploy)..."
$maxRetries = 30
$retry = 0
while ($retry -lt $maxRetries) {
  Start-Sleep -Seconds 10
  try {
    $r = Invoke-WebRequest -Uri "$backendUrl/health" -TimeoutSec 10 -UseBasicParsing
    Write-OK "Backend: $($r.StatusCode) - $($r.Content.Substring(0, [Math]::Min(100, $r.Content.Length)))"
    break
  } catch {
    $retry++
    Write-Host "  ...attente ($retry/$maxRetries)" -ForegroundColor DarkGray
  }
}

# ── 6. Resume final
Write-Step "Deploiement termine !"
Write-Host @"
  
  Frontend:  $frontendUrl
  Backend:   $backendUrl
  Health:    $backendUrl/health
  API Docs:  $backendUrl/docs
  
  Variables secretes a configurer sur Railway:
    railway variables --set GEMINI_API_KEY=your-key
    railway variables --set SUPABASE_URL=your-url
    railway variables --set SUPABASE_KEY=your-key

"@ -ForegroundColor Yellow
