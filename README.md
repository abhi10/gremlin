# Gremlin

> Exploratory QA agent that surfaces risk scenarios using curated patterns + LLM reasoning

## What is Gremlin?

Gremlin is a CLI tool that answers: **"What could break in [feature X]?"**

It combines:
- **50 curated QA patterns** (domain-specific "what if?" questions)
- **Claude's reasoning** (applies patterns intelligently to your context)
- **Rich terminal output** (actionable risk scenarios)

## Installation

```bash
pip install gremlin-qa
```

## Quick Start

```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY=sk-ant-...

# Review a feature for risks
gremlin review "checkout flow with Stripe integration"

# Deep analysis with lower confidence threshold
gremlin review "auth system" --depth deep --threshold 60

# See available patterns
gremlin patterns list

# Show patterns for a specific domain
gremlin patterns show payments
```

## Example Output

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Risk Scenarios for: checkout flow                                           │
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

## Commands

| Command | Description |
|---------|-------------|
| `gremlin review "scope"` | Analyze a feature for QA risks |
| `gremlin patterns list` | Show all available pattern categories |
| `gremlin patterns show <domain>` | Show patterns for a specific domain |

## Options for `review`

| Option | Default | Description |
|--------|---------|-------------|
| `--depth` | `quick` | Analysis depth: `quick` or `deep` |
| `--threshold` | `80` | Confidence filter (0-100) |
| `--output` | `rich` | Output format: `rich`, `md`, `json` |

## Pattern Domains

Gremlin includes curated patterns for these domains:

- **auth** - Authentication, sessions, tokens
- **payments** - Checkout, billing, refunds
- **file_upload** - File handling, validation
- **database** - Queries, transactions, migrations
- **api** - Rate limiting, endpoints
- **deployment** - Config, containers, environments
- **infrastructure** - Servers, certs, resources
- And more...

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
    │ Build prompt    │  system.md + patterns + scope
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

## Gremlin Agent for Claude Code

In addition to the CLI tool, Gremlin provides a Claude Code agent for code review:

**Usage**: Invoke the Gremlin agent during code review sessions in Claude Code

**Benefits**:
- Line-specific risk identification in PRs
- Code-focused patterns (database, concurrency, caching)
- Automatic pattern matching during code review
- Optional CLI integration for comprehensive analysis

**Agent Patterns**: 45-50 code-review patterns optimized for:
- Database queries and transactions
- Concurrency and race conditions
- Authentication and token handling
- Caching and distributed systems
- Background jobs and workers
- Observability and monitoring

**When to Use**:
- CLI: Feature-scope analysis from PRD
- Agent: Code review in Claude Code sessions
- Both: Comprehensive coverage (recommended)

See [docs/INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md) for details.

## Development

```bash
# Clone the repo
git clone https://github.com/abhi10/gremlin.git
cd gremlin

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .
```

## License

MIT

## Contributing

Contributions welcome! Please open an issue first to discuss what you'd like to change.

## Acknowledgments

- Inspired by exploratory testing principles from James Bach and James Whittaker
- Powered by [Claude](https://anthropic.com) from Anthropic
