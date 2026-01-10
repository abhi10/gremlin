"""Project collectors for eval suite expansion.

This package provides tools for collecting real-world code samples from
GitHub and other sources for use in the eval benchmark suite.
"""

from evals.collectors.github import GitHubCollector
from evals.collectors.filters import (
    DomainFilter,
    QualityFilter,
    filter_by_domain,
    filter_by_quality,
)

__all__ = [
    "GitHubCollector",
    "DomainFilter",
    "QualityFilter",
    "filter_by_domain",
    "filter_by_quality",
]
