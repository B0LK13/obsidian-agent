@echo off
REM ============================================================
REM B0LK13v2 Master Setup Script
REM Complete system setup for AI/ML PKM-Agent development
REM ============================================================

echo.
echo ============================================================
echo    B0LK13v2 PKM-Agent - AI/ML Development Environment
echo ============================================================
echo.
echo This script will:
echo   1. Generate GitHub issues from your analysis
echo   2. Set up Python virtual environment
echo   3. Install AI/ML dependencies
echo   4. Create project structure
echo   5. Optimize system for development
echo.
echo Estimated time: 10-15 minutes
echo.
pause

REM Step 1: Run issue generator
echo.
echo [Step 1/3] Generating GitHub issues...
echo ------------------------------------------------------------
python create-github-issues.py
if %errorlevel% neq 0 (
    echo ERROR: Failed to generate issues
    echo Make sure Python is installed and in PATH
    pause
    exit /b 1
)
echo.
echo [OK] Issues generated in github-issues\ folder
echo.

REM Step 2: Set up AI/ML environment
echo.
echo [Step 2/3] Setting up AI/ML development environment...
echo ------------------------------------------------------------
call setup-ai-ml-env.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to set up environment
    pause
    exit /b 1
)
echo.
echo [OK] Development environment ready
echo.

REM Step 3: Run system optimization (PowerShell)
echo.
echo [Step 3/3] Running system diagnostics and optimization...
echo ------------------------------------------------------------
echo This may take a few moments...
echo.
powershell.exe -ExecutionPolicy Bypass -File optimize-system.ps1
echo.

REM Final summary
echo.
echo ============================================================
echo    SETUP COMPLETE!
echo ============================================================
echo.
echo Your B0LK13v2 PKM-Agent development environment is ready!
echo.
echo What was created:
echo   [✓] 67 GitHub issues in github-issues\ folder
echo   [✓] Python virtual environment in venv\
echo   [✓] Project structure (src\, tests\, notebooks\, etc.)
echo   [✓] AI/ML dependencies installed
echo   [✓] Configuration files (.env.example, requirements.txt)
echo   [✓] System optimizations applied
echo.
echo Next steps:
echo   1. Review github-issues\00-SUMMARY.md for issue overview
echo   2. Copy .env.example to .env and add your API keys
echo   3. Activate environment: venv\Scripts\activate.bat
echo   4. Start development: python src\main.py
echo   5. Open Jupyter: jupyter notebook
echo.
echo Documentation:
echo   - START-HERE.md       : Quick start guide
echo   - PROJECT-TODO.md     : All 67 tasks with details
echo   - DEV-GUIDE.md        : Development workflow
echo   - AI-ML-OPTIMIZATION.md : Performance optimization guide
echo   - INDEX.md            : Navigation hub
echo.
echo Happy coding! 🚀
echo.
pause
