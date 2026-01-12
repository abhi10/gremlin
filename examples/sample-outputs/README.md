# Sample Gremlin Outputs

This directory contains real examples of Gremlin output in all three supported formats.

## Files

| File | Format | Scope | Description |
|------|--------|-------|-------------|
| [auth-example-rich.txt](auth-example-rich.txt) | Rich | Authentication | Terminal output with colors and formatting |
| [checkout-example.md](checkout-example.md) | Markdown | Checkout Flow | Markdown format for documentation |
| [api-example.json](api-example.json) | JSON | API Search | JSON format for automation |

## Format Examples

### Rich Format (Terminal Output)

**File:** [auth-example-rich.txt](auth-example-rich.txt)

**Features:**
- Color-coded severity indicators (🔴 CRITICAL, 🟠 HIGH, 🟡 MEDIUM)
- Unicode box drawing for visual separation
- Confidence scores visible inline
- Summary statistics at bottom
- Execution time included

**Use Cases:**
- Interactive terminal usage
- Development reviews
- Demos and presentations

**Generate:**
```bash
gremlin review "user authentication with JWT" > output.txt
```

### Markdown Format

**File:** [checkout-example.md](checkout-example.md)

**Features:**
- Standard markdown syntax
- Proper heading hierarchy (H1, H2, H3)
- Blockquotes for "what if?" questions
- Bold emphasis for impact
- Clean, readable structure

**Use Cases:**
- README files
- GitHub PR comments
- Documentation sites (Confluence, Notion)
- Email reports
- Slack/Discord formatted messages

**Generate:**
```bash
gremlin review "checkout flow with Stripe" --output md > checkout-risks.md
```

### JSON Format

**File:** [api-example.json](api-example.json)

**Features:**
- Structured, parseable data
- Consistent schema across all outputs
- Metadata included (timestamp, model, config)
- Aggregated statistics (by severity, by domain)
- Execution time tracking

**Use Cases:**
- CI/CD pipelines
- Custom tooling integration
- Database storage
- Analytics dashboards
- Automated processing

**Generate:**
```bash
gremlin review "REST API search" --output json > api-risks.json
```

## Schema Reference

### JSON Schema

```json
{
  "scope": "string",              // User-provided scope
  "timestamp": "ISO 8601",        // When analysis was run
  "model": "string",              // Claude model used
  "config": {
    "depth": "quick|deep",        // Analysis depth
    "threshold": 0-100            // Confidence threshold
  },
  "risks": [
    {
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "confidence": 0-100,
      "title": "string",
      "question": "string",       // The "what if?" scenario
      "impact": "string",         // Concrete impact description
      "domains": ["string"]       // Relevant domains
    }
  ],
  "summary": {
    "total": number,
    "by_severity": {
      "CRITICAL": number,
      "HIGH": number,
      "MEDIUM": number,
      "LOW": number
    },
    "by_domain": {
      "domain_name": number
    },
    "avg_confidence": number
  },
  "execution_time_seconds": number
}
```

## Severity Indicators

All formats use consistent severity levels:

| Severity | Emoji | Threshold | Description |
|----------|-------|-----------|-------------|
| CRITICAL | 🔴 | 90-100% | Immediate production issues, data loss, security breaches |
| HIGH | 🟠 | 75-89% | Significant impact, user-facing problems |
| MEDIUM | 🟡 | 60-74% | Moderate issues, degraded experience |
| LOW | 🟢 | 40-59% | Minor concerns, edge cases |

## Reading the Examples

### Authentication Example (Rich Format)

**Highlights:**
- 3 CRITICAL risks (JWT expiration, timing attacks, rate limiting)
- 3 HIGH risks (session management, algorithm confusion, token reuse)
- 2 MEDIUM risks (email verification, secret storage)
- Total: 8 scenarios covering auth and security domains

**Key Patterns Triggered:**
- JWT security patterns
- Rate limiting patterns
- Session management patterns
- Cryptographic timing patterns

### Checkout Example (Markdown Format)

**Highlights:**
- 3 CRITICAL risks (webhook race, inventory, idempotency)
- 3 HIGH risks (session expiry, double-click, webhook verification)
- 3 MEDIUM risks (timeouts, price recalc, cleanup)
- Total: 9 scenarios covering payments, concurrency, and database domains

**Key Patterns Triggered:**
- Payment processing patterns
- Race condition patterns
- State synchronization patterns
- Webhook security patterns

### API Example (JSON Format)

**Highlights:**
- 0 CRITICAL risks (well-designed API, but needs improvements)
- 3 HIGH risks (SQL injection, rate limiting, unbounded results)
- 3 MEDIUM risks (indexing, auth, query complexity)
- 1 LOW risk (caching)
- Average confidence: 81.1%

**Key Patterns Triggered:**
- SQL injection patterns
- Rate limiting patterns
- Database performance patterns
- API security patterns

## Generating Your Own Examples

### Example 1: Authentication Review

```bash
# Rich format (terminal)
gremlin review "OAuth 2.0 authentication flow"

# Markdown (for docs)
gremlin review "OAuth 2.0 authentication flow" --output md > oauth-risks.md

# JSON (for automation)
gremlin review "OAuth 2.0 authentication flow" --output json > oauth-risks.json
```

### Example 2: With Context

```bash
# Add tech stack context
gremlin review "checkout flow" \
  --context "Next.js, Stripe Payment Intents, PostgreSQL, Redis" \
  --output md > checkout-risks.md
```

### Example 3: From Code Changes

```bash
# Analyze PR diff
git diff main...feature-branch | \
  gremlin review "PR changes" \
  --context - \
  --output json > pr-risks.json
```

## Processing JSON Output

### Extract CRITICAL Risks Only

```bash
jq '.risks[] | select(.severity == "CRITICAL")' api-example.json
```

### Count Risks by Severity

```bash
jq '.summary.by_severity' api-example.json
```

### List All Risk Titles

```bash
jq -r '.risks[].title' api-example.json
```

### Filter High Confidence Risks

```bash
jq '.risks[] | select(.confidence >= 90)' api-example.json
```

## Comparing Outputs

All three examples demonstrate:

1. **Consistent Risk Structure:** Same information across formats
2. **Severity Accuracy:** Appropriate severity levels based on impact
3. **Domain Coverage:** Multiple domains identified per risk
4. **Actionable Insights:** Clear "what if?" questions and concrete impacts

## Next Steps

- **Try different scopes:** See what risks Gremlin finds for your features
- **Experiment with formats:** Find the right format for your workflow
- **Add context:** Get more specific risks with tech stack details
- **Integrate with tools:** Use JSON format for custom processing

## Related Documentation

- [Basic Usage Examples](../basic-usage.md)
- [Output Formats Guide](../output-formats.md)
- [CI/CD Integration](../ci-integration.md)
- [Using Context](../with-context.md)
