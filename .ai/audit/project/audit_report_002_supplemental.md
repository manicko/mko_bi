# Supplemental Project Audit Report — mkobi BI Dashboard

**Date:** 2026-05-19
**Auditor:** OWL (Architecture Audit Agent)
**Scope:** Deep-dive into areas NOT fully covered by audit_report_001.md
**Report Version:** 002 (Supplemental)

---

## 1. Purpose

This report supplements `audit_report_001.md` with findings from a deeper inspection of:
- Database starter / migration concurrency
- Service layer transaction boundaries
- Data worker error handling
- Configuration edge cases
- Docker/production deployment concerns
- Test infrastructure gaps

Findings from report 001 are NOT duplicated here.

---

## 2. New Findings

### 2.1 HIGH — Database Starter Concurrency Issues

| # | Severity | File | Line(s) | Problem | Impact | Recommendation |
|---|---|---|---|---|---|---|
| S1 | HIGH | `src/mkobi/db/starter.py` | 166-177 | `recreate_test_database()` hardcodes `bidb_test` database name in raw SQL. | Breaks if test DB name differs from `bidb_test`. Not configurable. | Parse DB name from URL using `sqlalchemy.engine.url.make_url()`. |
| S2 | HIGH | `src/mkobi/db/starter.py` | 166-177 | `DROP DATABASE IF EXISTS bidb_test` uses f-string interpolation with no SQL injection protection. | Even for internal tooling, this is a bad practice. If DB name ever comes from user input, it's exploitable. | Use `psycopg2.sql.Identifier` or at minimum validate the name against `^[a-zA-Z0-9_]+$`. |
| S3 | HIGH | `src/mkobi/db/starter.py` | 191-207 | `_apply_migrations()` runs Alembic without a distributed lock. In multi-instance deployments (K8s replicas, Gunicorn workers), parallel migrations can corrupt the schema. | Schema corruption, failed startups, data loss in concurrent deployments. | Use `pg_advisory_lock()` before running migrations, or use an external migration job that runs before app startup. |
| S4 | HIGH | `src/mkobi/db/starter.py` | 209-253 | `ensure_admin_user()` has a race condition: `get_by_email` → `if None` → `create`. Two concurrent startups can both pass the check before either creates the user. The `IntegrityError` catch is a partial mitigation but still produces error logs. | Duplicate admin creation attempts, noisy error logs, potential for inconsistent state if the `IntegrityError` path has bugs. | Use `INSERT ... ON CONFLICT DO NOTHING` (UPSERT) instead of check-then-create. |

### 2.2 HIGH — Service Layer Transaction Boundary Issues

| # | Severity | File | Line(s) | Problem | Impact | Recommendation |
|---|---|---|---|---|---|---|
| S5 | HIGH | `src/mkobi/services/auth_service.py` | 141-143, 192-194, 229-231, etc. | Multiple service methods (`register_user`, `login_user`, `get_user_by_id`, etc.) create their own DB session when called without `db` parameter. This means the caller's transaction boundary is bypassed. | If a caller starts a transaction and calls multiple service methods, each method may use a different session, breaking atomicity. Partial commits can leave the DB in an inconsistent state. | Remove the "create your own session" fallback. Require `db` as a mandatory parameter. Let FastAPI dependency injection handle session lifecycle. |
| S6 | HIGH | `src/mkobi/services/data_service.py` | 100-109, 166-172, 241-245, etc. | Same pattern: `DataService` methods create their own sessions when `db=None`. The `process_upload` → `_execute_upload` flow creates a new session if none is provided, but the file processing and log creation should be in the same transaction. | File saved to disk but processing log not committed, or vice versa. Orphaned temp files with no DB record. | Require `db` parameter. Use a unit-of-work pattern if transaction coordination across services is needed. |

### 2.3 MEDIUM — Data Worker Issues

| # | Severity | File | Line(s) | Problem | Impact | Recommendation |
|---|---|---|---|---|---|---|
| S7 | MEDIUM | `src/mkobi/workers/data_worker.py` | 32-66 | `_update_processing_log_status()` creates a new session for each status update. If the worker crashes between the file processing and the final status update, the log can be left in `PROCESSING` state forever. | Stale `PROCESSING` entries that never resolve to `SUCCESS` or `FAILED`. Admin has no way to distinguish "still running" from "crashed". | Add a heartbeat mechanism or a timeout-based cleanup job that marks stale `PROCESSING` entries as `FAILED`. |
| S8 | MEDIUM | `src/mkobi/workers/data_worker.py` | 193-269 | `_store_aggregates()` uses `session.begin()` which creates a nested transaction. If `save_aggregates` fails after partial writes, the rollback may not clean up all data depending on savepoint behavior. | Partial data writes — some aggregates saved, others not, with no clear indication of inconsistency. | Use a single top-level transaction. Consider using `TRUNCATE + INSERT` for overwrite mode instead of `DELETE + INSERT` for atomicity. |
| S9 | MEDIUM | `src/mkobi/workers/data_worker.py` | 227-243 | When `graph.dimensions` is empty or invalid, the fallback uses `df.columns[:3]` as dimensions. This is implicit and may produce incorrect results silently. | Wrong data aggregation — first 3 columns may not be the intended dimensions. No error is raised. | Raise an explicit error when dimensions are invalid, or require dimensions to be explicitly set before processing. |

### 2.4 MEDIUM — Configuration & Deployment Issues

| # | Severity | File | Line(s) | Problem | Impact | Recommendation |
|---|---|---|---|---|---|---|
| S10 | MEDIUM | `src/mkobi/config.py` | 454-470 | `get_config()` uses a global singleton (`_settings`). Once initialized, the config cannot be reloaded without restarting the process. | Cannot change configuration at runtime (e.g., log level, feature flags). Testing with different configs requires monkeypatching the global. | Consider a reload mechanism or use `lru_cache` with a clear invalidation path for tests. |
| S11 | MEDIUM | `src/mkobi/config.py` | 258-272 | `validate_admin_credentials()` checks `admin_username == "admin"` but the default admin email in `.env` is `admin@example.com`. The validator won't catch if someone sets `ADMIN_USERNAME=admin` in production. | The check is bypassed by using `admin` as username instead of `admin@example.com`. | Check against a set of known-weak values: `{"admin", "administrator", "root"}`. |
| S12 | MEDIUM | `Dockerfile` | 81 | Dev stage runs as root with `--reload`. This is acceptable for dev but the comment says "needed for writable mounted volumes with egg-info" — this is a workaround, not a solution. | Running as root in containers is a security anti-pattern. If the container is compromised, the attacker has root. | Use `USER app` and fix the volume permissions instead. Use `chmod` in the Dockerfile or an entrypoint script. |
| S13 | MEDIUM | `docker-compose.yml` | 57 | `AUTO_MIGRATE: "false"` in production compose. This means migrations must be run manually or via a separate job. But there's no migration job defined in the compose file. | If someone deploys without running migrations, the app will fail to start (schema mismatch). No automated migration path in the compose setup. | Add a migration service/job that runs before the app starts, or use an init container pattern. |

### 2.5 MEDIUM — Security Concerns

| # | Severity | File | Line(s) | Problem | Impact | Recommendation |
|---|---|---|---|---|---|---|
| S14 | MEDIUM | `src/mkobi/core/security.py` | 149 | `hash_password()` logs "Password hashed successfully" at INFO level on every hash operation. | In production, this creates noise in logs and could leak timing information about user creation/registration events. | Change to DEBUG level. Never log security-relevant operations at INFO. |
| S15 | MEDIUM | `src/mkobi/core/security.py` | 179, 260 | `verify_password()` and `decode_token()` log success at INFO level. | Same as above — logs every successful auth, creating noise and potential information leakage. | Change to DEBUG level. |
| S16 | MEDIUM | `src/mkobi/db/starter.py` | 205 | `_apply_migrations()` logs the full database URL: `logger.info("Running migrations for %s...", db_url)`. The URL may contain credentials. | Credentials leaked to logs. | Use `url.render_as_string(hide_password=True)` or strip the password before logging. |
| S17 | MEDIUM | `src/mkobi/api/routes/auth.py` | 47-48 | Login rate limiting uses `f"login:{email}"` as the key. An attacker can enumerate emails by observing which keys are rate-limited. | Email enumeration via rate limit side-channel. | Use IP-based rate limiting for login, or a combination of IP + email with a cooldown period. |

### 2.6 LOW — Code Quality & Maintainability

| # | Severity | File | Line(s) | Problem | Impact | Recommendation |
|---|---|---|---|---|---|---|
| S18 | LOW | `src/mkobi/db/starter.py` | 68 | `self._test_engine: AsyncEngine | None = None` is declared but never assigned or used. | Dead state — confusing for maintainers. | Remove the unused field. |
| S19 | LOW | `src/mkobi/db/starter.py` | 185-187 | `migration_engine = create_async_engine(test_url)` is created but never used — only passed to `_apply_migrations` which doesn't use it either. | Unnecessary engine creation. Wastes resources. | Remove the unused engine. |
| S20 | LOW | `src/mkobi/db/starter.py` | 254-272 | `cleanup_old_logs()` is defined but never called from `startup()` or anywhere else. | Dead code. Log table grows unbounded. | Either call it from startup on a schedule, or remove it. |
| S21 | LOW | `src/mkobi/api/deps.py` | 109-113 | `get_db()` in `permissions.py` and `get_db_dependency()` in `deps.py` are nearly identical — both create a session context manager. | Duplicated logic. If session management changes, both need updating. | Consolidate into a single dependency. Import from `deps.py` in `permissions.py`. |
| S22 | LOW | `src/mkobi/api/deps.py` | 39 | `get_session` is imported with `# noqa: F401` for backwards compatibility, but it's unclear who imports it from here. | Implicit coupling. | Add a deprecation comment with a timeline for removal. |
| S23 | LOW | `src/mkobi/services/dashboard_service.py` | 169 | Admin bypass check `user_role == UserRole.ADMIN` works due to StrEnum implicit comparison, but `user_role` comes from `UserRead.role` which is already a `UserRole` enum. The comparison is correct but the type flow is unclear. | Future maintainers may not understand why string comparison works. | Add a type annotation or explicit cast for clarity. |
| S24 | LOW | `src/mkobi/data/storage/manager.py` | 443-504 | `save_aggregated_data`, `clear_graph_data_compat`, `clear_dashboard_data_compat` are compatibility classmethods that duplicate instance methods. | Code duplication. Two ways to do the same thing. | Deprecate the classmethods. Migrate callers to use instance methods. |
| S25 | LOW | `pyproject.toml` | 169-195 | Multiple `mypy.overrides` sections with `ignore_errors = true` for `db.*`, `interfaces.*`, `models.*`. This suppresses real type errors. | Type safety is weakened. Bugs that mypy could catch are hidden. | Gradually remove these overrides and fix the underlying type issues. |

---

## 3. Database Starter Detailed Analysis

The `DatabaseStarter` class in `src/mkobi/db/starter.py` is the most architecturally problematic module. Beyond the findings above:

### 3.1 Startup Does Too Much

The `startup()` method sequentially:
1. Creates the main engine
2. Checks DB connectivity
3. Runs Alembic migrations
4. Validates schema via Alembic revision check
5. Ensures admin user exists
6. Cleans up stale temp files
7. Optionally recreates the test database

This is an orchestration script, not a database initialization module. Under load or in containerized environments, this creates a long startup time and multiple failure points.

**Recommendation:** Split into separate concerns:
- `MigrationService` — handles Alembic with advisory lock
- `AdminBootstrapService` — handles admin user creation with UPSERT
- `CleanupService` — handles temp file cleanup (can be async/background)
- `TestDatabaseService` — handles test DB recreation (test-only)

### 3.2 No Startup Observability

The startup is a linear script with no structured progress tracking. If startup fails at step 5 of 7, there's no indication of how far it got.

**Recommendation:** Implement a startup stage enum with structured logging:
```python
class StartupStage(StrEnum):
    CONNECT_DB = "connect_db"
    RUN_MIGRATIONS = "run_migrations"
    VERIFY_SCHEMA = "verify_schema"
    ENSURE_ADMIN = "ensure_admin"
    CLEANUP = "cleanup"
```

This enables better observability, retry support, and metrics.

---

## 4. Test Infrastructure Gaps

### 4.1 Test Coverage Unknown

The `pyproject.toml` sets `fail_under = 80` for coverage, but there's no evidence this threshold is actually met. The test suite has 16 test files covering:
- Auth, auth service, config, dashboards API, data service, filters, graphs, graph service, layouts, processing logs, pydantic models, repositories, security, storage manager, upload API, users API

**Missing test areas:**
- `DatabaseStarter` — no tests for migration logic, admin bootstrap, test DB recreation
- `data_worker.py` — no tests for background CSV processing
- `file_processing.py` — no tests for `process_upload_with_session`, `enqueue_processing_job`
- `transformations.py` — no tests for `_parse_formula`, `_calculate_yoy`, `_calculate_share`
- `permissions.py` — no tests for `check_dashboard_access` with admin bypass
- Integration tests — no end-to-end upload → process → retrieve flow

### 4.2 Test Database Configuration

Tests use `Base.metadata.create_all()` (via `init_db()`) rather than running Alembic migrations. This means the test schema may differ from the production schema (missing indexes, constraints, defaults).

**Recommendation:** Use Alembic migrations in tests to ensure schema parity, or at minimum verify that `create_all()` produces the same schema as the migrations.

---

## 5. Deployment Safety

### 5.1 No Migration Job in Docker Compose

The production compose file sets `AUTO_MIGRATE: "false"` but provides no alternative migration mechanism. The `alembic.ini` has `sqlalchemy.url` commented out, relying on `env.py` to set it at runtime.

**Risk:** Deploying a new version without running migrations first will cause startup failure.

**Recommendation:** Add a migration job:
```yaml
migrate:
  build:
    context: .
    target: prod
  command: ["alembic", "upgrade", "head"]
  depends_on:
    db:
      condition: service_healthy
```

### 5.2 Health Check Timing

The app's health check (`/health`) does a `SELECT 1` on the database. But the app's startup includes migrations, admin bootstrap, and cleanup. The health check will return 200 as soon as the DB is reachable, even if migrations haven't run yet.

**Risk:** Load balancer may route traffic to an instance that hasn't completed startup.

**Recommendation:** Add a readiness check that verifies migrations are up to date, or use a startup probe in K8s.

### 5.3 No Graceful Shutdown Handling

The `lifespan` shutdown handler calls `starter.shutdown()` which disposes engines. But there's no handling for in-flight requests or background tasks.

**Risk:** Requests being processed during shutdown may fail with connection errors.

**Recommendation:** Add a shutdown delay or use Starlette's `lifespan` with proper cleanup ordering.

---

## 6. Summary of New Findings

| Severity | Count | Key Areas |
|---|---|---|
| HIGH | 4 | DB starter concurrency, transaction boundaries, migration locking |
| MEDIUM | 13 | Data worker reliability, config issues, security logging, rate limiting |
| LOW | 8 | Dead code, duplicated logic, type safety gaps |

### New Critical Risks (not in report 001)

1. **HIGH — Migration concurrency:** No distributed lock on Alembic migrations. Multi-instance deployments risk schema corruption.
2. **HIGH — Transaction boundaries:** Service methods that create their own sessions break atomicity. Can lead to orphaned files or inconsistent DB state.
3. **HIGH — Admin user race condition:** Check-then-create pattern in `ensure_admin_user()` is not safe for concurrent startups.
4. **MEDIUM — Credential logging:** Database URLs with passwords logged at INFO level during migrations.
5. **MEDIUM — No migration job:** Production compose has no migration mechanism despite `AUTO_MIGRATE=false`.

---

## 7. Consolidated Fix Priority (with report 001 findings)

### Immediate (before production):
1. Fix `graphs` table schema mismatch (report 001, #2)
2. Add missing composite index (report 001, #1)
3. Add advisory lock for migrations (this report, S3)
4. Fix admin user race condition with UPSERT (this report, S4)
5. Remove credential logging from migration URL (this report, S16)
6. Add migration job to Docker compose (this report, S13)

### Short-term (next sprint):
7. Add admin bypass to `check_dashboard_access()` (report 001, #4)
8. Add log date filtering and pagination (report 001, #3)
9. Fix service transaction boundaries (this report, S5, S6)
10. Bound token cache (report 001, #5)
11. Fix security log levels (this report, S14, S15)

### Medium-term:
12. Refactor DatabaseStarter into separate services
13. Add heartbeat/timeout for stale processing logs (this report, S7)
14. Improve test coverage for data worker and transformations
15. Remove dead code and consolidate duplicated logic

---

**End of Supplemental Report**
