# Windows Installation Guide - Obsidian Agent

**Complete step-by-step guide for Windows users**

This guide addresses common Windows-specific issues and provides detailed installation steps with troubleshooting.

---

## 📋 Prerequisites for Windows

Before installing Obsidian Agent, ensure you have:

- ✅ **Windows 10** or **Windows 11**
- ✅ **Obsidian** version 0.15.0 or higher
- ✅ **PowerShell** 5.1 or higher (pre-installed on Windows 10/11)
- ✅ **Internet connection** for cloud AI providers
- ✅ **Administrator access** (for some setup steps)

---

## 🚀 Quick Install (Recommended)

### Step 1: Download the Plugin

1. Visit [Releases](https://github.com/B0LK13/obsidian-agent/releases)
2. Download `obsidian-agent-1.0.0.zip`
3. The file will be saved to your Downloads folder (`C:\Users\YourName\Downloads`)

### Step 2: Locate Your Obsidian Vault

Your Obsidian vault is typically located at:
```
C:\Users\YourName\Documents\Obsidian Vaults\YourVaultName
```

**Don't know where your vault is?**
1. Open Obsidian
2. Open any note
3. Right-click in the note
4. Select "Reveal file in system explorer"
5. Go up folders until you see `.obsidian` folder

### Step 3: Extract the Plugin

**Option A: Using Windows Explorer (Easiest)**

1. Open File Explorer (`Win + E`)
2. Navigate to your vault: `C:\Users\YourName\Documents\Obsidian Vaults\YourVaultName`
3. Open the `.obsidian` folder (you may need to show hidden files)
4. Open (or create) the `plugins` folder
5. Create a new folder named `obsidian-agent`
6. Go to your Downloads folder
7. Right-click `obsidian-agent-1.0.0.zip`
8. Select "Extract All..."
9. Browse to `C:\Users\YourName\Documents\Obsidian Vaults\YourVaultName\.obsidian\plugins\obsidian-agent`
10. Click "Extract"

**Option B: Using PowerShell (Advanced)**

1. Press `Win + X` and select "Windows PowerShell" or "Terminal"
2. Run these commands (replace `YourVaultName` with your actual vault name):

```powershell
# Set your vault name
$vaultName = "YourVaultName"

# Navigate to plugins folder
cd "$env:USERPROFILE\Documents\Obsidian Vaults\$vaultName\.obsidian\plugins"

# Create plugin folder if it doesn't exist
New-Item -ItemType Directory -Force -Path "obsidian-agent"

# Extract the downloaded zip
Expand-Archive -Path "$env:USERPROFILE\Downloads\obsidian-agent-1.0.0.zip" -DestinationPath "obsidian-agent" -Force
```

### Step 4: Enable the Plugin in Obsidian

1. **Close Obsidian completely** (important!)
2. **Reopen Obsidian**
3. Go to `Settings` (gear icon) → `Community plugins`
4. If prompted, click "Turn on community plugins"
5. Find "Obsidian Agent" in the list
6. Toggle it ON (enable it)
7. You should see the plugin activated!

---

## 🔧 Windows-Specific Setup

### PowerShell Execution Policy

If you encounter "script execution disabled" errors when running PowerShell scripts:

```powershell
# Run PowerShell as Administrator
# Right-click PowerShell → "Run as Administrator"

# Check current policy
Get-ExecutionPolicy

# If it says "Restricted", set it to RemoteSigned
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# Confirm the change
Get-ExecutionPolicy
```

### Show Hidden Files and Folders

To see the `.obsidian` folder:

1. Open File Explorer
2. Click the `View` tab
3. Check the box for "Hidden items"

**Or via PowerShell:**
```powershell
# Show hidden files
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" -Name "Hidden" -Value 1

# Restart File Explorer
Stop-Process -Name explorer -Force
```

### Windows Defender Setup (Critical!)

**Windows Defender may flag the plugin as suspicious.** Run this automated setup:

```powershell
# Download and run the setup script
# Right-click PowerShell → "Run as Administrator"

cd "$env:USERPROFILE\Documents\Obsidian Vaults\YourVaultName\.obsidian\plugins\obsidian-agent"
.\scripts\setup-defender-exclusions.ps1
```

**Manual Windows Defender exclusions:**

1. Press `Win` key, type "Windows Security"
2. Click "Virus & threat protection"
3. Click "Manage settings" under "Virus & threat protection settings"
4. Scroll to "Exclusions" → Click "Add or remove exclusions"
5. Click "Add an exclusion" → "Process"
6. Type: `python.exe` → Add
7. Click "Add an exclusion" → "Folder"
8. Browse to: `C:\Users\YourName\Documents\Obsidian Vaults\YourVaultName\.obsidian\plugins\obsidian-agent`
9. Select the folder → Done

---

## ⚙️ Configuration

### Configure AI Provider

1. Open Obsidian
2. Go to `Settings` → `Obsidian Agent`
3. Choose your AI provider:

#### For OpenAI:
1. Select "OpenAI" from dropdown
2. Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)
3. Paste key in "API Key" field
4. Select model (recommended: `gpt-4` or `gpt-3.5-turbo`)
5. Click "Test Connection"

#### For Anthropic:
1. Select "Anthropic" from dropdown
2. Get API key from [Anthropic Console](https://console.anthropic.com/)
3. Paste key in "API Key" field
4. Select model (recommended: `claude-3-opus-20240229`)
5. Click "Test Connection"

#### For Ollama (Local AI - No Internet Required):

**Install Ollama:**
1. Download from [ollama.com](https://ollama.com/download/windows)
2. Run the installer `OllamaSetup.exe`
3. Follow installation wizard

**Download a model:**
```powershell
# Open PowerShell
# Download Llama 2 (recommended for beginners)
ollama pull llama2

# Or for better quality (larger download):
ollama pull llama2:13b

# Or for coding tasks:
ollama pull codellama
```

**Configure in Obsidian Agent:**
1. Select "Ollama" from dropdown
2. Set URL to: `http://localhost:11434`
3. Enter model name: `llama2` (or whatever you downloaded)
4. Click "Test Connection"

**Start Ollama server:**
```powershell
# Ollama typically starts automatically, but if needed:
ollama serve
```

---

## 🐛 Troubleshooting

### Issue: Plugin Won't Load

**Symptoms:** Plugin doesn't appear in Community Plugins list

**Solutions:**
1. ✅ Verify folder name is exactly `obsidian-agent` (no spaces, correct case)
2. ✅ Check that `manifest.json` exists in the plugin folder
3. ✅ Restart Obsidian completely (close all windows)
4. ✅ Check Obsidian version is 0.15.0 or higher

### Issue: "PowerShell Script Cannot Be Loaded"

**Symptoms:** Error when running PowerShell scripts

**Solution:**
```powershell
# Run as Administrator
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: Cannot See `.obsidian` Folder

**Symptoms:** Folder appears to be missing

**Solution:**
Enable hidden files in File Explorer:
- Press `Alt` key in File Explorer
- Go to `Tools` → `Folder Options`
- Click `View` tab
- Select "Show hidden files, folders, and drives"
- Click OK

### Issue: Windows Defender Blocks Plugin

**Symptoms:** Slow startup, warnings from Windows Defender

**Solution:**
Run the automated setup script (as Administrator):
```powershell
cd "$env:USERPROFILE\Documents\Obsidian Vaults\YourVaultName\.obsidian\plugins\obsidian-agent"
.\scripts\setup-defender-exclusions.ps1
```

See [INSTALLATION.md](INSTALLATION.md#windows-defender-false-positive-windows-only) for detailed instructions.

### Issue: API Connection Failed

**Symptoms:** "Connection failed" error when testing

**Solutions:**
1. ✅ Verify API key is correct (no extra spaces)
2. ✅ Check internet connection
3. ✅ For Ollama: Ensure `ollama serve` is running
4. ✅ For Ollama: Check firewall isn't blocking port 11434
5. ✅ Try different model if current one doesn't work

### Issue: Ollama Not Connecting

**Symptoms:** "Failed to connect to Ollama" error

**Solutions:**
```powershell
# Check if Ollama is running
Get-Process ollama -ErrorAction SilentlyContinue

# Start Ollama server
ollama serve

# Test Ollama from command line
ollama list  # Should show downloaded models

# Test Ollama API
curl http://localhost:11434/api/tags
```

### Issue: "Path is too long"

**Symptoms:** Cannot extract files, path too long error

**Solution:**
Enable long paths in Windows:
```powershell
# Run as Administrator
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

Or install to a shorter path:
```
C:\Obsidian\Vaults\MyVault
```

---

## 📹 Video Tutorial

**Coming soon!** A step-by-step video guide for Windows users.

In the meantime, follow this guide or ask for help in [GitHub Discussions](https://github.com/B0LK13/obsidian-agent/discussions).

---

## 🆘 Getting Help

If you're still having issues:

1. **Check existing issues:** [GitHub Issues](https://github.com/B0LK13/obsidian-agent/issues)
2. **Ask in discussions:** [GitHub Discussions](https://github.com/B0LK13/obsidian-agent/discussions)
3. **Create a new issue:** Include:
   - Windows version (e.g., Windows 11)
   - Obsidian version
   - Plugin version
   - Error messages (screenshots helpful!)
   - What you've already tried

---

## ✅ Verification Checklist

After installation, verify everything works:

- [ ] Plugin appears in Community Plugins list
- [ ] Plugin is enabled (toggle is ON)
- [ ] Settings page opens (Settings → Obsidian Agent)
- [ ] API connection test succeeds
- [ ] Command palette shows "Ask AI Agent" commands
- [ ] Test query works in a note

---

## 🎉 Next Steps

Now that installation is complete:

1. Try the **Quick Summary** command on a note
2. Experiment with different **AI providers and models**
3. Customize **system prompts** for your use case
4. Explore **conversation persistence** features
5. Check out the **enhanced chat UI**

Happy note-taking! 🚀

---

**Last Updated:** February 3, 2026  
**Version:** 1.1.0  
**For:** Windows 10/11
