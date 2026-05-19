# Project Audit Report — mkobi BI Dashboard

**Date:** 2026-05-19
**Auditor:** OWL (Architecture Audit Agent)
**Scope:** Full codebase audit against `docs/SPEC.md` and all `docs/**/*.md`
**Report Version:** 001

---

## 1. Executive Summary

The mkobi BI Dashboard is a well-structured full-stack application following Clean Architecture (backend) and Feature-Sliced Design (frontend). The codebase demonstrates strong adherence to the project specification with proper layer separation, type safety, and security practices.

**Overall Quality:** High — the architecture is sound, the code is readable, and the specification compliance is strong.

**Readiness Level:** 7/10 — The system is architecturally solid and nearly production-ready. Key gaps remain around admin log pagination, some missing DB indexes, and the `graphs.created_at` column mismatch between the migration and the DB model.

**Main Risks:**
1. Missing `idx_aggregated_data_dashboard_graph` composite index in migration (HIGH)
2. Missing `graphs.created_at` column in migration vs. model (HIGH)
3. Admin logs endpoint lacks date filtering and pagination (MEDIUM)
4. `check_dashboard_access` does not implement admin bypass (MEDIUM)
5. `dashboard_filters` unique index name mismatch (LOW)

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

### Maintainability Assessment
The codebase is highly maintainable. Functions are small and focused, naming is consistent, comments are in English, and the architecture is intuitive. The separation into `file_processing.py` (extracted from `DataService`) shows good refactoring discipline.

---

## 3. Requirements Coverage

| Requirement | Status | Notes |
|---|---|---|
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
|---|---|---|---|---|---|---|
| 1 | HIGH | `alembic/versions/7130ecb0388c_true_initial_migration.py` | 160-163 | Missing composite index `idx_aggregated_data_dashboard_graph` on `(dashboard_id, graph_id)`. The spec requires this index but the migration only creates individual indexes and the GIN index. | Queries filtering by both `dashboard_id` and `graph_id` (very common pattern) will not use an optimal index, causing sequential scans on large datasets. | Add `op.execute("CREATE INDEX IF NOT EXISTS idx_aggregated_data_dashboard_graph ON aggregated_data (dashboard_id, graph_id)")` |
| 2 | HIGH | `alembic/versions/7130ecb0388c_true_initial_migration.py` vs `src/mkobi/db/models/graphs.py` | Migration line 93-105 vs model | The `graphs` table migration does not include a `created_at` column, but the SQLAlchemy model (`graphs.py`) defines `created_at: Mapped[datetime]`. | Schema mismatch — the model expects a column that doesn't exist in the migration. This will cause `MissingColumnError` at runtime when querying graphs. | Add `created_at TIMESTAMPTZ NOT NULL DEFAULT now()` to the `graphs` table in the migration and add a corresponding `op.execute("ALTER TABLE graphs ADD COLUMN ...")` or regenerate the migration. |

### 4.3 MEDIUM

| # | Severity | File | Line(s) | Problem | Impact | Recommendation |
|---|---|---|---|---|---|---|
| 3 | MEDIUM | `src/mkobi/api/routes/admin.py` | 127-149 | `GET /api/v1/admin/logs` lacks `date_from`/`date_to` query parameters and pagination (`page`/`page_size`). SPEC requires both. | Admins cannot filter logs by date range or paginate results. Large log tables will return all rows. | Add `date_from`, `date_to`, `page`, `page_size` query params. Implement offset/limit in the repository. Return `{items, total, page, page_size}`. |
| 4 | MEDIUM | `src/mkobi/core/permissions.py` | 210-327 | `check_dashboard_access()` does not implement admin bypass. It always checks the `dashboard_access` table, even for admins. | Admins without explicit `dashboard_access` entries will be denied access. The admin bypass is only implemented in `DashboardService.get_dashboard()`, not in the standalone `check_dashboard_access()` function used by `data.py` and `dashboards.py` filter/graph endpoints. | Add admin role check at the start of `check_dashboard_access()`: if user role is `UserRole.ADMIN`, return `True` immediately. |
| 5 | MEDIUM | `src/mkobi/core/permissions.py` | 34, 330-353 | `_token_cache` is a module-level `dict` with no size bounds or periodic cleanup. | In long-running processes with many unique tokens, this dict grows unbounded, causing memory leaks. | Add a maximum cache size (e.g., 1000 entries) with LRU eviction, or use `functools.lru_cache` with `maxsize`. |
| 6 | MEDIUM | `src/mkobi/api/routes/dashboards.py` | 471-540, 543-612 | `bind_filter_endpoint` and `unbind_filter_endpoint` handle `IntegrityError` and generic `Exception` with `db.rollback()` but the `filter_repo.get()` call at line 493 is outside the `try` block. | If `filter_repo.get()` raises an exception, it won't be caught by the error handlers, resulting in a 500 without proper logging. | Move the `filter_repo.get()` call inside the `try` block. |
| 7 | MEDIUM | `src/mkobi/services/dashboard_service.py` | 169 | Admin bypass in `get_dashboard()` compares `user_role == UserRole.ADMIN` using `==` on StrEnum. While this works, the comparison is against the enum value, not the enum member. | If `user_role` is passed as a string `"admin"` (which it is from the route), the comparison `user_role == UserRole.ADMIN` works because StrEnum supports string comparison. However, this is implicit behavior. | Add explicit type handling: `if user_role and UserRole(user_role) == UserRole.ADMIN:` for clarity and safety. |

### 4.4 LOW

| # | Severity | File | Line(s) | Problem | Impact | Recommendation |
|---|---|---|---|---|---|---|
| 8 | LOW | `alembic/versions/7130ecb0388c_true_initial_migration.py` | 139 | Index name `idx_dashboard_filters_dashboard_filter` does not follow the naming convention of other indexes (e.g., `idx_aggregated_data_graph_id`). | Inconsistent naming makes index management harder. | Rename to `idx_dashboard_filters_dashboard` and `idx_dashboard_filters_filter` (separate indexes) or keep composite but name consistently. |
| 9 | LOW | `src/mkobi/api/routes/admin.py` | 177-181 | Registration request approval uses `HTTP_400_BAD_REQUEST` for already-processed requests. SPEC says `409 Conflict`. | Incorrect HTTP status code for conflict scenarios. | Change to `status.HTTP_409_CONFLICT`. |
| 10 | LOW | `src/mkobi/api/routes/admin.py` | 240-244 | Same issue for rejection endpoint — uses `400` instead of `409` for already-processed requests. | Same as above. | Change to `status.HTTP_409_CONFLICT`. |
| 11 | LOW | `src/mkobi/services/dashboard_service.py` | 283-291 | `update_dashboard()` has complex nested `if/else` for handling `config` parameter with `update_data` being either `dict` or Pydantic model. | Code is harder to follow than necessary. The `config` parameter handling could be simplified. | Refactor to normalize `update_data` to a dict at the start of the method. |
| 12 | LOW | `src/mkobi/api/routes/upload.py` | 136-140 | File content is read entirely into memory (`await file.read()`). For very large files (up to 100MB limit), this creates memory pressure. | Large uploads consume significant memory. | Consider streaming the file write using `aiofiles` with chunked reads. |
| 13 | LOW | `src/mkobi/data/processing/transformations.py` | 449-522 | `_parse_formula` treats all tokens as column references via `pl.col()`. Numeric literals like `"revenue * 100"` will look for a column named `"100"`. | Users cannot use numeric constants in custom metric formulas. | Document this limitation clearly in the API docs, or enhance the parser to distinguish numeric literals from column names. |
| 14 | LOW | `src/mkobi/api/routes/data.py` | 101 | `get_aggregated_data()` is called without passing `db` parameter, so it creates its own session internally. | The access check and data query run in separate sessions, creating a small window for race conditions. | Pass the `db` session from the route to the service method. |
| 15 | LOW | `frontend/src/shared/types/api.types.ts` | 1 | `Data` and `Layout` are imported from `plotly.js` but the actual chart components use `react-plotly.js`. | Type mismatch — `plotly.js` `Data` type may not perfectly align with `react-plotly.js` props. | Verify type compatibility or use types from `react-plotly.js` if available. |

---

## 5. File-Level Recommendations

### `src/mkobi/api/routes/admin.py`
**Problems:**
- Missing `date_from`/`date_to` filtering on logs endpoint
- Missing pagination (`page`, `page_size`, `total`) on logs endpoint
- Uses `400 Bad Request` instead of `409 Conflict` for already-processed registration requests

**Recommendations:**
- Add date range and pagination parameters to `GET /api/v1/admin/logs`
- Change status code from 400 to 409 for already-processed requests
- Add `total` count to paginated responses

### `src/mkobi/core/permissions.py`
**Problems:**
- `check_dashboard_access()` lacks admin bypass
- `_token_cache` has no size bounds

**Recommendations:**
- Add admin role check at the start of `check_dashboard_access()`
- Implement LRU eviction or max size for `_token_cache`

### `src/mkobi/services/dashboard_service.py`
**Problems:**
- Admin bypass comparison relies on implicit StrEnum string comparison
- `update_dashboard()` has complex parameter handling

**Recommendations:**
- Make admin bypass comparison explicit with `UserRole(user_role) == UserRole.ADMIN`
- Simplify `update_dashboard()` parameter normalization

### `alembic/versions/7130ecb0388c_true_initial_migration.py`
**Problems:**
- Missing `idx_aggregated_data_dashboard_graph` composite index
- Missing `created_at` column in `graphs` table
- `dashboard_filters` index naming inconsistency

**Recommendations:**
- Add the missing composite index
- Add `created_at` column to `graphs` table
- Standardize index naming

---

## 6. Missing Features vs Specification

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

## 7. Frontend-Specific Findings

### 7.1 Architecture (FSD)
- **Compliance:** PASS — Proper `app/`, `features/`, `shared/` structure
- **No business logic in components** — Components use hooks (`useAuth`, `useDashboard`) for state management
- **Correct TanStack Query usage** — `useDashboard`, `useAggregatedData` used in `DashboardView.tsx`

### 7.2 TypeScript
- **No `any` types** found in the codebase
- **Zod schemas** used for form validation (`formSchemas.ts`)
- **Correct API types** in `api.types.ts` with proper interfaces

### 7.3 Components
- All required pages implemented: `LoginForm`, `RegisterForm`, `DashboardList`, `DashboardView`, `AdminPanel`, `UserProfile`, `ChangePasswordPage`
- Chart rendering via `PlotlyChart` wrapper with `BarChart`, `LineChart`, `PieChart`, `TableChart`
- `UploadModal` embedded in `DashboardView` (per SPEC: upload as modal, not separate page)
- `ConfirmDialog` pattern and `react-hot-toast` notifications implemented
- `DataGrid` tables for admin and dashboard list (per SPEC)

### 7.4 API Integration
- `axiosInstance` configured with JWT interceptors
- Token expiration checked before attaching to requests
- 401 handling removes token and redirects to `/login`
- `react-hot-toast` for error notifications

### 7.5 Frontend Security
- JWT stored in memory (production) or sessionStorage (development) — NOT localStorage
- `ProtectedRoute` component works correctly
- `RoleBasedAccess` component for role-based UI elements
- Email validation via Zod schema

---

## 8. Security Assessment

### 8.1 Backend
| Area | Status | Notes |
|---|---|---|
| JWT | PASS | HS256 algorithm explicitly set, expiration enforced, secret from env |
| Password hashing | PASS | bcrypt with 12 rounds, 72-byte truncation |
| SQL injection | PASS | SQLAlchemy ORM/Core with parameterized queries throughout |
| Upload security | PASS | MIME-type, extension, size validation; path traversal protection via `Path(filename).name` |
| Rate limiting | PASS | Redis-based with fail-open/closed config; login (5/5min), register (3/hour), upload (10/hour) |
| Production credentials | PASS | Refuses to start with default `admin`/`admin` in production |
| CORS | PASS | Explicit origins/methods/headers; validated at startup in production |
| Docker secrets | PASS | `_FILE` suffix support via `SecretsFileSource` |
| Email domain blocklist | PASS | Configurable in `app.yaml`, validated on backend via Pydantic |

### 8.2 Frontend
| Area | Status | Notes |
|---|---|---|
| JWT storage | PASS | Memory (prod) / sessionStorage (dev) — NOT localStorage |
| ProtectedRoute | PASS | Redirects to `/login` when no user |
| RoleBasedAccess | PASS | Checks role against allowed list |
| XSS protection | PASS | No `dangerouslySetInnerHTML`; React auto-escapes |

---

## 9. Performance Assessment

### 9.1 Backend
| Area | Status | Notes |
|---|---|---|
| Processing | PASS | Polars with lazy evaluation for files > 10MB threshold |
| DB indexes | PARTIAL | Most indexes present; missing `idx_aggregated_data_dashboard_graph` composite index |
| Connection pooling | PASS | `pool_pre_ping=True`, `pool_recycle=300` |
| JSONB queries | PASS | GIN index on `dims` column |
| Transactions | PASS | Atomic processing with commit/rollback in services |
| Temp file cleanup | PASS | `cleanup_stale_temp_files()` on startup + per-task cleanup in worker |

### 9.2 Frontend
| Area | Status | Notes |
|---|---|---|
| Bundle optimization | PASS | Vite build with production mode |
| API caching | PASS | TanStack Query with `staleTime` |
| Rendering | PASS | MUI components with proper key props |

---

## 10. Final Assessment

| Dimension | Score (1-10) | Notes |
|---|---|---|
| **Maintainability** | 9 | Clean architecture, small functions, clear naming, English comments |
| **Production Readiness** | 7 | Missing log pagination/filtering, minor schema mismatches |
| **Scalability** | 7 | In-memory task queue (MVP); Redis/RQ migration path documented; connection pooling configured |
| **Security** | 9 | Comprehensive security measures; minor: token cache unbounded |
| **Code Quality** | 9 | No `print()`, no `any`, full type hints, StrEnum everywhere, structured logging |

### Key Technical Risks

1. **HIGH — Schema mismatch:** `graphs` table missing `created_at` column in migration vs. model. Will cause runtime errors.
2. **HIGH — Missing composite index:** `idx_aggregated_data_dashboard_graph` not created. Will degrade query performance.
3. **MEDIUM — Admin access inconsistency:** `check_dashboard_access()` doesn't implement admin bypass, creating inconsistent access control.
4. **MEDIUM — Admin log endpoint incomplete:** Missing date filtering and pagination limits admin usability.
5. **LOW — Token cache memory leak:** Unbounded `_token_cache` dict in long-running processes.

### Fix Priority

1. **CRITICAL** — None
2. **HIGH** — Fix `graphs` table schema mismatch and add missing composite index (Findings #1, #2)
3. **MEDIUM** — Add admin bypass to `check_dashboard_access()`, add log filtering/pagination, bound token cache (Findings #3, #4, #5)
4. **LOW** — Fix status codes, simplify code, document formula limitations (Findings #8-#15)

---

**End of Report**
