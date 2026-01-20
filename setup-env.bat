@echo off
REM Windows Batch Environment Setup Script for Obsidian Agent
REM Run this script to set up all necessary environment variables

echo ========================================
echo Obsidian Agent - Environment Setup
echo ========================================
echo.

REM Check if .env.example exists
if not exist ".env.example" (
    echo ERROR: .env.example file not found!
    echo Please ensure .env.example exists in the project root.
    pause
    exit /b 1
)

echo Setup Mode:
echo 1. Create .env from template
echo 2. Set system environment variables (persistent)
echo.

set /p SETUP_MODE="Choose setup mode [1-2]: "

if "%SETUP_MODE%"=="1" (
    REM Copy template
    echo.
    echo Creating .env from template...
    
    if exist ".env" (
        set /p OVERWRITE=".env already exists. Overwrite? (y/n): "
        if /i not "%OVERWRITE%"=="y" (
            echo Cancelled.
            pause
            exit /b 0
        )
    )
    
    copy ".env.example" ".env"
    echo Created .env file
    echo.
    echo Please edit .env and fill in your values.
    echo File location: %CD%\.env
    
) else if "%SETUP_MODE%"=="2" (
    REM Set system environment variables
    echo.
    echo Setting system environment variables...
    echo This will set variables persistently for your user account.
    echo.
    
    set /p CONFIRM="Continue? (y/n): "
    if /i not "%CONFIRM%"=="y" (
        echo Cancelled.
        pause
        exit /b 0
    )
    
    REM Vault Configuration
    set /p VAULT_PATH="Obsidian vault path [%USERPROFILE%\Documents\ObsidianVault]: "
    if "%VAULT_PATH%"=="" set VAULT_PATH=%USERPROFILE%\Documents\ObsidianVault
    setx OBSIDIAN_VAULT_PATH "%VAULT_PATH%"
    echo Set OBSIDIAN_VAULT_PATH
    
    REM Database Configuration
    set /p DB_PATH="Database path [%LOCALAPPDATA%\obsidian-agent\vault.db]: "
    if "%DB_PATH%"=="" set DB_PATH=%LOCALAPPDATA%\obsidian-agent\vault.db
    setx OBSIDIAN_DATABASE__PATH "%DB_PATH%"
    echo Set OBSIDIAN_DATABASE__PATH
    
    REM Vector Store Configuration
    set /p CHROMA_PATH="ChromaDB directory [%LOCALAPPDATA%\obsidian-agent\chroma]: "
    if "%CHROMA_PATH%"=="" set CHROMA_PATH=%LOCALAPPDATA%\obsidian-agent\chroma
    setx OBSIDIAN_VECTOR_STORE__PERSIST_DIRECTORY "%CHROMA_PATH%"
    echo Set OBSIDIAN_VECTOR_STORE__PERSIST_DIRECTORY
    
    REM AI Configuration
    set /p AI_PROVIDER="AI Provider (openai/anthropic/ollama) [openai]: "
    if "%AI_PROVIDER%"=="" set AI_PROVIDER=openai
    setx AI_PROVIDER "%AI_PROVIDER%"
    echo Set AI_PROVIDER
    
    set /p AI_MODEL="AI Model [gpt-4]: "
    if "%AI_MODEL%"=="" set AI_MODEL=gpt-4
    setx AI_MODEL "%AI_MODEL%"
    echo Set AI_MODEL
    
    echo.
    echo System environment variables set!
    echo Note: You may need to restart your terminal for changes to take effect.
    
) else (
    echo Invalid option. Exiting.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Next Steps:
echo 1. Review and edit .env file if needed
echo 2. For Python backend:
echo    cd python_backend
echo    poetry install
echo 3. For TypeScript plugin:
echo    npm install
echo    npm run build
echo.
echo For more information, see DEVELOPER.md
echo ========================================

pause
