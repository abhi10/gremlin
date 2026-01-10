"""Bridge for Claude Code agent to invoke Gremlin CLI.

This module provides utilities for the Gremlin agent to detect and invoke
the Gremlin CLI tool for enhanced analysis. The agent works 100% standalone
but can optionally leverage the CLI if installed.
"""

import json
import subprocess
from typing import Optional


def check_cli_available() -> bool:
    """Check if gremlin CLI is installed.

    Returns:
        True if gremlin command is available, False otherwise

    Example:
        >>> if check_cli_available():
        ...     print("Gremlin CLI is installed")
        ... else:
        ...     print("Gremlin CLI not found - agent will work standalone")
    """
    try:
        result = subprocess.run(
            ["which", "gremlin"],
            capture_output=True,
            timeout=5,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False


def analyze_with_cli(
    scope: str,
    context: Optional[str] = None,
    threshold: int = 80,
    depth: str = "quick"
) -> Optional[dict]:
    """Run Gremlin CLI analysis and return JSON results.

    This function allows the Gremlin agent to invoke the CLI tool for
    complementary feature-scope analysis. The agent provides code-focused
    patterns while the CLI provides feature-scope patterns.

    Args:
        scope: Feature description or scope to analyze (e.g., "checkout flow")
        context: Code snippet, file path (@file.py), or additional context
        threshold: Confidence threshold 0-100 (default: 80)
        depth: Analysis depth 'quick' or 'deep' (default: 'quick')

    Returns:
        Parsed JSON dict of analysis results with structure:
        {
            "risks": [...],
            "domains": [...],
            "metrics": {...}
        }
        Returns None if CLI is unavailable or analysis fails.

    Example:
        >>> result = analyze_with_cli(
        ...     scope="checkout flow",
        ...     context="Using Stripe payment gateway",
        ...     threshold=70
        ... )
        >>> if result:
        ...     print(f"Found {len(result.get('risks', []))} feature-scope risks")
        ...     # Combine with agent's code-focused findings
        ... else:
        ...     print("CLI not available - using agent patterns only")
    """
    if not check_cli_available():
        return None

    cmd = [
        "gremlin", "review", scope,
        "--output", "json",
        "--threshold", str(threshold),
        "--depth", depth
    ]

    if context:
        cmd.extend(["--context", context])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            return json.loads(result.stdout)
        return None

    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        return None
