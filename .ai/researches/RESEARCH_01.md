# 01 Standalone Test Compose - Research

**Researched:** 2026-05-24
**Domain:** Docker Compose — standalone test environment configuration
**Confidence:** HIGH

## Summary

This research covers the conversion of `docker-compose.test.yml` from an overlay file (merged on top of `docker-compose.yml`) into a fully standalone, independent compose configuration. The goal is zero shared state between dev and test environments — separate containers, volumes, and networks — runnable in parallel via `docker compose -f docker-compose.test.yml up -d`.

The standard Docker Compose pattern for this is a **base file + explicit `-f` invocation** (no merge). A standalone compose file defines ALL services, volumes, and networks it needs from scratch. Docker Compose v2 (current as of 2026) supports this natively — no `version:` key needed, no `extends`, no YAML anchors pointing to other files.

**Primary recommendation:** Build `docker-compose.test.yml` as a complete, self-contained Compose file with prefixed service names (`test-db`, `test-redis`, `test-migrate`, `test-app`), separate networks (`test_network`), separate volumes (`test_postgres_data`), and mapped host ports shifted by +1 from dev defaults (8001, 5433, 6380). Clean `docker-compose.yml` to remove any test artifacts. Use a dedicated `test-migrate` service (reusable one-shot pattern, same as production `migrate`), not inline migration logic in `test-app`.

## Standard Stack

### Core

| Component | Version | Purpose | Why Standard |
|-----------|---------|---------|--------------|
| Docker Compose | v2 (2026) | Multi-container orchestration | Industry standard, no `version:` key needed |
| PostgreSQL | 16 | Test database container | Same version as dev/prod; official image supports `/docker-entrypoint-initdb.d` |
| Redis | 7-alpine | Test cache/task queue | Lightweight; same version as production |
| Docker Engine | ≥24.0 | Container runtime | Restart policies, health checks, named volumes |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Standalone compose file | `docker compose --profile test` | Profiles don't solve port/volume conflicts; still shares services |
| Standalone compose file | `include:` directive | Include still merges into a parent file — not truly isolated |
| Standalone compose file | `COMPOSE_PROJECT_NAME` prefix | Good for CI but doesn't prevent merge-based override issues |
| Separate `test-migrate` service | Inline migration in test-app entrypoint | Tiny overhead, but maintains clean separation of concerns matching production pattern |

**No installation needed** — these are Docker Compose YAML patterns.

## Architecture Patterns

### Recommended Project Structure

```
mkobi/
├── docker-compose.yml              # Production base (clean, no test artifacts)
├── docker-compose.override.yml     # Dev overlay (auto-loaded, unchanged)
├── docker-compose.test.yml         # Standalone test config (THIS PHASE)
├── Dockerfile                      # Multi-stage: base, dev, test, prod
├── .env                            # Shared environment variables
├── docker/
│   └── init-scripts/
│       └── 01-create-app-role.sh   # App role setup (for dev; test uses admin URL)
└── alembic/                        # Migrations (shared)
```

### Pattern 1: Fully Standalone Compose File

**What:** A compose file that defines all services, networks, and volumes from scratch — no merge, no overlay, no `extends`.

**When to use:** When you need truly isolated environments running in parallel (dev + test on the same host).

**Example:**
```yaml
# docker-compose.test.yml — fully standalone, zero merge
services:
  test-db:
    image: postgres:16
    container_name: test-db
    environment:
      POSTGRES_DB: bidb_test
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DATABASE__PASSWORD:-test_password}
      MKOBI_APP_PASSWORD: ${MKOBI_APP_PASSWORD:-test_app_password}
    volumes:
      - test_postgres_data:/var/lib/postgresql/data
    ports:
      - "5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - test_network

  test-redis:
    image: redis:7-alpine
    container_name: test-redis
    volumes:
      - test_redis_data:/data
    ports:
      - "6380:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 3
    restart: unless-stopped
    networks:
      - test_network

  test-migrate:
    build:
      context: .
      dockerfile: Dockerfile
      target: test
    container_name: test-migrate
    command: ["alembic", "upgrade", "head"]
    environment:
      ENV: test
      DATABASE__HOST: test-db
      DATABASE__PORT: 5432
      DATABASE__USER: postgres
      DATABASE__PASSWORD: ${DATABASE__PASSWORD:-test_password}
      DATABASE__DBNAME: bidb_test
      DATABASE__TEST_DBNAME: bidb_test
      DATABASE__ADMIN_USER: postgres
      DATABASE__ADMIN_PASSWORD: ${DATABASE__PASSWORD:-test_password}
      JWT__SECRET_KEY: ${JWT__SECRET_KEY:-test_secret_key}
      JWT__ALGORITHM: HS256
    depends_on:
      test-db:
        condition: service_healthy
    restart: "no"
    networks:
      - test_network

  test-app:
    build:
      context: .
      dockerfile: Dockerfile
      target: test
    container_name: test-app
    environment:
      ENV: test
      DATABASE__HOST: test-db
      DATABASE__PORT: 5432
      DATABASE__USER: postgres
      DATABASE__PASSWORD: ${DATABASE__PASSWORD:-test_password}
      DATABASE__DBNAME: bidb_test
      DATABASE__TEST_DBNAME: bidb_test
      DATABASE__ADMIN_USER: postgres
      DATABASE__ADMIN_PASSWORD: ${DATABASE__PASSWORD:-test_password}
      JWT__SECRET_KEY: ${JWT__SECRET_KEY:-test_secret_key}
      JWT__ALGORITHM: HS256
      LOGGING__LEVEL: WARNING
      AUTO_MIGRATE: "true"
      RECREATE_TEST_DB: "true"
    ports:
      - "8001:8000"
    depends_on:
      test-migrate:
        condition: service_completed_successfully
      test-db:
        condition: service_healthy
    healthcheck:
      disable: true
    restart: unless-stopped
    networks:
      - test_network
    command: ["tail", "-f", "/dev/null"]

volumes:
  test_postgres_data:
  test_redis_data:

networks:
  test_network:
    driver: bridge
```

### Anti-Patterns to Avoid

- **Overlay merge pattern** (`docker compose -f base.yml -f test.yml`): This is what we're replacing — it causes shared networks, merged volumes, and service name collisions. Services from the base file bleed into the test environment.
- **Relying on `version:` key**: Obsolete in Docker Compose v2 (2026). Compose files use the open Compose Specification; the `version:` field is ignored if present.
- **YAML anchors for cross-file reuse**: Anchors/`<<:` only work within a single file. Don't try to reference anchors across compose files.
- **Static volume names without prefix in standalone files**: Use `test_postgres_data` not `postgres_data. When running in parallel, Docker won't auto-prefix volumes for standalone files run with `-f`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Port conflict avoidance | Custom port-allocator scripts | Explicit fixed port mapping in compose file | Fixed ports (8001/5433/6380) are deterministic and obvious |
| Database initialization | Custom init container | PostgreSQL `/docker-entrypoint-initdb.d` | Official image handles ordering, idempotency, and edge cases |
| Migration orchestration | Custom migration runner in app startup | Dedicated `test-migrate` service with `depends_on: service_completed_successfully` | Same pattern as production; one-shot job, clean separation |
| Network isolation | Manual `docker network create` | Compose-declared networks with `driver: bridge` | Compose manages lifecycle; auto-removed on `down` |
| Health check polling | Custom wait-for-it scripts | Native `healthcheck` + `depends_on: condition: service_healthy` | Built into Compose; race-condition-free |

**Key insight:** Docker Compose v2 already solves all the orchestration problems (health-gated dependencies, restart policies, network isolation, volume lifecycle). The job is to configure it declaratively, not to add procedural glue.

## Common Pitfalls

### Pitfall 1: Shared Networks Across `-f` Files

**What goes wrong:** When compose files are specified together (`-f base.yml -f test.yml`), services from both files are placed on a **shared default network**. Services can discover each other via DNS. A `test-db` service might accidentally connect to a `dev-db` database if DNS names collide or defaults are used.

**Why it happens:** Compose merges multiple `-f` files into a single project model. Networks are shared unless explicitly isolated with `external: true` or separate network names with different `name:` attributes — which still doesn't fully prevent DNS leakage.

**How to avoid:** Use only ONE compose file in the `-f` flag for the test environment. No merge means no shared network.

**Warning signs:** `docker network ls` shows a single network for both dev and test; services can resolve names from the other environment.

### Pitfall 2: Init Scripts Not Running on Named Volumes

**What goes wrong:** PostgreSQL initialization scripts in `/docker-entrypoint-initdb.d/` only execute when the data directory is **empty** (first container start with a fresh volume). If a named volume has been recreated or the data directory had files from a previous run, init scripts are silently skipped.

**Why it happens:** The official PostgreSQL image checks if `/var/lib/postgresql/data` is empty before running initialization. Named volumes persist across `docker compose down` cycles (only removed with `docker compose down -v`).

**How to avoid:** Test environment uses a dedicated `test_postgres_data` volume. The init script (`01-create-app-role.sh`) mounts into the test-db service. For the test environment, since `test-app` uses `postgres` superuser during migration (not `mkobi_app`), the init script is primarily needed for app role creation when tests run with `mkobi_app` user.

**Source:** [Docker PostgreSQL Init Docs](https://docs.docker.com/guides/postgresql/advanced-configuration-and-initialization/) (verified 2025)

**Warning signs:** "Role mkobi_app does not exist" error on test startup; permissions issues on test database objects.

### Pitfall 3: `restart: "no"` vs `restart: "unless-stopped"` Confusion

**What goes wrong:** The production `migrate` service uses `restart: "no"` (one-shot). If incorrectly set to `unless-stopped`, the migrate job would restart in an infinite loop after completing successfully, consuming resources and potentially causing migration table lock conflicts.

**Why it happens:** `restart: "no"` maps to `container.RestartPolicyDisabled` in the Docker Engine API. `restart: "unless-stopped"` (the default for service containers) tells the engine to restart the container whenever it exits.

**How to use correctly:**
- `test-migrate`: `restart: "no"` — runs once, completes, exits
- `test-db`: `restart: unless-stopped` — long-running stateful service
- `test-redis`: `restart: unless-stopped` — long-running stateful service
- `test-app`: `restart: unless-stopped` — or `no` if it should stay down after the `tail -f /dev/null` command exits

**Source:** Docker Compose internal `mapRestartPolicyCondition()` maps `"no"` → `RestartPolicyDisabled`, `"unless-stopped"` → `RestartPolicyUnlessStopped` (from [docker/compose source](https://github.com/docker/compose/blob/main/compose/pkg/compose/create.go))

**Warning signs:** `test-migrate` container restarting repeatedly; migration table (`alembic_version`) locked.

### Pitfall 4: Service Name vs Container Name

**What goes wrong:** In a standalone compose file, service names (used for DNS resolution within the Docker network) should differ from the current docker-compose.yml service names. If `docker-compose.yml` defines `db` and `docker-compose.test.yml` also defines `db`, running them "in parallel" with separate `-f` invocations works BUT they share a default network name (based on the directory/compose project), causing cross-traffic.

**Why it happens:** Docker Compose defaults the network name to `{project_name}_default` where `project_name` defaults to the directory name. Two separate `docker compose -f ... up` commands in the same directory get the same project name unless `COMPOSE_PROJECT_NAME` or `-p` is used.

**How to use correctly:**
- Prefix all service names with `test-`: `test-db`, `test-redis`, `test-app`, `test-migrate`
- Prefix volume names: `test_postgres_data`, `test_redis_data`
- Prefix/explicitly name the network: `test_network` with `name: test_network` or rely on the fact that separate `-f` invocations are isolated
- Use `container_name` explicitly to avoid any auto-naming collisions

**Warning signs:** `docker ps` shows duplicate container names; network conflicts in `docker network ls`.

### Pitfall 5: `test-app` Health Check in Test Environment

**What goes wrong:** The production `app` service has a healthcheck (`curl -f http://localhost:8000/health`). In the test environment, the container runs `tail -f /dev/null` (not the app server), so the healthcheck would fail and the container would be marked unhealthy, and with a restart policy of `unless-stopped`, it would restart continuously.

**Why it happens:** Health checks inherit from Dockerfile CMD or compose overrides. If not explicitly disabled, the healthcheck from the production config (in `docker-compose.yml`) would apply if merge was used.

**How to avoid:** Explicitly disable healthcheck in test-app: `healthcheck: disable: true`. This is already present in the current overlay and must be preserved in the standalone.

**Warning signs:** `test-app` container in restart loop; `docker ps` shows `unhealthy` status.

### Pitfall 6: `RECREATE_TEST_DB` Connection Privilege Issue

**What goes wrong:** The current codebase's `DatabaseStarter.recreate_test_database()` uses `DATABASE__ADMIN_USER` (postgres superuser) to drop/create the database. The init script `01-create-app-role.sh` grants `CREATEDB` to `mkobi_app`. However, if the test environment uses `mkobi_app` as `DATABASE__USER` (instead of `postgres`), the `DROP DATABASE` operation will fail because `mkobi_app` owns objects in the test database.

**Why it happens:** In the current overlay `docker-compose.test.yml`, `DATABASE__USER` is set to `mkobi_app`. When `RECREATE_TEST_DB=true`, the `DatabaseStarter.startup()` first connects as `mkobi_app`, checks the main database, and then attempts to recreate the test database. The `recreate_test_database()` method internally uses `DATABASE__ADMIN_USER` (postgres) for the drop/create, so this should work — but the initial `DATABASE__USER` check via `_check_db_connection()` connects to the main DB as `mkobi_app`.

**How to avoid:** In standalone test compose, use `postgres` as `DATABASE__USER` for the test-app service since it connects to `bidb_test`. The `mkobi_app` role doesn't need to exist in a freshly-created test database (migrations create all tables). After migrations, grant `mkobi_app` privileges if needed for runtime tests. Alternatively, set `DATABASE__USER: postgres` in the test compose for simplicity.

**Warning signs:** "must be owner of database bidb_test" error; `DROP DATABASE` permission denied.

## Code Examples

### docker-compose.yml Cleanup

Remove the test-related `RECREATE_TEST_DB` references and usage comment from the head:

**Before** (lines 1-8 and 93-94 in current `docker-compose.yml`):
```yaml
# ...
# Usage:
#   Production:  docker compose up -d
#   Development: docker compose -f docker-compose.yml -f docker-compose.override.yml up -d
#   Test:        docker compose -f docker-compose.yml -f docker-compose.test.yml up -d
# ...
# In app service:
      RECREATE_TEST_DB: "false"
# In rq-worker service:
      RECREATE_TEST_DB: "false"
```

**After** (cleaned):
```yaml
# =============================================================================
# Docker Compose for mkobi BI Dashboard System
# Production configuration with multi-stage Dockerfile support
# Usage:
#   Production:  docker compose up -d
#   Development: docker compose -f docker-compose.yml -f docker-compose.override.yml up -d
#   Test:        docker compose -f docker-compose.test.yml up -d
# =============================================================================
```
- Remove `RECREATE_TEST_DB: "false"` from both `app` and `rq-worker` services (these are production services; `RECREATE_TEST_DB` is test-only and should not appear in production config).
- Update the comment: test compose is standalone, not an overlay.

### Current App Role Init Script (for reference)

The existing `docker/init-scripts/01-create-app-role.sh` creates the `mkobi_app` role with limited privileges and `CREATEDB`. For the test environment, this script should be mounted into `test-db` so the role exists for migration and runtime operations.

Source: [`docker/init-scripts/01-create-app-role.sh`](/docker/init-scripts/01-create-app-role.sh)

### Standalone Test Compose — Minimal Migration Service Pattern

```yaml
  test-migrate:
    build:
      context: .
      dockerfile: Dockerfile
      target: test
    command: ["alembic", "upgrade", "head"]
    environment:
      ENV: test
      DATABASE__HOST: test-db
      DATABASE__PORT: 5432  # Internal port, always 5432
      DATABASE__USER: postgres
      DATABASE__PASSWORD: ${DATABASE__PASSWORD:-test_password}
      DATABASE__DBNAME: bidb_test
      DATABASE__TEST_DBNAME: bidb_test
      DATABASE__ADMIN_USER: postgres
      DATABASE__ADMIN_PASSWORD: ${DATABASE__PASSWORD:-test_password}
      JWT__SECRET_KEY: ${JWT__SECRET_KEY:-test_secret_key}
      JWT__ALGORITHM: HS256
    depends_on:
      test-db:
        condition: service_healthy
    restart: "no"
    networks:
      - test_network
```

Key points:
- Uses `target: test` (same as test-app)
- Connects to `test-db` via service name (Docker DNS) on internal port 5432
- `restart: "no"` — one-shot job, exits after migrations complete
- `depends_on: test-db: condition: service_healthy` — waits for DB to be ready

### Running Tests Against Standalone Compose

```bash
# Start the full test stack
docker compose -f docker-compose.test.yml up -d --build

# Wait for everything to be healthy
docker compose -f docker-compose.test.yml up -d --wait --wait-timeout 60

# Run tests inside the test-app container
docker compose -f docker-compose.test.yml exec test-app uv run pytest tests/ -v

# Tear down (keep volumes for faster next run)
docker compose -f docker-compose.test.yml down

# Tear down and remove volumes (clean slate)
docker compose -f docker-compose.test.yml down -v
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `docker-compose.yml -f docker-compose.test.yml` (overlay merge) | `docker-compose -f docker-compose.test.yml` (standalone) | This phase | Zero shared state, parallel execution |
| `version: '3.8'` in compose files | No `version:` key | Compose Spec 1.0 (2020+) | Cleaner files, vendor-neutral spec |
| `depends_on: - db` (no condition) | `depends_on: db: condition: service_healthy` | Compose v2.1+ (2021+) | Eliminates race conditions |
| `restart: always` | `restart: unless-stopped` | Docker Engine 1.12+ | Won't restart after explicit `docker stop` |
| `RECREATE_TEST_DB` in production compose | Removed from production compose | This phase | Production config stays clean |

**Deprecated/outdated:**
- `version:` top-level key in compose files — ignored by Compose v2, creates confusion
- Overlay merge pattern for test environments — causes shared networks, volume conflicts, and service name collisions
- `docker-compose` (hyphen) CLI — replaced by `docker compose` (space) in Compose V2

## Open Questions

1. **Should `test-app` use `postgres` or `mkobi_app` as `DATABASE__USER`?**
   - What we know: The current overlay uses `mkobi_app`. The `DatabaseStarter` uses `DATABASE__ADMIN_USER` (postgres) for `RECREATE_TEST_DB` operations. The init script creates `mkobi_app` with `CREATEDB`.
   - What's unclear: Whether the test environment needs `mkobi_app` at all, or if `postgres` is simpler for tests.
   - Recommendation: Use `postgres` for `DATABASE__USER` in test compose. Tests run with full privileges. The `mkobi_app` role is a production security concern, not a test concern. If tests specifically need to verify `mkobi_app` permissions, add a separate init script for `test-db`.

2. **Should `test-app` have `restart: "no"` or `restart: unless-stopped"`?**
   - What we know: The test container runs `tail -f /dev/null` to stay alive for `exec` commands.
   - What's unclear: If the container exits (e.g., OOM), should it auto-restart?
   - Recommendation: `restart: unless-stopped` — if the container crashes during a long test run, it auto-recovers. Use `"no"` only if you want explicit control.

3. **Does `test-redis` need to be included?**
   - What we know: The test `conftest.py` mocks Redis entirely (`MockRedis`). The `rq-worker` is excluded from test scope.
   - What's unclear: Whether any integration tests depend on a real Redis.
   - Recommendation: Include `test-redis` in the compose file for completeness (it's cheap), but tests should continue to mock it. If no tests use it, it can be removed later.

4. **Should the init script (`01-create-app-role.sh`) be mounted into `test-db`?**
   - What we know: The script creates `mkobi_app` role with `CONNECT` on `bidb` (not `bidb_test`). It grants privileges on the `public` schema.
   - What's unclear: Whether the script needs to be adapted for `bidb_test` or if it's even needed when using `postgres` user.
   - Recommendation: If using `postgres` as `DATABASE__USER`, the init script is not needed for `test-db`. If using `mkobi_app`, mount the init script and adapt it to grant on `bidb_test`.

## Sources

### Primary (HIGH confidence)
- Docker Compose internal source code (`compose/pkg/compose/create.go`) — restart policy mapping, health check observation
- Docker Compose internal source code (`compose/pkg/compose/convergence.go`) — health check behavior
- Project source: `docker-compose.yml`, `docker-compose.test.yml`, `docker-compose.override.yml`, `Dockerfile`, `.env.example`
- Project source: `src/mkobi/db/starter.py` — `DatabaseStarter` class, `recreate_test_database()` method
- Project source: `src/mkobi/app.py` — `lifespan()` startup flow, `DatabaseStarterConfig` construction
- Project source: `tests/conftest.py` — test database setup, `RECREATE_TEST_DB=true`, `setup_test_database` fixture
- Project source: `docker/init-scripts/01-create-app-role.sh` — app role creation script
- Project decisions: `.ai/problems/decisions/DECISION_01.md` — locked architecture decisions

### Secondary (MEDIUM confidence)
- [Docker Compose: Setting up a CI test environment (2026-04-13)](https://lours.me/posts/compose-tip-052-ci-test-environment/) — verified patterns for CI test compose, `--exit-code-from`, `--wait`, `--project-name`
- [Docker Compose for grown-ups (2026-01-05)](https://authorial.org/byern/docker-compose-for-grown-ups-a-lightweight-convention-set-that-prevents-chaos) — verified compose file structure conventions, `.env` handling, anti-patterns
- [Docker Compose: Powering the Full App Lifecycle (2025-07-07)](https://www.docker.com/blog/docker-compose-powering-the-full-app-lifecycle/) — verified compose as CI spine, health-gated dependencies
- [Scaling Beyond Shared Staging: Ephemeral Test Environments (2026-04-30)](https://www.desplega.ai/blog/deep-dive-ephemeral-environments-docker-compose) — verified `COMPOSE_PROJECT_NAME` isolation, parameterized ports, migrate service pattern
- [Docker Compose Multi-File Composition (2026-04-28)](https://medium.com/@FKosa/docker-compose-multi-file-composition-007fe8eb4b81) — verified `include` vs merge distinction, self-contained file requirements
- [Docker Compose Best Practices (2026-03-28)](https://simi.studio/en/posts/docker-compose-best-practices/) — verified no `version:` key, override patterns, `.env` discipline
- [Docker Compose v2 Tutorial 2026 (2026-05-12)](https://tutorials.technology/tutorials/docker-compose-v2-tutorial-2026.html) — verified compose v2 spec, top-level keys, profiles, health checks
- [Docker PostgreSQL Advanced Configuration](https://docs.docker.com/guides/postgresql/advanced-configuration-and-initialization/) — verified `/docker-entrypoint-initdb.d` behavior, init scripts only run on empty data directory

### Tertiary (LOW confidence)
- None — all findings verified against primary sources or official documentation.

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — Docker Compose v2 is stable; PostgreSQL 16 and Redis 7 are pinned versions; patterns verified against official docs and source code.
- Architecture: **HIGH** — Standalone compose pattern is well-documented; all service definitions derived from existing project code; port mapping and network isolation follow locked decisions.
- Pitfalls: **HIGH** — All pitfalls derived from actual project code analysis (starter.py, conftest.py, init scripts) and official Docker documentation. The `RECREATE_TEST_DB` privilege issue is directly traceable to the codebase.

**Research date:** 2026-05-24
**Valid until:** 2026-06-24 (30 days — Docker Compose v2 and PostgreSQL 16 are stable; no expected changes)
