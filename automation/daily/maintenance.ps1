# Daily Development Environment Maintenance
# Scheduled to run daily at 6 AM
# Logs to F:\DevDrive\logs\maintenance-YYYY-MM-DD.log

$ErrorActionPreference = "Continue"
$logDir = "F:\DevDrive\logs"
$logFile = "$logDir\maintenance-$(Get-Date -Format 'yyyy-MM-dd').log"

# Ensure log directory exists
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logEntry = "[$timestamp] [$Level] $Message"
    $logEntry | Tee-Object -FilePath $logFile -Append
}

Log "========================================" 
Log "Daily Maintenance Started"
Log "========================================"

# 1. Docker Cleanup
Log "Pruning Docker containers..."
$containerResult = docker container prune -f 2>&1
Log "Containers: $containerResult"

Log "Pruning Docker images..."
$imageResult = docker image prune -f 2>&1
Log "Images: $imageResult"

# 2. Check Container Health
Log "Checking container health..."
$unhealthy = docker ps --filter "health=unhealthy" --format "{{.Names}}" 2>&1
if ($unhealthy) {
    Log "WARNING: Unhealthy containers detected: $unhealthy" "WARN"
} else {
    Log "All containers healthy"
}

# 3. Disk Space Check
Log "Checking disk space..."
$drives = Get-Volume | Where-Object { $_.DriveLetter -and $_.SizeRemaining -lt 50GB }
foreach ($drive in $drives) {
    $freeGB = [math]::Round($drive.SizeRemaining / 1GB, 1)
    Log "WARNING: Drive $($drive.DriveLetter): has only ${freeGB}GB free" "WARN"
}

# 4. MCP Server Status
Log "Checking MCP servers..."
$mcpStatus = docker mcp server ls 2>&1 | Select-Object -First 5
Log "MCP Status: $($mcpStatus -join ' | ')"

# 5. Update MCP Catalog (weekly on Sundays)
if ((Get-Date).DayOfWeek -eq 'Sunday') {
    Log "Updating MCP catalog..."
    docker mcp catalog update 2>&1 | Out-Null
    Log "MCP catalog updated"
}

# 6. Clean old logs (keep 30 days)
Log "Cleaning old logs..."
$oldLogs = Get-ChildItem "$logDir\*.log" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) }
if ($oldLogs) {
    $oldLogs | Remove-Item -Force
    Log "Removed $($oldLogs.Count) old log files"
}

# 7. Git garbage collection (weekly on Saturdays)
if ((Get-Date).DayOfWeek -eq 'Saturday') {
    Log "Running Git garbage collection..."
    $gitDirs = Get-ChildItem -Path "C:\Users\Admin\Documents" -Filter ".git" -Recurse -Directory -ErrorAction SilentlyContinue | Select-Object -First 10
    foreach ($gitDir in $gitDirs) {
        $repoPath = Split-Path $gitDir.FullName -Parent
        Push-Location $repoPath
        git gc --auto 2>&1 | Out-Null
        Pop-Location
    }
    Log "Git GC completed for $($gitDirs.Count) repositories"
}

# 8. System Resource Summary
Log "System Resource Summary:"
$memory = Get-CimInstance Win32_OperatingSystem
$memUsed = [math]::Round(($memory.TotalVisibleMemorySize - $memory.FreePhysicalMemory) / 1MB, 1)
$memTotal = [math]::Round($memory.TotalVisibleMemorySize / 1MB, 1)
Log "  Memory: ${memUsed}GB / ${memTotal}GB used"

$dockerDf = docker system df --format "{{.Type}}: {{.Size}} ({{.Reclaimable}} reclaimable)" 2>&1
Log "  Docker: $($dockerDf -join ', ')"

Log "========================================"
Log "Daily Maintenance Completed"
Log "========================================"
