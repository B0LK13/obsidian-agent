# Obsidian AI CLI Tools Setup Guide

## ✅ Completed Setup

The AI CLI tools have been integrated into Obsidian's Terminal plugin!

## 🎯 Available Commands in Obsidian Terminal

When you open a terminal in Obsidian, you'll have access to:

### 1. **opencode** (or **oc**) - GitHub Copilot CLI
```powershell
opencode "how do I list files recursively"
opencode -Explain "docker ps -a"
oc "create a git branch"
```

### 2. **codex** - OpenAI Codex CLI
```powershell
codex "write a function to sort an array"
codex "explain this error message"
```

### 3. **gemini** - Google Gemini CLI
```powershell
gemini "explain quantum computing"
gemini "write a poem about code"
```

---

## 🚀 How to Use

### Opening Terminal in Obsidian

1. **Command Palette**: Press `Ctrl+P` → Type "Terminal" → Select "Terminal: Open terminal"
2. **Context Menu**: Right-click in any note → "Open terminal here"
3. **Ribbon Icon**: Click the terminal icon in the left sidebar

### First Time Usage

When the terminal opens, you'll see:
```
╔════════════════════════════════════════════════════════════╗
║          AI CLI Tools for Obsidian Terminal                ║
╚════════════════════════════════════════════════════════════╝

✅ AI CLI Tools loaded successfully

Available commands:
  opencode (oc) - GitHub Copilot CLI
  codex         - OpenAI Codex CLI
  gemini        - Google Gemini CLI

Examples:
  opencode "how do I list files recursively"
  codex "write a Python function to sort"
  gemini "explain quantum computing"

📂 Working directory: C:\Users\Admin\Documents\B0LK13v2\B0LK13v2
```

---

## 📋 Configuration Details

### Terminal Settings Changed
- **Shell**: Changed from CMD to PowerShell
- **Startup Script**: Auto-loads AI CLI Tools module
- **Working Directory**: Automatically set to your vault folder

### Files Created

1. **PowerShell Module**: `C:\Users\Admin\Documents\WindowsPowerShell\Modules\AICLITools\AICLITools.psm1`
   - Core functionality for all AI CLI commands
   - Auto-loads in all PowerShell sessions

2. **Startup Script**: `C:\Users\Admin\Documents\WindowsPowerShell\ObsidianTerminal.ps1`
   - Runs when Obsidian Terminal opens
   - Shows welcome message and available commands

3. **Batch Files**: `C:\Users\Admin\AppData\Roaming\npm\`
   - `opencode.cmd` - For CMD compatibility
   - `codex.cmd` - Already installed
   - `gemini.cmd` - Already installed

---

## 🔧 Troubleshooting

### Commands Not Found

If you see "command not recognized":

1. **Close and reopen** Obsidian Terminal
2. **Manually import module**:
   ```powershell
   Import-Module AICLITools
   ```

### Terminal Opens CMD Instead of PowerShell

1. Restart Obsidian completely
2. Check: `.obsidian/plugins/terminal/data.json`
3. Should show: `"executable": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"`

### Module Not Loading

Check if module exists:
```powershell
Get-Module -ListAvailable AICLITools
```

If not found, reinstall:
```powershell
# Re-import the module
Import-Module C:\Users\Admin\Documents\WindowsPowerShell\Modules\AICLITools\AICLITools.psm1
```

---

## 🔐 API Keys Required

### For Codex (OpenAI)
```powershell
$env:OPENAI_API_KEY = "your-key-here"
# Or permanently:
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "your-key", "User")
```

### For Gemini (Google)
```powershell
$env:GOOGLE_API_KEY = "your-key-here"
# Or permanently:
[Environment]::SetEnvironmentVariable("GOOGLE_API_KEY", "your-key", "User")
```

### For GitHub Copilot
Already authenticated via `gh auth login`

---

## 📖 Usage Examples

### GitHub Copilot (opencode)

**Get command suggestions**:
```powershell
opencode "list all Python files modified in last week"
opencode "find and replace text in all files"
```

**Explain commands**:
```powershell
opencode -Explain "git rebase -i HEAD~3"
opencode -Explain "docker-compose up -d"
```

### OpenAI Codex

**Code generation**:
```powershell
codex "write a Python function to calculate fibonacci"
codex "create a React component for a login form"
```

**Code explanation**:
```powershell
codex "explain what async/await does"
```

### Google Gemini

**General queries**:
```powershell
gemini "explain the observer pattern"
gemini "what are the benefits of functional programming"
```

**Creative writing**:
```powershell
gemini "write a haiku about debugging"
```

---

## 🎨 PowerShell Features

All commands support PowerShell features:

**Tab completion**:
```powershell
open<Tab>  # Completes to opencode
```

**Help documentation**:
```powershell
Get-Help Open-Code
Get-Help Invoke-Codex -Detailed
```

**Pipeline support**:
```powershell
"how do I list files" | opencode
```

---

## 🔄 Updates and Maintenance

### Update Commands

If you update the npm packages:
```powershell
npm update -g @openai/codex
npm update -g @google/gemini-cli
```

### Update PowerShell Module

Edit the module directly:
```powershell
notepad $env:USERPROFILE\Documents\WindowsPowerShell\Modules\AICLITools\AICLITools.psm1
```

Then reload:
```powershell
Import-Module AICLITools -Force
```

---

## 📊 Testing

Verify everything works:

```powershell
# Test module loaded
Get-Module AICLITools

# Test commands available
Get-Command opencode, codex, gemini

# Test actual execution
opencode "test"
codex --version
gemini --version
```

---

## 🌟 Benefits

### Why This Setup?

1. **Integrated**: Works directly in Obsidian Terminal
2. **Persistent**: Commands available in all PowerShell sessions
3. **Aliases**: Short commands (`oc` instead of `opencode`)
4. **Auto-load**: No manual setup needed each time
5. **Native**: Uses PowerShell functions, not external scripts
6. **Help**: Full PowerShell help documentation
7. **Cross-compatible**: Works in regular PowerShell too

### Comparison: CMD vs PowerShell

| Feature | CMD (.cmd files) | PowerShell (Module) |
|---------|------------------|---------------------|
| Auto-load | ❌ Requires PATH | ✅ Module system |
| Tab completion | ⚠️ Basic | ✅ Advanced |
| Help system | ❌ None | ✅ Full Get-Help |
| Aliases | ❌ No | ✅ Multiple aliases |
| Parameters | ⚠️ Limited | ✅ Rich parameters |
| Error handling | ⚠️ Basic | ✅ Try/Catch |

---

## 📂 File Locations Reference

```
C:\Users\Admin\
├── Documents\
│   └── WindowsPowerShell\
│       ├── Modules\
│       │   └── AICLITools\
│       │       ├── AICLITools.psm1     (Main module)
│       │       └── AICLITools.psd1     (Manifest)
│       ├── ObsidianTerminal.ps1        (Startup script)
│       └── Microsoft.PowerShell_profile.ps1  (Profile)
│
└── AppData\
    └── Roaming\
        └── npm\
            ├── opencode.cmd            (CMD wrapper)
            ├── codex.cmd               (Codex CMD)
            └── gemini.cmd              (Gemini CMD)
```

---

## 🎯 Next Steps

1. ✅ Open Obsidian Terminal
2. ✅ Verify welcome message appears
3. ✅ Test each command
4. ✅ Add API keys if needed
5. ✅ Start using AI assistance!

---

## 📝 Notes

- **Restart Required**: Close and reopen Obsidian for terminal changes
- **Backward Compatible**: CMD versions still work outside Obsidian
- **Module Auto-loads**: In all PowerShell sessions, not just Obsidian
- **Customizable**: Edit startup script for different welcome message

---

**Created**: 2026-01-20  
**Status**: ✅ Fully Configured  
**Version**: 1.0.0  
**Author**: B0LK13
