# 🚀 B0LK13v2 - Quick Command Reference

## ✅ COMPLETE SETUP NOW

### Run This Command:
```powershell
.\CONTINUE-SETUP.bat
```

**What it does:**
- ✅ Installs all remaining packages (without gensim)
- ✅ Creates complete project structure
- ✅ Generates src\main.py
- ✅ Creates .env.example
- ✅ Sets up .gitignore
- ✅ Saves requirements.txt

**Time:** 10-15 minutes

---

## 🧪 TEST INSTALLATION

### After setup completes:
```powershell
.\START-NOW.bat
```

**What it does:**
- ✅ Tests package imports
- ✅ Creates .env file
- ✅ Opens .env in Notepad (add your API keys)
- ✅ Starts API server
- ✅ Opens browser to http://localhost:8000

---

## 🔑 CONFIGURE API KEYS

Edit your .env file:
```powershell
notepad .env
```

Replace these:
```
OPENAI_API_KEY=sk-your-actual-key-here
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

Get keys from:
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/

---

## 💻 DAILY COMMANDS

### Start Development Session:
```powershell
# Activate environment
.\venv\Scripts\activate.bat

# Run API server
python src\main.py
```

### Run Tests:
```powershell
pytest tests/ -v
```

### Format Code:
```powershell
black src/
```

### Start Jupyter:
```powershell
jupyter notebook
```

### Check Installed Packages:
```powershell
pip list
```

---

## 📝 WEEK 1 TASKS

See PROJECT-TODO.md for details:

1. **Database Schema** - Create models for Task, TaskEvent, Artifact, SandboxRef
2. **Task Lifecycle** - Implement state machine (CREATED→COMPLETED)
3. **Task API** - Build REST endpoints (POST, GET)
4. **UI Components** - Task list, create modal, detail page

---

## 🐛 TROUBLESHOOTING

### If API won't start:
```powershell
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Use different port
# Edit src\main.py, change port=8000 to port=8001
```

### If packages fail to import:
```powershell
# Reinstall specific package
pip install --force-reinstall package-name
```

### If gensim is needed later:
1. Install Visual C++ Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Then: `pip install gensim`

---

## 📚 DOCUMENTATION

- **PROJECT-TODO.md** - All 67 tasks with acceptance criteria
- **DEV-GUIDE.md** - Development workflow
- **AI-ML-OPTIMIZATION.md** - Performance tips
- **SETUP-COMPLETE.md** - Comprehensive overview

---

## ✅ VERIFICATION CHECKLIST

After setup:
- [ ] Virtual environment active (venv)
- [ ] All packages installed (check with `pip list`)
- [ ] Project folders created (src/, tests/, data/, etc.)
- [ ] src\main.py exists and runs
- [ ] .env file created with API keys
- [ ] API accessible at http://localhost:8000
- [ ] API docs at http://localhost:8000/docs

---

## 🎯 CURRENT STATUS

**What's done:**
- ✅ Virtual environment created
- ✅ Basic packages installed
- ⏳ Need to run CONTINUE-SETUP.bat
- ⏳ Need to configure API keys
- ⏳ Need to test API

**What's next:**
1. Run `.\CONTINUE-SETUP.bat`
2. Wait for installation (10-15 min)
3. Run `.\START-NOW.bat`
4. Add API keys to .env
5. Start coding!

---

## 🚀 EXECUTE NOW:

```powershell
.\CONTINUE-SETUP.bat
```

**Then after it completes:**

```powershell
.\START-NOW.bat
```

---

**You're almost there! Just run the commands above!** 🎯
