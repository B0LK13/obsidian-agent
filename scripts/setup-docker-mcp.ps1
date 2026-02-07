# Docker MCP Server Setup Script
# Configures essential MCP servers for development workflows

param(
    [switch]$EnableAll,
    [switch]$ListAvailable
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Docker MCP Server Configuration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Essential MCP servers for development
$essentialServers = @(
    @{ Name = "docker"; Description = "Docker container management" },
    @{ Name = "filesystem"; Description = "File system operations" },
    @{ Name = "git"; Description = "Git repository operations" },
    @{ Name = "github"; Description = "GitHub API integration" },
    @{ Name = "postgres"; Description = "PostgreSQL database operations" },
    @{ Name = "redis"; Description = "Redis cache operations" },
    @{ Name = "fetch"; Description = "HTTP fetch capabilities" },
    @{ Name = "time"; Description = "Time and timezone utilities" }
)

# Optional but useful servers
$optionalServers = @(
    @{ Name = "brave-search"; Description = "Web search via Brave" },
    @{ Name = "playwright"; Description = "Browser automation" },
    @{ Name = "memory"; Description = "Persistent memory storage" },
    @{ Name = "sequentialthinking"; Description = "Sequential reasoning" },
    @{ Name = "context7"; Description = "Context management" }
)

if ($ListAvailable) {
    Write-Host "Fetching available MCP servers from catalog..." -ForegroundColor Yellow
    docker mcp catalog show docker-mcp
    exit 0
}

# Check current status
Write-Host "## Current MCP Server Status" -ForegroundColor Yellow
$currentServers = docker mcp server ls 2>&1
Write-Host $currentServers -ForegroundColor White
Write-Host ""

# Enable essential servers
Write-Host "## Enabling Essential MCP Servers" -ForegroundColor Yellow
Write-Host ""

foreach ($server in $essentialServers) {
    Write-Host "Enabling $($server.Name)... " -NoNewline -ForegroundColor White
    try {
        $result = docker mcp server enable $server.Name 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "OK" -ForegroundColor Green
        } else {
            Write-Host "SKIPPED (may already be enabled or unavailable)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "FAILED: $_" -ForegroundColor Red
    }
}

if ($EnableAll) {
    Write-Host ""
    Write-Host "## Enabling Optional MCP Servers" -ForegroundColor Yellow
    Write-Host ""
    
    foreach ($server in $optionalServers) {
        Write-Host "Enabling $($server.Name)... " -NoNewline -ForegroundColor White
        try {
            $result = docker mcp server enable $server.Name 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "OK" -ForegroundColor Green
            } else {
                Write-Host "SKIPPED" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "FAILED: $_" -ForegroundColor Red
        }
    }
}

# Show final status
Write-Host ""
Write-Host "## Final MCP Server Status" -ForegroundColor Yellow
docker mcp server ls

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MCP Configuration Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To connect MCP to a client, run:" -ForegroundColor White
Write-Host "  docker mcp client connect <client-name>" -ForegroundColor Gray
Write-Host ""
Write-Host "Supported clients: claude-desktop, cursor, vscode, codex, continue, etc." -ForegroundColor Gray
Write-Host ""
