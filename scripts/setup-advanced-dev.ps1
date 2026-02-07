# Advanced Development System Setup Script
# Configures Windows 11 Pro for optimal development workflows

#Requires -RunAsAdministrator

param(
    [switch]$SkipWSL,
    [switch]$SkipDocker,
    [switch]$SkipTools,
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Advanced Development System Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

function Write-Step {
    param([string]$Message)
    Write-Host "► $Message" -ForegroundColor Yellow
}

function Write-Success {
    param([string]$Message)
    Write-Host "  ✓ $Message" -ForegroundColor Green
}

function Write-Skip {
    param([string]$Message)
    Write-Host "  ○ $Message" -ForegroundColor Gray
}

function Write-Error {
    param([string]$Message)
    Write-Host "  ✗ $Message" -ForegroundColor Red
}

# ============================================
# 1. Windows Features
# ============================================
Write-Step "Configuring Windows Features"

if (-not $SkipWSL) {
    # Enable WSL
    $wslFeature = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
    if ($wslFeature.State -ne "Enabled") {
        if (-not $DryRun) {
            Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -NoRestart | Out-Null
        }
        Write-Success "WSL feature enabled"
    } else {
        Write-Skip "WSL already enabled"
    }

    # Enable Virtual Machine Platform
    $vmFeature = Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform
    if ($vmFeature.State -ne "Enabled") {
        if (-not $DryRun) {
            Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -NoRestart | Out-Null
        }
        Write-Success "Virtual Machine Platform enabled"
    } else {
        Write-Skip "Virtual Machine Platform already enabled"
    }

    # Enable Hyper-V (for advanced scenarios)
    $hyperv = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -ErrorAction SilentlyContinue
    if ($hyperv -and $hyperv.State -ne "Enabled") {
        if (-not $DryRun) {
            Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -NoRestart | Out-Null
        }
        Write-Success "Hyper-V enabled"
    } else {
        Write-Skip "Hyper-V already enabled or not available"
    }
}

# ============================================
# 2. WSL Configuration
# ============================================
Write-Host ""
Write-Step "Configuring WSL2"

if (-not $SkipWSL) {
    # Set WSL2 as default
    if (-not $DryRun) {
        wsl --set-default-version 2 2>$null
    }
    Write-Success "WSL2 set as default"

    # Create .wslconfig if not exists
    $wslConfigPath = "$env:USERPROFILE\.wslconfig"
    if (-not (Test-Path $wslConfigPath)) {
        $wslConfig = @"
[wsl2]
memory=48GB
processors=12
swap=8GB
localhostForwarding=true
nestedVirtualization=true

[experimental]
sparseVhd=true
autoMemoryReclaim=gradual
"@
        if (-not $DryRun) {
            $wslConfig | Out-File -FilePath $wslConfigPath -Encoding UTF8
        }
        Write-Success "Created .wslconfig with optimized settings"
    } else {
        Write-Skip ".wslconfig already exists"
    }
}

# ============================================
# 3. Install CLI Tools via Winget
# ============================================
Write-Host ""
Write-Step "Installing CLI Tools"

if (-not $SkipTools) {
    $tools = @(
        @{ Id = "Git.Git"; Name = "Git" },
        @{ Id = "GitHub.cli"; Name = "GitHub CLI" },
        @{ Id = "Microsoft.PowerShell"; Name = "PowerShell 7" },
        @{ Id = "Microsoft.WindowsTerminal"; Name = "Windows Terminal" },
        @{ Id = "JanDeDobbeleer.OhMyPosh"; Name = "Oh My Posh" },
        @{ Id = "sharkdp.fd"; Name = "fd" },
        @{ Id = "BurntSushi.ripgrep.MSVC"; Name = "ripgrep" },
        @{ Id = "junegunn.fzf"; Name = "fzf" },
        @{ Id = "sharkdp.bat"; Name = "bat" },
        @{ Id = "ajeetdsouza.zoxide"; Name = "zoxide" },
        @{ Id = "jqlang.jq"; Name = "jq" },
        @{ Id = "stedolan.jq"; Name = "jq (alt)" }
    )

    foreach ($tool in $tools) {
        $installed = winget list --id $tool.Id 2>$null | Select-String $tool.Id
        if (-not $installed) {
            if (-not $DryRun) {
                Write-Host "    Installing $($tool.Name)..." -ForegroundColor Gray
                winget install --id $tool.Id --accept-source-agreements --accept-package-agreements -h 2>$null
            }
            Write-Success "Installed $($tool.Name)"
        } else {
            Write-Skip "$($tool.Name) already installed"
        }
    }
}

# ============================================
# 4. PowerShell Profile Configuration
# ============================================
Write-Host ""
Write-Step "Configuring PowerShell Profile"

$profileContent = @'
# Advanced PowerShell Profile

# Oh My Posh (if installed)
if (Get-Command oh-my-posh -ErrorAction SilentlyContinue) {
    oh-my-posh init pwsh --config "$env:POSH_THEMES_PATH\powerlevel10k_rainbow.omp.json" | Invoke-Expression
}

# Zoxide (if installed)
if (Get-Command zoxide -ErrorAction SilentlyContinue) {
    Invoke-Expression (& { (zoxide init powershell | Out-String) })
}

# Aliases
Set-Alias -Name g -Value git
Set-Alias -Name k -Value kubectl
Set-Alias -Name d -Value docker
Set-Alias -Name dc -Value docker-compose
Set-Alias -Name cat -Value bat -Option AllScope
Set-Alias -Name ll -Value Get-ChildItem

# Functions
function which($command) { Get-Command $command -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Path }
function touch($file) { if (Test-Path $file) { (Get-Item $file).LastWriteTime = Get-Date } else { New-Item $file -ItemType File } }
function mkcd($dir) { New-Item -ItemType Directory -Path $dir -Force; Set-Location $dir }

# Git shortcuts
function gs { git status }
function ga { git add $args }
function gc { git commit -m $args }
function gp { git push }
function gl { git log --oneline -10 }
function gd { git diff $args }

# Docker shortcuts
function dps { docker ps $args }
function dimg { docker images $args }
function dlogs { docker logs -f $args }
function dexec { docker exec -it $args }

# PSReadLine configuration
Set-PSReadLineOption -PredictionSource History
Set-PSReadLineOption -PredictionViewStyle ListView
Set-PSReadLineOption -EditMode Windows
Set-PSReadLineKeyHandler -Key Tab -Function MenuComplete
Set-PSReadLineKeyHandler -Key UpArrow -Function HistorySearchBackward
Set-PSReadLineKeyHandler -Key DownArrow -Function HistorySearchForward

# Environment
$env:EDITOR = "code"
$env:PAGER = "bat"
'@

$profilePath = $PROFILE.CurrentUserAllHosts
$profileDir = Split-Path $profilePath -Parent

if (-not (Test-Path $profileDir)) {
    if (-not $DryRun) {
        New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
    }
}

if (-not (Test-Path $profilePath) -or (Get-Content $profilePath -Raw) -notmatch "Advanced PowerShell Profile") {
    if (-not $DryRun) {
        $profileContent | Out-File -FilePath $profilePath -Encoding UTF8 -Append
    }
    Write-Success "PowerShell profile configured"
} else {
    Write-Skip "PowerShell profile already configured"
}

# ============================================
# 5. Git Configuration
# ============================================
Write-Host ""
Write-Step "Configuring Git"

$gitConfigs = @(
    @{ Key = "core.autocrlf"; Value = "true" },
    @{ Key = "core.editor"; Value = "code --wait" },
    @{ Key = "pull.rebase"; Value = "true" },
    @{ Key = "push.autoSetupRemote"; Value = "true" },
    @{ Key = "rebase.autoStash"; Value = "true" },
    @{ Key = "merge.conflictStyle"; Value = "diff3" },
    @{ Key = "diff.algorithm"; Value = "histogram" },
    @{ Key = "init.defaultBranch"; Value = "main" },
    @{ Key = "alias.co"; Value = "checkout" },
    @{ Key = "alias.br"; Value = "branch" },
    @{ Key = "alias.ci"; Value = "commit" },
    @{ Key = "alias.st"; Value = "status" },
    @{ Key = "alias.lg"; Value = "log --oneline --graph --decorate --all" }
)

foreach ($config in $gitConfigs) {
    if (-not $DryRun) {
        git config --global $config.Key $config.Value 2>$null
    }
}
Write-Success "Git configured with recommended settings"

# ============================================
# 6. Docker MCP Configuration
# ============================================
Write-Host ""
Write-Step "Configuring Docker MCP"

if (-not $SkipDocker) {
    $mcpServers = @("docker", "filesystem", "git", "github", "fetch", "time", "redis", "memory", "sequentialthinking")
    
    foreach ($server in $mcpServers) {
        if (-not $DryRun) {
            docker mcp server enable $server 2>$null
        }
    }
    Write-Success "MCP servers enabled"

    # Connect to clients
    $clients = @("vscode", "cursor", "claude-desktop")
    foreach ($client in $clients) {
        if (-not $DryRun) {
            docker mcp client connect $client --global 2>$null
        }
    }
    Write-Success "MCP clients connected"
}

# ============================================
# 7. VS Code Extensions
# ============================================
Write-Host ""
Write-Step "Installing VS Code Extensions"

$extensions = @(
    "ms-vscode-remote.remote-containers",
    "ms-vscode-remote.remote-wsl",
    "ms-azuretools.vscode-docker",
    "GitHub.copilot",
    "GitHub.copilot-chat",
    "eamodio.gitlens",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "usernamehw.errorlens",
    "gruntfuggly.todo-tree",
    "streetsidesoftware.code-spell-checker",
    "redhat.vscode-yaml",
    "ms-vscode.hexeditor"
)

$codeCmd = Get-Command code -ErrorAction SilentlyContinue
if ($codeCmd) {
    foreach ($ext in $extensions) {
        if (-not $DryRun) {
            code --install-extension $ext --force 2>$null | Out-Null
        }
    }
    Write-Success "VS Code extensions installed"
} else {
    Write-Skip "VS Code not found in PATH"
}

# ============================================
# Summary
# ============================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Restart your terminal to apply profile changes" -ForegroundColor White
Write-Host "  2. Restart VS Code/Cursor to activate MCP" -ForegroundColor White
Write-Host "  3. Run 'wsl --install -d Ubuntu-22.04' if Ubuntu not installed" -ForegroundColor White
Write-Host "  4. Configure Docker Desktop WSL2 integration" -ForegroundColor White
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN] No changes were made" -ForegroundColor Yellow
}
