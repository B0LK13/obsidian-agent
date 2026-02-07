# Fix Python PATH and test installation
# Run in PowerShell: .\fix_python_path.ps1

Write-Host "=== Fixing Python PATH ===" -ForegroundColor Cyan

# Check possible Python locations
$pythonPaths = @(
    "F:\DevDrive\scoop\apps\python\current\python.exe",
    "C:\Users\Admin\scoop\apps\python\current\python.exe",
    "C:\Python312\python.exe",
    "C:\Python311\python.exe"
)

$foundPython = $null
foreach ($p in $pythonPaths) {
    if (Test-Path $p) {
        $foundPython = $p
        Write-Host "Found Python at: $p" -ForegroundColor Green
        break
    }
}

if (-not $foundPython) {
    Write-Host "Python not found! Installing via winget..." -ForegroundColor Yellow
    winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    $foundPython = "C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe"
}

# Get Python directory
$pythonDir = Split-Path $foundPython -Parent
$scriptsDir = Join-Path $pythonDir "Scripts"

# Add to PATH for this session
$env:Path = "$pythonDir;$scriptsDir;" + $env:Path

# Test Python
Write-Host "`n=== Testing Python ===" -ForegroundColor Cyan
& $foundPython --version
& "$scriptsDir\pip.exe" --version

# Make PATH permanent
Write-Host "`n=== Making PATH permanent ===" -ForegroundColor Cyan
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$pythonDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$pythonDir;$scriptsDir;$userPath", "User")
    Write-Host "PATH updated permanently" -ForegroundColor Green
}

# Install PKM Agent
Write-Host "`n=== Installing PKM Agent ===" -ForegroundColor Cyan
$pkmAgentPath = "F:\DevDrive\projects\B0LK13v2\apps\pkm-agent"
if (-not (Test-Path $pkmAgentPath)) {
    $pkmAgentPath = "C:\Users\Admin\Documents\B0LK13v2\apps\pkm-agent"
}

if (Test-Path $pkmAgentPath) {
    Set-Location $pkmAgentPath
    Write-Host "Installing from: $pkmAgentPath" -ForegroundColor Gray
    & "$scriptsDir\pip.exe" install -e .
    
    Write-Host "`n=== Testing PKM Agent ===" -ForegroundColor Cyan
    & $foundPython -c "from pkm_agent import PKMAgentApp, Config; print('Core imports OK')"
    & $foundPython -c "from pkm_agent.rag import Chunker, VectorStore; print('RAG imports OK')"
    & $foundPython -c "from pkm_agent.llm import OpenAIProvider, OllamaProvider; print('LLM imports OK')"
    
    # Test CLI
    Write-Host "`n=== Testing CLI ===" -ForegroundColor Cyan
    & "$scriptsDir\pkm-agent.exe" --help
} else {
    Write-Host "PKM Agent path not found!" -ForegroundColor Red
}

Write-Host "`n=== Done ===" -ForegroundColor Green
Write-Host "Open a NEW terminal to use Python globally."
