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


def merge_patterns(base: dict, additional: dict) -> dict:
    """Merge additional patterns into base patterns.

    Args:
        base: Base patterns dict (modified in place)
        additional: Additional patterns to merge

    Returns:
        Merged patterns dict
    """
    # Merge universal patterns (deduplicate by pattern text)
    base_universal = base.get("universal", [])
    add_universal = additional.get("universal", [])

    # Create set of existing pattern texts for deduplication
    existing = set()
    for cat in base_universal:
        for p in cat.get("patterns", []):
            existing.add(p.lower().strip())

    for cat in add_universal:
        cat_name = cat.get("category", "Uncategorized")
        cat_patterns = cat.get("patterns", [])

        # Find or create matching category in base
        base_cat = None
        for bc in base_universal:
            if bc.get("category") == cat_name:
                base_cat = bc
                break

        if base_cat is None:
            base_cat = {"category": cat_name, "patterns": []}
            base_universal.append(base_cat)

        # Add non-duplicate patterns
        for p in cat_patterns:
            if p.lower().strip() not in existing:
                base_cat["patterns"].append(p)
                existing.add(p.lower().strip())

    base["universal"] = base_universal

    # Merge domain-specific patterns
    base_domains = base.get("domain_specific", {})
    add_domains = additional.get("domain_specific", {})

    for domain, config in add_domains.items():
        if domain not in base_domains:
            base_domains[domain] = {"keywords": [], "patterns": []}

        # Merge keywords (deduplicate)
        existing_kw = set(base_domains[domain].get("keywords", []))
        for kw in config.get("keywords", []):
            if kw.lower() not in {k.lower() for k in existing_kw}:
                base_domains[domain].setdefault("keywords", []).append(kw)
                existing_kw.add(kw.lower())

        # Merge patterns (deduplicate)
        existing_pat = {p.lower().strip() for p in base_domains[domain].get("patterns", [])}
        for p in config.get("patterns", []):
            if p.lower().strip() not in existing_pat:
                base_domains[domain].setdefault("patterns", []).append(p)
                existing_pat.add(p.lower().strip())

    base["domain_specific"] = base_domains
    return base


def load_all_patterns(patterns_dir: Path) -> dict:
    """Load and merge patterns from all YAML files in directory.

    Loads breaking.yaml first as base, then merges any additional
    pattern files from the directory and subdirectories.

    Args:
        patterns_dir: Directory containing pattern YAML files

    Returns:
        Merged patterns dict from all sources
    """
    base_file = patterns_dir / "breaking.yaml"
    if not base_file.exists():
        return {"universal": [], "domain_specific": {}}

    patterns = load_patterns(base_file)

    # Find and merge additional pattern files
    for yaml_file in sorted(patterns_dir.rglob("*.yaml")):
        # Skip the base file and code-review patterns (agent-specific)
        if yaml_file.name in ("breaking.yaml", "code-review.yaml"):
            continue

        try:
            additional = load_patterns(yaml_file)
            if additional:
                patterns = merge_patterns(patterns, additional)
        except Exception:
            # Skip invalid files silently
            pass

    return patterns


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
