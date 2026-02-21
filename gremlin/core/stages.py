"""Stage data classes for the Gremlin analysis pipeline.

Each dataclass represents the output artifact of one pipeline stage.
All are JSON-serializable for disk caching and inter-stage communication.

Stages in order:
    UnderstandingResult  ← infer_domains()
    IdeationResult       ← select_patterns()
    RolloutResult        ← LLM call (provider.complete)
    JudgmentResult       ← _parse_risks() + optional validator

Note: JudgmentResult stores risks as list[dict] to avoid a circular import
with gremlin.api (which owns the Risk dataclass). api.py converts dicts to
Risk objects at the boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_SCHEMA_VERSION = "1"


@dataclass(frozen=True)
class UnderstandingResult:
    """Output of the Understanding stage.

    Captures the resolved scope, matched domains, and analysis parameters
    before any pattern selection or LLM calls occur.
    """

    scope: str
    matched_domains: list[str]
    depth: str
    threshold: int
    context: str | None = None
    version: str = _SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "scope": self.scope,
            "matched_domains": self.matched_domains,
            "depth": self.depth,
            "threshold": self.threshold,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> UnderstandingResult:
        return cls(
            scope=d["scope"],
            matched_domains=d.get("matched_domains", []),
            depth=d.get("depth", "quick"),
            threshold=d.get("threshold", 80),
            context=d.get("context"),
            version=d.get("version", _SCHEMA_VERSION),
        )


@dataclass(frozen=True)
class IdeationResult:
    """Output of the Ideation stage.

    Captures which patterns were selected and from which domains,
    ready to be injected into the rollout prompt.
    """

    understanding: UnderstandingResult
    selected_patterns: dict[str, Any]   # {"universal": [...], "domain_specific": {...}}
    pattern_count: int
    version: str = _SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "understanding": self.understanding.to_dict(),
            "selected_patterns": self.selected_patterns,
            "pattern_count": self.pattern_count,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> IdeationResult:
        return cls(
            understanding=UnderstandingResult.from_dict(d["understanding"]),
            selected_patterns=d.get("selected_patterns", {}),
            pattern_count=d.get("pattern_count", 0),
            version=d.get("version", _SCHEMA_VERSION),
        )


@dataclass(frozen=True)
class RolloutResult:
    """Output of the Rollout stage.

    Contains the raw markdown response from the LLM before any parsing
    or validation.
    """

    ideation: IdeationResult
    raw_response: str
    version: str = _SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "ideation": self.ideation.to_dict(),
            "raw_response": self.raw_response,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RolloutResult:
        return cls(
            ideation=IdeationResult.from_dict(d["ideation"]),
            raw_response=d.get("raw_response", ""),
            version=d.get("version", _SCHEMA_VERSION),
        )


@dataclass(frozen=True)
class JudgmentResult:
    """Output of the Judgment stage.

    Stores risks as list[dict] (not list[Risk]) to avoid a circular import
    with gremlin.api. The Gremlin class converts dicts to Risk objects.

    validation_summary is populated only when validate=True was requested.
    """

    rollout: RolloutResult
    risks: list[dict[str, Any]]          # serialized Risk dicts
    validation_summary: str | None = None
    validated: bool = False
    version: str = _SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "rollout": self.rollout.to_dict(),
            "risks": self.risks,
            "validation_summary": self.validation_summary,
            "validated": self.validated,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> JudgmentResult:
        return cls(
            rollout=RolloutResult.from_dict(d["rollout"]),
            risks=d.get("risks", []),
            validation_summary=d.get("validation_summary"),
            validated=d.get("validated", False),
            version=d.get("version", _SCHEMA_VERSION),
        )

    @property
    def matched_domains(self) -> list[str]:
        """Convenience accessor for matched domains from understanding stage."""
        return self.rollout.ideation.understanding.matched_domains

    @property
    def scope(self) -> str:
        """Convenience accessor for scope from understanding stage."""
        return self.rollout.ideation.understanding.scope

    @property
    def pattern_count(self) -> int:
        """Convenience accessor for pattern count from ideation stage."""
        return self.rollout.ideation.pattern_count

    @property
    def depth(self) -> str:
        """Convenience accessor for depth from understanding stage."""
        return self.rollout.ideation.understanding.depth

    @property
    def threshold(self) -> int:
        """Convenience accessor for threshold from understanding stage."""
        return self.rollout.ideation.understanding.threshold
