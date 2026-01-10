# Gremlin Evaluation Framework

Comprehensive evaluation system for benchmarking Gremlin's pattern-driven risk analysis against baseline LLM performance.

## Overview

This eval framework enables:
- **Real-world validation**: Collect code samples from 100+ GitHub projects
- **Multi-provider support**: Test across Anthropic, OpenAI, and local models
- **Statistical rigor**: Multiple trials, consistency metrics, and cross-model comparison
- **Automated reporting**: Generate benchmark reports as marketing assets

## Quick Start

```bash
# 1. Collect 20-30 real-world code samples
python evals/collect_projects.py --per-domain 3 --total 30

# 2. Generate eval cases from fixtures
python evals/generate_cases.py

# 3. Run evaluations
./evals/run_eval.py --all --trials 3

# 4. Generate benchmark report
python evals/generate_report.py --output docs/BENCHMARK.md
```

## Architecture

```
evals/
├── collectors/              # GitHub project collection
│   ├── github.py           # GitHub API client
│   └── filters.py          # Domain/quality filters
├── fixtures/               # Collected code samples (.txt + .meta.json)
├── cases/                  # Eval case definitions (.yaml)
│   └── real-world/         # Generated from fixtures
├── results/                # Eval results (.json)
├── metrics.py              # Advanced consistency metrics
├── collect_projects.py     # Main collection script
├── generate_cases.py       # Case generator
├── run_eval.py             # Eval runner
└── generate_report.py      # Report generator
```

## Workflow

### Phase 1: Collection (Week 1)

Collect real-world code samples from GitHub:

```bash
# Collect specific domain
python evals/collect_projects.py --domain auth --per-domain 5

# Collect across all domains
python evals/collect_projects.py --total 30

# Requires GITHUB_TOKEN for higher rate limits
export GITHUB_TOKEN=ghp_your_token_here
```

**Output:**
- `evals/fixtures/*.txt` - Code samples
- `evals/fixtures/*.meta.json` - Metadata (repo, stars, domain, etc.)

### Phase 2: Case Generation

Convert fixtures into eval cases:

```bash
# Generate all cases
python evals/generate_cases.py

# Regenerate existing
python evals/generate_cases.py --regenerate

# Filter by domain
python evals/generate_cases.py --domain payments
```

**Output:**
- `evals/cases/real-world/*.yaml` - Eval case definitions

**Case Format:**
```yaml
name: auth-octocat-login-01
description: Real-world auth code from octocat/auth (1000⭐)
source:
  repo: octocat/auth
  file: src/login.ts
  url: https://github.com/octocat/auth/blob/main/src/login.ts
  stars: 1000
  domain: auth
input:
  scope: Authentication system
  context_file: ../fixtures/auth-octocat-login-01.txt
  depth: quick
  threshold: 70
expected:
  min_total: 2
  categories: [auth]
  keywords: []
```

### Phase 3: Evaluation

Run evals with multiple trials:

```bash
# Run all cases (3 trials per case)
./evals/run_eval.py --all --trials 3

# Run specific case
./evals/run_eval.py auth-octocat-login-01

# Cross-model comparison
./evals/run_eval.py --all --provider anthropic --model claude-opus-4-5-20251101
```

**Advanced Options:**
```bash
# Custom baseline model
./evals/run_eval.py --all \
  --provider anthropic \
  --model claude-sonnet-4-20250514 \
  --baseline-provider anthropic \
  --baseline-model claude-opus-4-5-20251101

# Adjust trial count and threshold
./evals/run_eval.py --all --trials 5 --threshold 0.8
```

**Output:**
- `evals/results/case-name-timestamp.json` - Detailed results with metrics

### Phase 4: Reporting

Generate markdown benchmark report:

```bash
# Generate from all results
python evals/generate_report.py --output docs/BENCHMARK.md

# Custom title
python evals/generate_report.py \
  --title "Gremlin v0.2 Benchmark (100 Projects)" \
  --output BENCHMARK_V0.2.md
```

**Report Includes:**
- Executive summary with win rate
- Per-case performance breakdown
- Domain coverage analysis
- Consistency metrics (CV, stability)
- Methodology description

## LLM Provider Abstraction

The framework supports multiple LLM providers via a clean abstraction layer.

### Adding New Provider

1. Implement `LLMProvider` interface:

```python
# gremlin/llm/providers/openai.py
from gremlin.llm.base import LLMProvider, LLMConfig, LLMResponse

class OpenAIProvider(LLMProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        # Initialize OpenAI client

    def complete(self, system_prompt: str, user_message: str, **kwargs) -> LLMResponse:
        # Call OpenAI API
        pass

    def validate_config(self) -> bool:
        # Validate configuration
        pass
```

2. Register provider:

```python
# gremlin/llm/factory.py
from gremlin.llm.providers.openai import OpenAIProvider

PROVIDER_REGISTRY["openai"] = OpenAIProvider
```

3. Use in evals:

```bash
./evals/run_eval.py --provider openai --model gpt-4-turbo
```

### Environment Variables

- `ANTHROPIC_API_KEY` - Anthropic API key
- `OPENAI_API_KEY` - OpenAI API key
- `GITHUB_TOKEN` - GitHub personal access token (optional, for higher rate limits)
- `GREMLIN_PROVIDER` - Default provider (default: anthropic)
- `GREMLIN_MODEL` - Default model (provider-specific default)

## Metrics

### Trial Metrics

Calculated per eval case across multiple trials:

- **pass@1**: First trial passed
- **pass@k**: Any trial passed
- **pass^k**: All trials passed
- **Consistency**: Pass rate across trials
- **Mean Score**: Average score
- **Standard Deviation**: Score variability

### Consistency Metrics

Measure stability across runs:

- **Coefficient of Variation (CV)**: std_dev / mean
  - CV < 0.15: Stable
  - CV 0.15-0.30: Moderate variability
  - CV > 0.30: High variability

### Cross-Model Metrics

Compare outputs between models:

- **Agreement Rate**: % of risks both models found
- **Jaccard Similarity**: Intersection / union of identified risks
- **Relative Coverage**: Gremlin risk count / baseline count

## Expanding to 100 Projects

Current pilot: 20-30 projects. To scale to 100:

```bash
# Phase 1: Collect 50 more samples
python evals/collect_projects.py --total 50 --per-domain 10

# Phase 2: Generate cases
python evals/generate_cases.py

# Phase 3: Run evals (consider batching)
./evals/run_eval.py --all --trials 3

# Phase 4: Generate final report
python evals/generate_report.py \
  --title "Gremlin Benchmark: 100 Real-World Projects" \
  --output docs/BENCHMARK_100.md
```

**Estimated Timeline:**
- Collection: 2-3 hours (with GitHub token)
- Case generation: 5 minutes
- Eval execution: 4-6 hours (100 cases × 3 trials × 2-3 min each)
- Reporting: 1 minute

**Cost Estimate (Anthropic):**
- Input: ~200K tokens per case (patterns + code)
- Output: ~1K tokens per case
- 100 cases × 3 trials × 2 runs = 600 API calls
- ~$20-30 total at Claude Sonnet 4 pricing

## Best Practices

### Collection
- Use `GITHUB_TOKEN` to avoid rate limiting
- Start with `min_stars=100` to ensure quality
- Target `50-800` lines of code per sample
- Collect across diverse domains for broad coverage

### Evaluation
- Use 3+ trials for statistical significance
- Save results with `--all` (default behavior)
- Consider domain-specific thresholds
- Monitor API costs with large-scale runs

### Reporting
- Generate reports after significant eval runs
- Include methodology section for credibility
- Update report as patterns evolve
- Share reports as marketing assets

## Troubleshooting

### GitHub Rate Limiting
```bash
# Check rate limit
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/rate_limit

# Wait or use different token
```

### Eval Timeouts
```python
# In run_eval.py, increase timeout
result = subprocess.run(cmd, timeout=300)  # 5 min
```

### Model Not Found
```bash
# List available providers
python -c "from gremlin.llm.factory import list_providers; print(list_providers())"

# Check model name
# Anthropic: claude-sonnet-4-20250514, claude-opus-4-5-20251101
# OpenAI: gpt-4-turbo-preview, gpt-4
```

## Future Enhancements

- [ ] Ground truth validation (mine GitHub issues for known bugs)
- [ ] Semantic similarity for cross-model comparison
- [ ] Domain-specific scoring weights
- [ ] Continuous evaluation CI/CD pipeline
- [ ] Interactive HTML reports
- [ ] Pattern effectiveness ranking
- [ ] Automated pattern refinement based on eval results

---

## Quick Reference

```bash
# Full pipeline
python evals/collect_projects.py --total 30
python evals/generate_cases.py
./evals/run_eval.py --all --trials 3
python evals/generate_report.py --output BENCHMARK.md

# Cross-model comparison
./evals/run_eval.py --all \
  --provider anthropic \
  --model claude-sonnet-4-20250514 \
  --baseline-model claude-opus-4-5-20251101

# Domain-specific eval
python evals/collect_projects.py --domain auth --per-domain 10
python evals/generate_cases.py --domain auth
./evals/run_eval.py --all
```
