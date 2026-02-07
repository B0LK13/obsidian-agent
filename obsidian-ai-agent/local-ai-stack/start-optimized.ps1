#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start the Optimized Local AI Stack
.DESCRIPTION
    Platform-independent launcher with performance optimizations
.NOTES
    Version: 2.0.0 (Optimized)
#>

[CmdletBinding()]
param(
    [switch]$CpuOnly,
    [switch]$Benchmark,
    [string]$ConfigFile = "$PSScriptRoot\ai_stack\config.yaml",
    [string]$ModelPath = "$PSScriptRoot\models",
    [int]$LlmPort = 8000,
    [int]$EmbedPort = 8001,
    [int]$VectorPort = 8002
)

# Banner
Write-Host @"

================================================================================
  OBSIDIAN AI AGENT - Optimized Local AI Stack v2.0
================================================================================
  Features:
  - Model caching & hot-swapping
  - Prompt caching for repeated queries
  - GPU auto-detection & optimization
  - Batched inference
  - Performance monitoring
================================================================================

"@ -ForegroundColor Cyan

# Check Python
$pythonVersion = & python --version 2>&1
Write-Host "Python: $pythonVersion" -ForegroundColor Gray

# Detect hardware
Write-Host "`nHardware Detection..." -ForegroundColor Yellow

$hasGpu = $false
try {
    $nvidiaSmi = & nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>$null
    if ($nvidiaSmi) {
        $hasGpu = $true
        Write-Host "  GPU: $nvidiaSmi" -ForegroundColor Green
    }
} catch {
    Write-Host "  GPU: None detected" -ForegroundColor Yellow
}

$cpuCores = (Get-CimInstance Win32_Processor).NumberOfLogicalProcessors
Write-Host "  CPU Cores: $cpuCores" -ForegroundColor Gray

# Check models
Write-Host "`nModel Check..." -ForegroundColor Yellow
$models = Get-ChildItem -Path $ModelPath -Filter "*.gguf" -ErrorAction SilentlyContinue
if ($models.Count -eq 0) {
    Write-Host "  ⚠ No models found!" -ForegroundColor Red
    Write-Host "  Download with: python ai_stack/model_manager_cli.py recommend" -ForegroundColor Yellow
} else {
    Write-Host "  Found $($models.Count) model(s):" -ForegroundColor Green
    $models | ForEach-Object { Write-Host "    - $($_.Name)" -ForegroundColor Gray }
}

# Start optimized LLM server
Write-Host "`nStarting Optimized LLM Server..." -ForegroundColor Yellow

$llmScript = @"
import sys
sys.path.insert(0, r'$PSScriptRoot')
from ai_stack.llm_server_optimized import start_llm_server
start_llm_server(
    host='127.0.0.1',
    port=$LlmPort,
    model_path=r'$ModelPath',
    cpu_only=$(if ($CpuOnly) { 'True' } else { 'False' }),
    workers=2
)
"@

$llmProcess = Start-Process -FilePath python -ArgumentList "-c", $llmScript -PassThru -WindowStyle Hidden
Write-Host "  LLM Server PID: $($llmProcess.Id)" -ForegroundColor Green

# Start embeddings
Start-Sleep -Seconds 2
Write-Host "`nStarting Embeddings Server..." -ForegroundColor Yellow
$embedScript = @"
import sys
sys.path.insert(0, r'$PSScriptRoot')
from ai_stack.embed_server import start_embed_server
start_embed_server(host='127.0.0.1', port=$EmbedPort)
"@
$embedProcess = Start-Process -FilePath python -ArgumentList "-c", $embedScript -PassThru -WindowStyle Hidden
Write-Host "  Embeddings PID: $($embedProcess.Id)" -ForegroundColor Green

# Start vector DB
Start-Sleep -Seconds 2
Write-Host "`nStarting Vector DB..." -ForegroundColor Yellow
$vectorScript = @"
import sys
sys.path.insert(0, r'$PSScriptRoot')
from ai_stack.vector_server import start_vector_server
start_vector_server(host='127.0.0.1', port=$VectorPort)
"@
$vectorProcess = Start-Process -FilePath python -ArgumentList "-c", $vectorScript -PassThru -WindowStyle Hidden
Write-Host "  Vector DB PID: $($vectorProcess.Id)" -ForegroundColor Green

# Wait for health
Write-Host "`nHealth Check..." -ForegroundColor Yellow
$services = @(
    @{ Name = "LLM"; Port = $LlmPort },
    @{ Name = "Embeddings"; Port = $EmbedPort },
    @{ Name = "Vector DB"; Port = $VectorPort }
)

foreach ($svc in $services) {
    $healthy = $false
    for ($i = 0; $i -lt 30; $i++) {
        try {
            $resp = Invoke-WebRequest -Uri "http://127.0.0.1:$($svc.Port)/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($resp.StatusCode -eq 200) {
                $healthy = $true
                break
            }
        } catch {}
        Start-Sleep -Seconds 1
    }
    $status = if ($healthy) { "✓ OK" } else { "✗ FAIL" }
    Write-Host "  $($svc.Name): $status" -ForegroundColor $(if ($healthy) { "Green" } else { "Red" })
}

# Benchmark if requested
if ($Benchmark) {
    Write-Host "`nRunning Performance Benchmark..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
    python $PSScriptRoot\ai_stack\benchmark.py --url "http://127.0.0.1:$LlmPort"
}

# Status
Write-Host @"

================================================================================
  OPTIMIZED STACK RUNNING
================================================================================
  LLM:      http://127.0.0.1:$LlmPort  (with caching & GPU opt)
  Embed:    http://127.0.0.1:$EmbedPort
  Vector:   http://127.0.0.1:$VectorPort

  Admin:    http://127.0.0.1:$LlmPort/admin/stats
  Cache:    POST http://127.0.0.1:$LlmPort/admin/clear-cache

  Press Ctrl+C to stop
================================================================================

"@ -ForegroundColor Green

# Wait
try {
    while ($true) {
        if ($llmProcess.HasExited -or $embedProcess.HasExited -or $vectorProcess.HasExited) {
            Write-Host "`nService stopped unexpectedly!" -ForegroundColor Red
            break
        }
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Host "`nStopping services..." -ForegroundColor Yellow
    @($llmProcess, $embedProcess, $vectorProcess) | ForEach-Object {
        if (-not $_.HasExited) { $_.Kill() }
    }
    Write-Host "Done!" -ForegroundColor Green
}
