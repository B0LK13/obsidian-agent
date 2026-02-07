# Link Management Guide

## Overview

The PKM-Agent now includes powerful link management features:
- **Automated broken link detection** across your entire vault
- **Fuzzy matching** to suggest fixes for broken links
- **Auto-healing** to automatically repair broken links
- **Link graph analysis** to understand vault structure

## Quick Start

### Check for Broken Links

```bash
# Basic check
pkm-agent check-links

# Output as JSON
pkm-agent check-links --json
```

**Example Output:**
```
=== Link Validation Results ===

Total broken links: 23
Fixable: 18
Unfixable: 5

=== Broken Links ===

  Projects/2024/AI Research.md:45
    → [[Deep Lerning Basics]] (type: wikilink)
  
  Daily/2024-01-15.md:12
    → [[Meating Notes]] (type: wikilink)

=== Fix Suggestions ===

  Projects/2024/AI Research.md:45
    Deep Lerning Basics → Deep Learning Basics (85.2%)
  
  Daily/2024-01-15.md:12
    Meating Notes → Meeting Notes (91.7%)

💡 Run with --fix to automatically repair 18 broken links
```

### Auto-Fix Broken Links (Dry Run)

```bash
# Simulate fixes without making changes
pkm-agent check-links --fix --dry-run
```

**Example Output:**
```
=== DRY RUN ===

Processed: 23 links
Fixed: 18
Failed: 2
Skipped: 3

💡 Run with --fix (without --dry-run) to apply these changes
```

### Auto-Fix Broken Links (For Real)

```bash
# Fix with default 70% confidence threshold
pkm-agent check-links --fix

# Fix with custom confidence threshold
pkm-agent check-links --fix --min-confidence 0.85
```

**Example Output:**
```
=== Applying Fixes ===

Processed: 23 links
Fixed: 18
Failed: 2
Skipped: 3

✅ Successfully fixed 18 broken links!
```

### Analyze Link Graph

```bash
# Show top hub notes (most incoming links)
pkm-agent link-graph --top 20

# Include orphan notes (no incoming links)
pkm-agent link-graph --top 20 --orphans

# JSON output
pkm-agent link-graph --json
```

**Example Output:**
```
=== Vault Link Graph ===

Total links: 1,247
Broken links: 23
Orphan notes: 45
Connected notes: 312

=== Top 20 Hub Notes ===

  89 ← Concepts/Machine Learning.md
  67 ← Index/AI Resources.md
  54 ← Projects/Research Hub.md
  42 ← Reference/Python Cheatsheet.md
  ...

=== Orphan Notes (first 20) ===

  • Drafts/Untitled.md
  • Archive/Old Ideas.md
  • Temporary/Scratch.md
  ...
```

## Link Types Supported

The analyzer detects and repairs multiple link formats:

### 1. Wikilinks
```markdown
[[Note Title]]
[[Note Title|Custom Display Text]]
```

### 2. Embeds
```markdown
![[Image.png]]
![[Another Note]]
```

### 3. Markdown Links
```markdown
[Display Text](path/to/note.md)
[Display Text](../relative/path.md)
```

### 4. Tags (Detection Only)
```markdown
#project #research #ai
```

**Note:** Tags are detected but not validated (they don't point to files).

## How Fuzzy Matching Works

The validator uses intelligent fuzzy matching with multiple scoring factors:

### Base Similarity
Uses `difflib.SequenceMatcher` for character-level similarity:
```
"Deep Lerning" vs "Deep Learning" → 92% base similarity
```

### Prefix Boost (+20%)
Exact prefix matches get bonus points:
```
"Meeting" starts with "Mee" → +20%
```

### Suffix Boost (+10%)
Exact suffix matches get bonus points:
```
"Notes" ends with "tes" → +10%
```

### Word Overlap (+30% per match)
Matching words get significant boost:
```
"AI Research Notes" vs "AI Research Paper"
  → 2 matching words ("AI", "Research") → +60%
```

### Final Score Calculation
```
Final Score = Base + Prefix Boost + Suffix Boost + Word Overlap
```

Only suggestions above the confidence threshold (default 70%) are shown.

## Configuration

### Confidence Threshold

Control how conservative the auto-fix is:

```bash
# Very conservative (only fix obvious matches)
pkm-agent check-links --fix --min-confidence 0.9

# Balanced (default)
pkm-agent check-links --fix --min-confidence 0.7

# Aggressive (fix more uncertain matches)
pkm-agent check-links --fix --min-confidence 0.5
```

**Recommendations:**
- **0.9+**: Very safe, but may miss some fixable links
- **0.7-0.8**: Good balance (recommended)
- **<0.7**: More fixes, but higher risk of incorrect replacements

### Dry Run Mode

Always test first with `--dry-run`:

```bash
# Step 1: Check what would be fixed
pkm-agent check-links --fix --dry-run --min-confidence 0.7

# Step 2: Review the output carefully

# Step 3: Apply fixes for real
pkm-agent check-links --fix --min-confidence 0.7
```

## Advanced Usage

### Scripting with JSON Output

```bash
# Export broken links to JSON file
pkm-agent check-links --json > broken-links.json

# Export link graph to JSON file
pkm-agent link-graph --json > link-graph.json
```

**Example JSON Structure:**
```json
{
  "total_broken": 23,
  "fixable": 18,
  "unfixable": 5,
  "broken_links": [
    {
      "source_path": "Projects/AI.md",
      "target": "Deep Lerning",
      "link_type": "wikilink",
      "line_number": 45,
      "column": 120,
      "is_broken": true
    }
  ],
  "suggestions": [
    {
      "source": "Projects/AI.md",
      "line": 45,
      "original": "Deep Lerning",
      "suggested": "Deep Learning",
      "confidence": 0.852,
      "reason": "Fuzzy match (similarity: 85.20%)"
    }
  ]
}
```

### Python API Usage

```python
from pathlib import Path
from pkm_agent.data.link_analyzer import LinkAnalyzer
from pkm_agent.data.link_healer import LinkValidator, LinkHealer

# Initialize
vault_root = Path("/path/to/vault")
analyzer = LinkAnalyzer(vault_root)
validator = LinkValidator(analyzer, min_confidence=0.7)

# Find broken links
broken_links = analyzer.find_broken_links()
print(f"Found {len(broken_links)} broken links")

# Validate and get suggestions
result = validator.validate_vault(auto_suggest=True)
print(f"Fixable: {result['fixable']}, Unfixable: {result['unfixable']}")

# Auto-heal (dry run)
healer = LinkHealer(validator, dry_run=True)
healing_result = healer.heal_vault()
print(f"Would fix {healing_result['fixed']} links")

# Auto-heal (for real)
healer = LinkHealer(validator, dry_run=False)
healing_result = healer.heal_vault()
print(f"Fixed {healing_result['fixed']} links")
```

## Troubleshooting

### "No suggestions available"

**Cause:** No similar note titles found with sufficient confidence.

**Solutions:**
1. Lower the confidence threshold: `--min-confidence 0.6`
2. Check if the target note actually exists
3. The link might be an external URL (not fixable)

### "Link pattern not found in line"

**Cause:** The link format changed between detection and healing.

**Solutions:**
1. Run check-links again (file might have been modified)
2. Check for special characters or formatting issues
3. The link might be in a code block (ignored by design)

### "Confidence X% below threshold Y%"

**Cause:** Best match found but confidence too low.

**Solutions:**
1. Review the suggestion in dry-run mode
2. Lower the threshold if suggestion looks good
3. Fix manually if auto-fix is too uncertain

### High False Positive Rate

**Cause:** Confidence threshold too low.

**Solutions:**
1. Increase threshold: `--min-confidence 0.8`
2. Use dry-run mode to review suggestions first
3. Review and fix manually for critical notes

## Best Practices

### 1. Regular Maintenance

Run link checks weekly:
```bash
# Add to cron/scheduled task
pkm-agent check-links --json > ~/vault-health/links-$(date +%Y%m%d).json
```

### 2. Safe Auto-Fix Workflow

```bash
# Step 1: Analyze
pkm-agent link-graph --orphans

# Step 2: Check
pkm-agent check-links

# Step 3: Test
pkm-agent check-links --fix --dry-run --min-confidence 0.8

# Step 4: Review output

# Step 5: Apply
pkm-agent check-links --fix --min-confidence 0.8

# Step 6: Verify
git diff  # Review changes before committing
```

### 3. Backup Before Auto-Fix

```bash
# Create backup
tar -czf vault-backup-$(date +%Y%m%d).tar.gz /path/to/vault

# Run auto-fix
pkm-agent check-links --fix

# Verify results
# If problems, restore from backup
```

### 4. Use Version Control

```bash
# Commit before auto-fix
git add -A
git commit -m "Pre-link-fix snapshot"

# Run auto-fix
pkm-agent check-links --fix

# Review changes
git diff

# Commit fixes
git commit -am "Auto-fix broken links"

# Or revert if needed
git reset --hard HEAD^
```

## Performance Tips

### Large Vaults (10k+ notes)

The link analyzer is optimized for performance but consider:

1. **First run builds cache** (~10-30s for 50k notes)
2. **Subsequent runs are faster** (cache reused)
3. **Incremental checks** on specific files:

```python
# Python API for single file
from pathlib import Path
from pkm_agent.data.link_analyzer import LinkAnalyzer

analyzer = LinkAnalyzer(vault_root)
file_path = vault_root / "Projects/MyNote.md"
broken = analyzer.find_broken_links(file_path)
```

4. **JSON output is faster** than formatted output

### Memory Usage

- **10k notes**: ~100 MB RAM
- **50k notes**: ~500 MB RAM
- Cache is built in-memory for fast lookups

## Future Enhancements

Planned features:
- [ ] Link suggestions based on content similarity
- [ ] Automatic backlink creation
- [ ] Dead link cleanup automation
- [ ] Link preview in TUI
- [ ] Integration with Obsidian UI
- [ ] Graph visualization export

## Examples

### Example 1: Clean Up Research Vault

```bash
# 1. Check current state
pkm-agent link-graph --top 10

# 2. Find broken links
pkm-agent check-links

# 3. Fix high-confidence matches
pkm-agent check-links --fix --min-confidence 0.85

# 4. Review remaining
pkm-agent check-links
```

### Example 2: Weekly Maintenance Script

```bash
#!/bin/bash
# weekly-vault-check.sh

DATE=$(date +%Y%m%d)
REPORT_DIR="$HOME/vault-reports"
mkdir -p "$REPORT_DIR"

echo "Running weekly vault health check..."

# Link graph analysis
pkm-agent link-graph --json > "$REPORT_DIR/graph-$DATE.json"

# Broken link detection
pkm-agent check-links --json > "$REPORT_DIR/broken-links-$DATE.json"

# Auto-fix with conservative threshold
pkm-agent check-links --fix --min-confidence 0.8 > "$REPORT_DIR/fixes-$DATE.log"

echo "Reports saved to $REPORT_DIR"
```

### Example 3: Find Most Influential Notes

```bash
# Top hub notes (most linked to)
pkm-agent link-graph --top 50 > hub-notes.txt

# Find orphans (candidates for deletion or linking)
pkm-agent link-graph --orphans > orphan-notes.txt
```

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/B0LK13/obsidian-agent/issues
- Documentation: See `PHASE_2_PROGRESS.md`
- API Docs: See `link_analyzer.py` and `link_healer.py`
