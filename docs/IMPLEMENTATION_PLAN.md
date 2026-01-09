# Gremlin MVP — Implementation Plan

> **Status:** Ready for Implementation
> **Author:** Abhi
> **Date:** January 2026
> **Version:** 1.0

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture](#2-architecture)
3. [Use Cases](#3-use-cases)
4. [Acceptance Criteria](#4-acceptance-criteria)
5. [Phased Implementation Plan](#5-phased-implementation-plan)
6. [Tech Stack & Language Decision](#6-tech-stack--language-decision)
7. [Risk & Mitigation](#7-risk--mitigation)
8. [Success Metrics](#8-success-metrics)

---

## 1. Executive Summary

### What We're Building

**Gremlin** is a CLI tool that answers: *"What could break in [feature X]?"*

It combines:
- **50 curated QA patterns** (domain-specific "what if?" questions)
- **Claude's reasoning** (applies patterns intelligently to user's context)
- **Rich terminal output** (actionable risk scenarios)

### Core Value Proposition

| Without Gremlin | With Gremlin |
|-----------------|--------------|
| Generic "what could break?" yields generic answers | Domain-specific patterns surface non-obvious risks |
| Developer bias - you assume your code works | External QA lens challenges assumptions |
| QA happens after implementation | Risk identification during development |

### MVP Scope

| In Scope | Out of Scope |
|----------|--------------|
| `gremlin review "scope"` command | `gremlin learn` (pattern ingestion) |
| 50 curated patterns (12 domains) | SQLite persistence |
| Domain inference from scope | Vector search / Chroma |
| Rich terminal + Markdown output | Multiple agents |
| Claude API integration | Web dashboard |

---

## 2. Architecture

### 2.1 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER TERMINAL                                   │
│                                                                             │
│   $ gremlin review "checkout flow with Stripe integration"                  │
│                                                                             │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              GREMLIN CLI                                     │
│                           (Python + Typer)                                   │
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Argument  │    │   Domain    │    │   Pattern   │    │   Output    │  │
│  │   Parser    │───▶│   Inferrer  │───▶│   Selector  │───▶│   Renderer  │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                  │                  │                  │          │
│         │                  │                  │                  │          │
│         ▼                  ▼                  ▼                  ▼          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         PROMPT BUILDER                               │   │
│  │                                                                      │   │
│  │   system.md + selected_patterns + user_scope + depth + threshold    │   │
│  └─────────────────────────────────┬───────────────────────────────────┘   │
│                                    │                                        │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CLAUDE API                                        │
│                        (Anthropic SDK)                                       │
│                                                                             │
│   Model: claude-sonnet-4-20250514                                            │
│   Max Tokens: 4096                                                          │
│   Temperature: default                                                       │
│                                                                             │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RISK SCENARIOS                                     │
│                                                                             │
│   ## Risk Scenarios for: checkout flow                                      │
│                                                                             │
│   ### Critical (90%+ confidence)                                            │
│   **Webhook Race Condition**                                                │
│   > What if Stripe webhook arrives before order record commits?             │
│   - Impact: Payment captured but order not created                          │
│   - Domain: payments                                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GREMLIN COMPONENTS                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   CLI Layer     │     │  Core Logic     │     │   External      │
│                 │     │                 │     │                 │
│ ┌─────────────┐ │     │ ┌─────────────┐ │     │ ┌─────────────┐ │
│ │ typer app   │ │     │ │ domain      │ │     │ │ Claude API  │ │
│ │             │ │────▶│ │ inference   │ │────▶│ │             │ │
│ │ - review    │ │     │ └─────────────┘ │     │ └─────────────┘ │
│ │ - patterns  │ │     │                 │     │                 │
│ └─────────────┘ │     │ ┌─────────────┐ │     │ ┌─────────────┐ │
│                 │     │ │ pattern     │ │     │ │ File System │ │
│ ┌─────────────┐ │     │ │ selection   │ │     │ │             │ │
│ │ Rich        │ │◀────│ └─────────────┘ │◀────│ │ - patterns/ │ │
│ │ Console     │ │     │                 │     │ │ - prompts/  │ │
│ └─────────────┘ │     │ ┌─────────────┐ │     │ └─────────────┘ │
│                 │     │ │ prompt      │ │     │                 │
└─────────────────┘     │ │ builder     │ │     └─────────────────┘
                        │ └─────────────┘ │
                        │                 │
                        └─────────────────┘
```

### 2.3 Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW                                    │
└──────────────────────────────────────────────────────────────────────────┘

User Input                    Processing                         Output
──────────                    ──────────                         ──────

┌─────────────┐
│ scope:      │
│ "checkout   │──┐
│  flow"      │  │
└─────────────┘  │
                 │     ┌─────────────────────────────────────┐
┌─────────────┐  │     │          DOMAIN INFERENCE           │
│ --depth:    │  │     │                                     │
│ "deep"      │──┼────▶│  "checkout" ──▶ payments           │
└─────────────┘  │     │  "flow"     ──▶ (no match)         │
                 │     │                                     │
┌─────────────┐  │     │  Result: ["payments"]               │
│ --threshold │  │     └──────────────────┬──────────────────┘
│ 80          │──┘                        │
└─────────────┘                           ▼
                       ┌─────────────────────────────────────┐
                       │         PATTERN SELECTION           │
                       │                                     │
┌─────────────┐        │  Universal: 30 patterns (always)   │
│ patterns/   │        │  + payments: 8 patterns            │
│ breaking.   │───────▶│                                     │
│ yaml        │        │  Total: 38 patterns selected       │
└─────────────┘        └──────────────────┬──────────────────┘
                                          │
                                          ▼
                       ┌─────────────────────────────────────┐
                       │          PROMPT ASSEMBLY            │
┌─────────────┐        │                                     │
│ prompts/    │        │  ┌─────────────────────────────┐   │
│ system.md   │───────▶│  │ System: Gremlin persona     │   │
└─────────────┘        │  │ + Selected patterns (YAML)  │   │
                       │  │ + User scope + depth        │   │
                       │  │ + Threshold instructions    │   │
                       │  └─────────────────────────────┘   │
                       └──────────────────┬──────────────────┘
                                          │
                                          ▼
                       ┌─────────────────────────────────────┐
                       │           CLAUDE API                │
                       │                                     │
                       │   POST /v1/messages                 │
                       │   model: claude-sonnet-4-20250514    │
                       │   max_tokens: 4096                  │
                       └──────────────────┬──────────────────┘
                                          │
                                          ▼
                       ┌─────────────────────────────────────┐
                       │         OUTPUT RENDERING            │      ┌──────────┐
                       │                                     │      │ Terminal │
                       │  --output rich ──▶ Rich Markdown   │─────▶│ (color)  │
                       │  --output md   ──▶ Raw Markdown    │      └──────────┘
                       │  --output json ──▶ Structured JSON │      ┌──────────┐
                       │                                     │─────▶│ File     │
                       └─────────────────────────────────────┘      └──────────┘
```

### 2.4 File Structure

```
gremlin/
├── gremlin/
│   ├── __init__.py
│   ├── cli.py              # Typer CLI commands
│   ├── core/
│   │   ├── __init__.py
│   │   ├── inference.py    # Domain inference logic
│   │   ├── patterns.py     # Pattern loading & selection
│   │   └── prompts.py      # Prompt building
│   ├── llm/
│   │   ├── __init__.py
│   │   └── claude.py       # Claude API integration
│   └── output/
│       ├── __init__.py
│       └── renderer.py     # Rich/MD/JSON output
├── patterns/
│   └── breaking.yaml       # 50 curated QA patterns
├── prompts/
│   └── system.md           # Gremlin persona prompt
├── tests/
│   ├── __init__.py
│   ├── test_inference.py
│   ├── test_patterns.py
│   └── test_cli.py
├── pyproject.toml
├── README.md
└── .env.example
```

---

## 3. Use Cases

### 3.1 Primary Use Case: Feature Risk Review

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ UC-01: Review Feature for Risks                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Actor: Developer                                                            │
│ Trigger: Developer wants QA perspective on a feature before shipping        │
├─────────────────────────────────────────────────────────────────────────────┤
│ Preconditions:                                                              │
│ - ANTHROPIC_API_KEY environment variable is set                             │
│ - Gremlin is installed (pip install gremlin-qa)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Main Flow:                                                                  │
│ 1. Developer runs: gremlin review "checkout flow with Stripe"               │
│ 2. Gremlin parses scope string                                              │
│ 3. Gremlin infers domains: ["payments"]                                     │
│ 4. Gremlin selects patterns: universal + payments                           │
│ 5. Gremlin builds prompt with system.md + patterns + scope                  │
│ 6. Gremlin calls Claude API                                                 │
│ 7. Claude returns risk scenarios                                            │
│ 8. Gremlin renders output in terminal with Rich                             │
│ 9. Developer reviews scenarios and addresses high-risk items                │
├─────────────────────────────────────────────────────────────────────────────┤
│ Postconditions:                                                             │
│ - Developer has list of risk scenarios to consider                          │
│ - High-confidence risks are highlighted                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ Alternative Flows:                                                          │
│ A1. No domain matched:                                                      │
│     - Gremlin uses only universal patterns                                  │
│     - Output notes "No specific domain detected"                            │
│ A2. API error:                                                              │
│     - Gremlin shows friendly error message                                  │
│     - Suggests checking API key                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Use Case: Deep Analysis

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ UC-02: Deep Analysis with Lower Threshold                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ Actor: Developer                                                            │
│ Trigger: Developer wants thorough analysis before major release             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Main Flow:                                                                  │
│ 1. Developer runs: gremlin review "auth system" --depth deep --threshold 60 │
│ 2. Gremlin processes with extended analysis                                 │
│ 3. Claude provides more detailed scenarios (lower confidence included)      │
│ 4. Output includes medium-confidence risks (60-79%)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ Notes:                                                                      │
│ - --depth deep instructs Claude to be more thorough                         │
│ - --threshold 60 includes scenarios Claude is 60%+ confident about          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Use Case: List Available Patterns

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ UC-03: Explore Available Patterns                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ Actor: Developer                                                            │
│ Trigger: Developer wants to see what patterns Gremlin knows about           │
├─────────────────────────────────────────────────────────────────────────────┤
│ Main Flow:                                                                  │
│ 1. Developer runs: gremlin patterns list                                    │
│ 2. Gremlin displays all categories and domains                              │
│ 3. Developer runs: gremlin patterns show payments                           │
│ 4. Gremlin displays all patterns for payments domain                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ Output Example:                                                             │
│                                                                             │
│ Universal Categories:                                                       │
│   - Input Validation (4 patterns)                                           │
│   - Concurrency (4 patterns)                                                │
│   - State & Data (4 patterns)                                               │
│   ...                                                                       │
│                                                                             │
│ Domain-Specific:                                                            │
│   - auth (8 patterns) - triggers: login, token, session...                  │
│   - payments (8 patterns) - triggers: checkout, stripe, billing...          │
│   ...                                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.4 Use Case: Export to Markdown

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ UC-04: Export Risk Report                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ Actor: Developer / Tech Lead                                                │
│ Trigger: Need to share risk assessment with team or include in PR           │
├─────────────────────────────────────────────────────────────────────────────┤
│ Main Flow:                                                                  │
│ 1. Developer runs: gremlin review "new feature" --output md > risks.md      │
│ 2. Gremlin outputs raw markdown (no Rich formatting)                        │
│ 3. Developer attaches risks.md to PR or shares in Slack                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Acceptance Criteria

### 4.1 CLI Commands

#### AC-01: `gremlin review` Command

| ID | Criteria | Priority |
|----|----------|----------|
| AC-01.1 | `gremlin review "scope"` executes without error | Must |
| AC-01.2 | Scope string is required; shows error if missing | Must |
| AC-01.3 | `--depth` accepts `quick` or `deep` (default: `quick`) | Must |
| AC-01.4 | `--threshold` accepts 0-100 integer (default: `80`) | Must |
| AC-01.5 | `--output` accepts `rich`, `md`, `json` (default: `rich`) | Must |
| AC-01.6 | Shows spinner/status during API call | Should |
| AC-01.7 | Gracefully handles API errors with user-friendly message | Must |
| AC-01.8 | Respects `ANTHROPIC_API_KEY` environment variable | Must |

#### AC-02: `gremlin patterns` Command

| ID | Criteria | Priority |
|----|----------|----------|
| AC-02.1 | `gremlin patterns list` shows all categories and domains | Must |
| AC-02.2 | `gremlin patterns show <domain>` shows patterns for domain | Must |
| AC-02.3 | Shows error if domain not found | Must |
| AC-02.4 | Displays pattern count per category | Should |

### 4.2 Domain Inference

| ID | Criteria | Priority |
|----|----------|----------|
| AC-03.1 | "checkout" triggers `payments` domain | Must |
| AC-03.2 | "login" triggers `auth` domain | Must |
| AC-03.3 | "upload" triggers `file_upload` domain | Must |
| AC-03.4 | Multiple domains can be triggered from one scope | Must |
| AC-03.5 | Unknown scope uses only universal patterns | Must |
| AC-03.6 | Inference is case-insensitive | Must |

### 4.3 Pattern Selection

| ID | Criteria | Priority |
|----|----------|----------|
| AC-04.1 | Universal patterns always included | Must |
| AC-04.2 | Domain patterns added based on inference | Must |
| AC-04.3 | Patterns loaded from YAML file | Must |
| AC-04.4 | Invalid YAML shows helpful error | Must |

### 4.4 Output Quality

| ID | Criteria | Priority |
|----|----------|----------|
| AC-05.1 | Output contains at least 3 risk scenarios | Must |
| AC-05.2 | Each scenario has: question, impact, severity, confidence | Must |
| AC-05.3 | Scenarios filtered by threshold | Must |
| AC-05.4 | Rich output uses colors for severity levels | Should |
| AC-05.5 | Markdown output is valid markdown | Must |
| AC-05.6 | At least 1 "non-obvious" insight per review | Should |

### 4.5 Performance

| ID | Criteria | Priority |
|----|----------|----------|
| AC-06.1 | `--depth quick` completes in < 30 seconds | Must |
| AC-06.2 | `--depth deep` completes in < 2 minutes | Should |
| AC-06.3 | Pattern loading < 100ms | Should |

### 4.6 Error Handling

| ID | Criteria | Priority |
|----|----------|----------|
| AC-07.1 | Missing API key shows: "Set ANTHROPIC_API_KEY env var" | Must |
| AC-07.2 | API rate limit shows retry suggestion | Should |
| AC-07.3 | Network error shows "Check your connection" | Must |
| AC-07.4 | Invalid arguments show usage help | Must |

---

## 5. Phased Implementation Plan

### Phase Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         IMPLEMENTATION PHASES                                │
└─────────────────────────────────────────────────────────────────────────────┘

Phase 1          Phase 2          Phase 3          Phase 4          Phase 5
─────────        ─────────        ─────────        ─────────        ─────────
Project          Pattern          Claude           Output &         Testing &
Setup            System           Integration      Polish           Release

Days 1-2         Days 3-4         Days 5-6         Day 7            Days 8-10

┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐
│ pyproj  │      │ YAML    │      │ API     │      │ Rich    │      │ Unit    │
│ CLI     │─────▶│ Schema  │─────▶│ Client  │─────▶│ Output  │─────▶│ Tests   │
│ Typer   │      │ Domain  │      │ Prompts │      │ Errors  │      │ Dogfood │
└─────────┘      │ Infer   │      │ Build   │      │ Help    │      │ PyPI    │
                 └─────────┘      └─────────┘      └─────────┘      └─────────┘
```

---

### Phase 1: Project Setup (Days 1-2)

#### Objectives
- Initialize Python project structure
- Set up CLI framework with Typer
- Configure development environment

#### Tasks

| Task | Description | Deliverable |
|------|-------------|-------------|
| 1.1 | Create project directory structure | `gremlin/` folder structure |
| 1.2 | Initialize `pyproject.toml` with dependencies | Working `pip install -e .` |
| 1.3 | Create Typer CLI skeleton | `gremlin --help` works |
| 1.4 | Add `review` command stub | `gremlin review "x"` prints scope |
| 1.5 | Add `patterns` command stub | `gremlin patterns list` prints TODO |
| 1.6 | Create `.env.example` | API key template |
| 1.7 | Set up basic README | Installation instructions |

#### Acceptance Criteria
- [ ] `pip install -e .` installs gremlin
- [ ] `gremlin --help` shows available commands
- [ ] `gremlin review "test"` runs without error (prints stub)
- [ ] Project structure matches architecture spec

#### Dependencies
```toml
[project]
name = "gremlin-qa"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "typer>=0.9.0",
    "rich>=13.0.0",
    "anthropic>=0.18.0",
    "pyyaml>=6.0",
]

[project.scripts]
gremlin = "gremlin.cli:app"
```

---

### Phase 2: Pattern System (Days 3-4)

#### Objectives
- Create pattern YAML schema
- Implement domain inference
- Build pattern selection logic

#### Tasks

| Task | Description | Deliverable |
|------|-------------|-------------|
| 2.1 | Define YAML schema for patterns | `patterns/breaking.yaml` structure |
| 2.2 | Create 30 universal patterns | Universal categories populated |
| 2.3 | Create 20 domain patterns (from braindump) | Domain sections populated |
| 2.4 | Implement `load_patterns()` | Patterns loaded from YAML |
| 2.5 | Implement `infer_domains()` | Domain detection from scope |
| 2.6 | Implement `select_patterns()` | Universal + domain patterns |
| 2.7 | Wire up `gremlin patterns list` | Shows categories/domains |
| 2.8 | Wire up `gremlin patterns show` | Shows patterns for domain |

#### Pattern YAML Schema

```yaml
# patterns/breaking.yaml

universal:
  - category: Input Validation
    patterns:
      - "What if input is empty/null/undefined?"
      - "What if input exceeds expected length?"
      # ... more patterns

domain_specific:
  auth:
    keywords: [login, auth, token, session, jwt, oauth, password]
    patterns:
      - "What if different components use different auth providers?"
      - "What if user's permissions are revoked but JWT is still valid?"
      # ... more patterns

  payments:
    keywords: [checkout, payment, billing, stripe, subscription]
    patterns:
      - "What if webhook arrives before transaction commits?"
      # ... more patterns
```

#### Acceptance Criteria
- [ ] YAML loads without error
- [ ] `infer_domains("checkout flow")` returns `["payments"]`
- [ ] `infer_domains("login system")` returns `["auth"]`
- [ ] `infer_domains("random thing")` returns `[]`
- [ ] `select_patterns()` includes universal + matched domains
- [ ] `gremlin patterns list` shows all 12 domains
- [ ] `gremlin patterns show auth` shows 8 auth patterns

---

### Phase 3: Claude Integration (Days 5-6)

#### Objectives
- Integrate Anthropic SDK
- Build prompt assembly
- Implement API call with error handling

#### Tasks

| Task | Description | Deliverable |
|------|-------------|-------------|
| 3.1 | Create `prompts/system.md` | Gremlin persona prompt |
| 3.2 | Implement `build_prompt()` | Assembles system + patterns + scope |
| 3.3 | Implement Claude API client | `call_claude()` function |
| 3.4 | Add API key validation | Check env var on startup |
| 3.5 | Add error handling | Graceful API error messages |
| 3.6 | Wire up `gremlin review` | End-to-end working |
| 3.7 | Implement `--depth` logic | Quick vs deep prompts |
| 3.8 | Implement `--threshold` logic | Confidence filtering |

#### System Prompt (prompts/system.md)

```markdown
# Gremlin — Exploratory QA Agent

You are Gremlin, an exploratory QA specialist. Your job is to think like
a tester who wants to break things — not maliciously, but to find risks
before users do.

## Your Mindset

- **Assume nothing works** until proven otherwise
- **Think adversarially** — what would a confused user do? A malicious actor?
- **Follow the data** — where does it flow? Where could it get corrupted?
- **Question timing** — what if things happen out of order?
- **Challenge assumptions** — what did the developer assume that might not hold?

## Output Guidelines

- Be specific, not generic
- Focus on **scenarios**, not test cases
- Rank by actual likelihood and impact
- Skip obvious stuff the developer definitely considered

## Output Format

For each risk scenario, provide:
1. **What if:** The scenario question
2. **Impact:** What breaks and business consequence
3. **Severity:** Critical / High / Medium / Low
4. **Confidence:** Your confidence percentage (0-100)
5. **Domain:** Which pattern domain this relates to

## Severity Levels

- **Critical:** Data loss, security breach, financial impact
- **High:** Feature broken for subset of users, poor UX, recovery needed
- **Medium:** Edge case failures, minor UX issues
- **Low:** Cosmetic, rare edge cases
```

#### Acceptance Criteria
- [ ] Missing API key shows clear error message
- [ ] `gremlin review "checkout"` returns risk scenarios
- [ ] Output includes scenarios with severity and confidence
- [ ] `--depth deep` produces more detailed output
- [ ] `--threshold 60` includes lower confidence scenarios
- [ ] API errors show user-friendly messages

---

### Phase 4: Output & Polish (Day 7)

#### Objectives
- Implement Rich terminal output
- Add Markdown and JSON output
- Polish error messages and help text

#### Tasks

| Task | Description | Deliverable |
|------|-------------|-------------|
| 4.1 | Implement Rich output renderer | Colored, formatted terminal output |
| 4.2 | Add severity color coding | Critical=red, High=orange, etc. |
| 4.3 | Implement Markdown output | `--output md` works |
| 4.4 | Implement JSON output (basic) | `--output json` works |
| 4.5 | Add loading spinner | Shows during API call |
| 4.6 | Polish help text | All commands have good help |
| 4.7 | Add version command | `gremlin --version` |
| 4.8 | Update README | Full usage documentation |

#### Output Example (Rich)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Risk Scenarios for: checkout flow with Stripe                               │
└─────────────────────────────────────────────────────────────────────────────┘

🔴 CRITICAL (95% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Webhook Race Condition

  What if the Stripe webhook arrives before the order record is committed
  to the database?

  Impact: Payment is captured but order is not created. Customer is charged
          but has no record of purchase. Requires manual reconciliation.

  Domain: payments

🟠 HIGH (87% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Double Submit on Payment Button

  What if the user clicks "Pay Now" twice rapidly before the first request
  completes?

  Impact: Potential duplicate charges. Customer charged twice for single
          order.

  Domain: payments, concurrency
```

#### Acceptance Criteria
- [ ] Rich output has colored severity levels
- [ ] `--output md` produces valid markdown
- [ ] `--output json` produces valid JSON
- [ ] Spinner shows during API call
- [ ] Help text is clear and complete
- [ ] `gremlin --version` shows version

---

### Phase 5: Testing & Release (Days 8-10)

#### Objectives
- Write unit tests
- Dogfood on real projects
- Publish to PyPI

#### Tasks

| Task | Description | Deliverable |
|------|-------------|-------------|
| 5.1 | Write tests for domain inference | `test_inference.py` |
| 5.2 | Write tests for pattern selection | `test_patterns.py` |
| 5.3 | Write tests for CLI commands | `test_cli.py` |
| 5.4 | Dogfood on Chitram project | Real-world validation |
| 5.5 | Dogfood on 2 other projects | Cross-project validation |
| 5.6 | Fix issues from dogfooding | Bug fixes |
| 5.7 | Prepare PyPI package | `pyproject.toml` metadata |
| 5.8 | Publish to PyPI | `pip install gremlin-qa` works |
| 5.9 | Create release notes | CHANGELOG.md |

#### Test Cases

```python
# test_inference.py

def test_infer_payments_domain():
    assert "payments" in infer_domains("checkout flow")
    assert "payments" in infer_domains("Stripe integration")
    assert "payments" in infer_domains("billing system")

def test_infer_auth_domain():
    assert "auth" in infer_domains("login page")
    assert "auth" in infer_domains("JWT token handling")
    assert "auth" in infer_domains("OAuth integration")

def test_infer_multiple_domains():
    domains = infer_domains("checkout with user authentication")
    assert "payments" in domains
    assert "auth" in domains

def test_infer_no_domain():
    assert infer_domains("random feature") == []

def test_inference_case_insensitive():
    assert infer_domains("LOGIN") == infer_domains("login")
```

#### Acceptance Criteria
- [ ] All unit tests pass
- [ ] Dogfooding produces ≥3 relevant scenarios per review
- [ ] At least 1 "I didn't think of that" moment per project
- [ ] False positive rate < 30%
- [ ] Package published to PyPI
- [ ] `pip install gremlin-qa` works on clean machine

---

## 6. Tech Stack & Language Decision

### 6.1 Why Python? (vs Go, Rust, TypeScript)

#### Decision: **Python** for MVP

| Factor | Python | Go | Rust | TypeScript |
|--------|--------|-----|------|------------|
| **Time to MVP** | 1-2 weeks | 2-3 weeks | 3-4 weeks | 1-2 weeks |
| **LLM SDK maturity** | Excellent (official Anthropic SDK) | Good (community) | Limited | Good |
| **CLI libraries** | Typer (excellent) | Cobra (excellent) | Clap (good) | Commander (good) |
| **Rich terminal UI** | Rich (best-in-class) | Limited options | Limited | Ink (React-based) |
| **Distribution** | pip install | Single binary | Single binary | npm/npx |
| **Your familiarity** | High | Medium | Low | High |

#### Detailed Analysis

**Python Pros:**
```
+ Fastest path to working MVP (your primary goal)
+ Official Anthropic SDK with best documentation
+ Rich library = beautiful terminal output with minimal effort
+ Typer = type-safe CLI with auto-generated help
+ Easy to iterate on prompts and patterns
+ Most LLM examples/tutorials are in Python
+ pip install works for your target audience (developers)
```

**Python Cons:**
```
- Requires Python runtime installed
- Slower startup time (~200ms vs ~10ms for Go)
- Dependency management can be messy
- No single binary distribution
```

**Go Would Be Better If:**
```
- You needed single-binary distribution (no runtime)
- Startup time was critical (it's not for this use case)
- You were building a long-running service
- You wanted to distribute to non-developers
```

**Rust Would Be Better If:**
```
- Performance was critical (it's not - we're waiting on API calls)
- Memory safety was paramount (not for a CLI tool)
- You wanted the smallest possible binary
- You had more time and Rust experience
```

**TypeScript Would Be Better If:**
```
- You were building a VS Code extension
- You wanted to share code with a web frontend
- Your team was JS-heavy
```

#### The Real Answer: **It Doesn't Matter Much for MVP**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        WHERE TIME IS SPENT                                   │
└─────────────────────────────────────────────────────────────────────────────┘

User runs command ──▶ Parse args ──▶ Load YAML ──▶ Call Claude ──▶ Render output
                      ~10ms          ~50ms         ~5-20 sec       ~100ms

                                                   ▲
                                                   │
                                            99% of time is HERE
                                            (waiting for Claude API)

Language choice affects: ~160ms
API call takes: ~5,000-20,000ms

Conclusion: Language performance is irrelevant for this tool.
```

#### Decision Matrix

| Criteria | Weight | Python | Go | Rust |
|----------|--------|--------|-----|------|
| Time to MVP | 40% | 10 | 7 | 5 |
| LLM ecosystem | 25% | 10 | 7 | 5 |
| Terminal UI | 15% | 10 | 6 | 6 |
| Distribution | 10% | 6 | 10 | 10 |
| Your familiarity | 10% | 9 | 6 | 4 |
| **Weighted Score** | | **9.35** | **7.05** | **5.55** |

#### When to Reconsider

Consider **rewriting in Go** if:
- [ ] MVP is validated and you want wider distribution
- [ ] Users complain about Python dependency
- [ ] You want to embed in other tools
- [ ] You're building the larger Chakram ecosystem

The beauty of this architecture: **Core logic is simple enough to port.** The value is in the patterns and prompts, not the code.

---

### 6.2 Tech Stack Summary

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Language | Python 3.10+ | Fastest MVP, best LLM ecosystem |
| CLI Framework | Typer | Type-safe, auto-help, clean API |
| Terminal UI | Rich | Best-in-class formatting, colors, tables |
| LLM | Claude API (Sonnet) | Strong reasoning, follows instructions well |
| Config | PyYAML | Human-readable pattern storage |
| HTTP | Anthropic SDK | Official SDK, handles auth/retries |
| Testing | pytest | Standard, simple |
| Packaging | pyproject.toml | Modern Python packaging |

### 6.3 Version Requirements

```
Python >= 3.10
typer >= 0.9.0
rich >= 13.0.0
anthropic >= 0.18.0
pyyaml >= 6.0
pytest >= 7.0.0 (dev)
```

### 6.4 Distribution Strategy

**MVP (Python):**
```bash
pip install gremlin-qa
```

**Future (if needed):**
```bash
# Option A: PyInstaller single binary
./gremlin-linux-amd64

# Option B: Go rewrite
brew install gremlin-qa

# Option C: Docker
docker run --rm -e ANTHROPIC_API_KEY gremlin-qa review "checkout"
```

---

## 7. Risk & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Claude generates generic scenarios | Medium | High | Strong system prompt + curated patterns |
| Domain inference misses context | Medium | Medium | Expand keywords, add fallback to universal |
| API costs too high | Low | Medium | Use Sonnet (not Opus), cache common queries |
| Pattern quality varies | Medium | Medium | Curate from real incidents, iterate based on feedback |
| Output too verbose | Low | Low | Threshold filtering, summary mode option |

---

## 8. Success Metrics

### MVP Definition of Done

- [ ] `gremlin review "X"` returns relevant risk scenarios
- [ ] Domain inference works (checkout → payments patterns)
- [ ] Output is actionable (not generic advice)
- [ ] 50 patterns curated (30 universal + 20 domain)
- [ ] Works on 3+ real projects (dogfooding)
- [ ] Published to PyPI

### Quality Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Relevant scenarios per review | ≥ 3 | Manual review |
| "I didn't think of that" moments | ≥ 1 per review | User feedback |
| False positive rate | < 30% | Manual assessment |
| Time to result (quick) | < 30s | CLI timing |
| Time to result (deep) | < 2min | CLI timing |

---

## Appendix A: Command Reference

```bash
# Primary command
gremlin review <scope> [OPTIONS]

Arguments:
  scope         Feature or area to analyze (required)

Options:
  --depth       Analysis depth: quick or deep (default: quick)
  --threshold   Confidence filter 0-100 (default: 80)
  --output      Output format: rich, md, json (default: rich)
  --help        Show help message

# Pattern exploration
gremlin patterns list              # Show all categories/domains
gremlin patterns show <domain>     # Show patterns for domain

# Utility
gremlin --version                  # Show version
gremlin --help                     # Show help
```

## Appendix B: Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API key |
| `GREMLIN_MODEL` | No | Model override (default: claude-sonnet-4-20250514) |
| `GREMLIN_DEBUG` | No | Enable debug logging |

---

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| Jan 2026 | 1.0 | Initial implementation plan | Abhi |
