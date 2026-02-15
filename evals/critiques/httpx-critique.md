# Gremlin Critique: encode/httpx

> Risk analysis of [httpx](https://github.com/encode/httpx) — a fully featured HTTP client for Python 3

**Date:** 2026-02-14
**Gremlin Version:** 0.2.0
**Depth:** deep | **Threshold:** 70%

## Summary

| Area | Critical | High | Medium | Low | Total |
|------|----------|------|--------|-----|-------|
| Authentication System | 2 | 3 | 5 | 0 | 10 |
| Connection Pooling & Transport | 2 | 3 | 4 | 0 | 9 |
| Redirect Handling | 2 | 3 | 4 | 1 | 10 |
| SSL/TLS Configuration | 2 | 3 | 3 | 1 | 9 |
| Multipart Uploads | 1 | 3 | 4 | 0 | 8 |
| Request/Response Models | 2 | 3 | 4 | 1 | 10 |
| URL Parsing | 1 | 3 | 4 | 0 | 8 |
| Content Decoders & Error Handling | 2 | 3 | 4 | 0 | 9 |
| **Total** | **14** | **24** | **32** | **3** | **73** |

## Top Critical Risks

### 🔴 Digest Auth Nonce Count Race Condition (85%)
**Area:** Authentication System | **Files:** `httpx/_auth.py`

> What if concurrent requests increment `_nonce_count` simultaneously, causing duplicate or out-of-order nonce counts?

**Impact:** Server rejects requests with duplicate `nc` values, causing authentication failures under load. Multiple threads/async tasks accessing the same `DigestAuth` instance create race conditions.

### 🔴 Credential Leakage via Generator Exception Stack Traces (90%)
**Area:** Authentication System | **Files:** `httpx/_auth.py`

> What if an exception occurs inside the `auth_flow` generator while credentials are in local variables, exposing them in stack traces?

**Impact:** Username/password appear in logs, error monitoring systems, or debug output when `_build_auth_header` or parsing fails mid-flow.

### 🔴 Connection Pool Starvation Cascade (85%)
**Area:** Connection Pooling & Transport | **Files:** `httpx/_transports/default.py`

> What if all connections are held by long-running requests when `max_connections` is reached?

**Impact:** New requests hang indefinitely waiting for available connections, creating cascading timeout failures across the application. Users see timeouts, background jobs fail, health checks fail.

### 🔴 HTTP/2 Stream Limit Exhaustion (80%)
**Area:** Connection Pooling & Transport | **Files:** `httpx/_transports/default.py`

> What if HTTP/2 multiplexing hits the server's max concurrent streams limit but httpx doesn't handle the GOAWAY gracefully?

**Impact:** Requests fail with obscure protocol errors instead of falling back to new connections. Particularly dangerous because HTTP/2 defaults to `http2=False`, so teams enabling it may not test this edge case thoroughly.

### 🔴 Auth Header Persistence Across Malicious Redirects (85%)
**Area:** Redirect Handling | **Files:** `httpx/_client.py`

> What if an attacker controls a redirect destination and the auth header isn't properly stripped when crossing origins?

**Impact:** API keys, bearer tokens, or credentials leaked to attacker-controlled domains. Complete account compromise.

### 🔴 Infinite Redirect Loop Resource Exhaustion (90%)
**Area:** Redirect Handling | **Files:** `httpx/_client.py`

> What if circular redirect detection fails when URLs differ by query params, fragments, or encoding but resolve to same resource?

**Impact:** Memory exhaustion from growing redirect chain tracking, CPU spinning until timeout, DoS affecting all client requests.

### 🔴 Environment Variable CA Bundle Poisoning (85%)
**Area:** SSL/TLS Configuration | **Files:** `httpx/_config.py`

> What if attacker controls SSL_CERT_FILE or SSL_CERT_DIR environment variables?

**Impact:** Complete TLS bypass - attacker can MITM all HTTPS traffic by providing malicious CA bundle that trusts their certificates. Silent data exfiltration without detection.

### 🔴 Client Certificate Private Key Exposure in Logs (80%)
**Area:** SSL/TLS Configuration | **Files:** `httpx/_config.py`

> What if client certificate loading fails and stack traces log the certificate file paths or partial key data?

**Impact:** Private keys exposed in application logs, enabling impersonation attacks and unauthorized access to certificate-protected services.

### 🔴 Memory Exhaustion via Large File Streaming (85%)
**Area:** Multipart Uploads | **Files:** `httpx/_multipart.py`

> What if a file claims small size in headers but streams gigabytes without length validation?

**Impact:** OOM crash affecting all users, server becomes unresponsive

### 🔴 Malicious Content-Encoding Bomb (85%)
**Area:** Request/Response Models | **Files:** `httpx/_models.py`, `httpx/_content.py`

> What if a malicious server sends a tiny gzipped response that decompresses to gigabytes?

**Impact:** Memory exhaustion crashes the application, affecting all users. Attackers can DoS with minimal bandwidth.

### 🔴 Charset Detection Bypass Attack (80%)
**Area:** Request/Response Models | **Files:** `httpx/_models.py`, `httpx/_content.py`

> What if malicious content uses encoding declaration mismatch (declares UTF-8 but contains Latin-1) to bypass input validation?

**Impact:** Charset auto-detection could interpret malicious payloads differently than downstream parsers, enabling injection attacks or data corruption.

### 🔴 IDNA Decoding Bypass via Mixed Unicode/ASCII (85%)
**Area:** URL Parsing | **Files:** `httpx/_urls.py`, `httpx/_urlparse.py`

> What if an attacker crafts a URL with mixed IDNA-encoded and Unicode characters that bypass host validation?

**Impact:** Security controls that validate hostnames could be bypassed, enabling SSRF attacks or redirect to malicious domains. `url.host` shows decoded Unicode while `url.raw_host` shows encoded ASCII - inconsistent validation between these could allow domain confusion attacks.

### 🔴 Memory bomb through malicious compression (85%)
**Area:** Content Decoders & Error Handling | **Files:** `httpx/_decoders.py`, `httpx/_exceptions.py`

> What if an attacker sends a small compressed payload that expands to gigabytes when decompressed?

**Impact:** OOM crash bringing down the entire service. Classic zip bomb attack vector. All decoders (gzip, brotli, zstd) decompress without size limits.

### 🔴 Infinite loop in ZStandard multi-frame handling (80%)
**Area:** Content Decoders & Error Handling | **Files:** `httpx/_decoders.py`, `httpx/_exceptions.py`

> What if malicious zstd data creates a cycle where `unused_data` keeps producing more frames that reference each other?

**Impact:** CPU spin loop, service hangs indefinitely. The `while` loop in ZStandardDecoder assumes forward progress but doesn't validate frame integrity.

---

## Detailed Results by Area

### Authentication System
**Files:** `httpx/_auth.py`
**Risks:** 10 (2C / 3H / 5M / 0L)

#### 🔴 CRITICAL (85%) — Digest Auth Nonce Count Race Condition

> What if concurrent requests increment `_nonce_count` simultaneously, causing duplicate or out-of-order nonce counts?

**Impact:** Server rejects requests with duplicate `nc` values, causing authentication failures under load. Multiple threads/async tasks accessing the same `DigestAuth` instance create race conditions.

#### 🔴 CRITICAL (90%) — Credential Leakage via Generator Exception Stack Traces

> What if an exception occurs inside the `auth_flow` generator while credentials are in local variables, exposing them in stack traces?

**Impact:** Username/password appear in logs, error monitoring systems, or debug output when `_build_auth_header` or parsing fails mid-flow.

#### 🟠 HIGH (80%) — NetRC File Parsing with Malformed Entries

> What if the `.netrc` file contains malformed entries or is corrupted, causing the `netrc.netrc()` constructor to fail during request processing?

**Impact:** Authentication completely broken for all requests using NetRCAuth, no graceful fallback. The lazy import means failures happen at request time, not initialization.

#### 🟠 HIGH (85%) — Digest Challenge Replay Attack Window

> What if an attacker captures a 401 response with digest challenge and replays it to trigger credential disclosure in subsequent requests?

**Impact:** `_last_challenge` is cached and reused. If an attacker can inject stale/malicious challenges, they might be able to influence the auth header generation process.

#### 🟠 HIGH (75%) — Memory Exhaustion from Malformed WWW-Authenticate Headers

> What if a malicious server sends extremely large or deeply nested `WWW-Authenticate` headers causing `parse_http_list()` to consume excessive memory?

**Impact:** DoS through memory exhaustion. The parsing happens before validation, and there's no apparent size limit on header processing.

#### 🟡 MEDIUM (80%) — Base64 Encoding Bloat with Large Credentials

> What if username/password contain binary data or are extremely long, causing the base64-encoded auth header to exceed HTTP header size limits?

**Impact:** Requests rejected by proxies/servers with header size limits. The code doesn't validate credential length before encoding.

#### 🟡 MEDIUM (85%) — Algorithm Case Sensitivity Mismatch

> What if the server sends `algorithm="md5"` (lowercase) but the lookup dictionary uses uppercase keys, causing a KeyError?

**Impact:** Authentication fails due to case mismatch. Code uses `challenge.algorithm.upper()` for lookup but stores the original case in the challenge object.

#### 🟡 MEDIUM (75%) — Infinite Auth Loop on Persistent 401s

> What if the server always returns 401 even with correct digest auth, causing the flow to infinitely retry authentication?

**Impact:** Infinite loop consuming resources. The generator doesn't track retry counts or detect authentication failure loops.

#### 🟡 MEDIUM (80%) — Stale Nonce Handling Without Server Guidance

> What if the server's nonce expires but doesn't provide a `stale=true` parameter, causing the client to retry with the same stale challenge indefinitely?

**Impact:** Authentication appears to work initially but fails on subsequent requests using cached challenge data. No mechanism to detect or handle stale nonces.

#### 🟡 MEDIUM (75%) — Cookie Injection During Auth Retry

> What if the response contains malicious cookies that get automatically attached to the retry request via `Cookies(response.cookies).set_cookie_header(request=request)`?

**Impact:** Unvalidated cookies from auth responses are blindly forwarded to retry requests, potentially enabling session fixation or injection attacks.

---

### Connection Pooling & Transport
**Files:** `httpx/_transports/default.py`
**Risks:** 9 (2C / 3H / 4M / 0L)

#### 🔴 CRITICAL (85%) — Connection Pool Starvation Cascade

> What if all connections are held by long-running requests when `max_connections` is reached?

**Impact:** New requests hang indefinitely waiting for available connections, creating cascading timeout failures across the application. Users see timeouts, background jobs fail, health checks fail.

#### 🔴 CRITICAL (80%) — HTTP/2 Stream Limit Exhaustion

> What if HTTP/2 multiplexing hits the server's max concurrent streams limit but httpx doesn't handle the GOAWAY gracefully?

**Impact:** Requests fail with obscure protocol errors instead of falling back to new connections. Particularly dangerous because HTTP/2 defaults to `http2=False`, so teams enabling it may not test this edge case thoroughly.

#### 🟠 HIGH (90%) — Keepalive Connection Reuse Race

> What if a keepalive connection gets closed by the server between the pool's availability check and actual request sending?

**Impact:** Request fails with connection errors instead of transparently retrying on a fresh connection. Creates intermittent failures that are hard to reproduce in testing.

#### 🟠 HIGH (85%) — Proxy Authentication Header Persistence

> What if proxy authentication headers leak into the actual request headers sent to the target server?

**Impact:** Sensitive proxy credentials exposed to downstream servers, potential security breach if servers log full request headers.

#### 🟠 HIGH (75%) — Socket Option Application Timing

> What if custom socket options conflict with HTTP/2 connection requirements or get applied after connection negotiation?

**Impact:** Connections fail to establish properly or negotiate wrong protocols. Silent degradation where connections work but with poor performance characteristics.

#### 🟡 MEDIUM (80%) — UDS Path Resolution Race

> What if the Unix Domain Socket path gets deleted/recreated between connection attempts during server restart?

**Impact:** Connection attempts fail with "No such file or directory" errors instead of retrying. Particularly problematic during rolling deployments.

#### 🟡 MEDIUM (75%) — Retry Logic Double-Execution

> What if the `retries=1` config causes non-idempotent requests (POST/PUT with side effects) to execute twice when connection fails mid-request?

**Impact:** Duplicate orders, payments, or other side effects. The httpcore layer may retry connection failures without knowing if the request body was partially sent.

#### 🟡 MEDIUM (75%) — SSL Context Validation Bypass

> What if `verify=True` with custom `cert` parameters creates an SSL context that validates the client cert but ignores server cert validation?

**Impact:** Man-in-the-middle attacks possible despite appearing to have SSL verification enabled. Subtle misconfiguration that passes basic testing.

#### 🟡 MEDIUM (70%) — Connection Pool Context Manager Leak

> What if the transport is used after `__exit__` is called but before garbage collection, or if `__exit__` raises an exception leaving the pool in invalid state?

**Impact:** Connections remain open consuming resources, or subsequent requests fail with obscure state errors. Memory leaks in long-running processes.

---

### Redirect Handling
**Files:** `httpx/_client.py`
**Risks:** 10 (2C / 3H / 4M / 1L)

#### 🔴 CRITICAL (85%) — Auth Header Persistence Across Malicious Redirects

> What if an attacker controls a redirect destination and the auth header isn't properly stripped when crossing origins?

**Impact:** API keys, bearer tokens, or credentials leaked to attacker-controlled domains. Complete account compromise.

#### 🔴 CRITICAL (90%) — Infinite Redirect Loop Resource Exhaustion

> What if circular redirect detection fails when URLs differ by query params, fragments, or encoding but resolve to same resource?

**Impact:** Memory exhaustion from growing redirect chain tracking, CPU spinning until timeout, DoS affecting all client requests.

#### 🟠 HIGH (80%) — Method Downgrade on Cross-Origin POST Redirect

> What if a POST to a payment endpoint redirects cross-origin and gets downgraded to GET, exposing sensitive data in URL logs?

**Impact:** Payment details, personal data exposed in server logs, referrer headers, browser history. GDPR/compliance violations.

#### 🟠 HIGH (75%) — Race Condition in Concurrent Redirect Following

> What if the same client follows redirects concurrently and redirect count tracking gets corrupted between threads?

**Impact:** max_redirects bypass leading to infinite loops, or premature termination of legitimate requests.

#### 🟠 HIGH (78%) — Fragment Injection in Location Header

> What if redirect location contains malicious fragment (#) that breaks URL parsing and causes client to request unintended endpoints?

**Impact:** Client makes requests to wrong URLs, potential SSRF if fragments manipulate host parsing, unexpected behavior.

#### 🟡 MEDIUM (82%) — Cookie Domain Confusion on Subdomain Redirects

> What if redirect from `api.example.com` to `evil.example.com` retains cookies due to loose domain matching?

**Impact:** Session cookies leaked to untrusted subdomain, session hijacking if subdomain is compromised.

#### 🟡 MEDIUM (75%) — HTTP/HTTPS Upgrade Detection Edge Case

> What if `_is_https_redirect()` incorrectly identifies non-upgrade redirects as upgrades when custom ports are involved (http://site:8080 → https://site:8443)?

**Impact:** Auth headers incorrectly preserved across what should be treated as cross-origin redirect, credential exposure.

#### 🟡 MEDIUM (88%) — Redirect Chain Header Accumulation

> What if headers from intermediate redirects accumulate in the final request instead of being reset?

**Impact:** Stale auth headers sent to wrong endpoints, cache headers causing incorrect caching behavior, debug headers leaking internal info.

#### 🟡 MEDIUM (72%) — Location Header Unicode Normalization Attack

> What if Location header contains Unicode characters that normalize differently causing origin comparison bypass?

**Impact:** Cross-origin redirect treated as same-origin, auth headers leaked to attacker domain using Unicode spoofing.

#### 🟢 LOW (85%) — Redirect Timing Side Channel

> What if time-to-redirect varies significantly based on internal routing, leaking information about infrastructure?

**Impact:** Internal network topology, endpoint existence, or routing logic exposed through timing analysis.

---

### SSL/TLS Configuration
**Files:** `httpx/_config.py`
**Risks:** 9 (2C / 3H / 3M / 1L)

#### 🔴 CRITICAL (85%) — Environment Variable CA Bundle Poisoning

> What if attacker controls SSL_CERT_FILE or SSL_CERT_DIR environment variables?

**Impact:** Complete TLS bypass - attacker can MITM all HTTPS traffic by providing malicious CA bundle that trusts their certificates. Silent data exfiltration without detection.

#### 🔴 CRITICAL (80%) — Client Certificate Private Key Exposure in Logs

> What if client certificate loading fails and stack traces log the certificate file paths or partial key data?

**Impact:** Private keys exposed in application logs, enabling impersonation attacks and unauthorized access to certificate-protected services.

#### 🟠 HIGH (90%) — verify=False Propagation in Production

> What if verify=False gets set in production due to development workarounds or configuration errors?

**Impact:** All HTTPS connections become vulnerable to MITM attacks. Credentials, API keys, and sensitive data transmitted in clear to attackers.

#### 🟠 HIGH (85%) — CA Bundle File Corruption or Deletion

> What if SSL_CERT_FILE points to corrupted, empty, or deleted certificate file?

**Impact:** SSL context creation fails silently or with cryptic errors, causing all HTTPS requests to fail. Service becomes unusable until fixed.

#### 🟠 HIGH (75%) — Hostname Verification Bypass on Custom Contexts

> What if developers pass pre-configured SSLContext that has check_hostname=False without realizing it?

**Impact:** Connections succeed to wrong servers with valid certificates, enabling subtle MITM attacks that bypass certificate validation.

#### 🟡 MEDIUM (80%) — Client Certificate Chain Loading Race Condition

> What if certificate file is rotated/updated while load_cert_chain() is reading it?

**Impact:** Partial certificate data loaded, causing SSL handshake failures and intermittent connection errors that are hard to diagnose.

#### 🟡 MEDIUM (75%) — trust_env Inconsistency Between Environments

> What if trust_env=True in production but SSL environment variables only exist in development?

**Impact:** Different SSL behavior across environments - connections that work in dev fail in production, or worse, use different CA validation.

#### 🟡 MEDIUM (70%) — Deprecated cert Parameter Memory Leak

> What if deprecated cert parameter is used repeatedly with different certificate files?

**Impact:** SSL contexts accumulate in memory without cleanup, potentially causing memory growth and eventual OOM in long-running services.

#### 🟢 LOW (75%) — Certificate Directory Traversal

> What if SSL_CERT_DIR contains symlinks that point outside expected certificate directories?

**Impact:** SSL context loads unintended certificate files, potentially including private keys or certificates that shouldn't be trusted.

---

### Multipart Uploads
**Files:** `httpx/_multipart.py`
**Risks:** 8 (1C / 3H / 4M / 0L)

#### 🔴 CRITICAL (85%) — Memory Exhaustion via Large File Streaming

> What if a file claims small size in headers but streams gigabytes without length validation?

**Impact:** OOM crash affecting all users, server becomes unresponsive

#### 🟠 HIGH (90%) — Boundary Collision Attack

> What if uploaded file content contains the exact multipart boundary sequence?

**Impact:** Parser confusion, data corruption, potential data leakage between form fields

#### 🟠 HIGH (80%) — Unicode Filename Encoding Mismatch

> What if filename contains Unicode characters that get mangled during HTML5 form encoding?

**Impact:** Files saved with wrong names, potential path traversal if encoding creates `../` sequences

#### 🟠 HIGH (75%) — File Handle Exhaustion via Unseekable Streams

> What if multiple large unseekable streams (pipes, network streams) are processed simultaneously?

**Impact:** Resource exhaustion, failed uploads for legitimate users

#### 🟡 MEDIUM (85%) — Content-Length Miscalculation with Mixed Encodings

> What if field names contain UTF-8 characters that expand during URL encoding?

**Impact:** HTTP protocol violations, request truncation, upstream proxy errors

#### 🟡 MEDIUM (80%) — MIME Type Spoofing via Extension Manipulation

> What if filename is "malware.txt.exe" and `mimetypes.guess_type()` only sees the ".txt"?

**Impact:** Bypassed security filters, malicious files served with safe MIME types

#### 🟡 MEDIUM (75%) — Chunked Transfer Encoding Edge Case

> What if content length calculation fails due to unseekable file, but server doesn't support chunked encoding?

**Impact:** Upload failures, inconsistent behavior across different server configurations

#### 🟡 MEDIUM (70%) — Concurrent File Access Race Condition

> What if the same file object is used in multiple concurrent multipart uploads?

**Impact:** Corrupted uploads, partial data, one request affecting another

---

### Request/Response Models
**Files:** `httpx/_models.py`, `httpx/_content.py`
**Risks:** 10 (2C / 3H / 4M / 1L)

#### 🔴 CRITICAL (85%) — Malicious Content-Encoding Bomb

> What if a malicious server sends a tiny gzipped response that decompresses to gigabytes?

**Impact:** Memory exhaustion crashes the application, affecting all users. Attackers can DoS with minimal bandwidth.

#### 🔴 CRITICAL (80%) — Charset Detection Bypass Attack

> What if malicious content uses encoding declaration mismatch (declares UTF-8 but contains Latin-1) to bypass input validation?

**Impact:** Charset auto-detection could interpret malicious payloads differently than downstream parsers, enabling injection attacks or data corruption.

#### 🟠 HIGH (90%) — Cookie Jar Race Condition

> What if concurrent requests modify the same CookieJar instance simultaneously?

**Impact:** Corrupted cookie state leads to authentication failures, session mixups between users, or lost session data requiring re-login.

#### 🟠 HIGH (85%) — Stream Double-Consumption

> What if code calls `response.read()` twice on a consumed stream without checking `StreamConsumed` exception?

**Impact:** Silent data loss or empty responses in retry scenarios. Business logic receives partial data thinking it's complete.

#### 🟠 HIGH (75%) — Header Encoding Bomb via Fallback Chain

> What if headers contain mixed encodings that cause the encoding detection loop to process massive headers repeatedly?

**Impact:** CPU exhaustion during encoding detection with crafted headers containing strategic decode failures across ASCII→UTF-8→ISO-8859-1 chain.

#### 🟡 MEDIUM (85%) — Content-Type Charset Injection

> What if `Content-Type: text/html; charset="utf-8\"; malicious=script"` bypasses the email.message parser?

**Impact:** Malformed charset declarations could cause parsing inconsistencies between httpx and downstream systems, potentially enabling header injection.

#### 🟡 MEDIUM (80%) — Decoder Chain State Corruption

> What if a `MultiDecoder` chain fails mid-stream and leaves partial decoded data in buffers?

**Impact:** Subsequent requests get corrupted data prepended from previous failed decode, causing parser errors or data integrity issues.

#### 🟡 MEDIUM (75%) — Link Header Regex DoS

> What if `_parse_header_links()` processes a Link header with nested patterns like `<http://a.com/(((((((`?

**Impact:** The `re.split(", *<", value)` with crafted input could trigger exponential backtracking, freezing request processing.

#### 🟡 MEDIUM (75%) — Streaming Body Leak on Connection Drop

> What if network connection drops mid-stream but `UnattachedStream` isn't properly closed?

**Impact:** File descriptors and memory leak over time as interrupted streams aren't cleaned up, eventually exhausting system resources.

#### 🟢 LOW (75%) — Headers Case Sensitivity Edge Case

> What if upstream systems depend on exact header casing but the case-insensitive Headers dict changes it?

**Impact:** Integration failures with legacy systems that expect `Content-Type` not `content-type`, causing API rejections or parsing errors.

---

### URL Parsing
**Files:** `httpx/_urls.py`, `httpx/_urlparse.py`
**Risks:** 8 (1C / 3H / 4M / 0L)

#### 🔴 CRITICAL (85%) — IDNA Decoding Bypass via Mixed Unicode/ASCII

> What if an attacker crafts a URL with mixed IDNA-encoded and Unicode characters that bypass host validation?

**Impact:** Security controls that validate hostnames could be bypassed, enabling SSRF attacks or redirect to malicious domains. `url.host` shows decoded Unicode while `url.raw_host` shows encoded ASCII - inconsistent validation between these could allow domain confusion attacks.

#### 🟠 HIGH (90%) — Username/Password Extraction from Malformed Userinfo

> What if userinfo contains multiple colons or encoded colon characters that break username/password parsing?

**Impact:** `username` and `password` properties use `partition(":")` which only splits on the first colon. URLs like `user%3Aname:pass%3Aword@host` could result in incorrect credential extraction, breaking auth flows or leaking sensitive data in logs.

#### 🟠 HIGH (80%) — Query Parameter Pollution via Encoding Mismatch

> What if query parameters contain both raw bytes and URL-encoded strings that get double-encoded or inconsistently decoded?

**Impact:** The `params` property creates `QueryParams` from raw query string, but kwargs handling converts bytes to ASCII. This encoding mismatch could cause parameter pollution attacks where `?user=admin&user%3D=hacker` creates ambiguous parameter sets.

#### 🟠 HIGH (75%) — Port Normalization Logic Confusion

> What if non-standard schemes use default ports that aren't in the normalization list?

**Impact:** Port normalization only handles "http", "https", "ws", "wss", and "ftp". Custom schemes like `redis://host:6379` won't normalize, causing `URL("redis://host") != URL("redis://host:6379")` even if 6379 is Redis's default port. This breaks URL equality checks and caching.

#### 🟡 MEDIUM (85%) — IDNA Exception Handling on Malformed Unicode

> What if `host` property encounters IDNA decoding failure on malformed xn-- domains?

**Impact:** `idna.decode(host)` can throw exceptions for malformed punycode. The code has no try/catch, so malformed domains like `xn--invalid` would crash the property access rather than gracefully falling back to raw representation.

#### 🟡 MEDIUM (80%) — Raw Path vs Path Encoding Inconsistency

> What if `raw_path` and `path` properties get out of sync due to encoding edge cases?

**Impact:** `raw_path` is used for HTTP requests while `path` is for display/logic. If certain byte sequences decode differently than they encode (normalization differences), the actual request path might differ from what application logic expects, causing routing failures.

#### 🟡 MEDIUM (75%) — Fragment Handling in URL Construction

> What if fragment contains characters that break when reconstructing URLs?

**Impact:** Fragment property is mentioned in docstring but not visible in the provided code. If fragments aren't properly encoded/decoded consistently with other URL components, URL reconstruction could generate invalid URLs or lose fragment data.

#### 🟡 MEDIUM (70%) — Kwargs Type Validation Bypass

> What if kwargs validation accepts None values but downstream code assumes non-None?

**Impact:** The type checking explicitly allows None values (`if value is not None`), but properties like `netloc.encode("ascii")` would fail if the underlying `_uri_reference.netloc` is None. This creates a validation gap.

---

### Content Decoders & Error Handling
**Files:** `httpx/_decoders.py`, `httpx/_exceptions.py`
**Risks:** 9 (2C / 3H / 4M / 0L)

#### 🔴 CRITICAL (85%) — Memory bomb through malicious compression

> What if an attacker sends a small compressed payload that expands to gigabytes when decompressed?

**Impact:** OOM crash bringing down the entire service. Classic zip bomb attack vector. All decoders (gzip, brotli, zstd) decompress without size limits.

#### 🔴 CRITICAL (80%) — Infinite loop in ZStandard multi-frame handling

> What if malicious zstd data creates a cycle where `unused_data` keeps producing more frames that reference each other?

**Impact:** CPU spin loop, service hangs indefinitely. The `while` loop in ZStandardDecoder assumes forward progress but doesn't validate frame integrity.

#### 🟠 HIGH (90%) — Resource exhaustion through decoder state accumulation

> What if a client opens thousands of concurrent streaming connections and never calls flush(), leaving decompressor objects with internal buffers hanging?

**Impact:** Memory leak as each decoder maintains internal state. No cleanup mechanism for abandoned decoders. Gradual service degradation.

#### 🟠 HIGH (85%) — Brotli package switching breaks production

> What if deployment switches from `brotli` to `brotlicffi` package and the method detection logic (`hasattr` checks) fails or behaves differently under load?

**Impact:** Runtime AttributeError crashes for all brotli-compressed requests. The dual-package support is fragile and untested in production.

#### 🟠 HIGH (80%) — MultiDecoder amplifies partial failures

> What if one decoder in the chain fails after partially processing data, but earlier decoders already consumed and transformed the input?

**Impact:** Data corruption or truncation. The chain processes sequentially but has no rollback mechanism. Partial success creates inconsistent state.

#### 🟡 MEDIUM (85%) — ByteChunker buffer grows unbounded

> What if chunk_size is large but incoming data arrives in tiny increments, causing the internal BytesIO buffer to grow but never flush?

**Impact:** Memory accumulation per connection. The buffer only flushes when reaching chunk_size, but small increments below threshold accumulate indefinitely.

#### 🟡 MEDIUM (80%) — Deflate fallback creates double-processing vulnerability

> What if the first deflate attempt fails but consumes/modifies the input data before falling back to the second decompressor instance?

**Impact:** Data corruption or failed decompression. The fallback mechanism doesn't preserve original input state between attempts.

#### 🟡 MEDIUM (75%) — TextDecoder encoding assumption breaks on dynamic headers

> What if Content-Type charset changes mid-stream or conflicts with actual byte encoding, but TextDecoder was initialized with hardcoded 'utf-8'?

**Impact:** Mojibake or replacement characters in decoded text. The encoding is set at initialization and can't adapt to runtime content discovery.

#### 🟡 MEDIUM (70%) — Flush ordering in MultiDecoder creates incomplete output

> What if flush() is called on MultiDecoder but some child decoders have internal state that requires specific flush ordering to complete properly?

**Impact:** Truncated or incomplete decoded data. The flush implementation processes children in reverse order but doesn't handle interdependencies.

---

## Methodology

This critique was generated by [Gremlin](https://pypi.org/project/gremlin-critic/) v0.2.0 using:
- **93 curated QA patterns** across 12 domains
- **Claude Sonnet** for risk reasoning with code context
- **Deep analysis** mode with 70% confidence threshold
- Source code from each feature area passed as context

Each area was analyzed independently with relevant source files provided as context.