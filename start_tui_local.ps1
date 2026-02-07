# PowerShell script to start the PKM Agent TUI with Local LLM (LM Studio) configuration

# 1. Configuration for Local LLM
$env:PKMA_LLM__PROVIDER = "openai"
$env:PKMA_LLM__BASE_URL = "http://localhost:1234/v1"
$env:PKMA_LLM__API_KEY = "lm-studio"
$env:PKMA_LLM__MODEL = "local-model"

# Point to the demo environment (so it sees the notes we just created!)
$env:PKMA_PKM_ROOT = "$PSScriptRoot\demo_rag_env\vault"
$env:PKMA_DATA_DIR = "$PSScriptRoot\demo_rag_env\.pkm-agent"

# Ensure directories exist (fixes [WinError 2] if demo wasn't run)
if (-not (Test-Path $env:PKMA_PKM_ROOT)) {
    New-Item -ItemType Directory -Force -Path $env:PKMA_PKM_ROOT | Out-Null
    Write-Host "⚠️  Created missing vault directory: $env:PKMA_PKM_ROOT" -ForegroundColor Yellow
}

# 2. General Config
$env:PYTHONIOENCODING = "utf-8"
$ScriptPath = $PSScriptRoot
$Env:PYTHONPATH = "$ScriptPath\B0LK13v2\pkm-agent\src"

# 3. Find Python
if (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonExe = "python"
} elseif (Test-Path "C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe") {
    $PythonExe = "C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe"
} else {
    Write-Error "Could not find Python! Please add python to PATH."
    exit 1
}

# 4. Launch TUI
Write-Host "🚀 Starting PKM Agent TUI (Local LLM Mode)..." -ForegroundColor Cyan
Write-Host "   Backend: http://localhost:1234/v1" -ForegroundColor Gray
Write-Host "   Using Python: $PythonExe" -ForegroundColor Gray
Write-Host "   Make sure LM Studio Server is running!" -ForegroundColor Yellow

& $PythonExe -m pkm_agent.cli tui --prompt "What can you do?"
