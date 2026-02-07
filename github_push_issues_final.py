#!/usr/bin/env python3
"""
GitHub Issues Push Script - Final Version
Uses GitHub API directly to create issues with proper label handling.
"""

import csv
import json
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# Configuration
REPO = "B0LK13/obsidian-agent"
GITHUB_API = "https://api.github.com"
CSV_FILE = "github-issues-import.csv"

# Issues already created (skip these)
ALREADY_CREATED = [
    "FEAT: Implement Incremental Indexing Mechanism",
    "FEAT: Implement Vector Database Layer for Semantic Search",
    "FEAT: Implement Automated Link Suggestions",
    "FEAT: Implement Dead Link Detection and Repair",
    "FEAT: Implement Caching and Optimization Layer",
]

# Labels to create
LABELS = [
    ("priority:high", "d73a4a", "High priority"),
    ("priority:medium", "fbca04", "Medium priority"),
    ("priority:low", "0e8a16", "Low priority"),
    ("priority:P0", "b60205", "Critical priority"),
    ("priority:P1", "d93f0b", "High priority"),
    ("priority:P2", "fbca04", "Medium priority"),
    ("week:1", "1d76db", "Week 1 milestone"),
    ("week:2", "1d76db", "Week 2 milestone"),
    ("week:3", "1d76db", "Week 3 milestone"),
    ("week:4", "1d76db", "Week 4 milestone"),
    ("week:5", "1d76db", "Week 5 milestone"),
    ("week:6", "1d76db", "Week 6 milestone"),
    ("week:7", "1d76db", "Week 7 milestone"),
    ("week:8", "1d76db", "Week 8 milestone"),
    ("service:UI", "c5def5", "UI service"),
    ("service:Orchestrator", "c5def5", "Orchestrator service"),
    ("service:Sandbox", "c5def5", "Sandbox service"),
    ("service:Artifacts", "c5def5", "Artifacts service"),
    ("feature", "0e8a16", "New feature"),
    ("enhancement", "a2eeef", "Enhancement"),
    ("refactor", "d4c5f9", "Code refactoring"),
    ("performance", "f9d0c4", "Performance related"),
    ("reliability", "c2e0c6", "Reliability related"),
    ("ml", "bfdadc", "Machine learning related"),
    ("visualization", "b6b6b6", "Visualization related"),
    ("architecture", "e99695", "Architecture related"),
    ("async", "f9d0c4", "Asynchronous processing"),
    ("testing", "d4c5f9", "Testing related"),
    ("documentation", "0075ca", "Documentation"),
    ("windows", "c5def5", "Windows specific"),
    ("gpu", "84b6eb", "GPU related"),
    ("security", "d73a4a", "Security related"),
    ("mobile", "c5def5", "Mobile support"),
    ("training", "d4c5f9", "Training related"),
    ("research", "e99695", "Research related"),
    ("scalability", "f9d0c4", "Scalability related"),
    ("quality", "c2e0c6", "Quality related"),
    ("v2.0", "b60205", "Version 2.0 target"),
]


def get_github_token():
    """Get GitHub token from gh CLI."""
    result = subprocess.run(
        ["gh", "auth", "token"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def api_request(method, endpoint, data=None, token=None):
    """Make GitHub API request."""
    url = f"{GITHUB_API}/repos/{REPO}{endpoint}"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    if data:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())
    except Exception as e:
        return 0, str(e)


def create_label(name, color, description, token):
    """Create a single label."""
    status, result = api_request(
        "POST",
        "/labels",
        {"name": name, "color": color, "description": description},
        token
    )
    return status == 201 or status == 422  # 422 = already exists


def create_issue(title, body, labels, token):
    """Create a single issue."""
    status, result = api_request(
        "POST",
        "/issues",
        {"title": title, "body": body, "labels": labels},
        token
    )
    return status == 201, result


def read_issues_from_csv(csv_path):
    """Read issues from CSV file."""
    issues = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            issues.append({
                'title': row['title'].strip('"'),
                'body': row['body'].strip('"').replace('""', '"'),
                'labels': [l.strip() for l in row['labels'].strip('"').split(',')],
                'milestone': row.get('milestone', '').strip('"')
            })
    return issues


def main():
    dry_run = '--dry-run' in sys.argv
    skip_labels = '--skip-labels' in sys.argv
    
    print("=" * 60)
    print("GitHub Issues Push - Final Version")
    print(f"Repository: {REPO}")
    print("=" * 60)
    print()
    
    # Get token
    token = get_github_token()
    if not token:
        print("[ERROR] Could not get GitHub token. Run: gh auth login")
        sys.exit(1)
    print("[OK] GitHub token obtained")
    
    # Check CSV
    if not Path(CSV_FILE).exists():
        print(f"[ERROR] CSV file not found: {CSV_FILE}")
        sys.exit(1)
    
    # Read issues
    issues = read_issues_from_csv(CSV_FILE)
    remaining = [i for i in issues if i['title'] not in ALREADY_CREATED]
    
    print(f"[INFO] Total issues: {len(issues)}")
    print(f"[INFO] Already created: {len(issues) - len(remaining)}")
    print(f"[INFO] Remaining: {len(remaining)}")
    print()
    
    if dry_run:
        print("[DRY RUN] No changes will be made")
        print()
    
    # Create labels
    if not dry_run and not skip_labels:
        print("Creating labels...")
        created = 0
        for name, color, desc in LABELS:
            if create_label(name, color, desc, token):
                created += 1
        print(f"[OK] Labels ready: {created}/{len(LABELS)}")
        print()
    
    if not remaining:
        print("[DONE] All issues already created!")
        return
    
    # Confirm
    if not dry_run:
        confirm = input(f"Create {len(remaining)} issues? (yes/no): ")
        if confirm.lower() != 'yes':
            print("[ABORT] Cancelled")
            sys.exit(0)
        print()
    
    # Create issues
    created_count = 0
    failed_count = 0
    
    for i, issue in enumerate(remaining, 1):
        title = issue['title']
        print(f"[{i}/{len(remaining)}] {title[:50]}...", end=" ")
        
        if dry_run:
            print("[DRY RUN]")
            created_count += 1
            continue
        
        success, result = create_issue(title, issue['body'], issue['labels'], token)
        
        if success:
            print(f"[OK] #{result.get('number', '?')}")
            created_count += 1
        else:
            print(f"[FAIL] {result}")
            failed_count += 1
        
        # Rate limiting
        if i < len(remaining):
            time.sleep(1)
    
    print()
    print("=" * 60)
    print("Import Complete!")
    print(f"Created: {created_count}")
    print(f"Failed: {failed_count}")
    print("=" * 60)
    
    if failed_count > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
