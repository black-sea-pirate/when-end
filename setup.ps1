# when-end Setup Script
# Run this script to check prerequisites and setup the application

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  when-end Application Setup   " -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker
Write-Host "Checking Docker..." -ForegroundColor Yellow
if (Get-Command docker -ErrorAction SilentlyContinue) {
    $dockerVersion = docker --version
    Write-Host "✓ Docker found: $dockerVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Docker not found! Please install Docker Desktop." -ForegroundColor Red
    Write-Host "  Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Red
    exit 1
}

# Check Docker Compose
Write-Host "Checking Docker Compose..." -ForegroundColor Yellow
if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
    $composeVersion = docker-compose --version
    Write-Host "✓ Docker Compose found: $composeVersion" -ForegroundColor Green
} else {
    Write-Host "! Docker Compose not found as separate command, checking docker compose..." -ForegroundColor Yellow
    try {
        docker compose version | Out-Null
        Write-Host "✓ Docker compose (built-in) is available" -ForegroundColor Green
    } catch {
        Write-Host "✗ Docker Compose not available!" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  Environment Setup               " -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

# Check if .env exists
if (Test-Path ".env") {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
    $overwrite = Read-Host "Do you want to overwrite it? (y/N)"
    if ($overwrite -ne "y") {
        Write-Host "Keeping existing .env file" -ForegroundColor Yellow
    } else {
        Copy-Item "ops\.env.example" ".env" -Force
        Write-Host "✓ Created new .env file from template" -ForegroundColor Green
    }
} else {
    Copy-Item "ops\.env.example" ".env"
    Write-Host "✓ Created .env file from template" -ForegroundColor Green
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  Configuration Required          " -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "You need to configure the following in .env file:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Google OAuth Credentials" -ForegroundColor Cyan
Write-Host "   - Go to: https://console.cloud.google.com/" -ForegroundColor White
Write-Host "   - Create OAuth 2.0 credentials" -ForegroundColor White
Write-Host "   - Add redirect URI: http://localhost:3000/api/auth/google/callback" -ForegroundColor White
Write-Host "   - Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env" -ForegroundColor White
Write-Host ""
Write-Host "2. JWT Secret Keys" -ForegroundColor Cyan
Write-Host "   Generate with: " -ForegroundColor White
Write-Host "   [Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))" -ForegroundColor Gray
Write-Host "   Set JWT_SECRET_KEY and JWT_REFRESH_SECRET_KEY in .env" -ForegroundColor White
Write-Host ""

$configure = Read-Host "Open .env file now? (Y/n)"
if ($configure -ne "n") {
    if (Get-Command notepad -ErrorAction SilentlyContinue) {
        notepad .env
    } else {
        Write-Host "Please edit .env file manually" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  Ready to Start!                 " -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "After configuring .env, run:" -ForegroundColor Green
Write-Host "  docker compose up -d" -ForegroundColor Cyan
Write-Host ""
Write-Host "Then access the application at:" -ForegroundColor Green
Write-Host "  http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "For more help, see:" -ForegroundColor Yellow
Write-Host "  - README.md" -ForegroundColor White
Write-Host "  - QUICKSTART.md" -ForegroundColor White
Write-Host "  - ARCHITECTURE.md" -ForegroundColor White
Write-Host ""
