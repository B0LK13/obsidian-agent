# Obsidian MCP - Quick Start Guide

## Installation

### 1. Install Python Dependencies

```bash
cd "obsidian-agent apps\obsidian-mcp"
pip install -r requirements.txt
```

### 2. Configure Environment

The `.env` file is already configured with your API token:
```
OBSIDIAN_API_TOKEN=4f99f4adac4ced58022f93437efbd796f43ea4a42ac9d2c974342ed9361f10ca
```

### 3. Start Obsidian Local REST API

1. Open Obsidian
2. Install "Local REST API" plugin if not installed
3. Enable the plugin
4. Note the port (default: 27123)

## Usage

### As MCP Server (for Claude/Cursor)

```bash
python -m obsidian_mcp.server
```

### Using CLI

```bash
# Check status
python -m obsidian_mcp.cli status

# List all notes
python -m obsidian_mcp.cli list

# Create a note
python -m obsidian_mcp.cli create "Projects/Idea" "# My Idea\n\nThis is a great idea!"

# Read a note
python -m obsidian_mcp.cli read "Projects/Idea"

# Search notes
python -m obsidian_mcp.cli search "MCP"

# List tags
python -m obsidian_mcp.cli tags

# Show vault stats
python -m obsidian_mcp.cli stats

# Analyze graph
python -m obsidian_mcp.cli graph
```

## Example Claude Prompts

### Create Notes
```
Create a new note called "Meeting Notes 2024-01-30" with today's meeting summary
```

### Search
```
Search for all notes containing "project" or "task"
```

### Graph Analysis
```
Find orphan notes in my vault (notes with no connections)
```

### Tag Management
```
List all tags in my vault and show which ones are most used
```

### Link Suggestions
```
Analyze my note on "Machine Learning" and suggest which existing notes I should link to it
```

### Daily Notes
```
Create today's daily note with a task list
```

## Available Tools (46 Total)

### Note Management (12)
- create_note
- read_note
- update_note
- delete_note
- list_notes
- search_notes
- search_by_tag
- get_note_metadata
- append_to_note
- create_daily_note
- get_daily_note
- get_note_links

### Link & Graph Analysis (8)
- get_backlinks
- get_forward_links
- get_orphan_notes
- get_hub_notes
- get_shortest_path
- get_connected_notes
- analyze_graph
- suggest_links

### Tag Management (5)
- list_all_tags
- search_by_tag
- get_tag_statistics
- rename_tag
- get_related_tags

### Folder Management (6)
- list_folders
- create_folder
- move_note
- rename_note
- get_folder_notes
- get_vault_statistics

### Search & Query (5)
- advanced_search
- search_by_date
- search_recent
- find_duplicates
- search_untagged

### Templates (4)
- apply_template
- create_from_template
- list_templates
- batch_create_notes

### Canvas (3)
- list_canvases
- read_canvas
- create_canvas

### External (3)
- extract_urls
- get_external_links
- create_bibliography

## Troubleshooting

### Connection Error
```
Error: Cannot connect to Obsidian API
```
**Solution**: Ensure Obsidian is running and Local REST API plugin is enabled.

### API Token Error
```
Error: 401 Unauthorized
```
**Solution**: Check that OBSIDIAN_API_TOKEN in `.env` matches your Obsidian plugin settings.

### Port Already in Use
```
Error: Port 27123 in use
```
**Solution**: Change the port in Obsidian plugin settings and update `.env`.

## Configuration Files

- `.env` - Environment variables
- `claude_desktop_config.json` - Claude Desktop MCP configuration
- `requirements.txt` - Python dependencies

## More Documentation

- `README.md` - Full documentation
- Full API documentation in source code
