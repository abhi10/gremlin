#!/usr/bin/env python3
"""Eval runner for comparing Gremlin vs raw Claude outputs."""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import anthropic
import yaml
from rich.console import Console
from rich.table import Table

console = Console()


def load_case(case_path: Path) -> dict:
    """Load eval case from YAML file."""
    with open(case_path) as f:
        return yaml.safe_load(f)


def run_gremlin(case: dict) -> dict:
    """Run Gremlin CLI and capture output."""
    input_cfg = case["input"]
    scope = input_cfg["scope"]

    cmd = ["gremlin", "review", scope, "--output", "json"]

    # Add context
    if "context_file" in input_cfg:
        cmd.extend(["--context", f"@{input_cfg['context_file']}"])
    elif "context" in input_cfg:
        cmd.extend(["--context", input_cfg["context"]])

    if "depth" in input_cfg:
        cmd.extend(["--depth", input_cfg["depth"]])
    if "threshold" in input_cfg:
        cmd.extend(["--threshold", str(input_cfg["threshold"])])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = result.stdout

        # Try to parse JSON from output
        try:
            return {"raw": output, "parsed": json.loads(output), "error": None}
        except json.JSONDecodeError:
            # Fallback: extract risk info from raw output
            return {"raw": output, "parsed": None, "error": None}
    except subprocess.TimeoutExpired:
        return {"raw": "", "parsed": None, "error": "timeout"}
    except Exception as e:
        return {"raw": "", "parsed": None, "error": str(e)}


def run_raw_claude(case: dict) -> dict:
    """Run raw Claude without Gremlin patterns."""
    input_cfg = case["input"]
    scope = input_cfg["scope"]

    # Build context
    context = ""
    if "context_file" in input_cfg:
        context_path = Path(input_cfg["context_file"])
        if context_path.exists():
            context = context_path.read_text()
    elif "context" in input_cfg:
        context = input_cfg["context"]

    prompt = f"""Analyze this scope for risks: {scope}

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
        output = response.content[0].text
        return {"raw": output, "parsed": None, "error": None}
    except Exception as e:
        return {"raw": "", "parsed": None, "error": str(e)}


def extract_metrics(output: str) -> dict:
    """Extract metrics from output text."""
    output_lower = output.lower()

    # Count severities
    critical = len(re.findall(r"critical", output_lower))
    high = len(re.findall(r"(?<!-)high(?!-)", output_lower))
    medium = len(re.findall(r"medium", output_lower))
    low = len(re.findall(r"(?<!-)low(?!-)", output_lower))

    # Count "what if" questions as proxy for total risks
    what_ifs = len(re.findall(r"what if", output_lower))

    return {
        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low,
        "total_risks": max(what_ifs, critical + high + medium + low),
    }


def check_keywords(output: str, keywords: list[str]) -> dict:
    """Check which keywords appear in output."""
    output_lower = output.lower()
    found = []
    missing = []

    for kw in keywords:
        if kw.lower() in output_lower:
            found.append(kw)
        else:
            missing.append(kw)

    return {"found": found, "missing": missing}


def check_categories(output: str, categories: list[str]) -> dict:
    """Check which risk categories are covered."""
    output_lower = output.lower()
    found = []
    missing = []

    for cat in categories:
        if cat.lower() in output_lower:
            found.append(cat)
        else:
            missing.append(cat)

    return {"found": found, "missing": missing}


def evaluate_output(output: str, expected: dict) -> dict:
    """Evaluate output against expected criteria."""
    metrics = extract_metrics(output)
    keywords = check_keywords(output, expected.get("keywords", []))
    categories = check_categories(output, expected.get("categories", []))

    # Calculate pass/fail
    passes = []
    fails = []

    if metrics["critical"] >= expected.get("min_critical", 0):
        passes.append(f"Critical risks: {metrics['critical']} >= {expected.get('min_critical', 0)}")
    else:
        fails.append(f"Critical risks: {metrics['critical']} < {expected.get('min_critical', 0)}")

    if metrics["high"] >= expected.get("min_high", 0):
        passes.append(f"High risks: {metrics['high']} >= {expected.get('min_high', 0)}")
    else:
        fails.append(f"High risks: {metrics['high']} < {expected.get('min_high', 0)}")

    if metrics["total_risks"] >= expected.get("min_total", 0):
        passes.append(f"Total risks: {metrics['total_risks']} >= {expected.get('min_total', 0)}")
    else:
        fails.append(f"Total risks: {metrics['total_risks']} < {expected.get('min_total', 0)}")

    keyword_coverage = len(keywords["found"]) / len(expected.get("keywords", []) or [1])
    if keyword_coverage >= 0.5:
        passes.append(f"Keywords: {len(keywords['found'])}/{len(expected.get('keywords', []))}")
    else:
        fails.append(f"Keywords: {len(keywords['found'])}/{len(expected.get('keywords', []))}")

    exp_categories = expected.get("categories", [])
    category_coverage = len(categories["found"]) / len(exp_categories or [1])
    cat_msg = f"Categories: {len(categories['found'])}/{len(exp_categories)}"
    if category_coverage >= 0.5:
        passes.append(cat_msg)
    else:
        fails.append(cat_msg)

    return {
        "metrics": metrics,
        "keywords": keywords,
        "categories": categories,
        "passes": passes,
        "fails": fails,
        "score": len(passes) / (len(passes) + len(fails)) if (passes or fails) else 0,
    }


def run_single_eval(case_path: Path, save_results: bool = True) -> dict:
    """Run a single eval case."""
    case = load_case(case_path)
    console.print(f"\n[bold cyan]Running eval:[/bold cyan] {case['name']}")
    console.print(f"[dim]{case['description']}[/dim]\n")

    # Run Gremlin
    console.print("[yellow]Running Gremlin...[/yellow]")
    gremlin_result = run_gremlin(case)

    # Run raw Claude
    console.print("[yellow]Running raw Claude...[/yellow]")
    claude_result = run_raw_claude(case)

    # Evaluate both
    expected = case.get("expected", {})
    gremlin_eval = evaluate_output(gremlin_result["raw"], expected)
    claude_eval = evaluate_output(claude_result["raw"], expected)

    # Display comparison
    table = Table(title=f"Results: {case['name']}")
    table.add_column("Metric", style="cyan")
    table.add_column("Gremlin", style="green")
    table.add_column("Raw Claude", style="yellow")

    gm = gremlin_eval["metrics"]
    cm = claude_eval["metrics"]
    table.add_row("Critical", str(gm["critical"]), str(cm["critical"]))
    table.add_row("High", str(gm["high"]), str(cm["high"]))
    table.add_row("Medium", str(gm["medium"]), str(cm["medium"]))
    table.add_row("Low", str(gm["low"]), str(cm["low"]))
    table.add_row("Total Risks", str(gm["total_risks"]), str(cm["total_risks"]))

    exp_kw = expected.get("keywords", [])
    exp_cat = expected.get("categories", [])
    gkw = len(gremlin_eval["keywords"]["found"])
    ckw = len(claude_eval["keywords"]["found"])
    gcat = len(gremlin_eval["categories"]["found"])
    ccat = len(claude_eval["categories"]["found"])

    table.add_row("Keywords Found", f"{gkw}/{len(exp_kw)}", f"{ckw}/{len(exp_kw)}")
    table.add_row("Categories Found", f"{gcat}/{len(exp_cat)}", f"{ccat}/{len(exp_cat)}")
    table.add_row("Score", f"{gremlin_eval['score']:.0%}", f"{claude_eval['score']:.0%}")

    console.print(table)

    # Show pass/fail details
    if gremlin_eval["fails"]:
        console.print("\n[red]Gremlin Fails:[/red]")
        for f in gremlin_eval["fails"]:
            console.print(f"  - {f}")

    if claude_eval["fails"]:
        console.print("\n[red]Claude Fails:[/red]")
        for f in claude_eval["fails"]:
            console.print(f"  - {f}")

    result = {
        "case": case["name"],
        "timestamp": datetime.now().isoformat(),
        "gremlin": {
            "output": gremlin_result["raw"],
            "evaluation": gremlin_eval,
            "error": gremlin_result["error"],
        },
        "claude": {
            "output": claude_result["raw"],
            "evaluation": claude_eval,
            "error": claude_result["error"],
        },
        "winner": (
            "gremlin" if gremlin_eval["score"] > claude_eval["score"]
            else "claude" if claude_eval["score"] > gremlin_eval["score"]
            else "tie"
        ),
    }

    # Save results
    if save_results:
        results_dir = Path(__file__).parent / "results"
        results_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        result_file = results_dir / f"{case['name']}-{timestamp}.json"
        with open(result_file, "w") as f:
            json.dump(result, f, indent=2, default=str)
        console.print(f"\n[dim]Results saved to: {result_file}[/dim]")

    return result


def run_all_evals(cases_dir: Path = None) -> list[dict]:
    """Run all eval cases in directory."""
    if cases_dir is None:
        cases_dir = Path(__file__).parent / "cases"

    results = []
    case_files = sorted(cases_dir.glob("*.yaml"))

    console.print(f"[bold]Found {len(case_files)} eval cases[/bold]")

    for case_file in case_files:
        try:
            result = run_single_eval(case_file)
            results.append(result)
        except Exception as e:
            console.print(f"[red]Error running {case_file.name}: {e}[/red]")

    # Summary
    console.print("\n" + "=" * 50)
    console.print("[bold]Summary[/bold]")

    gremlin_wins = sum(1 for r in results if r["winner"] == "gremlin")
    claude_wins = sum(1 for r in results if r["winner"] == "claude")
    ties = sum(1 for r in results if r["winner"] == "tie")

    console.print(f"  Gremlin wins: {gremlin_wins}")
    console.print(f"  Claude wins: {claude_wins}")
    console.print(f"  Ties: {ties}")

    return results


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run Gremlin evals")
    parser.add_argument("case", nargs="?", help="Specific case file to run")
    parser.add_argument("--all", action="store_true", help="Run all cases")
    parser.add_argument("--no-save", action="store_true", help="Don't save results")

    args = parser.parse_args()

    if args.case:
        case_path = Path(args.case)
        if not case_path.exists():
            # Try in cases directory
            case_path = Path(__file__).parent / "cases" / f"{args.case}.yaml"
        if not case_path.exists():
            console.print(f"[red]Case not found: {args.case}[/red]")
            sys.exit(1)
        run_single_eval(case_path, save_results=not args.no_save)
    elif args.all:
        run_all_evals()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
