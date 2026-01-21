"""
CLI interface for Obsidian Agent
"""

import sys
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from obsidian_agent.indexer import VaultIndexer
from obsidian_agent.search import VaultSearcher


console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="obsidian-agent")
def main():
    """Obsidian Agent CLI - Index and search your Obsidian vault"""
    pass


@main.command()
@click.argument('vault_path', type=click.Path(exists=True), required=False)
@click.option('--index-dir', '-i', type=click.Path(), help='Custom index directory')
@click.option('--force', '-f', is_flag=True, help='Force reindex all documents')
def index(vault_path, index_dir, force):
    """Index the Obsidian vault for searching"""
    
    # Use current directory if no vault path provided
    if vault_path is None:
        vault_path = Path.cwd()
        console.print(f"[yellow]No vault path provided, using current directory: {vault_path}[/yellow]")
    
    try:
        console.print(f"[blue]Indexing vault at: {vault_path}[/blue]")
        
        indexer = VaultIndexer(vault_path, index_dir)
        
        with console.status("[bold green]Indexing documents..."):
            stats = indexer.index_vault(force=force)
        
        # Display results
        console.print(f"\n[green]✓[/green] Indexing complete!")
        console.print(f"  • Indexed: {stats['indexed']} documents")
        console.print(f"  • Skipped: {stats['skipped']} files")
        if stats['errors'] > 0:
            console.print(f"  • [red]Errors: {stats['errors']}[/red]")
        
        return 0
    except Exception as e:
        console.print(f"[red]✗ Error during indexing: {e}[/red]")
        return 1


@main.command()
@click.argument('query', nargs=-1, required=True)
@click.argument('vault_path', type=click.Path(exists=True), required=False)
@click.option('--index-dir', '-i', type=click.Path(), help='Custom index directory')
@click.option('--limit', '-l', type=int, default=10, help='Maximum number of results')
@click.option('--fields', '-f', multiple=True, help='Fields to search (title, content, tags)')
def search(query, vault_path, index_dir, limit, fields):
    """Search the indexed vault"""
    
    # Use current directory if no vault path provided
    if vault_path is None:
        vault_path = Path.cwd()
    
    # Join query terms
    query_str = ' '.join(query)
    
    try:
        searcher = VaultSearcher(vault_path, index_dir)
        
        # Convert fields tuple to list if provided
        search_fields = list(fields) if fields else None
        
        with console.status("[bold green]Searching..."):
            results = searcher.search(query_str, limit=limit, fields=search_fields)
        
        if not results:
            console.print(f"\n[yellow]No results found for: {query_str}[/yellow]")
            return 0
        
        # Display results
        console.print(f"\n[green]Found {len(results)} result(s) for: {query_str}[/green]\n")
        
        for i, result in enumerate(results, 1):
            console.print(f"[bold cyan]{i}. {result['title']}[/bold cyan]")
            console.print(f"   Path: {result['path']}")
            console.print(f"   Score: {result['score']:.2f}")
            if result.get('excerpt'):
                console.print(f"   Excerpt: {result['excerpt'][:200]}...")
            console.print()
        
        return 0
    except ValueError as e:
        console.print(f"[red]✗ {e}[/red]")
        console.print("[yellow]Hint: Run 'obsidian-agent index' first to create the index.[/yellow]")
        return 1
    except Exception as e:
        console.print(f"[red]✗ Error during search: {e}[/red]")
        return 1


@main.command()
@click.argument('vault_path', type=click.Path(exists=True), required=False)
@click.option('--index-dir', '-i', type=click.Path(), help='Custom index directory')
def stats(vault_path, index_dir):
    """Display vault statistics"""
    
    # Use current directory if no vault path provided
    if vault_path is None:
        vault_path = Path.cwd()
    
    try:
        indexer = VaultIndexer(vault_path, index_dir)
        stats = indexer.get_stats()
        
        # Create a table for stats
        table = Table(title="Vault Statistics", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Vault Path", stats['vault_path'])
        table.add_row("Index Path", stats['index_path'])
        table.add_row("Indexed Documents", str(stats['indexed_documents']))
        table.add_row("Total Vault Files", str(stats['vault_files']))
        
        console.print("\n")
        console.print(table)
        console.print("\n")
        
        return 0
    except Exception as e:
        console.print(f"[red]✗ Error getting stats: {e}[/red]")
        return 1


if __name__ == '__main__':
    sys.exit(main())
