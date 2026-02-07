@echo off
REM Push Obsidian MCP Server to GitHub
REM Repository: https://github.com/B0LK13/obsidian-agent

echo ============================================
echo  Pushing to GitHub: B0LK13/obsidian-agent
echo ============================================
echo.

REM Navigate to project directory
cd /d "%~dp0"

REM Check if git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed!
    echo Please install Git from https://git-scm.com/
    pause
    exit /b 1
)

REM Initialize git if not already done
if not exist .git (
    echo Initializing Git repository...
    git init
    git remote add origin https://github.com/B0LK13/obsidian-agent.git
) else (
    echo Git repository already initialized.
)

REM Configure git user if not set
git config user.email >nul 2>&1
if errorlevel 1 (
    git config user.email "obsidian-mcp@example.com"
    git config user.name "Obsidian MCP"
)

REM Add all files
echo.
echo Adding files to git...
git add .

REM Commit
echo.
echo Committing changes...
git commit -m "feat: Add comprehensive Obsidian MCP Server with 46+ tools

Core Features:
- Complete MCP server implementation
- 46 powerful tools for Obsidian vault management
- Note CRUD operations (create, read, update, delete)
- Link and graph analysis (backlinks, orphans, hubs, shortest path)
- Tag management (list, stats, rename, related tags)
- Folder management (create, move, rename)
- Advanced search (regex, date range, duplicates)
- Template system (daily, project, meeting, research)
- Canvas support (list, read, create)
- External integration (URL extraction, bibliography)

Tools by Category:
- Note Management: 12 tools
- Link & Graph: 8 tools
- Tag Management: 5 tools
- Folder Management: 6 tools
- Search & Query: 5 tools
- Templates: 4 tools
- Canvas: 3 tools
- External: 3 tools

Configuration:
- Environment-based configuration
- Claude Desktop integration ready
- Command-line interface included
- Full API client with error handling

Documentation:
- README.md with full documentation
- QUICK_START.md for fast setup
- Code comments throughout

Author: Obsidian MCP Team
License: MIT"

REM Push to GitHub
echo.
echo Pushing to GitHub...
git branch -M main
git push -u origin main

if errorlevel 1 (
    echo.
    echo ============================================
    echo  PUSH FAILED
    echo ============================================
    echo.
    echo Possible issues:
    echo 1. Authentication required - enter credentials
    echo 2. Repository doesn't exist - create it first
    echo 3. Network connection issue
    echo.
    echo To authenticate, use:
    echo - GitHub Personal Access Token
    echo - Or: git config --global credential.helper store
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo ============================================
    echo  SUCCESSFULLY PUSHED TO GITHUB!
    echo ============================================
    echo.
    echo Repository: https://github.com/B0LK13/obsidian-agent
    echo.
    pause
)
