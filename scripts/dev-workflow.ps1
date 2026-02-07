# Development Workflow Helper
# Quick commands for common development tasks

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "status", "logs", "shell", "build", "test", "clean", "mcp", "help")]
    [string]$Command = "help",
    
    [Parameter(Position=1)]
    [string]$Target = "all"
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot

function Show-Help {
    Write-Host @"
Development Workflow Helper
===========================

Usage: dev-workflow.ps1 <command> [target]

Commands:
  start [service]    Start development services
  stop [service]     Stop development services
  status             Show status of all services
  logs [service]     View logs (default: all)
  shell [service]    Open shell in container
  build [target]     Build project or container
  test [type]        Run tests (unit/integration/e2e/all)
  clean              Clean build artifacts and caches
  mcp                Show MCP status and tools
  help               Show this help message

Examples:
  .\dev-workflow.ps1 start
  .\dev-workflow.ps1 logs api
  .\dev-workflow.ps1 test unit
  .\dev-workflow.ps1 shell db

"@ -ForegroundColor Cyan
}

function Start-Services {
    param([string]$Service)
    
    Write-Host "Starting services..." -ForegroundColor Yellow
    
    if ($Service -eq "all") {
        docker-compose up -d
    } else {
        docker-compose up -d $Service
    }
    
    Write-Host "Services started!" -ForegroundColor Green
    docker-compose ps
}

function Stop-Services {
    param([string]$Service)
    
    Write-Host "Stopping services..." -ForegroundColor Yellow
    
    if ($Service -eq "all") {
        docker-compose down
    } else {
        docker-compose stop $Service
    }
    
    Write-Host "Services stopped!" -ForegroundColor Green
}

function Show-Status {
    Write-Host "=== Docker Containers ===" -ForegroundColor Cyan
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    Write-Host ""
    Write-Host "=== Docker Resources ===" -ForegroundColor Cyan
    docker system df --format "table {{.Type}}\t{{.Size}}\t{{.Reclaimable}}"
    
    Write-Host ""
    Write-Host "=== MCP Servers ===" -ForegroundColor Cyan
    docker mcp server ls 2>$null
}

function Show-Logs {
    param([string]$Service)
    
    if ($Service -eq "all") {
        docker-compose logs -f --tail=100
    } else {
        docker-compose logs -f --tail=100 $Service
    }
}

function Open-Shell {
    param([string]$Service)
    
    if ($Service -eq "all") {
        Write-Host "Please specify a service name" -ForegroundColor Red
        return
    }
    
    docker-compose exec $Service sh -c "if command -v bash > /dev/null; then bash; else sh; fi"
}

function Build-Project {
    param([string]$Target)
    
    Write-Host "Building $Target..." -ForegroundColor Yellow
    
    switch ($Target) {
        "docker" {
            docker-compose build --no-cache
        }
        "all" {
            docker-compose build
        }
        default {
            docker-compose build $Target
        }
    }
    
    Write-Host "Build complete!" -ForegroundColor Green
}

function Run-Tests {
    param([string]$Type)
    
    Write-Host "Running $Type tests..." -ForegroundColor Yellow
    
    switch ($Type) {
        "unit" {
            $result = npm run test:unit 2>$null
            if (-not $?) { docker-compose exec app npm run test:unit }
        }
        "integration" {
            $result = npm run test:integration 2>$null
            if (-not $?) { docker-compose exec app npm run test:integration }
        }
        "e2e" {
            $result = npm run test:e2e 2>$null
            if (-not $?) { docker-compose exec app npm run test:e2e }
        }
        "all" {
            $result = npm test 2>$null
            if (-not $?) { docker-compose exec app npm test }
        }
        default {
            $result = npm test 2>$null
            if (-not $?) { docker-compose exec app npm test }
        }
    }
}

function Clean-Project {
    Write-Host "Cleaning project..." -ForegroundColor Yellow
    
    # Stop containers
    docker-compose down -v 2>$null
    
    # Remove build artifacts
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue node_modules, dist, build, .next, coverage, .dub
    
    # Docker cleanup
    docker system prune -f
    docker volume prune -f
    docker buildx prune -f
    
    Write-Host "Clean complete!" -ForegroundColor Green
}

function Show-MCP {
    Write-Host "=== MCP Servers ===" -ForegroundColor Cyan
    docker mcp server ls
    
    Write-Host ""
    Write-Host "=== MCP Tools (first 20) ===" -ForegroundColor Cyan
    docker mcp tools ls 2>$null | Select-Object -First 25
    
    Write-Host ""
    Write-Host "=== Connected Clients ===" -ForegroundColor Cyan
    docker mcp client connect --help 2>&1 | Select-String "connected"
}

# Main execution
Set-Location $ProjectRoot

switch ($Command) {
    "start"  { Start-Services -Service $Target }
    "stop"   { Stop-Services -Service $Target }
    "status" { Show-Status }
    "logs"   { Show-Logs -Service $Target }
    "shell"  { Open-Shell -Service $Target }
    "build"  { Build-Project -Target $Target }
    "test"   { Run-Tests -Type $Target }
    "clean"  { Clean-Project }
    "mcp"    { Show-MCP }
    "help"   { Show-Help }
    default  { Show-Help }
}
