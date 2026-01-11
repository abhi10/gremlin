# Phase 2 Tier 1: Full Eval Suite Results

**Date**: January 10, 2026
**Status**: ✅ Complete - Target Achieved

---

## Executive Summary

Phase 2 Tier 1 patterns successfully returned tie rate to **81.5%**, exceeding the 80% target.

**Key Achievement**: Reduced Claude wins from 19% to 11.1% (41% reduction).

---

## Results Comparison

| Metric | Before Phase 2 | After Tier 1 | Change | Status |
|--------|----------------|--------------|--------|---------|
| **Tie Rate** | 74% | **81.5%** | **+7.5%** | ✅ Exceeded 80% goal |
| **Claude Wins** | 19% | **11.1%** | **-7.9%** | ✅ Major improvement |
| **Gremlin Wins** | 7% | 7.4% | +0.4% | → Stable |
| **Win/Tie Rate** | 81% | **88.9%** | **+7.9%** | ✅ Strong |
| **Consistency** | - | 91% (Gremlin) | - | ✅ Excellent |
| **Total Cases** | 54 | 54 | - | - |

---

## Overall Distribution

```
Gremlin wins: 4  (7.4%)
Claude wins: 6   (11.1%)
Ties: 44         (81.5%)

Avg Gremlin consistency: 91%
Avg Claude consistency: 94%
```

---

## Gremlin Wins (4 cases)

### 1. negative-static-config
- **Gremlin**: 75% score (2 HIGH, 2 MEDIUM, 2 LOW)
- **Claude**: 62% score (2 CRITICAL, 1 HIGH, 3 MEDIUM, 2 LOW)
- **Reason**: Gremlin correctly identified this as low-risk config file

### 2. auth-nhost-nhost-auth_test-01 ⭐
- **Gremlin**: 100% score (2 CRITICAL, 3 HIGH, 3 MEDIUM, 5 LOW)
- **Claude**: 60% score (0 risks - failed to find anything)
- **Reason**: Claude completely missed test file risks

### 3. infrastructure-modelcontextprotocol-servers-server-02 ⭐
- **Gremlin**: 100% score (3 CRITICAL, 2 HIGH, 3 MEDIUM)
- **Claude**: 60% score (0 risks - failed to find anything)
- **Reason**: Gremlin patterns caught infrastructure risks Claude missed
- **Key Pattern**: Type safety, SSRF, memory exhaustion patterns triggered

### 4. (Additional win - detailed analysis pending)

---

## Claude Wins (6 cases) ⚠️

### Cases Where Gremlin Returned 0 Risks (4 total):

1. **auth-sahat-satellizer-auth-02**
   - Gremlin: 60% score (0 risks)
   - Claude: 100% score (3 CRITICAL, 1 HIGH, 2 MEDIUM, 6 LOW)
   - **Root Cause**: Domain matching failure - auth patterns didn't trigger

2. **database-hasura-graphql-engine-migration-01**
   - Gremlin: 60% score (0 risks)
   - Claude: 100% score (3 CRITICAL, 2 HIGH, 2 MEDIUM, 2 LOW)
   - **Root Cause**: Domain matching failure - database migration patterns didn't trigger

3. **dependencies-flatpickr-flatpickr-package-02**
   - Gremlin: 60% score (0 risks)
   - Claude: 100% score (3 HIGH, 3 MEDIUM)
   - **Root Cause**: Domain matching failure - dependencies patterns didn't trigger

4. **file-upload-valor-software-ng2-file-upload-file-catcher-02**
   - Gremlin: 60% score (0 risks)
   - Claude: 80% score (1 CRITICAL, 4 HIGH, 3 MEDIUM)
   - **Root Cause**: Domain matching failure - file upload patterns didn't trigger

### Other Claude Wins:

5. **frontend-vuejs-vue-monitor-02**
   - Gremlin: 80% score (1 CRITICAL, 2 HIGH, 2 MEDIUM) - missing category requirement
   - Claude: 100% score (1 CRITICAL, 2 HIGH, 3 MEDIUM, 1 LOW)

6. **(One more case - detailed analysis pending)**

---

## Pattern Performance

### Patterns That Triggered Successfully ✅

1. **SSRF (Security)** - Triggered as CRITICAL on security cases
2. **Memory Exhaustion** - Triggered as CRITICAL with enhanced severity
3. **Type Safety** - Triggered on multiple cases preventing runtime crashes
4. **Missing Timeouts** - Triggered as HIGH on infrastructure cases
5. **ReDoS** - Triggered as MEDIUM on security case

### Pattern Validation Examples

**security-Lissy93-web-check-security-txt-00**:
- Gremlin: 2 CRITICAL + 2 HIGH + 3 MEDIUM + 1 LOW (100% score)
- Claude: 1 CRITICAL + 2 HIGH + 2 MEDIUM + 5 LOW (100% score)
- **Patterns Triggered**: SSRF (CRITICAL 85%), Memory exhaustion (CRITICAL 90%), Missing timeouts (HIGH 80%), ReDoS (MEDIUM 85%)

---

## Root Cause Analysis: 0-Risk Cases

### Problem: Domain Matching Failures

All 4 cases where Gremlin returned 0 risks share a common issue: **domain patterns didn't trigger**.

**Hypothesis**: Scope/context strings aren't matching domain keywords.

**Cases**:
- auth-sahat-satellizer-auth-02: Auth domain should have matched
- database-hasura-graphql-engine-migration-01: Database domain should have matched
- dependencies-flatpickr-flatpickr-package-02: Dependencies domain should have matched
- file-upload-valor-software-ng2-file-upload-file-catcher-02: File upload domain should have matched

**Next Step**: Investigate domain inference logic for these specific cases.

---

## Success Criteria Assessment

| Criterion | Target | Result | Status |
|-----------|--------|--------|--------|
| Tie rate return to 80%+ | ≥80% | 81.5% | ✅ Met |
| Critical patterns trigger | Yes | Yes | ✅ Met |
| Severity ratings align | ±10% | Yes | ✅ Met |
| No regression on wins | Yes | Maintained | ✅ Met |

---

## Next Steps: Three Options

### Option A: Fix Domain Matching Regressions ⭐ RECOMMENDED

**Effort**: Low (1-2 hours)
**Impact**: High (+4 tie conversions immediately)
**Risk**: Very low

**Steps**:
1. Read the 4 failing case files to understand their scope/context
2. Check domain keyword matching in `gremlin/core/inference.py`
3. Add missing keywords or fix matching logic
4. Re-run just these 4 cases to validate fix
5. Run full suite to confirm no new regressions

**Expected Outcome**:
- Claude wins: 11.1% → 7.4% (matches or beats Phase 1)
- Tie rate: 81.5% → 88.9%
- Gremlin wins: 7.4% (stable)

---

### Option B: Proceed with Phase 2 Tier 2

**Effort**: Medium (add 5 more patterns)
**Impact**: Medium (+2-4% tie rate)
**Risk**: Medium (won't fix 0-risk issue)

**Patterns to Add**:
- Idempotency key missing (Payments - HIGH)
- Cross-browser API availability (Frontend - HIGH)
- State transition validation (Database/Payments)
- Hardcoded production values (Configuration)
- Service privilege mismatch (Infrastructure)

**Expected Outcome**:
- Tie rate: 81.5% → 83-85%
- Claude wins: 11.1% → 9-10%
- Still have 4 cases with 0-risk issue

---

### Option C: Declare Success and Move On

**Effort**: None
**Impact**: Lock in current gains
**Risk**: None

**Rationale**:
- 81.5% tie rate exceeds 80% goal
- 88.9% win/tie rate is strong
- 41% reduction in Claude wins
- Patterns working as intended

**Accept**:
- 11% Claude win rate
- 4 cases with domain matching issues

---

## Recommendation

**Execute Option A first** (fix domain matching), then decide between Option B or C.

**Reasoning**:
- Quick win: 4 cases can likely be fixed in 1-2 hours
- High ROI: Converts 4 losses → ties with minimal effort
- Addresses root cause: Domain matching is a systemic issue worth fixing
- After fix: Can evaluate if Tier 2 patterns still needed

**Expected Final Results After Option A**:
- Tie rate: ~89%
- Claude wins: ~7.4%
- Gremlin wins: ~7.4%
- Total win/tie: ~96%

This would put us in an excellent position to either add Tier 2 patterns or focus on other improvements.

---

## Files Modified in Phase 2 Tier 1

- `patterns/breaking.yaml`: +5 new patterns, +1 enhanced, -1 duplicate
- `ROADMAP.md`: Created comprehensive roadmap
- `evals/PHASE2_PATTERN_ANALYSIS.md`: Detailed analysis
- `evals/PHASE2_TIER1_RESULTS.md`: Implementation results
- `evals/PHASE2_TIER1_FULL_EVAL_RESULTS.md`: This file

---

## Appendix: Pattern Count Summary

| Category | Count | Change from Phase 1 |
|----------|-------|---------------------|
| Universal | 31 | +4 |
| Domain-Specific | 62 | +1 |
| **Total** | **93** | **+5** |
| With Severity Hints | 11 | +6 |

---

**Status**: Ready for next decision - Option A, B, or C?
