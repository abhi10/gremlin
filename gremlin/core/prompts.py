"""Prompt building for Claude API."""

from pathlib import Path

import yaml


def load_system_prompt(prompt_path: Path) -> str:
    """Load system prompt from file.

    Args:
        prompt_path: Path to system.md file

    Returns:
        System prompt string
    """
    with open(prompt_path) as f:
        return f.read()


def build_prompt(
    system_prompt: str,
    selected_patterns: dict,
    scope: str,
    depth: str,
    threshold: int,
) -> tuple[str, str]:
    """Build full system and user prompts for Claude.

    Args:
        system_prompt: Base system prompt
        selected_patterns: Selected universal + domain patterns
        scope: User-provided scope
        depth: Analysis depth (quick/deep)
        threshold: Confidence threshold

    Returns:
        Tuple of (full_system_prompt, user_message)
    """
    patterns_yaml = yaml.dump(selected_patterns, default_flow_style=False)

    full_system = f"""{system_prompt}

## Available Breaking Patterns

{patterns_yaml}
"""

    user_msg = f"""Analyze this scope for risks: **{scope}**

Depth: {depth}
Confidence threshold: Only include scenarios where you're >{threshold}% confident this could actually happen.

Apply the breaking patterns above. For each risk scenario:
1. State the "what if?" question
2. Explain the potential impact
3. Rate severity (critical/high/medium/low)
4. Provide your confidence percentage

Focus on non-obvious risks. Skip generic advice."""

    return full_system, user_msg
