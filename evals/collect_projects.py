#!/usr/bin/env python3
"""Collect real-world projects for eval benchmarking.

This script collects code samples from GitHub across multiple domains
to build a comprehensive eval benchmark suite.

Usage:
    # Collect 20-30 projects across all domains
    python evals/collect_projects.py

    # Collect specific domain
    python evals/collect_projects.py --domain auth

    # Collect with custom limits
    python evals/collect_projects.py --per-domain 5 --total 30

Environment:
    GITHUB_TOKEN: Optional GitHub personal access token for higher rate limits
"""

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Add parent to path to import evals modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from evals.collectors.filters import (
    DOMAIN_FILTERS,
    Domain,
    QualityFilter,
)
from evals.collectors.github import GitHubCollector

console = Console()


def collect_projects(
    domains: list[Domain] | None = None,
    samples_per_domain: int = 3,
    total_limit: int = 30,
    output_dir: Path | None = None,
) -> dict[Domain, int]:
    """Collect projects across domains.

    Args:
        domains: List of domains to collect (None = all)
        samples_per_domain: Samples to collect per domain
        total_limit: Total sample limit across all domains
        output_dir: Output directory for fixtures

    Returns:
        Dictionary mapping domain to number of samples collected
    """
    if output_dir is None:
        output_dir = Path(__file__).parent / "fixtures"

    if domains is None:
        # Default: collect from key domains
        domains = [
            Domain.AUTH,
            Domain.PAYMENTS,
            Domain.DATABASE,
            Domain.API,
            Domain.FILE_UPLOAD,
        ]

    # Initialize collector
    collector = GitHubCollector()

    # Quality filter
    quality_filter = QualityFilter(
        min_stars=100,
        min_code_lines=50,
        max_code_lines=800,
        languages=["TypeScript", "JavaScript", "Python", "Go"],
    )

    results = {}
    total_collected = 0

    console.print(f"\n[bold cyan]Collecting {total_limit} projects across {len(domains)} domains[/bold cyan]\n")

    for domain in domains:
        if total_collected >= total_limit:
            console.print(f"[yellow]Reached total limit of {total_limit} samples[/yellow]")
            break

        # Get domain filter
        domain_filter = DOMAIN_FILTERS.get(domain)
        if not domain_filter:
            console.print(f"[red]No filter defined for {domain.value}, skipping[/red]")
            continue

        # Adjust samples to not exceed total limit
        remaining = total_limit - total_collected
        samples_to_collect = min(samples_per_domain, remaining)

        console.print(f"[bold]Collecting {samples_to_collect} samples for [cyan]{domain.value}[/cyan]...[/bold]")

        # Collect samples
        try:
            samples = collector.collect(
                domain=domain,
                domain_filter=domain_filter,
                quality_filter=quality_filter,
                max_samples=samples_to_collect,
                output_dir=output_dir,
            )

            results[domain] = len(samples)
            total_collected += len(samples)

        except Exception as e:
            console.print(f"[red]Error collecting {domain.value}: {e}[/red]")
            results[domain] = 0

    return results


def display_summary(results: dict[Domain, int]) -> None:
    """Display collection summary.

    Args:
        results: Collection results by domain
    """
    table = Table(title="Collection Summary")
    table.add_column("Domain", style="cyan")
    table.add_column("Samples", style="green", justify="right")

    total = 0
    for domain, count in sorted(results.items(), key=lambda x: x[1], reverse=True):
        table.add_row(domain.value, str(count))
        total += count

    table.add_row("[bold]Total[/bold]", f"[bold]{total}[/bold]")

    console.print("\n")
    console.print(table)

    if total > 0:
        console.print(f"\n[green]✓ Successfully collected {total} code samples[/green]")
        console.print(f"[dim]Saved to: evals/fixtures/[/dim]")
    else:
        console.print("\n[red]✗ No samples collected[/red]")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Collect real-world projects for eval benchmarking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Collect 20-30 projects (default)
  python evals/collect_projects.py

  # Collect only auth projects
  python evals/collect_projects.py --domain auth

  # Collect 50 total samples, 10 per domain
  python evals/collect_projects.py --per-domain 10 --total 50

Environment Variables:
  GITHUB_TOKEN    GitHub personal access token (recommended for higher rate limits)
        """,
    )

    parser.add_argument(
        "--domain",
        choices=[d.value for d in Domain],
        help="Collect specific domain only",
    )
    parser.add_argument(
        "--per-domain",
        type=int,
        default=3,
        help="Samples per domain (default: 3)",
    )
    parser.add_argument(
        "--total",
        type=int,
        default=30,
        help="Total sample limit (default: 30)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output directory (default: evals/fixtures)",
    )

    args = parser.parse_args()

    # Determine domains
    domains = [Domain(args.domain)] if args.domain else None

    # Collect projects
    try:
        results = collect_projects(
            domains=domains,
            samples_per_domain=args.per_domain,
            total_limit=args.total,
            output_dir=args.output,
        )

        display_summary(results)

    except KeyboardInterrupt:
        console.print("\n[yellow]Collection cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
