# Obsidian Agent - Windows Defender Exclusion Setup Script
# Addresses Issue #104: Windows Defender False Positive
# Run as Administrator

param(
    [Parameter(Mandatory=$false)]
    [string]$VaultPath
)

# Function to check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check administrator privileges
if (-not (Test-Administrator)) {
    Write-Host "ERROR: This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Obsidian Agent - Windows Defender Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# If no vault path provided, try to find it
if (-not $VaultPath) {
    Write-Host "Searching for Obsidian vaults..." -ForegroundColor Yellow
    
    $possiblePaths = @(
        "$env:USERPROFILE\Documents\Obsidian Vaults",
        "$env:USERPROFILE\OneDrive\Documents\Obsidian Vaults",
        "$env:USERPROFILE\Obsidian"
    )
    
    $foundVaults = @()
    foreach ($basePath in $possiblePaths) {
        if (Test-Path $basePath) {
            $vaults = Get-ChildItem -Path $basePath -Directory -ErrorAction SilentlyContinue
            foreach ($vault in $vaults) {
                $obsidianPath = Join-Path -Path $vault.FullName -ChildPath ".obsidian"
                if (Test-Path $obsidianPath) {
                    $foundVaults += $vault.FullName
                }
            }
        }
    }
    
    if ($foundVaults.Count -eq 0) {
        Write-Host "No Obsidian vaults found automatically." -ForegroundColor Yellow
        Write-Host "Please provide the vault path manually:" -ForegroundColor Yellow
        Write-Host 'Example: .\setup-defender-exclusions.ps1 -VaultPath "C:\Users\YourName\Documents\Obsidian Vaults\YourVault"' -ForegroundColor Gray
        exit 1
    }
    elseif ($foundVaults.Count -eq 1) {
        $VaultPath = $foundVaults[0]
        Write-Host "Found vault: $VaultPath" -ForegroundColor Green
    }
    else {
        Write-Host "Multiple vaults found:" -ForegroundColor Yellow
        for ($i = 0; $i -lt $foundVaults.Count; $i++) {
            Write-Host "  [$i] $($foundVaults[$i])"
        }
        $selection = Read-Host "Select vault number (0-$($foundVaults.Count - 1))"
        $VaultPath = $foundVaults[[int]$selection]
    }
}

# Validate vault path
if (-not (Test-Path $VaultPath)) {
    Write-Host "ERROR: Vault path does not exist: $VaultPath" -ForegroundColor Red
    exit 1
}

$obsidianPath = Join-Path -Path $VaultPath -ChildPath ".obsidian"
if (-not (Test-Path $obsidianPath)) {
    Write-Host "ERROR: Not a valid Obsidian vault (missing .obsidian folder): $VaultPath" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Setting up Windows Defender exclusions..." -ForegroundColor Green
Write-Host "Vault: $VaultPath" -ForegroundColor Gray
Write-Host ""

$successCount = 0
$failCount = 0

# Add Python process exclusion
Write-Host "[1/3] Adding python.exe to process exclusions..." -ForegroundColor Cyan
try {
    Add-MpPreference -ExclusionProcess "python.exe" -ErrorAction Stop
    Write-Host "      ✓ Successfully added python.exe exclusion" -ForegroundColor Green
    $successCount++
} catch {
    if ($_.Exception.Message -like "*already exists*") {
        Write-Host "      ⓘ python.exe already excluded" -ForegroundColor Gray
        $successCount++
    } else {
        Write-Host "      ✗ Failed: $_" -ForegroundColor Red
        $failCount++
    }
}

# Add plugins folder exclusion
$pluginsPath = Join-Path -Path $VaultPath -ChildPath ".obsidian\plugins"
Write-Host "[2/3] Adding plugins folder to path exclusions..." -ForegroundColor Cyan
Write-Host "      Path: $pluginsPath" -ForegroundColor Gray
try {
    Add-MpPreference -ExclusionPath $pluginsPath -ErrorAction Stop
    Write-Host "      ✓ Successfully added plugins folder exclusion" -ForegroundColor Green
    $successCount++
} catch {
    if ($_.Exception.Message -like "*already exists*") {
        Write-Host "      ⓘ Plugins folder already excluded" -ForegroundColor Gray
        $successCount++
    } else {
        Write-Host "      ✗ Failed: $_" -ForegroundColor Red
        $failCount++
    }
}

# Add specific plugin folder exclusion
$pluginPath = Join-Path -Path $pluginsPath -ChildPath "obsidian-agent"
if (Test-Path $pluginPath) {
    Write-Host "[3/3] Adding obsidian-agent plugin folder..." -ForegroundColor Cyan
    Write-Host "      Path: $pluginPath" -ForegroundColor Gray
    try {
        Add-MpPreference -ExclusionPath $pluginPath -ErrorAction Stop
        Write-Host "      ✓ Successfully added plugin folder exclusion" -ForegroundColor Green
        $successCount++
    } catch {
        if ($_.Exception.Message -like "*already exists*") {
            Write-Host "      ⓘ Plugin folder already excluded" -ForegroundColor Gray
            $successCount++
        } else {
            Write-Host "      ✗ Failed: $_" -ForegroundColor Red
            $failCount++
        }
    }
} else {
    Write-Host "[3/3] Skipping plugin-specific exclusion (plugin not yet installed)" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Successful: $successCount" -ForegroundColor Green
if ($failCount -gt 0) {
    Write-Host "Failed: $failCount" -ForegroundColor Red
}
Write-Host ""

# Verify exclusions
Write-Host "Current Windows Defender exclusions:" -ForegroundColor Cyan
Write-Host ""
Write-Host "Process Exclusions:" -ForegroundColor Gray
$processExclusions = (Get-MpPreference).ExclusionProcess
if ($processExclusions) {
    foreach ($proc in $processExclusions) {
        if ($proc -like "*python*") {
            Write-Host "  ✓ $proc" -ForegroundColor Green
        } else {
            Write-Host "  - $proc" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "  (none)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Path Exclusions:" -ForegroundColor Gray
$pathExclusions = (Get-MpPreference).ExclusionPath
if ($pathExclusions) {
    foreach ($path in $pathExclusions) {
        if ($path -like "*obsidian*" -or $path -like "*Obsidian*") {
            Write-Host "  ✓ $path" -ForegroundColor Green
        } else {
            Write-Host "  - $path" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "  (none)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Restart Obsidian for changes to take effect" -ForegroundColor Yellow
Write-Host "  2. Test the plugin functionality" -ForegroundColor Yellow
Write-Host "  3. If issues persist, check Windows Security → Virus & threat protection" -ForegroundColor Yellow
Write-Host ""
Write-Host "For more help, visit: https://github.com/B0LK13/obsidian-agent/issues/104" -ForegroundColor Gray
Write-Host ""

# Offer to open Windows Security
$openSecurity = Read-Host "Open Windows Security to review exclusions? (Y/N)"
if ($openSecurity -eq "Y" -or $openSecurity -eq "y") {
    Start-Process "windowsdefender://threatsettings"
}
