# BTC AI Platform — Start Cloudflare Tunnels
# This script starts two cloudflared tunnels to expose the frontend and backend publicly.

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$CF = Join-Path $ROOT "cloudflared.exe"

if (-not (Test-Path $CF)) {
    Write-Host "ERROR: cloudflared.exe not found. Download it first:" -ForegroundColor Red
    Write-Host "  curl.exe -L -o cloudflared.exe 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe'"
    exit 1
}

# Kill existing tunnels
Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force 2>$null
Start-Sleep 2

Write-Host "Starting backend tunnel (port 8000)..." -ForegroundColor Cyan
$backendProc = Start-Process -FilePath $CF -ArgumentList "tunnel","--url","http://localhost:8000" -NoNewWindow -RedirectStandardError "tunnel-backend-err.log" -PassThru

Write-Host "Starting frontend tunnel (port 3000)..." -ForegroundColor Cyan
$frontendProc = Start-Process -FilePath $CF -ArgumentList "tunnel","--url","http://localhost:3000" -NoNewWindow -RedirectStandardError "tunnel-frontend-err.log" -PassThru

Write-Host "Waiting for tunnels to initialize..." -ForegroundColor Yellow
Start-Sleep 15

# Extract URLs from logs
function Get-TunnelUrl($logFile) {
    if (Test-Path $logFile) {
        $lines = Get-Content $logFile
        $visitIdx = ($lines | Select-String "Visit").LineNumber
        if ($visitIdx) {
            $urlLine = $lines[$visitIdx[0]]
            if ($urlLine -match "(https://[a-z-]+\.trycloudflare\.com)") {
                return $Matches[1]
            }
        }
    }
    return $null
}

$backendUrl = Get-TunnelUrl "tunnel-backend-err.log"
$frontendUrl = Get-TunnelUrl "tunnel-frontend-err.log"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Tunnels are live!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
if ($backendUrl)  { Write-Host "  Backend:  $backendUrl" -ForegroundColor White }
if ($frontendUrl) { Write-Host "  Frontend: $frontendUrl" -ForegroundColor White }
Write-Host ""
Write-Host "  Login: admin@btc-ai.local / btc2025" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Press Ctrl+C to stop tunnels." -ForegroundColor Gray
Write-Host ""

# Update .env.local with backend URL
if ($backendUrl -and (Test-Path "frontend/.env.local")) {
    $envContent = "NEXT_PUBLIC_API_URL=$backendUrl`nNEXT_PUBLIC_SUPABASE_URL=`nNEXT_PUBLIC_SUPABASE_ANON_KEY="
    Set-Content -Path "frontend/.env.local" -Value $envContent -Encoding UTF8
    Write-Host "  Updated frontend/.env.local with backend URL" -ForegroundColor Cyan
}

# Keep running
try {
    Wait-Process -Id $backendProc.Id, $frontendProc.Id
} catch {
    Write-Host "Tunnels stopped." -ForegroundColor Yellow
}
