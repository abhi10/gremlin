# Gremlin Pattern Brain Dump

> **Purpose:** Raw collection of bugs, near-misses, and "what could break" scenarios
> **Source Project:** Chitram Image Hosting Service + General Experience
> **Date:** January 2025

---

## Tech Stack Context

| Component | Technology |
|-----------|------------|
| Backend | Python / FastAPI |
| Storage | MinIO / S3 |
| CDN | - |
| Database | PostgreSQL |
| Image Processing | Pillow |
| Auth | Supabase + Local JWT |
| Cache | Redis |
| Hosting | Docker |

---

# PART 1: Chitram Risk Patterns Catalog

**Source:** Code analysis + incident retrospectives
**Last Updated:** 2026-01-08

---

## High Priority Patterns (Score 4-5)

### 1. Pillow Memory DoS from Corrupt EXIF

- **What if:** An attacker uploads a JPEG with malicious EXIF dimensions (e.g., 100000x100000)?
- **Impact:** Pillow attempts to allocate gigabytes of memory, causing OOM kill or server hang. Semaphore slot is held during decode, blocking other uploads.
- **Domain:** image_processing
- **Non-obvious score:** 5/5
- **Status:** Not mitigated
- **Code location:** `backend/app/services/image_service.py:62-65`, `backend/app/services/thumbnail_service.py:67-81`

### 2. Auth Provider Mismatch Between Components (ACTUAL INCIDENT)

- **What if:** Web UI uses local JWT verification but API uses Supabase?
- **Impact:** Users appear logged out despite valid Supabase tokens. Nav shows "Login" instead of user email. Happened Jan 8, 2026 - took 12 hours to detect.
- **Domain:** auth
- **Non-obvious score:** 5/5
- **Status:** Fixed (PR #36), but pattern could recur
- **Code location:** `backend/app/api/web.py:41-74` (fixed), `backend/app/api/auth.py:37-56`
- **Incident:** [docs/retrospectives/2026-01-08-supabase-nav-auth-bug.md](../retrospectives/2026-01-08-supabase-nav-auth-bug.md)

### 3. Cross-Cutting Concerns Applied Inconsistently

- **What if:** A new auth/caching/logging pattern is added to API routes but not web routes?
- **Impact:** Two different code paths for the same feature. One works, one breaks. Users see inconsistent behavior.
- **Domain:** architecture
- **Non-obvious score:** 5/5
- **Status:** Requires manual audit
- **Prevention:** `grep -r "AuthService\|verify_token" --include="*.py"` when changing auth

### 4. Orphaned Files from Failed Deletion

- **What if:** Storage deletion fails but database deletion succeeds?
- **Impact:** Files remain in S3/MinIO forever, consuming storage costs. No cleanup mechanism exists. Code explicitly says "File may be orphaned" and continues.
- **Domain:** storage
- **Non-obvious score:** 4/5
- **Status:** Not mitigated
- **Code location:** `backend/app/services/image_service.py:355-365`

### 5. Memory Exhaustion from Concurrent Uploads

- **What if:** 10 users upload 5MB files simultaneously?
- **Impact:** 50MB in file buffers + 100-150MB for Pillow decoded images = 150-200MB peak memory. With more concurrent users, OOM possible.
- **Domain:** file_upload
- **Non-obvious score:** 4/5
- **Status:** Not mitigated (semaphore limits concurrency but not memory)
- **Code location:** `backend/app/api/images.py:126-141`, `backend/app/services/image_service.py:68-81`

### 6. Rate Limiter Bypass via X-Forwarded-For Spoofing

- **What if:** Attacker sends different X-Forwarded-For headers with each request?
- **Impact:** Each spoofed IP gets its own rate limit bucket. Attacker bypasses 10 req/min limit entirely.
- **Domain:** api
- **Non-obvious score:** 4/5
- **Status:** Not mitigated
- **Code location:** `backend/app/api/images.py:57-63`, `backend/app/services/rate_limiter.py:60`

### 7. Thumbnail Generation Hangs Indefinitely

- **What if:** Pillow gets stuck on a corrupt image during thumbnail generation?
- **Impact:** Background task runs forever, no timeout. Memory held until server restart. No monitoring of task completion.
- **Domain:** image_processing
- **Non-obvious score:** 4/5
- **Status:** Not mitigated
- **Code location:** `backend/app/services/thumbnail_service.py:112-175`

### 8. Test Environment Differs from Production

- **What if:** Tests use `AUTH_PROVIDER=local` but production uses `supabase`?
- **Impact:** All tests pass locally, production breaks immediately. This exact scenario caused the Jan 8 incident.
- **Domain:** deployment
- **Non-obvious score:** 4/5
- **Status:** Documented, requires manual verification
- **Related:** [docs/learning/supabase-integration-learnings.md](supabase-integration-learnings.md)

### 9. Docker Env Vars Not Passed Through

- **What if:** docker-compose.yml doesn't explicitly map environment variables?
- **Impact:** Container runs with defaults instead of production values. App appears to work but uses wrong config (e.g., local auth instead of Supabase).
- **Domain:** deployment
- **Non-obvious score:** 4/5
- **Status:** Fixed for known vars, new vars could have same issue
- **Code location:** `deploy/docker-compose.yml`

### 10. Config Loaded at Import Time

- **What if:** Tests import app modules before setting test environment variables?
- **Impact:** Tests try to connect to real Supabase instead of using mock. Tests fail with external service errors.
- **Domain:** testing
- **Non-obvious score:** 4/5
- **Status:** Fixed in conftest.py
- **Code location:** `backend/tests/conftest.py` (line 1-10)

---

## Medium Priority Patterns (Score 3)

### 11. PNG Transparency Lost in JPEG Thumbnail

- **What if:** User uploads PNG with alpha channel, thumbnail is generated as JPEG?
- **Impact:** Transparency converted to white/black background. User's logo with transparent background becomes opaque. No warning given.
- **Domain:** image_processing
- **Non-obvious score:** 3/5
- **Status:** Not mitigated
- **Code location:** `backend/app/services/thumbnail_service.py:69-70`

### 12. Rate Limiter Fails Open During Redis Outage

- **What if:** Redis goes down during a traffic spike or DDoS?
- **Impact:** All rate limiting disabled. API completely unprotected. Intentional design choice (availability over protection).
- **Domain:** api
- **Non-obvious score:** 3/5
- **Status:** Intentional (fail-open design)
- **Code location:** `backend/app/services/rate_limiter.py:83-85`

### 13. Delete Token Leakage Enables Unauthorized Deletion

- **What if:** Anonymous delete token is logged, stored in localStorage, or visible in browser history?
- **Impact:** Anyone with the token can delete the image. No rate limiting on delete endpoint. Token only shown once at upload.
- **Domain:** auth
- **Non-obvious score:** 3/5
- **Status:** Not mitigated
- **Code location:** `backend/app/api/images.py:162-187`, `backend/app/services/image_service.py:283-323`

### 14. Concurrent Upload Timeout Without Client Backoff

- **What if:** Many clients get 503 "Server busy" and immediately retry?
- **Impact:** Server returns `Retry-After` header, but clients may ignore it. Retry storm amplifies load. No exponential backoff enforced.
- **Domain:** file_upload
- **Non-obvious score:** 3/5
- **Status:** Partially mitigated (has Retry-After header)
- **Code location:** `backend/app/api/images.py:128-137`

### 15. Magic Bytes Check Only Validates File Header

- **What if:** Attacker creates polyglot file with JPEG header + executable payload?
- **Impact:** File passes validation (only first 3-4 bytes checked). If served directly without content-type header, browser might execute it.
- **Domain:** file_upload
- **Non-obvious score:** 3/5
- **Status:** Partially mitigated (content-type header set on storage)
- **Code location:** `backend/app/utils/validation.py:12-22`

### 16. SDK Version Breaking Changes

- **What if:** Third-party SDK updates its API between versions?
- **Impact:** `AttributeError: 'ClientOptions' object has no attribute 'storage'` - production crash on startup. Supabase v2.x changed the API.
- **Domain:** dependencies
- **Non-obvious score:** 3/5
- **Status:** Fixed for Supabase, could recur with other deps
- **Related:** [docs/learning/supabase-integration-learnings.md](supabase-integration-learnings.md)

### 17. Existing User Can't Login After Auth Migration

- **What if:** User exists in local DB but not in Supabase?
- **Impact:** "Invalid Credentials" error even with correct password. User must re-register in Supabase to link accounts.
- **Domain:** auth
- **Non-obvious score:** 3/5
- **Status:** Expected behavior (documented)
- **Related:** Sync-on-auth pattern in Supabase learnings

---

## Lower Priority Patterns (Score 1-2) - Well Handled

### 18. Storage Backend Unavailable During Upload

- **What if:** MinIO is down when saving file?
- **Impact:** Clean failure - HTTP 500 returned, no DB record created, no orphaned data.
- **Domain:** storage
- **Non-obvious score:** 2/5
- **Status:** Properly handled
- **Code location:** `backend/app/services/image_service.py:120-137`

### 19. Redis Cache Unavailable

- **What if:** Redis is down for 30 minutes?
- **Impact:** Graceful degradation - falls back to DB queries. System slower but functional.
- **Domain:** cache
- **Non-obvious score:** 1/5
- **Status:** Properly handled
- **Code location:** `backend/app/services/cache_service.py:110-123`

### 20. Thumbnail Task Runs After Image Deleted

- **What if:** User deletes image before thumbnail background task executes?
- **Impact:** Task queries DB, finds no image, logs warning, exits cleanly.
- **Domain:** background_tasks
- **Non-obvious score:** 2/5
- **Status:** Properly handled
- **Code location:** `backend/app/services/thumbnail_service.py:126-134`

### 21. Manual Production Edits Create Permission Issues

- **What if:** Someone manually edits files on the production server?
- **Impact:** Git fails with `unable to unlink old file: Permission denied` and `dubious ownership` errors. Requires `chown` and `git clean` to fix.
- **Domain:** deployment
- **Non-obvious score:** 2/5
- **Status:** Documented, avoid manual edits
- **Related:** [docs/learning/supabase-integration-learnings.md](supabase-integration-learnings.md)

### 22. Alembic Not Available in Production Container

- **What if:** You need to run a database migration but Alembic isn't in the Docker image?
- **Impact:** `alembic upgrade head` fails. Must use raw SQL via `psql` as workaround.
- **Domain:** deployment
- **Non-obvious score:** 2/5
- **Status:** Known limitation, use direct SQL

---

# PART 2: Gemini-Generated Patterns (Image Hosting Context)

**Source:** Google Gemini analysis of common image hosting failure modes
**Curated:** January 2026

---

## I. Authentication & Session Patterns

### G1. Zombie Token Pattern

- **What if:** User's permissions are revoked (or password changed) in DB, but their stateless JWT is still valid until expiration?
- **Impact:** User retains access to private images during the token validity window. Tests cache invalidation and token introspection latency.
- **Domain:** auth
- **Non-obvious score:** 4/5

### G2. Concurrent Session Race

- **What if:** Access token is refreshed using refresh token simultaneously from two different devices/threads?
- **Impact:** PostgreSQL unique constraints on token usage trigger race conditions, causing 500 errors or logging user out of both sessions.
- **Domain:** auth
- **Non-obvious score:** 4/5

### G3. Clock Skew Environment

- **What if:** Time drift exists between Auth Service container and PostgreSQL server?
- **Impact:** Tokens may be generated "in the future" (nbf claim) or expire instantly, causing authentication loops during upload.
- **Domain:** auth
- **Non-obvious score:** 5/5

---

## II. Upload Functionality Patterns

### G4. Polyglot File Injection

- **What if:** Uploaded file is a valid image but contains embedded malicious code in EXIF metadata or appended data?
- **Impact:** If backend processes EXIF without sanitization, triggers script execution or SQL injection via image metadata.
- **Domain:** file_upload
- **Non-obvious score:** 4/5

### G5. Partial Upload Network Cut

- **What if:** Large image upload is interrupted at 99%, then user reconnects and tries to upload same file again?
- **Impact:** Tests orphaned data handling. Temp storage fills up. DB may have "ghost" image record that breaks gallery because file doesn't exist.
- **Domain:** file_upload
- **Non-obvious score:** 4/5

### G6. MIME-Type Masquerade

- **What if:** File extension is changed (virus.exe → image.png) versus actual magic bytes are modified?
- **Impact:** If validator only checks extension (not binary signature), system accepts executables. If validates signature but relies on extension for storage, may execute on retrieval.
- **Domain:** file_upload
- **Non-obvious score:** 3/5

### G7. Filename Collision Race Condition

- **What if:** Two users upload different images with exact same filename at the exact same millisecond?
- **Impact:** Tests file naming strategy (UUID vs raw name). Naive implementation: one image overwrites other in storage, but both DB records point to single file.
- **Domain:** file_upload
- **Non-obvious score:** 4/5

### G8. Zero-Byte Bomb

- **What if:** User uploads 0-byte file or file with corrupted header indicating 10GB size?
- **Impact:** Tests memory allocation of upload parser. May try to allocate buffer based on header size (OOM crash) or fail gracefully.
- **Domain:** file_upload
- **Non-obvious score:** 3/5

---

## III. Image Gallery (Read Path) Patterns

### G9. N+1 Query Flood

- **What if:** Gallery page with 50 images requires separate DB lookup for each image's user profile or like count?
- **Impact:** Under load, causes connection storm to PostgreSQL, exhausting connection pool and blocking auth service.
- **Domain:** database
- **Non-obvious score:** 3/5

### G10. Pagination Drift Pattern

- **What if:** User views Page 1, another user deletes 5 images from Page 1, first user clicks "Next Page"?
- **Impact:** Offset shifted - user sees duplicate images or misses images entirely. Tests cursor vs offset pagination.
- **Domain:** database
- **Non-obvious score:** 4/5

### G11. Deep Link Auth Bypass

- **What if:** User copies direct URL of private image (from CDN/blob storage) and shares with unauthenticated user?
- **Impact:** If storage is public and security only enforced at UI/API level, image accessible to anyone with link.
- **Domain:** auth
- **Non-obvious score:** 3/5

### G12. Metadata XSS Render

- **What if:** Image uploaded with XSS payload in alt text or description field?
- **Impact:** When gallery renders, browser may execute JavaScript stored in PostgreSQL text field.
- **Domain:** security
- **Non-obvious score:** 3/5

---

## IV. PostgreSQL & Data Integrity Patterns

### G13. Transaction Deadlock Loop

- **What if:** User A uploads (writes Image Table → updates User Quota) while User B views gallery (reads Quota → reads Image Table)?
- **Impact:** High concurrency of opposing locking orders causes PostgreSQL deadlocks, requests hang until timeout.
- **Domain:** database
- **Non-obvious score:** 4/5

### G14. Integer Overflow Edge Case

- **What if:** Primary key ID or view count integer reaches maximum value (2,147,483,647)?
- **Impact:** Next upload/view triggers overflow error, crashing write functionality permanently until schema migration.
- **Domain:** database
- **Non-obvious score:** 3/5

### G15. Connection Pool Starvation

- **What if:** Image processing service takes 5 seconds per image and holds DB connection open while processing?
- **Impact:** 100 uploads = all DB connections held by slow processing, preventing auth service from verifying anyone.
- **Domain:** database
- **Non-obvious score:** 4/5

### G16. Replication Lag Window

- **What if:** (Using read replicas) User uploads image, gets "Success", immediately redirected to gallery?
- **Impact:** Gallery reads from replica that hasn't received data yet. User sees empty gallery or 404.
- **Domain:** database
- **Non-obvious score:** 4/5

---

## V. Infrastructure & Environment Patterns

### G17. Thundering Herd Restart

- **What if:** Auth service crashes, and as it reboots, 10,000 pending client retry requests hit it simultaneously?
- **Impact:** Tests startup readiness probes and caching. Service often crashes again because cache is cold and DB overwhelmed.
- **Domain:** infrastructure
- **Non-obvious score:** 4/5

### G18. Latency Chaos Pattern

- **What if:** Artificial 3000ms latency introduced between web tier and blob storage?
- **Impact:** HTTP request times out before backend finishes upload. Backend may keep writing anyway, creating "zombie files" no one owns.
- **Domain:** infrastructure
- **Non-obvious score:** 4/5

### G19. Disk Full Hard Stop

- **What if:** "No space left on device" error on database volume or temp upload directory?
- **Impact:** May corrupt database index, show friendly error, or dump stack trace revealing internal paths.
- **Domain:** infrastructure
- **Non-obvious score:** 3/5

### G20. Version Mismatch Rollout

- **What if:** New API version expects new DB column, but runs against old schema (migration failure)?
- **Impact:** Does app crash entirely or degrade gracefully (gallery works, upload fails)?
- **Domain:** deployment
- **Non-obvious score:** 3/5

---

# PART 3: Other Bugs & Patterns from Experience

**Source:** General software engineering experience

---

## Bugs You've Seen

### E1. Feature Flag Missing in Production

- **What if:** Feature flag not added during rollout to production?
- **Impact:** Feature either always on or always off, no ability to control rollout or kill switch.
- **Domain:** deployment
- **Non-obvious score:** 3/5

### E2. DB Inconsistency During Product Integration

- **What if:** Two different products integrated share data but have inconsistent DB states?
- **Impact:** User-facing errors, data corruption, or confusing UX.
- **Domain:** database
- **Non-obvious score:** 4/5

### E3. Long-Running Migration OOM

- **What if:** Database migration runs out of memory or CPU during execution?
- **Impact:** Migration fails mid-way, leaving DB in inconsistent state. Rollback may be difficult.
- **Domain:** database
- **Non-obvious score:** 4/5

### E4. Browser Resize Breaks Frontend

- **What if:** User resizes browser window to unusual dimensions?
- **Impact:** Layout breaks, elements overlap, functionality becomes unusable.
- **Domain:** frontend
- **Non-obvious score:** 2/5

### E5. Large Input Text Breaks UX

- **What if:** User pastes extremely large text into input field?
- **Impact:** UI freezes, layout breaks, or backend rejects with unhelpful error.
- **Domain:** frontend
- **Non-obvious score:** 2/5

### E6. File Download Format Failure

- **What if:** Download file in specific format doesn't work?
- **Impact:** User can't export their data, feature appears broken.
- **Domain:** file_upload
- **Non-obvious score:** 2/5

### E7. Rating/Review UI Mismatch

- **What if:** Rating popup shows incorrect image icons or star counts?
- **Impact:** User confusion, incorrect ratings submitted.
- **Domain:** frontend
- **Non-obvious score:** 2/5

### E8. Sorting/Filtering Breaks for Specific Feature

- **What if:** Sorting or filtering doesn't work for ratings in e-commerce context?
- **Impact:** Users can't find relevant reviews, impacts purchase decisions.
- **Domain:** frontend
- **Non-obvious score:** 3/5

### E9. Payment Workflow External Dependencies

- **What if:** Payment process has multiple workflows with external dependencies not testable in lower environments?
- **Impact:** Bugs only discovered in production, high-risk releases.
- **Domain:** payments
- **Non-obvious score:** 4/5

### E10. Feature Parity Gap Between Environments

- **What if:** Prod and Pre-prod have different feature sets?
- **Impact:** Higher risk, more manual testing needed, bugs slip through.
- **Domain:** deployment
- **Non-obvious score:** 3/5

### E11. Cross-Browser Incompatibility

- **What if:** Feature works on Chrome but not Safari/Firefox?
- **Impact:** Subset of users can't use feature, hard to detect without explicit testing.
- **Domain:** frontend
- **Non-obvious score:** 2/5

### E12. Desktop vs Mobile UX Gap

- **What if:** Web app works on desktop but has poor UX on mobile?
- **Impact:** Mobile users have degraded experience, may abandon.
- **Domain:** frontend
- **Non-obvious score:** 2/5

### E13. External API Deprecated Without Notice

- **What if:** Internal API depends on external API that gets deprecated?
- **Impact:** Core workflow (checkout, etc.) breaks without warning from 3rd party.
- **Domain:** dependencies
- **Non-obvious score:** 5/5

---

## The "Oh Shit" List (Catastrophic Fears)

1. **Dependency API deprecated** - External service stops working, breaks core functionality
2. **Service cert expires** - SSL/TLS cert expires, service unavailable to customers
3. **OTA update fails** - Over-the-air update doesn't go through, devices stuck on old version

---

# PART 4: Consolidated "What If?" Patterns for Gremlin

> Ready-to-use patterns extracted from all sources above

---

## Domain: auth

**Keywords:** login, auth, token, session, jwt, oauth, supabase, user, credential, password, permission

| # | Pattern | Source |
|---|---------|--------|
| 1 | What if different components use different auth providers/verification methods? | Chitram #2 |
| 2 | What if a secret token is leaked via logs, localStorage, or URL? | Chitram #13 |
| 3 | What if user exists in one auth system but not the migrated one? | Chitram #17 |
| 4 | What if token verification works in tests but fails in production? | Chitram #8 |
| 5 | What if user's permissions are revoked but their JWT is still valid? | Gemini G1 |
| 6 | What if token refresh happens simultaneously from two devices? | Gemini G2 |
| 7 | What if clock skew exists between auth service and database? | Gemini G3 |
| 8 | What if direct storage URL bypasses API-level auth checks? | Gemini G11 |

---

## Domain: file_upload

**Keywords:** upload, file, multipart, stream, size, concurrent, attachment

| # | Pattern | Source |
|---|---------|--------|
| 1 | What if many users upload large files simultaneously? | Chitram #5 |
| 2 | What if clients ignore Retry-After and create a retry storm? | Chitram #14 |
| 3 | What if file validation only checks magic bytes, not full content? | Chitram #15 |
| 4 | What if uploaded file contains malicious code in EXIF metadata? | Gemini G4 |
| 5 | What if upload is interrupted at 99% and user retries? | Gemini G5 |
| 6 | What if file extension doesn't match actual file content? | Gemini G6 |
| 7 | What if two users upload files with identical names simultaneously? | Gemini G7 |
| 8 | What if file header claims massive size but file is tiny (or vice versa)? | Gemini G8 |

---

## Domain: image_processing

**Keywords:** image, resize, thumbnail, pillow, process, convert, transform, exif

| # | Pattern | Source |
|---|---------|--------|
| 1 | What if image has malicious EXIF metadata claiming huge dimensions? | Chitram #1 |
| 2 | What if image processing hangs indefinitely on corrupt file? | Chitram #7 |
| 3 | What if format conversion loses data (transparency, color profile)? | Chitram #11 |
| 4 | What if memory is exhausted during concurrent image processing? | Chitram #5 |

---

## Domain: storage

**Keywords:** s3, minio, storage, bucket, file, delete, save, cdn, blob

| # | Pattern | Source |
|---|---------|--------|
| 1 | What if storage deletion fails but DB deletion succeeds (orphaned files)? | Chitram #4 |
| 2 | What if storage is unavailable during upload? | Chitram #18 |

---

## Domain: database

**Keywords:** postgres, sql, query, connection, pool, transaction, migration

| # | Pattern | Source |
|---|---------|--------|
| 1 | What if N+1 queries cause connection pool exhaustion under load? | Gemini G9 |
| 2 | What if pagination offset shifts due to concurrent deletes? | Gemini G10 |
| 3 | What if concurrent transactions with opposing lock orders cause deadlock? | Gemini G13 |
| 4 | What if integer ID or counter reaches maximum value? | Gemini G14 |
| 5 | What if long-running operations hold DB connections open? | Gemini G15 |
| 6 | What if read replica hasn't received data when user is redirected? | Gemini G16 |
| 7 | What if DB migration runs out of memory mid-execution? | Experience E3 |
| 8 | What if two integrated products have inconsistent DB states? | Experience E2 |

---

## Domain: api

**Keywords:** api, rate, limit, endpoint, request, header, rest

| # | Pattern | Source |
|---|---------|--------|
| 1 | What if rate limiting is bypassed via header spoofing (X-Forwarded-For)? | Chitram #6 |
| 2 | What if rate limiting fails open when Redis is down? | Chitram #12 |

---

## Domain: deployment

**Keywords:** deploy, docker, env, config, production, container, rollout

| # | Pattern | Source |
|---|---------|--------|
| 1 | What if environment variables aren't passed through to containers? | Chitram #9 |
| 2 | What if test config differs from production config? | Chitram #8 |
| 3 | What if config is loaded at import time before env vars are set? | Chitram #10 |
| 4 | What if new API version runs against old DB schema (migration failure)? | Gemini G20 |
| 5 | What if feature flag not added during production rollout? | Experience E1 |
| 6 | What if prod and pre-prod have different feature sets? | Experience E10 |

---

## Domain: dependencies

**Keywords:** sdk, library, package, version, upgrade, pip, external, third-party

| # | Pattern | Source |
|---|---------|--------|
| 1 | What if third-party SDK changes its API between versions? | Chitram #16 |
| 2 | What if external API is deprecated without notice? | Experience E13 |

---

## Domain: infrastructure

**Keywords:** server, restart, disk, memory, latency, network, cert

| # | Pattern | Source |
|---|---------|--------|
| 1 | What if service restarts and gets hit by thundering herd of retries? | Gemini G17 |
| 2 | What if latency spike causes client timeout before server finishes? | Gemini G18 |
| 3 | What if disk fills up on database or temp directory? | Gemini G19 |
| 4 | What if SSL/TLS certificate expires? | Experience Oh Shit #2 |

---

## Domain: security

**Keywords:** xss, injection, sanitize, escape, vulnerability

| # | Pattern | Source |
|---|---------|--------|
| 1 | What if user input in metadata field contains XSS payload? | Gemini G12 |

---

## Domain: frontend

**Keywords:** ui, browser, mobile, desktop, resize, layout

| # | Pattern | Source |
|---|---------|--------|
| 1 | What if browser window resized to unusual dimensions? | Experience E4 |
| 2 | What if extremely large text pasted into input field? | Experience E5 |
| 3 | What if feature works in one browser but not another? | Experience E11 |
| 4 | What if desktop UI doesn't work well on mobile? | Experience E12 |

---

## Domain: payments

**Keywords:** checkout, payment, billing, subscription, refund, stripe

| # | Pattern | Source |
|---|---------|--------|
| 1 | What if payment workflow has external dependencies not testable in lower environments? | Experience E9 |

---

# Pattern Count Summary

| Source | Count |
|--------|-------|
| Chitram (real incidents) | 22 |
| Gemini (generated) | 20 |
| Experience (other bugs) | 13 |
| **Total Raw Patterns** | **55** |
| **Deduplicated for Gremlin** | **~50** |

---

## References

- [Incident Retrospective: Nav Auth Bug](../retrospectives/2026-01-08-supabase-nav-auth-bug.md)
- [Supabase Integration Learnings](supabase-integration-learnings.md)
- [Post-Deploy Checklist](../deployment/POST_DEPLOY_CHECKLIST.md)
- [ADR-0010: Concurrency Control](../adr/0010-upload-concurrency-control.md)
- [ADR-0009: Redis Caching](../adr/0009-redis-metadata-caching.md)
