"""Gremlin API - Programmatic interface for risk analysis.

This module provides the core API for using Gremlin as a library, enabling
integration with agent frameworks, CI/CD pipelines, and custom tools.
"""

import asyncio
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gremlin.core.inference import infer_domains
from gremlin.core.patterns import (
    get_domain_keywords,
    load_all_patterns,
    select_patterns,
)
from gremlin.core.prompts import build_prompt, load_system_prompt
from gremlin.core.stages import IdeationResult, JudgmentResult, RolloutResult, UnderstandingResult
from gremlin.core.validator import VALIDATION_SYSTEM_PROMPT, build_validation_prompt
from gremlin.llm.factory import get_provider

# Pre-compiled regex patterns for response parsing (avoid recompiling per call)
_HEADER_PATTERN = re.compile(
    r'^\s*(?:🔴|🟠|🟡|🟢)?\s*(?:\[)?(\w+)(?:\])?\s*\((\d+)%?\)',
    re.IGNORECASE
)
_IMPACT_PATTERN = re.compile(
    r'-?\s*\*\*Impact:?\*\*\s*(.+)', re.IGNORECASE
)
_DOMAIN_PATTERN = re.compile(
    r'-?\s*\*\*Domain:?\*\*\s*(.+)', re.IGNORECASE
)


@dataclass
class Risk:
    """Structured risk finding.

    Attributes:
        severity: Risk severity level (CRITICAL, HIGH, MEDIUM, LOW)
        confidence: Confidence score 0-100
        scenario: The "What if..." description
        impact: Business/technical impact description
        domains: Matched pattern domains
        title: Short title for the risk (optional)
    """

    severity: str
    confidence: int
    scenario: str
    impact: str
    domains: list[str] = field(default_factory=list)
    title: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "severity": self.severity,
            "confidence": self.confidence,
            "scenario": self.scenario,
            "impact": self.impact,
            "domains": self.domains,
            "title": self.title,
        }

    @property
    def is_critical(self) -> bool:
        """Check if this is a critical risk."""
        return self.severity.upper() == "CRITICAL"

    @property
    def is_high_severity(self) -> bool:
        """Check if this is high severity or above."""
        return self.severity.upper() in ("CRITICAL", "HIGH")


@dataclass
class AnalysisResult:
    """Complete analysis response.

    Attributes:
        scope: The feature/scope that was analyzed
        risks: List of identified risks
        matched_domains: Domains detected in the scope
        pattern_count: Number of patterns applied
        raw_response: Original LLM response text
        depth: Analysis depth used (quick/deep)
        threshold: Confidence threshold applied
    """

    scope: str
    risks: list[Risk]
    matched_domains: list[str]
    pattern_count: int
    raw_response: str = ""
    depth: str = "quick"
    threshold: int = 80

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON/API responses."""
        return {
            "scope": self.scope,
            "risks": [risk.to_dict() for risk in self.risks],
            "matched_domains": self.matched_domains,
            "pattern_count": self.pattern_count,
            "depth": self.depth,
            "threshold": self.threshold,
            "summary": {
                "total_risks": len(self.risks),
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
            },
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def to_junit(self) -> str:
        """Format as JUnit XML for CI integration.

        Each risk becomes a test case. Critical/High risks are failures,
        Medium/Low risks are warnings (passed tests with system-out).
        """
        test_count = len(self.risks)
        failure_count = sum(1 for r in self.risks if r.is_high_severity)

        xml_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<testsuite name="Gremlin QA Analysis" '
            f'tests="{test_count}" failures="{failure_count}">',
        ]

        for i, risk in enumerate(self.risks, 1):
            classname = f"gremlin.{self.scope.replace(' ', '_')}"
            testname = risk.title or f"risk_{i}"

            xml_parts.append(f'  <testcase classname="{classname}" name="{testname}">')

            if risk.is_high_severity:
                xml_parts.append(f'    <failure message="{risk.severity}: {risk.scenario}">')
                xml_parts.append(f'Severity: {risk.severity}')
                xml_parts.append(f'Confidence: {risk.confidence}%')
                xml_parts.append(f'Impact: {risk.impact}')
                xml_parts.append(f'Domains: {", ".join(risk.domains)}')
                xml_parts.append('    </failure>')
            else:
                xml_parts.append('    <system-out>')
                xml_parts.append(f'{risk.severity} ({risk.confidence}%): {risk.scenario}')
                xml_parts.append(f'Impact: {risk.impact}')
                xml_parts.append('    </system-out>')

            xml_parts.append('  </testcase>')

        xml_parts.append('</testsuite>')
        return '\n'.join(xml_parts)

    def format_for_llm(self) -> str:
        """Format for consumption by LLM agents.

        Returns a concise, structured summary suitable for including
        in agent context or tool responses.
        """
        if not self.risks:
            return f"No significant risks found for: {self.scope}"

        parts = [
            f"Risk Analysis for: {self.scope}",
            f"Found {len(self.risks)} risks "
            f"({self.critical_count} critical, {self.high_count} high)",
            "",
        ]

        for risk in self.risks:
            parts.append(f"[{risk.severity}] {risk.scenario}")
            parts.append(f"  Impact: {risk.impact}")
            if risk.domains:
                parts.append(f"  Domains: {', '.join(risk.domains)}")
            parts.append("")

        return "\n".join(parts)

    def has_critical_risks(self) -> bool:
        """Check if any critical risks were found."""
        return any(risk.is_critical for risk in self.risks)

    def has_high_severity_risks(self) -> bool:
        """Check if any high severity (or above) risks were found."""
        return any(risk.is_high_severity for risk in self.risks)

    @property
    def critical_count(self) -> int:
        """Count of critical risks."""
        return sum(1 for r in self.risks if r.severity.upper() == "CRITICAL")

    @property
    def high_count(self) -> int:
        """Count of high severity risks."""
        return sum(1 for r in self.risks if r.severity.upper() == "HIGH")

    @property
    def medium_count(self) -> int:
        """Count of medium severity risks."""
        return sum(1 for r in self.risks if r.severity.upper() == "MEDIUM")

    @property
    def low_count(self) -> int:
        """Count of low severity risks."""
        return sum(1 for r in self.risks if r.severity.upper() == "LOW")


class Gremlin:
    """Programmatic API for Gremlin risk analysis.

    This class provides the main entry point for using Gremlin as a library.

    Examples:
        >>> from gremlin import Gremlin
        >>>
        >>> # Basic usage
        >>> gremlin = Gremlin()
        >>> result = gremlin.analyze("checkout flow")
        >>> if result.has_critical_risks():
        ...     print(f"Found {result.critical_count} critical risks!")
        >>>
        >>> # With context
        >>> result = gremlin.analyze(
        ...     scope="user authentication",
        ...     context="Using JWT tokens with Redis session store"
        ... )
        >>>
        >>> # Different provider
        >>> gremlin = Gremlin(provider="openai", model="gpt-4-turbo")
        >>> result = gremlin.analyze("payment processing")
        >>>
        >>> # Async usage
        >>> result = await gremlin.analyze_async("file upload")
    """

    def __init__(
        self,
        provider: str = "anthropic",
        model: str | None = None,
        threshold: int = 80,
        patterns_dir: Path | None = None,
        system_prompt_path: Path | None = None,
    ):
        """Initialize Gremlin analyzer.

        Args:
            provider: LLM provider name (anthropic, openai, ollama)
            model: Specific model to use (None uses provider default)
            threshold: Confidence threshold 0-100 for filtering risks
            patterns_dir: Custom patterns directory (None uses built-in)
            system_prompt_path: Custom system prompt (None uses built-in)
        """
        self.provider_name = provider
        self.model_name = model
        self.threshold = threshold

        # Resolve paths to built-in resources (inside gremlin package)
        package_dir = Path(__file__).parent
        self.patterns_dir = patterns_dir or (package_dir / "patterns")
        self.system_prompt_path = system_prompt_path or (
            package_dir / "prompts" / "system.md"
        )

        # Load patterns and system prompt once
        self._patterns = load_all_patterns(self.patterns_dir)
        self._system_prompt = load_system_prompt(self.system_prompt_path)
        self._domain_keywords = get_domain_keywords(self._patterns)

        # Lazy-initialized LLM provider (created on first analyze() call)
        self._provider = None

    def analyze(
        self,
        scope: str,
        context: str | None = None,
        depth: str = "quick",
        validate: bool = False,
    ) -> AnalysisResult:
        """Analyze a scope for QA risks (synchronous).

        Args:
            scope: Feature or area to analyze (e.g., "checkout flow")
            context: Optional additional context (code, requirements, etc.)
            depth: Analysis depth - "quick" or "deep"
            validate: Run a second LLM pass to filter hallucinations and
                duplicates. Increases quality at the cost of one extra API call.
                On validation failure, falls back to unvalidated results.

        Returns:
            AnalysisResult with identified risks and metadata

        Raises:
            ValueError: If provider configuration is invalid
            Exception: If LLM API call fails

        Examples:
            >>> gremlin = Gremlin()
            >>> result = gremlin.analyze("user registration")
            >>> print(f"Found {len(result.risks)} risks")
            >>>
            >>> # With validation pass
            >>> result = gremlin.analyze("checkout", validate=True)
            >>>
            >>> # With code context
            >>> code = open("checkout.py").read()
            >>> result = gremlin.analyze("checkout", context=code)
        """
        u = self._run_understanding(scope, context, depth)
        i = self._run_ideation(u)
        r = self._run_rollout(i)
        j = self._run_judgment(r, validate=validate)
        return self._build_result(j, raw_response=r.raw_response)

    async def analyze_async(
        self,
        scope: str,
        context: str | None = None,
        depth: str = "quick",
        validate: bool = False,
    ) -> AnalysisResult:
        """Analyze a scope for QA risks (asynchronous).

        This method runs the analysis in a thread pool to avoid blocking
        the event loop, making it suitable for use in async agent frameworks.

        Args:
            scope: Feature or area to analyze
            context: Optional additional context
            depth: Analysis depth - "quick" or "deep"
            validate: Run a second LLM pass to filter hallucinations and duplicates

        Returns:
            AnalysisResult with identified risks and metadata

        Examples:
            >>> gremlin = Gremlin()
            >>> result = await gremlin.analyze_async("payment flow")
            >>> if result.has_critical_risks():
            ...     print("Critical issues found!")
        """
        # Run synchronous analyze() in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self.analyze(scope, context, depth, validate)
        )

    # ------------------------------------------------------------------
    # Pipeline stage methods (internal)
    # Called sequentially by analyze(). Exposed as private to allow
    # independent testing and future CLI stage commands (v0.3).
    # ------------------------------------------------------------------

    def _run_understanding(
        self, scope: str, context: str | None, depth: str
    ) -> UnderstandingResult:
        """Stage 1 — Understanding: infer domains from scope keywords."""
        try:
            matched_domains = infer_domains(scope, self._domain_keywords)
            return UnderstandingResult(
                scope=scope,
                matched_domains=matched_domains,
                depth=depth,
                threshold=self.threshold,
                context=context,
            )
        except Exception as e:
            raise RuntimeError(f"[understanding stage] {e}") from e

    def _run_ideation(self, u: UnderstandingResult) -> IdeationResult:
        """Stage 2 — Ideation: select patterns for the matched domains."""
        try:
            selected = select_patterns(u.scope, self._patterns, u.matched_domains)
            pattern_count = len(selected.get("universal", [])) + sum(
                len(p) for p in selected.get("domain_specific", {}).values()
            )
            return IdeationResult(
                understanding=u,
                selected_patterns=selected,
                pattern_count=pattern_count,
            )
        except Exception as e:
            raise RuntimeError(f"[ideation stage] {e}") from e

    def _run_rollout(self, i: IdeationResult) -> RolloutResult:
        """Stage 3 — Rollout: call the LLM with the constructed prompt."""
        try:
            u = i.understanding
            full_system, user_message = build_prompt(
                self._system_prompt,
                i.selected_patterns,
                u.scope,
                u.depth,
                u.threshold,
                u.context,
            )
            if self._provider is None:
                self._provider = get_provider(
                    provider=self.provider_name,
                    model=self.model_name,
                )
            response = self._provider.complete(full_system, user_message)
            return RolloutResult(ideation=i, raw_response=response.text)
        except RuntimeError:
            raise  # Already tagged by a nested stage call
        except Exception as e:
            raise RuntimeError(f"[rollout stage] {e}") from e

    def _run_judgment(self, r: RolloutResult, validate: bool = False) -> JudgmentResult:
        """Stage 4 — Judgment: parse risks and optionally validate them.

        When validate=True, a second LLM call filters hallucinations and
        duplicates. On any validation error, falls back to unvalidated risks.
        """
        try:
            response_text = r.raw_response
            validation_summary: str | None = None
            validated = False

            if validate:
                try:
                    validation_prompt = build_validation_prompt(
                        r.ideation.understanding.scope, response_text
                    )
                    validated_response = self._provider.complete(
                        VALIDATION_SYSTEM_PROMPT, validation_prompt
                    )
                    response_text = validated_response.text
                    validated = True
                    # Extract summary block appended by the validator
                    if "---" in response_text:
                        validation_summary = response_text.split("---")[-1].strip()
                except Exception:
                    pass  # Graceful fallback to unvalidated

            risks = self._parse_risks(response_text, r.ideation.understanding.matched_domains)
            return JudgmentResult(
                rollout=r,
                risks=[risk.to_dict() for risk in risks],
                validation_summary=validation_summary,
                validated=validated,
            )
        except RuntimeError:
            raise  # Already tagged
        except Exception as e:
            raise RuntimeError(f"[judgment stage] {e}") from e

    def _build_result(self, j: JudgmentResult, raw_response: str) -> AnalysisResult:
        """Construct the public AnalysisResult from a completed JudgmentResult."""
        risks = [
            Risk(
                severity=d["severity"],
                confidence=d["confidence"],
                scenario=d["scenario"],
                impact=d["impact"],
                domains=d.get("domains", []),
                title=d.get("title", ""),
            )
            for d in j.risks
        ]
        return AnalysisResult(
            scope=j.scope,
            risks=risks,
            matched_domains=j.matched_domains,
            pattern_count=j.pattern_count,
            raw_response=raw_response,
            depth=j.depth,
            threshold=j.threshold,
        )

    def _parse_risks(self, response_text: str, domains: list[str]) -> list[Risk]:
        """Parse LLM response into structured Risk objects.

        Extracts risks from markdown format:
        ### [SEVERITY] (confidence%)
        **[Title]**
        > What if [scenario]?
        - **Impact:** [impact text]
        - **Domain:** [domain]

        Args:
            response_text: Raw markdown response from LLM
            domains: Detected domains to associate with risks

        Returns:
            List of parsed Risk objects
        """
        risks = []

        # Uses pre-compiled module-level _HEADER_PATTERN, _IMPACT_PATTERN, _DOMAIN_PATTERN

        # Split by ## or ### headers (LLM may use either heading level)
        sections = re.split(r'\n#{2,3}\s+', '\n' + response_text)

        for section in sections[1:]:  # Skip first empty section
            section = section.strip()
            if not section:
                continue

            lines = section.split('\n')
            if not lines:
                continue

            # Parse severity and confidence from header (first line)
            header_match = _HEADER_PATTERN.match(lines[0])
            if not header_match:
                continue

            severity = header_match.group(1).upper()
            try:
                confidence = int(header_match.group(2))
            except (ValueError, IndexError):
                confidence = 50  # Default if parsing fails

            # Extract title (usually in bold on line after header)
            title = ""
            for line in lines[1:5]:  # Check first few lines after header
                line = line.strip()
                if line.startswith('**') and line.endswith('**'):
                    title = line.strip('*').strip()
                    break
                title_match = re.search(r'\*\*(.+?)\*\*', line)
                if title_match:
                    title = title_match.group(1).strip()
                    break

            # Extract scenario (starts with "What if" or in blockquote >)
            scenario = ""
            for line in lines:
                line_stripped = line.strip()
                # Check for blockquote
                if line_stripped.startswith('>'):
                    scenario = line_stripped[1:].strip()
                    break
                # Check for "What if" in regular text
                elif line_stripped.lower().startswith('what if'):
                    scenario = line_stripped
                    break

            # Extract impact (line starting with - **Impact:**)
            impact = ""
            for line in lines:
                impact_match = _IMPACT_PATTERN.search(line)
                if impact_match:
                    impact = impact_match.group(1).strip()
                    break

            # Extract domains from text or use matched domains
            risk_domains = []
            for line in lines:
                domain_match = _DOMAIN_PATTERN.search(line)
                if domain_match:
                    domain_text = domain_match.group(1).strip()
                    risk_domains = [d.strip() for d in domain_text.split(',')]
                    break

            if not risk_domains:
                risk_domains = domains.copy()

            # Only add if we have minimum required fields
            if scenario and impact:
                risks.append(
                    Risk(
                        severity=severity,
                        confidence=confidence,
                        scenario=scenario,
                        impact=impact,
                        domains=risk_domains,
                        title=title,
                    )
                )

        return risks
