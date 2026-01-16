# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gremlin is an exploratory QA tool (CLI + Python library) that identifies risk scenarios in software features using:
- 93 curated QA patterns (domain-specific "what if?" questions)
- Claude's reasoning (applies patterns intelligently to user-provided scope)
- Rich terminal output (actionable risk scenarios)

**Two ways to use Gremlin:**
1. **CLI:** `gremlin review "checkout flow"` - Command-line interface
2. **API:** `from gremlin import Gremlin` - Python library for integrations

Users receive ranked risk scenarios with severity, confidence, and impact analysis.

## ⚠️ CRITICAL: Always Create a New Branch First

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

This rule applies to:
- ✅ New features and functionality
- ✅ Bug fixes and corrections
- ✅ Refactoring and code improvements
- ✅ Documentation updates
- ✅ Any change to the codebase

**Exception:** None. Always use a branch.

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
# Run all tests
pytest

# Run specific test file
pytest tests/test_patterns.py

# Run with coverage
pytest --cov=gremlin
```

### Linting
```bash
# Check code
ruff check .

# Auto-fix issues
ruff check --fix .
```

### Running the Tool

**CLI Usage:**
```bash
# Basic review
gremlin review "checkout flow"

# With options
gremlin review "auth system" --depth deep --threshold 60 --output json

# With context
gremlin review "checkout" --context "Using Stripe, Next.js"
gremlin review "auth" --context @src/auth/login.ts
git diff | gremlin review "changes" --context -

# View patterns
gremlin patterns list
gremlin patterns show payments
```

**Programmatic API Usage (New):**
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
# Run A/B testing evaluation comparing Gremlin vs raw Claude
./evals/run_eval.py

# Results are saved to evals/results/<timestamp>/
```

## Architecture

### Core Flow
The application follows this pipeline:

**Entry Points:**
- **CLI:** `gremlin/cli.py` - Parses command-line arguments
- **API:** `gremlin/api.py` - Programmatic interface (`Gremlin` class)

**Analysis Pipeline (used by both CLI and API):**

1. **Domain Inference** (`gremlin/core/inference.py`)
   - Matches scope keywords to pattern domains
   - Example: "checkout" → `payments` domain

2. **Pattern Selection** (`gremlin/core/patterns.py`)
   - Loads patterns from `patterns/breaking.yaml`
   - Selects universal patterns + matched domain patterns
   - Universal patterns always apply, domain-specific only when matched

3. **Prompt Building** (`gremlin/core/prompts.py`)
   - Combines system prompt (`prompts/system.md`) with selected patterns
   - Adds user scope, depth, threshold, and optional context
   - Creates structured prompt for Claude API

4. **LLM Call** (`gremlin/llm/factory.py` + `gremlin/llm/providers/`)
   - Calls LLM API with constructed prompts
   - Supports multiple providers: Anthropic (default), OpenAI, Ollama
   - Uses `claude-sonnet-4-20250514` by default (override via `GREMLIN_MODEL` env var)

5. **Response Processing:**
   - **API:** Returns structured `AnalysisResult` with `Risk` objects
   - **CLI:** Renders via `gremlin/output/renderer.py` (rich, markdown, or JSON)

## Gremlin Agent vs CLI Tool

The Gremlin project provides two complementary tools:

### Gremlin CLI Tool
**Location**: `gremlin/` (Python package)
**Purpose**: Feature-scope QA analysis from PRD/specification
**Patterns**: 72 patterns in `patterns/breaking.yaml`
**Usage**: `gremlin review "checkout flow"`

**When to use**:
- Analyzing features from PRD/design docs
- Pre-implementation risk assessment
- Comprehensive feature-scope analysis
- Sharing reports with stakeholders

### Gremlin Agent
**Location**: `plugins/gremlin/agents/gremlin.md`
**Purpose**: Code-focused QA review in Claude Code sessions
**Patterns**: 45-50 code-review patterns in `patterns/code-review.yaml`
**Usage**: Invoke agent during code review in Claude Code

**When to use**:
- PR review and code inspection
- Line-specific risk identification
- Implementation detail analysis
- Database, concurrency, and security pattern matching

### Integration
The agent can optionally invoke the CLI for enhanced analysis:
- Agent performs code-focused review (embedded patterns)
- If CLI installed, agent can run feature-scope analysis
- Combined analysis provides comprehensive coverage

### Pattern Files
- `patterns/breaking.yaml` - CLI patterns (72 total, feature-focused)
- `patterns/code-review.yaml` - Agent patterns (45-50 total, code-focused)
- Universal patterns duplicated in both for independence
- Quarterly sync process maintains alignment

### Key Design Patterns

**Pattern Structure** (`patterns/breaking.yaml`):
- `universal`: Categories of patterns applied to every analysis
- `domain_specific`: Domain-keyed patterns with keywords for inference
- Each domain has `keywords` (for matching) and `patterns` (what-if questions)

**Context Resolution** (cli.py:29-55):
- Direct string: `--context "Using Stripe"`
- File reference: `--context @path/to/file`
- Stdin pipe: `--context -` (reads from stdin if not TTY)

**Eval Framework** (`evals/run_eval.py`):
- A/B tests Gremlin (with patterns) vs raw Claude (no patterns)
- Uses dataclasses for eval cases, metrics, and results
- Extracts metrics by regex matching severity levels and "what if" counts
- Saves detailed JSON results with diff analysis

## Important Files

- `patterns/breaking.yaml`: 93 curated QA patterns organized by domain
- `prompts/system.md`: System prompt defining Gremlin's persona and output format
- `gremlin/api.py`: Programmatic API with `Gremlin`, `Risk`, and `AnalysisResult` classes
- `gremlin/cli.py`: CLI entry point (thin wrapper around api.py)
- `gremlin/__init__.py`: Public API exports (`Gremlin`, `Risk`, `AnalysisResult`)
- `tests/test_api.py`: Comprehensive API test suite (23 tests)
- `pyproject.toml`: Build configuration, dependencies, and tool settings

## Environment Variables

- `ANTHROPIC_API_KEY` (required): Anthropic API key
- `GREMLIN_MODEL` (optional): Override default Claude model

## Adding New Pattern Domains

To add a new domain (e.g., "notifications"):

1. Edit `patterns/breaking.yaml`:
   ```yaml
   domain_specific:
     notifications:
       keywords: [notification, push, email, sms, alert]
       patterns:
         - "What if notification sent twice due to retry?"
         - "What if user unsubscribed but still receives alerts?"
   ```

2. The domain is automatically detected via keyword matching in user scope
3. No code changes needed - patterns are loaded dynamically

## Testing Philosophy

- Unit tests focus on pattern loading, domain inference, and prompt building
- No LLM mocking - actual API calls are integration tests (use sparingly)
- Eval framework provides systematic A/B testing for quality assessment

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
