#Requires -Version 5.1
<#
.SYNOPSIS
    Automated Windows setup for Obsidian AI Agent

.DESCRIPTION
    One-command setup script that handles:
    - Python verification
    - Virtual environment creation
    - Dependency installation
    - Windows Defender configuration
    - Model download (optional)

.NOTES
    GitHub Issue: https://github.com/B0LK13/obsidian-agent/issues/111
#>

param(
    [switch]$SkipDefender,
    [switch]$SkipModel,
    [string]$ModelName = "phi-2"
)

$ErrorActionPreference = "Stop"

# Colors
function Write-Step { Write-Host "`n▶ $args" -ForegroundColor Cyan }
function Write-Success { Write-Host "  ✅ $args" -ForegroundColor Green }
function Write-Info { Write-Host "  ℹ️  $args" -ForegroundColor White }
function Write-Warn { Write-Host "  ⚠️  $args" -ForegroundColor Yellow }
function Write-Fail { Write-Host "  ❌ $args" -ForegroundColor Red }

Write-Host "`n" -NoNewline
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Magenta
Write-Host "  🚀 Obsidian AI Agent - Windows Setup" -ForegroundColor Magenta
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Magenta

# Step 1: Check Python
Write-Step "Checking Python installation..."

try {
    $pythonVersion = python --version 2>&1 | Out-String
    if ($pythonVersion -match "Python (3\.\d+)\.\d+") {
        $major = [int]$matches[1].Split('.')[0]
        $minor = [int]$matches[1].Split('.')[1]
        
        if ($major -eq 3 -and $minor -ge 10 -and $minor -le 12) {
            Write-Success "Python $pythonVersion"
        } else {
            Write-Warn "Python version $pythonVersion detected"
            Write-Info "Recommended: Python 3.10-3.12"
        }
    }
} catch {
    Write-Fail "Python not found!"
    Write-Info "Install Python from: https://www.python.org/downloads/"
    Write-Info "Make sure to check 'Add Python to PATH' during installation"
    exit 1
}

# Step 2: Create virtual environment
Write-Step "Creating virtual environment..."

if (Test-Path "venv") {
    Write-Info "Virtual environment already exists"
} else {
    python -m venv venv
    Write-Success "Created virtual environment"
}

# Step 3: Activate venv and upgrade pip
Write-Step "Activating virtual environment..."

& ".\venv\Scripts\Activate.ps1"
Write-Success "Activated"

Write-Step "Upgrading pip..."
python -m pip install --upgrade pip setuptools wheel --quiet
Write-Success "pip upgraded"

# Step 4: Install dependencies
Write-Step "Installing dependencies..."
Write-Info "This may take 5-10 minutes..."

pip install -r requirements.txt --quiet
Write-Success "Core dependencies installed"

# Step 5: Install PKM agent
if (Test-Path "pkm-agent") {
    Write-Step "Installing PKM agent..."
    Push-Location pkm-agent
    pip install -e . --quiet
    Pop-Location
    Write-Success "PKM agent installed"
}

# Step 6: Windows Defender setup
if (-not $SkipDefender) {
    Write-Step "Configuring Windows Defender..."
    
    $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    
    if ($isAdmin) {
        if (Test-Path "scripts\windows-defender-setup.ps1") {
            & ".\scripts\windows-defender-setup.ps1"
        } else {
            Write-Warn "Windows Defender script not found"
            Write-Info "Run manually: .\scripts\windows-defender-setup.ps1"
        }
    } else {
        Write-Warn "Not running as Administrator"
        Write-Info "To configure Windows Defender, run this script as Administrator"
        Write-Info "Or run: .\scripts\windows-defender-setup.ps1"
    }
} else {
    Write-Info "Skipping Windows Defender setup (use --SkipDefender to enable)"
}

# Step 7: Download model
if (-not $SkipModel) {
    Write-Step "Downloading AI model..."
    Write-Info "Model: $ModelName (~1.5-4GB)"
    
    if (Test-Path "obsidian-ai-agent\local-ai-stack\ai_stack\model_downloader.py") {
        Push-Location "obsidian-ai-agent\local-ai-stack\ai_stack"
        python model_downloader.py download $ModelName --quant Q4_K_M
        Pop-Location
        Write-Success "Model downloaded"
    } else {
        Write-Warn "Model downloader not found"
        Write-Info "Download manually later"
    }
} else {
    Write-Info "Skipping model download (use --SkipModel=false to enable)"
}

# Step 8: Verification
Write-Step "Verifying installation..."

$checks = @{
    "Python" = { python --version }
    "pip" = { pip --version }
    "pkm-agent" = { pkm-agent --version }
}

foreach ($check in $checks.Keys) {
    try {
        $result = & $checks[$check] 2>&1
        Write-Success "$check OK"
    } catch {
        Write-Fail "$check FAILED"
    }
}

# Final message
Write-Host "`n" -NoNewline
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✅ Setup Complete!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Green

Write-Host "`n📝 Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Configure .env file:" -ForegroundColor White
Write-Host "     copy .env.example .env" -ForegroundColor Gray
Write-Host "     notepad .env" -ForegroundColor Gray
Write-Host "`n  2. Start PKM agent:" -ForegroundColor White
Write-Host "     .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "     pkm-agent tui" -ForegroundColor Gray
Write-Host "`n  3. Read the docs:" -ForegroundColor White
Write-Host "     docs\WINDOWS_INSTALLATION_GUIDE.md" -ForegroundColor Gray
Write-Host ""
