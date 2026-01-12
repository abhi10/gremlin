# Gremlin

> Exploratory QA agent that surfaces risk scenarios using curated patterns + LLM reasoning

## What is Gremlin?

Gremlin is a CLI tool that answers: **"What could break in [feature X]?"**

It combines:
- **93 curated QA patterns** (domain-specific "what if?" questions)
- **Claude's reasoning** (applies patterns intelligently to your context)
- **Rich terminal output** (actionable risk scenarios)

## Installation

```bash
# Clone the repo
git clone https://github.com/abhi10/gremlin.git
cd gremlin

# Install
pip install -e .

# Set your Anthropic API key
export ANTHROPIC_API_KEY=sk-ant-...
```

## Quick Start

```bash
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
| `--patterns` | - | Custom patterns file (YAML) |
| `--context` | - | Additional context: string, `@file`, or `-` for stdin |
| `--validate` | `false` | Run second pass to filter hallucinations |

## Custom Patterns

Add domain-specific patterns for your codebase:

### Project-level (auto-loaded)

```yaml
# .gremlin/patterns.yaml
domain_specific:
  image_processing:
    keywords: [image, photo, upload, resize, cdn]
    patterns:
      - "What if EXIF rotation is ignored during resize?"
      - "What if CDN cache serves stale image after update?"
```

### Via `--patterns` flag

```bash
gremlin review "image upload" --patterns @my-patterns.yaml
```

### Learn from incidents

```bash
gremlin learn "Portrait images displayed sideways" --domain files --source prod-incident
```

See [docs/CUSTOM_PATTERNS.md](docs/CUSTOM_PATTERNS.md) for the full authoring guide.

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

## Performance

Gremlin's pattern-based approach achieves **90.7% tie rate** with baseline Claude Sonnet 4 across 54 real-world test cases:

| Metric | Result | Notes |
|--------|--------|-------|
| **Tie Rate** | 90.7% | Gremlin matches baseline Claude quality |
| **Win/Tie Rate** | 98.1% | Combined wins + ties |
| **Gremlin Wins** | 7.4% | Cases where patterns provide unique value |
| **Claude Wins** | 1.9% | Minor category labeling differences |
| **Pattern Count** | 93 | Universal + domain-specific patterns |

**Key Achievement**: 90% reduction in quality gaps (19% → 1.9%) through strategic pattern improvements.

See [Phase 2 Tier 1 Results](evals/RESULTS.md) for detailed analysis.

## Claude Code Integration

Gremlin also provides a Claude Code agent for code-focused risk analysis during PR reviews. See [docs/INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md) for setup.

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
