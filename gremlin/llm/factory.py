"""Factory for creating LLM providers."""

import os
from typing import Type

from gremlin.llm.base import LLMConfig, LLMProvider
from gremlin.llm.providers.anthropic import AnthropicProvider


# Registry of available providers
PROVIDER_REGISTRY: dict[str, Type[LLMProvider]] = {
    "anthropic": AnthropicProvider,
}


def get_provider(
    provider: str | None = None,
    model: str | None = None,
    config: LLMConfig | None = None,
    **kwargs
) -> LLMProvider:
    """Create an LLM provider instance.

    Args:
        provider: Provider name (anthropic, openai, ollama). If None, reads from
            GREMLIN_PROVIDER env var or defaults to "anthropic"
        model: Model identifier. If None, reads from GREMLIN_MODEL env var or
            uses provider default
        config: Full LLMConfig object (overrides provider/model args)
        **kwargs: Additional config parameters passed to LLMConfig

    Returns:
        Initialized LLM provider

    Raises:
        ValueError: If provider is not supported or configuration is invalid

    Examples:
        >>> # Use default (Anthropic + env model)
        >>> provider = get_provider()

        >>> # Explicit provider and model
        >>> provider = get_provider("anthropic", "claude-sonnet-4-20250514")

        >>> # Full config
        >>> config = LLMConfig(
        ...     provider="anthropic",
        ...     model="claude-opus-4-5-20251101",
        ...     max_tokens=8192
        ... )
        >>> provider = get_provider(config=config)
    """
    # If full config provided, use it directly
    if config is not None:
        provider_name = config.provider
    else:
        # Resolve provider from args or env
        provider_name = provider or os.environ.get("GREMLIN_PROVIDER", "anthropic")

        # Resolve model from args or env
        if model is None:
            model = os.environ.get("GREMLIN_MODEL") or _get_default_model(provider_name)

        # Build config
        config = LLMConfig(
            provider=provider_name,
            model=model,
            **kwargs
        )

    # Validate provider exists
    provider_name_lower = provider_name.lower()
    if provider_name_lower not in PROVIDER_REGISTRY:
        available = ", ".join(PROVIDER_REGISTRY.keys())
        raise ValueError(
            f"Unsupported provider: {provider_name}. "
            f"Available providers: {available}"
        )

    # Instantiate and validate
    provider_class = PROVIDER_REGISTRY[provider_name_lower]
    provider_instance = provider_class(config)
    provider_instance.validate_config()

    return provider_instance


def register_provider(name: str, provider_class: Type[LLMProvider]) -> None:
    """Register a new LLM provider.

    Allows third-party or custom providers to be registered at runtime.

    Args:
        name: Provider identifier (e.g., "custom-llm")
        provider_class: LLMProvider subclass

    Raises:
        TypeError: If provider_class is not a valid LLMProvider subclass
    """
    if not issubclass(provider_class, LLMProvider):
        raise TypeError(
            f"Provider class must inherit from LLMProvider, got {provider_class}"
        )

    PROVIDER_REGISTRY[name.lower()] = provider_class


def list_providers() -> list[str]:
    """Get list of registered provider names.

    Returns:
        List of available provider identifiers
    """
    return sorted(PROVIDER_REGISTRY.keys())


def _get_default_model(provider: str) -> str:
    """Get default model for a provider.

    Args:
        provider: Provider name

    Returns:
        Default model identifier
    """
    defaults = {
        "anthropic": "claude-sonnet-4-20250514",
        "openai": "gpt-4-turbo-preview",
        "ollama": "llama3.1",
    }
    return defaults.get(provider.lower(), "")
