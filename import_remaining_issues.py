#!/usr/bin/env python3
"""
Import remaining GitHub issues from CSV file.
Skips the 6 issues that were already created.
"""

import csv
import subprocess
import sys
import time
from pathlib import Path

# Configuration
REPO = "B0LK13/obsidian-agent"
CSV_FILE = "github-issues-import.csv"

# Issues already created (first 6 in the CSV)
ALREADY_CREATED = [
    "FEAT: Implement Incremental Indexing Mechanism",
    "FEAT: Implement Vector Database Layer for Semantic Search",
    "FEAT: Implement Caching and Optimization Layer",
    "FEAT: Implement Dead Link Detection and Repair",
    "REFACTOR: Implement Defensive Coding and Error Handling",
    "FEAT: Implement Automated Link Suggestions",
]


def read_issues_from_csv(csv_path: str) -> list[dict]:
    """Read issues from CSV file."""
    issues = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            issues.append({
                'title': row['title'].strip('"'),
                'body': row['body'].strip('"').replace('""', '"'),
                'labels': row['labels'].strip('"'),
                'milestone': row.get('milestone', '').strip('"')
            })
    return issues


def issue_exists(title: str) -> bool:
    """Check if issue title was already created."""
    return title in ALREADY_CREATED


def create_issue(issue: dict, dry_run: bool = False) -> bool:
    """Create a single GitHub issue using gh CLI."""
    title = issue['title']
    body = issue['body']
    labels = issue['labels']
    
    # Build the command
    cmd = [
        'gh', 'issue', 'create',
        '--repo', REPO,
        '--title', title,
        '--body', body,
        '--label', labels
    ]
    
    if dry_run:
        print(f"[DRY RUN] Would create: {title}")
        return True
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"[OK] Created: {title}")
            return True
        else:
            print(f"[FAIL] Failed: {title}")
            print(f"   Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] Timeout: {title}")
        return False
    except Exception as e:
        print(f"[ERROR] Error creating '{title}': {e}")
        return False


def main():
    """Main entry point."""
    dry_run = '--dry-run' in sys.argv
    
    print("=" * 60)
    print("GitHub Issues Bulk Import")
    print(f"Repository: {REPO}")
    print(f"CSV File: {CSV_FILE}")
    print("=" * 60)
    print()
    
    # Check if CSV exists
    if not Path(CSV_FILE).exists():
        print(f"[ERROR] CSV file not found: {CSV_FILE}")
        sys.exit(1)
    
    # Read all issues
    all_issues = read_issues_from_csv(CSV_FILE)
    print(f"Total issues in CSV: {len(all_issues)}")
    
    # Filter out already created issues
    remaining_issues = [i for i in all_issues if not issue_exists(i['title'])]
    print(f"Already created: {len(all_issues) - len(remaining_issues)}")
    print(f"Remaining to create: {len(remaining_issues)}")
    print()
    
    if dry_run:
        print("DRY RUN MODE - No issues will be created")
        print()
    
    if not remaining_issues:
        print("All issues have already been created!")
        return
    
    # Confirm before creating
    if not dry_run:
        response = input(f"Create {len(remaining_issues)} issues? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted")
            sys.exit(0)
        print()
    
    # Create issues
    success_count = 0
    fail_count = 0
    
    for i, issue in enumerate(remaining_issues, 1):
        print(f"[{i}/{len(remaining_issues)}] ", end="")
        
        if create_issue(issue, dry_run=dry_run):
            success_count += 1
        else:
            fail_count += 1
        
        # Rate limiting - sleep between requests
        if not dry_run and i < len(remaining_issues):
            time.sleep(1)
    
    print()
    print("=" * 60)
    print("Import Complete!")
    print(f"Created: {success_count}")
    print(f"Failed: {fail_count}")
    print("=" * 60)
    
    if fail_count > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
