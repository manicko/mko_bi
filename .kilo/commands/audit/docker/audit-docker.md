---
name: audit-docker
description: audit-docker
agent: auditor
alwaysApply: false
---

# Docker & Runtime Environment Audit — mkobi BI Dashboard

## Objective

Audit Docker setup for:
1. **Runtime correctness** — does Docker actually start? Do containers run without errors?
2. **Config validation** — does config match `docs/` requirements?
3. **Best practices** — does it follow current Docker/security standards beyond the spec?
4. **Doc accuracy** — when code diverges from docs, which is right?

**You MUST run Docker and verify it actually works. Static file checks alone are not sufficient.**

## Recommendation Types

Label every finding:
- `[RUNTIME-ERROR]` — Docker fails to start, containers crash, services unreachable
- `[SPEC-DEVIATION]` — config differs from docs. Decide: fix config or update docs.
- `[BEST-PRACTICE]` — improvement beyond current spec. Advisory, not mandatory.
- `[DOC-UPDATE]` — docs should reflect current config reality.

## Research

Use `websearch` to verify current best practices for:
- Docker security hardening
- Multi-stage build patterns
- Health check strategies
- Production deployment patterns

---

## Step 1 — Start Docker and Check Runtime Status

**This step is mandatory. Do not skip.**

### 1.1 Start services

```powershell
docker compose -f docker/docker-compose.yml up -d
```

Wait 30 seconds for services to initialize.

### 1.2 Check container status

```powershell
docker compose -f docker/docker-compose.yml ps
```

Verify all containers are in `running` or `healthy` state. If any container is `exited`, `restarting`, or `unhealthy` — this is a `[RUNTIME-ERROR]`.

### 1.3 Check logs for ALL services

For **each** service (app, db, redis), run:

```powershell
docker compose -f docker/docker-compose.yml logs <service>
```

Check for:
- **ERROR** or **FATAL** level messages
- Database connection failures (authentication errors, connection refused, database not found)
- Missing credentials or misconfigured passwords
- Import errors, missing modules, startup failures
- Health check failures
- Permission errors

**Every ERROR in logs must become a finding in the report.**

### 1.4 Check inter-service connectivity

```powershell
# Check if app reaches database
docker compose -f docker/docker-compose.yml logs app | Select-String -Pattern "database|db|postgresql|password|connection"

# Check if database is ready
docker compose -f docker/docker-compose.yml logs db | Select-String -Pattern "ready|accepting|listening"
```

### 1.5 Verify health endpoints

```powershell
# App health
curl http://localhost:8000/health

# If app is not reachable, check: is port 8000 mapped? Did the app crash?
```

### Document runtime findings

Record:
- Which containers started successfully and which didn't
- Every error from logs with full context (service, timestamp, error message, stack trace)
- Root cause analysis for each error (wrong password? missing role? mismatched config?)
- Inter-service connectivity issues

---

## Step 2 — Dockerfile Analysis

### Build Structure

- Multi-stage build with targets: `base`, `dev`, `test`, `prod`, `prod-slim` (per `docs/10-deployment/deployment.md`)
- `base` target: `python:3.12-slim-bookworm` with system dependencies only
- `dev` target: all dependencies (including dev), 1 worker with `--reload`
- `test` target: all dependencies (including dev), runs pytest
- `prod` target: production dependencies only, 4 uvicorn workers
- `prod-slim` target: minimal runtime, 1 worker, for constrained environments
- Pinned base image versions (no `latest` tags)
- No unnecessary system packages in production stages
- Dev dependencies excluded from `prod` and `prod-slim` stages

### Security

- Container does NOT run as root (non-root user configured)
- Secrets NOT baked into image (no `ENV JWT__SECRET_KEY=hardcoded`)
- `.env` file NOT copied into image
- No hardcoded credentials in any stage
- `uv.lock` copied for reproducible installs

### Runtime

- Correct startup command
- Healthcheck configured: `HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8000/health || exit 1`
- `uv` used as package manager (not pip directly)
- Predictable working directory (`/app`)
- `PYTHONUNBUFFERED=1` for log visibility

---

## Step 3 — Docker Compose Analysis

### Service Separation

- `app` — FastAPI backend
- `db` — PostgreSQL 16+
- `redis` — Redis 7 (for rate limiting, task queue)
- `rq-worker` — RQ worker for background processing (production)
- `nginx` — reverse proxy (optional, production profile)

### Compose Files

- `docker-compose.yml` — base services (app, db, redis)
- `docker-compose.override.yml` — development overrides (hot reload, dev dependencies)
- `docker-compose.test.yml` — test configuration
- Production profile: `docker compose --profile production up -d` (includes nginx)

### Volumes

| Volume | Container Path | Purpose |
|--------|---------------|---------|
| `postgres_data` | `/var/lib/postgresql/data` | Database persistence |
| `app_data` | `/app/data` | Uploads, logs, temp files |
| `redis_data` | `/data` | Task queue persistence (if used) |

### Environment Variables

- `ENV` — environment name (development/test/production)
- `DATABASE__HOST`, `DATABASE__PORT`, `DATABASE__PASSWORD` — DB connection
- `MKOBI_APP_PASSWORD` — application DB role password
- `JWT__SECRET_KEY` — JWT signing key (required in production)
- `CORS_ORIGINS` — explicit allowed origins
- `AUTO_MIGRATE=true` — runs Alembic migrations on startup
- `RECREATE_TEST_DB=true` — recreates test database (test env only)
- `RATE_LIMITER_FAIL_CLOSED` — rate limiter failure mode
- Production credentials enforced via `${JWT__SECRET_KEY:?JWT__SECRET_KEY is required}` syntax

### Restart Policies

- `app`: `restart: unless-stopped`
- `db`: `restart: unless-stopped`
- `redis`: `restart: unless-stopped`

### Networking

- No unnecessary exposed ports (only 8000 for app, 5432 for db if needed externally)
- Internal service communication via Docker network
- Services reference each other by service name (e.g., `db`, `redis`)

---

## Step 4 — Persistence & Temp Files

- Temp files directory: `/app/data` (mounted volume, survives container restarts)
- Temp file cleanup: application removes files after processing (success and failure)
- Stale temp file cleanup: `DatabaseStarter` removes orphaned files on startup
- PostgreSQL data persisted via named volume
- Redis data persisted via named volume (if used)

---

## Step 5 — Production Readiness

- Environment-based configuration (no `.env` in production)
- Configurable ports and hosts via env vars
- Logging to stdout/stderr (structured JSON logging)
- Debug mode disabled in production (`LOGGING__LEVEL=WARNING`)
- CORS origins explicitly configured (no wildcards)
- Health check endpoint available at `/health`
- `AUTO_MIGRATE=true` for automatic schema migrations
- Production credential enforcement

---

## Step 6 — Cross-Reference Runtime Errors with Config

For **every** `[RUNTIME-ERROR]` found in Step 1:

1. Identify which config file/setting causes the error
2. Trace the value through the chain: compose file → env var → container → application config → database connection
3. Determine root cause: is it a missing var? wrong password? init script not running? role not created?
4. Provide a concrete fix with the exact config change needed

**Example pattern:**
```
Log: "password authentication failed for user \"mkobi_app\""
→ Compose sets MKOBI_APP_PASSWORD via env var
→ App config reads it and constructs connection string
→ DB init script creates role with CREATE USER mkobi_app PASSWORD '...'
→ Mismatch: password in compose doesn't match what init script sets, OR init script didn't run, OR role doesn't exist yet at app startup
→ Fix: [specific change to reconcile the password]
```

---

## What Counts as Problems

### CRITICAL (from runtime)
- Container exits or crashes on startup
- Database connection fails (wrong password, role missing, DB unreachable)
- Authentication errors preventing app startup
- Health endpoint unreachable

### CRITICAL (from static analysis)
- Container runs as root
- Secrets baked into image
- Debug mode enabled in production
- Mutable runtime behavior (state stored only in container)

### HIGH
- No dependency pinning (missing `uv.lock`)
- No persistence strategy (no volumes for DB)
- Dev dependencies in production image
- No non-root user
- Missing production credential enforcement

### MEDIUM
- Oversized production image (unnecessary packages)
- Poor Dockerfile structure (not multi-stage)
- Inconsistent env var handling
- Missing Redis service (rate limiting won't work)
- No RQ worker service (background processing won't work)

---

## Report Format

Create file: `C:\py_dev\mkobi\.ai\audit\docker\audit_report_<number>.md` (next available number)

### Runtime Status Summary

```
Containers:
- app:    [running | exited | restarting] — [brief status]
- db:     [running | exited | restarting] — [brief status]
- redis:  [running | exited | restarting] — [brief status]

Health endpoint: [reachable | unreachable] — [response or error]
```

### Findings Table

| Severity | Type | File | Line | Problem | Impact | Recommendation |
|----------|------|------|------|---------|--------|----------------|
| CRITICAL | [RUNTIME-ERROR] | - | - | `password authentication failed for user "mkobi_app"` — DB init script didn't create the role or password mismatch | App cannot start at all | Fix DB init script or reconcile MKOBI_APP_PASSWORD |
| CRITICAL | [SPEC-DEVIATION] | docker-compose.yml | 23 | MKOBI_APP_PASSWORD defaults to placeholder | Role may have wrong password | Enforce with `${MKOBI_APP_PASSWORD:?...}` |
| HIGH | [BEST-PRACTICE] | Dockerfile | 45 | No HEALTHCHECK in Dockerfile | Image not self-contained for k8s/ECS | Add HEALTHCHECK instruction |
| MEDIUM | [DOC-UPDATE] | docker-compose.yml | 28 | Dev dependencies in prod | Larger attack scope | Update spec or split stages |

Type column: `[RUNTIME-ERROR]`, `[SPEC-DEVIATION]`, `[BEST-PRACTICE]`, or `[DOC-UPDATE]`.

### Final Assessment

```
Deployment Readyв/ / LOOKS_GOOD  
:- READY- PARTIALLY_READY
- NOT_READY
```

### Runtime Errors Section (if any)

For each runtime error:
- Full error message and stack trace excerpt
- Root cause analysis
- Config chain trace (how the bad value flows from compose → app → DB)
- Exact fix needed

### File-Level Recommendations

For each problematic file:

```
File: docker/docker-compose.yml

Problems:
- MKOBI_APP_PASSWORD not enforced
- Hardcoded dev secret in override

Recommendations:
- Use ${MKOBI_APP_PASSWORD:?MKOBI_APP_PASSWORD is required}
- Use ${JWT__SECRET_KEY:-dev-secret-key-for-local-development} in override
```
