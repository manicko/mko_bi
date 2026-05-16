# mkobi BI Dashboard — Full Audit Report

**Date:** 2026-05-16
**Auditor:** OWL (Architecture Audit Agent)
**Scope:** Backend + Frontend + Data Layer + DevOps
**Spec Version:** 2.0 (2026-05-05)

---

## 1. Executive Summary

| Dimension | Score (1-10) | Notes |
|-----------|:---:|-------|
| Architecture & Separation of Concerns | 8 | Clean Architecture well-implemented; minor layer mixing in routes |
| Security & Access Control | 7 | JWT + bcrypt + RBAC present; several gaps in token handling & secrets |
| Requirements Coverage (SPEC) | ~75% | Core flows implemented; several API endpoints missing/partial |
| Code Quality & Type Safety | 8 | Strong StrEnum usage, good typing; some `any` and `cast()` overuse |
| Data Layer & Migrations | 7 | Good JSONB + GIN design; 17 migration files indicate migration drift |
| Frontend (FSD) | 7 | FSD structure present; some missing layers (entities, lib) |
| Performance & Stability | 6 | Polars + lazy loading good; in-memory task queue is a bottleneck |
| Configuration & Deployment | 8 | Multi-stage Docker, pydantic-settings, secrets support — solid |
| **Overall Readiness** | **7/10** | **Functional MVP; needs hardening for production** |

---

## 2. Architecture Compliance

### 2.1 Backend — Clean Architecture

**Structure:** `src/mkobi/` follows the prescribed layout:
- `api/` — HTTP layer (routes + deps)
- `services/` — Business logic (9 service files)
- `db/` — SQLAlchemy models + repositories
- `models/` — Pydantic schemas + enums
- `core/` — Security, permissions, logging, config
- `data/` — Loaders, processing, storage
- `interfaces/` — Abstract interfaces for DI
- `workers/` — Background tasks

**Strengths:**
- Clear API → Service → Repository separation
- Interface-based DI (`IAuthService`, `IUserRepository`, etc.)
- `BaseRepository[T]` generic class reduces duplication
- All enums use `StrEnum` as required
- Factory pattern for FastAPI app creation
- Proper lifespan management with `DatabaseStarter`

**Issues Found:**

| Severity | File | Problem | Recommendation |
|----------|------|---------|----------------|
| MEDIUM | `api/routes/dashboards.py` (lines 484-497, 520-533) | Direct repository instantiation in route handlers (`FilterRepository()`, `DashboardFilterRepository()`) bypasses DI | Use `Depends(get_filter_repository)` pattern consistently |
| MEDIUM | `api/routes/dashboards.py` (lines 658-683) | `get_graph_repository()` called directly inside route, not via Depends | Inject via `Depends(get_graph_repository)` |
| MEDIUM | `api/routes/admin.py` (lines 140, 168, 226) | `get_registration_request_repository()` called directly in route body | Use DI consistently |
| LOW | `api/routes/users.py` (line 156) | Role check done manually in route (`current_user.role != UserRole.ADMIN`) instead of using `require_admin_role` dependency | Use role dependency for consistency |
| LOW | `core/permissions.py` (lines 423-459) | Duplicate `get_current_user_dependency` — same function exists in both `core/permissions.py` and `api/deps.py` | Remove the one in `core/permissions.py`; use only `api/deps.py` |
| LOW | `core/permissions.py` (lines 501-553) | Duplicate `require_dashboard_access` — same pattern in `api/deps.py` | Consolidate into single source |

### 2.2 Frontend — Feature-Sliced Design

**Structure:** `frontend/src/` follows FSD:
- `app/` — providers + routes
- `features/` — auth, dashboards, upload, admin, users
- `shared/` — api, components, types

**Strengths:**
- Features have proper `api/`, `model/`, `ui/` slices
- Shared types with `enums.ts` matching backend StrEnum values
- `ProtectedRoute` + `RoleBasedAccess` components for access control
- Zod schemas for form validation matching backend rules
- TanStack Query for server state management
- JWT stored in memory (prod) / sessionStorage (dev) — not localStorage

**Issues Found:**

| Severity | File | Problem | Recommendation |
|----------|------|---------|----------------|
| MEDIUM | `features/auth/api/authApi.ts` (line 20) | `logoutClient()` uses `sessionStorage.removeItem` directly instead of the `removeToken()` abstraction | Use `removeToken()` from `authToken.ts` for consistency |
| LOW | `features/` | Missing `lib/` and `entities/` layers in FSD structure | Add `lib/` for feature-specific utilities; consider `entities/` for domain models |
| LOW | `shared/types/api.types.ts` (lines 157-162) | `UploadResponse` interface defined twice (lines 51-55 and 157-162) with different shapes | Remove duplicate definition |
| LOW | `app/routes.tsx` | No catch-all 404 route | Add `<Route path="*" element={<NotFound />} />` |

### 2.3 Data Processing Pipeline

**Strengths:**
- Polars used exclusively (no pandas)
- Clear pipeline: upload → validate → parse (CSVLoader) → transform → aggregate → save
- Lazy loading for large files (configurable threshold)
- `StorageManager` with proper UPSERT support via PostgreSQL `ON CONFLICT`
- Temp file cleanup on startup (`cleanup_stale_temp_files`) and after processing

**Issues Found:**

| Severity | File | Problem | Recommendation |
|----------|------|---------|----------------|
| HIGH | `workers/data_worker.py` (lines 157-160) | Temp file deletion in `process_csv_background` — if `unlink` fails, the error is silently caught but the file remains | Add retry logic or log a warning for failed deletions |
| MEDIUM | `services/data_service.py` (lines 612-626) | `cleanup_task_files` is a module-level function, not integrated with the worker's error path | Ensure cleanup is always called via `finally` block in the worker |
| MEDIUM | `data/processing/transformations.py` (lines 449-481) | `_parse_formula` uses simple regex split — doesn't handle parentheses, nested expressions, or column names with special chars | Document limitation or use a proper expression parser |

---

## 3. Security Assessment

### 3.1 JWT Authentication

**Strengths:**
- bcrypt with 12 salt rounds
- JWT with configurable expiration (default 30 min)
- UUID conversion handled in token creation
- Token expiration check on frontend via JWT payload parsing

**Issues Found:**

| Severity | File | Problem | Recommendation |
|----------|------|---------|----------------|
| **CRITICAL** | `core/security.py` (line 190-194) | JWT algorithm defaults to HS256 but `jwt.encode()` doesn't explicitly specify `algorithms` parameter — if `secret_key` is None, encoding will fail silently | Add explicit `algorithms=[get_config().jwt.algorithm]` to `jwt.encode()` call |
| HIGH | `core/security.py` (line 221-225) | `decode_token` uses `algorithms=[get_config().jwt.algorithm]` but doesn't explicitly reject `none` algorithm | Add explicit check: reject `algorithm: none` in JWT header |
| HIGH | `frontend/src/features/auth/model/authToken.ts` (line 13) | `USE_MEMORY_STORAGE = import.meta.env.PROD` — if `PROD` is undefined (e.g., misconfigured build), tokens fall back to sessionStorage | Use `import.meta.env.MODE === 'production'` or explicit env variable |
| MEDIUM | `api/routes/auth.py` (lines 211-256) | `/auth/refresh` endpoint accepts any valid JWT and issues a new one — no refresh token mechanism, no token rotation | Implement proper refresh token rotation or document this as intentional for MVP |
| MEDIUM | `core/security.py` (line 115) | Password hash decoded as `latin-1` — works but non-standard; bcrypt output is ASCII-safe | Use `utf-8` for consistency (bcrypt hashes are ASCII) |

### 3.2 Access Control

**Strengths:**
- Role hierarchy: admin > editor > viewer
- `dashboard_access` table with permission levels (view/edit/admin)
- `check_dashboard_access` used in data endpoints
- Frontend `ProtectedRoute` + `RoleBasedAccess`

**Issues Found:**

| Severity | File | Problem | Recommendation |
|----------|------|---------|----------------|
| HIGH | `api/routes/data.py` (lines 73-87) | `check_dashboard_access` in `/data/aggregated` creates its own session if `db` is None, but the route doesn't pass `db` — it relies on the function creating a new session | Pass `db` explicitly via `Depends(get_db_dependency)` to avoid duplicate sessions |
| MEDIUM | `api/routes/dashboards.py` (lines 536-557) | `get_dashboard_filters_endpoint` has no access check — any authenticated user can list filters for any dashboard | Add `require_viewer_role` or dashboard access check |
| MEDIUM | `api/routes/dashboards.py` (lines 686-723) | `get_dashboard_graphs_endpoint` has no access check — any authenticated user can list graphs for any dashboard | Add dashboard access check |
| LOW | `core/permissions.py` (lines 324-337) | `_decode_token_cached` uses `@lru_cache` — cached decoded tokens can't be invalidated if user is deactivated | Add TTL or cache invalidation on user status change |

### 3.3 Upload Security

**Strengths:**
- MIME-type validation against `MimeTypeEnum`
- File extension validation against `FileExtensionEnum`
- File size limit enforced (configurable, default 100MB)
- Rate limiting on upload endpoint (10 attempts per hour per user)
- Filename sanitized with `Path(filename).name` to prevent path traversal
- Temp files cleaned up after processing and on startup

**Issues Found:**

| Severity | File | Problem | Recommendation |
|----------|------|---------|----------------|
| HIGH | `api/routes/upload.py` (line 103) | File size check uses `file.size` which is set by FastAPI from the `Content-Length` header — can be spoofed; actual bytes read could differ | Also check `len(file_content)` after reading as a secondary guard |
| MEDIUM | `api/routes/upload.py` (line 136) | `file_content = await file.read()` reads entire file into memory — for a 100MB file this is 100MB in RAM | Consider streaming to disk first for large files |
| MEDIUM | `config.py` (line 124) | `max_file_size_mb` defaults to 100 — no upper bound validation in the settings model | Add a `Field(le=500)` constraint to prevent accidental huge limits |

### 3.4 Secrets Management

**Strengths:**
- Docker secrets support via `_FILE` env vars
- pydantic-settings with proper priority chain
- JWT secret validated on startup
- CORS origins validated in production

**Issues Found:**

| Severity | File | Problem | Recommendation |
|----------|------|---------|----------------|
| HIGH | `config.py` (lines 235-236) | `admin_password` defaults to `"admin"` — if not changed, the admin account uses a well-known password | Force explicit configuration in production; fail startup if default is used |
| MEDIUM | `docker-compose.yml` (line 43) | `DATABASE__PASSWORD` defaults to `1234` in compose — acceptable for dev but documented as production config | Add a comment warning to change defaults; consider using Docker secrets |
| LOW | `alembic.ini` (line 89) | Hardcoded database URL with plaintext password | Use environment variable substitution in alembic.ini |

---

## 4. Requirements Coverage

| SPEC Requirement | Status | Notes |
|-----------------|:------:|-------|
| **Auth Endpoints** | | |
| `POST /api/v1/auth/login` | ✅ PASS | Implemented with rate limiting |
| `POST /api/v1/auth/register-request` | ✅ PASS | Implemented with rate limiting + domain blocklist |
| `GET /api/v1/auth/me` | ✅ PASS | Returns `UserRead` |
| **Dashboard Endpoints** | | |
| `GET /api/v1/dashboards/my` | ✅ PASS | Returns user's accessible dashboards |
| `GET /api/v1/dashboards/:id` | ✅ PASS | With access check |
| `POST /api/v1/dashboards` (admin) | ✅ PASS | Admin-only |
| `PUT /api/v1/dashboards/:id` (admin) | ✅ PASS | Admin-only |
| `DELETE /api/v1/dashboards/:id` (admin) | ✅ PASS | Admin-only |
| **Data Endpoints** | | |
| `GET /api/v1/data/aggregated` | ⚠️ PARTIAL | No server-side filter implementation (filters param accepted but not applied to query) |
| `POST /api/v1/upload/:dashboard_id` | ✅ PASS | With mode, rate limiting, validation |
| **Admin Endpoints** | | |
| `GET /api/v1/admin/users` | ✅ PASS | Admin-only |
| `PATCH /api/v1/admin/users/:id/role` | ✅ PASS | Admin-only |
| `GET /api/v1/admin/registration-requests` | ✅ PASS | Admin-only |
| `POST /api/v1/admin/registration-requests/:id/approve` | ⚠️ PARTIAL | Creates user with hardcoded password `"temppass123"` — no email notification |
| `GET /api/v1/admin/logs` | ❌ MISSING | No dedicated admin logs endpoint (processing_logs routes exist but not under `/admin`) |
| **Frontend Pages** | | |
| Login Page (`/login`) | ✅ PASS | With Zod validation |
| Registration Page (`/register`) | ✅ PASS | With Zod validation |
| Dashboard List (`/dashboards`) | ✅ PASS | |
| Dashboard View (`/dashboard/:id`) | ✅ PASS | With Plotly charts |
| User Profile (`/profile`) | ✅ PASS | With delete account |
| Admin Panel (`/admin`) | ⚠️ PARTIAL | Structure exists; sub-components (UserManagement, etc.) not fully reviewed |
| Upload Page (`/dashboard/:id/upload`) | ✅ PASS | With dropzone, mode toggle |
| **Data Processing** | | |
| Polars-only processing | ✅ PASS | No pandas found |
| Upload → Parse → Transform → Aggregate → Save | ✅ PASS | Full pipeline implemented |
| YoY calculation | ✅ PASS | In `transformations.py` |
| Share calculation | ✅ PASS | In `transformations.py` |
| Custom metrics | ✅ PASS | Formula parser implemented |
| **Database** | | |
| JSONB for dims/metrics | ✅ PASS | |
| GIN index on dims | ✅ PASS | |
| All required indexes | ✅ PASS | |
| Alembic migrations | ⚠️ PARTIAL | 17 migration files — indicates migration drift; should be squashed |

---

## 5. Critical Findings

| # | Severity | Component | File | Problem | Recommendation |
|---|----------|-----------|------|---------|----------------|
| 1 | **CRITICAL** | Security | `core/security.py:190` | `jwt.encode()` doesn't explicitly specify algorithms | Add `algorithms=[...]` parameter |
| 2 | **HIGH** | Security | `config.py:236` | Default admin password is `"admin"` | Force explicit config in production |
| 3 | **HIGH** | Security | `core/security.py:221` | No explicit rejection of `none` algorithm in JWT | Add algorithm whitelist check |
| 4 | **HIGH** | Security | `api/routes/upload.py:103` | File size check relies on spoofable `Content-Length` header | Add secondary size check after reading content |
| 5 | **HIGH** | Security | `api/routes/data.py:73` | `check_dashboard_access` creates implicit session | Pass `db` explicitly via DI |
| 6 | **HIGH** | Backend | `admin.py:185` | Hardcoded temp password `"temppass123"` for approved users | Generate random password + email notification |
| 7 | **MEDIUM** | Architecture | `api/routes/dashboards.py:484` | Direct repository instantiation bypasses DI | Use `Depends()` pattern |
| 8 | **MEDIUM** | Data | `data.py:101` | `get_aggregated_data` doesn't apply filters to query | Implement server-side JSONB filtering |
| 9 | **MEDIUM** | Migrations | `alembic/versions/` | 17 migration files with overlapping changes | Squash migrations into a single initial + incremental |
| 10 | **MEDIUM** | Reliability | `data_worker.py:157` | Temp file cleanup can fail silently | Add retry + logging for failed deletions |

---

## 6. Findings & Recommendations (Detailed)

### 6.1 Backend

| Severity | Finding | Recommendation |
|----------|---------|----------------|
| HIGH | Duplicate `get_current_user_dependency` in `core/permissions.py` and `api/deps.py` | Remove from `core/permissions.py`; single source in `api/deps.py` |
| HIGH | Duplicate `require_dashboard_access` in both files | Consolidate into `api/deps.py` |
| MEDIUM | `api/routes/dashboards.py` directly instantiates `FilterRepository`, `DashboardFilterRepository`, `GraphRepository` | Use `Depends(get_*_repository)` consistently |
| MEDIUM | `api/routes/admin.py` directly instantiates `get_registration_request_repository()` | Use DI |
| MEDIUM | `api/routes/data.py` — `get_aggregated_data` accepts `filters` param but doesn't apply it to the SQL query | Implement JSONB filtering: `WHERE dims @> '{"year": "2024"}'` |
| MEDIUM | `services/data_service.py` — `get_aggregated_data` doesn't accept `db` parameter in the public method signature (only in private) | Add `db` parameter to public method for consistency |
| MEDIUM | `workers/data_worker.py` — `_store_aggregates` uses `graph_id` as string in aggregate dict but `AggregatedData.graph_id` is UUID | Ensure type consistency (cast to UUID or let SQLAlchemy handle) |
| LOW | `api/routes/users.py:156` — manual role check instead of dependency | Use `require_admin_role` |
| LOW | `models/data.py` — `ProcessingConfig` model has `yoy_config`, `share_config`, `custom_metrics` fields but they're not in the SPEC | Verify if these are needed or remove |
| LOW | `services/dashboard_service.py` — not reviewed in detail | Audit for business logic correctness |

### 6.2 Frontend

| Severity | Finding | Recommendation |
|----------|---------|----------------|
| MEDIUM | `authApi.ts:20` — `logoutClient()` bypasses `removeToken()` abstraction | Use `removeToken()` |
| MEDIUM | Missing 404/catch-all route | Add `<Route path="*" element={<NotFound />} />` |
| LOW | Duplicate `UploadResponse` interface in `api.types.ts` | Remove duplicate |
| LOW | `admin/ui/AdminPanel.tsx` — sub-components (`UserManagement`, `RegistrationRequests`, etc.) not fully implemented | Complete implementation |
| LOW | No `entities/` or `lib/` layers in FSD | Add as needed per FSD spec |
| LOW | `vite.config.ts` — no proxy configured for API in dev mode | Add proxy: `/api` → `http://localhost:8000` |
| LOW | `package.json` — React 19.2.5 is used; SPEC says React 18+ | Verify compatibility or pin to React 18 |

### 6.3 Data Layer

| Severity | Finding | Recommendation |
|----------|---------|----------------|
| MEDIUM | 17 alembic migrations with overlapping changes (e.g., multiple `add_processing_logs_dashboard_id_index`, `change_json_to_jsonb`, `fix_unique_constraint`) | Squash into clean initial + incremental migrations |
| MEDIUM | `alembic.ini` has hardcoded password in `sqlalchemy.url` | Use env var: `sqlalchemy.url = %(DATABASE_URL)s` |
| LOW | `aggregated_data` table uses `BIGSERIAL` for `id` — consider using UUID for consistency | Evaluate if BIGSERIAL is intentional (it is for performance) |
| LOW | `processing_logs` table missing `updated_at` field | Add if audit trail is needed |
| LOW | `downgrade()` in initial migration uses `CASCADE` which may drop dependent objects | Review downgrade safety |

### 6.4 Configuration & Deployment

| Severity | Finding | Recommendation |
|----------|---------|----------------|
| MEDIUM | `docker-compose.yml` — nginx service has `profiles: ["production"]` but `nginx.conf` may not exist | Verify nginx config exists or add to repo |
| MEDIUM | `Dockerfile` — dev stage runs as root; prod stage runs as `app` user | Document this is intentional for dev volume mounts |
| LOW | `pyproject.toml` — `classifiers` list Python 3.13 and 3.14 but `requires-python = ">=3.12"` | Align classifiers with actual support |
| LOW | `pyproject.toml` — `pandas-stubs` in dev dependencies despite pandas being forbidden | Remove (not harmful since pandas isn't a runtime dep, but confusing) |
| LOW | `mypy.ini` exists but `pyproject.toml` also has mypy config | Consolidate into `pyproject.toml` |

---

## 7. Missing / Partially Implemented Features

| Feature | Status | Details |
|---------|:-------:|---------|
| Server-side filtering on `/data/aggregated` | ⚠️ PARTIAL | `filters` param accepted but not applied to SQL query |
| Admin logs endpoint (`GET /api/v1/admin/logs`) | ❌ MISSING | Processing logs routes exist but not under `/admin` prefix |
| Email notification on registration approval | ❌ MISSING | User created with hardcoded password; no email sent |
| Nginx configuration file | ⚠️ PARTIAL | Referenced in docker-compose but not verified in repo |
| Frontend admin sub-components | ⚠️ PARTIAL | `UserManagement`, `RegistrationRequests`, `DashboardManagement`, `LogViewer` — structure exists but not fully implemented |
| Refresh token rotation | ❌ MISSING | Current `/auth/refresh` re-issues from same JWT |
| API rate limiting on non-upload endpoints | ⚠️ PARTIAL | Only login and upload have rate limiting |
| Frontend error boundary | ❌ MISSING | No React error boundary for crash recovery |
| CSRF protection | ⚠️ PARTIAL | `withCredentials: true` set but no CSRF token mechanism |
| Database connection health monitoring | ✅ PASS | `/health` and `/health/detailed` endpoints implemented |

---

## 8. Final Assessment & Risks

### Production Readiness: **7/10**

**What works well:**
- Solid Clean Architecture with clear separation of concerns
- Comprehensive enum system using `StrEnum`
- Polars-based data processing with lazy loading
- Multi-stage Docker build with proper production defaults
- JWT + bcrypt + RBAC security model
- Frontend follows FSD with proper type safety
- Good test coverage structure (17 test files)

**Key risks before production:**

1. **Security hardening needed** — Default admin password, JWT algorithm handling, and file size validation need immediate attention
2. **Migration drift** — 17 migration files indicate the schema evolved through many fixes; should be squashed for clarity
3. **Task queue is in-memory** — The `TaskQueue` class uses `asyncio.Queue`; if the app restarts, all pending tasks are lost. For production, use Redis + RQ (which is already in dependencies)
4. **Server-side filtering not implemented** — The `/data/aggregated` endpoint accepts filters but doesn't apply them; all filtering happens client-side
5. **Hardcoded temp password** — Registration approval creates users with `"temppass123"` — a security risk
6. **No email integration** — No email service for password reset or registration approval notifications

### Recommended Next Steps (Priority Order):

1. Fix CRITICAL security findings (JWT algorithm, default passwords)
2. Implement server-side JSONB filtering for `/data/aggregated`
3. Replace in-memory task queue with Redis + RQ
4. Squash alembic migrations
5. Complete admin panel frontend components
6. Add email service for user notifications
7. Add CSRF protection
8. Implement proper refresh token rotation
9. Add React error boundary
10. Configure nginx for production deployment

---

*End of Audit Report*
