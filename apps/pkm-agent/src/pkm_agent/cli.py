"""CLI for PKM Agent."""

import asyncio
import json
import logging
from pathlib import Path

import click

from pkm_agent.app import PKMAgentApp
from pkm_agent.config import Config, load_config
from pkm_agent.logging_config import setup_logging

logger = logging.getLogger(__name__)


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
    """PKM Agent - AI-enhanced Personal Knowledge Management."""
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
    pkm_app = PKMAgentApp(config)

    if not no_index:
        asyncio.run(pkm_app.initialize())

    tui_app = PKMTUI(pkm_app, initial_prompt=prompt)
    try:
        tui_app.run()
    finally:
        asyncio.run(pkm_app.close())


@cli.command()
@click.option("--no-index", is_flag=True, help="Skip indexing on startup")
@click.option("--prompt", "-p", help="Initial prompt to send")
@click.pass_context
def studio(ctx: click.Context, no_index: bool, prompt: str | None):
    """Launch the advanced PKM Studio TUI."""
    from pkm_agent.studio import PKMStudio

    config = ctx.obj["config"]
    pkm_app = PKMAgentApp(config)

    if not no_index:
        asyncio.run(pkm_app.initialize())

    studio_app = PKMStudio(pkm_app, initial_prompt=prompt)
    try:
        studio_app.run()
    finally:
        asyncio.run(pkm_app.close())


@cli.command()
@click.option("--no-index", is_flag=True, help="Skip indexing")
@click.pass_context
def index(ctx: click.Context, no_index: bool):
    """Index the PKM directory."""
    config = ctx.obj["config"]

    async def run():
        app = PKMAgentApp(config)

        if no_index:
            click.echo("Skipping indexing...")
            return

        with click.progressbar(length=100, label="Indexing") as bar:
            stats = await app.index_pkm()
            bar.update(100)

        click.echo(f"\nIndexed {stats['indexed']} notes")

        db_stats = app.db.get_stats()
        click.echo(f"Database: {db_stats['notes']} notes, {db_stats['tags']} tags")

        vs_stats = app.vectorstore.get_stats()
        click.echo(f"Vector store: {vs_stats['total_chunks']} chunks")

        await app.close()

    asyncio.run(run())


@cli.command()
@click.argument("query")
@click.option("--limit", "-n", default=10, help="Number of results")
@click.option("--area", help="Filter by area")
@click.option("--tag", help="Filter by tag")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def search(
    ctx: click.Context,
    query: str,
    limit: int,
    area: str | None,
    tag: str | None,
    as_json: bool,
):
    """Search for notes."""
    config = ctx.obj["config"]

    async def run():
        app = PKMAgentApp(config)
        await app.initialize()

        filters = {}
        if area:
            filters["area"] = area
        if tag:
            filters["tags"] = tag

        results = await app.search(query, limit=limit, filters=filters)

        if as_json:
            click.echo(json.dumps(results, indent=2))
        else:
            click.echo(f"\nFound {len(results)} results for: {query}\n")
            for i, r in enumerate(results, 1):
                click.echo(f"{i}. {r['title']}")
                click.echo(f"   {r['path']}")
                click.echo(f"   Score: {r['score']:.2f}")
                click.echo(f"   {r['snippet'][:200]}...")
                click.echo()

        await app.close()

    asyncio.run(run())


@cli.command()
@click.argument("message")
@click.option("--conversation", "-c", help="Conversation ID to continue")
@click.option("--no-context", is_flag=True, help="Don't use knowledge base context")
@click.pass_context
def ask(
    ctx: click.Context,
    message: str,
    conversation: str | None,
    no_context: bool,
):
    """Ask a question to the PKM agent."""
    config = ctx.obj["config"]

    async def run():
        app = PKMAgentApp(config)
        await app.initialize()

        if no_context:
            click.echo("Response:")
            async for chunk in app.chat(message, conversation_id=conversation, use_context=False):
                click.echo(chunk, nl=False)
        else:
            click.echo("Response:")
            async for chunk in app.ask_with_context(message):
                click.echo(chunk, nl=False)

        click.echo("\n")
        await app.close()

    asyncio.run(run())


@cli.command()
@click.pass_context
def stats(ctx: click.Context):
    """Show PKM statistics."""
    config = ctx.obj["config"]

    async def run():
        app = PKMAgentApp(config)
        await app.initialize()

        stats = await app.get_stats()

        click.echo("\n=== PKM Agent Statistics ===\n")
        click.echo(f"PKM Root: {stats['pkm_root']}")
        click.echo(f"\nNotes: {stats['notes']}")
        click.echo(f"Tags: {stats['tags']}")
        click.echo(f"Links: {stats['links']}")
        click.echo(f"Total Words: {stats['total_words']:,}")
        click.echo("\nVector Store:")
        click.echo(f"  Chunks: {stats['vector_store']['total_chunks']}")
        click.echo(f"  Collection: {stats['vector_store']['collection_name']}")
        click.echo("\nLLM:")
        click.echo(f"  Provider: {stats['llm']['provider']}")
        click.echo(f"  Model: {stats['llm']['model']}")

        await app.close()

    asyncio.run(run())


@cli.command()
@click.pass_context
def conversations(ctx: click.Context):
    """List all conversations."""
    config = ctx.obj["config"]

    async def run():
        app = PKMAgentApp(config)
        await app.initialize()

        convs = app.list_conversations()

        if not convs:
            click.echo("No conversations found.")
            return

        click.echo(f"\n=== Conversations ({len(convs)}) ===\n")
        for conv in convs:
            click.echo(f"ID: {conv['id']}")
            click.echo(f"Started: {conv['started_at']}")
            click.echo(f"Messages: {conv['message_count']}")
            click.echo()

        await app.close()

    asyncio.run(run())


def main():
    """Entry point for the CLI."""
    cli(obj={}, max_content_width=120)


if __name__ == "__main__":
    main()
