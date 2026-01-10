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
class EvalConfig:
    """Configuration for eval runs."""

    trials: int = 3  # Number of trials per case
    pass_threshold: float = 0.7  # Score threshold for pass/fail


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

    # Minimum thresholds (for positive cases)
    min_critical: int = 0
    min_high: int = 0
    min_total: int = 0
    # Maximum thresholds (for negative cases - None means no limit)
    max_critical: int | None = None
    max_high: int | None = None
    max_total: int | None = None
    # Content checks
    categories: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "ExpectedCriteria":
        return cls(
            min_critical=d.get("min_critical", 0),
            min_high=d.get("min_high", 0),
            min_total=d.get("min_total", 0),
            max_critical=d.get("max_critical"),
            max_high=d.get("max_high"),
            max_total=d.get("max_total"),
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

    # Minimum threshold checks (positive cases)
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

    # Maximum threshold checks (negative cases - prevent over-triggering)
    if expected.max_critical is not None:
        checks.append(
            (metrics.critical <= expected.max_critical,
             f"Max Critical: {metrics.critical} <= {expected.max_critical}")
        )
    if expected.max_high is not None:
        checks.append(
            (metrics.high <= expected.max_high,
             f"Max High: {metrics.high} <= {expected.max_high}")
        )
    if expected.max_total is not None:
        checks.append(
            (metrics.total_risks <= expected.max_total,
             f"Max Total: {metrics.total_risks} <= {expected.max_total}")
        )

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


def calculate_trial_metrics(
    scores: list[float], threshold: float = 0.7
) -> dict[str, float]:
    """Calculate pass@k and pass^k metrics from trial scores.

    Args:
        scores: List of scores from each trial
        threshold: Score threshold for pass/fail (default 0.7)

    Returns:
        Dict with pass_at_1, pass_at_k, pass_pow_k, and consistency metrics
    """
    if not scores:
        return {
            "pass_at_1": 0.0,
            "pass_at_k": 0.0,
            "pass_pow_k": 0.0,
            "consistency": 0.0,
            "mean_score": 0.0,
            "trials": 0,
        }

    passes = [s >= threshold for s in scores]
    k = len(scores)

    return {
        "pass_at_1": 1.0 if passes[0] else 0.0,
        "pass_at_k": 1.0 if any(passes) else 0.0,
        "pass_pow_k": 1.0 if all(passes) else 0.0,
        "consistency": sum(passes) / k,
        "mean_score": sum(scores) / k,
        "trials": k,
    }


def display_trial_metrics(metrics: dict[str, float], label: str = "Gremlin") -> None:
    """Display trial metrics in a formatted table."""
    table = Table(title=f"{label} Trial Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    rows = [
        ("Trials", str(metrics["trials"])),
        ("Mean Score", f"{metrics['mean_score']:.0%}"),
        ("pass@1", f"{metrics['pass_at_1']:.0%}"),
        ("pass@k (any pass)", f"{metrics['pass_at_k']:.0%}"),
        ("pass^k (all pass)", f"{metrics['pass_pow_k']:.0%}"),
        ("Consistency", f"{metrics['consistency']:.0%}"),
    ]

    for metric, value in rows:
        table.add_row(metric, value)

    console.print(table)


def run_eval(
    case_path: Path, config: EvalConfig | None = None, save: bool = True
) -> dict:
    """Run a single eval case with mode support and multiple trials.

    Args:
        case_path: Path to the eval case YAML file
        config: Eval configuration (trials, threshold). Defaults to 3 trials.
        save: Whether to save results to disk

    Returns:
        Dict containing all trial results and aggregated metrics
    """
    config = config or EvalConfig()
    case = EvalCase.from_yaml(case_path)

    console.print(f"\n[bold cyan]Running eval:[/bold cyan] {case.name}")
    console.print(f"[dim]{case.description}[/dim]")
    console.print(f"[dim]Mode: {case.mode.value} | Trials: {config.trials}[/dim]\n")

    # Run multiple trials
    all_trials: list[dict] = []
    gremlin_scores: list[float] = []
    claude_scores: list[float] = []

    for trial_num in range(config.trials):
        console.print(f"[bold]Trial {trial_num + 1}/{config.trials}[/bold]")

        if case.mode == EvalMode.AGENT:
            # Agent-only mode
            console.print("[yellow]Running Agent (code-review patterns)...[/yellow]")
            agent_output = run_agent_eval(case)

            console.print("[yellow]Running raw Claude (baseline)...[/yellow]")
            claude_output = run_raw_claude(case)

            agent_eval = evaluate(agent_output, case.expected)
            claude_eval = evaluate(claude_output, case.expected)

            gremlin_scores.append(agent_eval.score)
            claude_scores.append(claude_eval.score)

            trial_result = {
                "trial": trial_num + 1,
                "agent": {"output": agent_output, "score": agent_eval.score},
                "claude": {"output": claude_output, "score": claude_eval.score},
                "winner": determine_winner(agent_eval, claude_eval),
            }

            # Display results for last trial only (avoid spam)
            if trial_num == config.trials - 1:
                display_results(case, agent_eval, claude_eval)

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

            gremlin_scores.append(combined_eval.score)
            claude_scores.append(cli_eval.score)  # Use CLI as baseline for combined

            trial_result = {
                "trial": trial_num + 1,
                "cli": {"output": cli_output, "score": cli_eval.score},
                "agent": {"output": agent_output, "score": agent_eval.score},
                "combined": {"output": combined_output, "score": combined_eval.score},
            }

            # Display results for last trial only
            if trial_num == config.trials - 1:
                table = Table(title=f"Results: {case.name}")
                table.add_column("Metric", style="cyan")
                table.add_column("CLI", style="green")
                table.add_column("Agent", style="blue")
                table.add_column("Combined", style="magenta")

                cm = cli_eval.metrics
                am = agent_eval.metrics
                compm = combined_eval.metrics
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

        else:
            # CLI mode (default/original behavior)
            console.print("[yellow]Running Gremlin CLI...[/yellow]")
            gremlin_output = run_gremlin(case)

            console.print("[yellow]Running raw Claude...[/yellow]")
            claude_output = run_raw_claude(case)

            gremlin_eval = evaluate(gremlin_output, case.expected)
            claude_eval = evaluate(claude_output, case.expected)

            gremlin_scores.append(gremlin_eval.score)
            claude_scores.append(claude_eval.score)

            trial_result = {
                "trial": trial_num + 1,
                "gremlin": {"output": gremlin_output, "score": gremlin_eval.score},
                "claude": {"output": claude_output, "score": claude_eval.score},
                "winner": determine_winner(gremlin_eval, claude_eval),
            }

            # Display results for last trial only
            if trial_num == config.trials - 1:
                display_results(case, gremlin_eval, claude_eval)

        all_trials.append(trial_result)

    # Calculate and display trial metrics
    gremlin_metrics = calculate_trial_metrics(gremlin_scores, config.pass_threshold)
    claude_metrics = calculate_trial_metrics(claude_scores, config.pass_threshold)

    console.print("\n[bold]Trial Summary[/bold]")
    display_trial_metrics(gremlin_metrics, "Gremlin")
    display_trial_metrics(claude_metrics, "Claude (baseline)")

    # Determine overall winner based on consistency
    if gremlin_metrics["pass_pow_k"] > claude_metrics["pass_pow_k"]:
        overall_winner = "gremlin"
    elif claude_metrics["pass_pow_k"] > gremlin_metrics["pass_pow_k"]:
        overall_winner = "claude"
    elif gremlin_metrics["mean_score"] > claude_metrics["mean_score"]:
        overall_winner = "gremlin"
    elif claude_metrics["mean_score"] > gremlin_metrics["mean_score"]:
        overall_winner = "claude"
    else:
        overall_winner = "tie"

    console.print(f"\n[bold]Overall Winner:[/bold] {overall_winner}")

    result = {
        "case": case.name,
        "mode": case.mode.value,
        "timestamp": datetime.now().isoformat(),
        "config": {"trials": config.trials, "pass_threshold": config.pass_threshold},
        "trials": all_trials,
        "gremlin_metrics": gremlin_metrics,
        "claude_metrics": claude_metrics,
        "overall_winner": overall_winner,
    }

    if save:
        results_dir = Path(__file__).parent / "results"
        results_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        result_file = results_dir / f"{case.name}-{ts}.json"
        result_file.write_text(json.dumps(result, indent=2, default=str))
        console.print(f"\n[dim]Saved: {result_file}[/dim]")

    return result


def run_all(
    cases_dir: Path | None = None, config: EvalConfig | None = None
) -> list[dict]:
    """Run all eval cases with multiple trials.

    Args:
        cases_dir: Directory containing eval case YAML files
        config: Eval configuration (trials, threshold)

    Returns:
        List of result dicts for each case
    """
    config = config or EvalConfig()
    cases_dir = cases_dir or Path(__file__).parent / "cases"
    case_files = sorted(cases_dir.glob("*.yaml"))

    console.print(f"[bold]Found {len(case_files)} eval cases[/bold]")
    threshold_pct = f"{config.pass_threshold:.0%}"
    console.print(f"[dim]Config: {config.trials} trials, {threshold_pct} threshold[/dim]\n")

    results = []
    for case_file in case_files:
        try:
            results.append(run_eval(case_file, config=config))
        except Exception as e:
            console.print(f"[red]Error running {case_file.name}: {e}[/red]")

    # Summary
    console.print("\n" + "=" * 50)
    console.print("[bold]Overall Summary[/bold]")

    wins = {"gremlin": 0, "claude": 0, "tie": 0}
    total_consistency = {"gremlin": 0.0, "claude": 0.0}

    for r in results:
        winner = r.get("overall_winner", r.get("winner", "tie"))
        wins[winner] += 1
        total_consistency["gremlin"] += r.get("gremlin_metrics", {}).get("consistency", 0)
        total_consistency["claude"] += r.get("claude_metrics", {}).get("consistency", 0)

    n = len(results) if results else 1
    console.print(f"  Gremlin wins: {wins['gremlin']}")
    console.print(f"  Claude wins: {wins['claude']}")
    console.print(f"  Ties: {wins['tie']}")
    console.print(f"  Avg Gremlin consistency: {total_consistency['gremlin']/n:.0%}")
    console.print(f"  Avg Claude consistency: {total_consistency['claude']/n:.0%}")

    return results


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run Gremlin evals")
    parser.add_argument("case", nargs="?", help="Case name or path")
    parser.add_argument("--all", action="store_true", help="Run all cases")
    parser.add_argument("--no-save", action="store_true", help="Don't save results")
    parser.add_argument(
        "--trials", type=int, default=3, help="Number of trials per case (default: 3)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="Pass/fail score threshold (default: 0.7)",
    )

    args = parser.parse_args()

    config = EvalConfig(trials=args.trials, pass_threshold=args.threshold)

    if args.case:
        path = Path(args.case)
        if not path.exists():
            path = Path(__file__).parent / "cases" / f"{args.case}.yaml"
        if not path.exists():
            console.print(f"[red]Case not found: {args.case}[/red]")
            sys.exit(1)
        run_eval(path, config=config, save=not args.no_save)
    elif args.all:
        run_all(config=config)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
