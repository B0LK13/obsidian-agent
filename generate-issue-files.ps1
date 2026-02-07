# Manual GitHub Issues Creator (No GitHub CLI required)
# This script generates individual issue files that can be copy-pasted to GitHub

Write-Host "=== B0LK13v2 GitHub Issues Generator ===" -ForegroundColor Cyan
Write-Host "This script will create markdown files for each issue that you can manually create on GitHub" -ForegroundColor White
Write-Host ""

# Create issues directory
$issuesDir = "github-issues"
if (-not (Test-Path $issuesDir)) {
    New-Item -ItemType Directory -Path $issuesDir | Out-Null
    Write-Host "Created directory: $issuesDir" -ForegroundColor Green
}

# Import CSV
$csv = Import-Csv -Path "github-issues-import.csv"
$issueCount = 0

Write-Host "Processing $($csv.Count) issues..." -ForegroundColor Green
Write-Host ""

# Group issues by milestone
$issuesByMilestone = $csv | Group-Object -Property milestone

foreach ($group in $issuesByMilestone) {
    $milestone = $group.Name
    $milestoneDir = Join-Path $issuesDir $milestone
    
    if (-not (Test-Path $milestoneDir)) {
        New-Item -ItemType Directory -Path $milestoneDir | Out-Null
    }
    
    Write-Host "Processing milestone: $milestone ($($group.Count) issues)" -ForegroundColor Cyan
    
    foreach ($issue in $group.Group) {
        $issueCount++
        
        # Clean filename
        $filename = $issue.title -replace '[\\/:*?"<>|]', '-'
        $filename = "$issueCount. $filename.md"
        $filepath = Join-Path $milestoneDir $filename
        
        # Create issue content
        $content = @"
# $($issue.title)

**Labels:** $($issue.labels)  
**Milestone:** $($issue.milestone)

---

$($issue.body)

---

## To Create This Issue on GitHub:

1. Go to: https://github.com/YOUR-USERNAME/YOUR-REPO/issues/new
2. Copy the title above (without the #)
3. Copy the body content above (between the --- lines)
4. Add labels: $($issue.labels)
5. Set milestone: $($issue.milestone)
6. Click "Submit new issue"

"@
        
        $content | Out-File -FilePath $filepath -Encoding UTF8
        Write-Host "  ✅ Created: $filename" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "✅ Generated $issueCount issue files in: $issuesDir" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Create a GitHub repository if you haven't already" -ForegroundColor White
Write-Host "2. Open the issue files in the '$issuesDir' folder" -ForegroundColor White
Write-Host "3. Copy and paste each issue to GitHub" -ForegroundColor White
Write-Host ""
Write-Host "OR install GitHub CLI for automatic creation:" -ForegroundColor Yellow
Write-Host "  1. Download from: https://cli.github.com/" -ForegroundColor White
Write-Host "  2. Run: gh auth login" -ForegroundColor White
Write-Host "  3. Run: .\setup-github-issues.ps1" -ForegroundColor White
Write-Host ""

# Create a summary file
$summaryPath = Join-Path $issuesDir "00-SUMMARY.md"
$summary = @"
# Issues Summary

**Total Issues:** $issueCount

## By Milestone

"@

foreach ($group in $issuesByMilestone | Sort-Object Name) {
    $summary += "`n### $($group.Name) ($($group.Count) issues)`n`n"
    $num = 1
    foreach ($issue in $group.Group) {
        $summary += "$num. **$($issue.title)** - Labels: $($issue.labels)`n"
        $num++
    }
}

$summary += @"

---

## Quick Start

### Option 1: Manual Creation
1. Navigate through the milestone folders
2. Open each .md file
3. Follow the instructions in each file to create the issue on GitHub

### Option 2: GitHub CLI (Recommended)
1. Install GitHub CLI from https://cli.github.com/
2. Run: ``gh auth login``
3. Run: ``.\setup-github-issues.ps1``

### Option 3: GitHub API Script
If you're comfortable with REST APIs, you can use the GitHub API to bulk create these issues.

---

## Labels to Create First

Create these labels in your GitHub repository before creating issues:

**Priority Labels:**
- priority:high (red: #d73a4a)
- priority:medium (yellow: #fbca04)
- priority:low (green: #0e8a16)
- priority:P0 (dark red: #b60205)
- priority:P1 (red: #d93f0b)
- priority:P2 (yellow: #fbca04)

**Week Labels:**
- week:1 through week:8 (blue: #1d76db)

**Service Labels:**
- service:UI (light blue: #c5def5)
- service:Orchestrator (light blue: #c5def5)
- service:Sandbox (light blue: #c5def5)
- service:Artifacts (light blue: #c5def5)

**Type Labels:**
- feature (green: #0e8a16)
- enhancement (light blue: #a2eeef)
- refactor (purple: #d4c5f9)

**Category Labels:**
- performance (red: #ff6b6b)
- reliability (teal: #4ecdc4)
- ml (yellow: #f9ca24)
- visualization (purple: #a29bfe)
- architecture (pink: #fd79a8)
- async (orange: #fdcb6e)

---

## Milestones to Create

1. **Foundation** - Core PKM-Agent improvements and foundation
2. **Week 1** - Foundation - Task infrastructure
3. **Week 2** - Core Workflow - Events and cancellation
4. **Week 3** - Sandbox Integration
5. **Week 4** - Browser Tools
6. **Week 5** - Outputs & Completion
7. **Week 6** - Projects & Knowledge Base
8. **Week 7** - API & Export
9. **Week 8** - Polish & Webhooks

"@

$summary | Out-File -FilePath $summaryPath -Encoding UTF8
Write-Host "✅ Created summary file: $summaryPath" -ForegroundColor Green
Write-Host ""
