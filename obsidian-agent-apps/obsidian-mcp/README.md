# Obsidian MCP Server

A comprehensive Model Context Protocol (MCP) server for Obsidian, enabling AI assistants to create, read, update, delete, search, and manage notes with advanced features like tags, links, graph analysis, and more.

## Features

### Core Note Management
- ✅ Create, read, update, delete notes
- ✅ Search notes by content, title, or metadata
- ✅ List all notes in vault
- ✅ Get note metadata (creation date, modification date, tags, links)

### Advanced Features
- 🔗 Backlinks and forward links analysis
- 🏷️ Tag management and search
- 📊 Graph analysis (connected notes, orphans, hubs)
- 📝 Template-based note creation
- 🔍 Full-text search with regex support
- 📁 Folder management
- 🎨 Canvas support
- 📅 Daily notes management
- 🔗 External link extraction

### AI-Powered Features
- 🤖 Automatic note linking suggestions
- 📈 Note importance scoring
- 🔗 Knowledge graph navigation
- 📝 Smart note templates
- 📊 Vault statistics and insights

## Installation

### Prerequisites
- Python 3.9+
- Obsidian with Local REST API plugin enabled
- API token from Obsidian

### Install

```bash
cd "obsidian-agent apps\obsidian-mcp"
pip install -r requirements.txt
```

### Configuration

Create `.env` file:

```env
OBSIDIAN_API_TOKEN=4f99f4adac4ced58022f93437efbd796f43ea4a42ac9d2c974342ed9361f10ca
OBSIDIAN_API_URL=http://127.0.0.1:27123
VAULT_PATH=C:\Users\Admin\Documents\obsidian-agent apps
```

## Usage

### As MCP Server

```bash
python -m obsidian_mcp.server
```

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "python",
      "args": ["-m", "obsidian_mcp.server"],
      "env": {
        "OBSIDIAN_API_TOKEN": "4f99f4adac4ced58022f93437efbd796f43ea4a42ac9d2c974342ed9361f10ca",
        "OBSIDIAN_API_URL": "http://127.0.0.1:27123"
      }
    }
  }
}
```

## Available Tools

### Note Management (12 tools)
| Tool | Description |
|------|-------------|
| `create_note` | Create a new note with content |
| `read_note` | Read note content |
| `update_note` | Update note content |
| `delete_note` | Delete a note |
| `list_notes` | List all notes in vault |
| `search_notes` | Search notes by content |
| `search_by_tag` | Search notes by tag |
| `get_note_metadata` | Get note metadata (tags, links, dates) |
| `append_to_note` | Append content to existing note |
| `create_daily_note` | Create today's daily note |
| `get_daily_note` | Get today's daily note |
| `get_note_links` | Get all links in a note |

### Link & Graph Analysis (8 tools)
| Tool | Description |
|------|-------------|
| `get_backlinks` | Get all notes linking to a note |
| `get_forward_links` | Get all notes linked from a note |
| `get_orphan_notes` | Find notes with no connections |
| `get_hub_notes` | Find highly connected notes |
| `get_shortest_path` | Find shortest path between two notes |
| `get_connected_notes` | Get all notes connected to a note |
| `analyze_graph` | Analyze vault graph statistics |
| `suggest_links` | Suggest links for unlinked text |

### Tag Management (5 tools)
| Tool | Description |
|------|-------------|
| `list_all_tags` | List all tags in vault |
| `search_by_tag` | Find notes with specific tag |
| `get_tag_statistics` | Get tag usage statistics |
| `rename_tag` | Rename a tag across all notes |
| `get_related_tags` | Find related/co-occurring tags |

### Folder & Organization (6 tools)
| Tool | Description |
|------|-------------|
| `list_folders` | List all folders |
| `create_folder` | Create a new folder |
| `move_note` | Move note to different folder |
| `rename_note` | Rename a note |
| `get_folder_notes` | Get all notes in a folder |
| `get_vault_statistics` | Get vault statistics |

### Search & Query (5 tools)
| Tool | Description |
|------|-------------|
| `advanced_search` | Search with regex and filters |
| `search_by_date` | Search notes by date range |
| `search_recent` | Get recently modified notes |
| `find_duplicates` | Find potential duplicate notes |
| `search_untagged` | Find notes without tags |

### Template & Automation (4 tools)
| Tool | Description |
|------|-------------|
| `apply_template` | Apply template to note |
| `create_from_template` | Create note from template |
| `list_templates` | List available templates |
| `batch_create_notes` | Create multiple notes at once |

### Canvas & Visualization (3 tools)
| Tool | Description |
|------|-------------|
| `list_canvases` | List all canvas files |
| `read_canvas` | Read canvas content |
| `create_canvas` | Create a new canvas |

### External Integration (3 tools)
| Tool | Description |
|------|-------------|
| `extract_urls` | Extract all URLs from vault |
| `get_external_links` | Get external links from note |
| `create_bibliography` | Create bibliography from citations |

**Total: 46 powerful tools for Obsidian!**

## Example Usage

### Create a Note
```
Claude: Create a new note called "Project Ideas" in the Projects folder with initial content about AI automation
```

### Search Notes
```
Claude: Search for all notes containing "MCP" or "API"
```

### Graph Analysis
```
Claude: Find the most connected notes in my vault (hub notes)
```

### Tag Management
```
Claude: List all tags and show me which ones are used most frequently
```

### Daily Notes
```
Claude: Create today's daily note with a template including tasks and meetings
```

### Smart Suggestions
```
Claude: Analyze my note on "Machine Learning" and suggest which existing notes I should link to it
```

## License

MIT
