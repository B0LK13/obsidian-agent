# Verify PKM Agent installation
$pythonExe = "C:\Users\Admin\scoop\apps\python\current\python.exe"

Write-Host "=== Checking Installation ===" -ForegroundColor Cyan

# Check which Python
Write-Host "`nPython location:"
& $pythonExe -c "import sys; print(sys.executable)"

# Check if package is installed
Write-Host "`nInstalled packages (pkm):"
& $pythonExe -m pip list | Select-String "pkm"

# Check site-packages
Write-Host "`nSite-packages location:"
& $pythonExe -c "import site; print(site.getsitepackages())"

# Check if editable install link exists
Write-Host "`nEditable install links (.pth files):"
& $pythonExe -c "import site; import os; sp = site.getsitepackages()[0]; print([f for f in os.listdir(sp) if f.endswith('.pth') or f.endswith('.egg-link')])"

# Try direct import with path
Write-Host "`nTrying direct import with sys.path modification:"
& $pythonExe -c @"
import sys
sys.path.insert(0, r'C:\Users\Admin\Documents\B0LK13v2\apps\pkm-agent\src')
from pkm_agent import PKMAgentApp, Config
print('Direct import OK!')
"@
