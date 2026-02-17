# Gremlin

> AI critic for your codebase — surfaces breaking risk scenarios before they reach production

## What is Gremlin?

Gremlin is a **pre-ship risk critic** (CLI + Python library) that answers: **"What could break?"**

Feed it a feature spec, PR diff, or plain English — Gremlin critiques it for blind spots using:
- **107 curated risk patterns** across 14 domains (payments, auth, infra, serialization, distributed systems, and more)
- **LLM reasoning** (applies patterns intelligently to your specific context)
- **Structured output** (severity-ranked risk scenarios with confidence scores)

## Installation

```bash
# Install from PyPI
pip install gremlin-critic

# Set your Anthropic API key
export ANTHROPIC_API_KEY=sk-ant-...
```

> **For development:** `git clone https://github.com/abhi10/gremlin.git && pip install -e ".[dev]"`

## Quick Start

### CLI Usage

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

### Programmatic API (New in v0.2.0)

```python
from gremlin import Gremlin

# Basic usage
gremlin = Gremlin()
result = gremlin.analyze("user authentication")

# Check for critical risks
if result.has_critical_risks():
    print(f"Found {result.critical_count} critical risks!")
    for risk in result.risks:
        print(f"- [{risk.severity}] {risk.scenario}")

# Multiple output formats
json_output = result.to_json()       # JSON string
junit_xml = result.to_junit()        # JUnit XML for CI
llm_format = result.format_for_llm() # Concise format for agents

# Async support for agent frameworks
result = await gremlin.analyze_async("payment processing")

# With additional context
result = gremlin.analyze(
    scope="checkout flow",
    context="Using Stripe API with webhook handling",
    depth="deep"
)
```

See the [API documentation](#programmatic-api) below for detailed usage.

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

## Risk Dashboard

Interactive visualization of Gremlin analysis results — live at **[abhi10.github.io/gremlin](https://abhi10.github.io/gremlin/)**

[![Gremlin Risk Dashboard](https://img.shields.io/badge/Live%20Demo-Risk%20Dashboard-6366F1?style=flat-square)](https://abhi10.github.io/gremlin/)

Features:
- **Heatmap visualization** — severity distribution across feature areas (CRITICAL / HIGH / MEDIUM / LOW)
- **Severity donut chart** — at-a-glance risk breakdown
- **Domain bar chart** — risk count per domain (concurrency, auth, payments...)
- **Interactive risk table** — sortable, filterable, expandable rows with full scenario + impact
- **Multi-project** — includes scans of [celery](https://github.com/celery/celery), [pydantic](https://github.com/pydantic/pydantic), [openclaw](https://github.com/openclaw/openclaw)

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
| **Pattern Count** | 107 | Universal + domain-specific patterns |

**Key Achievement**: 90% reduction in quality gaps (19% → 1.9%) through strategic pattern improvements.

See [Phase 2 Tier 1 Results](evals/RESULTS.md) for detailed analysis.

## Claude Code Integration

Gremlin also provides a Claude Code agent for code-focused risk critique during PR reviews. See [docs/INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md) for setup.

## Programmatic API

Gremlin can be used as a Python library for integration with CI/CD pipelines, agent frameworks, and custom tools.

### Installation

```bash
pip install gremlin-critic
# Or for development:
pip install -e ".[dev]"
```

### Basic Usage

```python
from gremlin import Gremlin, Risk, AnalysisResult

# Initialize analyzer
gremlin = Gremlin()

# Analyze a scope
result = gremlin.analyze("checkout flow")

# Access results
print(f"Found {len(result.risks)} risks")
print(f"Matched domains: {result.matched_domains}")
print(f"Pattern count: {result.pattern_count}")
```

### Configuration

```python
# Use different provider/model
gremlin = Gremlin(
    provider="anthropic",           # anthropic, openai, ollama
    model="claude-sonnet-4-20250514",
    threshold=80                     # Confidence threshold
)

# Analyze with context
result = gremlin.analyze(
    scope="user authentication",
    context="Using JWT with Redis session store",
    depth="deep"                     # quick or deep
)
```

### Output Formats

```python
# Dictionary (for JSON APIs)
data = result.to_dict()

# JSON string
json_str = result.to_json()

# JUnit XML (for CI/CD integration)
junit_xml = result.to_junit()

# LLM-friendly format (for agent consumption)
agent_input = result.format_for_llm()
```

### Risk Analysis

```python
# Check risk severity
if result.has_critical_risks():
    print(f"⚠️  {result.critical_count} critical risks found")

if result.has_high_severity_risks():
    print(f"Found {result.high_count} high + {result.critical_count} critical")

# Iterate through risks
for risk in result.risks:
    print(f"[{risk.severity}] ({risk.confidence}%)")
    print(f"  Scenario: {risk.scenario}")
    print(f"  Impact: {risk.impact}")
    print(f"  Domains: {', '.join(risk.domains)}")
```

### Async Support

```python
import asyncio
from gremlin import Gremlin

async def analyze_features():
    gremlin = Gremlin()

    # Run multiple analyses concurrently
    results = await asyncio.gather(
        gremlin.analyze_async("checkout flow"),
        gremlin.analyze_async("user authentication"),
        gremlin.analyze_async("file upload")
    )

    for result in results:
        print(f"{result.scope}: {len(result.risks)} risks")

asyncio.run(analyze_features())
```

### Use Cases

**1. LLM Agent Tool**
```python
from gremlin import Gremlin

def analyze_code_risks(code: str, feature: str) -> str:
    """Tool for LLM agents to analyze code risks."""
    gremlin = Gremlin()
    result = gremlin.analyze(scope=feature, context=code)
    return result.format_for_llm()

# Use with LangChain, CrewAI, AutoGen, etc.
```

**2. CI/CD Integration**
```python
from gremlin import Gremlin
import sys

gremlin = Gremlin(threshold=70)
result = gremlin.analyze("PR changes", context=diff_content)

# Output JUnit XML
with open("gremlin-results.xml", "w") as f:
    f.write(result.to_junit())

# Exit with error if critical risks found
if result.has_critical_risks():
    print(f"❌ Found {result.critical_count} critical risks")
    sys.exit(1)
```

**3. Custom Validation Pipeline**
```python
from gremlin import Gremlin

def validate_feature_design(prd: str, feature_name: str) -> dict:
    """Validate a feature design for risks."""
    gremlin = Gremlin(depth="deep")
    result = gremlin.analyze(feature_name, context=prd)

    return {
        "feature": feature_name,
        "risk_count": len(result.risks),
        "critical": result.critical_count,
        "high": result.high_count,
        "requires_review": result.has_high_severity_risks(),
        "report": result.to_dict()
    }
```

### API Reference

**Classes:**
- `Gremlin` - Main analyzer class
- `Risk` - Individual risk finding with severity, confidence, scenario, impact
- `AnalysisResult` - Complete analysis with multiple output formats

**Methods:**
- `Gremlin.analyze(scope, context, depth)` - Synchronous analysis
- `Gremlin.analyze_async(scope, context, depth)` - Async analysis
- `AnalysisResult.to_dict()` - Dictionary serialization
- `AnalysisResult.to_json()` - JSON string
- `AnalysisResult.to_junit()` - JUnit XML
- `AnalysisResult.format_for_llm()` - LLM-friendly format
- `AnalysisResult.has_critical_risks()` - Check for critical risks
- `AnalysisResult.has_high_severity_risks()` - Check for high+ risks

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
