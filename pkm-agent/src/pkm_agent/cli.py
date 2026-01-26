"""CLI interface for PKM Agent"""

import typer

app = typer.Typer(help="PKM Agent - Personal Knowledge Management")


@app.command()
def index(vault: str = typer.Option(..., help="Path to Obsidian vault")):
    """Index vault for search"""
    typer.echo(f"Indexing vault: {vault}")
    # Actual indexing implementation would go here


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Host to bind to"),
    port: int = typer.Option(8765, help="Port to bind to"),
):
    """Start WebSocket sync server"""
    typer.echo(f"Starting server on {host}:{port}")
    # Actual server implementation would go here


@app.command()
def search(query: str, limit: int = typer.Option(10, help="Number of results")):
    """Search indexed vault"""
    typer.echo(f"Searching for: {query} (limit: {limit})")
    # Actual search implementation would go here


if __name__ == "__main__":
    app()
