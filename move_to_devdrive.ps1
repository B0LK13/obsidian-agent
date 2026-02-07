# Move all developer files to F:\DevDrive
# Run: powershell -ExecutionPolicy Bypass -File move_to_devdrive.ps1

Write-Host "=== Moving Developer Files to F:\DevDrive ===" -ForegroundColor Cyan

# Create destination
if (-not (Test-Path "F:\DevDrive")) {
    New-Item -ItemType Directory -Path "F:\DevDrive" -Force | Out-Null
    Write-Host "Created F:\DevDrive" -ForegroundColor Green
}

# Developer directories to move
$devDirs = @(
    # From Documents
    @{ Source = "C:\Users\Admin\Documents\B0LK13v2"; Dest = "F:\DevDrive\B0LK13v2" },
    @{ Source = "C:\Users\Admin\Documents\Cline"; Dest = "F:\DevDrive\Cline" },
    @{ Source = "C:\Users\Admin\Documents\zed-dev-extension"; Dest = "F:\DevDrive\zed-dev-extension" },
    
    # From User root
    @{ Source = "C:\Users\Admin\agent-zero-advanced"; Dest = "F:\DevDrive\agent-zero-advanced" },
    @{ Source = "C:\Users\Admin\BlackAgencyOS"; Dest = "F:\DevDrive\BlackAgencyOS" },
    @{ Source = "C:\Users\Admin\CascadeProjects"; Dest = "F:\DevDrive\CascadeProjects" },
    @{ Source = "C:\Users\Admin\Development"; Dest = "F:\DevDrive\Development" },
    @{ Source = "C:\Users\Admin\Projects"; Dest = "F:\DevDrive\Projects" }
)

$moved = @()
$failed = @()

foreach ($dir in $devDirs) {
    if (Test-Path $dir.Source) {
        Write-Host "`nMoving: $($dir.Source)" -ForegroundColor Yellow
        Write-Host "    -> $($dir.Dest)" -ForegroundColor Gray
        
        try {
            # Use robocopy for faster copying with progress
            $robocopyArgs = @($dir.Source, $dir.Dest, "/E", "/MT:8", "/R:1", "/W:1", "/NP", "/NFL", "/NDL")
            $result = Start-Process -FilePath "robocopy" -ArgumentList $robocopyArgs -Wait -PassThru -NoNewWindow
            
            if ($result.ExitCode -lt 8) {
                $moved += $dir.Dest
                Write-Host "    [OK]" -ForegroundColor Green
            } else {
                $failed += $dir.Source
                Write-Host "    [FAILED]" -ForegroundColor Red
            }
        } catch {
            # Fallback to Copy-Item
            Copy-Item -Path $dir.Source -Destination $dir.Dest -Recurse -Force -ErrorAction SilentlyContinue
            $moved += $dir.Dest
            Write-Host "    [OK]" -ForegroundColor Green
        }
    }
}

# Check E:\ for dev projects
if (Test-Path "E:\") {
    Write-Host "`n=== Scanning E:\ for dev projects ===" -ForegroundColor Cyan
    $eItems = Get-ChildItem -Path "E:\" -Directory -ErrorAction SilentlyContinue
    
    foreach ($item in $eItems) {
        $indicators = @("package.json", "pyproject.toml", ".git", "Cargo.toml", "go.mod", "pom.xml")
        $isDev = $false
        
        foreach ($indicator in $indicators) {
            if (Test-Path (Join-Path $item.FullName $indicator)) {
                $isDev = $true
                break
            }
        }
        
        if ($isDev) {
            $destPath = "F:\DevDrive\$($item.Name)"
            Write-Host "Found: $($item.FullName) -> $destPath" -ForegroundColor Yellow
            
            robocopy $item.FullName $destPath /E /MT:8 /R:1 /W:1 /NP /NFL /NDL | Out-Null
            $moved += $destPath
        }
    }
}

# Summary
Write-Host "`n" + "="*50 -ForegroundColor Cyan
Write-Host "=== SUMMARY ===" -ForegroundColor Cyan
Write-Host "="*50 -ForegroundColor Cyan

Write-Host "`nMoved to F:\DevDrive:" -ForegroundColor Green
foreach ($m in $moved) {
    Write-Host "  - $m" -ForegroundColor White
}

if ($failed.Count -gt 0) {
    Write-Host "`nFailed:" -ForegroundColor Red
    foreach ($f in $failed) {
        Write-Host "  - $f" -ForegroundColor Red
    }
}

# Next steps
Write-Host "`n=== NEXT STEPS ===" -ForegroundColor Yellow
Write-Host @"

1. Open new terminal in F:\DevDrive\B0LK13v2

2. Install PKM Agent:
   cd F:\DevDrive\B0LK13v2\apps\pkm-agent
   pip install -e .
   pkm-agent --help

3. Build Obsidian Plugin:
   cd F:\DevDrive\B0LK13v2\apps\obsidian-plugin
   npm install
   npm run build

4. Update your IDE workspace to F:\DevDrive\B0LK13v2

"@ -ForegroundColor White

Write-Host "Done!" -ForegroundColor Green
