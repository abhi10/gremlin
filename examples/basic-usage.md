# Basic Usage Examples

This guide shows common Gremlin usage patterns for everyday QA scenarios.

## Example 1: Authentication Flow

Review a standard authentication system:

```bash
gremlin review "user login with email and password"
```

**Output:**

```
🔴 CRITICAL (92% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Timing Attack on Password Comparison

  What if an attacker measures response time differences during password validation?

  Impact: Password enumeration through timing analysis. Fixed-time comparison required.
  Domain: auth, security

🔴 CRITICAL (88% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  No Rate Limiting on Login Attempts

  What if an attacker tries thousands of password combinations per minute?

  Impact: Brute force attacks succeed. User accounts compromised.
  Domain: auth, security

🟠 HIGH (85% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Session Token Not Invalidated on Logout

  What if logout only clears the client-side token but doesn't invalidate server-side?

  Impact: Stolen tokens remain valid indefinitely. Session hijacking possible.
  Domain: auth
```

**Key Risks Identified:**
- Timing attacks (CRITICAL)
- Rate limiting gaps (CRITICAL)
- Session management issues (HIGH)

## Example 2: Payment Processing

Analyze a checkout flow:

```bash
gremlin review "Stripe checkout with order creation"
```

**Output:**

```
🔴 CRITICAL (95% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Webhook Race Condition

  What if the Stripe webhook arrives before the order record is committed to the database?

  Impact: Payment captured but order not created. Customer charged without confirmation.
           Money collected but fulfillment never triggered.
  Domain: payments, concurrency

🔴 CRITICAL (90% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Payment Succeeds but Inventory Reservation Fails

  What if payment completes but the subsequent inventory update throws an exception?

  Impact: Money charged, item shown as sold, but inventory not decremented.
           Overselling occurs. Customer charged for unavailable items.
  Domain: payments, database

🟠 HIGH (87% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Double-Click Payment Submission

  What if the user clicks "Pay Now" twice in rapid succession?

  Impact: Duplicate payment intents created. Customer potentially double-charged.
  Domain: payments, concurrency, frontend
```

**Key Risks Identified:**
- Webhook race conditions (CRITICAL)
- Transaction rollback gaps (CRITICAL)
- Duplicate submission (HIGH)

## Example 3: File Upload

Review file upload functionality:

```bash
gremlin review "file upload for user profile pictures"
```

**Output:**

```
🔴 CRITICAL (93% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Unrestricted File Upload

  What if an attacker uploads a .php or .jsp file disguised as an image?

  Impact: Remote code execution. Server compromise if file is executed.
  Domain: file_upload, security

🟠 HIGH (88% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  No File Size Limit

  What if users upload gigabyte-sized files?

  Impact: Server disk space exhaustion. Memory overflow during processing. DoS.
  Domain: file_upload, universal

🟠 HIGH (82% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Image Processing Vulnerability

  What if a malicious image triggers vulnerabilities in the image processing library?

  Impact: Memory corruption, DoS, potential RCE through crafted image files.
  Domain: file_upload, dependencies
```

**Key Risks Identified:**
- File type validation (CRITICAL)
- Size limits (HIGH)
- Image processing security (HIGH)

## Example 4: Database Operations

Analyze database queries:

```bash
gremlin review "user search with filters and pagination"
```

**Output:**

```
🟠 HIGH (90% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  SQL Injection via Search Parameter

  What if the search term contains SQL injection payloads?

  Impact: Unauthorized data access. Potential data deletion or modification.
  Domain: database, security

🟠 HIGH (85% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Unbounded Query Results

  What if pagination is bypassed or set to fetch thousands of records?

  Impact: Database memory exhaustion. Slow query performance affecting all users.
  Domain: database, api

🟡 MEDIUM (75% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Missing Index on Filtered Column

  What if the filter column lacks an index and queries scan full table?

  Impact: Degraded performance as data grows. Query timeouts in production.
  Domain: database
```

**Key Risks Identified:**
- SQL injection (HIGH)
- Pagination vulnerabilities (HIGH)
- Performance issues (MEDIUM)

## Example 5: API Endpoints

Review API design:

```bash
gremlin review "REST API for product catalog search"
```

**Output:**

```
🟠 HIGH (88% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  No Rate Limiting

  What if a malicious user sends thousands of search requests per second?

  Impact: API resource exhaustion. Service degradation for legitimate users.
  Domain: api, security

🟠 HIGH (83% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Missing Authentication Check

  What if the API endpoint is accessible without authentication?

  Impact: Unauthorized access to catalog data. Potential data scraping.
  Domain: api, auth

🟡 MEDIUM (78% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  No Cache-Control Headers

  What if expensive search results aren't cached?

  Impact: Repeated database queries for identical searches. Increased server load.
  Domain: api
```

**Key Risks Identified:**
- Rate limiting (HIGH)
- Authentication (HIGH)
- Caching strategy (MEDIUM)

## Example 6: Deployment Configuration

Analyze deployment setup:

```bash
gremlin review "Docker container deployment with environment variables"
```

**Output:**

```
🔴 CRITICAL (90% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Secrets in Environment Variables

  What if API keys or database passwords are passed as plain environment variables?

  Impact: Secrets visible in logs, process listings, and container inspection.
           Credential exposure through various leak vectors.
  Domain: deployment, security

🟠 HIGH (87% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Container Running as Root

  What if the Docker container runs as root user?

  Impact: Container escape = host compromise. Privilege escalation attacks.
  Domain: infrastructure, deployment

🟠 HIGH (82% confidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  No Health Check Endpoint

  What if the container crashes but orchestration doesn't detect it?

  Impact: Dead containers receiving traffic. Failed requests until manual intervention.
  Domain: infrastructure, deployment
```

**Key Risks Identified:**
- Secrets management (CRITICAL)
- Container security (HIGH)
- Health checks (HIGH)

## Using with Different Depths

### Quick Analysis (Default)

Fast, high-confidence scenarios:

```bash
gremlin review "user registration"
```

### Deep Analysis

More thorough, includes edge cases:

```bash
gremlin review "user registration" --depth deep
```

Deep analysis typically returns:
- 2-3x more scenarios
- Lower confidence risks (60-80%)
- More edge cases and corner scenarios

## Filtering by Confidence

Show only high-confidence risks:

```bash
gremlin review "checkout flow" --threshold 90
```

Show all risks including low-confidence:

```bash
gremlin review "checkout flow" --threshold 50
```

**Recommendation:** Use default (80) for most cases, adjust based on phase:
- Design/early development: 70-75 (broader exploration)
- Pre-production/critical features: 85-90 (focus on likely issues)

## Next Steps

- **Add context**: See [with-context.md](with-context.md) for context usage
- **Try different formats**: See [output-formats.md](output-formats.md)
- **Integrate with CI**: See [ci-integration.md](ci-integration.md)
- **View sample outputs**: Check [sample-outputs/](sample-outputs/) directory
