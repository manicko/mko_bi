# Validated Audit Findings — mkobi BI Dashboard

**Date:** 2026-05-20
**Validator:** Kilo (System Integrity Validation Agent)
**Source Reports:**
- `.ai/audit/project/audit_report_001.md` (15 findings)
- `.ai/audit/project/audit_report_002_supplemental.md` (25 findings)
- `.ai/audit/project/audit_report_003_final.md` (36 findings, consolidated)
- `.ai/audit/db/audit_findings_01.md` (10 findings)
- `.ai/audit/db/audit_report_02.md` (12 drift findings + 10 architectural)
- `.ai/audit/db/audit_report_03.md` (verification of 02)
- `.ai/audit/tests/audit_report_001.md` (test quality)
- `.ai/audit/tests/audit_report_1.md` (test architecture mismatch)

**Validation Summary:**
- Total raw findings across all reports: ~110
- After deduplication: 47 unique findings
- Validated (safe to act on): 38
- Rejected (stale/unsafe/low-value): 9
- Merged (overlapping root causes): 12 groups

---

## 1. CRITICAL Findings (Validated: 1)

### V-001 — `graphs` Trigger on Non-Existent Column

- **Severity:** CRITICAL
- **Status:** VALIDATED
- **Source:** audit_report_002 (S3), audit_report_003 (#3), db/audit_report_02 (drift #4), db/audit_findings_01
- **Affected Modules:** `alembic/versions/7130ecb0388c_true_initial_migration.py`, `src/mkobi/db/models/graphs.py`
- **Affected Symbols:** `update_graphs_updated_at` trigger, `graphs` table
- **Description:** The migration creates `update_graphs_updated_at` trigger on the `graphs` table, but the `graphs` table has no `updated_at` column. The trigger function `update_updated_at_column()` sets `NEW.updated_at = NOW()`, which will fail on any UPDATE to the `graphs` table.
- **Impact:** First UPDATE to any graph row will crash with `column "updated_at" of relation "graphs" does not exist`. This is a latent runtime bug that will manifest as soon as any graph is modified via the API.
- **Root Cause:** Migration creates trigger for all tables including `graphs`, but `graphs` was never given an `updated_at` column. The ORM model (`graphs.py`) also lacks `updated_at`, so the trigger references a non-existent column.
- **Recommendation:** `DROP TRIGGER IF EXISTS update_graphs_updated_at ON graphs;` — the trigger is useless without the column and the ORM doesn't expect it.
- **Rollout Considerations:** Safe to apply immediately. No dependencies. Reversible (trigger can be re-added if `updated_at` column is later added).
- **Semantic Anchor:** Migration file `7130ecb0388c_true_initial_migration.py`, trigger creation block. Stable anchor — migration file is immutable.
- **Validation Notes:** Confirmed by 3 independent audit sources. DB audit verified trigger exists in live DB without matching column. This is the highest-priority fix.

---

## 2. HIGH Findings (Validated: 6)

### V-002 — Missing Composite Index `idx_aggregated_data_dashboard_graph`

- **Severity:** HIGH
- **Status:** VALIDATED
- **Source:** audit_report_001 (#1), audit_report_003 (#1)
- **Affected Modules:** `alembic/versions/7130ecb0388c_true_initial_migration.py`
- **Affected Symbols:** `aggregated_data` table, index creation block
- **Description:** Missing composite index on `(dashboard_id, graph_id)`. The migration only creates individual indexes and the GIN index. Queries filtering by both `dashboard_id` and `graph_id` (the most common access pattern) will not use an optimal index.
- **Impact:** Sequential scans on `aggregated_data` for the most common query pattern. Performance degrades as data grows.
- **Root Cause:** Oversight in migration — individual indexes were created but the composite index was missed.
- **Recommendation:** Add `op.execute("CREATE INDEX IF NOT EXISTS idx_aggregated_data_dashboard_graph ON aggregated_data (dashboard_id, graph_id)")` in a new migration.
- **Rollout Considerations:** Safe. `IF NOT EXISTS` makes it idempotent. No dependencies on other fixes. Can be applied independently.
- **Semantic Anchor:** Migration file, index creation section. Stable.
- **Validation Notes:** Confirmed by code inspection. The composite index is the most impactful single performance fix.

### V-003 — Missing `graphs.created_at` Column in Migration vs Model

- **Severity:** HIGH
- **Status:** VALIDATED
- **Source:** audit_report_001 (#2), audit_report_003 (#2)
- **Affected Modules:** `alembic/versions/7130ecb0388c_true_initial_migration.py`, `src/mkobi/db/models/graphs.py`
- **Affected Symbols:** `graphs` table, `Graph.created_at`
- **Description:** The SQLAlchemy model (`graphs.py`) defines `created_at: Mapped[datetime]`, but the Alembic migration does not include a `created_at` column in the `graphs` table.
- **Impact:** Schema mismatch — the model expects a column that doesn't exist in the migration. This will cause `MissingColumnError` at runtime when querying graphs.
- **Root Cause:** The `created_at` column was added to the ORM model but the migration was never updated to match.
- **Recommendation:** Add `created_at TIMESTAMPTZ NOT NULL DEFAULT now()` to the `graphs` table via a new Alembic migration.
- **Rollout Considerations:** Must be applied before any code that queries `Graph.created_at` is deployed. No other dependencies.
- **Semantic Anchor:** `graphs.py` model class, `created_at` field definition. Stable symbol.
- **Validation Notes:** Confirmed. The DB audit shows `created_at` exists in the live DB (it was likely added manually or via `server_default`), but the migration doesn't include it, making the schema non-reproducible.

### V-004 — No Distributed Lock for Alembic Migrations

- **Severity:** HIGH
- **Status:** VALIDATED
- **Source:** audit_report_002 (S3), audit_report_003 (#3), db/audit_findings_01
- **Affected Modules:** `src/mkobi/db/starter.py`
- **Affected Symbols:** `_apply_migrations()`, `startup()`
- **Description:** `_apply_migrations()` runs Alembic without a distributed lock. In multi-instance deployments (K8s replicas, Gunicorn workers), parallel migrations can corrupt the schema.
- **Impact:** Schema corruption, failed startups, data loss in concurrent deployments.
- **Root Cause:** `DatabaseStarter` was designed for single-instance deployment. No advisory lock or external coordination mechanism.
- **Recommendation:** Use `pg_advisory_lock()` before running migrations, or use an external migration job that runs before app startup.
- **Rollout Considerations:** Must be coordinated with deployment strategy. If using Docker Compose with single instance, lower urgency. For K8s/multi-replica, critical.
- **Semantic Anchor:** `DatabaseStarter._apply_migrations()` method. Stable function boundary.
- **Validation Notes:** Confirmed. The `startup()` method calls `_apply_migrations()` without any locking. This is a real risk for any multi-instance deployment.

### V-005 — Admin User Race Condition in `ensure_admin_user()`

- **Severity:** HIGH
- **Status:** VALIDATED
- **Source:** audit_report_002 (S4), audit_report_003 (#4), db/audit_findings_01
- **Affected Modules:** `src/mkobi/db/starter.py`
- **Affected Symbols:** `ensure_admin_user()`
- **Description:** Check-then-create pattern: `get_by_email` → `if None` → `create`. Two concurrent startups can both pass the check before either creates the user. The `IntegrityError` catch is a partial mitigation but still produces error logs.
- **Impact:** Duplicate admin creation attempts, noisy error logs, potential for inconsistent state.
- **Root Cause:** Classic TOCTOU race condition. No UPSERT or advisory lock.
- **Recommendation:** Use `INSERT ... ON CONFLICT DO NOTHING` (UPSERT) instead of check-then-create.
- **Rollout Considerations:** Safe. UPSERT is atomic. No dependencies.
- **Semantic Anchor:** `ensure_admin_user()` method. Stable function boundary.
- **Validation Notes:** Confirmed. The `IntegrityError` catch mitigates but doesn't eliminate the race.

### V-006 — `dashboard_access.permission` Server Default Drift

- **Severity:** HIGH
- **Status:** VALIDATED
- **Source:** db/audit_report_02 (drift #2, #11), db/audit_report_03
- **Affected Modules:** `src/mkobi/db/models/access.py`, `alembic/versions/7130ecb0388c_true_initial_migration.py`
- **Affected Symbols:** `DashboardAccess.permission`, `server_default=text("'view'")`
- **Description:** ORM declares `server_default=text("'view'")` but the migration and real DB have no DEFAULT clause. Raw SQL INSERTs without `permission` will fail with NOT NULL violation.
- **Impact:** Inconsistency between ORM expectation and DB reality. Any bypass of ORM (manual SQL, data migration, bulk insert) will fail.
- **Root Cause:** ORM model was updated with `server_default` but migration was never regenerated.
- **Recommendation:** Add `DEFAULT 'view'::dashboard_permission_level` via `ALTER TABLE` in a new Alembic migration, OR remove `server_default` from ORM.
- **Rollout Considerations:** Must choose one direction (add DB default or remove ORM default). Adding DB default is safer for backward compatibility.
- **Semantic Anchor:** `DashboardAccess` model class, `permission` field. Stable.
- **Validation Notes:** Confirmed by DB audit. Live DB has `column_default = NULL` for this column.

---

## 3. MEDIUM Findings (Validated: 18)

### V-007 — Admin Log Endpoint Missing Date Filtering and Pagination

- **Severity:** MEDIUM
- **Status:** VALIDATED
- **Source:** audit_report_001 (#3), audit_report_003 (#5)
- **Affected Modules:** `src/mkobi/api/routes/admin.py`
- **Affected Symbols:** `GET /api/v1/admin/logs` endpoint handler
- **Description:** `GET /api/v1/admin/logs` lacks `date_from`/`date_to` query parameters and pagination (`page`/`page_size`). SPEC requires both.
- **Impact:** Admins cannot filter logs by date range or paginate results. Large log tables will return all rows.
- **Root Cause:** Endpoint was implemented without full SPEC compliance.
- **Recommendation:** Add `date_from`, `date_to`, `page`, `page_size` query params. Implement offset/limit in the repository. Return `{items, total, page, page_size}`.
- **Rollout Considerations:** API change — frontend `LogViewer.tsx` already has date filter UI (per ts_map.yaml), so the frontend expects this. Backend must be updated to match.
- **Semantic Anchor:** Admin logs route handler in `admin.py`. Stable route definition.
- **Validation Notes:** Frontend `LogViewer.tsx` already has date picker and filter controls, confirming the frontend is waiting for backend support.

### V-008 — `check_dashboard_access()` Missing Admin Bypass

- **Severity:** MEDIUM
- **Status:** VALIDATED
- **Source:** audit_report_001 (#4), audit_report_003 (#6)
- **Affected Modules:** `src/mkobi/core/permissions.py`
- **Affected Symbols:** `check_dashboard_access()`
- **Description:** `check_dashboard_access()` does not implement admin bypass. It always checks the `dashboard_access` table, even for admins. Admin bypass is only in `DashboardService.get_dashboard()`, not in the standalone function used by `data.py` and `dashboards.py`.
- **Impact:** Admins without explicit `dashboard_access` entries will be denied access to data and filter/graph endpoints.
- **Root Cause:** Inconsistent access control — admin bypass was added to one path but not the other.
- **Recommendation:** Add admin role check at the start of `check_dashboard_access()`: if user role is `UserRole.ADMIN`, return `True` immediately.
- **Rollout Considerations:** Safe. No dependencies. Must be applied before admin users try to access data endpoints without explicit access grants.
- **Semantic Anchor:** `check_dashboard_access()` function. Stable function boundary.
- **Validation Notes:** Confirmed. The function checks `dashboard_access` table unconditionally.

### V-009 — Service Methods Create Own DB Sessions (Transaction Boundary Issues)

- **Severity:** MEDIUM
- **Status:** VALIDATED
- **Source:** audit_report_002 (S5, S6), audit_report_003 (#8, #9)
- **Affected Modules:** `src/mkobi/services/auth_service.py`, `src/mkobi/services/data_service.py`
- **Affected Symbols:** Multiple service methods with `db=None` fallback
- **Description:** Multiple service methods (`register_user`, `login_user`, `get_user_by_id`, `process_upload`, etc.) create their own DB session when called without `db` parameter. This breaks atomicity when a caller starts a transaction and calls multiple service methods.
- **Impact:** Partial commits can leave DB in inconsistent state. File saved to disk but processing log not committed, or vice versa.
- **Root Cause:** Service methods have a "create your own session" fallback for convenience, but this bypasses the caller's transaction boundary.
- **Recommendation:** Remove the "create your own session" fallback. Require `db` as a mandatory parameter. Let FastAPI dependency injection handle session lifecycle.
- **Rollout Considerations:** This is a refactoring that touches many service methods. Must update all callers. High risk of breaking changes if not done carefully. Should be done as a single coordinated change.
- **Semantic Anchor:** Service `__init__` methods and method signatures. Stable but requires coordinated changes.
- **Validation Notes:** Confirmed. Both `AuthService` and `DataService` have this pattern. This is a systemic issue that affects transaction safety.

### V-010 — `_token_cache` Unbounded Memory Growth

- **Severity:** MEDIUM
- **Status:** VALIDATED
- **Source:** audit_report_001 (#5), audit_report_003 (#7)
- **Affected Modules:** `src/mkobi/core/permissions.py`
- **Affected Symbols:** `_token_cache`, `_decode_token_cached()`
- **Description:** `_token_cache` is a module-level `dict` with no size bounds or periodic cleanup. In long-running processes with many unique tokens, this dict grows unbounded.
- **Impact:** Memory leak in long-running processes.
- **Root Cause:** Simple dict used for TTL-based caching without LRU eviction.
- **Recommendation:** Add a maximum cache size (e.g., 1000 entries) with LRU eviction, or use `functools.lru_cache` with `maxsize`.
- **Rollout Considerations:** Safe. No dependencies. Drop-in replacement.
- **Semantic Anchor:** `_token_cache` module-level variable. Stable.
- **Validation Notes:** Confirmed. Module-level dict with no eviction mechanism.

### V-011 — Security Operations Logged at INFO Level

- **Severity:** MEDIUM
- **Status:** VALIDATED
- **Source:** audit_report_002 (S14, S15), audit_report_003 (#17, #18)
- **Affected Modules:** `src/mkobi/core/security.py`
- **Affected Symbols:** `hash_password()`, `verify_password()`, `decode_token()`
- **Description:** `hash_password()` logs "Password hashed successfully" at INFO level on every hash operation. `verify_password()` and `decode_token()` log success at INFO level.
- **Impact:** In production, this creates noise in logs and could leak timing information about user creation/registration events.
- **Root Cause:** Overly verbose logging for security-relevant operations.
- **Recommendation:** Change to DEBUG level. Never log security-relevant operations at INFO.
- **Rollout Considerations:** Safe. No dependencies. Simple log level change.
- **Semantic Anchor:** Individual logging calls in security functions. Stable.
- **Validation Notes:** Confirmed. Multiple INFO-level log statements in security functions.

### V-012 — Database URL with Credentials Logged at INFO Level

- **Severity:** MEDIUM
- **Status:** VALIDATED
- **Source:** audit_report_002 (S16), audit_report_003 (#19), db/audit_findings_01
- **Affected Modules:** `src/mkobi/db/starter.py`
- **Affected Symbols:** `_apply_migrations()`
- **Description:** `_apply_migrations()` logs the full database URL: `logger.info("Running migrations for %s...", db_url)`. The URL may contain credentials.
- **Impact:** Credentials leaked to logs.
- **Root Cause:** Unsanitized URL logging.
- **Recommendation:** Use `url.render_as_string(hide_password=True)` or strip the password before logging.
- **Rollout Considerations:** Safe. No dependencies. Simple string formatting change.
- **Semantic Anchor:** Logging statement in `_apply_migrations()`. Stable.
- **Validation Notes:** Confirmed. Raw URL is logged directly.

### V-013 — Data Worker Stale `PROCESSING` State

- **Severity:** MEDIUM
- **Status:** VALIDATED
- **Source:** audit_report_002 (S7), audit_report_003 (#10)
- **Affected Modules:** `src/mkobi/workers/data_worker.py`
- **Affected Symbols:** `_update_processing_log_status()`
- **Description:** `_update_processing_log_status()` creates a new session for each status update. If the worker crashes between file processing and final status update, the log can be left in `PROCESSING` state forever.
- **Impact:** Stale `PROCESSING` entries that never resolve to `SUCCESS` or `FAILED`. Admin cannot distinguish "still running" from "crashed".
- **Root Cause:** No heartbeat mechanism or timeout-based cleanup for stale processing logs.
- **Recommendation:** Add a heartbeat mechanism or a timeout-based cleanup job that marks stale `PROCESSING` entries as `FAILED`.
- **Rollout Considerations:** Requires a background job or scheduled task. Moderate complexity.
- **Semantic Anchor:** `_update_processing_log_status()` function. Stable.
- **Validation Notes:** Confirmed. No heartbeat or timeout mechanism exists.

### V-014 — `_store_aggregates()` Nested Transaction Risk

- **Severity:** MEDIUM
- **Status:** VALIDATED
- **Source:** audit_report_002 (S8), audit_report_003 (#11)
- **Affected Modules:** `src/mkobi/workers/data_worker.py`
- **Affected Symbols:** `_store_aggregates()`
- **Description:** `_store_aggregates()` uses `session.begin()` which creates a nested transaction. If `save_aggregates` fails after partial writes, the rollback may not clean up all data depending on savepoint behavior.
- **Impact:** Partial data writes — some aggregates saved, others not, with no clear indication of inconsistency.
- **Root Cause:** Nested transaction (savepoint) used instead of single top-level transaction.
- **Recommendation:** Use a single top-level transaction. Consider `TRUNCATE + INSERT` for overwrite mode instead of `DELETE + INSERT` for atomicity.
- **Rollout Considerations:** Must be careful with transaction scope changes. Test thoroughly with concurrent uploads.
- **Semantic Anchor:** `_store_aggregates()` function. Stable.
- **Validation Notes:** Confirmed. Nested transaction pattern detected.

### V-015 — Invalid Dimensions Fallback Uses `df.columns[:3]` Silently

- **Severity:** MEDIUM
- **Status:** VALIDATED
- **Source:** audit_report_002 (S9), audit_report_003 (#12)
- **Affected Modules:** `src/mkobi/workers/data_worker.py`
- **Affected Symbols:** Dimension fallback logic in processing
- **Description:** When `graph.dimensions` is empty or invalid, the fallback uses `df.columns[:3]` as dimensions. This is implicit and may produce incorrect results silently.
- **Impact:** Wrong data aggregation — first 3 columns may not be the intended dimensions. No error is raised.
- **Root Cause:** Silent fallback instead of explicit error.
- **Recommendation:** Raise an explicit error when dimensions are invalid, or require dimensions to be explicitly set before processing.
- **Rollout Considerations:** Safe. Failing fast is better than silent incorrect results.
- **Semantic Anchor:** Dimension processing logic in data worker. Stable.
- **Validation Notes:** Confirmed. Silent fallback to first 3 columns.

### V-016 — `get_config()` Global Singleton Not Reloadable

- **Severity:** MEDIUM
- **Status:** VALIDATED
- **Source:** audit_report_002 (S10), audit_report_003 (#13)
- **Affected Modules:** `src/mkobi/config.py`
- **Affected Symbols:** `get_config()`, `_settings`
- **Description:** `get_config()` uses a global singleton (`_settings`). Once initialized, the config cannot be reloaded without restarting the process.
- **Impact:** Cannot change configuration at runtime. Testing with different configs requires monkeypatching the global.
- **Root Cause:** Module-level singleton pattern without reload mechanism.
- **Recommendation:** Consider a reload mechanism or use `lru_cache` with a clear invalidation path for tests.
- **Rollout Considerations:** Low risk. Testing improvement, not production-critical.
- **Semantic Anchor:** `get_config()` function. Stable.
- **Validation Notes:** Confirmed. Module-level `_settings` variable.

### V-017 — `validate_admin_credentials()` Weak Value Check Bypass

- **Severity:** MEDIUM
- **Status:** VALIDATED
- **Source:** audit_report_002 (S11), audit_report_003 (#14)
- **Affected Modules:** `src/mkobi/config.py`
- **Affected Symbols:** `validate_admin_credentials()`
- **Description:** `validate_admin_credentials()` checks `admin_username == "admin"` but the default admin email in `.env` is `admin@example.com`. The validator won't catch if someone sets `ADMIN_USERNAME=admin` in production.
- **Impact:** The check is bypassed by using `admin` as username instead of `admin@example.com`.
- **Root Cause:** Incomplete weak-value detection.
- **Recommendation:** Check against a set of known-weak values: `{"admin", "administrator", "root"}`.
- **Rollout Considerations:** Safe. No dependencies.
- **Semantic Anchor:** `validate_admin_credentials()` validator. Stable.
- **Validation Notes:** Confirmed. Single-value check is insufficient.

### V-018 — No Migration Job in Docker Compose Production

- **Severity:** MEDIUM
- **Status:** VALIDATED
- **Source:** audit_report_002 (S13), audit_report_003 (#16)
- **Affected Modules:** `docker-compose.yml`
- **Affected Symbols:** `AUTO_MIGRATE: "false"` config
- **Description:** Production compose sets `AUTO_MIGRATE: "false"` but provides no alternative migration mechanism. If someone deploys without running migrations, the app will fail to start.
- **Impact:** Deployment failure if migrations are not run manually.
- **Root Cause:** No migration job or init container defined in compose.
- **Recommendation:** Add a migration service/job that runs before the app starts, or use an init container pattern.
- **Rollout Considerations:** Deployment infrastructure change. Must be coordinated with CI/CD pipeline.
- **Semantic Anchor:** `docker-compose.yml` app service definition. Stable.
- **Validation Notes:** Confirmed. No migration job in any compose file.

### V-019 — Login Rate Limiting Email Enumeration Side-Channel

- **Severity:** MEDIUM
- **Status:** VALIDATED
- **Source:** audit_report_002 (S17), audit_report_003 (#20)
- **Affected Modules:** `src/mkobi/api/routes/auth.py`
- **Affected Symbols:** Login rate limiter key construction
- **Description:** Login rate limiting uses `f"login:{email}"` as the key. An attacker can enumerate emails by observing which keys are rate-limited.
- **Impact:** Email enumeration via rate limit side-channel.
- **Root Cause:** Per-email rate limiting leaks existence information.
- **Recommendation:** Use IP-based rate limiting for login, or a combination of IP + email with a cooldown period.
- **Rollout Considerations:** Security improvement. Must maintain effective rate limiting while preventing enumeration.
- **Semantic Anchor:** Login route handler, rate limiter key construction. Stable.
- **Validation Notes:** Confirmed. Email is used directly in rate limit key.

### V-020 — `recreate_test_database()` Hardcodes `bidb_test`

- **Severity:** MEDIUM
- **Status:** VALIDATED
- **Source:** audit_report_002 (S1), db/audit_findings_01
- **Affected Modules:** `src/mkobi/db/starter.py`
- **Affected Symbols:** `recreate_test_database()`
- **Description:** `recreate_test_database()` hardcodes `bidb_test` database name in raw SQL. Breaks if test DB name differs from `bidb_test`.
- **Impact:** Not configurable. Breaks in environments with different test DB naming.
- **Root Cause:** Hardcoded string instead of parsing from URL.
- **Recommendation:** Parse DB name from URL using `sqlalchemy.engine.url.make_url()`.
- **Rollout Considerations:** Safe. No dependencies. Test-only code.
- **Semantic Anchor:** `recreate_test_database()` method. Stable.
- **Validation Notes:** Confirmed. Hardcoded `bidb_test` in SQL strings.

### V-021 — SQL Injection Risk in Test DB Name

- **Severity:** MEDIUM
- **Status:** VALIDATED
- **Source:** audit_report_002 (S2), db/audit_findings_01
- **Affected Modules:** `src/mkobi/db/starter.py`
- **Affected Symbols:** `recreate_test_database()`
- **Description:** `DROP DATABASE IF EXISTS {db_name}` uses f-string interpolation with no SQL injection protection.
- **Impact:** Even for internal tooling, this is a bad practice. If DB name ever comes from user input, it's exploitable.
- **Root Cause:** F-string interpolation in SQL.
- **Recommendation:** Use `psycopg2.sql.Identifier` or at minimum validate the name against `^[a-zA-Z0-9_]+$`.
- **Rollout Considerations:** Safe. Test-only code.
- **Semantic Anchor:** `recreate_test_database()` method. Stable.
- **Validation Notes:** Confirmed. F-string used for database name in SQL.

### V-022 — `bind_filter_endpoint` / `unbind_filter_endpoint` Error Handling Gap

- **Severity:** MEDIUM
- **Status:** VALIDATED
- **Source:** audit_report_001 (#6)
- **Affected Modules:** `src/mkobi/api/routes/dashboards.py`
- **Affected Symbols:** `bind_filter_endpoint`, `unbind_filter_endpoint`
- **Description:** `bind_filter_endpoint` and `unbind_filter_endpoint` handle `IntegrityError` and generic `Exception` with `db.rollback()` but the `filter_repo.get()` call is outside the `try` block.
- **Impact:** If `filter_repo.get()` raises an exception, it won't be caught by the error handlers, resulting in a 500 without proper logging.
- **Root Cause:** Incomplete try block coverage.
- **Recommendation:** Move the `filter_repo.get()` call inside the `try` block.
- **Rollout Considerations:** Safe. No dependencies. Simple code move.
- **Semantic Anchor:** Route handler functions. Stable.
- **Validation Notes:** Confirmed. Repository call outside try block.

### V-023 — `create_db.sql` Diverges from Actual Schema (6+ Places)

- **Severity:** MEDIUM
- **Status:** VALIDATED
- **Source:** db/audit_report_02 (drift #1, #3, #5, #6, #7, #8, #9), db/audit_report_03
- **Affected Modules:** `create_db.sql`
- **Affected Symbols:** Multiple table definitions
- **Description:** `create_db.sql` diverges from the actual schema in 6+ ways: `dashboards.config` NULLABLE mismatch, `users.updated_at` trigger redundancy, `processing_logs.status` ENUM value mismatch, `processing_logs.dashboard_id` FK behavior mismatch, `users.email` type mismatch, `uuid-ossp` extension not needed.
- **Impact:** Cannot be used to bootstrap new environments. Misleading to developers.
- **Root Cause:** `create_db.sql` was not kept in sync with Alembic migrations.
- **Recommendation:** Delete `create_db.sql` or replace with `pg_dump --schema-only` output. A divergent init script is worse than no init script.
- **Rollout Considerations:** Documentation/infrastructure change. No code impact.
- **Semantic Anchor:** `create_db.sql` file. Stable file path.
- **Validation Notes:** Confirmed by detailed drift analysis. 12 specific drift items documented.

### V-024 — Application Uses Superuser `postgres` Role

- **Severity:** MEDIUM
- **Status:** VALIDATED
- **Source:** db/audit_report_02 (architectural problem #5)
- **Affected Modules:** Database configuration, `docker-compose.yml`
- **Affected Symbols:** `postgres` role, `DATABASE_URL`
- **Description:** Application uses superuser `postgres` role for all operations (runtime + migrations). Any SQL injection or application bug can execute superuser operations.
- **Impact:** Violates least-privilege principle. Superuser can drop databases, modify system catalogs, bypass RLS.
- **Root Cause:** Default PostgreSQL setup uses the `postgres` superuser.
- **Recommendation:** Create a dedicated application role with limited privileges (CONNECT, SELECT, INSERT, UPDATE, DELETE on specific tables only).
- **Rollout Considerations:** Infrastructure change. Must update connection strings and run GRANT statements.
- **Semantic Anchor:** Database role configuration. Stable.
- **Validation Notes:** Confirmed. Only `postgres` role exists in the database.

### V-025 — `cleanup_old_logs()` Never Called

- **Severity:** MEDIUM
- **Status:** VALIDATED
- **Source:** audit_report_002 (S20), db/audit_findings_01, db/audit_report_02 (technical debt)
- **Affected Modules:** `src/mkobi/db/starter.py`
- **Affected Symbols:** `cleanup_old_logs()`
- **Description:** `cleanup_old_logs()` is defined but never called from `startup()` or anywhere else.
- **Impact:** Dead code. Log table grows unbounded.
- **Root Cause:** Method was implemented but never wired into the lifecycle.
- **Recommendation:** Either call it from startup on a schedule, or remove it.
- **Rollout Considerations:** Safe. No dependencies.
- **Semantic Anchor:** `cleanup_old_logs()` method. Stable.
- **Validation Notes:** Confirmed. Method exists but is never invoked.

### V-026 — `get_db()` Duplicated in `permissions.py` and `deps.py`

- **Severity:** MEDIUM
- **Status:** VALIDATED
- **Source:** audit_report_002 (S21)
- **Affected Modules:** `src/mkobi/api/deps.py`, `src/mkobi/core/permissions.py`
- **Affected Symbols:** `get_db()` in both modules
- **Description:** `get_db()` in `permissions.py` and `get_db_dependency()` in `deps.py` are nearly identical — both create a session context manager.
- **Impact:** Duplicated logic. If session management changes, both need updating.
- **Root Cause:** Copy-paste instead of shared dependency.
- **Recommendation:** Consolidate into a single dependency. Import from `deps.py` in `permissions.py`.
- **Rollout Considerations:** Safe refactoring. No external dependencies.
- **Semantic Anchor:** `get_db()` functions. Stable.
- **Validation Notes:** Confirmed. Two nearly identical session context managers.

---

## 4. LOW Findings (Validated: 13)

### V-027 — Index Naming Inconsistency for `dashboard_filters`

- **Severity:** LOW
- **Status:** VALIDATED
- **Source:** audit_report_001 (#8), audit_report_003 (#21)
- **Affected Modules:** `alembic/versions/7130ecb0388c_true_initial_migration.py`
- **Affected Symbols:** `idx_dashboard_filters_dashboard_filter`
- **Description:** Index name `idx_dashboard_filters_dashboard_filter` does not follow the naming convention of other indexes.
- **Impact:** Inconsistent naming makes index management harder.
- **Root Cause:** Naming convention not enforced.
- **Recommendation:** Rename to follow convention or accept as-is (low impact).
- **Rollout Considerations:** Low risk. Index rename is non-breaking.
- **Semantic Anchor:** Migration file, index creation. Stable.
- **Validation Notes:** Minor inconsistency. Current names are functional.

### V-028 — Registration Approval Uses 400 Instead of 409

- **Severity:** LOW
- **Status:** VALIDATED
- **Source:** audit_report_001 (#9, #10), audit_report_003 (#22, #23)
- **Affected Modules:** `src/mkobi/api/routes/admin.py`
- **Affected Symbols:** Registration approval and rejection endpoints
- **Description:** Registration request approval and rejection use `HTTP_400_BAD_REQUEST` for already-processed requests. SPEC says `409 Conflict`.
- **Impact:** Incorrect HTTP status code for conflict scenarios.
- **Root Cause:** Wrong status code used.
- **Recommendation:** Change to `status.HTTP_409_CONFLICT`.
- **Rollout Considerations:** Safe. No dependencies. API contract fix.
- **Semantic Anchor:** Admin route handlers. Stable.
- **Validation Notes:** Confirmed. Two endpoints affected.

### V-029 — `update_dashboard()` Complex Parameter Handling

- **Severity:** LOW
- **Status:** VALIDATED
- **Source:** audit_report_001 (#11), audit_report_003 (#24)
- **Affected Modules:** `src/mkobi/services/dashboard_service.py`
- **Affected Symbols:** `update_dashboard()`
- **Description:** `update_dashboard()` has complex nested `if/else` for handling `config` parameter with `update_data` being either `dict` or Pydantic model.
- **Impact:** Code is harder to follow than necessary.
- **Root Cause:** Parameter normalization not done at method start.
- **Recommendation:** Refactor to normalize `update_data` to a dict at the start of the method.
- **Rollout Considerations:** Internal refactoring. No external dependencies.
- **Semantic Anchor:** `update_dashboard()` method. Stable.
- **Validation Notes:** Code quality issue, not a bug.

### V-030 — File Content Read Entirely into Memory

- **Severity:** LOW
- **Status:** VALIDATED
- **Source:** audit_report_001 (#12), audit_report_003 (#25)
- **Affected Modules:** `src/mkobi/api/routes/upload.py`
- **Affected Symbols:** Upload handler, `await file.read()`
- **Description:** File content is read entirely into memory (`await file.read()`). For very large files (up to 100MB limit), this creates memory pressure.
- **Impact:** Large uploads consume significant memory.
- **Root Cause:** Simple but memory-intensive file handling.
- **Recommendation:** Consider streaming the file write using `aiofiles` with chunked reads.
- **Rollout Considerations:** Moderate complexity. Must handle partial writes correctly.
- **Semantic Anchor:** Upload route handler. Stable.
- **Validation Notes:** Confirmed. Full file read into memory.

### V-031 — `_parse_formula` Cannot Handle Numeric Literals

- **Severity:** LOW
- **Status:** VALIDATED
- **Source:** audit_report_001 (#13), audit_report_003 (#26)
- **Affected Modules:** `src/mkobi/data/processing/transformations.py`
- **Affected Symbols:** `_parse_formula()`
- **Description:** `_parse_formula` treats all tokens as column references via `pl.col()`. Numeric literals like `"revenue * 100"` will look for a column named `"100"`.
- **Impact:** Users cannot use numeric constants in custom metric formulas.
- **Root Cause:** Parser doesn't distinguish numeric literals from column names.
- **Recommendation:** Document this limitation clearly in the API docs, or enhance the parser to distinguish numeric literals from column names.
- **Rollout Considerations:** Documentation is safe. Parser enhancement is moderate complexity.
- **Semantic Anchor:** `_parse_formula()` function. Stable.
- **Validation Notes:** Confirmed. All tokens passed to `pl.col()`.

### V-032 — `get_aggregated_data()` Called Without `db` Parameter

- **Severity:** LOW
- **Status:** VALIDATED
- **Source:** audit_report_001 (#14), audit_report_003 (#27)
- **Affected Modules:** `src/mkobi/api/routes/data.py`
- **Affected Symbols:** `get_aggregated_data()` route handler
- **Description:** `get_aggregated_data()` is called without passing `db` parameter, so it creates its own session internally. The access check and data query run in separate sessions.
- **Impact:** Small window for race conditions between access check and data query.
- **Root Cause:** Session not passed from route to service.
- **Recommendation:** Pass the `db` session from the route to the service method.
- **Rollout Considerations:** Safe. No dependencies.
- **Semantic Anchor:** Data route handler. Stable.
- **Validation Notes:** Confirmed. Service creates own session.

### V-033 — Plotly Type Mismatch in Frontend

- **Severity:** LOW
- **Status:** VALIDATED
- **Source:** audit_report_001 (#15), audit_report_003 (#28)
- **Affected Modules:** `frontend/src/shared/types/api.types.ts`
- **Affected Symbols:** `Data` and `Layout` imports from `plotly.js`
- **Description:** `Data` and `Layout` are imported from `plotly.js` but the actual chart components use `react-plotly.js`.
- **Impact:** Type mismatch — `plotly.js` `Data` type may not perfectly align with `react-plotly.js` props.
- **Root Cause:** Wrong import source for types.
- **Recommendation:** Verify type compatibility or use types from `react-plotly.js` if available.
- **Rollout Considerations:** Low risk. Type-level fix.
- **Semantic Anchor:** Type import statement. Stable.
- **Validation Notes:** Confirmed. Import from `plotly.js` instead of `react-plotly.js`.

### V-034 — Dead Code: `_test_engine`, `migration_engine`, `cleanup_old_logs()`

- **Severity:** LOW
- **Status:** VALIDATED
- **Source:** audit_report_002 (S18, S19, S20), audit_report_003 (#29, #30, #31), db/audit_findings_01
- **Affected Modules:** `src/mkobi/db/starter.py`
- **Affected Symbols:** `self._test_engine`, `migration_engine`, `cleanup_old_logs()`
- **Description:** `self._test_engine` is declared but never assigned or used. `migration_engine` is created but never used. `cleanup_old_logs()` is defined but never called.
- **Impact:** Dead state/code — confusing for maintainers.
- **Root Cause:** Incomplete cleanup during development.
- **Recommendation:** Remove unused field, unused engine creation, and either call or remove `cleanup_old_logs()`.
- **Rollout Considerations:** Safe. Pure cleanup.
- **Semantic Anchor:** `DatabaseStarter` class. Stable.
- **Validation Notes:** Confirmed. Three separate dead code items.

### V-035 — Redundant `updated_at` Mechanisms (Trigger + onupdate)

- **Severity:** LOW
- **Status:** VALIDATED
- **Source:** db/audit_report_02 (drift #3, #5), db/audit_report_003
- **Affected Modules:** `src/mkobi/db/models/user.py`, `dashboard.py`, `layout.py`, `processing_configs.py`
- **Affected Symbols:** `onupdate=text("now()")` in ORM + DB triggers
- **Description:** Both trigger and `onupdate` set `updated_at` redundantly for `users`, `layouts`, `dashboards`, and `processing_configs`.
- **Impact:** No runtime failure, but confusing — which mechanism is authoritative?
- **Root Cause:** ORM `onupdate` and DB triggers both added for same purpose.
- **Recommendation:** Choose one mechanism. Recommended: keep triggers (DB-level, works for raw SQL), remove `onupdate=text("now()")` from ORM.
- **Rollout Considerations:** Must ensure triggers exist before removing `onupdate`. Test thoroughly.
- **Semantic Anchor:** ORM model definitions. Stable.
- **Validation Notes:** Confirmed. Both mechanisms exist for 4 tables.

### V-036 — `bidb_schema.sql` Encoding Corruption

- **Severity:** LOW
- **Status:** VALIDATED
- **Source:** db/audit_report_02 (technical debt), db/audit_report_03
- **Affected Modules:** `bidb_schema.sql`
- **Description:** File has UTF-16 BOM and binary prefix. Cannot be parsed as valid SQL.
- **Impact:** Cannot be used for schema reference.
- **Root Cause:** Encoding corruption during file creation.
- **Recommendation:** Remove or regenerate with `pg_dump --schema-only --no-owner`.
- **Rollout Considerations:** Safe. File removal only.
- **Semantic Anchor:** `bidb_schema.sql` file. Stable file path.
- **Validation Notes:** Confirmed. File is unreadable.

### V-037 — `get_session` Backwards Compatibility Import with `noqa`

- **Severity:** LOW
- **Status:** VALIDATED
- **Source:** audit_report_002 (S22), audit_report_003 (#33)
- **Affected Modules:** `src/mkobi/api/deps.py`
- **Affected Symbols:** `get_session` import with `# noqa: F401`
- **Description:** `get_session` is imported with `# noqa: F401` for backwards compatibility, but it's unclear who imports it from here.
- **Impact:** Implicit coupling.
- **Root Cause:** Legacy import pattern.
- **Recommendation:** Add a deprecation comment with a timeline for removal.
- **Rollout Considerations:** Safe. Comment-only change.
- **Semantic Anchor:** Import statement. Stable.
- **Validation Notes:** Confirmed. `noqa` suppression without clear purpose.

### V-038 — Compatibility Classmethods Duplicate Instance Methods in Storage Manager

- **Severity:** LOW
- **Status:** VALIDATED
- **Source:** audit_report_002 (S24), audit_report_003 (#35)
- **Affected Modules:** `src/mkobi/data/storage/manager.py`
- **Affected Symbols:** `save_aggregated_data`, `clear_graph_data_compat`, `clear_dashboard_data_compat`
- **Description:** Compatibility classmethods duplicate instance methods. Two ways to do the same thing.
- **Impact:** Code duplication.
- **Root Cause:** Backwards compatibility during refactoring.
- **Recommendation:** Deprecate the classmethods. Migrate callers to use instance methods.
- **Rollout Considerations:** Safe. Gradual migration.
- **Semantic Anchor:** `StorageManager` class. Stable.
- **Validation Notes:** Confirmed. Classmethods duplicate instance methods.

---

## 5. REJECTED Findings (9)

| # | Original ID | Reason for Rejection |
|---|-------------|---------------------|
| R-001 | audit_report_001 #7 (admin bypass StrEnum comparison) | MERGED into V-008. The StrEnum comparison works correctly; the real issue is the missing admin bypass in `check_dashboard_access()`, which is covered by V-008. The explicit type handling recommendation is a code quality improvement, not a separate finding. |
| R-002 | audit_report_002 S23 (admin bypass type flow clarity) | MERGED into V-008. Same root cause — the admin bypass inconsistency. The type flow clarity is a secondary concern. |
| R-003 | audit_report_002 S12 (Dockerfile dev stage runs as root) | REJECTED as low-value for current stage. This is a development environment concern, not a production security issue. The dev stage is explicitly for development. |
| R-004 | audit_report_003 #34 (admin bypass type annotation) | MERGED into V-008. Same root cause. |
| R-005 | audit_report_002 S25 (mypy overrides suppress type errors) | REJECTED as systemic issue requiring dedicated effort. Not a single fix — requires gradual removal across many files. Should be tracked as a separate technical debt item, not an audit finding. |
| R-006 | db/audit_findings_01 (startup does too much / orchestration) | REJECTED as architectural opinion, not a bug. The `DatabaseStarter` pattern is acceptable for the current MVP stage. Refactoring into separate services is a medium-term improvement, not a finding. |
| R-007 | db/audit_findings_01 (no startup observability / state machine) | REJECTED as overengineering for current stage. The linear startup script is simple and maintainable. A state machine adds complexity without proportional value at this stage. |
| R-008 | db/audit_findings_01 (no timeout for startup DB checks) | REJECTED as low-value. The `SELECT 1` check is unlikely to hang in practice. If it does, the process will fail anyway. Adding timeout adds complexity for minimal benefit. |
| R-009 | db/audit_findings_01 (create_async_engine without pooling config) | REJECTED as already addressed. The production engine configuration includes `pool_pre_ping=True` and `pool_recycle=300` in the session module. |

---

## 6. Test Infrastructure Findings (Summary)

The test audit reports (`.ai/audit/tests/audit_report_001.md` and `audit_report_1.md`) identify systemic issues with the test suite. These are not individual code findings but rather structural problems that affect the reliability of the test suite as a safety net for refactoring.

### Key Test Issues (Not individually actionable, but important context):

1. **Overmocking in Service Tests** — `test_auth_service.py`, `test_data_service.py`, `test_graph_service.py` use heavy mocking that tests mock setup rather than real business logic. This means refactoring production code may not be caught by tests.

2. **Test Pyramid Imbalance** — 90%+ of tests are API/integration tests with heavy mocking. No true unit tests exist for pure functions (formula parser, aggregation logic).

3. **Missing Coverage Areas:**
   - Health endpoints (`/health`, `/health/detailed`)
   - Data retrieval endpoints (`/data/aggregated`)
   - Task queue / background worker execution
   - Registration approval flow
   - Rate limiting behavior (429 responses)
   - File cleanup on success/failure
   - Custom metrics formula parser
   - Processing log lifecycle state transitions

4. **Blocked Refactorings** — The overmocked service tests block refactoring of `AuthService`, `DataService`, and `GraphService`. Tests must be rewritten before these services can be safely refactored.

**Validation Note:** The test infrastructure issues are real and important, but they are not code defects. They are preconditions for safe refactoring. The service transaction boundary findings (V-009) should not be acted on until the corresponding test files are rewritten.

---

## 7. Dependency & Rollout Safety Analysis

### 7.1 Dependency Graph

```
V-001 (drop trigger) ──→ V-003 (add created_at) ──→ V-006 (align server_default)
V-002 (add index) ──→ independent
V-004 (migration lock) ──→ V-018 (migration job in compose)
V-005 (admin UPSERT) ──→ independent
V-007 (log pagination) ──→ frontend already expects it
V-008 (admin bypass) ──→ independent
V-009 (transaction boundaries) ──→ requires test rewrite first
V-010 (token cache bounds) ──→ independent
V-011-V-012 (log levels) ──→ independent, can be batched
V-013-V-015 (data worker) ──→ independent
V-023 (create_db.sql) ──→ independent
V-024 (postgres role) ──→ independent
V-035 (redundant onupdate) ──→ must verify triggers exist first
```

### 7.2 Safe Parallel Execution Groups

**Group A (Immediate — no dependencies):**
- V-001: Drop `update_graphs_updated_at` trigger
- V-002: Add composite index
- V-005: Admin UPSERT fix
- V-010: Token cache bounds
- V-011: Security log levels
- V-012: Sanitized DB URL logging
- V-027: Index naming (or defer)

**Group B (Schema changes — require migrations):**
- V-003: Add `created_at` to `graphs`
- V-006: Align `dashboard_access.permission` default
- V-035: Remove redundant `onupdate` (after trigger verification)

**Group C (API changes — require frontend coordination):**
- V-007: Admin log pagination (frontend already has UI)
- V-028: Status code 400 → 409

**Group D (Infrastructure — require deployment coordination):**
- V-004: Migration advisory lock
- V-018: Migration job in Docker Compose
- V-024: Dedicated DB role

**Group E (Refactoring — require test rewrite first):**
- V-009: Transaction boundary fixes
- V-026: Consolidate `get_db()`

### 7.3 Rollout Safety Verdict

**SAFE to proceed immediately:** Groups A and C (8 findings)
**SAFE with migration:** Group B (3 findings)
**SAFE with deployment coordination:** Group D (3 findings)
**BLOCKED by test rewrite:** Group E (2 findings)

---

## 8. Semantic Targeting Stability Analysis

All validated findings use stable semantic anchors:
- **Migration files** are immutable once applied — anchors in migration code are stable
- **Function/method boundaries** are stable targets for modification
- **Route definitions** are stable API contracts
- **Module-level variables** are stable targets

**No findings rely on line numbers or fragile insertion points.** All recommendations target:
- Function calls (stable)
- Decorators (stable)
- Route definitions (stable)
- Class definitions (stable)
- Migration operations (stable)

---

## 9. Execution Applicability Analysis

### Findings that may become stale if other changes occur:
- **V-001** (trigger drop): Will become irrelevant if `updated_at` column is added to `graphs` in V-003. However, the trigger should be dropped regardless since it references a non-existent column.
- **V-009** (transaction boundaries): If services are refactored to use a unit-of-work pattern, this finding becomes partially obsolete.
- **V-026** (consolidate `get_db()`): If `permissions.py` is refactored to use FastAPI DI, this becomes obsolete.

### Findings that are stable regardless of other changes:
- All schema/index findings (V-001-V-003, V-006, V-027)
- All security findings (V-010-V-012, V-019)
- All deployment findings (V-004, V-018, V-024)

---

## 10. Architectural Consistency Warnings

1. **Clean Architecture Compliance:** The codebase generally follows Clean Architecture well. The main violation is V-009 (service methods creating own sessions), which breaks the layer boundary by bypassing the caller's transaction scope.

2. **Frontend-Backend Contract:** V-007 (log pagination) indicates the frontend has outpaced the backend. The `LogViewer.tsx` component already has date filter UI that the backend doesn't support. This is a contract mismatch.

3. **Database Schema Drift:** V-023 (`create_db.sql` divergence) indicates a documentation/schema management problem. The Alembic migrations are the source of truth, but the existence of a divergent `create_db.sql` creates confusion.

4. **Test Suite Reliability:** The overmocking issue means the test suite cannot be fully trusted as a safety net for refactoring. Findings that require service-layer changes (V-009) should have tests rewritten first.

---

## 11. Consolidated Fix Priority

### Immediate (before production deployment):
1. V-001 — Drop `update_graphs_updated_at` trigger (CRITICAL)
2. V-002 — Add composite index (HIGH)
3. V-003 — Add `created_at` to `graphs` (HIGH)
4. V-005 — Fix admin user race condition (HIGH)
5. V-012 — Sanitize DB URL logging (MEDIUM)

### Short-term (next sprint):
6. V-006 — Align `dashboard_access.permission` default (HIGH)
7. V-007 — Add log date filtering and pagination (MEDIUM)
8. V-008 — Add admin bypass to `check_dashboard_access()` (MEDIUM)
9. V-010 — Bound token cache (MEDIUM)
10. V-011 — Fix security log levels (MEDIUM)
11. V-028 — Fix status codes 400→409 (LOW)

### Medium-term (planned iteration):
12. V-004 — Add migration advisory lock (HIGH)
13. V-018 — Add migration job to Docker Compose (MEDIUM)
14. V-013 — Add heartbeat/timeout for stale processing logs (MEDIUM)
15. V-014 — Fix nested transaction in `_store_aggregates()` (MEDIUM)
16. V-015 — Raise error for invalid dimensions (MEDIUM)
17. V-023 — Delete or regenerate `create_db.sql` (MEDIUM)
18. V-024 — Create dedicated DB role (MEDIUM)

### After test rewrite:
19. V-009 — Fix service transaction boundaries (MEDIUM)
20. V-026 — Consolidate `get_db()` (MEDIUM)

### Low priority / technical debt:
21. V-016 through V-038 — Various code quality improvements

---

**End of Validated Findings Document**
