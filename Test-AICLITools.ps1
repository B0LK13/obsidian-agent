# AI CLI Tools - Verification Test Script
# Run this in Obsidian Terminal to verify setup

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     AI CLI Tools - Verification Test                      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$testResults = @()

# Test 1: Module loaded
Write-Host "[Test 1] Checking if AICLITools module is loaded..." -ForegroundColor Yellow
$module = Get-Module AICLITools
if ($module) {
    Write-Host "  ✅ PASS: Module loaded" -ForegroundColor Green
    $testResults += $true
} else {
    Write-Host "  ❌ FAIL: Module not loaded" -ForegroundColor Red
    Write-Host "  Attempting to load..." -ForegroundColor Yellow
    Import-Module AICLITools -ErrorAction SilentlyContinue
    if (Get-Module AICLITools) {
        Write-Host "  ✅ Module loaded successfully" -ForegroundColor Green
        $testResults += $true
    } else {
        Write-Host "  ❌ Failed to load module" -ForegroundColor Red
        $testResults += $false
    }
}
Write-Host ""

# Test 2: Commands available
Write-Host "[Test 2] Checking if commands are available..." -ForegroundColor Yellow
$commands = @('opencode', 'codex', 'gemini', 'Open-Code', 'Invoke-Codex', 'Invoke-Gemini')
$allFound = $true
foreach ($cmd in $commands) {
    $cmdObj = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($cmdObj) {
        Write-Host "  ✅ $cmd - Available ($($cmdObj.CommandType))" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $cmd - Not found" -ForegroundColor Red
        $allFound = $false
    }
}
$testResults += $allFound
Write-Host ""

# Test 3: GitHub CLI
Write-Host "[Test 3] Checking GitHub CLI (gh)..." -ForegroundColor Yellow
$ghExists = Get-Command gh -ErrorAction SilentlyContinue
if ($ghExists) {
    $ghVersion = & gh --version 2>&1 | Select-Object -First 1
    Write-Host "  ✅ PASS: $ghVersion" -ForegroundColor Green
    $testResults += $true
} else {
    Write-Host "  ❌ FAIL: GitHub CLI not found" -ForegroundColor Red
    $testResults += $false
}
Write-Host ""

# Test 4: npm global commands
Write-Host "[Test 4] Checking npm global commands..." -ForegroundColor Yellow
$npmPath = "C:\Users\Admin\AppData\Roaming\npm"
if (Test-Path "$npmPath\codex.cmd") {
    Write-Host "  ✅ codex.cmd exists" -ForegroundColor Green
} else {
    Write-Host "  ❌ codex.cmd missing" -ForegroundColor Red
}
if (Test-Path "$npmPath\gemini.cmd") {
    Write-Host "  ✅ gemini.cmd exists" -ForegroundColor Green
} else {
    Write-Host "  ❌ gemini.cmd missing" -ForegroundColor Red
}
if (Test-Path "$npmPath\opencode.cmd") {
    Write-Host "  ✅ opencode.cmd exists" -ForegroundColor Green
    $testResults += $true
} else {
    Write-Host "  ❌ opencode.cmd missing" -ForegroundColor Red
    $testResults += $false
}
Write-Host ""

# Test 5: PATH configuration
Write-Host "[Test 5] Checking PATH configuration..." -ForegroundColor Yellow
$env:PATH -split ';' | Where-Object { $_ -like "*npm*" } | ForEach-Object {
    Write-Host "  ✅ Found in PATH: $_" -ForegroundColor Green
}
$testResults += $true
Write-Host ""

# Test 6: PowerShell Profile
Write-Host "[Test 6] Checking PowerShell Profile..." -ForegroundColor Yellow
if (Test-Path $PROFILE.CurrentUserAllHosts) {
    $profileContent = Get-Content $PROFILE.CurrentUserAllHosts -Raw
    if ($profileContent -like "*AICLITools*") {
        Write-Host "  ✅ PASS: Module auto-load configured in profile" -ForegroundColor Green
        $testResults += $true
    } else {
        Write-Host "  ⚠️  WARN: Module not in profile (manual load needed)" -ForegroundColor Yellow
        $testResults += $false
    }
} else {
    Write-Host "  ⚠️  WARN: Profile file not found" -ForegroundColor Yellow
    $testResults += $false
}
Write-Host ""

# Test 7: Obsidian Terminal Configuration
Write-Host "[Test 7] Checking Obsidian Terminal config..." -ForegroundColor Yellow
$terminalConfig = "C:\Users\Admin\Documents\B0LK13v2\B0LK13v2\.obsidian\plugins\terminal\data.json"
if (Test-Path $terminalConfig) {
    $config = Get-Content $terminalConfig -Raw | ConvertFrom-Json
    $executable = $config.profiles.win32IntegratedDefault.executable
    if ($executable -like "*powershell*") {
        Write-Host "  ✅ PASS: Terminal configured for PowerShell" -ForegroundColor Green
        Write-Host "  Executable: $executable" -ForegroundColor Gray
        $testResults += $true
    } else {
        Write-Host "  ⚠️  WARN: Terminal using $executable" -ForegroundColor Yellow
        $testResults += $false
    }
} else {
    Write-Host "  ❌ FAIL: Terminal config not found" -ForegroundColor Red
    $testResults += $false
}
Write-Host ""

# Test 8: Startup Script
Write-Host "[Test 8] Checking startup script..." -ForegroundColor Yellow
$startupScript = "$env:USERPROFILE\Documents\WindowsPowerShell\ObsidianTerminal.ps1"
if (Test-Path $startupScript) {
    Write-Host "  ✅ PASS: Startup script exists" -ForegroundColor Green
    Write-Host "  Location: $startupScript" -ForegroundColor Gray
    $testResults += $true
} else {
    Write-Host "  ❌ FAIL: Startup script not found" -ForegroundColor Red
    $testResults += $false
}
Write-Host ""

# Summary
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                    TEST SUMMARY                            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$passed = ($testResults | Where-Object { $_ -eq $true }).Count
$total = $testResults.Count
$percentage = [math]::Round(($passed / $total) * 100, 0)

Write-Host "Tests Passed: $passed / $total ($percentage%)" -ForegroundColor $(if ($percentage -ge 80) { "Green" } elseif ($percentage -ge 60) { "Yellow" } else { "Red" })
Write-Host ""

if ($percentage -eq 100) {
    Write-Host "🎉 All tests passed! AI CLI Tools are ready to use." -ForegroundColor Green
} elseif ($percentage -ge 80) {
    Write-Host "✅ Most tests passed. Minor issues detected." -ForegroundColor Yellow
} else {
    Write-Host "⚠️  Several tests failed. Review errors above." -ForegroundColor Red
}

Write-Host ""
Write-Host "To test actual commands, try:" -ForegroundColor Cyan
Write-Host '  opencode "test"' -ForegroundColor Gray
Write-Host "  codex --version" -ForegroundColor Gray
Write-Host "  gemini --version" -ForegroundColor Gray
Write-Host ""
