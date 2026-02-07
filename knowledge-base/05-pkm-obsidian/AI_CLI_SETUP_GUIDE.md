# AI CLI Tools Setup Guide

## ✅ Installed Commands

### 1. `opencode` - GitHub Copilot CLI
**Command**: `opencode <query>`

**Examples**:
```cmd
opencode "how do I list files recursively"
opencode "create a Python web server"
opencode explain "docker ps -a"
```

**What it does**:
- Routes to `gh copilot suggest` for general queries
- Use `opencode explain <command>` to explain commands
- Interactive AI assistant for command-line tasks

---

### 2. `codex` - OpenAI Codex CLI
**Command**: `codex <query>`

**Examples**:
```cmd
codex "write a function to sort an array"
codex "explain this error message"
```

**Version**: 0.87.0

**What it does**:
- OpenAI Codex-powered coding assistant
- Generates code snippets and explanations
- Requires OPENAI_API_KEY environment variable

---

### 3. `gemini` - Google Gemini CLI
**Command**: `gemini <query>`

**Examples**:
```cmd
gemini "explain quantum computing"
gemini "write a poem about code"
```

**Version**: 0.24.0

**What it does**:
- Google Gemini AI assistant
- General-purpose AI queries
- Requires GOOGLE_API_KEY environment variable

---

## 🔧 Troubleshooting

### Commands not found in CMD

If you get "command not recognized" in Command Prompt:

1. **Close and reopen** Command Prompt to refresh PATH
2. **Or run this in CMD**:
   ```cmd
   set PATH=%PATH%;C:\Users\Admin\AppData\Roaming\npm
   ```
3. **Permanent fix**: Already done ✅

### Commands work in PowerShell but not CMD

- User PATH was updated, but CMD sessions don't auto-refresh
- Solution: **Close all CMD windows** and open new ones

### API Keys Required

For `codex`:
```cmd
setx OPENAI_API_KEY "your-key-here"
```

For `gemini`:
```cmd
setx GOOGLE_API_KEY "your-key-here"
```

---

## 🚀 Quick Reference

| Command | Purpose | Auth Required |
|---------|---------|---------------|
| `opencode` | GitHub Copilot CLI (suggest/explain commands) | GitHub auth |
| `codex` | OpenAI Codex coding assistant | OpenAI API key |
| `gemini` | Google Gemini AI assistant | Google API key |

---

## 📍 Installation Locations

- **Commands**: `C:\Users\Admin\AppData\Roaming\npm\`
- **Node packages**: Installed globally via npm
- **GitHub CLI**: `C:\Program Files\GitHub CLI\gh.exe`

---

## ✅ Verification

Run these commands to verify setup:

```cmd
opencode "test"
codex --version
gemini --version
gh --version
```

All commands should work without "not recognized" errors.

---

Created: 2026-01-20
Status: ✅ All commands configured and working
