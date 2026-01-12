# Gremlin Examples

This directory contains comprehensive examples and usage patterns for Gremlin.

## Quick Navigation

| Guide | Description |
|-------|-------------|
| [basic-usage.md](basic-usage.md) | Common usage patterns for everyday QA scenarios |
| [with-context.md](with-context.md) | Adding context for more specific risk analysis |
| [output-formats.md](output-formats.md) | Using rich, markdown, and JSON outputs |
| [ci-integration.md](ci-integration.md) | Integrating Gremlin into CI/CD pipelines |
| [sample-outputs/](sample-outputs/) | Real Gremlin output examples |

## Getting Started

If you're new to Gremlin, start here:

1. **[Basic Usage](basic-usage.md)** - Learn the fundamentals:
   - Authentication flow analysis
   - Payment processing reviews
   - File upload security
   - Database query analysis
   - API endpoint reviews
   - Deployment configuration checks

2. **[Using Context](with-context.md)** - Provide tech stack details:
   - Direct string context
   - File reference context
   - Stdin/pipe context
   - Best practices for context usage

3. **[Output Formats](output-formats.md)** - Choose the right format:
   - Rich (colorful terminal output)
   - Markdown (documentation/PR comments)
   - JSON (automation/tooling)

4. **[CI Integration](ci-integration.md)** - Automate reviews:
   - GitHub Actions
   - GitLab CI/CD
   - CircleCI, Jenkins, Azure DevOps
   - Pre-commit hooks

## Common Scenarios

### Scenario 1: Review a Feature

```bash
gremlin review "checkout flow with Stripe payment"
```

### Scenario 2: Analyze Code Changes

```bash
git diff | gremlin review "PR changes" --context -
```

### Scenario 3: Deep Security Review

```bash
gremlin review "authentication system" --depth deep --threshold 85
```

### Scenario 4: Generate Documentation

```bash
gremlin review "payment processing" --output md > docs/payment-risks.md
```

### Scenario 5: CI/CD Integration

```yaml
# GitHub Actions
- run: |
    git diff origin/main...HEAD | \
    gremlin review "PR changes" --context - --output md >> $GITHUB_STEP_SUMMARY
```

## Real-World Examples

See [sample-outputs/](sample-outputs/) for complete examples with actual Gremlin output:

- Authentication system risks
- Payment processing vulnerabilities
- File upload security issues
- API endpoint concerns
- Database query problems

## Example Workflows

### Development Workflow

```bash
# 1. Design phase - review feature scope
gremlin review "new user registration feature"

# 2. Implementation - review specific code
gremlin review "registration logic" --context @src/auth/register.ts

# 3. PR review - analyze changes
git diff main | gremlin review "registration PR" --context -
```

### Security Audit Workflow

```bash
# Run comprehensive security review
FEATURES=("auth" "payments" "file_upload" "api" "database")

for feature in "${FEATURES[@]}"; do
  gremlin review "$feature security" \
    --depth deep \
    --threshold 90 \
    --output md > "security-audit-$feature.md"
done
```

### Documentation Workflow

```bash
# Generate risk documentation for all major features
echo "# Risk Assessment" > RISKS.md
echo "Generated: $(date)" >> RISKS.md

gremlin review "authentication" --output md >> RISKS.md
gremlin review "payments" --output md >> RISKS.md
gremlin review "data storage" --output md >> RISKS.md
```

## Tips for Effective Usage

### 1. Be Specific with Scope

**Good:**
- "checkout flow with Stripe webhooks and inventory updates"
- "JWT authentication with Redis sessions"

**Less Effective:**
- "the app"
- "backend"

### 2. Provide Context

**Good:**
```bash
gremlin review "auth" --context "Using JWT, Redis, PostgreSQL, bcrypt"
```

**Better:**
```bash
gremlin review "auth" --context @src/auth/login.ts
```

### 3. Adjust Threshold by Phase

- Design phase: `--threshold 70` (explore more scenarios)
- Pre-production: `--threshold 90` (focus on critical)

### 4. Use Appropriate Depth

- Quick review: `--depth quick` (default, faster)
- Thorough analysis: `--depth deep` (more scenarios)

## Pattern Coverage

Gremlin includes **93 curated patterns** across 11 domains:

- **auth** (12 patterns): Authentication, sessions, tokens
- **payments** (8 patterns): Checkout, billing, refunds
- **file_upload** (6 patterns): File handling, validation
- **database** (15 patterns): Queries, transactions, migrations
- **api** (10 patterns): Rate limiting, endpoints
- **deployment** (7 patterns): Config, containers
- **infrastructure** (8 patterns): Servers, resources
- **search** (5 patterns): Indexing, queries
- **dependencies** (6 patterns): Package management
- **frontend** (7 patterns): UI, state, routing
- **security** (9 patterns): General security

Plus 31 universal patterns that apply to all domains.

## Need Help?

- **Documentation**: [../docs/quickstart.md](../docs/quickstart.md)
- **Issues**: [github.com/abhi10/gremlin/issues](https://github.com/abhi10/gremlin/issues)
- **Main README**: [../README.md](../README.md)

## Contributing Examples

Have a useful Gremlin workflow? Contribute it!

1. Fork the repository
2. Add your example to the appropriate file
3. Submit a pull request

Examples should include:
- Clear use case description
- Complete code/commands
- Expected output (if applicable)
- Context about when to use it
