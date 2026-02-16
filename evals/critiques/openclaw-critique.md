# OpenClaw Risk Analysis

**Project**: [openclaw/openclaw](https://github.com/openclaw/openclaw) — Personal AI Assistant Framework
**Scan Date**: February 15, 2026
**Tool**: Gremlin v0.2.0 (deep scan, 107 patterns)
**Feature Areas Scanned**: 9

---

## Executive Summary

| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | 16 | System compromise, data loss, security bypass |
| HIGH | 27 | Service degradation, resource exhaustion, race conditions |
| MEDIUM | 27 | Intermittent failures, UX issues, edge cases |
| LOW | 2 | Configuration quirks, cosmetic issues |
| **Total** | **72** | |

**Top 3 Risk Themes:**
1. **Security perimeter** — Tool execution privilege escalation, webhook signature bypasses, credential persistence after compromise
2. **Concurrency & state** — Multi-device session collisions, hot-reload races, reconnection thundering herds
3. **Resource exhaustion** — WebSocket frame bombs, dead letter queue overflow, session restore memory spikes

---

## Category 1: WebSocket Gateway

*Core transport layer — all channels connect through ws://127.0.0.1:18789*

### CRITICAL

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| WS-1 | **WebSocket Frame Bomb Attack** — Malicious client sends crafted frames with claimed 2GB payload length but only sends headers | 95% | Node.js pre-allocates buffer based on claimed length, exhausting memory instantly. Gateway crashes, all channels disconnect. |
| WS-2 | **Channel Identity Confusion During Reconnection** — Client reconnects with same session ID but different channel type | 90% | Messages route to wrong platforms. WhatsApp messages could appear in Slack workspace. Personal data leaks across channels. |

### HIGH

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| WS-3 | **Heartbeat Storm During Network Flap** — Mass disconnections followed by synchronized reconnection attempts | 92% | Thundering herd overwhelms event loop, new connections can't be established during critical recovery window. |
| WS-4 | **Binary Frame Memory Exhaustion** — Multiple channels send large attachments buffered in memory simultaneously | 85% | Memory spikes cause GC pauses, all connections timeout during freeze. Users see assistant as unresponsive. |
| WS-5 | **Device Pairing Race Condition** — Two devices pair with same account simultaneously, both receive success | 88% | Messages duplicate across devices, session state corrupts. User receives every response twice. |
| WS-6 | **Session Cleanup Memory Leak** — Abnormal connection closures (network drops) skip cleanup handlers | 83% | Session objects accumulate indefinitely. After days of operation, gateway OOMs during peak usage. |

### MEDIUM

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| WS-7 | **Agent Runtime Blocking Event Loop** — Synchronous operation hangs during user request processing | 85% | Entire gateway freezes, no heartbeats processed, all channels appear dead. |
| WS-8 | **Port Conflict During Development** — Multiple instances on same port 18789 | 87% | Gateway fails to start with confusing EADDRINUSE error. Hard to diagnose in containers. |
| WS-9 | **WebSocket Upgrade Header Injection** — Crafted upgrade request headers with newlines/control characters | 82% | Log corruption, monitoring misinterpretation, potential header smuggling in downstream proxies. |

---

## Category 2: Multi-Channel Messaging

*12+ messaging protocols bridged through unified inbox*

### CRITICAL

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| MC-1 | **Webhook Signature Replay Attack** — Attacker captures valid webhook payload and replays with original signature | 95% | Duplicate messages, spam, potential billing charges for outbound messages. |
| MC-2 | **Cross-Channel Message Loop** — WhatsApp-to-Slack bridge auto-forwards back to WhatsApp | 90% | Exponential message multiplication, API quota exhaustion across all channels, potential service suspension. |

### HIGH

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| MC-3 | **Signature Verification Timing Attack** — HMAC verification timing variance enables brute-force | 95% | Authentication bypass, spoofed messages injected into trusted channel. |
| MC-4 | **Rate Limit Cascade Failure** — Telegram rate limit causes queue backup that triggers WhatsApp limits | 90% | Complete messaging outage across all channels simultaneously. |
| MC-5 | **Adapter Memory Exhaustion on Large Media** — Discord 8MB files loaded into memory during format translation | 88% | OOM crashes when bridging large media files between channels. |
| MC-6 | **At-Least-Once Delivery Duplication Storm** — Network hiccup during webhook ACK causes redelivery to 6+ channels | 85% | Duplicate messages across all connected channels. |

### MEDIUM

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| MC-7 | **Unicode Normalization Mismatch** — iMessage NFD vs Matrix NFC causes broken emoji/international text | 92% | Corrupted messages, broken international communication. |
| MC-8 | **Webhook Signature Algorithm Confusion** — Discord payload sent to WhatsApp endpoint, RSA validated against HMAC key | 88% | Authentication bypass, incorrect message routing. |
| MC-9 | **Clock Skew Timestamp Verification** — Server clock drift beyond Signal webhook timestamp window | 85% | Valid messages rejected, intermittent hard-to-diagnose failures. |
| MC-10 | **Adapter State Poisoning** — Slack adapter crash leaves partial message in shared state | 83% | Corrupted message bridging, cross-channel contamination. |
| MC-11 | **Connection Pool Starvation** — Slow Matrix federation holds HTTP connections, starves fast channels | 82% | Fast channels (Telegram) become unresponsive due to resource contention. |

### LOW

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| MC-12 | **Feature Flag Channel Isolation Failure** — Disabled WhatsApp still shows contacts in inbox | 85% | Messages appear sent but never deliver. |

---

## Category 3: AI Agent Runtime & Tool Execution

*Agent workflows, tool sandboxing, and skills registry (ClawHub)*

### CRITICAL

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| AG-1 | **Tool Execution Privilege Escalation** — ClawHub skill executes with higher privileges than intended | 95% | Arbitrary code execution, system compromise, data exfiltration through browser automation. |
| AG-2 | **AI Model Injection via Tool Parameters** — Model crafts parameters that escape sandbox (shell injection) | 90% | Command execution on host system via device actions and cron job tools. |

### HIGH

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| AG-3 | **Skills Hot-Reload Race Condition** — Skill reloaded while agent mid-execution using that skill | 92% | Runtime crashes, partial state corruption, agent stuck in undefined state. |
| AG-4 | **Tool Timeout Bypass via Async Operations** — Tool spawns browser tabs/processes that outlive timeout | 88% | Resource leakage, zombie processes accumulate, eventual resource exhaustion. |
| AG-5 | **Workflow Dependency Deadlock** — Circular dependencies in tool ordering, sequential tools waiting on parallel tools | 85% | Agent hangs indefinitely, workflow never completes. |
| AG-6 | **ClawHub Registry Poisoning** — Malicious skill updates pass validation but contain backdoors | 83% | Persistent compromise of agent capabilities, data theft. |

### MEDIUM

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| AG-7 | **Tool Result Serialization Memory Bomb** — Browser automation captures massive DOM, exhausting memory | 90% | OOM crash affecting all agent instances. DoS through crafted web pages. |
| AG-8 | **AI Model Context Window Overflow** — Tool results exceed context window mid-workflow | 87% | Silent truncation of critical context. Agent makes decisions on incomplete information. |
| AG-9 | **Webhook Replay Attack in Tool Execution** — No idempotency on webhook tools | 85% | Duplicate browser sessions, repeated device commands, cascading side effects. |
| AG-10 | **Skills Registry Cache Poisoning** — HTTP 304 but skill changed, stale cached skills persist | 82% | Agent uses outdated implementations, hard-to-diagnose workflow failures. |
| AG-11 | **Tool Parameter Schema Drift** — Model outputs evolve faster than tool parameter schemas | 81% | Previously working workflows start failing without obvious cause. |

---

## Category 4: Voice & Audio Processing

*Always-on wake word detection on macOS, iOS, Android with ElevenLabs TTS*

### CRITICAL

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| VO-1 | **Audio Buffer Overflow on Long Sessions** — Continuous buffering without bounds checking | 95% | Application crash, device freeze, loss of conversation history. |
| VO-2 | **Wake Word False Positives with Sensitive Audio** — Detection triggers during private conversations/meetings | 90% | Privacy breach. Audio containing passwords, business secrets transmitted to processing servers. |

### HIGH

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| VO-3 | **Audio Device Switching Mid-Stream** — Bluetooth disconnect routes output to laptop speakers | 90% | Private AI responses broadcast in public/office setting. |
| VO-4 | **ElevenLabs Rate Limiting During Bursts** — Rapid voice interactions exceed rate limits | 88% | TTS responses fail silently, user perceives AI as broken. |
| VO-5 | **Concurrent Device Session Conflicts** — Voice activated on iPhone and Mac simultaneously | 85% | Duplicate API calls, audio feedback loops, session state corruption. |
| VO-6 | **ElevenLabs API Key Exposure in Memory Dumps** — Plaintext key in crash dumps | 85% | Unauthorized API usage, billing fraud, service disruption. |

### MEDIUM

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| VO-7 | **Audio Format Incompatibility** — Transcoding between iOS/Android/macOS degrades wake word accuracy | 85% | Increasing false negatives, user frustration with voice activation. |
| VO-8 | **Audio Stream Corruption During Network Handoff** — WiFi/cellular switch corrupts stream to ElevenLabs | 85% | Nonsensical TTS responses, conversation context lost. |
| VO-9 | **Background App Audio Interference** — Zoom/Spotify claims exclusive audio device access | 82% | Wake word detection stops silently. Missed voice commands. |
| VO-10 | **Wake Word Detection CPU Drain** — Always-on ML inference on mobile devices | 80% | Severe battery drain, users disable voice features. |

---

## Category 5: Device Pairing & Management

*Cross-platform device nodes connected via WebSocket + Tailscale*

### CRITICAL

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| DP-1 | **Credential Rotation Race Condition** — Certificate rotation during active pairing caches old cert | 95% | Device permanently orphaned with invalid credentials. Requires full re-setup. |
| DP-2 | **Tailscale Key Compromise During Network Failures** — Cleanup fails, leaving active node keys for orphaned sessions | 90% | Zombie devices retain remote access indefinitely. Former employees maintain backdoor. |

### HIGH

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| DP-3 | **Cross-Platform Session Desynchronization** — iOS backgrounds during reconnection while macOS claims same identity | 92% | Two platforms own same device, commands sent to wrong endpoint. |
| DP-4 | **WebSocket Certificate Chain Validation** — Intermediate cert expires but root passes | 88% | Platform-specific failures. iOS connects while Android fails. |
| DP-5 | **Device Capability Enumeration Attack** — Crafted pairing requests fingerprint network topology | 85% | Network reconnaissance, device fingerprinting, lateral movement preparation. |

### MEDIUM

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| DP-6 | **Orphaned Session Cleanup Cascade** — Cleanup job failure blocks processing of subsequent sessions | 90% | Growing zombie sessions, memory leaks, database bloat. |
| DP-7 | **Concurrent Device Claiming Race** — Two users claim same unclaimed device simultaneously | 87% | Double-claimed device with inconsistent ownership. |
| DP-8 | **Platform-Specific JSON Schema Drift** — iOS app updated but macOS still uses old schema | 83% | Silent data truncation, settings don't sync between platforms. |
| DP-9 | **WebSocket Reconnection Storm After Restart** — All devices reconnect simultaneously | 82% | Sustained load spikes, some devices never reconnect. |

### LOW

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| DP-10 | **Tailscale Env Var Mismatch** — API keys loaded before Docker env vars set, silent localhost fallback | 84% | Remote access silently disabled. Users can pair but not access remotely. |

---

## Category 6: Session Persistence & State

*Local-first architecture with workspace at ~/.openclaw/workspace*

### CRITICAL

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| SP-1 | **Workspace Directory Takeover** — Symlinks in ~/.openclaw/workspace point to /etc/passwd or ~/.ssh/keys | 95% | Agent reads/exposes sensitive system files. Complete system compromise. |
| SP-2 | **Session Resurrection Attack** — Restored session backup contains elevated permissions after revocation | 90% | Privilege escalation, access to tools beyond authorized scope. |

### HIGH

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| SP-3 | **Cross-Device Session Collision** — Two devices persist conflicting agent states to same workspace | 88% | Agent state corruption, lost conversation history, tool executions in wrong context. |
| SP-4 | **Gateway Restart Memory Exhaustion** — Thousands of sessions restored simultaneously with large histories | 85% | Memory exhaustion during startup, all users locked out. |
| SP-5 | **Orphaned Session Resource Leak** — Failed cleanup doesn't release file handles/db connections | 84% | Gradual exhaustion prevents new sessions. Silent degradation until failure. |
| SP-6 | **Database Migration State Corruption** — Partial migration leaves mixed schema sessions | 83% | Runtime errors for some users, data inconsistency between old/new format. |

### MEDIUM

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| SP-7 | **Workspace Permission Drift** — chmod/ownership changes between sessions | 87% | Sessions fail to start, agent configurations lost. |
| SP-8 | **Tool Context Poisoning** — Failed operations corrupt tool execution context, saved to persistent state | 82% | Tools fail mysteriously on session restore. |
| SP-9 | **Session Migration Race Window** — New session created during database migration, mixed state format | 81% | Undefined session state, data loss on next persist. |

---

## Category 7: Cron Jobs, Webhooks & Event Scheduling

*Event-driven pub/sub with per-channel webhook handlers*

### CRITICAL

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| EV-1 | **Dead Letter Queue Resource Exhaustion** — Failures accumulate faster than DLQ processing capacity | 90% | Unbounded queue growth until OOM. Complete system failure, data loss of legitimate events. |
| EV-2 | **Webhook Signature Verification Race** — Timing-unsafe comparison enables brute-force bypass | 85% | Complete webhook authentication bypass. Attacker injects arbitrary events. |

### HIGH

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| EV-3 | **Exponential Backoff Thundering Herd** — Synchronized retry timers across failed endpoints | 95% | Amplified load prevents recovery. Cascading failures across webhook providers. |
| EV-4 | **Webhook Replay Attack Window** — No timestamp validation allows indefinite replay of old webhooks | 90% | Duplicate processing of stale events, data corruption from time-sensitive operations. |
| EV-5 | **Concurrent Consumer State Corruption** — Events processed out of order (edit before create) | 88% | Inconsistent state, phantom data references, impossible UI states. |
| EV-6 | **Cron Job Clock Skew Drift** — System clock drift causes unexpected execution intervals | 85% | Critical maintenance tasks execute incorrectly, data inconsistency. |

### MEDIUM

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| EV-7 | **Webhook Content-Type Confusion** — JSON handler receives form-encoded, parsing errors bypass signature check | 92% | Processing failures, potential security bypass. |
| EV-8 | **Event Deduplication Key Collision** — Weak timestamp-based keys collide during high-frequency events | 90% | Lost events during rapid interactions (typing indicators, reactions). |
| EV-9 | **Cron Job Zombie Process Accumulation** — Subprocess cleanup fails on timeout | 85% | Slow resource leak, service instability during high activity. |
| EV-10 | **Dead Letter Queue Poison Message Loop** — DLQ processing itself fails and creates new DLQ entries | 83% | Infinite retry loops consuming processing capacity. |

---

## Category 8: Docker Deployment & Infrastructure

*Docker Compose with Tailscale, SSH tunnels, Node.js 22+*

### CRITICAL

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| DK-1 | **Tailscale Funnel Bypasses Container Network** — Internal ports exposed directly to internet | 95% | Databases, admin panels publicly accessible without auth. Complete security breach. |
| DK-2 | **Signal Handling Race During Orchestration** — SIGTERM arrives mid-transaction during Compose restart | 90% | Data corruption across multiple containers. Inconsistent state hard to detect/recover. |

### HIGH

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| DK-3 | **Environment Variable Injection via .env** — Attacker-controlled values override SSL_CERT_DIR | 95% | Complete TLS bypass, potential RCE via malicious certificates. |
| DK-4 | **Port 18789 Connection Exhaustion** — WebSocket connections accumulate during container restarts | 90% | New connections fail, application unresponsive. Requires manual intervention. |
| DK-5 | **SSH Tunnel Breaks During Network Partition** — App doesn't detect tunnel failure, continues processing | 85% | Operations appear successful but data never arrives. Silent data loss. |
| DK-6 | **Container Restart Policy Amplifies Failures** — Rapid restarts overwhelm healthy containers | 85% | Entire stack unstable as healthy services get overwhelmed by restart storms. |

### MEDIUM

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| DK-7 | **Service Discovery Lag After Recreation** — Old container IPs cached for 30+ seconds | 90% | Intermittent 502/503 errors during deployment window. |
| DK-8 | **Tailscale Network Split-Brain** — Different IP assignments break cached WebSocket connections | 85% | Active users lose connections mid-session. Real-time features stop working. |
| DK-9 | **Node.js 22+ Feature Flag Divergence** — Different containers run different experimental features | 85% | Inconsistent behavior across requests. Same input, different outputs. |
| DK-10 | **Docker Volume Mount Permission Drift** — UID/GID shifts make mounted volumes unreadable | 80% | Application starts but fails on file access. Misleading log messages. |

---

## Category 9: Authentication & Security

*OAuth, API keys, webhook signatures, tool sandboxing across 12+ channels*

### CRITICAL

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| AU-1 | **OAuth Token Scope Creep Between Services** — Token for service A reused for service B with broader permissions | 90% | Assistant gets delete/modify access across services intended for read-only. |
| AU-2 | **Device Credential Persistence After Compromise** — Cached tokens remain valid across all channels after device compromise | 85% | Attacker gains persistent access to all connected services. Local-first means credentials survive device wipes. |
| AU-3 | **Webhook Signature Algorithm Downgrade** — Verification accepts multiple algorithms, attacker forces weaker one | 88% | Malicious webhooks trigger unauthorized tool executions and data corruption. |

### HIGH

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| AU-4 | **WebSocket Auth Race During Reconnection** — New session before old session cleanup | 85% | Two authenticated sessions for same user. Sensitive data sent to wrong client. |
| AU-5 | **API Key Rotation Without Coordination** — Anthropic/OpenAI keys rotate but not all channels update | 90% | Partial degradation. Some channels work, others fail. Users retry causing cost spikes. |
| AU-6 | **Tailscale Split-Brain Authentication** — Stale ACL after network partition | 82% | Revoked user retains access until network heals. Compliance violations. |
| AU-7 | **Tool Sandbox Escape via Nested Execution** — Sandboxed tool spawns another tool with broader permissions | 83% | AI agent gains filesystem/network access beyond sandbox. Data exfiltration possible. |

### MEDIUM

| # | Risk | Confidence | Impact |
|---|------|-----------|--------|
| AU-8 | **Session Token Collision Across Device Types** — Insufficient entropy in token generation | 85% | Random logouts when using multiple devices. Inconsistent state. |
| AU-9 | **OAuth State Parameter Reuse** — State params not invalidated after use | 82% | Attacker hijacks OAuth callback, gains access to connected services. |
| AU-10 | **Local Data Encryption Key Derivation Weakness** — Keys derived from predictable device identifiers | 88% | Offline key derivation attack exposes conversation history and API keys. |

---

## Risk Heatmap

| Category | CRIT | HIGH | MED | LOW | Total |
|----------|------|------|-----|-----|-------|
| WebSocket Gateway | 2 | 4 | 3 | 0 | **9** |
| Multi-Channel Messaging | 2 | 4 | 5 | 1 | **12** |
| AI Agent Runtime | 2 | 4 | 5 | 0 | **11** |
| Voice & Audio | 2 | 4 | 4 | 0 | **10** |
| Device Pairing | 2 | 3 | 4 | 1 | **10** |
| Session Persistence | 2 | 4 | 3 | 0 | **9** |
| Cron/Webhooks/Events | 2 | 4 | 4 | 0 | **10** |
| Docker/Infrastructure | 2 | 4 | 4 | 0 | **10** |
| Auth & Security | 3 | 4 | 3 | 0 | **10** |
| **Total** | **19** | **35** | **35** | **2** | **91** |

---

## Pattern Coverage Analysis

### Domains That Matched Well
- **distributed** (6 patterns) — Cron, webhooks, message queues
- **auth** (8 patterns) — Device pairing, sessions, OAuth
- **deployment** (6 patterns) — Docker, env vars, containers
- **serialization** (6 patterns) — Cross-channel data, session persistence
- **infrastructure** (6 patterns) — TLS, networking, resource limits
- **Universal patterns** (28 patterns) — Concurrency, input validation, error paths, state, resources

### Domains With No Match
- payments, image_processing, search, frontend

### Recommended New Pattern Domains

Based on gaps revealed by this scan, the following domains would improve future scans:

| Proposed Domain | Keywords | Why Needed |
|-----------------|----------|------------|
| **websocket** | websocket, ws, wss, frame, socket, connection, upgrade, heartbeat, ping, pong, backpressure | Core transport not covered. Frame bombs, reconnection storms, upgrade injection. |
| **multi_channel** | channel, bridge, adapter, protocol, webhook, signature, hmac, delivery, inbox, relay | Protocol bridging creates unique risks: message loops, format mismatches, rate limit cascades. |
| **agent_execution** | agent, tool, skill, sandbox, execute, workflow, runtime, spawn, privilege, permission | AI tool execution has novel risks: privilege escalation, model injection, sandbox escape. |
| **voice_audio** | voice, audio, wake, microphone, speaker, tts, stt, stream, buffer, elevenlabs | Always-on audio creates unique privacy and resource risks. |
| **device_pairing** | device, pair, claim, node, credential, certificate, rotation, tailscale, tunnel | Cross-platform device management has pairing races, credential lifecycle, orphaned sessions. |

---

## Scan Methodology

- **Tool**: Gremlin v0.2.0 with 107 curated patterns (34 universal + 73 domain-specific)
- **Depth**: Deep (all scans)
- **Context**: Architecture-specific context provided per feature area based on project documentation
- **Limitations**: Scan based on project architecture description, not source code analysis. Results represent pattern-matched risk scenarios, not confirmed vulnerabilities.

---

*Generated by [Gremlin](https://github.com/abhi10/gremlin) — Exploratory QA risk analysis*
