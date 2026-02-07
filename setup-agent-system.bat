@echo off
REM Setup script for Obsidian Agent System with AgentZero and MCP

echo ========================================
echo   Obsidian Agent System Setup
echo ========================================
echo.

REM Check prerequisites
echo Checking prerequisites...

where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js not found. Please install Node.js 18+
    goto :error
)

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found. Please install Python 3.11+
    goto :error
)

echo [OK] Node.js found
node --version
echo [OK] Python found
python --version
echo.

REM Create necessary directories
echo Creating directories...
if not exist ".mcp" mkdir .mcp
if not exist "pkm-agent\data" mkdir pkm-agent\data
if not exist "pkm-agent\.pkm-agent" mkdir pkm-agent\.pkm-agent
echo [OK] Directories created
echo.

REM Install Obsidian MCP Server
echo Installing Obsidian MCP Server...
where npx >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Installing npx...
    npm install -g npx
)

npx obsidian-mcp-server --version >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Obsidian MCP Server already installed
) else (
    echo Installing obsidian-mcp-server globally...
    npm install -g obsidian-mcp-server
    echo [OK] Obsidian MCP Server installed
)
echo.

REM Install Python dependencies
echo Installing Python PKM Agent...
cd pkm-agent

if not exist ".venv" (
    echo Creating Python virtual environment...
    python -m venv .venv
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing package dependencies...
pip install -e ".[dev,ollama]"

echo [OK] Python PKM Agent installed
call deactivate
cd ..
echo.

REM Install Obsidian plugin dependencies
echo Installing Obsidian plugin dependencies...
cd obsidian-pkm-agent

if not exist "node_modules" (
    echo Installing npm packages...
    npm install
    echo [OK] Obsidian plugin dependencies installed
) else (
    echo [OK] Obsidian plugin dependencies already installed
)

echo Building Obsidian plugin...
call npm run build
echo [OK] Obsidian plugin built

cd ..
echo.

REM Configure MCP settings
echo Configuring MCP settings...

if not exist ".mcp\config.json" (
    echo MCP config not found. Please edit .mcp\config.json with your settings.
    echo Required settings:
    echo   - OBSIDIAN_API_KEY: Your Obsidian Local REST API key
    echo   - PKMA_LLM__API_KEY: Your OpenAI API key (or Ollama config)
) else (
    echo [OK] MCP config exists
)
echo.

REM Create example environment file
echo Creating example environment file...

(
echo # LLM Configuration
echo PKMA_LLM__PROVIDER=openai
echo PKMA_LLM__MODEL=gpt-4o-mini
echo PKMA_LLM__API_KEY=your-openai-api-key-here
echo.
echo # For Ollama, use:
echo # PKMA_LLM__PROVIDER=ollama
echo # PKMA_LLM__MODEL=llama2
echo # PKMA_LLM__BASE_URL=http://localhost:11434
echo.
echo # RAG Configuration
echo PKMA_RAG__EMBEDDING_MODEL=all-MiniLM-L6-v2
echo PKMA_RAG__CHUNK_SIZE=512
echo PKMA_RAG__TOP_K=5
echo.
echo # Paths
echo PKMA_PKM_ROOT=./pkm
echo PKMA_DATA_DIR=./.pkm-agent
echo PKMA_DB_PATH=./data/pkm.db
echo PKMA_CHROMA_PATH=./data/chroma
echo.
echo # MCP Configuration
echo MCP_LOG_LEVEL=info
echo OBSIDIAN_BASE_URL=http://127.0.0.1:27123
echo OBSIDIAN_API_KEY=your-obsidian-api-key-here
echo OBSIDIAN_VERIFY_SSL=false
echo OBSIDIAN_ENABLE_CACHE=true
) > pkm-agent\.env.example

echo [OK] Example environment file created at pkm-agent\.env.example
echo.

REM Create startup script
echo Creating startup script...

(
echo @echo off
echo REM Startup script for Obsidian Agent System
echo.
echo echo Starting Obsidian Agent System...
echo.
echo REM Check if Obsidian Local REST API is running
echo curl -s http://127.0.0.1:27123 ^>nul 2^>^&1
echo if %%ERRORLEVEL%% NEQ 0 ^(
echo     echo [WARNING] Obsidian Local REST API is not running.
echo     echo Please ensure Obsidian is running with Local REST API plugin enabled.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo [OK] Obsidian Local REST API is running
echo.
echo REM Start PKM RAG MCP Server
echo echo Starting PKM RAG MCP Server...
echo cd pkm-agent
echo call .venv\Scripts\activate.bat
echo.
echo REM Run MCP server
echo echo PKM RAG MCP Server started. Press Ctrl+C to stop.
echo python -m pkm_agent.mcp_server
echo.
) > start-agent-system.bat

echo [OK] Startup script created: start-agent-system.bat
echo.

REM Final instructions
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Next steps:
echo.
echo 1. Configure your API keys:
echo    - Edit .mcp\config.json
echo    - Copy pkm-agent\.env.example to pkm-agent\.env
echo    - Add your API keys to both files
echo.
echo 2. Start Obsidian and enable Local REST API plugin:
echo    - Settings -^> Community Plugins -^> Obsidian Local REST API
echo    - Generate an API key
echo    - Note the base URL (default: http://127.0.0.1:27123)
echo.
echo 3. Copy Obsidian plugin to your vault:
echo    - Copy obsidian-pkm-agent\dist\* to %%USERPROFILE%%\Documents\Obsidian\YourVault\.obsidian\plugins\obsidian-pkm-agent\
echo.
echo 4. Enable PKM Agent plugin in Obsidian:
echo    - Settings -^> Community Plugins -^> PKM Agent
echo.
echo 5. Start the agent system:
echo    - Run: start-agent-system.bat
echo.
echo 6. Open PKM Agent sidebar in Obsidian and start chatting!
echo.
echo For detailed documentation, see: AGENTZERO_OBSIDIAN_INTEGRATION.md
echo.
pause

exit /b 0

:error
exit /b 1
