# mkobi BI Dashboard — Full Audit Report

**Date:** 2026-05-14
**Auditor:** OWL Architecture Audit System
**Scope:** Backend (FastAPI) + Frontend (React/TS) + Data Layer (PostgreSQL/Polars) + DevOps (Docker)
**Report Version:** 3

---

## 1. Executive Summary

| Dimension | Score (1-10) | Notes |
|-----------|:---:|-------|
| Architecture Compliance | 8 | Clean Architecture + FSD well followed, minor deviations |
| Security | 7 | Solid JWT/bcrypt/rate-limiting, but several gaps found |
| Requirements Coverage | 7.5 | Most SPEC endpoints implemented, some missing/partial |
| Code Quality | 8 | Good type hints, StrEnum usage, logging. Minor issues |
| Data Layer | 8 | Good schema, JSONB+GIN indexes, proper migrations |
| Performance & Stability | 7 | Connection pooling, Polars, but task queue is in-memory only |
| Configuration & Deployment | 8 | Multi-stage Docker, secrets management, health checks |
| Frontend Quality | 7.5 | FSD structure, TS types, but uses MUI not specified in SPEC |
| **Overall Readiness** | **7.6** | **Production-ready with noted fixes required** |

---

## 2. Architecture Compliance

### 2.1 Backend — Clean Architecture

**Status: COMPLIANT with minor deviations**

The backend follows a clear layered architecture:

- **API Layer** (`api/routes/`) — Routes delegate to services. No raw SQL in routes.
- **Service Layer** (`services/`) — Business logic properly encapsulated.
- **Repository Layer** (`db/repositories/`) — Data access abstracted behind interfaces.
- **Models** — Pydantic models in `models/`, SQLAlchemy models in `db/models/`.
- **Core** — Security, permissions, logging, config properly separated.
- **Interfaces** — Abstract interfaces for DI in `interfaces/`.
- **Data** — Polars-based loaders, transformations, storage manager.

**Positive findings:**
- Clear separation API → Service → Repository
- Dependency injection via FastAPI `Depends()` with typed aliases (`CurrentUser`, `AdminUser`, etc.)
- Abstract repository and service interfaces for testability
- No `print()` statements found — proper logging throughout
- All enums use `StrEnum` as required

**Deviations found:**

| Severity | Issue | Location |
|----------|-------|----------|
| MEDIUM | Repository instantiated directly in some routes instead of DI | `dashboards.py:38`, `graphs.py:33`, `admin.py:142` |
| LOW | `layouts.py` checks role manually instead of using `require_admin_role` dependency | `layouts.py:61-70` |
| LOW | `processing_logs.py:106-115` directly imports and uses `ProcessingLogRepository` | `processing_logs.py` |

### 2.2 Frontend — Feature-Sliced Design

**Status: COMPLIANT**

Structure follows FSD:
- `app/` — Providers, routing
- `features/` — `auth/`, `dashboards/`, `upload/`, `admin/`, `users/` each with `ui/`, `api/`, `model/`
- `shared/` — `api/`, `components/`, `types/`

**Note:** SPEC specifies Material UI v5 OR Ant Design. The project uses MUI v5 (`@mui/material`), which is compliant.

### 2.3 Data Processing Pipeline

**Status: COMPLIANT**

- Uses **Polars** exclusively (no pandas found)
- Pipeline: upload → validate → parse (Polars CSVLoader) → transform → aggregate → save (StorageManager)
- Background processing via in-memory async task queue
- Temp file cleanup in worker after processing

---

## 3. Security Assessment

### 3.1 Authentication & JWT

| Aspect | Status | Notes |
|--------|--------|-------|
| JWT creation | OK | HS256, configurable secret, expiration |
| JWT decoding | OK | Proper error handling, algorithm verification |
| Password hashing | OK | bcrypt with 12 rounds, 72-byte truncation |
| Token storage (FE) | OK | Memory-first, sessionStorage fallback for dev |
| Token expiration check | OK | Client-side JWT payload parsing |
| Token refresh | PARTIAL | `/auth/refresh` exists but uses same JWT (no refresh token rotation) |

### 3.2 Access Control

| Aspect | Status | Notes |
|--------|--------|-------|
| Role-based access | OK | `require_admin_role`, `require_editor_role`, `require_viewer_role` |
| Dashboard-level access | OK | `check_dashboard_access()` with permission hierarchy |
| Access check on endpoints | OK | Most endpoints use `require_*_role` dependencies |
| Access check on data access | PARTIAL | `data.py` endpoint doesn't validate dashboard access |

### 3.3 Upload Security

| Aspect | Status | Notes |
|--------|--------|-------|
| MIME-type validation | OK | Checked in `DataService._validate_mime_type()` |
| File extension validation | OK | Checked in `DataService._validate_file()` |
| File size limit | OK | Enforced in both route (pre-read) and service |
| Rate limiting | OK | Redis-based rate limiter on upload endpoint |
| Temp file cleanup | OK | Cleanup in worker after success and on error |
| Path traversal | OK | `Path(filename).name` sanitization |

### 3.4 Security Issues Found

| Severity | Issue | Location | Recommendation |
|----------|-------|----------|----------------|
| **HIGH** | `/api/v1/data/aggregated` endpoint does not validate user's dashboard access | `data.py:39-95` | Add `require_dashboard_read_access` or call `check_dashboard_access()` |
| **HIGH** | `/api/v1/upload/{dashboard_id}` file size check uses `file.size` which may be `None` for streaming uploads | `upload.py:68` | Add null check: `if file.size and file.size > config.max_file_size * 1024 * 1024` |
| **MEDIUM** | Default JWT secret in docker-compose is `"change-me-in-production"` | `docker-compose.yml:46` | Enforce secret via Docker secrets or fail on default in production |
| **MEDIUM** | Default database password `"1234"` in docker-compose | `docker-compose.yml:16` | Enforce password change in production |
| **MEDIUM** | CORS allows `allow_methods=["*"]` and `allow_headers=["*"]` | `app.py:116-118` | Restrict to specific methods/headers in production |
| **MEDIUM** | `register-request` endpoint doesn't validate email domain against blocklist | `auth.py:291-365` | Add `EmailSettings.blocked_domains` check |
| **LOW** | No `iss` or `aud` claims in JWT tokens | `security.py:154-196` | Add issuer/audience claims for production |
| **LOW** | `dashboard_access` endpoint at `POST /{dashboard_id}/access` uses `require_viewer_role` instead of `require_admin_role` | `dashboards.py:371` | Change to `require_admin_role` — granting access should be admin-only |

---

## 4. Requirements Coverage

| SPEC Requirement | Endpoint | Status |
|-----------------|----------|--------|
| `POST /api/v1/auth/login` | `auth.py:76` | PASS |
| `POST /api/v1/auth/register-request` | `auth.py:291` | PASS |
| `GET /api/v1/auth/me` | `auth.py:265` | PASS |
| `GET /api/v1/dashboards/my` | `dashboards.py:128` | PASS |
| `GET /api/v1/dashboards/:id` | `dashboards.py:179` | PASS |
| `POST /api/v1/dashboards` | `dashboards.py:52` | PASS |
| `PUT /api/v1/dashboards/:id` | `dashboards.py:250` | PASS |
| `DELETE /api/v1/dashboards/:id` | `dashboards.py:319` | PASS |
| `GET /api/v1/data/aggregated` | `data.py:39` | PARTIAL — missing dashboard access check |
| `POST /api/v1/upload/:dashboard_id` | `upload.py:46` | PASS |
| `GET /api/v1/admin/users` | `admin.py:40` | PASS |
| `PATCH /api/v1/admin/users/:id/role` | `admin.py:64` | PASS |
| `GET /api/v1/admin/registration-requests` | `admin.py:136` | PASS |
| `POST /api/v1/admin/registration-requests/:id/approve` | `admin.py:160` | PASS |
| `GET /api/v1/admin/logs` | `processing_logs.py:32` | PASS |
| Rate limiting on upload | `upload.py:83-96` | PASS |
| MIME-type validation | `data_service.py:341-354` | PASS |
| File size limit | `upload.py:68-80` | PASS |
| Temp file cleanup | `data_worker.py:158-160,181-185` | PASS |
| Registration request flow | `auth.py:291-365` | PASS |
| Password bcrypt hashing | `security.py:93-116` | PASS |
| StrEnum for all constants | `models/enums.py` | PASS |
| Polars for data processing | `data/loaders/loader.py` | PASS |
| JSONB for aggregated data | `db/models/aggregated_data.py` | PASS |
| GIN index on dims | `aggregated_data.py:53` | PASS |

---

## 5. Critical Findings

| # | Severity | Component | File | Problem | Recommendation |
|---|----------|-----------|------|---------|----------------|
| 1 | **HIGH** | Security | `data.py:39-95` | No dashboard access check on aggregated data endpoint | Add `check_dashboard_access(user_id, dashboard_id, "view")` call |
| 2 | **HIGH** | Security | `upload.py:68` | `file.size` may be `None` causing `TypeError` | Add null guard before comparison |
| 3 | **MEDIUM** | Security | `dashboards.py:371` | Grant access endpoint only requires viewer role | Change to `require_admin_role` |
| 4 | **MEDIUM** | Security | `auth.py:338` | No email domain blocklist check on register-request | Add blocked domain validation |
| 5 | **MEDIUM** | Reliability | `task_queue.py` | In-memory task queue — tasks lost on restart | Document as MVP limitation; plan Redis/RQ migration |
| 6 | **MEDIUM** | Security | `docker-compose.yml:46` | Default JWT secret | Fail startup if default in production |
| 7 | **LOW** | Correctness | `graphs.py:237-239` | Duplicate `_graph_repo.update()` call | Remove duplicate line |
| 8 | **LOW** | Architecture | `dashboards.py:38` | Module-level `_graph_repo = GraphRepository()` singleton | Use DI via `Depends(get_graph_repository)` |
| 9 | **LOW** | Architecture | `layouts.py:61-70` | Manual role check instead of dependency | Use `dependencies=[Depends(require_admin_role)]` |
| 10 | **LOW** | Security | `app.py:116-118` | CORS allows all methods/headers | Restrict in production |

---

## 6. Findings & Recommendations

### 6.1 Security (Critical Priority)

**FINDING 1 — HIGH: Missing access control on data endpoint**
The `GET /api/v1/data/aggregated` endpoint accepts `dashboard_id` and `graph_id` as query parameters but never checks if the authenticated user has access to the specified dashboard. Any authenticated user can access any dashboard's data.

```python
# data.py — current code has no access check
# Recommendation: Add access validation
has_access = await check_dashboard_access(
    user_id=current_user.id,
    dashboard_id=dashboard_id,
    required_permission="view",
    db=db,
)
if not has_access:
    raise HTTPException(status_code=403, detail="Access denied")
```

**FINDING 2 — HIGH: Potential TypeError on file.size**
FastAPI's `UploadFile.size` can be `None` for streaming uploads. The comparison `file.size > config.max_file_size * 1024 * 1024` will raise `TypeError`.

**FINDING 3 — MEDIUM: Inconsistent access control on grant_access**
The `POST /{dashboard_id}/access` endpoint uses `require_viewer_role` (any authenticated user) instead of `require_admin_role`. This allows any user to grant access to any dashboard they can view.

### 6.2 Code Quality

**FINDING 4 — LOW: Duplicate update call in graphs.py**
At `graphs.py:237-239`, `_graph_repo.update()` is called twice consecutively — a clear copy-paste error.

**FINDING 5 — LOW: Module-level repository singletons**
`dashboards.py:38` and `graphs.py:33` instantiate repositories at module level (`_graph_repo = GraphRepository()`). This bypasses DI and makes testing harder. Should use `Depends(get_graph_repository)`.

**FINDING 6 — LOW: Manual role checks in layouts.py**
`layouts.py` manually checks `current_user.role != UserRole.ADMIN` instead of using the `require_admin_role` dependency, which is the pattern used everywhere else.

### 6.3 Architecture

**FINDING 7 — MEDIUM: In-memory task queue**
The `TaskQueue` class in `core/task_queue.py` uses `asyncio.Queue` — tasks are lost on application restart. The code itself documents this as MVP. For production, migrate to Redis + RQ or Celery.

**FINDING 8 — LOW: Service self-management of database sessions**
Many services (e.g., `AuthService.register_user`, `DashboardService.create_dashboard`) accept `db: AsyncSession | None = None` and create their own session if `None`. This pattern can lead to inconsistent transaction boundaries. Consider always requiring the session from the caller.

### 6.4 Data Layer

**FINDING 9 — LOW: Missing `updated_at` trigger on `users` table**
The `users` model has `updated_at` with `onupdate=text("now()")`, but this only works for SQLAlchemy updates. Direct SQL updates won't trigger it. Consider a database-level trigger for consistency.

**FINDING 10 — INFO: Alembic migration chain has duplicates**
Multiple migrations exist for the same index (e.g., `3f7a1b2c9d0e` and `4bfb28b3732d` both add `processing_logs_dashboard_id_index`). While functional, this indicates merge conflicts were resolved by creating duplicate migrations.

### 6.5 Frontend

**FINDING 11 — LOW: No `console.log` linting rule found**
The project uses ESLint but no explicit `no-console` rule was found in `eslint.config.js`. Production builds may contain debug logging.

**FINDING 12 — LOW: `react-plotly.d.ts` is a type declaration stub**
The file `frontend/src/react-plotly.d.ts` provides minimal typing for Plotly. Consider using `@types/react-plotly.js` for complete type safety.

**FINDING 13 — INFO: MUI used instead of Ant Design**
SPEC allows either MUI v5 or Ant Design. The project chose MUI. This is compliant but should be documented as the chosen UI kit.

### 6.6 Configuration & Deployment

**FINDING 14 — MEDIUM: Default secrets in docker-compose**
Both `DATABASE__PASSWORD` and `JWT__SECRET_KEY` have fallback defaults. In production, these should be required (no defaults).

**FINDING 15 — LOW: Dev stage runs as root**
The `dev` Dockerfile stage explicitly comments "Run as root in dev mode" — acceptable for development but should be documented as a security consideration.

**FINDING 16 — INFO: Nginx service uses `profiles: ["production"]`**
The Nginx reverse proxy is correctly gated behind a Docker Compose profile, so it won't start in dev/test. Good practice.

---

## 7. Missing / Partially Implemented Features

| Feature | SPEC Reference | Status | Notes |
|---------|---------------|--------|-------|
| Email notification on registration approval | `admin.py:186` | MISSING | Hardcoded password `"temppass123"` with TODO comment |
| Refresh token rotation | `auth.py:190-255` | PARTIAL | Uses same JWT, no separate refresh token |
| Dashboard access check on data endpoint | `data.py` | MISSING | No `check_dashboard_access` call |
| Email domain blocklist validation | `auth.py:291` | MISSING | `EmailSettings.blocked_domains` exists but not checked |
| Persistent task queue | `core/task_queue.py` | MVP ONLY | In-memory only, documented as limitation |
| Frontend pages: `/register`, `/profile`, `/admin` | SPEC 18.x | IMPLEMENTED | All UI components exist |
| Role-based upload button visibility | SPEC 18.4 | IMPLEMENTED | `RoleBasedAccess` component used |
| Plotly.js React charts | SPEC 11-12 | IMPLEMENTED | Bar, Line, Pie, Table chart components |

---

## 8. Final Assessment & Risks

### Strengths
1. **Clean architecture** — Well-layered backend with proper DI, interfaces, and separation of concerns
2. **Type safety** — Comprehensive use of type hints (Python) and TypeScript with shared enums
3. **Security foundation** — JWT + bcrypt, rate limiting, input validation, CORS, non-root Docker user
4. **Data layer** — Proper PostgreSQL schema with JSONB, GIN indexes, UPSERT support, Alembic migrations
5. **Polars usage** — Consistent use of Polars (no pandas) with lazy loading for large files
6. **Docker setup** — Multi-stage builds, health checks, secrets management, separate dev/test/prod targets
7. **Testing infrastructure** — pytest with async support, MockRedis, test database setup

### Risks
1. **Data leakage risk (HIGH)** — Missing access control on the aggregated data endpoint is the most critical issue. Any authenticated user can query any dashboard's data.
2. **Task queue reliability (MEDIUM)** — In-memory queue means processing tasks are lost on restart. Acceptable for MVP but must be addressed before production.
3. **Hardcoded credentials (MEDIUM)** — Default secrets in docker-compose could lead to misconfigured production deployments.
4. **Registration approval flow (LOW)** — Users created via approval get a hardcoded password with no email notification mechanism.

### Recommended Priority Actions
1. **Immediate:** Add dashboard access check to `GET /api/v1/data/aggregated`
2. **Immediate:** Fix `file.size` null check in upload endpoint
3. **Immediate:** Change `grant_access` endpoint to require admin role
4. **Short-term:** Enforce non-default secrets in production environment
5. **Short-term:** Add email domain blocklist validation to registration
6. **Medium-term:** Migrate task queue from in-memory to Redis/RQ
7. **Medium-term:** Implement proper email notification for registration approval

---

*Audit completed. Total files reviewed: 80+ across backend, frontend, data layer, and infrastructure.*
