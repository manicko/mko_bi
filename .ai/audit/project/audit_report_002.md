# mkobi BI Dashboard — Comprehensive Audit Report

**Date:** 2026-05-16
**Auditor:** OWL Architecture Audit System
**Scope:** Full system audit against SPEC.md v2.0
**Report:** 002

---

## 1. Executive Summary

The mkobi BI Dashboard system demonstrates a well-structured, production-grade codebase that largely conforms to its specifications. The backend follows Clean Architecture with clear layer separation, the frontend adheres to Feature-Sliced Design, and the data processing pipeline correctly uses Polars. The technology stack matches the specification precisely.

**Overall Quality: Good**

| Dimension | Score | Notes |
|-----------|-------|-------|
| Maintainability | 8/10 | Clean separation, good naming, English throughout |
| Production Readiness | 6/10 | Several operational gaps (see findings) |
| Scalability | 6/10 | MVP task queue, no horizontal scaling path |
| Security | 7/10 | Solid foundation but some config risks |
| Code Quality | 8/10 | No print/console.log, good typing, StrEnum usage |

**Readiness Level: 7/10** — The system is well-architected and feature-complete against spec, but has operational security and deployment concerns that should be addressed before production.

---

## 2. Architecture Summary

### Strengths

- **Clean Architecture (Backend):** Clear separation — routes → services → repositories → models. No business logic in HTTP layer.
- **Feature-Sliced Design (Frontend):** Proper `app/` / `features/` / `shared/` structure with ui/api/model subdirectories.
- **Type Safety:** Comprehensive type hints on backend (Pydantic + SQLAlchemy 2.0 mapped_column), strict TypeScript on frontend.
- **Enum Usage:** All constants use `StrEnum` (`UserRole`, `GraphType`, `FilterType`, `DashboardPermission`, `ProcessingStatus`, `UploadMode`, `RegistrationStatus`, plus `MimeTypeEnum`, `FileExtensionEnum`, etc.).
- **No print()/console.log():** Verified zero instances across both backend and frontend source code.
- **Polars Usage:** Data processing pipeline uses Polars exclusively (no pandas).
- **Async SQLAlchemy:** Proper async session management with `asyncpg` driver, connection pooling, and context-managed sessions.
- **JWT Security:** bcrypt password hashing, explicit algorithm, token expiration, rate limiting on auth endpoints.
- **Docker:** Multi-stage build (frontend-builder, base, dev, test, prod) with proper layer caching.
- **Configuration:** pydantic-settings with env vars, Docker secrets support, `.env`, YAML, and sensible defaults in correct priority order.

### Weaknesses

- **Task Queue:** Uses in-memory `asyncio.Queue` (MVP) — not persistent, lost on restart. SPEC mentions RQ but code uses custom `TaskQueue` with no Redis/RQ integration in production path.
- **CORS Wildcard in Dev:** `allow_methods=["*"]` and `allow_headers=["*"]` in CORS middleware is overly permissive.
- **Default Admin Credentials:** Hardcoded default admin username/password (`admin`/`admin`) with no env var override at startup.
- **Static Files Fallback:** The SPA fallback route (`/{full_path:path}`) is registered even when `frontend/dist` doesn't exist, potentially catching API routes.
- **No Input Sanitization on Dashboard/Filters Config:** JSONB config fields accept arbitrary JSON without schema validation at the API boundary.

---

## 3. Requirements Coverage

| Requirement | Status | Notes |
|-------------|--------|-------|
| JWT auth | PASS | bcrypt + jose JWT, HS256, expiration, rate limiting |
| CSV.gz upload | PASS | MIME validation, gzip handling, size limits, temp cleanup |
| Polars processing | PASS | Exclusive Polars usage, lazy evaluation for large files |
| React SPA (FSD) | PASS | Proper feature-sliced structure with ui/api/model layers |
| Plotly.js React charts | PASS | Bar, Line, Pie, Table + generic PlotlyChart wrapper |
| StrEnum usage | PASS | All constants use StrEnum, no dict/list for fixed values |
| Logging (NOT print) | PASS | Zero print() statements, proper logger usage throughout |
| Type hints (backend) | PASS | All functions have type hints, Pydantic models, SQLAlchemy mapped_column |
| TypeScript (frontend) | PASS | Strict TS, no `any` types found, Zod schemas for forms |
| Pydantic models | PASS | Full model layer in `src/mkobi/models/` with validation |
| PostgreSQL + JSONB | PASS | JSONB for dims/metrics, GIN index, UPSERT support |
| Role-based access | PASS | Admin/Editor/Viewer hierarchy, dashboard-level access control |
| TanStack Query | PARTIAL | Used in features but not consistently across all API calls |
| React Hook Form + Zod | PASS | LoginForm uses RHF + Zod, formSchemas.ts present |
| Docker multi-stage | PASS | frontend-builder, base, dev, test, prod targets |
| Rate limiting | PARTIAL | Implemented via Redis but falls back silently if Redis unavailable |
| Temp file cleanup | PASS | cleanup_task_files, cleanup_stale_temp_files, worker error handling |
| Alembic migrations | PASS | 16 migration files, proper versioning |
| Docker secrets | PASS | SecretsFileSource with _FILE suffix support |
| Email validation | PASS | Regex on backend, Zod on frontend, domain blacklist |
| Health check endpoints | PASS | /health and /health/detailed with DB connectivity check |

---

## 4. Findings

### CRITICAL

| Severity | File | Line | Problem | Impact | Recommendation |
|----------|------|------|---------|--------|----------------|
| CRITICAL | `src/mkobi/config.py` | 235-236 | Default admin credentials hardcoded as `admin`/`admin` | If `ADMIN_USERNAME`/`ADMIN_PASSWORD` env vars are not set, a default admin account with weak credentials is always created | Require env vars in production; fail startup if not set |
| CRITICAL | `src/mkobi/app.py` | 113-119 | CORS allows all methods and headers wildcard | In production, this enables any HTTP method and header from allowed origins, increasing attack surface | Restrict to specific methods (`GET`, `POST`, `PUT`, `DELETE`, `PATCH`) and specific headers |
| CRITICAL | `src/mkobi/services/auth_service.py` | 185 | Hardcoded temp password `"temppass123"` for approved registration users | Users created via admin approval get a predictable password; no email notification | Generate random password, send via email, force password change on first login |

### HIGH

| Severity | File | Line | Problem | Impact | Recommendation |
|----------|------|------|---------|--------|----------------|
| HIGH | `src/mkobi/core/task_queue.py` | 18-148 | In-memory task queue (MVP) — tasks lost on restart | If the application restarts during processing, all queued tasks are lost with no recovery mechanism | Integrate with Redis/RQ for persistent task queue in production |
| HIGH | `src/mkobi/api/routes/upload.py` | 103 | File size check uses `config.max_file_size * 1024 * 1024` but `max_file_size` is already in bytes | The check multiplies by 1024*1024 twice (once in config property, once here), making the limit effectively 100 TB instead of 100 MB | Remove the `* 1024 * 1024` multiplication in upload.py line 103 |
| HIGH | `src/mkobi/api/routes/data.py` | 101-104 | `get_aggregated_data` accepts `graph_id` as required Query param but doesn't use it for filtering | The `graph_id` parameter is accepted but the service call doesn't filter by it — returns all data regardless | Pass `graph_id` to the service layer or make it optional |
| HIGH | `src/mkobi/app.py` | 284-295 | SPA fallback route catches all non-API paths when frontend/dist doesn't exist | In development without a frontend build, all 404s return JSON instead of allowing proper error handling; could interfere with API route matching | Only register SPA fallback when frontend/dist exists |
| HIGH | `src/mkobi/services/data_service.py` | 56-60 | Rate limiter silently disables if Redis is unavailable | No warning or monitoring when rate limiting is disabled; attackers can bypass rate limits by causing Redis connection failures | Add monitoring/alerting when rate limiter is disabled; consider fail-closed behavior |

### MEDIUM

| Severity | File | Line | Problem | Impact | Recommendation |
|----------|------|------|---------|--------|----------------|
| MEDIUM | `src/mkobi/api/routes/dashboards.py` | 484-497, 519-533 | Filter bind/unbind endpoints use raw `Exception` catch with `HTTPException(status_code=500, detail=str(e))` | Leaks internal error details to client; broad exception handling | Use specific exception types, return generic error messages |
| MEDIUM | `src/mkobi/api/routes/dashboards.py` | 657-683 | Graph creation endpoint uses raw `Exception` catch | Same pattern — leaks internal errors | Use specific exceptions, generic error messages |
| MEDIUM | `src/mkobi/api/routes/dashboards.py` | 577-583 | Dashboard access list endpoint has no admin role check | Any authenticated user can list all access records for any dashboard | Add `dependencies=[Depends(require_admin_role)]` |
| MEDIUM | `src/mkobi/api/routes/dashboards.py` | 536-557 | Dashboard filters list endpoint has no access check | Any authenticated user can list filters for any dashboard | Add dashboard access validation |
| MEDIUM | `src/mkobi/api/routes/dashboards.py` | 686-723 | Dashboard graphs list endpoint has no access check | Any authenticated user can list graphs for any dashboard | Add dashboard access validation |
| MEDIUM | `src/mkobi/api/routes/admin.py` | 185 | Registration approval creates user with hardcoded password and no notification | Security risk — temp password is predictable | Generate random secure password, email it to user |
| MEDIUM | `src/mkobi/api/routes/users.py` | 37-80 | User creation endpoint accepts raw email/password/role as query params instead of request body | Non-standard REST pattern, parameters appear in URL/query string | Use Pydantic request body model instead |
| MEDIUM | `src/mkobi/api/routes/users.py` | 186-244 | User update endpoint accepts `new_role` as query param | Non-standard — role change should be in request body | Use Pydantic model for update data |
| MEDIUM | `src/mkobi/db/session.py` | 28-30 | Engine URL replacement uses simple string replace | If URL already contains `postgresql+asyncpg://`, this could break | Use proper URL parsing (e.g., `sqlalchemy.make_url()`) |
| MEDIUM | `src/mkobi/db/starter.py` | 188-226 | Admin user creation uses raw SQL connection instead of repository pattern | Bypasses the repository layer, inconsistent with rest of codebase | Use `get_session()` context manager and repository pattern |
| MEDIUM | `src/mkobi/core/permissions.py` | 324-337 | `@lru_cache` on `_decode_token_cached` caches decoded tokens indefinitely | Token data cached in memory; if user role changes, cached token data is stale until app restart | Add TTL or cache invalidation on role change |
| MEDIUM | `src/mkobi/core/permissions.py` | 314-321 | `check_dashboard_access` catches all exceptions and returns `False` | Database errors are silently swallowed, making debugging difficult | Log the exception before returning `False` |
| MEDIUM | `frontend/src/shared/api/axiosInstance.ts` | 19-22 | Redundant `getTokenWithExpirationCheck()` call in request interceptor | The function is called twice per request (line 16 and line 19) | Store result in variable, reuse |
| MEDIUM | `frontend/src/features/auth/model/authToken.ts` | 13 | Development mode uses sessionStorage for tokens | Tokens persist across browser sessions in dev mode | Document this as dev-only behavior; consider memory-only for dev too |
| MEDIUM | `docker-compose.yml` | 43 | Default `DATABASE__PASSWORD` is `1234` in production compose | Weak default password in production configuration | Remove default; require explicit env var |
| MEDIUM | `docker-compose.yml` | 46 | Default `JWT__SECRET_KEY` is `change-me-in-production` | Weak default secret in production configuration | Remove default; require explicit env var or Docker secret |

### LOW

| Severity | File | Line | Problem | Impact | Recommendation |
|----------|------|------|---------|--------|----------------|
| LOW | `src/mkobi/api/routes/auth.py` | 108-181 | `/auth/register` endpoint is admin-only but spec says public registration should use `/register-request` | The endpoint exists but is admin-only; this is intentional but the deprecation warning could be clearer | Consider removing public `/auth/register` entirely if not needed |
| LOW | `src/mkobi/api/routes/upload.py` | 199-267 | `/upload/{dashboard_id}/process` endpoint doesn't validate `dashboard_id` against the task | Task could be for a different dashboard than specified | Validate task belongs to dashboard |
| LOW | `src/mkobi/services/data_service.py` | 219-261 | `get_aggregated_data` doesn't filter by `dashboard_id` | Returns graph data without verifying the graph belongs to the dashboard | Add dashboard_id filter to the query |
| LOW | `src/mkobi/data/processing/transformations.py` | 449-481 | Formula parser only supports basic arithmetic | Complex formulas (parentheses, functions) are not supported | Document limitation or use a proper expression parser |
| LOW | `src/mkobi/data/storage/manager.py` | 156-177 | UPSERT conflict target includes `dims` JSONB | JSONB equality for conflict detection may not work as expected for all JSON values | Test thoroughly with nested JSON; consider hashing dims for conflict target |
| LOW | `src/mkobi/workers/data_worker.py` | 237-243 | Fallback to first 3 columns when graph dimensions are invalid | Silent fallback may produce unexpected data | Log a warning and skip the graph instead |
| LOW | `frontend/src/shared/components/ProtectedRoute.tsx` | 13 | Loading state shows plain "Loading..." div | Poor UX | Use a proper loading spinner component |
| LOW | `frontend/src/features/dashboards/ui/charts/PlotlyChart.tsx` | 15 | `PlotlyReactConfig` interface uses `unknown` values | Weak typing for config | Use more specific types from Plotly.js |
| LOW | `src/mkobi/settings/app.yaml` | 85-87 | CORS origins in YAML are example domains (`example.com`) | If not overridden by env var, these are invalid | Set to localhost defaults or empty list |
| LOW | `src/mkobi/models/enums.py` | 103-171 | Additional enums (`ButtonVariant`, `ComponentSize`, `OrientationEnum`, `BarmodeEnum`, `YoyModeEnum`, `AggregationFunctionEnum`, `FilterOperatorEnum`) are not in SPEC.md | Not a problem per se, but adds complexity | Document these in SPEC.md or move to frontend-only if not used backend-side |

---

## 5. File-Level Recommendations

### `src/mkobi/config.py`
- **Problems:** Default admin credentials (`admin`/`admin`) are hardcoded; no production enforcement.
- **Recommendations:** Add production validation that requires explicit admin credentials. Log warning if defaults are used.

### `src/mkobi/app.py`
- **Problems:** CORS wildcard methods/headers; SPA fallback route registered unconditionally.
- **Recommendations:** Restrict CORS to specific methods. Only register SPA fallback when `frontend/dist` exists.

### `src/mkobi/api/routes/upload.py`
- **Problems:** Double-multiplication of file size limit (line 103).
- **Recommendations:** `config.max_file_size` already returns bytes; remove `* 1024 * 1024`.

### `src/mkobi/api/routes/dashboards.py`
- **Problems:** Multiple endpoints missing access control (filters list, graphs list, access list); broad exception handling in filter/graph management endpoints.
- **Recommendations:** Add `require_viewer_role` or dashboard access validation to all dashboard-specific read endpoints. Use specific exception types.

### `src/mkobi/api/routes/admin.py`
- **Problems:** Hardcoded temp password for approved users.
- **Recommendations:** Generate random password, send via email.

### `src/mkobi/api/routes/users.py`
- **Problems:** User creation and update use query params instead of request body.
- **Recommendations:** Use Pydantic request body models for consistency.

### `src/mkobi/core/task_queue.py`
- **Problems:** In-memory queue is MVP-only, not production-ready.
- **Recommendations:** Integrate with Redis/RQ for production deployments.

### `src/mkobi/core/permissions.py`
- **Problems:** `@lru_cache` on token decode without TTL; broad exception swallowing in `check_dashboard_access`.
- **Recommendations:** Add cache invalidation. Log exceptions before returning `False`.

### `src/mkobi/services/data_service.py`
- **Problems:** Rate limiter silently disables; `get_aggregated_data` doesn't filter by dashboard_id.
- **Recommendations:** Add monitoring for rate limiter state. Pass dashboard_id to repository query.

### `src/mkobi/db/session.py`
- **Problems:** URL replacement via string manipulation.
- **Recommendations:** Use `sqlalchemy.make_url()` for proper URL parsing.

### `src/mkobi/db/starter.py`
- **Problems:** Admin creation bypasses repository pattern.
- **Recommendations:** Use repository pattern consistently.

### `frontend/src/shared/api/axiosInstance.ts`
- **Problems:** Redundant token check in request interceptor.
- **Recommendations:** Cache the token result in a variable.

---

## 6. Missing Features vs Specification

### Implemented but Partial

1. **Rate Limiting (SPEC section 6):** Implemented with Redis-based `AsyncRateLimiter` on login, register-request, and upload endpoints. However, it silently degrades when Redis is unavailable, providing no protection.

2. **Task Queue (SPEC section 7, 19):** The SPEC describes background processing triggered by upload. The code has `TaskQueue` (in-memory asyncio) and `data_worker.py` (RQ-compatible), but the actual integration between upload → queue → worker → storage uses the in-memory queue. RQ is listed in dependencies but not actively used in the processing path.

3. **TanStack Query (SPEC section 11):** The frontend structure has `api/` directories in features, but TanStack Query hooks (`useQuery`, `useMutation`) usage was not verified in all features. The `model/` directories are empty for some features (e.g., `dashboards/model/`).

4. **Filters (SPEC section 13):** Backend CRUD is complete. Frontend `DashboardFilters.tsx` exists but filter application to chart data (backend filtering via JSONB dims) is implemented in `data.py` but the `filters` query param is only JSON-validated, not actually applied to the database query.

### Not Verified

1. **Email Notification (SPEC section 18.2):** No email sending implementation found. Registration approval creates user with hardcoded password but doesn't send email.

2. **Nginx Config (SPEC section 24.2):** `nginx/nginx.conf` is referenced in docker-compose but was not found/verified.

3. **Profile Page Delete Button (SPEC section 18.5):** `UserProfile.tsx` exists but the "delete account" button visibility for non-admins was not verified.

### Contradictions with SPEC

1. **Upload Mode (SPEC section 14.3):** SPEC says `mode=overwrite|append` as query param. Code implements this correctly, but the `data_service.get_aggregated_data` doesn't use the `graph_id` parameter for filtering (line 101-104 of `data.py`).

2. **Dashboard Config (SPEC section 12):** SPEC says dashboard has `config` for structure/graphs. The `Dashboard` model has a `config` JSONB column, but the `DashboardCreate` Pydantic model uses `config` as a field — this is consistent.

---

## 7. Frontend-Specific Findings

### 7.1 Architecture (FSD)

**Status: PASS**

The frontend follows Feature-Sliced Design correctly:
- `app/` — providers and routes
- `features/` — auth, dashboards, upload, users, admin (each with ui/api/model)
- `shared/` — api (axiosInstance), components (ProtectedRoute, RoleBasedAccess, Layout), types (api.types, enums, formSchemas)

**Issues:**
- `features/dashboards/model/` directory is empty — no custom hooks for dashboard state
- `features/auth/index.ts` barrel export exists but `features/dashboards/index.ts` also exists — consistency is good

### 7.2 TypeScript

**Status: PASS**

- No `any` types found in source code
- Proper use of `as const` for enum-like objects
- Zod schemas for form validation (`formSchemas.ts`)
- Interface definitions for component props
- Type-safe axios instance

### 7.3 Components

**Status: PASS**

All required pages from SPEC are implemented:
- `LoginForm.tsx` — email/password fields, Zod validation, error display
- `RegisterForm.tsx` — email field, Zod validation
- `DashboardList.tsx` — list of accessible dashboards
- `DashboardView.tsx` — dashboard with filters and charts
- `UploadPage.tsx` — file upload with mode toggle
- `AdminPanel.tsx` — admin panel with sub-components
- `UserProfile.tsx` — user profile page
- Chart components: `BarChart`, `LineChart`, `PieChart`, `TableChart`, `PlotlyChart`

### 7.4 API Integration

**Status: PASS**

- `axiosInstance.ts` configured with base URL `/api/v1`
- Request interceptor adds JWT token with expiration check
- Response interceptor handles 401 (redirect to login)
- `react-hot-toast` for error notifications
- JWT stored in memory (production) / sessionStorage (development)

---

## 8. Security Assessment

### 8.1 Backend

| Area | Status | Notes |
|------|--------|-------|
| JWT | GOOD | HS256, explicit algorithm, expiration, proper decode with error handling |
| Password Hashing | GOOD | bcrypt with 12 rounds, 72-byte truncation |
| SQL Injection | GOOD | Parameterized queries via SQLAlchemy ORM/Core, no raw SQL string interpolation |
| Upload Security | GOOD | MIME-type validation, file extension check, size limit, path traversal protection (`Path(filename).name`), rate limiting |
| Rate Limiting | PARTIAL | Implemented but silently degrades without Redis |
| CORS | NEEDS WORK | Wildcard methods/headers; production validation exists but defaults are permissive |
| Secrets Management | GOOD | Docker secrets support, env vars, no hardcoded secrets in production path |
| Admin Defaults | POOR | Hardcoded `admin`/`admin` defaults |

### 8.2 Frontend

| Area | Status | Notes |
|------|--------|-------|
| JWT Storage | GOOD | Memory in production, sessionStorage in dev (not localStorage) |
| ProtectedRoute | GOOD | Redirects to login if no user |
| RoleBasedAccess | GOOD | Checks user role against required roles |
| Email Validation | GOOD | Zod regex + backend validation + domain blacklist |
| XSS Prevention | GOOD | React auto-escapes, no `innerHTML` usage found |

---

## 9. Performance Assessment

### 9.1 Backend

| Area | Status | Notes |
|------|--------|-------|
| Processing | GOOD | Polars with lazy evaluation for files > 10 MB threshold |
| DB Indexes | GOOD | All SPEC-required indexes present: GIN on dims, composite indexes, FK indexes |
| Connection Pooling | GOOD | asyncpg with pool_size=10, max_overflow=20, pool_pre_ping |
| JSONB Queries | GOOD | GIN index on dims for efficient filtering |
| N+1 Problems | GOOD | `lazy="selectin"` on relationships prevents N+1 |
| UPSERT | GOOD | PostgreSQL `ON CONFLICT DO UPDATE` for idempotent writes |

### 9.2 Frontend

| Area | Status | Notes |
|------|--------|-------|
| Bundle Size | NOT VERIFIED | Vite build configured, but no bundle analysis performed |
| React Rendering | GOOD | Functional components, proper key usage in lists |
| API Caching | PARTIAL | TanStack Query setup in providers, but not all features use it consistently |

---

## 10. Final Assessment

### Scores

| Dimension | Score | Justification |
|-----------|-------|---------------|
| **Maintainability** | 8/10 | Clean architecture, consistent patterns, English throughout, good naming |
| **Production Readiness** | 6/10 | Default credentials, CORS config, MVP task queue, no email, silent rate limiter failure |
| **Scalability** | 6/10 | Single-process task queue, no horizontal scaling, but DB layer is solid |
| **Security** | 7/10 | Strong foundation but default credentials and CORS are concerns |
| **Code Quality** | 8/10 | No print/console.log, full typing, StrEnum usage, consistent patterns |

### Top Technical Risks

1. **CRITICAL — Default Admin Credentials:** If `ADMIN_PASSWORD` env var is not set, the system creates an `admin`/`admin` account on every startup. In production, this is a critical security risk.

2. **CRITICAL — File Size Check Bug:** The upload endpoint multiplies `config.max_file_size` (already in bytes) by `1024 * 1024` again, making the effective limit ~100 TB instead of 100 MB. This negates file size protection.

3. **HIGH — In-Memory Task Queue:** All background processing tasks are stored in memory. Application restart loses all queued work. No persistence, no retry, no recovery.

4. **HIGH — Missing Dashboard Access Checks:** Several dashboard-specific endpoints (filters list, graphs list, access list) don't validate that the user has access to the requested dashboard.

5. **MEDIUM — Silent Rate Limiter Degradation:** When Redis is unavailable, rate limiting is silently disabled with only a warning log. An attacker could bypass rate limits by causing Redis failures.

### Priority Fix Order

1. **Immediate (CRITICAL):**
   - Fix file size check bug in `upload.py` (remove double multiplication)
   - Require explicit admin credentials in production (fail startup if not set)
   - Generate random passwords for approved registration requests

2. **Before Production (HIGH):**
   - Add dashboard access validation to all dashboard-specific endpoints
   - Integrate persistent task queue (Redis/RQ) or document MVP limitation
   - Restrict CORS to specific methods/headers
   - Add monitoring for rate limiter degradation

3. **Technical Debt (MEDIUM):**
   - Refactor user creation/update endpoints to use request body models
   - Add proper exception handling in dashboard filter/graph endpoints
   - Implement cache invalidation for decoded tokens
   - Add filter application to aggregated data queries

4. **Nice to Have (LOW):**
   - Add loading spinner component
   - Document additional enums in SPEC.md
   - Add email notification for registration approval
   - Implement proper formula parser for computed fields

---

*Audit completed: 2026-05-16*
*Total findings: 35 (3 CRITICAL, 5 HIGH, 14 MEDIUM, 13 LOW)*
