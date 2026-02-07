@echo off
REM ================================================================================
REM   FOLLOW-UP ACTIONS EXECUTION SCRIPT
REM   Execute all immediate actions from FOLLOW_UP_ACTIONS.md
REM ================================================================================

echo.
echo ================================================================================
echo    PKM-Agent Follow-Up Actions - Immediate Execution
echo ================================================================================
echo.
echo This script will execute all Day 1 immediate actions:
echo   1. Environment verification
echo   2. Dependency installation
echo   3. Comprehensive testing
echo   4. POC demonstration
echo   5. TypeScript plugin build
echo.
echo Estimated total time: 60 minutes
echo.
pause

REM Set project paths
set "PROJECT_ROOT=C:\Users\Admin\Documents\B0LK13v2\B0LK13v2"
set "PKM_AGENT=%PROJECT_ROOT%\pkm-agent"
set "OBSIDIAN_PLUGIN=%PROJECT_ROOT%\obsidian-pkm-agent"

echo.
echo ================================================================================
echo    STEP 1: ENVIRONMENT VERIFICATION (5 minutes)
echo ================================================================================
echo.
echo Running verify_setup.py...
echo.

cd /d "%PROJECT_ROOT%"
if exist verify_setup.py (
    python verify_setup.py
    if errorlevel 1 (
        echo.
        echo [ERROR] Environment verification failed!
        echo Please review the output above and fix any issues.
        pause
        exit /b 1
    )
    echo.
    echo [SUCCESS] Environment verification complete!
) else (
    echo [WARNING] verify_setup.py not found!
    echo Skipping environment verification...
)

echo.
pause

echo.
echo ================================================================================
echo    STEP 2: INSTALL PYTHON DEPENDENCIES (10 minutes)
echo ================================================================================
echo.
echo Installing Python dependencies for pkm-agent...
echo.

cd /d "%PKM_AGENT%"
if exist pyproject.toml (
    echo Installing in editable mode with dev dependencies...
    pip install -e ".[dev]"
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install Python dependencies!
        echo.
        echo Trying without dev dependencies...
        pip install -e .
        if errorlevel 1 (
            echo.
            echo [ERROR] Installation failed completely!
            echo Please check your Python installation and try manually:
            echo   cd %PKM_AGENT%
            echo   pip install -e ".[dev]"
            pause
            exit /b 1
        )
    )
    echo.
    echo [SUCCESS] Python dependencies installed!
) else (
    echo [ERROR] pyproject.toml not found!
    echo Expected at: %PKM_AGENT%\pyproject.toml
    pause
    exit /b 1
)

echo.
pause

echo.
echo ================================================================================
echo    STEP 3: RUN COMPREHENSIVE TESTS (15 minutes)
echo ================================================================================
echo.
echo Running test_comprehensive.py...
echo This will generate test_results.json with detailed results.
echo.

cd /d "%PROJECT_ROOT%"
if exist test_comprehensive.py (
    python test_comprehensive.py
    if errorlevel 1 (
        echo.
        echo [WARNING] Some tests failed!
        echo Review the output above for details.
        echo.
        echo Continue anyway? (Press Ctrl+C to abort)
        pause
    ) else (
        echo.
        echo [SUCCESS] All tests passed!
    )
    
    REM Check if results file was created
    if exist test_results.json (
        echo.
        echo Test results saved to: test_results.json
        echo.
        echo Opening results file...
        type test_results.json
    )
) else (
    echo [WARNING] test_comprehensive.py not found!
    echo Skipping comprehensive tests...
)

echo.
pause

echo.
echo ================================================================================
echo    STEP 4: RUN INTERACTIVE POC DEMO (15 minutes)
echo ================================================================================
echo.
echo Running demo_poc.py...
echo This is an interactive demonstration - follow the prompts.
echo.
echo Press Enter to start the demo, or Ctrl+C to skip...
pause

cd /d "%PROJECT_ROOT%"
if exist demo_poc.py (
    python demo_poc.py
    echo.
    echo [SUCCESS] Demo complete!
) else (
    echo [WARNING] demo_poc.py not found!
    echo Skipping POC demo...
)

echo.
pause

echo.
echo ================================================================================
echo    STEP 5: BUILD TYPESCRIPT PLUGIN (15 minutes)
echo ================================================================================
echo.
echo Building Obsidian plugin...
echo.

cd /d "%OBSIDIAN_PLUGIN%"
if exist package.json (
    echo Installing npm dependencies...
    call npm install
    if errorlevel 1 (
        echo.
        echo [ERROR] npm install failed!
        echo Please check your Node.js installation.
        pause
        exit /b 1
    )
    
    echo.
    echo Building plugin...
    call npm run build
    if errorlevel 1 (
        echo.
        echo [ERROR] Build failed!
        echo Please check the output above for errors.
        pause
        exit /b 1
    )
    
    echo.
    echo [SUCCESS] Plugin built successfully!
    echo.
    echo Build output should be in: %OBSIDIAN_PLUGIN%\build
    
) else (
    echo [ERROR] package.json not found!
    echo Expected at: %OBSIDIAN_PLUGIN%\package.json
    pause
    exit /b 1
)

echo.
pause

echo.
echo ================================================================================
echo    STEP 6: VERIFY INSTALLATIONS
echo ================================================================================
echo.
echo Checking installed components...
echo.

echo Python version:
python --version

echo.
echo Node.js version:
node --version

echo.
echo npm version:
npm --version

echo.
echo Installed Python packages (pkm-agent):
cd /d "%PKM_AGENT%"
pip list | findstr "pkm-agent websockets rapidfuzz watchdog"

echo.
echo TypeScript build artifacts:
cd /d "%OBSIDIAN_PLUGIN%"
if exist build (
    echo [SUCCESS] Build directory exists
    dir /b build
) else (
    echo [WARNING] Build directory not found!
)

echo.
pause

echo.
echo ================================================================================
echo    EXECUTION COMPLETE!
echo ================================================================================
echo.
echo Summary of actions completed:
echo   [*] Environment verification
echo   [*] Python dependencies installed
echo   [*] Comprehensive tests run
echo   [*] POC demo executed
echo   [*] TypeScript plugin built
echo.
echo Next steps (from FOLLOW_UP_ACTIONS.md):
echo   1. Review DEPLOYMENT_CHECKLIST.md
echo   2. Create production vault backup
echo   3. Configure production settings
echo   4. Deploy backend to production
echo   5. Deploy plugin to Obsidian
echo.
echo For detailed next steps, see:
echo   %PROJECT_ROOT%\FOLLOW_UP_ACTIONS.md
echo   %PROJECT_ROOT%\SPRINT_PLANNING.md
echo.
echo ================================================================================
pause
