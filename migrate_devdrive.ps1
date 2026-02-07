# Complete DevDrive Migration Script
# Moves ALL dev tools including scoop, pipx, conda to F:\DevDrive

# Self-elevate if not admin
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Restarting as Administrator..." -ForegroundColor Yellow
    Start-Process powershell.exe "-ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

Write-Host @"
==============================================================
         COMPLETE DEVDRIVE MIGRATION SCRIPT
         Moving all dev files to F:\DevDrive
==============================================================
"@ -ForegroundColor Cyan

# ============================================
# STEP 1: CREATE DEVDRIVE STRUCTURE
# ============================================
Write-Host "`n[1/6] Creating DevDrive structure..." -ForegroundColor Yellow

$devDriveDirs = @(
    "F:\DevDrive",
    "F:\DevDrive\scoop",
    "F:\DevDrive\tools",
    "F:\DevDrive\projects",
    "F:\DevDrive\_backups"
)

foreach ($dir in $devDriveDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created: $dir" -ForegroundColor Green
    }
}

# ============================================
# STEP 2: MIGRATE SCOOP
# ============================================
Write-Host "`n[2/6] Migrating Scoop to F:\DevDrive\scoop..." -ForegroundColor Yellow

$oldScoop = "C:\Users\Admin\scoop"
$newScoop = "F:\DevDrive\scoop"

if (Test-Path $oldScoop) {
    Write-Host "  Copying scoop files (this may take a few minutes)..." -ForegroundColor Gray
    robocopy $oldScoop $newScoop /E /MT:8 /R:1 /W:1 /NP /NDL /NJS /NJH 2>&1 | Out-Null
    
    # Update environment variables
    Write-Host "  Updating SCOOP environment variable..." -ForegroundColor Gray
    [Environment]::SetEnvironmentVariable("SCOOP", $newScoop, "User")
    $env:SCOOP = $newScoop
    
    # Update PATH
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $newPath = $userPath -replace [regex]::Escape($oldScoop), $newScoop
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    
    Write-Host "  [OK] Scoop migrated" -ForegroundColor Green
}

# ============================================
# STEP 3: MIGRATE PIPX
# ============================================
Write-Host "`n[3/6] Migrating pipx..." -ForegroundColor Yellow

$oldPipx = "C:\Users\Admin\pipx"
$newPipx = "F:\DevDrive\tools\pipx"

if (Test-Path $oldPipx) {
    robocopy $oldPipx $newPipx /E /MT:8 /R:1 /W:1 /NP /NDL /NJS /NJH 2>&1 | Out-Null
    [Environment]::SetEnvironmentVariable("PIPX_HOME", $newPipx, "User")
    [Environment]::SetEnvironmentVariable("PIPX_BIN_DIR", "$newPipx\bin", "User")
    Write-Host "  [OK] Pipx migrated" -ForegroundColor Green
}

# ============================================
# STEP 4: MIGRATE PROJECT DIRECTORIES
# ============================================
Write-Host "`n[4/6] Migrating project directories..." -ForegroundColor Yellow

$projects = @(
    @{ From = "C:\Users\Admin\Documents\B0LK13v2"; To = "F:\DevDrive\projects\B0LK13v2" },
    @{ From = "C:\Users\Admin\Documents\Cline"; To = "F:\DevDrive\projects\Cline" },
    @{ From = "C:\Users\Admin\Documents\zed-dev-extension"; To = "F:\DevDrive\projects\zed-dev-extension" },
    @{ From = "C:\Users\Admin\agent-zero-advanced"; To = "F:\DevDrive\projects\agent-zero-advanced" },
    @{ From = "C:\Users\Admin\BlackAgencyOS"; To = "F:\DevDrive\projects\BlackAgencyOS" },
    @{ From = "C:\Users\Admin\CascadeProjects"; To = "F:\DevDrive\projects\CascadeProjects" },
    @{ From = "C:\Users\Admin\Development"; To = "F:\DevDrive\projects\Development" },
    @{ From = "C:\Users\Admin\Projects"; To = "F:\DevDrive\projects\Projects" }
)

foreach ($proj in $projects) {
    if (Test-Path $proj.From) {
        $name = Split-Path $proj.From -Leaf
        Write-Host "  Moving: $name" -ForegroundColor Gray
        robocopy $proj.From $proj.To /E /MT:8 /R:1 /W:1 /NP /NDL /NJS /NJH 2>&1 | Out-Null
        Write-Host "    [OK]" -ForegroundColor Green
    }
}

# ============================================
# STEP 5: MIGRATE DEV CONFIGS & DATA
# ============================================
Write-Host "`n[5/6] Migrating dev configs and data..." -ForegroundColor Yellow

$configs = @(
    @{ From = "C:\Users\Admin\.pkm-agent"; To = "F:\DevDrive\tools\.pkm-agent" },
    @{ From = "C:\Users\Admin\.mcp"; To = "F:\DevDrive\tools\.mcp" },
    @{ From = "C:\Users\Admin\.conda"; To = "F:\DevDrive\tools\.conda" },
    @{ From = "C:\Users\Admin\.bun"; To = "F:\DevDrive\tools\.bun" },
    @{ From = "C:\Users\Admin\Documents\PowerShell"; To = "F:\DevDrive\_backups\PowerShell" },
    @{ From = "C:\Users\Admin\Desktop\VSIX Extensions"; To = "F:\DevDrive\_backups\VSIX-Extensions" },
    @{ From = "C:\Users\Admin\archives"; To = "F:\DevDrive\_backups\archives" }
)

foreach ($cfg in $configs) {
    if (Test-Path $cfg.From) {
        $name = Split-Path $cfg.From -Leaf
        Write-Host "  Moving: $name" -ForegroundColor Gray
        robocopy $cfg.From $cfg.To /E /MT:8 /R:1 /W:1 /NP /NDL /NJS /NJH 2>&1 | Out-Null
        Write-Host "    [OK]" -ForegroundColor Green
    }
}

# Copy individual config files
$configFiles = @(".gitconfig", ".npmrc", ".mcp.json", "winsurf-mcp.json")
New-Item -ItemType Directory -Path "F:\DevDrive\_backups\configs" -Force | Out-Null
foreach ($file in $configFiles) {
    $src = "C:\Users\Admin\$file"
    if (Test-Path $src) {
        Copy-Item $src "F:\DevDrive\_backups\configs\" -Force
        Write-Host "  Copied: $file" -ForegroundColor Green
    }
}

# ============================================
# STEP 6: SCAN E:\ DRIVE
# ============================================
Write-Host "`n[6/6] Scanning E:\ for dev projects..." -ForegroundColor Yellow

if (Test-Path "E:\") {
    $eItems = Get-ChildItem -Path "E:\" -Directory -ErrorAction SilentlyContinue
    foreach ($item in $eItems) {
        $indicators = @("package.json", "pyproject.toml", ".git", "Cargo.toml", "go.mod")
        foreach ($ind in $indicators) {
            if (Test-Path (Join-Path $item.FullName $ind)) {
                Write-Host "  Found: $($item.Name)" -ForegroundColor Gray
                robocopy $item.FullName "F:\DevDrive\projects\$($item.Name)" /E /MT:8 /R:1 /W:1 /NP /NDL /NJS /NJH 2>&1 | Out-Null
                Write-Host "    [OK]" -ForegroundColor Green
                break
            }
        }
    }
} else {
    Write-Host "  E:\ not accessible" -ForegroundColor Gray
}

# ============================================
# UPDATE PATH FOR NEW SESSION
# ============================================
Write-Host "`n[FINAL] Updating PATH..." -ForegroundColor Yellow

$newPaths = @(
    "F:\DevDrive\scoop\shims",
    "F:\DevDrive\scoop\apps\python\current",
    "F:\DevDrive\scoop\apps\python\current\Scripts",
    "F:\DevDrive\scoop\apps\nodejs-lts\current",
    "F:\DevDrive\scoop\apps\go\current\bin",
    "F:\DevDrive\scoop\apps\rust\current\bin",
    "F:\DevDrive\tools\pipx\bin"
)

$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
foreach ($p in $newPaths) {
    if ($currentPath -notlike "*$p*") {
        $currentPath = "$p;$currentPath"
    }
}
[Environment]::SetEnvironmentVariable("Path", $currentPath, "User")

# ============================================
# SUMMARY
# ============================================
Write-Host @"

==============================================================
                    MIGRATION COMPLETE
==============================================================
"@ -ForegroundColor Green

Write-Host "`nF:\DevDrive structure:" -ForegroundColor Cyan
Get-ChildItem "F:\DevDrive" -Directory | ForEach-Object { Write-Host "  [DIR] $($_.Name)" }

Write-Host @"

IMPORTANT: Close this terminal and open a NEW PowerShell window
to use the updated PATH.

Then test with:
  python --version
  pip --version
  cd F:\DevDrive\projects\B0LK13v2\apps\pkm-agent
  pip install -e .
  pkm-agent --help

Press any key to exit...
"@ -ForegroundColor Yellow

$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
