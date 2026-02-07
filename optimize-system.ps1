# System Optimization for AI/ML Development
# Comprehensive diagnostic and optimization script

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "AI/ML Development System Optimization & Diagnostics" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if running as Administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

$isAdmin = Test-Administrator
if (-not $isAdmin) {
    Write-Host "WARNING: Not running as Administrator" -ForegroundColor Yellow
    Write-Host "Some optimizations require admin privileges" -ForegroundColor Yellow
    Write-Host ""
}

# =============================================================================
# SECTION 1: System Diagnostics
# =============================================================================

Write-Host "[1] SYSTEM DIAGNOSTICS" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Gray

# CPU Information
Write-Host "`n CPU Information:" -ForegroundColor Cyan
Get-WmiObject -Class Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed | Format-List

# Memory Information
Write-Host "Memory Information:" -ForegroundColor Cyan
$memory = Get-WmiObject -Class Win32_ComputerSystem
$totalRAM = [math]::Round($memory.TotalPhysicalMemory / 1GB, 2)
$freeRAM = [math]::Round((Get-WmiObject -Class Win32_OperatingSystem).FreePhysicalMemory / 1MB, 2)
Write-Host "Total RAM: $totalRAM GB"
Write-Host "Free RAM: $freeRAM GB"

# GPU Information
Write-Host "`nGPU Information:" -ForegroundColor Cyan
$gpu = Get-WmiObject -Class Win32_VideoController
$gpu | Select-Object Name, AdapterRAM, DriverVersion | Format-List

# Disk Space
Write-Host "Disk Space:" -ForegroundColor Cyan
Get-WmiObject -Class Win32_LogicalDisk -Filter "DriveType=3" | 
    Select-Object DeviceID, 
        @{Name="Size(GB)";Expression={[math]::Round($_.Size / 1GB, 2)}},
        @{Name="FreeSpace(GB)";Expression={[math]::Round($_.FreeSpace / 1GB, 2)}},
        @{Name="Used(%)";Expression={[math]::Round((($_.Size - $_.FreeSpace) / $_.Size) * 100, 2)}} |
    Format-Table

# =============================================================================
# SECTION 2: Python Environment Check
# =============================================================================

Write-Host "`n[2] PYTHON ENVIRONMENT CHECK" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Gray

# Check Python installations
Write-Host "`nSearching for Python installations..." -ForegroundColor Cyan

$pythonPaths = @()
$pathDirs = $env:PATH -split ';'
foreach ($dir in $pathDirs) {
    $pythonExe = Join-Path $dir "python.exe"
    if (Test-Path $pythonExe) {
        try {
            $version = & $pythonExe --version 2>&1
            $pythonPaths += @{Path=$pythonExe; Version=$version}
        } catch {}
    }
}

if ($pythonPaths.Count -gt 0) {
    Write-Host "Found $($pythonPaths.Count) Python installation(s):" -ForegroundColor Green
    $pythonPaths | ForEach-Object {
        Write-Host "  $($_.Version) at $($_.Path)" -ForegroundColor Gray
    }
} else {
    Write-Host "No Python installations found in PATH" -ForegroundColor Red
    Write-Host "Install Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
}

# Check pip
Write-Host "`nChecking pip..." -ForegroundColor Cyan
try {
    $pipVersion = python -m pip --version 2>&1
    Write-Host "pip: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "pip not found" -ForegroundColor Red
}

# =============================================================================
# SECTION 3: AI/ML Dependencies Check
# =============================================================================

Write-Host "`n[3] AI/ML DEPENDENCIES CHECK" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Gray

$requiredPackages = @(
    "numpy",
    "pandas",
    "scikit-learn",
    "torch",
    "transformers",
    "sentence-transformers",
    "chromadb",
    "faiss-cpu",
    "openai",
    "anthropic"
)

Write-Host "`nChecking installed AI/ML packages..." -ForegroundColor Cyan
$installedPackages = @()
$missingPackages = @()

foreach ($package in $requiredPackages) {
    try {
        $check = python -c "import $package; print($package.__version__)" 2>&1
        if ($LASTEXITCODE -eq 0) {
            $installedPackages += $package
            Write-Host "  [OK] $package" -ForegroundColor Green
        } else {
            $missingPackages += $package
            Write-Host "  [MISSING] $package" -ForegroundColor Red
        }
    } catch {
        $missingPackages += $package
        Write-Host "  [MISSING] $package" -ForegroundColor Red
    }
}

Write-Host "`nSummary: $($installedPackages.Count)/$($requiredPackages.Count) packages installed" -ForegroundColor Cyan

if ($missingPackages.Count -gt 0) {
    Write-Host "`nTo install missing packages, run:" -ForegroundColor Yellow
    Write-Host "  .\setup-ai-ml-env.bat" -ForegroundColor White
}

# =============================================================================
# SECTION 4: CUDA/GPU Support Check
# =============================================================================

Write-Host "`n[4] GPU ACCELERATION CHECK" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Gray

Write-Host "`nChecking for NVIDIA GPU and CUDA..." -ForegroundColor Cyan

$nvidiaSMI = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($nvidiaSMI) {
    Write-Host "NVIDIA GPU detected!" -ForegroundColor Green
    try {
        nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
        Write-Host "`nCUDA is available. Consider installing PyTorch with CUDA support:" -ForegroundColor Yellow
        Write-Host "  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118" -ForegroundColor White
    } catch {
        Write-Host "nvidia-smi failed to execute" -ForegroundColor Red
    }
} else {
    Write-Host "No NVIDIA GPU detected or CUDA not installed" -ForegroundColor Yellow
    Write-Host "Using CPU for ML computations (slower but functional)" -ForegroundColor Gray
}

# =============================================================================
# SECTION 5: Development Tools Check
# =============================================================================

Write-Host "`n[5] DEVELOPMENT TOOLS CHECK" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Gray

$devTools = @{
    "Git" = "git --version"
    "Node.js" = "node --version"
    "npm" = "npm --version"
    "Docker" = "docker --version"
    "GitHub CLI" = "gh --version"
    "VS Code" = "code --version"
}

Write-Host "`nChecking development tools..." -ForegroundColor Cyan
foreach ($tool in $devTools.GetEnumerator()) {
    try {
        $result = Invoke-Expression $tool.Value 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] $($tool.Key)" -ForegroundColor Green
        } else {
            Write-Host "  [NOT FOUND] $($tool.Key)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  [NOT FOUND] $($tool.Key)" -ForegroundColor Yellow
    }
}

# =============================================================================
# SECTION 6: Performance Optimizations
# =============================================================================

Write-Host "`n[6] PERFORMANCE OPTIMIZATIONS" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Gray

Write-Host "`nApplying performance optimizations..." -ForegroundColor Cyan

# Set NumPy to use multiple threads
Write-Host "`nSetting environment variables for optimal performance..." -ForegroundColor Cyan
[System.Environment]::SetEnvironmentVariable("OMP_NUM_THREADS", "4", "User")
[System.Environment]::SetEnvironmentVariable("MKL_NUM_THREADS", "4", "User")
[System.Environment]::SetEnvironmentVariable("NUMEXPR_NUM_THREADS", "4", "User")
Write-Host "  Set OMP_NUM_THREADS, MKL_NUM_THREADS, NUMEXPR_NUM_THREADS to 4" -ForegroundColor Green

# Increase Python's buffer size
[System.Environment]::SetEnvironmentVariable("PYTHONUNBUFFERED", "1", "User")
Write-Host "  Set PYTHONUNBUFFERED=1" -ForegroundColor Green

# Set PyTorch to use optimal threads
[System.Environment]::SetEnvironmentVariable("TORCH_NUM_THREADS", "4", "User")
Write-Host "  Set TORCH_NUM_THREADS=4" -ForegroundColor Green

Write-Host "`nEnvironment variables set for current user" -ForegroundColor Green
Write-Host "Restart your terminal for changes to take effect" -ForegroundColor Yellow

# =============================================================================
# SECTION 7: Disk Optimization
# =============================================================================

Write-Host "`n[7] DISK OPTIMIZATION" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Gray

if ($isAdmin) {
    Write-Host "`nOptimizing disk performance..." -ForegroundColor Cyan
    
    # Enable TRIM for SSD
    try {
        $trimStatus = fsutil behavior query DisableDeleteNotify
        Write-Host "TRIM Status: $trimStatus" -ForegroundColor Gray
    } catch {
        Write-Host "Could not check TRIM status" -ForegroundColor Yellow
    }
    
    Write-Host "  To optimize further, consider:" -ForegroundColor Cyan
    Write-Host "    - Disabling hibernation: powercfg /h off" -ForegroundColor Gray
    Write-Host "    - Disabling pagefile (if you have 16GB+ RAM)" -ForegroundColor Gray
    Write-Host "    - Using SSD for project files" -ForegroundColor Gray
} else {
    Write-Host "Run as Administrator to apply disk optimizations" -ForegroundColor Yellow
}

# =============================================================================
# SECTION 8: Memory Optimization
# =============================================================================

Write-Host "`n[8] MEMORY OPTIMIZATION" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Gray

Write-Host "`nMemory optimization recommendations:" -ForegroundColor Cyan

if ($totalRAM -lt 8) {
    Write-Host "  [WARNING] Low RAM ($totalRAM GB)" -ForegroundColor Red
    Write-Host "    - Recommended: 16GB+ for AI/ML development" -ForegroundColor Yellow
    Write-Host "    - Use smaller models and batch sizes" -ForegroundColor Yellow
} elseif ($totalRAM -lt 16) {
    Write-Host "  [INFO] Moderate RAM ($totalRAM GB)" -ForegroundColor Yellow
    Write-Host "    - Sufficient for most tasks" -ForegroundColor Gray
    Write-Host "    - Consider upgrading to 16GB+ for better performance" -ForegroundColor Gray
} else {
    Write-Host "  [OK] Excellent RAM ($totalRAM GB)" -ForegroundColor Green
    Write-Host "    - Sufficient for AI/ML development" -ForegroundColor Gray
}

# =============================================================================
# SECTION 9: Network Optimization
# =============================================================================

Write-Host "`n[9] NETWORK OPTIMIZATION" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Gray

Write-Host "`nTesting network connectivity..." -ForegroundColor Cyan

$testSites = @{
    "GitHub" = "github.com"
    "PyPI" = "pypi.org"
    "OpenAI" = "api.openai.com"
    "Anthropic" = "api.anthropic.com"
}

foreach ($site in $testSites.GetEnumerator()) {
    try {
        $ping = Test-Connection -ComputerName $site.Value -Count 1 -Quiet
        if ($ping) {
            Write-Host "  [OK] $($site.Key) ($($site.Value))" -ForegroundColor Green
        } else {
            Write-Host "  [FAIL] $($site.Key) ($($site.Value))" -ForegroundColor Red
        }
    } catch {
        Write-Host "  [ERROR] $($site.Key) ($($site.Value))" -ForegroundColor Red
    }
}

# =============================================================================
# SECTION 10: Security & Configuration
# =============================================================================

Write-Host "`n[10] SECURITY & CONFIGURATION" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Gray

Write-Host "`nSecurity recommendations:" -ForegroundColor Cyan
Write-Host "  1. Never commit API keys to Git" -ForegroundColor Yellow
Write-Host "  2. Use .env file for secrets (already in .gitignore)" -ForegroundColor Gray
Write-Host "  3. Enable 2FA on GitHub account" -ForegroundColor Gray
Write-Host "  4. Use virtual environments for isolation" -ForegroundColor Gray
Write-Host "  5. Regularly update dependencies: pip install --upgrade -r requirements.txt" -ForegroundColor Gray

# Check .env file
if (Test-Path .env) {
    Write-Host "`n  [OK] .env file exists" -ForegroundColor Green
} else {
    if (Test-Path .env.example) {
        Write-Host "`n  [ACTION NEEDED] Copy .env.example to .env and configure" -ForegroundColor Yellow
    }
}

# =============================================================================
# FINAL SUMMARY
# =============================================================================

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "OPTIMIZATION SUMMARY" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host "`nSystem Status:" -ForegroundColor Green
Write-Host "  CPU Cores: $($env:NUMBER_OF_PROCESSORS)" -ForegroundColor Gray
Write-Host "  Total RAM: $totalRAM GB" -ForegroundColor Gray
Write-Host "  Free RAM: $freeRAM GB" -ForegroundColor Gray
Write-Host "  Python: $(if ($pythonPaths.Count -gt 0) { 'Installed' } else { 'Not Found' })" -ForegroundColor $(if ($pythonPaths.Count -gt 0) { 'Green' } else { 'Red' })
Write-Host "  AI/ML Packages: $($installedPackages.Count)/$($requiredPackages.Count)" -ForegroundColor $(if ($installedPackages.Count -eq $requiredPackages.Count) { 'Green' } else { 'Yellow' })

Write-Host "`nNext Steps:" -ForegroundColor Green
if ($missingPackages.Count -gt 0) {
    Write-Host "  1. Run: .\setup-ai-ml-env.bat" -ForegroundColor Yellow
} else {
    Write-Host "  1. [OK] All dependencies installed" -ForegroundColor Green
}
Write-Host "  2. Copy .env.example to .env and configure API keys" -ForegroundColor White
Write-Host "  3. Activate virtual environment: venv\Scripts\activate.bat" -ForegroundColor White
Write-Host "  4. Start development: python src\main.py" -ForegroundColor White
Write-Host "  5. Review PROJECT-TODO.md for tasks" -ForegroundColor White

Write-Host "`nOptimization complete!" -ForegroundColor Green
Write-Host ""
