"""CLI interface using Typer"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import (
    ObsidianAgentConfig,
    VaultConfig,
    DatabaseConfig,
    VectorStoreConfig,
    SearchConfig,
    IndexingConfig,
)

app = typer.Typer(
    name="obsidian-agent",
    help="Obsidian Agent CLI - Advanced indexing and search for your Obsidian vault",
)
console = Console()
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def get_default_config(vault_path: Optional[Path] = None) -> ObsidianAgentConfig:
    """Get default configuration"""
    vault_config = VaultConfig(path=vault_path or Path.home() / "Documents" / "Vault")
    return ObsidianAgentConfig(
        vault=vault_config,
        database=DatabaseConfig(),
        vector_store=VectorStoreConfig(),
        search=SearchConfig(),
        indexing=IndexingConfig(),
    )


@app.command()
def index(
    vault: Path = typer.Option(..., "--vault", "-v", help="Path to Obsidian vault"),
    incremental: bool = typer.Option(True, "--incremental/--full", "-i", help="Incremental indexing"),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-index all files"),
    embeddings: bool = typer.Option(True, "--embeddings/--no-embeddings", help="Generate vector embeddings"),
):
    """Index all notes in the vault"""
    if not vault.exists():
        console.print(f"[bold red]Error:[/bold red] Vault path does not exist: {vault}")
        raise typer.Exit(1)
    
    console.print(f"[bold green]Indexing vault:[/bold green] {vault}")
    
    try:
        from .database import DatabaseConnection
        from .indexing import VaultIndexer
        from .vector_store import ChromaDBStore
        
        config = get_default_config(vault)
        config.vault.path = vault
        
        db = DatabaseConnection(config.database.path)
        db.initialize_database()
        
        vector_store = None
        if embeddings:
            console.print("[dim]Loading embedding model...[/dim]")
            vector_store = ChromaDBStore(config.vector_store)
            vector_store.initialize()
        
        indexer = VaultIndexer(
            vault_config=config.vault,
            indexing_config=config.indexing,
            db=db,
            vector_store=vector_store,
        )
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task("Indexing notes...", total=None)
            
            def update_progress(current, total):
                progress.update(task, description=f"Indexing notes... ({current}/{total})")
            
            stats = indexer.index_vault(incremental=incremental, force=force, progress_callback=update_progress)
        
        console.print(f"\n[bold green]Indexing complete![/bold green]")
        console.print(f"  Indexed: {stats['indexed']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}, Duration: {stats['duration']:.2f}s")
        
        db.close()
        if vector_store:
            vector_store.close()
            
    except ImportError as e:
        console.print(f"[bold red]Error:[/bold red] Missing dependency: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        logger.exception("Indexing failed")
        raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    vault: Optional[Path] = typer.Option(None, "--vault", "-v", help="Path to Obsidian vault"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of results"),
    semantic: bool = typer.Option(True, "--semantic/--keyword", help="Use semantic vs keyword search"),
    threshold: Optional[float] = typer.Option(None, "--threshold", "-t", help="Similarity threshold (0-1)"),
):
    """Search the indexed vault"""
    search_type = "semantic" if semantic else "keyword"
    console.print(f"[bold blue]Searching ({search_type}):[/bold blue] {query}")
    
    try:
        from .database import DatabaseConnection
        from .search import SearchService
        from .vector_store import ChromaDBStore
        
        config = get_default_config(vault)
        db = DatabaseConnection(config.database.path)
        
        vector_store = None
        if semantic:
            try:
                vector_store = ChromaDBStore(config.vector_store)
                vector_store.initialize()
            except Exception:
                console.print("[yellow]Warning: Vector store unavailable, falling back to keyword search[/yellow]")
                semantic = False
        
        search_service = SearchService(config=config.search, db=db, vector_store=vector_store)
        results = search_service.search(query=query, limit=limit, semantic=semantic, threshold=threshold)
        
        if not results:
            console.print("[dim]No results found.[/dim]")
        else:
            console.print(f"\n[bold]Found {len(results)} results:[/bold]\n")
            for i, result in enumerate(results, 1):
                score_str = f"{result.score:.2f}" if result.score else "N/A"
                console.print(f"[cyan]{i}.[/cyan] [bold]{result.title}[/bold] (score: {score_str})")
                console.print(f"   [dim]{result.path}[/dim]")
                if result.snippet:
                    console.print(f"   {result.snippet[:200]}")
                console.print()
        
        db.close()
        if vector_store:
            vector_store.close()
            
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        logger.exception("Search failed")
        raise typer.Exit(1)


@app.command()
def stats(vault: Optional[Path] = typer.Option(None, "--vault", "-v", help="Path to Obsidian vault")):
    """Show vault statistics"""
    console.print("[bold green]Vault Statistics[/bold green]\n")
    
    try:
        from .database import DatabaseConnection
        from .search import SearchService
        from .vector_store import ChromaDBStore
        
        config = get_default_config(vault)
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric")
        table.add_column("Value", justify="right")
        
        if config.database.path.exists():
            db = DatabaseConnection(config.database.path)
            vector_store = None
            if config.vector_store.persist_directory.exists():
                try:
                    vector_store = ChromaDBStore(config.vector_store)
                    vector_store.initialize()
                except:
                    pass
            
            search_service = SearchService(config=config.search, db=db, vector_store=vector_store)
            stats = search_service.get_stats()
            
            table.add_row("Total Notes", str(stats["total_notes"]))
            table.add_row("Vector Indexed", str(stats["vector_indexed"]))
            table.add_row("Database Path", str(config.database.path))
            
            db.close()
            if vector_store:
                vector_store.close()
        else:
            table.add_row("Status", "[yellow]Not indexed yet[/yellow]")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def health():
    """Check system health"""
    asyncio.run(_health())


async def _health():
    """Run health checks"""
    from .health import HealthChecker, HealthStatus
    
    config = get_default_config()
    checker = HealthChecker()
    
    console.print("[bold]Running health checks...[/bold]\n")
    
    checks = await checker.check_all(
        db_path=config.database.path,
        vault_path=config.vault.path if config.vault.path.exists() else None,
        vector_persist_dir=config.vector_store.persist_directory,
    )
    
    table = Table(title="System Health")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Message")
    
    overall_healthy = True
    for name, check in checks.items():
        if check.status == HealthStatus.HEALTHY:
            status_icon = "[green]HEALTHY[/green]"
        elif check.status == HealthStatus.DEGRADED:
            status_icon = "[yellow]DEGRADED[/yellow]"
            overall_healthy = False
        else:
            status_icon = "[red]UNHEALTHY[/red]"
            overall_healthy = False
        table.add_row(check.name, status_icon, check.message)
    
    console.print(table)
    
    if overall_healthy:
        console.print("\n[green]All systems operational[/green]")
    else:
        console.print("\n[yellow]Some components need attention[/yellow]")


@app.command()
def version():
    """Show version information"""
    from . import __version__
    console.print(f"[bold green]Obsidian Agent[/bold green] v{__version__}")


if __name__ == "__main__":
    app()
