# ============================================
# Zwift RGB Control - PowerShell Launcher
# ============================================

# Get script directory
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# Pretty banner
Write-Host "`n" -ForegroundColor Cyan
Write-Host "  ╔════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║   🚴 Zwift RGB Control Panel      ║" -ForegroundColor Cyan
Write-Host "  ╚════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host "`n" -ForegroundColor Cyan

# Change to project directory
Set-Location $projectRoot

# Check if venv exists
$venvPath = Join-Path $projectRoot ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "  ❌ Virtual environment not found at: $venvPath" -ForegroundColor Red
    Write-Host "  💡 Run: python -m venv .venv" -ForegroundColor Yellow
    Read-Host "  Press Enter to exit"
    exit 1
}

# Activate venv
Write-Host "  ⚙️  Activating virtual environment..." -ForegroundColor Yellow
& "$venvPath\Scripts\Activate.ps1"

# Check if main.py exists
if (-not (Test-Path "app\main.py")) {
    Write-Host "  ❌ app\main.py not found!" -ForegroundColor Red
    Read-Host "  Press Enter to exit"
    exit 1
}

# Start the app
Write-Host "  ▶️  Starting Zwift RGB Controller..." -ForegroundColor Green
Write-Host "  📊 Monitor your power levels in real-time!" -ForegroundColor Cyan
Write-Host "`n" -ForegroundColor Cyan

python -m app.main

# If app exits with error
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n  ❌ Application stopped with error code: $LASTEXITCODE" -ForegroundColor Red
    Read-Host "  Press Enter to close"
} else {
    Write-Host "`n  ✅ Application closed successfully" -ForegroundColor Green
    Start-Sleep -Milliseconds 2000
}
