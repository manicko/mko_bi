# Phase 01: Standalone Test Compose - Context

**Gathered:** 2026-05-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Convert `docker-compose.test.yml` from an overlay/override file (merged on top of `docker-compose.yml`) into a **fully standalone, independent compose configuration**. Test and dev environments must run in parallel without port conflicts, shared volumes, or shared networks. Dev environment should be cleaned up — production stays in `docker-compose.yml`, dev stays in `docker-compose.override.yml`, test gets its own complete file.

</domain>

<decisions>
## Implementation Decisions

### Architecture: fully separate containers

- Two completely independent environments: **dev** and **test**
- No merging, no overlay, no `docker compose -f docker-compose.yml -f docker-compose.test.yml`
- `docker-compose.test.yml` defines ALL services it needs from scratch
- Service names prefixed: `dev-db`, `test-db`, `dev-app`, `test-app`, etc.
- Zero shared state between environments — separate volumes, separate networks, separate containers

### Port mapping strategy

| Service | Dev (host→container) | Test (host→container) |
|---------|----------------------|-----------------------|
| App     | 8000 → 8000          | 8001 → 8000           |
| DB      | 5432 → 5432          | 5433 → 5432           |
| Redis   | 6379 → 6379          | 6380 → 6379           |

- Containers internally use standard ports — only host mapping differs
- Simple, obvious, no tricks

### Database isolation

- Separate `test-db` container, not sharing the dev DB container
- Separate Docker volume: `test_postgres_data` (dev uses `postgres_data`)
- Same Postgres 16 image, independent lifecycle
- Test DB name: `bidb_test`

### Service scope (test environment)

**Included:**
- `test-db` — PostgreSQL 16
- `test-redis` — Redis 7 (if tests depend on RQ / task queue)
- `test-migrate` — Alembic migrations against test-db
- `test-app` — Application in test mode (build target: `test`, `ENV=test`, `RECREATE_TEST_DB=true`)

**Excluded:**
- `nginx` — not needed for tests
- `rq-worker` — tests run via pytest, not via background workers
- Frontend — separate concern

### Network isolation

- Dev environment: `dev_network`
- Test environment: `test_network`
- Fully separate Docker bridge networks — no cross-environment DNS resolution
- Services communicate via compose service names within their own network

### Environment / config

- Single `.env` file for shared values (image tags, etc.)
- `docker-compose.test.yml` inline env overrides for test-specific values (`DATABASE__DBNAME=bidb_test`, `RECREATE_TEST_DB=true`, `AUTO_MIGRATE=true`)
- No separate `.env.test` file needed — test compose is self-contained

### Dev environment cleanup

- `docker-compose.yml` → production-only configuration (clean, no test artifacts)
- `docker-compose.override.yml` → dev environment (current behavior, unchanged)
- `docker-compose.test.yml` → fully standalone test configuration (this phase)
- Remove any test-related conditions/overrides from `docker-compose.yml`

### KiloCode's Discretion

- Exact `docker-compose.yml` cleanup steps (which lines to remove/move)
- Dockerfile `test` target details (if any changes needed)
- Test database initialization scripts
- Exact restart policies for test services
- Whether `test-migrate` should be a separate service or handled inside `test-app` entrypoint

</decisions>

<specifics>
## Specific Ideas

- "I want two working environments running in parallel — dev and test — with zero interference between them"
- The user's original note proposed 8001/5433 for test — this is adopted as the port scheme
- Standalone means standalone: no `extends`, no YAML anchors pointing to the main compose, no merge

</specifics>

<deferred>
## Deferred Ideas

- CI/CD pipeline integration with the test compose — separate phase
- Test data seeding / fixtures — separate phase
- Frontend test environment (if needed) — separate phase
- Docker Compose profiles for switching environments — possible future improvement

</deferred>

---

_Phase: 01-standalone-test-compose_
_Context gathered: 2026-05-24_
