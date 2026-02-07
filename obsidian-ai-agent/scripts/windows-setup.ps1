#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Complete Windows Setup for Obsidian AI Agent
    Automates installation, configuration, and first run

.DESCRIPTION
    This script performs a complete setup of the Obsidian AI Agent on Windows:
    - Checks Python installation
    - Creates virtual environment
    - Installs dependencies
    - Configures Windows Defender
    - Downloads a default model
    - Starts the AI stack

.NOTES
    Must be run as Administrator
    Version: 1.0.0
#>

[CmdletBinding()]
param(
    [switch]$SkipModelDownload,
    [switch]$SkipDefenderSetup,
    [string]$Model = "phi-2"
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "Continue"

# Configuration
$script:ProjectRoot = Split-Path -Parent $PSScriptRoot
$script:VenvPath = Join-Path $ProjectRoot "venv"
$script:ModelsPath = Join-Path $ProjectRoot "models"
$script:PythonMinVersion = "3.10"

function Show-Banner {
    Clear-Host
    Write-Host @"
╔══════════════════════════════════════════════════════════════════╗
║          Obsidian AI Agent - Complete Windows Setup              ║
║                                                                  ║
║  This script will set up everything you need to run the         ║
║  Obsidian AI Agent on your Windows system.                      ║
╚══════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan
    Write-Host ""
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-Python {
    Write-Host "🔍 Checking Python installation..." -ForegroundColor Cyan
    
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            $version = "$major.$minor"
            
            Write-Host "   ✓ Found Python $version" -ForegroundColor Green
            
            # Check version
            if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
                Write-Host "   ✗ Python $script:PythonMinVersion or higher required" -ForegroundColor Red
                return $false
            }
            
            return $true
        }
    }
    catch {
        Write-Host "   ✗ Python not found in PATH" -ForegroundColor Red
    }
    
    return $false
}

function Install-Python {
    Write-Host "`n⚠️  Python not found or version too old." -ForegroundColor Yellow
    Write-Host "Please download and install Python $script:PythonMinVersion or higher from:" -ForegroundColor Yellow
    Write-Host "https://www.python.org/downloads/" -ForegroundColor Cyan
    Write-Host "`nMake sure to check 'Add Python to PATH' during installation." -ForegroundColor Yellow
    Write-Host "`nPress any key to open the download page..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    Start-Process "https://www.python.org/downloads/"
    exit 1
}

function Initialize-VirtualEnvironment {
    Write-Host "`n🐍 Setting up Python virtual environment..." -ForegroundColor Cyan
    
    Set-Location $script:ProjectRoot
    
    if (Test-Path $script:VenvPath) {
        Write-Host "   ℹ Virtual environment already exists" -ForegroundColor Gray
    } else {
        Write-Host "   Creating virtual environment..." -ForegroundColor Gray
        python -m venv $script:VenvPath
        Write-Host "   ✓ Virtual environment created" -ForegroundColor Green
    }
    
    # Activate
    Write-Host "   Activating virtual environment..." -ForegroundColor Gray
    $activateScript = Join-Path $script:VenvPath "Scripts\Activate.ps1"
    & $activateScript
    
    Write-Host "   ✓ Virtual environment activated" -ForegroundColor Green
}

function Install-Dependencies {
    Write-Host "`n📦 Installing dependencies..." -ForegroundColor Cyan
    
    $requirementsFile = Join-Path $script:ProjectRoot "local-ai-stack\requirements.txt"
    
    if (Test-Path $requirementsFile) {
        Write-Host "   Installing from requirements.txt..." -ForegroundColor Gray
        pip install -r $requirementsFile -q
        Write-Host "   ✓ Dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "   Installing core packages..." -ForegroundColor Gray
        pip install llama-cpp-python flask numpy -q
        Write-Host "   ✓ Core packages installed" -ForegroundColor Green
    }
    
    # Optional: hnswlib for optimized vector store
    Write-Host "   Installing optional packages..." -ForegroundColor Gray
    pip install hnswlib -q 2>$null
    if ($?) {
        Write-Host "   ✓ HNSW support installed" -ForegroundColor Green
    } else {
        Write-Host "   ⚠ HNSW not available (using linear search fallback)" -ForegroundColor Yellow
    }
}

function Invoke-DefenderSetup {
    if ($SkipDefenderSetup) {
        Write-Host "`n⏭ Skipping Windows Defender setup" -ForegroundColor Gray
        return
    }
    
    Write-Host "`n🛡️ Configuring Windows Defender..." -ForegroundColor Cyan
    
    $defenderScript = Join-Path $PSScriptRoot "windows-defender-setup.ps1"
    
    if (Test-Path $defenderScript) {
        # Run in non-interactive mode
        & $defenderScript -CheckOnly | Out-Null
        
        $response = Read-Host "   Add Windows Defender exclusions? (recommended) [Y/n]"
        if ($response -eq '' -or $response -eq 'Y' -or $response -eq 'y') {
            & $defenderScript
        } else {
            Write-Host "   ⚠ Skipped. You may experience slow startup." -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ⚠ Defender setup script not found" -ForegroundColor Yellow
    }
}

function Invoke-ModelDownload {
    if ($SkipModelDownload) {
        Write-Host "`n⏭ Skipping model download" -ForegroundColor Gray
        return
    }
    
    Write-Host "`n🤖 Downloading AI model..." -ForegroundColor Cyan
    
    # Create models directory
    New-Item -ItemType Directory -Force -Path $script:ModelsPath | Out-Null
    
    # Check if model already exists
    $existingModels = Get-ChildItem -Path $script:ModelsPath -Filter "*.gguf" -ErrorAction SilentlyContinue
    if ($existingModels) {
        Write-Host "   ℹ Models already exist:" -ForegroundColor Gray
        $existingModels | ForEach-Object { Write-Host "     - $($_.Name)" -ForegroundColor Gray }
        
        $response = Read-Host "   Download another model? [y/N]"
        if ($response -ne 'Y' -and $response -ne 'y') {
            Write-Host "   Using existing models" -ForegroundColor Green
            return
        }
    }
    
    # Download using model manager
    $modelManager = Join-Path $script:ProjectRoot "local-ai-stack\ai_stack\model_manager_cli.py"
    
    if (Test-Path $modelManager) {
        Write-Host "   Downloading $Model model (this may take several minutes)..." -ForegroundColor Gray
        python $modelManager download $Model --quant Q4_K_M
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✓ Model downloaded successfully" -ForegroundColor Green
        } else {
            Write-Host "   ⚠ Model download failed. You can download manually later." -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ⚠ Model manager not found" -ForegroundColor Yellow
    }
}

function Start-AIStack {
    Write-Host "`n🚀 Starting Local AI Stack..." -ForegroundColor Cyan
    Write-Host "   Press Ctrl+C to stop the servers" -ForegroundColor Gray
    Write-Host ""
    
    Set-Location (Join-Path $script:ProjectRoot "local-ai-stack")
    
    # Find a model
    $modelFile = Get-ChildItem -Path $script:ModelsPath -Filter "*.gguf" | Select-Object -First 1
    
    if (-not $modelFile) {
        Write-Host "   ⚠ No model found. Please download a model first." -ForegroundColor Yellow
        return
    }
    
    Write-Host "   Using model: $($modelFile.Name)" -ForegroundColor Gray
    
    # Use GPU-safe server if available
    $llmServer = Join-Path $script:ProjectRoot "local-ai-stack\ai_stack\llm_server_gpu_safe.py"
    if (-not (Test-Path $llmServer)) {
        $llmServer = Join-Path $script:ProjectRoot "local-ai-stack\ai_stack\llm_server_optimized.py"
    }
    if (-not (Test-Path $llmServer)) {
        $llmServer = Join-Path $script:ProjectRoot "local-ai-stack\ai_stack\llm_server.py"
    }
    
    # Start servers
    try {
        Write-Host "   Starting LLM Server..." -ForegroundColor Gray
        Start-Process python -ArgumentList "`"$llmServer`"", "--model-path", "`"$script:ModelsPath`"" -NoNewWindow
        
        Start-Sleep -Seconds 3
        
        Write-Host "   Starting Embedding Server..." -ForegroundColor Gray
        $embedServer = Join-Path $script:ProjectRoot "local-ai-stack\ai_stack\embed_server.py"
        if (Test-Path $embedServer) {
            Start-Process python -ArgumentList "`"$embedServer`"" -NoNewWindow
        }
        
        Start-Sleep -Seconds 2
        
        Write-Host "   Starting Vector DB Server..." -ForegroundColor Gray
        $vectorServer = Join-Path $script:ProjectRoot "local-ai-stack\ai_stack\vector_server_optimized.py"
        if (-not (Test-Path $vectorServer)) {
            $vectorServer = Join-Path $script:ProjectRoot "local-ai-stack\ai_stack\vector_server.py"
        }
        if (Test-Path $vectorServer) {
            Start-Process python -ArgumentList "`"$vectorServer`"" -NoNewWindow
        }
        
        Start-Sleep -Seconds 2
        
        Write-Host "`n✅ AI Stack started successfully!" -ForegroundColor Green
        Write-Host "   LLM Server: http://127.0.0.1:8000" -ForegroundColor Gray
        Write-Host "   Embed Server: http://127.0.0.1:8001" -ForegroundColor Gray
        Write-Host "   Vector Server: http://127.0.0.1:8002" -ForegroundColor Gray
        
    } catch {
        Write-Host "   ✗ Failed to start servers: $_" -ForegroundColor Red
    }
}

function Show-NextSteps {
    Write-Host "`n" + "="*70 -ForegroundColor Cyan
    Write-Host "Setup Complete!" -ForegroundColor Green
    Write-Host "="*70 -ForegroundColor Cyan
    
    Write-Host "`nNext Steps:" -ForegroundColor Yellow
    Write-Host "1. Open Obsidian" -ForegroundColor White
    Write-Host "2. Install/Enable the PKM Agent plugin" -ForegroundColor White
    Write-Host "3. Configure plugin settings:" -ForegroundColor White
    Write-Host "   - LLM Endpoint: http://127.0.0.1:8000" -ForegroundColor Gray
    Write-Host "   - Embeddings Endpoint: http://127.0.0.1:8001" -ForegroundColor Gray
    Write-Host "   - Vector DB Endpoint: http://127.0.0.1:8002" -ForegroundColor Gray
    Write-Host "4. Test the connection" -ForegroundColor White
    Write-Host "5. Start chatting with your AI agent!" -ForegroundColor White
    
    Write-Host "`nUseful Commands:" -ForegroundColor Yellow
    Write-Host "  - View logs: Get-Content .\local-ai-stack\server.log -Tail 50" -ForegroundColor Gray
    Write-Host "  - Stop servers: Get-Process python | Stop-Process" -ForegroundColor Gray
    Write-Host "  - Run tests: python .\local-ai-stack\tests\run_tests.py" -ForegroundColor Gray
    
    Write-Host "`nDocumentation:" -ForegroundColor Yellow
    Write-Host "  - Installation Guide: docs\WINDOWS_INSTALLATION_GUIDE.md" -ForegroundColor Gray
    Write-Host "  - Troubleshooting: See docs\WINDOWS_INSTALLATION_GUIDE.md#troubleshooting" -ForegroundColor Gray
    
    Write-Host "`nPress any key to exit..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Main execution
Show-Banner

# Check admin privileges
if (-not (Test-Administrator)) {
    Write-Host "❌ ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "`nPlease right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Administrator privileges confirmed" -ForegroundColor Green

# Check Python
if (-not (Test-Python)) {
    Install-Python
}

# Setup virtual environment
Initialize-VirtualEnvironment

# Install dependencies
Install-Dependencies

# Configure Windows Defender
Invoke-DefenderSetup

# Download model
Invoke-ModelDownload

# Start AI stack
Start-AIStack

# Show completion
Show-NextSteps
