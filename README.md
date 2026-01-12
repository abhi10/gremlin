# Gremlin

**Find breaking risks before they break production.**

Gremlin is an AI-powered exploratory QA agent that surfaces "what if?" scenarios before code ships. It combines 70+ curated risk patterns from real-world incidents with Claude's reasoning to find the edge cases your team misses.

## Who Is This For?

| Role | How Gremlin Helps |
|------|-------------------|
| **Engineering Leads** | Catch architecture risks in PRDs before sprint planning |
| **Senior Engineers** | Review your own code with production-incident patterns |
| **QA Engineers** | Generate exploratory test cases in seconds, not hours |
| **Platform Teams** | Validate infrastructure changes against known failure modes |

---

## Quick Start

### Install

```bash
pip install gremlin-qa
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Your First Analysis

```bash
gremlin review "checkout flow with Stripe"
```

**Output:**
```
🔍 Analyzing: checkout flow with Stripe
Detected domains: payments

╭─────────────────────────────────────────────────╮
│ Risk Scenarios for: checkout flow with Stripe  │
╰─────────────────────────────────────────────────╯

🔴 CRITICAL (95%)
Webhook Race Condition
▌ What if the Stripe webhook arrives before the order record is committed?
• Impact: Payment captured but order not created. Customer charged without record.
• Domain: payments

🟠 HIGH (88%)
Double Submit on Payment Button
▌ What if the user clicks "Pay Now" twice rapidly?
• Impact: Potential duplicate charges.
• Domain: payments, concurrency
```

---

## Context-Aware Analysis

Gremlin becomes more powerful when you provide context:

```bash
# From a PRD file
gremlin review "checkout flow" --context @docs/PRD-checkout.md

# With tech stack info
gremlin review "payment processing" --context "Stripe webhooks, PostgreSQL, Redis"

# From a git diff
git diff main | gremlin review "my changes" --context -
```

---

## Real-World Examples

### Pre-Sprint PRD Review

```bash
gremlin review "team invitations" --context @prd/team-invites.md --depth deep
```

**Finds:**
- What if invited user already has an account with different email?
- What if invitation expires while user is mid-signup?
- What if team hits member limit after invite sent but before accepted?

### Pre-Commit Code Review

```bash
git diff --staged | gremlin review "caching implementation" --context -
```

**Finds:**
- What if cache invalidation races with concurrent writes?
- What if cache size grows unbounded on high-cardinality keys?

### Architecture Decision Review

```bash
gremlin review "REST to GraphQL migration" --context "Express REST API, 50 endpoints"
```

**Finds:**
- What if N+1 queries explode without DataLoader?
- What if deeply nested queries cause timeout?

---

## Commands

| Command | Description |
|---------|-------------|
| `gremlin review "<scope>"` | Analyze a feature for QA risks |
| `gremlin review "<scope>" --context "<info>"` | Add context (string, @file, or `-` for stdin) |
| `gremlin review "<scope>" --depth deep` | More thorough analysis |
| `gremlin review "<scope>" --threshold 60` | Lower confidence threshold (default: 80) |
| `gremlin review "<scope>" --output md` | Output as Markdown |
| `gremlin patterns list` | List all pattern domains |
| `gremlin patterns show <domain>` | Show patterns for a domain |

---

## Pattern Domains

Gremlin includes 70+ patterns across these domains:

| Domain | Example Patterns |
|--------|------------------|
| **auth** | Token expiry, session hijacking, OAuth state |
| **payments** | Double charges, webhook ordering, refund races |
| **data** | Migration failures, cascade deletes, encoding |
| **concurrency** | Race conditions, deadlocks, thundering herd |
| **external** | API rate limits, timeout handling, retries |
| **file_handling** | Upload validation, storage limits, path traversal |
| **caching** | Invalidation, stampedes, stale reads |

---

## Integration Ideas

### CI/CD Pipeline

```yaml
# .github/workflows/gremlin.yml
- name: Risk Analysis
  run: |
    pip install gremlin-qa
    git diff origin/main | gremlin review "PR changes" --context - --output md >> $GITHUB_STEP_SUMMARY
```

### Pre-Commit Hook

```bash
# .git/hooks/pre-commit
git diff --staged | gremlin review "staged changes" --context - --threshold 90
```

---

## How It Works

```
User: gremlin review "checkout flow"
         │
         ▼
    ┌─────────────┐
    │ Parse scope │
    └──────┬──────┘
           │
           ▼
    ┌─────────────────┐
    │ Infer domains   │  "checkout" → payments
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ Select patterns │  universal + payments
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ Build prompt    │  system.md + patterns + context
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ Call Claude API │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ Render output   │  Risk scenarios
    └─────────────────┘
```

---

## Development

```bash
# Clone and setup
git clone https://github.com/abhi10/gremlin.git
cd gremlin
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ANTHROPIC_API_KEY not set` | Run `export ANTHROPIC_API_KEY="sk-ant-..."` |
| `No patterns matched` | Try broader scope or check `gremlin patterns list` |
| `Rate limited` | Wait 60s or reduce `--depth` |
| `Context file not found` | Check path, use `@` prefix for files |

---

## License

MIT

---

*Gremlin: Because the best bug is the one you never ship.*
