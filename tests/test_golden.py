"""Tests for golden set fixtures (schema validation, no LLM calls)."""

import json
from pathlib import Path

import pytest

GOLDEN_DIR = Path(__file__).parent.parent / "evals" / "golden"
REQUIRED_FIXTURE_FIELDS = {"version", "project", "scope", "fixtures"}
REQUIRED_ENTRY_FIELDS = {"id", "risk_keywords", "scenario_fragment", "min_confidence"}


def golden_fixture_paths():
    return list(GOLDEN_DIR.glob("*.json"))


class TestGoldenFixtureSchema:
    """Unit tests that validate fixture JSON schema without LLM calls."""

    def test_golden_dir_exists(self):
        assert GOLDEN_DIR.exists(), f"evals/golden/ directory not found at {GOLDEN_DIR}"

    def test_at_least_one_fixture(self):
        paths = golden_fixture_paths()
        assert len(paths) >= 1, "No golden fixture JSON files found"

    @pytest.mark.parametrize("fixture_path", golden_fixture_paths())
    def test_fixture_is_valid_json(self, fixture_path):
        with open(fixture_path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    @pytest.mark.parametrize("fixture_path", golden_fixture_paths())
    def test_fixture_top_level_fields(self, fixture_path):
        with open(fixture_path) as f:
            data = json.load(f)
        missing = REQUIRED_FIXTURE_FIELDS - set(data.keys())
        assert not missing, f"{fixture_path.name} missing top-level fields: {missing}"

    @pytest.mark.parametrize("fixture_path", golden_fixture_paths())
    def test_fixture_has_entries(self, fixture_path):
        with open(fixture_path) as f:
            data = json.load(f)
        assert len(data["fixtures"]) > 0, f"{fixture_path.name} has no fixture entries"

    @pytest.mark.parametrize("fixture_path", golden_fixture_paths())
    def test_fixture_entry_fields(self, fixture_path):
        with open(fixture_path) as f:
            data = json.load(f)
        for entry in data["fixtures"]:
            missing = REQUIRED_ENTRY_FIELDS - set(entry.keys())
            assert not missing, (
                f"{fixture_path.name} entry '{entry.get('id', '?')}' "
                f"missing fields: {missing}"
            )

    @pytest.mark.parametrize("fixture_path", golden_fixture_paths())
    def test_fixture_risk_keywords_non_empty(self, fixture_path):
        with open(fixture_path) as f:
            data = json.load(f)
        for entry in data["fixtures"]:
            assert len(entry["risk_keywords"]) > 0, (
                f"Entry '{entry['id']}' has empty risk_keywords"
            )

    @pytest.mark.parametrize("fixture_path", golden_fixture_paths())
    def test_fixture_min_confidence_in_range(self, fixture_path):
        with open(fixture_path) as f:
            data = json.load(f)
        for entry in data["fixtures"]:
            conf = entry["min_confidence"]
            assert 0 <= conf <= 100, (
                f"Entry '{entry['id']}' min_confidence {conf} outside [0,100]"
            )

    @pytest.mark.parametrize("fixture_path", golden_fixture_paths())
    def test_fixture_version_field(self, fixture_path):
        with open(fixture_path) as f:
            data = json.load(f)
        assert "version" in data
        assert isinstance(data["version"], str)

    @pytest.mark.parametrize("fixture_path", golden_fixture_paths())
    def test_fixture_entry_ids_unique(self, fixture_path):
        with open(fixture_path) as f:
            data = json.load(f)
        ids = [e["id"] for e in data["fixtures"]]
        assert len(ids) == len(set(ids)), f"{fixture_path.name} has duplicate entry IDs"


class TestGoldenEvalLogic:
    """Unit tests for the recall evaluation logic (no LLM calls)."""

    def test_risk_matches_fixture_keyword_hit(self):
        from unittest.mock import Mock

        from evals.golden_eval import risk_matches_fixture

        risk = Mock()
        risk.scenario = "What if timeout occurs during connection?"
        risk.impact = "Request fails silently"
        risk.confidence = 80

        fixture = {
            "risk_keywords": ["timeout", "connect"],
            "min_confidence": 70,
        }
        assert risk_matches_fixture(risk, fixture)

    def test_risk_matches_fixture_keyword_miss(self):
        from unittest.mock import Mock

        from evals.golden_eval import risk_matches_fixture

        risk = Mock()
        risk.scenario = "What if auth token expires?"
        risk.impact = "User logged out"
        risk.confidence = 85

        fixture = {
            "risk_keywords": ["timeout", "connection"],
            "min_confidence": 70,
        }
        assert not risk_matches_fixture(risk, fixture)

    def test_risk_matches_fixture_confidence_below_threshold(self):
        from unittest.mock import Mock

        from evals.golden_eval import risk_matches_fixture

        risk = Mock()
        risk.scenario = "What if timeout happens?"
        risk.impact = "Request fails"
        risk.confidence = 50

        fixture = {
            "risk_keywords": ["timeout"],
            "min_confidence": 70,
        }
        assert not risk_matches_fixture(risk, fixture)

    def test_evaluate_fixture_recall(self):
        from unittest.mock import Mock

        from evals.golden_eval import evaluate_fixture

        fixture_data = {
            "project": "test",
            "scope": "test scope",
            "fixtures": [
                {"id": "t-001", "risk_keywords": ["timeout"], "min_confidence": 60,
                 "scenario_fragment": "timeout"},
                {"id": "t-002", "risk_keywords": ["auth", "token"], "min_confidence": 60,
                 "scenario_fragment": "auth"},
            ],
        }

        # One matching risk, one not
        risk1 = Mock()
        risk1.scenario = "What if timeout occurs?"
        risk1.impact = "Request fails"
        risk1.confidence = 80

        risk2 = Mock()
        risk2.scenario = "What if deploy fails?"
        risk2.impact = "Outage"
        risk2.confidence = 85

        result = evaluate_fixture(fixture_data, [risk1, risk2])

        assert result["total_fixtures"] == 2
        assert result["matched"] == 1
        assert result["recall"] == 0.5
