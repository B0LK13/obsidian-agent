# Windows Installation Guide for Obsidian AI Agent

Complete step-by-step guide for installing and configuring the Obsidian AI Agent on Windows.

## Prerequisites

Before you begin, ensure you have:

- Windows 10/11 (64-bit)
- Administrator access
- Internet connection
- At least 8GB RAM (16GB+ recommended)
- 10GB free disk space

## Quick Start (Automated)

The fastest way to get started is using the automated setup script:

### Step 1: Open PowerShell as Administrator

1. Press `Win + X`
2. Select **"Windows PowerShell (Admin)"** or **"Terminal (Admin)"**
3. If prompted by UAC, click **Yes**

### Step 2: Run the Setup Script

```powershell
# Navigate to the project directory
cd "$env:USERPROFILE\Documents\B0LK13v2\obsidian-ai-agent"

# Run the automated setup
.\scripts\windows-setup.ps1
```

This script will:
- Check Python installation
- Install required dependencies
- Configure Windows Defender exclusions
- Download a default model (if none exists)
- Start the local AI stack

### Step 3: Install the Obsidian Plugin

1. Open Obsidian
2. Go to **Settings** → **Community Plugins**
3. Turn on **Safe Mode** (disable it temporarily if needed)
4. Click **Browse** and search for "PKM Agent"
5. Click **Install**, then **Enable**

### Step 4: Configure the Plugin

1. In Obsidian, go to **Settings** → **PKM Agent**
2. Verify the endpoints:
   - LLM Endpoint: `http://127.0.0.1:8000`
   - Embeddings Endpoint: `http://127.0.0.1:8001`
   - Vector DB Endpoint: `http://127.0.0.1:8002`
3. Click **Test Connection**

## Manual Installation

If you prefer manual installation or the automated script fails:

### 1. Install Python

Download and install Python 3.10 or higher from [python.org](https://python.org):

1. Go to https://www.python.org/downloads/
2. Download Python 3.10+ (64-bit)
3. Run the installer
4. **Important**: Check **"Add Python to PATH"**
5. Click **Install Now**

Verify installation:
```powershell
python --version
pip --version
```

### 2. Install Git (Optional but Recommended)

Download from [git-scm.com](https://git-scm.com/download/win) or install via winget:
```powershell
winget install Git.Git
```

### 3. Clone or Download the Repository

```powershell
# Using git
git clone https://github.com/B0LK13/obsidian-ai-agent.git
cd obsidian-ai-agent

# Or download and extract the ZIP manually
```

### 4. Create Virtual Environment

```powershell
# Navigate to the local-ai-stack folder
cd local-ai-stack

# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Your prompt should now show (venv)
```

**If you get an execution policy error**, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 5. Install Dependencies

```powershell
# Install base requirements
pip install -r requirements.txt

# For GPU support (NVIDIA only)
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121

# For CPU-only
pip install llama-cpp-python
```

### 6. Download a Model

```powershell
# Download a recommended model
python ai_stack\model_manager_cli.py recommend

# Download Llama-2-7B (recommended for beginners)
python ai_stack\model_manager_cli.py download llama-2-7b-chat --quant Q4_K_M

# Or download Mistral-7B
python ai_stack\model_manager_cli.py download mistral-7b-instruct --quant Q4_K_M
```

### 7. Configure Windows Defender

Windows Defender may flag Python processes as suspicious. To prevent this:

```powershell
# Run as Administrator
.\scripts\windows-defender-setup.ps1
```

Or manually add exclusions:
1. Open **Windows Security** → **Virus & threat protection** → **Manage settings**
2. Scroll to **Exclusions** → **Add or remove exclusions**
3. Add these exclusions:
   - Folder: `C:\Users\<YourName>\Documents\B0LK13v2`
   - Process: `python.exe`
   - Process: `ollama.exe`

### 8. Start the Local AI Stack

```powershell
# Using the start script
.\start-local-ai-stack.ps1

# Or manually
python ai_stack\llm_server_optimized.py --model-path .\models
python ai_stack\embed_server.py
python ai_stack\vector_server_optimized.py
```

### 9. Install Obsidian Plugin

See Step 3 in Quick Start above.

## Troubleshooting

### PowerShell Execution Policy Error

**Error**: `cannot be loaded because running scripts is disabled`

**Solution**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Python Not Found

**Error**: `'python' is not recognized`

**Solution**:
1. Reinstall Python with "Add to PATH" checked
2. Or use `py` instead of `python`

### CUDA/GPU Issues

**Error**: `CUDA out of memory` or `CUDA not available`

**Solutions**:
1. Use CPU-only mode: `--cpu-only` flag
2. Reduce context size in `config.yaml`
3. Use a smaller model (Phi-2 instead of Llama-2-13B)
4. Run the GPU-safe server: `python ai_stack\llm_server_gpu_safe.py`

### Windows Defender Blocking

**Symptoms**: Slow startup, "Suspicious process" warnings

**Solution**: Run the Defender setup script:
```powershell
.\scripts\windows-defender-setup.ps1
```

### Port Already in Use

**Error**: `Address already in use`

**Solution**:
```powershell
# Find and kill processes using ports 8000-8002
Get-NetTCPConnection -LocalPort 8000,8001,8002 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

### Model Download Fails

**Error**: Download interrupted or fails

**Solutions**:
1. Check internet connection
2. Try manual download from HuggingFace
3. Use wget or curl as alternative:
   ```powershell
   # Install wget via chocolatey
   choco install wget
   
   # Download model
   wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf -O models\llama-2-7b-chat.Q4_K_M.gguf
   ```

## Connecting Obsidian to Local AI

### Method 1: Using Ollama (Recommended for Beginners)

1. Install Ollama from https://ollama.com
2. Pull a model:
   ```powershell
   ollama pull llama3.2
   ```
3. In Obsidian PKM Agent settings:
   - Set LLM Endpoint to: `http://127.0.0.1:11434/v1`
   - Set Model to: `llama3.2`

### Method 2: Using Custom Local Stack

1. Start the custom servers (see Step 8)
2. In Obsidian PKM Agent settings:
   - LLM Endpoint: `http://127.0.0.1:8000`
   - Embeddings Endpoint: `http://127.0.0.1:8001`
   - Vector DB Endpoint: `http://127.0.0.1:8002`

## Performance Optimization

### For Low-End Systems (8GB RAM)

Use these settings in `config.yaml`:
```yaml
performance:
  context_size: 2048
  gpu_layers: 0  # CPU only
  threads: 4

models:
  default:
    path: "./models/phi-2.Q4_K_M.gguf"  # Smaller model
```

### For High-End Systems (16GB+ RAM, GPU)

```yaml
performance:
  context_size: 8192
  gpu_layers: -1  # Auto-detect
  threads: 8

models:
  default:
    path: "./models/llama-2-13b-chat.Q4_K_M.gguf"
```

## Updating

To update to the latest version:

```powershell
# Navigate to project
cd "$env:USERPROFILE\Documents\B0LK13v2\obsidian-ai-agent"

# Pull latest changes (if using git)
git pull

# Update dependencies
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt --upgrade

# Update Obsidian plugin through Obsidian settings
```

## Getting Help

If you encounter issues:

1. Check the logs in the terminal where you started the servers
2. Open Obsidian Developer Tools: `Ctrl + Shift + I`
3. Check the Console tab for errors
4. File an issue on GitHub with:
   - Error message
   - Windows version
   - Python version (`python --version`)
   - GPU model (if applicable)

## Post-Installation Checklist

- [ ] Python installed and in PATH
- [ ] Virtual environment created and activated
- [ ] Dependencies installed without errors
- [ ] Model downloaded successfully
- [ ] Windows Defender exclusions added
- [ ] Local AI stack starts without errors
- [ ] Obsidian plugin installed and enabled
- [ ] Connection test successful
- [ ] Can send a test message in chat

---

**Next Steps**: See the README for how to use the AI Agent features.
