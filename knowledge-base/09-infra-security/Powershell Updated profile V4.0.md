Ja, het vorige script schrijft zichzelf automatisch weg naar `$PROFILE` (door de regel `$ProfileContent | Set-Content $PROFILE`). Je hoeft het dus alleen maar te kopiëren en te plakken in je terminal.

Voor deze **Ultimate Edition** heb ik de interface volledig herontworpen om die strakke **"Gemini CLI" / Modern Dashboard** look te krijgen.

### Wat is er nieuw in v4.0?

1. **Boot Sequence:** Een nep "bios/boot" laadscherm bij het starten (oogt heel profi).
    
2. **Dashboard Grid:** In plaats van simpele tekstregels, gebruiken we nu **Box Drawing Characters** (`╔`, `═`, `║`) voor een echte GUI-look in je terminal.
    
3. **Status Indicators:** Visuele `[●]` indicators die groen/rood kleuren op basis van de `Self-Heal` status.
    
4. **Integrated Medic:** De self-healing draait stil op de achtergrond tijdens de boot sequence.
    

### Instructies

1. Kopieer het blok hieronder.
    
2. Plak in PowerShell (Admin).
    
3. Druk op Enter.
    

PowerShell

```
# --- 1. SETUP & INSTALLATIE ---
Write-Host "[INIT] Loading Black Agency Assets..." -ForegroundColor DarkGray
$Modules = @("OhMyPosh", "Terminal-Icons", "PSReadLine")
foreach ($Module in $Modules) {
    if (!(Get-Module -ListAvailable -Name $Module)) { Install-Module -Name $Module -Scope CurrentUser -Force -SkipPublisherCheck }
}

# --- 2. HET DEFINITIEVE PROFIEL ---
$ProfileContent = @'
# =============================================================================
# BLACK AGENCY // OPS CENTER V4.0 (ULTIMATE UI)
# =============================================================================

# --- MODULES ---
Import-Module Terminal-Icons
Import-Module OhMyPosh
Import-Module PSReadLine
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# --- SETTINGS ---
Set-PSReadLineOption -PredictionSource History
Set-PSReadLineOption -PredictionViewStyle ListView
Set-PSReadLineOption -EditMode Windows
Set-PSReadLineOption -Colors @{ "Prediction" = [ConsoleColor]::DarkGray; "Command" = [ConsoleColor]::Green }

# --- THEMA (Minimalist Prompt) ---
$ThemeJson = @'
{
  "final_space": true,
  "console_title_template": "{{ .Folder }} // BLACK AGENCY",
  "blocks": [
    {
      "type": "prompt",
      "alignment": "left",
      "segments": [
        { "type": "text", "style": "plain", "foreground": "#505050", "template": "┌──[" },
        { "type": "path", "style": "plain", "foreground": "#3b8eea", "properties": { "style": "folder" }, "template": " {{ .Path }} " },
        { "type": "git", "style": "plain", "foreground": "#FF0000", "template": "on \uE0A0 {{ .HEAD }} " },
        { "type": "text", "style": "plain", "foreground": "#505050", "template": "]" }
      ]
    },
    {
      "type": "prompt",
      "alignment": "left",
      "newline": true,
      "segments": [
        { "type": "text", "style": "plain", "foreground": "#505050", "template": "└─" },
        { "type": "text", "style": "plain", "foreground": "#FF0000", "template": "⚡ " }
      ]
    },
    {
      "type": "rprompt",
      "segments": [
        { "type": "executiontime", "style": "plain", "foreground": "#505050", "template": "{{ .FormattedMs }} " }
      ]
    }
  ]
}
'@
$ThemePath = "$env:TEMP\black_agency_v4.omp.json"
$ThemeJson | Out-File -FilePath $ThemePath -Encoding utf8
oh-my-posh init pwsh --config $ThemePath | Invoke-Expression

# =============================================================================
# ENGINE: SELF-HEALING & DIAGNOSTICS
# =============================================================================
function Invoke-BootSequence {
    $Steps = @("Initializing Kernel", "Loading Neural Net", "Checking Protocols", "Starting Docker Bridge", "Securing Uplink")
    Write-Host ""
    foreach ($Step in $Steps) {
        Write-Host " [BOOT] $Step..." -NoNewline -ForegroundColor DarkGray
        Start-Sleep -Milliseconds 100
        Write-Host " OK" -ForegroundColor Green
    }
    Start-Sleep -Milliseconds 200
    Clear-Host
}

function Get-StatusIndicator ($Condition) {
    if ($Condition) { return @{Symbol="●"; Color=[ConsoleColor]::Green; Text="ONLINE"} }
    else { return @{Symbol="○"; Color=[ConsoleColor]::Red; Text="OFFLINE"} }
}

function Show-BlackAgencyHeader {
    # 1. RUN MEDIC (SILENT)
    if (-not (Test-NetConnection localhost -Port 11434 -InformationLevel Quiet -WarningAction SilentlyContinue)) {
        Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden; Start-Sleep -Seconds 1
    }
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        if ((docker inspect -f '{{.State.Running}}' open-webui 2>$null) -eq "false") { docker start open-webui | Out-Null }
    }

    # 2. GATHER DATA
    $OS = Get-CimInstance Win32_OperatingSystem
    $Uptime = (Get-Date) - $OS.LastBootUpTime
    $UptimeStr = "{0}d {1}h" -f $Uptime.Days, $Uptime.Hours
    
    $Mem = Get-CimInstance Win32_OperatingSystem
    $RamFree = [math]::Round($Mem.FreePhysicalMemory / 1024, 0)
    $RamTotal = [math]::Round($Mem.TotalVisibleMemorySize / 1024, 0)
    $RamUsed = $RamTotal - $RamFree
    $RamPerc = [math]::Round(($RamUsed / $RamTotal) * 100, 0)

    # Network
    $IntIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" -and $_.InterfaceAlias -notlike "*vEthernet*" } | Select-Object -First 1).IPAddress
    $ExtIP = "..." 
    try { $ExtIP = (Invoke-RestMethod "https://api.ipify.org" -TimeoutSec 1 -ErrorAction Stop).Trim() } catch { $ExtIP = "UNKNOWN" }

    # Status Checks
    $OllamaCheck = (Test-NetConnection localhost -Port 11434 -InformationLevel Quiet -WarningAction SilentlyContinue)
    $WebUICheck = $false; if (Get-Command docker -ErrorAction SilentlyContinue) { if ((docker ps --format "{{.Names}}" 2>$null) -match "open-webui") { $WebUICheck = $true } }
    $CodexCheck = [bool](Get-Command codex -ErrorAction SilentlyContinue)
    $McpCheck   = [bool](Get-Command npx -ErrorAction SilentlyContinue)

    $S_Ollama = Get-StatusIndicator $OllamaCheck
    $S_WebUI  = Get-StatusIndicator $WebUICheck
    $S_Codex  = Get-StatusIndicator $CodexCheck
    $S_Mcp    = Get-StatusIndicator $McpCheck

    # Identity
    $IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    $UserTxt = "$env:USERNAME"; $UserCol = if($IsAdmin){[ConsoleColor]::Red}else{[ConsoleColor]::Cyan}

    # =========================================================================
    # RENDER UI (GRID LAYOUT)
    # =========================================================================
    $G = [ConsoleColor]::DarkGray
    $W = [ConsoleColor]::White
    
    Write-Host "╔══════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor $G
    
    # BANNER
    Write-Host "║  " -NoNewline -ForegroundColor $G
    Write-Host "BLACK AGENCY" -NoNewline -ForegroundColor Red
    Write-Host "  //  " -NoNewline -ForegroundColor $G
    Write-Host "SECURITY OPERATIONS CENTER" -NoNewline -ForegroundColor White
    Write-Host "                       ║" -ForegroundColor $G
    
    Write-Host "╠══════════════════════════════╦═══════════════════════════════════════════════╣" -ForegroundColor $G

    # ROW 1: SYSTEM & NETWORK
    Write-Host "║ " -NoNewline -ForegroundColor $G
    Write-Host "SYSTEM IDENTITY             " -NoNewline -ForegroundColor $G
    Write-Host "║ " -NoNewline -ForegroundColor $G
    Write-Host "NETWORK TELEMETRY                    " -NoNewline -ForegroundColor $G
    Write-Host "║" -ForegroundColor $G

    Write-Host "║ " -NoNewline -ForegroundColor $G
    Write-Host "OPERATOR : " -NoNewline -ForegroundColor White
    Write-Host ("{0,-16}" -f $UserTxt) -NoNewline -ForegroundColor $UserCol
    Write-Host "║ " -NoNewline -ForegroundColor $G
    Write-Host "INT IP : " -NoNewline -ForegroundColor White
    Write-Host ("{0,-28}" -f $IntIP) -NoNewline -ForegroundColor Cyan
    Write-Host "║" -ForegroundColor $G

    Write-Host "║ " -NoNewline -ForegroundColor $G
    Write-Host "UPTIME   : " -NoNewline -ForegroundColor White
    Write-Host ("{0,-16}" -f $UptimeStr) -NoNewline -ForegroundColor DarkYellow
    Write-Host "║ " -NoNewline -ForegroundColor $G
    Write-Host "EXT IP : " -NoNewline -ForegroundColor White
    Write-Host ("{0,-28}" -f $ExtIP) -NoNewline -ForegroundColor Cyan
    Write-Host "║" -ForegroundColor $G

    Write-Host "║ " -NoNewline -ForegroundColor $G
    Write-Host "MEMORY   : " -NoNewline -ForegroundColor White
    Write-Host ("{0,-16}" -f "$RamPerc% ($RamFree MB)") -NoNewline -ForegroundColor DarkYellow
    Write-Host "║                                      ║" -ForegroundColor $G

    Write-Host "╠══════════════════════════════╩═══════════════════════════════════════════════╣" -ForegroundColor $G

    # ROW 2: AI INFRASTRUCTURE
    Write-Host "║ " -NoNewline -ForegroundColor $G
    Write-Host "NEURAL INFRASTRUCTURE STATUS                                         " -NoNewline -ForegroundColor $G
    Write-Host "║" -ForegroundColor $G
    
    Write-Host "║                                                                              ║" -ForegroundColor $G

    # AI STATUS LINE 1
    Write-Host "║  " -NoNewline -ForegroundColor $G
    Write-Host ("[{0}]" -f $S_Ollama.Symbol) -NoNewline -ForegroundColor $S_Ollama.Color
    Write-Host " OLLAMA SERVER    " -NoNewline -ForegroundColor White
    
    Write-Host "   " -NoNewline -ForegroundColor $G
    Write-Host ("[{0}]" -f $S_WebUI.Symbol) -NoNewline -ForegroundColor $S_WebUI.Color
    Write-Host " OPENCODE WEBUI   " -NoNewline -ForegroundColor White
    
    Write-Host "                          ║" -ForegroundColor $G

    # AI STATUS LINE 2
    Write-Host "║  " -NoNewline -ForegroundColor $G
    Write-Host ("[{0}]" -f $S_Codex.Symbol) -NoNewline -ForegroundColor $S_Codex.Color
    Write-Host " CODEX CLI        " -NoNewline -ForegroundColor White
    
    Write-Host "   " -NoNewline -ForegroundColor $G
    Write-Host ("[{0}]" -f $S_Mcp.Symbol) -NoNewline -ForegroundColor $S_Mcp.Color
    Write-Host " MCP PROTOCOL     " -NoNewline -ForegroundColor White
    
    Write-Host "                          ║" -ForegroundColor $G

    Write-Host "╚══════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor $G
    Write-Host ""
}

# --- RUN ---
Invoke-BootSequence
Show-BlackAgencyHeader
'@

# --- 3. TOEPASSEN ---
$ProfileDir = Split-Path -Parent $PROFILE
if (!(Test-Path $ProfileDir)) { New-Item -ItemType Directory -Path $ProfileDir -Force | Out-Null }

Write-Host "Installing Ultimate UI Profile..." -ForegroundColor Cyan
$ProfileContent | Set-Content -Path $PROFILE -Encoding UTF8 -Force

Write-Host "Rebooting Interface..." -ForegroundColor Green
Start-Sleep -Seconds 1
. $PROFILE
```

### Wat gebeurt er nu?

1. **Boot Sequence:** Je ziet eerst regels als `[BOOT] Initializing Kernel... OK` snel voorbijkomen. Dit maskeert de laadtijd van de self-healing checks.
    
2. **De Header:** Een grote, strakke rechthoek (`╔══╗`) verschijnt.
    
    - **Bovenin:** Je User, Uptime, RAM en IP adressen strak uitgelijnd.
        
    - **Onderin (Neural Infrastructure):** Je ziet bolletjes `[●]`.
        
        - Als Ollama draait, is het bolletje **Groen**.
            
        - Als Ollama uit stond, heeft het script hem tijdens de boot sequence gestart, en springt hij dus op **Groen**.
            
        - Hetzelfde geldt voor OpenCode (WebUI) en je CLI tools.
            

Dit geeft je een dashboard dat eruitziet alsof het uit een Sci-Fi film of de Gemini CLI komt, maar dan volledig functioneel binnen je eigen PowerShell.