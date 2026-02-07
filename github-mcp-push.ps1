# GitHub MCP-style Issue Push Script
# Pushes all remaining issues from CSV to GitHub
# Author: B0LK13
# Date: 2026-02-03

param(
    [switch]$DryRun,
    [switch]$SkipConfirm,
    [string]$Repo = "B0LK13/obsidian-agent",
    [string]$CsvPath = "github-issues-import.csv"
)

# Configuration
$DelaySeconds = 2
$AlreadyCreated = @(
    "FEAT: Implement Incremental Indexing Mechanism",
    "FEAT: Implement Vector Database Layer for Semantic Search", 
    "FEAT: Implement Caching and Optimization Layer",
    "FEAT: Implement Dead Link Detection and Repair",
    "REFACTOR: Implement Defensive Coding and Error Handling",
    "FEAT: Implement Automated Link Suggestions"
)

# Colors
$ColorHeader = "Cyan"
$ColorSuccess = "Green"
$ColorWarning = "Yellow"
$ColorError = "Red"
$ColorInfo = "White"

function Write-Header {
    param([string]$Text)
    Write-Host "`n========================================" -ForegroundColor $ColorHeader
    Write-Host $Text -ForegroundColor $ColorHeader
    Write-Host "========================================`n" -ForegroundColor $ColorHeader
}

function Write-Status {
    param([string]$Status, [string]$Message, [string]$Color = $ColorInfo)
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] [$Status] " -NoNewline -ForegroundColor $Color
    Write-Host $Message
}

function Test-GitHubAuth {
    Write-Status "CHECK" "Verifying GitHub authentication..." $ColorInfo
    $status = gh auth status 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Status "OK" "GitHub CLI authenticated" $ColorSuccess
        return $true
    } else {
        Write-Status "FAIL" "GitHub CLI not authenticated. Run: gh auth login" $ColorError
        return $false
    }
}

function Import-Issues {
    param([array]$Issues)
    
    $total = $Issues.Count
    $created = 0
    $skipped = 0
    $failed = 0
    
    Write-Header "Importing $total Issues to $Repo"
    
    for ($i = 0; $i -lt $Issues.Count; $i++) {
        $issue = $Issues[$i]
        $current = $i + 1
        $title = $issue.title.Trim('"')
        $body = $issue.body.Trim('"').Replace('""', '"')
        $labels = $issue.labels.Trim('"')
        $milestone = if ($issue.milestone) { $issue.milestone.Trim('"') } else { "" }
        
        # Skip already created
        if ($AlreadyCreated -contains $title) {
            Write-Status "SKIP" "[$current/$total] $title" $ColorWarning
            $skipped++
            continue
        }
        
        Write-Status "CREATE" "[$current/$total] $title" $ColorInfo
        
        if ($DryRun) {
            Write-Host "  [DRY RUN] Would create issue with labels: $labels" -ForegroundColor $ColorWarning
            $created++
            continue
        }
        
        try {
            # Build command
            $cmd = @(
                "issue", "create",
                "--repo", $Repo,
                "--title", $title,
                "--body", $body,
                "--label", $labels
            )
            
            # Execute
            $result = gh @cmd 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Status "OK" "Created: $result" $ColorSuccess
                $created++
            } else {
                Write-Status "FAIL" "Error: $result" $ColorError
                $failed++
            }
        }
        catch {
            Write-Status "ERROR" "Exception: $_" $ColorError
            $failed++
        }
        
        # Rate limiting
        if ($current -lt $total) {
            Start-Sleep -Seconds $DelaySeconds
        }
    }
    
    # Summary
    Write-Header "Import Complete"
    Write-Host "Total: $total" -ForegroundColor $ColorInfo
    Write-Host "Created: $created" -ForegroundColor $ColorSuccess
    Write-Host "Skipped: $skipped" -ForegroundColor $ColorWarning
    Write-Host "Failed: $failed" -ForegroundColor $ColorError
    
    if ($failed -gt 0) {
        exit 1
    }
}

# Main
Write-Header "GitHub Issues MCP Push"

# Check GitHub auth
if (-not (Test-GitHubAuth)) {
    exit 1
}

# Check CSV exists
if (-not (Test-Path $CsvPath)) {
    Write-Status "ERROR" "CSV file not found: $CsvPath" $ColorError
    exit 1
}

# Read CSV
Write-Status "LOAD" "Reading issues from $CsvPath..." $ColorInfo
$issues = Import-Csv -Path $CsvPath
$totalIssues = $issues.Count
$remainingIssues = $issues | Where-Object { $AlreadyCreated -notcontains $_.title.Trim('"') }

Write-Status "INFO" "Total in CSV: $totalIssues" $ColorInfo
Write-Status "INFO" "Already created: $($totalIssues - $remainingIssues.Count)" $ColorWarning
Write-Status "INFO" "Remaining to push: $($remainingIssues.Count)" $ColorSuccess

if ($remainingIssues.Count -eq 0) {
    Write-Status "DONE" "All issues already created!" $ColorSuccess
    exit 0
}

# Confirm
if (-not $SkipConfirm -and -not $DryRun) {
    Write-Host "`nReady to push $($remainingIssues.Count) issues to $Repo" -ForegroundColor $ColorWarning
    $confirm = Read-Host "Continue? (yes/no)"
    if ($confirm -ne "yes") {
        Write-Status "ABORT" "User cancelled" $ColorWarning
        exit 0
    }
}

# Import
Import-Issues -Issues $issues
