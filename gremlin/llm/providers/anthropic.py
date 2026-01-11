"""Anthropic (Claude) LLM provider implementation."""

import os
from typing import Any

from anthropic import Anthropic, APIError, APITimeoutError

from gremlin.llm.base import LLMConfig, LLMProvider, LLMProviderError, LLMResponse


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider implementation.

    Supports all Claude models via the Anthropic API.
    """

    def __init__(self, config: LLMConfig):
        """Initialize Anthropic provider.

        Args:
            config: Provider configuration with Anthropic API key

        Raises:
            ValueError: If API key is missing
        """
        super().__init__(config)

        # Get API key from config or environment
        api_key = config.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required. Set it in config or environment.\n"
                "Get your API key from https://console.anthropic.com/\n"
                "Then run: export ANTHROPIC_API_KEY=sk-ant-..."
            )

        # Initialize Anthropic client
        client_kwargs = {"api_key": api_key}
        if config.api_base:
            client_kwargs["base_url"] = config.api_base
        if config.timeout:
            client_kwargs["timeout"] = config.timeout

        self.client = Anthropic(**client_kwargs)

    def validate_config(self) -> bool:
        """Validate Anthropic configuration.

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        # Check model name format
        if not self.config.model:
            raise ValueError("Model name is required")

        # Validate model prefix (should be claude-*)
        if not self.config.model.startswith("claude-"):
            raise ValueError(
                f"Invalid Anthropic model: {self.config.model}. "
                "Expected model starting with 'claude-'"
            )

        return True

    def complete(
        self,
        system_prompt: str,
        user_message: str,
        **kwargs: Any
    ) -> LLMResponse:
        """Generate completion using Anthropic API.

        Args:
            system_prompt: System instructions
            user_message: User message
            **kwargs: Additional parameters (overrides config values)
                - max_tokens: Override config.max_tokens
                - temperature: Override config.temperature

        Returns:
            LLMResponse with generated text and metadata

        Raises:
            LLMProviderError: If API call fails
        """
        try:
            # Build request parameters
            max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
            temperature = kwargs.get("temperature", self.config.temperature)

            # Call Anthropic API
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            # Extract response text
            text = response.content[0].text

            # Build usage stats
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            }

            return LLMResponse(
                text=text,
                model=self.config.model,
                provider="anthropic",
                usage=usage,
                raw_response=response,
            )

        except APITimeoutError as e:
            raise LLMProviderError(
                "anthropic",
                f"Request timeout after {self.config.timeout}s",
                original_error=e
            )
        except APIError as e:
            raise LLMProviderError(
                "anthropic",
                f"API error: {str(e)}",
                original_error=e
            )
        except Exception as e:
            raise LLMProviderError(
                "anthropic",
                f"Unexpected error: {str(e)}",
                original_error=e
            )
