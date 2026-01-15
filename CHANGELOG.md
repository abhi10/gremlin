# Changelog

All notable changes to Gremlin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-11

### Added

**Core Features:**
- Initial release of Gremlin CLI tool for exploratory QA
- 93 curated QA patterns across 11 domains
- Rich terminal output with severity-based risk scenarios
- Domain inference from user scope keywords
- Multiple output formats: rich (default), markdown, JSON
- Context support via direct string, file reference (`@path`), or stdin (`-`)
- Pattern browsing commands (`patterns list`, `patterns show <domain>`)

**Pattern Domains:**
- Universal patterns (31): Apply to all analyses
- Domain-specific patterns (62): auth, payments, file_upload, database, api, deployment, infrastructure, search, dependencies, frontend, security

**Evaluation Framework:**
- A/B testing framework comparing Gremlin vs baseline Claude
- 54 real-world test cases across 11 domains
- Multi-trial support with consistency metrics (pass@k)
- Parallel execution support with configurable workers
- Comprehensive JSON result output with winner determination
- Negative test case support for false positive detection

**Gremlin Agent (Claude Code Integration):**
- Code-review focused agent with 45-50 embedded patterns
- Optimized for PR review and line-specific risk identification
- Optional CLI integration for comprehensive analysis
- Separate pattern file (`patterns/code-review.yaml`)

### Changed

**Phase 1: Revised Strategy (Severity Hints)**
- Added severity hints to 5 critical patterns (Git hooks, infrastructure configs)
- Enhanced 2 existing patterns with impact descriptions
- Fixed infrastructure domain keyword matching
- **Result**: Improved from initial approach, validated severity guidance

**Phase 2 Tier 1: Strategic Pattern Expansion**
- Added 5 new high-impact patterns:
  - Type Assumptions on Parsed Data (Input Validation)
  - SSRF Vulnerabilities (Security - CRITICAL)
  - API Authentication Missing in Tests (Security - CRITICAL)
  - Missing Timeouts (External Dependencies - HIGH)
  - ReDoS Catastrophic Backtracking (Input Validation)
- Enhanced Memory Exhaustion pattern (MEDIUM → CRITICAL with specific impact)
- Removed 1 duplicate pattern
- **Result**: 90.7% tie rate with baseline Claude Sonnet 4 (98.1% win/tie rate)

### Performance

**Benchmark Results (54 real-world test cases):**
- **Tie Rate**: 90.7% (matches baseline Claude quality)
- **Win/Tie Rate**: 98.1%
- **Gremlin Wins**: 7.4% (patterns provide unique value)
- **Claude Wins**: 1.9% (minor category labeling differences)

**Pattern Effectiveness:**
- All CRITICAL patterns trigger at intended severity (SSRF 85%, Memory Exhaustion 90%)
- HIGH severity patterns validated (Missing Timeouts 80%)
- Consistent severity ratings across trials

**Key Achievement**: 90% reduction in quality gaps (19% → 1.9% Claude wins) through strategic pattern improvements.

### Documentation

- Comprehensive README with installation, usage, and examples
- Developer guide in CLAUDE.md
- Evaluation documentation in `evals/` directory:
  - Pattern analysis and selection methodology
  - Phase 1 and Phase 2 Tier 1 results with detailed investigations
  - Rate limit analysis and best practices
- Roadmap documenting future improvement paths

### Technical Details

**Dependencies:**
- anthropic>=0.40.0 (Claude API)
- click>=8.1.7 (CLI framework)
- pyyaml>=6.0.1 (Pattern loading)
- rich>=13.7.0 (Terminal output)
- jinja2>=3.1.3 (Prompt templating)

**Python Support:**
- Requires Python >=3.9

**Environment Variables:**
- `ANTHROPIC_API_KEY` (required): Anthropic API key
- `GREMLIN_MODEL` (optional): Override default Claude model

### Known Issues

**API Rate Limits:**
- Running 54+ cases in parallel with `--workers 5` can hit Anthropic rate limits:
  - 30,000 input tokens/minute
  - 8,000 output tokens/minute
- **Workaround**: Use `--workers 2` or run sequentially for large eval runs

**Category Labeling:**
- 1 eval case (1.9%) shows minor category labeling difference
- Risk quality is equivalent, only presentation differs
- Not a functional issue, tracking for future improvement

## [0.2.0] - 2026-01-15

### Added

**Programmatic API (Phase 1):**
- Python library interface via `from gremlin import Gremlin`
- `Gremlin` class with synchronous and asynchronous analysis methods
- `Risk` dataclass for structured risk findings (severity, confidence, scenario, impact, domains)
- `AnalysisResult` dataclass with comprehensive output formats:
  - `to_dict()` - Dictionary serialization
  - `to_json()` - JSON string output
  - `to_junit()` - JUnit XML for CI/CD integration
  - `format_for_llm()` - Concise format for LLM agent consumption
- Async support via `analyze_async()` for agent frameworks
- Risk severity checking methods: `has_critical_risks()`, `has_high_severity_risks()`
- Risk counting properties: `critical_count`, `high_count`, `medium_count`, `low_count`
- Provider-agnostic design (supports Anthropic, OpenAI, Ollama)
- Structured risk parsing from LLM markdown responses

**Testing:**
- Comprehensive test suite with 23 new tests for API functionality
- Unit tests for all dataclasses and methods
- Mock-based tests for isolation
- Integration tests with real API calls
- Async test coverage using anyio

### Changed

- Updated project description from "CLI tool" to "CLI + Python library"
- CLI is now a thin wrapper around the new programmatic API
- Version bumped to 0.2.0 (minor version for new feature)
- Development status upgraded from Alpha to Beta

### Documentation

- Extensive README updates with API documentation and usage examples
- Three use case examples: LLM agent tool, CI/CD integration, custom validation
- Updated CLAUDE.md with API architecture documentation
- API reference section with all classes and methods
- Async usage examples

### Technical Details

**New Dependencies:**
- pytest-asyncio>=0.21.0 (async test support)

**Python Support:**
- Python 3.10, 3.11, 3.12, 3.13 officially supported
- Added "Framework :: AsyncIO" classifier

**Architecture:**
- New `gremlin/api.py` module (478 lines)
- Public API exports in `gremlin/__init__.py`
- Clean separation between CLI and library interfaces
- Full backward compatibility with v0.1.0 CLI

## [Unreleased]

### Planned Features

**Phase 2: Framework Integrations:**
- Optional LangChain Tool wrapper
- CrewAI/AutoGen integration examples
- Direct usage patterns (framework-agnostic)

**Phase 3: CI/CD Mode:**
- Diff analysis (`--diff origin/main..HEAD`)
- SARIF output format for GitHub Code Scanning
- Exit codes for CI pipelines
- GitHub Actions integration

**Phase 4: IDE Extension:**
- VS Code extension (thin client using API)
- Inline risk feedback
- File save triggers

**Market Readiness:**
- PyPI publishing
- Example code directory
- Quickstart guide
- Demo assets (asciicast, screenshots)

**Pattern Enhancements:**
- Pattern quality scoring system
- Ablation studies for pattern effectiveness
- Quarterly sync between CLI and Agent pattern files

---

## Release Notes

### v0.1.0 - Initial Release

This is the first public release of Gremlin, featuring a production-ready exploratory QA tool with 93 curated patterns achieving 90.7% tie rate with state-of-the-art LLMs.

**Highlights:**
- 🎯 Pattern-based QA approach combining human expertise with LLM reasoning
- 🚀 90.7% quality parity with baseline Claude Sonnet 4
- 📊 Validated across 54 real-world code samples
- 🔧 Rich CLI with multiple output formats
- 🤖 Integrated Claude Code agent for PR reviews

**Getting Started:**
```bash
pip install gremlin-qa
export ANTHROPIC_API_KEY=sk-ant-...
gremlin review "checkout flow with Stripe integration"
```

See [README.md](README.md) for complete documentation.

---

[0.1.0]: https://github.com/abhi10/gremlin/releases/tag/v0.1.0
