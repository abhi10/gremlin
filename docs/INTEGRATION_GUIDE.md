# Gremlin Integration Guide

## Decision Tree: CLI vs Agent

### Use Gremlin CLI when:

✅ Analyzing a feature from PRD/specification
✅ Early design phase (no code yet)
✅ Want comprehensive feature-scope analysis
✅ Need to share report with stakeholders
✅ Doing exploratory QA on planned features

**Examples**:
- `gremlin review "payment integration with Stripe"`
- `gremlin review "auth migration" --context @design.md`
- CI/CD: `gremlin review "$FEATURE" --output json > risks.json`

### Use Gremlin Agent when:

✅ Reviewing actual code in Claude Code session
✅ PR review or pre-commit check
✅ Need line-specific risk identification
✅ Want code-focused deep dive
✅ Analyzing implementation details

**Examples**:
- "Review this PR for database risks"
- "Check this cache implementation for edge cases"
- "Any race conditions in this background job code?"

### Best Practice: Use Both

**Workflow**:
1. **Design phase**: CLI on PRD → Feature-scope risks
2. **Implementation**: Agent on code → Code-specific risks
3. **PR review**: Agent + optionally CLI with `--context @file.py`

## Agent + CLI Integration

The agent can invoke the CLI for enhanced analysis:

```markdown
In Claude Code:

User: "Review this checkout implementation"

Agent:
1. Performs code-focused review (embedded patterns)
2. Detects gremlin CLI installed
3. Runs: gremlin review "checkout" --context @src/checkout.py
4. Combines findings in final report
```

## Pattern Differences

| Aspect | CLI Patterns | Agent Patterns |
|--------|--------------|----------------|
| File | `patterns/breaking.yaml` | `patterns/code-review.yaml` |
| Count | 72 patterns | 45-50 patterns |
| Focus | Feature scope, user workflows | Code inspection, implementation |
| Domains | 12 domains | 10 domains + 3 agent-only |
| Agent-only | - | Caching, Background Jobs, Observability |
| CLI-only | Payments, Frontend, Infrastructure | - |

## Installation

**CLI only**:
```bash
pip install gremlin-qa
export ANTHROPIC_API_KEY=sk-ant-...
gremlin review "scope"
```

**Agent only** (no installation needed):
- Agent definition in `plugins/gremlin/agents/gremlin.md`
- Invoke in Claude Code sessions
- Works standalone, no CLI required

**Both** (recommended):
```bash
pip install gremlin-qa  # Gets CLI
# Agent automatically available in Claude Code
# Agent can invoke CLI when needed
```
