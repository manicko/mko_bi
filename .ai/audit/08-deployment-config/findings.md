# Phase 08 Audit Findings — Deployment Configuration

**Executor:** auditor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** yes

---

## Findings

### DC-001: Missing .env.production File for Production Deployments

| Field | Value |
|-------|-------|
| **ID** | DC-001 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `docker/docker-compose.yml`, `docker/.env.production` |
| **Classification** | mandatory |

**Description:** The documentation specifies `docker/.env.production` as the production configuration template (`docs/11-guides/docker.md` lines 159-162), but this file is missing required environment variables. The file exists as a template but contains only placeholder values without the actual required secrets (`DATABASE__PASSWORD`, `MKOBI_APP_PASSWORD`, `JWT__SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`). Users deploying to production must manually copy values from `.env.example` or create their own values, but the template itself should include all required variables with clear placeholders.

**Evidence:**
- `docker/.env.production` (lines 1-38): Contains template comments but missing required password/secret values
- `docker/.env.development` (lines 10-22): Has placeholder values for development, but production template lacks them
- `docker-compose.yml` (lines 21-23, 64-67, 96, 102, 105-106): Multiple services require `DATABASE__PASSWORD`, `MKOBI_APP_PASSWORD`, `JWT__SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD` with `:?required` syntax

**Recommendation:** Add all required environment variables to `docker/.env.production` with clear "CHANGE_ME" placeholders to match the pattern used in `docker/.env.development` and `.env.example`. This ensures the template is complete and users understand what values must be set.

---

### DC-002: Default .env File Contains Production-Insecure Credentials for Development

| Field | Value |
|-------|-------|
| **ID** | DC-002 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `.env` |
| **Classification** | advisory |

**Description:** The `.env` file at the project root contains `JWT__SECRET_KEY=dev-secret-key-for-security-testing-do-not-use-in-prod-32chars` and `DATABASE__PASSWORD=postgres`. While documented as development-only, these values could accidentally be used in production if the wrong env file is referenced. The file is gitignored but developers might copy it to production environments without understanding the security implications.

**Evidence:**
- `.env` (line 15): 69-character JWT secret that's explicitly marked as development-only in its name
- `.env` (line 10): Database password set to "postgres" (a well-known default)
- `src/mkobi/config.py` (line 189): WEAK_SECRETS includes similar patterns, but this specific value isn't in the list because it's 32+ chars

**Recommendation:** Rename the development secret to be more clearly non-functional (e.g., include "INVALID" in the name) or add a runtime check that detects this known development secret and warns. Consider using environment variable defaults that will fail at startup rather than accepting placeholder values.

---

### DC-003: Stale Temp File Cleanup Uses Default Threshold Without Configuration Override

| Field | Value |
|-------|-------|
| **ID** | DC-003 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/services/file_cleanup.py`, `src/mkobi/db/starter.py` |
| **Classification** | advisory |

**Description:** The `cleanup_stale_temp_files()` function uses a default threshold of 24 hours (hardcoded in Settings) but doesn't accept an override parameter during the startup cleanup call in `DatabaseStarter.startup()`. The function signature supports `max_age_hours` but line 176-178 of `starter.py` calls it without any arguments, always using the default.

**Evidence:**
- `src/mkobi/services/file_cleanup.py` (lines 45-63): Function accepts `max_age_hours` parameter but uses config default
- `src/mkobi/db/starter.py` (line 176): `cleanup_stale_temp_files()` called without arguments

**Recommendation:** Either document that the startup cleanup always uses the configured threshold, or pass the configuration value explicitly to make the dependency clear. The current code works correctly but the parameter passing is implicit.

---

### DC-004: No Graceful Shutdown Handler for Database Session Factory

| Field | Value |
|-------|-------|
| **ID** | DC-004 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/db/session.py`, `src/mkobi/app.py` |
| **Classification** | advisory |

**Description:** The `DatabaseStarter.shutdown()` method (line 391-396 in `db/starter.py`) disposes of `_main_engine` but there's no corresponding cleanup for the global `_engine` and `_SessionLocal` in `db/session.py`. This could lead to connection pool leakage on application shutdown, as the session module creates its own engine independently.

**Evidence:**
- `src/mkobi/db/session.py` (lines 13-14): Global `_engine` and `_SessionLocal` without cleanup function
- `src/mkobi/db/starter.py` (lines 391-396): Only `_main_engine` disposed in shutdown
- `src/mkobi/app.py` (lines 159-167): Lifespan shutdown triggers `starter.shutdown()` but doesn't dispose session engine

**Recommendation:** Add a shutdown/dispose function in `db/session.py` and call it from the application lifespan's `finally` block to ensure all database connections are properly closed.

---

### DC-005: Missing docker/.dockerignore for Consistent Build Context

| Field | Value |
|-------|-------|
| **ID** | DC-005 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `docker/` directory |
| **Classification** | advisory |

**Description:** The project has `.dockerignore` at the root level but Docker documentation recommends placing it in the same directory as the Dockerfile or using `.dockerignore` in the build context root. With multi-stage builds and the Dockerfile in `docker/`, a `docker/.dockerignore` file would ensure consistent build context exclusions when developers run builds from different working directories.

**Evidence:**
- `.dockerignore` (root): Only exists at root level
- `docker/Dockerfile`: Build context is `..` (project root), so root `.dockerignore` is used
- No `.dockerignore` in `docker/` folder

**Recommendation:** While the current setup works (root `.dockerignore` is used because context is project root), consider adding a note in documentation or a duplicate `.dockerignore` in the docker folder for clarity. This is a minor organizational issue.

---

### DC-006: CORS Origins Default May Mislead Production Deployments

| Field | Value |
|-------|-------|
| **ID** | DC-006 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `docker-compose.yml`, `docker/.env.production` |
| **Classification** | mandatory |

**Description:** In `docker-compose.yml` line 109, `CORS_ORIGINS` defaults to `["http://localhost:3000"]` when not set. However, the documentation and security requirements state that CORS origins must be configured for production. This default could allow the application to start in production without proper CORS configuration if the deployment doesn't override the environment variable.

**Evidence:**
- `docker/docker-compose.yml` (line 109): `CORS_ORIGINS: ${CORS_ORIGINS:-["http://localhost:3000"]}`
- `src/mkobi/app.py` (lines 189-202): Production mode validates CORS origins but the default passes this check
- `docker/.env.production`: No CORS_ORIGINS value set (relies on default)

**Recommendation:** Remove the default in `docker-compose.yml` or change to fail-closed (empty array or require explicit configuration). Production deployments should never default to localhost origins.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 2 |
| LOW | 4 |

## Mandatory Fixes

- DC-001: Missing .env.production File for Production Deployments
- DC-006: CORS Origins Default May Mislead Production Deployments

## Advisory Recommendations

- DC-002: Default .env File Contains Production-Insecure Credentials for Development
- DC-003: Stale Temp File Cleanup Uses Default Threshold Without Configuration Override
- DC-004: No Graceful Shutdown Handler for Database Session Factory
- DC-005: Missing docker/.dockerignore for Consistent Build Context

---

## Verification Notes

**Runtime Environment Status:**
- Test environment running: test-app (port 8001), test-db (port 5433), test-redis (port 6380)
- Production environment could not be started without proper .env file (verified at R0)

**Configuration Validation Verified:**
- Settings module properly validates JWT secret strength (32+ chars, not in WEAK_SECRETS)
- Settings module validates admin credentials in production
- Settings module validates debug mode in production
- CORS origins are validated as HTTP/HTTPS URLs
- Docker secrets (_FILE suffix) support is implemented and tested

**Startup Sequence Verified:**
- Dependency check in `main.py` prevents startup with missing packages
- Database connection checked with retries
- Migrations applied via dedicated `migrate` service (not inline)
- Admin user creation is idempotent via UPSERT
- Stale temp file cleanup runs on startup
- Old processing logs cleanup runs on startup

**Production Readiness Verified:**
- Security headers middleware added (HSTS, CSP in production)
- Debug mode disabled in production via validator
- Logging level appropriate (WARNING in test, INFO/WARNING in production configs)
- Database role uses least-privilege (mkobi_app instead of postgres superuser for runtime)