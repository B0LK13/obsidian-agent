"""Command-line interface for Obsidian MCP."""

import asyncio
import json
from typing import Any

import click
from rich.console import Console
from rich.json import JSON as RichJSON
from rich.panel import Panel
from rich.table import Table

from obsidian_mcp.config import get_settings
from obsidian_mcp.client import ObsidianClient
from obsidian_mcp.tools import (
    create_note, read_note, update_note, delete_note,
    list_notes, search_notes, search_by_tag,
    list_all_tags, get_vault_statistics, analyze_graph,
)

console = Console()


def coro(f):
    """Decorator to run async functions."""
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.pass_context
def cli(ctx: click.Context, debug: bool) -> None:
    """Obsidian MCP - Command-line interface for Obsidian vault management."""
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug


@cli.command()
@coro
async def status() -> None:
    """Check Obsidian connection status."""
    settings = get_settings()
    client = ObsidianClient()
    
    try:
        files = await client.list_files()
        await client.close()
        
        console.print(Panel(
            f"[green]Connected to Obsidian[/green]\n"
            f"API URL: {settings.obsidian_api_url}\n"
            f"Files in vault: {len(files)}",
            title="Status",
            border_style="green",
        ))
    except Exception as e:
        console.print(Panel(
            f"[red]Connection failed[/red]\n"
            f"Error: {e}",
            title="Status",
            border_style="red",
        ))


@cli.command()
@click.argument("path")
@click.argument("content")
@click.option("--folder", default="", help="Folder path")
@coro
async def create(path: str, content: str, folder: str) -> None:
    """Create a new note."""
    result = await create_note(path, content, folder)
    console.print(RichJSON(result))


@cli.command()
@click.argument("path")
@coro
async def read(path: str) -> None:
    """Read a note."""
    result = await read_note(path)
    data = json.loads(result)
    
    if data.get("success"):
        console.print(Panel(
            data["content"],
            title=f"📄 {path}",
            border_style="blue",
        ))
    else:
        console.print(f"[red]Error: {data.get('error')}[/red]")


@cli.command()
@click.argument("path")
@click.argument("content")
@coro
async def update(path: str, content: str) -> None:
    """Update a note."""
    result = await update_note(path, content)
    console.print(RichJSON(result))


@cli.command()
@click.argument("path")
@coro
async def delete(path: str) -> None:
    """Delete a note."""
    result = await delete_note(path)
    console.print(RichJSON(result))


@cli.command(name="list")
@click.option("--folder", default="", help="Folder to list")
@click.option("--ext", default=".md", help="File extension filter")
@coro
async def list_cmd(folder: str, ext: str) -> None:
    """List notes in vault."""
    result = await list_notes(folder, ext)
    data = json.loads(result)
    
    if data.get("success"):
        table = Table(title=f"Notes in {folder or 'root'}")
        table.add_column("Path", style="cyan")
        
        for note in data.get("notes", [])[:50]:  # Limit to 50
            table.add_row(note)
        
        console.print(table)
        console.print(f"Total: {data.get('count')} notes")
    else:
        console.print(f"[red]Error: {data.get('error')}[/red]")


@cli.command()
@click.argument("query")
@coro
async def search(query: str) -> None:
    """Search notes."""
    result = await search_notes(query)
    console.print(RichJSON(result))


@cli.command()
@click.argument("tag")
@coro
async def tags(tag: str = None) -> None:
    """List all tags or search by tag."""
    if tag:
        result = await search_by_tag(tag)
    else:
        result = await list_all_tags()
    
    data = json.loads(result)
    
    if data.get("success"):
        if "tags" in data:
            table = Table(title="Tags in Vault")
            table.add_column("Tag", style="cyan")
            table.add_column("Count", style="green", justify="right")
            
            for tag_name, count in list(data["tags"].items())[:30]:
                table.add_row(f"#{tag_name}", str(count))
            
            console.print(table)
        else:
            console.print(RichJSON(result))
    else:
        console.print(f"[red]Error: {data.get('error')}[/red]")


@cli.command()
@coro
async def stats() -> None:
    """Show vault statistics."""
    result = await get_vault_statistics()
    console.print(RichJSON(result))


@cli.command()
@coro
async def graph() -> None:
    """Analyze vault graph."""
    result = await analyze_graph()
    console.print(RichJSON(result))


def main() -> None:
    """Entry point."""
    cli()


if __name__ == "__main__":
    main()
