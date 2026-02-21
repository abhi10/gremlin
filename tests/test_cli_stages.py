"""Tests for v0.3 pipeline stage CLI commands."""

import json
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from gremlin.cli import app
from gremlin.llm.base import LLMResponse

runner = CliRunner()


def _make_llm_response(text: str) -> LLMResponse:
    return LLMResponse(text=text, model="test", provider="test")


SAMPLE_LLM_RESPONSE = """### 🔴 CRITICAL (95%)

**Payment Race Condition**

> What if payment succeeds but order creation fails?

- **Impact:** Customer charged but receives no order confirmation
- **Domain:** payments
"""


@pytest.fixture
def tmp_run_dir(tmp_path):
    run_dir = tmp_path / ".gremlin" / "run"
    run_dir.mkdir(parents=True)
    return run_dir


class TestUnderstandCommand:
    def test_understand_creates_artifact(self, tmp_run_dir):
        result = runner.invoke(
            app, ["understand", "checkout flow", "--run-dir", str(tmp_run_dir)]
        )
        assert result.exit_code == 0
        artifact = tmp_run_dir / "understanding.json"
        assert artifact.exists()
        data = json.loads(artifact.read_text())
        assert data["scope"] == "checkout flow"
        assert "matched_domains" in data
        assert "version" in data

    def test_understand_detects_payments_domain(self, tmp_run_dir):
        runner.invoke(
            app, ["understand", "stripe checkout", "--run-dir", str(tmp_run_dir)]
        )
        data = json.loads((tmp_run_dir / "understanding.json").read_text())
        assert "payments" in data["matched_domains"]

    def test_understand_with_depth(self, tmp_run_dir):
        runner.invoke(
            app, ["understand", "auth system", "--depth", "deep", "--run-dir", str(tmp_run_dir)]
        )
        data = json.loads((tmp_run_dir / "understanding.json").read_text())
        assert data["depth"] == "deep"

    def test_understand_with_threshold(self, tmp_run_dir):
        runner.invoke(
            app, ["understand", "auth", "--threshold", "70", "--run-dir", str(tmp_run_dir)]
        )
        data = json.loads((tmp_run_dir / "understanding.json").read_text())
        assert data["threshold"] == 70

    def test_understand_no_llm_call(self, tmp_run_dir):
        """understand stage must not make any LLM calls."""
        with patch("gremlin.api.get_provider") as mock_get_provider:
            runner.invoke(
                app, ["understand", "checkout", "--run-dir", str(tmp_run_dir)]
            )
            mock_get_provider.assert_not_called()


class TestIdeateCommand:
    def test_ideate_creates_artifact(self, tmp_run_dir):
        # Prerequisite: understanding artifact
        runner.invoke(app, ["understand", "checkout flow", "--run-dir", str(tmp_run_dir)])

        result = runner.invoke(app, ["ideate", "--run-dir", str(tmp_run_dir)])
        assert result.exit_code == 0
        artifact = tmp_run_dir / "scenarios.json"
        assert artifact.exists()
        data = json.loads(artifact.read_text())
        assert data["pattern_count"] > 0
        assert "selected_patterns" in data

    def test_ideate_fails_without_understanding(self, tmp_run_dir):
        result = runner.invoke(app, ["ideate", "--run-dir", str(tmp_run_dir)])
        assert result.exit_code == 1

    def test_ideate_no_llm_call(self, tmp_run_dir):
        """ideate stage must not make any LLM calls."""
        runner.invoke(app, ["understand", "checkout", "--run-dir", str(tmp_run_dir)])
        with patch("gremlin.api.get_provider") as mock_get_provider:
            runner.invoke(app, ["ideate", "--run-dir", str(tmp_run_dir)])
            mock_get_provider.assert_not_called()


class TestRolloutCommand:
    @patch("gremlin.api.get_provider")
    def test_rollout_creates_artifact(self, mock_get_provider, tmp_run_dir):
        mock_provider = Mock()
        mock_provider.complete.return_value = _make_llm_response(SAMPLE_LLM_RESPONSE)
        mock_get_provider.return_value = mock_provider

        runner.invoke(app, ["understand", "checkout", "--run-dir", str(tmp_run_dir)])
        runner.invoke(app, ["ideate", "--run-dir", str(tmp_run_dir)])
        result = runner.invoke(app, ["rollout", "--run-dir", str(tmp_run_dir)])

        assert result.exit_code == 0
        artifact = tmp_run_dir / "results.json"
        assert artifact.exists()
        data = json.loads(artifact.read_text())
        assert "raw_response" in data
        assert data["raw_response"] == SAMPLE_LLM_RESPONSE

    @patch("gremlin.api.get_provider")
    def test_rollout_makes_one_llm_call(self, mock_get_provider, tmp_run_dir):
        mock_provider = Mock()
        mock_provider.complete.return_value = _make_llm_response(SAMPLE_LLM_RESPONSE)
        mock_get_provider.return_value = mock_provider

        runner.invoke(app, ["understand", "checkout", "--run-dir", str(tmp_run_dir)])
        runner.invoke(app, ["ideate", "--run-dir", str(tmp_run_dir)])
        runner.invoke(app, ["rollout", "--run-dir", str(tmp_run_dir)])

        assert mock_provider.complete.call_count == 1

    def test_rollout_fails_without_scenarios(self, tmp_run_dir):
        result = runner.invoke(app, ["rollout", "--run-dir", str(tmp_run_dir)])
        assert result.exit_code == 1


class TestJudgeCommand:
    def _setup_results(self, tmp_run_dir):
        """Write a ready-made results.json for judge tests."""
        from gremlin.core.stages import (
            IdeationResult,
            RolloutResult,
            UnderstandingResult,
        )

        u = UnderstandingResult("checkout", ["payments"], "quick", 80)
        i = IdeationResult(u, {"universal": []}, 5)
        r = RolloutResult(i, SAMPLE_LLM_RESPONSE)
        (tmp_run_dir / "results.json").write_text(json.dumps(r.to_dict(), indent=2))

    def test_judge_creates_artifact(self, tmp_run_dir):
        self._setup_results(tmp_run_dir)
        result = runner.invoke(app, ["judge", "--run-dir", str(tmp_run_dir)])

        assert result.exit_code == 0
        artifact = tmp_run_dir / "scores.json"
        assert artifact.exists()
        data = json.loads(artifact.read_text())
        assert "risks" in data
        assert len(data["risks"]) > 0

    def test_judge_parses_critical_risk(self, tmp_run_dir):
        self._setup_results(tmp_run_dir)
        runner.invoke(app, ["judge", "--run-dir", str(tmp_run_dir)])

        data = json.loads((tmp_run_dir / "scores.json").read_text())
        assert data["risks"][0]["severity"] == "CRITICAL"
        assert data["risks"][0]["confidence"] == 95

    def test_judge_validate_makes_second_llm_call(self, tmp_run_dir):
        # judge --validate sets g._provider via gremlin.cli.get_provider
        self._setup_results(tmp_run_dir)
        with patch("gremlin.cli.get_provider") as mock_get_provider:
            mock_provider = Mock()
            mock_provider.complete.return_value = _make_llm_response(SAMPLE_LLM_RESPONSE)
            mock_get_provider.return_value = mock_provider

            runner.invoke(
                app, ["judge", "--validate", "--run-dir", str(tmp_run_dir)]
            )
            assert mock_provider.complete.call_count == 1  # validation LLM call

    def test_judge_fails_without_results(self, tmp_run_dir):
        result = runner.invoke(app, ["judge", "--run-dir", str(tmp_run_dir)])
        assert result.exit_code == 1


class TestReviewCommandUnchanged:
    """Verify gremlin review behaviour is unchanged after v0.3 additions."""

    @patch("gremlin.cli.get_provider")
    def test_review_still_works(self, mock_get_provider):
        mock_provider = Mock()
        mock_provider.complete.return_value = _make_llm_response(SAMPLE_LLM_RESPONSE)
        mock_get_provider.return_value = mock_provider

        result = runner.invoke(app, ["review", "checkout flow", "-o", "md"])
        assert result.exit_code == 0

    @patch("gremlin.cli.get_provider")
    def test_review_makes_one_call_by_default(self, mock_get_provider):
        mock_provider = Mock()
        mock_provider.complete.return_value = _make_llm_response(SAMPLE_LLM_RESPONSE)
        mock_get_provider.return_value = mock_provider

        runner.invoke(app, ["review", "auth", "-o", "md"])
        assert mock_provider.complete.call_count == 1
