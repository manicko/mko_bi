---
name: audit-project-general
description: audit-project-general
agent: auditor
alwaysApply: false
---

# General Project Audit — mkobi BI Dashboard

## Objective

Perform a general audit of the **mkobi** project (Backend + Frontend + Data Layer + DevOps) for compliance with:
- Project specification (`docs/SPEC.md` and all `docs/**/*.md`)
- Clean Architecture (backend) and Feature-Sliced Design (frontend) principles
- Code quality, security, and maintainability standards

**Guiding principle:** Production code must be understandable, safe, maintainable, and specification-compliant. Simplicity is preferred over unnecessary complexity.

---

## Audit Rules

**Inspection order:**
1. Specification compliance
2. Architecture and Separation of Concerns
3. Security and reliability
4. Code quality and type safety
5. Performance and maintainability

**Do NOT flag as issues:**
- Simple, readable, and consistent solutions
- Minimal architecture (if consistent and extensible)
- Absence of enterprise patterns where not needed

**Flag as CRITICAL:**
- Security vulnerabilities (SQL injection, path traversal, secret leaks)
- Layer mixing / business logic in route handlers
- Data loss or missing temp file cleanup
- `print()` instead of structured logging
- Missing `StrEnum` for fixed-value constants
- Missing type hints / `any` in TypeScript
- Access control bypass or missing enforcement
- Missing JSONB normalization (dims key sorting)
- Production credential enforcement failures

---

## BLOCK 1 — Architecture & Project Structure

### 1.1 Backend (Clean Architecture)

Verify `src/mkobi/` layer separation:

| Layer | Directory | Responsibility |
|-------|-----------|----------------|
| API | `src/mkobi/api/` | Routing, input validation, service calls only |
| Services | `src/mkobi/services/` | All business logic |
| Repositories | `src/mkobi/db/repositories/` | Data access via SQLAlchemy async |
| Models | `src/mkobi/models/` | Pydantic v2 + StrEnum definitions |
| DB Models | `src/mkobi/db/models/` | SQLAlchemy ORM models |
| Core | `src/mkobi/core/` | Security, permissions, logging, config, task queue |
| Data | `src/mkobi/data/` | Polars loaders, transformations, storage |
| Interfaces | `src/mkobi/interfaces/` | DI abstractions |
| Workers | `src/mkobi/workers/` | Background task functions |

**Forbidden:**
- Business logic in route handlers
- SQL in API layer
- Cyclic imports
- Global mutable state
- `pandas` imports (Polars only)

### 1.2 Frontend (Feature-Sliced Design)

Verify `frontend/src/` structure:
- `app/` — providers, routing
- `features/` — business features (auth, dashboards, upload, admin, users)
- `shared/` — reusable code (api, components, types)

Each feature must separate: `ui/`, `api/`, `model/`, `types/`.

### 1.3 Data Processing Pipeline

Verify the pipeline in `src/mkobi/data/`:
- Upload → Parse (Polars) → Transform → Aggregate → Save → Cleanup
- Polars used exclusively (no pandas)
- Temp file cleanup via `platformdirs` in `finally` blocks
- JSONB key normalization (recursive sort) before writes

---

## BLOCK 2 — Security & Access Control

### 2.1 Authentication & JWT
- Login returns `TokenWithUser` (token + user profile with `display_name`)
- JWT algorithm explicitly set (not default)
- JWT expiration validated
- bcrypt for password hashing (no plaintext, no MD5/SHA)
- Rate limiting on login (5/5min per email) and register-request (3/hour per IP/email)

### 2.2 Access Control
- `dashboard_access` checked on every dashboard-related request
- Admin bypass: admins see all dashboards without explicit `dashboard_access` entries
- 403/404 dual-signal: 404 for not-found, 403 for no-access (prevents ID enumeration)
- Role checks use `UserRole` StrEnum, not string literals
- Permission checks use `DashboardPermission` StrEnum

### 2.3 Upload Security
- MIME-type whitelist: `text/csv`, `application/gzip`, `application/x-gzip`
- File extension validation: `.csv`, `.csv.gz`
- Max file size enforced
- Path traversal protection
- Temp file cleanup after processing (success and failure)
- Rate limiting on upload endpoints

### 2.4 Secrets & Config
- No hardcoded secrets
- Pydantic-settings with nested env vars (`DATABASE__HOST`, `JWT__SECRET_KEY`)
- Docker secrets support (`_FILE` suffix)
- Production credential enforcement (refuses to start with default `admin`/`admin`)
- CORS: explicit origins, methods, headers (no wildcards in production)

### 2.5 Rate Limiting
- Redis-based sliding window
- Fail-open (default) vs fail-closed (production recommendation)
- Health tracking when Redis is unavailable

---

## BLOCK 3 — Backend API & Business Logic

### 3.1 Auth Endpoints
- `POST /api/v1/auth/login` → `TokenWithUser` (token + user with `display_name`)
- `POST /api/v1/auth/login/form` → OAuth2 form variant
- `POST /api/v1/auth/register-request` → creates `registration_requests` record
- `POST /api/v1/auth/refresh` → token refresh
- `GET /api/v1/auth/me` → current user profile
- `POST /api/v1/auth/change-password` → password change

### 3.2 Dashboard Endpoints
- `GET /api/v1/dashboards/my` — lists accessible dashboards (admin sees all)
- `GET /api/v1/dashboards/:id` — 403/404 dual-signal
- `POST /api/v1/dashboards` — admin only
- `PUT /api/v1/dashboards/:id` — admin only
- `DELETE /api/v1/dashboards/:id` — admin only, cascading delete

### 3.3 Data & Upload Endpoints
- `POST /api/v1/upload/:dashboard_id?mode=overwrite|append`
- `POST /api/v1/upload/:dashboard_id/process` — manual trigger
- `GET /api/v1/upload/status/:task_id`
- `GET /api/v1/upload/result/:task_id`
- `GET /api/v1/data/aggregated?dashboard_id=&graph_id=&filters=`

### 3.4 Admin Endpoints
- `GET /api/v1/admin/users`
- `PATCH /api/v1/admin/users/:id/role`
- `DELETE /api/v1/admin/users/:id`
- `GET /api/v1/admin/registration-requests`
- `POST /api/v1/admin/registration-requests/:id/approve`
- `POST /api/v1/admin/registration-requests/:id/reject`
- `GET /api/v1/admin/logs`
- `GET /api/v1/admin/logs/:log_id`

### 3.5 Health Endpoints
- `GET /health` — basic health + DB connectivity
- `GET /health/detailed` — per-component status
- `GET /` — API identification

### 3.6 All Endpoints Must:
- Use Pydantic models for request/response validation
- Return proper HTTP status codes via `HTTPException`
- Enforce access control
- Use structured logging (no `print()`)

---

## BLOCK 4 — Data Layer (PostgreSQL)

### 4.1 Schema Compliance
Verify all 10 tables match specification:
- `users` — UUID PK, `user_role` ENUM, bcrypt password_hash
- `layouts` — UUID PK, JSONB definition
- `dashboards` — UUID PK, FK to layouts/users (SET NULL), JSONB config
- `graphs` — UUID PK, FK to dashboards (CASCADE), `graph_type` ENUM, JSONB config/dimensions/metrics
- `filters` — UUID PK, `filter_type` ENUM, JSONB config
- `dashboard_access` — composite PK (user_id, dashboard_id), `dashboard_permission_level` ENUM
- `dashboard_filters` — composite PK (dashboard_id, filter_id)
- `processing_configs` — dashboard_id PK/FK, JSONB settings
- `aggregated_data` — BIGSERIAL PK, FK to dashboards/graphs (CASCADE), JSONB dims/metrics
- `processing_logs` — UUID PK, `processing_status` ENUM, timestamps
- `registration_requests` — UUID PK, `registration_status` ENUM, INET IP

### 4.2 JSONB Usage
- `aggregated_data.dims` — dimension key-value pairs
- `aggregated_data.metrics` — metric key-value pairs
- `dims` keys sorted recursively before writes (UPSERT determinism)
- GIN index on `dims` for containment queries
- Unique index on `(dashboard_id, graph_id, dims::text)` for UPSERT

### 4.3 Indexes
Verify all indexes from `docs/09-database/indexes.md`:
- 7 core indexes (SPEC.md section 16.2)
- Additional unique indexes on names, composite keys
- GIN index on `aggregated_data.dims`

### 4.4 Migrations
- Alembic migration chain is intact and reproducible
- All migrations apply cleanly from empty database
- Downgrade paths exist and are tested
- No manual SQL changes outside migrations

---

## BLOCK 5 — StrEnum Usage

All fixed values must use `StrEnum` (17 classes per spec):

| StrEnum | Values | PostgreSQL ENUM |
|---------|--------|-----------------|
| `UserRole` | admin, editor, viewer | `user_role` |
| `DashboardPermission` | view, edit, admin | `dashboard_permission_level` |
| `GraphType` | bar, line, pie, table | `graph_type` |
| `FilterType` | select, multiselect, range, date | `filter_type` |
| `RegistrationStatus` | pending, approved, rejected | `registration_status` |
| `UploadMode` | overwrite, append | — |
| `ProcessingStatus` | started, uploaded, processing, success, failed, completed | `processing_status` |
| `EnvironmentEnum` | production, staging, development, test | — |
| `MimeTypeEnum` | text/csv, application/gzip, application/x-gzip | — |
| `FileExtensionEnum` | csv, csv.gz | — |
| `AggregationFunctionEnum` | sum, mean, count, min, max, median, std, var, first, last | — |
| `FilterOperatorEnum` | ==, !=, >, <, >=, <= | — |
| `OrientationEnum` | v, h | — |
| `BarmodeEnum` | group, stack | — |
| `YoyModeEnum` | absolute, percent | — |
| `ButtonVariant` | primary, secondary, success, danger, warning, info, light, dark | — |
| `ComponentSize` | sm, md, lg | — |

**Forbidden:** string literals for role/status/type checks (e.g., `if user.role == "admin"`).

---

## BLOCK 6 — Code Quality

### 6.1 Backend
- Full type hints on all public functions (parameters + return types)
- Pydantic v2 models for all API boundaries
- `logger = logging.getLogger(__name__)` — no `print()`
- Async correctness (no blocking I/O in async endpoints)
- Error handling: no swallowed exceptions, no broad `except Exception`
- English-only comments, logs, and docstrings

### 6.2 Frontend
- TypeScript with strict mode — no `any`
- TanStack Query for server state (no Redux/Zustand)
- React Hook Form + Zod for form validation
- Plotly.js React for charts (bar, line, pie, table)
- `axiosInstance` with JWT interceptors (no hardcoded URLs)
- `ProtectedRoute` and `RoleBasedAccess` components
- No `console.log()` in production code

---

## BLOCK 7 — Performance & Stability

- Polars used for all data processing (memory-efficient)
- Connection pooling (asyncpg)
- Rate limiting on sensitive endpoints
- Temp file cleanup (no disk leaks)
- JSONB GIN index for filter queries
- N+1 query detection in repositories
- Task queue: in-memory (MVP) with Redis/RQ migration path

---

## BLOCK 8 — Configuration & Deployment

- Pydantic-settings with nested env vars
- Config priority: env vars > Docker secrets > .env > app.yaml > defaults
- Multi-stage Dockerfile (dev, test, prod, prod-slim)
- Docker Compose with service separation (app, db, redis)
- Health checks configured for load balancers
- Production: FastAPI serves static files OR Nginx reverse proxy
- `AUTO_MIGRATE=true` for containerized deployments

---

## Report Format

Create file: `C:\py_dev\mkobi\.ai\audit\project\audit_report_<number>.md` (next available number)

### Report Structure:

1. **Executive Summary** — Quality scores 1–10 per area + overall readiness
2. **Architecture Compliance** — Clean Architecture + FSD adherence
3. **Security Assessment** — Auth, access control, upload, secrets
4. **Requirements Coverage** — PASS/FAIL table against SPEC
5. **Critical Findings** — Table with severity
6. **Findings & Recommendations** — Grouped by severity
7. **Missing / Partially Implemented Features**
8. **Final Assessment & Risks**

**Findings table format:**

| Severity | Component | File | Problem | Recommendation |
|----------|-----------|------|---------|----------------|
| CRITICAL | Security | upload.py | No temp file cleanup | Add `finally` block with `os.remove()` |
| HIGH | Auth | routes.py | String literal role check | Use `UserRole.ADMIN` StrEnum |
| MEDIUM | API | dashboards.py | Missing rate limit | Add `@rate_limit` decorator |

---

**Auditor rule:** Prefer simple and reliable over complex and "correct." The primary criteria are **maintainability** and **safety**.
