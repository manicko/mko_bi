# =============================================================================
# Docker Image Scan Script
# Scans built Docker images for known vulnerabilities using Trivy.
#
# Prerequisites:
#   Install Trivy: https://trivy.dev/latest/getting-started/installation/
#   On Windows with winget: winget install AquaSecurity.Trivy
#
# Usage:
#   # Scan production image
#   .\docker\scripts\scan-images.ps1
#
#   # Scan specific target
#   .\docker\scripts\scan-images.ps1 -Target prod
#
#   # Scan all targets (dev, test, prod)
#   .\docker\scripts\scan-images.ps1 -AllTargets
#
#   # Fail on CRITICAL only (default: CRITICAL + HIGH)
#   .\docker\scripts\scan-images.ps1 -Severity CRITICAL
#
# Exit codes:
#   0 - No vulnerabilities found at the specified severity level
#   1 - Vulnerabilities found
# =============================================================================

param(
    [ValidateSet("dev", "test", "prod")]
    [string]$Target = "prod",

    [ValidateSet("CRITICAL", "HIGH", "MEDIUM", "LOW")]
    [string]$Severity = "HIGH",

    [switch]$AllTargets
)

$ErrorActionPreference = "Stop"

# Check Trivy is available
$trivy = Get-Command trivy -ErrorAction SilentlyContinue
if (-not $trivy) {
    Write-Error @"
Trivy not found. Install it first:
  winget install AquaSecurity.Trivy
Or see: https://trivy.dev/latest/getting-started/installation/
"@
    exit 1
}

$targets = if ($AllTargets) { @("dev", "test", "prod") } else { @($Target) }

$overallExitCode = 0

foreach ($t in $targets) {
    $imageName = "mkobi-$t"
    $dockerfilePath = Join-Path $PSScriptRoot ".." "Dockerfile"
    $buildContext = Join-Path $PSScriptRoot ".." ".."

    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Building $t image..." -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan

    # Build the image
    & docker build -f $dockerfilePath --target $t -t $imageName $buildContext
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Build failed for target: $t"
        $overallExitCode = 1
        continue
    }

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Scanning $imageName for $Severity+ vulnerabilities..." -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan

    # Scan the built image
    & trivy image `
        --severity $Severity `
        --exit-code 1 `
        --ignore-unfixed `
        --format table `
        $imageName

    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Vulnerabilities found in $imageName at $Severity+ severity"
        $overallExitCode = 1
    } else {
        Write-Host "No $Severity+ vulnerabilities found in $imageName" -ForegroundColor Green
    }

    Write-Host ""
}

exit $overallExitCode
