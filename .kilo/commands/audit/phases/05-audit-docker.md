---
name: 05-docker
description: Infrastructure audit covering reproducibility, secrets management, isolation, resilience, and deployment safety
agent: audit-executor
alwaysApply: false
problems-only: true
---

# Phase 05 Audit — Infrastructure & Runtime Environment

## Output Mode

`problems-only: true` — **only problems, bugs, and deviations are documented.**

- **Do NOT** write sections that say "X is correct" or "no issues found in Y".
- **Do NOT** include checklist rows where the check passes — omit them entirely.
- If a dimension has zero findings after investigation, **omit the dimension entirely**.
- Every finding must be actionable: it describes a real problem, its evidence (code/logs/output), and its impact.
- If `problems-only: false` were set, you would produce a full report with compliance statements. But it is `true`, so the report is exclusively findings.

---

## Discovery Stage

Before performing audit checks, discover the project's infrastructure architecture:

1. **Container Discovery** — Identify container definition files, map service separation, discover volume/mount configurations, locate health checks.
2. **Build Discovery** — Identify multi-stage build strategy, map dependency management, discover artifact optimizations, find build caching.
3. **Secrets Discovery** — Identify secret injection mechanisms, map configuration priority, discover secrets never baked into images, find prod vs dev differences.
4. **Runtime Discovery** — Identify restart policies, map service dependencies and startup order, discover resource limits, find backup/restore procedures.

---

## Mandatory Runtime Verification

**Before evaluating any checklist item, you MUST complete these steps. Use the commands provided in the project's commands file. Skip only if a step is impossible — document why.**

### Step R1 — Build All Container Images

Build all services using the project's container build commands.

- **Record the full output.** A build failure is CRITICAL — the app cannot be deployed.
- Check build time: note if build is unreasonably long (inefficient caching, too many layers).
- Check image sizes: note if images are excessively large (missing multi-stage build, unnecessary packages).

### Step R2 — Start the Full Stack

Start all services in detached mode and verify their status.

- Verify all services are in `running` or `healthy` state.
- If any service is `restarting`, `exited`, or `unhealthy`, that is a CRITICAL finding.

### Step R3 — Inspect Container Logs for Errors

Wait after startup, then inspect logs for ALL services.

- **Search each log for ERROR, CRITICAL, FATAL, traceback, exception, failed, denied.**
- Every error in the log is a finding. The error message, service name, and timestamp are evidence.
- If the backend crashes on startup, that is CRITICAL — the API does not work.
- If the frontend fails to build/render in the container, that is CRITICAL — the UI does not work.
- If the database fails to accept connections, that is CRITICAL — the entire system is down.
- Warnings should also be recorded as LOW or MEDIUM depending on impact.

### Step R4 — Verify Health Checks Work

Inspect each service's health status.

- For each service with a health check: verify it reports `healthy`.
- For each service without a health check: verify one exists and that it actually checks functional readiness (not just "process started").

### Step R5 — Verify Service Connectivity

From inside each container, test connectivity to its dependent services.

- Non-200 responses (or connection refused) are CRITICAL — services cannot communicate.
- Document the expected topology and compare with actual connectivity.

### Step R6 — Verify Port Exposure and Network Isolation

Inspect published ports and network configuration.

- Verify only necessary ports are exposed to the host. Any unnecessary port exposure is a finding.
- Verify internal services (DB, Redis) are NOT exposed to the host. If the DB port is published, that is a security finding.
- Verify services are on the expected network(s).

### Step R7 — Verify Secret Injection

Check that no secrets are baked into images at build time.

- Verify secrets come from environment variables or mounted secret files, not from Docker build-time instructions.
- If secrets appear in image layers, that is CRITICAL.

### Step R8 — Graceful Shutdown Behavior

Stop a service and check its logs for graceful shutdown messages.

- No cleanup = resources may leak. Finding.
- Restart the service after verification.

---

## Audit Scope

Reproducibility, secrets management, isolation, resilience, container security, deployment safety.

---

## Audit Dimensions

### 1. Reproducibility

| Check | Description |
|-------|-------------|
| Base images use pinned versions | No `latest` tags. |
| Dependencies pinned to specific versions | No floating versions. |
| Build produces reproducible artifacts | Same input produces same output. |
| Configuration files version-controlled | No manual config drift. |
| No manual steps required for deployment | Fully automated deployment. |

**Evidence required:** Step R1 build output. Read each Dockerfile for `FROM` lines with `latest` tag.

### 2. Secrets Management

| Check | Description |
|-------|-------------|
| Secrets injected via environment/files, not hardcoded | No hardcoded secrets in compose files. |
| No secrets baked into container images | No secrets in image layers. |
| Secret injection supports multiple sources | `.env`, `_FILE`, etc. |
| Production credentials enforced at startup | App fails to start without real secrets. |
| Development credentials not used in production | Separate credential sets. |

**Evidence required:** Step R7 secret injection analysis. Step R3 logs for startup validation of secrets.

### 3. Isolation

| Check | Description |
|-------|-------------|
| Development environment isolated from production | Separate compose files or profiles. |
| Test environment uses separate database | No shared DB between test and dev/prod. |
| Service-to-service communication via defined network | Explicit network configuration. |
| No unnecessary port exposure | Only required ports published. |
| File system isolation (volumes for data only) | No shared code volumes. |

**Evidence required:** Step R6 network and port analysis. Read compose files for network definitions.

### 4. Resilience

| Check | Description |
|-------|-------------|
| Health checks verify service liveness | Health checks exist and work. |
| Health check intervals appropriate | Not too aggressive or too lax. |
| Services restart on failure | Restart policy is configured. |
| Graceful shutdown implemented | Cleanup on shutdown. |
| Resource cleanup on startup | Stale files removed. |
| Error handling prevents cascade failures | One service failure doesn't bring down others. |

**Evidence required:** Step R4 health check verification. Step R3 logs for crash messages. Step R8 graceful shutdown. Read compose files for restart policy.

### 5. Container Security

| Check | Description |
|-------|-------------|
| Containers run as non-root user | `USER` directive in Dockerfile. |
| No unnecessary system packages in production images | Minimal production images. |
| Multi-stage builds separate build from runtime | Build tools not in production. |
| Development dependencies excluded from production | Dev packages not in prod image. |

**Evidence required:** Check the user inside running containers. Read Dockerfiles for `USER` directive and multi-stage structure.

### 6. Deployment Safety

| Check | Description |
|-------|-------------|
| Debug mode disabled in production | No debug flags in prod config. |
| Logging level appropriate for production | Not DEBUG in production. |
| Production refuses insecure defaults | Fail-fast on bad config. |
| Migration strategy defined and tested | Migrations run automatically or documented. |
| Rollback procedure documented | How to roll back a bad deploy. |

**Evidence required:** Read production compose/config files for debug flags. Step R3 logs for log level. Check migration execution strategy.

---

## Report Output

Write findings to: `.ai/audit/05-infrastructure/findings.md` using template `.ai/audit/templates/audit-findings.md`.

Use prefix `INF-` for finding IDs.

**`problems-only: true` rules:**
- The report contains **only findings** — real problems discovered during investigation.
- Do NOT include sections, dimensions, or checklist rows where everything is correct.
- If after completing all Runtime Verification steps and all Audit Dimensions, no problems were found, write a single line: `No problems found in this phase.`
- Every finding MUST include:
  1. **Runtime evidence** — container build output, container logs, health check status, connectivity test results.
  2. **Not just:** "violates invariant X" — show the exact Dockerfile line, compose service definition, or log entry.
