#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start the Local AI Stack for Obsidian AI Agent
.DESCRIPTION
    Platform-independent launcher for local AI services (LLM, Embeddings, Vector DB)
    All services bind to 127.0.0.1 only - no network egress
.NOTES
    File Name      : start-local-ai-stack.ps1
    Author         : Obsidian AI Agent
    Prerequisite   : PowerShell 7+, Python 3.10+, local model files
    Version        : 1.0.0
#>

[CmdletBinding()]
param(
    [switch]$CpuOnly,
    [int]$LlmPort = 8000,
    [int]$EmbedPort = 8001,
    [int]$VectorPort = 8002,
    [string]$ModelPath = "$PSScriptRoot\models",
    [switch]$SkipHealthCheck
)

# Configuration
$ErrorActionPreference = "Stop"

# ASCII Banner
Write-Host @"

================================================================================
  OBSIDIAN AI AGENT - Local AI Stack
================================================================================
  Platform: Windows (PowerShell)
  Mode: Local-only (127.0.0.1)
  Network Egress: BLOCKED
================================================================================

"@ -ForegroundColor Cyan

# Validate environment
Write-Host "[1/5] Validating environment..." -ForegroundColor Yellow

# Check Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Error "Python not found in PATH. Please install Python 3.10+"
    exit 1
}
$pythonVersion = & python --version 2>&1
Write-Host "      Python: $pythonVersion" -ForegroundColor Gray

# Check model directory
if (-not (Test-Path $ModelPath)) {
    Write-Host "      Creating model directory: $ModelPath" -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $ModelPath | Out-Null
}

# Detect hardware
Write-Host "`n[2/5] Hardware detection..." -ForegroundColor Yellow

$hasGpu = $false
$gpuInfo = "CPU Only"

if (-not $CpuOnly) {
    try {
        # Check for NVIDIA GPU
        $nvidiaSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
        if ($nvidiaSmi) {
            $gpuOutput = & nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>$null
            if ($gpuOutput) {
                $hasGpu = $true
                $gpuInfo = "NVIDIA GPU: $gpuOutput"
            }
        }
    } catch {
        Write-Host "      GPU detection failed, using CPU" -ForegroundColor Yellow
    }
}

Write-Host "      Mode: $(if ($hasGpu -and -not $CpuOnly) { 'GPU Accelerated' } else { 'CPU Only' })" -ForegroundColor $(if ($hasGpu -and -not $CpuOnly) { 'Green' } else { 'Yellow' })
Write-Host "      $gpuInfo" -ForegroundColor Gray

# Check for models
Write-Host "`n[3/5] Checking model availability..." -ForegroundColor Yellow

$modelFiles = Get-ChildItem -Path $ModelPath -Filter "*.gguf" -ErrorAction SilentlyContinue
Write-Host "      Found $($modelFiles.Count) model file(s)" -ForegroundColor Gray

foreach ($model in $modelFiles) {
    Write-Host "      - $($model.Name) ($([math]::Round($model.Length/1GB, 2)) GB)" -ForegroundColor Gray
}

if ($modelFiles.Count -eq 0) {
    Write-Host @"
      
      WARNING: No models found in $ModelPath
      
      Please download models to this directory:
      - LLM: https://huggingface.co/models?search=gguf
        Recommended: llama-2-7b-chat.Q4_K_M.gguf (4GB)
      - Embeddings: https://huggingface.co/sentence-transformers
        Recommended: all-MiniLM-L6-v2 (80MB)
      
"@ -ForegroundColor Red
    
    $continue = Read-Host "Continue anyway? (y/N)"
    if ($continue -ne 'y') { exit 1 }
}

# Start services
Write-Host "`n[4/5] Starting local AI services..." -ForegroundColor Yellow

$processes = @()

# Service 1: LLM Server
Write-Host "      Starting LLM Server on 127.0.0.1:$LlmPort..." -ForegroundColor Gray -NoNewline

try {
    $llmScript = @"
import sys
sys.path.insert(0, r'$PSScriptRoot')
from ai_stack.llm_server import start_llm_server
start_llm_server(host='127.0.0.1', port=$LlmPort, model_path=r'$ModelPath', cpu_only=$(if ($CpuOnly -or -not $hasGpu) { 'True' } else { 'False' }))
"@
    
    $llmProcess = Start-Process -FilePath python -ArgumentList "-c", $llmScript -PassThru -WindowStyle Hidden
    $processes += @{ Name = "LLM Server"; Process = $llmProcess; Port = $LlmPort; Url = "http://127.0.0.1:$LlmPort" }
    Write-Host " PID:$($llmProcess.Id)" -ForegroundColor Green
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Error "Failed to start LLM server: $_"
}

# Service 2: Embeddings Server
Start-Sleep -Seconds 2
Write-Host "      Starting Embeddings Server on 127.0.0.1:$EmbedPort..." -ForegroundColor Gray -NoNewline

try {
    $embedScript = @"
import sys
sys.path.insert(0, r'$PSScriptRoot')
from ai_stack.embed_server import start_embed_server
start_embed_server(host='127.0.0.1', port=$EmbedPort, model_path=r'$ModelPath')
"@
    
    $embedProcess = Start-Process -FilePath python -ArgumentList "-c", $embedScript -PassThru -WindowStyle Hidden
    $processes += @{ Name = "Embeddings"; Process = $embedProcess; Port = $EmbedPort; Url = "http://127.0.0.1:$EmbedPort" }
    Write-Host " PID:$($embedProcess.Id)" -ForegroundColor Green
} catch {
    Write-Host " FAILED" -ForegroundColor Red
}

# Service 3: Vector DB
Start-Sleep -Seconds 2
Write-Host "      Starting Vector DB on 127.0.0.1:$VectorPort..." -ForegroundColor Gray -NoNewline

try {
    $vectorScript = @"
import sys
sys.path.insert(0, r'$PSScriptRoot')
from ai_stack.vector_server import start_vector_server
start_vector_server(host='127.0.0.1', port=$VectorPort, data_path=r'$PSScriptRoot\data')
"@
    
    $vectorProcess = Start-Process -FilePath python -ArgumentList "-c", $vectorScript -PassThru -WindowStyle Hidden
    $processes += @{ Name = "Vector DB"; Process = $vectorProcess; Port = $VectorPort; Url = "http://127.0.0.1:$VectorPort" }
    Write-Host " PID:$($vectorProcess.Id)" -ForegroundColor Green
} catch {
    Write-Host " FAILED" -ForegroundColor Red
}

# Health checks
if (-not $SkipHealthCheck) {
    Write-Host "`n[5/5] Running health checks..." -ForegroundColor Yellow
    
    $maxRetries = 30
    $retryDelay = 1
    
    foreach ($svc in $processes) {
        Write-Host "      Checking $($svc.Name)..." -ForegroundColor Gray -NoNewline
        
        $healthy = $false
        for ($i = 0; $i -lt $maxRetries; $i++) {
            try {
                $response = Invoke-WebRequest -Uri "$($svc.Url)/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
                if ($response.StatusCode -eq 200) {
                    $healthy = $true
                    break
                }
            } catch {
                Start-Sleep -Seconds $retryDelay
            }
        }
        
        if ($healthy) {
            Write-Host " OK" -ForegroundColor Green
        } else {
            Write-Host " TIMEOUT" -ForegroundColor Red
        }
    }
}

# Print status
Write-Host @"

================================================================================
  LOCAL AI STACK STATUS
================================================================================
"@ -ForegroundColor Cyan

foreach ($svc in $processes) {
    $status = if ($svc.Process.HasExited) { "STOPPED" } else { "RUNNING" }
    $color = if ($svc.Process.HasExited) { "Red" } else { "Green" }
    Write-Host "  [$status] $($svc.Name.PadRight(15)) $($svc.Url)" -ForegroundColor $color
}

Write-Host @"

================================================================================
  NETWORK SECURITY
================================================================================
  Egress Policy: DENY ALL (localhost only)
  Bind Address:  127.0.0.1 (IPv4 loopback)
  External Access: BLOCKED
================================================================================

  OBSIDIAN PLUGIN CONFIGURATION:
  -----------------------------
  LLM Endpoint:      http://127.0.0.1:$LlmPort/v1/chat/completions
  Embeddings:        http://127.0.0.1:$EmbedPort/embed
  Vector DB:         http://127.0.0.1:$VectorPort

  Press Ctrl+C to stop all services

"@ -ForegroundColor Green

# Wait for Ctrl+C
try {
    while ($true) {
        $allRunning = $processes | Where-Object { -not $_.Process.HasExited }
        if (-not $allRunning) {
            Write-Host "`nOne or more services have stopped unexpectedly." -ForegroundColor Red
            break
        }
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Host "`n[STOPPING] Shutting down services..." -ForegroundColor Yellow
    foreach ($svc in $processes) {
        if (-not $svc.Process.HasExited) {
            Write-Host "      Stopping $($svc.Name)..." -ForegroundColor Gray -NoNewline
            $svc.Process.Kill()
            $svc.Process.WaitForExit(5000) | Out-Null
            Write-Host " OK" -ForegroundColor Green
        }
    }
    Write-Host "`nAll services stopped." -ForegroundColor Green
}
