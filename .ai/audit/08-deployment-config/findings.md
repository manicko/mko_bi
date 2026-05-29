---
name: audit-findings
description: Structured findings template for audit phase output
agent: audit-executor
alwaysApply: false
---

# Phase 08 Audit Findings — Configuration & Lifecycle

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### DC-001: Configuration centralized in single module

| Field | Value |
|-------|-------|
| **ID** | DC-001 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/config.py |
| **Classification** | advisory |

**Description:** Configuration is well-organized in a single `config.py` module with nested Pydantic models (DatabaseSettings, JWTSettings, RedisSettings, etc.) and a central Settings class inheriting from BaseSettings. The module follows a clean architecture pattern with pydantic-settings for environment variable parsing.

**Evidence:** src/mkobi/config.py:232-503 - Settings class with nested settings for database, JWT, Redis, upload, logging, charts, app, email, dashboard. Related constants (WEAK_USERNAMES, WEAK_PASSWORDS) defined at module level (lines 17-18). Settings custom sources method properly orders priority (lines 341-374).

**Recommendation:** Current implementation is well-structured. Consider documenting the configuration priority order in the module docstring for future maintainers.

---

### DC-002: Secrets derived from environment variables with multiple source support

| Field | Value |
|-------|-------|
| **ID** | DC-002 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/config.py |
| **Classification** | advisory |

**Description:** Secrets are properly obtained from environment variables with support for multiple sources including Docker secrets via the `_FILE` suffix pattern. The priority order is correctly documented and implemented: environment variables > Docker secrets files > .env file > YAML config > defaults.

**Evidence:** src/mkobi/config.py:36-74 - SecretsFileSource class handles DATABASE__PASSWORD_FILE and JWT__SECRET_KEY_FILE patterns. Lines 361-374 show the priority order in `settings_customise_sources()`. Tests confirm Docker secrets work correctly (tests/test_config.py:122-151).

**Recommendation:** Continue current approach. No changes needed - this is a security best practice properly implemented.

---

### DC-003: Production refuses insecure defaults for admin credentials

| Field | Value |
|-------|-------|
| **ID** | DC-003 |
| **Severity** | CRITICAL |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/config.py |
| **Classification** | mandatory |

**Description:** Production environment refuses insecure default credentials. When `ENV=production`, the validator checks against known-weak usernames and passwords, preventing startup with default "admin/admin" credentials.

**Evidence:** src/mkobi/config.py:285-310 - `validate_admin_credentials()` model_validator raises ValueError for weak credentials in production. Lines 32-34 define WEAK_USERNAMES and WEAK_PASSWORDS constants. Tests verify this behavior (tests/test_config.py:316-349).

**Recommendation:** Continue current approach. No changes needed - this is a security best practice properly implemented.

---

### DC-004: Configuration validated at startup

| Field | Value |
|-------|-------|
| **ID** | DC-004 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/config.py, src/mkobi/app.py |
| **Classification** | advisory |

**Description:** Configuration is validated at startup through Pydantic model validators and the create_app() function. JWT secret key is validated, CORS configuration is validated for production, and admin credentials are validated.

**Evidence:** src/mkobi/app.py:120-138 - JWT secret key validation and CORS validation for production. src/mkobi/config.py:285-310 - Admin credential validation.

**Recommendation:** Consider adding explicit validation that database URL is provided (currently returns None if password not set, which could cause unclear errors later).

---

### DC-005: No hardcoded values in configuration

| Field | Value |
|-------|-------|
| **ID** | DC-005 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/config.py |
| **Classification** | advisory |

**Description:** No hardcoded secrets in production configuration. All sensitive values (passwords, JWT secret) default to None or must be provided via environment variables/secret files.

**Evidence:** src/mkobi/config.py:79-87 - DatabaseSettings with password defaulting to None. Line 127 - JWTSettings secret_key defaulting to None. The Docker deploy uses required environment variables with `:${VAR:-}` syntax (docker/docker-compose.yml:21,53,56,60,85,87,91).

---

### DC-006: Dependency check on startup

| Field | Value |
|-------|-------|
| **ID** | DC-006 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/main.py |
| **Classification** | advisory |

**Description:** Application performs dependency import verification on startup to ensure all required packages are available before the application begins serving requests.

**Evidence:** src/mkobi/main.py:10-50 - REQUIRED_MODULES list checked via __import__() in check_dependencies(). Missing dependencies cause SystemExit(1). This runs before imports to prevent cryptic import errors later.

---

### DC-007: Database connectivity verified before accepting requests

| Field | Value |
|-------|-------|
| **ID** | DC-007 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/db/starter.py, src/mkobi/app.py |
| **Classification** | mandatory |

**Description:** The application verifies database connectivity with timeout and retry logic before accepting requests. The DatabaseStarter performs connection checks with configurable retry count and exponential backoff.

**Evidence:** src/mkobi/db/starter.py:75-111 - `_check_db_connection()` method with timeout (10s) and retry logic (up to 5 attempts). src/mkobi/app.py:46-92 - `lifespan()` calls `await starter.startup()` which includes connectivity verification.

---

### DC-008: Schema existence verified on startup

| Field | Value |
|-------|-------|
| **ID** | DC-008 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/db/starter.py |
| **Classification** | mandatory |

**Description:** Application checks for alembic revision presence to verify database schema is initialized before proceeding. If no schema is found, a SchemaNotFoundError is raised.

**Evidence:** src/mkobi/db/starter.py:112-130 - `_get_alembic_revision()` queries alembic_version table. Lines 155-160 - Startup raises SchemaNotFoundError if no revision found.

---

### DC-009: Migrations run automatically when configured

| Field | Value |
|-------|-------|
| **ID** | DC-009 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/db/starter.py |
| **Classification** | advisory |

**Description:** Auto-migrations are supported via the `AUTO_MIGRATE` configuration option. In Docker production, migrations run via a dedicated `migrate` service that completes before the app starts.

**Evidence:** src/mkobi/db/starter.py:131,152-153 - `auto_migrate` check in startup() calls `_apply_migrations()`. docker/docker-compose.yml:40-65 - Separate migrate service runs `alembic upgrade head`.

---

### DC-010: Admin user creation is idempotent

| Field | Value |
|-------|-------|
| **ID** | DC-010 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/db/starter.py |
| **Classification** | advisory |

**Description:** Admin user creation uses atomic UPSERT (`INSERT ... ON CONFLICT (email) DO NOTHING`) to avoid race conditions on concurrent startup.

**Evidence:** src/mkobi/db/starter.py:300-334 - `ensure_admin_user()` method. Lines 322-334 show the INSERT with ON CONFLICT DO NOTHING pattern.

---

### DC-011: Stale temp files cleaned on startup

| Field | Value |
|-------|-------|
| **ID** | DC-011 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/db/starter.py, src/mkobi/services/file_cleanup.py |
| **Classification** | advisory |

**Description:** Stale temporary files are cleaned up on application startup via `cleanup_stale_temp_files()` which removes files older than the configured threshold.

**Evidence:** src/mkobi/db/starter.py:166-169 - Calls `cleanup_stale_temp_files()` during startup. src/mkobi/services/file_cleanup.py:39-96 - Implementation that deletes files older than threshold_hours.

---

### DC-012: Test database recreated when configured

| Field | Value |
|-------|-------|
| **ID** | DC-012 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/db/starter.py |
| **Classification** | advisory |

**Description:** Test database recreation is supported via `RECREATE_TEST_DB` and `ENV=test` configuration options. The recreation process drops and recreates the test database with proper permissions.

**Evidence:** src/mkobi/db/starter.py:174-176 - Check for test environment or recreate flag. Lines 180-275 - `recreate_test_database()` method. docker/docker-compose.test.yml:78-116 - Test compose uses RECREATE_TEST_DB=true.

---

### DC-013: Production debug mode disabled

| Field | Value |
|-------|-------|
| **ID** | DC-013 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/app.py |
| **Classification** | mandatory |

**Description:** Production mode disables FastAPI debug mode and API documentation endpoints. Debug mode defaults to False, and docs/redoc URLs are set to None when environment is PRODUCTION.

**Evidence:** src/mkobi/app.py:144-147 - `debug=config.debug` (defaults to False) and `docs_url=None if config.environment == EnvironmentEnum.PRODUCTION else "/docs"`.

---

### DC-014: Logging level appropriate for production

| Field | Value |
|-------|-------|
| **ID** | DC-014 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/core/logging_config.py |
| **Classification** | advisory |

**Description:** Production logging uses JSON format by default with INFO level, which is appropriate for a production environment. Log file path is configurable.

**Evidence:** src/mkobi/settings/app.yaml:53-57 - JSON logging enabled with INFO level. src/mkobi/core/logging_config.py:72-187 - `setup_logging()` function configures JSON or standard formatters.

---

### DC-015: Production credentials enforced in Docker

| Field | Value |
|-------|-------|
| **ID** | DC-015 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | docker/docker-compose.yml |
| **Classification** | advisory |

**Description:** Docker production compose uses required environment variable syntax (`:${VAR:?error}`) to enforce production credentials cannot be omitted.

**Evidence:** docker/docker-compose.yml:21,23,53,56,59-60,85,87,91,94-95 - All sensitive variables use `?VAR is required` syntax to fail container startup if not provided.

---

### DC-016: CORS origins validated in production

| Field | Value |
|-------|-------|
| **ID** | DC-016 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/app.py |
| **Classification** | mandatory |

**Description:** Production mode validates that CORS origins are configured and rejects wildcard (*) which would be a security risk.

**Evidence:** src/mkobi/app.py:126-138 - Validates `cors_origins` is set and rejects `"*"` in production with clear error messages.

---

### DC-017: Graceful shutdown with resource cleanup

| Field | Value |
|-------|-------|
| **ID** | DC-017 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/app.py, src/mkobi/db/starter.py |
| **Classification** | mandatory |

**Description:** Application implements graceful shutdown in the lifespan finally block, disposing database engines and cancelling background tasks.

**Evidence:** src/mkobi/app.py:93-105 - Shutdown logs and cancels cleanup task. src/mkobi/db/starter.py:357-362 - `shutdown()` method disposes the main engine.

---

### DC-018: Background task termination on shutdown

| Field | Value |
|-------|-------|
| **ID** | DC-018 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/app.py |
| **Classification** | mandatory |

**Description:** Background cleanup task for stale processing logs is properly cancelled on shutdown using asyncio cancellation pattern.

**Evidence:** src/mkobi/app.py:96-103 - Background task cancellation with proper asyncio.CancelledError handling.

---

### DC-019: Advisory lock for concurrent migrations

| Field | Value |
|-------|-------|
| **ID** | DC-019 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | alembic/env.py |
| **Classification** | mandatory |

**Description:** Migrations use PostgreSQL advisory lock to prevent concurrent schema modifications in multi-instance deployments.

**Evidence:** alembic/env.py:54-125 - Advisory lock key 42 is acquired before migrations and released afterwards, even on errors (lines 111-136).

---

### DC-020: Dedicated application database role

| Field | Value |
|-------|-------|
| **ID** | DC-020 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | docker/init-scripts/01-create-app-role.sh |
| **Classification** | advisory |

**Description:** Production uses a dedicated `mkobi_app` database role with least-privilege principle instead of the superuser, requiring CREATEDB privilege only for test database operations.

**Evidence:** docker/init-scripts/01-create-app-role.sh - Creates mkobi_app role with specific privileges. docker/docker-compose.yml:84-87 - App connects as mkobi_app, admin operations use postgres role.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 1 |
| HIGH | 0 |
| MEDIUM | 7 |
| LOW | 12 |

## Mandatory Fixes

- DC-003: Production refuses insecure defaults for admin credentials
- DC-007: Database connectivity verified before accepting requests
- DC-008: Schema existence verified on startup
- DC-013: Production debug mode disabled
- DC-016: CORS origins validated in production
- DC-017: Graceful shutdown with resource cleanup
- DC-018: Background task termination on shutdown
- DC-019: Advisory lock for concurrent migrations

## Advisory Recommendations

- DC-001: Configuration centralized in single module
- DC-002: Secrets derived from environment variables with multiple source support
- DC-004: Configuration validated at startup
- DC-005: No hardcoded values in configuration
- DC-006: Dependency check on startup
- DC-009: Migrations run automatically when configured
- DC-010: Admin user creation is idempotent
- DC-011: Stale temp files cleaned on startup
- DC-012: Test database recreated when configured
- DC-014: Logging level appropriate for production
- DC-015: Production credentials enforced in Docker
- DC-020: Dedicated application database role

## Doc Updates Needed

None

---