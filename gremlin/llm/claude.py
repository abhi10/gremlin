"""Claude API client."""

import os

from anthropic import Anthropic


def get_client() -> Anthropic:
    """Get Anthropic client.

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
) -> str:
    """Call Claude API with prompts.

    Args:
        client: Anthropic client
        system_prompt: System prompt
        user_message: User message
        model: Model to use (default from env or claude-sonnet-4-20250514)
        max_tokens: Maximum tokens in response

    Returns:
        Claude's response text
    """
    if model is None:
        model = os.environ.get("GREMLIN_MODEL", "claude-sonnet-4-20250514")

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    return response.content[0].text
