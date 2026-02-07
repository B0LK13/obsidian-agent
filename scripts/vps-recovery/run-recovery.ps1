# VPS Recovery Helper - Windows PowerShell
# Copies recovery commands to clipboard for pasting into Hostinger Console

param(
    [Parameter(Position=0)]
    [ValidateSet("diagnose", "fix-ssh", "restore-docker", "verify", "moltbot", "cloudflare", "all")]
    [string]$Step = "diagnose",
    
    [Parameter()]
    [ValidateSet("vps1", "vps2")]
    [string]$Target = "vps1"
)

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VPS Recovery Helper" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# VPS Info
$VPS = @{
    "vps1" = @{
        Name = "VPS-1 (Teacher Agent)"
        TailscaleIP = "100.106.57.38"
        Services = @("Teacher Agent", "n8n", "Portainer", "Dashboard")
    }
    "vps2" = @{
        Name = "VPS-2 (Learner Agent)"
        TailscaleIP = "100.123.199.47"
        Services = @("Learner Agent", "Qdrant")
    }
}

Write-Host "Target: $($VPS[$Target].Name)" -ForegroundColor Yellow
Write-Host "Tailscale IP: $($VPS[$Target].TailscaleIP)" -ForegroundColor Yellow
Write-Host ""

function Get-ScriptContent {
    param([string]$ScriptName)
    $path = Join-Path $ScriptRoot $ScriptName
    if (Test-Path $path) {
        return Get-Content $path -Raw
    }
    return $null
}

function Copy-ToClipboard {
    param([string]$Content, [string]$Description)
    $Content | Set-Clipboard
    Write-Host "✅ $Description copied to clipboard!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Paste this into Hostinger Console (hPanel → VPS → Terminal)" -ForegroundColor Yellow
    Write-Host ""
}

switch ($Step) {
    "diagnose" {
        Write-Host "Step 1: Diagnose VPS Issues" -ForegroundColor Cyan
        $script = Get-ScriptContent "01-diagnose.sh"
        if ($script) {
            Copy-ToClipboard $script "Diagnostic script"
        }
    }
    
    "fix-ssh" {
        Write-Host "Step 2: Fix SSH & Firewall" -ForegroundColor Cyan
        $script = Get-ScriptContent "02-fix-ssh-firewall.sh"
        if ($script) {
            Copy-ToClipboard $script "SSH/Firewall fix script"
        }
    }
    
    "restore-docker" {
        Write-Host "Step 3: Restore Docker Services" -ForegroundColor Cyan
        $script = Get-ScriptContent "03-restore-docker-services.sh"
        if ($script) {
            Copy-ToClipboard $script "Docker restoration script"
        }
    }
    
    "verify" {
        Write-Host "Step 4: Verify Services" -ForegroundColor Cyan
        $script = Get-ScriptContent "04-verify-services.sh"
        if ($script) {
            Copy-ToClipboard $script "Verification script"
        }
    }
    
    "moltbot" {
        Write-Host "Step 5: Setup Moltbot" -ForegroundColor Cyan
        $script = Get-ScriptContent "05-setup-moltbot.sh"
        if ($script) {
            Copy-ToClipboard $script "Moltbot setup script"
        }
    }
    
    "cloudflare" {
        Write-Host "Step 6: Cloudflare DNS Setup" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "⚠️  This requires your Cloudflare API token and VPS public IP" -ForegroundColor Yellow
        Write-Host ""
        
        $cfToken = Read-Host "Enter Cloudflare API Token (or press Enter to skip)"
        $vpsIP = Read-Host "Enter VPS Public IP (or press Enter to skip)"
        
        if ($cfToken -and $vpsIP) {
            $script = Get-ScriptContent "06-cloudflare-dns-setup.sh"
            $script = $script -replace 'YOUR_CLOUDFLARE_API_TOKEN', $cfToken
            $script = $script -replace 'YOUR_VPS_PUBLIC_IP', $vpsIP
            Copy-ToClipboard $script "Cloudflare DNS script (with your tokens)"
        } else {
            Write-Host "Skipped - tokens not provided" -ForegroundColor Gray
        }
    }
    
    "all" {
        Write-Host "Full Recovery Procedure" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Run these steps in order:" -ForegroundColor Yellow
        Write-Host "  1. .\run-recovery.ps1 diagnose" -ForegroundColor White
        Write-Host "  2. .\run-recovery.ps1 fix-ssh" -ForegroundColor White
        Write-Host "  3. .\run-recovery.ps1 restore-docker" -ForegroundColor White
        Write-Host "  4. .\run-recovery.ps1 verify" -ForegroundColor White
        Write-Host "  5. .\run-recovery.ps1 moltbot (optional)" -ForegroundColor White
        Write-Host "  6. .\run-recovery.ps1 cloudflare (optional)" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Hostinger Console Access:" -ForegroundColor Yellow
Write-Host "  1. Go to https://hpanel.hostinger.com" -ForegroundColor White
Write-Host "  2. Select your VPS" -ForegroundColor White
Write-Host "  3. Click 'Terminal' or 'VNC'" -ForegroundColor White
Write-Host "  4. Paste the script (Ctrl+Shift+V)" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
