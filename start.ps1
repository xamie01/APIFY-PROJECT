#!/usr/bin/env powershell
# O-SATE Complete Startup Script
# Automatically starts backend (Python Flask) and frontend (Node.js Vite) servers

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "O-SATE: Open-Source AI Safety Testing Environment" -ForegroundColor Cyan
Write-Host "Web UI - Startup Helper" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = Get-Location
Write-Host "Project Root: $projectRoot" -ForegroundColor Green

# Check if venv exists
if (-not (Test-Path "venv")) {
    Write-Host "Virtual environment not found. Creating venv..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "venv created." -ForegroundColor Green
}

# Activate venv
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& "venv\Scripts\Activate.ps1"

# Check dependencies
Write-Host "Installing dependencies..." -ForegroundColor Cyan
pip install -q pyyaml python-dotenv openai requests flask flask-cors 2>$null

# Start backend (Flask)
Write-Host "Starting Backend API (Flask)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$projectRoot`"; & venv\Scripts\Activate.ps1; python frontend/app.py" `
    -WindowStyle Normal

# Start frontend (Vite)
Write-Host "Starting Frontend Dev Server (Vite)..." -ForegroundColor Yellow
$frontendPath = Join-Path $projectRoot "frontend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$frontendPath`"; npm run dev" `
    -WindowStyle Normal

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Green
Write-Host "SERVERS STARTED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "=====================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Open your browser and visit: http://localhost:3000" -ForegroundColor Cyan
Write-Host "Backend API running on port 5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Close this window to stop both servers." -ForegroundColor Gray
Write-Host "=====================================================================" -ForegroundColor Gray
