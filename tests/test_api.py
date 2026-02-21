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

    def test_parse_risks_h2_format(self):
        """Test risk parsing with ## headers (actual LLM output format)."""
        gremlin = Gremlin()

        response = """
## 🔴 CRITICAL (85%)

**Token Verification Mismatch**

> What if the UI uses a different OAuth verification method than the API routes?

- **Impact:** Users appear logged in but all API calls fail with 401/403
- **Domain:** auth

## 🟠 HIGH (90%)

**Cross-Device Token Collision**

> What if token refresh happens simultaneously from mobile app and web browser?

- **Impact:** One device gets invalidated token, forcing re-login
- **Domain:** auth
"""
        risks = gremlin._parse_risks(response, ["auth"])
        assert len(risks) == 2
        assert risks[0].severity == "CRITICAL"
        assert risks[0].confidence == 85
        assert risks[0].title == "Token Verification Mismatch"
        assert "OAuth" in risks[0].scenario
        assert risks[1].severity == "HIGH"
        assert risks[1].confidence == 90

    def test_parse_risks_mixed_header_levels(self):
        """Test risk parsing with mixed ## and ### headers."""
        gremlin = Gremlin()

        response = """
## 🔴 CRITICAL (95%)

**First Risk**

> What if first scenario happens?

- **Impact:** First impact
- **Domain:** payments

### 🟡 MEDIUM (70%)

**Second Risk**

> What if second scenario happens?

- **Impact:** Second impact
- **Domain:** auth
"""
        risks = gremlin._parse_risks(response, ["payments"])
        assert len(risks) == 2
        assert risks[0].severity == "CRITICAL"
        assert risks[1].severity == "MEDIUM"

    def test_parse_risks_no_matches(self):
        """Test parsing with non-matching format."""
        gremlin = Gremlin()
        response = "This is just plain text with no risk format."

        risks = gremlin._parse_risks(response, [])
        assert len(risks) == 0

    def test_analyze_validate_false_makes_one_call(self, mock_llm_response):
        """Default validate=False makes exactly one LLM call."""
        with patch("gremlin.api.get_provider") as mock_get_provider:
            mock_provider = Mock()
            mock_provider.complete.return_value = mock_llm_response
            mock_get_provider.return_value = mock_provider

            gremlin = Gremlin()
            result = gremlin.analyze("checkout flow")

            assert mock_provider.complete.call_count == 1
            assert len(result.risks) == 2

    def test_analyze_validate_true_makes_two_calls(self, mock_llm_response):
        """validate=True makes two LLM calls: rollout + judgment."""
        with patch("gremlin.api.get_provider") as mock_get_provider:
            mock_provider = Mock()
            # First call: rollout. Second call: validation judgment.
            mock_provider.complete.side_effect = [
                mock_llm_response,
                LLMResponse(
                    text="""### 🔴 CRITICAL (95%)

**Payment Race Condition**

> What if payment succeeds but order creation fails?

- **Impact:** Customer charged but receives no order confirmation
- **Domain:** payments
""",
                    model="test-model",
                    provider="test",
                ),
            ]
            mock_get_provider.return_value = mock_provider

            gremlin = Gremlin()
            result = gremlin.analyze("checkout flow", validate=True)

            assert mock_provider.complete.call_count == 2
            # Judgment filtered 2 risks down to 1
            assert len(result.risks) == 1
            assert result.risks[0].severity == "CRITICAL"

    def test_analyze_validate_passes_scope_to_judgment(self, mock_llm_response):
        """Validation prompt includes the original scope."""
        with patch("gremlin.api.get_provider") as mock_get_provider:
            mock_provider = Mock()
            mock_provider.complete.return_value = mock_llm_response
            mock_get_provider.return_value = mock_provider

            gremlin = Gremlin()
            gremlin.analyze("auth system", validate=True)

            second_call_args = mock_provider.complete.call_args_list[1]
            user_message = second_call_args[0][1]
            assert "auth system" in user_message

    def test_analyze_validate_graceful_fallback(self, mock_llm_response):
        """When validation LLM call fails, falls back to unvalidated results."""
        with patch("gremlin.api.get_provider") as mock_get_provider:
            mock_provider = Mock()
            mock_provider.complete.side_effect = [
                mock_llm_response,
                Exception("API rate limit"),
            ]
            mock_get_provider.return_value = mock_provider

            gremlin = Gremlin()
            result = gremlin.analyze("checkout", validate=True)

            # Should not raise; returns unvalidated risks
            assert len(result.risks) == 2

    def test_analyze_async_validate_param_forwarded(self, mock_llm_response):
        """analyze_async forwards validate param to analyze()."""
        import anyio

        async def run_test():
            with patch("gremlin.api.get_provider") as mock_get_provider:
                mock_provider = Mock()
                mock_provider.complete.return_value = mock_llm_response
                mock_get_provider.return_value = mock_provider

                gremlin = Gremlin()
                result = await gremlin.analyze_async("checkout", validate=False)

                assert mock_provider.complete.call_count == 1
                assert isinstance(result, AnalysisResult)

        anyio.run(run_test)


class TestGremlinStageMethods:
    """Test the internal _run_* stage methods introduced in Step 3."""

    @pytest.fixture
    def mock_rollout_response(self):
        return LLMResponse(
            text="""### 🔴 CRITICAL (95%)

**Payment Race Condition**

> What if payment succeeds but order creation fails?

- **Impact:** Customer charged but receives no order confirmation
- **Domain:** payments
""",
            model="test-model",
            provider="test",
        )

    def test_stage_methods_exist(self):
        g = Gremlin()
        assert callable(g._run_understanding)
        assert callable(g._run_ideation)
        assert callable(g._run_rollout)
        assert callable(g._run_judgment)
        assert callable(g._build_result)

    def test_run_understanding_returns_correct_domains(self):
        """_run_understanding infers domains without an LLM call."""
        g = Gremlin()
        result = g._run_understanding("checkout flow with Stripe", None, "quick")

        assert result.scope == "checkout flow with Stripe"
        assert "payments" in result.matched_domains
        assert result.depth == "quick"
        assert result.threshold == g.threshold
        assert result.context is None

    def test_run_understanding_with_context(self):
        g = Gremlin()
        result = g._run_understanding("auth system", "Using JWT", "deep")

        assert result.context == "Using JWT"
        assert result.depth == "deep"

    def test_run_ideation_selects_patterns(self):
        """_run_ideation returns a non-zero pattern count without an LLM call."""
        from gremlin.core.stages import UnderstandingResult

        g = Gremlin()
        u = UnderstandingResult(
            scope="checkout flow",
            matched_domains=["payments"],
            depth="quick",
            threshold=80,
        )
        result = g._run_ideation(u)

        assert result.pattern_count > 0
        assert "universal" in result.selected_patterns
        assert result.understanding is u

    def test_run_rollout_calls_provider_once(self, mock_rollout_response):
        """_run_rollout makes exactly one LLM call."""
        from gremlin.core.stages import IdeationResult, UnderstandingResult

        with patch("gremlin.api.get_provider") as mock_get_provider:
            mock_provider = Mock()
            mock_provider.complete.return_value = mock_rollout_response
            mock_get_provider.return_value = mock_provider

            g = Gremlin()
            u = UnderstandingResult("checkout", ["payments"], "quick", 80)
            i = IdeationResult(u, {"universal": []}, 0)
            result = g._run_rollout(i)

            assert mock_provider.complete.call_count == 1
            assert result.raw_response == mock_rollout_response.text

    def test_run_judgment_parses_risks(self, mock_rollout_response):
        """_run_judgment returns a JudgmentResult with parsed risk dicts."""
        from gremlin.core.stages import IdeationResult, RolloutResult, UnderstandingResult

        g = Gremlin()
        u = UnderstandingResult("checkout", ["payments"], "quick", 80)
        i = IdeationResult(u, {"universal": []}, 0)
        r = RolloutResult(i, mock_rollout_response.text)

        result = g._run_judgment(r, validate=False)

        assert len(result.risks) == 1
        assert result.risks[0]["severity"] == "CRITICAL"
        assert result.risks[0]["confidence"] == 95
        assert result.validated is False

    def test_build_result_produces_analysis_result(self, mock_rollout_response):
        """_build_result converts JudgmentResult → AnalysisResult correctly."""
        from gremlin.core.stages import IdeationResult, JudgmentResult, RolloutResult, UnderstandingResult

        g = Gremlin()
        u = UnderstandingResult("checkout", ["payments"], "quick", 80)
        i = IdeationResult(u, {"universal": []}, 5)
        r = RolloutResult(i, mock_rollout_response.text)
        j = JudgmentResult(
            rollout=r,
            risks=[{
                "severity": "CRITICAL", "confidence": 95,
                "scenario": "What if payment fails?", "impact": "Order lost",
                "domains": ["payments"], "title": "Payment Failure",
            }],
        )

        result = g._build_result(j, raw_response=mock_rollout_response.text)

        assert result.scope == "checkout"
        assert len(result.risks) == 1
        assert result.risks[0].severity == "CRITICAL"
        assert result.risks[0].title == "Payment Failure"
        assert result.pattern_count == 5
        assert result.matched_domains == ["payments"]


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
        # Parser must extract risks from the LLM response
        assert len(result.risks) > 0, (
            f"Parser returned 0 risks but raw_response was: {result.raw_response[:200]}"
        )
        assert all(isinstance(r, Risk) for r in result.risks)
        assert all(r.severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW") for r in result.risks)
        assert all(r.scenario for r in result.risks)
        assert all(r.impact for r in result.risks)

    def test_real_async_api_call(self):
        """Test actual async API call."""
        import anyio

        async def run_test():
            gremlin = Gremlin()
            result = await gremlin.analyze_async("file upload")

            assert isinstance(result, AnalysisResult)
            assert result.scope == "file upload"

        anyio.run(run_test)
