#!/usr/bin/env python3
"""Golden set recall evaluation.

Measures Gremlin's recall against verified ground-truth risk fixtures.
Unlike A/B evals (which measure consistency vs baseline), this measures
correctness: did Gremlin find known real risks?

Usage:
    python evals/golden_eval.py              # run all fixtures
    python evals/golden_eval.py --fast       # single fixture (for CI)
    python evals/golden_eval.py --fixture evals/golden/httpx-golden.json
    python evals/golden_eval.py --threshold 0.6  # custom pass threshold
"""

import argparse
import json
import sys
from pathlib import Path

GOLDEN_DIR = Path(__file__).parent / "golden"
DEFAULT_RECALL_THRESHOLD = 0.5   # fraction of fixtures that must match


def load_fixture(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def load_all_fixtures() -> list[dict]:
    fixtures = []
    for p in sorted(GOLDEN_DIR.glob("*.json")):
        fixtures.append(load_fixture(p))
    return fixtures


def risk_matches_fixture(risk, fixture: dict) -> bool:
    """Return True if a risk satisfies a golden fixture's match criteria.

    Matching is keyword-based: at least one risk_keyword must appear in the
    scenario or impact (case-insensitive). The risk must also meet the
    fixture's minimum confidence.
    """
    text = (risk.scenario + " " + risk.impact).lower()
    confidence_ok = risk.confidence >= fixture["min_confidence"]
    keyword_ok = any(kw.lower() in text for kw in fixture["risk_keywords"])
    return confidence_ok and keyword_ok


def evaluate_fixture(fixture_data: dict, risks) -> dict:
    """Return per-fixture recall results."""
    results = []
    for f in fixture_data["fixtures"]:
        matched = any(risk_matches_fixture(r, f) for r in risks)
        results.append({
            "id": f["id"],
            "matched": matched,
            "scenario_fragment": f["scenario_fragment"],
            "verified_issue": f.get("verified_issue", ""),
        })

    matched_count = sum(1 for r in results if r["matched"])
    recall = matched_count / len(results) if results else 0.0

    return {
        "project": fixture_data["project"],
        "scope": fixture_data["scope"],
        "total_fixtures": len(results),
        "matched": matched_count,
        "recall": recall,
        "fixtures": results,
    }


def run_gremlin_on_scope(scope: str, threshold: int = 65):
    """Run Gremlin analysis and return Risk objects."""
    from gremlin import Gremlin

    g = Gremlin(threshold=threshold)
    result = g.analyze(scope)
    return result.risks


def main():
    parser = argparse.ArgumentParser(description="Gremlin golden set recall evaluation")
    parser.add_argument("--fast", action="store_true",
                        help="Run only the first fixture (for CI)")
    parser.add_argument("--fixture", type=Path,
                        help="Path to a specific golden fixture JSON")
    parser.add_argument(
        "--threshold", type=float, default=DEFAULT_RECALL_THRESHOLD,
        help=f"Minimum recall fraction to pass (default {DEFAULT_RECALL_THRESHOLD})",
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate fixture schemas without making LLM calls")
    args = parser.parse_args()

    # Load fixtures
    if args.fixture:
        fixture_files = [args.fixture]
    else:
        fixture_files = sorted(GOLDEN_DIR.glob("*.json"))

    if not fixture_files:
        print("No golden fixtures found in evals/golden/", file=sys.stderr)
        sys.exit(1)

    if args.fast:
        fixture_files = fixture_files[:1]

    all_results = []
    exit_code = 0

    for fixture_path in fixture_files:
        fixture_data = load_fixture(fixture_path)
        scope = fixture_data["scope"]
        print(f"\n{'='*60}")
        print(f"Project: {fixture_data['project']}")
        print(f"Scope:   {scope}")
        print(f"Fixtures: {len(fixture_data['fixtures'])}")

        if args.dry_run:
            print("  [dry-run] Skipping LLM call — fixture schema valid")
            continue

        try:
            risks = run_gremlin_on_scope(scope)
        except Exception as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            exit_code = 1
            continue

        result = evaluate_fixture(fixture_data, risks)
        all_results.append(result)

        print(f"Risks found: {len(risks)}")
        print(f"Recall:      {result['matched']}/{result['total_fixtures']} "
              f"= {result['recall']:.0%}")

        for f in result["fixtures"]:
            status = "✓" if f["matched"] else "✗"
            print(f"  {status} {f['id']}: {f['scenario_fragment']}")

        if result["recall"] < args.threshold:
            print(f"\n  FAIL: recall {result['recall']:.0%} < threshold {args.threshold:.0%}")
            exit_code = 1

    if all_results and not args.dry_run:
        total_fixtures = sum(r["total_fixtures"] for r in all_results)
        total_matched = sum(r["matched"] for r in all_results)
        overall = total_matched / total_fixtures if total_fixtures else 0.0
        print(f"\n{'='*60}")
        print(f"Overall recall: {total_matched}/{total_fixtures} = {overall:.0%}")
        if exit_code == 0:
            print("PASS")
        else:
            print("FAIL")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
