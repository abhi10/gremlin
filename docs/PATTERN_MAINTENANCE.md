# Pattern Maintenance Guide

## Classification Criteria

### Code-Focused Pattern
**Goes in**: `patterns/code-review.yaml` (agent)

**Characteristics**:
- Requires reading actual code to assess
- Looks for specific code patterns (N+1 queries, lock ordering)
- Needs line-by-line analysis
- Examples:
  - "What if N+1 queries cause connection pool exhaustion?"
  - "What if concurrent transactions deadlock from opposing lock order?"
  - "What if config loaded at import time before env vars set?"

### Feature-Focused Pattern
**Goes in**: `patterns/breaking.yaml` (CLI only)

**Characteristics**:
- Applicable from feature description alone
- Asks about workflow/user behavior
- Doesn't need code to identify
- Examples:
  - "What if user clicks Pay button twice rapidly?"
  - "What if webhook arrives before local transaction commits?"
  - "What if user refreshes page during payment redirect?"

### Universal Pattern
**Goes in**: Both files

**Characteristics**:
- Always applicable regardless of context
- Examples:
  - "What if input is null/empty?"
  - "What if disk fills up?"
  - "What if external API times out?"

## Adding New Patterns

### Decision Tree

```
New pattern identified
    │
    ├─> Can assess from PRD/feature description alone?
    │   └─> YES → Add to breaking.yaml only (CLI)
    │
    └─> NO → Requires code inspection?
            ├─> YES → Add to code-review.yaml (Agent)
            │         Also add to breaking.yaml if feature-applicable
            │
            └─> UNIVERSAL → Add to both files
```

### Process

1. **Identify domain**: Auth, Database, Caching, etc.
2. **Classify**: Code-focused, feature-focused, or universal
3. **Add to appropriate file(s)**:
   - Code-focused → `code-review.yaml`
   - Feature-focused → `breaking.yaml`
   - Universal → both files
4. **Update agent markdown**: If code-review.yaml changed
5. **Test**: Run evals to validate pattern effectiveness
6. **Document**: Add example scenario and source

### Example Addition

**New pattern**: "What if metric cardinality explodes from user IDs in labels?"

**Classification**: Code-focused (requires seeing metric instrumentation code)

**Domain**: Observability

**Add to**:
- ✅ `patterns/code-review.yaml` under `observability` domain
- ❌ `patterns/breaking.yaml` (not feature-focused)
- ✅ `plugins/gremlin/agents/gremlin.md` (update Observability section)

## Quarterly Sync Process

**Schedule**: Last week of each quarter (Mar, Jun, Sep, Dec)

**Steps**:
1. **Review universal patterns**: Ensure identical in both files
2. **Check for drift**: Any patterns added to one file but not the other?
3. **Reclassify if needed**: Patterns that should move between files
4. **Domain coverage**: New domains added to CLI or agent?
5. **Run comparative evals**: CLI vs agent quality check
6. **Update documentation**: CLAUDE.md, integration guide

**Tools**:
```bash
# Compare universal patterns
diff <(yq '.universal' patterns/breaking.yaml) \
     <(yq '.universal' patterns/code-review.yaml)

# Count patterns by domain
yq '.domain_specific | keys' patterns/breaking.yaml
yq '.domain_specific | keys' patterns/code-review.yaml
```

## Ownership

- **Patterns**: Same maintainer for both files
- **Agent markdown**: Sync with code-review.yaml after pattern changes
- **Evals**: Run after any pattern modifications
