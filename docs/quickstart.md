# Quickstart Guide

Get started with Gremlin in 5 minutes.

## Installation

```bash
pip install gremlin-critic
```

## Setup

Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Get your API key from [console.anthropic.com](https://console.anthropic.com).

## Your First Review

Let's analyze a checkout flow for potential issues:

```bash
gremlin review "checkout flow with Stripe integration"
```

You'll see output like:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Risk Scenarios for: checkout flow with Stripe integration                   │
└─────────────────────────────────────────────────────────────────────────────┘

🔴 CRITICAL (95% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Webhook Race Condition

  What if the Stripe webhook arrives before the order record is committed?

  Impact: Payment captured but order not created. Customer charged without record.
  Domain: payments

🟠 HIGH (87% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Double Submit on Payment Button

  What if the user clicks "Pay Now" twice rapidly?

  Impact: Potential duplicate charges.
  Domain: payments, concurrency
```

## Common Use Cases

### 1. Quick Feature Review

Analyze any feature scope with natural language:

```bash
# Authentication system
gremlin review "user login with OAuth"

# Database operations
gremlin review "user profile update with transactions"

# API endpoints
gremlin review "REST API for product search"
```

### 2. Deep Analysis

For more thorough analysis, use `--depth deep`:

```bash
gremlin review "payment processing" --depth deep
```

This will:
- Surface more edge cases
- Include lower-confidence scenarios
- Provide more detailed impact analysis

### 3. Filter by Confidence

Only show high-confidence risks:

```bash
gremlin review "auth flow" --threshold 85
```

Threshold range: 0-100 (default: 80)

### 4. Adding Context

Provide additional context to get more specific risks:

**Direct context:**
```bash
gremlin review "checkout" --context "Using Next.js, Stripe, PostgreSQL"
```

**From a file:**
```bash
gremlin review "auth" --context @src/auth/login.ts
```

**From stdin (pipe):**
```bash
git diff | gremlin review "recent changes" --context -
```

### 5. Different Output Formats

**Markdown** (great for documentation):
```bash
gremlin review "checkout" --output md > risks.md
```

**JSON** (for tooling integration):
```bash
gremlin review "checkout" --output json > risks.json
```

**Rich** (default, colorful terminal output):
```bash
gremlin review "checkout" --output rich
```

## Exploring Patterns

See what patterns Gremlin uses:

```bash
# List all pattern domains
gremlin patterns list
```

Output:
```
Available Pattern Domains:
  • auth (12 patterns)
  • payments (8 patterns)
  • database (15 patterns)
  • file_upload (6 patterns)
  • api (10 patterns)
  ...
```

Show patterns for a specific domain:

```bash
gremlin patterns show payments
```

Output:
```
Patterns for 'payments' domain:

1. What if the webhook arrives before the transaction is committed?
2. What if payment succeeds but inventory update fails?
3. What if user clicks "Pay" multiple times rapidly?
...
```

## Understanding Results

### Severity Levels

Gremlin rates risks by severity:

- **🔴 CRITICAL** (90-100%): Immediate production issues, data loss, security breaches
- **🟠 HIGH** (75-89%): Significant impact, user-facing problems
- **🟡 MEDIUM** (60-74%): Moderate issues, degraded experience
- **🟢 LOW** (40-59%): Minor concerns, edge cases

### Confidence Scores

Each risk includes a confidence score (0-100%):

- **95%+**: Very likely to occur or cause impact
- **85-94%**: High confidence
- **75-84%**: Moderate confidence
- **60-74%**: Lower confidence, but worth considering

### Impact Analysis

Each risk explains:
- **What could go wrong** (the "what if?" question)
- **Why it matters** (concrete impact on users/system)
- **What domain** it belongs to

## Advanced Usage

### Environment Variables

**Required:**
- `ANTHROPIC_API_KEY`: Your Anthropic API key

**Optional:**
- `GREMLIN_MODEL`: Override default Claude model
  ```bash
  export GREMLIN_MODEL=claude-opus-4-5-20251101
  ```

### Development Mode

Install Gremlin in development mode:

```bash
git clone https://github.com/abhi10/gremlin.git
cd gremlin
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run tests:
```bash
pytest
```

### Integration with CI/CD

Add Gremlin to your CI pipeline:

```yaml
# .github/workflows/qa-review.yml
name: QA Review
on: [pull_request]

jobs:
  gremlin:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install gremlin-critic
      - run: |
          git diff origin/main...HEAD | \
          gremlin review "code changes in this PR" \
            --context - \
            --output md >> $GITHUB_STEP_SUMMARY
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Tips & Best Practices

### 1. Be Specific with Scope

**Good:**
```bash
gremlin review "checkout flow with Stripe webhooks and inventory updates"
```

**Less Effective:**
```bash
gremlin review "the app"
```

### 2. Use Context for Technical Details

Provide tech stack context for more relevant risks:
```bash
gremlin review "auth" --context "Using JWT, Redis sessions, PostgreSQL"
```

### 3. Combine with Code Review

Use Gremlin during different stages:
- **Design phase**: Review feature scope from PRD
- **Implementation**: Review specific code with `--context @file.ts`
- **PR review**: Pipe `git diff` to analyze changes

### 4. Filter Appropriately

Adjust threshold based on phase:
- **Early design**: Lower threshold (70) to surface more scenarios
- **Pre-production**: Higher threshold (90) to focus on critical issues

### 5. Export for Documentation

Generate risk documentation:
```bash
gremlin review "payment system" --output md > docs/payment-risks.md
```

## Common Questions

### How is Gremlin different from Claude?

Gremlin uses **93 curated QA patterns** combined with Claude's reasoning:
- More consistent risk identification (90.7% quality parity)
- Domain-specific patterns (payments, auth, database, etc.)
- Structured output optimized for QA workflows

### What domains does Gremlin cover?

11 domains with 93 patterns:
- auth, payments, file_upload, database, api
- deployment, infrastructure, search, dependencies
- frontend, security

### Can I add custom patterns?

Yes! Edit `patterns/breaking.yaml` to add domain-specific patterns:

```yaml
domain_specific:
  your_domain:
    keywords: [your, domain, keywords]
    patterns:
      - "What if your custom scenario happens?"
```

### How accurate is Gremlin?

Gremlin achieves **90.7% tie rate** with baseline Claude Sonnet 4 across 54 real-world test cases:
- 98.1% win/tie rate
- 91% consistency across multiple trials
- See [evaluation results](../evals/PHASE2_TIER1_INVESTIGATION_COMPLETE.md)

## Next Steps

- **Read the [full documentation](../README.md)** for all features
- **Explore [examples](../examples/)** for common use cases
- **Check the [evaluation framework](../evals/README.md)** to understand quality metrics
- **Join discussions** on GitHub for questions and feedback

## Getting Help

- **Documentation**: [README.md](../README.md)
- **Issues**: [github.com/abhi10/gremlin/issues](https://github.com/abhi10/gremlin/issues)
- **Examples**: [examples/](../examples/)

---

**Ready to find risks?** Run your first review:

```bash
gremlin review "your feature scope here"
```
