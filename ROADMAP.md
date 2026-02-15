# Gremlin Improvement Roadmap

**Last Updated**: February 15, 2026
**Current Status**: Phase 2 Tier 1 Complete ✅

---

## Table of Contents

- [Completed Work](#completed-work)
  - [Phase 1: Eval → Pattern Feedback Loop](#-phase-1-eval--pattern-feedback-loop-complete)
  - [Phase 2 Tier 1: Strategic Pattern Expansion](#-phase-2-tier-1-strategic-pattern-expansion-complete)
- [Cleanup Recommendations](#cleanup-recommendations)
- [Next Steps: Paths Forward](#next-steps-paths-forward)
  - [Priority 1: Market Readiness](#priority-1-market-readiness--recommended)
  - [Priority 1.5: Evaluation Maturity](#priority-15-evaluation-maturity--new)
  - [Priority 2: Additional Patterns](#priority-2-phase-2-tier-2---additional-patterns-optional)
  - [Priority 3: Agent Enhancement](#priority-3-agent-enhancement-alternative)
  - [Priority 4: Pattern Pruning + Quality Scoring](#priority-4-pattern-pruning--quality-scoring-advanced)
- [Recommended Immediate Action](#recommended-immediate-action)
- [Success Metrics](#success-metrics)
- [Resources](#resources)

---

## Completed Work

### ✅ Phase 1: Eval → Pattern Feedback Loop (Complete)
**Goal**: Improve win rate by adding patterns Claude caught but Gremlin missed

**Approach Taken**: Quality over Quantity
- Added 3 critical strategic patterns (Git hooks, TOCTOU, implicit globals)
- Enhanced 2 existing patterns with severity/impact hints
- Fixed infrastructure domain keyword matching bug
- **Net**: +3 patterns (~4% growth, strategic not generic)

**Key Learnings**:
- ❌ More patterns ≠ better (initial approach: +8 patterns caused 80%→74% tie rate drop)
- ✅ Severity hints work (Git hooks now CRITICAL 90% instead of missing)
- ✅ Quality beats quantity (domain-specific > universal)

**Deliverables**:
- Updated `patterns/breaking.yaml` with severity hints
- Documentation: `evals/PHASE1_*.md` and `evals/phase1_*.md`

### ✅ Phase 2 Tier 1: Strategic Pattern Expansion (Complete)
**Goal**: Achieve 80%+ tie rate by adding high-impact patterns that Claude caught but Gremlin missed

**Approach Taken**: Strategic Pattern Addition
- Added 5 new critical patterns (SSRF, Type Safety, Missing Timeouts, ReDoS, API Auth)
- Enhanced 1 existing pattern with severity hints (Memory Exhaustion)
- Removed 1 duplicate pattern
- **Net**: +5 patterns (~5% growth, highly targeted)

**Results Exceeded All Targets**:
- **Tie Rate**: 74% → **90.7%** (+16.7%)
- **Win/Tie Rate**: 81% → **98.1%** (+17.1%)
- **Claude Wins**: 19% → **1.9%** (90% reduction)
- **Gremlin Wins**: 7% → 7.4% (stable)

**Key Learnings**:
- ✅ Severity hints highly effective (SSRF triggers as CRITICAL 85%, Memory Exhaustion 90%)
- ✅ Domain-specific patterns differentiate better than universal
- ✅ Strategic selection > adding many patterns
- ⚠️ API rate limits real (30k input tokens/min, 8k output tokens/min)

**Investigation Completed**:
- 6 initial "Claude wins" analyzed
- 5 were API rate limit errors (converted to ties when re-run)
- 1 legitimate win due to category labeling (risk quality was equal)
- Final status: **READY FOR PRODUCTION** 🚀

**Deliverables**:
- Updated `patterns/breaking.yaml`: 88 → 93 patterns
- Severity hints: 5 → 11 patterns with hints
- Documentation:
  - `evals/PHASE2_PATTERN_ANALYSIS.md`
  - `evals/PHASE2_TIER1_RESULTS.md`
  - `evals/PHASE2_TIER1_FULL_EVAL_RESULTS.md`
  - `evals/PHASE2_TIER1_FINAL_RESULTS.md`
  - `evals/PHASE2_TIER1_INVESTIGATION_COMPLETE.md`

---

## Cleanup Recommendations

### ✅ Already Clean
- `evals/results/` - 121 JSON files (1.7MB) **already gitignored** ✅
- No uncommitted changes in working directory
- All Phase 1 work committed and merged

### Optional Cleanup (Not Required)
```bash
# Optional: Archive old test results to save disk space
tar -czf evals/results-20260110-archive.tar.gz evals/results/*20260110*.json
rm evals/results/*20260110*.json

# Keep documentation - it's valuable reference (only 23KB)
# evals/PHASE1_*.md files document approach/learnings
```

**Recommendation**: Keep everything as-is. Results are gitignored, docs are useful.

---

## Next Steps: Paths Forward

### Priority 1: Market Readiness 🚀 (Recommended)
**Effort**: Medium | **Impact**: High | **Risk**: Low

**Objective**: Prepare Gremlin for public release and user adoption

**Rationale**:
- Current performance is production-ready (90.7% tie rate, 98.1% win/tie)
- More value in adoption than marginal gains (90.7% → 95% has limited ROI)
- Validate approach with real users before further optimization

**Steps**:
1. **Documentation Polish** (2-3 hours)
   - ✅ Update README.md with Phase 2 results
   - ✅ Create CHANGELOG.md
   - ✅ Update ROADMAP.md
   - Create quickstart guide
   - Document evaluation methodology

2. **Examples Creation** (3-4 hours)
   - Create `examples/` directory with real usage examples
   - Sample outputs for common scenarios
   - Integration examples (CI/CD, pre-commit hooks)

3. **Publishing** (1-2 hours)
   - Publish to PyPI (`pip install gremlin-critic`)
   - Create GitHub release v0.1.0
   - Tag and document release notes

4. **Marketing Assets** (2-3 hours)
   - Record asciicast demo
   - Capture screenshots
   - Create comparison table (Gremlin vs manual QA vs Claude)

**Expected Outcome**:
- Package installable via pip
- Clear onboarding path for new users
- Demo materials for sharing
- Real-world feedback for future improvements

**Files to Create**:
- `examples/` directory with usage examples
- `docs/quickstart.md`
- `docs/evaluation-results.md`

---

### Priority 1.5: Evaluation Maturity 🧪 (New)
**Effort**: Medium | **Impact**: High | **Risk**: Low

**Objective**: Improve how Gremlin measures quality — move from consistency metrics to correctness metrics

**Rationale** (from [AI Evaluation Fundamentals](https://en.wikipedia.org/wiki/LLM_evaluation)):
- Current evals measure *consistency* (pass@k, pass^k) but not *correctness* — a system can be consistently wrong
- `validator.py` implements LLM-as-judge but is completely disconnected from the pipeline
- Default `temperature=1.0` is a confounding variable that makes it hard to isolate pattern contribution
- The httpx validation (16.4% of risks map to real bugs) proved golden set methodology works but is currently manual
- Deterministic checks (regex, format validation) should catch quality issues before expensive LLM calls

**Steps**:

1. **Wire up `validator.py`** (2-3 hours)
   - Integrate existing LLM-as-judge into `api.py` `analyze()` pipeline
   - Expose via `--validate` flag in CLI (flag exists but isn't connected)
   - Checks: relevance, specificity, duplicates, severity alignment
   - Related: [#13 — Implement transcript structure](https://github.com/abhi10/gremlin/issues/13)

2. **Add deterministic quality pre-checks** (2-3 hours)
   - Minimum risk count validation (did the LLM actually produce risks?)
   - Format compliance (every risk must have scenario + impact)
   - Domain relevance check (did "checkout flow" produce payments-related risks?)
   - Duplicate detection via string similarity before LLM dedup
   - Related: [#14 — Add pattern test format](https://github.com/abhi10/gremlin/issues/14)

3. **Formalize golden set evaluation** (3-4 hours)
   - Convert the 12 validated httpx risks into verified ground truth fixtures
   - Measure recall: how many of the 12 does Gremlin find each run?
   - Extend to pydantic/celery critiques once cross-validated
   - Related: [#9 — Complete 100-project eval expansion](https://github.com/abhi10/gremlin/issues/9)

4. **Add eval temperature control** (1-2 hours)
   - Support `--temperature` flag in eval runner
   - Run evals at both 0.3 (isolate pattern contribution) and 1.0 (creative diversity)
   - Compare: do patterns help more at low temperature (where LLM creativity is constrained)?

5. **Integrate golden sets into CI** (2-3 hours)
   - Run golden set recall check on PR (fast: 1 case, 1 trial)
   - Fail if recall drops below baseline threshold
   - Related: [#12 — Add eval harness CI](https://github.com/abhi10/gremlin/issues/12)

**Expected Outcome**:
- Quality measured by correctness (recall against verified bugs), not just consistency
- Hallucinated risks filtered by LLM-as-judge before reaching user
- Fast deterministic checks catch 80% of quality issues without API calls
- Clear signal on whether patterns add value beyond LLM baseline

**Key Insight**: Blend deterministic and non-deterministic checks. Simple regex for format/dedup is cheaper, faster, and more reliable than LLM calls. Use LLM-as-judge only for semantic quality that regex can't catch.

**Files to Modify**:
- `gremlin/api.py` — wire validator into analyze() pipeline
- `gremlin/core/validator.py` — already exists, needs integration
- `evals/run_eval.py` — add temperature flag, golden set mode
- `evals/golden/` — new directory for verified ground truth fixtures

---

### Priority 2: Phase 2 Tier 2 - Additional Patterns (Optional)
**Effort**: Medium | **Impact**: Low | **Risk**: Low

**Objective**: Push tie rate from 90.7% to 92-95% with 5 more strategic patterns

**Rationale**: Diminishing returns at current quality level, better to gather real-world feedback first

**Candidate Patterns**:
1. Idempotency key missing (Payments - HIGH)
2. Cross-browser API availability (Frontend - HIGH)
3. State transition validation (Database/Payments)
4. Hardcoded production values (Configuration)
5. Service privilege mismatch (Infrastructure)

**Expected Outcome**:
- Tie rate: 90.7% → 92-95%
- Claude wins: 1.9% → 0-1%
- Marginal improvement with moderate effort

**Recommendation**: Defer until after gathering user feedback from Priority 1

---

### Priority 3: Agent Enhancement (Alternative)
**Effort**: Low-Medium | **Impact**: Medium | **Risk**: Medium

**Objective**: Improve system prompt and agent instructions for better severity calibration

**Current Issue**: Baseline Claude Sonnet 4 has excellent reasoning without patterns. Need to differentiate through better prompting.

**Steps**:
1. Review `prompts/system.md` - current persona and instructions
2. Add few-shot examples showing correct severity ratings
3. Add structured reasoning prompts (e.g., "First assess attack surface, then rate severity")
4. Test prompt variations on subset of cases

**Expected Outcome**:
- More consistent severity ratings across trials
- Better domain inference from scope
- Improved confidence calibration

**Files to Modify**:
- `prompts/system.md`
- `gremlin/core/prompts.py` (if adding few-shot examples)

**Risk**: Prompt engineering is trial-and-error, may not improve results

---

### Priority 4: Pattern Pruning + Quality Scoring (Advanced)
**Effort**: High | **Impact**: Medium | **Risk**: Medium

**Objective**: Remove low-value generic patterns, keep only high-quality domain-specific ones

**Hypothesis**: Some universal patterns are redundant with Claude's base reasoning

**Steps**:
1. Run ablation study: Remove 5 generic universal patterns
2. Measure impact on win/tie rate
3. Create pattern effectiveness scoring:
   - Track which patterns trigger in wins vs losses
   - Score patterns by: trigger_rate × win_correlation
4. Prune bottom 20% patterns by score

**Expected Outcome**:
- Fewer patterns (65-70 total, down from 75)
- Higher signal-to-noise ratio
- Potentially better differentiation from baseline

**Files to Modify**:
- `patterns/breaking.yaml` (remove patterns)
- New: `evals/pattern_scoring.py` (analysis tool)

**Risk**: Might remove patterns that help in edge cases

---

## Recommended Immediate Action

**Priority 1 (Market Readiness)** is largely complete:
1. ✅ Production-ready performance (90.7% tie rate achieved)
2. ✅ Published to PyPI (`pip install gremlin-critic`)
3. ✅ Phase 1 API released (v0.2.0)
4. ✅ Real-world validation: httpx critique validated 16.4% against real issues
5. ✅ Architecture diagrams created

**Next: Focus on Priority 1.5 (Evaluation Maturity)** because:
1. Current evals measure consistency, not correctness — this is a blind spot
2. `validator.py` is already written but disconnected — highest-impact quick win
3. Golden set methodology proven by httpx validation — needs formalization
4. Must improve measurement before optimizing further (Priority 2/3/4)

**Timeline**:
- **Week 1**: Wire `validator.py` + add deterministic quality checks (Steps 1-2)
- **Week 2**: Formalize golden sets + temperature control (Steps 3-4)
- **Week 3**: Integrate into eval CI (Step 5)

**Decision Point**: After eval maturity is in place, use the improved metrics to decide if Priority 2 (Tier 2 patterns) or Priority 3 (Agent enhancement) has more impact

---

## Success Metrics

### ✅ Phase 2 Tier 1 Achievement (EXCEEDED ALL TARGETS)
- ✅ Tie rate: 90.7% (target was 80%)
- ✅ Win/tie rate: 98.1% (exceeded 87% baseline)
- ✅ Claude wins reduced: 19% → 1.9% (90% reduction)
- ✅ Severity ratings aligned: CRITICAL patterns trigger at 85-90% confidence
- ✅ No regressions: Gremlin wins stable at 7.4%

### Market Readiness Success Criteria
- [x] Package published to PyPI (`gremlin-critic`)
- [x] Phase 1 API released (v0.2.0)
- [x] Examples directory with usage examples
- [x] Quickstart guide created
- [x] Architecture diagrams (draw.io + PNG)
- [x] Real-world critiques: httpx (73 risks), pydantic (58), celery (47)
- [x] httpx issue validation: 12/73 risks map to real open issues

### Evaluation Maturity Success Criteria
- [ ] `validator.py` integrated into `api.py` pipeline
- [ ] `--validate` flag functional in CLI
- [ ] Deterministic pre-checks: format, min count, domain relevance
- [ ] Golden set: 12 httpx verified risks as ground truth fixtures
- [ ] Golden set recall measured per eval run
- [ ] Temperature control in eval runner (0.3 + 1.0)
- [ ] Eval CI runs golden set on PRs ([#12](https://github.com/abhi10/gremlin/issues/12))

### Long-term North Star
- **Differentiation**: Gremlin wins on domain-specific critical risks ✅
- **Consistency**: 90%+ consistency across trials ✅ (91% achieved)
- **Quality**: 90%+ tie rate with baseline Claude ✅ (90.7% achieved)
- **Value-add**: Clear wins on infrastructure/frontend/security domains ✅
- **Adoption**: Real-world usage and feedback from 10+ users 🎯

---

## Resources

### Key Files
- Pattern library: `gremlin/patterns/breaking.yaml` (107 patterns, 14 domains)
- System prompt: `gremlin/prompts/system.md`
- API: `gremlin/api.py` (Gremlin class, Risk, AnalysisResult)
- Validator: `gremlin/core/validator.py` (LLM-as-judge, needs integration)
- Eval runner: `evals/run_eval.py`
- Eval metrics: `evals/metrics.py`
- Critiques: `evals/critiques/` (httpx, pydantic, celery)
- Architecture: `docs/architecture.drawio` (draw.io, 2 tabs)

### Documentation
- **Phase 1**: `evals/phase1_pattern_analysis.md`, `evals/PHASE1_*.md`
- **Phase 2 Tier 1**: `evals/PHASE2_*.md` (5 files documenting journey to 90.7% tie rate)
- **Changelog**: `CHANGELOG.md` (v0.1.0 features)
- **Roadmap**: This file

### Commands
```bash
# Run full eval suite (sequential to avoid rate limits)
./evals/run_eval.py --all --trials 1

# Run full eval suite (parallel with safe worker count)
./evals/run_eval.py --all --trials 1 --parallel --workers 2

# Run specific domain
./evals/run_eval.py evals/cases/real-world/infrastructure-*.yaml --trials 3

# Test single case with detailed output
./evals/run_eval.py evals/cases/real-world/<case>.yaml --trials 1

# Generate eval cases from collected projects
python evals/generate_cases.py

# Collect more real-world projects
python evals/collect_projects.py --total 30
```

---

**Current Status**: Market Readiness ✅ Complete | Moving to Evaluation Maturity (Priority 1.5)
