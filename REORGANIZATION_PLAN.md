# B0LK13v2 Project Reorganization Plan

## Current Issues
1. **Deep nesting**: `B0LK13v2/B0LK13v2/B0LK13v2/` creates confusion
2. **Duplicate codebases**: Multiple copies of pkm-agent and obsidian plugins
3. **Empty directories**: pkm-agent-local, various nested folders
4. **Scattered documentation**: MD files spread across multiple locations
5. **Redundant setup scripts**: Multiple .bat files doing similar things

## New Unified Structure

```
B0LK13v2/
├── README.md                    # Main project README
├── .env.example                 # Environment template
├── .gitignore                   # Unified gitignore
├── pyproject.toml               # Python project config
├── package.json                 # Root workspace for JS/TS
│
├── apps/                        # Application packages
│   ├── pkm-agent/               # Python PKM Agent (consolidated)
│   │   ├── src/pkm_agent/       # Main Python source
│   │   ├── tests/               # Python tests
│   │   ├── pyproject.toml       # Package config
│   │   └── README.md
│   │
│   ├── obsidian-plugin/         # Obsidian Plugin (consolidated)
│   │   ├── src/                 # TypeScript source
│   │   ├── main.ts              # Plugin entry
│   │   ├── package.json
│   │   └── README.md
│   │
│   └── web/                     # Next.js Blog/Web UI
│       ├── components/
│       ├── pages/
│       ├── package.json
│       └── README.md
│
├── docs/                        # All documentation
│   ├── setup/                   # Setup guides
│   ├── architecture/            # Architecture docs
│   ├── api/                     # API documentation
│   └── changelog/               # Change history
│
├── knowledge-base/              # PKM vault content (keep as-is)
│
├── scripts/                     # Utility scripts
│   ├── setup.bat                # Windows setup
│   ├── setup.sh                 # Unix setup
│   └── verify.py                # Verification script
│
├── configs/                     # Configuration files
│   └── .env.example
│
└── archive/                     # Old/deprecated files
    └── (moved old duplicates here)
```

## Migration Steps

### Phase 1: Create New Structure
- [x] Create this plan document
- [ ] Create apps/ directory structure
- [ ] Create docs/ directory structure
- [ ] Create scripts/ directory

### Phase 2: Consolidate PKM Agent
- [ ] Use B0LK13v2/pkm-agent as base (most complete)
- [ ] Move to apps/pkm-agent/
- [ ] Merge any unique code from pkm-agent/

### Phase 3: Consolidate Obsidian Plugin
- [ ] Merge obsidian-agent and obsidian-pkm-agent
- [ ] Move to apps/obsidian-plugin/

### Phase 4: Consolidate Web/Blog
- [ ] Move B0LK13 to apps/web/
- [ ] Clean up unnecessary files

### Phase 5: Consolidate Documentation
- [ ] Move all .md files to docs/
- [ ] Organize by category
- [ ] Remove duplicates

### Phase 6: Cleanup
- [ ] Move old directories to archive/
- [ ] Remove empty directories
- [ ] Update all imports and paths
- [ ] Create unified README

## Files to Archive (Not Delete)
- B0LK13v2/B0LK13v2/ (nested duplicate)
- pkm-agent/ (duplicate of B0LK13v2/pkm-agent)
- pkm-agent-local/ (empty)
- Multiple redundant .bat files
- Duplicate .md documentation files
