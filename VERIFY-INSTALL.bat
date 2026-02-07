@echo off
REM ==================================================================
REM B0LK13v2 - Installation Verification Script
REM Checks if everything is set up correctly
REM ==================================================================

echo.
echo ========================================
echo   B0LK13v2 Installation Verification
echo ========================================
echo.

cd /d "%~dp0"

set ERRORS=0

REM Check Python
echo [1/12] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] Python not found
    set /a ERRORS+=1
) else (
    python --version
    echo [PASS] Python installed
)
echo.

REM Check virtual environment
echo [2/12] Checking virtual environment...
if exist venv\Scripts\activate.bat (
    echo [PASS] Virtual environment exists
) else (
    echo [FAIL] Virtual environment not found
    set /a ERRORS+=1
)
echo.

REM Activate environment
call venv\Scripts\activate.bat 2>nul

REM Check pip
echo [3/12] Checking pip...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] pip not found
    set /a ERRORS+=1
) else (
    pip --version
    echo [PASS] pip installed
)
echo.

REM Check NumPy
echo [4/12] Checking NumPy...
python -c "import numpy; print('NumPy version:', numpy.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo [FAIL] NumPy not installed
    set /a ERRORS+=1
) else (
    echo [PASS] NumPy installed
)
echo.

REM Check PyTorch
echo [5/12] Checking PyTorch...
python -c "import torch; print('PyTorch version:', torch.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo [FAIL] PyTorch not installed
    set /a ERRORS+=1
) else (
    echo [PASS] PyTorch installed
)
echo.

REM Check Transformers
echo [6/12] Checking Transformers...
python -c "import transformers; print('Transformers version:', transformers.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo [FAIL] Transformers not installed
    set /a ERRORS+=1
) else (
    echo [PASS] Transformers installed
)
echo.

REM Check ChromaDB
echo [7/12] Checking ChromaDB...
python -c "import chromadb; print('ChromaDB installed')" 2>nul
if %errorlevel% neq 0 (
    echo [FAIL] ChromaDB not installed
    set /a ERRORS+=1
) else (
    echo [PASS] ChromaDB installed
)
echo.

REM Check FastAPI
echo [8/12] Checking FastAPI...
python -c "import fastapi; print('FastAPI version:', fastapi.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo [FAIL] FastAPI not installed
    set /a ERRORS+=1
) else (
    echo [PASS] FastAPI installed
)
echo.

REM Check OpenAI
echo [9/12] Checking OpenAI SDK...
python -c "import openai; print('OpenAI SDK installed')" 2>nul
if %errorlevel% neq 0 (
    echo [FAIL] OpenAI SDK not installed
    set /a ERRORS+=1
) else (
    echo [PASS] OpenAI SDK installed
)
echo.

REM Check project structure
echo [10/12] Checking project structure...
set MISSING=0
if not exist src\ (echo [MISS] src\ folder & set /a MISSING+=1)
if not exist tests\ (echo [MISS] tests\ folder & set /a MISSING+=1)
if not exist data\ (echo [MISS] data\ folder & set /a MISSING+=1)
if not exist notebooks\ (echo [MISS] notebooks\ folder & set /a MISSING+=1)
if %MISSING%==0 (
    echo [PASS] All project folders exist
) else (
    echo [FAIL] Missing %MISSING% folders
    set /a ERRORS+=1
)
echo.

REM Check main.py
echo [11/12] Checking src\main.py...
if exist src\main.py (
    echo [PASS] main.py exists
) else (
    echo [FAIL] main.py not found
    set /a ERRORS+=1
)
echo.

REM Check GitHub issues
echo [12/12] Checking GitHub issues...
if exist github-issues\ (
    dir /b github-issues\*.md 2>nul | find /c ".md" > temp.txt
    set /p COUNT=<temp.txt
    del temp.txt
    echo [PASS] GitHub issues folder exists
) else (
    echo [FAIL] GitHub issues not generated
    set /a ERRORS+=1
)
echo.

REM Summary
echo ========================================
echo   VERIFICATION SUMMARY
echo ========================================
echo.
if %ERRORS%==0 (
    echo [✓] ALL CHECKS PASSED!
    echo.
    echo Your environment is ready for development.
    echo.
    echo Next steps:
    echo   1. Copy .env.example to .env
    echo   2. Add your API keys to .env
    echo   3. Run: python src\main.py
    echo   4. Visit: http://localhost:8000
    echo.
) else (
    echo [✗] FOUND %ERRORS% ERROR(S)
    echo.
    echo Please run QUICK-SETUP.bat to fix issues.
    echo.
)

pause
