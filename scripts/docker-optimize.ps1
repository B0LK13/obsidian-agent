# Docker Optimization and Cleanup Script
# Run this script to analyze and optimize Docker resources

param(
    [switch]$Cleanup,
    [switch]$Force,
    [switch]$DryRun
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Docker Optimization Analysis" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker is running
try {
    docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Docker is not running. Please start Docker Desktop." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "ERROR: Docker is not available." -ForegroundColor Red
    exit 1
}

# Get disk usage summary
Write-Host "## Disk Usage Summary" -ForegroundColor Yellow
Write-Host ""
$diskUsage = docker system df --format "table {{.Type}}\t{{.TotalCount}}\t{{.Size}}\t{{.Reclaimable}}"
$diskUsage | ForEach-Object { Write-Host $_ }
Write-Host ""

# Analyze images
Write-Host "## Image Analysis" -ForegroundColor Yellow
$images = docker images --format "{{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.ID}}" | ConvertFrom-Csv -Delimiter "`t" -Header "Image","Size","ID"
$totalImages = $images.Count
Write-Host "  Total Images: $totalImages" -ForegroundColor White

# Find dangling images
$danglingImages = docker images --filter "dangling=true" -q
$danglingCount = if ($danglingImages) { ($danglingImages | Measure-Object).Count } else { 0 }
Write-Host "  Dangling Images: $danglingCount" -ForegroundColor $(if ($danglingCount -gt 0) { "Yellow" } else { "Green" })

# Find large images (>1GB)
Write-Host ""
Write-Host "  Large Images (>1GB):" -ForegroundColor White
docker images --format "{{.Repository}}:{{.Tag}}\t{{.Size}}" | ForEach-Object {
    if ($_ -match "(\d+\.?\d*)(GB)") {
        $size = [float]$matches[1]
        if ($size -ge 1) {
            Write-Host "    $_" -ForegroundColor Yellow
        }
    }
}

# Analyze containers
Write-Host ""
Write-Host "## Container Analysis" -ForegroundColor Yellow
$runningContainers = docker ps -q | Measure-Object
$stoppedContainers = docker ps -a --filter "status=exited" -q | Measure-Object
Write-Host "  Running Containers: $($runningContainers.Count)" -ForegroundColor Green
Write-Host "  Stopped Containers: $($stoppedContainers.Count)" -ForegroundColor $(if ($stoppedContainers.Count -gt 0) { "Yellow" } else { "Green" })

# Analyze volumes
Write-Host ""
Write-Host "## Volume Analysis" -ForegroundColor Yellow
$volumes = docker volume ls -q | Measure-Object
$danglingVolumes = docker volume ls --filter "dangling=true" -q | Measure-Object
Write-Host "  Total Volumes: $($volumes.Count)" -ForegroundColor White
Write-Host "  Dangling Volumes: $($danglingVolumes.Count)" -ForegroundColor $(if ($danglingVolumes.Count -gt 0) { "Yellow" } else { "Green" })

# Analyze networks
Write-Host ""
Write-Host "## Network Analysis" -ForegroundColor Yellow
$networks = docker network ls --format "{{.Name}}" | Where-Object { $_ -notin @("bridge", "host", "none") }
$networkCount = ($networks | Measure-Object).Count
Write-Host "  Custom Networks: $networkCount" -ForegroundColor White

# Build cache analysis
Write-Host ""
Write-Host "## Build Cache Analysis" -ForegroundColor Yellow
$buildCache = docker buildx du 2>&1 | Select-String "Reclaimable:"
if ($buildCache) {
    Write-Host "  $buildCache" -ForegroundColor Yellow
}

# Recommendations
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Recommendations" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$recommendations = @()

if ($danglingCount -gt 0) {
    $recommendations += "- Remove $danglingCount dangling images: docker image prune -f"
}

if ($stoppedContainers.Count -gt 0) {
    $recommendations += "- Remove $($stoppedContainers.Count) stopped containers: docker container prune -f"
}

if ($danglingVolumes.Count -gt 0) {
    $recommendations += "- Remove $($danglingVolumes.Count) dangling volumes: docker volume prune -f"
}

$recommendations += "- Clean build cache: docker buildx prune -f"
$recommendations += "- Full cleanup (careful!): docker system prune -a --volumes"

foreach ($rec in $recommendations) {
    Write-Host $rec -ForegroundColor White
}

# Cleanup if requested
if ($Cleanup) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Performing Cleanup" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    if ($DryRun) {
        Write-Host "[DRY RUN] Would execute the following:" -ForegroundColor Yellow
    }

    # Remove dangling images
    if ($danglingCount -gt 0) {
        if ($DryRun) {
            Write-Host "  docker image prune -f" -ForegroundColor Gray
        } else {
            Write-Host "Removing dangling images..." -ForegroundColor Yellow
            docker image prune -f
        }
    }

    # Remove stopped containers
    if ($stoppedContainers.Count -gt 0) {
        if ($DryRun) {
            Write-Host "  docker container prune -f" -ForegroundColor Gray
        } else {
            Write-Host "Removing stopped containers..." -ForegroundColor Yellow
            docker container prune -f
        }
    }

    # Remove dangling volumes
    if ($danglingVolumes.Count -gt 0) {
        if ($DryRun) {
            Write-Host "  docker volume prune -f" -ForegroundColor Gray
        } else {
            Write-Host "Removing dangling volumes..." -ForegroundColor Yellow
            docker volume prune -f
        }
    }

    # Clean build cache
    if ($DryRun) {
        Write-Host "  docker buildx prune -f" -ForegroundColor Gray
    } else {
        Write-Host "Cleaning build cache..." -ForegroundColor Yellow
        docker buildx prune -f
    }

    # Full cleanup if forced
    if ($Force -and -not $DryRun) {
        Write-Host ""
        Write-Host "WARNING: Full cleanup requested. This will remove:" -ForegroundColor Red
        Write-Host "  - All unused images" -ForegroundColor Red
        Write-Host "  - All unused volumes" -ForegroundColor Red
        Write-Host "  - All unused networks" -ForegroundColor Red
        Write-Host ""
        $confirm = Read-Host "Are you sure? (yes/no)"
        if ($confirm -eq "yes") {
            docker system prune -a --volumes -f
        } else {
            Write-Host "Full cleanup cancelled." -ForegroundColor Yellow
        }
    }

    Write-Host ""
    Write-Host "Cleanup complete!" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Analysis Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
