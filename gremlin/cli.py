"""Gremlin CLI - Exploratory QA Agent."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from gremlin import __version__
from gremlin.core.patterns import load_patterns, get_domain_keywords

app = typer.Typer(
    name="gremlin",
    help="Exploratory QA agent that surfaces risk scenarios",
    add_completion=False,
)
console = Console()

# Path to patterns file
PATTERNS_PATH = Path(__file__).parent.parent / "patterns" / "breaking.yaml"


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"gremlin version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """Gremlin - Exploratory QA Agent.

    Surfaces risk scenarios using curated patterns + LLM reasoning.
    """
    pass


@app.command()
def review(
    scope: str = typer.Argument(..., help="Feature or area to analyze"),
    depth: str = typer.Option("quick", "--depth", "-d", help="Analysis depth: quick or deep"),
    threshold: int = typer.Option(80, "--threshold", "-t", help="Confidence threshold (0-100)"),
    output: str = typer.Option("rich", "--output", "-o", help="Output format: rich, md, json"),
) -> None:
    """Analyze a feature/scope for QA risks.

    Examples:
        gremlin review "checkout flow"
        gremlin review "auth system" --depth deep
        gremlin review "file upload" --threshold 60 --output md
    """
    # TODO: Implement in Phase 3
    console.print(f"[bold]Reviewing:[/bold] {scope}")
    console.print(f"[dim]Depth: {depth}, Threshold: {threshold}%, Output: {output}[/dim]")
    console.print("\n[yellow]Implementation coming in Phase 3...[/yellow]")


@app.command()
def patterns(
    action: str = typer.Argument("list", help="Action: list or show"),
    domain: str = typer.Argument(None, help="Domain to show patterns for"),
) -> None:
    """List or show available QA patterns.

    Examples:
        gremlin patterns list
        gremlin patterns show payments
        gremlin patterns show auth
    """
    try:
        all_patterns = load_patterns(PATTERNS_PATH)
    except FileNotFoundError:
        console.print("[red]Error: patterns/breaking.yaml not found[/red]")
        raise typer.Exit(1)

    if action == "list":
        _list_patterns(all_patterns)
    elif action == "show" and domain:
        _show_domain_patterns(all_patterns, domain)
    else:
        console.print("[red]Usage: gremlin patterns list OR gremlin patterns show <domain>[/red]")
        raise typer.Exit(1)


def _list_patterns(all_patterns: dict) -> None:
    """List all available pattern categories."""
    # Universal categories
    console.print("\n[bold cyan]Universal Patterns[/bold cyan]")
    console.print("[dim]Applied to every analysis[/dim]\n")

    universal = all_patterns.get("universal", [])
    table = Table(show_header=True, header_style="bold")
    table.add_column("Category", style="cyan")
    table.add_column("Patterns", justify="right")

    for item in universal:
        category = item.get("category", "Unknown")
        patterns_list = item.get("patterns", [])
        table.add_row(category, str(len(patterns_list)))

    console.print(table)

    # Domain-specific
    console.print("\n[bold green]Domain-Specific Patterns[/bold green]")
    console.print("[dim]Applied when domain is detected in scope[/dim]\n")

    domain_keywords = get_domain_keywords(all_patterns)
    domain_specific = all_patterns.get("domain_specific", {})

    table = Table(show_header=True, header_style="bold")
    table.add_column("Domain", style="green")
    table.add_column("Patterns", justify="right")
    table.add_column("Keywords", style="dim")

    for domain, config in domain_specific.items():
        pattern_count = len(config.get("patterns", []))
        keywords = ", ".join(domain_keywords.get(domain, [])[:4])
        if len(domain_keywords.get(domain, [])) > 4:
            keywords += "..."
        table.add_row(domain, str(pattern_count), keywords)

    console.print(table)
    console.print(f"\n[dim]Use 'gremlin patterns show <domain>' for details[/dim]")


def _show_domain_patterns(all_patterns: dict, domain: str) -> None:
    """Show patterns for a specific domain."""
    domain_specific = all_patterns.get("domain_specific", {})
    universal = all_patterns.get("universal", [])

    # Check if it's a universal category (case-insensitive match)
    for item in universal:
        category = item.get("category", "")
        # Match by category name (case-insensitive, handle spaces/underscores)
        normalized = category.lower().replace(" ", "_").replace("&", "and")
        if domain.lower() == normalized or domain.lower() == category.lower():
            console.print(f"\n[bold cyan]Universal: {category}[/bold cyan]\n")
            for i, pattern in enumerate(item.get("patterns", []), 1):
                console.print(f"  {i}. {pattern}")
            return

    # Check domain-specific
    if domain not in domain_specific:
        universal_categories = [item.get("category", "").lower().replace(" ", "_") for item in universal]
        available = list(domain_specific.keys()) + universal_categories
        console.print(f"[red]Unknown domain: {domain}[/red]")
        console.print(f"[dim]Available: {', '.join(available)}[/dim]")
        raise typer.Exit(1)

    config = domain_specific[domain]
    keywords = config.get("keywords", [])
    patterns_list = config.get("patterns", [])

    console.print(f"\n[bold green]{domain.upper()}[/bold green]")
    console.print(f"[dim]Keywords: {', '.join(keywords)}[/dim]\n")

    for i, pattern in enumerate(patterns_list, 1):
        console.print(f"  {i}. {pattern}")


if __name__ == "__main__":
    app()
