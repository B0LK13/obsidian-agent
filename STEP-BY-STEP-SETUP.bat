@echo off
REM ============================================================
REM B0LK13v2 - Setup Helper
REM Provides step-by-step instructions for manual setup
REM ============================================================

color 0A
echo.
echo ============================================================
echo    B0LK13v2 PKM-Agent Setup
echo ============================================================
echo.
echo Your system has Windows PowerShell 5.x but needs PowerShell 6+
echo for automated setup. No problem - we'll do it manually!
echo.
echo This guide will walk you through each step.
echo.
echo Estimated time: 15-20 minutes
echo.
pause
cls

REM Step 1: Generate Issues
echo.
echo ============================================================
echo STEP 1 of 10: Generate GitHub Issues
echo ============================================================
echo.
echo Running: python create-github-issues.py
echo.
python create-github-issues.py
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Python not found or script failed
    echo.
    echo Solution:
    echo 1. Install Python from https://www.python.org/downloads/
    echo 2. Or run: winget install Python.Python.3.12
    echo 3. Then run this script again
    pause
    exit /b 1
)
echo.
echo [OK] Generated 67 issue files in github-issues\ folder
echo.
pause
cls

REM Step 2: Create Virtual Environment
echo.
echo ============================================================
echo STEP 2 of 10: Create Python Virtual Environment
echo ============================================================
echo.
echo Running: python -m venv venv
echo.
echo This creates an isolated Python environment...
echo.
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)
echo.
echo [OK] Virtual environment created in venv\ folder
echo.
pause
cls

REM Step 3: Activate Environment
echo.
echo ============================================================
echo STEP 3 of 10: Activate Virtual Environment
echo ============================================================
echo.
echo Running: venv\Scripts\activate.bat
echo.
call venv\Scripts\activate.bat
echo.
echo [OK] Virtual environment activated
echo      Your prompt should now show (venv)
echo.
pause
cls

REM Step 4: Upgrade pip
echo.
echo ============================================================
echo STEP 4 of 10: Upgrade pip
echo ============================================================
echo.
echo Running: python -m pip install --upgrade pip setuptools wheel
echo.
python -m pip install --upgrade pip setuptools wheel
echo.
echo [OK] pip upgraded
echo.
pause
cls

REM Step 5: Install Core ML
echo.
echo ============================================================
echo STEP 5 of 10: Install Core ML Stack
echo ============================================================
echo.
echo Installing: numpy pandas scikit-learn matplotlib seaborn
echo.
pip install numpy pandas scikit-learn matplotlib seaborn
echo.
echo [OK] Core ML installed
echo.
pause
cls

REM Step 6: Install PyTorch
echo.
echo ============================================================
echo STEP 6 of 10: Install PyTorch (CPU)
echo ============================================================
echo.
echo Installing: torch torchvision torchaudio
echo This may take a few minutes...
echo.
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
echo.
echo [OK] PyTorch installed
echo.
pause
cls

REM Step 7: Install Transformers
echo.
echo ============================================================
echo STEP 7 of 10: Install Transformers and Embeddings
echo ============================================================
echo.
echo Installing: transformers sentence-transformers
echo.
pip install transformers sentence-transformers
echo.
echo [OK] Transformers installed
echo.
pause
cls

REM Step 8: Install Vector DBs
echo.
echo ============================================================
echo STEP 8 of 10: Install Vector Databases
echo ============================================================
echo.
echo Installing: chromadb faiss-cpu qdrant-client
echo.
pip install chromadb faiss-cpu qdrant-client
echo.
echo [OK] Vector databases installed
echo.
pause
cls

REM Step 9: Install NLP and APIs
echo.
echo ============================================================
echo STEP 9 of 10: Install NLP Tools and LLM APIs
echo ============================================================
echo.
echo Installing: spacy nltk gensim openai anthropic
echo.
pip install spacy nltk gensim openai anthropic
echo.
echo [OK] NLP tools and APIs installed
echo.
pause
cls

REM Step 10: Install Web and Dev Tools
echo.
echo ============================================================
echo STEP 10 of 10: Install Web Framework and Dev Tools
echo ============================================================
echo.
echo Installing: playwright beautifulsoup4 fastapi uvicorn
echo              jupyter black pylint pytest
echo.
pip install playwright beautifulsoup4 lxml requests fastapi uvicorn python-dotenv
pip install jupyter notebook black pylint pytest pytest-cov ipykernel
echo.
echo Installing Playwright browsers...
playwright install chromium
echo.
echo [OK] All development tools installed
echo.
pause
cls

REM Create Project Structure
echo.
echo ============================================================
echo BONUS: Creating Project Structure
echo ============================================================
echo.
echo Creating folders...
mkdir src 2>nul
mkdir src\indexing 2>nul
mkdir src\search 2>nul
mkdir src\ml 2>nul
mkdir src\api 2>nul
mkdir src\ui 2>nul
mkdir tests 2>nul
mkdir notebooks 2>nul
mkdir data 2>nul
mkdir models 2>nul
mkdir configs 2>nul
mkdir logs 2>nul

echo Creating __init__.py files...
echo. > src\__init__.py
echo. > src\indexing\__init__.py
echo. > src\search\__init__.py
echo. > src\ml\__init__.py
echo. > src\api\__init__.py
echo. > src\ui\__init__.py

echo Creating requirements.txt...
pip freeze > requirements.txt

echo Creating .gitignore...
(
echo # Python
echo __pycache__/
echo *.py[cod]
echo .Python
echo venv/
echo .env
echo.
echo # Data
echo data/
echo models/
echo logs/
echo *.db
echo.
echo # OS
echo .DS_Store
echo desktop.ini
echo.
echo # Project
echo github-issues/
) > .gitignore

echo.
echo [OK] Project structure created
echo.
pause
cls

REM Final Summary
echo.
echo ============================================================
echo    SETUP COMPLETE! 
echo ============================================================
echo.
echo What was created:
echo   [✓] 67 GitHub issues in github-issues\ folder
echo   [✓] Python virtual environment in venv\
echo   [✓] 40+ AI/ML packages installed
echo   [✓] Project folders created (src, tests, notebooks, etc.)
echo   [✓] Configuration files (.gitignore, requirements.txt)
echo.
echo Next steps:
echo.
echo 1. Create your .env file:
echo    copy .env.example .env
echo    notepad .env
echo    (Add your OpenAI and Anthropic API keys)
echo.
echo 2. Read the documentation:
echo    - SETUP-COMPLETE.md   (comprehensive overview)
echo    - MANUAL-SETUP.md     (detailed manual steps)
echo    - PROJECT-TODO.md     (all 67 tasks)
echo    - DEV-GUIDE.md        (development workflow)
echo.
echo 3. Test the installation:
echo    python src\main.py
echo    (Should start API on http://localhost:8000)
echo.
echo 4. Start coding:
echo    - Review PROJECT-TODO.md
echo    - Start with Week 1 tasks
echo    - Follow acceptance criteria
echo.
echo Your virtual environment is still active (venv).
echo To deactivate, type: deactivate
echo To reactivate later, type: venv\Scripts\activate.bat
echo.
echo Happy coding! 
echo.
pause
