"""Base LLM provider interface.

This module defines the abstract interface for LLM providers, enabling
multi-model support and avoiding tight coupling to any single provider.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMConfig:
    """Configuration for LLM provider.

    Attributes:
        provider: Provider name (anthropic, openai, ollama, etc.)
        model: Model identifier (e.g., claude-sonnet-4-20250514, gpt-4)
        api_key: API key for the provider (if required)
        api_base: Optional custom API base URL (for local/self-hosted)
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature
        timeout: Request timeout in seconds
        extra: Additional provider-specific parameters
    """

    provider: str
    model: str
    api_key: str | None = None
    api_base: str | None = None
    max_tokens: int = 4096
    temperature: float = 1.0
    timeout: int = 120
    extra: dict[str, Any] | None = None


@dataclass
class LLMResponse:
    """Standardized response from LLM providers.

    Attributes:
        text: The generated text response
        model: Model that generated the response
        provider: Provider that served the request
        usage: Token usage stats (prompt_tokens, completion_tokens, total_tokens)
        raw_response: Original provider-specific response object
    """

    text: str
    model: str
    provider: str
    usage: dict[str, int] | None = None
    raw_response: Any | None = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    All LLM providers must implement this interface to be compatible with
    Gremlin's eval framework and analysis pipeline.
    """

    def __init__(self, config: LLMConfig):
        """Initialize the provider with configuration.

        Args:
            config: Provider configuration
        """
        self.config = config

    @abstractmethod
    def complete(
        self,
        system_prompt: str,
        user_message: str,
        **kwargs: Any
    ) -> LLMResponse:
        """Generate a completion from the LLM.

        Args:
            system_prompt: System instructions/context
            user_message: User message to respond to
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse with generated text and metadata

        Raises:
            LLMProviderError: If the request fails
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """Validate that the provider is properly configured.

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        pass

    @property
    def name(self) -> str:
        """Get provider name.

        Returns:
            Provider identifier (e.g., 'anthropic', 'openai')
        """
        return self.config.provider

    @property
    def model_name(self) -> str:
        """Get model identifier.

        Returns:
            Model name (e.g., 'claude-sonnet-4-20250514')
        """
        return self.config.model


class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""

    def __init__(self, provider: str, message: str, original_error: Exception | None = None):
        """Initialize error.

        Args:
            provider: Provider that raised the error
            message: Error description
            original_error: Original exception if wrapped
        """
        self.provider = provider
        self.original_error = original_error
        super().__init__(f"[{provider}] {message}")
