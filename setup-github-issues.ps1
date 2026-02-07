# GitHub Issues Setup Script for B0LK13v2 Project
# This script helps set up GitHub repository and create issues from the TODO list

Write-Host "=== B0LK13v2 GitHub Issues Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check if Git is initialized
if (-not (Test-Path .git)) {
    Write-Host "❌ Not a Git repository." -ForegroundColor Yellow
    Write-Host "Initializing Git repository..." -ForegroundColor Green
    git init
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Git repository initialized" -ForegroundColor Green
    }
}

# Check for GitHub CLI
$ghInstalled = Get-Command gh -ErrorAction SilentlyContinue
if (-not $ghInstalled) {
    Write-Host "❌ GitHub CLI (gh) is not installed." -ForegroundColor Red
    Write-Host ""
    Write-Host "To install GitHub CLI:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://cli.github.com/" -ForegroundColor White
    Write-Host "2. Or use winget: winget install --id GitHub.cli" -ForegroundColor White
    Write-Host "3. Or use Chocolatey: choco install gh" -ForegroundColor White
    Write-Host ""
    Write-Host "After installation, run: gh auth login" -ForegroundColor Yellow
    Write-Host ""
    
    # Offer alternative: Create repository manually
    Write-Host "=== Alternative: Manual Setup ===" -ForegroundColor Cyan
    Write-Host "1. Create a GitHub repository at: https://github.com/new" -ForegroundColor White
    Write-Host "2. Name it: B0LK13v2 or pkm-agent" -ForegroundColor White
    Write-Host "3. Copy the repository URL" -ForegroundColor White
    Write-Host "4. Run these commands:" -ForegroundColor White
    Write-Host "   git remote add origin <YOUR-REPO-URL>" -ForegroundColor Gray
    Write-Host "   git add ." -ForegroundColor Gray
    Write-Host "   git commit -m 'Initial commit with TODO list'" -ForegroundColor Gray
    Write-Host "   git push -u origin main" -ForegroundColor Gray
    Write-Host ""
    
    exit 1
}

# Check GitHub CLI authentication
Write-Host "Checking GitHub CLI authentication..." -ForegroundColor Green
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Not authenticated with GitHub CLI" -ForegroundColor Red
    Write-Host "Please run: gh auth login" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ GitHub CLI is authenticated" -ForegroundColor Green
Write-Host ""

# Check if repository exists
Write-Host "Checking for GitHub repository..." -ForegroundColor Green
$remotes = git remote -v 2>&1
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($remotes)) {
    Write-Host "❌ No GitHub remote configured" -ForegroundColor Yellow
    Write-Host ""
    
    # Offer to create a new repository
    $createNew = Read-Host "Would you like to create a new GitHub repository? (y/n)"
    if ($createNew -eq 'y' -or $createNew -eq 'Y') {
        $repoName = Read-Host "Enter repository name (default: B0LK13v2)"
        if ([string]::IsNullOrWhiteSpace($repoName)) {
            $repoName = "B0LK13v2"
        }
        
        $repoDesc = "PKM Agent System - Personal Knowledge Management with AI-powered features"
        $isPrivate = Read-Host "Make repository private? (y/n, default: n)"
        
        $visibility = "public"
        if ($isPrivate -eq 'y' -or $isPrivate -eq 'Y') {
            $visibility = "private"
        }
        
        Write-Host "Creating GitHub repository: $repoName ($visibility)..." -ForegroundColor Green
        
        if ($visibility -eq "private") {
            gh repo create $repoName --private --description $repoDesc --source=. --remote=origin
        } else {
            gh repo create $repoName --public --description $repoDesc --source=. --remote=origin
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Repository created successfully" -ForegroundColor Green
        } else {
            Write-Host "❌ Failed to create repository" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "Please add a remote manually:" -ForegroundColor Yellow
        Write-Host "  git remote add origin <YOUR-REPO-URL>" -ForegroundColor Gray
        exit 1
    }
}

# Get repository info
$repoInfo = gh repo view --json nameWithOwner,url 2>&1 | ConvertFrom-Json
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Repository: $($repoInfo.nameWithOwner)" -ForegroundColor Green
    Write-Host "   URL: $($repoInfo.url)" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "⚠️  Could not fetch repository info" -ForegroundColor Yellow
}

# Create labels
Write-Host "=== Creating Labels ===" -ForegroundColor Cyan
$labels = @(
    @{name="feature"; color="0e8a16"; description="New feature or request"},
    @{name="enhancement"; color="a2eeef"; description="Improvement to existing feature"},
    @{name="refactor"; color="d4c5f9"; description="Code refactoring"},
    @{name="priority:high"; color="d73a4a"; description="High priority"},
    @{name="priority:medium"; color="fbca04"; description="Medium priority"},
    @{name="priority:low"; color="0e8a16"; description="Low priority"},
    @{name="priority:P0"; color="b60205"; description="Critical priority (P0)"},
    @{name="priority:P1"; color="d93f0b"; description="High priority (P1)"},
    @{name="priority:P2"; color="fbca04"; description="Medium priority (P2)"},
    @{name="week:1"; color="1d76db"; description="Week 1 sprint"},
    @{name="week:2"; color="1d76db"; description="Week 2 sprint"},
    @{name="week:3"; color="1d76db"; description="Week 3 sprint"},
    @{name="week:4"; color="1d76db"; description="Week 4 sprint"},
    @{name="week:5"; color="1d76db"; description="Week 5 sprint"},
    @{name="week:6"; color="1d76db"; description="Week 6 sprint"},
    @{name="week:7"; color="1d76db"; description="Week 7 sprint"},
    @{name="week:8"; color="1d76db"; description="Week 8 sprint"},
    @{name="service:UI"; color="c5def5"; description="UI/Frontend service"},
    @{name="service:Orchestrator"; color="c5def5"; description="Orchestrator service"},
    @{name="service:Sandbox"; color="c5def5"; description="Sandbox service"},
    @{name="service:Artifacts"; color="c5def5"; description="Artifacts service"},
    @{name="performance"; color="ff6b6b"; description="Performance related"},
    @{name="reliability"; color="4ecdc4"; description="Reliability related"},
    @{name="ml"; color="f9ca24"; description="Machine learning"},
    @{name="visualization"; color="a29bfe"; description="Visualization"},
    @{name="architecture"; color="fd79a8"; description="Architecture"},
    @{name="async"; color="fdcb6e"; description="Asynchronous processing"}
)

foreach ($label in $labels) {
    $existingLabel = gh label list --json name 2>&1 | ConvertFrom-Json | Where-Object { $_.name -eq $label.name }
    if (-not $existingLabel) {
        Write-Host "Creating label: $($label.name)" -ForegroundColor Gray
        gh label create $label.name --color $label.color --description $label.description 2>&1 | Out-Null
    }
}
Write-Host "✅ Labels created" -ForegroundColor Green
Write-Host ""

# Create milestones
Write-Host "=== Creating Milestones ===" -ForegroundColor Cyan
$milestones = @(
    @{title="Foundation"; description="Core PKM-Agent improvements and foundation"},
    @{title="Week 1"; description="Foundation - Task infrastructure"},
    @{title="Week 2"; description="Core Workflow - Events and cancellation"},
    @{title="Week 3"; description="Sandbox Integration"},
    @{title="Week 4"; description="Browser Tools"},
    @{title="Week 5"; description="Outputs & Completion"},
    @{title="Week 6"; description="Projects & Knowledge Base"},
    @{title="Week 7"; description="API & Export"},
    @{title="Week 8"; description="Polish & Webhooks"}
)

foreach ($milestone in $milestones) {
    # Check if milestone exists
    $existingMilestone = gh api repos/:owner/:repo/milestones --jq ".[] | select(.title == `"$($milestone.title)`")" 2>&1
    if ([string]::IsNullOrWhiteSpace($existingMilestone)) {
        Write-Host "Creating milestone: $($milestone.title)" -ForegroundColor Gray
        gh api repos/:owner/:repo/milestones -f title="$($milestone.title)" -f description="$($milestone.description)" -f state="open" 2>&1 | Out-Null
    }
}
Write-Host "✅ Milestones created" -ForegroundColor Green
Write-Host ""

# Ask before creating issues
Write-Host "=== Ready to Create Issues ===" -ForegroundColor Cyan
Write-Host "This will create 67 issues from github-issues-import.csv" -ForegroundColor White
Write-Host ""
$createIssues = Read-Host "Proceed with creating issues? (y/n)"

if ($createIssues -ne 'y' -and $createIssues -ne 'Y') {
    Write-Host "Cancelled. You can create issues later by running this script again." -ForegroundColor Yellow
    exit 0
}

# Import issues from CSV
Write-Host ""
Write-Host "Creating issues from CSV..." -ForegroundColor Green

$csv = Import-Csv -Path "github-issues-import.csv"
$issueCount = 0
$totalIssues = $csv.Count

foreach ($row in $csv) {
    $issueCount++
    Write-Host "[$issueCount/$totalIssues] Creating: $($row.title)" -ForegroundColor Gray
    
    # Parse labels
    $labelArray = $row.labels -split ','
    $labelArgs = @()
    foreach ($label in $labelArray) {
        $labelArgs += "--label"
        $labelArgs += $label.Trim()
    }
    
    # Create issue
    $createArgs = @(
        "issue", "create",
        "--title", $row.title,
        "--body", $row.body
    )
    
    if ($labelArgs.Count -gt 0) {
        $createArgs += $labelArgs
    }
    
    if (-not [string]::IsNullOrWhiteSpace($row.milestone)) {
        $createArgs += "--milestone"
        $createArgs += $row.milestone
    }
    
    & gh $createArgs 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Created" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Failed" -ForegroundColor Red
    }
    
    # Rate limiting - pause briefly between issues
    Start-Sleep -Milliseconds 500
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "✅ Created $issueCount issues" -ForegroundColor Green
Write-Host "View them at: $($repoInfo.url)/issues" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Review issues on GitHub" -ForegroundColor White
Write-Host "2. Update PROJECT-TODO.md as you complete tasks" -ForegroundColor White
Write-Host "3. Link commits to issues using #<issue-number> in commit messages" -ForegroundColor White
Write-Host ""
