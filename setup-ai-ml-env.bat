@echo off
REM ============================================================
REM B0LK13v2 AI/ML Development Environment Setup
REM ============================================================

echo ============================================================
echo B0LK13v2 AI/ML Development Environment Setup
echo ============================================================
echo.

REM Step 1: Check Python
echo [1/10] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo.
    echo Please install Python 3.10 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Or use winget: winget install Python.Python.3.12
    echo.
    pause
    exit /b 1
)

python --version
echo [OK] Python found
echo.

REM Step 2: Create virtual environment
echo [2/10] Creating Python virtual environment...
if exist venv (
    echo [INFO] Virtual environment already exists
) else (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)
echo.

REM Step 3: Activate virtual environment and install dependencies
echo [3/10] Installing AI/ML dependencies...
call venv\Scripts\activate.bat

echo Installing core packages...
pip install --upgrade pip setuptools wheel

echo Installing AI/ML frameworks...
pip install numpy pandas scikit-learn matplotlib seaborn
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install transformers sentence-transformers
pip install openai anthropic

echo Installing vector databases...
pip install chromadb faiss-cpu qdrant-client

echo Installing NLP tools...
pip install spacy nltk gensim
python -m spacy download en_core_web_sm

echo Installing web scraping and automation...
pip install playwright beautifulsoup4 selenium
playwright install chromium

echo Installing development tools...
pip install jupyter ipython black pylint pytest pytest-cov
pip install python-dotenv pyyaml

echo Installing API and web frameworks...
pip install fastapi uvicorn requests httpx aiohttp

echo Installing database tools...
pip install sqlalchemy alembic psycopg2-binary

echo [OK] Dependencies installed
echo.

REM Step 4: Generate GitHub issues
echo [4/10] Generating GitHub issues...
python create-github-issues.py
echo.

REM Step 5: Create project structure
echo [5/10] Creating AI/ML project structure...
if not exist src mkdir src
if not exist src\indexing mkdir src\indexing
if not exist src\search mkdir src\search
if not exist src\ml mkdir src\ml
if not exist src\api mkdir src\api
if not exist src\ui mkdir src\ui
if not exist tests mkdir tests
if not exist data mkdir data
if not exist models mkdir models
if not exist notebooks mkdir notebooks
if not exist configs mkdir configs
if not exist logs mkdir logs

echo [OK] Project structure created
echo.

REM Step 6: Create configuration files
echo [6/10] Creating configuration files...

REM Create .env template
echo # Environment Configuration > .env.example
echo # Copy this to .env and fill in your values >> .env.example
echo. >> .env.example
echo # API Keys >> .env.example
echo OPENAI_API_KEY=your_openai_key_here >> .env.example
echo ANTHROPIC_API_KEY=your_anthropic_key_here >> .env.example
echo. >> .env.example
echo # Database >> .env.example
echo DATABASE_URL=sqlite:///./pkm_agent.db >> .env.example
echo. >> .env.example
echo # Vector Database >> .env.example
echo VECTOR_DB_PATH=./data/vector_db >> .env.example
echo. >> .env.example
echo # Application >> .env.example
echo DEBUG=True >> .env.example
echo LOG_LEVEL=INFO >> .env.example

REM Create requirements.txt
echo # AI/ML Development Requirements > requirements.txt
echo # Core >> requirements.txt
echo numpy>=1.24.0 >> requirements.txt
echo pandas>=2.0.0 >> requirements.txt
echo scikit-learn>=1.3.0 >> requirements.txt
echo. >> requirements.txt
echo # Deep Learning >> requirements.txt
echo torch>=2.0.0 >> requirements.txt
echo transformers>=4.30.0 >> requirements.txt
echo sentence-transformers>=2.2.0 >> requirements.txt
echo. >> requirements.txt
echo # Vector Databases >> requirements.txt
echo chromadb>=0.4.0 >> requirements.txt
echo faiss-cpu>=1.7.4 >> requirements.txt
echo qdrant-client>=1.5.0 >> requirements.txt
echo. >> requirements.txt
echo # NLP >> requirements.txt
echo spacy>=3.6.0 >> requirements.txt
echo nltk>=3.8.0 >> requirements.txt
echo gensim>=4.3.0 >> requirements.txt
echo. >> requirements.txt
echo # Web >> requirements.txt
echo playwright>=1.38.0 >> requirements.txt
echo beautifulsoup4>=4.12.0 >> requirements.txt
echo. >> requirements.txt
echo # API >> requirements.txt
echo fastapi>=0.100.0 >> requirements.txt
echo uvicorn>=0.23.0 >> requirements.txt
echo requests>=2.31.0 >> requirements.txt
echo openai>=1.0.0 >> requirements.txt
echo anthropic>=0.3.0 >> requirements.txt
echo. >> requirements.txt
echo # Database >> requirements.txt
echo sqlalchemy>=2.0.0 >> requirements.txt
echo alembic>=1.11.0 >> requirements.txt
echo. >> requirements.txt
echo # Development >> requirements.txt
echo jupyter>=1.0.0 >> requirements.txt
echo black>=23.0.0 >> requirements.txt
echo pylint>=2.17.0 >> requirements.txt
echo pytest>=7.4.0 >> requirements.txt
echo pytest-cov>=4.1.0 >> requirements.txt
echo python-dotenv>=1.0.0 >> requirements.txt

echo [OK] Configuration files created
echo.

REM Step 7: Create starter code
echo [7/10] Creating starter code templates...

REM Create main application entry point
echo # PKM-Agent Main Application > src\main.py
echo from fastapi import FastAPI >> src\main.py
echo from fastapi.middleware.cors import CORSMiddleware >> src\main.py
echo import uvicorn >> src\main.py
echo. >> src\main.py
echo app = FastAPI(title="PKM-Agent API", version="0.1.0") >> src\main.py
echo. >> src\main.py
echo # CORS >> src\main.py
echo app.add_middleware( >> src\main.py
echo     CORSMiddleware, >> src\main.py
echo     allow_origins=["*"], >> src\main.py
echo     allow_credentials=True, >> src\main.py
echo     allow_methods=["*"], >> src\main.py
echo     allow_headers=["*"], >> src\main.py
echo ) >> src\main.py
echo. >> src\main.py
echo @app.get("/") >> src\main.py
echo async def root(): >> src\main.py
echo     return {"message": "PKM-Agent API", "version": "0.1.0"} >> src\main.py
echo. >> src\main.py
echo if __name__ == "__main__": >> src\main.py
echo     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) >> src\main.py

REM Create indexing module
echo # Incremental Indexing Module > src\indexing\incremental_indexer.py
echo """Incremental indexing for PKM notes""" >> src\indexing\incremental_indexer.py
echo import os >> src\indexing\incremental_indexer.py
echo from pathlib import Path >> src\indexing\incremental_indexer.py
echo from typing import List, Dict >> src\indexing\incremental_indexer.py
echo. >> src\indexing\incremental_indexer.py
echo class IncrementalIndexer: >> src\indexing\incremental_indexer.py
echo     """Handles incremental indexing of notes""" >> src\indexing\incremental_indexer.py
echo     def __init__(self, index_path: str): >> src\indexing\incremental_indexer.py
echo         self.index_path = Path(index_path) >> src\indexing\incremental_indexer.py
echo         self.index = {} >> src\indexing\incremental_indexer.py
echo. >> src\indexing\incremental_indexer.py
echo     def index_note(self, note_path: str) -^> Dict: >> src\indexing\incremental_indexer.py
echo         """Index a single note""" >> src\indexing\incremental_indexer.py
echo         pass >> src\indexing\incremental_indexer.py
echo. >> src\indexing\incremental_indexer.py
echo     def update_index(self, changed_files: List[str]) -^> None: >> src\indexing\incremental_indexer.py
echo         """Update index for changed files only""" >> src\indexing\incremental_indexer.py
echo         pass >> src\indexing\incremental_indexer.py

REM Create vector search module
echo # Vector Search Module > src\search\vector_search.py
echo """Vector-based semantic search""" >> src\search\vector_search.py
echo from sentence_transformers import SentenceTransformer >> src\search\vector_search.py
echo import chromadb >> src\search\vector_search.py
echo from typing import List, Dict >> src\search\vector_search.py
echo. >> src\search\vector_search.py
echo class VectorSearch: >> src\search\vector_search.py
echo     """Semantic search using vector embeddings""" >> src\search\vector_search.py
echo     def __init__(self, model_name: str = "all-MiniLM-L6-v2"): >> src\search\vector_search.py
echo         self.model = SentenceTransformer(model_name) >> src\search\vector_search.py
echo         self.client = chromadb.Client() >> src\search\vector_search.py
echo. >> src\search\vector_search.py
echo     def embed_text(self, text: str): >> src\search\vector_search.py
echo         """Generate embeddings for text""" >> src\search\vector_search.py
echo         return self.model.encode(text) >> src\search\vector_search.py
echo. >> src\search\vector_search.py
echo     def search(self, query: str, top_k: int = 5) -^> List[Dict]: >> src\search\vector_search.py
echo         """Perform semantic search""" >> src\search\vector_search.py
echo         pass >> src\search\vector_search.py

REM Create ML module
echo # ML Link Suggestion Module > src\ml\link_suggester.py
echo """ML-powered link suggestion engine""" >> src\ml\link_suggester.py
echo from typing import List, Tuple >> src\ml\link_suggester.py
echo import numpy as np >> src\ml\link_suggester.py
echo. >> src\ml\link_suggester.py
echo class LinkSuggester: >> src\ml\link_suggester.py
echo     """Suggests relevant links between notes""" >> src\ml\link_suggester.py
echo     def __init__(self): >> src\ml\link_suggester.py
echo         pass >> src\ml\link_suggester.py
echo. >> src\ml\link_suggester.py
echo     def suggest_links(self, note_id: str, top_n: int = 5) -^> List[Tuple[str, float]]: >> src\ml\link_suggester.py
echo         """Suggest top N relevant links for a note""" >> src\ml\link_suggester.py
echo         pass >> src\ml\link_suggester.py

echo [OK] Starter code created
echo.

REM Step 8: Create Jupyter notebook
echo [8/10] Creating Jupyter notebook for experimentation...
echo { > notebooks\01_vector_search_exploration.ipynb
echo   "cells": [ >> notebooks\01_vector_search_exploration.ipynb
echo     { >> notebooks\01_vector_search_exploration.ipynb
echo       "cell_type": "markdown", >> notebooks\01_vector_search_exploration.ipynb
echo       "metadata": {}, >> notebooks\01_vector_search_exploration.ipynb
echo       "source": ["# Vector Search Exploration\n", "Experimenting with semantic search for PKM notes"] >> notebooks\01_vector_search_exploration.ipynb
echo     }, >> notebooks\01_vector_search_exploration.ipynb
echo     { >> notebooks\01_vector_search_exploration.ipynb
echo       "cell_type": "code", >> notebooks\01_vector_search_exploration.ipynb
echo       "execution_count": null, >> notebooks\01_vector_search_exploration.ipynb
echo       "metadata": {}, >> notebooks\01_vector_search_exploration.ipynb
echo       "outputs": [], >> notebooks\01_vector_search_exploration.ipynb
echo       "source": ["import sys\n", "sys.path.append('../src')\n", "\n", "from search.vector_search import VectorSearch\n", "import numpy as np"] >> notebooks\01_vector_search_exploration.ipynb
echo     } >> notebooks\01_vector_search_exploration.ipynb
echo   ], >> notebooks\01_vector_search_exploration.ipynb
echo   "metadata": { >> notebooks\01_vector_search_exploration.ipynb
echo     "kernelspec": { >> notebooks\01_vector_search_exploration.ipynb
echo       "display_name": "Python 3", >> notebooks\01_vector_search_exploration.ipynb
echo       "language": "python", >> notebooks\01_vector_search_exploration.ipynb
echo       "name": "python3" >> notebooks\01_vector_search_exploration.ipynb
echo     } >> notebooks\01_vector_search_exploration.ipynb
echo   }, >> notebooks\01_vector_search_exploration.ipynb
echo   "nbformat": 4, >> notebooks\01_vector_search_exploration.ipynb
echo   "nbformat_minor": 4 >> notebooks\01_vector_search_exploration.ipynb
echo } >> notebooks\01_vector_search_exploration.ipynb

echo [OK] Notebook created
echo.

REM Step 9: Create .gitignore
echo [9/10] Creating .gitignore...
echo # Python > .gitignore
echo __pycache__/ >> .gitignore
echo *.py[cod] >> .gitignore
echo *$py.class >> .gitignore
echo *.so >> .gitignore
echo .Python >> .gitignore
echo venv/ >> .gitignore
echo ENV/ >> .gitignore
echo. >> .gitignore
echo # IDEs >> .gitignore
echo .vscode/ >> .gitignore
echo .idea/ >> .gitignore
echo *.swp >> .gitignore
echo *.swo >> .gitignore
echo. >> .gitignore
echo # Environment >> .gitignore
echo .env >> .gitignore
echo .env.local >> .gitignore
echo. >> .gitignore
echo # Data >> .gitignore
echo data/ >> .gitignore
echo *.db >> .gitignore
echo *.sqlite >> .gitignore
echo. >> .gitignore
echo # Models >> .gitignore
echo models/*.pt >> .gitignore
echo models/*.pth >> .gitignore
echo models/*.pkl >> .gitignore
echo. >> .gitignore
echo # Logs >> .gitignore
echo logs/ >> .gitignore
echo *.log >> .gitignore
echo. >> .gitignore
echo # Jupyter >> .gitignore
echo .ipynb_checkpoints/ >> .gitignore
echo. >> .gitignore
echo # OS >> .gitignore
echo .DS_Store >> .gitignore
echo Thumbs.db >> .gitignore
echo desktop.ini >> .gitignore
echo. >> .gitignore
echo # GitHub issues >> .gitignore
echo github-issues/ >> .gitignore

echo [OK] .gitignore created
echo.

REM Step 10: Create development guide
echo [10/10] Creating development guide...
echo # PKM-Agent AI/ML Development Guide > DEV-GUIDE.md
echo. >> DEV-GUIDE.md
echo ## Quick Start >> DEV-GUIDE.md
echo. >> DEV-GUIDE.md
echo ### 1. Activate Virtual Environment >> DEV-GUIDE.md
echo ```cmd >> DEV-GUIDE.md
echo venv\Scripts\activate.bat >> DEV-GUIDE.md
echo ``` >> DEV-GUIDE.md
echo. >> DEV-GUIDE.md
echo ### 2. Start Development Server >> DEV-GUIDE.md
echo ```cmd >> DEV-GUIDE.md
echo python src\main.py >> DEV-GUIDE.md
echo ``` >> DEV-GUIDE.md
echo. >> DEV-GUIDE.md
echo ### 3. Run Jupyter Notebooks >> DEV-GUIDE.md
echo ```cmd >> DEV-GUIDE.md
echo jupyter notebook >> DEV-GUIDE.md
echo ``` >> DEV-GUIDE.md
echo. >> DEV-GUIDE.md
echo ### 4. Run Tests >> DEV-GUIDE.md
echo ```cmd >> DEV-GUIDE.md
echo pytest tests/ >> DEV-GUIDE.md
echo ``` >> DEV-GUIDE.md
echo. >> DEV-GUIDE.md
echo ## AI/ML Components >> DEV-GUIDE.md
echo. >> DEV-GUIDE.md
echo ### 1. Incremental Indexing (P1) >> DEV-GUIDE.md
echo - Location: `src\indexing\incremental_indexer.py` >> DEV-GUIDE.md
echo - Goal: Process 1000 notes in ^<10s >> DEV-GUIDE.md
echo - Strategy: Track file changes, update index incrementally >> DEV-GUIDE.md
echo. >> DEV-GUIDE.md
echo ### 2. Vector Search (P1) >> DEV-GUIDE.md
echo - Location: `src\search\vector_search.py` >> DEV-GUIDE.md
echo - Model: sentence-transformers/all-MiniLM-L6-v2 >> DEV-GUIDE.md
echo - Database: ChromaDB >> DEV-GUIDE.md
echo - Goal: Semantic search with 0.8+ relevance score >> DEV-GUIDE.md
echo. >> DEV-GUIDE.md
echo ### 3. Link Suggestions (P1) >> DEV-GUIDE.md
echo - Location: `src\ml\link_suggester.py` >> DEV-GUIDE.md
echo - Algorithm: Cosine similarity on embeddings >> DEV-GUIDE.md
echo - Goal: 80%% accuracy, suggest 5+ relevant links >> DEV-GUIDE.md
echo. >> DEV-GUIDE.md
echo ## Development Workflow >> DEV-GUIDE.md
echo. >> DEV-GUIDE.md
echo 1. Pick an issue from PROJECT-TODO.md >> DEV-GUIDE.md
echo 2. Create feature branch: `git checkout -b feature/issue-name` >> DEV-GUIDE.md
echo 3. Implement with tests >> DEV-GUIDE.md
echo 4. Run tests: `pytest` >> DEV-GUIDE.md
echo 5. Format code: `black src/` >> DEV-GUIDE.md
echo 6. Commit: `git commit -m "feat: description (#issue)"` >> DEV-GUIDE.md
echo 7. Push and create PR >> DEV-GUIDE.md
echo. >> DEV-GUIDE.md
echo ## Performance Targets >> DEV-GUIDE.md
echo. >> DEV-GUIDE.md
echo - Indexing: 1000 notes in ^<10s >> DEV-GUIDE.md
echo - Search response: ^<2s >> DEV-GUIDE.md
echo - Vector embeddings: 1000 notes in ^<60s >> DEV-GUIDE.md
echo - Cache hit rate: ^>80%% >> DEV-GUIDE.md
echo. >> DEV-GUIDE.md
echo ## Useful Commands >> DEV-GUIDE.md
echo. >> DEV-GUIDE.md
echo ```cmd >> DEV-GUIDE.md
echo # Activate venv >> DEV-GUIDE.md
echo venv\Scripts\activate.bat >> DEV-GUIDE.md
echo. >> DEV-GUIDE.md
echo # Install new package >> DEV-GUIDE.md
echo pip install package-name >> DEV-GUIDE.md
echo pip freeze ^> requirements.txt >> DEV-GUIDE.md
echo. >> DEV-GUIDE.md
echo # Run API server >> DEV-GUIDE.md
echo python src\main.py >> DEV-GUIDE.md
echo. >> DEV-GUIDE.md
echo # Run Jupyter >> DEV-GUIDE.md
echo jupyter notebook >> DEV-GUIDE.md
echo. >> DEV-GUIDE.md
echo # Run tests >> DEV-GUIDE.md
echo pytest tests/ -v >> DEV-GUIDE.md
echo. >> DEV-GUIDE.md
echo # Format code >> DEV-GUIDE.md
echo black src/ tests/ >> DEV-GUIDE.md
echo. >> DEV-GUIDE.md
echo # Lint code >> DEV-GUIDE.md
echo pylint src/ >> DEV-GUIDE.md
echo ``` >> DEV-GUIDE.md

echo [OK] Development guide created
echo.

echo ============================================================
echo Setup Complete!
echo ============================================================
echo.
echo Virtual environment: venv\
echo Source code: src\
echo Notebooks: notebooks\
echo Configuration: .env.example (copy to .env and configure)
echo.
echo Next steps:
echo 1. Copy .env.example to .env and add your API keys
echo 2. Activate virtual environment: venv\Scripts\activate.bat
echo 3. Start coding! Read DEV-GUIDE.md for workflow
echo 4. Review PROJECT-TODO.md for prioritized tasks
echo.
echo To start the API server:
echo   venv\Scripts\activate.bat
echo   python src\main.py
echo.
echo To start Jupyter:
echo   venv\Scripts\activate.bat
echo   jupyter notebook
echo.
pause
