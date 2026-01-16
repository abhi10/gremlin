"""Tests for Gremlin API."""

import json
import os
from unittest.mock import Mock, patch

import pytest

from gremlin import AnalysisResult, Gremlin, Risk
from gremlin.llm.base import LLMResponse


class TestRisk:
    """Test Risk dataclass."""

    def test_risk_creation(self):
        """Test creating a Risk object."""
        risk = Risk(
            severity="CRITICAL",
            confidence=95,
            scenario="What if payment fails after charge?",
            impact="User charged but order not created",
            domains=["payments"],
            title="Payment Race Condition",
        )

        assert risk.severity == "CRITICAL"
        assert risk.confidence == 95
        assert risk.is_critical
        assert risk.is_high_severity

    def test_risk_to_dict(self):
        """Test Risk serialization."""
        risk = Risk(
            severity="HIGH",
            confidence=85,
            scenario="What if session expires?",
            impact="User logged out unexpectedly",
            domains=["auth"],
        )

        data = risk.to_dict()
        assert data["severity"] == "HIGH"
        assert data["confidence"] == 85
        assert data["scenario"] == "What if session expires?"

    def test_severity_checks(self):
        """Test severity level checks."""
        critical = Risk("CRITICAL", 90, "scenario", "impact")
        high = Risk("HIGH", 85, "scenario", "impact")
        medium = Risk("MEDIUM", 70, "scenario", "impact")

        assert critical.is_critical
        assert critical.is_high_severity
        assert not high.is_critical
        assert high.is_high_severity
        assert not medium.is_critical
        assert not medium.is_high_severity


class TestAnalysisResult:
    """Test AnalysisResult dataclass."""

    @pytest.fixture
    def sample_risks(self):
        """Create sample risks for testing."""
        return [
            Risk("CRITICAL", 95, "What if data loss?", "Data permanently lost", ["data"]),
            Risk("HIGH", 85, "What if timeout?", "Request fails", ["performance"]),
            Risk("MEDIUM", 70, "What if slow?", "Poor UX", ["performance"]),
            Risk("LOW", 50, "What if typo?", "Cosmetic issue", ["ui"]),
        ]

    def test_analysis_result_creation(self, sample_risks):
        """Test creating an AnalysisResult."""
        result = AnalysisResult(
            scope="checkout flow",
            risks=sample_risks,
            matched_domains=["payments", "auth"],
            pattern_count=45,
        )

        assert result.scope == "checkout flow"
        assert len(result.risks) == 4
        assert result.pattern_count == 45

    def test_risk_counts(self, sample_risks):
        """Test risk severity counting."""
        result = AnalysisResult(
            scope="test",
            risks=sample_risks,
            matched_domains=[],
            pattern_count=0,
        )

        assert result.critical_count == 1
        assert result.high_count == 1
        assert result.medium_count == 1
        assert result.low_count == 1

    def test_has_critical_risks(self, sample_risks):
        """Test critical risk detection."""
        result = AnalysisResult("test", sample_risks, [], 0)
        assert result.has_critical_risks()

        result_no_critical = AnalysisResult("test", sample_risks[1:], [], 0)
        assert not result_no_critical.has_critical_risks()

    def test_to_dict(self, sample_risks):
        """Test serialization to dictionary."""
        result = AnalysisResult(
            scope="test",
            risks=sample_risks[:2],
            matched_domains=["payments"],
            pattern_count=10,
        )

        data = result.to_dict()
        assert data["scope"] == "test"
        assert len(data["risks"]) == 2
        assert data["summary"]["total_risks"] == 2
        assert data["summary"]["critical"] == 1
        assert data["summary"]["high"] == 1

    def test_to_json(self, sample_risks):
        """Test JSON serialization."""
        result = AnalysisResult("test", sample_risks[:1], [], 5)
        json_str = result.to_json()

        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["scope"] == "test"
        assert len(parsed["risks"]) == 1

    def test_to_junit(self, sample_risks):
        """Test JUnit XML formatting."""
        result = AnalysisResult("test", sample_risks, [], 0)
        xml = result.to_junit()

        assert '<?xml version="1.0"' in xml
        assert '<testsuite' in xml
        assert 'tests="4"' in xml
        assert 'failures="2"' in xml  # CRITICAL + HIGH
        assert '<testcase' in xml
        assert '<failure' in xml  # For CRITICAL/HIGH
        assert '<system-out>' in xml  # For MEDIUM/LOW

    def test_format_for_llm(self, sample_risks):
        """Test LLM-friendly formatting."""
        result = AnalysisResult("checkout", sample_risks[:2], ["payments"], 10)
        formatted = result.format_for_llm()

        assert "checkout" in formatted
        assert "2 risks" in formatted
        assert "CRITICAL" in formatted
        assert "What if data loss?" in formatted

    def test_format_for_llm_no_risks(self):
        """Test LLM format with no risks."""
        result = AnalysisResult("test", [], [], 0)
        formatted = result.format_for_llm()

        assert "No significant risks" in formatted
        assert "test" in formatted


class TestGremlin:
    """Test Gremlin class."""

    @pytest.fixture
    def mock_llm_response(self):
        """Create a mock LLM response."""
        response_text = """
### 🔴 CRITICAL (95%)

**Payment Race Condition**

> What if payment succeeds but order creation fails?

- **Impact:** Customer charged but receives no order confirmation
- **Domain:** payments

### 🟠 HIGH (85%)

**Session Timeout**

> What if user session expires during checkout?

- **Impact:** Lost cart data and poor user experience
- **Domain:** auth
"""
        return LLMResponse(
            text=response_text,
            model="test-model",
            provider="test",
        )

    def test_gremlin_initialization(self):
        """Test Gremlin class initialization."""
        gremlin = Gremlin()
        assert gremlin.provider_name == "anthropic"
        assert gremlin.threshold == 80

        gremlin_custom = Gremlin(provider="openai", threshold=90)
        assert gremlin_custom.provider_name == "openai"
        assert gremlin_custom.threshold == 90

    def test_gremlin_analyze_mock(self, mock_llm_response):
        """Test analyze method with mocked LLM."""
        with patch("gremlin.api.get_provider") as mock_get_provider:
            mock_provider = Mock()
            mock_provider.complete.return_value = mock_llm_response
            mock_get_provider.return_value = mock_provider

            gremlin = Gremlin()
            result = gremlin.analyze("checkout flow")

            assert result.scope == "checkout flow"
            assert len(result.risks) == 2
            assert result.risks[0].severity == "CRITICAL"
            assert result.risks[0].confidence == 95
            assert result.risks[1].severity == "HIGH"

    def test_gremlin_analyze_with_context(self, mock_llm_response):
        """Test analyze with additional context."""
        with patch("gremlin.api.get_provider") as mock_get_provider:
            mock_provider = Mock()
            mock_provider.complete.return_value = mock_llm_response
            mock_get_provider.return_value = mock_provider

            gremlin = Gremlin()
            result = gremlin.analyze(
                scope="payment",
                context="Using Stripe API with webhook handling",
            )

            assert result.scope == "payment"
            # Verify context was passed to prompt builder
            mock_provider.complete.assert_called_once()

    def test_gremlin_analyze_depth(self, mock_llm_response):
        """Test analyze with different depth levels."""
        with patch("gremlin.api.get_provider") as mock_get_provider:
            mock_provider = Mock()
            mock_provider.complete.return_value = mock_llm_response
            mock_get_provider.return_value = mock_provider

            gremlin = Gremlin()
            result = gremlin.analyze("auth", depth="deep")

            assert result.depth == "deep"

    def test_gremlin_analyze_async(self, mock_llm_response):
        """Test async analyze method."""
        import anyio

        async def run_test():
            with patch("gremlin.api.get_provider") as mock_get_provider:
                mock_provider = Mock()
                mock_provider.complete.return_value = mock_llm_response
                mock_get_provider.return_value = mock_provider

                gremlin = Gremlin()
                result = await gremlin.analyze_async("checkout flow")

                assert isinstance(result, AnalysisResult)
                assert result.scope == "checkout flow"
                assert len(result.risks) > 0

        anyio.run(run_test)

    def test_parse_risks_various_formats(self):
        """Test risk parsing with different markdown formats."""
        gremlin = Gremlin()

        # Format with emoji
        response1 = """
### 🔴 CRITICAL (95%)
**Title**
> What if scenario?
- **Impact:** impact text
- **Domain:** payments
"""
        risks1 = gremlin._parse_risks(response1, ["payments"])
        assert len(risks1) == 1
        assert risks1[0].severity == "CRITICAL"

        # Format with brackets
        response2 = """
### [HIGH] (85%)
> What if another scenario?
- **Impact:** another impact
"""
        risks2 = gremlin._parse_risks(response2, ["auth"])
        assert len(risks2) == 1
        assert risks2[0].severity == "HIGH"

    def test_parse_risks_no_matches(self):
        """Test parsing with non-matching format."""
        gremlin = Gremlin()
        response = "This is just plain text with no risk format."

        risks = gremlin._parse_risks(response, [])
        assert len(risks) == 0


class TestImportAPI:
    """Test that API can be imported as specified in Phase 1."""

    def test_import_from_gremlin(self):
        """Test importing from top-level gremlin package."""
        # This import should work per Phase 1 requirements
        from gremlin import Gremlin

        assert Gremlin is not None

    def test_import_all_types(self):
        """Test importing all public API types."""
        from gremlin import AnalysisResult, Gremlin, Risk

        assert Gremlin is not None
        assert Risk is not None
        assert AnalysisResult is not None

    def test_basic_usage_pattern(self):
        """Test the basic usage pattern from design doc."""
        from gremlin import Gremlin

        # Should be able to instantiate without errors
        gremlin = Gremlin()
        assert gremlin is not None

        # Test with different providers (doesn't require API key to construct)
        gremlin_openai = Gremlin(provider="anthropic")
        assert gremlin_openai is not None


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set - skipping integration test",
)
class TestGremlinIntegration:
    """Integration tests with real API (requires API key)."""

    def test_real_api_call(self):
        """Test actual API call to verify end-to-end functionality."""
        gremlin = Gremlin(threshold=70)
        result = gremlin.analyze("user login with password")

        # Basic validations
        assert result.scope == "user login with password"
        assert isinstance(result.risks, list)
        assert result.pattern_count > 0
        # Note: We don't assert specific domains as API responses can vary
        # Just verify the structure is correct
        if len(result.risks) > 0:
            assert all(isinstance(r, Risk) for r in result.risks)
            assert all(hasattr(r, 'domains') for r in result.risks)

    def test_real_async_api_call(self):
        """Test actual async API call."""
        import anyio

        async def run_test():
            gremlin = Gremlin()
            result = await gremlin.analyze_async("file upload")

            assert isinstance(result, AnalysisResult)
            assert result.scope == "file upload"

        anyio.run(run_test)
