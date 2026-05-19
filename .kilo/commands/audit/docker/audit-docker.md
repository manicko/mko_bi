---
name: audit-docker
description: audit-docker
agent: auditor
alwaysApply: false
---

# Docker & Runtime Environment Audit — mkobi BI Dockerfile

## Dockerfile Verification

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

- Correct startup command: `uv run uvicorn mkobi.main:app --host 0.0.0.0 --port 8000`
- Healthcheck configured: `HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8000/health || exit 1`
- `uv` used as package manager (not pip directly)
- Predictable working directory (`/app`)
- `PYTHONUNBUFFERED=1` for log visibility

---

## Docker Compose / Orchestration Verification

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

## Persistence & Temp Files

### Verify

- Temp files directory: `/app/data` (mounted volume, survives container restarts)
- Temp file cleanup: application removes files after processing (success and failure)
- Stale temp file cleanup: `DatabaseStarter` removes orphaned files on startup (threshold: `STALE_FILE_THRESHOLD_HOURS`, default 24h)
- PostgreSQL data persisted via named volume
- Redis data persisted via named volume (if used)

---

## Production Readiness

### Verify

- Environment-based configuration (no `.env` in production)
- Configurable ports and hosts via env vars
- Logging to stdout/stderr (structured JSON logging)
- Debug mode disabled in production (`LOGGING__LEVEL=WARNING`)
- CORS origins explicitly configured (no wildcards)
- Health check endpoint available at `/health`
- `AUTO_MIGRATE=true` for automatic schema migrations
- Production credential enforcement (refuses to start without `JWT__SECRET_KEY` and `DATABASE__PASSWORD`)

---

## Dependency Management

### Verify

- `uv` used as package manager
- `uv.lock` present and committed (reproducible installs)
- `pyproject.toml` defines all dependencies
- Lock file consistent with `pyproject.toml`
- No pip fallback in Dockerfile

---

## What Counts as Problems

### CRITICAL
- Container runs as root
- Secrets baked into image
- Debug mode enabled in production
- Mutable runtime behavior (state stored only in container)
- No health check configured

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

### Findings Table

| Severity | File | Line | Problem | Impact | Recommendation |
|----------|------|------|---------|--------|----------------|
| CRITICAL | Dockerfile | 12 | container runs as root | security risk | add non-root user |
| HIGH | docker-compose.yml | 45 | no volume for postgres_data | data loss on restart | add named volume |
| MEDIUM | Dockerfile | 28 | dev dependencies in prod | larger attack scope | use multi-stage build |

### Final Assessment

```text
Deployment Readiness:
- READY
- PARTIALLY READY
- NOT READY
```

### File-Level Recommendations

For each problematic file:

```text
File: Dockerfile

Problems:
- single-stage build (no multi-stage)
- runs as root
- .env copied into image

Recommendations:
- implement multi-stage build (base/dev/test/prod)
- add non-root USER instruction
- remove .env COPY, use env vars or Docker secrets
- add HEALTHCHECK instruction
```
