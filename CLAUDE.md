# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gremlin is a pre-ship risk critic (CLI + Python library) that surfaces breaking risk scenarios before they reach production using:
- 107 curated QA patterns across 14 domains (domain-specific "what if?" questions)
- LLM reasoning via Anthropic Claude (applies patterns intelligently to user-provided scope)
- Rich terminal output (actionable risk scenarios with severity, confidence, and impact)

**Package**: `gremlin-critic` on PyPI (v0.2.0)
**Python**: >=3.10

**Three ways to use Gremlin:**
1. **CLI:** `gremlin review "checkout flow"` - Command-line interface
2. **API:** `from gremlin import Gremlin` - Python library for integrations
3. **Agent:** Claude Code agent for code-focused QA review (`plugins/gremlin/agents/gremlin.md`)

## CRITICAL: Always Create a New Branch First

**BEFORE starting ANY new requirement, feature, fix, or refactor:**

1. **ALWAYS create a new feature branch from main**
2. **NEVER commit directly to main**
3. **ALWAYS create a PR for review before merging**

```bash
# For EVERY new task, start with:
git checkout main
git pull origin main
git checkout -b <prefix>/descriptive-name

# Prefixes: feat/ fix/ refactor/ docs/ chore/
# Example: feat/add-custom-patterns
```

This rule applies to ALL changes. No exceptions.

## Development Commands

### Setup
```bash
# Create virtual environment and install in development mode
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Set API key (required for running)
export ANTHROPIC_API_KEY=sk-ant-...
```

### Testing
```bash
# Run all tests (50 tests across 6 files)
pytest

# Run specific test file
pytest tests/test_patterns.py

# Run with coverage
pytest --cov=gremlin

# Run only unit tests (no API key needed)
pytest -k "not Integration"
```

### Linting & Type Checking
```bash
# Check code (line-length=100, rules: E,F,I,N,W)
ruff check .

# Auto-fix issues
ruff check --fix .

# Type check
mypy gremlin/
```

### Running the Tool

**CLI Usage:**
```bash
# Basic review
gremlin review "checkout flow"

# With options
gremlin review "auth system" --depth deep --threshold 60 --output json

# With context (string, file reference, or stdin)
gremlin review "checkout" --context "Using Stripe, Next.js"
gremlin review "auth" --context @src/auth/login.ts
git diff | gremlin review "changes" --context -

# With custom patterns (merged with built-in)
gremlin review "checkout" --patterns @my-patterns.yaml

# With validation pass (second LLM call filters hallucinations)
gremlin review "checkout" --validate

# View patterns
gremlin patterns list
gremlin patterns show payments

# Learn from incidents
gremlin learn "Nav bar showed Login after successful auth" --domain auth --source myproject
```

**Programmatic API Usage:**
```python
from gremlin import Gremlin

# Basic usage
gremlin = Gremlin()
result = gremlin.analyze("checkout flow")

# Check results
if result.has_critical_risks():
    print(f"Found {result.critical_count} critical risks")

# Multiple output formats
json_output = result.to_json()
junit_xml = result.to_junit()
llm_format = result.format_for_llm()

# Async support
result = await gremlin.analyze_async("payment processing")
```

### Evaluation Framework
```bash
# Run A/B testing (Gremlin vs raw Claude)
./evals/run_eval.py --all --trials 1

# Parallel with safe worker count
./evals/run_eval.py --all --trials 1 --parallel --workers 2

# Run specific domain
./evals/run_eval.py evals/cases/real-world/infrastructure-*.yaml --trials 3

# Results are saved to evals/results/
```

## Architecture

### Core Flow
The application follows this pipeline:

**Entry Points:**
- **CLI:** `gremlin/cli.py` — Implements full pipeline independently (patterns, prompts, LLM call, rendering)
- **API:** `gremlin/api.py` — Programmatic interface (`Gremlin` class) with structured output

**Note:** The CLI and API both implement the analysis pipeline independently. They share the same core modules but CLI does NOT wrap `Gremlin.analyze()`. Changes to the pipeline need to be applied in both entry points.

**Analysis Pipeline (shared core modules):**

1. **Domain Inference** (`gremlin/core/inference.py`)
   - Matches scope keywords to pattern domains
   - Example: "checkout" → `payments` domain

2. **Pattern Selection** (`gremlin/core/patterns.py`)
   - Loads patterns from `gremlin/patterns/breaking.yaml` + incidents
   - Merges project-level patterns from `.gremlin/patterns.yaml` if present
   - Selects universal patterns + matched domain patterns

3. **Prompt Building** (`gremlin/core/prompts.py`)
   - Combines system prompt with selected patterns via YAML serialization
   - Adds user scope, depth, threshold, and optional context

4. **LLM Call** (`gremlin/llm/factory.py` + `gremlin/llm/providers/anthropic.py`)
   - Calls Anthropic API with constructed prompts
   - Currently only Anthropic provider is implemented (provider factory supports future additions)
   - Default model: `claude-sonnet-4-20250514` (override via `GREMLIN_MODEL` env var)
   - Default temperature: 1.0, max_tokens: 4096, timeout: 120s

5. **Response Processing:**
   - **API:** Parses markdown into structured `Risk` objects via regex, returns `AnalysisResult`
   - **CLI:** Renders raw markdown via `gremlin/output/renderer.py` (rich, markdown, or JSON)

6. **Optional Validation** (CLI only via `--validate` flag):
   - Second LLM pass using `gremlin/core/validator.py`
   - Checks relevance, specificity, duplicates, severity alignment
   - Not wired into the API — API users must validate separately

### Architecture Diagrams
- `docs/architecture.drawio` — Editable 2-tab diagram (high-level + data flow)
- `docs/architecture-high-level.png` — System layer overview
- `docs/architecture-data-flow.png` — 7-step pipeline visualization

## Gremlin Agent vs CLI Tool

### Gremlin CLI Tool
**Location**: `gremlin/` (Python package)
**Purpose**: Feature-scope QA analysis from PRD/specification
**Patterns**: 107 patterns in `gremlin/patterns/breaking.yaml` (7 universal categories, 14 domains)
**Usage**: `gremlin review "checkout flow"`

### Gremlin Agent
**Location**: `plugins/gremlin/agents/gremlin.md`
**Purpose**: Code-focused QA review in Claude Code sessions
**Patterns**: 65 code-review patterns in `gremlin/patterns/code-review.yaml` (5 universal categories, 10 domains)
**Usage**: Invoke agent during code review in Claude Code

### Integration
- Agent is 100% standalone but can optionally invoke CLI via `gremlin/integrations/agent_bridge.py`
- Agent patterns: code-centric (what could break in implementation)
- CLI patterns: feature-centric (what could break in user experience)
- Universal patterns duplicated in both for independence

### Pattern Files
- `gremlin/patterns/breaking.yaml` — CLI patterns (107 total across 14 domains)
- `gremlin/patterns/code-review.yaml` — Agent patterns (65 total across 10 domains)
- `gremlin/patterns/incidents/` — Patterns learned from real incidents via `gremlin learn`

### Key Design Patterns

**Pattern Structure** (`gremlin/patterns/breaking.yaml`):
- `universal`: Categories of patterns applied to every analysis
- `domain_specific`: Domain-keyed patterns with keywords for inference
- Each domain has `keywords` (for matching) and `patterns` (what-if questions)

**Context Resolution** (`gremlin/cli.py`):
- Direct string: `--context "Using Stripe"`
- File reference: `--context @path/to/file`
- Stdin pipe: `--context -` (reads from stdin if not TTY)

**Project-Level Patterns**:
- CLI checks `.gremlin/patterns.yaml` in the current working directory
- If found, patterns are merged with built-in patterns
- Allows teams to add project-specific risk patterns

## Important Files

### Core Package
- `gremlin/api.py`: Programmatic API — `Gremlin`, `Risk`, `AnalysisResult` classes
- `gremlin/cli.py`: CLI entry point — `review`, `patterns`, `learn` commands
- `gremlin/__init__.py`: Public exports (`Gremlin`, `Risk`, `AnalysisResult`, `__version__`)
- `gremlin/core/validator.py`: LLM-as-judge risk quality checker (CLI `--validate` only)
- `gremlin/core/patterns.py`: Pattern loading, merging, and selection
- `gremlin/core/prompts.py`: System prompt loading and prompt construction
- `gremlin/core/inference.py`: Domain keyword matching from scope
- `gremlin/llm/factory.py`: Provider factory and registry
- `gremlin/llm/providers/anthropic.py`: Anthropic Claude implementation
- `gremlin/llm/claude.py`: **DEPRECATED** — backward compat, no longer imported
- `gremlin/integrations/agent_bridge.py`: Agent-to-CLI bridge utilities
- `gremlin/output/renderer.py`: Rich, markdown, JSON output rendering

### Patterns & Prompts
- `gremlin/patterns/breaking.yaml`: 107 QA patterns (14 domains)
- `gremlin/patterns/code-review.yaml`: 65 code-review patterns (10 domains)
- `gremlin/patterns/incidents/`: Incident-learned patterns (populated by `gremlin learn`)
- `gremlin/prompts/system.md`: System prompt defining persona and output format

### Configuration & Docs
- `pyproject.toml`: Build config (hatchling), dependencies, ruff/pytest/mypy settings
- `.github/workflows/ci.yml`: CI pipeline — ruff + pytest + coverage on Python 3.10/3.11/3.12
- `ROADMAP.md`: Project roadmap and priorities
- `CHANGELOG.md`: Version history

### Tests
- `tests/` — 50 tests across 6 files
- Unit tests mock LLM providers; 2 integration tests require `ANTHROPIC_API_KEY`

### Eval Framework
- `evals/run_eval.py`: A/B testing runner (54 test cases: 7 curated + 47 real-world)
- `evals/cases/`: YAML test case definitions
- `evals/critiques/`: Manual quality assessments (httpx, pydantic, celery)
- `evals/results/`: Timestamped JSON results (gitignored)

## Environment Variables

- `ANTHROPIC_API_KEY` (required): Anthropic API key for LLM calls
- `GREMLIN_MODEL` (optional): Override default model (default: `claude-sonnet-4-20250514`)
- `GREMLIN_PROVIDER` (optional): Override LLM provider (default: `anthropic` — currently the only implemented provider)

## Adding New Pattern Domains

To add a new domain (e.g., "notifications"):

1. Edit `gremlin/patterns/breaking.yaml`:
   ```yaml
   domain_specific:
     notifications:
       keywords: [notification, push, email, sms, alert]
       patterns:
         - "What if notification sent twice due to retry?"
         - "What if user unsubscribed but still receives alerts?"
   ```

2. The domain is automatically detected via keyword matching in user scope
3. No code changes needed — patterns are loaded dynamically

To learn from incidents:
```bash
gremlin learn "Nav bar showed Login after successful auth" --domain auth --source myproject
```

## Testing Philosophy

- Unit tests mock LLM providers to test pattern loading, domain inference, prompt building, and risk parsing
- Integration tests (gated by `ANTHROPIC_API_KEY`) verify end-to-end API calls
- Eval framework provides systematic A/B testing comparing Gremlin vs raw Claude
- CI runs ruff + pytest on every push/PR to main

## Gotchas

- **CLI ≠ API wrapper**: `cli.py` reimplements the pipeline; it does NOT call `Gremlin.analyze()`. Changes must be applied to both.
- **Validator is CLI-only**: `gremlin/core/validator.py` is wired into `--validate` flag but not into `api.py`'s `analyze()` method.
- **Only Anthropic works**: `factory.py` has default model names for OpenAI/Ollama but no actual provider implementations.
- **`gremlin/llm/claude.py` is dead code**: Marked DEPRECATED, no longer imported. Use `gremlin.llm.factory.get_provider()` instead.
- **`docs/*` is gitignored**: `.gitignore` excludes `docs/*` except `quickstart.md`, `architecture.drawio`, and architecture PNGs. New docs files need explicit exceptions.
- **`temperature=1.0` default**: `LLMConfig` defaults to maximum sampling diversity.

## Git Workflow

**IMPORTANT: Always work on feature branches, never commit directly to main.**

### Branch Naming Convention
Use descriptive branch names with prefixes:
- `feat/` - New features (e.g., `feat/eval-multiple-trials`)
- `fix/` - Bug fixes (e.g., `fix/pattern-matching-edge-case`)
- `refactor/` - Code refactoring (e.g., `refactor/simplify-eval-runner`)
- `docs/` - Documentation (e.g., `docs/market-analysis`)
- `chore/` - Maintenance tasks (e.g., `chore/update-dependencies`)

### Workflow Steps
1. **Before starting work**: Create a new branch from main
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feat/your-feature-name
   ```

2. **During work**: Commit frequently with clear messages

3. **After completing**: Push branch and create PR
   ```bash
   git push -u origin feat/your-feature-name
   # Then create PR via GitHub
   ```

4. **Never**: Force push to main, commit directly to main, or skip PR review
