# Obsidian Agent - Installation Guide

Complete installation instructions for the Obsidian Agent plugin.

> 💡 **Windows Users:** See the detailed [Windows Installation Guide](WINDOWS_INSTALL_GUIDE.md) for step-by-step instructions specific to Windows 10/11.

## 📋 Prerequisites

- **Obsidian**: Version 0.15.0 or higher
- **Operating System**: Windows, macOS, or Linux
- **Internet Connection**: Required for cloud AI providers (OpenAI, Anthropic)
- **API Key**: From your chosen AI provider

## 🚀 Installation Methods

### Method 1: Manual Installation (Recommended)

#### Step 1: Download the Plugin

1. Go to the [Releases page](https://github.com/B0LK13/obsidian-agent/releases)
2. Download `obsidian-agent-1.0.0.zip`
3. Save it to a temporary location (e.g., Downloads folder)

#### Step 2: Extract to Plugins Folder

**Windows:**
```powershell
# Navigate to your vault's plugins folder
# Replace <YourVault> with your vault name
cd "%USERPROFILE%\Documents\Obsidian Vaults\<YourVault>\.obsidian\plugins"

# Extract the zip file
Expand-Archive -Path "~\Downloads\obsidian-agent-1.0.0.zip" -DestinationPath "obsidian-agent"
```

**macOS:**
```bash
# Navigate to your vault's plugins folder
# Replace <YourVault> with your vault name
cd ~/Documents/Obsidian\ Vaults/<YourVault>/.obsidian/plugins

# Extract the zip file
unzip ~/Downloads/obsidian-agent-1.0.0.zip -d obsidian-agent
```

**Linux:**
```bash
# Navigate to your vault's plugins folder
cd ~/Obsidian\ Vaults/<YourVault>/.obsidian/plugins

# Extract the zip file
unzip ~/Downloads/obsidian-agent-1.0.0.zip -d obsidian-agent
```

#### Step 3: Manual Extraction (GUI)

1. Close Obsidian completely
2. Navigate to your vault folder
3. Open `.obsidian/plugins/` (create if doesn't exist)
4. Create new folder named `obsidian-agent`
5. Extract `obsidian-agent-1.0.0.zip` into this folder
6. Verify these files are present:
   - `main.js`
   - `manifest.json`
   - `styles.css`
   - `styles-enhanced.css`

#### Step 4: Enable the Plugin

1. Open Obsidian
2. Go to **Settings** → **Community Plugins**
3. Click **Turn on community plugins** if not already enabled
4. Find "Obsidian Agent" in the list
5. Toggle the switch to enable it

### Method 2: Development Installation

For developers who want to modify the plugin:

#### Step 1: Clone Repository

```bash
cd <YourVault>/.obsidian/plugins/
git clone https://github.com/B0LK13/obsidian-agent.git
cd obsidian-agent
```

#### Step 2: Install Dependencies

```bash
npm install
```

#### Step 3: Build the Plugin

```bash
# Production build
npm run build

# Or development build with hot reload
npm run dev
```

#### Step 4: Enable in Obsidian

1. Open Obsidian
2. Go to **Settings** → **Community Plugins**
3. Enable "Obsidian Agent"

### Method 3: BRAT (Beta Reviewers Auto-update Tool)

If you have the BRAT plugin installed:

1. Open Command Palette (`Ctrl/Cmd + P`)
2. Type "BRAT: Add a beta plugin for testing"
3. Enter: `https://github.com/B0LK13/obsidian-agent`
4. Click "Add Plugin"
5. Enable the plugin in Community Plugins settings

## ⚙️ Initial Configuration

> 💡 **Windows Users:** Having trouble? Check the [Windows Installation Guide](WINDOWS_INSTALL_GUIDE.md) for detailed troubleshooting.

### Step 1: Open Settings

1. Go to **Settings** → **Obsidian Agent**

### Step 2: Select AI Provider

Choose your preferred AI provider:

#### Option A: OpenAI
1. Select "OpenAI" from the dropdown
2. Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
3. Paste the key in the "API Key" field
4. Recommended model: `gpt-4` or `gpt-3.5-turbo`

#### Option B: Anthropic
1. Select "Anthropic" from the dropdown
2. Get your API key from [Anthropic Console](https://console.anthropic.com/)
3. Paste the key in the "API Key" field
4. Recommended model: `claude-3-opus-20240229`

#### Option C: Ollama (Local AI)
1. Select "Ollama" from the dropdown
2. Install Ollama from [ollama.com](https://ollama.com)
3. Run: `ollama pull llama2` (or your preferred model)
4. Start Ollama server: `ollama serve`
5. Set URL to: `http://localhost:11434`
6. Enter model name: `llama2`

#### Option D: Custom API
1. Select "Custom" from the dropdown
2. Enter your API endpoint URL
3. Add your API key
4. Specify the model name

### Step 3: Test Connection

1. Click the "Test Connection" button
2. Wait for the success message
3. If it fails, check your API key and internet connection

### Step 4: Configure Preferences

Adjust these settings to your preference:

| Setting | Recommended Value | Description |
|---------|-------------------|-------------|
| Temperature | 0.7 | Balanced creativity |
| Max Tokens | 2000 | Response length limit |
| Enable Context Awareness | ON | Include note context |
| Enable Token Tracking | ON | Monitor usage |
| Enable Conversation Persistence | ON | Save chat history |

## 🎨 UI Configuration (Optional)

### Enable Enhanced UI

The 2025 Chat UI is enabled by default. To customize:

1. Go to **Settings** → **Appearance**
2. The enhanced styles will automatically apply
3. For high contrast mode, use the `.oa-high-contrast` CSS class

### Accessibility Settings

1. **Reduced Motion**: Respects your OS settings automatically
2. **High Contrast**: Add to your custom CSS:
   ```css
   body { --oa-high-contrast: true; }
   ```

## ✅ Verification

### Test the Plugin

1. Open any note in Obsidian
2. Press `Ctrl/Cmd + P` for Command Palette
3. Type "Ask AI Agent"
4. Enter a test question: "What is this note about?"
5. The AI should respond with the enhanced chat UI

### Verify Files

Your plugin folder should contain:
```
<Vault>/.obsidian/plugins/obsidian-agent/
├── main.js              ✅
├── manifest.json        ✅
├── styles.css           ✅
├── styles-enhanced.css  ✅
├── README.md            ✅
├── LICENSE              ✅
├── CHANGELOG.md         ✅
└── versions.json        ✅
```

## 🔄 Updating the Plugin

### Manual Update

1. Download the latest release
2. Close Obsidian
3. Replace the plugin folder contents with new files
4. Restart Obsidian

### Using Git (Development)

```bash
cd <Vault>/.obsidian/plugins/obsidian-agent
git pull origin main
npm install
npm run build
```

## 🐛 Troubleshooting

### Windows Defender False Positive (Windows Only)

**Problem**: Windows Defender flags the plugin or Python processes as suspicious, causing slow startup or quarantine

**Symptoms**:
- Slow plugin startup (>30 seconds)
- Windows Defender notification about "Suspicious process"
- Process gets quarantined in rare cases
- AI features not working properly

**Solutions**:

#### Option 1: Add Exclusions via PowerShell (Recommended)

Run PowerShell as Administrator and execute:

```powershell
# Add Python.exe to Windows Defender exclusions
Add-MpPreference -ExclusionProcess "python.exe"

# Add Obsidian vault plugins folder to exclusions
# Replace <YourVault> with your actual vault name
Add-MpPreference -ExclusionPath "$env:USERPROFILE\Documents\Obsidian Vaults\<YourVault>\.obsidian\plugins"

# Add the specific plugin folder
Add-MpPreference -ExclusionPath "$env:USERPROFILE\Documents\Obsidian Vaults\<YourVault>\.obsidian\plugins\obsidian-agent"

# Verify exclusions were added
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath
Get-MpPreference | Select-Object -ExpandProperty ExclusionProcess
```

#### Option 2: Add Exclusions via Windows Security GUI

1. Open **Windows Security** (Windows key → type "Windows Security")
2. Click **Virus & threat protection**
3. Scroll down to **Virus & threat protection settings**
4. Click **Manage settings**
5. Scroll down to **Exclusions**
6. Click **Add or remove exclusions**
7. Click **Add an exclusion** → **Process**
8. Type: `python.exe` and click **Add**
9. Click **Add an exclusion** → **Folder**
10. Browse to: `%USERPROFILE%\Documents\Obsidian Vaults\<YourVault>\.obsidian\plugins\obsidian-agent`
11. Click **Select Folder**

#### Option 3: Automated Setup Script

Create a file named `setup-defender-exclusions.ps1` with the following content:

```powershell
# Obsidian Agent - Windows Defender Exclusion Setup Script
# Run as Administrator

param(
    [Parameter(Mandatory=$true)]
    [string]$VaultPath
)

Write-Host "Setting up Windows Defender exclusions for Obsidian Agent..." -ForegroundColor Green

# Add Python process exclusion
try {
    Add-MpPreference -ExclusionProcess "python.exe" -ErrorAction Stop
    Write-Host "✓ Added python.exe to process exclusions" -ForegroundColor Green
} catch {
    Write-Host "⚠ Could not add python.exe exclusion: $_" -ForegroundColor Yellow
}

# Add plugin folder exclusion
$pluginPath = Join-Path -Path $VaultPath -ChildPath ".obsidian\plugins\obsidian-agent"
if (Test-Path $pluginPath) {
    try {
        Add-MpPreference -ExclusionPath $pluginPath -ErrorAction Stop
        Write-Host "✓ Added $pluginPath to path exclusions" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Could not add path exclusion: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠ Plugin path not found: $pluginPath" -ForegroundColor Yellow
}

Write-Host "`nExclusions added successfully!" -ForegroundColor Green
Write-Host "Please restart Obsidian for changes to take effect." -ForegroundColor Cyan
```

Run it with:
```powershell
# Run as Administrator
.\setup-defender-exclusions.ps1 -VaultPath "C:\Users\YourName\Documents\Obsidian Vaults\YourVault"
```

#### Why This Happens

Windows Defender may flag Python processes spawned by the AI stack as suspicious due to:
- Behavioral heuristics detecting process spawning
- Network activity from API calls
- Dynamic code execution patterns
- Unsigned executables

#### Notes

- These exclusions are **safe** and only affect the specific plugin folder and Python processes
- Exclusions do not disable Windows Defender globally
- The plugin does not contain malicious code (open source: verify on GitHub)
- Consider these exclusions only if you trust the plugin source

#### Alternative: Use Cloud AI Providers

If you cannot modify Windows Defender settings:
- Use cloud-based AI providers (OpenAI, Anthropic) instead of local models
- This avoids Python process spawning entirely
- Configure in Settings → Obsidian Agent → API Provider

### Plugin Not Appearing

**Problem**: Plugin doesn't show in Community Plugins list

**Solutions**:
1. Check folder name is exactly `obsidian-agent`
2. Verify `manifest.json` exists
3. Restart Obsidian completely
4. Check Obsidian version is 0.15.0+

### Build Errors (Development)

**Problem**: `npm run build` fails

**Solutions**:
```bash
# Clear node_modules and reinstall
rm -rf node_modules
npm install
npm run build
```

### API Connection Failed

**Problem**: "Connection failed" error

**Solutions**:
1. Verify API key is correct
2. Check internet connection
3. For Ollama: Ensure server is running (`ollama serve`)
4. Check firewall/antivirus settings

### UI Not Loading

**Problem**: Chat UI appears broken

**Solutions**:
1. Check both `styles.css` and `styles-enhanced.css` exist
2. Reload Obsidian (Command Palette → "Reload app without saving")
3. Check browser console for errors (Ctrl+Shift+I)

### Performance Issues

**Problem**: Plugin is slow

**Solutions**:
1. Reduce max tokens setting
2. Disable conversation persistence if not needed
3. Clear cache: Settings → Obsidian Agent → Clear Cache
4. Use local Ollama instead of cloud APIs

## 🗑️ Uninstallation

### Method 1: Via Obsidian

1. Go to **Settings** → **Community Plugins**
2. Find "Obsidian Agent"
3. Toggle off to disable
4. Click the trash icon to delete

### Method 2: Manual

```bash
# Navigate to plugins folder
cd <Vault>/.obsidian/plugins/

# Delete the plugin folder
rm -rf obsidian-agent
```

### Remove Configuration

Plugin settings are stored in Obsidian's data. To completely remove:

1. Disable the plugin first
2. Close Obsidian
3. Delete `<Vault>/.obsidian/plugins/obsidian-agent/`
4. Settings will be removed automatically

## 📞 Support

If you encounter issues:

1. Check [Troubleshooting](#-troubleshooting) section
2. Review [GitHub Issues](https://github.com/B0LK13/obsidian-agent/issues)
3. Create a new issue with:
   - Obsidian version
   - Plugin version
   - Error messages
   - Steps to reproduce

## 🎉 Next Steps

After installation:

1. Try the **Quick Summary** command on a note
2. Experiment with **AI Profiles** for different tasks
3. Explore **Conversation Persistence** features
4. Check out the **Enhanced UI** features

---

**Need Help?** Visit our [GitHub Discussions](https://github.com/B0LK13/obsidian-agent/discussions)

**Version**: 1.0.0  
**Last Updated**: 2026-01-29
