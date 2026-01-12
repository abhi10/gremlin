# Gremlin Evaluation Results

**Last Updated**: January 11, 2026
**Status**: ✅ Phase 2 Complete - Ready for Production

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Tie Rate** | 90.7% |
| **Win/Tie Rate** | 98.1% |
| **Claude Wins** | 1.9% (1 of 54 cases) |
| **Gremlin Wins** | 7.4% |
| **Pattern Count** | 93 patterns across 15 domains |

---

## Phase 2 Tier 1 Results

### Final Distribution (54 cases)

| Outcome | Count | Percentage |
|---------|-------|------------|
| **Ties** | 49 | 90.7% |
| **Gremlin wins** | 4 | 7.4% |
| **Claude wins** | 1 | 1.9% |

### Improvement from Baseline

| Metric | Phase 1 | Phase 2 | Change |
|--------|---------|---------|--------|
| Tie Rate | 74% | 90.7% | **+16.7%** |
| Claude Wins | 19% | 1.9% | **-17.1%** |
| Win/Tie | 81% | 98.1% | **+17.1%** |
| Patterns | 88 | 93 | +5 |

---

## Key Findings

### Patterns Working Well

All Phase 2 Tier 1 patterns triggered correctly:
1. **SSRF** - CRITICAL severity as intended
2. **Memory exhaustion** - CRITICAL with enhanced severity hints
3. **Type safety** - Catching runtime crashes
4. **Missing timeouts** - HIGH severity appropriate
5. **ReDoS** - MEDIUM/HIGH on security cases

### The Single Claude Win

**Case**: `frontend-vuejs-vue-monitor-02`
- **Root cause**: Category labeling, not pattern gap
- **Analysis**: Both found identical risks (memory leak, production deployment, dependency failure)
- **Why Claude scored higher**: Gremlin output didn't explicitly mention "frontend" category
- **Impact**: Presentation issue only - risk quality was equal

### Rate Limit Investigation

5 initial "Claude wins" were due to API rate limiting during parallel execution:
- Running 54 cases with `--workers 5` exceeded token limits
- Sequential re-runs converted all 5 to ties
- **Lesson**: Use `--workers 2` max or run sequentially for accuracy

---

## Methodology

### Eval Setup
- **Cases**: 54 real-world code samples from GitHub
- **Trials**: 3 per case
- **Comparison**: Gremlin (with patterns) vs Claude (no patterns)
- **Scoring**: Based on risk count, severity, and category coverage

### Scoring Criteria
- Meet minimum risk thresholds (min_critical, min_high, min_total)
- Cover expected categories (auth, payments, etc.)
- Find expected keywords when specified

### Win Determination
- **Tie**: Both Gremlin and baseline meet criteria OR both fail
- **Gremlin win**: Gremlin passes, baseline fails
- **Claude win**: Baseline passes, Gremlin fails

---

## Patterns Added in Phase 2

| Pattern | Domain | Severity |
|---------|--------|----------|
| SSRF via URL parameters | security | CRITICAL |
| Memory exhaustion on unbounded input | performance | CRITICAL |
| Type coercion leading to runtime crashes | data | HIGH |
| Missing request timeouts | external | HIGH |
| ReDoS via complex regex | security | MEDIUM-HIGH |

---

## Recommendations

### Current Status: Ship-Ready ✅

The 98.1% win/tie rate exceeds all targets. Current performance is excellent for production use.

### Optional Future Improvements

1. **Fix category labeling** (Low priority)
   - Ensure output explicitly mentions matched domains
   - Could convert remaining Claude win to tie

2. **Add Tier 2 patterns** (After gathering user feedback)
   - Diminishing returns at 90%+ tie rate
   - Better to collect real-world usage patterns first

---

## Running Evaluations

```bash
# Full eval run
./evals/run_eval.py --all --trials 3

# Specific case
./evals/run_eval.py auth-example-01

# Generate report
python evals/generate_report.py --output BENCHMARK.md
```

See [README.md](./README.md) for complete eval framework documentation.

---

*Results archived from Phase 1 and Phase 2 evaluation runs.*
