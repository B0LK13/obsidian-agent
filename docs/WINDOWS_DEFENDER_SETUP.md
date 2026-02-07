# Windows Defender Configuration for Obsidian AI Agent

## Issue
Windows Defender may flag Python processes spawned by the AI stack as suspicious, causing:
- Slow startup (>30 seconds)
- "Suspicious process" notifications
- Process quarantine (rare)

## Quick Fix (Recommended)

### Option 1: PowerShell Script (Automated)

Run this in **PowerShell as Administrator**:

```powershell
# Add Python executable to exclusions
Add-MpPreference -ExclusionProcess "python.exe"
Add-MpPreference -ExclusionProcess "pythonw.exe"

# Add project directory to exclusions
$projectPath = "C:\Users\$env:USERNAME\Documents\B0LK13v2"
Add-MpPreference -ExclusionPath $projectPath

# Add virtual environment (if using)
Add-MpPreference -ExclusionPath "$projectPath\venv"
Add-MpPreference -ExclusionPath "$projectPath\obsidian-ai-agent\venv"

# Verify exclusions were added
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath
Get-MpPreference | Select-Object -ExpandProperty ExclusionProcess

Write-Host "✅ Windows Defender exclusions configured successfully!" -ForegroundColor Green
```

### Option 2: Manual GUI Configuration

1. Open **Windows Security** (Win + I → Privacy & Security → Windows Security)
2. Navigate to **Virus & threat protection**
3. Click **Manage settings** under "Virus & threat protection settings"
4. Scroll down to **Exclusions** and click **Add or remove exclusions**
5. Click **Add an exclusion** and add:

**Process Exclusions:**
- `python.exe`
- `pythonw.exe`

**Folder Exclusions:**
- `C:\Users\[YourUsername]\Documents\B0LK13v2`
- `C:\Users\[YourUsername]\Documents\B0LK13v2\venv`
- `C:\Users\[YourUsername]\Documents\B0LK13v2\obsidian-ai-agent\venv`

## Why This Happens

Windows Defender uses heuristic analysis to detect potentially malicious behavior. Python scripts that:
- Spawn multiple processes
- Access system resources
- Communicate over localhost
- Load large binary files (AI models)

...may trigger false positives.

## Security Considerations

### ⚠️ Risks
Adding exclusions reduces protection for those specific files/processes.

### ✅ Safe Practices
1. **Only exclude specific paths**, not entire `C:\Python*` directories
2. **Verify project source** - Only add exclusions for trusted code
3. **Keep Windows Defender enabled** for other system areas
4. **Regularly update** - Keep Windows Security up-to-date

## Alternative: Code Signing (Future)

For production releases, we plan to:
- [ ] Code sign Python executables
- [ ] Create MSI installer with proper metadata
- [ ] Submit to Microsoft for whitelist review

This will eliminate false positives without requiring exclusions.

## Verification

After adding exclusions, verify the AI agent starts quickly:

```bash
# From B0LK13v2 directory
cd obsidian-ai-agent\local-ai-stack
python -m ai_stack.llm_server_gpu_safe
```

Startup should complete in <5 seconds instead of 30+ seconds.

## Troubleshooting

### Issue: "Access Denied" when adding exclusions
**Solution**: Run PowerShell as Administrator (Right-click → Run as Administrator)

### Issue: Process still gets blocked
**Solution**: 
1. Check Windows Event Viewer for specific detections
2. Add those specific file paths to exclusions
3. Temporarily disable real-time protection to test (re-enable after)

### Issue: Performance still slow
**Solution**: The issue may not be Windows Defender. Check:
- GPU driver installation
- Model file download completion
- Available RAM (>8GB recommended)

## References
- GitHub Issue: [#104 - Windows Defender False Positive](https://github.com/B0LK13/obsidian-agent/issues/104)
- Microsoft Docs: [Exclusions for Windows Security](https://support.microsoft.com/en-us/windows/add-an-exclusion-to-windows-security-811816c0-4dfd-af4a-47e4-c301afe13b26)

---

**Last Updated**: 2026-02-03  
**Status**: ✅ Workaround Available | 🚧 Permanent Fix In Progress
