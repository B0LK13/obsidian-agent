@echo off
REM Simple verification runner using Python
REM No PowerShell 7+ required

echo.
echo ================================================================================
echo    PKM-AGENT VERIFICATION - Python Runner
echo ================================================================================
echo.

cd /d C:\Users\Admin\Documents\B0LK13v2\B0LK13v2

echo Running verification script...
echo.

python run_verification.py

echo.
echo ================================================================================
echo    VERIFICATION COMPLETE
echo ================================================================================
echo.
echo Check verification_results.json for detailed results
echo.
pause
