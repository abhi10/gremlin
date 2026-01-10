"""Integration utilities for Gremlin.

This module provides utilities for integrating the Gremlin CLI tool
with other systems, including the Claude Code agent.
"""

from gremlin.integrations.agent_bridge import analyze_with_cli, check_cli_available

__all__ = ["analyze_with_cli", "check_cli_available"]
