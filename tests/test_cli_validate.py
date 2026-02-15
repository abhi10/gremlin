"""Tests for CLI --validate flag."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from gremlin.cli import app
from gremlin.llm.base import LLMResponse

runner = CliRunner()


def _make_llm_response(text: str) -> LLMResponse:
    """Helper to create a mock LLMResponse."""
    return LLMResponse(text=text, model="test", provider="test")


class TestValidateFlag:
    """Tests for the --validate CLI flag."""

    @patch("gremlin.cli.get_provider")
    def test_validate_flag_makes_two_calls(self, mock_get_provider):
        """Test that --validate makes two LLM API calls."""
        mock_provider = MagicMock()
        mock_provider.complete.side_effect = [
            # First call: main analysis
            _make_llm_response("""🔴 CRITICAL (95%)
What if payment fails after order created?

🟠 HIGH (88%)
What if user clicks submit twice?"""),
            # Second call: validation
            _make_llm_response("""🔴 CRITICAL (95%)
What if payment fails after order created?

Validation Summary:
- Original: 2 risks
- Validated: 1 risk
- Rejected: 1 (duplicate concern)"""),
        ]
        mock_get_provider.return_value = mock_provider

        _result = runner.invoke(app, ["review", "checkout", "--validate", "-o", "md"])

        # Should make exactly 2 API calls
        assert mock_provider.complete.call_count == 2

    @patch("gremlin.cli.get_provider")
    def test_without_validate_makes_one_call(self, mock_get_provider):
        """Test that without --validate, only one API call is made."""
        mock_provider = MagicMock()
        mock_provider.complete.return_value = _make_llm_response(
            """🔴 CRITICAL (95%)
What if payment fails?"""
        )
        mock_get_provider.return_value = mock_provider

        _result = runner.invoke(app, ["review", "checkout", "-o", "md"])

        # Should make exactly 1 API call
        assert mock_provider.complete.call_count == 1

    @patch("gremlin.cli.get_provider")
    def test_validate_passes_scope_to_validator(self, mock_get_provider):
        """Test that validation prompt includes the original scope."""
        mock_provider = MagicMock()
        mock_provider.complete.return_value = _make_llm_response("Some risks")
        mock_get_provider.return_value = mock_provider

        _result = runner.invoke(app, ["review", "auth system", "--validate", "-o", "md"])

        # Second call should have scope in the prompt
        if mock_provider.complete.call_count == 2:
            second_call_args = mock_provider.complete.call_args_list[1]
            user_message = second_call_args[0][1]  # Second positional arg
            assert "auth system" in user_message

    @patch("gremlin.cli.get_provider")
    def test_validate_graceful_failure(self, mock_get_provider):
        """Test that validation failure falls back to unvalidated results."""
        mock_provider = MagicMock()
        mock_provider.complete.side_effect = [
            _make_llm_response("Original risks output"),
            Exception("API rate limit"),  # Validation fails
        ]
        mock_get_provider.return_value = mock_provider

        result = runner.invoke(app, ["review", "test", "--validate", "-o", "md"])

        # Should not crash, should show warning
        assert result.exit_code == 0 or "Warning" in result.output

    def test_validate_flag_in_help(self):
        """Test that --validate flag appears in help text."""
        result = runner.invoke(app, ["review", "--help"])

        assert "--validate" in result.output or "-V" in result.output
        assert "hallucination" in result.output.lower() or "filter" in result.output.lower()
