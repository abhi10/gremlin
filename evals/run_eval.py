#!/usr/bin/env python3
"""Eval runner for comparing Gremlin vs raw Claude outputs."""

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

import anthropic
import yaml
from rich.console import Console
from rich.table import Table

console = Console()


class EvalMode(Enum):
    """Evaluation mode."""
    CLI = "cli"
    AGENT = "agent"
    COMBINED = "combined"


@dataclass
class EvalMetrics:
    """Metrics extracted from output."""

    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    total_risks: int = 0

    @classmethod
    def from_text(cls, text: str) -> "EvalMetrics":
        """Extract metrics from output text."""
        t = text.lower()
        critical = len(re.findall(r"critical", t))
        high = len(re.findall(r"(?<!-)high(?!-)", t))
        medium = len(re.findall(r"medium", t))
        low = len(re.findall(r"(?<!-)low(?!-)", t))
        what_ifs = len(re.findall(r"what if", t))

        return cls(
            critical=critical,
            high=high,
            medium=medium,
            low=low,
            total_risks=max(what_ifs, critical + high + medium + low),
        )


@dataclass
class EvalResult:
    """Result of evaluating an output against criteria."""

    metrics: EvalMetrics
    keywords_found: list[str] = field(default_factory=list)
    keywords_missing: list[str] = field(default_factory=list)
    categories_found: list[str] = field(default_factory=list)
    categories_missing: list[str] = field(default_factory=list)
    passes: list[str] = field(default_factory=list)
    fails: list[str] = field(default_factory=list)

    @property
    def score(self) -> float:
        total = len(self.passes) + len(self.fails)
        return len(self.passes) / total if total > 0 else 0.0


@dataclass
class ExpectedCriteria:
    """Expected criteria for an eval case."""

    min_critical: int = 0
    min_high: int = 0
    min_total: int = 0
    categories: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "ExpectedCriteria":
        return cls(
            min_critical=d.get("min_critical", 0),
            min_high=d.get("min_high", 0),
            min_total=d.get("min_total", 0),
            categories=d.get("categories", []),
            keywords=d.get("keywords", []),
            domains=d.get("domains", []),
        )


@dataclass
class EvalCase:
    """An evaluation case with input and expected output."""

    name: str
    description: str
    scope: str
    context: str | None
    context_file: str | None
    depth: str
    threshold: int
    expected: ExpectedCriteria
    mode: EvalMode = EvalMode.CLI

    @classmethod
    def from_yaml(cls, path: Path) -> "EvalCase":
        with open(path) as f:
            data = yaml.safe_load(f)

        inp = data.get("input", {})
        mode_str = data.get("mode", "cli").lower()
        mode = (
            EvalMode[mode_str.upper()]
            if mode_str.upper() in EvalMode.__members__
            else EvalMode.CLI
        )

        return cls(
            name=data.get("name", path.stem),
            description=data.get("description", ""),
            scope=inp.get("scope", ""),
            context=inp.get("context"),
            context_file=inp.get("context_file"),
            depth=inp.get("depth", "quick"),
            threshold=inp.get("threshold", 80),
            expected=ExpectedCriteria.from_dict(data.get("expected", {})),
            mode=mode,
        )

    def resolve_context(self) -> str | None:
        """Resolve context from file or inline."""
        if self.context_file:
            path = Path(self.context_file)
            return path.read_text() if path.exists() else None
        return self.context


def evaluate(output: str, expected: ExpectedCriteria) -> EvalResult:
    """Evaluate output against expected criteria."""
    metrics = EvalMetrics.from_text(output)
    output_lower = output.lower()

    # Check keywords
    kw_found = [k for k in expected.keywords if k.lower() in output_lower]
    kw_missing = [k for k in expected.keywords if k.lower() not in output_lower]

    # Check categories
    cat_found = [c for c in expected.categories if c.lower() in output_lower]
    cat_missing = [c for c in expected.categories if c.lower() not in output_lower]

    # Build pass/fail list
    passes, fails = [], []

    checks = [
        (metrics.critical >= expected.min_critical,
         f"Critical: {metrics.critical} >= {expected.min_critical}"),
        (metrics.high >= expected.min_high,
         f"High: {metrics.high} >= {expected.min_high}"),
        (metrics.total_risks >= expected.min_total,
         f"Total: {metrics.total_risks} >= {expected.min_total}"),
        (len(kw_found) >= len(expected.keywords) / 2 if expected.keywords else True,
         f"Keywords: {len(kw_found)}/{len(expected.keywords)}"),
        (len(cat_found) >= len(expected.categories) / 2 if expected.categories else True,
         f"Categories: {len(cat_found)}/{len(expected.categories)}"),
    ]

    for passed, msg in checks:
        (passes if passed else fails).append(msg)

    return EvalResult(
        metrics=metrics,
        keywords_found=kw_found,
        keywords_missing=kw_missing,
        categories_found=cat_found,
        categories_missing=cat_missing,
        passes=passes,
        fails=fails,
    )


def run_gremlin(case: EvalCase) -> str:
    """Run Gremlin CLI and return output."""
    cmd = ["gremlin", "review", case.scope, "--output", "json",
           "--depth", case.depth, "--threshold", str(case.threshold)]

    if case.context_file:
        cmd.extend(["--context", f"@{case.context_file}"])
    elif case.context:
        cmd.extend(["--context", case.context])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return result.stdout
    except (subprocess.TimeoutExpired, Exception) as e:
        return f"Error: {e}"


def run_raw_claude(case: EvalCase) -> str:
    """Run raw Claude without Gremlin patterns."""
    context = case.resolve_context() or ""

    prompt = f"""Analyze this scope for risks: {case.scope}

{f"Context: {context}" if context else ""}

For each risk scenario:
1. State the "what if?" question
2. Explain the potential impact
3. Rate severity (critical/high/medium/low)
4. Provide your confidence percentage

Focus on non-obvious risks. Skip generic advice."""

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except Exception as e:
        return f"Error: {e}"


def run_agent_eval(case: EvalCase) -> str:
    """Run agent-mode evaluation using code-review.yaml patterns.

    This simulates the Gremlin agent's analysis by loading code-review patterns
    and applying them with Claude, matching the agent's behavior.
    """
    # Reuse existing pattern loading infrastructure
    try:
        # Add parent directory to path to import gremlin modules
        import sys
        gremlin_path = Path(__file__).parent.parent
        if str(gremlin_path) not in sys.path:
            sys.path.insert(0, str(gremlin_path))

        from gremlin.core.patterns import load_patterns

        # Load agent patterns from code-review.yaml
        patterns_path = gremlin_path / "patterns" / "code-review.yaml"
        patterns = load_patterns(patterns_path)
    except (ImportError, FileNotFoundError) as e:
        return f"Error loading patterns: {e}"

    context = case.resolve_context() or ""

    # Build agent prompt with code-review patterns
    patterns_yaml = yaml.dump(patterns, default_flow_style=False)

    system_prompt = f"""You are Gremlin, a risk-focused code reviewer.

Surface non-obvious risks from real incidents, not theoretical vulnerabilities.

## Code-Review Patterns

{patterns_yaml}

## Response Approach
1. Identify domains touched by code
2. Match patterns from catalog above
3. Score confidence (0-100) and severity (1-5)
4. Filter below threshold ({case.threshold})
5. Report with "What if?" framing
"""

    # Build context section (avoid backslash in f-string for Python 3.10)
    context_section = f"Context/Code:\n{context}" if context else ""

    user_prompt = f"""Analyze this code/scope for risks: {case.scope}

{context_section}

Depth: {case.depth}
Confidence threshold: Only include scenarios where you're >{case.threshold}% confident.

Apply the code-review patterns above. For each risk scenario:
1. State the "what if?" question
2. Explain the potential impact
3. Rate severity (critical/high/medium/low)
4. Provide your confidence percentage

Focus on code-level implementation risks."""

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text
    except Exception as e:
        return f"Error: {e}"


def run_combined_eval(case: EvalCase) -> tuple[str, str]:
    """Run combined CLI + Agent evaluation.

    Returns tuple of (cli_output, agent_output) which can be merged for analysis.
    """
    cli_output = run_gremlin(case)
    agent_output = run_agent_eval(case)
    return cli_output, agent_output


def display_results(case: EvalCase, gremlin: EvalResult, claude: EvalResult) -> None:
    """Display comparison table."""
    table = Table(title=f"Results: {case.name}")
    table.add_column("Metric", style="cyan")
    table.add_column("Gremlin", style="green")
    table.add_column("Raw Claude", style="yellow")

    gm, cm = gremlin.metrics, claude.metrics
    rows = [
        ("Critical", gm.critical, cm.critical),
        ("High", gm.high, cm.high),
        ("Medium", gm.medium, cm.medium),
        ("Low", gm.low, cm.low),
        ("Total Risks", gm.total_risks, cm.total_risks),
        ("Keywords", f"{len(gremlin.keywords_found)}/{len(case.expected.keywords)}",
         f"{len(claude.keywords_found)}/{len(case.expected.keywords)}"),
        ("Categories", f"{len(gremlin.categories_found)}/{len(case.expected.categories)}",
         f"{len(claude.categories_found)}/{len(case.expected.categories)}"),
        ("Score", f"{gremlin.score:.0%}", f"{claude.score:.0%}"),
    ]

    for row in rows:
        table.add_row(row[0], str(row[1]), str(row[2]))

    console.print(table)

    if gremlin.fails:
        console.print("\n[red]Gremlin Fails:[/red]")
        for f in gremlin.fails:
            console.print(f"  - {f}")

    if claude.fails:
        console.print("\n[red]Claude Fails:[/red]")
        for f in claude.fails:
            console.print(f"  - {f}")


def determine_winner(gremlin: EvalResult, claude: EvalResult) -> str:
    """Determine winner based on scores."""
    if gremlin.score > claude.score:
        return "gremlin"
    elif claude.score > gremlin.score:
        return "claude"
    return "tie"


def run_eval(case_path: Path, save: bool = True) -> dict:
    """Run a single eval case with mode support."""
    case = EvalCase.from_yaml(case_path)

    console.print(f"\n[bold cyan]Running eval:[/bold cyan] {case.name}")
    console.print(f"[dim]{case.description}[/dim]")
    console.print(f"[dim]Mode: {case.mode.value}[/dim]\n")

    if case.mode == EvalMode.AGENT:
        # Agent-only mode
        console.print("[yellow]Running Agent (code-review patterns)...[/yellow]")
        agent_output = run_agent_eval(case)

        console.print("[yellow]Running raw Claude (baseline)...[/yellow]")
        claude_output = run_raw_claude(case)

        agent_eval = evaluate(agent_output, case.expected)
        claude_eval = evaluate(claude_output, case.expected)

        display_results(case, agent_eval, claude_eval)

        result = {
            "case": case.name,
            "mode": case.mode.value,
            "timestamp": datetime.now().isoformat(),
            "agent": {"output": agent_output, "score": agent_eval.score},
            "claude": {"output": claude_output, "score": claude_eval.score},
            "winner": determine_winner(agent_eval, claude_eval),
        }

    elif case.mode == EvalMode.COMBINED:
        # Combined CLI + Agent mode
        console.print("[yellow]Running Gremlin CLI (feature patterns)...[/yellow]")
        cli_output = run_gremlin(case)

        console.print("[yellow]Running Agent (code patterns)...[/yellow]")
        agent_output = run_agent_eval(case)

        cli_eval = evaluate(cli_output, case.expected)
        agent_eval = evaluate(agent_output, case.expected)

        # Combine outputs for evaluation
        combined_output = (
            f"=== CLI Analysis ===\n{cli_output}\n\n"
            f"=== Agent Analysis ===\n{agent_output}"
        )
        combined_eval = evaluate(combined_output, case.expected)

        # Display 3-way comparison
        table = Table(title=f"Results: {case.name}")
        table.add_column("Metric", style="cyan")
        table.add_column("CLI", style="green")
        table.add_column("Agent", style="blue")
        table.add_column("Combined", style="magenta")

        cm, am, compm = cli_eval.metrics, agent_eval.metrics, combined_eval.metrics
        rows = [
            ("Critical", cm.critical, am.critical, compm.critical),
            ("High", cm.high, am.high, compm.high),
            ("Total Risks", cm.total_risks, am.total_risks, compm.total_risks),
            (
                "Score",
                f"{cli_eval.score:.0%}",
                f"{agent_eval.score:.0%}",
                f"{combined_eval.score:.0%}",
            ),
        ]

        for row in rows:
            table.add_row(row[0], str(row[1]), str(row[2]), str(row[3]))

        console.print(table)

        result = {
            "case": case.name,
            "mode": case.mode.value,
            "timestamp": datetime.now().isoformat(),
            "cli": {"output": cli_output, "score": cli_eval.score},
            "agent": {"output": agent_output, "score": agent_eval.score},
            "combined": {"output": combined_output, "score": combined_eval.score},
        }

    else:
        # CLI mode (default/original behavior)
        console.print("[yellow]Running Gremlin CLI...[/yellow]")
        gremlin_output = run_gremlin(case)

        console.print("[yellow]Running raw Claude...[/yellow]")
        claude_output = run_raw_claude(case)

        gremlin_eval = evaluate(gremlin_output, case.expected)
        claude_eval = evaluate(claude_output, case.expected)

        display_results(case, gremlin_eval, claude_eval)

        result = {
            "case": case.name,
            "mode": case.mode.value,
            "timestamp": datetime.now().isoformat(),
            "gremlin": {"output": gremlin_output, "score": gremlin_eval.score},
            "claude": {"output": claude_output, "score": claude_eval.score},
            "winner": determine_winner(gremlin_eval, claude_eval),
        }

    if save:
        results_dir = Path(__file__).parent / "results"
        results_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        result_file = results_dir / f"{case.name}-{ts}.json"
        result_file.write_text(json.dumps(result, indent=2, default=str))
        console.print(f"\n[dim]Saved: {result_file}[/dim]")

    return result


def run_all(cases_dir: Path | None = None) -> list[dict]:
    """Run all eval cases."""
    cases_dir = cases_dir or Path(__file__).parent / "cases"
    case_files = sorted(cases_dir.glob("*.yaml"))

    console.print(f"[bold]Found {len(case_files)} eval cases[/bold]")

    results = []
    for case_file in case_files:
        try:
            results.append(run_eval(case_file))
        except Exception as e:
            console.print(f"[red]Error running {case_file.name}: {e}[/red]")

    # Summary
    console.print("\n" + "=" * 50)
    console.print("[bold]Summary[/bold]")
    wins = {"gremlin": 0, "claude": 0, "tie": 0}
    for r in results:
        wins[r["winner"]] += 1

    console.print(f"  Gremlin wins: {wins['gremlin']}")
    console.print(f"  Claude wins: {wins['claude']}")
    console.print(f"  Ties: {wins['tie']}")

    return results


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run Gremlin evals")
    parser.add_argument("case", nargs="?", help="Case name or path")
    parser.add_argument("--all", action="store_true", help="Run all cases")
    parser.add_argument("--no-save", action="store_true", help="Don't save results")

    args = parser.parse_args()

    if args.case:
        path = Path(args.case)
        if not path.exists():
            path = Path(__file__).parent / "cases" / f"{args.case}.yaml"
        if not path.exists():
            console.print(f"[red]Case not found: {args.case}[/red]")
            sys.exit(1)
        run_eval(path, save=not args.no_save)
    elif args.all:
        run_all()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
