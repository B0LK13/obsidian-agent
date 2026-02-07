@echo off
REM Comprehensive Test and POC Runner for Windows
REM Run this script to test all implementations and see the demo

echo ========================================
echo PKM-Agent Test and Demo Suite
echo ========================================
echo.

REM Check Python
echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    echo Please install Python 3.11+
    pause
    exit /b 1
)
python --version
echo.

REM Install dependencies
echo [2/5] Installing dependencies...
cd /d "%~dp0pkm-agent"
pip install -e ".[dev]"
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

REM Run comprehensive tests
echo [3/5] Running comprehensive test suite...
cd /d "%~dp0"
python test_comprehensive.py
if errorlevel 1 (
    echo WARNING: Some tests failed
    echo Check test_results.json for details
) else (
    echo SUCCESS: All tests passed!
)
echo.
pause

REM Run POC demo
echo [4/5] Running Proof of Concept demo...
echo This is an interactive demo - follow the prompts
echo.
python demo_poc.py
echo.

REM Build TypeScript plugin
echo [5/5] Building TypeScript plugin...
cd /d "%~dp0obsidian-pkm-agent"
if exist "node_modules" (
    echo Running npm build...
    call npm run build
    if errorlevel 1 (
        echo ERROR: Build failed
    ) else (
        echo SUCCESS: Plugin built successfully
        echo Output: main.js
    )
) else (
    echo WARNING: node_modules not found
    echo Run 'npm install' first to build the plugin
)
cd /d "%~dp0"
echo.

echo ========================================
echo Test and Demo Complete
echo ========================================
echo.
echo Check the following:
echo   - test_results.json (test results)
echo   - obsidian-pkm-agent/main.js (built plugin)
echo.
echo Next steps:
echo   1. Review test results
echo   2. Copy plugin to Obsidian vault
echo   3. Follow DEPLOYMENT_CHECKLIST.md
echo.
pause
