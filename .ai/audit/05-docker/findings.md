---
name: audit-findings
description: Phase 05 Docker Infrastructure Audit Findings
agent: auditor
alwaysApply: false
---

# Phase 05 Audit Findings — Infrastructure & Runtime Environment

**Executor:** auditor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### INF-001: Production Docker Build Fails — Frontend Stage `tsc: not Found`

| Field | Value |
|-------|-------|
| **ID** | INF-001 |
| **Severity** | CRITICAL |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `docker/Dockerfile` (frontend-builder stage) |
| **Classification** | mandatory |

**Description:** The `frontend-builder` stage in `docker/Dockerfile` uses a BuildKit cache mount (`--mount=type=cache,target=/app/frontend/node_modules`) for `npm ci`. Cache mounts persist data across builds but do NOT write to the image layer. After `npm ci` completes, the `node_modules` directory in the image is empty. The subsequent `RUN npm run build` step fails with `sh: tsc: not found` because `node_modules/.bin/tsc` does not exist in the layer.

**Evidence:**
- Build output: `ERROR: process "/bin/sh -c npm run build" did not complete successfully: exit code: 127`
- Dockerfile line 18-19: `RUN --mount=type=cache,target=/app/frontend/node_modules \ npm ci`
- Dockerfile line 23: `RUN npm run build` (fails because `node_modules` is empty)
- The running `docker-app-1` container logs confirm: `WARNING: Static directory 'frontend/dist' not found or missing index.html. React SPA will not be served.`
- `docker exec docker-app-1 ls /app/frontend/dist/` → `ls: cannot access '/app/frontend/dist/': No such file or directory`

**Root Cause:** BuildKit cache mounts (`--mount=type=cache`) are designed to persist package manager caches (e.g., `/root/.npm`) across builds, not to install runtime dependencies into the image. Using `target=/app/frontend/node_modules` as the cache mount path means the actual installed `node_modules` is never written to the Docker image layer.

**Recommendation:** Either (a) remove the cache mount and use plain `npm ci` so `node_modules` is persisted in the layer, or (b) change the cache target to the npm cache directory (`/root/.npm`) and keep `node_modules` as a regular directory. The Dockerfile already copies `frontend/package*.json` first for layer caching, so the cache mount provides minimal benefit. Simplest fix: remove `--mount=type=cache,target=/app/frontend/node_modules` from line 18.

---

### INF-002: Nginx Healthcheck Fails — IPv6 `localhost` Not Bound

| Field | Value |
|-------|-------|
| **ID** | INF-002 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `docker/nginx/nginx.conf`, `docker/docker-compose.yml` (nginx service) |
| **Classification** | mandatory |

**Description:** The nginx container's healthcheck uses `wget --spider -q http://localhost/` which resolves `localhost` to IPv6 `[::1]`. However, the nginx configuration only binds to IPv4 (`listen 80;`), not dual-stack (`listen [::]:80;`). This causes the healthcheck to fail with "Connection refused" on every check, resulting in a permanent `unhealthy` status (458+ consecutive failures observed).

**Evidence:**
- `docker inspect docker-nginx-1` → `"Status":"unhealthy","FailingStreak":458`
- Healthcheck log: `wget: can't connect to remote host: Connection refused` (repeated every 30s)
- `docker exec docker-nginx-1 wget http://localhost/` → `Connecting to localhost ([::1]:80) ... Connection refused`
- `docker exec docker-nginx-1 wget http://127.0.0.1/` → succeeds (200 OK, 798 bytes)
- `ss -tlnp` inside nginx container shows: `tcp 0.0.0.0:80` (IPv4 only, no IPv6)
- nginx.conf line 14: `listen 80;` (IPv4-only by default in nginx 1.27)

**Recommendation:** Change `listen 80;` to `listen [::]:80;` in `docker/nginx/nginx.conf` to bind dual-stack. This is the standard approach for containers where `localhost` may resolve to either IPv4 or IPv6. The HTTPS server block template should also be updated.

---

### INF-003: `SecretsFileSource` Matches Non-Secret `_FILE` Environment Variables

| Field | Value |
|-------|-------|
| **ID** | INF-003 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/config.py` (SecretsFileSource class) |
| **Classification** | mandatory |

**Description:** The `SecretsFileSource.__call__()` method in `config.py` iterates ALL environment variables ending with `_FILE` and attempts to read them as secret files. The `docker-compose.override.yml` sets `LOGGING__LOG_FILE: ""` (empty string) to disable file logging in development. The `SecretsFileSource` matches `LOGGING__LOG_FILE`, gets an empty path, which resolves to `.` (current directory `/app`), and fails with `Is a directory` error. This produces warning noise on every application startup.

**Evidence:**
- App container logs: `Failed to read secret file .: [Errno 21] Is a directory: '.'` (appears twice on every startup)
- `docker exec docker-app-1 env | grep _FILE` → `LOGGING__LOG_FILE=`
- `config.py` line 66: `if env_var_name.endswith("_FILE"):` — matches `LOGGING__LOG_FILE`
- `config.py` line 69-70: `file_path_str = os.environ[env_var_name]` → empty string → `Path("")` → resolves to `.`
- `config.py` line 72: `if file_path.exists():` → `.` exists (it's the working directory)
- `config.py` line 74: `file_path.read_text()` → fails with `Is a directory`

**Recommendation:** Add a guard in `SecretsFileSource.__call__()` to skip empty values: `if not file_path_str.strip(): continue`. Additionally, consider checking `file_path.is_file()` instead of `file_path.exists()` to skip directories.

---

### INF-004: Development `.env` Contains Weak Credentials Without Production Enforcement

| Field | Value |
|-------|-------|
| **ID** | INF-004 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `.env`, `docker/docker-compose.yml` |
| **Classification** | advisory |

**Description:** The `.env` file (used for development) contains weak credentials: `DATABASE__PASSWORD=postgres`, `ADMIN_PASSWORD=admin@example.com`, `JWT__SECRET_KEY=dev-secret-key-for-security-testing-do-not-use-in-prod-32chars`. While the production compose file uses `${VAR:?error}` enforcement to refuse startup without explicit values, there is no mechanism preventing the `.env` file from being accidentally used with production compose commands (e.g., `docker compose -f docker/docker-compose.yml --env-file .env up -d` starts production services with dev credentials).

**Evidence:**
- `.env` line 10: `DATABASE__PASSWORD=postgres`
- `.env` line 19: `ADMIN_PASSWORD=admin@example.com`
- `.env` line 15: `JWT__SECRET_KEY=dev-secret-key-for-security-testing-do-not-use-in-prod-32chars`
- `docker-compose.yml` line 21: `POSTGRES_PASSWORD: ${DATABASE__PASSWORD:?DATABASE__PASSWORD is required}` — enforces variable presence but not strength
- Running `docker-app-1` container environment shows these weak values are active: `ADMIN_PASSWORD=admin@example.com`, `DATABASE__PASSWORD=dev-app-password`

**Recommendation:** The application already has `validate_admin_credentials()` for runtime weak-password detection. Consider adding a similar startup check that refuses to start with known-weak JWT secrets or database passwords when `ENV != development`. Alternatively, add a comment/warning banner in `.env` and ensure production deployment docs explicitly state to use a separate `.env.production` file.

---

### INF-005: Production Compose `rq-worker` Command Inconsistent Between Override and Base

| Field | Value |
|-------|-------|
| **ID** | INF-005 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `docker/docker-compose.yml`, `docker/docker-compose.override.yml` |
| **Classification** | advisory |

**Description:** The `rq-worker` service uses different command syntax between the production compose and the development override. The production compose uses `["uv", "run", "rq", "worker", "--url", "redis://redis:6379/0"]` while the development override uses `["/app/.venv/bin/rqworker", "--url", "redis://redis:6379/0"]`. The production command relies on `uv run` which requires the `uv` binary to be in PATH, while the override uses the direct vicon binary path. Both work, but the inconsistency suggests the production command was not tested end-to-end (the `uv run rq` form may behave differently with the `app` user's PATH).

**Evidence:**
- `docker-compose.yml` line 162: `command: ["uv", "run", "rq", "worker", "--url", "redis://redis:6379/0"]`
- `docker-compose.override.yml` line 106: `command: ["/app/.venv/bin/rqworker", "--url", "redis://redis:6379/0"]`
- The running `docker-rq-worker-1` container shows command `/app/.venv/bin/rqworker` (from override), not `uv run rq worker`

**Recommendation:** Standardize on the direct vicon binary path `/app/.venv/bin/rqworker` in both files for consistency and to avoid depending on `uv` being in the `app` user's PATH at runtime.

---

### INF-006: Database Port Exposed to Host in Production Compose Override

| Field | Value |
|-------|-------|
| **ID** | INF-006 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `docker/docker-compose.override.yml` (db service) |
| **Classification** | advisory |

**Description:** The development override exposes the PostgreSQL port to the host (`ports: - "5432:5432"`), which is expected for development. However, running `docker compose -f docker/docker-compose.yml --env-file .env up -d` (without the override) does NOT expose the port, which is correct for production. The issue is that the `docker-compose.yml` base file does not explicitly document that the db port should NOT be exposed in production, and there is no profile-based separation for the db port. If a developer accidentally runs the production compose with the override file, the database would be exposed.

**Evidence:**
- `docker-compose.override.yml` line 139-140: `ports: - "5432:5432"`
- `docker-compose.yml` base: no `ports` on db service
- Running `docker-db-1` shows: `0.0.0.0:5432->5432/tcp` (port is exposed because override is active)

**Recommendation:** This is acceptable for the current single-machine development setup. For production deployments, ensure the override file is not used. Consider adding a comment in the override file header: "WARNING: Do not use this override in production — exposes database port."

---

### INF-007: PostgreSQL Superuser Authentication Failures in Logs

| Field | Value |
|-------|-------|
| **ID** | INF-007 |
| **Severity** | LOW |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `docker/docker-compose.yml` (db service) |
| **Classification** | advisory |

**Description:** The production database container logs show repeated `FATAL: password authentication failed for user "postgres"` errors. These occur when the `migrate` or `app` services attempt to connect to the database before it is fully ready, or when stale connections from previously configured credentials attempt to authenticate. While the healthcheck eventually succeeds and the application connects correctly, these errors fill the logs and could mask real authentication issues.

**Evidence:**
- `docker logs docker-db-1` shows 30+ `FATAL: password authentication failed for user "postgres"` entries
- Timestamps show clusters at container startup (05:23:50) and after restarts (08:02:47)
- The database is currently healthy: `pg_isready` returns accepting connections

**Recommendation:** These are likely caused by the `migrate` service attempting connections before the database has completed initialization. The `depends_on: condition: service_healthy` should prevent this, but the healthcheck may pass before authentication is fully configured. Consider adding a brief `start_period` delay or using `pg_isready -U postgres -d bidb` to ensure the specific database is ready.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 1 |
| HIGH | 1 |
| MEDIUM | 2 |
| LOW | 3 |

## Mandatory Fixes

1. **INF-001** — Fix frontend-builder stage in Dockerfile (cache mount prevents `node_modules` from being written to image layer, causing production build failure)
2. **INF-002** — Fix nginx healthcheck IPv6 binding (add `listen [::]:80;` to nginx.conf)
3. **INF-003** — Fix `SecretsFileSource` to skip empty `_FILE` values (prevents false warnings from `LOGGING__LOG_FILE=""`)

## Advisory Recommendations

1. **INF-004** — Add production credential enforcement beyond variable presence checks
2. **INF-005** — Standardize `rq-worker` command syntax between compose files
3. **INF-006** — Document production port exposure risks in override file
4. **INF-007** — Investigate and reduce PostgreSQL authentication failure log noise

## Doc Updates Needed

- **INF-001**: Update `docs/11-guides/docker.md` "Frontend Build" section to document the cache mount behavior and the correct pattern for npm ci in multi-stage builds
- **INF-002**: Update `docs/10-deployment/deployment.md` nginx configuration to use dual-stack `listen [::]:80;`
- **INF-006**: Add warning comment in `docker-compose.override.yml` header about not using in production

---

## Runtime Verification Evidence

### Build Output
- **Test compose build**: SUCCESS — `docker-test-app` and `docker-test-migrate` built and exported successfully
- **Production compose build**: FAILED — `frontend-builder` stage fails with `sh: tsc: not found` (exit code 127)

### Container Status (at time of audit)
| Service | Status | Health |
|---------|--------|--------|
| docker-app-1 | running | null (disabled by override) |
| docker-db-1 | running | healthy |
| docker-redis-1 | running | healthy |
| docker-nginx-1 | running | **unhealthy** (458 failures) |
| docker-rq-worker-1 | running | N/A |
| test-db | running | healthy |
| test-redis | running | healthy |
| test-app | running | disabled |
| test-migrate | exited (0) | N/A |

### Connectivity Tests
- `test-app` → `test-db:5432`: TCP connection OK
- `test-app` → `test-redis:6379`: TCP connection OK
- `docker-app-1` → `localhost:8000/health`: HTTP 200, `{"status":"healthy","database":"connected"}`
- `docker-nginx-1` → `localhost/` (IPv6): Connection refused
- `docker-nginx-1` → `127.0.0.1/` (IPv4): HTTP 200

### Graceful Shutdown
- `test-redis`: Proper SIGTERM handling — saves RDB snapshot before exiting: `"Saving the final RDB snapshot before exiting"` → `"DB saved on disk"` → `"bye bye..."`
