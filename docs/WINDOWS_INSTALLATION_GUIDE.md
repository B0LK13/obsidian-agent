# Windows Installation Guide - Obsidian AI Agent

**Complete step-by-step guide for Windows users**

GitHub Issue: [#111 - Improve Windows Installation Guide](https://github.com/B0LK13/obsidian-agent/issues/111)

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Install (Recommended)](#quick-install)
3. [Manual Installation](#manual-installation)
4. [Common Issues](#common-issues)
5. [Verification](#verification)
6. [Next Steps](#next-steps)

---

## Prerequisites

### Required Software

| Software | Version | Download Link |
|----------|---------|---------------|
| **Windows** | 10/11 (64-bit) | - |
| **Python** | 3.10-3.12 | [python.org](https://www.python.org/downloads/) |
| **Git** | Latest | [git-scm.com](https://git-scm.com/download/win) |
| **PowerShell** | 5.1+ | Pre-installed on Windows 10/11 |

### Optional (Recommended)

- **NVIDIA GPU** with 6GB+ VRAM for local models
- **16GB+ RAM** for best performance
- **SSD storage** for faster model loading

---

## Quick Install (Recommended)

### Step 1: Download the Project

```powershell
# Open PowerShell (Win + X → PowerShell)
cd $HOME\Documents
git clone https://github.com/B0LK13/obsidian-agent.git
cd obsidian-agent
```

### Step 2: Run the Setup Script

```powershell
# Allow script execution (one-time)
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# Run automated setup
.\scripts\windows-setup.ps1
```

The script will:
- ✅ Check Python installation
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Configure Windows Defender exclusions
- ✅ Download default model
- ✅ Verify installation

### Step 3: Start the Agent

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start PKM agent
pkm-agent tui
```

**Done!** Skip to [Verification](#verification).

---

## Manual Installation

If the automated script doesn't work, follow these steps:

### 1. Install Python

#### Download Python

1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download **Python 3.11.x** (recommended)
3. Run the installer

#### ⚠️ IMPORTANT: Installation Options

![Python Installer](https://i.imgur.com/screenshots/python-install.png)

**During installation, MUST check:**
- ☑️ **Add Python to PATH** (critical!)
- ☑️ Install for all users (optional)
- ☑️ pip (should be checked by default)

**Click "Install Now"**

#### Verify Python Installation

```powershell
# Open NEW PowerShell window (important - refresh PATH)
python --version
# Should show: Python 3.11.x

python -m pip --version
# Should show: pip 24.x.x
```

**If "python not recognized"**:
- Close and reopen PowerShell
- If still not working, see [Python PATH issues](#python-path-issues)

---

### 2. Install Git

#### Download Git

1. Go to [git-scm.com/download/win](https://git-scm.com/download/win)
2. Download 64-bit installer
3. Run installer

#### Installation Options

- **Editor**: Choose default (Vim) or your preferred editor
- **PATH**: Select "Git from the command line and also from 3rd-party software"
- **Line endings**: Choose "Checkout Windows-style, commit Unix-style"
- **Terminal**: Use default Windows Console
- **Other options**: Keep defaults

#### Verify Git

```powershell
git --version
# Should show: git version 2.x.x
```

---

### 3. Clone the Repository

```powershell
# Navigate to Documents folder
cd $HOME\Documents

# Clone project
git clone https://github.com/B0LK13/obsidian-agent.git

# Enter project directory
cd obsidian-agent

# Verify files
dir
# Should see: README.md, requirements.txt, etc.
```

---

### 4. Create Virtual Environment

**Why use a virtual environment?**
- Isolates project dependencies
- Prevents conflicts with other Python projects
- Easy to reset if something goes wrong

```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Your prompt should now show: (venv)
```

**If activation fails** with "script execution disabled":
```powershell
# Fix PowerShell execution policy
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# Try activating again
.\venv\Scripts\Activate.ps1
```

---

### 5. Install Dependencies

```powershell
# Make sure venv is activated (you see "(venv)" in prompt)

# Upgrade pip first
python -m pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Install PKM agent in development mode
cd pkm-agent
pip install -e .
cd ..
```

**This will take 5-10 minutes** depending on your internet speed.

---

### 6. Configure Windows Defender (Critical!)

Windows Defender may flag Python processes as suspicious, causing **30+ second startup delays**.

#### Automated Fix (Recommended)

```powershell
# Run as Administrator (Right-click PowerShell → Run as Administrator)
cd scripts
.\windows-defender-setup.ps1

# Verify exclusions
.\windows-defender-setup.ps1 -Verify
```

#### Manual Fix

1. Open **Windows Security** (Win + I → Privacy & Security → Windows Security)
2. Go to **Virus & threat protection**
3. Click **Manage settings**
4. Scroll to **Exclusions** → **Add or remove exclusions**
5. Add these:

**Process Exclusions**:
- `python.exe`
- `pythonw.exe`

**Folder Exclusions**:
- `C:\Users\[YourUsername]\Documents\obsidian-agent`
- `C:\Users\[YourUsername]\Documents\obsidian-agent\venv`

See [WINDOWS_DEFENDER_SETUP.md](WINDOWS_DEFENDER_SETUP.md) for details.

---

### 7. Download AI Model

```powershell
# Navigate to model downloader
cd obsidian-ai-agent\local-ai-stack\ai_stack

# List available models
python model_downloader.py list

# Download recommended model (Llama 2 7B, ~4GB)
python model_downloader.py download llama-2-7b --quant Q4_K_M

# Or download lighter model for testing (Phi-2, ~1.5GB)
python model_downloader.py download phi-2
```

**Download time**: 5-15 minutes depending on internet speed.

---

### 8. Configure Settings

Create a `.env` file in the project root:

```powershell
# Copy example config
copy .env.example .env

# Edit with Notepad
notepad .env
```

**Minimal `.env` configuration:**
```env
# PKM Settings
PKM_ROOT=C:\Users\YourUsername\Documents\YourVault

# LLM Provider (choose one)
LLM_PROVIDER=ollama  # For local models
# LLM_PROVIDER=openai  # For OpenAI API

# If using OpenAI
# OPENAI_API_KEY=your-api-key-here

# Model path (if using local models)
MODEL_PATH=./models/llama-2-7b-chat.Q4_K_M.gguf
```

---

## Verification

### Test PKM Agent

```powershell
# Activate venv if not active
.\venv\Scripts\Activate.ps1

# Start TUI
pkm-agent tui
```

**Expected**: TUI interface should appear within 5 seconds

### Test Local AI Stack

```powershell
cd obsidian-ai-agent\local-ai-stack

# Start server
python -m ai_stack.llm_server_gpu_safe
```

**Expected**: 
```
✅ GPU detected: 6144MB total VRAM
✅ Loaded model with 35 GPU layers
🚀 Server running on http://127.0.0.1:8000
```

### Test Model Download

```powershell
cd ai_stack
python model_downloader.py downloaded
```

**Expected**: List of downloaded models with sizes

---

## Common Issues

### Python PATH Issues

**Symptom**: `python` command not recognized

**Fix 1**: Restart PowerShell
```powershell
# Close PowerShell and open new window
```

**Fix 2**: Add Python to PATH manually
```powershell
# Find Python installation
where.exe python

# If not found, add manually:
$env:Path += ";C:\Users\YourUsername\AppData\Local\Programs\Python\Python311"
$env:Path += ";C:\Users\YourUsername\AppData\Local\Programs\Python\Python311\Scripts"

# Make permanent
[System.Environment]::SetEnvironmentVariable("Path", $env:Path, [System.EnvironmentVariableTarget]::User)
```

---

### PowerShell Execution Policy

**Symptom**: "script execution is disabled"

**Fix**:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# If that fails, try:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

---

### Slow Startup (30+ seconds)

**Cause**: Windows Defender scanning Python processes

**Fix**: Run Windows Defender setup script
```powershell
# As Administrator
.\scripts\windows-defender-setup.ps1
```

See [WINDOWS_DEFENDER_SETUP.md](WINDOWS_DEFENDER_SETUP.md)

---

### GPU Not Detected

**Symptom**: "No GPU detected" even with NVIDIA GPU

**Fix**:
1. Update NVIDIA drivers: [nvidia.com/drivers](https://www.nvidia.com/drivers)
2. Install CUDA Toolkit (optional): [developer.nvidia.com/cuda-downloads](https://developer.nvidia.com/cuda-downloads)
3. Verify GPU:
   ```powershell
   nvidia-smi
   ```

---

### Model Download Fails

**Symptom**: Download interrupted or fails

**Fix**:
```powershell
# Downloads support resume - just run again
python model_downloader.py download llama-2-7b --quant Q4_K_M

# If still fails, try no-resume mode
python model_downloader.py download llama-2-7b --quant Q4_K_M --no-resume
```

---

### Out of Memory (OOM) Errors

**Symptom**: "CUDA out of memory" when loading model

**Fix**:
1. Use smaller quantization:
   ```powershell
   # Instead of Q5/Q6, use Q4
   python model_downloader.py download llama-2-7b --quant Q4_K_M
   ```

2. Reduce context size in `config.yaml`:
   ```yaml
   performance:
     context_size: 2048  # Instead of 4096
   ```

3. Use CPU-only mode:
   ```yaml
   performance:
     gpu_layers: 0  # Force CPU
   ```

See [GPU Memory Management Guide](../GITHUB_ISSUES.md#issue-103)

---

### pip Install Errors

**Symptom**: Package installation fails

**Fix**:
```powershell
# Upgrade pip
python -m pip install --upgrade pip setuptools wheel

# Install with verbose output to see errors
pip install -r requirements.txt -v

# If specific package fails, install individually
pip install package-name
```

---

## Next Steps

### 1. Configure Obsidian Plugin

```powershell
# Copy plugin to Obsidian vault
cd apps\obsidian-plugin
# Follow plugin README for installation
```

### 2. Set Up Knowledge Base

```powershell
# Initialize your vault
pkm-agent init --vault-path "C:\Users\YourUsername\Documents\MyVault"

# Index notes
pkm-agent index
```

### 3. Start Using

```powershell
# TUI interface
pkm-agent tui

# Or web interface
pkm-agent studio
```

---

## Additional Resources

- **Troubleshooting**: See [Common Issues](#common-issues) above
- **Windows Defender**: [WINDOWS_DEFENDER_SETUP.md](WINDOWS_DEFENDER_SETUP.md)
- **Model Downloads**: [Model Download Guide](../README.md#model-management)
- **GPU Issues**: [GitHub Issue #103](https://github.com/B0LK13/obsidian-agent/issues/103)
- **Community**: [GitHub Discussions](https://github.com/B0LK13/obsidian-agent/discussions)

---

## Video Tutorial

📺 **Coming Soon**: Step-by-step video walkthrough

---

## Getting Help

If you encounter issues:

1. Check [Common Issues](#common-issues)
2. Search [GitHub Issues](https://github.com/B0LK13/obsidian-agent/issues)
3. Create new issue with:
   - Windows version
   - Python version (`python --version`)
   - Error messages
   - Steps to reproduce

---

**Last Updated**: 2026-02-03  
**Status**: ✅ Complete Windows installation guide  
**GitHub Issue**: [#111](https://github.com/B0LK13/obsidian-agent/issues/111)
