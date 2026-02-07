@echo off
REM ============================================================
REM B0LK13v2 - Quick Start After Setup
REM Run this after CONTINUE-SETUP.bat completes
REM ============================================================

echo.
echo ========================================
echo   B0LK13v2 - Quick Start
echo ========================================
echo.

cd /d "%~dp0"

REM Activate environment
call venv\Scripts\activate.bat

echo Step 1: Testing Python imports...
python -c "import numpy, torch, transformers, chromadb, fastapi; print('✓ All core packages working!')"
if %errorlevel% neq 0 (
    echo [ERROR] Package import failed
    pause
    exit /b 1
)
echo.

echo Step 2: Creating .env file...
if not exist .env (
    copy .env.example .env >nul
    echo [OK] .env created from template
    echo.
    echo ⚠️  ACTION REQUIRED: Add your API keys
    echo    Opening .env file now...
    timeout /t 2 >nul
    notepad .env
) else (
    echo [OK] .env already exists
)
echo.

echo Step 3: Testing API server...
echo Starting API server for 10 seconds...
echo Visit http://localhost:8000 in your browser
echo.
timeout /t 2 >nul
start http://localhost:8000
start http://localhost:8000/docs
echo.
echo Server starting...
echo Press Ctrl+C to stop when done testing
echo.
python src\main.py
