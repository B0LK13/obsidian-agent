# B0LK13v2 Project Consolidation Script
# This script merges duplicate folders into a unified structure

$ErrorActionPreference = "Stop"
$root = "C:\Users\Admin\Documents\B0LK13v2"

Write-Host "=== B0LK13v2 Project Consolidation ===" -ForegroundColor Cyan

# Step 1: Copy PKM Agent (most complete version)
Write-Host "`n[1/5] Consolidating PKM Agent..." -ForegroundColor Yellow
$pkmSource = "$root\B0LK13v2\pkm-agent"
$pkmDest = "$root\apps\pkm-agent"

if (Test-Path $pkmSource) {
    # Copy src folder
    Copy-Item -Path "$pkmSource\src" -Destination $pkmDest -Recurse -Force
    # Copy config files
    Copy-Item -Path "$pkmSource\pyproject.toml" -Destination $pkmDest -Force -ErrorAction SilentlyContinue
    Copy-Item -Path "$pkmSource\Dockerfile" -Destination $pkmDest -Force -ErrorAction SilentlyContinue
    Copy-Item -Path "$pkmSource\docker-compose.yml" -Destination $pkmDest -Force -ErrorAction SilentlyContinue
    Copy-Item -Path "$pkmSource\.env.example" -Destination $pkmDest -Force -ErrorAction SilentlyContinue
    Copy-Item -Path "$pkmSource\README.md" -Destination $pkmDest -Force -ErrorAction SilentlyContinue
    # Copy tests
    if (Test-Path "$pkmSource\tests") {
        Copy-Item -Path "$pkmSource\tests" -Destination $pkmDest -Recurse -Force
    }
    # Copy docs
    if (Test-Path "$pkmSource\docs") {
        Copy-Item -Path "$pkmSource\docs" -Destination $pkmDest -Recurse -Force
    }
    Write-Host "  PKM Agent copied successfully" -ForegroundColor Green
} else {
    Write-Host "  Source not found: $pkmSource" -ForegroundColor Red
}

# Step 2: Copy Obsidian Plugin (merge both versions)
Write-Host "`n[2/5] Consolidating Obsidian Plugin..." -ForegroundColor Yellow
$obsSource1 = "$root\obsidian-agent"
$obsSource2 = "$root\B0LK13v2\obsidian-pkm-agent"
$obsDest = "$root\apps\obsidian-plugin"

# Use obsidian-agent as base (vanilla TS, cleaner)
if (Test-Path $obsSource1) {
    Copy-Item -Path "$obsSource1\*.ts" -Destination $obsDest -Force -ErrorAction SilentlyContinue
    Copy-Item -Path "$obsSource1\*.json" -Destination $obsDest -Force -ErrorAction SilentlyContinue
    Copy-Item -Path "$obsSource1\*.css" -Destination $obsDest -Force -ErrorAction SilentlyContinue
    Copy-Item -Path "$obsSource1\*.mjs" -Destination $obsDest -Force -ErrorAction SilentlyContinue
    Copy-Item -Path "$obsSource1\README.md" -Destination $obsDest -Force -ErrorAction SilentlyContinue
    Write-Host "  Obsidian Agent base copied" -ForegroundColor Green
}

# Copy additional src from obsidian-pkm-agent
if (Test-Path "$obsSource2\src") {
    New-Item -ItemType Directory -Path "$obsDest\src" -Force | Out-Null
    Copy-Item -Path "$obsSource2\src\*" -Destination "$obsDest\src" -Recurse -Force
    Write-Host "  PKM Agent src modules merged" -ForegroundColor Green
}

# Step 3: Copy Web/Blog (Next.js)
Write-Host "`n[3/5] Consolidating Web App..." -ForegroundColor Yellow
$webSource = "$root\B0LK13"
$webDest = "$root\apps\web"

if (Test-Path $webSource) {
    # Copy essential folders
    @("components", "pages", "posts", "public", "styles", "lib", "utils") | ForEach-Object {
        if (Test-Path "$webSource\$_") {
            Copy-Item -Path "$webSource\$_" -Destination $webDest -Recurse -Force
        }
    }
    # Copy config files
    @("package.json", "tsconfig.json", "next.config.js", "tailwind.config.js", "postcss.config.js", "README.md") | ForEach-Object {
        if (Test-Path "$webSource\$_") {
            Copy-Item -Path "$webSource\$_" -Destination $webDest -Force
        }
    }
    Write-Host "  Web app copied successfully" -ForegroundColor Green
}

# Step 4: Consolidate Documentation
Write-Host "`n[4/5] Consolidating Documentation..." -ForegroundColor Yellow

# Setup docs
$setupDocs = @(
    "$root\B0LK13v2\MANUAL-SETUP.md",
    "$root\B0LK13v2\README-SETUP.md",
    "$root\B0LK13v2\SETUP-COMPLETE.md",
    "$root\B0LK13v2\START-HERE.md",
    "$root\B0LK13v2\QUICK-REFERENCE.md"
)
foreach ($doc in $setupDocs) {
    if (Test-Path $doc) {
        Copy-Item -Path $doc -Destination "$root\docs\setup" -Force
    }
}

# Architecture docs
$archDocs = @(
    "$root\B0LK13v2\Final knowledge base arhitecture.md",
    "$root\B0LK13v2\AI-ML-OPTIMIZATION.md",
    "$root\B0LK13v2\AgentX configuration summary.md"
)
foreach ($doc in $archDocs) {
    if (Test-Path $doc) {
        Copy-Item -Path $doc -Destination "$root\docs\architecture" -Force
    }
}

# Changelog docs
$changelogDocs = @(
    "$root\B0LK13v2\001-config-fix-404-errors.md",
    "$root\B0LK13v2\002-developer-profiles.md",
    "$root\B0LK13v2\003-mcp-server.md",
    "$root\B0LK13v2\004-task-management-system.md",
    "$root\B0LK13v2\005-private-local-models.md",
    "$root\B0LK13v2\006-complete-change-summary.md"
)
foreach ($doc in $changelogDocs) {
    if (Test-Path $doc) {
        Copy-Item -Path $doc -Destination "$root\docs\changelog" -Force
    }
}
Write-Host "  Documentation consolidated" -ForegroundColor Green

# Step 5: Archive old directories
Write-Host "`n[5/5] Archiving old directories..." -ForegroundColor Yellow

$archiveItems = @(
    "$root\pkm-agent",
    "$root\pkm-agent-local",
    "$root\B0LK13v2\B0LK13v2",
    "$root\B0LK13v2\B0LK13"
)

foreach ($item in $archiveItems) {
    if (Test-Path $item) {
        $name = Split-Path $item -Leaf
        $destPath = "$root\archive\$name"
        if (Test-Path $destPath) {
            $destPath = "$root\archive\$name-$(Get-Date -Format 'yyyyMMdd')"
        }
        Move-Item -Path $item -Destination $destPath -Force -ErrorAction SilentlyContinue
        Write-Host "  Archived: $name" -ForegroundColor Gray
    }
}

Write-Host "`n=== Consolidation Complete ===" -ForegroundColor Cyan
Write-Host "New structure:"
Write-Host "  apps/pkm-agent/     - Python PKM Agent"
Write-Host "  apps/obsidian-plugin/ - Obsidian Plugin"
Write-Host "  apps/web/           - Next.js Web App"
Write-Host "  docs/               - All documentation"
Write-Host "  archive/            - Old directories"
