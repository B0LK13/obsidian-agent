#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Verify Obsidian AI Agent plugin installation and functionality
    
.DESCRIPTION
    Comprehensive verification script for the Obsidian AI Agent plugin
    Checks build, installation, configuration, and reports status
#>

param(
    [switch]$Detailed
)

$ErrorActionPreference = "Stop"
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "  Obsidian AI Agent - Installation Verification" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

# Paths
$projectPath = "F:\CascadeProjects\project_obsidian_agent"
$vaultPath = "C:\Users\Admin\Documents\B0LK13v2"
$pluginPath = "$vaultPath\.obsidian\plugins\obsidian-ai-agent"

$passed = 0
$failed = 0
$warnings = 0

function Test-Check {
    param(
        [string]$Name,
        [scriptblock]$Test,
        [string]$SuccessMsg = "✅ PASS",
        [string]$FailMsg = "❌ FAIL",
        [string]$Category = ""
    )
    
    if ($Category) {
        Write-Host "`n[$Category] " -NoNewline -ForegroundColor Yellow
    }
    Write-Host $Name -NoNewline
    
    try {
        $result = & $Test
        if ($result) {
            Write-Host " ... $SuccessMsg" -ForegroundColor Green
            $script:passed++
            return $true
        } else {
            Write-Host " ... $FailMsg" -ForegroundColor Red
            $script:failed++
            return $false
        }
    } catch {
        Write-Host " ... $FailMsg - $($_.Exception.Message)" -ForegroundColor Red
        $script:failed++
        return $false
    }
}

Write-Host "[1/6] Checking Build Files..." -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

Test-Check "main.js exists" {
    Test-Path "$projectPath\main.js"
} -Category "Build"

Test-Check "manifest.json exists" {
    Test-Path "$projectPath\manifest.json"
} -Category "Build"

Test-Check "styles.css exists" {
    Test-Path "$projectPath\styles.css"
} -Category "Build"

# Check build size
$mainSize = (Get-Item "$projectPath\main.js").Length / 1KB
Test-Check "main.js size is reasonable (<500KB)" {
    $mainSize -lt 500
} -Category "Build"

Write-Host "`n[2/6] Checking Installation..." -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

Test-Check "Vault exists" {
    Test-Path $vaultPath
} -Category "Installation"

Test-Check "Plugin directory exists" {
    Test-Path $pluginPath
} -Category "Installation"

Test-Check "Plugin main.js installed" {
    Test-Path "$pluginPath\main.js"
} -Category "Installation"

Test-Check "Plugin manifest.json installed" {
    Test-Path "$pluginPath\manifest.json"
} -Category "Installation"

Test-Check "Plugin styles.css installed" {
    Test-Path "$pluginPath\styles.css"
} -Category "Installation"

# Check if files are up-to-date
$sourceMain = Get-Item "$projectPath\main.js"
$installedMain = Get-Item "$pluginPath\main.js"

Test-Check "Installed plugin is current" {
    $sourceMain.LastWriteTime -eq $installedMain.LastWriteTime
} -Category "Installation"

Write-Host "`n[3/6] Checking Configuration..." -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Read manifest
$manifest = Get-Content "$pluginPath\manifest.json" | ConvertFrom-Json

Test-Check "Manifest ID is correct" {
    $manifest.id -eq "obsidian-ai-agent"
} -Category "Configuration"

Test-Check "Plugin name is set" {
    $manifest.name -eq "Obsidian AI Agent"
} -Category "Configuration"

Test-Check "Version is set" {
    $null -ne $manifest.version
} -Category "Configuration"

Test-Check "Desktop only flag is set" {
    $manifest.isDesktopOnly -eq $true
} -Category "Configuration"

Write-Host "`n[4/6] Checking Dependencies..." -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

Test-Check "node_modules exists" {
    Test-Path "$projectPath\node_modules"
} -Category "Dependencies"

Test-Check "TypeScript installed" {
    Test-Path "$projectPath\node_modules\typescript"
} -Category "Dependencies"

Test-Check "Obsidian API installed" {
    Test-Path "$projectPath\node_modules\obsidian"
} -Category "Dependencies"

Write-Host "`n[5/6] Checking Source Files..." -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

$sourceFiles = @(
    "main.ts",
    "settings.ts",
    "settingsTab.ts",
    "aiService.ts",
    "agentModalEnhanced.ts"
)

foreach ($file in $sourceFiles) {
    Test-Check "$file exists" {
        Test-Path "$projectPath\$file"
    } -Category "Source"
}

Write-Host "`n[6/6] Checking Ollama Configuration..." -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Check if Ollama is running
Test-Check "Ollama service is accessible" {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -Method GET -TimeoutSec 5 -ErrorAction SilentlyContinue
        $response.StatusCode -eq 200
    } catch {
        $false
    }
} -Category "Ollama"

# Check settings file for Ollama profile
$settingsContent = Get-Content "$projectPath\settings.ts" -Raw
Test-Check "Ollama profile defined in settings" {
    $settingsContent -match "ollama-local"
} -Category "Ollama"

Test-Check "Default Ollama endpoint configured" {
    $settingsContent -match "http://localhost:11434"
} -Category "Ollama"

Write-Host "`n=====================================================================" -ForegroundColor Cyan
Write-Host "  Verification Summary" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "✅ Passed:   $passed" -ForegroundColor Green
Write-Host "❌ Failed:   $failed" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })
Write-Host "⚠️  Warnings: $warnings" -ForegroundColor Yellow
Write-Host ""

$totalChecks = $passed + $failed
$successRate = [math]::Round(($passed / $totalChecks) * 100, 1)

Write-Host "Success Rate: $successRate%" -ForegroundColor $(if ($successRate -ge 90) { "Green" } elseif ($successRate -ge 70) { "Yellow" } else { "Red" })
Write-Host ""

# Installation details
Write-Host "Installation Details:" -ForegroundColor Cyan
Write-Host "  Project Path:  $projectPath" -ForegroundColor Gray
Write-Host "  Vault Path:    $vaultPath" -ForegroundColor Gray
Write-Host "  Plugin Path:   $pluginPath" -ForegroundColor Gray
Write-Host "  Plugin Version: $($manifest.version)" -ForegroundColor Gray
Write-Host "  Main.js Size:   $([math]::Round($mainSize, 2)) KB" -ForegroundColor Gray
Write-Host ""

if ($Detailed) {
    Write-Host "=====================================================================" -ForegroundColor Cyan
    Write-Host "  Additional Information" -ForegroundColor Cyan
    Write-Host "=====================================================================" -ForegroundColor Cyan
    Write-Host ""
    
    # List all commands (if we can grep them)
    Write-Host "Available Commands:" -ForegroundColor Yellow
    $commands = Select-String -Path "$projectPath\main.ts" -Pattern "addCommand\({" -Context 0,5 | Select-Object -First 10
    Write-Host "  Found $($commands.Count)+ commands registered" -ForegroundColor Gray
    Write-Host ""
    
    # Check test results
    if (Test-Path "$projectPath\test_results.json") {
        Write-Host "Test Results:" -ForegroundColor Yellow
        $testResults = Get-Content "$projectPath\test_results.json" | ConvertFrom-Json
        Write-Host "  $testResults" -ForegroundColor Gray
    }
}

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "  Next Steps" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Open Obsidian" -ForegroundColor White
Write-Host "2. Go to Settings → Community Plugins" -ForegroundColor White
Write-Host "3. Find 'Obsidian AI Agent' and enable it" -ForegroundColor White
Write-Host "4. Configure your AI provider (Ollama recommended for local)" -ForegroundColor White
Write-Host "5. Test with Ctrl/Cmd+P → 'Ask AI Agent'" -ForegroundColor White
Write-Host ""

if ($failed -gt 0) {
    Write-Host "⚠️  Some checks failed. Please review the output above." -ForegroundColor Red
    exit 1
} else {
    Write-Host "✅ All checks passed! Plugin is ready to use." -ForegroundColor Green
    exit 0
}
