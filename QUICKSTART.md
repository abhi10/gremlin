# Gremlin: Find Breaking Risks Before They Break Production

**Stop shipping bugs that your QA team could have caught — if they had time.**

Gremlin is an AI-powered exploratory QA agent that surfaces "what if?" scenarios before code hits production. It combines 70+ curated risk patterns from real-world incidents with Claude's reasoning to find the edge cases your team misses.

---

## Who Is This For?

| Role | How Gremlin Helps |
|------|-------------------|
| **Engineering Leads** | Catch architecture risks in PRDs before sprint planning |
| **Senior Engineers** | Review your own code with production-incident patterns |
| **QA Engineers** | Generate exploratory test cases in seconds, not hours |
| **Platform Teams** | Validate infrastructure changes against known failure modes |

**Best for teams that:**
- Ship weekly or faster
- Have experienced production incidents they want to prevent
- Review PRDs, designs, or code before implementation
- Value "shift-left" quality practices

---

## 5-Minute Setup

### Prerequisites
- Python 3.11+
- Anthropic API key ([get one here](https://console.anthropic.com/))

### Install

```bash
pip install gremlin-qa
```

### Configure

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Verify

```bash
gremlin --version
```

---

## Your First Analysis

### Analyze a Feature (from PRD or description)

```bash
gremlin review "user authentication with OAuth"
```

**Output:**
```
🔍 Analyzing: user authentication with OAuth
Detected domains: auth

╭─────────────────────────────────────────────────╮
│ Risk Scenarios for: user authentication with OAuth │
╰─────────────────────────────────────────────────╯

🔴 CRITICAL (92%)
OAuth Token Refresh Race Condition
▌ What if two browser tabs both try to refresh the token simultaneously?
• Impact: One succeeds, one fails. User randomly logged out.
• Domain: Auth + Concurrency

🟠 HIGH (88%)
State Parameter Reuse
▌ What if the OAuth state parameter is predictable or reused?
• Impact: CSRF attacks possible, potential account takeover.
• Domain: Auth + Security

...
```

### Analyze with Context (PRD, code, or tech stack)

```bash
# From a PRD file
gremlin review "checkout flow" --context @docs/PRD-checkout.md

# With tech stack info
gremlin review "payment processing" --context "Stripe, webhooks, PostgreSQL"

# From a git diff
git diff main | gremlin review "my changes" --context -
```

### View Available Patterns

```bash
# List all pattern domains
gremlin patterns list

# Show patterns for a specific domain
gremlin patterns show payments
```

---

## Real-World Examples

### Example 1: Pre-Sprint PRD Review

Your PM shares a PRD for a new "Team Invitations" feature. Before sprint planning:

```bash
gremlin review "team invitations" --context @prd/team-invites.md --depth deep
```

**Gremlin finds:**
- What if invited user already has an account with different email?
- What if invitation expires while user is mid-signup?
- What if team hits member limit after invite sent but before accepted?

**Result:** Three edge cases added to acceptance criteria before any code written.

---

### Example 2: Pre-Commit Code Review

You've implemented a new caching layer. Before pushing:

```bash
git diff --staged | gremlin review "caching implementation" --context -
```

**Gremlin finds:**
- What if cache invalidation races with concurrent writes?
- What if cache size grows unbounded on high-cardinality keys?
- What if cache miss triggers thundering herd to database?

**Result:** Add cache size limits and request coalescing before PR.

---

### Example 3: Architecture Decision Review

Evaluating whether to migrate from REST to GraphQL:

```bash
gremlin review "REST to GraphQL migration" --context "Current: Express REST API, 50 endpoints, PostgreSQL. Proposed: Apollo GraphQL."
```

**Gremlin finds:**
- What if N+1 queries explode without DataLoader?
- What if deeply nested queries cause timeout?
- What if field-level authorization differs from endpoint-level?

**Result:** Add DataLoader requirement and query depth limits to migration plan.

---

## Command Reference

| Command | Description |
|---------|-------------|
| `gremlin review "<scope>"` | Analyze a feature/scope for risks |
| `gremlin review "<scope>" --context "<info>"` | Add context (string, @file, or - for stdin) |
| `gremlin review "<scope>" --depth deep` | More thorough analysis |
| `gremlin review "<scope>" --threshold 60` | Lower confidence threshold (default: 80) |
| `gremlin review "<scope>" --output md` | Output as Markdown |
| `gremlin review "<scope>" --output json` | Output as JSON |
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
| **notifications** | Duplicate sends, template injection, delivery failure |
| **search** | Index lag, query injection, pagination |
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

### Slack Bot (coming soon)

```
/gremlin review checkout flow with Stripe
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

## What's Next?

- **Try it on your current sprint's PRD**
- **Run it on your last production incident's root cause**
- **Add it to your PR template checklist**

---

## Support & Feedback

- GitHub Issues: [github.com/abhi10/gremlin/issues](https://github.com/abhi10/gremlin/issues)
- Feature Requests: Open an issue with `[Feature]` prefix

---

*Gremlin: Because the best bug is the one you never ship.*
