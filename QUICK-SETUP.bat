@echo off
REM ==================================================================
REM B0LK13v2 - Quick Start Setup
REM This script works with standard Windows Command Prompt
REM ==================================================================

echo.
echo ========================================
echo   B0LK13v2 PKM-Agent Setup
echo ========================================
echo.
echo Starting setup process...
echo.

REM Change to project directory
cd /d "%~dp0"

REM Step 1: Check Python
echo [1/10] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python not found!
    echo.
    echo Please install Python from:
    echo https://www.python.org/downloads/
    echo.
    echo Or use Windows Package Manager:
    echo   winget install Python.Python.3.12
    echo.
    pause
    exit /b 1
)
python --version
echo [OK] Python is installed
echo.

REM Step 2: Generate GitHub Issues
echo [2/10] Generating GitHub issue files...
python create-github-issues.py
if %errorlevel% neq 0 (
    echo [ERROR] Failed to generate issues
    pause
    exit /b 1
)
echo [OK] Issues generated
echo.

REM Step 3: Create virtual environment
echo [3/10] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
)
echo [OK] Virtual environment ready
echo.

REM Step 4: Activate and upgrade pip
echo [4/10] Activating environment and upgrading pip...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel --quiet
echo [OK] pip upgraded
echo.

REM Step 5: Install core packages
echo [5/10] Installing core ML packages...
echo This may take a few minutes...
pip install numpy pandas scikit-learn matplotlib seaborn --quiet
echo [OK] Core ML installed
echo.

REM Step 6: Install PyTorch
echo [6/10] Installing PyTorch (CPU version)...
echo This is the largest package and may take 5-10 minutes...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu --quiet
echo [OK] PyTorch installed
echo.

REM Step 7: Install transformers
echo [7/10] Installing transformers and embeddings...
pip install transformers sentence-transformers --quiet
echo [OK] Transformers installed
echo.

REM Step 8: Install vector databases
echo [8/10] Installing vector databases...
pip install chromadb faiss-cpu qdrant-client --quiet
echo [OK] Vector databases installed
echo.

REM Step 9: Install NLP and APIs
echo [9/10] Installing NLP tools and LLM APIs...
pip install spacy nltk gensim openai anthropic --quiet
echo [OK] NLP and APIs installed
echo.

REM Step 10: Install web and dev tools
echo [10/10] Installing web framework and dev tools...
pip install playwright beautifulsoup4 lxml requests --quiet
pip install fastapi uvicorn python-dotenv --quiet
pip install jupyter notebook black pylint pytest pytest-cov ipykernel --quiet
echo [OK] Dev tools installed
echo.

REM Install Playwright browsers
echo Installing Playwright browsers...
playwright install chromium --quiet
echo [OK] Playwright ready
echo.

REM Create project structure
echo Creating project structure...
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

REM Create __init__.py files
type nul > src\__init__.py
type nul > src\indexing\__init__.py
type nul > src\search\__init__.py
type nul > src\ml\__init__.py
type nul > src\api\__init__.py
type nul > src\ui\__init__.py
echo [OK] Project structure created
echo.

REM Save requirements
echo Saving requirements.txt...
pip freeze > requirements.txt
echo [OK] Requirements saved
echo.

REM Create .gitignore
echo Creating .gitignore...
(
echo # Python
echo __pycache__/
echo *.py[cod]
echo .Python
echo venv/
echo .env
echo *.log
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
echo *.zip
) > .gitignore
echo [OK] .gitignore created
echo.

REM Create .env.example
echo Creating .env.example...
(
echo # B0LK13v2 Configuration
echo.
echo # OpenAI
echo OPENAI_API_KEY=sk-your-key-here
echo OPENAI_MODEL=gpt-4
echo.
echo # Anthropic
echo ANTHROPIC_API_KEY=sk-ant-your-key-here
echo ANTHROPIC_MODEL=claude-3-sonnet-20240229
echo.
echo # Vector DB
echo VECTOR_DB=chromadb
echo VECTOR_DB_PATH=./data/vector_db
echo.
echo # App
echo DEBUG=True
echo LOG_LEVEL=INFO
) > .env.example
echo [OK] .env.example created
echo.

REM Create main.py
echo Creating src\main.py...
(
echo """B0LK13v2 PKM-Agent - Main Application"""
echo.
echo from fastapi import FastAPI
echo from fastapi.middleware.cors import CORSMiddleware
echo import uvicorn
echo.
echo app = FastAPI^(
echo     title="B0LK13v2 PKM-Agent",
echo     description="AI-powered Personal Knowledge Management",
echo     version="0.1.0"
echo ^)
echo.
echo app.add_middleware^(
echo     CORSMiddleware,
echo     allow_origins=["*"],
echo     allow_credentials=True,
echo     allow_methods=["*"],
echo     allow_headers=["*"],
echo ^)
echo.
echo @app.get^("/^"^)
echo async def root^(^):
echo     return {
echo         "status": "running",
echo         "service": "B0LK13v2 PKM-Agent",
echo         "version": "0.1.0"
echo     }
echo.
echo @app.get^("/health"^)
echo async def health^(^):
echo     return {"status": "healthy"}
echo.
echo @app.get^("/api/v1/tasks"^)
echo async def list_tasks^(^):
echo     return {"tasks": [], "total": 0}
echo.
echo if __name__ == "__main__":
echo     print^("🚀 Starting B0LK13v2 PKM-Agent..."^)
echo     print^("📖 Docs: http://localhost:8000/docs"^)
echo     uvicorn.run^(app, host="0.0.0.0", port=8000^)
) > src\main.py
echo [OK] main.py created
echo.

REM Final summary
echo.
echo ========================================
echo   SETUP COMPLETE!
echo ========================================
echo.
echo Created:
echo   [✓] Virtual environment (venv\)
echo   [✓] 40+ AI/ML packages installed
echo   [✓] Project structure (src, tests, etc.)
echo   [✓] 67 GitHub issues (github-issues\)
echo   [✓] Configuration files
echo.
echo Next steps:
echo.
echo 1. Create your .env file:
echo    copy .env.example .env
echo    notepad .env
echo    (Add your API keys)
echo.
echo 2. Test the installation:
echo    python src\main.py
echo    (Visit http://localhost:8000)
echo.
echo 3. Start Jupyter:
echo    jupyter notebook
echo.
echo 4. Begin Week 1 tasks:
echo    See PROJECT-TODO.md
echo.
echo Documentation:
echo   - SETUP-COMPLETE.md
echo   - PROJECT-TODO.md
echo   - DEV-GUIDE.md
echo.
echo Virtual environment is active!
echo To deactivate: deactivate
echo To reactivate: venv\Scripts\activate.bat
echo.
pause
