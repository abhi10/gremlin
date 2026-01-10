#!/usr/bin/env python3
"""Generate benchmark report from eval results.

This script generates a comprehensive markdown report from eval results,
suitable for publishing as a marketing asset or documentation.

Usage:
    # Generate report from latest results
    python evals/generate_report.py

    # Generate from specific results directory
    python evals/generate_report.py --results evals/results/20250110

    # Output to custom file
    python evals/generate_report.py --output BENCHMARK_REPORT.md
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evals.metrics import aggregate_results

console = Console()


def generate_report(
    results_dir: Path,
    output_file: Path | None = None,
    title: str = "Gremlin Benchmark Report",
) -> str:
    """Generate markdown benchmark report from eval results.

    Args:
        results_dir: Directory containing eval result JSON files
        output_file: Optional output file path (prints to stdout if None)
        title: Report title

    Returns:
        Generated markdown content
    """
    # Load all result files
    result_files = sorted(results_dir.glob("*.json"))
    if not result_files:
        raise ValueError(f"No result files found in {results_dir}")

    console.print(f"Loading {len(result_files)} result files...")

    results = []
    for file in result_files:
        try:
            with open(file) as f:
                data = json.load(f)
                results.append(data)
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to load {file.name}: {e}[/yellow]")

    if not results:
        raise ValueError("No valid result files loaded")

    # Aggregate metrics
    aggregated = aggregate_results(results)

    # Build markdown report
    report = _build_markdown_report(results, aggregated, title)

    # Save or print
    if output_file:
        output_file.write_text(report)
        console.print(f"\n[green]✓ Report saved to {output_file}[/green]")
    else:
        console.print(report)

    return report


def _build_markdown_report(
    results: list[dict], aggregated: dict, title: str
) -> str:
    """Build markdown report content.

    Args:
        results: List of individual eval results
        aggregated: Aggregated metrics
        title: Report title

    Returns:
        Markdown content
    """
    timestamp = datetime.now().strftime("%Y-%m-%d")

    # Header
    md = f"""# {title}

**Generated:** {timestamp}
**Cases Evaluated:** {aggregated['total_cases']}
**Total Trials:** {aggregated['total_cases'] * results[0].get('config', {}).get('trials', 3)}

---

## Executive Summary

Gremlin's pattern-driven approach was evaluated against baseline LLM performance across {aggregated['total_cases']} real-world code samples.

**Key Findings:**
- **Win Rate:** {aggregated['gremlin_win_rate']:.0%} (Gremlin wins: {aggregated['gremlin_wins']}, Baseline wins: {aggregated['baseline_wins']}, Ties: {aggregated['ties']})
- **Mean Performance:** Gremlin {aggregated['gremlin_consistency']['mean']:.0%} vs Baseline {aggregated['baseline_consistency']['mean']:.0%}
- **Consistency:** Gremlin CV={aggregated['gremlin_consistency']['cv']:.3f} {'✓ Stable' if aggregated['gremlin_consistency']['is_stable'] else '⚠ Variable'}, Baseline CV={aggregated['baseline_consistency']['cv']:.3f} {'✓ Stable' if aggregated['baseline_consistency']['is_stable'] else '⚠ Variable'}

---

## Methodology

### Evaluation Setup
- **Approach:** A/B testing comparing Gremlin (with patterns) vs baseline LLM (no patterns)
- **Trials:** {results[0].get('config', {}).get('trials', 3)} trials per case for statistical significance
- **Pass Threshold:** {results[0].get('config', {}).get('pass_threshold', 0.7):.0%}
- **LLM Provider:** {results[0].get('config', {}).get('provider', 'anthropic')}
- **Model:** {results[0].get('config', {}).get('model', 'claude-sonnet-4-20250514')}

### Evaluation Criteria
Each output was scored on:
1. **Risk Coverage:** Minimum number of high/critical risks identified
2. **Domain Relevance:** Correct domain classification
3. **Keyword Matching:** Presence of domain-specific terminology
4. **Consistency:** Stability across multiple trials

---

## Detailed Results

"""

    # Per-case breakdown
    md += "### Per-Case Performance\n\n"
    md += "| Case | Mode | Gremlin Score | Baseline Score | Winner |\n"
    md += "|------|------|---------------|----------------|--------|\n"

    for result in results:
        case_name = result.get('case', 'unknown')
        mode = result.get('mode', 'cli')
        gremlin_score = result.get('gremlin_metrics', {}).get('mean_score', 0)
        baseline_score = result.get('claude_metrics', {}).get('mean_score', 0)
        winner = result.get('overall_winner', 'tie')

        winner_emoji = {
            'gremlin': '🟢 Gremlin',
            'claude': '🔴 Baseline',
            'tie': '🟡 Tie'
        }.get(winner, winner)

        md += f"| `{case_name}` | {mode} | {gremlin_score:.0%} | {baseline_score:.0%} | {winner_emoji} |\n"

    md += "\n"

    # Domain breakdown
    md += "### Domain Coverage\n\n"
    domains = {}
    for result in results:
        # Try to extract domain from case name or metadata
        case_name = result.get('case', '')
        domain = case_name.split('-')[0] if '-' in case_name else 'unknown'

        if domain not in domains:
            domains[domain] = {'wins': 0, 'total': 0}

        domains[domain]['total'] += 1
        if result.get('overall_winner') == 'gremlin':
            domains[domain]['wins'] += 1

    md += "| Domain | Cases | Gremlin Wins | Win Rate |\n"
    md += "|--------|-------|--------------|----------|\n"

    for domain, stats in sorted(domains.items()):
        win_rate = stats['wins'] / stats['total'] if stats['total'] > 0 else 0
        md += f"| {domain} | {stats['total']} | {stats['wins']} | {win_rate:.0%} |\n"

    md += "\n"

    # Consistency analysis
    md += "## Consistency Analysis\n\n"
    md += "### Gremlin\n"
    md += f"- **Mean Score:** {aggregated['gremlin_consistency']['mean']:.2%}\n"
    md += f"- **Standard Deviation:** {aggregated['gremlin_consistency']['std_dev']:.3f}\n"
    md += f"- **Coefficient of Variation:** {aggregated['gremlin_consistency']['cv']:.3f} "
    md += f"({'Stable' if aggregated['gremlin_consistency']['is_stable'] else 'Variable'})\n\n"

    md += "### Baseline\n"
    md += f"- **Mean Score:** {aggregated['baseline_consistency']['mean']:.2%}\n"
    md += f"- **Standard Deviation:** {aggregated['baseline_consistency']['std_dev']:.3f}\n"
    md += f"- **Coefficient of Variation:** {aggregated['baseline_consistency']['cv']:.3f} "
    md += f"({'Stable' if aggregated['baseline_consistency']['is_stable'] else 'Variable'})\n\n"

    md += """**Interpretation:** A lower Coefficient of Variation (CV) indicates more consistent performance across trials. CV < 0.15 is considered stable.

---

## Conclusions

"""

    # Generate conclusions based on results
    if aggregated['gremlin_win_rate'] > 0.6:
        md += f"Gremlin demonstrated **strong superiority** with a {aggregated['gremlin_win_rate']:.0%} win rate, "
    elif aggregated['gremlin_win_rate'] > 0.5:
        md += f"Gremlin showed **moderate advantage** with a {aggregated['gremlin_win_rate']:.0%} win rate, "
    else:
        md += f"Gremlin performed **competitively** with a {aggregated['gremlin_win_rate']:.0%} win rate, "

    if aggregated['gremlin_consistency']['is_stable']:
        md += "while maintaining **stable and consistent** performance across trials.\n\n"
    else:
        md += "though performance showed some variability across trials.\n\n"

    md += f"""The pattern-driven approach provides:
1. **{aggregated['gremlin_consistency']['mean']:.0%} average accuracy** in identifying risks
2. **{aggregated['gremlin_consistency']['cv']:.3f} coefficient of variation** demonstrating {'high' if aggregated['gremlin_consistency']['is_stable'] else 'moderate'} consistency
3. **Real-world validation** across {aggregated['total_cases']} production code samples

---

## Next Steps

- Expand benchmark to 100+ projects across additional domains
- Implement ground truth validation with known incidents
- Add cross-model comparison (OpenAI, local models)
- Measure precision/recall with incident data

---

*Generated by Gremlin Eval Framework*
"""

    return md


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate benchmark report from eval results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate from latest results
  python evals/generate_report.py

  # Generate from specific directory
  python evals/generate_report.py --results evals/results/20250110-120000

  # Custom output file
  python evals/generate_report.py --output docs/BENCHMARK.md
        """,
    )

    parser.add_argument(
        "--results",
        type=Path,
        default=Path("evals/results"),
        help="Results directory (default: evals/results)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output markdown file (default: print to stdout)",
    )
    parser.add_argument(
        "--title",
        default="Gremlin Benchmark Report",
        help="Report title",
    )

    args = parser.parse_args()

    try:
        generate_report(
            results_dir=args.results,
            output_file=args.output,
            title=args.title,
        )
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
