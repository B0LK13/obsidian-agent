"""Obsidian MCP Tools - 46+ tools for comprehensive note management."""

from obsidian_mcp.tools.note_tools import (
    create_note,
    read_note,
    update_note,
    delete_note,
    list_notes,
    search_notes,
    search_by_tag,
    get_note_metadata,
    append_to_note,
    create_daily_note,
    get_daily_note,
    get_note_links,
)

from obsidian_mcp.tools.link_tools import (
    get_backlinks,
    get_forward_links,
    get_orphan_notes,
    get_hub_notes,
    get_shortest_path,
    get_connected_notes,
    analyze_graph,
    suggest_links,
)

from obsidian_mcp.tools.tag_tools import (
    list_all_tags,
    get_tag_statistics,
    rename_tag,
    get_related_tags,
)

from obsidian_mcp.tools.folder_tools import (
    list_folders,
    create_folder,
    move_note,
    rename_note,
    get_folder_notes,
    get_vault_statistics,
)

from obsidian_mcp.tools.search_tools import (
    advanced_search,
    search_by_date,
    search_recent,
    find_duplicates,
    search_untagged,
)

from obsidian_mcp.tools.template_tools import (
    apply_template,
    create_from_template,
    list_templates,
    batch_create_notes,
)

from obsidian_mcp.tools.canvas_tools import (
    list_canvases,
    read_canvas,
    create_canvas,
)

from obsidian_mcp.tools.external_tools import (
    extract_urls,
    get_external_links,
    create_bibliography,
)

# Export all tool functions
__all__ = [
    # Note tools (12)
    "create_note",
    "read_note",
    "update_note",
    "delete_note",
    "list_notes",
    "search_notes",
    "search_by_tag",
    "get_note_metadata",
    "append_to_note",
    "create_daily_note",
    "get_daily_note",
    "get_note_links",
    
    # Link & Graph tools (8)
    "get_backlinks",
    "get_forward_links",
    "get_orphan_notes",
    "get_hub_notes",
    "get_shortest_path",
    "get_connected_notes",
    "analyze_graph",
    "suggest_links",
    
    # Tag tools (5)
    "list_all_tags",
    "search_by_tag",
    "get_tag_statistics",
    "rename_tag",
    "get_related_tags",
    
    # Folder tools (6)
    "list_folders",
    "create_folder",
    "move_note",
    "rename_note",
    "get_folder_notes",
    "get_vault_statistics",
    
    # Search tools (5)
    "advanced_search",
    "search_by_date",
    "search_recent",
    "find_duplicates",
    "search_untagged",
    
    # Template tools (4)
    "apply_template",
    "create_from_template",
    "list_templates",
    "batch_create_notes",
    
    # Canvas tools (3)
    "list_canvases",
    "read_canvas",
    "create_canvas",
    
    # External tools (3)
    "extract_urls",
    "get_external_links",
    "create_bibliography",
]
