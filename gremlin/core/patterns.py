"""Pattern loading and selection."""

from pathlib import Path

import yaml


def load_patterns(patterns_path: Path) -> dict:
    """Load patterns from YAML file.

    Args:
        patterns_path: Path to the breaking.yaml file

    Returns:
        Dict containing universal and domain_specific patterns
    """
    with open(patterns_path) as f:
        return yaml.safe_load(f)


def get_domain_keywords(patterns: dict) -> dict[str, list[str]]:
    """Extract domain keywords from patterns.

    Args:
        patterns: Loaded patterns dict

    Returns:
        Dict mapping domain names to keyword lists
    """
    domain_specific = patterns.get("domain_specific", {})
    return {
        domain: config.get("keywords", [])
        for domain, config in domain_specific.items()
    }


def select_patterns(scope: str, all_patterns: dict, matched_domains: list[str]) -> dict:
    """Select relevant patterns based on scope and matched domains.

    Args:
        scope: User-provided scope string
        all_patterns: All loaded patterns
        matched_domains: List of domains matched from inference

    Returns:
        Dict with universal patterns and matched domain patterns
    """
    selected = {
        "universal": all_patterns.get("universal", []),
        "domain": {},
    }

    domain_specific = all_patterns.get("domain_specific", {})
    for domain in matched_domains:
        if domain in domain_specific:
            selected["domain"][domain] = domain_specific[domain].get("patterns", [])

    return selected
