# Output Formats

Gremlin supports three output formats optimized for different use cases.

## Format Options

| Format | Use Case | Command Flag |
|--------|----------|--------------|
| **Rich** (default) | Terminal viewing | `--output rich` |
| **Markdown** | Documentation, PR comments | `--output md` |
| **JSON** | Tool integration, automation | `--output json` |

## Rich Format (Default)

Colorful, formatted terminal output with emoji indicators.

```bash
gremlin review "checkout flow"
```

**Output:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Risk Scenarios for: checkout flow                                           │
└─────────────────────────────────────────────────────────────────────────────┘

🔴 CRITICAL (95% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Webhook Race Condition

  What if the Stripe webhook arrives before the order record is committed?

  Impact: Payment captured but order not created. Customer charged without record.
  Domain: payments, concurrency


🟠 HIGH (87% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Double Submit on Payment Button

  What if the user clicks "Pay Now" twice rapidly?

  Impact: Potential duplicate charges.
  Domain: payments, concurrency, frontend


🟡 MEDIUM (72% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Abandoned Cart Cleanup

  What if carts are never cleaned up after checkout failures?

  Impact: Database bloat from abandoned cart records.
  Domain: database

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Found 3 risk scenarios
Severity breakdown: 1 CRITICAL, 1 HIGH, 1 MEDIUM
```

**Features:**
- Color-coded severity (🔴 CRITICAL, 🟠 HIGH, 🟡 MEDIUM, 🟢 LOW)
- Unicode borders and separators
- Confidence scores visible
- Summary statistics

**Best for:**
- Interactive terminal usage
- Quick reviews during development
- Presentations and demos

## Markdown Format

Clean markdown suitable for documentation and sharing.

```bash
gremlin review "checkout flow" --output md
```

**Output:**

```markdown
# Risk Scenarios for: checkout flow

## 🔴 CRITICAL (95% confidence)

### Webhook Race Condition

> What if the Stripe webhook arrives before the order record is committed?

**Impact:** Payment captured but order not created. Customer charged without record.

**Domain:** payments, concurrency

---

## 🟠 HIGH (87% confidence)

### Double Submit on Payment Button

> What if the user clicks "Pay Now" twice rapidly?

**Impact:** Potential duplicate charges.

**Domain:** payments, concurrency, frontend

---

## 🟡 MEDIUM (72% confidence)

### Abandoned Cart Cleanup

> What if carts are never cleaned up after checkout failures?

**Impact:** Database bloat from abandoned cart records.

**Domain:** database

---

**Summary:** Found 3 risk scenarios (1 CRITICAL, 1 HIGH, 1 MEDIUM)
```

**Features:**
- Standard markdown syntax
- Preserves severity indicators (emojis)
- Proper heading hierarchy
- Formatted blockquotes and emphasis

**Best for:**
- README.md files
- GitHub PR comments
- Documentation sites
- Confluence/Notion pages
- Email reports

### Save to File

```bash
gremlin review "checkout flow" --output md > risks.md
```

### Append to Existing Docs

```bash
gremlin review "auth flow" --output md >> PROJECT_RISKS.md
```

## JSON Format

Structured data for programmatic processing.

```bash
gremlin review "checkout flow" --output json
```

**Output:**

```json
{
  "scope": "checkout flow",
  "timestamp": "2026-01-11T14:30:00Z",
  "risks": [
    {
      "severity": "CRITICAL",
      "confidence": 95,
      "title": "Webhook Race Condition",
      "question": "What if the Stripe webhook arrives before the order record is committed?",
      "impact": "Payment captured but order not created. Customer charged without record.",
      "domains": ["payments", "concurrency"]
    },
    {
      "severity": "HIGH",
      "confidence": 87,
      "title": "Double Submit on Payment Button",
      "question": "What if the user clicks \"Pay Now\" twice rapidly?",
      "impact": "Potential duplicate charges.",
      "domains": ["payments", "concurrency", "frontend"]
    },
    {
      "severity": "MEDIUM",
      "confidence": 72,
      "title": "Abandoned Cart Cleanup",
      "question": "What if carts are never cleaned up after checkout failures?",
      "impact": "Database bloat from abandoned cart records.",
      "domains": ["database"]
    }
  ],
  "summary": {
    "total": 3,
    "by_severity": {
      "CRITICAL": 1,
      "HIGH": 1,
      "MEDIUM": 1,
      "LOW": 0
    }
  }
}
```

**Features:**
- Structured, parseable data
- Consistent schema
- Timestamp for tracking
- Aggregated statistics

**Best for:**
- CI/CD pipelines
- Custom tooling integration
- Database storage
- Analytics dashboards
- Slack/Discord bot integration

### Save to File

```bash
gremlin review "checkout flow" --output json > risks.json
```

### Pretty Print

```bash
gremlin review "checkout flow" --output json | jq '.'
```

## Use Case Examples

### Use Case 1: PR Comment Automation

Generate markdown for GitHub PR comments:

```bash
#!/bin/bash
# .github/workflows/gremlin-review.sh

REVIEW=$(gremlin review "PR changes" --context - --output md <<< "$(git diff origin/main)")

gh pr comment $PR_NUMBER --body "$REVIEW"
```

### Use Case 2: Risk Dashboard

Collect risks as JSON for dashboard:

```bash
#!/bin/bash
# scripts/collect-risks.sh

FEATURES=("checkout" "auth" "profile" "search")

for feature in "${FEATURES[@]}"; do
  gremlin review "$feature flow" --output json > "data/risks-$feature.json"
done

# Aggregate for dashboard
jq -s '.' data/risks-*.json > dashboard/all-risks.json
```

### Use Case 3: Documentation Generation

Build risk documentation:

```bash
#!/bin/bash
# scripts/generate-risk-docs.sh

echo "# Project Risk Assessment" > docs/RISKS.md
echo "" >> docs/RISKS.md
echo "Generated: $(date)" >> docs/RISKS.md
echo "" >> docs/RISKS.md

gremlin review "authentication system" --output md >> docs/RISKS.md
echo "" >> docs/RISKS.md

gremlin review "payment processing" --output md >> docs/RISKS.md
echo "" >> docs/RISKS.md

gremlin review "data storage" --output md >> docs/RISKS.md
```

### Use Case 4: Slack Notifications

Post critical risks to Slack:

```bash
#!/bin/bash
# scripts/notify-critical-risks.sh

RISKS=$(gremlin review "production deployment" --output json)

CRITICAL_COUNT=$(echo "$RISKS" | jq '.summary.by_severity.CRITICAL')

if [ "$CRITICAL_COUNT" -gt 0 ]; then
  MESSAGE="⚠️ Found $CRITICAL_COUNT critical risks in production deployment review"
  curl -X POST $SLACK_WEBHOOK_URL \
    -H 'Content-Type: application/json' \
    -d "{\"text\": \"$MESSAGE\", \"attachments\": [{\"text\": \"$RISKS\"}]}"
fi
```

### Use Case 5: Terminal vs File Output

Interactive review in terminal, save to file:

```bash
# View in terminal
gremlin review "checkout flow"

# Also save for documentation
gremlin review "checkout flow" --output md > docs/checkout-risks.md
gremlin review "checkout flow" --output json > data/checkout-risks.json
```

## Format Comparison

### Same Input

```bash
gremlin review "file upload for profile pictures"
```

### Rich Output (Terminal)

```
🔴 CRITICAL (93% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Unrestricted File Upload

  What if an attacker uploads a .php or .jsp file disguised as an image?

  Impact: Remote code execution. Server compromise if file is executed.
  Domain: file_upload, security
```

### Markdown Output

```markdown
## 🔴 CRITICAL (93% confidence)

### Unrestricted File Upload

> What if an attacker uploads a .php or .jsp file disguised as an image?

**Impact:** Remote code execution. Server compromise if file is executed.

**Domain:** file_upload, security
```

### JSON Output

```json
{
  "severity": "CRITICAL",
  "confidence": 93,
  "title": "Unrestricted File Upload",
  "question": "What if an attacker uploads a .php or .jsp file disguised as an image?",
  "impact": "Remote code execution. Server compromise if file is executed.",
  "domains": ["file_upload", "security"]
}
```

## Advanced JSON Processing

### Filter by Severity

```bash
# Only CRITICAL risks
gremlin review "auth" --output json | jq '.risks[] | select(.severity == "CRITICAL")'
```

### Extract Titles

```bash
# List all risk titles
gremlin review "checkout" --output json | jq -r '.risks[].title'
```

### Count by Domain

```bash
# Risk count per domain
gremlin review "API" --output json | \
  jq '.risks[].domains[]' | \
  sort | uniq -c | sort -rn
```

### High Confidence Only

```bash
# Risks with 90%+ confidence
gremlin review "payment" --output json | \
  jq '.risks[] | select(.confidence >= 90)'
```

## Combining Formats

Run multiple formats for different audiences:

```bash
#!/bin/bash
SCOPE="checkout flow"

# Terminal view for dev
gremlin review "$SCOPE"

# Markdown for documentation
gremlin review "$SCOPE" --output md > docs/checkout-risks.md

# JSON for analytics
gremlin review "$SCOPE" --output json > data/checkout-risks.json

# Summary in terminal
echo "📊 Analysis complete:"
echo "  - Markdown: docs/checkout-risks.md"
echo "  - JSON: data/checkout-risks.json"
```

## Best Practices

### 1. Choose Format by Use Case

- **Interactive development:** Rich (default)
- **Documentation/sharing:** Markdown
- **Automation/integration:** JSON

### 2. Consistent File Naming

```bash
# Use timestamp for tracking
DATE=$(date +%Y%m%d-%H%M%S)
gremlin review "auth" --output json > "risks/auth-$DATE.json"
```

### 3. Version Control for Markdown

```bash
# Track risk evolution
gremlin review "checkout" --output md > docs/risks/checkout.md
git add docs/risks/checkout.md
git commit -m "docs: update checkout flow risk assessment"
```

### 4. JSON Schema Validation

```bash
# Validate JSON output structure
gremlin review "auth" --output json | jq -e '.risks | length > 0'
```

## Next Steps

- **Integration examples:** See [ci-integration.md](ci-integration.md)
- **Sample outputs:** Check [sample-outputs/](sample-outputs/) directory
- **Context usage:** See [with-context.md](with-context.md)
- **Basic usage:** Back to [basic-usage.md](basic-usage.md)
