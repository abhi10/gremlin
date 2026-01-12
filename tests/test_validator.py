"""Tests for risk validation module."""


from gremlin.core.validator import (
    VALIDATION_SYSTEM_PROMPT,
    build_validation_prompt,
)


class TestValidationPrompt:
    """Tests for validation prompt building."""

    def test_build_validation_prompt_includes_scope(self):
        """Test that validation prompt includes the original scope."""
        scope = "checkout flow with Stripe"
        risks = "Some risk output"

        prompt = build_validation_prompt(scope, risks)

        assert scope in prompt
        assert "checkout flow with Stripe" in prompt

    def test_build_validation_prompt_includes_risks(self):
        """Test that validation prompt includes the risks to validate."""
        scope = "auth system"
        risks = """
        🔴 CRITICAL (95%)
        What if the JWT token is not validated on the server?

        🟠 HIGH (88%)
        What if the session expires during checkout?
        """

        prompt = build_validation_prompt(scope, risks)

        assert "JWT token" in prompt
        assert "session expires" in prompt

    def test_build_validation_prompt_has_instructions(self):
        """Test that validation prompt includes review instructions."""
        prompt = build_validation_prompt("scope", "risks")

        assert "Validate" in prompt or "validate" in prompt
        assert "quality" in prompt.lower() or "review" in prompt.lower()


class TestValidationSystemPrompt:
    """Tests for validation system prompt."""

    def test_system_prompt_exists(self):
        """Test that system prompt is defined."""
        assert VALIDATION_SYSTEM_PROMPT
        assert len(VALIDATION_SYSTEM_PROMPT) > 100

    def test_system_prompt_includes_quality_checks(self):
        """Test that system prompt defines quality checks."""
        prompt = VALIDATION_SYSTEM_PROMPT.lower()

        # Should check for relevance
        assert "relevan" in prompt

        # Should check for specificity
        assert "specific" in prompt

        # Should check for duplicates
        assert "duplicate" in prompt

    def test_system_prompt_mentions_rejection(self):
        """Test that system prompt explains what to reject."""
        prompt = VALIDATION_SYSTEM_PROMPT.lower()

        assert "reject" in prompt

    def test_system_prompt_mentions_output_format(self):
        """Test that system prompt specifies output format."""
        prompt = VALIDATION_SYSTEM_PROMPT.lower()

        assert "format" in prompt or "return" in prompt
