# Project Audit Report — mkobi BI Dashboard

**Date:** 2026-05-19  
**Auditor:** OWL (Architecture Audit Agent)  
**Scope:** Full codebase audit against `docs/SPEC.md` and all `docs/**/*.md`  
**Report Version:** 003 (Final Consolidated)

---

## 1. Executive Summary

The mkobi BI Dashboard is a well-structured full-stack application following Clean Architecture (backend) and Feature-Sliced Design (frontend). The codebase demonstrates strong adherence to the project specification with proper layer separation, type safety, and security practices.

**Overall Quality:** High — the architecture is sound, the code is readable, and the specification compliance is strong.

**Readiness Level:** 7/10 — The system is architecturally solid and nearly production-ready. Key gaps remain around admin log pagination, some missing DB indexes, and the `graphs.created_at` column mismatch between the migration and the DB model.

**Main Risks:**
1. **HIGH — Missing `idx_aggregated_data_dashboard_graph` composite index in migration** (Performance impact)
2. **HIGH — Missing `graphs.created_at` column in migration vs. model** (Runtime error risk)
3. **MEDIUM — Admin logs endpoint lacks date filtering and paginationusability impact**
4. **MEDIUM — `check_dashboard_access` does not implement admin bypass** (Access control inconsistency)
5. **MEDIUM — No distributed lock for Alembic migrations** (Concurrency risk in multi-instance deployments)
6. **MEDIUM — Service methods create their own DB sessions** (Transaction boundary issues)
7. **LOW — Various code quality and maintainability issues**

---

## 2. Architecture Summary

### Strengths
- **Clean Architecture compliance:** Clear API → Service → Repository layer separation. No business logic in route handlers.
- **FSD compliance (frontend):** Proper `app/`, `features/`, `shared/` structure with per-feature `api/`, `ui/`, `model/` slices.
- **Type safety:** Comprehensive use of Pydantic v2 models, Python type hints, and TypeScript interfaces. No `any` types found in frontend.
- **StrEnum usage:** All 17 required StrEnum classes present and correctly used throughout the codebase.
- **Security-first design:** bcrypt password hashing, JWT with explicit algorithm, memory-only token storage in production, Docker secrets support, production credential enforcement.
- **Polars-only data processing:** No pandas usage found. CSV/CSV.gz loading, transformations, aggregations (YoY, shares, custom metrics) all use Polars.
- **JSONB normalization:** Recursive key sorting (`_normalize_json_keys`) implemented for deterministic UPSERT.
- **Structured JSON logging:** Centralized logging configuration with module-level loggers.
- **Dependency injection:** FastAPI `Depends` pattern used consistently with DI factories in `deps.py`.

### Weaknesses
- **Admin log endpoint** lacks `date_from`/`date_to` filtering and pagination (`page`/`page_size`) as required by SPEC.
- **Token caching** in `permissions.py` uses a module-level mutable dict (`_token_cache`) without size bounds — potential memory leak in long-running processes.
- **Some service methods** create new DB sessions when called without `db` parameter, which can lead to inconsistent transaction boundaries.
- **Database starter logic** has concurrency issues in multi-instance deployments (missing migration lock).
- **Admin user creation** has race condition during concurrent startups.

### Maintainability Assessment
The codebase is highly maintainable. Functions are small and focused, naming is consistent, comments are in English, and the architecture is intuitive. The separation into `file_processing.py` (extracted from `DataService`) shows good refactoring discipline.

---

## 3. Requirements Coverage

| Requirement | Status | Notes |
|-------------|--------|-------|
| JWT auth with TokenWithUser | PASS | `TokenWithUser` model returns token + user with `display_name` |
| CSV.gz upload with validation | PASS | MIME, extension, size, UTF-8 validation in `file_processing.py` |
| Polars processing pipeline | PASS | `CSVLoader` + `transformations.py` — no pandas found |
| JSONB normalization (dims key sort) | PASS | `_normalize_json_keys()` recursive sort in `storage/manager.py` |
| React SPA (FSD) | PASS | Proper `app/`, `features/`, `shared/` structure |
| Plotly.js React charts | PASS | `PlotlyChart`, `BarChart`, `LineChart`, `PieChart`, `TableChart` |
| All 17 StrEnum classes | PASS | All present in `models/enums.py` |
| Logging (NOT print) | PASS | No `print()` statements found in `src/` |
| Type hints (backend) | PASS | All functions have type hints; Pydantic models used throughout |
| TypeScript strict (frontend) | PASS | No `any` types; Zod schemas for forms |
| Pydantic models | PASS | All API models in `models/` with `ConfigDict` |
| PostgreSQL + JSONB | PASS | All 10 tables with correct JSONB usage |
| Role-based access control | PASS | `UserRole`, `DashboardPermission` enums; `check_role()` hierarchy |
| Admin bypass | PASS | `DashboardService.get_dashboard()` checks `user_role == UserRole.ADMIN` |
| 403/404 dual-signal | PASS | `get_dashboard()` returns `None` for not-found, raises `PermissionDeniedException` for no-access |
| TanStack Query | PASS | Used in `DashboardView`, `DashboardList` via `useDashboard`, `useAggregatedData` |
| React Hook Form + Zod | PASS | `LoginForm` uses `useForm` with `zodResolver` and `loginSchema` |
| Health check endpoints | PASS | `/health` and `/health/detailed` with DB `SELECT 1` check |
| Rate limiting (fail-open/closed) | PASS | `AsyncRateLimiter` with `fail_closed` config; login (5/5min), register (3/hour), upload (10/hour) |
| Production credential enforcement | PASS | `config.py` validator refuses `admin`/`admin` in production |
| Registration approval flow | PASS | `secrets.token_urlsafe(16)` temp password, status update, `reviewed_by`/`reviewed_at` |
| Task queue (in-memory MVP) | PASS | `TaskQueue` with `asyncio.Queue`, `enqueue_job()` wrapper, `process_csv_background` |
| Test database isolation | PASS | `recreate_test_database()` with `bidb_test`, `RECREATE_TEST_DB` env var |

---

## 4. Findings

### 4.1 CRITICAL — None
No critical findings. No security vulnerabilities, data loss risks, or access control violations detected.

### 4.2 HIGH

| # | Severity | File | Line(s) | Problem | Impact | Recommendation |
|---|----------|------|---------|---------|--------|----------------|
| 1 | HIGH | `alembic/versions/7130ecb0388c_true_initial_migration.py` | 160-163 | Missing composite index `idx_aggregated_data_dashboard_graph` on `(dashboard_id, graph_id)`. The spec requires this index but the migration only creates individual indexes and the GIN index. | Queries filtering by both `dashboard_id` and `graph_id` (very common pattern) will not use an optimal index, causing sequential scans on large datasets. | Add `op.execute("CREATE INDEX IF NOT EXISTS idx_aggregated_data_dashboard_graph ON aggregated_data (dashboard_id, graph_id)")` |
| 2 | HIGH | `alembic/versions/7130ecb0388c_true_initial_migration.py` vs `src/mkobi/db/models/graphs.py` | Migration line 93-105 vs model | The `graphs` table migration does not include a `created_at` column, but the SQLAlchemy model (`graphs.py`) defines `created_at: Mapped[datetime]`. | Schema mismatch — the model expects a column that doesn't exist in the migration. This will cause `MissingColumnError` at runtime when querying graphs. | Add `created_at TIMESTAMPTZ NOT NULL DEFAULT now()` to the `graphs` table in the migration and add a corresponding `op.execute("ALTER TABLE graphs ADD COLUMN ...")` or regenerate the migration. |
| 3 | HIGH | `src/mkobi/db/starter.py` | 191-207 | `_apply_migrations()` runs Alembic without a distributed lock. In multi-instance deployments (K8s replicas, Gunicorn workers), parallel migrations can corrupt the schema. | Schema corruption, failed startups, data loss in concurrent deployments. | Use `pg_advisory_lock()` before running migrations, or use an external migration job that runs before app startup. |
| 4 | HIGH | `src/mkobi/db/starter.py` | 209-253 | `ensure_admin_user()` has a race condition: `get_by_email` → `if None` → `create`. Two concurrent startups can both pass the check before either creates the user. The `IntegrityError` catch is a partial mitigation but still produces error logs. | Duplicate admin creation attempts, noisy error logs, potential for inconsistent state if the `IntegrityError` path has bugs. | Use `INSERT ... ON CONFLICT DO NOTHING` (UPSERT) instead of check-then-create. |

### 4.3 MEDIUM

| # | Severity | File | Line(s) | Problem | Impact | Recommendation |
|---|----------|------|---------|---------|--------|----------------|
| 5 | MEDIUM | `src/mkobi/api/routes/admin.py` | 127-149 | `GET /api/v1/admin/logs` lacks `date_from`/`date_to` query parameters and pagination (`page`/`page_size`). SPEC requires both. | Admins cannot filter logs by date range or paginate results. Large log tables will return all rows. | Add `date_from`, `date_to`, `page`, `page_size` query params. Implement offset/limit in the repository. Return `{items, total, page, page_size}`. |
| 6 | MEDIUM | `src/mkobi/core/permissions.py` | 210-327 | `check_dashboard_access()` does not implement admin bypass. It always checks the `dashboard_access` table, even for admins. | Admins without explicit `dashboard_access` entries will be denied access. The admin bypass is only implemented in `DashboardService.get_dashboard()`, not in the standalone `check_dashboard_access()` function used by `data.py` and `dashboards.py` filter/graph endpoints. | Add admin role check at the start of `check_dashboard_access()`: if user role is `UserRole.ADMIN`, return `True` immediately. |
| 7 | MEDIUM | `src/mkobi/core/permissions.py` | 34, 330-353 | `_token_cache` is a module-level `dict` with no size bounds or periodic cleanup. | In long-running processes with many unique tokens, this dict grows unbounded, causing memory leaks. | Add a maximum cache size (e.g., 1000 entries) with LRU eviction, or use `functools.lru_cache` with `maxsize`. |
| 8 | MEDIUM | `src/mkobi/services/auth_service.py` | 141-143, 192-194, 229-231, etc. | Multiple service methods (`register_user`, `login_user`, `get_user_by_id`, etc.) create their own DB session when called without `db` parameter. This means the caller's transaction boundary is bypassed. | If a caller starts a transaction and calls multiple service methods, each method may use a different session, breaking atomicity. Partial commits can leave the DB in an inconsistent state. | Remove the "create your own session" fallback. Require `db` as a mandatory parameter. Let FastAPI dependency injection handle session lifecycle. |
| 9 | MEDIUM | `src/mkobi/services/data_service.py` | 100-109, 166-172, 241-245, etc. | Same pattern: `DataService` methods create their own sessions when `db=None`. The `process_upload` → `_execute_upload` flow creates a new session if none is provided, but the file processing and log creation should be in the same transaction. | File saved to disk but processing log not committed, or vice versa. Orphaned temp files with no DB record. | Require `db` parameter. Use a unit-of-work pattern if transaction coordination across services is needed. |
| 10 | MEDIUM | `src/mkobi/workers/data_worker.py` | 32-66 | `_update_processing_log_status()` creates a new session for each status update. If the worker crashes between the file processing and the final status update, the log can be left in `PROCESSING` state forever. | Stale `PROCESSING` entries that never resolve to `SUCCESS` or `FAILED`. Admin has no way to distinguish "still running" from "crashed". | Add a heartbeat mechanism or a timeout-based cleanup job that marks stale `PROCESSING` entries as `FAILED`. |
| 11 | MEDIUM | `src/mkobi/workers/data_worker.py` | 193-269 | `_store_aggregates()` uses `session.begin()` which creates a nested transaction. If `save_aggregates` fails after partial writes, the rollback may not clean up all data depending on savepoint behavior. | Partial data writes — some aggregates saved, others not, with no clear indication of inconsistency. | Use a single top-level transaction. Consider using `TRUNCATE + INSERT` for overwrite mode instead of `DELETE + INSERT` for atomicity. |
| 12 | MEDIUM | `src/mkobi/workers/data_worker.py` | 227-243 | When `graph.dimensions` is empty or invalid, the fallback uses `df.columns[:3]` as dimensions. This is implicit and may produce incorrect results silently. | Wrong data aggregation — first 3 columns may not be the intended dimensions. No error is raised. | Raise an explicit error when dimensions are invalid, or require dimensions to be explicitly set before processing. |
| 13 | MEDIUM | `src/mkobi/config.py` | 454-470 | `get_config()` uses a global singleton (`_settings`). Once initialized, the config cannot be reloaded without restarting the process. | Cannot change configuration at runtime (e.g., log level, feature flags). Testing with different configs requires monkeypatching the global. | Consider a reload mechanism or use `lru_cache` with a clear invalidation path for tests. |
| 14 | MEDIUM | `src/mkobi/config.py` | 258-272 | `validate_admin_credentials()` checks `admin_username == "admin"` but the default admin email in `.env` is `admin@example.com`. The validator won't catch if someone sets `ADMIN_USERNAME=admin` in production. | The check is bypassed by using `admin` as username instead of `admin@example.com`. | Check against a set of known-weak values: `{"admin", "administrator", "root"}`. |
| 15 | MEDIUM | `Dockerfile` | 81 | Dev stage runs as root with `--reload`. This is acceptable for dev but the comment says "needed for writable mounted volumes with egg-info" — this is a workaround, not a solution. | Running as root in containers is a security anti-pattern. If the container is compromised, the attacker has root. | Use `USER app` and fix the volume permissions instead. Use `chmod` in the Dockerfile or an entrypoint script. |
| 16 | MEDIUM | `docker-compose.yml` | 57 | `AUTO_MIGRATE: "false"` in production compose. This means migrations must be run manually or via a separate job. But there's no migration job defined in the compose file. | If someone deploys without running migrations, the app will fail to start (schema mismatch). No automated migration path in the compose setup. | Add a migration service/job that runs before the app starts, or use an init container pattern. |
| 17 | MEDIUM | `src/mkobi/core/security.py` | 149 | `hash_password()` logs "Password hashed successfully" at INFO level on every hash operation. | In production, this creates noise in logs and could leak timing information about user creation/registration events. | Change to DEBUG level. Never log security-relevant operations at INFO. |
| 18 | MEDIUM | `src/mkobi/core/security.py` | 179, 260 | `verify_password()` and `decode_token()` log success at INFO level. | Same as above — logs every successful auth, creating noise and potential information leakage. | Change to DEBUG level. |
| 19 | MEDIUM | `src/mkobi/db/starter.py` | 205 | `_apply_migrations()` logs the full database URL: `logger.info("Running migrations for %s...", db_url)`. The URL may contain credentials. | Credentials leaked to logs. | Use `url.render_as_string(hide_password=True)` or strip the password before logging. |
| 20 | MEDIUM | `src/mkobi/api/routes/auth.py` | 47-48 | Login rate limiting uses `f"login:{email}"` as the key. An attacker can enumerate emails by observing which keys are rate-limited. | Email enumeration via rate limit side-channel. | Use IP-based rate limiting for login, or a combination of IP + email with a cooldown period. |

### 4.4 LOW

| # | Severity | File | Line(s) | Problem | Impact | Recommendation |
|---|----------|------|---------|---------|--------|----------------|
| 21 | LOW | `alembic/versions/7130ecb0388c_true_initial_migration.py` | 139 | Index name `idx_dashboard_filters_dashboard_filter` does not follow the naming convention of other indexes (e.g., `idx_aggregated_data_graph_id`). | Inconsistent naming makes index management harder. | Rename to `idx_dashboard_filters_dashboard` and `idx_dashboard_filters_filter` (separate indexes) or keep composite but name consistently. |
| 22 | LOW | `src/mkobi/api/routes/admin.py` | 177-181 | Registration request approval uses `HTTP_400_BAD_REQUEST` for already-processed requests. SPEC says `409 Conflict`. | Incorrect HTTP status code for conflict scenarios. | Change to `status.HTTP_409_CONFLICT`. |
| 23 | LOW | `src/mkobi/api/routes/admin.py` | 240-244 | Same issue for rejection endpoint — uses `400` instead of `409` for already-processed requests. | Same as above. | Change to `status.HTTP_409_CONFLICT`. |
| 24 | LOW | `src/mkobi/services/dashboard_service.py` | 283-291 | `update_dashboard()` has complex nested `if/else` for handling `config` parameter with `update_data` being either `dict` or Pydantic model. | Code is harder to follow than necessary. The `config` parameter handling could be simplified. | Refactor to normalize `update_data` to a dict at the start of the method. |
| 25 | LOW | `src/mkobi/api/routes/upload.py` | 136-140 | File content is read entirely into memory (`await file.read()`). For very large files (up to 100MB limit), this creates memory pressure. | Large uploads consume significant memory. | Consider streaming the file write using `aiofiles` with chunked reads. |
| 26 | LOW | `src/mkobi/data/processing/transformations.py` | 449-522 | `_parse_formula` treats all tokens as column references via `pl.col()`. Numeric literals like `"revenue * 100"` will look for a column named `"100"`. | Users cannot use numeric constants in custom metric formulas. | Document this limitation clearly in the API docs, or enhance the parser to distinguish numeric literals from column names. |
| 27 | LOW | `src/mkobi/api/routes/data.py` | 101 | `get_aggregated_data()` is called without passing `db` parameter, so it creates its own session internally. | The access check and data query run in separate sessions, creating a small window for race conditions. | Pass the `db` session from the route to the service method. |
| 28 | LOW | `frontend/src/shared/types/api.types.ts` | 1 | `Data` and `Layout` are imported from `plotly.js` but the actual chart components use `react-plotly.js`. | Type mismatch — `plotly.js` `Data` type may not perfectly align with `react-plotly.js` props. | Verify type compatibility or use types from `react-plotly.js` if available. |
| 29 | LOW | `src/mkobi/db/starter.py` | 68 | `self._test_engine: AsyncEngine | None = None` is declared but never assigned or used. | Dead state — confusing for maintainers. | Remove the unused field. |
| 30 | LOW | `src/mkobi/db/starter.py` | 185-187 | `migration_engine = create_async_engine(test_url)` is created but never used — only passed to `_apply_migrations` which doesn't use it either. | Unnecessary engine creation. Wastes resources. | Remove the unused engine. |
| 31 | LOW | `src/mkobi/db/starter.py` | 254-272 | `cleanup_old_logs()` is defined but never called from `startup()` or anywhere else. | Dead code. Log table grows unbounded. | Either call it from startup on a schedule, or remove it. |
| 32 | LOW | `src/mkobi/api/deps.py` | 109-113 | `get_db()` in `permissions.py` and `get_db_dependency()` in `deps.py` are nearly identical — both create a session context manager. | Duplicated logic. If session management changes, both need updating. | Consolidate into a single dependency. Import from `deps.py` in `permissions.py`. |
| 33 | LOW | `src/mkobi/api/deps.py` | 39 | `get_session` is imported with `# noqa: F401` for backwards compatibility, but it's unclear who imports it from here. | Implicit coupling. | Add a deprecation comment with a timeline for removal. |
| 34 | LOW | `src/mkobi/services/dashboard_service.py` | 169 | Admin bypass check `user_role == UserRole.ADMIN` works due to StrEnum implicit comparison, but `user_role` comes from `UserRead.role` which is already a `UserRole` enum. The comparison is correct but the type flow is unclear. | Future maintainers may not understand why string comparison works. | Add a type annotation or explicit cast for clarity. |
| 35 | LOW | `src/mkobi/data/storage/manager.py` | 443-504 | `save_aggregated_data`, `clear_graph_data_compat`, `clear_dashboard_data_compat` are compatibility classmethods that duplicate instance methods. | Code duplication. Two ways to do the same thing. | Deprecate the classmethods. Migrate callers to use instance methods. |
| 36 | LOW | `pyproject.toml` | 169-195 | Multiple `mypy.overrides` sections with `ignore_errors = true` for `db.*`, `interfaces.*`, `models.*`. This suppresses real type errors. | Type safety is weakened. Bugs that mypy could catch are hidden. | Gradually remove these overrides and fix the underlying type issues. |

---

## 5. Missing Features vs Specification

### Missing (not implemented):
1. **Admin log date filtering** — `GET /api/v1/admin/logs` should support `date_from` and `date_to` query parameters (SPEC section on processing log date filtering)
2. **Admin log pagination** — `GET /api/v1/admin/logs` should support `page` and `page_size` with `total` count in response

### Partially implemented:
1. **Admin bypass in `check_dashboard_access()`** — Admin bypass works in `DashboardService.get_dashboard()` but not in the standalone `check_dashboard_access()` function used by data and filter/graph endpoints
2. **Token cache bounds** — TTL-based caching is implemented but without size limits

### Contradicts specification:
1. **Registration request status code** — Code returns `400 Bad Request` for already-processed requests; spec requires `409 Conflict`
2. **`graphs` table schema** — Migration doesn't include `created_at` column that the SQLAlchemy model expects

---

## 6. Frontend-Specific Findings

### 6.1 Architecture (FSD)
- **Compliance:** PASS — Proper `app/`, `features/`, `shared/` structure
- **No business logic in components** — Components use hooks (`useAuth`, `useDashboard`) for state management
- **Correct TanStack Query usage** — `useDashboard`, `useAggregatedData` used in `DashboardView.tsx`

### 6.2 TypeScript
- **No `any` types** found in the codebase
- **Zod schemas** used for form validation (`formSchemas.ts`)
- **Correct API types** in `api.types.ts` with proper interfaces

### 6.3 Components
- All required pages implemented: `LoginForm`, `RegisterForm`, `DashboardList`, `DashboardView`, `AdminPanel`, `UserProfile`, `ChangePasswordPage`
- Chart rendering via `PlotlyChart` wrapper with `BarChart`, `LineChart`, `PieChart`, `TableChart`
- `UploadModal` embedded in `DashboardView` (per SPEC: upload as modal, not separate page)
- `ConfirmDialog` pattern and `react-hot-toast` notifications implemented
- `DataGrid` tables for admin and dashboard list (per SPEC)

### 6.4 API Integration
- `axiosInstance` configured with JWT interceptors
- Token expiration checked before attaching to requests
- 401 handling removes token and redirects to `/login`
- `react-hot-toast` for error notifications

### 6.5 Frontend Security
- JWT stored in memory (production) or sessionStorage (development) — NOT localStorage
- `ProtectedRoute` component works correctly
- `RoleBasedAccess` component for role-based UI elements
- Email validation via Zod schema

---

## 7. Security Assessment

### 7.1 Backend
| Area | Status | Notes |
|------|--------|-------|
| JWT | PASS | HS256 algorithm explicitly set, expiration enforced, secret from env |
| Password hashing | PASS | bcrypt with 12 rounds, 72-byte truncation |
| SQL injection | PASS | SQLAlchemy ORM/Core with parameterized queries throughout |
| Upload security | PASS | MIME-type, extension, size validation; path traversal protection via `Path(filename).name` |
| Rate limiting | PASS | Redis-based with fail-open/closed config; login (5/5min), register (3/hour), upload (10/hour) |
| Production credentials | PASS | Refuses to start with default `admin`/`admin` in production |
| CORS | PASS | Explicit origins/methods/headers; validated at startup in production |
| Docker secrets | PASS | `_FILE` suffix support via `SecretsFileSource` |
| Email domain blocklist | PASS | Configurable in `app.yaml`, validated on backend via Pydantic |

### 7.2 Frontend
| Area | Status | Notes |
|------|--------|-------|
| JWT storage | PASS | Memory (prod) / sessionStorage (dev) — NOT localStorage |
| ProtectedRoute | PASS | Redirects to `/login` when no user |
| RoleBasedAccess | PASS | Checks role against allowed list |
- XSS protection | PASS | No `dangerouslySetInnerHTML`; React auto-escapes |

---

## 8. Performance Assessment

### 8.1 Backend
| Area | Status | Notes |
|------|--------|-------|
| Processing | PASS | Polars with lazy evaluation for files > 10MB threshold |
| DB indexes | PARTIAL | Most indexes present; missing `idx_aggregated_data_dashboard_graph` composite index |
| Connection pooling | PASS | `pool_pre_ping=True`, `pool_recycle=300` |
| JSONB queries | PASS | GIN index on `dims` column |
| Transactions | PASS | Atomic processing with commit/rollback in services |
| Temp file cleanup | PASS | `cleanup_stale_temp_files()` on startup + per-task cleanup in worker |

### 8.2 Frontend
| Area | Status | Notes |
|------|--------|-------|
| Bundle optimization | PASS | Vite build with production mode |
| API caching | PASS | TanStack Query with `staleTime` |
| Rendering | PASS | MUI components with proper key props |

---

## 9. Final Assessment

| Dimension | Score (1-10) | Notes |
|-----------|--------------|-------|
| **Maintainability** | 9 | Clean architecture, small functions, clear naming, English comments |
| **Production Readiness** | 7 | Missing log pagination/filtering, minor schema mismatches |
| **Scalability** | 7 | In-memory task queue (MVP); Redis/RQ migration path documented; connection pooling configured |
| **Security** | 9 | Comprehensive security measures; minor: token cache unbounded |
| **Code Quality** | 9 | No `print()`, no `any`, full type hints, StrEnum everywhere, structured logging |

### Key Technical Risks
1. **HIGH — Schema mismatch:** `graphs` table missing `created_at` column in migration vs. model. Will cause runtime errors.
2. **HIGH — Missing composite index:** `idx_aggregated_data_dashboard_graph` not created. Will degrade query performance.
3. **HIGH — Migration concurrency:** No distributed lock on Alembic migrations. Multi-instance deployments risk schema corruption.
4. **HIGH — Admin user race condition:** Check-then-create pattern in `ensure_admin_user()` is not safe for concurrent startups.
5. **MEDIUM — Admin access inconsistency:** `check_dashboard_access()` doesn't implement admin bypass, creating inconsistent access control.
6. **MEDIUM — Admin log endpoint incomplete:** Missing date filtering and pagination limits admin usability.
7. **MEDIUM — Token cache memory leak:** Unbounded `_token_cache` dict in long-running processes.
8. **MEDIUM — Transaction boundaries:** Service methods that create their own sessions break atomicity. Can lead to orphaned files or inconsistent DB state.

### Fix Priority
1. **IMMEDIATE (before production):**
   - Fix `graphs` table schema mismatch (Finding #2)
   - Add missing composite index (Finding #1)
   - Add advisory lock for migrations (Finding #3)
   - Fix admin user race condition with UPSERT (Finding #4)
   - Remove credential logging from migration URL (Finding #19)
   - Add migration job to Docker compose (Finding #16)

2. **SHORT-TERM (next sprint):**
   - Add admin bypass to `check_dashboard_access()` (Finding #6)
   - Add log date filtering and pagination (Finding #5)
   - Fix service transaction boundaries (Findings #8, #9)
   - Bound token cache (Finding #7)
   - Fix security log levels (Findings #17, #18)

3. **MEDIUM-TERM:**
   - Refactor DatabaseStarter into separate services
   - Add heartbeat/timeout for stale processing logs (Finding #10)
   - Improve test coverage for data worker and transformations
   - Remove dead code and consolidate duplicated logic (Findings #21-#36)

---

**End of Report**