# Clean Install PKM Agent
# Run in PowerShell: .\install_pkm_agent.ps1

Write-Host "=== PKM Agent Clean Installation ===" -ForegroundColor Cyan

# Find executables
$pythonExe = "F:\DevDrive\scoop\apps\python\current\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "C:\Users\Admin\scoop\apps\python\current\python.exe"
}
$scriptsDir = (Split-Path $pythonExe -Parent) + "\Scripts"
$pipExe = "$scriptsDir\pip.exe"

Write-Host "Python: $pythonExe" -ForegroundColor Gray

# Step 1: Clear pip cache
Write-Host "`n[1/6] Clearing pip cache..." -ForegroundColor Yellow
& $pipExe cache purge

# Step 2: Uninstall conflicting packages
Write-Host "`n[2/6] Removing conflicting packages..." -ForegroundColor Yellow
& $pipExe uninstall -y chromadb onnxruntime chroma-hnswlib 2>$null

# Step 3: Upgrade pip
Write-Host "`n[3/6] Upgrading pip..." -ForegroundColor Yellow
& $pythonExe -m pip install --upgrade pip

# Step 4: Install core dependencies first
Write-Host "`n[4/6] Installing numpy and faiss-cpu..." -ForegroundColor Yellow
& $pipExe install numpy faiss-cpu

# Step 5: Install PKM Agent (use local copy, not F:\DevDrive)
Write-Host "`n[5/6] Installing PKM Agent from C:\Users\Admin\Documents..." -ForegroundColor Yellow
$pkmPath = "C:\Users\Admin\Documents\B0LK13v2\apps\pkm-agent"

Set-Location $pkmPath
Write-Host "  Installing from: $pkmPath" -ForegroundColor Gray
& $pipExe install -e . --no-cache-dir

# Step 6: Test imports
Write-Host "`n[6/6] Testing imports..." -ForegroundColor Cyan
& $pythonExe -c "from pkm_agent import PKMAgentApp, Config; print('Core imports OK')"
& $pythonExe -c "from pkm_agent.rag import Chunker, VectorStore; print('RAG imports OK')"
& $pythonExe -c "from pkm_agent.llm import OpenAIProvider, OllamaProvider; print('LLM imports OK')"

# Test CLI
Write-Host "`n=== Testing CLI ===" -ForegroundColor Cyan
$cliPath = "$scriptsDir\pkm-agent.exe"
if (Test-Path $cliPath) {
    & $cliPath --help
} else {
    Write-Host "CLI not found at $cliPath" -ForegroundColor Yellow
    Write-Host "Trying Python module directly..." -ForegroundColor Gray
    & $pythonExe -m pkm_agent --help
}

Write-Host "`n=== Installation Complete ===" -ForegroundColor Green
