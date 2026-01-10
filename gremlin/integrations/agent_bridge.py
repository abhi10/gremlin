"""Bridge for Claude Code agent to invoke Gremlin CLI.

This module provides utilities for the Gremlin agent to detect and invoke
the Gremlin CLI tool for enhanced analysis. The agent works 100% standalone
but can optionally leverage the CLI if installed.
"""

import json
import logging
import shutil
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


def check_cli_available() -> bool:
    """Check if gremlin CLI is installed (cross-platform).

    Returns:
        True if gremlin command is available, False otherwise

    Example:
        >>> if check_cli_available():
        ...     print("Gremlin CLI is installed")
        ... else:
        ...     print("Gremlin CLI not found - agent will work standalone")
    """
    try:
        # Use shutil.which for cross-platform support (works on Windows too)
        gremlin_path = shutil.which("gremlin")
        if gremlin_path:
            logger.debug(f"Gremlin CLI found at: {gremlin_path}")
            return True
        logger.debug("Gremlin CLI not found in PATH")
        return False
    except Exception as e:
        logger.warning(f"Error checking for Gremlin CLI: {e}")
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

        if result.returncode != 0:
            logger.warning(f"Gremlin CLI failed with code {result.returncode}: {result.stderr}")
            return None

        # Parse and validate JSON response
        try:
            data = json.loads(result.stdout)
            # Basic validation - CLI should return dict
            if not isinstance(data, dict):
                logger.warning(f"Gremlin CLI returned invalid JSON structure: {type(data)}")
                return None
            return data
        except json.JSONDecodeError as e:
            logger.warning(f"Gremlin CLI returned invalid JSON: {e}")
            return None

    except subprocess.TimeoutExpired:
        logger.warning("Gremlin CLI timed out after 120 seconds")
        return None
    except Exception as e:
        logger.error(f"Unexpected error calling Gremlin CLI: {e}")
        return None
