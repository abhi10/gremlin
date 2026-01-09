"""Tests for pattern loading and selection."""

from pathlib import Path

from gremlin.core.patterns import (
    get_domain_keywords,
    load_patterns,
    select_patterns,
)

# Path to actual patterns file
PATTERNS_PATH = Path(__file__).parent.parent / "patterns" / "breaking.yaml"


class TestLoadPatterns:
    """Tests for pattern loading."""

    def test_load_patterns_success(self):
        """Test that patterns load successfully."""
        patterns = load_patterns(PATTERNS_PATH)
        assert "universal" in patterns
        assert "domain_specific" in patterns

    def test_patterns_have_universal_categories(self):
        """Test that universal patterns have expected categories."""
        patterns = load_patterns(PATTERNS_PATH)
        categories = [cat["category"] for cat in patterns["universal"]]
        assert "Input Validation" in categories
        assert "Concurrency" in categories
        assert "Error Paths" in categories

    def test_patterns_have_domain_specific(self):
        """Test that domain-specific patterns exist."""
        patterns = load_patterns(PATTERNS_PATH)
        domains = patterns["domain_specific"].keys()
        assert "auth" in domains
        assert "payments" in domains
        assert "file_upload" in domains


class TestGetDomainKeywords:
    """Tests for keyword extraction."""

    def test_get_domain_keywords(self):
        """Test that domain keywords are extracted correctly."""
        patterns = load_patterns(PATTERNS_PATH)
        keywords = get_domain_keywords(patterns)

        assert "auth" in keywords
        assert "login" in keywords["auth"]
        assert "token" in keywords["auth"]

        assert "payments" in keywords
        assert "checkout" in keywords["payments"]
        assert "stripe" in keywords["payments"]


class TestSelectPatterns:
    """Tests for pattern selection."""

    def test_select_universal_always_included(self):
        """Test that universal patterns are always included."""
        patterns = load_patterns(PATTERNS_PATH)
        selected = select_patterns("random scope", patterns, [])
        assert "universal" in selected
        assert len(selected["universal"]) > 0

    def test_select_domain_patterns(self):
        """Test that matched domain patterns are included."""
        patterns = load_patterns(PATTERNS_PATH)
        selected = select_patterns("checkout", patterns, ["payments"])
        assert "payments" in selected["domain"]
        assert len(selected["domain"]["payments"]) > 0

    def test_select_multiple_domains(self):
        """Test that multiple domains can be selected."""
        patterns = load_patterns(PATTERNS_PATH)
        selected = select_patterns("checkout login", patterns, ["payments", "auth"])
        assert "payments" in selected["domain"]
        assert "auth" in selected["domain"]
