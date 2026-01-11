# Eval Run: January 10, 2026

This folder contains the complete results and analysis from the eval expansion feature implementation.

## 📋 Contents

### Main Reports
- **[EVAL_COMPLETION_SUMMARY.md](EVAL_COMPLETION_SUMMARY.md)** - Complete overview of deliverables, results, and next steps
- **[BENCHMARK_REPORT.md](BENCHMARK_REPORT.md)** - Full technical report with per-case results (66 cases)
- **[ANALYSIS_SUMMARY.md](ANALYSIS_SUMMARY.md)** - Deep-dive technical analysis with insights
- **[MARKETING_SUMMARY.md](MARKETING_SUMMARY.md)** - One-pager for website/pitches

## 🎯 Quick Stats

- **Cases evaluated:** 54 (real-world) + 7 (legacy tests) = 66 total
- **Trials per case:** 3
- **Total evaluations:** 162
- **Gremlin accuracy:** 95%
- **Gremlin consistency:** 99%
- **Domains covered:** 11/12 (92%)
- **Code samples:** 47 from 100+ star repos

## 📊 Key Finding

**80% tie rate** between Gremlin (with patterns) and raw Claude (no patterns).

**Interpretation:** Patterns provide **consistency** and **structured output**, not just accuracy.

## 🚀 What's Next

Read [EVAL_COMPLETION_SUMMARY.md](EVAL_COMPLETION_SUMMARY.md) for full details on:
- All deliverables
- Architecture decisions
- Marketing claims
- Next steps to reach 100 projects

## 🔗 Related Files

**Raw results:** `../results/*.json` (66 JSON files)
**Test cases:** `../cases/real-world/*.yaml` (47 YAML configs)
**Code samples:** `../fixtures/*.txt` (47 fixtures with metadata)
