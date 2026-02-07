"""CLI for PKM Agent."""

import asyncio
import json
import logging
from pathlib import Path

import click

from pkm_agent.app import PKMAgentApp
from pkm_agent.config import Config, load_config
from pkm_agent.data.link_analyzer import LinkAnalyzer
from pkm_agent.data.link_healer import LinkHealer, LinkValidator
from pkm_agent.logging_config import setup_logging

logger = logging.getLogger(__name__)


@click.group()
@click.option("--config", type=click.Path(exists=True), help="Path to config file")
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.pass_context
def cli(ctx: click.Context, config: Path | None, debug: bool):
    """PKM Agent - AI-enhanced Personal Knowledge Management."""
    cfg = load_config(config) if config else Config()
    
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

    # Only use asyncio.run for initialization/cleanup
    # Let Textual handle its own event loop for the TUI
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

    # Only use asyncio.run for initialization/cleanup
    # Let Textual handle its own event loop for the TUI
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
            import json
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
@click.option("--category", help="Filter by category (command/indexer/vectorstore/conversation)")
@click.option("--action", help="Filter by action")
@click.option("--limit", default=50, show_default=True, help="Number of entries to show")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def audit(ctx: click.Context, category: str | None, action: str | None, limit: int, as_json: bool):
    """Show recent audit log entries."""
    config = ctx.obj["config"]

    async def run():
        app = PKMAgentApp(config)
        await app.initialize()

        with app.db._get_connection() as conn:
            where_clauses = []
            params = []
            if category:
                where_clauses.append("category = ?")
                params.append(category)
            if action:
                where_clauses.append("action = ?")
                params.append(action)
            where_sql = ""
            if where_clauses:
                where_sql = "WHERE " + " AND ".join(where_clauses)
            rows = conn.execute(
                f"SELECT category, action, metadata, created_at FROM audit_logs {where_sql} ORDER BY created_at DESC LIMIT ?",
                (*params, limit),
            ).fetchall()

        entries = []
        for row in rows:
            meta = row["metadata"]
            try:
                meta = json.loads(meta) if meta else {}
            except Exception:
                meta = meta or {}
            entries.append({
                "category": row["category"],
                "action": row["action"],
                "metadata": meta,
                "created_at": row["created_at"],
            })

        if as_json:
            click.echo(json.dumps(entries, indent=2))
        else:
            if not entries:
                click.echo("No audit entries found.")
            else:
                click.echo(f"\n=== Audit Log (showing {len(entries)}) ===\n")
                for e in entries:
                    click.echo(f"[{e['created_at']}] {e['category']}.{e['action']}")
                    click.echo(f"  meta: {e['metadata']}")

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


@cli.command(name="check-links")
@click.option("--fix", is_flag=True, help="Automatically fix broken links")
@click.option("--dry-run", is_flag=True, help="Simulate fixes without writing changes")
@click.option("--min-confidence", type=float, default=0.7, help="Minimum confidence for auto-fix (0.0-1.0)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def check_links(ctx: click.Context, fix: bool, dry_run: bool, min_confidence: float, as_json: bool):
    """Check for broken links in the vault."""
    config = ctx.obj["config"]

    # Create analyzer
    analyzer = LinkAnalyzer(config.pkm_root)
    validator = LinkValidator(analyzer, min_confidence=min_confidence)

    # Validate vault
    result = validator.validate_vault(auto_suggest=True)

    if as_json:
        click.echo(json.dumps(result, indent=2))
        return

    # Display results
    click.echo("\n=== Link Validation Results ===\n")
    click.echo(f"Total broken links: {result['total_broken']}")
    click.echo(f"Fixable: {result['fixable']}")
    click.echo(f"Unfixable: {result['unfixable']}")

    if result['broken_links']:
        click.echo("\n=== Broken Links ===\n")
        for link in result['broken_links'][:20]:  # Show first 20
            click.echo(f"  {link['source_path']}:{link['line_number']}")
            click.echo(f"    → [[{link['target']}]] (type: {link['link_type']})")

        if len(result['broken_links']) > 20:
            click.echo(f"  ... and {len(result['broken_links']) - 20} more")

    if result['suggestions']:
        click.echo("\n=== Fix Suggestions ===\n")
        for sugg in result['suggestions'][:10]:  # Show first 10
            click.echo(f"  {sugg['source']}:{sugg['line']}")
            click.echo(f"    {sugg['original']} → {sugg['suggested']} ({sugg['confidence']:.1%})")

        if len(result['suggestions']) > 10:
            click.echo(f"  ... and {len(result['suggestions']) - 10} more")

    # Auto-fix if requested
    if fix:
        click.echo(f"\n{'=== DRY RUN ===' if dry_run else '=== Applying Fixes ==='}\n")

        healer = LinkHealer(validator, dry_run=dry_run)
        healing_result = healer.heal_vault(min_confidence=min_confidence)

        click.echo(f"Processed: {healing_result['total_processed']} links")
        click.echo(f"Fixed: {healing_result['fixed']}")
        click.echo(f"Failed: {healing_result['failed']}")
        click.echo(f"Skipped: {healing_result['skipped']}")

        if not dry_run and healing_result['fixed'] > 0:
            click.echo(f"\n✅ Successfully fixed {healing_result['fixed']} broken links!")
        elif dry_run:
            click.echo("\n💡 Run with --fix (without --dry-run) to apply these changes")
    elif result['fixable'] > 0:
        click.echo(f"\n💡 Run with --fix to automatically repair {result['fixable']} broken links")


@cli.command(name="link-graph")
@click.option("--top", type=int, default=20, help="Number of top hub notes to show")
@click.option("--orphans", is_flag=True, help="Show orphan notes (no incoming links)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def link_graph(ctx: click.Context, top: int, orphans: bool, as_json: bool):
    """Analyze the link graph structure of the vault."""
    config = ctx.obj["config"]

    analyzer = LinkAnalyzer(config.pkm_root)
    result = analyzer.analyze_vault()

    if as_json:
        data = {
            "total_links": result.total_links,
            "broken_links": len(result.broken_links),
            "orphan_notes": result.orphan_notes,
            "hub_notes": [{"note": n, "incoming_links": c} for n, c in result.hub_notes],
            "link_graph": {k: list(v) for k, v in result.link_graph.items()},
        }
        click.echo(json.dumps(data, indent=2))
        return

    click.echo("\n=== Vault Link Graph ===\n")
    click.echo(f"Total links: {result.total_links}")
    click.echo(f"Broken links: {len(result.broken_links)}")
    click.echo(f"Orphan notes: {len(result.orphan_notes)}")
    click.echo(f"Connected notes: {len(result.link_graph)}")

    if result.hub_notes:
        click.echo(f"\n=== Top {min(top, len(result.hub_notes))} Hub Notes ===\n")
        for note, count in result.hub_notes[:top]:
            click.echo(f"  {count:3d} ← {note}")

    if orphans and result.orphan_notes:
        click.echo("\n=== Orphan Notes (first 20) ===\n")
        for note in result.orphan_notes[:20]:
            click.echo(f"  • {note}")

        if len(result.orphan_notes) > 20:
            click.echo(f"  ... and {len(result.orphan_notes) - 20} more")


@cli.command()
@click.option("--fix", is_flag=True, help="Attempt to automatically fix issues")
@click.pass_context
def doctor(ctx: click.Context, fix: bool):
    """Diagnose and repair system issues."""
    config = ctx.obj["config"]
    from pkm_agent.health import SelfHealer, HealthChecker

    async def run():
        if fix:
            healer = SelfHealer(config)
            report = await healer.diagnose_and_heal()
            import json
            click.echo(json.dumps(report, indent=2))
        else:
            checker = HealthChecker(config)
            status = await checker.check_health(detailed=True)
            click.echo("\n=== System Health Check ===\n")
            click.echo(f"Status: {status['status'].upper()}")
            click.echo(f"Uptime: {status['uptime_seconds']:.1f}s")
            click.echo("\nChecks:")
            for check, result in status['checks'].items():
                icon = "✅" if result.get('healthy') else "❌"
                click.echo(f"  {icon} {check}: {result}")
            
            if status['status'] != 'healthy':
                click.echo("\n💡 Run 'pkm-agent doctor --fix' to attempt repairs.")

    asyncio.run(run())


@cli.command(name="mcp-server")
@click.option("--port", default=3000, help="Port for HTTP health checks")
@click.option("--no-health", is_flag=True, help="Disable HTTP health check server")
@click.option("--health-only", is_flag=True, help="Run only health server (no stdio MCP)")
@click.pass_context
def mcp_server(ctx: click.Context, port: int, no_health: bool, health_only: bool):
    """Run the MCP server with stdio transport and HTTP health checks."""
    config = ctx.obj["config"]
    from pkm_agent.health import HealthCheckServer
    from pkm_agent.mcp_server import run_stdio_server
    from pkm_agent.app import PKMAgentApp

    async def run():
        # Ensure directories exist
        config.ensure_dirs()
        
        # Initialize the app
        app = PKMAgentApp(config)
        await app.initialize()
        
        # Start health check server in background
        if not no_health:
            health_server = HealthCheckServer(config, port=port)
            asyncio.create_task(health_server.start())
            logger.info(f"Health check server started on port {port}")
        
        if health_only:
            # Keep running with just health server (for Docker)
            logger.info("Running in health-only mode (no stdio MCP)")
            while True:
                await asyncio.sleep(3600)  # Sleep forever, health server runs in background
        else:
            # Run MCP server on stdio
            logger.info("Starting MCP server on stdio...")
            await run_stdio_server(app)

    asyncio.run(run())


def main():
    """Entry point for the CLI."""
    cli(obj={}, max_content_width=120)


if __name__ == "__main__":
    main()
