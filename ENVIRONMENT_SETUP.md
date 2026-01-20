# Environment Setup Guide

This guide explains how to set up environment variables for the Obsidian Agent project.

## Quick Start

### Windows (PowerShell - Recommended)
```powershell
.\setup-env.ps1
```

### Windows (Command Prompt)
```cmd
setup-env.bat
```

### Linux/macOS
```bash
chmod +x setup-env.sh
./setup-env.sh
```

## Setup Modes

All scripts support multiple setup modes:

### 1. Interactive Setup (Recommended)
Walks you through configuration with prompts and default values:
- Vault path configuration
- Database location
- AI provider and API keys
- Vector store settings
- Creates `.env` file automatically

### 2. Template Mode
Creates `.env` from `.env.example` template:
- Copy the template file
- Manually edit values
- Good for advanced users

### 3. System Environment Variables (PowerShell/Bash only)
Sets persistent environment variables:
- Variables persist across sessions
- Stored in user profile
- Requires terminal restart

## Environment Variables Reference

### Essential Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OBSIDIAN_VAULT_PATH` | Path to your Obsidian vault | `C:\Users\...\Documents\MyVault` |
| `OBSIDIAN_DATABASE__PATH` | SQLite database location | `%LOCALAPPDATA%\obsidian-agent\vault.db` |
| `AI_PROVIDER` | AI service provider | `openai`, `anthropic`, `ollama` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-...` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OBSIDIAN_VECTOR_STORE__EMBEDDING_MODEL` | Embedding model | `all-MiniLM-L6-v2` |
| `OBSIDIAN_SEARCH__DEFAULT_LIMIT` | Default search results | `10` |
| `AI_MODEL` | AI model to use | `gpt-4` |
| `AI_TEMPERATURE` | Response creativity | `0.7` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `CACHE_ENABLED` | Enable response caching | `true` |

### Full Configuration

See `.env.example` for all available variables with detailed descriptions.

## Platform-Specific Notes

### Windows

#### Using PowerShell (Recommended)
PowerShell script provides the best experience with:
- Colored output
- Secure password input
- Interactive prompts
- Option to persist variables

**Run as:**
```powershell
.\setup-env.ps1
```

#### Using Command Prompt
Basic functionality for creating `.env` or setting system variables:
```cmd
setup-env.bat
```

#### Path Examples
- Vault: `C:\Users\YourName\Documents\ObsidianVault`
- Database: `%LOCALAPPDATA%\obsidian-agent\vault.db`
- ChromaDB: `%LOCALAPPDATA%\obsidian-agent\chroma`

### Linux/macOS

#### Make Script Executable
```bash
chmod +x setup-env.sh
```

#### Run Setup
```bash
./setup-env.sh
```

#### Path Examples
- Vault: `~/Documents/ObsidianVault`
- Database: `~/.local/share/obsidian-agent/vault.db`
- ChromaDB: `~/.local/share/obsidian-agent/chroma`

#### Shell Configuration
The script can automatically add variables to:
- `~/.bashrc` (Bash)
- `~/.zshrc` (Zsh)

## Manual Setup

If you prefer to set up manually:

### 1. Copy Template
```bash
cp .env.example .env
```

### 2. Edit .env
Open `.env` in your editor and fill in values:
```env
OBSIDIAN_VAULT_PATH=/path/to/your/vault
OPENAI_API_KEY=your-api-key-here
AI_MODEL=gpt-4
```

### 3. Set Environment Variables (Optional)

**PowerShell:**
```powershell
$env:OBSIDIAN_VAULT_PATH = "C:\path\to\vault"
```

**Bash/Zsh:**
```bash
export OBSIDIAN_VAULT_PATH="/path/to/vault"
```

**Windows System:**
```cmd
setx OBSIDIAN_VAULT_PATH "C:\path\to\vault"
```

## Python Backend Setup

After setting environment variables, install Python backend:

```bash
cd python_backend
poetry install

# Or with pip
pip install -e .
```

### Verify Setup
```bash
obsidian-agent config --show
```

## TypeScript Plugin Setup

Install and build TypeScript plugin:

```bash
npm install
npm run build
```

## Verification

### Check Environment Variables

**PowerShell:**
```powershell
Get-ChildItem Env: | Where-Object { $_.Name -like "OBSIDIAN*" -or $_.Name -like "AI*" }
```

**Bash/Zsh:**
```bash
env | grep -E "OBSIDIAN|AI_"
```

### Test Python Backend
```bash
cd python_backend
obsidian-agent --version
obsidian-agent config --show
```

### Test TypeScript Build
```bash
npm run build
# Should complete without errors
```

## Troubleshooting

### "Environment variable not found"
- **Windows**: Restart terminal after using `setx`
- **Linux/Mac**: Run `source ~/.bashrc` or restart terminal

### "Permission denied" (Linux/Mac)
```bash
chmod +x setup-env.sh
```

### ".env file not loading"
- Ensure `.env` is in project root
- Check file encoding (should be UTF-8)
- Verify no syntax errors in `.env`

### "API key invalid"
- Check for extra spaces in API key
- Ensure key is from correct provider
- Verify key has required permissions

### Python backend not finding config
- Check `OBSIDIAN_VAULT_PATH` is set correctly
- Verify paths use correct separators for your OS
- Try absolute paths instead of relative

## Security Notes

### API Keys
- **Never commit** `.env` to version control
- `.env` is in `.gitignore` by default
- Use environment variables for production
- Rotate keys regularly

### File Permissions
Set restrictive permissions on `.env`:

**Linux/Mac:**
```bash
chmod 600 .env
```

**Windows:**
Use File Properties > Security to restrict access

## Integration with IDEs

### VS Code
Install "DotENV" extension for syntax highlighting.

Add to `.vscode/settings.json`:
```json
{
  "files.associations": {
    ".env*": "dotenv"
  }
}
```

### JetBrains IDEs
Environment variables automatically loaded from `.env` when using EnvFile plugin.

## Advanced Configuration

### Multiple Environments
Create environment-specific files:
- `.env.development`
- `.env.production`
- `.env.test`

Load with:
```bash
export $(cat .env.development | xargs)
```

### Docker
Use `.env` with Docker Compose:
```yaml
version: '3'
services:
  backend:
    env_file: .env
```

## Next Steps

After setup:
1. ✅ Verify all variables are set
2. ✅ Install dependencies
3. ✅ Build the project
4. 📖 Read [DEVELOPER.md](DEVELOPER.md)
5. 🚀 Start developing!

## Support

For issues or questions:
- Check [DEVELOPER.md](DEVELOPER.md)
- Review [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)
- Open an issue on GitHub
