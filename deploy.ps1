# Cortex Deployment Script — PowerShell (Windows)
# Google Cloud Gen AI Academy APAC 2026 — Cohort 1 Hackathon

$ErrorActionPreference = "Stop"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "Cortex Deployment — Cloud Run (Windows)" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Load .env file if it exists
$envFile = ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | Where-Object { $_ -notmatch '^#' -and $_ -match '=' } | ForEach-Object {
        $parts = $_.Split('=', 2)
        if ($parts.Count -eq 2) {
            [Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim(), "Process")
        }
    }
    Write-Host "[OK] Loaded environment from .env" -ForegroundColor Green
}

# Validate required variables
$required = @("PROJECT_ID", "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")
$missing = $required | Where-Object { [string]::IsNullOrEmpty([Environment]::GetEnvironmentVariable($_)) }
if ($missing.Count -gt 0) {
    Write-Host "ERROR: Missing required environment variables: $($missing -join ', ')" -ForegroundColor Red
    Write-Host "Copy .env.example to .env and fill in all values." -ForegroundColor Yellow
    exit 1
}

$projectId = $env:PROJECT_ID
$region = if ($env:REGION) { $env:REGION } else { "europe-west1" }
$serviceName = "cortex-agent"
$imageUri = "gcr.io/$projectId/$serviceName`:latest"

Write-Host "Project: $projectId" -ForegroundColor White
Write-Host "Region: $region" -ForegroundColor White
Write-Host "Service: $serviceName" -ForegroundColor White

# Step 1: Build Docker image
Write-Host "`nStep 1: Building Docker image with Cloud Build..." -ForegroundColor Yellow
gcloud builds submit --tag $imageUri --project=$projectId
if ($LASTEXITCODE -ne 0) { throw "Cloud Build failed" }
Write-Host "[OK] Docker image built: $imageUri" -ForegroundColor Green

# Step 2: Deploy to Cloud Run
Write-Host "`nStep 2: Deploying to Cloud Run..." -ForegroundColor Yellow
$deployCmd = @(
    "run", "deploy", $serviceName,
    "--image=$imageUri",
    "--platform=managed",
    "--region=$region",
    "--allow-unauthenticated",
    "--port=8080",
    "--memory=512Mi",
    "--cpu=1",
    "--set-env-vars=DB_HOST=$($env:DB_HOST),DB_PORT=$($env:DB_PORT),DB_NAME=$($env:DB_NAME),DB_USER=$($env:DB_USER),DB_PASSWORD=$($env:DB_PASSWORD),PROJECT_ID=$projectId,FLASK_ENV=production",
    "--project=$projectId"
)
& gcloud @deployCmd
if ($LASTEXITCODE -ne 0) { throw "Cloud Run deployment failed" }

# Step 3: Get service URL
Write-Host "`nStep 3: Getting service URL..." -ForegroundColor Yellow
$serviceUrl = gcloud run services describe $serviceName --platform=managed --region=$region --format="value(status.url)" --project=$projectId

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "✅ Cortex deployed successfully!" -ForegroundColor Green
Write-Host "🌐 URL: $serviceUrl" -ForegroundColor White
Write-Host "📋 API: $serviceUrl/api/query" -ForegroundColor White
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Set up Cloud SQL PostgreSQL and run db/schema.sql + db/seed.sql"
Write-Host "2. Configure Google OAuth for Gmail/Calendar APIs (see tools/authenticate.py)"
Write-Host "3. Submit: https://vision.hack2skill.com/event/apac-genaiacademy"
