"""Enhanced CLI with Phase 1 features: research, stats, rollback, cache management."""

import asyncio
import json
import logging
from pathlib import Path

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from pkm_agent.app_enhanced import EnhancedPKMAgent
from pkm_agent.config import Config, load_config
from pkm_agent.logging_config import setup_logging

logger = logging.getLogger(__name__)
console = Console()


def find_config_file() -> Path | None:
    """Find config file in standard locations."""
    locations = [
        Path.cwd() / ".pkm-agent" / "config.toml",
        Path.cwd() / "config.toml",
        Path.home() / ".pkm-agent" / "config.toml",
        Path.home() / ".config" / "pkm-agent" / "config.toml",
    ]
    for loc in locations:
        if loc.exists():
            return loc
    return None


@click.group()
@click.option("--config", type=click.Path(exists=True), help="Path to config file")
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.pass_context
def cli(ctx: click.Context, config: Path | None, debug: bool):
    """PKM Agent - AI-enhanced Personal Knowledge Management (Enhanced)."""
    config_path = Path(config) if config else find_config_file()
    cfg = load_config(config_path) if config_path else Config()
    
    if debug:
        cfg.debug = True
        cfg.log_level = "DEBUG"
        
    setup_logging(cfg)
    
    ctx.ensure_object(dict)
    ctx.obj["config"] = cfg


@cli.command()
@click.option("--no-index", is_flag=True, help="Skip indexing on startup")
@click.option("--prompt", "-p", help="Initial prompt to send")
@click.pass_context
def tui(ctx: click.Context, no_index: bool, prompt: str | None):
    """Launch the TUI interface."""
    from pkm_agent.tui import PKMTUI

    config = ctx.obj["config"]
    app = EnhancedPKMAgent(config)
    
    tui_app = PKMTUI(app)
    
    async def run():
        if not no_index:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task(description="Initializing PKM Agent...", total=None)
                await app.initialize()
        
        if prompt:
            # Auto-send prompt after startup
            pass  # TUI would handle this
        
        await tui_app.run_async()
    
    asyncio.run(run())


@cli.command()
@click.argument("topic")
@click.option("--create-note", is_flag=True, help="Create a summary note")
@click.option("--max-steps", default=10, help="Maximum agent iterations")
@click.pass_context
def research(ctx: click.Context, topic: str, create_note: bool, max_steps: int):
    """Autonomous research using ReAct agent.
    
    Example:
        pkma research "machine learning" --create-note
    """
    config = ctx.obj["config"]
    app = EnhancedPKMAgent(config)
    
    async def run():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(description="Initializing...", total=None)
            await app.initialize()
            
            progress.update(task, description=f"Researching '{topic}'...")
            result = await app.research(topic, create_summary=create_note)
        
        # Display results
        console.print(Panel(f"[bold green]Research Complete: {result['status']}", expand=False))
        console.print()
        
        # Show reasoning chain
        console.print("[bold]Reasoning Chain:[/bold]")
        for step in result["reasoning_chain"]:
            console.print(f"[cyan]Step {step['step']}:[/cyan]")
            console.print(f"  Thought: {step['thought']}")
            if step['action']:
                console.print(f"  Action: {step['action']}")
            if step['observation']:
                console.print(f"  Observation: {step['observation'][:200]}...")
            console.print()
        
        # Show final answer
        console.print(Panel(Markdown(result["answer"]), title="[bold]Final Answer", expand=False))
        
        await app.close()
    
    asyncio.run(run())


@cli.command()
@click.pass_context
def stats(ctx: click.Context):
    """Show PKM Agent statistics including cache and audit metrics."""
    config = ctx.obj["config"]
    app = EnhancedPKMAgent(config)
    
    async def run():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Gathering statistics...", total=None)
            await app.initialize()
            stats = await app.get_stats()
        
        # Display stats in tables
        console.print(Panel("[bold green]PKM Agent Statistics", expand=False))
        console.print()
        
        # General stats
        table = Table(title="General")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("PKM Root", stats.get("pkm_root", "N/A"))
        table.add_row("Total Notes", str(stats.get("total_notes", 0)))
        table.add_row("Total Chunks", str(stats.get("vector_store", {}).get("total_chunks", 0)))
        console.print(table)
        console.print()
        
        # Cache stats
        cache_stats = stats.get("cache", {})
        if cache_stats:
            table = Table(title="Cache Performance")
            table.add_column("Cache Type", style="cyan")
            table.add_column("Hits", style="green")
            table.add_column("Misses", style="yellow")
            table.add_column("Hit Rate", style="magenta")
            
            query_cache = cache_stats.get("query_cache", {})
            table.add_row(
                "Query Cache",
                str(query_cache.get("hits", 0)),
                str(query_cache.get("misses", 0)),
                f"{query_cache.get('hit_rate', 0):.1%}",
            )
            
            embed_cache = cache_stats.get("embedding_cache", {})
            table.add_row(
                "Embedding Cache",
                "-",
                "-",
                f"{embed_cache.get('entries', 0)} entries ({embed_cache.get('total_size_mb', 0):.1f} MB)",
            )
            
            console.print(table)
            console.print()
        
        # Audit stats
        audit_stats = stats.get("audit", {})
        if audit_stats:
            table = Table(title="Audit Trail")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            table.add_row("Total Operations", str(audit_stats.get("total_entries", 0)))
            table.add_row("Rolled Back", str(audit_stats.get("rolled_back", 0)))
            
            by_action = audit_stats.get("by_action", {})
            for action, count in sorted(by_action.items(), key=lambda x: x[1], reverse=True)[:5]:
                table.add_row(f"  {action}", str(count))
            
            console.print(table)
        
        await app.close()
    
    asyncio.run(run())


@cli.command()
@click.option("--action", help="Filter by action type")
@click.option("--limit", default=20, help="Number of entries to show")
@click.pass_context
def audit(ctx: click.Context, action: str | None, limit: int):
    """View audit log history.
    
    Example:
        pkma audit --action research --limit 10
    """
    config = ctx.obj["config"]
    app = EnhancedPKMAgent(config)
    
    async def run():
        await app.initialize()
        history = await app.audit_logger.get_history(action=action, limit=limit)
        
        if not history:
            console.print("[yellow]No audit entries found.")
            await app.close()
            return
        
        table = Table(title=f"Audit Log ({len(history)} entries)")
        table.add_column("Timestamp", style="cyan")
        table.add_column("Action", style="yellow")
        table.add_column("Target", style="green")
        table.add_column("Reversible", style="magenta")
        
        for entry in history:
            table.add_row(
                entry.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                entry.action,
                entry.target or "-",
                "✓" if entry.reversible else "✗",
            )
        
        console.print(table)
        await app.close()
    
    asyncio.run(run())


@cli.command()
@click.argument("operation_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def rollback(ctx: click.Context, operation_id: str, yes: bool):
    """Rollback a previous operation by ID.
    
    Example:
        pkma rollback abc-123-def --yes
    """
    config = ctx.obj["config"]
    app = EnhancedPKMAgent(config)
    
    async def run():
        await app.initialize()
        
        # Get operation details
        entry = await app.audit_logger.get_entry(operation_id)
        
        if not entry:
            console.print(f"[red]Operation {operation_id} not found.")
            await app.close()
            return
        
        if not entry.reversible:
            console.print(f"[red]Operation {operation_id} is not reversible.")
            await app.close()
            return
        
        # Show details
        console.print(Panel(f"[bold]Operation Details", expand=False))
        console.print(f"  Action: {entry.action}")
        console.print(f"  Target: {entry.target}")
        console.print(f"  Timestamp: {entry.timestamp}")
        console.print()
        
        if not yes:
            confirm = click.confirm("Do you want to rollback this operation?")
            if not confirm:
                console.print("[yellow]Rollback cancelled.")
                await app.close()
                return
        
        # Perform rollback
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Rolling back operation...", total=None)
            success = await app.rollback_operation(operation_id)
        
        if success:
            console.print("[green]✓ Operation rolled back successfully!")
        else:
            console.print("[red]✗ Rollback failed.")
        
        await app.close()
    
    asyncio.run(run())


@cli.command()
@click.option("--all", "clear_all", is_flag=True, help="Clear all caches")
@click.option("--query", is_flag=True, help="Clear query cache")
@click.option("--embedding", is_flag=True, help="Clear embedding cache")
@click.option("--chunk", is_flag=True, help="Clear chunk cache")
@click.pass_context
def clear_cache(ctx: click.Context, clear_all: bool, query: bool, embedding: bool, chunk: bool):
    """Clear PKM Agent caches.
    
    Example:
        pkma clear-cache --all
        pkma clear-cache --query --embedding
    """
    config = ctx.obj["config"]
    app = EnhancedPKMAgent(config)
    
    async def run():
        await app.initialize()
        
        if clear_all or (not query and not embedding and not chunk):
            app.cache.clear_all()
            console.print("[green]✓ All caches cleared!")
        else:
            if query:
                app.cache.query_cache.clear()
                console.print("[green]✓ Query cache cleared!")
            if embedding:
                app.cache.embedding_cache.clear()
                console.print("[green]✓ Embedding cache cleared!")
            if chunk:
                app.cache.chunk_cache.clear()
                console.print("[green]✓ Chunk cache cleared!")
        
        await app.close()
    
    asyncio.run(run())


def main():
    """Entry point for CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
