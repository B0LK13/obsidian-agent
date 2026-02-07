# Create GitHub Labels for Obsidian Agent Repository
param(
    [string]$Repo = "B0LK13/obsidian-agent"
)

$labels = @(
    # Priority labels
    @{name="priority:high"; color="d73a4a"; desc="High priority"},
    @{name="priority:medium"; color="fbca04"; desc="Medium priority"},
    @{name="priority:low"; color="0e8a16"; desc="Low priority"},
    @{name="priority:P0"; color="b60205"; desc="Critical priority"},
    @{name="priority:P1"; color="d93f0b"; desc="High priority"},
    @{name="priority:P2"; color="fbca04"; desc="Medium priority"},
    
    # Week labels
    @{name="week:1"; color="1d76db"; desc="Week 1 milestone"},
    @{name="week:2"; color="1d76db"; desc="Week 2 milestone"},
    @{name="week:3"; color="1d76db"; desc="Week 3 milestone"},
    @{name="week:4"; color="1d76db"; desc="Week 4 milestone"},
    @{name="week:5"; color="1d76db"; desc="Week 5 milestone"},
    @{name="week:6"; color="1d76db"; desc="Week 6 milestone"},
    @{name="week:7"; color="1d76db"; desc="Week 7 milestone"},
    @{name="week:8"; color="1d76db"; desc="Week 8 milestone"},
    
    # Service labels
    @{name="service:UI"; color="c5def5"; desc="UI service"},
    @{name="service:Orchestrator"; color="c5def5"; desc="Orchestrator service"},
    @{name="service:Sandbox"; color="c5def5"; desc="Sandbox service"},
    @{name="service:Artifacts"; color="c5def5"; desc="Artifacts service"},
    
    # Type labels
    @{name="feature"; color="0e8a16"; desc="New feature"},
    @{name="enhancement"; color="a2eeef"; desc="Enhancement"},
    @{name="refactor"; color="d4c5f9"; desc="Code refactoring"},
    @{name="bug"; color="d73a4a"; desc="Bug fix"},
    
    # Category labels
    @{name="performance"; color="f9d0c4"; desc="Performance related"},
    @{name="reliability"; color="c2e0c6"; desc="Reliability related"},
    @{name="ml"; color="bfdadc"; desc="Machine learning related"},
    @{name="visualization"; color="b6b6b6"; desc="Visualization related"},
    @{name="architecture"; color="e99695"; desc="Architecture related"},
    @{name="async"; color="f9d0c4"; desc="Asynchronous processing"},
    @{name="testing"; color="d4c5f9"; desc="Testing related"},
    @{name="documentation"; color="0075ca"; desc="Documentation"},
    @{name="windows"; color="c5def5"; desc="Windows specific"},
    @{name="gpu"; color="84b6eb"; desc="GPU related"},
    @{name="security"; color="d73a4a"; desc="Security related"},
    @{name="ux"; color="fef2c0"; desc="User experience"},
    @{name="mobile"; color="c5def5"; desc="Mobile support"},
    @{name="training"; color="d4c5f9"; desc="Training related"},
    @{name="research"; color="e99695"; desc="Research related"},
    @{name="scalability"; color="f9d0c4"; desc="Scalability related"},
    @{name="quality"; color="c2e0c6"; desc="Quality related"},
    @{name="v2.0"; color="b60205"; desc="Version 2.0 target"}
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Creating GitHub Labels" -ForegroundColor Cyan
Write-Host "Repository: $Repo" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$created = 0
$failed = 0

foreach ($label in $labels) {
    $name = $label.name
    $color = $label.color
    $desc = $label.desc
    
    Write-Host "Creating label: $name" -NoNewline
    
    $result = gh label create --repo $Repo --name $name --color $color --description $desc 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host " [OK]" -ForegroundColor Green
        $created++
    } elseif ($result -match "already exists") {
        Write-Host " [EXISTS]" -ForegroundColor Yellow
    } else {
        Write-Host " [FAIL] $result" -ForegroundColor Red
        $failed++
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Label Creation Complete" -ForegroundColor Cyan
Write-Host "Created: $created" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Cyan
