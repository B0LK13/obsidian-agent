# PowerShell Script to Verify OpenAI API Key
param(
    [Parameter(Mandatory=$false)]
    [string]$ApiKey
)

# 1. Check for API Key
if ([string]::IsNullOrEmpty($ApiKey)) {
    $ApiKey = $env:OPENAI_API_KEY
}

if ([string]::IsNullOrEmpty($ApiKey)) {
    Write-Host "⚠️  OPENAI_API_KEY not found in environment." -ForegroundColor Yellow
    $ApiKey = Read-Host "Please enter your OpenAI API Key (sk-...)" -AsSecureString
    $ApiKey = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($ApiKey))
}

if ([string]::IsNullOrEmpty($ApiKey)) {
    Write-Error "❌ No API Key provided. Exiting."
    exit 1
}

# 2. Set Environment Variables
$env:OPENAI_API_KEY = $ApiKey
$env:PYTHONIOENCODING = "utf-8"
$ScriptPath = $PSScriptRoot
$Env:PYTHONPATH = "$ScriptPath\B0LK13v2\pkm-agent\src"

Write-Host "`n🚀 Starting Verification..." -ForegroundColor Cyan
Write-Host "   PYTHONPATH: $Env:PYTHONPATH" -ForegroundColor Gray

# 3. Run the Python Verification Script
try {
    python "$ScriptPath\B0LK13v2\test_openai_connection.py"
} catch {
    Write-Error "Failed to execute python script. Make sure python is in your PATH."
}
