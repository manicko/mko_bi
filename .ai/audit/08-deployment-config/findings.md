# Phase 08 Audit Findings — Configuration & Lifecycle

**Executor:** audit-executor
**Template:** C:\py_dev\mkobi\.ai\audit\templates\audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### DC-001: `.env` File Contains Committed Secrets (Weak Credentials)

| Field | Value |
|-------|-------|
| **ID** | DC-001 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `docker/.env`, `.env` |
| **Classification** | mandatory |

**Description:** Both `docker/.env` and `.env` at the project root contain real (albeit weak) credentials — `DATABASE__PASSWORD=1234`, `JWT__SECRET_KEY=dev-secret-key-for-local-development`, `MKOBI_APP_PASSWORD=dev_password`, `ADMIN_PASSWORD=admin@example.com`. Although `.gitignore` properly excludes `.env`, the files exist in the working tree and could be accidentally committed. The `.env.example` file correctly uses placeholder values like `change_me_in_production`, but the actual `.env` files contradict this safety pattern.

**Evidence:**
- `docker/.env` lines 7–8: `DATABASE__PASSWORD=1234`
- `.env` lines 7–8: `DATABASE__PASSWORD=1234`
- `.env` line 13: `JWT__SECRET_KEY=dev-secret-key-for-local-development`
- `.env` line 33: `MKOBI_APP_PASSWORD=dev_password`
- `.env` line 36: `ADMIN_PASSWORD=admin@example.com`
- `.gitignore` line 151: `.env` (properly ignored, but files exist in working tree)

**Recommendation:** Remove both `.env` files from the working tree entirely. Add them to `.gitignore` with a comment. Provide only `.env.example` with `change_me` placeholders. If developers need a local `.env`, they should create it from `.env.example` and never commit it. Consider adding a pre-commit hook that rejects commits containing files matching `.env` (not `.env.example`).

---

### DC-002: Production Default for `RATE_LIMITER_FAIL_CLOSED` Inconsistent Between Code and Docker Compose

| Field | Value |
|-------|-------|
| **ID** | DC-002 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/config.py`, `docker/docker-compose.yml` |
| **Classification** | advisory |

**Description:** The code-level default for `rate_limiter_fail_closed` is `False` (fail-open) in `config.py` line 283. However, `docker-compose.yml` line 102 sets `RATE_LIMITER_FAIL_CLOSED: ${RATE_LIMITER_FAIL_CLOSED:-true}`, defaulting to fail-closed in Docker deployments. This inconsistency means that running the application outside Docker (e.g., local development, bare-metal production) defaults to fail-open, which is less secure. The documentation (`security-checklist.md`, `security-overview.md`) states production should always use fail-closed.

**Evidence:**
- `src/mkobi/config.py` line 283: `rate_limiter_fail_closed: bool = Field(default=False, alias="RATE_LIMITER_FAIL_CLOSED")`
- `docker/docker-compose.yml` line 102: `RATE_LIMITER_FAIL_CLOSED: ${RATE_LIMITER_FAIL_CLOSED:-true}`
- `docs/08-security/security-overview.md` line 57: "Fail-closed — Production — prevents rate limit bypass during Redis outages"

**Recommendation:** Change the code-level default to `True` (fail-closed) in `config.py`. The `docker-compose.override.yml` can explicitly set it to `false` for development. This ensures fail-closed is the universal default, and developers must consciously opt into fail-open.

---

### DC-003: `DEBUG=false` in `.env` Files Despite `ENV=development`

| Field | Value |
|-------|-------|
| **ID** | DC-003 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `docker/.env`, `.env` |
| **Classification** | advisory |

**Description:** Both `.env` files set `ENV=development` but also set `DEBUG=false`. In a development environment, debug mode is expected to be enabled (for detailed error traces, auto-reload, etc.). The `docker-compose.override.yml` does not override `DEBUG`, so the development Docker deployment runs with debug disabled, which is counter-intuitive and reduces developer productivity.

**Evidence:**
- `docker/.env` line 25: `DEBUG=false`
- `.env` line 25: `DEBUG=false`
- `docker/docker-compose.override.yml`: No `DEBUG` override for the `app` service
- `src/mkobi/app.py` line 163: `docs_url=None if config.environment == EnvironmentEnum.PRODUCTION else "/docs"` — docs are enabled for non-production, but debug mode controls error detail

**Recommendation:** Set `DEBUG=true` in `docker-compose.override.yml` for the `app` service, or change the `.env` files to `DEBUG=true`. This aligns the development environment with developer expectations.

---

### DC-004: `ADMIN_PASSWORD` Defaults to `admin` in Code, Weak in `.env`

| Field | Value |
|-------|-------|
| **ID** | DC-004 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/config.py`, `docker/.env`, `.env` |
| **Classification** | advisory |

**Description:** The `Settings` class in `config.py` sets `admin_password` default to `"admin"` (line 248). While the production validator rejects weak passwords, the development environment uses `ADMIN_PASSWORD=admin@example.com` in `.env` files — which is in the `WEAK_PASSWORDS` set and would fail in production. The `docker-compose.override.yml` also defaults to `ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin@example.com}`. This creates a risk that developers may reuse the same weak password pattern when moving to production.

**Evidence:**
- `src/mkobi/config.py` line 248: `admin_password: str = Field(default="admin", alias="ADMIN_PASSWORD")`
- `src/mkobi/config.py` line 12: `WEAK_PASSWORDS = {"password", "123456", "admin", "secret", "test", "admin@example.com"}`
- `docker/.env` line 37: `ADMIN_PASSWORD=admin@example.com`
- `docker/docker-compose.override.yml` line 47: `ADMIN_PASSWORD: ${ADMIN_PASSWORD:-admin@example.com}`

**Recommendation:** Remove the weak default from `config.py` (make it `None` or empty string). In `docker-compose.override.yml`, use a clearly placeholder value like `change_me_admin_password`. This forces developers to consciously set a password and reduces the risk of weak credentials leaking to production.

---

### DC-005: `CORS_ORIGINS` Default in `docker-compose.yml` Allows `localhost:3000` in Production

| Field | Value |
|-------|-------|
| **ID** | DC-005 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `docker/docker-compose.yml` |
| **Classification** | advisory |

**Description:** The `docker-compose.yml` sets `CORS_ORIGINS: ${CORS_ORIGINS:-["http://localhost:3000"]}` for the `app` service. If `CORS_ORIGINS` is not explicitly set in the environment, the production deployment will default to allowing `http://localhost:3000` — a development origin. While the `app.py` `create_app()` function validates that CORS origins are set and not wildcard in production, it does not validate that the origins are appropriate for production (i.e., not localhost).

**Evidence:**
- `docker/docker-compose.yml` line 101: `CORS_ORIGINS: ${CORS_ORIGINS:-["http://localhost:3000"]}`
- `src/mkobi/app.py` lines 149–157: Validates CORS origins are non-empty and not wildcard in production, but does not check for localhost

**Recommendation:** Remove the default value from `docker-compose.yml` (make it required: `${CORS_ORIGINS:?CORS_ORIGINS is required}`). This forces production deployments to explicitly configure CORS origins, preventing accidental localhost exposure.

---

### DC-006: `rq-worker` Service Uses Production Profile but Override Removes It — Inconsistent Defaults

| Field | Value |
|-------|-------|
| **ID** | DC-006 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `docker/docker-compose.yml`, `docker/docker-compose.override.yml` |
| **Classification** | advisory |

**Description:** The `rq-worker` service in `docker-compose.yml` is gated behind `profiles: [production]`, meaning it won't start by default. The `docker-compose.override.yml` removes the profile (`profiles: []`) to enable it in development. However, the override does not set `AUTO_MIGRATE: "false"` for the worker, inheriting the production default of `"true"` from the base compose file. This could cause the worker to attempt migrations in development, conflicting with the dedicated `migrate` service.

**Evidence:**
- `docker/docker-compose.yml` line 138: `profiles: [production]` under `rq-worker`
- `docker/docker-compose.override.yml` line 62: `profiles: []` under `rq-worker`
- `docker/docker-compose.yml` line 136: `AUTO_MIGRATE: "false"` is set for `rq-worker` in production
- `docker/docker-compose.override.yml` line 64: No `AUTO_MIGRATE` override for `rq-worker` in development

**Recommendation:** Explicitly set `AUTO_MIGRATE: "false"` for `rq-worker` in `docker-compose.override.yml` to prevent migration conflicts in development.

---

### DC-007: `DATABASE__USER` Not Set in `docker-compose.yml` `app` Service Environment

| Field | Value |
|-------|-------|
| **ID** | DC-007 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `docker/docker-compose.yml` |
| **Classification** | advisory |

**Description:** The `app` service in `docker-compose.yml` sets `DATABASE__USER: mkobi_app` but the `migrate` service sets `DATABASE__USER: postgres`. This is intentional (least-privilege), but the `migrate` service does not explicitly document why it uses `postgres` instead of `mkobi_app`. A comment explains it, but the `DATABASE__USER` key is not present in the `migrate` service environment block — it relies on the default from `DatabaseSettings.user` which is `mkobi_app`. Wait — actually the `migrate` service sets `DATABASE__USER: postgres` explicitly. This is correct but could be confusing.

**Evidence:**
- `docker/docker-compose.yml` line 57: `DATABASE__USER: postgres` (migrate service)
- `docker/docker-compose.yml` line 85: `DATABASE__USER: mkobi_app` (app service)

**Recommendation:** No code change needed — the behavior is correct. However, add a comment near the `migrate` service's `DATABASE__USER: postgres` explaining that migrations require superuser privileges. (This is already partially done in the comment above, but could be more explicit.)

---

### DC-008: `test-app` Service Uses `tail -f /dev/null` Instead of Running Tests Automatically

| Field | Value |
|-------|-------|
| **ID** | DC-008 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `docker/docker-compose.test.yml` |
| **Classification** | advisory |

**Description:** The `test-app` service in `docker-compose.test.yml` uses `command: ["tail", "-f", "/dev/null"]` to keep the container running indefinitely. This is a common pattern for interactive test execution, but it means the test database is created and migrations are run even if no tests are executed. The `RECREATE_TEST_DB: "true"` setting means the test database is dropped and recreated every time the test container starts, which is wasteful if the container is just idling.

**Evidence:**
- `docker/docker-compose.test.yml` line 80: `command: ["tail", "-f", "/dev/null"]`
- `docker/docker-compose.test.yml` line 77: `RECREATE_TEST_DB: "true"`

**Recommendation:** Consider changing the command to run pytest directly (`["pytest", "tests/", "-v"]`) or making it configurable via an environment variable. Alternatively, document that users should run `docker compose -f docker/docker-compose.test.yml exec test-app uv run pytest tests/ -v` to execute tests.

---

### DC-009: `JWT__ACCESS_TOKEN_EXPIRE_MINUTES` Differs Between `.env` and `app.yaml`

| Field | Value |
|-------|-------|
| **ID** | DC-009 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `docker/.env`, `.env`, `src/mkobi/settings/app.yaml` |
| **Classification** | advisory |

**Description:** The `.env` files set `JWT__ACCESS_TOKEN_EXPIRE_MINUTES=30`, while `app.yaml` sets `access_token_expire_minutes: 15`. Since environment variables take priority over YAML, the effective value is 30 in most deployments. However, this inconsistency is confusing and could lead to unexpected behavior if the `.env` file is not loaded (e.g., in Docker where env vars are set directly).

**Evidence:**
- `docker/.env` line 14: `JWT__ACCESS_TOKEN_EXPIRE_MINUTES=30`
- `.env` line 14: `JWT__ACCESS_TOKEN_EXPIRE_MINUTES=30`
- `src/mkobi/settings/app.yaml` line 32: `access_token_expire_minutes: 15`

**Recommendation:** Align the values. Choose either 15 or 30 minutes and use it consistently across all configuration sources. Document the chosen value and its rationale.

---

### DC-010: `app.yaml` Contains `cors_origins` and `email` Settings Not Present in `Settings` Class

| Field | Value |
|-------|-------|
| **ID** | DC-010 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/settings/app.yaml`, `src/mkobi/config.py` |
| **Classification** | advisory |

**Description:** The `app.yaml` file contains `cors_origins`, `email`, and `dashboard` sections. While the `Settings` class does have corresponding fields (`cors_origins`, `email`, `dashboard`), the YAML file's `cors_origins` values (`http://localhost:3000`, `http://localhost:5173`) are development-only. If the YAML file is used in production (e.g., via Docker secrets or mounted config), these development origins would be used unless overridden by environment variables.

**Evidence:**
- `src/mkobi/settings/app.yaml` lines 62–64: `cors_origins: ["http://localhost:3000", "http://localhost:5173"]`
- `src/mkobi/config.py` line 243: `cors_origins: list[str] = []` (default is empty list)

**Recommendation:** Remove `cors_origins` from `app.yaml` entirely, leaving it as an environment-variable-only setting. This prevents accidental use of development CORS origins in production.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 3 |
| LOW | 6 |

## Mandatory Fixes

- **DC-001**: Remove `.env` files from working tree; ensure secrets are never committed.

## Advisory Recommendations

- **DC-002**: Change `rate_limiter_fail_closed` default to `True` in code.
- **DC-003**: Set `DEBUG=true` in development environment.
- **DC-004**: Remove weak default for `admin_password` in config.
- **DC-005**: Make `CORS_ORIGINS` required (no default) in `docker-compose.yml`.
- **DC-006**: Explicitly set `AUTO_MIGRATE: "false"` for `rq-worker` in override.
- **DC-007**: Add explicit comment for `DATABASE__USER: postgres` in migrate service.
- **DC-008**: Consider running pytest directly in `test-app` command.
- **DC-009**: Align `JWT__ACCESS_TOKEN_EXPIRE_MINUTES` across config sources.
- **DC-010**: Remove `cors_origins` from `app.yaml`.

## Doc Updates Needed

- **DC-007**: Document why `migrate` service uses `postgres` superuser.
- **DC-008**: Document test execution workflow for Docker test environment.
