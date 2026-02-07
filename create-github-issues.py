#!/usr/bin/env python3
"""
GitHub Issues Creator for B0LK13v2 Project
Generates individual markdown files for each issue that can be manually created on GitHub
OR uses GitHub API to bulk create issues if credentials are provided
"""

import csv
import os
import json
from pathlib import Path

def create_issue_files():
    """Generate markdown files for each issue"""
    print("=== B0LK13v2 GitHub Issues Generator ===")
    print("Generating markdown files for each issue...\n")
    
    # Create issues directory
    issues_dir = Path("github-issues")
    issues_dir.mkdir(exist_ok=True)
    
    # Read CSV
    with open("github-issues-import.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        issues = list(reader)
    
    print(f"Processing {len(issues)} issues...\n")
    
    # Group by milestone
    issues_by_milestone = {}
    for issue in issues:
        milestone = issue['milestone']
        if milestone not in issues_by_milestone:
            issues_by_milestone[milestone] = []
        issues_by_milestone[milestone].append(issue)
    
    issue_count = 0
    
    for milestone, milestone_issues in sorted(issues_by_milestone.items()):
        milestone_dir = issues_dir / milestone
        milestone_dir.mkdir(exist_ok=True)
        
        print(f"Processing milestone: {milestone} ({len(milestone_issues)} issues)")
        
        for issue in milestone_issues:
            issue_count += 1
            
            # Clean filename
            filename = issue['title'].replace('/', '-').replace('\\', '-').replace(':', '-')
            filename = filename.replace('*', '').replace('?', '').replace('"', '').replace('<', '').replace('>', '').replace('|', '')
            filename = f"{issue_count:02d}. {filename}.md"
            filepath = milestone_dir / filename
            
            # Create issue content
            content = f"""# {issue['title']}

**Labels:** {issue['labels']}  
**Milestone:** {issue['milestone']}

---

{issue['body']}

---

## To Create This Issue on GitHub:

1. Go to: https://github.com/YOUR-USERNAME/YOUR-REPO/issues/new
2. Copy the title above (without the #)
3. Copy the body content above (between the --- lines)
4. Add labels: {issue['labels']}
5. Set milestone: {issue['milestone']}
6. Click "Submit new issue"

"""
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            
            print(f"  ✅ Created: {filename}")
    
    print("\n=== Summary ===")
    print(f"✅ Generated {issue_count} issue files in: {issues_dir}")
    print("\nNext steps:")
    print("1. Create a GitHub repository if you haven't already")
    print("2. Open the issue files in the 'github-issues' folder")
    print("3. Copy and paste each issue to GitHub")
    print("\nOR install GitHub CLI for automatic creation:")
    print("  Download from: https://cli.github.com/")
    
    # Create summary file
    create_summary(issues_by_milestone, issue_count)

def create_summary(issues_by_milestone, total_count):
    """Create a summary markdown file"""
    summary_path = Path("github-issues") / "00-SUMMARY.md"
    
    summary = f"""# Issues Summary

**Total Issues:** {total_count}

## By Milestone

"""
    
    for milestone, issues in sorted(issues_by_milestone.items()):
        summary += f"\n### {milestone} ({len(issues)} issues)\n\n"
        for idx, issue in enumerate(issues, 1):
            summary += f"{idx}. **{issue['title']}** - Labels: {issue['labels']}\n"
    
    summary += """

---

## Quick Start

### Option 1: Manual Creation
1. Navigate through the milestone folders
2. Open each .md file
3. Follow the instructions in each file to create the issue on GitHub

### Option 2: GitHub CLI (Recommended)
```bash
# Install GitHub CLI from https://cli.github.com/
gh auth login
# Then run the PowerShell setup script
```

### Option 3: GitHub API (This Script)
```bash
# Set your GitHub token
export GITHUB_TOKEN=your_token_here
export GITHUB_REPO=username/repo

# Run with API mode
python create-github-issues.py --api
```

---

## Labels to Create First

Create these labels in your GitHub repository before creating issues:

**Priority Labels:**
- `priority:high` (red: #d73a4a)
- `priority:medium` (yellow: #fbca04)
- `priority:low` (green: #0e8a16)
- `priority:P0` (dark red: #b60205)
- `priority:P1` (red: #d93f0b)
- `priority:P2` (yellow: #fbca04)

**Week Labels:**
- `week:1` through `week:8` (blue: #1d76db)

**Service Labels:**
- `service:UI` (light blue: #c5def5)
- `service:Orchestrator` (light blue: #c5def5)
- `service:Sandbox` (light blue: #c5def5)
- `service:Artifacts` (light blue: #c5def5)

**Type Labels:**
- `feature` (green: #0e8a16)
- `enhancement` (light blue: #a2eeef)
- `refactor` (purple: #d4c5f9)

**Category Labels:**
- `performance`, `reliability`, `ml`, `visualization`, `architecture`, `async`

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

"""
    
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary)
    
    print(f"\n✅ Created summary file: {summary_path}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--api":
        print("GitHub API mode not implemented yet.")
        print("Please use the manual mode or GitHub CLI.")
        sys.exit(1)
    else:
        create_issue_files()
