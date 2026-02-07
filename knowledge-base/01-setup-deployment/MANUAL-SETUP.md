# B0LK13v2 - Manual Execution Guide

## ⚠️ System Limitation Detected

The automated PowerShell scripts require PowerShell 6+ (pwsh), but your system only has Windows PowerShell 5.x.

**No problem!** You can execute everything manually with these simple commands.

---

## 🚀 Quick Start (Copy & Paste)

### Step 1: Generate GitHub Issues (2 minutes)

Open Command Prompt or PowerShell and run:

```cmd
cd C:\Users\Admin\Documents\B0LK13v2
python create-github-issues.py
```

**Expected Output:**
```
Generating GitHub issues from CSV...
Created: github-issues/00-SUMMARY.md
Created: github-issues/Foundation/1-incremental-indexing.md
...
Successfully generated 67 issue files!
```

**Verify:**
- Check that `github-issues\` folder exists
- Should contain 67 `.md` files organized by milestone

---

### Step 2: Set Up Python Virtual Environment (5 minutes)

```cmd
cd C:\Users\Admin\Documents\B0LK13v2
python -m venv venv
```

**Expected Output:**
- Creates `venv\` folder
- Contains Python isolated environment

**Verify:**
```cmd
dir venv
```
Should show: `Include\`, `Lib\`, `Scripts\`, `pyvenv.cfg`

---

### Step 3: Activate Virtual Environment (Instant)

```cmd
venv\Scripts\activate.bat
```

**Expected Output:**
Your prompt changes to:
```
(venv) C:\Users\Admin\Documents\B0LK13v2>
```

This means the virtual environment is active!

---

### Step 4: Upgrade pip (1 minute)

```cmd
python -m pip install --upgrade pip setuptools wheel
```

**Expected Output:**
```
Successfully installed pip-24.x setuptools-69.x wheel-0.42.x
```

---

### Step 5: Install AI/ML Dependencies (5-10 minutes)

This is the longest step. Install packages in groups:

#### Core ML Stack
```cmd
pip install numpy pandas scikit-learn matplotlib seaborn
```

#### Deep Learning
```cmd
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

#### Transformers & Embeddings
```cmd
pip install transformers sentence-transformers
```

#### Vector Databases
```cmd
pip install chromadb faiss-cpu qdrant-client
```

#### NLP Tools
```cmd
pip install spacy nltk gensim
```

#### LLM APIs
```cmd
pip install openai anthropic
```

#### Web & API
```cmd
pip install playwright beautifulsoup4 lxml requests fastapi uvicorn python-dotenv
```

#### Development Tools
```cmd
pip install jupyter notebook black pylint pytest pytest-cov ipykernel
```

**Or install everything at once:**
```cmd
pip install numpy pandas scikit-learn matplotlib seaborn torch torchvision torchaudio transformers sentence-transformers chromadb faiss-cpu qdrant-client spacy nltk gensim openai anthropic playwright beautifulsoup4 lxml requests fastapi uvicorn python-dotenv jupyter notebook black pylint pytest pytest-cov ipykernel
```

---

### Step 6: Install Playwright Browsers (2 minutes)

```cmd
playwright install chromium
```

**Expected Output:**
```
Downloading Chromium...
Chromium installed successfully
```

---

### Step 7: Create Project Structure (1 minute)

```cmd
mkdir src
mkdir src\indexing
mkdir src\search
mkdir src\ml
mkdir src\api
mkdir src\ui
mkdir tests
mkdir notebooks
mkdir data
mkdir models
mkdir configs
mkdir logs
```

**Verify:**
```cmd
dir
```
Should show all new folders.

---

### Step 8: Create Starter Files (Copy & Paste)

#### Create `src\__init__.py`
```cmd
echo. > src\__init__.py
```

#### Create `src\main.py`
```cmd
notepad src\main.py
```

Paste this code:
```python
"""
B0LK13v2 PKM-Agent - Main Application
Fast API application for AI-powered knowledge management
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="B0LK13v2 PKM-Agent",
    description="AI-powered Personal Knowledge Management Agent",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "status": "running",
        "service": "B0LK13v2 PKM-Agent",
        "version": "0.1.0",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "tasks": "/api/v1/tasks"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/api/v1/tasks")
async def list_tasks():
    """List all tasks"""
    return {"tasks": [], "total": 0}

if __name__ == "__main__":
    print("🚀 Starting B0LK13v2 PKM-Agent...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Save and close.

#### Create `.env.example`
```cmd
notepad .env.example
```

Paste this:
```env
# B0LK13v2 PKM-Agent Configuration

# OpenAI API
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_MODEL=gpt-4

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Vector Database
VECTOR_DB=chromadb
VECTOR_DB_PATH=./data/vector_db

# Application
DEBUG=True
LOG_LEVEL=INFO
```

Save and close.

#### Create `requirements.txt`
```cmd
pip freeze > requirements.txt
```

This saves all installed packages.

#### Create `.gitignore`
```cmd
notepad .gitignore
```

Paste this:
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Environment
.env
*.log

# Data
data/
models/
logs/
*.db
*.sqlite

# OS
.DS_Store
Thumbs.db
desktop.ini

# Project
github-issues/
*.zip
```

Save and close.

---

### Step 9: Test Installation (30 seconds)

```cmd
python src\main.py
```

**Expected Output:**
```
🚀 Starting B0LK13v2 PKM-Agent...
📖 API Documentation: http://localhost:8000/docs
🔍 Health Check: http://localhost:8000/health
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Test in browser:**
- Open: http://localhost:8000
- Should see JSON response: `{"status": "running", ...}`
- Open: http://localhost:8000/docs
- Should see interactive API documentation

Press `Ctrl+C` to stop the server.

---

### Step 10: Create Your `.env` File

```cmd
copy .env.example .env
notepad .env
```

Replace the placeholder API keys with your actual keys:
- Get OpenAI key from: https://platform.openai.com/api-keys
- Get Anthropic key from: https://console.anthropic.com/

Save and close.

---

### Step 11: System Optimization (Optional - Windows PowerShell 5.x)

You can run the optimization script with regular Windows PowerShell:

```cmd
powershell -ExecutionPolicy Bypass -File optimize-system.ps1
```

This will:
- Check CPU, RAM, GPU
- Verify Python installation
- Test AI/ML packages
- Check dev tools
- Set environment variables
- Generate report

---

## ✅ Verification Checklist

After completing all steps, verify:

```cmd
# Check Python version
python --version

# Check virtual environment is active (should show venv path)
where python

# Check installed packages
pip list

# Check project structure
dir

# Test API
python src\main.py
```

Expected results:
- ✅ Python 3.10+ installed
- ✅ Virtual environment active (path contains `venv`)
- ✅ 40+ packages installed
- ✅ Folders: src, tests, notebooks, data, models, configs, logs
- ✅ API runs on http://localhost:8000
- ✅ `.env` file exists with API keys

---

## 🎯 Next Steps - Start Development

### Week 1, Issue #1: Database Schema

Create `src\database.py`:

```python
"""Database models for B0LK13v2 PKM-Agent"""

from sqlalchemy import create_engine, Column, String, Integer, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Task(Base):
    """Task model"""
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True)
    prompt = Column(String, nullable=False)
    status = Column(String, default="CREATED")  # CREATED, PLANNING, EXECUTING, DELIVERING, COMPLETED, FAILED, CANCELLED
    project_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, default={})

class TaskEvent(Base):
    """Task event/timeline model"""
    __tablename__ = "task_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)  # state_change, tool_call, error
    step_id = Column(String, nullable=True)
    tool_name = Column(String, nullable=True)
    status = Column(String, nullable=True)
    data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class Artifact(Base):
    """Artifact model"""
    __tablename__ = "artifacts"
    
    id = Column(String, primary_key=True)
    task_id = Column(String, nullable=False, index=True)
    artifact_type = Column(String, nullable=False)  # report, file, zip
    filename = Column(String, nullable=False)
    path = Column(String, nullable=False)
    size_bytes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, default={})

class SandboxRef(Base):
    """Sandbox reference model"""
    __tablename__ = "sandbox_refs"
    
    id = Column(String, primary_key=True)
    task_id = Column(String, nullable=False, index=True)
    sandbox_id = Column(String, nullable=False)
    status = Column(String, default="CREATED")  # CREATED, RUNNING, STOPPED, DESTROYED
    created_at = Column(DateTime, default=datetime.utcnow)
    destroyed_at = Column(DateTime, nullable=True)

# Create engine and tables
engine = create_engine("sqlite:///data/pkm_agent.db")
Base.metadata.create_all(engine)

# Create session factory
SessionLocal = sessionmaker(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Test it:
```cmd
python -c "from src.database import engine, Base; Base.metadata.create_all(engine); print('✅ Database created!')"
```

---

## 📚 Documentation

All documentation is ready:

1. **SETUP-COMPLETE.md** - Comprehensive overview
2. **PROJECT-TODO.md** - All 67 tasks with acceptance criteria
3. **DEV-GUIDE.md** - Development workflow
4. **AI-ML-OPTIMIZATION.md** - Performance tips
5. **INDEX.md** - Navigation hub

---

## 🐛 Troubleshooting

### Python not found
```cmd
# Check if Python is installed
python --version

# If not, download from:
# https://www.python.org/downloads/
# Or use winget:
winget install Python.Python.3.12
```

### pip not found
```cmd
python -m ensurepip --upgrade
python -m pip install --upgrade pip
```

### Virtual environment activation fails
```cmd
# Use full path
C:\Users\Admin\Documents\B0LK13v2\venv\Scripts\activate.bat
```

### Package installation fails
```cmd
# Upgrade pip first
python -m pip install --upgrade pip setuptools wheel

# Install packages one at a time
pip install numpy
pip install pandas
# etc.
```

### PyTorch installation fails
```cmd
# Try CPU-only version
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

---

## 🎉 You're Done!

Your development environment is now fully set up!

**Time to code:** Start with Week 1 tasks in PROJECT-TODO.md

**Questions?** Check DEV-GUIDE.md for workflow guidance

**Performance?** See AI-ML-OPTIMIZATION.md for optimization tips

---

**Happy Coding! 🚀**
