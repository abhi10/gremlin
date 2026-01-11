#!/usr/bin/env python3
"""Generate eval cases from collected fixtures.

This script generates YAML eval case files from collected code samples,
making them ready for benchmark evaluation.

Usage:
    # Generate cases from all fixtures
    python evals/generate_cases.py

    # Generate cases for specific domain
    python evals/generate_cases.py --domain auth

    # Regenerate all cases (overwrite existing)
    python evals/generate_cases.py --regenerate
"""

import argparse
import json
import sys
from pathlib import Path

import yaml
from rich.console import Console

console = Console()


def generate_case(
    fixture_file: Path,
    metadata_file: Path,
    output_dir: Path,
) -> Path | None:
    """Generate eval case YAML from fixture.

    Args:
        fixture_file: Path to code fixture (.txt)
        metadata_file: Path to metadata (.meta.json)
        output_dir: Output directory for eval case

    Returns:
        Path to generated case file, or None if generation failed
    """
    try:
        # Load metadata
        with open(metadata_file) as f:
            metadata = json.load(f)

        # Extract info
        domain = metadata.get("domain", "unknown")
        repo_name = metadata.get("repo", "unknown")
        file_path = metadata.get("file_path", "unknown")
        url = metadata.get("url", "")
        stars = metadata.get("stars", 0)

        # Create case name from fixture filename
        case_name = fixture_file.stem

        # Build case description
        description = (
            f"Real-world {domain} code from {repo_name} "
            f"({stars}⭐). File: {file_path}"
        )

        # Infer scope from domain and file path
        scope_map = {
            "auth": "Authentication system",
            "payments": "Payment processing",
            "database": "Database operations",
            "api": "API endpoint",
            "file-upload": "File upload handler",
            "image-processing": "Image processing",
            "deployment": "Deployment configuration",
            "infrastructure": "Infrastructure management",
            "dependencies": "Dependency management",
            "security": "Security implementation",
            "frontend": "Frontend component",
            "search": "Search functionality",
        }
        scope = scope_map.get(domain, f"{domain} implementation")

        # Create eval case structure
        # Use path relative to repo root (where evals are run from)
        relative_fixture_path = f"evals/fixtures/{fixture_file.name}"

        case_data = {
            "name": case_name,
            "description": description,
            "source": {
                "repo": repo_name,
                "file": file_path,
                "url": url,
                "stars": stars,
                "domain": domain,
            },
            "input": {
                "scope": scope,
                "context_file": relative_fixture_path,
                "depth": "quick",
                "threshold": 70,
            },
            "expected": {
                # Conservative expectations - we don't have ground truth yet
                "min_total": 2,  # Expect at least 2 risks identified
                "categories": [domain],  # Should identify the domain
                "keywords": [],  # Will be populated manually later
            },
        }

        # Write YAML
        output_file = output_dir / f"{case_name}.yaml"
        with open(output_file, "w") as f:
            yaml.dump(case_data, f, default_flow_style=False, sort_keys=False)

        return output_file

    except Exception as e:
        console.print(f"[red]Error generating case for {fixture_file.name}: {e}[/red]")
        return None


def generate_all_cases(
    fixtures_dir: Path,
    cases_dir: Path,
    domain_filter: str | None = None,
    regenerate: bool = False,
) -> int:
    """Generate all eval cases from fixtures.

    Args:
        fixtures_dir: Directory containing fixtures
        cases_dir: Output directory for cases
        domain_filter: Optional domain filter
        regenerate: If True, regenerate existing cases

    Returns:
        Number of cases generated
    """
    cases_dir.mkdir(parents=True, exist_ok=True)

    # Find all fixture files
    fixture_files = sorted(fixtures_dir.glob("*.txt"))

    if not fixture_files:
        console.print(f"[yellow]No fixtures found in {fixtures_dir}[/yellow]")
        return 0

    console.print(
        f"\n[bold cyan]Generating eval cases from {len(fixture_files)} "
        f"fixtures[/bold cyan]\n"
    )

    generated = 0
    skipped = 0

    for fixture_file in fixture_files:
        # Check for corresponding metadata
        meta_file = fixture_file.with_suffix(".txt.meta.json")
        if not meta_file.exists():
            # Try alternate naming
            meta_file = fixtures_dir / f"{fixture_file.stem}.meta.json"
            if not meta_file.exists():
                console.print(f"[yellow]✗ No metadata for {fixture_file.name}, skipping[/yellow]")
                skipped += 1
                continue

        # Load metadata to check domain filter
        if domain_filter:
            with open(meta_file) as f:
                metadata = json.load(f)
                if metadata.get("domain") != domain_filter:
                    skipped += 1
                    continue

        # Check if case already exists
        case_file = cases_dir / f"{fixture_file.stem}.yaml"
        if case_file.exists() and not regenerate:
            console.print(f"[dim]○ {fixture_file.name} (case exists, skipping)[/dim]")
            skipped += 1
            continue

        # Generate case
        generated_file = generate_case(fixture_file, meta_file, cases_dir)

        if generated_file:
            console.print(f"[green]✓ {fixture_file.name} → {generated_file.name}[/green]")
            generated += 1
        else:
            skipped += 1

    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  Generated: {generated}")
    console.print(f"  Skipped: {skipped}")
    console.print(f"  Total: {len(fixture_files)}")

    if generated > 0:
        console.print(f"\n[green]✓ Generated {generated} eval cases in {cases_dir}[/green]")

    return generated


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate eval cases from collected fixtures",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all cases
  python evals/generate_cases.py

  # Generate only auth cases
  python evals/generate_cases.py --domain auth

  # Regenerate all (overwrite existing)
  python evals/generate_cases.py --regenerate
        """,
    )

    parser.add_argument(
        "--fixtures",
        type=Path,
        default=Path("evals/fixtures"),
        help="Fixtures directory (default: evals/fixtures)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evals/cases/real-world"),
        help="Output directory (default: evals/cases/real-world)",
    )
    parser.add_argument(
        "--domain",
        help="Filter by domain",
    )
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Regenerate existing cases",
    )

    args = parser.parse_args()

    try:
        count = generate_all_cases(
            fixtures_dir=args.fixtures,
            cases_dir=args.output,
            domain_filter=args.domain,
            regenerate=args.regenerate,
        )

        sys.exit(0 if count > 0 else 1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
