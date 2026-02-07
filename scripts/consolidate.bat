@echo off
REM B0LK13v2 Project Consolidation Script
REM Run this script from the B0LK13v2 root directory

setlocal enabledelayedexpansion
set ROOT=C:\Users\Admin\Documents\B0LK13v2

echo === B0LK13v2 Project Consolidation ===
echo.

REM Step 1: Copy PKM Agent
echo [1/5] Consolidating PKM Agent...
xcopy /E /I /Y "%ROOT%\B0LK13v2\pkm-agent\src" "%ROOT%\apps\pkm-agent\src"
xcopy /Y "%ROOT%\B0LK13v2\pkm-agent\pyproject.toml" "%ROOT%\apps\pkm-agent\"
xcopy /Y "%ROOT%\B0LK13v2\pkm-agent\Dockerfile" "%ROOT%\apps\pkm-agent\"
xcopy /Y "%ROOT%\B0LK13v2\pkm-agent\docker-compose.yml" "%ROOT%\apps\pkm-agent\"
xcopy /Y "%ROOT%\B0LK13v2\pkm-agent\.env.example" "%ROOT%\apps\pkm-agent\"
xcopy /Y "%ROOT%\B0LK13v2\pkm-agent\README.md" "%ROOT%\apps\pkm-agent\"
xcopy /E /I /Y "%ROOT%\B0LK13v2\pkm-agent\tests" "%ROOT%\apps\pkm-agent\tests"
xcopy /E /I /Y "%ROOT%\B0LK13v2\pkm-agent\docs" "%ROOT%\apps\pkm-agent\docs"
echo   PKM Agent copied.

REM Step 2: Copy Obsidian Plugin
echo [2/5] Consolidating Obsidian Plugin...
xcopy /Y "%ROOT%\obsidian-agent\*.ts" "%ROOT%\apps\obsidian-plugin\"
xcopy /Y "%ROOT%\obsidian-agent\*.json" "%ROOT%\apps\obsidian-plugin\"
xcopy /Y "%ROOT%\obsidian-agent\*.css" "%ROOT%\apps\obsidian-plugin\"
xcopy /Y "%ROOT%\obsidian-agent\*.mjs" "%ROOT%\apps\obsidian-plugin\"
xcopy /Y "%ROOT%\obsidian-agent\README.md" "%ROOT%\apps\obsidian-plugin\"
mkdir "%ROOT%\apps\obsidian-plugin\src" 2>nul
xcopy /E /I /Y "%ROOT%\B0LK13v2\obsidian-pkm-agent\src" "%ROOT%\apps\obsidian-plugin\src"
echo   Obsidian Plugin copied.

REM Step 3: Copy Web App
echo [3/5] Consolidating Web App...
xcopy /E /I /Y "%ROOT%\B0LK13\components" "%ROOT%\apps\web\components"
xcopy /E /I /Y "%ROOT%\B0LK13\pages" "%ROOT%\apps\web\pages"
xcopy /E /I /Y "%ROOT%\B0LK13\posts" "%ROOT%\apps\web\posts"
xcopy /E /I /Y "%ROOT%\B0LK13\public" "%ROOT%\apps\web\public"
xcopy /E /I /Y "%ROOT%\B0LK13\styles" "%ROOT%\apps\web\styles"
xcopy /E /I /Y "%ROOT%\B0LK13\lib" "%ROOT%\apps\web\lib"
xcopy /E /I /Y "%ROOT%\B0LK13\utils" "%ROOT%\apps\web\utils"
xcopy /Y "%ROOT%\B0LK13\package.json" "%ROOT%\apps\web\"
xcopy /Y "%ROOT%\B0LK13\tsconfig.json" "%ROOT%\apps\web\"
echo   Web App copied.

REM Step 4: Consolidate Documentation
echo [4/5] Consolidating Documentation...
xcopy /Y "%ROOT%\B0LK13v2\MANUAL-SETUP.md" "%ROOT%\docs\setup\"
xcopy /Y "%ROOT%\B0LK13v2\README-SETUP.md" "%ROOT%\docs\setup\"
xcopy /Y "%ROOT%\B0LK13v2\SETUP-COMPLETE.md" "%ROOT%\docs\setup\"
xcopy /Y "%ROOT%\B0LK13v2\START-HERE.md" "%ROOT%\docs\setup\"
xcopy /Y "%ROOT%\B0LK13v2\QUICK-REFERENCE.md" "%ROOT%\docs\setup\"
xcopy /Y "%ROOT%\B0LK13v2\AI-ML-OPTIMIZATION.md" "%ROOT%\docs\architecture\"
xcopy /Y "%ROOT%\B0LK13v2\001-*.md" "%ROOT%\docs\changelog\"
xcopy /Y "%ROOT%\B0LK13v2\002-*.md" "%ROOT%\docs\changelog\"
xcopy /Y "%ROOT%\B0LK13v2\003-*.md" "%ROOT%\docs\changelog\"
xcopy /Y "%ROOT%\B0LK13v2\004-*.md" "%ROOT%\docs\changelog\"
xcopy /Y "%ROOT%\B0LK13v2\005-*.md" "%ROOT%\docs\changelog\"
xcopy /Y "%ROOT%\B0LK13v2\006-*.md" "%ROOT%\docs\changelog\"
echo   Documentation copied.

REM Step 5: Archive old directories
echo [5/5] Archiving old directories...
if exist "%ROOT%\pkm-agent" move "%ROOT%\pkm-agent" "%ROOT%\archive\pkm-agent-old"
if exist "%ROOT%\pkm-agent-local" move "%ROOT%\pkm-agent-local" "%ROOT%\archive\pkm-agent-local-old"
echo   Old directories archived.

echo.
echo === Consolidation Complete ===
echo.
echo New structure:
echo   apps\pkm-agent\      - Python PKM Agent
echo   apps\obsidian-plugin\ - Obsidian Plugin  
echo   apps\web\            - Next.js Web App
echo   docs\                - All documentation
echo   archive\             - Old directories
echo.
pause
