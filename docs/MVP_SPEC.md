# Gremlin MVP — Standalone QA Agent

> **Status:** Approved for MVP
> **Author:** Abhi
> **Date:** January 2025
> **Version:** 1.0
> **Parent:** Derived from Chakram.sh proposal (v0.2)

---

## Executive Summary

**Gremlin** is a standalone CLI tool that applies an "exploratory QA lens" to your code. It surfaces risk scenarios ("what if?") by combining curated breaking patterns with Claude's reasoning.

This is a **stripped-down MVP** focused on proving core value before building ecosystem features.

---

## 1. What We're Building

### One-liner

A CLI that answers: *"What could break in [feature X]?"* — using curated QA patterns + LLM reasoning.

### Core Insight

Generic "what could break?" questions to Claude yield generic answers. **The value is in curated, domain-specific patterns** that surface non-obvious risks.

---

## 2. Scope

### In Scope (MVP)

| Feature | Description |
|---------|-------------|
| `gremlin review "scope"` | Single command to analyze a feature/area |
| 50 curated patterns | 30 universal + 20 domain-specific |
| Domain inference | Auto-select relevant patterns from scope string |
| Markdown output | Risk scenarios with severity + confidence |

### Out of Scope (Deferred)

| Feature | Reason | Revisit |
|---------|--------|---------|
| `gremlin learn` | Validate `review` first | After 2 weeks usage |
| SQLite persistence | Manual usage first | After 5+ uses |
| Skills/marketplace | Ecosystem is premature | V2+ |
| Shared/community patterns | Prove local value first | V2+ |
| Vector search (Chroma) | 50 patterns fit in context | Never (probably) |
| Multiple agents | One agent, prove it works | V2+ |
| Web dashboard | CLI only | V2+ |

---

## 3. Architecture

### Project Structure

```
gremlin/
├── gremlin.py              # CLI entry point (~200 lines)
├── patterns/
│   └── breaking.yaml       # 50 curated QA patterns
├── prompts/
│   └── system.md           # Exploratory QA system prompt
├── pyproject.toml          # Dependencies
└── README.md
```

### Dependencies (Minimal)

```toml
[project]
name = "gremlin-qa"
version = "0.1.0"
dependencies = [
    "typer>=0.9.0",
    "rich>=13.0.0",
    "anthropic>=0.18.0",
    "pyyaml>=6.0",
]
```

### Data Flow

```
User runs: gremlin review "checkout flow"
    ↓
1. Parse scope string ("checkout flow")
    ↓
2. Infer domain → payments, e-commerce
    ↓
3. Select patterns: universal + domain-specific
    ↓
4. Build prompt: system.md + selected patterns + scope
    ↓
5. Call Claude API
    ↓
6. Output: Risk scenarios (markdown)
```

---

## 4. Patterns Strategy

### The 80/20 Split

| Type | Count | Purpose |
|------|-------|---------|
| Universal | ~30 | Always apply (input validation, concurrency, errors) |
| Domain-Specific | ~20 | High-value, non-obvious risks |
| Stack-Specific | 0 | Claude knows stacks; add via `learn` later |

### Pattern Structure

```yaml
# patterns/breaking.yaml

universal:
  - category: Input Validation
    patterns:
      - "What if input is empty/null/undefined?"
      - "What if input exceeds expected length?"
      - "What if input contains special characters or unicode?"
      - "What if input type doesn't match expectation?"

  - category: Concurrency
    patterns:
      - "What if two users perform this action simultaneously?"
      - "What if the same user triggers this twice rapidly?"
      - "What if a background job runs while user is mid-action?"

  - category: State & Data
    patterns:
      - "What if referenced data was deleted?"
      - "What if data changed between read and write?"
      - "What if cache is stale?"

  - category: External Dependencies
    patterns:
      - "What if the external API times out?"
      - "What if the external API returns unexpected schema?"
      - "What if the external API rate limits us?"

  - category: Error Paths
    patterns:
      - "What if this fails halfway through?"
      - "What if retry logic triggers duplicate actions?"
      - "What if the error message leaks sensitive info?"

domain_specific:
  payments:
    keywords: [checkout, payment, billing, subscription, refund, stripe, invoice]
    patterns:
      - "What if webhook arrives before local transaction commits?"
      - "What if user refreshes page during payment redirect?"
      - "What if partial refund exceeds captured amount?"
      - "What if currency conversion happens between quote and charge?"

  auth:
    keywords: [login, signup, authentication, session, token, oauth, password]
    patterns:
      - "What if token expires during a long-running operation?"
      - "What if user logs in on two devices simultaneously?"
      - "What if OAuth provider returns different email casing?"
      - "What if password reset link is used twice?"

  file_upload:
    keywords: [upload, file, attachment, image, document, s3, storage]
    patterns:
      - "What if upload is interrupted at 99%?"
      - "What if file extension doesn't match content type?"
      - "What if filename contains path traversal characters?"
      - "What if file size is reported incorrectly by client?"

  search:
    keywords: [search, query, filter, index, elasticsearch, algolia]
    patterns:
      - "What if search index is out of sync with database?"
      - "What if user searches while reindex is running?"
      - "What if search query triggers regex catastrophic backtracking?"
```

### Domain Inference (No Config Required)

```python
def infer_domains(scope: str) -> list[str]:
    """Infer relevant domains from scope string."""
    scope_lower = scope.lower()
    matched = []

    for domain, config in DOMAIN_PATTERNS.items():
        if any(kw in scope_lower for kw in config["keywords"]):
            matched.append(domain)

    return matched if matched else ["general"]
```

---

## 5. CLI Interface

### Commands

```bash
# Primary use case (MVP)
gremlin review "checkout flow"

# With options
gremlin review "auth system" --depth deep
gremlin review "file upload" --threshold 70
gremlin review "search" --output json

# Utility (MVP)
gremlin patterns list              # Show available patterns
gremlin patterns show payments     # Show domain patterns

# Future (post-MVP)
gremlin learn retro.md             # Ingest patterns from doc
gremlin status                     # Show project context
```

### Arguments for `gremlin review`

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `scope` | string | required | Feature/area to analyze |
| `--depth` | enum | `quick` | `quick` (faster) or `deep` (thorough) |
| `--threshold` | int | `80` | Confidence filter (0-100) |
| `--output` | enum | `rich` | `rich` (terminal), `md`, `json` |
| `--context` | path | none | Additional context file (post-MVP) |

### Output Format

```markdown
## Risk Scenarios for: checkout flow

### 🔴 Critical (90%+ confidence)

**1. Webhook Race Condition**
> What if the Stripe webhook arrives before the order record is committed?

- **Impact:** Payment captured but order not created; customer charged without record
- **Domain:** payments
- **Pattern:** webhook_race

### 🟠 High (80-89% confidence)

**2. Double Submit**
> What if user clicks "Pay" twice rapidly?

- **Impact:** Duplicate charges possible
- **Domain:** payments, concurrency
- **Pattern:** rapid_duplicate_action

### 🟡 Medium (70-79% confidence)
...
```

---

## 6. Implementation

### gremlin.py (Minimal)

```python
#!/usr/bin/env python3
"""Gremlin - Exploratory QA Agent"""

import typer
from pathlib import Path
from anthropic import Anthropic
from rich.console import Console
from rich.markdown import Markdown
import yaml

app = typer.Typer(help="Exploratory QA agent that surfaces risk scenarios")
console = Console()
client = Anthropic()

ROOT = Path(__file__).parent
PATTERNS_PATH = ROOT / "patterns" / "breaking.yaml"
PROMPT_PATH = ROOT / "prompts" / "system.md"


def load_patterns() -> dict:
    with open(PATTERNS_PATH) as f:
        return yaml.safe_load(f)


def load_system_prompt() -> str:
    with open(PROMPT_PATH) as f:
        return f.read()


def infer_domains(scope: str, patterns: dict) -> list[str]:
    """Infer relevant domains from scope string."""
    scope_lower = scope.lower()
    matched = []

    for domain, config in patterns.get("domain_specific", {}).items():
        keywords = config.get("keywords", [])
        if any(kw in scope_lower for kw in keywords):
            matched.append(domain)

    return matched


def select_patterns(scope: str, all_patterns: dict) -> dict:
    """Select relevant patterns based on scope."""
    selected = {
        "universal": all_patterns.get("universal", []),
        "domain": {}
    }

    domains = infer_domains(scope, all_patterns)
    for domain in domains:
        if domain in all_patterns.get("domain_specific", {}):
            selected["domain"][domain] = all_patterns["domain_specific"][domain]["patterns"]

    return selected


@app.command()
def review(
    scope: str = typer.Argument(..., help="Feature or area to analyze"),
    depth: str = typer.Option("quick", help="Analysis depth: quick or deep"),
    threshold: int = typer.Option(80, help="Confidence threshold (0-100)"),
    output: str = typer.Option("rich", help="Output format: rich, md, json"),
):
    """Analyze a feature/scope for QA risks."""

    # Load resources
    all_patterns = load_patterns()
    system_prompt = load_system_prompt()

    # Select relevant patterns
    selected = select_patterns(scope, all_patterns)
    patterns_yaml = yaml.dump(selected, default_flow_style=False)

    # Build full system prompt
    full_system = f"""{system_prompt}

## Available Breaking Patterns

{patterns_yaml}
"""

    # Build user message
    user_msg = f"""Analyze this scope for risks: **{scope}**

Depth: {depth}
Confidence threshold: Only include scenarios where you're >{threshold}% confident this could actually happen.

Apply the breaking patterns above. For each risk scenario:
1. State the "what if?" question
2. Explain the potential impact
3. Rate severity (critical/high/medium/low)
4. Provide your confidence percentage

Focus on non-obvious risks. Skip generic advice."""

    # Call Claude
    with console.status("[bold green]Analyzing risks..."):
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=full_system,
            messages=[{"role": "user", "content": user_msg}]
        )

    result = response.content[0].text

    # Output
    if output == "rich":
        console.print(Markdown(result))
    elif output == "md":
        print(result)
    elif output == "json":
        # TODO: Parse and structure as JSON
        print(result)


@app.command()
def patterns(
    action: str = typer.Argument("list", help="list or show"),
    domain: str = typer.Argument(None, help="Domain to show patterns for"),
):
    """List or show available patterns."""
    all_patterns = load_patterns()

    if action == "list":
        console.print("\n[bold]Universal Categories:[/bold]")
        for cat in all_patterns.get("universal", []):
            console.print(f"  • {cat['category']} ({len(cat['patterns'])} patterns)")

        console.print("\n[bold]Domain-Specific:[/bold]")
        for domain_name, config in all_patterns.get("domain_specific", {}).items():
            keywords = ", ".join(config.get("keywords", [])[:3])
            console.print(f"  • {domain_name} ({len(config['patterns'])} patterns) - triggers: {keywords}...")

    elif action == "show" and domain:
        if domain in all_patterns.get("domain_specific", {}):
            config = all_patterns["domain_specific"][domain]
            console.print(f"\n[bold]{domain} patterns:[/bold]")
            for p in config["patterns"]:
                console.print(f"  • {p}")
        else:
            console.print(f"[red]Domain '{domain}' not found[/red]")


if __name__ == "__main__":
    app()
```

### prompts/system.md

```markdown
# Gremlin — Exploratory QA Agent

You are Gremlin, an exploratory QA specialist. Your job is to think like a tester who wants to break things — not maliciously, but to find risks before users do.

## Your Mindset

- **Assume nothing works** until proven otherwise
- **Think adversarially** — what would a confused user do? A malicious actor?
- **Follow the data** — where does it flow? Where could it get corrupted?
- **Question timing** — what if things happen out of order?
- **Challenge assumptions** — what did the developer assume that might not hold?

## Output Guidelines

- Be specific, not generic. "Input validation" is useless. "What if email contains + character and breaks downstream parsing?" is useful.
- Focus on **scenarios**, not test cases. You identify risks; writing tests is someone else's job.
- Rank by actual likelihood and impact, not theoretical possibility.
- Skip obvious stuff the developer definitely considered.
- When in doubt, ask "would a senior QA engineer find this insight valuable?"

## Severity Levels

- **Critical:** Data loss, security breach, financial impact
- **High:** Feature broken for subset of users, poor UX, recovery needed
- **Medium:** Edge case failures, minor UX issues
- **Low:** Cosmetic, rare edge cases

Be the paranoid friend who asks "but what if...?" at the right moments.
```

---

## 7. Success Criteria

### MVP Definition of Done

- [ ] `gremlin review "X"` returns relevant risk scenarios
- [ ] Domain inference works (checkout → payments patterns)
- [ ] Output is actionable (not generic advice)
- [ ] 50 patterns curated (30 universal + 20 domain)
- [ ] Works on 3+ real projects (dogfooding)

### Quality Bar

| Metric | Target |
|--------|--------|
| Relevant scenarios per review | ≥3 |
| "I didn't think of that" moments | ≥1 per review |
| False positive rate | <30% |
| Time to result | <30s |

---

## 8. Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Week 1 | 3-4 days | Patterns curation (the hard part) |
| Week 1 | 1-2 days | CLI + prompt + integration |
| Week 2 | 5 days | Dogfooding on real projects |
| Week 3 | TBD | Iterate based on usage |

---

## 9. Open Questions (Resolved)

| Question | Decision |
|----------|----------|
| Generic or domain-specific patterns? | Both. 30 universal + 20 domain |
| Vector search for patterns? | No. 50 patterns fit in context |
| Separate repo or Kai? | **Separate repo** — proves standalone value |
| Stack-specific patterns? | Deferred. Claude knows stacks. Add `learn` later |

---

## 10. Future Roadmap (Post-MVP)

| Feature | Trigger to Build |
|---------|------------------|
| `gremlin learn` | After 2 weeks of manual usage |
| SQLite persistence | After 5+ reviews want history |
| More domains | User requests specific domains |
| Kai integration | If valuable, wrap as skill |
| `--context` flag | Need to pass design docs |

---

## Appendix: Why Standalone?

### Kai Already Has

- Agent composition (AgentFactory)
- Skill routing (SKILL.md)
- Memory/patterns (Data/ YAML)
- CLI integration (hooks)

### Why Not Use It?

1. **Validation speed** — Separate repo ships in 1 week vs 2-3 weeks
2. **Distribution** — `pip install gremlin-qa` vs "install Kai first"
3. **Focus** — Prove the patterns + prompt value without infrastructure
4. **Future flexibility** — Can wrap as Kai skill later if valuable

### Integration Path

If Gremlin proves valuable:
```
gremlin/           →    Packs/kai-qa-skill/
├── gremlin.py          ├── Tools/Gremlin.ts
├── patterns/           ├── Data/
└── prompts/            └── SKILL.md
```

The decoupling is clean. Build standalone, integrate later.
