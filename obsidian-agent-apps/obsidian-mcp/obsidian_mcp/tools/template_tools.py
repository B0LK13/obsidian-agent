"""Template and automation tools for Obsidian MCP."""

import json
from datetime import datetime
from typing import Dict, List

from obsidian_mcp.client import ObsidianClient


# Default templates
DEFAULT_TEMPLATES = {
    "daily": """# {{date}}

## Tasks
- [ ] 

## Meetings
- 

## Notes


## Thoughts

""",
    "project": """# {{title}}

## Overview

## Goals
- 

## Tasks
- [ ] 

## Resources
- 

## Notes

""",
    "meeting": """# {{title}}

**Date:** {{date}}
**Attendees:** 

## Agenda
- 

## Notes

## Action Items
- [ ] 

""",
    "research": """# {{title}}

## Research Question

## Key Findings
- 

## Sources
- 

## Notes

""",
}


async def apply_template(note_path: str, template_name: str, variables: Dict = None) -> str:
    """Apply a template to an existing note.
    
    Args:
        note_path: Path to the note
        template_name: Name of template to apply
        variables: Optional variables for template
        
    Returns:
        JSON string with result
    """
    client = ObsidianClient()
    
    try:
        # Get current content
        current_content = await client.read_note(note_path)
        
        # Get template
        template = DEFAULT_TEMPLATES.get(template_name, "")
        if not template:
            return json.dumps({
                "success": False,
                "error": f"Template '{template_name}' not found",
                "available_templates": list(DEFAULT_TEMPLATES.keys()),
            }, indent=2)
        
        # Process variables
        variables = variables or {}
        variables.setdefault("date", datetime.now().strftime("%Y-%m-%d"))
        variables.setdefault("title", note_path.split("/")[-1].replace(".md", ""))
        
        for key, value in variables.items():
            template = template.replace(f"{{{{{key}}}}}", value)
        
        # Append template
        new_content = current_content + "\n\n" + template
        
        await client.update_note(note_path, new_content)
        await client.close()
        
        return json.dumps({
            "success": True,
            "message": f"Applied template '{template_name}' to {note_path}",
            "note_path": note_path,
            "template": template_name,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def create_from_template(
    note_path: str,
    template_name: str,
    variables: Dict = None,
) -> str:
    """Create a new note from a template.
    
    Args:
        note_path: Path for new note
        template_name: Name of template to use
        variables: Optional variables for template
        
    Returns:
        JSON string with creation result
    """
    client = ObsidianClient()
    
    try:
        # Get template
        template = DEFAULT_TEMPLATES.get(template_name, "")
        if not template:
            return json.dumps({
                "success": False,
                "error": f"Template '{template_name}' not found",
                "available_templates": list(DEFAULT_TEMPLATES.keys()),
            }, indent=2)
        
        # Process variables
        variables = variables or {}
        variables.setdefault("date", datetime.now().strftime("%Y-%m-%d"))
        variables.setdefault("time", datetime.now().strftime("%H:%M"))
        variables.setdefault("title", note_path.split("/")[-1].replace(".md", ""))
        
        for key, value in variables.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))
        
        # Create note
        await client.create_note(note_path, template)
        await client.close()
        
        return json.dumps({
            "success": True,
            "message": f"Created note from template '{template_name}'",
            "note_path": note_path,
            "template": template_name,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)


async def list_templates() -> str:
    """List all available templates.
    
    Returns:
        JSON string with template list
    """
    return json.dumps({
        "success": True,
        "template_count": len(DEFAULT_TEMPLATES),
        "templates": {
            name: template.split("\n")[0]  # First line as description
            for name, template in DEFAULT_TEMPLATES.items()
        },
        "template_details": {
            name: {
                "lines": len(template.split("\n")),
                "description": template.split("\n")[0].replace("# ", ""),
            }
            for name, template in DEFAULT_TEMPLATES.items()
        },
    }, indent=2)


async def batch_create_notes(
    notes: List[Dict],
    template_name: str = None,
) -> str:
    """Create multiple notes at once.
    
    Args:
        notes: List of note definitions {"path": str, "content": str, "variables": dict}
        template_name: Optional template to apply to all
        
    Returns:
        JSON string with batch creation result
    """
    client = ObsidianClient()
    
    try:
        results = []
        success_count = 0
        error_count = 0
        
        for note_def in notes:
            try:
                path = note_def.get("path")
                content = note_def.get("content", "")
                variables = note_def.get("variables", {})
                
                if template_name:
                    template = DEFAULT_TEMPLATES.get(template_name, "")
                    # Process variables
                    for key, value in {**variables, "title": path.split("/")[-1].replace(".md", "")}.items():
                        template = template.replace(f"{{{{{key}}}}}", str(value))
                    content = template
                
                await client.create_note(path, content)
                
                results.append({
                    "path": path,
                    "success": True,
                })
                success_count += 1
                
            except Exception as e:
                results.append({
                    "path": note_def.get("path", "unknown"),
                    "success": False,
                    "error": str(e),
                })
                error_count += 1
        
        await client.close()
        
        return json.dumps({
            "success": True,
            "total": len(notes),
            "created": success_count,
            "failed": error_count,
            "results": results,
        }, indent=2)
    
    except Exception as e:
        await client.close()
        return json.dumps({
            "success": False,
            "error": str(e),
        }, indent=2)
