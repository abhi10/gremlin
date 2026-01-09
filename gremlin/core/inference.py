"""Domain inference from scope string."""


def infer_domains(scope: str, domain_keywords: dict[str, list[str]]) -> list[str]:
    """Infer relevant domains from scope string.

    Args:
        scope: The user-provided scope string (e.g., "checkout flow")
        domain_keywords: Dict mapping domain names to keyword lists

    Returns:
        List of matched domain names
    """
    scope_lower = scope.lower()
    matched = []

    for domain, keywords in domain_keywords.items():
        if any(kw in scope_lower for kw in keywords):
            matched.append(domain)

    return matched
