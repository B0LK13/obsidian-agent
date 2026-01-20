"""CLI interface using Typer"""

import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from typing import Optional

from .config import ObsidianAgentConfig

app = typer.Typer(
    name="obsidian-agent",
    help="Obsidian Agent CLI - Advanced indexing and search for your Obsidian vault",
)
console = Console()


@app.command()
def index(
    vault: Path = typer.Option(..., "--vault", "-v", help="Path to Obsidian vault"),
    incremental: bool = typer.Option(False, "--incremental", "-i", help="Incremental indexing"),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-index all files"),
    embeddings: bool = typer.Option(
        True, "--embeddings/--no-embeddings", help="Generate vector embeddings"
    ),
):
    """Index all notes in the vault"""
    console.print(f"[bold green]📊 Indexing vault:[/bold green] {vault}")

    if not vault.exists():
        console.print(f"[bold red]Error:[/bold red] Vault path does not exist: {vault}")
        raise typer.Exit(1)

    # TODO: Implement indexing
    console.print("[yellow]⚠️  Indexing not yet implemented[/yellow]")
    console.print("[dim]Coming soon: Full-text indexing and vector embeddings[/dim]")


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of results"),
    semantic: bool = typer.Option(
        True, "--semantic/--keyword", help="Use semantic search vs keyword search"
    ),
    threshold: Optional[float] = typer.Option(
        None, "--threshold", "-t", help="Similarity threshold (0-1)"
    ),
):
    """Search the indexed vault"""
    search_type = "semantic" if semantic else "keyword"
    console.print(f"[bold blue]🔍 Searching ([/bold blue]{search_type}[bold blue]):[/bold blue] {query}")

    # TODO: Implement search
    console.print("[yellow]⚠️  Search not yet implemented[/yellow]")
    console.print("[dim]Coming soon: Semantic and keyword search[/dim]")


@app.command()
def stats(
    vault: Optional[Path] = typer.Option(None, "--vault", "-v", help="Path to Obsidian vault")
):
    """Show vault statistics"""
    console.print("[bold green]📈 Vault Statistics[/bold green]\n")

    # TODO: Implement stats
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric")
    table.add_column("Value", justify="right")

    table.add_row("Total Notes", "[dim]N/A[/dim]")
    table.add_row("Total Words", "[dim]N/A[/dim]")
    table.add_row("Average Note Length", "[dim]N/A[/dim]")
    table.add_row("Indexed Notes", "[dim]N/A[/dim]")
    table.add_row("Last Index Time", "[dim]N/A[/dim]")

    console.print(table)
    console.print("\n[yellow]⚠️  Statistics not yet implemented[/yellow]")


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
):
    """Start API server (requires fastapi extra)"""
    console.print(f"[bold green]🚀 Starting API server[/bold green] on {host}:{port}")

    try:
        import uvicorn
        from .api.server import app as fastapi_app

        uvicorn.run(fastapi_app, host=host, port=port, reload=reload)
    except ImportError:
        console.print(
            "[bold red]Error:[/bold red] FastAPI not installed. "
            "Install with: pip install -e '.[api]'"
        )
        raise typer.Exit(1)


@app.command()
def export(
    format: str = typer.Option("json", "--format", "-f", help="Output format (json/csv/markdown)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Export vault data"""
    console.print(f"[bold green]📤 Exporting data[/bold green] as {format}")

    # TODO: Implement export
    console.print("[yellow]⚠️  Export not yet implemented[/yellow]")


@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    init: bool = typer.Option(False, "--init", help="Initialize configuration file"),
):
    """Manage configuration"""
    if show:
        config = ObsidianAgentConfig()
        console.print("[bold green]Current Configuration:[/bold green]")
        console.print(config.model_dump())

    if init:
        config_path = Path.home() / ".config/obsidian-agent/config.yaml"
        config = ObsidianAgentConfig()
        config.save_to_file(config_path)
        console.print(f"[bold green]✅ Configuration saved to:[/bold green] {config_path}")


@app.command()
def version():
    """Show version information"""
    from . import __version__

    console.print(f"[bold green]Obsidian Agent[/bold green] v{__version__}")
    console.print("Python backend for advanced Obsidian features")


if __name__ == "__main__":
    app()
