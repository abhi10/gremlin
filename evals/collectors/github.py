"""GitHub project collector.

Collects real-world code samples from GitHub for eval benchmarking.
"""

import base64
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from evals.collectors.filters import (
    Domain,
    DomainFilter,
    QualityFilter,
    filter_by_domain,
    filter_by_quality,
)


@dataclass
class CodeSample:
    """A collected code sample from GitHub.

    Attributes:
        repo_name: Full repository name (owner/repo)
        file_path: Path to file within repository
        content: File content
        url: GitHub URL to the file
        domain: Matched domain
        language: Programming language
        stars: Repository star count
        metadata: Additional metadata
    """

    repo_name: str
    file_path: str
    content: str
    url: str
    domain: Domain
    language: str
    stars: int
    metadata: dict[str, Any]


class GitHubCollector:
    """Collects code samples from GitHub repositories.

    Uses GitHub REST API to search for repositories and download relevant files.
    """

    def __init__(self, api_token: str | None = None):
        """Initialize GitHub collector.

        Args:
            api_token: GitHub personal access token (optional, but recommended
                for higher rate limits). If None, reads from GITHUB_TOKEN env var.
        """
        self.api_token = api_token or os.environ.get("GITHUB_TOKEN")
        self.api_base = "https://api.github.com"
        self.samples_collected = 0

    def collect(
        self,
        domain: Domain,
        domain_filter: DomainFilter,
        quality_filter: QualityFilter,
        max_samples: int = 5,
        output_dir: Path | None = None,
    ) -> list[CodeSample]:
        """Collect code samples for a domain.

        Args:
            domain: Target domain
            domain_filter: Domain matching criteria
            quality_filter: Quality requirements
            max_samples: Maximum samples to collect
            output_dir: Optional directory to save samples (if None, returns only)

        Returns:
            List of collected code samples

        Raises:
            ValueError: If GitHub API returns error
        """
        samples: list[CodeSample] = []

        # Search for repositories
        repos = self._search_repositories(
            domain_filter=domain_filter,
            quality_filter=quality_filter,
            limit=max_samples * 3,  # Over-fetch to account for filtering
        )

        print(f"Found {len(repos)} candidate repositories for {domain.value}")

        # Collect samples from repositories
        for repo_data in repos:
            if len(samples) >= max_samples:
                break

            repo_name = repo_data["full_name"]
            print(f"  Scanning {repo_name}...")

            # Find relevant files
            files = self._find_files(repo_name, domain_filter)

            for file_data in files:
                if len(samples) >= max_samples:
                    break

                # Download file content
                content = self._download_file(repo_name, file_data["path"])
                if not content:
                    continue

                # Check code length
                lines = len(content.splitlines())
                if lines < quality_filter.min_code_lines:
                    continue
                if lines > quality_filter.max_code_lines:
                    continue

                # Create sample
                sample = CodeSample(
                    repo_name=repo_name,
                    file_path=file_data["path"],
                    content=content,
                    url=file_data["html_url"],
                    domain=domain,
                    language=repo_data.get("language", "unknown"),
                    stars=repo_data.get("stargazers_count", 0),
                    metadata={
                        "repo_description": repo_data.get("description"),
                        "repo_topics": repo_data.get("topics", []),
                        "file_size": file_data.get("size", 0),
                    },
                )

                samples.append(sample)
                print(f"    ✓ {file_data['path']} ({lines} lines)")

        print(f"Collected {len(samples)} samples for {domain.value}\n")

        # Save to disk if output directory specified
        if output_dir:
            self._save_samples(samples, output_dir)

        return samples

    def _search_repositories(
        self,
        domain_filter: DomainFilter,
        quality_filter: QualityFilter,
        limit: int = 15,
    ) -> list[dict[str, Any]]:
        """Search GitHub for repositories matching criteria.

        Args:
            domain_filter: Domain matching criteria
            quality_filter: Quality requirements
            limit: Maximum repositories to return

        Returns:
            List of repository data dictionaries
        """
        # Build search query (simplified - use primary keyword)
        # GitHub search doesn't handle complex OR queries well
        query_parts = []

        # Use first keyword only for better results
        primary_keyword = domain_filter.keywords[0]
        query_parts.append(primary_keyword)

        # Add quality filters
        query_parts.append(f"stars:>{quality_filter.min_stars}")

        # Use first language only
        if quality_filter.languages:
            query_parts.append(f"language:{quality_filter.languages[0]}")

        query = " ".join(query_parts)

        # Call GitHub search API
        url = f"{self.api_base}/search/repositories"
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": min(limit, 30),  # GitHub max is 30
        }

        try:
            data = self._api_call(url, params)
            repos = data.get("items", [])

            # GitHub search already filtered by our criteria, just return results
            # Additional filtering would be too restrictive
            return repos[:limit]

        except Exception as e:
            print(f"Error searching repositories: {e}")
            return []

    def _find_files(
        self, repo_name: str, domain_filter: DomainFilter, max_depth: int = 3
    ) -> list[dict[str, Any]]:
        """Find files in repository matching domain patterns.

        Args:
            repo_name: Full repository name (owner/repo)
            domain_filter: Domain filter with file patterns
            max_depth: Maximum directory depth to search

        Returns:
            List of file data dictionaries
        """
        # Get repository tree
        url = f"{self.api_base}/repos/{repo_name}/git/trees/HEAD"
        params = {"recursive": "1"}

        try:
            data = self._api_call(url, params)
            tree = data.get("tree", [])

            # Filter files by pattern
            matching_files = []
            for item in tree:
                if item["type"] != "blob":  # Only files, not directories
                    continue

                path = item["path"]

                # Check if path matches any domain pattern
                # Simple pattern matching (can be improved with glob patterns)
                for pattern in domain_filter.file_patterns:
                    # Extract core pattern (e.g., "auth*.ts" -> "auth", "ts")
                    pattern_parts = pattern.replace("**/", "").split("*")
                    if len(pattern_parts) >= 2:
                        prefix = pattern_parts[0]
                        suffix = pattern_parts[-1].replace("{", "").replace("}", "")
                        extensions = suffix.split(",")

                        # Check if file matches
                        filename = Path(path).name.lower()
                        if any(filename.startswith(prefix) and filename.endswith(f".{ext}") for ext in extensions):
                            matching_files.append({
                                "path": path,
                                "sha": item["sha"],
                                "size": item.get("size", 0),
                                "html_url": f"https://github.com/{repo_name}/blob/HEAD/{path}",
                            })
                            break

            return matching_files[:5]  # Limit to 5 files per repo

        except Exception as e:
            print(f"    Error finding files: {e}")
            return []

    def _download_file(self, repo_name: str, file_path: str) -> str | None:
        """Download file content from repository.

        Args:
            repo_name: Full repository name
            file_path: Path to file within repository

        Returns:
            File content as string, or None if download fails
        """
        url = f"{self.api_base}/repos/{repo_name}/contents/{file_path}"

        try:
            data = self._api_call(url)
            content_b64 = data.get("content", "")

            # Decode base64 content
            content = base64.b64decode(content_b64).decode("utf-8")
            return content

        except UnicodeDecodeError:
            print(f"    ✗ Cannot decode {file_path} (binary file?)")
            return None
        except Exception as e:
            print(f"    ✗ Error downloading {file_path}: {e}")
            return None

    def _api_call(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make GitHub API call with rate limiting.

        Args:
            url: API endpoint URL
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            ValueError: If API call fails
        """
        # Build URL with params
        if params:
            query_string = urlencode(params)
            url = f"{url}?{query_string}"

        # Build request with auth header
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.api_token:
            headers["Authorization"] = f"token {self.api_token}"

        request = Request(url, headers=headers)

        try:
            with urlopen(request, timeout=30) as response:
                data = json.loads(response.read())
                time.sleep(0.5)  # Rate limit courtesy delay
                return data

        except HTTPError as e:
            if e.code == 403:
                # Check if rate limited
                reset_time = e.headers.get("X-RateLimit-Reset")
                if reset_time:
                    print(f"Rate limited. Reset at: {reset_time}")
                raise ValueError("GitHub API rate limit exceeded")
            raise ValueError(f"GitHub API error {e.code}: {e.reason}")

        except URLError as e:
            raise ValueError(f"Network error: {e.reason}")

    def _save_samples(self, samples: list[CodeSample], output_dir: Path) -> None:
        """Save code samples to disk.

        Args:
            samples: Code samples to save
            output_dir: Output directory
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, sample in enumerate(samples):
            # Create filename: domain-repo-file-index
            repo_slug = sample.repo_name.replace("/", "-")
            file_slug = Path(sample.file_path).stem
            filename = f"{sample.domain.value}-{repo_slug}-{file_slug}-{i:02d}"

            # Save code
            code_file = output_dir / f"{filename}.txt"
            code_file.write_text(sample.content)

            # Save metadata
            meta_file = output_dir / f"{filename}.meta.json"
            metadata = {
                "repo": sample.repo_name,
                "file_path": sample.file_path,
                "url": sample.url,
                "domain": sample.domain.value,
                "language": sample.language,
                "stars": sample.stars,
                **sample.metadata,
            }
            meta_file.write_text(json.dumps(metadata, indent=2))

        print(f"Saved {len(samples)} samples to {output_dir}")
