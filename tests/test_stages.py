"""Tests for pipeline stage data classes (gremlin/core/stages.py)."""

import json

import pytest

from gremlin.core.stages import (
    IdeationResult,
    JudgmentResult,
    RolloutResult,
    UnderstandingResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def understanding():
    return UnderstandingResult(
        scope="checkout flow",
        matched_domains=["payments", "auth"],
        depth="quick",
        threshold=80,
        context="Using Stripe",
    )


@pytest.fixture
def ideation(understanding):
    return IdeationResult(
        understanding=understanding,
        selected_patterns={
            "universal": ["What if network fails?"],
            "domain_specific": {"payments": ["What if webhook arrives late?"]},
        },
        pattern_count=2,
    )


@pytest.fixture
def rollout(ideation):
    return RolloutResult(
        ideation=ideation,
        raw_response="### 🔴 CRITICAL (95%)\n> What if payment fails?\n- **Impact:** Order lost",
    )


@pytest.fixture
def judgment(rollout):
    return JudgmentResult(
        rollout=rollout,
        risks=[
            {
                "severity": "CRITICAL",
                "confidence": 95,
                "scenario": "What if payment fails?",
                "impact": "Order lost",
                "domains": ["payments"],
                "title": "Payment Failure",
            }
        ],
        validation_summary="1 of 1 risks passed validation",
        validated=True,
    )


# ---------------------------------------------------------------------------
# UnderstandingResult
# ---------------------------------------------------------------------------


class TestUnderstandingResult:
    def test_round_trip(self, understanding):
        d = understanding.to_dict()
        restored = UnderstandingResult.from_dict(d)

        assert restored.scope == understanding.scope
        assert restored.matched_domains == understanding.matched_domains
        assert restored.depth == understanding.depth
        assert restored.threshold == understanding.threshold
        assert restored.context == understanding.context

    def test_json_serializable(self, understanding):
        d = understanding.to_dict()
        # Must not raise
        serialized = json.dumps(d)
        parsed = json.loads(serialized)
        restored = UnderstandingResult.from_dict(parsed)
        assert restored.scope == understanding.scope

    def test_version_field_present(self, understanding):
        d = understanding.to_dict()
        assert "version" in d
        assert isinstance(d["version"], str)

    def test_from_dict_missing_optional_fields(self):
        """from_dict must handle missing optional fields with sensible defaults."""
        minimal = {"scope": "test scope"}
        result = UnderstandingResult.from_dict(minimal)
        assert result.scope == "test scope"
        assert result.matched_domains == []
        assert result.depth == "quick"
        assert result.threshold == 80
        assert result.context is None

    def test_no_context(self):
        u = UnderstandingResult(
            scope="auth", matched_domains=[], depth="deep", threshold=70
        )
        assert u.context is None
        assert u.to_dict()["context"] is None


# ---------------------------------------------------------------------------
# IdeationResult
# ---------------------------------------------------------------------------


class TestIdeationResult:
    def test_round_trip(self, ideation):
        d = ideation.to_dict()
        restored = IdeationResult.from_dict(d)

        assert restored.pattern_count == ideation.pattern_count
        assert restored.selected_patterns == ideation.selected_patterns
        assert restored.understanding.scope == ideation.understanding.scope

    def test_json_serializable(self, ideation):
        serialized = json.dumps(ideation.to_dict())
        parsed = json.loads(serialized)
        restored = IdeationResult.from_dict(parsed)
        assert restored.pattern_count == ideation.pattern_count

    def test_version_field_present(self, ideation):
        assert "version" in ideation.to_dict()

    def test_nested_understanding_preserved(self, ideation):
        d = ideation.to_dict()
        restored = IdeationResult.from_dict(d)
        assert restored.understanding.context == ideation.understanding.context
        assert restored.understanding.threshold == ideation.understanding.threshold


# ---------------------------------------------------------------------------
# RolloutResult
# ---------------------------------------------------------------------------


class TestRolloutResult:
    def test_round_trip(self, rollout):
        d = rollout.to_dict()
        restored = RolloutResult.from_dict(d)

        assert restored.raw_response == rollout.raw_response
        assert restored.ideation.pattern_count == rollout.ideation.pattern_count

    def test_json_serializable(self, rollout):
        serialized = json.dumps(rollout.to_dict())
        parsed = json.loads(serialized)
        restored = RolloutResult.from_dict(parsed)
        assert restored.raw_response == rollout.raw_response

    def test_version_field_present(self, rollout):
        assert "version" in rollout.to_dict()

    def test_empty_raw_response(self, ideation):
        r = RolloutResult(ideation=ideation, raw_response="")
        d = r.to_dict()
        restored = RolloutResult.from_dict(d)
        assert restored.raw_response == ""


# ---------------------------------------------------------------------------
# JudgmentResult
# ---------------------------------------------------------------------------


class TestJudgmentResult:
    def test_round_trip(self, judgment):
        d = judgment.to_dict()
        restored = JudgmentResult.from_dict(d)

        assert len(restored.risks) == 1
        assert restored.risks[0]["severity"] == "CRITICAL"
        assert restored.validation_summary == judgment.validation_summary
        assert restored.validated is True

    def test_json_serializable(self, judgment):
        serialized = json.dumps(judgment.to_dict())
        parsed = json.loads(serialized)
        restored = JudgmentResult.from_dict(parsed)
        assert restored.risks[0]["confidence"] == 95

    def test_version_field_present(self, judgment):
        assert "version" in judgment.to_dict()

    def test_convenience_properties(self, judgment):
        assert judgment.scope == "checkout flow"
        assert judgment.matched_domains == ["payments", "auth"]
        assert judgment.pattern_count == 2
        assert judgment.depth == "quick"
        assert judgment.threshold == 80

    def test_no_validation_summary(self, rollout):
        j = JudgmentResult(rollout=rollout, risks=[], validated=False)
        assert j.validation_summary is None
        d = j.to_dict()
        assert d["validation_summary"] is None

    def test_from_dict_missing_optional_fields(self, rollout):
        minimal = {"rollout": rollout.to_dict()}
        restored = JudgmentResult.from_dict(minimal)
        assert restored.risks == []
        assert restored.validation_summary is None
        assert restored.validated is False


# ---------------------------------------------------------------------------
# Cross-stage chain
# ---------------------------------------------------------------------------


class TestStageChain:
    def test_full_chain_round_trip(self, judgment):
        """Serialize the full nested chain and restore it intact."""
        d = judgment.to_dict()
        serialized = json.dumps(d)
        parsed = json.loads(serialized)
        restored = JudgmentResult.from_dict(parsed)

        # Check all the way down through nesting
        assert restored.scope == "checkout flow"
        assert restored.rollout.ideation.understanding.context == "Using Stripe"
        assert (
            restored.rollout.raw_response
            == "### 🔴 CRITICAL (95%)\n> What if payment fails?\n- **Impact:** Order lost"
        )
        assert restored.risks[0]["title"] == "Payment Failure"
