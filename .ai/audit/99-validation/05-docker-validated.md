---
name: docker-findings-validated
description: Validation report for Phase 05 Docker Infrastructure Audit Findings
agent: validator
alwaysApply: false
---

# Phase 05 Docker Findings — Validation Report

**Source:** `.ai/audit/05-docker/findings.md`  
**Validated:** 2026-06-15

---

All audit findings validated. No rejections, merges, or conflicts.

---

## Actionable Recommendations

### INF-004: Development `.env` — Add Production Credential Guard

**Problem:** The `.env` file contains weak development credentials. Nothing prevents accidentally using it with the production compose file (`docker compose -f docker/docker-compose.yml --env-file .env up -d`), which would start production services with dev credentials. The existing `${VAR:?error}` enforcement only checks variable *presence*, not *strength*.

**Recommended Solution:** Add an explicit production startup guard in the application code that rejects known-weak credential values when `ENV=production`. This is the strongest approach because it is self-documenting, fails fast, and does not depend on operator discipline.

**Why this over alternatives:**
- A comment/warning banner in `.env` is passive and will be ignored by automation.
- A separate `.env.production` file is good practice but does not prevent misuse of `.env`.
- The application already has `validate_admin_credentials()` for admin credentials — extending this pattern to database passwords and JWT secrets is the minimal, consistent approach.

**Changes:**

**File: `src/mkobi/config.py`**

Add a `model_validator` to `Settings` that checks credential strength in production for database passwords and JWT secrets. The existing `WEAK_PASSWORDS` set and `JWTSettings.WEAK_SECRETS` set already define weak values — the validator reuses them:

```python
# Add to the Settings class, after validate_cors_origins_not_placeholder:

    @model_validator(mode="after")
    def validate_production_credentials(self) -> "Settings":
        """Reject known-weak credentials when running in production.

        Extends the existing validate_admin_credentials pattern to cover
        database passwords and JWT secrets. Fails fast on startup rather
        than allowing a production deployment with compromised credentials.
        """
        if self.environment == EnvironmentEnum.PRODUCTION:
            # Check database password against known-weak values
            db_password = self.database.password
            if db_password and db_password.lower() in {
                p.lower() for p in WEAK_PASSWORDS
            }:
                raise ValueError(
                    "DATABASE__PASSWORD is a known weak/placeholder value. "
                    "Set a strong password for production."
                )
            # Check JWT secret against known-weak values
            jwt_secret = self.jwt.secret_key
            if jwt_secret and jwt_secret.lower() in {
                s.lower() for s in JWTSettings.WEAK_SECRETS
            }:
                raise ValueError(
                    "JWT__SECRET_KEY is a known weak/placeholder value. "
                    "Generate a strong secret for production."
                )
        return self
```

**File: `.env`**

Add a prominent warning at the top of the file:

```env
# =============================================================================
# WARNING: This file contains DEVELOPMENT-ONLY credentials.
# DO NOT use this file with production compose commands.
# For production, create a separate .env.production with strong credentials.
# =============================================================================
```

**File: `docker/docker-compose.yml`**

Add a comment to the `db` service `POSTGRES_PASSWORD` line clarifying that the `${VAR:?}` check is presence-only:

```yaml
      # NOTE: ${VAR:?} enforces presence, not strength.
      # The application validates credential strength at startup when ENV=production.
      POSTGRES_PASSWORD: ${DATABASE__PASSWORD:?DATABASE__PASSWORD is required}
```

---

### INF-005: `rq-worker` Command — Standardize on Direct Binary Path

**Problem:** The production compose uses `["uv", "run", "rq", "worker", ...]` while the development override uses `["/app/.venv/bin/rqworker", ...]`. The `uv run` form depends on `uv` being in the `app` user's PATH at runtime, which is not guaranteed (the `prod-base` Dockerfile installs uv to `/root/.local/bin` but the container runs as `app` user).

**Recommended Solution:** Change the production compose to use the direct binary path `/app/.venv/bin/rqworker`, matching the development override.

**Why this over alternatives:**
- The direct binary path is more reliable: it does not depend on PATH resolution or `uv` being accessible at runtime.
- The development override already uses this form and it works.
- The `rqworker` binary is installed into `.venv` by `uv sync --frozen --no-dev` in the prod stage.
- Using `uv run` at runtime adds unnecessary overhead (uv's dependency resolution) for a command that is already installed.

**File: `docker/docker-compose.yml`**

Change line 162 from:

```yaml
    command: ["uv", "run", "rq", "worker", "--url", "redis://redis:6379/0"]
```

to:

```yaml
    command: ["/app/.venv/bin/rqworker", "--url", "redis://redis:6379/0"]
```

Also update the healthcheck `test` on lines 194-200 to use the direct path for consistency (the healthcheck also uses `uv run`):

```yaml
    healthcheck:
      test:
        - "CMD"
        - "/app/.venv/bin/python"
        - "-c"
        - "from redis import Redis; r = Redis(host='redis', port=6379, db=0); r.ping()"
```

---

### INF-006: Database Port Exposure — Add Warning Comment and Document Risk

**Problem:** The development override exposes PostgreSQL port 5432 to the host. If a developer accidentally runs the production compose with the override file, the database is exposed to the network. The current setup relies on operator awareness.

**Recommended Solution:** Add a prominent warning comment at the top of the override file and bind the development database port to `127.0.0.1` instead of `0.0.0.0` to limit exposure to the local machine.

**Why this over alternatives:**
- Removing the port entirely would break the documented development workflow (GUI tools, direct `psql` access).
- A comment alone is passive but is the minimum required; binding to `127.0.0.1` is an active defense.
- Binding to `127.0.0.1` instead of `0.0.0.0` means even if the override is accidentally used, the database is only accessible from the host machine, not the network.

**File: `docker/docker-compose.override.yml`**

Change the header comment (lines 1-4) from:

```yaml
# =============================================================================
# Docker Compose Override for Development
# Usage: docker compose -f docker/docker-compose.yml -f docker/docker-compose.override.yml up -d
# =============================================================================
```

to:

```yaml
# =============================================================================
# Docker Compose Override for Development
# Usage: docker compose -f docker/docker-compose.yml -f docker/docker-compose.override.yml up -d
#
# WARNING: Do NOT use this override in production.
# This file exposes the database port (5432) to the host machine.
# Running production compose with this override exposes the database to the network.
# =============================================================================
```

Change the db port binding (lines 139-140) from:

```yaml
    ports:
      - "5432:5432"
```

to:

```yaml
    ports:
      # Bound to 127.0.0.1 to limit exposure to local machine only.
      # Do not change to 0.0.0.0 — that would expose the database to the network.
      - "127.0.0.1:5432:5432"
```

---

### INF-007: PostgreSQL Auth Failures — Fix Healthcheck and Add `start_period`

**Problem:** The database healthcheck uses `pg_isready -U postgres` without specifying the database name. When `pg_isready` connects without `-d`, PostgreSQL defaults the database name to the username (`postgres`). This works, but during initialization the `postgres` database may not be ready yet, causing authentication failures that fill the logs. Additionally, the healthcheck has no `start_period`, so failures during the initial PostgreSQL startup count toward the retry limit.

**Recommended Solution:** Add `-d bidb` to the healthcheck command and add a `start_period` of 10 seconds. Apply this to all three compose files.

**Why this over alternatives:**
- Adding `-d bidb` ensures the healthcheck verifies the actual application database is ready, not just that the PostgreSQL process is listening. This eliminates the auth failures caused by connecting to a database that isn't ready yet.
- Adding `start_period: 10s` gives PostgreSQL time to complete initialization before failures count. This is the documented best practice (Docker docs, multiple 2025-2026 sources recommend 10-60s for databases).
- Using `pg_isready -U postgres -d bidb` is more accurate than the current `pg_isready -U postgres` because it checks the specific database the application uses.
- This is simpler and more reliable than adding a separate `start_period` delay script.

**File: `docker/docker-compose.yml`** — db service healthcheck (line 32-36):

Change from:

```yaml
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
```

to:

```yaml
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d bidb"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s
```

**File: `docker/docker-compose.test.yml`** — test-db service healthcheck (line 43-47):

Change from:

```yaml
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
```

to:

```yaml
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d bidb_test"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s
```