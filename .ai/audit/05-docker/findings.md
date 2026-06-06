# Phase 05 Audit Findings — Infrastructure & Runtime Environment

**Executor:** audit-executor
**Template:** .kilo/commands/audit/phases/05-audit-docker.md
**Status:** complete
**Validated:** no

---

## Findings

### INF-001: nginx image uses unversioned `alpine` tag

| Field | Value |
|-------|-------|
| **ID** | INF-001 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `docker/docker-compose.yml` (nginx service, line 178) |
| **Classification** | advisory |

**Description:** The nginx service in `docker-compose.yml` uses `image: nginx:alpine` — a floating tag with no major or minor version pin. Unlike `postgres:16` and `redis:7-alpine` which pin to a major version, `nginx:alpine` will resolve to different nginx versions across pulls, breaking reproducibility. An `alpine` tag update could introduce breaking changes (e.g., nginx 1.26 → 1.28 config incompatibilities) without any code change.

**Evidence:** `docker/docker-compose.yml` line 178: `image: nginx:alpine`. Compare with `db` (line 15): `image: postgres:16` and `redis` (line 117): `image: redis:7-alpine` which both pin major versions.

**Recommendation:** Pin to a specific version, e.g., `nginx:1.27-alpine` or `nginx:1.27.4-alpine`. Follow the same version-pinning pattern used by other services in the compose file.

---

### INF-002: No resource limits on any service

| Field | Value |
|-------|-------|
| **ID** | INF-002 |
| **Severity** | HIGH |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `docker/docker-compose.yml` (all services) |
| **Classification** | advisory |

**Description:** No Docker Compose service defines `mem_limit`, `cpus`, or `deploy.resources.limits`. Runtime verification confirms all containers have `Memory:0 CPUs:0` (unlimited). In production, a single service (e.g., a large Polars aggregation or a malformed upload) can consume all host memory/CPU, causing OOM kills or cascading failures across all co-located services.

**Evidence:** `docker inspect docker-app-1 --format='Memory:{{.HostConfig.Memory}} CPUs:{{.HostConfig.NanoCpus}}'` returns `Memory:0 CPUs:0`. Same for `docker-db-1`. No `deploy.resources.limits` or `mem_limit`/`cpus` keys in any service in `docker/docker-compose.yml`.

**Recommendation:** Add resource limits to all production services. For example:
- `app`: `mem_limit: 1g`, `cpus: 1.0`
- `db`: `mem_limit: 2g`, `cpus: 2.0`
- `redis`: `mem_limit: 512m`, `cpus: 0.5`
- `rq-worker`: `mem_limit: 1g`, `cpus: 1.0`
- `nginx`: `mem_limit: 256m`, `cpus: 0.5`

---

### INF-003: Duplicate migration execution — AUTO_MIGRATE=true with dedicated migrate service

| Field | Value |
|-------|-------|
| **ID** | INF-003 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `docker/docker-compose.yml` (app service, line 100; migrate service) |
| **Classification** | advisory |

**Description:** The production `app` service has `AUTO_MIGRATE: "true"` (line 100) AND `depends_on: migrate: condition: service_completed_successfully` (line 76). The `migrate` service already runs `alembic upgrade head` before the app starts. Then the app startup also runs migrations via `AUTO_MIGRATE=true`. This causes redundant migration execution on every container start. While the PostgreSQL advisory lock prevents parallel corruption, the double execution adds unnecessary startup latency and log noise.

**Evidence:** `docker/docker-compose.yml` line 100: `AUTO_MIGRATE: "true"`. Line 76: `depends_on: migrate: condition: service_completed_successfully`. The `migrate` service (line 45): `command: ["alembic", "upgrade", "head"]`. The dev override correctly sets `AUTO_MIGRATE: "false"` (line 67), but the production compose does not.

**Recommendation:** Set `AUTO_MIGRATE: "false"` in the `app` service of `docker/docker-compose.yml` since the dedicated `migrate` service already handles schema updates. This aligns with the documented migration strategy in `docs/10-deployment/deployment.md`: "For production Docker Compose deployments, a dedicated migrate service runs alembic upgrade head before the app service starts... This allows AUTO_MIGRATE=false in the app config."

---

### INF-004: rq-worker health check is non-functional

| Field | Value |
|-------|-------|
| **ID** | INF-004 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `docker/docker-compose.yml` (rq-worker service, line 165) |
| **Classification** | advisory |

**Description:** The rq-worker health check uses `test: ["CMD", "pgrep", "-f", "rq"]` which only verifies a process with "rq" in its command line exists. This is a superficial liveness check — it does not verify the worker can connect to Redis, accept jobs, or process them. A zombie process or a worker that lost its Redis connection would still pass this health check. A health check should verify functional readiness, not just process existence.

**Evidence:** `docker/docker-compose.yml` line 165: `test: ["CMD", "pgrep", "-f", "rq"]`. Compare with the `app` health check (line 109) that hits `curl -f http://localhost:8000/health` — a functional endpoint that verifies DB connectivity.

**Recommendation:** Replace `pgrep -f rq` with a functional health check. Options:
1. Add a `/health` endpoint to the RQ worker that checks Redis connectivity (preferred).
2. Use a script that checks both process existence AND Redis connectivity: `pgrep -f rq && redis-cli -h redis -p 6379 ping`.
3. At minimum, check that the worker process is running AND can reach Redis.

---

### INF-005: Persistent database authentication failures from external clients

| Field | Value |
|-------|-------|
| **ID** | INF-005 |
| **Severity** | MEDIUM |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `docker/docker-compose.override.yml` (db port exposure), running `docker-db-1` container |
| **Classification** | advisory |

**Description:** The development database container (`docker-db-1`) has 148+ `FATAL: password authentication failed for user "postgres"` errors in its logs, with 31 occurring in the last 5 hours alone. The failures come in rapid pairs (within milliseconds) followed by exponential backoff gaps, indicating an external client (IDE, database GUI, or tool) is repeatedly attempting connections with incorrect credentials via the exposed port 5432. These persistent failures pollute the DB logs, can mask real authentication issues, and consume connection resources.

**Evidence:** `docker logs docker-db-1` shows repeated entries:
```
2026-06-06 00:41:34.146 UTC [13883] FATAL:  password authentication failed for user "postgres"
2026-06-06 00:41:34.149 UTC [13884] FATAL:  password authentication failed for user "postgres"
...
```
Total count: 148 failures. The dev override exposes the DB port: `docker/docker-compose.override.yml` line 93: `ports: - "5432:5432"`.

**Recommendation:** Either:
1. Configure pg_hba.conf to rate-limit authentication failures (e.g., `auth_delay` extension).
2. Document the correct database connection parameters (host: localhost, port: 5432, user: mkobi_app, password: from MKOBI_APP_PASSWORD) in the development guide.
3. Verify that any local tools/IDEs use the correct application role credentials (`mkobi_app`) rather than the `postgres` superuser.

---

### INF-006: PostgreSQL enum introspection query uses pre-v10 column name

| Field | Value |
|-------|-------|
| **ID** | INF-006 |
| **Severity** | MEDIUM |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `test-db` container (PostgreSQL 16), unspecified introspection library |
| **Classification** | mandatory |

**Description:** The test database logs contain an ERROR indicating a query references `pg_enum.enum_typid`, which was the column name in PostgreSQL 9.x and earlier. Since PostgreSQL 10, the column was renamed to `pg_enum.enumtypid` (no underscore). The query `SELECT enum_typid::regtype AS enum_type, enumlabel FROM pg_enum ORDER BY enum_typid, enumsortorder` fails with "column 'enum_typid' does not exist". This suggests an outdated database introspection library (possibly SQLAlchemy or Alembic inspector) that hasn't been updated for PostgreSQL 10+.

**Evidence:** `docker logs test-db`:
```
2026-06-06 01:12:33.180 UTC [20864] ERROR:  column "enum_typid" does not exist at character 8
2026-06-06 01:12:33.180 UTC [20864] HINT:  Perhaps you meant to reference the column "pg_enum.enumtypid".
2026-06-06 01:12:33.180 UTC [20864] STATEMENT:  SELECT enum_typid::regtype AS enum_type, enumlabel FROM pg_enum ORDER BY enum_typid, enumsortorder
```

**Recommendation:** Identify which library/code is issuing this query. Update SQLAlchemy, Alembic, or any custom introspection code to a version compatible with PostgreSQL 10+. The `pg_enum.enumtypid` column name has been in use since PostgreSQL 10 (released 2017).

---

### INF-007: Development seeders fail with SQLAlchemy InvalidRequestError

| Field | Value |
|-------|-------|
| **ID** | INF-007 |
| **Severity** | MEDIUM |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/db/seeders/test_media_dash.py` (line 192), `src/mkobi/db/dev_seeders.py` (line 33), running `docker-app-1` container |
| **Classification** | mandatory |

**Description:** The development app container logs show 2 occurrences of `Development seeders failed` with a SQLAlchemy `InvalidRequestError: Can't operate on closed transaction inside context manager`. The error originates from `test_media_dash.py` line 192 calling `await db.refresh(dashboard)` on a dashboard object whose session transaction has already been closed. While the app still starts (seeders are non-fatal in dev), this is a code bug that will prevent test data from being seeded correctly.

**Evidence:** `docker logs docker-app-1`:
```json
{"timestamp": "2026-06-04 16:29:19", "level": "ERROR", "service": "mkobi", "message": "Development seeders failed: Failed to seed test_media_dash: Can't operate on closed transaction inside context manager.  Please complete the context manager before emitting further commands.", "module": "dev_seeders", "function": "run_dev_seeders"}
```
Traceback: `src/mkobi/db/seeders/test_media_dash.py:192` → `await db.refresh(dashboard)` → `sqlalchemy.exc.InvalidRequestError`.

**Recommendation:** Fix the transaction scoping in `test_media_dash.py`. The `db.refresh(dashboard)` call at line 192 is being made after the session's transaction context has been closed. Ensure the refresh happens within the same async context manager scope as the transaction, or restructure to avoid cross-session object references.

---

### INF-008: Unexpected EOF on client connections with open transactions in test database

| Field | Value |
|-------|-------|
| **ID** | INF-008 |
| **Severity** | LOW |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `test-db` container, test runner teardown |
| **Classification** | advisory |

**Description:** The test database logs show 4 occurrences of `unexpected EOF on client connection with an open transaction`. This indicates that test clients (likely pytest sessions) are disconnecting without properly committing or rolling back transactions. This can leave locks held temporarily and may cause flaky test behavior in parallel test scenarios.

**Evidence:** `docker logs test-db`:
```
2026-06-05 04:09:00.454 UTC [67496] LOG:  unexpected EOF on client connection with an open transaction
2026-06-05 07:28:42.337 UTC [86223] LOG:  unexpected EOF on client connection with an open transaction
2026-06-05 18:43:02.382 UTC [4994] LOG:  unexpected EOF on client connection with an open transaction
```

**Recommendation:** Review test teardown/fixture code to ensure database sessions are properly closed. Use `finally:` blocks or async context managers in test fixtures to guarantee transaction cleanup even on assertion failures or exceptions.

---

### INF-009: No rollback procedure documented for production deployments

| Field | Value |
|-------|-------|
| **ID** | INF-009 |
| **Severity** | LOW |
| **Type** | DOC-UPDATE |
| **Affected Modules** | `docs/10-deployment/deployment.md` |
| **Classification** | advisory |

**Description:** The deployment documentation covers how to deploy (build, start, run migrations) but does not document a rollback procedure. If a bad deployment is pushed (e.g., a migration that breaks the schema, or a code change that crashes), there is no documented path to revert. This includes: reverting to a previous image tag, rolling back Alembic migrations, and restoring database volumes from backup.

**Evidence:** `docs/10-deployment/deployment.md` — no match for "rollback" or "roll back" in the document. The migration section mentions `alembic upgrade head` but not `alembic downgrade` or restoration procedures.

**Recommendation:** Add a "Rollback Procedure" section to `docs/10-deployment/deployment.md` covering:
1. Reverting to a previous Docker image tag (`docker compose up -d --build` with a pinned image or git checkout).
2. Running `alembic downgrade` to the previous migration revision.
3. Restoring `postgres_data` volume from a pre-deployment backup.
4. Document the pre-deployment backup step as part of the standard deploy process.

---

### INF-010: Dockerfile base images use floating major-version tags

| Field | Value |
|-------|-------|
| **ID** | INF-010 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `docker/Dockerfile` (lines 10, 28, 64) |
| **Classification** | advisory |

**Description:** The Dockerfile uses floating major-version tags in FROM directives: `node:20-alpine` (line 10), `python:3.12-slim-bookworm` (lines 28, 64). While these are better than `latest`, they still float across minor versions (e.g., `python:3.12.4` → `python:3.12.5` on next pull). This can cause subtle build non-determinism: a dependency compiled against a specific C Python version may break on a minor Python update, or a Node.js security patch could change behavior. Docker's content-addressable layer cache mitigates this for cached builds, but fresh builds on a new host will pull different base images.

**Evidence:** `docker/Dockerfile` line 10: `FROM node:20-alpine AS frontend-builder`. Line 28: `FROM python:3.12-slim-bookworm AS base`. Line 64: `FROM python:3.12-slim-bookworm AS prod-base`.

**Recommendation:** Pin base images to specific versions for full reproducibility:
- `node:20.19.0-alpine3.21` (or current stable patch)
- `python:3.12.10-slim-bookworm` (or current stable patch)

Alternatively, use `docker-compose.yml` build args to make the base image version configurable while pinning defaults.

---

### INF-011: Test database and Redis ports exposed to host

| Field | Value |
|-------|-------|
| **ID** | INF-011 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `docker/docker-compose.test.yml` (test-db line 20, test-redis line 36) |
| **Classification** | advisory |

**Description:** The test compose file exposes `test-db` on host port 5433 and `test-redis` on host port 6380. While this is convenient for running pytest from the host and debugging with external tools, it places internal infrastructure services on the host network. Any host process can connect to the test database. In CI/CD environments or shared developer machines, this could lead to unintended cross-talk or data interference.

**Evidence:** `docker/docker-compose.test.yml` line 20: `ports: - "5433:5432"`. Line 36: `ports: - "6380:6379"`. Runtime verification confirms: `docker port test-db` → `5432/tcp -> 0.0.0.0:5433`, `docker port test-redis` → `6379/tcp -> 0.0.0.0:6380`.

**Recommendation:** For CI/CD environments, remove host port mappings and run all tests inside the Docker network (`docker compose exec test-app pytest`). Keep the port mappings only in a local-development variant of the test compose, or make them conditional via profiles.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 5 |
| LOW | 3 |

## Mandatory Fixes

- **INF-006**: PostgreSQL enum introspection query uses pre-v10 column name — code issuing `SELECT enum_typid` must be updated for PostgreSQL 10+ compatibility.
- **INF-007**: Development seeders fail with SQLAlchemy InvalidRequestError on closed transaction — transaction scoping bug in `test_media_dash.py:192`.

## Advisory Recommendations

- **INF-001**: Pin nginx image to a versioned tag (e.g., `nginx:1.27-alpine`).
- **INF-002**: Add resource limits (`mem_limit`, `cpus`) to all production services.
- **INF-003**: Set `AUTO_MIGRATE: "false"` in the app service of `docker-compose.yml` since the `migrate` service handles migrations.
- **INF-004**: Replace `pgrep -f rq` health check with a functional readiness check for the rq-worker.
- **INF-005**: Address persistent DB auth failures — configure external tools with correct app role credentials.
- **INF-008**: Review test teardown to properly close database transactions.
- **INF-009**: Add rollback procedure documentation to deployment guide.
- **INF-010**: Pin Dockerfile base images to specific patch versions for reproducibility.
- **INF-011**: Consider removing test DB/Redis port exposure to host for CI/CD environments.

## Doc Updates Needed

- **INF-009**: Add rollback procedure section to `docs/10-deployment/deployment.md`.

---
