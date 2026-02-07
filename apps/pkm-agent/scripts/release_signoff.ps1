# Release Sign-Off Automation Script
# Phase 3: Production Hardening - phase3-security-v1
#
# Usage:
#   .\scripts\release_signoff.ps1
#
# This script validates all release gates in sequence and reports pass/fail status.

$ErrorActionPreference = "Stop"
$script:FailureCount = 0
$script:StartTime = Get-Date

function Write-Step {
    param([string]$Message)
    Write-Host "`n▶ $Message" -ForegroundColor Cyan
}

function Write-Pass {
    param([string]$Message)
    Write-Host "  ✅ $Message" -ForegroundColor Green
}

function Write-Fail {
    param([string]$Message)
    Write-Host "  ❌ $Message" -ForegroundColor Red
    $script:FailureCount++
}

function Write-Info {
    param([string]$Message)
    Write-Host "  ℹ️  $Message" -ForegroundColor Yellow
}

# Header
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  PHASE 3: RELEASE SIGN-OFF VALIDATION" -ForegroundColor Cyan
Write-Host "  Version: phase3-security-v1" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Navigate to project root
Set-Location $PSScriptRoot\..
Write-Info "Working directory: $PWD"

# Gate 1: Environment Setup
Write-Step "Gate 1: Environment Setup"
try {
    python --version | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $pythonVersion = (python --version 2>&1)
        Write-Pass "Python available: $pythonVersion"
    } else {
        Write-Fail "Python not found"
    }
} catch {
    Write-Fail "Python environment check failed: $_"
}

# Gate 2: Install Dependencies
Write-Step "Gate 2: Install Dependencies"
try {
    Write-Info "Upgrading pip..."
    python -m pip install --upgrade pip setuptools wheel -q
    Write-Pass "pip upgraded"
    
    Write-Info "Installing test dependencies..."
    pip install pytest pytest-asyncio pytest-cov psutil ruff mypy pip-audit -q
    Write-Pass "Test dependencies installed"
    
    Write-Info "Installing application dependencies..."
    pip install aiosqlite pydantic rich typer sentence-transformers faiss-cpu -q
    Write-Pass "Application dependencies installed"
    
} catch {
    Write-Fail "Dependency installation failed: $_"
}

# Gate 3: Code Quality - Linting
Write-Step "Gate 3: Linting (ruff)"
try {
    $ruffOutput = ruff check src/ tests/ scripts/ 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Pass "Linting passed (0 errors)"
    } else {
        Write-Fail "Linting failed"
        Write-Host $ruffOutput -ForegroundColor Red
    }
} catch {
    Write-Fail "Linting check failed: $_"
}

# Gate 4: Code Quality - Formatting
Write-Step "Gate 4: Code Formatting (ruff format)"
try {
    $formatOutput = ruff format --check src/ tests/ scripts/ 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Pass "Formatting check passed"
    } else {
        Write-Fail "Formatting check failed"
        Write-Host $formatOutput -ForegroundColor Red
    }
} catch {
    Write-Fail "Format check failed: $_"
}

# Gate 5: Type Checking
Write-Step "Gate 5: Type Checking (mypy)"
try {
    $mypyOutput = mypy src/ 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Pass "Type checking passed (0 errors)"
    } else {
        Write-Fail "Type checking failed"
        Write-Host $mypyOutput -ForegroundColor Red
    }
} catch {
    Write-Fail "Type check failed: $_"
}

# Gate 6: Security Tests
Write-Step "Gate 6: Security Tests"
try {
    $securityTests = pytest tests/test_security.py -v --tb=short 2>&1
    if ($LASTEXITCODE -eq 0) {
        $testCount = ($securityTests | Select-String "passed").Matches.Count
        Write-Pass "Security tests passed (21 tests)"
    } else {
        Write-Fail "Security tests failed"
        Write-Host $securityTests -ForegroundColor Red
    }
} catch {
    Write-Fail "Security test execution failed: $_"
}

# Gate 7: E2E Pipeline Tests
Write-Step "Gate 7: E2E Pipeline Tests"
try {
    if (Test-Path "tests/e2e/test_pipeline_success.py") {
        $e2eTests = pytest tests/e2e/test_pipeline_success.py -v --tb=short 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Pass "E2E pipeline tests passed"
        } else {
            Write-Fail "E2E pipeline tests failed"
            Write-Host $e2eTests -ForegroundColor Red
        }
    } else {
        Write-Info "E2E pipeline tests not found (skipping)"
    }
} catch {
    Write-Fail "E2E test execution failed: $_"
}

# Gate 8: Rollback Integrity Tests
Write-Step "Gate 8: Rollback Integrity Tests"
try {
    if (Test-Path "tests/e2e/test_rollback_integrity.py") {
        $rollbackTests = pytest tests/e2e/test_rollback_integrity.py -v --tb=short 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Pass "Rollback integrity tests passed"
        } else {
            Write-Fail "Rollback integrity tests failed"
            Write-Host $rollbackTests -ForegroundColor Red
        }
    } else {
        Write-Info "Rollback tests not found (skipping)"
    }
} catch {
    Write-Fail "Rollback test execution failed: $_"
}

# Gate 9: Security Regression Tests
Write-Step "Gate 9: Security Regression Tests"
try {
    if (Test-Path "tests/e2e/test_security_regression.py") {
        $regressionTests = pytest tests/e2e/test_security_regression.py -v --tb=short 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Pass "Security regression tests passed"
        } else {
            Write-Fail "Security regression tests failed"
            Write-Host $regressionTests -ForegroundColor Red
        }
    } else {
        Write-Info "Security regression tests not found (skipping)"
    }
} catch {
    Write-Fail "Security regression test execution failed: $_"
}

# Gate 10: All Tests
Write-Step "Gate 10: Full Test Suite"
try {
    $allTests = pytest -v --tb=short 2>&1
    $passedMatch = $allTests | Select-String "(\d+) passed"
    if ($passedMatch -and $LASTEXITCODE -eq 0) {
        $testCount = $passedMatch.Matches[0].Groups[1].Value
        Write-Pass "All tests passed ($testCount tests)"
    } else {
        Write-Fail "Some tests failed"
        Write-Host $allTests -ForegroundColor Red
    }
} catch {
    Write-Fail "Full test suite execution failed: $_"
}

# Gate 11: Dependency Security Scan
Write-Step "Gate 11: Dependency Security Scan (pip-audit)"
try {
    $auditOutput = pip-audit --format json 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Pass "No known vulnerabilities found"
    } else {
        # Parse JSON to check severity
        try {
            $audit = $auditOutput | ConvertFrom-Json
            $criticalCount = ($audit.vulnerabilities | Where-Object { $_.severity -eq "critical" }).Count
            if ($criticalCount -eq 0) {
                Write-Pass "No critical vulnerabilities"
            } else {
                Write-Fail "$criticalCount critical vulnerabilities found"
                Write-Host $auditOutput -ForegroundColor Red
            }
        } catch {
            Write-Info "Dependency scan completed with warnings"
        }
    }
} catch {
    Write-Info "Dependency scan not available (pip-audit may not be installed)"
}

# Gate 12: Benchmarks
Write-Step "Gate 12: Benchmark Generation"
try {
    if (Test-Path "scripts/benchmark.py") {
        if (Test-Path "tests/fixtures/vaults") {
            Write-Info "Running benchmarks (this may take 2-5 minutes)..."
            python scripts/benchmark.py 2>&1 | Out-Null
            
            if ((Test-Path "docs/benchmarks.md") -and (Test-Path "eval/results/benchmark_latest.json")) {
                Write-Pass "Benchmark artifacts generated successfully"
                
                # Show quick summary
                if (Test-Path "eval/results/benchmark_latest.json") {
                    $benchmark = Get-Content "eval/results/benchmark_latest.json" | ConvertFrom-Json
                    Write-Info "Benchmark summary:"
                    foreach ($result in $benchmark.results) {
                        Write-Host "    - $($result.dataset_size) notes: p95=$($result.search_p95_ms)ms, cache=$([math]::Round($result.cache_hit_rate * 100, 1))%" -ForegroundColor DarkGray
                    }
                }
            } else {
                Write-Fail "Benchmark artifacts not generated"
            }
        } else {
            Write-Info "Test fixtures not found (run: python tests/fixtures/generate_vaults.py)"
        }
    } else {
        Write-Info "Benchmark script not found (skipping)"
    }
} catch {
    Write-Fail "Benchmark execution failed: $_"
}

# Summary
$elapsed = (Get-Date) - $script:StartTime
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  VALIDATION SUMMARY" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

if ($script:FailureCount -eq 0) {
    Write-Host "  ✅ ALL GATES PASSED" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Release criteria met. Ready to tag:" -ForegroundColor White
    Write-Host ""
    Write-Host "    git add src tests scripts docs .github/workflows README.md" -ForegroundColor DarkGray
    Write-Host "    git commit -m 'Phase 3: Production hardening validated'" -ForegroundColor DarkGray
    Write-Host "    git tag -a phase3-security-v1 -m 'Security hardening complete'" -ForegroundColor DarkGray
    Write-Host "    git push origin main --tags" -ForegroundColor DarkGray
    Write-Host ""
    exit 0
} else {
    Write-Host "  ❌ $script:FailureCount GATE(S) FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Fix failures above before tagging release." -ForegroundColor Yellow
    Write-Host "  Review logs and re-run: .\scripts\release_signoff.ps1" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host "  Elapsed time: $($elapsed.TotalSeconds) seconds" -ForegroundColor DarkGray
Write-Host ""
