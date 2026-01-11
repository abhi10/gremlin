"""Filters for project collection.

Provides domain-based and quality-based filtering for collected projects.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Domain(str, Enum):
    """Gremlin pattern domains."""

    AUTH = "auth"
    PAYMENTS = "payments"
    DATABASE = "database"
    API = "api"
    FILE_UPLOAD = "file-upload"
    IMAGE_PROCESSING = "image-processing"
    DEPLOYMENT = "deployment"
    INFRASTRUCTURE = "infrastructure"
    DEPENDENCIES = "dependencies"
    SECURITY = "security"
    FRONTEND = "frontend"
    SEARCH = "search"


@dataclass
class DomainFilter:
    """Configuration for domain-based filtering.

    Attributes:
        domain: Target domain
        keywords: GitHub topics/keywords to search
        file_patterns: File patterns to match (e.g., "auth*.ts", "payment*.py")
        exclude_patterns: Patterns to exclude
        min_files: Minimum number of matching files
    """

    domain: Domain
    keywords: list[str]
    file_patterns: list[str]
    exclude_patterns: list[str] | None = None
    min_files: int = 1


@dataclass
class QualityFilter:
    """Configuration for quality-based filtering.

    Attributes:
        min_stars: Minimum GitHub stars
        min_code_lines: Minimum lines of code in sample
        max_code_lines: Maximum lines of code in sample
        languages: Allowed programming languages
        has_tests: Require tests to be present
        recent_activity_days: Require activity within N days
    """

    min_stars: int = 100
    min_code_lines: int = 50
    max_code_lines: int = 1000
    languages: list[str] | None = None
    has_tests: bool = False
    recent_activity_days: int | None = None


# Domain filter presets aligned with patterns/breaking.yaml
DOMAIN_FILTERS: dict[Domain, DomainFilter] = {
    Domain.AUTH: DomainFilter(
        domain=Domain.AUTH,
        keywords=[
            "authentication",
            "oauth",
            "jwt",
            "passport",
            "login",
            "session",
            "2fa",
            "mfa",
        ],
        file_patterns=[
            "**/auth*.{ts,js,py,go,java}",
            "**/login*.{ts,js,py,go,java}",
            "**/session*.{ts,js,py,go,java}",
        ],
    ),
    Domain.PAYMENTS: DomainFilter(
        domain=Domain.PAYMENTS,
        keywords=["stripe", "payment", "checkout", "billing", "subscription"],
        file_patterns=[
            "**/payment*.{ts,js,py,go,java}",
            "**/checkout*.{ts,js,py,go,java}",
            "**/billing*.{ts,js,py,go,java}",
            "**/stripe*.{ts,js,py,go,java}",
        ],
    ),
    Domain.DATABASE: DomainFilter(
        domain=Domain.DATABASE,
        keywords=["database", "orm", "sql", "postgres", "mongodb", "migration"],
        file_patterns=[
            "**/db*.{ts,js,py,go,java}",
            "**/database*.{ts,js,py,go,java}",
            "**/migration*.{ts,js,py,go,java}",
            "**/models*.{ts,js,py,go,java}",
        ],
    ),
    Domain.API: DomainFilter(
        domain=Domain.API,
        keywords=["api", "rest", "graphql", "endpoint", "server"],
        file_patterns=[
            "**/api*.{ts,js,py,go,java}",
            "**/routes*.{ts,js,py,go,java}",
            "**/endpoints*.{ts,js,py,go,java}",
            "**/controller*.{ts,js,py,go,java}",
        ],
    ),
    Domain.FILE_UPLOAD: DomainFilter(
        domain=Domain.FILE_UPLOAD,
        keywords=["upload", "file-upload", "s3", "storage", "multipart"],
        file_patterns=[
            "**/upload*.{ts,js,py,go,java}",
            "**/storage*.{ts,js,py,go,java}",
            "**/file*.{ts,js,py,go,java}",
        ],
    ),
    Domain.IMAGE_PROCESSING: DomainFilter(
        domain=Domain.IMAGE_PROCESSING,
        keywords=["image", "resize", "thumbnail", "pillow", "sharp"],
        file_patterns=[
            "**/image*.{ts,js,py,go,java}",
            "**/thumbnail*.{ts,js,py,go,java}",
            "**/resize*.{ts,js,py,go,java}",
        ],
    ),
    Domain.DEPLOYMENT: DomainFilter(
        domain=Domain.DEPLOYMENT,
        keywords=["deploy", "docker", "kubernetes", "k8s", "container"],
        file_patterns=[
            "**/deploy*.{ts,js,py,go,java,yaml,yml}",
            "**/docker*.{ts,js,py,go,java}",
            "**/k8s*.{ts,js,py,go,java,yaml,yml}",
        ],
    ),
    Domain.INFRASTRUCTURE: DomainFilter(
        domain=Domain.INFRASTRUCTURE,
        keywords=["server", "infrastructure", "cert", "ssl", "tls"],
        file_patterns=[
            "**/server*.{ts,js,py,go,java}",
            "**/cert*.{ts,js,py,go,java}",
            "**/ssl*.{ts,js,py,go,java}",
        ],
    ),
    Domain.DEPENDENCIES: DomainFilter(
        domain=Domain.DEPENDENCIES,
        keywords=["dependency", "package", "version", "upgrade", "npm"],
        file_patterns=[
            "**/package*.{ts,js,py,go,java,json}",
            "**/dependency*.{ts,js,py,go,java}",
            "**/version*.{ts,js,py,go,java}",
        ],
    ),
    Domain.SECURITY: DomainFilter(
        domain=Domain.SECURITY,
        keywords=["security", "xss", "injection", "sanitize", "vulnerability"],
        file_patterns=[
            "**/security*.{ts,js,py,go,java}",
            "**/sanitize*.{ts,js,py,go,java}",
            "**/validate*.{ts,js,py,go,java}",
        ],
    ),
    Domain.FRONTEND: DomainFilter(
        domain=Domain.FRONTEND,
        keywords=["frontend", "react", "vue", "ui", "component"],
        file_patterns=[
            "**/component*.{ts,js,tsx,jsx}",
            "**/ui*.{ts,js,tsx,jsx}",
            "**/*Component.{ts,js,tsx,jsx}",
        ],
    ),
    Domain.SEARCH: DomainFilter(
        domain=Domain.SEARCH,
        keywords=["search", "elasticsearch", "algolia", "index", "query"],
        file_patterns=[
            "**/search*.{ts,js,py,go,java}",
            "**/index*.{ts,js,py,go,java}",
            "**/query*.{ts,js,py,go,java}",
        ],
    ),
}


def filter_by_domain(repo_data: dict[str, Any], domain_filter: DomainFilter) -> bool:
    """Check if repository matches domain filter.

    Args:
        repo_data: GitHub repository data
        domain_filter: Domain filter configuration

    Returns:
        True if repository matches domain criteria
    """
    # Check topics
    topics = repo_data.get("topics", [])
    if any(keyword in topics for keyword in domain_filter.keywords):
        return True

    # Check description
    description = (repo_data.get("description") or "").lower()
    if any(keyword.lower() in description for keyword in domain_filter.keywords):
        return True

    # Check repo name
    name = repo_data.get("name", "").lower()
    if any(keyword.lower() in name for keyword in domain_filter.keywords):
        return True

    return False


def filter_by_quality(repo_data: dict[str, Any], quality_filter: QualityFilter) -> bool:
    """Check if repository meets quality standards.

    Args:
        repo_data: GitHub repository data
        quality_filter: Quality filter configuration

    Returns:
        True if repository meets quality criteria
    """
    # Check stars
    stars = repo_data.get("stargazers_count", 0)
    if stars < quality_filter.min_stars:
        return False

    # Check language
    if quality_filter.languages:
        language = repo_data.get("language", "").lower()
        if language not in [lang.lower() for lang in quality_filter.languages]:
            return False

    # Check recent activity (if specified)
    if quality_filter.recent_activity_days:
        from datetime import datetime, timedelta

        updated_at = repo_data.get("updated_at")
        if updated_at:
            try:
                last_update = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                days_ago = datetime.now(last_update.tzinfo) - timedelta(
                    days=quality_filter.recent_activity_days
                )
                if last_update < days_ago:
                    return False
            except (ValueError, AttributeError):
                pass

    return True
