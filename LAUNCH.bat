@echo off
color 0A
title B0LK13v2 PKM-Agent - Launch Center

:MENU
cls
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                                                                ║
echo ║              B0LK13v2 PKM-Agent - Launch Center                ║
echo ║                                                                ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo  What would you like to do?
echo.
echo  [1] 🚀 QUICK SETUP - Run complete setup (15-20 min)
echo  [2] ✅ VERIFY - Check installation status
echo  [3] 🔧 CONFIGURE - Edit .env file (API keys)
echo  [4] 💻 START API - Run the API server
echo  [5] 📊 JUPYTER - Open Jupyter Notebook
echo  [6] 🧪 RUN TESTS - Execute test suite
echo  [7] 📖 VIEW DOCS - Open documentation
echo  [8] 📋 ISSUES - Generate GitHub issues only
echo  [9] ℹ️  INFO - View project summary
echo  [0] ❌ EXIT
echo.
set /p choice="Enter your choice (0-9): "

if "%choice%"=="1" goto SETUP
if "%choice%"=="2" goto VERIFY
if "%choice%"=="3" goto CONFIGURE
if "%choice%"=="4" goto STARTAPI
if "%choice%"=="5" goto JUPYTER
if "%choice%"=="6" goto TESTS
if "%choice%"=="7" goto DOCS
if "%choice%"=="8" goto ISSUES
if "%choice%"=="9" goto INFO
if "%choice%"=="0" goto EXIT

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto MENU

:SETUP
cls
echo.
echo ========================================
echo   Running Complete Setup
echo ========================================
echo.
echo This will:
echo   - Generate 67 GitHub issues
echo   - Create virtual environment
echo   - Install 40+ AI/ML packages
echo   - Create project structure
echo.
echo Estimated time: 15-20 minutes
echo.
pause
call QUICK-SETUP.bat
pause
goto MENU

:VERIFY
cls
echo.
echo ========================================
echo   Verifying Installation
echo ========================================
echo.
call VERIFY-INSTALL.bat
pause
goto MENU

:CONFIGURE
cls
echo.
echo ========================================
echo   Configuring API Keys
echo ========================================
echo.
if not exist .env (
    echo Creating .env from template...
    copy .env.example .env >nul 2>&1
    echo .env file created.
    echo.
)
echo Opening .env file in Notepad...
echo.
echo Add your API keys:
echo   OPENAI_API_KEY=sk-your-key
echo   ANTHROPIC_API_KEY=sk-ant-your-key
echo.
pause
notepad .env
echo.
echo .env file updated!
echo.
pause
goto MENU

:STARTAPI
cls
echo.
echo ========================================
echo   Starting API Server
echo ========================================
echo.
if not exist venv\Scripts\activate.bat (
    echo ERROR: Virtual environment not found!
    echo Please run Setup (option 1) first.
    pause
    goto MENU
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting FastAPI server...
echo.
echo API will be available at:
echo   - http://localhost:8000
echo   - http://localhost:8000/docs (API documentation)
echo   - http://localhost:8000/health (Health check)
echo.
echo Press Ctrl+C to stop the server.
echo.
python src\main.py
pause
goto MENU

:JUPYTER
cls
echo.
echo ========================================
echo   Starting Jupyter Notebook
echo ========================================
echo.
if not exist venv\Scripts\activate.bat (
    echo ERROR: Virtual environment not found!
    echo Please run Setup (option 1) first.
    pause
    goto MENU
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting Jupyter Notebook...
echo.
echo Jupyter will open in your browser automatically.
echo Navigate to the notebooks\ folder to begin.
echo.
echo Press Ctrl+C to stop Jupyter.
echo.
jupyter notebook
pause
goto MENU

:TESTS
cls
echo.
echo ========================================
echo   Running Test Suite
echo ========================================
echo.
if not exist venv\Scripts\activate.bat (
    echo ERROR: Virtual environment not found!
    echo Please run Setup (option 1) first.
    pause
    goto MENU
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Running pytest...
echo.
pytest tests/ -v --cov=src
echo.
pause
goto MENU

:DOCS
cls
echo.
echo ========================================
echo   Documentation
echo ========================================
echo.
echo Available documentation:
echo.
echo  1. EXECUTE-NOW.md       - Quick execution guide
echo  2. SETUP-COMPLETE.md    - Comprehensive overview
echo  3. PROJECT-TODO.md      - All 67 tasks
echo  4. DEV-GUIDE.md         - Development workflow
echo  5. AI-ML-OPTIMIZATION.md - Performance tips
echo  6. MANUAL-SETUP.md      - Manual setup steps
echo  7. INDEX.md             - Navigation hub
echo  8. PROJECT-SUMMARY.txt  - Visual summary
echo.
set /p doc="Enter number (1-8) or 0 to return: "

if "%doc%"=="1" notepad EXECUTE-NOW.md
if "%doc%"=="2" notepad SETUP-COMPLETE.md
if "%doc%"=="3" notepad PROJECT-TODO.md
if "%doc%"=="4" notepad DEV-GUIDE.md
if "%doc%"=="5" notepad AI-ML-OPTIMIZATION.md
if "%doc%"=="6" notepad MANUAL-SETUP.md
if "%doc%"=="7" notepad INDEX.md
if "%doc%"=="8" notepad PROJECT-SUMMARY.txt
if "%doc%"=="0" goto MENU

goto DOCS

:ISSUES
cls
echo.
echo ========================================
echo   Generating GitHub Issues
echo ========================================
echo.
echo Running issue generator...
python create-github-issues.py
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to generate issues.
    echo Make sure Python is installed.
) else (
    echo.
    echo Success! 67 issue files created in github-issues\ folder
)
echo.
pause
goto MENU

:INFO
cls
echo.
type PROJECT-SUMMARY.txt
echo.
echo.
echo Press any key to return to menu...
pause >nul
goto MENU

:EXIT
cls
echo.
echo ========================================
echo   Thank you for using B0LK13v2!
echo ========================================
echo.
echo Next time, run this launcher again to access all tools.
echo.
echo Documentation: EXECUTE-NOW.md
echo Quick setup: QUICK-SETUP.bat
echo.
echo Happy coding! 🚀
echo.
timeout /t 3
exit
