"""Gremlin CLI - Exploratory QA Agent."""

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from gremlin import __version__
from gremlin.core.inference import infer_domains
from gremlin.core.patterns import get_domain_keywords, load_patterns, select_patterns
from gremlin.core.prompts import build_prompt, load_system_prompt
from gremlin.llm.claude import call_claude, get_client
from gremlin.output.renderer import render_json, render_markdown, render_rich

app = typer.Typer(
    name="gremlin",
    help="Exploratory QA agent that surfaces risk scenarios",
    add_completion=False,
)
console = Console()

# Paths to data files
PATTERNS_PATH = Path(__file__).parent.parent / "patterns" / "breaking.yaml"
PROMPTS_PATH = Path(__file__).parent.parent / "prompts" / "system.md"


def resolve_context(context: str | None) -> str | None:
    """Resolve context from string, file reference, or stdin.

    Args:
        context: Context string, @filepath, or - for stdin

    Returns:
        Resolved context string or None
    """
    if context is None:
        return None

    # Stdin mode
    if context == "-":
        if sys.stdin.isatty():
            return None  # No piped input
        return sys.stdin.read().strip() or None

    # File reference mode
    if context.startswith("@"):
        filepath = Path(context[1:])
        if not filepath.exists():
            raise FileNotFoundError(f"Context file not found: {filepath}")
        return filepath.read_text().strip() or None

    # Direct string mode
    return context.strip() or None


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
    context: str = typer.Option(
        None,
        "--context",
        "-c",
        help="Additional context: string, @filepath, or - for stdin",
    ),
    depth: str = typer.Option(
        "quick", "--depth", "-d", help="Analysis depth: quick or deep"
    ),
    threshold: int = typer.Option(
        80, "--threshold", "-t", help="Confidence threshold (0-100)"
    ),
    output: str = typer.Option(
        "rich", "--output", "-o", help="Output format: rich, md, json"
    ),
) -> None:
    """Analyze a feature/scope for QA risks.

    Examples:
        gremlin review "checkout flow"
        gremlin review "auth system" --depth deep
        gremlin review "checkout" --context "Using Stripe, Next.js"
        gremlin review "auth" --context @src/auth/login.ts
        git diff | gremlin review "changes" --context -
    """
    # Resolve context input
    try:
        resolved_context = resolve_context(context)
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    # Load patterns and system prompt
    try:
        all_patterns = load_patterns(PATTERNS_PATH)
        system_prompt = load_system_prompt(PROMPTS_PATH)
    except FileNotFoundError as e:
        console.print(f"[red]Error: Required file not found: {e.filename}[/red]")
        raise typer.Exit(1)

    # Infer domains from scope
    domain_keywords = get_domain_keywords(all_patterns)
    matched_domains = infer_domains(scope, domain_keywords)

    # Select relevant patterns
    selected_patterns = select_patterns(scope, all_patterns, matched_domains)

    # Build prompts
    full_system, user_message = build_prompt(
        system_prompt, selected_patterns, scope, depth, threshold, resolved_context
    )

    # Show what we're analyzing
    if output == "rich":
        console.print()
        console.print(f"[bold cyan]🔍 Analyzing:[/bold cyan] {scope}")
        if matched_domains:
            console.print(f"[dim]Detected domains: {', '.join(matched_domains)}[/dim]")
        if resolved_context:
            # Show truncated context preview
            if len(resolved_context) > 80:
                preview = resolved_context[:80] + "..."
            else:
                preview = resolved_context
            preview = preview.replace("\n", " ")
            console.print(f"[dim]Context: {preview}[/dim]")
        console.print()

    # Call Claude
    try:
        client = get_client()
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    with console.status("[bold green]Thinking...[/bold green]", spinner="dots"):
        try:
            response = call_claude(client, full_system, user_message)
        except Exception as e:
            console.print(f"[red]Error calling Claude API: {e}[/red]")
            raise typer.Exit(1)

    # Render output
    if output == "rich":
        render_rich(response, scope, console)
    elif output == "md":
        render_markdown(response)
    elif output == "json":
        render_json(response)
    else:
        console.print(f"[red]Unknown output format: {output}[/red]")
        raise typer.Exit(1)


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
    console.print("\n[dim]Use 'gremlin patterns show <domain>' for details[/dim]")


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
        universal_categories = [
            item.get("category", "").lower().replace(" ", "_") for item in universal
        ]
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
