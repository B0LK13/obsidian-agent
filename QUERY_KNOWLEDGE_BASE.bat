@echo off
chcp 65001 >nul
echo ============================================
echo  Knowledge Database Query Tool
echo ============================================
echo.

set PYTHONPATH=C:\Users\Admin\Documents\B0LK13v2\venv\Scripts\python.exe
set SCRIPT=C:\Users\Admin\Documents\B0LK13v2\mcp-server\direct_query.py

"%PYTHONPATH%" "%SCRIPT%" %*

if errorlevel 1 (
    echo.
    echo ERROR: Query failed
    pause
    exit /b 1
)
