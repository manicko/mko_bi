# MKOBI BI Dashboard — Full Audit Report

**Project:** mkobi BI Dashboard  
**Location:** `C:\py_dev\mkobi`  
**Audit Date:** 2026-05-13  
**Auditor:** Kilo (Automated Code Review)  
**Version:** 1.0  

---

## Executive Summary

The mkobi BI Dashboard is a production-ready, full-stack analytics platform built with FastAPI, Polars, PostgreSQL, and React. The codebase demonstrates strong adherence to Clean Architecture on the backend and Feature-Sliced Design on the frontend. Security is well-implemented with JWT authentication, bcrypt password hashing, and Redis-backed rate limiting. The data processing pipeline is robust, leveraging Polars for high-performance transformations with proper retry logic.

**Overall Score: 8.5 / 10** — The system is production-ready with minor improvements recommended.

---

## Table of Contents

1. [Backend Architecture (Clean Architecture)](#1-backend-architecture)
2. [Frontend Architecture (FSD)](#2-frontend-architecture)
3. [Security](#3-security)
4. [Backend API & Business Logic](#4-backend-api--business-logic)
5. [Data Layer](#5-data-layer)
6. [Code Quality](#6-code-quality)
7. [Performance & Stability](#7-performance--stability)
8. [Configuration & Deployment](#8-configuration--deployment)
9. [Findings Summary](#9-findings-summary)
10. [Scoring](#10-scoring)

---

## 1. Backend Architecture

**Score: 9 / 10**

### 1.1 Layered Architecture Compliance

The backend strictly follows Clean Architecture with clear separation across four layers:

| Layer | Path | Responsibility |
|-------|------|----------------|
| **API** | `src/mkobi/api/routes/` | HTTP handlers, request/response models, dependency injection |
| **Services** | `src/mkobi/services/` | Business logic, orchestration, validation |
| **DB / Repositories** | `src/mkobi/db/repositories/` | Data access, SQL queries, ORM interactions |
| **Models** | `src/mkobi/models/` + `src/mkobi/db/models/` | Pydantic schemas (API), SQLAlchemy ORM (DB) |
| **Core** | `src/mkobi/core/` | Security, permissions, logging, Redis client, task queue |
| **Data** | `src/mkobi/data/` | File loading, transformations, aggregation, storage |
| **Workers** | `src/mkobi/workers/` | Background RQ task processing |
| **Interfaces** | `src/mkobi/interfaces/` | Abstract interfaces for DI |

**Strengths:**
- Routes depend on service interfaces, not concrete implementations.
- Services depend on repository interfaces (`IDashboardRepository`, `IUserRepository`, etc.).
- Dependency injection is achieved through FastAPI's `Depends()` mechanism consistently.
- Each layer can be tested independently via interface mocking.

### 1.2 Module Structure

```
src/mkobi/
├── api/
│   ├── deps.py                    # Shared dependencies (DB session, services)
│   ├── __init__.py
│   └── routes/
│       ├── auth.py                # /auth/* endpoints
│       ├── dashboards.py          # /dashboards/* endpoints
│       ├── upload.py              # /upload/* endpoints
│       ├── data.py                # /data/* endpoints
│       ├── graphs.py              # /graphs/* endpoints
│       ├── filters.py             # /filters/* endpoints
│       ├── layouts.py             # /layouts/* endpoints
│       ├── processing_configs.py  # /processing-configs/* endpoints
│       ├── processing_logs.py     # /processing-logs/* endpoints
│       ├── users.py               # /users/* endpoints
│       └── admin.py               # /admin/* endpoints (admin-only)
├── services/
│   ├── __init__.py
│   ├── auth_service.py
│   ├── dashboard_service.py
│   ├── data_service.py
│   ├── graph_service.py
│   ├── filter_service.py
│   ├── layout_service.py
│   ├── processing_config_service.py
│   ├── processing_log_service.py
│   └── user_service.py
├── db/
│   ├── __init__.py
│   ├── base.py                    # Base repository with session helpers
│   ├── models/                    # SQLAlchemy ORM models
│   ├── repositories/              # Concrete repository implementations
│   ├── session.py                 # Async session factory
│   └── starter.py                 # DB initialization
├── models/                        # Pydantic schemas (API layer models)
├── core/
│   ├── security.py                # bcrypt, JWT, rate limiting
│   ├── permissions.py             # Access control logic
│   ├── redis_client.py            # Redis connection
│   ├── task_queue.py              # RQ enqueue helpers
│   ├── logging_config.py          # Structured logging setup
│   └── base_repository.py         # Abstract base repository
├── data/
│   ├── loaders/                   # CSV file loading
│   ├── processing/                # Transformations, aggregation logic
│   ├── storage/                   # StorageManager for aggregates
│   └── __init__.py
└── workers/
    └── data_worker.py             # Background processing tasks
```

---

## 2. Frontend Architecture

**Score: 8.5 / 10**

### 2.1 Feature-Sliced Design Compliance

The frontend follows a clear FSD-inspired structure:

```
frontend/src/
├── app/                           # App shell, providers, routing
├── features/                      # Feature modules
│   ├── auth/
│   │   ├── model/                 # Types, token management
│   │   ├── api/                   # Auth API calls
│   │   └── ui/                    # Auth UI components
│   ├── dashboards/                # Dashboard feature
│   ├── upload/                    # File upload feature
│   └── admin/                     # Admin panel feature
├── shared/                        # Shared utilities, components, API client
└── widgets/                       # Shared widgets
```

**Strengths:**
- **React 18 + TypeScript**: Full type safety with no `any` usage found across the codebase.
- **TanStack Query (React Query)**: Used for server state management, providing caching, background refetching, and optimistic updates.
- **React Hook Form + Zod**: Used for all form validation with proper schema definitions.
- **Plotly.js React**: Used for interactive chart rendering (`react-plotly.js`).
- Each feature is self-contained with clear boundaries.

### 2.2 Token Management (`authToken.ts`)

Located at `frontend/src/features/auth/model/authToken.ts`:

- **Memory-first approach** in production — tokens are not persisted to storage.
- `sessionStorage` used as fallback in development mode.
- Token expiration checking via JWT payload parsing.
- `removeToken()` clears both `memoryToken` and `sessionStorage` — correct behavior.

---

## 3. Security

**Score: 8.5 / 10**

### 3.1 Authentication

| Aspect | Implementation | Status |
|--------|---------------|--------|
| **Password Hashing** | bcrypt with 12 salt rounds, 72-byte truncation | ✅ Correct |
| **JWT Algorithm** | HS256 (configurable) | ✅ Correct |
| **Token Expiration** | 30 min default (configurable) | ✅ Correct |
| **Refresh Mechanism** | JWT re-issuance via `/auth/refresh` | ✅ Correct |
| **Token Storage (Frontend)** | Memory (prod), sessionStorage (dev) | ✅ Correct |

### 3.2 Rate Limiting

- Implemented via `AsyncRateLimiter` (async) and `RateLimiter` (sync) in `src/mkobi/core/security.py`.
- Backed by Redis with atomic increment + TTL pipeline operations.
- Applied on:
  - Login (5 attempts / 5 min per email)
  - File upload (10 attempts / 60 min per user)
  - Registration requests (3 attempts / 60 min per IP/email)

### 3.3 Access Control

- `src/mkobi/core/permissions.py` implements `check_dashboard_access()` function.
- Every protected endpoint validates user permissions before proceeding.
- `DashboardPermission` StrEnum enforces `view`, `edit`, `admin` levels.
- Admin-only endpoints use `require_admin_role` dependency.

### 3.4 Upload Security

- File size validation enforced before reading content.
- MIME-type validation against allowlist.
- File extension validation against `FileExtensionEnum` (CSV, CSV.GZ).
- Upload rate limiting per user.

### 3.5 Docker Secrets

- `SecretsFileSource` in `config.py` supports the `_FILE` suffix pattern.
- Environment variables like `DATABASE__PASSWORD_FILE` point to files containing secret values.
- Maps to nested dict structure (e.g., `DATABASE__PASSWORD_FILE` → `database.password`).

### 3.6 Findings

| # | Sev | File | Finding |
|---|-----|------|---------|
| 1 | **MEDIUM** | `src/mkobi/api/routes/auth.py:43` | `_handle_login()` creates a new `AsyncRateLimiter` instance on every login attempt instead of reusing a shared instance. The `auth_service.py` already caches its rate limiter in `self._rate_limiter` (line 48), but the login route ignores this and creates a fresh one each time. |

---

## 4. Backend API & Business Logic

**Score: 9 / 10**

### 4.1 Route Coverage

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/register` | POST | Admin | Direct user registration (deprecated, use register-request) |
| `/auth/register-request` | POST | Public | Submit registration request |
| `/auth/login` | POST | Public | Email/password login |
| `/auth/login/form` | POST | Public | OAuth2 form login |
| `/auth/refresh` | POST | Authenticated | Refresh JWT token |
| `/auth/me` | GET | Authenticated | Get current user info |
| `/dashboards` | POST | Editor+ | Create dashboard |
| `/dashboards/{id}` | GET | Viewer+ | Get dashboard by ID |
| `/dashboards/{id}` | PATCH | Editor+ | Update dashboard |
| `/dashboards/{id}` | DELETE | Editor+ | Delete dashboard |
| `/upload/{id}` | POST | Editor+ | Upload CSV file |
| `/upload/{id}/process` | POST | Editor+ | Trigger processing |
| `/upload/status/{id}` | GET | Editor+ | Check processing status |
| `/upload/result/{id}` | GET | Editor+ | Get processing result |
| `/data/aggregated` | GET | Viewer+ | Get aggregated data |
| `/admin/users` | GET | Admin | List all users |
| `/admin/users/{id}/role` | PATCH | Admin | Update user role |
| `/admin/users/{id}` | DELETE | Admin | Delete user |
| `/admin/registration-requests` | GET | Admin | List all registration requests |
| `/admin/registration-requests/{id}/approve` | POST | Admin | Approve registration |
| `/admin/registration-requests/{id}/reject` | POST | Admin | Reject registration |

### 4.2 Error Handling

- All routes use try/except patterns with specific HTTPException responses per error type.
- `PermissionError` → 403
- `ValueError` → 422 or context-specific status
- Generic `Exception` → 500
- Global exception handler in `app.py` catches unhandled exceptions.
- All errors include structured logging with relevant context.

### 4.3 Findings

| # | Sev | File | Finding |
|---|-----|------|---------|
| 2 | **MEDIUM** | `src/mkobi/api/routes/upload.py:126-209` | Significant code duplication between the inner `try/except ValueError` block (lines 126–157) and the outer `try/except ValueError` block (lines 178–209). The ValueError classification logic (mime, format, size, limit checks) is repeated verbatim in both blocks. The inner block is unreachable since `data_service.process_upload` doesn't raise `ValueError` — only `PermissionError` and generic `Exception` are raised from it. |
| 3 | **LOW** | `src/mkobi/api/routes/admin.py:32-53` | `GET /admin/users` returns all users without pagination. Could cause performance issues with large user bases. |
| 4 | **LOW** | `src/mkobi/api/routes/admin.py:128-150` | `GET /admin/registration-requests` returns all requests without pagination. |

---

## 5. Data Layer

**Score: 9 / 10**

### 5.1 Database Schema

- PostgreSQL with asyncpg driver.
- SQLAlchemy 2.0 declarative models with proper relationships.
- CASCADE deletes configured on related entities (dashboard → graphs → aggregated data).
- All models defined in `src/mkobi/db/models/`.

### 5.2 Indexing Strategy

| Index Type | Table | Column(s) | Purpose |
|------------|-------|-----------|---------|
| Primary Key | `dashboards` | `id` | Unique identification |
| Primary Key | `users` | `id` | Unique identification |
| Unique | `users` | `email` | Prevent duplicate emails |
| GIN | `aggregated_data` | `dims` (JSONB) | Fast dimension lookups |
| Index | `access` | `dashboard_id, user_id` | Access check optimization |
| Index | `graphs` | `dashboard_id` | Graph retrieval by dashboard |

### 5.3 Migrations

- Alembic with proper `upgrade()` and `downgrade()` support in all migration scripts.
- Migration directory at `alembic/versions/`.
- Configuration via `alembic.ini` and `env.py`.

### 5.4 Repository Pattern

All repositories implement abstract interfaces declared in `src/mkobi/interfaces/repository_interfaces/`:

- `IDashboardRepository` — CRUD + `get_by_user`, `get_by_name`
- `IUserRepository` — CRUD + `get_by_email`, `get_by_email_with_hash`
- `IAccessRepository` — `grant_access`, `revoke_access`, `check_access`
- `IGraphRepository` — CRUD + `get_by_dashboard_id`
- `IAggregatedDataRepository` — `get_by_graph_id`, `save_aggregates`
- `IProcessingLogRepository` — CRUD + `get_by_id`
- `IRegistrationRequestRepository` — CRUD + `get_by_email`
- `IFilterRepository`, `IDashboardFilterRepository`, `ILayoutRepository`, `IProcessingConfigRepository`

### 5.5 Findings

| # | Sev | File | Finding |
|---|-----|------|---------|
| 5 | **LOW** | `src/mkobi/db/repositories/dashboard_repo.py:57-85` | `get_by_user()` performs a JOIN with `DashboardAccess` but only returns dashboard objects without the access permission level. Callers that need the permission level must make a separate query. Including the permission in the return value would reduce DB round-trips in `dashboard_service.py`. |

---

## 6. Code Quality

**Score: 8.5 / 10**

### 6.1 Python Standards

- **Type hints**: All public functions and methods include full type annotations.
- **StrEnum usage**: All enumerated values use `StrEnum` throughout — `UserRole`, `DashboardPermission`, `GraphType`, `FileExtensionEnum`, `MimeTypeEnum`, `ProcessingStatus`, `UploadMode`, `EnvironmentEnum`, `RegistrationStatus`.
- **Logging**: Consistent use of `logging.getLogger(__name__)` in every module. No `print()` calls found anywhere in the codebase.
- **Docstrings**: All public functions, classes, and methods have docstrings with Args/Returns/Raises sections.
- **Error handling**: Specific exceptions caught rather than bare `except` in most locations.

### 6.2 TypeScript Standards

- Strict mode enabled.
- No `any` type usage found — proper types defined for all data structures.
- Interface-based type definitions in `model/` subdirectories.
- Consistent naming conventions (camelCase for variables, PascalCase for types/interfaces).

### 6.3 Linting & Formatting

- **Ruff** configured for linting and formatting.
- **mypy** configured for type checking (`mypy.ini` present).
- **pyproject.toml** centralizes all tool configuration.

### 6.4 Findings

| # | Sev | File | Finding |
|---|-----|------|---------|
| 6 | **LOW** | `src/mkobi/config.py:17-29` | `_set_nested_value()` modifies the dict argument in-place and returns `None`. The docstring documents the behavior but the return type could be annotated more explicitly to signal that the function is a mutator, not a factory. |

---

## 7. Performance & Stability

**Score: 8 / 10**

### 7.1 Polars Usage

- Polars is the sole data processing engine — **pandas is not used anywhere**.
- CSV loading via `CSVLoader` with `pl.read_csv()`.
- Transformations applied via `apply_transformations()` in `src/mkobi/data/processing/transformations.py`.
- Aggregations via `calculate_aggregations()` with support for groupby, YoY comparisons, share calculations, and custom metrics.
- All Polars operations that are synchronous are wrapped in `asyncio.to_thread()` to avoid blocking the event loop.

### 7.2 Connection Pooling

- SQLAlchemy async engine configured with connection pooling (default pool size of 5, max overflow of 10).
- Redis connection managed via `redis.asyncio` with shared client instances.

### 7.3 Temp File Management

- Temp files created in `data/tmp_uploads/` with UUID-based names.
- Cleanup occurs in two places:
  - **Worker** (`data_worker.py:158-160`): Deletes file after successful processing.
  - **Worker** (`data_worker.py:181-185`): Deletes file on processing failure.
  - **DataService** (`data_service.py:605-619`): `cleanup_task_files()` function provides manual cleanup of task files.
- Temp directory auto-created on startup via `Settings._ensure_upload_dir()`.

### 7.4 Findings

| # | Sev | File | Finding |
|---|-----|------|---------|
| 7 | **MEDIUM** | `src/mkobi/workers/data_worker.py:226` | `_store_aggregates()` uses `df.columns[:3]` to determine which columns are dimensions. This **assumes the first 3 columns are always dimensions**, which breaks if column order changes or if a dashboard has a different number of dimension columns. The graph configuration (`graph.dimensions`) should be used instead to correctly partition dims vs. metrics. |
| 8 | **MEDIUM** | `src/mkobi/api/routes/upload.py:101-102` | `file_content = await file.read()` loads the entire file into memory before processing. For files near the 100MB limit, this could cause memory pressure. Consider streaming the file to a temp file first and reading from disk for large uploads. |

---

## 8. Configuration & Deployment

**Score: 9 / 10**

### 8.1 Configuration Management

- **pydantic-settings** used with `BaseSettings` for environment-based configuration.
- Configuration hierarchy (highest to lowest priority):
  1. Environment variables (e.g., `DATABASE__PASSWORD`)
  2. Docker secrets files (e.g., `DATABASE__PASSWORD_FILE=/run/secrets/db_password`)
  3. `.env` file (development)
  4. YAML config file (`settings/app.yaml`)
  5. Default values in code
- Nested configuration using `__` delimiter (e.g., `DATABASE__HOST` → `database.host`).

### 8.2 Docker

**Dockerfile:** Multi-stage build with three targets:

| Target | Base Image | Purpose |
|--------|-----------|---------|
| `base` | Python 3.12 slim | Shared dependencies |
| `dev` | `base` | Development with hot reload |
| `test` | `base` | Test execution |
| `prod` | `python:3.12-alpine` | Production (minimal image) |

- Production stage installs only production dependencies.
- Runs as non-root user.
- Healthcheck endpoint at `/health`.

**docker-compose.yml:**
- Three services: `app`, `postgres`, `redis`.
- Healthchecks configured on all services.
- Named volumes for PostgreSQL data persistence.
- Environment variables from `.env` or passed directly.
- Override file (`docker-compose.override.yml`) for development.

**nginx/**: Reverse proxy configuration for production deployment.

### 8.3 Task Queue

- Redis Queue (RQ) used for background job processing.
- `src/mkobi/core/task_queue.py` provides `enqueue_job()` wrapper.
- Worker entry points: `process_csv_background` (async) and `process_csv_background_sync` (sync wrapper for RQ).

---

## 9. Findings Summary

### 9.1 Issues by Severity

| # | Severity | Category | File | Summary |
|---|----------|----------|------|---------|
| 1 | **MEDIUM** | Data Layer | `workers/data_worker.py:226` | `df.columns[:3]` hardcodes dimension count; should use graph configuration |
| 2 | **MEDIUM** | Services | `services/dashboard_service.py:186` | `_dashboard_to_read()` catches broad `Exception`; should catch specific types |
| 3 | **MEDIUM** | API Routes | `api/routes/upload.py:126-209` | Duplicate ValueError handling between inner and outer except blocks |
| 4 | **MEDIUM** | Security | `api/routes/auth.py:43` | New `AsyncRateLimiter` created per login request instead of reusing shared instance |
| 5 | **MEDIUM** | Performance | `api/routes/upload.py:101` | Entire file loaded into memory; could cause issues near 100MB limit |
| 6 | **LOW** | Code Quality | `config.py:17` | `_set_nested_value` mutates dict in-place without clear return documentation |
| 7 | **LOW** | Data Layer | `db/repositories/dashboard_repo.py:57` | JOIN query doesn't return access permission, requiring separate query |
| 8 | **LOW** | Frontend | `frontend/src/features/auth/model/authToken.ts` | `removeToken()` accesses `sessionStorage` even in production mode (though it's a no-op since `memoryToken` is set to null first and production only reads memory) |
| 9 | **LOW** | API Routes | `api/routes/admin.py:32,128` | Missing pagination on user list and registration requests endpoints |

### 9.2 Positive Findings (Strengths)

| # | Category | Detail |
|---|----------|--------|
| 10 | **INFO** | Registry pipeline uses tenacity with exponential backoff (3 attempts, 4–10s wait) for transient DB errors |
| 11 | **INFO** | Temp file cleanup handled redundantly in both worker and data_service — no orphaned files |
| 12 | **INFO** | Docker Compose includes healthchecks for PostgreSQL, Redis, and the application |

---

## 10. Scoring

| Category | Score | Notes |
|----------|-------|-------|
| **Architecture** | **9 / 10** | Clean Architecture properly implemented; clear layer boundaries |
| **Security** | **8.5 / 10** | Strong bcrypt/JWT/rate-limiting; rate limiter instantiation could be optimized |
| **Code Quality** | **8.5 / 10** | Full type hints, StrEnum, logging — minor documentation gap |
| **Data Layer** | **9 / 10** | Proper repository pattern, GIN indexes, CASCADE deletes, Alembic migrations |
| **Performance** | **8 / 10** | Polars usage correct; dimension partitioning fragile; file upload memory concern |
| **Deployment** | **9 / 10** | Multi-stage Docker, healthchecks, Docker secrets, structured config |
| **Frontend** | **8.5 / 10** | React 18/TS with proper patterns; TanStack Query and React Hook Form well-used |
| **OVERALL** | **8.5 / 10** | Production-ready with minor improvements recommended |

---

## Recommendations

### Priority 1 — Medium Issues (resolve before next release)

1. **Fix dimension/metric partitioning** — Replace `df.columns[:3]` in `_store_aggregates()` with graph-aware logic that reads `graph.dimensions` and `graph.metrics` to determine column roles.

2. **Deduplicate upload error handling** — Extract the ValueError → HTTPException mapping into a shared helper function or remove the outer `except ValueError` block entirely since inner handling covers it.

3. **Cache rate limiter instance** — Inject a shared `AsyncRateLimiter` instance into `_handle_login()` instead of creating one per request. The `AuthService` already demonstrates this pattern with `self._rate_limiter`.

4. **Narrow exception catching** — In `_dashboard_to_read()`, replace `except Exception` with specific exception types (e.g., `ValidationError`, `KeyError`).

5. **Stream file uploads** — For files above a threshold, write directly to a temp file via streaming instead of buffering the entire content in memory.

### Priority 2 — Low Issues (schedule for future sprint)

6. **Add pagination** — Implement `page`/`limit` query parameters on `GET /admin/users` and `GET /admin/registration-requests`.

7. **Return permission in dashboard queries** — Include the access permission level in `get_by_user()` results to avoid a second query in the service layer.

8. **Document mutator functions** — Add return type annotations and docstring notes for functions like `_set_nested_value` that modify arguments in-place.

9. **Frontend token cleanup** — Ensure `removeToken()` behavior is consistent across environments; consider always calling `sessionStorage.removeItem()` regardless of environment for safety.

---

*End of audit report.*