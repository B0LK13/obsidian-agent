# Reinstall PKM Agent - Force rebuild
$pythonExe = "C:\Users\Admin\scoop\apps\python\current\python.exe"
$pipExe = "C:\Users\Admin\scoop\apps\python\current\Scripts\pip.exe"
$pkgDir = "C:\Users\Admin\Documents\B0LK13v2\pkm-agent"

Write-Host "=== Reinstalling PKM Agent ===" -ForegroundColor Cyan

# Uninstall completely
Write-Host "`n[1/4] Uninstalling..." -ForegroundColor Yellow
& $pipExe uninstall -y pkm-agent 2>$null

# Clear any cached builds
Write-Host "`n[2/4] Clearing build cache..." -ForegroundColor Yellow
$buildDirs = @(
    "$pkgDir\build",
    "$pkgDir\dist",
    "$pkgDir\*.egg-info",
    "$pkgDir\src\*.egg-info"
)
foreach ($d in $buildDirs) {
    if (Test-Path $d) {
        Remove-Item -Recurse -Force $d 2>$null
        Write-Host "  Removed: $d" -ForegroundColor Gray
    }
}

# Reinstall in editable mode
Write-Host "`n[3/4] Installing fresh (editable mode)..." -ForegroundColor Yellow
Set-Location $pkgDir
& $pipExe install -e . --no-cache-dir

# Test
Write-Host "`n[4/4] Testing..." -ForegroundColor Cyan
& $pythonExe -c "from pkm_agent import PKMAgentApp, Config; print('Core imports OK')"
& $pythonExe -c "from pkm_agent.rag import Chunker, VectorStore; print('RAG imports OK')"
& $pythonExe -c "from pkm_agent.llm import OpenAIProvider, OllamaProvider; print('LLM imports OK')"

Write-Host "`nTesting module execution:" -ForegroundColor Cyan
& $pythonExe -m pkm_agent --help

Write-Host "`nTesting CLI script:" -ForegroundColor Cyan
& "C:\Users\Admin\scoop\apps\python\current\Scripts\pkm-agent.exe" --help

Write-Host "`n=== Done ===" -ForegroundColor Green
