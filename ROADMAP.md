# Gremlin Improvement Roadmap

**Last Updated**: January 10, 2026
**Current Status**: Phase 1 Complete ✅

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

## Next Steps: Three Paths Forward

### Path A: Phase 2 - Pattern Quality Expansion (Recommended)
**Effort**: Medium | **Impact**: High | **Risk**: Low

**Objective**: Add severity hints to 10-15 more high-impact patterns

**Steps**:
1. Analyze full eval suite results to identify patterns with incorrect severity
2. Add severity hints to top 10-15 patterns that:
   - Trigger frequently but with wrong severity
   - Have high confidence (85%+) from Claude in eval wins
   - Are domain-specific (not universal)
3. Run targeted validation on 5-10 cases
4. Measure aggregate improvement

**Expected Outcome**:
- Win rate: 74% tie → 80-85% tie (return to pre-Phase 1 baseline or better)
- Gremlin wins: 7% → 12-15%

**Files to Modify**:
- `patterns/breaking.yaml` (add severity hints)

**Validation**:
```bash
# Run targeted test cases with patterns prone to severity issues
./evals/run_eval.py evals/cases/real-world/frontend-*.yaml --trials 1
./evals/run_eval.py evals/cases/real-world/security-*.yaml --trials 1
```

---

### Path B: Agent Definition Enhancement (Alternative)
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

### Path C: Pattern Pruning + Quality Scoring (Advanced)
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

**Start with Path A (Phase 2)** because:
1. ✅ Proven approach (Phase 1 Revised worked)
2. ✅ Low risk (additive changes, backward compatible)
3. ✅ Clear validation path (test before full rollout)
4. ✅ Builds on existing success (severity hints effective)

**Timeline**:
- Week 1: Analyze full eval results, identify top 10-15 patterns
- Week 2: Add severity hints, test on 5-10 cases
- Week 3: Run full eval suite, measure improvement
- Week 4: Document learnings, merge if successful

**Decision Point**: After Phase 2 validation, decide if Path B or C needed

---

## Success Metrics

### Phase 2 Success Criteria
- ✅ Win/tie rate returns to 87%+ (pre-Phase 1 baseline)
- ✅ Gremlin wins increase by 5-8% absolute
- ✅ No regression on currently winning cases
- ✅ Severity ratings align with Claude's confidence levels (±10%)

### Long-term North Star
- **Differentiation**: Gremlin should win on domain-specific critical risks
- **Consistency**: 90%+ consistency across trials
- **Accuracy**: 95%+ pass rate on eval cases
- **Value-add**: Clear wins on infrastructure/frontend/security domains vs generic reasoning

---

## Questions to Resolve

1. **Should we keep all 4 Phase 1 documentation files or consolidate into one?**
   - Current: 4 files (23KB total)
   - Option: Merge into single `evals/EVAL_FEEDBACK_LEARNINGS.md`

2. **Should we create a pattern changelog to track severity hint additions?**
   - Would help understand which hints were added when
   - Could inform future pattern quality scoring

3. **Should we archive old eval results periodically?**
   - Current: 121 JSON files from Jan 10 testing
   - Proposal: Keep last 7 days, archive older results

---

## Resources

### Key Files
- Pattern library: `patterns/breaking.yaml`
- System prompt: `prompts/system.md`
- Eval runner: `evals/run_eval.py`
- Pattern loader: `gremlin/core/patterns.py`

### Documentation
- Phase 1 analysis: `evals/phase1_pattern_analysis.md`
- Phase 1 results: `evals/PHASE1_REPORT.md`
- Revised strategy: `evals/PHASE1_REVISED_STRATEGY.md`

### Commands
```bash
# Run full eval suite
./evals/run_eval.py --all --trials 1 --parallel

# Run specific domain
./evals/run_eval.py evals/cases/real-world/infrastructure-*.yaml --trials 3

# Test single case with detailed output
./evals/run_eval.py evals/cases/real-world/<case>.yaml --trials 1
```

---

**Next Step**: Review this roadmap, choose Path A/B/C, and confirm cleanup approach.
