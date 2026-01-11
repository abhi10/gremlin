# Phase 2: Pattern Quality Expansion - Analysis

**Date**: January 10, 2026
**Objective**: Add severity hints to 10-15 high-impact patterns based on eval feedback

---

## Analysis Methodology

Building on Phase 1 analysis of 7 Claude wins, expanded to identify:
1. **Phase 1 Medium-Priority patterns** not yet added (3 patterns)
2. **Existing patterns** that trigger but with incorrect severity (5-7 patterns)
3. **Universal patterns** that are too generic and need specificity (3-5 patterns)

---

## Top 15 Patterns Needing Severity Hints

### Category A: Phase 1 Medium-Priority (Not Yet Added)

#### 1. Type Assumptions on Parsed Data ⭐ HIGH PRIORITY
**Current**: Missing from patterns
**Domain**: Input Validation
**Frequency**: 2 cases (deployment, frontend)
**Claude Confidence**: 85%

**Pattern to add**:
> What if parsed JSON/data contains unexpected types (object instead of string, null instead of array)? [Runtime crashes, type errors break critical flows]

**Example from evals**:
```javascript
const tags = JSON.parse(dockerMetaJson);
tags[0].split(':')[1]  // Crashes if tags[0] is object/number
```

---

#### 2. Hardcoded Values in Production Code ⭐ MEDIUM PRIORITY
**Current**: Partially covered by "test config differs from production"
**Domain**: Configuration
**Frequency**: 2 cases (payments, frontend)
**Claude Confidence**: 80%

**Pattern to enhance**:
> What if hardcoded IDs, tokens, or URLs in code reference real production resources? [Accidental modification of live data, security exposure]

**Example from evals**:
```javascript
const PAYMENT_INTENT_TEST_ID = 'pi_123'
// If this is a real Stripe ID, tests modify live payments
```

---

#### 3. Service Privilege Mismatch
**Current**: Missing from patterns
**Domain**: Infrastructure
**Frequency**: 1 case but HIGH severity
**Claude Confidence**: 65%

**Pattern to add**:
> What if service runs with elevated privileges but processes user-owned resources? [Unintended permission changes, security boundary violations]

---

### Category B: Existing Patterns Needing Severity Hints

#### 4. Memory Exhaustion Patterns ⭐ HIGH PRIORITY
**Current**: Multiple generic patterns exist
**Issue**: Rated as MEDIUM when should be HIGH/CRITICAL
**Frequency**: 5+ cases across domains

**Patterns to enhance with hints**:

**Resource Limits - Memory**:
> What if memory exhausted during large file/diff/response processing? [CRITICAL - DoS, service crash affecting all users]

**External Dependencies - Unbounded responses**:
> What if external API returns gigabytes of data without pagination? [Service OOM crash, cascading failures]

---

#### 5. API Authentication Missing in Tests ⭐ CRITICAL
**Current**: Not explicitly covered
**Domain**: Payments, API, Auth
**Frequency**: Payment tests case (CRITICAL 90%)
**Claude Confidence**: 90%

**Pattern to add**:
> What if test suite validates request structure but never tests authentication/authorization? [CRITICAL - security vulnerabilities ship to production undetected]

---

#### 6. Idempotency Key Missing ⭐ HIGH PRIORITY
**Current**: Exists in payments domain
**Issue**: Needs severity emphasis
**Domain**: Payments
**Frequency**: 1 case but HIGH impact
**Claude Confidence**: 75%

**Pattern to enhance**:
> What if idempotency key not properly implemented? [HIGH - duplicate payments, financial losses, customer chargebacks]

---

#### 7. State Transition Validation Missing
**Current**: Partially covered by state & data patterns
**Domain**: Payments, Database
**Frequency**: 1 case
**Claude Confidence**: 80%

**Pattern to add**:
> What if state transitions aren't validated (capture already-captured payment, cancel succeeded operation)? [Data inconsistencies, duplicate charges, failed refunds]

---

#### 8. SSRF (Server-Side Request Forgery) ⭐ CRITICAL
**Current**: Missing from security domain
**Domain**: Security
**Frequency**: 1 case (security.txt) but CRITICAL
**Claude Confidence**: 90%

**Pattern to add**:
> What if user-controlled URLs target internal services (localhost, cloud metadata, private IPs)? [CRITICAL - internal network scanning, cloud credential theft]

---

#### 9. Infinite Redirect/Retry Loops
**Current**: Partially covered by "retry storm"
**Domain**: External Dependencies
**Frequency**: 1 case
**Claude Confidence**: 80%

**Pattern to enhance**:
> What if external service returns infinite redirects or client retries indefinitely? [Resource exhaustion, connection pool depletion, cascading timeouts]

---

#### 10. Regex Catastrophic Backtracking (ReDoS) ⭐ HIGH PRIORITY
**Current**: "search query triggers catastrophic backtracking" (only in search domain)
**Domain**: Should be in Input Validation (universal)
**Frequency**: 1 case (security.txt) but applies broadly
**Claude Confidence**: 75%

**Pattern to add/enhance**:
> What if regex with nested quantifiers processes crafted input causing exponential backtracking? [HIGH - CPU exhaustion, application freeze, DoS]

---

#### 11. Prototype Pollution
**Current**: Missing from security domain
**Domain**: Security, Frontend
**Frequency**: 1 case but applies to JavaScript broadly
**Claude Confidence**: 70%

**Pattern to add**:
> What if object property assignment uses user-controlled keys like `__proto__` or `constructor`? [Prototype chain pollution affecting entire application]

---

#### 12. Missing Timeouts on Network Operations ⭐ MEDIUM-HIGH
**Current**: "latency spike causes timeout" (different issue)
**Domain**: External Dependencies
**Frequency**: 1 case but common issue
**Claude Confidence**: 85%

**Pattern to add**:
> What if HTTP/database operations have no timeout and server never responds? [Resource hanging, connection pool exhaustion over time]

---

#### 13. Cross-Browser API Availability
**Current**: "feature works in one browser but not another" (generic)
**Domain**: Frontend
**Frequency**: 1 case (memory stats)
**Claude Confidence**: 95%

**Pattern to enhance**:
> What if browser-specific APIs (performance.memory, WebRTC) are used without fallback detection? [HIGH - silent failures in Firefox/Safari, false confidence monitoring works]

---

#### 14. Normalization/Scaling Threshold Obsolescence
**Current**: Missing entirely
**Domain**: Frontend, Configuration
**Frequency**: 1 case but relevant to monitoring/visualization
**Claude Confidence**: 90%

**Pattern to add**:
> What if hardcoded normalization thresholds (30MB heap, 1000 QPS) become obsolete as scale increases? [Visualization becomes meaningless, monitoring loses effectiveness]

---

#### 15. DOM Manipulation Without Existence Checks
**Current**: Generic "null reference" covered
**Domain**: Frontend
**Frequency**: Multiple cases
**Claude Confidence**: 75%

**Pattern to enhance**:
> What if DOM manipulation assumes elements exist without checking (querySelector returns null)? [Runtime crashes, broken UI initialization, poor user experience]

---

## Priority Ranking for Phase 2

### Tier 1: Add Immediately (Critical Gaps)
1. ✅ Type assumptions on parsed data
2. ✅ API authentication missing in tests (CRITICAL)
3. ✅ SSRF vulnerabilities
4. ✅ Memory exhaustion (enhance existing)
5. ✅ ReDoS catastrophic backtracking

### Tier 2: Add Soon (High Impact)
6. ✅ Idempotency key missing (enhance existing)
7. ✅ Hardcoded production values
8. ✅ Cross-browser API availability (enhance)
9. ✅ Missing timeouts on network ops
10. ✅ Service privilege mismatch

### Tier 3: Consider (Medium Impact)
11. State transition validation
12. Infinite redirect/retry loops (enhance existing)
13. Prototype pollution
14. Normalization threshold obsolescence
15. DOM manipulation without checks (enhance)

---

## Recommended Approach

**Phase 2A** (Immediate - Tier 1):
- Add 5 critical patterns with severity hints
- Enhance 2 existing patterns (memory, ReDoS)
- **Total**: +5 new, ~2 enhanced

**Phase 2B** (Follow-up - Tier 2):
- Add 3 more patterns
- Enhance 2 existing patterns
- **Total**: +3 new, ~2 enhanced

**Phase 2C** (Optional - Tier 3):
- Based on Phase 2A/2B results
- Add remaining 5 if clear value

---

## Expected Outcomes

### Phase 2A (Tier 1)
- **Before**: 74% tie rate, 19% Claude wins
- **After**: 78-82% tie rate, 12-15% Claude wins
- **Gremlin wins**: 7% → 10-12%

### Phase 2B (Tier 2)
- **After**: 82-85% tie rate, 8-12% Claude wins
- **Gremlin wins**: 10-12% → 12-15%

### Success Criteria
- ✅ Return to 80%+ tie rate (pre-Phase 1 baseline)
- ✅ Critical patterns (SSRF, auth testing, type safety) trigger appropriately
- ✅ Severity ratings align with Claude's confidence (±10%)
- ✅ No regression on existing winning cases

---

## Next Steps

1. ✅ Review this analysis with user
2. ⏳ Implement Phase 2A (5 patterns + 2 enhancements)
3. ⏳ Test on 5-10 targeted cases (security, payments, frontend)
4. ⏳ If successful, proceed with Phase 2B
5. ⏳ Run full eval suite after Phase 2B complete

---

**Ready for implementation**: Tier 1 patterns identified and prioritized.
