"""Claude API client.

DEPRECATED: This module provides backward compatibility with the original
Anthropic-only implementation. New code should use gremlin.llm.factory.get_provider()
for multi-provider support.
"""

import os
from typing import Any

from anthropic import Anthropic

from gremlin.llm.factory import get_provider


def get_client() -> Anthropic:
    """Get Anthropic client.

    DEPRECATED: Use get_provider() for multi-provider support.

    Returns:
        Configured Anthropic client

    Raises:
        ValueError: If ANTHROPIC_API_KEY is not set
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable is not set.\n"
            "Get your API key from https://console.anthropic.com/\n"
            "Then run: export ANTHROPIC_API_KEY=sk-ant-..."
        )
    return Anthropic(api_key=api_key)


def call_claude(
    client: Anthropic,
    system_prompt: str,
    user_message: str,
    model: str | None = None,
    max_tokens: int = 4096,
    **kwargs: Any
) -> str:
    """Call Claude API with prompts.

    DEPRECATED: Use get_provider() for multi-provider support.

    This function maintains backward compatibility while internally using the
    new provider abstraction layer. Existing code continues to work unchanged.

    Args:
        client: Anthropic client (ignored, kept for backward compatibility)
        system_prompt: System prompt
        user_message: User message
        model: Model to use (default from env or claude-sonnet-4-20250514)
        max_tokens: Maximum tokens in response
        **kwargs: Additional parameters passed to provider

    Returns:
        Claude's response text
    """
    if model is None:
        model = os.environ.get("GREMLIN_MODEL", "claude-sonnet-4-20250514")

    # Use new provider abstraction
    provider = get_provider(provider="anthropic", model=model, max_tokens=max_tokens)
    response = provider.complete(system_prompt, user_message, **kwargs)
    return response.text
