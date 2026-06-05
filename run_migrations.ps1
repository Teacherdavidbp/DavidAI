# Run Alembic migrations for davidai_dev
$ProjectRoot = "C:\AI-LAB-DPEDTECH-LTD\03_PROJECTS\DavidAI"
$EnvFile = Join-Path $ProjectRoot ".env"

Set-Location $ProjectRoot

Write-Host "DavidAI - running database migrations (davidai_dev)" -ForegroundColor Cyan

if (-not (Test-Path $EnvFile)) {
    Write-Host "ERROR: .env not found. Copy .env.example to .env and configure it." -ForegroundColor Red
    exit 1
}

Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

Write-Host "Loaded .env" -ForegroundColor Green

$alembic = Get-Command alembic -ErrorAction SilentlyContinue
if (-not $alembic) {
    Write-Host "Alembic not found. Install dependencies first:" -ForegroundColor Yellow
    Write-Host "  cd backend; python -m pip install -r requirements.txt"
    exit 1
}

python -m alembic upgrade head
if ($LASTEXITCODE -eq 0) {
    Write-Host "Migrations complete." -ForegroundColor Green
} else {
    Write-Host "Migration failed. Run: python backend/check_config.py" -ForegroundColor Red
    exit 1
}
