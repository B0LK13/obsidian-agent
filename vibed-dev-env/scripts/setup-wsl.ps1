# Vibe.d Development Environment - WSL2 Setup Script
# Run this script as Administrator in PowerShell

#Requires -RunAsAdministrator

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Vibe.d Development Environment Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Windows version
$osVersion = [System.Environment]::OSVersion.Version
if ($osVersion.Build -lt 19041) {
    Write-Host "ERROR: Windows 10 version 2004 or higher is required for WSL2." -ForegroundColor Red
    Write-Host "Current build: $($osVersion.Build)" -ForegroundColor Red
    exit 1
}

Write-Host "Step 1: Enabling Windows Subsystem for Linux..." -ForegroundColor Yellow
try {
    $wslFeature = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
    if ($wslFeature.State -ne "Enabled") {
        Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -NoRestart
        Write-Host "  WSL feature enabled." -ForegroundColor Green
    } else {
        Write-Host "  WSL feature already enabled." -ForegroundColor Green
    }
} catch {
    Write-Host "  ERROR: Failed to enable WSL feature: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 2: Enabling Virtual Machine Platform..." -ForegroundColor Yellow
try {
    $vmFeature = Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform
    if ($vmFeature.State -ne "Enabled") {
        Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -NoRestart
        Write-Host "  Virtual Machine Platform enabled." -ForegroundColor Green
    } else {
        Write-Host "  Virtual Machine Platform already enabled." -ForegroundColor Green
    }
} catch {
    Write-Host "  ERROR: Failed to enable Virtual Machine Platform: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 3: Setting WSL2 as default version..." -ForegroundColor Yellow
try {
    wsl --set-default-version 2
    Write-Host "  WSL2 set as default." -ForegroundColor Green
} catch {
    Write-Host "  Note: You may need to restart and run 'wsl --set-default-version 2' manually." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Step 4: Checking for Ubuntu installation..." -ForegroundColor Yellow
$distros = wsl --list --quiet 2>$null
if ($distros -match "Ubuntu") {
    Write-Host "  Ubuntu is already installed." -ForegroundColor Green
} else {
    Write-Host "  Ubuntu not found. Installing Ubuntu 22.04..." -ForegroundColor Yellow
    try {
        wsl --install -d Ubuntu-22.04
        Write-Host "  Ubuntu 22.04 installation initiated." -ForegroundColor Green
    } catch {
        Write-Host "  Please install Ubuntu 22.04 from the Microsoft Store." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Step 5: Checking Docker Desktop..." -ForegroundColor Yellow
$dockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
if (Test-Path $dockerPath) {
    Write-Host "  Docker Desktop is installed." -ForegroundColor Green
    Write-Host "  Please ensure WSL2 backend is enabled in Docker Desktop settings." -ForegroundColor Yellow
} else {
    Write-Host "  Docker Desktop not found." -ForegroundColor Yellow
    Write-Host "  Please download and install Docker Desktop from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Restart your computer to complete WSL2 setup" -ForegroundColor White
Write-Host "2. Open Ubuntu from Start Menu and complete initial setup" -ForegroundColor White
Write-Host "3. Install Docker Desktop and enable WSL2 backend" -ForegroundColor White
Write-Host "4. Enable your Ubuntu distro in Docker Desktop -> Resources -> WSL Integration" -ForegroundColor White
Write-Host "5. Install VS Code extensions: Remote-Containers, CodeLLDB, D Language" -ForegroundColor White
Write-Host ""

$restart = Read-Host "Would you like to restart now? (y/n)"
if ($restart -eq "y" -or $restart -eq "Y") {
    Restart-Computer -Force
}
