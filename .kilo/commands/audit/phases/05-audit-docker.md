---
name: audit-docker
description: Docker and runtime environment audit covering Dockerfile, docker-compose, container health, security, persistence, production readiness, runtime verification
agent: audit-executor
alwaysApply: false
---

# Phase 5 Audit — Docker and Runtime Environment

**Executor:** audit-executor
**Status:** {pending|in-progress|complete}
**Validated:** {yes|no}

**IMPORTANT:** Base layer context is auto-included by orchestrator:
- Project: mkobi BI Dashboard (FastAPI + React + PostgreSQL)
- Structure: `.ai/structure/map.md`
- Commands: `.ai/context/commands.md`
- SPEC: `docs/SPEC.md`

---

## Phase-Specific File Paths

- `docker/Dockerfile`
- `docker/docker-compose.yml`
- `docker/docker-compose.override.yml`
- `docker/docker-compose.test.yml`
- `docker/.dockerignore`
- `.env`

---

## Checklist

### 1. Dockerfile Analysis

| Check | Status | Evidence |
|-------|--------|----------|
| Multi-stage build: base, dev, test, prod, prod-slim targets | | |
| Pinned base image versions (no `latest` tags) | | |
| No unnecessary system packages in production stages | | |
| Dev dependencies excluded from prod and prod-slim stages | | |
| Container does NOT run as root (non-root user configured) | | |
| Secrets NOT baked into image (no hardcoded credentials) | | |
| `.env` file NOT copied into image | | |
| No hardcoded credentials in any stage | | |
| `uv.lock` copied for reproducible installs | | |
| Correct startup command | | |
| Healthcheck configured: `HEALTHCHECK --interval=30s --timeout=5s --retries=3` | | |
| `uv` used as package manager (not pip directly) | | |
| Predictable working directory (`/app`) | | |
| `PYTHONUNBUFFERED=1` for log visibility | | |

### 2. Dependencies

| Check | Status | Evidence |
|-------|--------|----------|
| uv.lock: pinned dependencies, no floating versions | | |

### 3. Docker Compose Analysis

| Check | Status | Evidence |
|-------|--------|----------|
| Service separation: app (FastAPI), db (PostgreSQL 16+), redis (Redis 7) | | |
| Optional services: rq-worker (background processing), nginx (reverse proxy, production profile) | | |
| Volumes configured: postgres_data, app_data, redis_data | | |
| Restart policies: `restart: unless-stopped` for all services | | |
| Networking: internal communication via Docker network | | |
| No unnecessary exposed ports | | |
| Services reference each other by service name | | |

### 4. Environment Variables

| Check | Status | Evidence |
|-------|--------|----------|
| ENV — environment name (development/test/production) | | |
| DATABASE__HOST, DATABASE__PORT, DATABASE__PASSWORD — DB connection | | |
| MKOBI_APP_PASSWORD — application DB role password | | |
| JWT__SECRET_KEY — JWT signing key (required in production) | | |
| CORS_ORIGINS — explicit allowed origins | | |
| AUTO_MIGRATE=true — runs Alembic migrations on startup | | |
| RECREATE_TEST_DB=true — recreates test database (test env only) | | |
| RATE_LIMITER_FAIL_CLOSED — rate limiter failure mode | | |
| Production credentials enforced via `${VAR:?...}` syntax | | |
| No hardcoded secrets in compose files | | |

### 5. Health Checks

| Check | Status | Evidence |
|-------|--------|----------|
| db healthcheck: uses `pg_isready` | | |
| app healthcheck: HTTP `/health` endpoint | | |
| Configured intervals and retries for health checks | | |

### 6. Persistence

| Check | Status | Evidence |
|-------|--------|----------|
| `postgres_data` volume for database persistence | | |
| `app_data` volume for uploads, logs, temp files | | |
| `redis_data` volume for task queue persistence | | |
| Temp file cleanup on startup (DatabaseStarter removes orphaned files) | | |
| Temp files cleanup after processing (both success and failure) | | |

### 7. Security

| Check | Status | Evidence |
|-------|--------|----------|
| Non-root user in container | | |
| `.env` file not in image | | |
| No secrets baked into image | | |
| Debug mode disabled in production | | |
| CORS origins explicitly configured (no wildcards) | | |

### 8. Production Readiness

| Check | Status | Evidence |
|-------|--------|----------|
| Structured JSON logging | | |
| Debug disabled (`LOGGING__LEVEL=WARNING`) | | |
| Environment-based configuration | | |
| Auto-migrate enabled for automatic schema migrations | | |

### 9. Frontend Service

| Check | Status | Evidence |
|-------|--------|----------|
| Frontend service starts correctly | | |
| Responds on port 5173 | | |
| Proxy to backend works | | |
| Built frontend served on backend port (8000) | | |

---

## Runtime Verification Steps

### Step 1 — Start Docker and Check Runtime Status

**This step is mandatory. Do not skip.**

#### 1.1 Start services

```powershell
docker compose -f docker/docker-compose.yml up -d
```

Wait 30 seconds for services to initialize.

#### 1.2 Check container status

```powershell
docker compose -f docker/docker-compose.yml ps
```

Verify all containers are in `running` or `healthy` state. If any container is `exited`, `restarting`, or `unhealthy` — this is a `[RUNTIME-ERROR]`.

#### 1.3 Check logs for ALL services

For **each** service (app, db, redis), run:

```powershell
docker compose -f docker/docker-compose.yml logs <service>
```

Check for:
- ERROR or FATAL level messages
- Database connection failures
- Missing credentials or misconfigured passwords
- Import errors, missing modules, startup failures
- Health check failures
- Permission errors

#### 1.4 Test inter-service connectivity

```powershell
# Check if app reaches database
docker compose -f docker/docker-compose.yml logs app | Select-String -Pattern "database|db|postgresql|password|connection"

# Check if database is ready
docker compose -f docker/docker-compose.yml logs db | Select-String -Pattern "ready|accepting|listening"
```

#### 1.5 Verify health endpoints

```powershell
# App health
curl http://localhost:8000/health
```

If app is not reachable, check: is port 8000 mapped? Did the app crash?

### Step 2 — Verify Frontend

#### 2.1 Check frontend container status

```powershell
docker compose -f docker/docker-compose.yml -f docker/docker-compose.override.yml ps frontend
```

If frontend container is `exited` or `restarting` — this is a `[RUNTIME-ERROR]`.

#### 2.2 Check frontend container logs

```powershell
docker compose -f docker/docker-compose.yml -f docker/docker-compose.override.yml logs frontend
```

#### 2.3 Verify frontend responds

```powershell
# From host
Invoke-WebRequest -Uri http://localhost:5173/ -UseBasicParsing
```

Must return HTTP 200 with HTML containing `<div id="root">`.

#### 2.4 Verify frontend-to-backend proxy

```powershell
# From inside the frontend container
docker compose -f docker/docker-compose.yml -f docker/docker-compose.override.yml exec frontend wget -qO- http://app:8000/health
```

Must return `{"status":"healthy"}`.

#### 2.5 Verify built frontend on backend port

```powershell
# The backend (port 8000) should also serve the built frontend
Invoke-WebRequest -Uri http://localhost:8000/ -UseBasicParsing
```

Check:
- Returns HTTP 200
- HTML references a JS bundle that exists
- No ErrorBoundary fallback in the rendered page

---

## Findings

### DKR-{NN}: {Title}

| Field | Value |
|-------|-------|
| **ID** | DKR-{NN} |
| **Severity** | {severity} |
| **Type** | {type} |
| **Affected Modules** | {modules} |
| **Classification** | {mandatory\|advisory} |

**Description:** {description}

**Evidence:** {evidence}

**Recommendation:** {recommendation}

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |

## Mandatory Fixes

{List all findings classified as mandatory}

## Advisory Recommendations

{List all findings classified as advisory}

## Doc Updates Needed

{List all findings classified as DOC-UPDATE type}

---

## Template Field Reference

### Mandatory Fields Per Finding

| Field | Type | Values/Format |
|-------|------|---------------|
| `id` | string | Unique identifier with `DKR-` prefix (e.g., `DKR-001`, `DKR-002`) |
| `title` | string | Human-readable one-line summary |
| `type` | enum | `SPEC-DEVIATION`, `BEST-PRACTICE`, `DOC-UPDATE`, `RUNTIME-ERROR` |
| `severity` | enum | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `description` | string | Detailed problem description with context |
| `evidence` | string | File paths, line references, log excerpts, code snippets |
| `affected_modules` | list | Affected module paths (e.g., `docker/`, `.env`) |
| `recommendation` | string | Concrete fix direction: what to change and why |
| `classification` | enum | `mandatory` (security, data loss, correctness) or `advisory` (improvement, refactoring) |

### Classification Guide

- **mandatory**: Security vulnerabilities, data loss risks, correctness issues, spec deviations requiring immediate fix
- **advisory**: Code quality improvements, refactoring suggestions, best practice enhancements

---

**Report Format:** See `.kilo/commands/audit/templates/audit-findings.md` for full template.