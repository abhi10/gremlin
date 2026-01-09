"""Tests for domain inference."""

import pytest

from gremlin.core.inference import infer_domains


# Sample domain keywords for testing
DOMAIN_KEYWORDS = {
    "payments": ["checkout", "payment", "billing", "stripe", "refund"],
    "auth": ["login", "auth", "token", "session", "jwt", "oauth"],
    "file_upload": ["upload", "file", "attachment", "s3", "storage"],
    "database": ["postgres", "sql", "query", "migration", "db"],
}


class TestInferDomains:
    """Tests for infer_domains function."""

    def test_infer_payments_domain(self):
        """Test that payment-related scopes trigger payments domain."""
        assert "payments" in infer_domains("checkout flow", DOMAIN_KEYWORDS)
        assert "payments" in infer_domains("Stripe integration", DOMAIN_KEYWORDS)
        assert "payments" in infer_domains("billing system", DOMAIN_KEYWORDS)

    def test_infer_auth_domain(self):
        """Test that auth-related scopes trigger auth domain."""
        assert "auth" in infer_domains("login page", DOMAIN_KEYWORDS)
        assert "auth" in infer_domains("JWT token handling", DOMAIN_KEYWORDS)
        assert "auth" in infer_domains("OAuth integration", DOMAIN_KEYWORDS)

    def test_infer_multiple_domains(self):
        """Test that multiple domains can be matched."""
        domains = infer_domains("checkout with user authentication", DOMAIN_KEYWORDS)
        assert "payments" in domains
        assert "auth" in domains

    def test_infer_no_domain(self):
        """Test that unmatched scopes return empty list."""
        assert infer_domains("random feature", DOMAIN_KEYWORDS) == []
        assert infer_domains("something else", DOMAIN_KEYWORDS) == []

    def test_inference_case_insensitive(self):
        """Test that inference is case-insensitive."""
        assert infer_domains("LOGIN", DOMAIN_KEYWORDS) == infer_domains("login", DOMAIN_KEYWORDS)
        assert infer_domains("CHECKOUT", DOMAIN_KEYWORDS) == infer_domains("checkout", DOMAIN_KEYWORDS)

    def test_partial_keyword_match(self):
        """Test that partial matches work (keyword in larger word)."""
        # "checkout" contains "checkout"
        assert "payments" in infer_domains("checkout-flow", DOMAIN_KEYWORDS)
