#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Configure Windows Defender exclusions for Obsidian AI Agent

.DESCRIPTION
    Adds necessary exclusions to Windows Defender to prevent false positives
    that can cause slow startup or process blocking.

.NOTES
    Must be run as Administrator
    GitHub Issue: https://github.com/B0LK13/obsidian-agent/issues/104
#>

param(
    [switch]$Remove,
    [switch]$Verify
)

$ErrorActionPreference = "Stop"

# Colors
function Write-Success { Write-Host "✅ $args" -ForegroundColor Green }
function Write-Info { Write-Host "ℹ️  $args" -ForegroundColor Cyan }
function Write-Warn { Write-Host "⚠️  $args" -ForegroundColor Yellow }
function Write-Fail { Write-Host "❌ $args" -ForegroundColor Red }

Write-Host "`n🔒 Windows Defender Configuration for Obsidian AI Agent" -ForegroundColor Magenta
Write-Host "=" * 60 -ForegroundColor Gray

# Detect project path
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectPath = Split-Path -Parent $scriptPath

Write-Info "Project path: $projectPath"

# Define exclusions
$processExclusions = @(
    "python.exe",
    "pythonw.exe"
)

$pathExclusions = @(
    $projectPath,
    "$projectPath\venv",
    "$projectPath\obsidian-ai-agent\venv",
    "$projectPath\pkm-agent\venv",
    "$projectPath\models"
)

if ($Remove) {
    Write-Warn "Removing exclusions..."
    
    foreach ($process in $processExclusions) {
        try {
            Remove-MpPreference -ExclusionProcess $process -ErrorAction SilentlyContinue
            Write-Success "Removed process exclusion: $process"
        } catch {
            Write-Info "Process exclusion not found: $process"
        }
    }
    
    foreach ($path in $pathExclusions) {
        if (Test-Path $path) {
            try {
                Remove-MpPreference -ExclusionPath $path -ErrorAction SilentlyContinue
                Write-Success "Removed path exclusion: $path"
            } catch {
                Write-Info "Path exclusion not found: $path"
            }
        }
    }
    
    Write-Success "Exclusions removed successfully!"
    exit 0
}

if ($Verify) {
    Write-Info "Verifying exclusions..."
    
    $currentProcesses = (Get-MpPreference).ExclusionProcess
    $currentPaths = (Get-MpPreference).ExclusionPath
    
    Write-Host "`n📋 Process Exclusions:" -ForegroundColor Cyan
    foreach ($process in $processExclusions) {
        if ($currentProcesses -contains $process) {
            Write-Success "$process - Configured"
        } else {
            Write-Fail "$process - NOT configured"
        }
    }
    
    Write-Host "`n📁 Path Exclusions:" -ForegroundColor Cyan
    foreach ($path in $pathExclusions) {
        if ($currentPaths -contains $path) {
            Write-Success "$path - Configured"
        } else {
            Write-Fail "$path - NOT configured"
        }
    }
    
    exit 0
}

# Add exclusions
Write-Info "Adding Windows Defender exclusions...`n"

# Add process exclusions
Write-Host "📋 Adding process exclusions..." -ForegroundColor Cyan
foreach ($process in $processExclusions) {
    try {
        Add-MpPreference -ExclusionProcess $process -ErrorAction Stop
        Write-Success "Added: $process"
    } catch {
        if ($_.Exception.Message -like "*already exists*") {
            Write-Info "Already exists: $process"
        } else {
            Write-Fail "Failed to add $process : $($_.Exception.Message)"
        }
    }
}

# Add path exclusions
Write-Host "`n📁 Adding path exclusions..." -ForegroundColor Cyan
foreach ($path in $pathExclusions) {
    if (Test-Path $path) {
        try {
            Add-MpPreference -ExclusionPath $path -ErrorAction Stop
            Write-Success "Added: $path"
        } catch {
            if ($_.Exception.Message -like "*already exists*") {
                Write-Info "Already exists: $path"
            } else {
                Write-Fail "Failed to add $path : $($_.Exception.Message)"
            }
        }
    } else {
        Write-Warn "Path not found (skipping): $path"
    }
}

# Verify configuration
Write-Host "`n✅ Configuration complete!`n" -ForegroundColor Green

Write-Host "📊 Current Exclusions:" -ForegroundColor Cyan
Write-Host "`nProcesses:" -ForegroundColor Yellow
Get-MpPreference | Select-Object -ExpandProperty ExclusionProcess | Where-Object { $_ -in $processExclusions } | ForEach-Object { Write-Host "  - $_" }

Write-Host "`nPaths:" -ForegroundColor Yellow
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath | Where-Object { $_ -like "*B0LK13v2*" } | ForEach-Object { Write-Host "  - $_" }

Write-Host "`n" + "=" * 60 -ForegroundColor Gray
Write-Info "To verify exclusions later, run:"
Write-Host "    .\windows-defender-setup.ps1 -Verify" -ForegroundColor White
Write-Info "To remove exclusions, run:"
Write-Host "    .\windows-defender-setup.ps1 -Remove" -ForegroundColor White
Write-Host ""
Write-Success "Windows Defender is now configured for optimal performance!"
Write-Host ""
