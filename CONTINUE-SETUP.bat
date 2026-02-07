@echo off
REM ============================================================
REM B0LK13v2 - Fixed Setup (Without Gensim)
REM Installs all packages except gensim which needs C++ tools
REM ============================================================

echo.
echo ========================================
echo   B0LK13v2 - Continuing Setup
echo ========================================
echo.
echo Skipping gensim (requires C++ build tools)
echo Installing all other packages...
echo.

cd /d "%~dp0"

REM Activate environment
call venv\Scripts\activate.bat

REM Core ML packages
echo [1/9] Installing core ML packages...
pip install numpy pandas scikit-learn matplotlib seaborn --quiet
echo [OK] Core ML installed
echo.

REM PyTorch (CPU version)
echo [2/9] Installing PyTorch (CPU)...
echo This may take 5-10 minutes...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu --quiet
echo [OK] PyTorch installed
echo.

REM Transformers
echo [3/9] Installing transformers...
pip install transformers sentence-transformers --quiet
echo [OK] Transformers installed
echo.

REM Vector databases
echo [4/9] Installing vector databases...
pip install chromadb faiss-cpu qdrant-client --quiet
echo [OK] Vector databases installed
echo.

REM NLP tools (without gensim)
echo [5/9] Installing NLP tools...
pip install spacy nltk --quiet
echo [OK] NLP tools installed (gensim skipped)
echo.

REM LLM APIs
echo [6/9] Installing LLM APIs...
pip install openai anthropic --quiet
echo [OK] LLM APIs installed
echo.

REM Web tools
echo [7/9] Installing web tools...
pip install playwright beautifulsoup4 lxml requests --quiet
echo [OK] Web tools installed
echo.

REM FastAPI and server
echo [8/9] Installing FastAPI and server...
pip install fastapi uvicorn python-dotenv --quiet
echo [OK] FastAPI installed
echo.

REM Dev tools
echo [9/9] Installing development tools...
pip install jupyter notebook black pylint pytest pytest-cov ipykernel --quiet
echo [OK] Dev tools installed
echo.

REM Playwright browsers
echo Installing Playwright browsers...
playwright install chromium
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
echo         "version": "0.1.0",
echo         "endpoints": {
echo             "docs": "/docs",
echo             "health": "/health",
echo             "tasks": "/api/v1/tasks"
echo         }
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
echo     print^("📖 API Docs: http://localhost:8000/docs"^)
echo     print^("🔍 Health Check: http://localhost:8000/health"^)
echo     uvicorn.run^(app, host="0.0.0.0", port=8000^)
) > src\main.py
echo [OK] main.py created
echo.

REM Create .env.example
echo Creating .env.example...
(
echo # B0LK13v2 Configuration
echo.
echo # OpenAI API
echo OPENAI_API_KEY=sk-your-openai-key-here
echo OPENAI_MODEL=gpt-4
echo.
echo # Anthropic API
echo ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
echo ANTHROPIC_MODEL=claude-3-sonnet-20240229
echo.
echo # Vector Database
echo VECTOR_DB=chromadb
echo VECTOR_DB_PATH=./data/vector_db
echo.
echo # Application
echo DEBUG=True
echo LOG_LEVEL=INFO
) > .env.example
echo [OK] .env.example created
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

REM Final summary
echo.
echo ========================================
echo   SETUP COMPLETE!
echo ========================================
echo.
echo Installed packages:
echo   [✓] NumPy, Pandas, scikit-learn
echo   [✓] PyTorch (CPU version)
echo   [✓] Transformers, sentence-transformers
echo   [✓] ChromaDB, FAISS, Qdrant
echo   [✓] spaCy, NLTK (gensim skipped)
echo   [✓] OpenAI, Anthropic
echo   [✓] Playwright, BeautifulSoup
echo   [✓] FastAPI, Uvicorn
echo   [✓] Jupyter, Black, Pylint, pytest
echo.
echo Created:
echo   [✓] Project structure (src/, tests/, etc.)
echo   [✓] src\main.py (FastAPI app)
echo   [✓] .env.example (config template)
echo   [✓] requirements.txt
echo   [✓] .gitignore
echo.
echo Next steps:
echo.
echo 1. Configure API keys:
echo    copy .env.example .env
echo    notepad .env
echo.
echo 2. Test the API:
echo    python src\main.py
echo    Visit: http://localhost:8000
echo.
echo 3. Verify installation:
echo    .\VERIFY-INSTALL.bat
echo.
echo 4. Start coding:
echo    Review PROJECT-TODO.md
echo    Begin with Week 1 tasks
echo.
echo Note: gensim was skipped (needs C++ tools)
echo       You can install it later if needed.
echo.
pause
