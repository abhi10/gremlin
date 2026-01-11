# Using Context with Gremlin

Context helps Gremlin provide more specific, relevant risk scenarios by understanding your technical stack and implementation details.

## Three Ways to Provide Context

### 1. Direct String Context

Pass context directly as a string:

```bash
gremlin review "user authentication" --context "Using JWT tokens, Redis for sessions, PostgreSQL for user data"
```

**When to use:** Quick context about tech stack, frameworks, or high-level architecture.

### 2. File Reference Context

Reference a specific file:

```bash
gremlin review "authentication flow" --context @src/auth/login.ts
```

**When to use:** Reviewing specific code files or configuration files.

### 3. Stdin Context (Pipe)

Pipe content from commands:

```bash
git diff main...feature-branch | gremlin review "changes in this PR" --context -
```

**When to use:** Analyzing diffs, command output, or dynamic content.

## Example 1: Tech Stack Context

**Without context:**

```bash
gremlin review "checkout flow"
```

Returns generic payment risks.

**With context:**

```bash
gremlin review "checkout flow" --context "Using Stripe Payment Intents, Next.js API routes, PostgreSQL with Prisma ORM, Redis for cart sessions"
```

**Enhanced Output:**

```
🔴 CRITICAL (94% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Stripe Webhook Race with Prisma Transaction

  What if the Stripe webhook arrives before the Prisma transaction commits?

  Impact: Payment marked successful in Stripe but order record missing in PostgreSQL.
           Customer charged but no order created. Webhook processing fails on retry.
  Domain: payments, database

🟠 HIGH (89% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Redis Cart Session Expiry During Checkout

  What if the Redis cart session expires while the user is on the Stripe checkout page?

  Impact: Cart data lost when user returns. Cannot complete order. Cart must be rebuilt.
  Domain: payments, infrastructure

🟠 HIGH (85% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Next.js API Route Timeout on Payment

  What if the Stripe payment confirmation takes longer than Next.js serverless timeout?

  Impact: Payment succeeds but response never reaches client. User sees error, order actually created.
           Duplicate order attempts possible.
  Domain: payments, infrastructure
```

**Notice:** Risks are now specific to Stripe + Next.js + Prisma + Redis stack!

## Example 2: File-Based Context

Reviewing specific code:

```bash
gremlin review "database transaction logic" --context @src/db/orders.ts
```

**orders.ts content:**
```typescript
export async function createOrder(userId: string, items: CartItem[]) {
  return await prisma.$transaction(async (tx) => {
    const order = await tx.order.create({
      data: { userId, total: calculateTotal(items) }
    });

    for (const item of items) {
      await tx.orderItem.create({
        data: { orderId: order.id, ...item }
      });
      await tx.product.update({
        where: { id: item.productId },
        data: { stock: { decrement: item.quantity } }
      });
    }

    return order;
  });
}
```

**Output with file context:**

```
🔴 CRITICAL (92% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Stock Decrement Without Availability Check

  What if the product stock goes negative because decrement happens without checking current value?

  Impact: Overselling products. Negative inventory. Orders accepted for unavailable items.
  Domain: database, concurrency

🟠 HIGH (88% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Sequential Updates in Loop

  What if this transaction runs with hundreds of order items?

  Impact: Long-running transaction holds locks. Deadlocks with concurrent orders.
           Transaction timeout on large orders.
  Domain: database, performance

🟠 HIGH (83% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Prisma Transaction Serialization

  What if Prisma's default isolation level causes serialization failures under load?

  Impact: Frequent transaction rollbacks during high concurrency. Order failures spike at peak times.
  Domain: database, concurrency
```

**Notice:** Risks are code-specific, referencing the actual implementation!

## Example 3: Git Diff Context

Analyzing changes in a PR:

```bash
git diff main...feature/new-auth | gremlin review "authentication changes" --context -
```

**Diff content:**
```diff
+  const token = jwt.sign({ userId: user.id }, process.env.JWT_SECRET);
+  res.cookie('auth_token', token);
+  return res.json({ success: true });
```

**Output:**

```
🔴 CRITICAL (95% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  JWT Without Expiration

  What if the JWT token in the diff has no expiration time?

  Impact: Token valid forever. Stolen tokens never expire. No session rotation.
  Domain: auth, security

🔴 CRITICAL (90% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Cookie Without HttpOnly/Secure Flags

  What if the auth_token cookie lacks HttpOnly and Secure flags?

  Impact: XSS attacks can steal token. Token transmitted over HTTP in dev/staging.
  Domain: auth, security, frontend

🟠 HIGH (87% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  No Token Revocation Mechanism

  What if a user logs out but there's no server-side token invalidation?

  Impact: Logout is client-side only. Stolen tokens remain valid until natural expiry.
  Domain: auth
```

**Notice:** Risks reference the actual code changes in the diff!

## Example 4: Configuration Context

Reviewing infrastructure setup:

```bash
gremlin review "production deployment" --context @k8s/deployment.yaml
```

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: myapp:latest
        env:
        - name: DATABASE_URL
          value: "postgres://user:pass@db:5432/prod"
        resources:
          requests:
            memory: "128Mi"
```

**Output:**

```
🔴 CRITICAL (96% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Database Credentials in Plain Text

  What if the DATABASE_URL with plaintext password is visible in kubectl describe?

  Impact: Database credentials exposed to anyone with kubectl access. Logs contain passwords.
  Domain: infrastructure, security, deployment

🔴 CRITICAL (91% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Using 'latest' Tag in Production

  What if :latest image tag is deployed and image changes without notice?

  Impact: Unpredictable deployments. Rolling updates pull different code. No rollback path.
  Domain: deployment, infrastructure

🟠 HIGH (88% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Insufficient Memory Resources

  What if the 128Mi memory request is too low for production load?

  Impact: OOM kills under load. Pod restarts. Service degradation during traffic spikes.
  Domain: infrastructure
```

## Example 5: Combined Context

Use multiple context sources by chaining:

```bash
# Review code changes with tech stack context
git diff | gremlin review "PR changes" \
  --context - \
  --context "Stack: Next.js 14, tRPC, Prisma, PostgreSQL, deployed on Vercel"
```

**Note:** Currently only one `--context` flag is supported. To combine, merge contexts:

```bash
echo "Tech Stack: Next.js 14, tRPC, Prisma, PostgreSQL

Code Changes:
$(git diff)" | gremlin review "PR changes" --context -
```

## Best Practices

### 1. Be Specific with Tech Stack

**Good:**
```bash
--context "FastAPI with async PostgreSQL via asyncpg, Redis for caching, JWT auth"
```

**Less helpful:**
```bash
--context "Python backend with database"
```

### 2. Include Version Information

**Good:**
```bash
--context "React 18 with Next.js 14, using App Router and Server Components"
```

**Why:** Different versions have different risks (e.g., Next.js 13 vs 14 routing).

### 3. Mention Critical Libraries

**Good:**
```bash
--context "Using Stripe Payment Intents, SendGrid for emails, Bull for job queues"
```

**Why:** Third-party integrations have specific failure modes.

### 4. Reference File Sections

For large files, review specific sections:

```bash
# Extract function and review
sed -n '/^export async function checkout/,/^}/p' src/checkout.ts | \
  gremlin review "checkout function" --context -
```

### 5. Use Context for Architecture

```bash
gremlin review "API gateway" --context "Microservices: auth-service, order-service, payment-service. Communication via RabbitMQ. API Gateway uses Express with JWT validation."
```

## Context Length Considerations

### Optimal Context Size

- **Sweet spot:** 100-500 words / 500-2500 characters
- **Max effective:** ~2000 words / 10,000 characters

### Large Files

For files >500 lines:

```bash
# Review specific section
gremlin review "payment processing" --context @src/payments/checkout.ts:100-300
```

**Note:** Line range syntax not yet implemented. Current workaround:

```bash
sed -n '100,300p' src/payments/checkout.ts | gremlin review "payment processing" --context -
```

## Integration with Workflows

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

git diff --staged | gremlin review "staged changes" --context - --threshold 90 --output md
```

### PR Review Bot

```bash
#!/bin/bash
# Review PR changes
gh pr diff $PR_NUMBER | \
  gremlin review "PR #$PR_NUMBER changes" \
    --context - \
    --output md > review-comments.md
```

### Code Review Assistant

```bash
# Review specific commit
git show $COMMIT_SHA | gremlin review "commit $COMMIT_SHA" --context -
```

## Common Patterns

### Pattern 1: File + Stack Context

```bash
gremlin review "database queries" \
  --context @src/db/queries.ts \
  --context "PostgreSQL 15, Prisma 5.x, connection pooling via PgBouncer"
```

**Workaround for multiple --context:**
```bash
{
  echo "Stack: PostgreSQL 15, Prisma 5.x, PgBouncer"
  echo ""
  cat src/db/queries.ts
} | gremlin review "database queries" --context -
```

### Pattern 2: Diff + Issue Context

```bash
{
  echo "Fixing issue #123: Race condition in order processing"
  echo ""
  git diff
} | gremlin review "fix for race condition" --context -
```

### Pattern 3: Multi-file Review

```bash
{
  echo "=== checkout.ts ==="
  cat src/checkout.ts
  echo ""
  echo "=== payment.ts ==="
  cat src/payment.ts
} | gremlin review "checkout flow" --context -
```

## Next Steps

- **Try output formats:** See [output-formats.md](output-formats.md)
- **Integrate with CI:** See [ci-integration.md](ci-integration.md)
- **View examples:** Check [sample-outputs/](sample-outputs/) directory
- **Basic usage:** Back to [basic-usage.md](basic-usage.md)
