"""Advanced evaluation metrics for benchmark analysis.

Provides consistency metrics, cross-model comparison, and statistical analysis.
"""

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class ConsistencyMetrics:
    """Metrics for measuring consistency across runs.

    Attributes:
        mean_score: Average score across all trials
        std_dev: Standard deviation of scores
        coefficient_of_variation: Std dev / mean (normalized stability)
        min_score: Minimum score observed
        max_score: Maximum score observed
        range: max - min
        pass_rate: Percentage of trials that passed threshold
        trials: Number of trials measured
    """

    mean_score: float
    std_dev: float
    coefficient_of_variation: float
    min_score: float
    max_score: float
    range: float
    pass_rate: float
    trials: int

    @property
    def is_stable(self) -> bool:
        """Check if results are stable (CV < 0.15).

        Returns:
            True if coefficient of variation is below 15%
        """
        return self.coefficient_of_variation < 0.15


@dataclass
class CrossModelMetrics:
    """Metrics for comparing results across different models.

    Attributes:
        agreement_rate: Percentage of scenarios both models identified
        gremlin_only: Number of risks only Gremlin found
        baseline_only: Number of risks only baseline found
        overlap: Number of risks both found
        jaccard_similarity: Overlap / (gremlin + baseline - overlap)
        relative_coverage: gremlin / baseline ratio
    """

    agreement_rate: float
    gremlin_only: int
    baseline_only: int
    overlap: int
    jaccard_similarity: float
    relative_coverage: float


def calculate_consistency(
    scores: list[float], threshold: float = 0.7
) -> ConsistencyMetrics:
    """Calculate consistency metrics from multiple trial scores.

    Args:
        scores: List of scores from trials
        threshold: Pass/fail threshold

    Returns:
        ConsistencyMetrics with stability analysis
    """
    if not scores:
        return ConsistencyMetrics(
            mean_score=0.0,
            std_dev=0.0,
            coefficient_of_variation=0.0,
            min_score=0.0,
            max_score=0.0,
            range=0.0,
            pass_rate=0.0,
            trials=0,
        )

    n = len(scores)
    mean = sum(scores) / n
    min_score = min(scores)
    max_score = max(scores)
    score_range = max_score - min_score

    # Calculate standard deviation
    if n > 1:
        variance = sum((s - mean) ** 2 for s in scores) / (n - 1)
        std_dev = math.sqrt(variance)
    else:
        std_dev = 0.0

    # Coefficient of variation (normalized stability metric)
    cv = (std_dev / mean) if mean > 0 else 0.0

    # Pass rate
    passes = sum(1 for s in scores if s >= threshold)
    pass_rate = passes / n

    return ConsistencyMetrics(
        mean_score=mean,
        std_dev=std_dev,
        coefficient_of_variation=cv,
        min_score=min_score,
        max_score=max_score,
        range=score_range,
        pass_rate=pass_rate,
        trials=n,
    )


def compare_outputs(
    gremlin_output: str, baseline_output: str, case_name: str = ""
) -> CrossModelMetrics:
    """Compare two model outputs to measure agreement.

    This is a simple text-based comparison. For more sophisticated
    analysis, consider semantic similarity or risk category matching.

    Args:
        gremlin_output: Output from Gremlin
        baseline_output: Output from baseline model
        case_name: Optional case identifier

    Returns:
        CrossModelMetrics with agreement analysis
    """
    import re

    # Extract "what if" questions from each output
    def extract_whatifs(text: str) -> set[str]:
        """Extract normalized 'what if' questions."""
        whatifs = re.findall(r"what if[^?\n.]*[?\n.]", text, re.IGNORECASE)
        # Normalize: lowercase, remove punctuation, strip whitespace
        normalized = set()
        for w in whatifs:
            w = w.lower().strip()
            w = re.sub(r"[^\w\s]", "", w)  # Remove punctuation
            w = re.sub(r"\s+", " ", w)  # Normalize whitespace
            if w:
                normalized.add(w)
        return normalized

    gremlin_whatifs = extract_whatifs(gremlin_output)
    baseline_whatifs = extract_whatifs(baseline_output)

    # Calculate overlap
    overlap = len(gremlin_whatifs & baseline_whatifs)
    gremlin_only = len(gremlin_whatifs - baseline_whatifs)
    baseline_only = len(baseline_whatifs - gremlin_whatifs)

    # Jaccard similarity: intersection / union
    union = len(gremlin_whatifs | baseline_whatifs)
    jaccard = overlap / union if union > 0 else 0.0

    # Agreement rate (what % of all risks were found by both)
    total_unique = len(gremlin_whatifs | baseline_whatifs)
    agreement_rate = overlap / total_unique if total_unique > 0 else 0.0

    # Relative coverage (gremlin / baseline ratio)
    relative_coverage = (
        len(gremlin_whatifs) / len(baseline_whatifs)
        if len(baseline_whatifs) > 0
        else float("inf") if len(gremlin_whatifs) > 0 else 1.0
    )

    return CrossModelMetrics(
        agreement_rate=agreement_rate,
        gremlin_only=gremlin_only,
        baseline_only=baseline_only,
        overlap=overlap,
        jaccard_similarity=jaccard,
        relative_coverage=relative_coverage,
    )


def aggregate_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate metrics across multiple eval cases.

    Args:
        results: List of result dictionaries from run_eval()

    Returns:
        Dictionary with aggregated metrics
    """
    if not results:
        return {}

    # Extract scores from all results
    all_gremlin_scores = []
    all_baseline_scores = []

    for result in results:
        gremlin_metrics = result.get("gremlin_metrics", {})
        baseline_metrics = result.get("claude_metrics", {})

        if "mean_score" in gremlin_metrics:
            all_gremlin_scores.append(gremlin_metrics["mean_score"])
        if "mean_score" in baseline_metrics:
            all_baseline_scores.append(baseline_metrics["mean_score"])

    # Calculate aggregate consistency
    gremlin_consistency = calculate_consistency(all_gremlin_scores)
    baseline_consistency = calculate_consistency(all_baseline_scores)

    # Win/loss statistics
    wins = {"gremlin": 0, "baseline": 0, "tie": 0}
    for result in results:
        winner = result.get("overall_winner", result.get("winner", "tie"))
        if winner == "gremlin":
            wins["gremlin"] += 1
        elif winner in ("claude", "baseline"):
            wins["baseline"] += 1
        else:
            wins["tie"] += 1

    n = len(results)
    return {
        "total_cases": n,
        "gremlin_wins": wins["gremlin"],
        "baseline_wins": wins["baseline"],
        "ties": wins["tie"],
        "gremlin_win_rate": wins["gremlin"] / n if n > 0 else 0.0,
        "gremlin_consistency": {
            "mean": gremlin_consistency.mean_score,
            "std_dev": gremlin_consistency.std_dev,
            "cv": gremlin_consistency.coefficient_of_variation,
            "is_stable": gremlin_consistency.is_stable,
        },
        "baseline_consistency": {
            "mean": baseline_consistency.mean_score,
            "std_dev": baseline_consistency.std_dev,
            "cv": baseline_consistency.coefficient_of_variation,
            "is_stable": baseline_consistency.is_stable,
        },
    }
