#!/usr/bin/env pwsl
<#
  Deploy backend to Render.com via API
  Usage:
    1. Get your Render API key: https://dashboard.render.com/u/settings#api-keys
    2. Set environment variable: $env:RENDER_API_KEY = "your-key"
    3. Run: .\deploy-render.ps1
#>

$ErrorActionPreference = "Stop"

$apiKey = $env:RENDER_API_KEY
if (-not $apiKey) {
  Write-Host "RENDER_API_KEY not set. Get it from: https://dashboard.render.com/u/settings#api-keys" -ForegroundColor Red
  Write-Host "Then run: `$env:RENDER_API_KEY = 'your-key'" -ForegroundColor Yellow
  exit 1
}

$headers = @{
  "Authorization" = "Bearer $apiKey"
  "Content-Type" = "application/json"
  "Accept" = "application/json"
}

$repoUrl = "https://github.com/ngojubilee-coder/btc-ai-platform"
$serviceName = "btc-ai-platform-backend"

Write-Host "`n=== Creating Render web service ===" -ForegroundColor Cyan

$body = @{
  type = "web_service"
  name = $serviceName
  owner = $null
  repo = $repoUrl
  branch = "master"
  rootDir = "backend"
  runtime = "python"
  buildCommand = "pip install -r requirements.txt"
  startCommand = "uvicorn main:app --host 0.0.0.0 --port `$PORT --workers 4"
  healthCheckPath = "/health"
  plan = "free"
  envVars = @(
    @{ key = "PYTHON_VERSION"; value = "3.11" },
    @{ key = "CORS_ORIGINS"; value = "https://btc-ai-platform.jubilee-israel1.workers.dev" },
    @{ key = "DATA_DIR"; value = "./data" },
    @{ key = "PARQUET_PATH"; value = "./data/btc_enriched_dataset_1m.parquet" },
    @{ key = "HOST"; value = "0.0.0.0" },
    @{ key = "GEMINI_API_KEY"; sync = "false" },
    @{ key = "SUPABASE_URL"; sync = "false" },
    @{ key = "SUPABASE_KEY"; sync = "false" },
    @{ key = "JWT_SECRET"; sync = "false" }
  )
} | ConvertTo-Json -Depth 5

try {
  $resp = Invoke-RestMethod -Uri "https://api.render.com/v1/services" -Method POST -Headers $headers -Body $body
  Write-Host "  Service created: $($resp.service.name)" -ForegroundColor Green
  Write-Host "  URL: https://$($resp.service.name).onrender.com" -ForegroundColor Green
  Write-Host "  ID: $($resp.service.id)" -ForegroundColor Green
  Write-Host "`n  Set env vars at: https://dashboard.render.com/web/$($resp.service.id)/env" -ForegroundColor Yellow
} catch {
  Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
  if ($_.ErrorDetails) { Write-Host $_.ErrorDetails.Message -ForegroundColor Red }
}
