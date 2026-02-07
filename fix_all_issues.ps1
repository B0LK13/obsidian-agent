# Fix All Issues Script
# Fixes PATH, creates PKM Agent config

Write-Host "=== Fixing All Issues ===" -ForegroundColor Cyan

# ============================================
# 1. FIX PATH
# ============================================
Write-Host "`n[1/3] Fixing PATH..." -ForegroundColor Yellow

$pathsToAdd = @(
    "C:\Users\Admin\scoop\shims",
    "C:\Users\Admin\scoop\apps\python\current",
    "C:\Users\Admin\scoop\apps\python\current\Scripts",
    "F:\DevDrive\scoop\shims",
    "F:\DevDrive\scoop\apps\python\current",
    "F:\DevDrive\scoop\apps\python\current\Scripts"
)

# Add to current session
foreach ($p in $pathsToAdd) {
    if ((Test-Path $p) -and ($env:Path -notlike "*$p*")) {
        $env:Path = "$p;" + $env:Path
        Write-Host "  Added to session: $p" -ForegroundColor Green
    }
}

# Make permanent
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$changed = $false
foreach ($p in $pathsToAdd) {
    if ((Test-Path $p) -and ($userPath -notlike "*$p*")) {
        $userPath = "$p;$userPath"
        $changed = $true
    }
}
if ($changed) {
    [Environment]::SetEnvironmentVariable("Path", $userPath, "User")
    Write-Host "  PATH updated permanently" -ForegroundColor Green
}

# ============================================
# 2. CREATE PKM AGENT CONFIG
# ============================================
Write-Host "`n[2/3] Creating PKM Agent config..." -ForegroundColor Yellow

$configDir = "$env:USERPROFILE\.pkm-agent"
$configFile = "$configDir\config.toml"

if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

if (-not (Test-Path $configFile)) {
    $configContent = @"
# PKM Agent Configuration

[general]
pkm_root = "C:/Users/Admin/Documents/PKM"
db_path = "~/.pkm-agent/pkm.db"
cache_path = "~/.pkm-agent/cache"
chroma_path = "~/.pkm-agent/chroma"

[llm]
provider = "ollama"
model = "llama3.2"
base_url = "http://localhost:11434"
# api_key = ""  # Set for OpenAI

[rag]
embedding_model = "all-MiniLM-L6-v2"
chunk_size = 512
chunk_overlap = 50
top_k = 5

[sync]
host = "127.0.0.1"
port = 27125
"@
    Set-Content -Path $configFile -Value $configContent
    Write-Host "  Created: $configFile" -ForegroundColor Green
} else {
    Write-Host "  Config already exists: $configFile" -ForegroundColor Gray
}

# Create PKM root directory if needed
$pkmRoot = "$env:USERPROFILE\Documents\PKM"
if (-not (Test-Path $pkmRoot)) {
    New-Item -ItemType Directory -Path $pkmRoot -Force | Out-Null
    Write-Host "  Created PKM root: $pkmRoot" -ForegroundColor Green
}

# ============================================
# 3. VERIFY
# ============================================
Write-Host "`n[3/3] Verifying..." -ForegroundColor Yellow

Write-Host "`nPython:" -ForegroundColor Cyan
python --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Python not in PATH yet - restart terminal" -ForegroundColor Yellow
}

Write-Host "`nPKM Agent CLI:" -ForegroundColor Cyan
pkm-agent --help 2>$null
if ($LASTEXITCODE -ne 0) {
    & "C:\Users\Admin\scoop\apps\python\current\Scripts\pkm-agent.exe" --help
}

Write-Host "`n=== All Issues Fixed ===" -ForegroundColor Green
Write-Host "Restart your terminal for PATH changes to take effect." -ForegroundColor Yellow
