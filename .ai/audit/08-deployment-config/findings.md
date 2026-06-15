# Phase 08 Audit Findings — Configuration & Lifecycle

**Executor:** auditor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### DC-001: Nginx `X-Frame-Options` Conflicts with Application-Level `DENY`

| Field | Value |
|-------|-------|
| **ID** | DC-001 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `docker/nginx/nginx.conf`, `src/mkobi/app.py` |
| **Classification** | mandatory |

**Description:** The application's `SecurityHeadersMiddleware` sets `X-Frame-Options: DENY` (line 70 of `app.py`), which completely disallows iframe embedding. However, the Nginx reverse proxy sets `X-Frame-Options: SAMEORIGIN` (line 21 of `nginx.conf`). Since Nginx sits in front of the application in production profile deployments, the Nginx header value is what external clients actually receive. This creates two problems: (1) the documented security intent (`DENY`) is silently overridden by Nginx's weaker `SAMEORIGIN`, and (2) the Dash migration path (Strategy 1 — iframe fallback, documented in `docs/10-deployment/deployment.md` lines 384-394) will fail because `SAMEORIGIN` only allows iframes from the same origin, not from a different Dash server.

**Evidence:**
- `src/mkobi/app.py:70` — `response.headers["X-Frame-Options"] = "DENY"`
- `docker/nginx/nginx.conf:21` — `add_header X-Frame-Options "SAMEORIGIN" always;`
- `docs/10-deployment/deployment.md:384-394` — Dash iframe fallback strategy documented

**Recommendation:** Align Nginx with the application's security intent. Change Nginx to `DENY` if iframe embedding is not needed, or remove the `X-Frame-Options` from Nginx entirely and let the application middleware handle it (simpler, single source of truth). If the Dash iframe migration path is still active, use `SAMEORIGIN` intentionally in both places and document the deviation from `DENY`. Effort: trivial.

---

### DC-002: Nginx Does Not Proxy `/health/detailed` Endpoint

| Field | Value |
|-------|-------|
| **ID** | DC-002 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `docker/nginx/nginx.conf`, `src/mkobi/app.py` |
| **Classification** | advisory |

**Description:** The application exposes a `/health/detailed` endpoint (lines 271-309 of `app.py`) that returns component-level health status including database connectivity and static file availability. However, the Nginx configuration only proxies `/health` and `/api` — requests to `/health/detailed` will hit the Nginx `location /` block and return the React SPA `index.html` instead of the health check JSON. This means monitoring systems and admin dashboards that rely on `/health/detailed` will receive HTML instead of the expected JSON when Nginx is deployed in front.

**Evidence:**
- `src/mkobi/app.py:271-309` — `/health/detailed` endpoint implementation
- `docker/nginx/nginx.conf:42-46` — Only `/health` is proxied, not `/health/detailed`
- `docs/05-health/health-api.md:70-130` — `/health/detailed` documented as a public monitoring endpoint

**Recommendation:** Add a `location /health/detailed` block in `nginx.conf` that proxies to `http://app:8000`, similar to the existing `/health` block. Alternatively, combine both under a single `location /health` with a wildcard or regex. Effort: trivial.

---

### DC-003: `RATE_LIMITER_FAIL_CLOSED` Default Differs Between Code and Documentation

| Field | Value |
|-------|-------|
| **ID** | DC-003 |
| **Severity** | MEDIUM |
| **Type** | DOC-UPDATE |
| **Affected Modules** | `src/mkobi/config.py`, `docs/08-security/security-overview.md`, `docker/.env.production` |
| **Classification** | advisory |

**Description:** The code default for `RATE_LIMITER_FAIL_CLOSED` is `True` (line 362 of `config.py`: `rate_limiter_fail_closed: bool = Field(default=True, ...)`), meaning the rate limiter fails closed (rejects requests when Redis is down) by default. However, the security documentation at `docs/08-security/security-overview.md` lines 58-61 explicitly states: "**Fail-open** (default) `RATE_LIMITER_FAIL_CLOSED=false` — Requests are allowed through when Redis is down". The production env template (`docker/.env.production` line 38) sets `RATE_LIMITER_FAIL_CLOSED=true`, which is correct for production but contradicts the documented "default" behavior. This inconsistency means developers reading the docs may incorrectly assume fail-open is the default and not set the variable in production, when in fact the code already defaults to fail-closed.

**Evidence:**
- `src/mkobi/config.py:362` — `rate_limiter_fail_closed: bool = Field(default=True, ...)`
- `docs/08-security/security-overview.md:58-61` — Documents `false` as default
- `docker/.env.production:38` — `RATE_LIMITER_FAIL_CLOSED=true`

**Recommendation:** Update `docs/08-security/security-overview.md` to reflect that the code default is `true` (fail-closed), and that `false` (fail-open) must be explicitly set for development/availability-first deployments. The production env template is correct and should remain as-is. Effort: trivial (doc update only).

---

### DC-004: Development `.env` Contains Weak Passwords Without Warning; Override File Silently Relaxes Security

| Field | Value |
|-------|-------|
| **ID** | DC-004 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `.env`, `docker/docker-compose.override.yml`, `src/mkobi/config.py` |
| **Classification** | advisory |

**Description:** The development `.env` file (the one actually used, at project root) contains `DATABASE__PASSWORD=postgres`, `ADMIN_PASSWORD=admin@example.com`, and `MKOBI_APP_PASSWORD=dev-app-password` — all of which are in the `WEAK_PASSWORDS` blocklist in `config.py` (lines 19-31). While the `validate_admin_credentials` model validator only enforces these checks in production mode, the development environment silently accepts these weak credentials without any startup warning. The `docker-compose.override.yml` further relaxes security by setting `APP__COOKIE_SECURE=false` (line 63) and `LOGGING__LEVEL=DEBUG` (line 78). While this is intentional for development convenience, there is no guard preventing accidental use of the development `.env` in a production-like setting (e.g., if someone sets `ENV=production` in the root `.env` without changing passwords). The app would start in production with weak credentials because the `DATABASE__PASSWORD` placeholder check only runs against the `WEAK_PASSWORDS` set at the `DATABASE_URL` property level (lines 569-574 of `config.py`), but `admin@example.com` as admin password is in `WEAK_PASSWORDS` and would be caught — however, `postgres` as a database password IS in `WEAK_PASSWORDS` and would be caught. The real risk is that a developer could add a new weak password to `.env` that isn't in the blocklist.

**Evidence:**
- `.env:10-25` — Development credentials with weak passwords
- `src/mkobi/config.py:19-31` — `WEAK_PASSWORDS` set
- `src/mkobi/config.py:386-416` — `validate_admin_credentials` only enforces in production
- `docker/docker-compose.override.yml:63` — `APP__COOKIE_SECURE=false`

**Recommendation:** Add a startup warning in development mode when weak/default credentials are detected (similar to the existing warnings for default admin username/password at lines 403-415 of `config.py`, but extended to cover database password and `MKOBI_APP_PASSWORD`). This would alert developers without blocking startup. Effort: small.

---

### DC-005: `docker-compose.override.yml` Uses `rqworker` Command Instead of `rq worker`

| Field | Value |
|-------|-------|
| **ID** | DC-005 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `docker/docker-compose.override.yml`, `docker/docker-compose.yml` |
| **Classification** | mandatory |

**Description:** In `docker-compose.override.yml` line 106, the rq-worker command is `["/app/.venv/bin/rqworker", "--url", "redis://redis:6379/0"]` — using `rqworker` (no space). In the production compose file (`docker-compose.yml` line 162), the command is `["uv", "run", "rq", "worker", "--url", "redis://redis:6379/0"]` — using `rq worker` (with space). The RQ package provides the `rqworker` CLI entry point, so both forms should work. However, the override file uses the direct path `/app/.venv/bin/rqworker` while the production file uses `uv run rq worker`. This inconsistency means the development rq-worker may behave differently from production, and if `rqworker` binary is not present at that exact path (e.g., after a package update that changes entry point names), the development rq-worker container will fail to start with a cryptic error.

**Evidence:**
- `docker/docker-compose.override.yml:106` — `command: ["/app/.venv/bin/rqworker", "--url", "redis://redis:6379/0"]`
- `docker/docker-compose.yml:162` — `command: ["uv", "run", "rq", "worker", "--url", "redis://redis:6379/0"]`

**Recommendation:** Standardize both to use the same command format. Prefer `["uv", "run", "rq", "worker", ...]` for consistency with the production compose, or verify that `/app/.venv/bin/rqworker` is a reliable path across RQ versions. Effort: trivial.

---

### DC-006: `ADMIN_PASSWORD` Default in `config.py` Is a Placeholder That Passes Validation in Non-Production

| Field | Value |
|-------|-------|
| **ID** | DC-006 |
| **Severity** | HIGH |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/config.py`, `src/mkobi/db/starter.py` |
| **Classification** | mandatory |

**Description:** The `Settings` class defines `admin_password` with a default value of `"CHANGE_ME_ADMIN_PASSWORD"` (line 553 of `config.py`). This value is in the `WEAK_PASSWORDS` blocklist (line 27: `"change_me_admin_password"`). The `ensure_admin_user()` method in `db/starter.py` (lines 317-352) uses `config.admin_password` directly to create the admin user via `hash_password(admin_password)`. In development mode, the `validate_admin_credentials` validator only logs a warning (lines 402-415) and does not prevent startup. This means if a developer forgets to set `ADMIN_PASSWORD` in their `.env`, the admin user will be created with the hashed value of `"CHANGE_ME_ADMIN_PASSWORD"` — a publicly known string. While this is "just" development, it's a security anti-pattern: the code should never create real database users with known default passwords. The `ensure_admin_user` method also does not check whether the password being used is a placeholder value.

**Evidence:**
- `src/mkobi/config.py:553` — `admin_password: str = Field(default="CHANGE_ME_ADMIN_PASSWORD", ...)`
- `src/mkobi/config.py:27` — `"change_me_admin_password"` in `WEAK_PASSWORDS`
- `src/mkobi/config.py:386-416` — `validate_admin_credentials` only warns in non-production
- `src/mkobi/db/starter.py:326-352` — `ensure_admin_user` uses `config.admin_password` directly

**Recommendation:** In `ensure_admin_user()`, add a check that refuses to create the admin user if the password matches a known placeholder, even in development. Log an error and skip user creation rather than creating a user with a known password. Alternatively, generate a random password in development if none is configured and log it once at startup. Effort: small.

---

### DC-007: Test Compose Uses Default Passwords Without `${VAR:?}` Enforcement

| Field | Value |
|-------|-------|
| **ID** | DC-007 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `docker/docker-compose.test.yml` |
| **Classification** | advisory |

**Description:** The test Docker Compose file (`docker-compose.test.yml`) uses `${DATABASE__PASSWORD:-test_password}` syntax (line 33) with a default value, unlike the production compose which uses `${DATABASE__PASSWORD:?DATABASE__PASSWORD is required}` (line 21 of `docker-compose.yml`) that fails if the variable is not set. While this is intentional for test convenience (tests should work out of the box), it means the test environment silently falls back to `test_password` if the `.env` file doesn't set `DATABASE__PASSWORD`. This is documented as low-risk in the compose file's own comments (lines 12-23), but it creates a subtle difference: the test environment's security posture is weaker than production by design, which is correct, but the fallback passwords are hardcoded in the compose file itself, making them discoverable in version control.

**Evidence:**
- `docker/docker-compose.test.yml:33` — `POSTGRES_PASSWORD: ${DATABASE__PASSWORD:-test_password}`
- `docker/docker-compose.test.yml:34` — `MKOBI_APP_PASSWORD: ${MKOBI_APP_PASSWORD:-test_app_password}`
- `docker/docker-compose.yml:21` — `POSTGRES_PASSWORD: ${DATABASE__PASSWORD:?DATABASE__PASSWORD is required}`

**Recommendation:** This is acceptable for a test environment as documented. No code change needed. Consider adding a comment in the test compose file noting that these defaults are intentionally weak and must never be used in production. Effort: trivial (comment only).

---

### DC-008: `docs/06-backend/configuration.md` Documents Incorrect Default for `DATABASE__USER` and `JWT__ACCESS_TOKEN_EXPIRE_MINUTES`

| Field | Value |
|-------|-------|
| **ID** | DC-008 |
| **Severity** | LOW |
| **Type** | DOC-UPDATE |
| **Affected Modules** | `docs/06-backend/configuration.md`, `src/mkobi/config.py` |
| **Classification** | advisory |

**Description:** The configuration documentation at `docs/06-backend/configuration.md` lists incorrect defaults for two environment variables:
1. `DATABASE__USER` — Documented default is `postgres` (line 52), but the actual code default in `DatabaseSettings` is `mkobi_app` (line 94 of `config.py`).
2. `JWT__ACCESS_TOKEN_EXPIRE_MINUTES` — Documented default is `30` (line 56), but the actual code default in `JWTSettings` is `15` (line 185 of `config.py`).

These discrepancies mislead developers about the actual runtime behavior.

**Evidence:**
- `docs/06-backend/configuration.md:52` — `DATABASE__USER` default listed as `postgres`
- `src/mkobi/config.py:94` — `user: str = "mkobi_app"`
- `docs/06-backend/configuration.md:56` — `JWT__ACCESS_TOKEN_EXPIRE_MINUTES` default listed as `30`
- `src/mkobi/config.py:185` — `access_token_expire_minutes: int = 15`

**Recommendation:** Update `docs/06-backend/configuration.md` to reflect the actual code defaults: `DATABASE__USER` = `mkobi_app`, `JWT__ACCESS_TOKEN_EXPIRE_MINUTES` = `15`. Effort: trivial (doc update only).

---

### DC-009: `docs/06-backend/configuration.md` Documents `RECREATE_TEST_DB` Default as `false`, Code Default Is `false` but Test Compose Sets It to `true`

| Field | Value |
|-------|-------|
| **ID** | DC-009 |
| **Severity** | LOW |
| **Type** | DOC-UPDATE |
| **Affected Modules** | `docs/06-backend/configuration.md`, `src/mkobi/config.py`, `docker/docker-compose.test.yml` |
| **Classification** | advisory |

**Description:** The configuration documentation at line 67 of `docs/06-backend/configuration.md` lists `RECREATE_TEST_DB` default as `false`, which matches the code default (`config.py:488`). However, the test compose file sets `RECREATE_TEST_DB: "true"` (line 145 of `docker-compose.test.yml`), and the test `conftest.py` also sets `os.environ.setdefault("RECREATE_TEST_DB", "true")` (line 28). The documentation doesn't mention that the test environment explicitly overrides this to `true`, which is important context for understanding test behavior.

**Evidence:**
- `docs/06-backend/configuration.md:67` — `RECREATE_TEST_DB` default `false`
- `docker/docker-compose.test.yml:145` — `RECREATE_TEST_DB: "true"`
- `tests/conftest.py:28` — `os.environ.setdefault("RECREATE_TEST_DB", "true")`

**Recommendation:** Add a note in the documentation that the test environment explicitly sets `RECREATE_TEST_DB=true` to ensure a fresh database for each test run. Effort: trivial (doc update only).

---

### DC-010: `SecurityHeadersMiddleware` Sets HSTS and CSP Only in Production, but Nginx Sets Them Unconditionally

| Field | Value |
|-------|-------|
| **ID** | DC-010 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/app.py`, `docker/nginx/nginx.conf` |
| **Classification** | advisory |

**Description:** The `SecurityHeadersMiddleware` in `app.py` (lines 74-77) conditionally sets `Strict-Transport-Security` and `Content-Security-Policy` only when `config.environment == EnvironmentEnum.PRODUCTION`. However, the Nginx configuration sets `Content-Security-Policy` unconditionally (line 30 of `nginx.conf`) — even in development or HTTP contexts where CSP may cause issues with Vite's hot reload (inline scripts, eval). The Nginx HSTS header is correctly commented out (line 24-25) with a note that it should only be set on HTTPS. The CSP header in Nginx, however, is active on port 80 HTTP and may break the Vite dev server when accessed through Nginx.

**Evidence:**
- `src/mkobi/app.py:74-77` — Conditional HSTS/CSP only in production
- `docker/nginx/nginx.conf:30` — Unconditional CSP header
- `docker/nginx/nginx.conf:24-25` — HSTS correctly noted as HTTPS-only

**Recommendation:** Either remove the CSP from the Nginx config (let the application handle it) or add a comment noting that CSP may need adjustment for development. The current Nginx CSP includes `style-src 'unsafe-inline'` which accommodates React CSS-in-JS, but `script-src 'self'` without `'unsafe-eval'` will block Vite's HMR in development. Effort: trivial.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 3 |
| LOW | 5 |

## Mandatory Fixes

- **DC-001**: Align Nginx `X-Frame-Options` with application intent (`DENY` vs `SAMEORIGIN`)
- **DC-005**: Standardize rq-worker command format between override and production compose files
- **DC-006**: Prevent `ensure_admin_user()` from creating users with known placeholder passwords, even in development

## Advisory Recommendations

- **DC-002**: Add `/health/detailed` proxy to Nginx config
- **DC-004**: Add startup warnings for weak/default credentials in development mode
- **DC-007**: Consider adding comments about intentionally weak test passwords (no code change)
- **DC-010**: Review Nginx unconditional CSP header impact on development workflows

## Doc Updates Needed

- **DC-003**: Update `docs/08-security/security-overview.md` — `RATE_LIMITER_FAIL_CLOSED` default is `true` (fail-closed), not `false`
- **DC-008**: Update `docs/06-backend/configuration.md` — `DATABASE__USER` default is `mkobi_app`, `JWT__ACCESS_TOKEN_EXPIRE_MINUTES` default is `15`
- **DC-009**: Update `docs/06-backend/configuration.md` — note that test environment sets `RECREATE_TEST_DB=true`
