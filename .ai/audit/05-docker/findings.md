# Phase 05 Audit Findings — Infrastructure & Runtime Environment

**Executor:** audit-executor
**Template:** .kilo/commands/audit/phases/05-audit-docker.md
**Status:** complete
**Validated:** no

---

## Findings

### INF-01: Base Images Use Floating Tags (Not Pinned to Digest)

| Field | Value |
|-------|-------|
| **ID** | INF-01 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | docker/Dockerfile |
| **Classification** | advisory |

**Description:** The Dockerfile uses floating tags for base images: `python:3.12-slim-bookworm` (lines 28, 63) and `node:20-alpine` (line 10). These tags are mutable — Docker can push a new image under the same tag. This means builds are not fully reproducible: rebuilding the same Dockerfile at different times may pull different base images, introducing unexpected changes or vulnerabilities.

**Evidence:**
- `docker/Dockerfile` line 10: `FROM node:20-alpine AS frontend-builder`
- `docker/Dockerfile` line 28: `FROM python:3.12-slim-bookworm AS base`
- `docker/Dockerfile` line 63: `FROM python:3.12-slim-bookworm AS prod-base`

**Recommendation:** Pin base images to their SHA256 digest (e.g., `python:3.12-slim-bookworm@sha256:93ab4b7fa528b...`). Digests can be obtained from `docker pull` output or Dockerfile `FROM` resolution. Update digests deliberately via dependency update tooling (Dependabot, Renovate).

---

### INF-02: Development `.env` File with Weak Credentials Used by Default in Docker Compose

| Field | Value |
|-------|-------|
| **ID** | INF-02 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | docker/docker-compose.yml, .env, docker/.env, docker/docker-compose.override.yml |
| **Classification** | mandatory |

**Description:** The `.env` file in the project root contains weak default credentials (`DATABASE__PASSWORD=1234`, `JWT__SECRET_KEY=dev-secret-key-for-local-development`, `ADMIN_PASSWORD=admin@example.com`). This file is referenced via `--env-file .env` in all Docker Compose commands. While the production compose uses `${VAR:?error}` enforcement patterns, the `.env` satisfies them with development values. The `ENV` variable in `.env` is explicitly set to `development` (line 5), which overrides the production compose's `${ENV:-production}` default (docker-compose.yml line 47). This means running `docker compose -f docker/docker-compose.yml up -d` with the default `.env` starts the stack in `development` mode inside a `prod`-targeted container, with `LOGGING__LEVEL: DEBUG` possible in the override, insecure JWT secrets, and `COOKIE_SECURE=false`.

**Evidence:**
- `.env` line 5: `ENV=development`
- `.env` line 11: `DATABASE__PASSWORD=1234`
- `.env` line 19: `JWT__SECRET_KEY=dev-secret-key-for-local-development`
- `.env` line 49: `ADMIN_PASSWORD=admin@example.com`
- `docker-compose.yml` line 47: `ENV: ${ENV:-production}` — defaults to `production` only if `ENV` is unset, but `.env` provides `development`.
- `docker-compose.override.yml` line 65: `LOGGING__LEVEL: DEBUG`
- Runtime verification: `docker exec docker-app-1 sh -c 'echo $ENV'` returned `development`.

**Recommendation:** Remove or rename the default `.env` so production compose cannot accidentally load development credentials. Use a `.env.production` template with `${VAR:?error}` enforcement and no defaults for production deployments. Ensure production deployments explicitly set `ENV=production`, strong `DATABASE__PASSWORD`, strong `JWT__SECRET_KEY`, and strong `ADMIN_PASSWORD`.

---

### INF-03: No Health Checks on `rq-worker` and `nginx` Services

| Field | Value |
|-------|-------|
| **ID** | INF-03 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | docker/docker-compose.yml |
| **Classification** | advisory |

**Description:** The `rq-worker` service (line 128) and the `nginx` service (line 170) have no `healthcheck` definition. Docker cannot determine if these services are functionally healthy. If the rq-worker crashes or nginx fails to reload, Docker will continue reporting the container as `running` without detecting the failure. This affects monitoring, orchestration (auto-restart policies), and deployment safety.

**Evidence:**
- `docker/docker-compose.yml` lines 128-164 (`rq-worker`): no `healthcheck:` block present.
- `docker/docker-compose.yml` lines 170-181 (`nginx`): no `healthcheck:` block present.
- All other services (`db`, `app`, `redis`) have properly configured health checks.

**Recommendation:** Add health checks:
- For `rq-worker`: Use `uv run rq info --url redis://redis:6379/0` to verify the worker is connected to Redis.
- For `nginx`: Use `curl -f http://localhost:80/health || exit 1` or `nginx -t` for config test.

---

### INF-04: Redundant Migration Execution — AUTO_MIGRATE=true Combined with Dedicated Migrate Service

| Field | Value |
|-------|-------|
| **ID** | INF-04 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | docker/docker-compose.yml |
| **Classification** | advisory |

**Description:** The `docker-compose.yml` defines a dedicated `migrate` service (line 40) that runs `alembic upgrade head` before the app starts (`depends_on: migrate: condition: service_completed_successfully`). However, the `app` service also sets `AUTO_MIGRATE: "true"` (line 100), which causes the app to run migrations again on startup — once per worker (4 times in production with `--workers 4`). While the app uses a PostgreSQL advisory lock to prevent concurrent migration corruption, this wastes time, bloats logs, and indicates a configuration inconsistency. The purpose of the dedicated `migrate` service is to separate migration concerns; enabling `AUTO_MIGRATE` in the app defeats that separation.

**Evidence:**
- `docker/docker-compose.yml` line 100: `AUTO_MIGRATE: "true"`
- `docker/docker-compose.yml` line 40-65: dedicated `migrate` service with `restart: "no"`
- Runtime logs show: `"Running migrations for postgresql+asyncpg://mkobi_app:***@db:5432/bidb..."` logged 4 times (once per uvicorn worker) at app startup.
- `docker-compose.yml` line 100 (`AUTO_MIGRATE: "true"`) is set while `docs/10-deployment/deployment.md` line 194 describes setting `AUTO_MIGRATE=false` when using the migration job pattern.

**Recommendation:** Set `AUTO_MIGRATE: "false"` in the `app` service environment in `docker-compose.yml` when using the dedicated `migrate` service pattern. Since the `migrate` service already has `restart: "no"` and `condition: service_completed_successfully` dependency, the app service does not need to run migrations again.

---

### INF-05: Redis Runs Without Configuration File or Authentication

| Field | Value |
|-------|-------|
| **ID** | INF-05 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | docker/docker-compose.yml |
| **Classification** | advisory |

**Description:** The Redis service uses the default configuration with no custom `redis.conf`, no authentication (`requirepass`), and no command disabling (e.g., `FLUSHALL`, `CONFIG`). The container log confirms: `Warning: no config file specified, using the default config`. Any service on the `docker_default` network (or any compromised container) can execute arbitrary Redis commands, including flushing all data. Since Redis stores task queue data for the RQ worker, this is a data integrity risk in multi-tenant or compromised environments.

**Evidence:**
- `docker/docker-compose.yml` lines 117-125: `redis` service has no `command:` or `volumes:` entry mounting a config file.
- Container log: `Warning: no config file specified, using the default config. In order to specify a config file use redis-server /path/to/redis.conf`
- Redis port 6379 is accessible to all services on the `docker_default` network.

**Recommendation:** Provide a custom `redis.conf` with `requirepass`, rename dangerous commands (`FLUSHALL`, `CONFIG`), and mount it via `volumes:` in the compose file. Set the password via an environment variable or Docker secret.

---

### INF-06: PostgreSQL Uses `trust` Authentication for Local Connections

| Field | Value |
|-------|-------|
| **ID** | INF-06 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | docker/docker-compose.yml |
| **Classification** | advisory |

**Description:** PostgreSQL is initialized with `trust` authentication for all local connections (Unix socket, localhost IPv4/IPv6). While network connections use `scram-sha-256`, any process inside the `db` container can connect as `postgres` superuser without a password. The initialization message `initdb: warning: enabling "trust" authentication for local connections` confirms this. This is the default PostgreSQL behavior, but in a container context where only the database process should be running, it is a defense-in-depth gap.

**Evidence:**
- Container log: `initdb: warning: enabling "trust" authentication for local connections`
- `pg_hba.conf` analysis:
  ```
  local   all             all                                     trust
  host    all             all             127.0.0.1/32            trust
  host    all             all             ::1/128                 trust
  host    all             all             all                     scram-sha-256
  ```

**Recommendation:** For container deployments, the `trust` local connections are generally acceptable since only the postgres process runs in the container. However, for defense-in-depth, explicitly set `POSTGRES_HOST_AUTH_METHOD=scram-sha-256` or configure `pg_hba.conf` to use `scram-sha-256` for all connections. This is advisory since the risk is limited in single-process containers.

---

### INF-07: Production Image Is 706MB — Large Due to Heavy Python Dependencies

| Field | Value |
|-------|-------|
| **ID** | INF-07 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | docker/Dockerfile |
| **Classification** | advisory |

**Description:** The production application image (`docker-app`) is 706MB. This is relatively large for a Python FastAPI application. The large size is primarily due to heavy Python dependencies: `polars-runtime-32` (53MB download), `plotly` (9MB), and their transitive dependencies. The multi-stage build works correctly — no `node_modules` leaked into the final image, no build tools in the `prod-base` stage (`gcc`, `g++`, `make` are absent), and `pytest` is not installed in production. However, the image could be further optimized.

**Evidence:**
- `docker images` output: `docker-app:latest 706MB`, `docker-migrate:latest 706MB`
- Build output: `Downloading polars-runtime-32 (53.6MiB)`, `Downloading plotly (9.4MiB)`
- Verified no `node_modules` in final image: `docker exec docker-app-1 find / -name node_modules -type d` returned no results under `/app`.
- Verified no build tools: `docker exec docker-app-1 sh -c "which gcc g++ make 2>&1"` returned empty.
- Verified no pytest: `docker exec docker-app-1 sh -c "which pytest 2>&1"` returned empty.

**Recommendation:** Evaluate whether `plotly` (a frontend visualization library) needs to be a backend dependency at all — if it's only used for server-side chart generation, keep it; otherwise, move it to frontend-only dependencies. Consider using `python:3.12-alpine` as the production base to save ~40-50MB, though this introduces musl libc compatibility risks.

---

### INF-08: Production `docker-compose.yml` Lacks Explicit Network Configuration

| Field | Value |
|-------|-------|
| **ID** | INF-08 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | docker/docker-compose.yml |
| **Classification** | advisory |

**Description:** The production `docker-compose.yml` does not define explicit networks. Docker Compose automatically creates a `default` network, but there is no custom network definition, driver configuration, or subnet control. The `docker-compose.test.yml` does define an explicit `test_network` with `driver: bridge`, showing the pattern exists but was not applied to the production compose. Explicit network configuration improves isolation and makes service-to-service communication boundaries clear.

**Evidence:**
- `docker/docker-compose.yml` (full file): No `networks:` top-level key.
- `docker/docker-compose.test.yml` lines 122-124:
  ```yaml
  networks:
    test_network:
      driver: bridge
  ```
- `docker inspect docker_default` shows a `172.22.0.0/16` subnet — auto-assigned by Docker Compose with no explicit configuration.

**Recommendation:** Add explicit network configuration to the production `docker-compose.yml`:
```yaml
networks:
  backend:
    driver: bridge
    name: mkobi_backend
```
Assign all services to this network. Optionally add a separate `frontend` network for nginx-to-app communication only.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 4 |
| LOW | 3 |

## Mandatory Fixes

- **INF-02**: Development `.env` file with weak credentials used by default — ensure production deployments cannot accidentally load development credentials and that `ENV=production` is explicitly set.

## Advisory Recommendations

- **INF-01**: Pin base images to SHA256 digests for reproducible builds.
- **INF-03**: Add health checks for `rq-worker` and `nginx` services.
- **INF-04**: Set `AUTO_MIGRATE: "false"` when using the dedicated `migrate` service pattern.
- **INF-05**: Configure Redis with authentication and a custom `redis.conf`.
- **INF-06**: Strengthen PostgreSQL authentication for defense-in-depth (advisory for containers).
- **INF-07**: Optimize production image size (evaluate `plotly` as backend dependency, consider Alpine base).
- **INF-08**: Add explicit network configuration to production compose.

## Doc Updates Needed

None — no findings classified as DOC-UPDATE type.
