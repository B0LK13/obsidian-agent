# TBA NEXUS PRIME — Windows Command Prompt Configuration

A complete CMD.exe setup that mirrors the TBA NEXUS PRIME experience, featuring Clink for enhanced functionality, custom prompt, and matching aesthetics.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TBA NEXUS PRIME CMD STACK                        │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │    Clink    │  │   Clink     │  │    Lua      │  │   ANSI     │ │
│  │   (Shell)   │  │  Completions│  │  Scripts    │  │   Colors   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│                         CMD.EXE                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quick Installation Script

Save as `install-tba-cmd.ps1` and run in PowerShell as Administrator:

```powershell
#Requires -RunAsAdministrator
# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  TBA NEXUS PRIME — CMD INSTALLER                                           ║
# ╚════════════════════════════════════════════════════════════════════════════╝

$ErrorActionPreference = "Stop"

Write-Host @"
╔════════════════════════════════════════════════════════════════════════════╗
║  TBA NEXUS PRIME // CMD SETUP INSTALLER                                    ║
╚════════════════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Red

# ── Install Clink ──
Write-Host "[1/4] Installing Clink..." -ForegroundColor Cyan

if (Get-Command winget -ErrorAction SilentlyContinue) {
    winget install chrisant996.Clink --silent --accept-package-agreements --accept-source-agreements
} elseif (Get-Command scoop -ErrorAction SilentlyContinue) {
    scoop install clink
} elseif (Get-Command choco -ErrorAction SilentlyContinue) {
    choco install clink -y
} else {
    Write-Host "  Downloading Clink manually..." -ForegroundColor Yellow
    $clinkUrl = "https://github.com/chrisant996/clink/releases/latest/download/clink.zip"
    $clinkZip = "$env:TEMP\clink.zip"
    $clinkDir = "$env:LOCALAPPDATA\clink"
    
    Invoke-WebRequest -Uri $clinkUrl -OutFile $clinkZip
    Expand-Archive -Path $clinkZip -DestinationPath $clinkDir -Force
    Remove-Item $clinkZip
    
    # Add to PATH
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    if ($currentPath -notlike "*$clinkDir*") {
        [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$clinkDir", "User")
    }
}

# ── Create TBA directories ──
Write-Host "[2/4] Creating TBA directories..." -ForegroundColor Cyan

$tbaRoot = "$env:LOCALAPPDATA\TheBlackAgency"
$tbaDirs = @(
    "$tbaRoot\CMD",
    "$tbaRoot\CMD\scripts",
    "$tbaRoot\CMD\completions",
    "$tbaRoot\Cache",
    "$tbaRoot\Logs"
)

foreach ($dir in $tbaDirs) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}

# ── Create Clink profile directory ──
$clinkProfile = "$env:LOCALAPPDATA\clink"
New-Item -ItemType Directory -Path $clinkProfile -Force | Out-Null

Write-Host "[3/4] Configuration files will be created in:" -ForegroundColor Cyan
Write-Host "  - Clink: $clinkProfile" -ForegroundColor Gray
Write-Host "  - TBA:   $tbaRoot\CMD" -ForegroundColor Gray

# ── Enable ANSI colors in CMD ──
Write-Host "[4/4] Enabling ANSI colors in registry..." -ForegroundColor Cyan

$regPath = "HKCU:\Console"
Set-ItemProperty -Path $regPath -Name "VirtualTerminalLevel" -Value 1 -Type DWord -Force

Write-Host @"

╔════════════════════════════════════════════════════════════════════════════╗
║  INSTALLATION COMPLETE                                                     ║
╠════════════════════════════════════════════════════════════════════════════╣
║  Next steps:                                                               ║
║  1. Copy the Lua scripts to: $clinkProfile                                 ║
║  2. Copy tba_init.cmd to: $tbaRoot\CMD                                     ║
║  3. Restart CMD or run: clink inject                                       ║
╚════════════════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Green
```

---

## Main Clink Configuration: `%LOCALAPPDATA%\clink\tba_nexus.lua`

```lua
--[[
╔════════════════════════════════════════════════════════════════════════════════════════════╗
║  THE BLACK AGENCY // OPS CENTER V10.0 ── NEXUS PRIME CMD                                   ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║  CLASSIFICATION: BLACK | PROTOCOL: VIRTU-X | BUILD: 2025.06.NEXUS                          ║
╚════════════════════════════════════════════════════════════════════════════════════════════╝
--]]

--------------------------------------------------------------------------------
-- SECTION 1: CONFIGURATION
--------------------------------------------------------------------------------

local TBA = {
    -- Runtime flags (check environment variables)
    flags = {
        no_banner    = os.getenv("TBA_NO_BANNER") == "1",
        no_selfheal  = os.getenv("TBA_NO_SELFHEAL") == "1",
        no_glitch    = os.getenv("TBA_NO_GLITCH") == "1",
        debug        = os.getenv("TBA_DEBUG") == "1",
    },
    
    -- Paths
    paths = {
        root  = os.getenv("LOCALAPPDATA") .. "\\TheBlackAgency",
        cache = os.getenv("LOCALAPPDATA") .. "\\TheBlackAgency\\Cache",
        logs  = os.getenv("LOCALAPPDATA") .. "\\TheBlackAgency\\Logs",
    },
    
    -- Color palette (ANSI escape codes)
    colors = {
        reset       = "\x1b[0m",
        bold        = "\x1b[1m",
        dim         = "\x1b[2m",
        
        -- Primary
        virtu_red   = "\x1b[38;2;255;23;68m",
        void_black  = "\x1b[38;2;10;10;12m",
        nexus_cyan  = "\x1b[38;2;0;229;255m",
        
        -- Secondary  
        carbon      = "\x1b[38;2;18;19;23m",
        steel       = "\x1b[38;2;104;110;120m",
        chrome      = "\x1b[38;2;176;180;186m",
        ghost       = "\x1b[38;2;230;230;230m",
        
        -- Accents
        warning     = "\x1b[38;2;255;214;0m",
        success     = "\x1b[38;2;0;230;118m",
        error       = "\x1b[38;2;255;23;68m",
        info        = "\x1b[38;2;41;121;255m",
        magenta     = "\x1b[38;2;213;0;249m",
        
        -- Background
        bg_void     = "\x1b[48;2;10;10;12m",
        bg_carbon   = "\x1b[48;2;18;19;23m",
    },
    
    -- Version info
    version = {
        major = 10,
        minor = 0,
        patch = 0,
        build = "NEXUS_PRIME_CMD",
    },
    
    -- State cache
    cache = {
        external_ip = nil,
        ip_timestamp = 0,
        services = {},
    }
}

--------------------------------------------------------------------------------
-- SECTION 2: UTILITY FUNCTIONS
--------------------------------------------------------------------------------

-- Execute command and return output
local function exec(cmd)
    local handle = io.popen(cmd .. " 2>nul")
    if not handle then return nil end
    local result = handle:read("*a")
    handle:close()
    return result and result:gsub("^%s*(.-)%s*$", "%1") or nil
end

-- Check if file exists
local function file_exists(path)
    local f = io.open(path, "r")
    if f then f:close() return true end
    return false
end

-- Get console width
local function get_console_width()
    local width = exec("mode con 2>nul | findstr /i Columns")
    if width then
        local num = width:match("(%d+)")
        return tonumber(num) or 120
    end
    return 120
end

-- Center text
local function center_text(text, width)
    width = width or get_console_width()
    local text_len = #text
    if text_len >= width then return text:sub(1, width) end
    local pad = math.floor((width - text_len) / 2)
    return string.rep(" ", pad) .. text
end

-- Progress bar generator
local function progress_bar(percent, width, fill_char, empty_char)
    width = width or 20
    fill_char = fill_char or "█"
    empty_char = empty_char or "░"
    
    percent = math.max(0, math.min(100, percent))
    local fill_count = math.floor((percent / 100) * width)
    local empty_count = width - fill_count
    
    return string.rep(fill_char, fill_count) .. string.rep(empty_char, empty_count)
end

-- Glitch text effect
local function glitch_text(text, intensity)
    if TBA.flags.no_glitch then return text end
    intensity = intensity or 3
    
    local glyphs = {"█", "▒", "░", "▓", "■", "□", "▬", "▮", "▯", "┃", "╋", "╬"}
    local result = {}
    
    for i = 1, #text do
        local char = text:sub(i, i)
        if char ~= " " and math.random(1, 100) <= intensity then
            table.insert(result, glyphs[math.random(#glyphs)])
        else
            table.insert(result, char)
        end
    end
    
    return table.concat(result)
end

-- Format uptime
local function get_uptime()
    local wmic_output = exec("wmic os get lastbootuptime 2>nul")
    if not wmic_output then return "N/A" end
    
    local boot_time = wmic_output:match("(%d+)")
    if not boot_time or #boot_time < 14 then return "N/A" end
    
    local year = tonumber(boot_time:sub(1, 4))
    local month = tonumber(boot_time:sub(5, 6))
    local day = tonumber(boot_time:sub(7, 8))
    local hour = tonumber(boot_time:sub(9, 10))
    local min = tonumber(boot_time:sub(11, 12))
    local sec = tonumber(boot_time:sub(13, 14))
    
    local boot_ts = os.time({year=year, month=month, day=day, hour=hour, min=min, sec=sec})
    local now_ts = os.time()
    local diff = now_ts - boot_ts
    
    local days = math.floor(diff / 86400)
    local hours = math.floor((diff % 86400) / 3600)
    local minutes = math.floor((diff % 3600) / 60)
    
    return string.format("%02dd %02dh %02dm", days, hours, minutes)
end

-- Get memory info
local function get_memory_info()
    local wmic_output = exec("wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /Value 2>nul")
    if not wmic_output then return 0, 0, 0 end
    
    local free = tonumber(wmic_output:match("FreePhysicalMemory=(%d+)")) or 0
    local total = tonumber(wmic_output:match("TotalVisibleMemorySize=(%d+)")) or 1
    
    local used = total - free
    local percent = math.floor((used / total) * 100)
    
    -- Convert to GB
    local total_gb = total / 1024 / 1024
    local used_gb = used / 1024 / 1024
    
    return percent, used_gb, total_gb
end

-- Get external IP (cached)
local function get_external_ip()
    local now = os.time()
    
    -- Use cache if less than 5 minutes old
    if TBA.cache.external_ip and (now - TBA.cache.ip_timestamp) < 300 then
        return TBA.cache.external_ip
    end
    
    local endpoints = {
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://checkip.amazonaws.com",
    }
    
    for _, endpoint in ipairs(endpoints) do
        local result = exec('curl -s --max-time 2 "' .. endpoint .. '"')
        if result and result:match("^%d+%.%d+%.%d+%.%d+$") then
            TBA.cache.external_ip = result
            TBA.cache.ip_timestamp = now
            return result
        end
    end
    
    return "UNREACHABLE"
end

-- Check if port is open
local function check_port(host, port)
    local result = exec(string.format('powershell -Command "Test-NetConnection -ComputerName %s -Port %d -InformationLevel Quiet -WarningAction SilentlyContinue" 2>nul', host, port))
    return result and result:lower():match("true") ~= nil
end

-- Check if process is running
local function check_process(name)
    local result = exec(string.format('tasklist /FI "IMAGENAME eq %s" 2>nul | find /i "%s"', name, name))
    return result and #result > 0
end

-- Check admin status
local function is_admin()
    local result = exec('net session 2>nul')
    return result ~= nil
end

--------------------------------------------------------------------------------
-- SECTION 3: STATUS INDICATORS
--------------------------------------------------------------------------------

local function status_indicator(status, extended)
    local c = TBA.colors
    if status then
        if extended then
            return c.success .. "● ONLINE" .. c.reset
        else
            return c.success .. "●" .. c.reset
        end
    else
        if extended then
            return c.steel .. "○ OFFLINE" .. c.reset
        else
            return c.steel .. "○" .. c.reset
        end
    end
end

--------------------------------------------------------------------------------
-- SECTION 4: BANNER ART
--------------------------------------------------------------------------------

local BANNER_ART = [[
████████╗██████╗  █████╗     ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗
╚══██╔══╝██╔══██╗██╔══██╗    ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝
   ██║   ██████╔╝███████║    ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗
   ██║   ██╔══██╗██╔══██║    ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║
   ██║   ██████╔╝██║  ██║    ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║
   ╚═╝   ╚═════╝ ╚═╝  ╚═╝    ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝]]

--------------------------------------------------------------------------------
-- SECTION 5: HUD DISPLAY
--------------------------------------------------------------------------------

local function show_hud()
    if TBA.flags.no_banner then return end
    
    local c = TBA.colors
    local width = get_console_width()
    local separator = string.rep("─", width - 4)
    
    -- Clear screen
    os.execute("cls")
    
    -- ══════════════════════════════════════════════════════════════════════════
    -- BANNER
    -- ══════════════════════════════════════════════════════════════════════════
    
    print("")
    for line in BANNER_ART:gmatch("[^\n]+") do
        local glitched = glitch_text(line, 2)
        print(c.virtu_red .. center_text(glitched, width) .. c.reset)
    end
    print("")
    
    -- Tagline
    local tagline = "╔═══ THE BLACK AGENCY ═══╬═══ OPS CENTER V10 ═══╬═══ NEXUS PRIME ═══╗"
    print(c.magenta .. center_text(tagline, width) .. c.reset)
    print("")
    
    -- ══════════════════════════════════════════════════════════════════════════
    -- SYSTEM INFO
    -- ══════════════════════════════════════════════════════════════════════════
    
    -- Gather data
    local operator = os.getenv("USERNAME"):upper()
    local hostname = os.getenv("COMPUTERNAME"):upper()
    local admin = is_admin()
    local priv_level = admin and "ROOT // ELEVATED" or "USER // STANDARD"
    local priv_color = admin and c.error or c.success
    local uptime = get_uptime()
    local ext_ip = get_external_ip()
    
    -- Memory
    local mem_percent, mem_used, mem_total = get_memory_info()
    local mem_bar = progress_bar(mem_percent, 30)
    local mem_color = c.success
    if mem_percent > 85 then mem_color = c.error
    elseif mem_percent > 60 then mem_color = c.warning end
    
    -- Display
    print(string.format("  %s%s%s", c.steel, separator, c.reset))
    print(string.format("  %s│ %sOPERATOR    %s: %s%-20s%s│ %sPRIVILEGE   %s: %s%s%s",
        c.steel, c.nexus_cyan, c.steel, c.ghost, operator, c.steel, c.nexus_cyan, c.steel, priv_color, priv_level, c.reset))
    print(string.format("  %s│ %sHOSTNAME    %s: %s%-20s%s│ %sUPTIME      %s: %s%s%s",
        c.steel, c.nexus_cyan, c.steel, c.ghost, hostname, c.steel, c.nexus_cyan, c.steel, c.warning, uptime, c.reset))
    print(string.format("  %s│ %sNET_UPLINK  %s: %s%s%s",
        c.steel, c.nexus_cyan, c.steel, c.nexus_cyan, ext_ip, c.reset))
    print(string.format("  %s%s%s", c.steel, separator, c.reset))
    
    -- ══════════════════════════════════════════════════════════════════════════
    -- RESOURCE METERS
    -- ══════════════════════════════════════════════════════════════════════════
    
    print(string.format("  %s│ %sMEMORY_GRID %s: [%s%s%s] %s%d%%%s (%.1f / %.1f GB)%s",
        c.steel, c.nexus_cyan, c.steel, mem_color, mem_bar, c.steel, mem_color, mem_percent, c.steel, mem_used, mem_total, c.reset))
    print(string.format("  %s%s%s", c.steel, separator, c.reset))
    
    -- ══════════════════════════════════════════════════════════════════════════
    -- SERVICE STATUS
    -- ══════════════════════════════════════════════════════════════════════════
    
    print(string.format("  %s│ %sSERVICE_MATRIX%s", c.steel, c.magenta, c.reset))
    print(string.format("  %s│%s", c.steel, c.reset))
    
    -- Service checks
    local svc_ollama = check_port("localhost", 11434)
    local svc_docker = check_process("com.docker.backend.exe") or check_process("Docker Desktop.exe")
    local svc_wsl = check_process("wsl.exe") or check_process("wslhost.exe")
    local svc_git = exec("where git 2>nul") ~= nil
    
    print(string.format("  %s│   [%s] %sNEURAL_LINK    [%s] %sDOCKER         [%s] %sWSL            [%s] %sGIT%s",
        c.steel,
        status_indicator(svc_ollama), c.steel,
        status_indicator(svc_docker), c.steel,
        status_indicator(svc_wsl), c.steel,
        status_indicator(svc_git), c.steel,
        c.reset))
    
    print(string.format("  %s%s%s", c.steel, separator, c.reset))
    
    -- ══════════════════════════════════════════════════════════════════════════
    -- SELF-HEAL (Optional)
    -- ══════════════════════════════════════════════════════════════════════════
    
    if not TBA.flags.no_selfheal then
        show_selfheal()
    end
    
    -- ══════════════════════════════════════════════════════════════════════════
    -- FOOTER
    -- ══════════════════════════════════════════════════════════════════════════
    
    print("")
    local footer = string.format("TBA NEXUS PRIME v%d.%d.%d │ CMD │ %s",
        TBA.version.major, TBA.version.minor, TBA.version.patch, os.date("%Y-%m-%d %H:%M:%S"))
    print(c.steel .. center_text(footer, width) .. c.reset)
    print("")
end

--------------------------------------------------------------------------------
-- SECTION 6: SELF-HEAL SUBSYSTEM
--------------------------------------------------------------------------------

local function show_selfheal()
    local c = TBA.colors
    
    print("")
    print(c.magenta .. "╔═══[ SELF-HEAL SEQUENCE ]════════════════════════════════════════════╗" .. c.reset)
    
    -- Docker check
    io.write(string.format("%s║  %s⚙ DOCKER_DAEMON        %s", c.magenta, c.nexus_cyan, c.reset))
    local docker_running = check_process("com.docker.backend.exe")
    if docker_running then
        print(string.format("%s[ACTIVE]%s                                     %s║%s", c.success, c.steel, c.magenta, c.reset))
    else
        -- Try to start Docker Desktop
        local docker_path = os.getenv("ProgramFiles") .. "\\Docker\\Docker\\Docker Desktop.exe"
        if file_exists(docker_path) then
            os.execute('start "" "' .. docker_path .. '" 2>nul')
            print(string.format("%s[INITIATED]%s                                  %s║%s", c.warning, c.steel, c.magenta, c.reset))
        else
            print(string.format("%s[NOT_INSTALLED]%s                              %s║%s", c.steel, c.steel, c.magenta, c.reset))
        end
    end
    
    -- WSL check
    io.write(string.format("%s║  %s⚙ WSL_SUBSYSTEM        %s", c.magenta, c.nexus_cyan, c.reset))
    local wsl_available = exec("wsl --status 2>nul")
    if wsl_available and #wsl_available > 0 then
        print(string.format("%s[ACTIVE]%s                                     %s║%s", c.success, c.steel, c.magenta, c.reset))
    else
        print(string.format("%s[UNAVAILABLE]%s                                %s║%s", c.steel, c.steel, c.magenta, c.reset))
    end
    
    -- Environment check
    io.write(string.format("%s║  %s⚙ PATH_INTEGRITY       %s", c.magenta, c.nexus_cyan, c.reset))
    local path_ok = os.getenv("PATH") and #os.getenv("PATH") > 0
    if path_ok then
        print(string.format("%s[VERIFIED]%s                                   %s║%s", c.success, c.steel, c.magenta, c.reset))
    else
        print(string.format("%s[DEGRADED]%s                                   %s║%s", c.warning, c.steel, c.magenta, c.reset))
    end
    
    print(c.magenta .. "╚═════════════════════════════════════════════════════════════════════╝" .. c.reset)
end

--------------------------------------------------------------------------------
-- SECTION 7: QUICK STATUS FUNCTION
--------------------------------------------------------------------------------

local function show_status()
    local c = TBA.colors
    
    local mem_percent, _, _ = get_memory_info()
    local uptime = get_uptime()
    local ext_ip = TBA.cache.external_ip or "N/A"
    
    local mem_color = c.success
    if mem_percent > 80 then mem_color = c.error end
    
    print("")
    print(c.magenta .. "╔═══[ TBA QUICK STATUS ]═══╗" .. c.reset)
    print(string.format("%s║%s %sOperator%s : %s", c.magenta, c.reset, c.nexus_cyan, c.reset, os.getenv("USERNAME"):upper()))
    print(string.format("%s║%s %sMemory%s   : %s%d%%%s", c.magenta, c.reset, c.nexus_cyan, c.reset, mem_color, mem_percent, c.reset))
    print(string.format("%s║%s %sUptime%s   : %s%s%s", c.magenta, c.reset, c.nexus_cyan, c.reset, c.warning, uptime, c.reset))
    print(string.format("%s║%s %sExtIP%s    : %s%s%s", c.magenta, c.reset, c.nexus_cyan, c.reset, c.nexus_cyan, ext_ip, c.reset))
    print(c.magenta .. "╚══════════════════════════╝" .. c.reset)
    print("")
end

--------------------------------------------------------------------------------
-- SECTION 8: CUSTOM PROMPT
--------------------------------------------------------------------------------

local function tba_prompt_filter()
    local c = TBA.colors
    
    -- Get current directory
    local cwd = os.getcwd()
    local home = os.getenv("USERPROFILE")
    if home and cwd:sub(1, #home) == home then
        cwd = "~" .. cwd:sub(#home + 1)
    end
    
    -- Shorten path if too long
    local max_path_len = 40
    if #cwd > max_path_len then
        local parts = {}
        for part in cwd:gmatch("[^\\]+") do
            table.insert(parts, part)
        end
        if #parts > 3 then
            cwd = parts[1] .. "\\....\\" .. parts[#parts - 1] .. "\\" .. parts[#parts]
        end
    end
    
    -- Check admin status
    local admin = is_admin()
    local admin_indicator = admin and (c.error .. "⚡" .. c.reset) or ""
    
    -- Git branch (if available)
    local git_branch = ""
    local branch = exec("git rev-parse --abbrev-ref HEAD 2>nul")
    if branch and #branch > 0 then
        local dirty = exec("git status --porcelain 2>nul")
        local dirty_indicator = (dirty and #dirty > 0) and "*" or ""
        git_branch = string.format(" %s⎇ %s%s%s", c.virtu_red, branch, dirty_indicator, c.reset)
    end
    
    -- Build prompt
    local line1 = string.format("%s╔══❮%s %s%s%s %s❯%s%s",
        c.virtu_red,
        c.ghost, os.getenv("USERNAME"), c.virtu_red,
        c.chrome, cwd,
        c.reset, git_branch)
    
    local line2 = string.format("%s╚═%s %s%s❯❯%s ",
        c.steel, admin_indicator, c.virtu_red, c.bold, c.reset)
    
    -- Set the prompt
    clink.prompt.value = line1 .. "\n" .. line2
end

-- Register prompt filter
local prompt_filter = clink.promptfilter(10)
function prompt_filter:filter(prompt)
    tba_prompt_filter()
    return nil, false
end

--------------------------------------------------------------------------------
-- SECTION 9: RIGHT PROMPT (Time)
--------------------------------------------------------------------------------

local rprompt_filter = clink.promptfilter(10)
function rprompt_filter:rightfilter(prompt)
    local c = TBA.colors
    return string.format("%s│ %s%s%s", c.steel, c.virtu_red, os.date("%H:%M:%S"), c.reset)
end

--------------------------------------------------------------------------------
-- SECTION 10: CLINK SETTINGS
--------------------------------------------------------------------------------

-- History settings
settings.set("history.dupe_mode", "erase_prev")
settings.set("history.ignore_space", true)
settings.set("history.max_lines", 50000)
settings.set("history.shared", true)

-- Completion settings
settings.set("match.ignore_case", "relaxed")
settings.set("match.sort_dirs", "with")
settings.set("match.wild", true)

-- Color settings
settings.set("color.arg", "bold")
settings.set("color.arginfo", "sgr 38;2;104;110;120")
settings.set("color.cmd", "sgr 1;38;2;230;230;230")
settings.set("color.cmdredir", "sgr 38;2;255;23;68")
settings.set("color.cmdsep", "sgr 38;2;255;23;68")
settings.set("color.comment_row", "sgr 38;2;104;110;120")
settings.set("color.description", "sgr 38;2;104;110;120")
settings.set("color.doskey", "sgr 1;38;2;0;229;255")
settings.set("color.executable", "sgr 1;38;2;230;230;230")
settings.set("color.filtered", "sgr 38;2;104;110;120")
settings.set("color.flag", "sgr 38;2;104;110;120")
settings.set("color.hidden", "sgr 38;2;58;61;68")
settings.set("color.histexpand", "sgr 38;2;213;0;249")
settings.set("color.horizscroll", "sgr 38;2;104;110;120")
settings.set("color.input", "sgr 38;2;230;230;230")
settings.set("color.interact", "bold")
settings.set("color.message", "sgr 38;2;104;110;120")
settings.set("color.popup", "sgr 38;2;230;230;230")
settings.set("color.popup_desc", "sgr 38;2;104;110;120")
settings.set("color.prompt", "sgr 38;2;255;23;68")
settings.set("color.readonly", "sgr 38;2;104;110;120")
settings.set("color.selected_completion", "sgr 48;2;255;23;68")
settings.set("color.selection", "sgr 48;2;58;61;68")
settings.set("color.suggestion", "sgr 38;2;104;110;120")
settings.set("color.unexpected", "sgr 38;2;255;23;68")
settings.set("color.unrecognized", "sgr 38;2;255;23;68")

-- Terminal settings
settings.set("terminal.emulation", "auto")
settings.set("terminal.raw_esc", true)

-- Misc settings
settings.set("clink.autoupdate", true)
settings.set("clink.logo", "none")

--------------------------------------------------------------------------------
-- SECTION 11: KEY BINDINGS
--------------------------------------------------------------------------------

-- Completion
rl.setbinding([["\t"]], [["complete"]])
rl.setbinding([["\e[Z"]], [["menu-complete-backward"]])  -- Shift+Tab
rl.setbinding([[" "]], [["clink-expand-history-and-alias"]])

-- History
rl.setbinding([["\e[A"]], [["history-search-backward"]])  -- Up
rl.setbinding([["\e[B"]], [["history-search-forward"]])   -- Down
rl.setbinding([["\C-r"]], [["reverse-search-history"]])
rl.setbinding([["\C-s"]], [["forward-search-history"]])

-- Editing
rl.setbinding([["\C-u"]], [["unix-line-discard"]])
rl.setbinding([["\C-k"]], [["kill-line"]])
rl.setbinding([["\C-w"]], [["backward-kill-word"]])
rl.setbinding([["\e d"]], [["kill-word"]])  -- Alt+D
rl.setbinding([["\C-l"]], [["clear-screen"]])
rl.setbinding([["\C-a"]], [["beginning-of-line"]])
rl.setbinding([["\C-e"]], [["end-of-line"]])

-- Word movement
rl.setbinding([["\e[1;5C"]], [["forward-word"]])   -- Ctrl+Right
rl.setbinding([["\e[1;5D"]], [["backward-word"]])  -- Ctrl+Left

-- Undo/Redo
rl.setbinding([["\C-z"]], [["undo"]])
rl.setbinding([["\C-y"]], [["yank"]])

--------------------------------------------------------------------------------
-- SECTION 12: CUSTOM COMMANDS
--------------------------------------------------------------------------------

-- TBA HUD command
local function tba_cmd(arg)
    show_hud()
end

-- TBA Status command
local function tbastatus_cmd(arg)
    show_status()
end

-- TBA Refresh command  
local function tbarefresh_cmd(arg)
    TBA.cache.external_ip = nil
    TBA.cache.ip_timestamp = 0
    get_external_ip()  -- Force refresh
    show_hud()
end

-- Register commands as doskeys
os.execute('doskey tba=clink lua -e "require(\'tba_nexus\').show_hud()"')
os.execute('doskey tbastatus=clink lua -e "require(\'tba_nexus\').show_status()"')
os.execute('doskey tbarefresh=clink lua -e "require(\'tba_nexus\').refresh()"')

--------------------------------------------------------------------------------
-- SECTION 13: ALIASES
--------------------------------------------------------------------------------

local aliases = {
    -- Navigation
    [".."]     = "cd ..",
    ["..."]    = "cd ..\\..",
    ["...."]   = "cd ..\\..\\..",
    ["~"]      = "cd %USERPROFILE%",
    
    -- Listing
    ["ls"]     = "dir /b",
    ["ll"]     = "dir",
    ["la"]     = "dir /a",
    ["lt"]     = "dir /od",
    
    -- Safety (sort of)
    ["rm"]     = "del /p",
    ["cp"]     = "copy",
    ["mv"]     = "move",
    
    -- Git
    ["g"]      = "git",
    ["ga"]     = "git add",
    ["gaa"]    = "git add --all",
    ["gc"]     = "git commit -v",
    ["gcm"]    = "git commit -m",
    ["gco"]    = "git checkout",
    ["gcb"]    = "git checkout -b",
    ["gd"]     = "git diff",
    ["gds"]    = "git diff --staged",
    ["gf"]     = "git fetch",
    ["gl"]     = "git pull",
    ["gp"]     = "git push",
    ["gst"]    = "git status",
    ["glog"]   = "git log --oneline --decorate --graph",
    
    -- Docker
    ["d"]      = "docker",
    ["dc"]     = "docker compose",
    ["dps"]    = "docker ps",
    ["dpsa"]   = "docker ps -a",
    ["di"]     = "docker images",
    
    -- System
    ["cls"]    = "cls",
    ["c"]      = "cls",
    ["h"]      = "doskey /history",
    ["path"]   = "echo %PATH%",
    ["ip"]     = "ipconfig",
    ["ports"]  = "netstat -an",
    ["proc"]   = "tasklist",
    ["kill"]   = "taskkill /F /IM",
    
    -- Utils
    ["reload"] = "clink inject",
    ["edit"]   = "notepad",
    ["open"]   = "explorer",
    ["myip"]   = "curl -s https://api.ipify.org && echo.",
    
    -- PowerShell
    ["ps"]     = "powershell",
    ["pwsh"]   = "pwsh",
    
    -- WSL
    ["wsl"]    = "wsl",
    ["ubuntu"] = "wsl -d Ubuntu",
    ["kali"]   = "wsl -d kali-linux",
}

-- Apply aliases
for alias, command in pairs(aliases) do
    os.execute(string.format('doskey %s=%s $*', alias, command))
end

--------------------------------------------------------------------------------
-- SECTION 14: COMPLETIONS
--------------------------------------------------------------------------------

-- Git completions
local git_commands = {
    "add", "bisect", "branch", "checkout", "clone", "commit", "diff",
    "fetch", "grep", "init", "log", "merge", "mv", "pull", "push",
    "rebase", "reset", "restore", "rm", "show", "stash", "status",
    "switch", "tag"
}

local git_generator = clink.generator(10)
function git_generator:generate(line_state, match_builder)
    if line_state:getword(1) ~= "git" then return false end
    if line_state:getwordcount() == 2 then
        for _, cmd in ipairs(git_commands) do
            match_builder:addmatch(cmd)
        end
        return true
    end
    return false
end

-- Docker completions
local docker_commands = {
    "attach", "build", "commit", "compose", "cp", "create", "diff",
    "events", "exec", "export", "history", "image", "images", "import",
    "info", "inspect", "kill", "load", "login", "logout", "logs",
    "network", "pause", "port", "ps", "pull", "push", "rename",
    "restart", "rm", "rmi", "run", "save", "search", "start", "stats",
    "stop", "tag", "top", "unpause", "update", "version", "volume", "wait"
}

local docker_generator = clink.generator(10)
function docker_generator:generate(line_state, match_builder)
    local word1 = line_state:getword(1)
    if word1 ~= "docker" and word1 ~= "d" then return false end
    if line_state:getwordcount() == 2 then
        for _, cmd in ipairs(docker_commands) do
            match_builder:addmatch(cmd)
        end
        return true
    end
    return false
end

--------------------------------------------------------------------------------
-- SECTION 15: STARTUP
--------------------------------------------------------------------------------

-- Export functions for external use
TBA.show_hud = show_hud
TBA.show_status = show_status
TBA.refresh = function()
    TBA.cache.external_ip = nil
    TBA.cache.ip_timestamp = 0
    get_external_ip()
    show_hud()
end

-- Show HUD on startup
if not TBA.flags.no_banner then
    show_hud()
end

-- Return module for require()
return TBA

--------------------------------------------------------------------------------
-- END OF TBA NEXUS PRIME CMD V10
--------------------------------------------------------------------------------
```

---

## Clink Settings File: `%LOCALAPPDATA%\clink\clink_settings`

```ini
# TBA NEXUS PRIME — Clink Settings
# This file is auto-generated but can be manually edited

# History
history.dupe_mode                = erase_prev
history.ignore_space             = true
history.max_lines                = 50000
history.shared                   = true
history.time_stamp               = show

# Matching
match.ignore_case                = relaxed
match.sort_dirs                  = with
match.wild                       = true
match.expand_envvars             = true

# Colors (TBA-Nexus-Prime palette)
color.arg                        = bold
color.arginfo                    = sgr 38;2;104;110;120
color.cmd                        = sgr 1;38;2;230;230;230
color.cmdredir                   = sgr 38;2;255;23;68
color.cmdsep                     = sgr 38;2;255;23;68
color.comment_row                = sgr 38;2;104;110;120
color.description                = sgr 38;2;104;110;120
color.doskey                     = sgr 1;38;2;0;229;255
color.executable                 = sgr 1;38;2;230;230;230
color.filtered                   = sgr 38;2;104;110;120
color.flag                       = sgr 38;2;104;110;120
color.hidden                     = sgr 38;2;58;61;68
color.histexpand                 = sgr 38;2;213;0;249
color.horizscroll                = sgr 38;2;104;110;120
color.input                      = sgr 38;2;230;230;230
color.message                    = sgr 38;2;104;110;120
color.popup                      = sgr 38;2;230;230;230
color.popup_desc                 = sgr 38;2;104;110;120
color.prompt                     = sgr 38;2;255;23;68
color.readonly                   = sgr 38;2;104;110;120
color.selected_completion        = sgr 48;2;255;23;68
color.selection                  = sgr 48;2;58;61;68
color.suggestion                 = sgr 38;2;104;110;120
color.unexpected                 = sgr 38;2;255;23;68
color.unrecognized               = sgr 38;2;255;23;68

# Terminal
terminal.emulation               = auto
terminal.raw_esc                 = true

# Clink
clink.autoupdate                 = true
clink.logo                       = none
clink.path                       = %LOCALAPPDATA%\clink
clink.promptfilter               = true

# Editing
edit.blink_matching_paren        = true

# Readline
readline.hide_stderr             = true
```

---

## Batch Initialization Script: `%LOCALAPPDATA%\TheBlackAgency\CMD\tba_init.cmd`

```batch
@echo off
:: ╔════════════════════════════════════════════════════════════════════════════╗
:: ║  TBA NEXUS PRIME — CMD Initialization Script                               ║
:: ╚════════════════════════════════════════════════════════════════════════════╝

:: Enable ANSI colors
reg add HKCU\Console /v VirtualTerminalLevel /t REG_DWORD /d 1 /f >nul 2>&1

:: Set console code page to UTF-8
chcp 65001 >nul 2>&1

:: Set TBA environment variables
set TBA_ROOT=%LOCALAPPDATA%\TheBlackAgency
set TBA_VERSION=10.0.0
set TBA_BUILD=NEXUS_PRIME_CMD

:: Add TBA to PATH if not present
echo %PATH% | find /i "%TBA_ROOT%\CMD" >nul 2>&1
if errorlevel 1 (
    set PATH=%PATH%;%TBA_ROOT%\CMD
)

:: Inject Clink (if not already running)
where clink >nul 2>&1
if %errorlevel% equ 0 (
    clink inject --quiet 2>nul
)

:: Set window title
title TBA // NEXUS PRIME

:: Done
exit /b 0
```

---

## AutoRun Registry Setup: `tba_autorun.reg`

```registry
Windows Registry Editor Version 5.00

; TBA NEXUS PRIME — CMD AutoRun Configuration
; This enables TBA initialization for all CMD instances

[HKEY_CURRENT_USER\Software\Microsoft\Command Processor]
"AutoRun"="%LOCALAPPDATA%\\TheBlackAgency\\CMD\\tba_init.cmd"

; Enable ANSI colors in console
[HKEY_CURRENT_USER\Console]
"VirtualTerminalLevel"=dword:00000001
```

---

## Additional Completions: `%LOCALAPPDATA%\clink\tba_completions.lua`

```lua
--[[
╔════════════════════════════════════════════════════════════════════════════╗
║  TBA NEXUS PRIME — Extended Completions                                    ║
╚════════════════════════════════════════════════════════════════════════════╝
--]]

--------------------------------------------------------------------------------
-- NPM COMPLETIONS
--------------------------------------------------------------------------------

local npm_commands = {
    "access", "adduser", "audit", "bin", "bugs", "cache", "ci", "completion",
    "config", "dedupe", "deprecate", "diff", "dist-tag", "docs", "doctor",
    "edit", "exec", "explain", "explore", "find-dupes", "fund", "get",
    "help", "help-search", "hook", "init", "install", "install-ci-test",
    "install-test", "link", "ll", "login", "logout", "ls", "org", "outdated",
    "owner", "pack", "ping", "pkg", "prefix", "profile", "prune", "publish",
    "rebuild", "repo", "restart", "root", "run", "run-script", "search",
    "set", "shrinkwrap", "star", "stars", "start", "stop", "team", "test",
    "token", "uninstall", "unpublish", "unstar", "update", "version", "view",
    "whoami"
}

local npm_generator = clink.generator(20)
function npm_generator:generate(line_state, match_builder)
    if line_state:getword(1) ~= "npm" then return false end
    if line_state:getwordcount() == 2 then
        for _, cmd in ipairs(npm_commands) do
            match_builder:addmatch(cmd)
        end
        return true
    end
    return false
end

--------------------------------------------------------------------------------
-- KUBECTL COMPLETIONS
--------------------------------------------------------------------------------

local kubectl_commands = {
    "alpha", "annotate", "api-resources", "api-versions", "apply", "attach",
    "auth", "autoscale", "certificate", "cluster-info", "completion", "config",
    "cordon", "cp", "create", "debug", "delete", "describe", "diff", "drain",
    "edit", "exec", "explain", "expose", "get", "kustomize", "label", "logs",
    "patch", "plugin", "port-forward", "proxy", "replace", "rollout", "run",
    "scale", "set", "taint", "top", "uncordon", "version", "wait"
}

local kubectl_generator = clink.generator(20)
function kubectl_generator:generate(line_state, match_builder)
    local word1 = line_state:getword(1)
    if word1 ~= "kubectl" and word1 ~= "k" then return false end
    if line_state:getwordcount() == 2 then
        for _, cmd in ipairs(kubectl_commands) do
            match_builder:addmatch(cmd)
        end
        return true
    end
    return false
end

--------------------------------------------------------------------------------
-- WINGET COMPLETIONS
--------------------------------------------------------------------------------

local winget_commands = {
    "install", "show", "source", "search", "list", "upgrade", "uninstall",
    "hash", "validate", "settings", "features", "export", "import", "pin",
    "configure", "download"
}

local winget_generator = clink.generator(20)
function winget_generator:generate(line_state, match_builder)
    if line_state:getword(1) ~= "winget" then return false end
    if line_state:getwordcount() == 2 then
        for _, cmd in ipairs(winget_commands) do
            match_builder:addmatch(cmd)
        end
        return true
    end
    return false
end

--------------------------------------------------------------------------------
-- SCOOP COMPLETIONS
--------------------------------------------------------------------------------

local scoop_commands = {
    "alias", "bucket", "cache", "cat", "checkup", "cleanup", "config",
    "create", "depends", "download", "export", "help", "hold", "home",
    "import", "info", "install", "list", "prefix", "reset", "search",
    "shim", "status", "unhold", "uninstall", "update", "virustotal", "which"
}

local scoop_generator = clink.generator(20)
function scoop_generator:generate(line_state, match_builder)
    if line_state:getword(1) ~= "scoop" then return false end
    if line_state:getwordcount() == 2 then
        for _, cmd in ipairs(scoop_commands) do
            match_builder:addmatch(cmd)
        end
        return true
    end
    return false
end

--------------------------------------------------------------------------------
-- CHOCO COMPLETIONS
--------------------------------------------------------------------------------

local choco_commands = {
    "config", "download", "export", "feature", "find", "help", "info",
    "install", "list", "new", "outdated", "pack", "pin", "push", "search",
    "setapikey", "source", "template", "uninstall", "unpackself", "upgrade"
}

local choco_generator = clink.generator(20)
function choco_generator:generate(line_state, match_builder)
    local word1 = line_state:getword(1)
    if word1 ~= "choco" and word1 ~= "chocolatey" then return false end
    if line_state:getwordcount() == 2 then
        for _, cmd in ipairs(choco_commands) do
            match_builder:addmatch(cmd)
        end
        return true
    end
    return false
end

--------------------------------------------------------------------------------
-- DOTNET COMPLETIONS
--------------------------------------------------------------------------------

local dotnet_commands = {
    "add", "build", "build-server", "clean", "format", "help", "list",
    "msbuild", "new", "nuget", "pack", "publish", "remove", "restore",
    "run", "sdk", "sln", "store", "test", "tool", "vstest", "watch",
    "workload"
}

local dotnet_generator = clink.generator(20)
function dotnet_generator:generate(line_state, match_builder)
    if line_state:getword(1) ~= "dotnet" then return false end
    if line_state:getwordcount() == 2 then
        for _, cmd in ipairs(dotnet_commands) do
            match_builder:addmatch(cmd)
        end
        return true
    end
    return false
end

--------------------------------------------------------------------------------
-- AZ (Azure CLI) COMPLETIONS
--------------------------------------------------------------------------------

local az_commands = {
    "account", "acr", "ad", "advisor", "aks", "apim", "appconfig",
    "appservice", "backup", "batch", "billing", "bot", "cache", "cdn",
    "cloud", "cognitiveservices", "configure", "consumption", "container",
    "cosmosdb", "deployment", "disk", "dla", "dls", "dms", "eventgrid",
    "eventhubs", "extension", "feature", "feedback", "find", "functionapp",
    "group", "hdinsight", "identity", "image", "interactive", "iot",
    "keyvault", "kusto", "lab", "lock", "login", "logout", "managed-cassandra",
    "managedapp", "managedservices", "maps", "mariadb", "ml", "monitor",
    "mysql", "netappfiles", "network", "policy", "postgres", "ppg",
    "provider", "redis", "relay", "reservations", "resource", "rest",
    "role", "search", "security", "servicebus", "sf", "sig", "signalr",
    "snapshot", "sql", "sshkey", "staticwebapp", "storage", "synapse",
    "tag", "term", "ts", "upgrade", "version", "vm", "vmss", "webapp"
}

local az_generator = clink.generator(20)
function az_generator:generate(line_state, match_builder)
    if line_state:getword(1) ~= "az" then return false end
    if line_state:getwordcount() == 2 then
        for _, cmd in ipairs(az_commands) do
            match_builder:addmatch(cmd)
        end
        return true
    end
    return false
end

--------------------------------------------------------------------------------
-- WSL COMPLETIONS
--------------------------------------------------------------------------------

local wsl_commands = {
    "--help", "--install", "--list", "--set-default", "--set-default-version",
    "--set-version", "--shutdown", "--status", "--terminate", "--unregister",
    "--update", "--export", "--import", "--distribution", "-d", "-l", "-s",
    "-t", "-u", "--user", "--cd", "--exec", "-e"
}

local wsl_distros = {
    "Ubuntu", "Ubuntu-20.04", "Ubuntu-22.04", "Ubuntu-24.04",
    "Debian", "kali-linux", "openSUSE-Leap-15.5", "SLES-15",
    "Alpine", "Fedora"
}

local wsl_generator = clink.generator(20)
function wsl_generator:generate(line_state, match_builder)
    if line_state:getword(1) ~= "wsl" then return false end
    
    local word_count = line_state:getwordcount()
    local current_word = line_state:getword(word_count)
    
    if word_count == 2 then
        if current_word:sub(1, 1) == "-" then
            for _, opt in ipairs(wsl_commands) do
                match_builder:addmatch(opt)
            end
        end
        return true
    end
    
    -- After -d flag, suggest distros
    local prev_word = line_state:getword(word_count - 1)
    if prev_word == "-d" or prev_word == "--distribution" then
        for _, distro in ipairs(wsl_distros) do
            match_builder:addmatch(distro)
        end
        return true
    end
    
    return false
end

--------------------------------------------------------------------------------
-- TBA COMMAND COMPLETIONS
--------------------------------------------------------------------------------

local tba_commands = {
    "tba", "tbastatus", "tbarefresh"
}

local tba_generator = clink.generator(5)
function tba_generator:generate(line_state, match_builder)
    local word = line_state:getword(1)
    if line_state:getwordcount() == 1 and word:sub(1, 3) == "tba" then
        for _, cmd in ipairs(tba_commands) do
            match_builder:addmatch(cmd)
        end
        return true
    end
    return false
end

print("TBA Completions loaded: npm, kubectl, winget, scoop, choco, dotnet, az, wsl")
```

---

## Installation Summary

<details>
<summary><strong>📦 Complete Installation Steps</strong></summary>

```powershell
# Run as Administrator in PowerShell

# 1. Install Clink
winget install chrisant996.Clink

# 2. Create TBA directories
$tbaDirs = @(
    "$env:LOCALAPPDATA\TheBlackAgency\CMD",
    "$env:LOCALAPPDATA\TheBlackAgency\CMD\scripts",
    "$env:LOCALAPPDATA\TheBlackAgency\Cache",
    "$env:LOCALAPPDATA\TheBlackAgency\Logs",
    "$env:LOCALAPPDATA\clink"
)
$tbaDirs | ForEach-Object { New-Item -ItemType Directory -Path $_ -Force }

# 3. Enable ANSI colors
Set-ItemProperty -Path "HKCU:\Console" -Name "VirtualTerminalLevel" -Value 1 -Type DWord

# 4. Copy configuration files:
#    - tba_nexus.lua -> %LOCALAPPDATA%\clink\
#    - tba_completions.lua -> %LOCALAPPDATA%\clink\
#    - clink_settings -> %LOCALAPPDATA%\clink\
#    - tba_init.cmd -> %LOCALAPPDATA%\TheBlackAgency\CMD\

# 5. Set CMD AutoRun (optional)
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Command Processor" -Name "AutoRun" -Value "%LOCALAPPDATA%\TheBlackAgency\CMD\tba_init.cmd"

# 6. Restart CMD or run:
clink inject
```

</details>

<details>
<summary><strong>⌨️ Keybinding Reference</strong></summary>

| Action | Keybinding |
|--------|------------|
| Complete | `Tab` |
| Reverse Complete | `Shift+Tab` |
| History Search Up | `↑` |
| History Search Down | `↓` |
| Reverse Search | `Ctrl+R` |
| Forward Search | `Ctrl+S` |
| Kill Line Backward | `Ctrl+U` |
| Kill Line Forward | `Ctrl+K` |
| Kill Word Backward | `Ctrl+W` |
| Kill Word Forward | `Alt+D` |
| Clear Screen | `Ctrl+L` |
| Beginning of Line | `Ctrl+A` |
| End of Line | `Ctrl+E` |
| Forward Word | `Ctrl+Right` |
| Backward Word | `Ctrl+Left` |
| Undo | `Ctrl+Z` |

</details>

<details>
<summary><strong>🎨 Theme Matching</strong></summary>

| Element | PowerShell | CMD |
|---------|------------|-----|
| Prompt Start | `╔══❮` | `╔══❮` |
| Prompt End | `╚═ ⚡ ❯❯` | `╚═ ⚡ ❯❯` |
| Git Branch | `⎇ branch*` | `⎇ branch*` |
| Time Format | `HH:MM:SS` | `HH:MM:SS` |
| Colors | Virtu Red/Nexus Cyan | Virtu Red/Nexus Cyan |

</details>

<details>
<summary><strong>🛠️ TBA Commands</strong></summary>

| Command | Description |
|---------|-------------|
| `tba` | Display full HUD |
| `tbastatus` | Quick status check |
| `tbarefresh` | Force refresh with new data |

</details>

<details>
<summary><strong>📝 Aliases Available</strong></summary>

**Navigation:**
- `..` → `cd ..`
- `...` → `cd ..\..`
- `~` → `cd %USERPROFILE%`

**Git:**
- `g` → `git`
- `ga` → `git add`
- `gc` → `git commit -v`
- `gst` → `git status`
- `glog` → `git log --oneline --decorate --graph`

**Docker:**
- `d` → `docker`
- `dc` → `docker compose`
- `dps` → `docker ps`

**System:**
- `cls` / `c` → Clear screen
- `h` → `doskey /history`
- `myip` → Show external IP
- `reload` → `clink inject`

</details>

---

## Environment Variables

```batch
:: Add to system or user environment variables

:: Disable banner on startup
set TBA_NO_BANNER=1

:: Disable self-heal sequence
set TBA_NO_SELFHEAL=1

:: Disable glitch effects
set TBA_NO_GLITCH=1

:: Enable debug output
set TBA_DEBUG=1
```

Or via PowerShell:

```powershell
[Environment]::SetEnvironmentVariable("TBA_NO_BANNER", "1", "User")
[Environment]::SetEnvironmentVariable("TBA_NO_SELFHEAL", "1", "User")
[Environment]::SetEnvironmentVariable("TBA_NO_GLITCH", "1", "User")
```

---

## Windows Terminal Profile for CMD

Add this to your Windows Terminal `settings.json` profiles list:

```json
{
    "guid": "{tba-cmd-nexus}",
    "name": "⬛ TBA CMD",
    "commandline": "cmd.exe /k \"%LOCALAPPDATA%\\TheBlackAgency\\CMD\\tba_init.cmd\"",
    "icon": "⬛",
    "colorScheme": "TBA-Nexus-Prime",
    "font": {
        "face": "CaskaydiaCove Nerd Font",
        "size": 11
    },
    "opacity": 90,
    "useAcrylic": true,
    "padding": "14, 16, 14, 16",
    "startingDirectory": "%USERPROFILE%",
    "bellStyle": "none",
    "hidden": false
}
```