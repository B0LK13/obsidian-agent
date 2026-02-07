@echo off
echo ========================================
echo B0LK13v2 GitHub Issues Setup
echo ========================================
echo.

echo Checking for Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo Python found!
echo.
echo Running issue generator...
echo.

python create-github-issues.py

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Check the 'github-issues' folder for generated issue files
echo 2. Read README-SETUP.md for detailed instructions
echo 3. Create your GitHub repository and start adding issues
echo.
pause
