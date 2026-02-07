# Complete Developer Files Move Script
# Run: powershell -ExecutionPolicy Bypass -File move_all_dev_files.ps1

Write-Host "=== Complete Developer Files Migration to F:\DevDrive ===" -ForegroundColor Cyan
Write-Host ""

# Create destination
if (-not (Test-Path "F:\DevDrive")) {
    New-Item -ItemType Directory -Path "F:\DevDrive" -Force | Out-Null
    Write-Host "Created F:\DevDrive" -ForegroundColor Green
}

# ============================================
# MAIN PROJECT DIRECTORIES
# ============================================
$projectDirs = @(
    @{ Source = "C:\Users\Admin\Documents\B0LK13v2"; Dest = "F:\DevDrive\B0LK13v2"; Desc = "Main PKM Agent Project" },
    @{ Source = "C:\Users\Admin\Documents\Cline"; Dest = "F:\DevDrive\Cline"; Desc = "Cline AI" },
    @{ Source = "C:\Users\Admin\Documents\zed-dev-extension"; Dest = "F:\DevDrive\zed-dev-extension"; Desc = "Zed Extension" },
    @{ Source = "C:\Users\Admin\agent-zero-advanced"; Dest = "F:\DevDrive\agent-zero-advanced"; Desc = "Agent Zero" },
    @{ Source = "C:\Users\Admin\BlackAgencyOS"; Dest = "F:\DevDrive\BlackAgencyOS"; Desc = "Black Agency OS" },
    @{ Source = "C:\Users\Admin\CascadeProjects"; Dest = "F:\DevDrive\CascadeProjects"; Desc = "Cascade Projects" },
    @{ Source = "C:\Users\Admin\Development"; Dest = "F:\DevDrive\Development"; Desc = "Development" },
    @{ Source = "C:\Users\Admin\Projects"; Dest = "F:\DevDrive\Projects"; Desc = "Projects" }
)

# ============================================
# DEV TOOL DIRECTORIES (keep on C: but backup)
# ============================================
$devToolDirs = @(
    @{ Source = "C:\Users\Admin\scoop"; Dest = "F:\DevDrive\_backups\scoop"; Desc = "Scoop Package Manager" },
    @{ Source = "C:\Users\Admin\pipx"; Dest = "F:\DevDrive\_backups\pipx"; Desc = "Pipx Python Tools" },
    @{ Source = "C:\Users\Admin\.pkm-agent"; Dest = "F:\DevDrive\_backups\.pkm-agent"; Desc = "PKM Agent Data" },
    @{ Source = "C:\Users\Admin\.mcp"; Dest = "F:\DevDrive\_backups\.mcp"; Desc = "MCP Config" }
)

# ============================================
# CONFIG FILES TO BACKUP
# ============================================
$configFiles = @(
    @{ Source = "C:\Users\Admin\.gitconfig"; Dest = "F:\DevDrive\_backups\configs\.gitconfig" },
    @{ Source = "C:\Users\Admin\.npmrc"; Dest = "F:\DevDrive\_backups\configs\.npmrc" },
    @{ Source = "C:\Users\Admin\.mcp.json"; Dest = "F:\DevDrive\_backups\configs\.mcp.json" },
    @{ Source = "C:\Users\Admin\winsurf-mcp.json"; Dest = "F:\DevDrive\_backups\configs\winsurf-mcp.json" }
)

# ============================================
# POWERSHELL PROFILES
# ============================================
$psProfiles = @(
    @{ Source = "C:\Users\Admin\Documents\PowerShell"; Dest = "F:\DevDrive\_backups\PowerShell"; Desc = "PowerShell Profiles" },
    @{ Source = "C:\Users\Admin\Documents\WindowsPowerShell"; Dest = "F:\DevDrive\_backups\WindowsPowerShell"; Desc = "Windows PowerShell" }
)

# ============================================
# VSIX EXTENSIONS
# ============================================
$vsixDirs = @(
    @{ Source = "C:\Users\Admin\Desktop\VSIX Extensions"; Dest = "F:\DevDrive\_backups\VSIX-Extensions"; Desc = "VS Code Extensions" }
)

# ============================================
# ARCHIVES WITH DEV CONTENT
# ============================================
$archiveDirs = @(
    @{ Source = "C:\Users\Admin\archives"; Dest = "F:\DevDrive\_archives\user-archives"; Desc = "User Archives" },
    @{ Source = "C:\Users\Admin\Desktop\archives"; Dest = "F:\DevDrive\_archives\desktop-archives"; Desc = "Desktop Archives" }
)

# ============================================
# HELPER FUNCTION
# ============================================
function Move-DevItem {
    param($Source, $Dest, $Desc)
    
    if (Test-Path $Source) {
        Write-Host "  Moving: $Desc" -ForegroundColor Yellow
        Write-Host "    From: $Source" -ForegroundColor Gray
        Write-Host "    To:   $Dest" -ForegroundColor Gray
        
        $destParent = Split-Path $Dest -Parent
        if (-not (Test-Path $destParent)) {
            New-Item -ItemType Directory -Path $destParent -Force | Out-Null
        }
        
        try {
            if (Test-Path $Source -PathType Container) {
                robocopy $Source $Dest /E /MT:8 /R:1 /W:1 /NP /NFL /NDL /NJS /NJH 2>&1 | Out-Null
            } else {
                Copy-Item -Path $Source -Destination $Dest -Force
            }
            Write-Host "    [OK]" -ForegroundColor Green
            return $true
        } catch {
            Write-Host "    [FAILED] $_" -ForegroundColor Red
            return $false
        }
    }
    return $false
}

# ============================================
# EXECUTE MOVES
# ============================================
$moved = @()
$skipped = @()

Write-Host "`n=== MAIN PROJECT DIRECTORIES ===" -ForegroundColor Cyan
foreach ($item in $projectDirs) {
    if (Move-DevItem -Source $item.Source -Dest $item.Dest -Desc $item.Desc) {
        $moved += $item.Dest
    }
}

Write-Host "`n=== DEV TOOL BACKUPS ===" -ForegroundColor Cyan
foreach ($item in $devToolDirs) {
    if (Move-DevItem -Source $item.Source -Dest $item.Dest -Desc $item.Desc) {
        $moved += $item.Dest
    }
}

Write-Host "`n=== CONFIG FILES ===" -ForegroundColor Cyan
New-Item -ItemType Directory -Path "F:\DevDrive\_backups\configs" -Force | Out-Null
foreach ($item in $configFiles) {
    if (Test-Path $item.Source) {
        Copy-Item -Path $item.Source -Destination $item.Dest -Force
        Write-Host "  Copied: $(Split-Path $item.Source -Leaf)" -ForegroundColor Green
    }
}

Write-Host "`n=== POWERSHELL PROFILES ===" -ForegroundColor Cyan
foreach ($item in $psProfiles) {
    if (Move-DevItem -Source $item.Source -Dest $item.Dest -Desc $item.Desc) {
        $moved += $item.Dest
    }
}

Write-Host "`n=== VSIX EXTENSIONS ===" -ForegroundColor Cyan
foreach ($item in $vsixDirs) {
    if (Move-DevItem -Source $item.Source -Dest $item.Dest -Desc $item.Desc) {
        $moved += $item.Dest
    }
}

Write-Host "`n=== ARCHIVES ===" -ForegroundColor Cyan
foreach ($item in $archiveDirs) {
    if (Move-DevItem -Source $item.Source -Dest $item.Dest -Desc $item.Desc) {
        $moved += $item.Dest
    }
}

# ============================================
# SCAN E:\ DRIVE
# ============================================
Write-Host "`n=== SCANNING E:\ DRIVE ===" -ForegroundColor Cyan
if (Test-Path "E:\") {
    $eItems = Get-ChildItem -Path "E:\" -Directory -ErrorAction SilentlyContinue
    foreach ($item in $eItems) {
        $indicators = @("package.json", "pyproject.toml", ".git", "Cargo.toml", "go.mod", "pom.xml", "requirements.txt")
        $isDev = $false
        foreach ($indicator in $indicators) {
            if (Test-Path (Join-Path $item.FullName $indicator)) {
                $isDev = $true
                break
            }
        }
        if ($isDev) {
            $destPath = "F:\DevDrive\E-Drive\$($item.Name)"
            if (Move-DevItem -Source $item.FullName -Dest $destPath -Desc "E:\$($item.Name)") {
                $moved += $destPath
            }
        }
    }
} else {
    Write-Host "  E:\ drive not accessible" -ForegroundColor Gray
}

# ============================================
# SUMMARY
# ============================================
Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
Write-Host "=== MIGRATION COMPLETE ===" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Cyan

Write-Host "`nMoved $($moved.Count) items to F:\DevDrive" -ForegroundColor Green

Write-Host "`n=== FINAL STRUCTURE ===" -ForegroundColor Yellow
Get-ChildItem "F:\DevDrive" -Directory | ForEach-Object {
    Write-Host "  [DIR] $($_.Name)" -ForegroundColor White
}

Write-Host @"

=== NEXT STEPS ===

1. Set workspace to F:\DevDrive\B0LK13v2:
   cd F:\DevDrive\B0LK13v2

2. Install PKM Agent:
   cd apps\pkm-agent
   pip install -e .
   pkm-agent --help

3. Build Obsidian Plugin:
   cd apps\obsidian-plugin
   npm install
   npm run build

4. Update environment PATH if needed for scoop/pipx

"@ -ForegroundColor Cyan

Write-Host "Migration complete!" -ForegroundColor Green
