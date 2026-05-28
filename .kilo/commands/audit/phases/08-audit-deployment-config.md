---
name: 08-deployment-config
description: Deployment and configuration audit covering config management, startup lifecycle, deployment options, performance, stability, no-overengineering check
agent: audit-executor
alwaysApply: false
---

# Phase 08 Audit â€” Deployment & Configuration

**Executor:** audit-executor
**Status:** {pending|in-progress|complete}
**Validated:** {yes|no}

**IMPORTANT:** Base layer context is auto-included by orchestrator  (SKIP if you already have it):
- Project: mkobi BI Dashboard (FastAPI + React + PostgreSQL)
- Structure: `.ai/structure/map.md`
- Commands: `.ai/context/commands.md`
- SPEC: `docs/SPEC.md`

---

## Audit Dimensions

### 1. Configuration

Verify `src/mkobi/config.py` and `src/mkobi/settings/`:

| Check | Status | Evidence |
|-------|--------|----------|
| Pydantic-settings for config loading | | |
| Priority: env vars > Docker secrets > .env > app.yaml > defaults | | |
| Secrets via env vars (DATABASE__PASSWORD, JWT__SECRET_KEY) | | |
| Docker secrets support (_FILE suffix) | | |
| .env file for development only | | |
| app.yaml for non-sensitive settings only | | |
| Production credential enforcement at startup | | |

**Files to Audit:**
- `src/mkobi/config.py`
- `src/mkobi/settings/app.yaml`

### 2. Docker Secrets

Verify Docker secrets implementation:

| Check | Status | Evidence |
|-------|--------|----------|
| _FILE suffix support for secrets | | |
| Secrets read from files in production | | |
| .env used only in development | | |

### 3. Startup Lifecycle

Verify `src/mkobi/db/starter.py` and lifespan in `src/mkobi/app.py`:

| Check | Status | Evidence |
|-------|--------|----------|
| Dependency check (all required packages importable) | | |
| Database connectivity check (SELECT 1) | | |
| Schema existence check (alembic_version table) | | |
| Alembic migrations (when AUTO_MIGRATE=true) | | |
| Admin user creation (idempotent, SAVEPOINT for race conditions) | | |
| Stale temp file cleanup (STALE_FILE_THRESHOLD_HOURS, default 24h) | | |
| Test database recreation (when ENV=test or RECREATE_TEST_DB=true) | | |
| Application ready (accepts requests, task queue initialized) | | |
| Shutdown: engine connections disposed | | |

**Files to Audit:**
- `src/mkobi/db/starter.py`
- `src/mkobi/app.py`

### 4. Production Credential Enforcement

Verify startup security:

| Check | Status | Evidence |
|-------|--------|----------|
| Refuses to start with default admin/admin credentials | | |
| CORS origins validated at startup in production mode | | |

### 5. Docker Configuration

Verify `Dockerfile` and `docker-compose.yml`:

| Check | Status | Evidence |
|-------|--------|----------|
| Multi-stage build (dev, test, prod, prod-slim targets) | | |
| Only necessary dependencies in production image | | |
| Environment variables passed correctly | | |
| Volumes for data persistence (postgres_data, app_data) | | |
| Health checks (db: pg_isready, app: HTTP GET /health) | | |
| Non-root container user | | |
| No secrets baked into image | | |
| .env not copied into image | | |

**Files to Audit:**
- `docker/Dockerfile`
- `docker/docker-compose.yml`
- `docker/docker-compose.override.yml`
- `.env`, `.env.example`

### 6. Deployment Options

Verify deployment configurations:

| Check | Status | Evidence |
|-------|--------|----------|
| Development: React dev server (5173) + FastAPI (8000) with CORS | | |
| Development: Hot reload for both servers | | |
| Production Option A: FastAPI serves built React static files (frontend/dist) | | |
| Production Option A: StaticFiles for JS/CSS | | |
| Production Option A: All non-API routes fall through to React index.html | | |
| Production Option B: Nginx proxies /api -> FastAPI, everything else -> React SPA | | |
| Production Option B: SSL termination at Nginx | | |

### 7. Performance & Database

Verify performance-related configurations:

| Check | Status | Evidence |
|-------|--------|----------|
| JSONB GIN index on aggregated_data.dims | | |
| Connection pooling (asyncpg pool) | | |
| Short transactions (no deadlocks) | | |
| N+1 problems addressed (eager loading where needed) | | |
| Rate limiting configured (protection from abuse) | | |

**Files to Audit:**
- `src/mkobi/db/models/aggregated_data.py`
- `src/mkobi/db/repositories/`

### 8. Stability

Verify API stability measures:

| Check | Status | Evidence |
|-------|--------|----------|
| Error isolation (one endpoint failure doesn't crash others) | | |
| Long-running requests (timeout handling) | | |
| Rate limiting (protection from abuse) | | |
| CORS configured correctly (FastAPI CORSMiddleware, explicit origins/methods/headers) | | |

### 9. No Overengineering Check

Verify absence of unnecessary abstractions:

| Check | Status | Evidence |
|-------|--------|----------|
| No Redux/Zustand (TanStack Query sufficient for server state) | | |
| No unnecessary abstraction layers (axiosInstance -> direct API calls) | | |
| No duplicated Pydantic models | | |
| No complex patterns without necessity | | |
| No enterprise patterns where not required | | |

---

## Findings

### DC-{NN}: {Title}

| Field | Value |
|-------|-------|
| **ID** | DC-{NN} |
| **Severity** | {severity} |
| **Type** | {type} |
| **Affected Modules** | {modules} |
| **Classification** | {mandatory|advisory} |

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
| `id` | string | Unique identifier with `DC-` prefix (e.g., `DC-001`, `DC-002`) |
| `title` | string | Human-readable one-line summary |
| `type` | enum | `SPEC-DEVIATION`, `BEST-PRACTICE`, `DOC-UPDATE`, `RUNTIME-ERROR` |
| `severity` | enum | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `description` | string | Detailed problem description with context |
| `evidence` | string | File paths, line references, log excerpts, code snippets |
| `affected_modules` | list | Affected module paths (e.g., `src/mkobi/config/`, `docker/`) |
| `recommendation` | string | Concrete fix direction: what to change and why |
| `classification` | enum | `mandatory` (security, data loss, correctness) or `advisory` (improvement, refactoring) |

### Classification Guide

- **mandatory**: Security vulnerabilities, access control violations, data loss risks, correctness issues requiring immediate fix
- **advisory**: Best practice enhancements, security hardening suggestions

---

**Report Format:** See `.ai/audit/templates/audit-findings.md` for full template.