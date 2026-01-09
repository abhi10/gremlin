"""Gremlin CLI - Exploratory QA Agent."""

import typer
from rich.console import Console

from gremlin import __version__

app = typer.Typer(
    name="gremlin",
    help="Exploratory QA agent that surfaces risk scenarios",
    add_completion=False,
)
console = Console()


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
    # TODO: Implement in Phase 2
    if action == "list":
        console.print("[bold]Available Pattern Categories[/bold]\n")
        console.print("[yellow]Implementation coming in Phase 2...[/yellow]")
    elif action == "show" and domain:
        console.print(f"[bold]Patterns for domain: {domain}[/bold]\n")
        console.print("[yellow]Implementation coming in Phase 2...[/yellow]")
    else:
        console.print("[red]Usage: gremlin patterns list OR gremlin patterns show <domain>[/red]")


if __name__ == "__main__":
    app()
