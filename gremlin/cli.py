"""Gremlin CLI - Pre-Ship Risk Critic."""

import sys
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.table import Table

from gremlin import __version__
from gremlin.core.inference import infer_domains
from gremlin.core.patterns import (
    get_domain_keywords,
    load_all_patterns,
    load_patterns,
    merge_patterns,
    select_patterns,
)
from gremlin.core.prompts import build_prompt, load_system_prompt
from gremlin.core.validator import VALIDATION_SYSTEM_PROMPT, build_validation_prompt
from gremlin.llm.factory import get_provider
from gremlin.output.renderer import render_json, render_markdown, render_rich

app = typer.Typer(
    name="gremlin",
    help="AI critic that surfaces breaking risk scenarios before they reach production",
    add_completion=False,
)
console = Console()

# Paths to data files (inside gremlin package)
PATTERNS_DIR = Path(__file__).parent / "patterns"
PATTERNS_PATH = PATTERNS_DIR / "breaking.yaml"
PROMPTS_PATH = Path(__file__).parent / "prompts" / "system.md"
INCIDENTS_DIR = PATTERNS_DIR / "incidents"


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
    """Gremlin - Pre-Ship Risk Critic.

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
    patterns_file: str = typer.Option(
        None,
        "--patterns",
        "-p",
        help="Custom patterns file (YAML). Merged with built-in patterns.",
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
    validate: bool = typer.Option(
        False, "--validate", "-V", help="Run second pass to filter hallucinations"
    ),
) -> None:
    """Analyze a feature/scope for QA risks.

    Examples:
        gremlin review "checkout flow"
        gremlin review "auth system" --depth deep
        gremlin review "checkout" --context "Using Stripe, Next.js"
        gremlin review "auth" --context @src/auth/login.ts
        git diff | gremlin review "changes" --context -
        gremlin review "image upload" --patterns @my-patterns.yaml
        gremlin review "checkout" --validate  # Filter low-quality risks
    """
    # Resolve context input
    try:
        resolved_context = resolve_context(context)
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    # Load patterns and system prompt (includes incident patterns)
    try:
        all_patterns = load_all_patterns(PATTERNS_DIR)
        system_prompt = load_system_prompt(PROMPTS_PATH)
    except FileNotFoundError as e:
        console.print(f"[red]Error: Required file not found: {e.filename}[/red]")
        raise typer.Exit(1)

    # Load project-level patterns (.gremlin/patterns.yaml)
    project_patterns_path = Path.cwd() / ".gremlin" / "patterns.yaml"
    if project_patterns_path.exists():
        try:
            project_patterns = load_patterns(project_patterns_path)
            all_patterns = merge_patterns(all_patterns, project_patterns)
            if output == "rich":
                console.print("[dim]Loaded project patterns: .gremlin/patterns.yaml[/dim]")
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to load project patterns: {e}[/yellow]")

    # Load custom patterns from --patterns flag
    if patterns_file:
        # Support @filepath syntax like --context
        if patterns_file.startswith("@"):
            patterns_path = Path(patterns_file[1:])
        else:
            patterns_path = Path(patterns_file)

        if not patterns_path.exists():
            console.print(f"[red]Error: Custom patterns file not found: {patterns_path}[/red]")
            raise typer.Exit(1)

        try:
            custom_patterns = load_patterns(patterns_path)
            all_patterns = merge_patterns(all_patterns, custom_patterns)
            if output == "rich":
                console.print(f"[dim]Loaded custom patterns: {patterns_path}[/dim]")
        except Exception as e:
            console.print(f"[red]Error loading custom patterns: {e}[/red]")
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

    # Create LLM provider (reused for analysis + optional validation)
    try:
        provider = get_provider()
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    with console.status("[bold green]Thinking...[/bold green]", spinner="dots"):
        try:
            llm_response = provider.complete(full_system, user_message)
            response = llm_response.text
        except Exception as e:
            console.print(f"[red]Error calling LLM API: {e}[/red]")
            raise typer.Exit(1)

    # Optional validation pass
    if validate:
        if output == "rich":
            console.print("[dim]Running validation pass...[/dim]")
        with console.status("[bold yellow]Validating risks...[/bold yellow]", spinner="dots"):
            try:
                validation_prompt = build_validation_prompt(scope, response)
                val_response = provider.complete(VALIDATION_SYSTEM_PROMPT, validation_prompt)
                response = val_response.text
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Validation failed, using unvalidated results: {e}[/yellow]"
                )

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
        all_patterns = load_all_patterns(PATTERNS_DIR)
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


@app.command()
def learn(
    description: str = typer.Argument(..., help="Description of the incident/pattern"),
    domain: str = typer.Option(
        None, "--domain", "-d", help="Domain for this pattern (e.g., auth, files, payments)"
    ),
    source: str = typer.Option(
        None, "--source", "-s", help="Source project or incident ID"
    ),
) -> None:
    """Learn a new pattern from an incident description.

    Examples:
        gremlin learn "Nav bar showed Login after successful auth" --domain auth --source chitram
        gremlin learn "Landscape image rotated to portrait" --domain files --source chitram
    """
    import re

    # Convert description to "What if" pattern
    desc_lower = description.lower()
    if desc_lower.startswith("what if"):
        pattern = description
    else:
        # Convert statement to question form
        pattern = f"What if {description[0].lower()}{description[1:]}?"
        # Clean up double punctuation
        pattern = re.sub(r"\?\?+", "?", pattern)
        pattern = re.sub(r"\.\?", "?", pattern)

    # Determine target file
    source_name = source or "custom"
    target_file = INCIDENTS_DIR / f"{source_name}.yaml"

    # Ensure incidents directory exists
    INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing patterns or create new structure
    if target_file.exists():
        with open(target_file) as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {
            "# Patterns learned from incidents": None,
            "universal": [],
            "domain_specific": {},
        }
        # Remove the comment key (YAML quirk)
        data.pop("# Patterns learned from incidents", None)
        data = {"universal": [], "domain_specific": {}}

    # Add pattern to appropriate section
    if domain:
        if "domain_specific" not in data:
            data["domain_specific"] = {}
        if domain not in data["domain_specific"]:
            data["domain_specific"][domain] = {
                "keywords": [domain],
                "patterns": [],
            }
        patterns_list = data["domain_specific"][domain].get("patterns", [])
        if pattern not in patterns_list:
            patterns_list.append(pattern)
            data["domain_specific"][domain]["patterns"] = patterns_list
    else:
        # Add to universal patterns under "Incidents" category
        if "universal" not in data:
            data["universal"] = []

        incidents_cat = None
        for cat in data["universal"]:
            if cat.get("category") == "Incidents":
                incidents_cat = cat
                break

        if incidents_cat is None:
            incidents_cat = {"category": "Incidents", "patterns": []}
            data["universal"].append(incidents_cat)

        if pattern not in incidents_cat["patterns"]:
            incidents_cat["patterns"].append(pattern)

    # Write back to file
    with open(target_file, "w") as f:
        # Add header comment
        f.write(f"# Patterns learned from {source_name} incidents\n")
        f.write("# Auto-generated by 'gremlin learn'\n\n")
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    rel_path = target_file.relative_to(PATTERNS_DIR.parent)
    console.print(f"[green]✓[/green] Added pattern to {rel_path}")
    console.print(f"  [dim]{pattern}[/dim]")
    if domain:
        console.print(f"  [dim]Domain: {domain}[/dim]")


# ---------------------------------------------------------------------------
# Pipeline stage commands (v0.3)
# ---------------------------------------------------------------------------
# Each command reads a prerequisite artifact from --run-dir, executes one
# stage via the Gremlin API stage methods, and writes its output artifact.
# Artifacts are stored as JSON in .gremlin/run/ by default.
#
# Usage:
#   gremlin understand "checkout flow"   → .gremlin/run/understanding.json
#   gremlin ideate                        → .gremlin/run/scenarios.json
#   gremlin rollout                       → .gremlin/run/results.json
#   gremlin judge                         → .gremlin/run/scores.json
#   gremlin review "checkout flow"        # full pipeline unchanged
# ---------------------------------------------------------------------------

_DEFAULT_RUN_DIR = Path(".gremlin/run")


def _load_run_artifact(run_dir: Path, filename: str) -> dict:
    """Load a JSON artifact from the run directory, with a clear error."""
    path = run_dir / filename
    if not path.exists():
        console.print(f"[red]Error: {path} not found.[/red]")
        console.print(
            "[dim]Run the preceding stage first, or use a different --run-dir.[/dim]"
        )
        raise typer.Exit(1)
    import json

    return json.loads(path.read_text())


def _write_run_artifact(run_dir: Path, filename: str, data: dict) -> None:
    """Write a JSON artifact to the run directory."""
    import json

    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / filename).write_text(json.dumps(data, indent=2))


@app.command()
def understand(
    scope: str = typer.Argument(..., help="Feature or area to analyze"),
    context: str = typer.Option(
        None, "--context", "-c",
        help="Additional context: string, @filepath, or - for stdin",
    ),
    depth: str = typer.Option("quick", "--depth", "-d", help="Analysis depth: quick or deep"),
    threshold: int = typer.Option(80, "--threshold", "-t", help="Confidence threshold (0-100)"),
    run_dir: Path = typer.Option(
        _DEFAULT_RUN_DIR, "--run-dir", help="Directory for run artifacts"
    ),
) -> None:
    """Stage 1 — Understand: infer domains from scope (no LLM call).

    Writes: <run-dir>/understanding.json

    Examples:
        gremlin understand "checkout flow"
        gremlin understand "auth system" --depth deep --run-dir /tmp/gremlin
    """
    from gremlin.api import Gremlin

    try:
        resolved_context = resolve_context(context)
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    g = Gremlin(threshold=threshold)
    result = g._run_understanding(scope, resolved_context, depth)
    _write_run_artifact(run_dir, "understanding.json", result.to_dict())

    console.print("[green]✓[/green] Understanding complete")
    console.print(f"  Scope:   {result.scope}")
    if result.matched_domains:
        console.print(f"  Domains: {', '.join(result.matched_domains)}")
    console.print(f"  [dim]→ {run_dir}/understanding.json[/dim]")


@app.command()
def ideate(
    run_dir: Path = typer.Option(
        _DEFAULT_RUN_DIR, "--run-dir", help="Directory for run artifacts"
    ),
) -> None:
    """Stage 2 — Ideate: select patterns for the matched domains (no LLM call).

    Reads:  <run-dir>/understanding.json
    Writes: <run-dir>/scenarios.json

    Examples:
        gremlin ideate
        gremlin ideate --run-dir /tmp/gremlin
    """
    from gremlin.api import Gremlin
    from gremlin.core.stages import UnderstandingResult

    d = _load_run_artifact(run_dir, "understanding.json")
    u = UnderstandingResult.from_dict(d)

    g = Gremlin(threshold=u.threshold)
    result = g._run_ideation(u)
    _write_run_artifact(run_dir, "scenarios.json", result.to_dict())

    console.print("[green]✓[/green] Ideation complete")
    console.print(f"  Patterns selected: {result.pattern_count}")
    console.print(f"  [dim]→ {run_dir}/scenarios.json[/dim]")


@app.command()
def rollout(
    run_dir: Path = typer.Option(
        _DEFAULT_RUN_DIR, "--run-dir", help="Directory for run artifacts"
    ),
) -> None:
    """Stage 3 — Rollout: call the LLM with the selected patterns.

    Reads:  <run-dir>/scenarios.json
    Writes: <run-dir>/results.json

    Examples:
        gremlin rollout
        gremlin rollout --run-dir /tmp/gremlin
    """
    from gremlin.api import Gremlin
    from gremlin.core.stages import IdeationResult

    d = _load_run_artifact(run_dir, "scenarios.json")
    i = IdeationResult.from_dict(d)

    try:
        g = Gremlin(threshold=i.understanding.threshold)
        with console.status("[bold green]Thinking...[/bold green]", spinner="dots"):
            result = g._run_rollout(i)
    except Exception as e:
        console.print(f"[red]Error calling LLM API: {e}[/red]")
        raise typer.Exit(1)

    _write_run_artifact(run_dir, "results.json", result.to_dict())
    console.print("[green]✓[/green] Rollout complete")
    console.print(f"  [dim]→ {run_dir}/results.json[/dim]")


@app.command()
def judge(
    run_dir: Path = typer.Option(
        _DEFAULT_RUN_DIR, "--run-dir", help="Directory for run artifacts"
    ),
    validate: bool = typer.Option(
        False, "--validate", "-V",
        help="Run second LLM pass to filter hallucinations and duplicates",
    ),
    output: str = typer.Option(
        "rich", "--output", "-o", help="Output format: rich, md, json"
    ),
) -> None:
    """Stage 4 — Judge: parse risks and optionally validate them.

    Reads:  <run-dir>/results.json
    Writes: <run-dir>/scores.json

    Examples:
        gremlin judge
        gremlin judge --validate
        gremlin judge --output json
    """
    from gremlin.api import Gremlin
    from gremlin.core.stages import RolloutResult

    d = _load_run_artifact(run_dir, "results.json")
    r = RolloutResult.from_dict(d)

    g = Gremlin(threshold=r.ideation.understanding.threshold)
    if validate:
        try:
            g._provider = get_provider()
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
        with console.status("[bold yellow]Validating...[/bold yellow]", spinner="dots"):
            result = g._run_judgment(r, validate=True)
    else:
        result = g._run_judgment(r, validate=False)

    _write_run_artifact(run_dir, "scores.json", result.to_dict())

    risk_count = len(result.risks)
    console.print(f"[green]✓[/green] Judgment complete — {risk_count} risk(s)")
    if result.validated:
        console.print("  [dim]Validation pass applied[/dim]")
    console.print(f"  [dim]→ {run_dir}/scores.json[/dim]")

    if risk_count and output in ("rich", "md"):
        console.print()
        for r_dict in result.risks:
            sev = r_dict.get("severity", "RISK")
            conf = r_dict.get("confidence", 0)
            title = r_dict.get("title") or r_dict.get("scenario", "")[:60]
            console.print(f"  [{sev}] ({conf}%) {title}")


if __name__ == "__main__":
    app()
