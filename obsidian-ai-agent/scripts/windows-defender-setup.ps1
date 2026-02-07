#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Windows Defender Setup for Obsidian AI Agent
    Prevents false positive detections and improves startup performance

.DESCRIPTION
    This script configures Windows Defender exclusions for the Obsidian AI Agent
    to prevent false positive detections and reduce startup delays.

.NOTES
    Must be run as Administrator
    Version: 1.0.0
#>

[CmdletBinding()]
param(
    [switch]$RemoveExclusions,
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"

# Paths that need exclusions
$script:ExclusionPaths = @(
    "$env:USERPROFILE\Documents\B0LK13v2",
    "$env:USERPROFILE\Documents\B0LK13v2\obsidian-ai-agent",
    "$env:USERPROFILE\Documents\B0LK13v2\B0LK13v2\.obsidian\plugins\obsidian-pkm-agent",
    "$env:LOCALAPPDATA\Programs\Python",  # Python installation
    "$env:USERPROFILE\.cache\huggingface",  # HuggingFace cache
    "$env:USERPROFILE\.ollama"  # Ollama models
)

$script:ExclusionProcesses = @(
    "python.exe",
    "pythonw.exe",
    "ollama.exe",
    "obsidian.exe"
)

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-CurrentExclusions {
    Write-Host "`n📋 Current Windows Defender Exclusions:" -ForegroundColor Cyan
    Write-Host "=" * 60
    
    try {
        $pathExclusions = Get-MpPreference | Select-Object -ExpandProperty ExclusionPath
        $processExclusions = Get-MpPreference | Select-Object -ExpandProperty ExclusionProcess
        
        Write-Host "`nPath Exclusions:" -ForegroundColor Yellow
        if ($pathExclusions) {
            $pathExclusions | ForEach-Object { Write-Host "  ✓ $_" -ForegroundColor Green }
        } else {
            Write-Host "  (none)" -ForegroundColor Gray
        }
        
        Write-Host "`nProcess Exclusions:" -ForegroundColor Yellow
        if ($processExclusions) {
            $processExclusions | ForEach-Object { Write-Host "  ✓ $_" -ForegroundColor Green }
        } else {
            Write-Host "  (none)" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "  Error reading exclusions: $_" -ForegroundColor Red
    }
    
    Write-Host "=" * 60
}

function Add-DefenderExclusions {
    Write-Host "`n🔧 Adding Windows Defender Exclusions..." -ForegroundColor Cyan
    Write-Host "=" * 60
    
    $added = 0
    $skipped = 0
    
    # Add path exclusions
    foreach ($path in $script:ExclusionPaths) {
        if (Test-Path $path) {
            try {
                $existing = Get-MpPreference | Select-Object -ExpandProperty ExclusionPath
                if ($existing -contains $path) {
                    Write-Host "  ⏭ Already excluded: $path" -ForegroundColor Gray
                    $skipped++
                } else {
                    Add-MpPreference -ExclusionPath $path
                    Write-Host "  ✓ Added: $path" -ForegroundColor Green
                    $added++
                }
            }
            catch {
                Write-Host "  ✗ Failed: $path - $_" -ForegroundColor Red
            }
        } else {
            Write-Host "  ⚠ Path not found (skipped): $path" -ForegroundColor Yellow
        }
    }
    
    # Add process exclusions
    foreach ($process in $script:ExclusionProcesses) {
        try {
            $existing = Get-MpPreference | Select-Object -ExpandProperty ExclusionProcess
            if ($existing -contains $process) {
                Write-Host "  ⏭ Already excluded: $process" -ForegroundColor Gray
                $skipped++
            } else {
                Add-MpPreference -ExclusionProcess $process
                Write-Host "  ✓ Added process: $process" -ForegroundColor Green
                $added++
            }
        }
        catch {
            Write-Host "  ✗ Failed: $process - $_" -ForegroundColor Red
        }
    }
    
    Write-Host "=" * 60
    Write-Host "Added: $added, Skipped: $skipped" -ForegroundColor Cyan
}

function Remove-DefenderExclusions {
    Write-Host "`n Removing Windows Defender Exclusions..." -ForegroundColor Yellow
    Write-Host "=" * 60
    
    $removed = 0
    
    foreach ($path in $script:ExclusionPaths) {
        try {
            Remove-MpPreference -ExclusionPath $path -ErrorAction SilentlyContinue
            Write-Host "  ✓ Removed: $path" -ForegroundColor Green
            $removed++
        }
        catch {
            Write-Host "  ⚠ Not found or error: $path" -ForegroundColor Gray
        }
    }
    
    foreach ($process in $script:ExclusionProcesses) {
        try {
            Remove-MpPreference -ExclusionProcess $process -ErrorAction SilentlyContinue
            Write-Host "  ✓ Removed process: $process" -ForegroundColor Green
            $removed++
        }
        catch {
            Write-Host "  ⚠ Not found or error: $process" -ForegroundColor Gray
        }
    }
    
    Write-Host "=" * 60
    Write-Host "Removed: $removed exclusions" -ForegroundColor Yellow
}

function Test-DefenderStatus {
    Write-Host "`n🔍 Checking Windows Defender Status..." -ForegroundColor Cyan
    Write-Host "=" * 60
    
    try {
        $mpComputerStatus = Get-MpComputerStatus
        
        Write-Host "`nDefender Status:" -ForegroundColor Yellow
        Write-Host "  Antivirus enabled: $($mpComputerStatus.AntivirusEnabled)" -ForegroundColor $(if($mpComputerStatus.AntivirusEnabled){"Green"}else{"Red"})
        Write-Host "  Real-time protection: $($mpComputerStatus.RealTimeProtectionEnabled)" -ForegroundColor $(if($mpComputerStatus.RealTimeProtectionEnabled){"Green"}else{"Red"})
        Write-Host "  Behavior monitor: $($mpComputerStatus.BehaviorMonitorEnabled)" -ForegroundColor $(if($mpComputerStatus.BehaviorMonitorEnabled){"Green"}else{"Yellow"})
        
        if (-not $mpComputerStatus.RealTimeProtectionEnabled) {
            Write-Host "`n⚠️  Real-time protection is disabled. Exclusions may not be necessary." -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "  Error checking Defender status: $_" -ForegroundColor Red
    }
    
    Write-Host "=" * 60
}

function Show-Banner {
    Clear-Host
    Write-Host @"
╔══════════════════════════════════════════════════════════════════╗
║           Obsidian AI Agent - Windows Defender Setup             ║
║                                                                  ║
║  This script configures Windows Defender to prevent false        ║
║  positives and improve startup performance.                      ║
╚══════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan
}

function Show-CompletionMessage {
    Write-Host "`n✅ Setup Complete!" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Yellow
    Write-Host "  1. Restart Obsidian if it's currently running"
    Write-Host "  2. Start the local AI stack: .\start-local-ai-stack.ps1"
    Write-Host "  3. Open Obsidian and test the PKM Agent plugin"
    Write-Host "`nIf you still experience issues:" -ForegroundColor Yellow
    Write-Host "  - Check Windows Defender history for blocked items"
    Write-Host "  - Run this script again with -CheckOnly to verify exclusions"
    Write-Host "  - Check the troubleshooting guide in WINDOWS_DEFENDER_GUIDE.md"
}

# Main execution
Show-Banner

# Check admin privileges
if (-not (Test-Administrator)) {
    Write-Host "`n❌ ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "`nPlease:" -ForegroundColor Yellow
    Write-Host "  1. Close this window"
    Write-Host "  2. Right-click PowerShell"
    Write-Host "  3. Select 'Run as Administrator'"
    Write-Host "  4. Run this script again"
    exit 1
}

Write-Host "✓ Administrator privileges confirmed" -ForegroundColor Green

# Check Defender status
Test-DefenderStatus

# Show current exclusions
Get-CurrentExclusions

if ($CheckOnly) {
    Write-Host "`n📋 Check-only mode - no changes made." -ForegroundColor Cyan
    exit 0
}

if ($RemoveExclusions) {
    $confirm = Read-Host "`n⚠️  Are you sure you want to remove all exclusions? (yes/no)"
    if ($confirm -eq "yes") {
        Remove-DefenderExclusions
    } else {
        Write-Host "Cancelled." -ForegroundColor Yellow
    }
} else {
    Write-Host "`nℹ️  The following exclusions will be added:" -ForegroundColor Yellow
    Write-Host "`nPaths:" -ForegroundColor Cyan
    $script:ExclusionPaths | ForEach-Object { Write-Host "  • $_" }
    Write-Host "`nProcesses:" -ForegroundColor Cyan
    $script:ExclusionProcesses | ForEach-Object { Write-Host "  • $_" }
    
    $confirm = Read-Host "`nProceed? (yes/no)"
    if ($confirm -eq "yes") {
        Add-DefenderExclusions
        Get-CurrentExclusions
        Show-CompletionMessage
    } else {
        Write-Host "Cancelled." -ForegroundColor Yellow
    }
}

Write-Host "`nPress any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
