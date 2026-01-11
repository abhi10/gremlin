# Phase 1: Eval → Pattern Feedback Loop Analysis

**Date**: 2026-01-10
**Objective**: Extract winning patterns from baseline Claude to improve Gremlin win rate

## Methodology

Analyzed 7 cases where baseline Claude outperformed Gremlin:
- 3 frontend cases (vuejs-vue-ENV, vuejs-vue-memory-stats, vuejs-vue-monitor)
- 2 infrastructure cases (modelcontextprotocol-servers)
- 1 deployment case (lobehub-lobe-chat-docker-pr-comment)
- 1 auth case (nhost-auth - excluded, Gremlin had technical error)

## Key Pattern Gaps Identified

### 1. Implicit Global Variables (HIGH IMPACT)
**Domain**: Frontend, JavaScript
**Frequency**: Appeared in all 3 frontend cases
**Confidence**: 95%

**What Claude caught**:
```javascript
// Variables without 'var' become global
formatElapsed: function(elapsed) {
  minutes = Math.floor(elapsed / 60);  // No var!
  seconds = elapsed % 60;              // Implicit global
}
```

**Impact**: Cross-function state pollution, memory leaks in SPAs, hard-to-debug timing issues

**Pattern to add**:
> What if variables are declared without var/let/const and become implicit globals?

---

### 2. Git Hooks Execution (CRITICAL IMPACT)
**Domain**: Infrastructure, Git operations
**Frequency**: 1 case but rated CRITICAL by Claude (95% confidence)
**Confidence**: 95%

**What Claude caught**:
- Operations like `git commit` and `git checkout` trigger hooks (pre-commit, post-commit, post-checkout)
- If repository is compromised with malicious hooks, operations execute arbitrary code with server privileges
- Gremlin completely missed this attack vector

**Pattern to add**:
> What if the repository contains malicious Git hooks that execute during operations?

---

### 3. TOCTOU (Time-of-Check-Time-of-Use) Race Conditions (HIGH IMPACT)
**Domain**: Security, File Operations
**Frequency**: 2 infrastructure cases
**Confidence**: 85%

**What Claude caught**:
- Path validation happens at time T1
- Git operation executes at time T2
- Between T1 and T2, attacker can replace directories with symlinks
- Bypasses security boundaries

**Pattern to add**:
> What if file/directory state changes between validation and actual operation (TOCTOU)?

---

### 4. Sensitive URLs in Public Comments/Logs (MEDIUM-HIGH IMPACT)
**Domain**: Security, Deployment
**Frequency**: 1 deployment case
**Confidence**: 80%

**What Claude caught**:
```javascript
dockerhubUrl: "https://internal-registry.company.com/path?token=abc123"
// Gets posted in public PR comment
```

**Impact**: Internal infrastructure exposure, credential leaks, attack surface mapping

**Pattern to add**:
> What if internal URLs, registry paths, or tokens are exposed in public comments/logs?

---

### 5. Mock/Test Code Deployed to Production (HIGH IMPACT)
**Domain**: Configuration, Deployment
**Frequency**: 1 frontend case but rated CRITICAL (95% confidence)
**Confidence**: 95%

**What Claude caught**:
```javascript
// Hardcoded test data generator
generateRow: function(dbname) {
  queries: ["SELECT blah FROM something", "SELECT foo FROM bar"]
  // Uses Math.random() for all metrics
}
```

**Impact**: Meaningless production metrics, masking real issues, misleading operations teams

**Pattern to add**:
> What if test/mock/fixture code is accidentally deployed to production?

---

### 6. Type Assumptions on Dynamic Data (MEDIUM IMPACT)
**Domain**: Input Validation, Type Safety
**Frequency**: 2 cases
**Confidence**: 85%

**What Claude caught**:
```javascript
const tags = JSON.parse(dockerMetaJson);
// Assumes tags[0] is string
tags[0].split(':')[1]  // Crashes if tags[0] is object/number
```

**Pattern to add**:
> What if parsed JSON contains unexpected types (objects instead of strings, arrays instead of primitives)?

---

### 7. Privilege Escalation via Service Permissions (MEDIUM IMPACT)
**Domain**: Security, Infrastructure
**Frequency**: 1 case
**Confidence**: 65%

**What Claude caught**:
- Service runs with elevated privileges
- Processes repositories owned by different users
- Operations could change file ownership/permissions unexpectedly

**Pattern to add**:
> What if the service runs with different privileges than the resources it accesses?

---

### 8. Information Disclosure via Error Messages (MEDIUM IMPACT)
**Domain**: Security
**Frequency**: 1 case
**Confidence**: 75%

**What Claude caught**:
- Git operation errors leak file paths, repository structure, system configuration
- Error messages propagated to clients reveal internal architecture

**Pattern to add**:
> What if error messages leak internal paths, configuration, or system architecture?

---

## Recommended Additions to patterns/breaking.yaml

### High Priority (Add Immediately)
1. Implicit global variables (frontend domain)
2. Git hooks execution (infrastructure/git domain - CRITICAL)
3. TOCTOU race conditions (security domain)
4. Sensitive URLs in public output (deployment/security domains)
5. Mock/test code in production (configuration domain)

### Medium Priority (Add in Phase 2)
6. Type assumptions on dynamic data (input_validation domain)
7. Privilege escalation via permissions (infrastructure domain)
8. Information disclosure via errors (security domain)

## Expected Impact

Based on the 7 cases analyzed:
- **Current**: Gremlin scores 0.8 on these cases (wins 0)
- **After Phase 1**: Expected to win 2-3 of these cases
- **Win rate improvement**: 7% → ~15-20% (if applied across all 54 cases)

## Next Steps

1. Add high-priority patterns to patterns/breaking.yaml
2. Re-run the 7 failed cases
3. Measure actual win rate improvement
4. If successful (>10% improvement), proceed to add medium-priority patterns
