# Gremlin

> Pre-ship risk critic — surfaces what could break before it reaches production

[![PyPI](https://img.shields.io/pypi/v/gremlin-critic)](https://pypi.org/project/gremlin-critic/)
[![CI](https://github.com/abhi10/gremlin/actions/workflows/ci.yml/badge.svg)](https://github.com/abhi10/gremlin/actions/workflows/ci.yml)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Risk%20Dashboard-6366F1?style=flat-square)](https://abhi10.github.io/gremlin/)

Feed Gremlin a feature spec, PR diff, or plain English — it critiques it for blind spots using **107 curated "what if?" patterns** across 14 domains, applied by Claude.

```bash
pip install gremlin-critic
gremlin review "checkout flow with Stripe"
```

```
🔴 CRITICAL (95%) — Webhook Race Condition
   What if the Stripe webhook arrives before the order record is committed?
   Impact: Payment captured but order not created.

🟠 HIGH (87%) — Double Submit on Payment Button
   What if the user clicks "Pay Now" twice rapidly?
   Impact: Potential duplicate charges.
```

---

## Three ways to use it

### 1. CLI

```bash
# Review a feature
gremlin review "checkout flow"

# With context (diff, file, or string)
git diff | gremlin review "my changes" --context -
gremlin review "auth system" --context @src/auth/login.py

# Deep analysis, lower confidence threshold
gremlin review "payment refunds" --depth deep --threshold 60

# Learn from incidents
gremlin learn "Nav showed Login after auth" --domain auth --source prod
```

#### Pipeline stage commands (v0.3)

Run each analysis stage independently — useful for caching, debugging, or building custom pipelines:

```bash
# Stage 1 — infer domains, write understanding.json (no LLM call)
gremlin understand "checkout flow"

# Stage 2 — select patterns, write scenarios.json (no LLM call)
gremlin ideate

# Stage 3 — call LLM, write results.json
gremlin rollout

# Stage 4 — parse + score risks, write scores.json
gremlin judge

# With optional validation pass
gremlin judge --validate

# Custom run directory (default: .gremlin/run/)
gremlin understand "auth" --run-dir /tmp/my-run
gremlin ideate --run-dir /tmp/my-run
gremlin rollout --run-dir /tmp/my-run
gremlin judge --run-dir /tmp/my-run
```

Each stage reads the previous stage's artifact and writes its own — `understanding.json` → `scenarios.json` → `results.json` → `scores.json`.

### 2. GitHub Action

Add to any repo — Gremlin posts a risk report on every PR automatically.

```yaml
# .github/workflows/gremlin-review.yml
name: Gremlin Risk Review
on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install gremlin-critic
      - run: git diff origin/${{ github.base_ref }}...HEAD > /tmp/pr-diff.txt
      - run: |
          python3 .github/scripts/gremlin_analyze.py \
            "${{ github.event.pull_request.title }}" \
            /tmp/pr-diff.txt /tmp/gremlin-report.json
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      - uses: actions/github-script@v7
        with:
          script: |
            const data = JSON.parse(require('fs').readFileSync('/tmp/gremlin-report.json','utf8'));
            const risks = data.risks || [];
            const s = data.summary || {};
            const body = risks.length === 0
              ? '## Gremlin Risk Review\n\nNo risks above threshold.'
              : `## Gremlin Risk Review\n\n**${risks.length} risk(s)** — 🔴 ${s.critical||0} critical · 🟠 ${s.high||0} high · 🟡 ${s.medium||0} medium\n\n` +
                risks.map(r => `### ${r.severity}: ${r.title||r.scenario}\n**Confidence:** ${r.confidence}%\n\n${r.impact}`).join('\n\n---\n\n');
            github.rest.issues.createComment({issue_number: context.issue.number, owner: context.repo.owner, repo: context.repo.repo, body});
```

Set `ANTHROPIC_API_KEY` as a repository secret (Settings → Secrets → Actions). See [the full script](.github/scripts/gremlin_analyze.py) used in this repo.

### 3. Python API

```python
from gremlin import Gremlin

g = Gremlin()
result = g.analyze("checkout flow", context="Using Stripe + Next.js")

# Check severity
if result.has_critical_risks():
    print(f"{result.critical_count} critical risks found")

# Output formats
result.to_json()         # JSON string
result.to_junit()        # JUnit XML for CI
result.format_for_llm()  # Concise format for agents

# Async
result = await g.analyze_async("payment processing")

# Block CI on critical risks
if result.has_critical_risks():
    sys.exit(1)
```

---

## Risk Dashboard

Live visualization of Gremlin results applied to open-source projects — **[abhi10.github.io/gremlin](https://abhi10.github.io/gremlin/)**

- Heatmap · severity donut · domain bar chart · filterable risk table
- Applied to [celery](https://github.com/celery/celery), [pydantic](https://github.com/pydantic/pydantic), and more

---

## Pattern Domains

107 patterns across 14 domains — universal patterns run on every analysis, domain patterns trigger by keyword match:

| Domain | Keywords |
|--------|----------|
| `payments` | checkout, stripe, billing, refund |
| `auth` | login, session, token, oauth |
| `database` | query, migration, transaction |
| `concurrency` | async, queue, race, lock |
| `infrastructure` | deploy, config, cert, secret |
| `file_upload` | upload, image, file, cdn |
| `api` | endpoint, rate limit, webhook |
| + 7 more | ... |

### Custom patterns

```yaml
# .gremlin/patterns.yaml — auto-loaded per project
domain_specific:
  image_processing:
    keywords: [image, resize, cdn]
    patterns:
      - "What if EXIF rotation is ignored during resize?"
```

---

## Performance

**90.7% tie rate** vs. baseline Claude Sonnet across 54 real-world test cases — patterns match raw LLM quality while adding domain-specific coverage.

| Metric | Result |
|--------|--------|
| Win / Tie Rate | 98.1% |
| Gremlin Wins | 7.4% — patterns caught risks Claude missed |
| Pattern Count | 107 across 14 domains |

---

## Installation

```bash
pip install gremlin-critic
export ANTHROPIC_API_KEY=sk-ant-...
```

**Supports:** Anthropic (default) · OpenAI · Ollama (local, no API key needed)

```python
g = Gremlin(provider="ollama", model="llama3")  # fully local
```

**For development:**
```bash
git clone https://github.com/abhi10/gremlin.git
pip install -e ".[dev]"
pytest
```

---

## Commands

| Command | Description |
|---------|-------------|
| `gremlin review "scope"` | Full pipeline in one command |
| `gremlin review "scope" --context @file` | With file context |
| `git diff \| gremlin review "changes" --context -` | With diff via stdin |
| `gremlin patterns list` | Show all pattern domains |
| `gremlin patterns show payments` | Show patterns for a domain |
| `gremlin learn "incident" --domain auth` | Learn from incidents |
| `gremlin understand "scope"` | Stage 1 — infer domains (no LLM) |
| `gremlin ideate` | Stage 2 — select patterns (no LLM) |
| `gremlin rollout` | Stage 3 — call LLM |
| `gremlin judge` | Stage 4 — parse and score risks |

**`review` options:** `--depth quick|deep` · `--threshold 0-100` · `--output rich|md|json` · `--validate`

**`understand` options:** `--depth quick|deep` · `--threshold 0-100` · `--run-dir PATH`

**`judge` options:** `--validate` · `--run-dir PATH`

---

## License

MIT · Powered by [Claude](https://anthropic.com) · Inspired by exploratory testing principles from James Bach and James Whittaker
