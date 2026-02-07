#!/usr/bin/env python3
"""
PKM Directory Structure Generator
Creates the complete PARA + Zettelkasten folder structure
"""

import os
from pathlib import Path
from datetime import datetime

# Base directory for PKM
BASE_DIR = Path(__file__).parent / "pkm"

# Directory structure definition
STRUCTURE = {
    "_meta": {
        "_daily_notes": {
            "2024": {f"{i:02d}-{m}": {} for i, m in enumerate([
                "january", "february", "march", "april", "may", "june",
                "july", "august", "september", "october", "november", "december"
            ], 1)},
            "2025": {f"{i:02d}-{m}": {} for i, m in enumerate([
                "january", "february", "march", "april", "may", "june",
                "july", "august", "september", "october", "november", "december"
            ], 1)},
            "2026": {f"{i:02d}-{m}": {} for i, m in enumerate([
                "january", "february", "march", "april", "may", "june",
                "july", "august", "september", "october", "november", "december"
            ], 1)},
        },
        "_inbox": {
            "fleeting-notes": {},
            "captures": {},
        },
        "_changelog": {
            "2024": {f"{i:02d}-{m}": {} for i, m in enumerate([
                "january", "february", "march", "april", "may", "june",
                "july", "august", "september", "october", "november", "december"
            ], 1)},
            "2025": {f"{i:02d}-{m}": {} for i, m in enumerate([
                "january", "february", "march", "april", "may", "june",
                "july", "august", "september", "october", "november", "december"
            ], 1)},
            "2026": {f"{i:02d}-{m}": {} for i, m in enumerate([
                "january", "february", "march", "april", "may", "june",
                "july", "august", "september", "october", "november", "december"
            ], 1)},
        },
        "_templates": {},
        "_attachments": {
            "images": {},
            "pdfs": {},
            "exports": {},
        },
    },
    "01_projects": {
        "_inbox": {},
        "_templates": {},
        "active": {},
        "on-hold": {},
    },
    "02_areas": {
        "_career": {
            "goals": {},
            "skills-development": {},
            "certifications": {},
            "resume": {},
            "job-search": {},
            "performance-reviews": {},
        },
        "_finance": {
            "budgets": {},
            "investments": {},
            "taxes": {},
            "insurance": {},
        },
        "health": {
            "fitness": {},
            "medical": {},
            "mental-health": {},
        },
        "relationships": {
            "family": {},
            "professional-network": {},
            "mentorship": {},
        },
        "home": {
            "maintenance": {},
            "improvements": {},
        },
        "personal-development": {
            "habits": {},
            "learning-goals": {},
            "reflections": {},
        },
    },
    "03_resources": {
        "_programming": {
            "languages": {
                "python": {},
                "javascript": {},
                "typescript": {},
                "go": {},
                "rust": {},
                "sql": {},
            },
            "paradigms": {
                "functional": {},
                "object-oriented": {},
                "reactive": {},
            },
            "patterns": {
                "design-patterns": {},
                "architectural-patterns": {},
                "anti-patterns": {},
            },
            "algorithms": {},
            "data-structures": {},
        },
        "_tools": {
            "editors": {
                "vscode": {},
                "vim": {},
                "jetbrains": {},
            },
            "version-control": {
                "git": {},
                "github": {},
            },
            "containers": {
                "docker": {},
                "kubernetes": {},
            },
            "ci-cd": {},
            "databases": {
                "postgresql": {},
                "mongodb": {},
                "redis": {},
            },
            "cloud": {
                "aws": {},
                "gcp": {},
                "azure": {},
            },
            "monitoring": {},
        },
        "frameworks": {
            "frontend": {
                "react": {},
                "vue": {},
                "svelte": {},
            },
            "backend": {
                "fastapi": {},
                "express": {},
                "spring": {},
            },
            "testing": {
                "pytest": {},
                "jest": {},
                "cypress": {},
            },
        },
        "systems-design": {
            "distributed-systems": {},
            "microservices": {},
            "api-design": {},
            "scalability": {},
            "reliability": {},
        },
        "devops": {
            "infrastructure-as-code": {},
            "observability": {},
            "security": {},
        },
        "books": {
            "technical": {},
            "business": {},
            "personal-growth": {},
        },
        "courses": {},
        "articles": {},
        "podcasts": {},
        "cheatsheets": {},
    },
    "04_archive": {
        "projects": {
            "completed": {
                "2024": {},
                "2025": {},
                "2026": {},
            },
            "cancelled": {},
        },
        "areas": {},
        "resources": {
            "deprecated": {},
        },
        "daily_notes": {
            "2024": {},
            "2025": {},
        },
    },
    "99_zettelkasten": {
        "_index": {},
        "_maps": {},
        "notes": {},
    },
}

# Template files to create
TEMPLATES = {
    "_meta/_templates/daily-note.md": """---
date: {{date}}
tags:
  - daily
---

# {{date}}

## Morning

### Priorities
- [ ] 

### Schedule
- 

## Notes


## Evening Review

### Accomplished
- 

### Learned
- 

### Tomorrow
- 
""",
    "_meta/_templates/weekly-review.md": """---
date: {{date}}
week: {{week_number}}
tags:
  - review/weekly
---

# Week {{week_number}} Review

## Accomplishments
- 

## Challenges
- 

## Lessons Learned
- 

## Next Week Goals
- 

## Projects Status
| Project | Status | Progress |
|---------|--------|----------|
|         |        |          |
""",
    "_meta/_templates/monthly-review.md": """---
date: {{date}}
month: {{month}}
tags:
  - review/monthly
---

# {{month}} {{year}} Review

## Goals Review
### Set
- 

### Achieved
- 

### Carried Over
- 

## Key Accomplishments
- 

## Areas of Improvement
- 

## Next Month Focus
- 
""",
    "_meta/_templates/project.md": """---
title: {{project_name}}
status: active
created: {{date}}
due: 
tags:
  - project
---

# {{project_name}}

## Overview


## Goals
- [ ] 

## Timeline
| Milestone | Due | Status |
|-----------|-----|--------|
|           |     |        |

## Resources
- 

## Notes

""",
    "_meta/_templates/zettel.md": """---
id: {{id}}
title: {{title}}
created: {{date}}
tags:
  - 
---

# {{title}}

## Idea


## Context


## Connections
- [[]]

## References
- 
""",
    "_meta/_templates/meeting-notes.md": """---
date: {{date}}
attendees:
  - 
project: 
tags:
  - meeting
---

# Meeting: {{title}}

## Agenda
- 

## Discussion


## Decisions
- 

## Action Items
- [ ] @person - task - due date

## Follow-up
- 
""",
    "_meta/_templates/book-notes.md": """---
title: {{book_title}}
author: {{author}}
status: reading
started: {{date}}
finished: 
rating: 
tags:
  - book
---

# {{book_title}}

## Summary


## Key Ideas
1. 

## Quotes
> 

## Applications
- 

## Related
- [[]]
""",
    "_meta/_templates/changelog-entry.md": """---
date: {{date}}T{{time}}
action: {{action}}
target: {{target_path}}
tags:
  - action/{{action}}
  - area/{{area}}
---

# {{Action}}: {{target_name}}

## Summary
{{Brief description of what was done}}

## Changes
- {{Change 1}}

## Context
{{Why this action was taken}}

## Related
- [[]]
""",
    "01_projects/_templates/project-kickoff.md": """---
project: {{project_name}}
created: {{date}}
status: planning
owner: 
tags:
  - project/kickoff
---

# Project Kickoff: {{project_name}}

## Problem Statement


## Goals
- 

## Success Criteria
- 

## Scope
### In Scope
- 

### Out of Scope
- 

## Timeline
| Phase | Start | End | Deliverable |
|-------|-------|-----|-------------|
|       |       |     |             |

## Resources Required
- 

## Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
|      |        |            |

## Stakeholders
- 
""",
    "01_projects/_templates/sprint-planning.md": """---
sprint: {{sprint_number}}
start: {{start_date}}
end: {{end_date}}
project: 
tags:
  - sprint
---

# Sprint {{sprint_number}}

## Goals
- 

## Backlog
| Task | Priority | Estimate | Owner |
|------|----------|----------|-------|
|      |          |          |       |

## Capacity
- 

## Dependencies
- 

## Notes
- 
""",
    "01_projects/_templates/retrospective.md": """---
sprint: {{sprint_number}}
date: {{date}}
tags:
  - retrospective
---

# Sprint {{sprint_number}} Retrospective

## What Went Well
- 

## What Didn't Go Well
- 

## What to Improve
- 

## Action Items
- [ ] 
""",
    "01_projects/_templates/feature-spec.md": """---
feature: {{feature_name}}
project: 
status: draft
created: {{date}}
tags:
  - feature-spec
---

# Feature: {{feature_name}}

## Overview


## User Story
As a [user type], I want [goal] so that [benefit].

## Requirements
### Functional
- 

### Non-Functional
- 

## Design


## Technical Approach


## Testing Strategy
- 

## Rollout Plan
- 
""",
    "_meta/_changelog/changelog-index.md": """# Changelog Index

> Activity log for all PKM system actions

## Statistics

| Period | Creates | Edits | Moves | Deletes | Archives | Total |
|--------|---------|-------|-------|---------|----------|-------|
| 2026-01 | 1 | 0 | 0 | 0 | 0 | 1 |

## Recent Activity

### 2026-01-15
- [[2026-01-15T1300-create-pkm-structure]] - Initial PKM folder structure created

---

## Quick Filters

### By Action Type
- `#action/create` - New notes and folders
- `#action/edit` - Modifications
- `#action/move` - Relocations
- `#action/delete` - Removals
- `#action/archive` - Archival actions

### By Scope
- `#scope/major` - Significant structural changes
- `#scope/minor` - Small updates
""",
    "99_zettelkasten/_index/index-main.md": """# Zettelkasten Index

> Main entry point for the slip-box

## Structure Notes
- [[index-programming]] - Programming & Software Development
- [[index-systems]] - Systems Design & Architecture
- [[index-career]] - Career & Professional Growth
- [[index-concepts]] - General Concepts & Mental Models

## Recent Notes
- 

## Most Connected
- 
""",
    "99_zettelkasten/_index/index-programming.md": """# Programming Index

## Languages
- 

## Paradigms
- 

## Patterns
- 

## Best Practices
- 
""",
    "99_zettelkasten/_index/index-systems.md": """# Systems Design Index

## Distributed Systems
- 

## Architecture Patterns
- 

## Scalability
- 

## Reliability
- 
""",
    "99_zettelkasten/_index/index-career.md": """# Career Index

## Skills Development
- 

## Leadership
- 

## Communication
- 

## Growth
- 
""",
    "99_zettelkasten/_index/index-concepts.md": """# Concepts Index

## Mental Models
- 

## Decision Making
- 

## Learning
- 

## Productivity
- 
""",
}


def create_directories(base: Path, structure: dict, created: list):
    """Recursively create directory structure."""
    for name, substructure in structure.items():
        dir_path = base / name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path.relative_to(BASE_DIR.parent)))
        if substructure:
            create_directories(dir_path, substructure, created)


def create_templates(base: Path, templates: dict, created: list):
    """Create template files."""
    for rel_path, content in templates.items():
        file_path = base / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not file_path.exists():
            file_path.write_text(content, encoding="utf-8")
            created.append(str(file_path.relative_to(BASE_DIR.parent)))


def create_changelog_entry(base: Path, action: str, summary: str, changes: list):
    """Create a changelog entry for this action."""
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m-%B").lower()
    timestamp = now.strftime("%Y-%m-%dT%H%M")
    
    changelog_dir = base / "_meta" / "_changelog" / year / month
    changelog_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{timestamp}-{action}-pkm-structure.md"
    filepath = changelog_dir / filename
    
    changes_text = "\n".join(f"- {c}" for c in changes[:20])
    if len(changes) > 20:
        changes_text += f"\n- ... and {len(changes) - 20} more items"
    
    content = f"""---
date: {now.strftime("%Y-%m-%dT%H:%M:%S")}
action: {action}
target: pkm/
tags:
  - action/{action}
  - area/system
  - scope/major
---

# {action.title()}: PKM Directory Structure

## Summary
{summary}

## Changes
{changes_text}

## Context
Automated creation of PKM folder structure via Python script.
Structure follows PARA methodology with Zettelkasten integration.

## Related
- [[pkm-structure]]
"""
    filepath.write_text(content, encoding="utf-8")
    return str(filepath.relative_to(BASE_DIR.parent))


def main():
    """Main execution."""
    print(f"Creating PKM structure in: {BASE_DIR}")
    print("-" * 50)
    
    created_items = []
    
    # Create base directory
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create directory structure
    print("Creating directories...")
    create_directories(BASE_DIR, STRUCTURE, created_items)
    
    # Create template files
    print("Creating templates...")
    create_templates(BASE_DIR, TEMPLATES, created_items)
    
    # Create changelog entry
    print("Creating changelog entry...")
    changelog_entry = create_changelog_entry(
        BASE_DIR,
        "create",
        "Complete PKM directory structure created with all PARA folders, Zettelkasten, and templates.",
        created_items
    )
    
    print("-" * 50)
    print(f"Created {len(created_items)} items")
    print(f"Changelog entry: {changelog_entry}")
    print("\nPKM structure created successfully!")
    
    return created_items


if __name__ == "__main__":
    main()
