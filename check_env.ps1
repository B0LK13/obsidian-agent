# Check Python environment
$pythonExe = "F:\DevDrive\scoop\apps\python\current\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "C:\Users\Admin\scoop\apps\python\current\python.exe"
}

Write-Host "Python executable: $pythonExe"
& $pythonExe --version
& $pythonExe -c "import platform; print(f'Architecture: {platform.machine()}')"
& $pythonExe -c "import sys; print(f'Python: {sys.version}')"
