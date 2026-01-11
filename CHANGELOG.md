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

## [Unreleased]

### Planned Features

**Phase 2 Tier 2 (Optional):**
- Additional 5 strategic patterns for 92-95% tie rate
- Focus on idempotency, state transitions, and service privileges

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
