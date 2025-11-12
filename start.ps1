#!/usr/bin/env powershell
# O-SATE Complete Startup Script
# Starts both backend and frontend servers

Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       O-SATE: Open-Source AI Safety Testing Environment          ║" -ForegroundColor Cyan
Write-Host "║                   Web UI - Startup Helper                         ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$projectRoot = Get-Location
Write-Host "📍 Project Root: $projectRoot" -ForegroundColor Green

# Check if venv exists
if (-not (Test-Path "venv")) {
    Write-Host "⚠️  Virtual environment not found. Creating venv..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "✅ venv created" -ForegroundColor Green
}

# Activate venv
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Cyan
& "venv\Scripts\Activate.ps1"

# Check requirements
Write-Host "📦 Checking dependencies..." -ForegroundColor Cyan
pip install -q pyyaml python-dotenv openai requests flask flask-cors 2>$null

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                     READY TO START!                              ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "🚀 Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1️⃣  OPEN 2 TERMINALS (keep both open)" -ForegroundColor White
Write-Host ""
Write-Host "   Terminal 1 - Backend API:" -ForegroundColor Cyan
Write-Host "   $projectRoot\>" -NoNewline
Write-Host " python frontend/app.py" -ForegroundColor Green
Write-Host ""
Write-Host "   Terminal 2 - Frontend Dev Server:" -ForegroundColor Cyan
Write-Host "   $projectRoot\frontend\>" -NoNewline
Write-Host " npm run dev" -ForegroundColor Green
Write-Host ""
Write-Host "2️⃣  OPEN BROWSER" -ForegroundColor Cyan
Write-Host "   http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "3️⃣  ENJOY! 🎉" -ForegroundColor Magenta
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host "Tip: Backend runs on port 5000, Frontend on port 3000" -ForegroundColor Gray
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Gray
