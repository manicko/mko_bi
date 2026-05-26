---
name: audit-project-detailed
description: audit-project-detailed
agent: auditor
alwaysApply: false
---

# Detailed Project Audit — mkobi BI Dashboard

> **Prerequisite:** Docker services must be running before executing tests, lint, or type checks. See: `docs/11-guides/docker.md`

## Objective

Audit the BI Dashboard System for:
1. **Spec compliance** — does code match `docs/SPEC.md` and related docs?
2. **Best practices** — does it follow current standards beyond the spec?
3. **Doc accuracy** — when code legitimately diverges, recommend updating docs.

Spec docs are the **baseline**, not the target. Recommend evolution, not just compliance.

## Recommendation Types

Label every finding:
- `[SPEC-DEVIATION]` — code differs from docs. Decide: fix code or update docs.
- `[BEST-PRACTICE]` — improvement beyond current spec. Advisory, not mandatory.
- `[DOC-UPDATE]` — docs should reflect current code reality or new direction.

## Research

Use `websearch` to verify current best practices for:
- FastAPI async patterns, security, and deployment
- React 18+ performance, hooks patterns, bundle optimization
- PostgreSQL JSONB query patterns, index strategies
- Polars lazy evaluation and memory efficiency

---

# Audit Rules

## Core Principles

Inspection order:

1. Specification compliance (`docs/SPEC.md` + all `docs/**/*.md`)
2. Implementation correctness
3. Code quality

**Do NOT flag as issues:**

- Simple architecture that is consistent, readable, testable, and extensible
- Minimal abstraction layers
- Absence of enterprise patterns where not needed

**Flag as CRITICAL:**

- Security vulnerabilities
- Access control violations
- Data loss or corruption
- Mixed responsibilities (business logic in routes)
- Unstable data processing
- Async/blocking issues
- Hardcoded behavior
- Missing validation
- `print()` instead of logging
- Missing `StrEnum` where dict/list used for constants

---

# BLOCK 1 — Project Structure & Architecture

## 1.1 Backend Structure (`src/mkobi/`)

Verify Clean Architecture compliance:

### Application Layers

| Layer | Directory | Responsibility |
|-------|-----------|----------------|
| API Layer | `src/mkobi/api/routes/` | HTTP only, input validation, service calls |
| Service Layer | `src/mkobi/services/` | Business logic, orchestration |
| Repository Layer | `src/mkobi/db/repositories/` | Data access, SQL queries |
| Model Layer | `src/mkobi/models/` | Pydantic models for API |
| DB Models | `src/mkobi/db/models/` | SQLAlchemy ORM models |
| Interfaces | `src/mkobi/interfaces/` | DI abstractions |
| Core | `src/mkobi/core/` | Security, permissions, logging, config, task queue |
| Data Processing | `src/mkobi/data/` | Loaders, processing, storage |
| Config | `src/mkobi/config.py`, `src/mkobi/settings/` | Centralized configuration |
| Workers | `src/mkobi/workers/` | Background task functions |

### Verify Absence Of

- Business logic inside route handlers
- SQL inside controllers/routes
- Global mutable state
- Cyclic imports
- Hidden side effects
- Mixed responsibilities between layers

### Verify Presence Of

- Dependency Injection (via `src/mkobi/api/deps.py`)
- Config centralization (pydantic-settings, env vars, Docker secrets)
- Logging centralization (`src/mkobi/core/logging_config.py`)
- Enum usage (StrEnum in `src/mkobi/models/enums.py`)
- Task queue (`src/mkobi/core/task_queue.py` — in-memory MVP)

## 1.2 Frontend Structure (`frontend/src/`)

Verify Feature-Sliced Design (FSD) compliance:

### Structure

```
frontend/src/
├── app/                    # Initialization, providers
│   ├── providers.tsx       # QueryClient, Router, Theme
│   └── routes.tsx          # All routes
├── features/               # Business features
│   ├── auth/
│   ├── dashboards/
│   ├── upload/
│   ├── users/
│   └── admin/
├── shared/                 # Reusable code
│   ├── api/               # axiosInstance, errorHandling
│   ├── components/         # ProtectedRoute, Layout, RoleBasedAccess
│   ├── config/            # constants
│   └── types/             # api.types.ts
└── main.tsx
```

### Verify Per Feature

- **ui/**: React components (UI logic only)
- **api/**: API calls (axios, TanStack Query)
- **model/**: State, hooks (useAuth, useDashboards)
- **types/**: TypeScript types

### Verify Absence Of

- Business logic in components
- Duplicated API calls
- Hardcoded URLs (use axiosInstance)
- Mixed responsibilities

## 1.3 Processing Pipeline

Verify `src/mkobi/data/`:

Pipeline must be:

- Explicit (readable stages)
- Split into steps: upload → parse → transform → aggregate → save → cleanup
- Use Polars (NOT pandas)
- Have correct error handling
- Clean up temp files (`platformdirs`, `finally` blocks)
- Normalize JSONB `dims` keys (recursive sort) before writes for deterministic UPSERT

Verify files:

- `loaders/loader.py`: CSV/CSV.gz loading and validation
- `processing/transformations.py`: transformations, aggregations
- `processing/registry.py`: handler registry
- `storage/manager.py`: save to PostgreSQL (JSONB)

---

# BLOCK 1.5 — Runtime Verification (Docker)

> **Prerequisite:** Docker must be running. See `docs/11-guides/docker.md`.

## 1.5.1 Start Services

Start all services in development mode:

```powershell
docker compose -f docker/docker-compose.yml -f docker/docker-compose.override.yml --env-file .env up -d
```

Wait for all containers to be healthy. Check with `docker compose ps`.

## 1.5.2 Container Health Check

For each running container (`app`, `frontend`, `db`, `redis`):

1. **Check logs for errors/warnings** — `docker compose logs <service>`
2. **Check for restart loops** — look for repeated shutdown/startup cycles (e.g., `StatReload detected changes` firing repeatedly)
3. **Check for config errors** — missing env vars, volume mount issues

Flag as CRITICAL:
- Container crash loops
- Backend restarting due to volume-triggered hot reload from mounted `tests/` or `__pycache__/`
- Frontend failing to start

## 1.5.3 Frontend Rendering Verification

1. **Fetch frontend index** from both dev server (5173) and backend (8000):
   - `GET http://localhost:5173/` — must return 200 with valid HTML
   - `GET http://localhost:8000/` — must return 200 with valid HTML

2. **Check for JavaScript runtime errors:**
   - Load the page in a browser and check console for errors
   - Common issues: invalid React Router usage (non-`<Route>` children inside `<Routes>`), missing imports, runtime type errors
   - Verify the React app actually renders — not stuck on ErrorBoundary fallback ("Something went wrong")

3. **Verify asset availability:**
   - JS bundle referenced in index.html must be fetchable (hash must match actual file on disk)
   - Check both the host-built `frontend/dist/` and the container's `/app/frontend/dist/` are consistent

## 1.5.4 Cross-Service Connectivity

1. **Frontend → Backend proxy:**
   - From inside the frontend container, verify `http://app:8000/health` responds
   - Verify API calls from the browser reach the backend (check backend logs for proxied requests)

2. **Backend → Database:**
   - Verify health check shows `{"status":"healthy","database":"connected"}`
   - Run a test login API call and confirm it succeeds with valid credentials

## 1.5.5 Critical User Flow Smoke Test

Perform these checks and flag any failures as CRITICAL:

| Flow | Check | Expected |
|------|-------|----------|
| Load `/login` (frontend dev) | Page renders, no console errors | Login form with email/password fields visible |
| Load `/` (backend port 8000) | Index.html serves JS bundle | JS bundle hash matches actual file in `frontend/dist/assets/` |
| Login API | `POST /api/v1/auth/login` with admin credentials | Returns 200 with `access_token` |
| Frontend API proxy | Frontend makes `/api/v1/...` call through Vite proxy | Backend receives the request (check app logs) |

Flag failures with evidence: error messages, HTTP status codes, container log excerpts.

---

# BLOCK 2 — Backend API Layer (FastAPI)

## 2.1 Auth Endpoints

Verify `src/mkobi/api/routes/auth.py`:

### Endpoints

- `POST /api/v1/auth/login` → `TokenWithUser` (token + user with `display_name`)
- `POST /api/v1/auth/login/form` → OAuth2 form variant
- `POST /api/v1/auth/register-request` → `{message, id}`
- `POST /api/v1/auth/refresh` → `{access_token, token_type}`
- `GET /api/v1/auth/me` → `UserProfile`
- `POST /api/v1/auth/change-password` → `{message}`

### Verify

- Login returns `TokenWithUser` (token + full user profile including computed `display_name`)
- `display_name` is derived from email prefix (text before `@`)
- JWT generation (correct algorithm explicitly set, expiration)
- JWT validation (dependencies in `deps.py`)
- Password hashing (bcrypt, NOT plaintext)
- Email validation (Pydantic `EmailStr`)
- Rate limiting on login (5/5min per email) and register-request (3/hour per IP/email)
- No `print()`, only `logger`
- Refresh token verifies user still exists in DB
- Change-password requires current password, user stays logged in after change

## 2.2 Dashboard Endpoints

Verify `src/mkobi/api/routes/dashboards.py`:

### Endpoints

- `GET /api/v1/dashboards/my` → `DashboardSummary[]` (admin sees all)
- `GET /api/v1/dashboards/:id` → `DashboardDetail` (403/404 dual-signal)
- `POST /api/v1/dashboards` (admin only)
- `PUT /api/v1/dashboards/:id` (admin only)
- `DELETE /api/v1/dashboards/:id` (admin only, cascading)

### Verify

- Access validation (user ↔ dashboard via `dashboard_access`)
- Admin bypass: admins see all dashboards without explicit `dashboard_access` entries
- 403/404 dual-signal: 404 for not-found, 403 for exists-but-no-access
- Role-based permissions (admin/editor/viewer)
- Correct Pydantic models (`src/mkobi/models/dashboard.py`)
- Layout relationship (layout_id → layouts table)
- Errors via `HTTPException` (NOT `print`)

## 2.3 Data & Upload Endpoints

Verify `src/mkobi/api/routes/data.py` and `src/mkobi/api/routes/upload.py`:

### Endpoints

- `GET /api/v1/data/aggregated?dashboard_id=&graph_id=&filters=`
- `POST /api/v1/upload/:dashboard_id?mode=overwrite|append`
- `POST /api/v1/upload/:dashboard_id/process?task_id=`
- `GET /api/v1/upload/status/:task_id`
- `GET /api/v1/upload/result/:task_id`

### Verify Upload

- File type validation (MIME: `text/csv`, `application/gzip`, `application/x-gzip`)
- File extension validation (`.csv`, `.csv.gz`)
- UTF-8 encoding validation
- Max file size limit
- Temp file cleanup (`platformdirs`, `finally` block — both success and failure)
- CSV.gz handling (gzip decompression)
- Path traversal protection
- Unsafe filename handling
- Rate limiting
- Task ownership validation on manual trigger (task belongs to dashboard)

### Verify Data API

- Filters applied on backend (SQL/Polars)
- JSONB `dims` filtering (GIN index usage)
- Dashboard access validation
- `dims` keys sorted recursively before storage (UPSERT determinism)

## 2.4 Admin Endpoints

Verify `src/mkobi/api/routes/admin.py`:

### Endpoints

- `GET /api/v1/admin/users` → `User[]`
- `PATCH /api/v1/admin/users/:id/role`
- `DELETE /api/v1/admin/users/:id`
- `GET /api/v1/admin/registration-requests` (with status filter)
- `POST /api/v1/admin/registration-requests/:id/approve`
- `POST /api/v1/admin/registration-requests/:id/reject`
- `GET /api/v1/admin/logs` (with pagination, status/dashboard filters)
- `GET /api/v1/admin/logs/:log_id`

### Verify

- Only admin can execute
- Registration request approval flow:
  - Creates user with random temp password (`secrets.token_urlsafe(16)`)
  - Temp password returned in response (admin communicates to user)
  - Updates request status to `approved`, sets `reviewed_by` and `reviewed_at`
- Rejection updates status to `rejected`
- Cannot approve/reject already-processed requests (409 Conflict)
- No sensitive data leakage (password_hash excluded from responses)
- Processing logs include pagination (`page`, `page_size`, `total`)

## 2.5 Health Endpoints

Verify:

- `GET /health` → `{status, database}` (200 healthy, 503 unhealthy)
- `GET /health/detailed` → `{status, components: {database, static_files}}`
- `GET /` → `{message, status, version}`
- Health checks execute `SELECT 1` against PostgreSQL
- Detailed check verifies `frontend/dist` directory exists

## 2.6 Other Endpoints

Verify:

- `src/mkobi/api/routes/users.py`: user CRUD, profile, self-deletion (`DELETE /users/me`)
- `src/mkobi/api/routes/filters.py`: filter CRUD
- `src/mkobi/api/routes/graphs.py`: graph CRUD
- `src/mkobi/api/routes/layouts.py`: layout CRUD
- `src/mkobi/api/routes/processing_configs.py`: processing config CRUD
- `src/mkobi/api/routes/processing_logs.py`: processing log access

---

# BLOCK 3 — Access Control & Security

## 3.1 Access Control

Verify `src/mkobi/core/permissions.py`:

### Dashboard Access

- `dashboard_access` checked on every dashboard-related request
- Editor/viewer/admin restrictions enforced
- Direct object access vulnerabilities (user cannot access another user's dashboard)
- Admin bypass: admins have full access without explicit `dashboard_access` entries
- 403/404 dual-signal implementation in `DashboardService.get_dashboard()`

### User Roles

Verify `UserRole` StrEnum usage:

```python
class UserRole(StrEnum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"
```

All role checks must use StrEnum, NOT string literals.

### Dashboard Permissions

Verify `DashboardPermission` StrEnum:

```python
class DashboardPermission(StrEnum):
    VIEW = "view"
    EDIT = "edit"
    ADMIN = "admin"
```

## 3.2 JWT Security

Verify `src/mkobi/core/security.py`:

- Token expiration validation
- Invalid token handling (401 Unauthorized)
- Missing token handling (401 Unauthorized)
- Secret key stored in env (`JWT__SECRET_KEY`)
- Algorithm explicitly set (NOT default)
- Payload contains: `user_id`, `email`, `role`

## 3.3 Password Security

Verify:

- bcrypt usage (NOT md5, SHA, plaintext)
- Password hash stored in DB (NOT plaintext)
- No password logging
- Minimum 8 characters (frontend Zod schema)
- Temp password generated via `secrets.token_urlsafe(16)` on registration approval

## 3.4 Upload Security

Verify `src/mkobi/api/routes/upload.py`:

- Path traversal (`../../file.csv`)
- Unsafe filenames (use secure filename)
- Oversized files handling (limit via config)
- MIME-type validation (client + server side)
- Rate limiting (protection from spam upload)

## 3.5 SQL Safety

Verify repositories (`src/mkobi/db/repositories/`):

- No raw unsafe SQL
- Parameterized queries (SQLAlchemy ORM/Core)
- SQL formation via string interpolation forbidden (f-strings, `+`)
- ORM used for all operations

## 3.6 Secrets & Config

Verify `src/mkobi/config.py`:

- No hardcoded secrets
- Env-based configuration (pydantic-settings)
- Docker secrets support (`_FILE` suffix)
- Nested env vars (`DATABASE__HOST`, `DATABASE__PORT`, `JWT__SECRET_KEY`)
- `.env` file for development only
- `app.yaml` for non-sensitive settings only
- Production credential enforcement (refuses to start with default `admin`/`admin`)
- CORS origins validated at startup in production mode

## 3.7 Rate Limiting

Verify:

- Redis-based sliding window algorithm
- Fail-open (default) vs fail-closed (production) via `RATE_LIMITER_FAIL_CLOSED`
- Protected endpoints: login (5/5min), register-request (3/hour), upload (configured)
- Health tracking when Redis unavailable

## 3.8 Email Domain Blocklist

Verify:

- Configurable domain blocklist in `app.yaml`
- Validated on backend via Pydantic (security boundary)
- Also validated on frontend via Zod (UX convenience)

---

# BLOCK 4 — Data Processing (Polars)

## 4.1 Data Loaders

Verify `src/mkobi/data/loaders/loader.py`:

- Polars used (`import polars as pl`)
- pandas NOT used (`import pandas as pd` forbidden)
- CSV reading (`read_csv`)
- CSV.gz reading (`read_csv` with decompression)
- Schema validation (`validator.py`)
- Error handling (corrupted CSV, invalid schema, missing columns, empty files)

## 4.2 Transformations

Verify `src/mkobi/data/processing/transformations.py`:

### Aggregations

Verify presence of:

- GroupBy (Polars `group_by`)
- YoY (year-over-year calculations) with modes: `absolute`, `percent`
- Shares (ratio computations)
- Custom metrics (configurable metrics via formula parser)

### Custom Metrics Formula Parser

Verify:

- Supports: `revenue - cost`, `profit / revenue * 100`
- Operators: `+`, `-`, `*`, `/`
- Limitations documented: no parentheses, no numeric literals, no special chars in column names
- Invalid formulas produce clear error messages with position and nature

### Pipeline Correctness

- Parsing (CSV → Polars DataFrame)
- Transformations (per dashboard config)
- Aggregations (grouping, metrics)
- Full recalculation logic (all aggregates rebuilt on each upload)

## 4.3 Storage

Verify `src/mkobi/data/storage/manager.py`:

- Save to PostgreSQL (`aggregated_data` table)
- JSONB usage for `dims` and `metrics`
- Correct serialization
- DB transaction handling (atomic processing, rollback on failure)
- `dims` keys sorted recursively before writes (UPSERT determinism)
- Unique index on `(dashboard_id, graph_id, dims::text)` for conflict detection

## 4.4 Resource Handling

Verify:

- Temp files cleanup (`platformdirs`, deletion after processing — both success and failure)
- DB transaction handling (commit/rollback)
- Memory-efficient processing (Polars lazy evaluation where applicable)
- Errors handled and logged

---

# BLOCK 5 — PostgreSQL Layer

## 5.1 Schema Compliance

Verify all 10 tables match `docs/09-database/`:

### Core Tables

- `users`: UUID PK, email UNIQUE, password_hash, `user_role` ENUM, is_active, TIMESTAMPTZ timestamps
- `layouts`: UUID PK, name UNIQUE, JSONB definition, TIMESTAMPTZ timestamps
- `dashboards`: UUID PK, name UNIQUE, description, config JSONB, layout_id FK (SET NULL), created_by FK (SET NULL), TIMESTAMPTZ timestamps
- `graphs`: UUID PK, dashboard_id FK (CASCADE), name, `graph_type` ENUM, JSONB config/dimensions/metrics, UNIQUE(dashboard_id, name)
- `filters`: UUID PK, name UNIQUE, `filter_type` ENUM, JSONB config

### Access Tables

- `dashboard_access`: composite PK (user_id, dashboard_id), `dashboard_permission_level` ENUM, FK to users/dashboards (CASCADE)
- `dashboard_filters`: composite PK (dashboard_id, filter_id), FK to dashboards/filters (CASCADE)
- `registration_requests`: UUID PK, email UNIQUE, `registration_status` ENUM, INET IP, reviewed_by FK (SET NULL), timestamps

### Processing Tables

- `processing_configs`: dashboard_id PK/FK (CASCADE), JSONB settings, TIMESTAMPTZ updated_at
- `aggregated_data`: BIGSERIAL PK, dashboard_id FK (CASCADE), graph_id FK (CASCADE), JSONB dims/metrics
- `processing_logs`: UUID PK, dashboard_id FK (SET NULL), `processing_status` ENUM, message, TIMESTAMPTZ timestamps

### Verify

- Foreign keys present
- CASCADE behavior correct (dashboard deletion removes graphs, data, access, configs)
- SET NULL behavior correct (layout/user deletion preserves dashboard)
- CHECK constraints for enums
- UNIQUE constraints where needed
- `gen_random_uuid()` default for UUID PKs
- `TIMESTAMPTZ` for all timestamps

## 5.2 Indexes

Verify all indexes from `docs/09-database/indexes.md`:

**Core 7 indexes:**

```sql
CREATE INDEX idx_aggregated_data_graph_id ON aggregated_data(graph_id);
CREATE INDEX idx_aggregated_data_dashboard_id ON aggregated_data(dashboard_id);
CREATE INDEX idx_aggregated_data_dashboard_graph ON aggregated_data(dashboard_id, graph_id);
CREATE INDEX idx_aggregated_data_dims_gin ON aggregated_data USING GIN (dims);
CREATE INDEX idx_dashboard_access_user ON dashboard_access(user_id);
CREATE INDEX idx_dashboard_access_dashboard ON dashboard_access(dashboard_id);
CREATE INDEX idx_graphs_dashboard ON graphs(dashboard_id);
```

**Additional indexes:**

- `idx_dashboard_filters_dashboard_filter` on `dashboard_filters(dashboard_id, filter_id)`
- `uq_aggregated_data_dashboard_graph_dims` on `aggregated_data(dashboard_id, graph_id, dims::text)` — UNIQUE for UPSERT
- Unique indexes on: `users.email`, `layouts.name`, `dashboards.name`, `graphs(dashboard_id, name)`, `filters.name`
- `idx_users_role` on `users.role`
- `idx_processing_logs_dashboard_id` on `processing_logs(dashboard_id)`

## 5.3 Aggregated Data Model

Verify `src/mkobi/db/models/aggregated_data.py`:

- Correct JSONB usage (dims, metrics)
- Filtering via dims (GIN index)
- Metrics consistency
- 1 row = 1 chart data point
- `dims` keys sorted recursively before writes

## 5.4 Queries (Repositories)

Verify `src/mkobi/db/repositories/`:

- No N+1 problems
- Correct joins
- Index usage (GIN for JSONB)
- Prepared statements (SQLAlchemy)

## 5.5 Migrations (Alembic)

Verify `alembic/versions/`:

- All migrations apply correctly
- Reproducible from empty database
- No broken revisions
- No circular dependencies
- Descriptive migration names
- Correct migration order
- PostgreSQL ENUM types created with `checkfirst=True` for idempotency

---

# BLOCK 6 — Frontend (React SPA)

## 6.1 Architecture (FSD)

Verify Feature-Sliced Design compliance:

### App Layer

- `app/providers.tsx`: QueryClient (retry: 1, staleTime: 5min), Router, Theme providers
- `app/routes.tsx`: all application routes

### Routes

| Path | Component | Access |
|------|-----------|--------|
| `/login` | `LoginForm` | Public |
| `/register` | `RegisterForm` | Public |
| `/dashboards` | `DashboardList` | Authenticated |
| `/dashboard/:id` | `DashboardView` | Authenticated |
| `/dashboard/:id/upload` | `UploadPage` | Admin, Editor |
| `/admin` | `AdminPanel` | Admin only |
| `/profile` | `UserProfile` | Authenticated |
| `/profile/change-password` | `ChangePasswordPage` | Authenticated |
| `*` | `NotFound` | Public |

### Features Layer

For each feature verify:

- **auth**: LoginForm, RegisterForm, useAuth, authApi, authToken
- **dashboards**: DashboardList, DashboardView, DashboardFilters, useDashboards, dashboardApi
- **upload**: FileDropzone, UploadPage, uploadApi
- **users**: UserProfile, userApi
- **admin**: AdminPanel, UserManagement, LogViewer, RegistrationRequests, DashboardManagement, adminApi

### Shared Layer

- **api**: axiosInstance with JWT interceptors, base URL `/api/v1`, 401 handling
- **components**: ProtectedRoute, RoleBasedAccess, Layout (AppLayout, Header, Sidebar)
- **types**: api.types.ts (User, Dashboard, etc.), enums.ts (TypeScript enums)

## 6.2 Type Safety

Verify:

- TypeScript strict mode used (NO `any`)
- Types for API responses (AuthResponse, DashboardSummary, etc.)
- Types for components (props interfaces)
- Zod schemas for forms (React Hook Form)
- No type errors (`tsc --noEmit`)

## 6.3 API Integration

Verify `frontend/src/features/*/api/`:

- axiosInstance used (NOT direct axios)
- JWT added via request interceptor
- Token expiration checked before attaching
- Response interceptor handles 401 (removes token, toast notification, redirect to `/login`)
- TanStack Query for server state
- Polling for long operations (processing status)
- react-hot-toast for notifications

## 6.4 UI Components

### Login Page (`/login`)

- Fields: email, password
- Email format validation
- Login button
- Registration link
- Error message display
- On success: stores token + user state, redirects to `/dashboards`

### Registration Page (`/register`)

- Email field (Zod validation)
- Submit button
- Domain blocklist check
- Success message

### Dashboard List Page (`/dashboards`)

- List of accessible dashboards
- Cards: name, description, link
- GET `/api/v1/dashboards/my`
- User profile link in header

### Dashboard View Page (`/dashboard/:id`)

- Dashboard title
- Filters Panel (dynamic from config)
- Charts Grid (Plotly.js React)
- Upload button (editor+ only)
- GET `/api/v1/data/aggregated?dashboard_id=:id&filters=...`

### Data Upload Page (`/dashboard/:id/upload`)

- Mode Toggle: "Overwrite" / "Append"
- Dropzone (react-dropzone)
- Progress Bar
- POST `/api/v1/upload/:dashboard_id?mode=overwrite|append`

### Admin Panel (`/admin`)

- User Management (table, role change, delete)
- Registration Requests (approve/reject)
- Dashboard Management (CRUD)
- Log Viewer (filterable, paginated)

### User Profile Page (`/profile`)

- Email (read-only), role (read-only)
- `display_name` shown
- Delete Account button (non-admin only)
- Change Password link

## 6.5 State Management

Verify:

- TanStack Query for server state (NOT Redux/Zustand)
- React Hook Form for forms
- Zod for form validation
- Local state via `useState`/`useReducer` where appropriate
- No excessive global state

## 6.6 Chart Rendering

Verify `frontend/src/features/dashboards/ui/charts/`:

- BarChart (Plotly.js React)
- LineChart (Plotly.js React)
- PieChart (Plotly.js React)
- TableChart
- PlotlyChart (wrapper)
- Supported types: bar, line, pie, table
- Config-driven rendering (from `graph.config` JSONB)
- Invalid config handling
- Missing data handling

## 6.7 Frontend Security

Verify:

- JWT stored in memory (production) or sessionStorage (development) — NOT localStorage
- Axios interceptors add token
- ProtectedRoute component works
- RoleBasedAccess component works
- Email validation (Zod regex + blacklist domains)
- UI-level role checks are for UX only (backend enforces authorization)

---

# BLOCK 7 — Code Quality (Backend)

## 7.1 Typing

Verify `src/mkobi/`:

- Type hints on all functions (parameters + return value)
- Pydantic models for API (`src/mkobi/models/`)
- SQLAlchemy models for ORM (`src/mkobi/db/models/`)
- No `Any` types (except justified cases)
- mypy passes without errors

## 7.2 Pydantic Models

Verify `src/mkobi/models/`:

- All models inherit from `BaseModel`
- Types used: `EmailStr`, `UUID`, `datetime`
- Validators where needed (`validator`, `field_validator`)
- `model_config` configured
- No duplicated logic

Verify files:

- `auth.py`: LoginRequest, TokenWithUser, UserResponse (with `display_name`)
- `dashboard.py`: DashboardCreate, DashboardUpdate, DashboardResponse
- `user.py`: UserCreate, UserUpdate, UserResponse
- `enums.py`: ALL 17 StrEnum classes

## 7.3 Enum Usage (StrEnum)

Verify `src/mkobi/models/enums.py`:

All constants must be StrEnum, NOT dict or list. All 17 classes:

`UserRole`, `DashboardPermission`, `GraphType`, `FilterType`, `RegistrationStatus`, `UploadMode`, `ProcessingStatus`, `EnvironmentEnum`, `MimeTypeEnum`, `FileExtensionEnum`, `AggregationFunctionEnum`, `FilterOperatorEnum`, `OrientationEnum`, `BarmodeEnum`, `YoyModeEnum`, `ButtonVariant`, `ComponentSize`

Verify enum usage in code (NOT string literals):

- Bad: `if user.role == "admin":`
- Good: `if user.role == UserRole.ADMIN:`

## 7.4 Readability

Verify:

- No oversized functions (split into smaller ones)
- No duplicated logic (extract to helpers)
- Clear naming
- No magic constants (extract to constants or config)
- Comments only for non-trivial logic
- Comments MUST be in English (NOT Russian)

## 7.5 Logging Language

Verify:

- Log messages in English (NOT Russian)
- Exception messages in English
- Docstrings in English
- Example: `logger.info("User logged in")` (GOOD), `logger.info("Пользователь вошел")` (BAD)

## 7.6 Error Handling

Verify:

- No broad `except Exception:` without re-raise
- No swallowed exceptions (empty except blocks)
- Consistent errors (always return `HTTPException` with code)
- Error logging (`logger.error` with context)
- No `print()` statements

## 7.7 Async Correctness

Verify:

- No blocking I/O in async endpoints
- No sync DB calls in async endpoints (use async SQLAlchemy)
- No `time.sleep()` in async (use `asyncio.sleep`)
- Proper `await` usage

## 7.8 Logging

Verify logging usage:

```python
import logging
logger = logging.getLogger(__name__)
```

Verify logging present for:

- Upload events (start, complete, failure)
- Processing events (start, steps, complete, failure)
- Auth events (login success/failure)
- Errors (with stack trace)
- Levels: INFO, WARNING, ERROR (NOT DEBUG in production)

Verify absence of:

- `print()` statements
- `logger.info()` for errors (use `logger.error()`)

---

# BLOCK 8 — Code Quality (Frontend)

## 8.1 TypeScript

Verify:

- Type hints (interfaces, types)
- No `any` (use specific types)
- Zod schemas for runtime validation
- Correct props types for components
- `tsc --noEmit` passes without errors

## 8.2 React Best Practices

Verify:

- Functional components (NOT class components)
- Hooks usage (`useState`, `useEffect`, custom hooks)
- Key props in lists
- Memoization where needed (`useMemo`, `useCallback`)
- No business logic in components (extract to hooks/services)

## 8.3 Code Style

Verify:

- ESLint passes without errors
- Prettier (if configured)
- Naming: PascalCase for components, camelCase for variables
- No commented-out code
- No `console.log()` in production
- Comments MUST be in English (NOT Russian)

---

# BLOCK 9 — Task Queue & Background Processing

## 9.1 In-Memory Task Queue (MVP)

Verify `src/mkobi/core/task_queue.py`:

- `TaskQueue` class with `asyncio.Queue`
- `default_queue` singleton
- `enqueue_job()` compatibility wrapper
- `get_task_queue()` returns singleton
- Task lifecycle: `STARTED` → `PROCESSING` → `SUCCESS`/`FAILED`
- Status/result/error tracking in memory dicts

## 9.2 Background Worker

Verify `src/mkobi/workers/data_worker.py`:

- `process_csv_background()` — async entry point
- `process_csv_background_sync()` — sync wrapper for RQ compatibility
- Full pipeline: parse → transform → aggregate → save → cleanup
- Processing log updates at each stage

## 9.3 Redis/RQ Migration Readiness

Verify migration path documented in `docs/03-processing/task-queue.py`:

- `process_csv_background_sync` prepared for RQ
- Dual-mode operation support (`USE_REDIS_QUEUE` env var)
- Rollback plan documented

---

# BLOCK 10 — Performance & Stability

## 10.1 Processing Scalability

Verify:

- Memory-efficient processing (Polars lazy evaluation where applicable)
- Full file loading considerations for large files
- No unbounded memory growth

## 10.2 API Stability

Verify:

- Error isolation (one endpoint failure doesn't crash others)
- Long-running requests (timeout handling)
- Rate limiting (protection from abuse)
- CORS configured correctly (FastAPI CORSMiddleware, explicit origins/methods/headers)

## 10.3 Database

Verify:

- Heavy JSONB scans use GIN index
- Missing indexes detected via query plans
- Connection pooling (asyncpg pool)
- Short transactions (no deadlocks)
- N+1 problems addressed (eager loading where needed)

---

# BLOCK 11 — Configuration & Deployment

## 11.1 Configuration

Verify `src/mkobi/config.py` and `src/mkobi/settings/`:

- Pydantic-settings for config loading
- Priority: env vars > Docker secrets > .env > app.yaml > defaults
- Secrets via env vars (`DATABASE__PASSWORD`, `JWT__SECRET_KEY`)
- Docker secrets support (`_FILE` suffix)
- `.env` file for development only
- `app.yaml` for non-sensitive settings only
- Production credential enforcement at startup

## 11.2 Database Initialization & Startup Lifecycle

Verify `src/mkobi/db/starter.py` and lifespan in `src/mkobi/app.py`:

1. Dependency check (all required packages importable)
2. Database connectivity check (`SELECT 1`)
3. Schema existence check (`alembic_version` table)
4. Alembic migrations (when `AUTO_MIGRATE=true`)
5. Admin user creation (idempotent, SAVEPOINT for race conditions)
6. Stale temp file cleanup (threshold: `STALE_FILE_THRESHOLD_HOURS`, default 24h)
7. Test database recreation (when `ENV=test` or `RECREATE_TEST_DB=true`)
8. Application ready (accepts requests, task queue initialized)
9. Shutdown: engine connections disposed

## 11.3 Docker

Verify `Dockerfile` and `docker-compose.yml`:

- Multi-stage build (dev, test, prod, prod-slim targets)
- Only necessary dependencies in production image
- Environment variables passed correctly
- Volumes for data persistence (`postgres_data`, `app_data`)
- Health checks (db: `pg_isready`, app: HTTP GET `/health`)
- Non-root container
- No secrets baked into image
- `.env` not copied into image

## 11.4 Deployment Options

**Development:**

- React dev server (port 5173) + FastAPI (port 8000) with CORS
- Hot reload for both servers
- Environment variables via `.env` files

**Production (Option A — Recommended):**

- FastAPI serves built React static files (`frontend/dist`)
- Static files via `StaticFiles`
- All non-API routes fall through to React `index.html`

**Production (Option B — Nginx):**

- Nginx proxies `/api` → FastAPI, everything else → React SPA
- SSL termination at Nginx

---

# BLOCK 12 — No Overengineering Check

Verify absence of:

- Redux/Zustand (TanStack Query sufficient for server state)
- Unnecessary abstraction layers (axiosInstance → direct API calls)
- Duplicated Pydantic models
- Complex patterns without necessity (if simple solution works)
- Enterprise patterns where not required

---

# Report Format

Create file: `C:\py_dev\mkobi\.ai\audit\project\audit_report_<number>.md` (next available number)

## 1. Executive Summary

Briefly:

- Overall system quality
- Main risks
- Readiness level (1–10)
- Specification compliance

---

## 2. Architecture Summary

Briefly:

- Strengths
- Weaknesses
- Maintainability assessment
- Clean Architecture compliance
- FSD compliance (Frontend)

---

## 3. Requirements Coverage

Table (based on `docs/SPEC.md` and all `docs/**/*.md`):

| Requirement | Status | Notes |
|-------------|--------|-------|
| JWT auth with TokenWithUser | PASS/FAIL | ... |
| CSV.gz upload with validation | PASS/FAIL | ... |
| Polars processing pipeline | PASS/FAIL | ... |
| JSONB normalization (dims key sort) | PASS/FAIL | ... |
| React SPA (FSD) | PASS/FAIL | ... |
| Plotly.js React charts | PASS/FAIL | ... |
| All 17 StrEnum classes | PASS/FAIL | ... |
| Logging (NOT print) | PASS/FAIL | ... |
| Type hints (backend) | PASS/FAIL | ... |
| TypeScript strict (frontend) | PASS/FAIL | ... |
| Pydantic models | PASS/FAIL | ... |
| PostgreSQL + JSONB | PASS/FAIL | ... |
| Role-based access control | PASS/FAIL | ... |
| Admin bypass | PASS/FAIL | ... |
| 403/404 dual-signal | PASS/FAIL | ... |
| TanStack Query | PASS/FAIL | ... |
| React Hook Form + Zod | PASS/FAIL | ... |
| Health check endpoints | PASS/FAIL | ... |
| Rate limiting (fail-open/closed) | PASS/FAIL | ... |
| Production credential enforcement | PASS/FAIL | ... |
| Registration approval flow | PASS/FAIL | ... |
| Task queue (in-memory MVP) | PASS/FAIL | ... |
| Test database isolation | PASS/FAIL | ... |

---

## 3.5 Runtime Findings

Separate section for issues found only through runtime observation (BLOCK 1.5):

| Severity | Type | Flow | Problem | Evidence | Recommendation |
|----------|------|------|---------|----------|----------------|
| CRITICAL | [RUNTIME] | Frontend rendering | App crashes on load | Console: TrailingSlashRedirect is not a `<Route>` component | Move component inside `<Route element={}>` |
| CRITICAL | [RUNTIME] | Login page | Page shows "Something went wrong" | ErrorBoundary caught render error | Fix root cause of render crash |
| MEDIUM | [RUNTIME] | Backend startup | Reload loop from volume mounts | Logs: repeated `StatReload detected changes` | Exclude `tests/` or `__pycache__/` from mount |

Flag as CRITICAL any runtime finding that prevents the user from using the application:
- Frontend fails to render (blank page, error boundary fallback)
- Backend in restart loop (intermittent 503s)
- API proxy broken (frontend cannot reach backend)

---

## 4. Findings (main section)

For each issue:

| Severity | Type | File | Line | Problem | Impact | Recommendation |
|----------|------|------|------|---------|--------|----------------|
| CRITICAL | [SPEC-DEVIATION] | api/upload.py | 84 | temp files not deleted | disk leaks | add finally cleanup |
| HIGH | [BEST-PRACTICE] | models/enums.py | 12 | dict used instead of StrEnum | maintainability | refactor to StrEnum |
| MEDIUM | [DOC-UPDATE] | services/processing.py | 156 | print() instead of logger | logging standards | replace + update spec |
| LOW | frontend/src/features/auth/ui/LoginForm.tsx | 23 | any type used | type safety | add interface |

Severity:

- **CRITICAL**: blocks operation, security vulnerability, data loss
- **HIGH**: serious issue affecting stability or security
- **MEDIUM**: quality issue, technical debt
- **LOW**: style, naming, minor improvements

---

## 5. File-Level Recommendations

For each problematic file:

```text
File: src/mkobi/data/processing/transformations.py

Problems:
- oversized function (process_data: 200+ lines)
- mixed responsibilities (parse + transform + aggregate)
- transaction handling unclear
- print() statements for debug

Recommendations:
- split into parse/transform/aggregate functions
- isolate DB writes in storage/manager.py
- add typed intermediate models
- replace print() with logger
- add docstrings (Google style)
```

---

## 6. Missing Features vs Specification

List separately:

**Missing (not implemented):**

- Feature X from SPEC.md section Y
- Endpoint Z from docs

**Partially implemented:**

- Feature A (missing B, C)

**Contradicts specification:**

- Code has X, spec says Y

---

## 7. Frontend-Specific Findings

Separate section for React SPA:

### 7.1 Architecture (FSD)

- Compliance with features/shared/app structure
- No business logic in components
- Correct TanStack Query usage

### 7.2 TypeScript

- No `any`
- Correct API types
- Zod schemas for forms

### 7.3 Components

- All pages from spec implemented
- Chart rendering works (Plotly.js React)
- Filters applied correctly

### 7.4 API Integration

- axiosInstance configured
- JWT interceptors work
- Error handling (react-hot-toast)

---

## 8. Security Assessment

### 8.1 Backend

- JWT: correct
- Password hashing: bcrypt
- SQL injection: protected via ORM
- Upload: path traversal, oversized files protected
- Rate limiting: configured
- Production credential enforcement: active
- CORS: explicit origins/methods/headers

### 8.2 Frontend

- JWT storage: memory/sessionStorage (NOT localStorage)
- ProtectedRoute: works
- RoleBasedAccess: works

---

## 9. Performance Assessment

### 9.1 Backend

- Processing: Polars used, memory-efficient
- DB: indexes configured, GIN for JSONB
- API: CORS, rate limiting

### 9.2 Frontend

- Bundle size: optimized
- React rendering: memoization
- API calls: TanStack Query caching

---

## 10. Final Assessment

Rate:

- **Maintainability**: easy to maintain? (1–10)
- **Production Readiness**: ready for production? (1–10)
- **Scalability**: scalability (1–10)
- **Security**: security level (1–10)
- **Code Quality**: code quality (1–10)

### Key Technical Risks

1. Risk 1 (CRITICAL/HIGH/MEDIUM/LOW)
2. Risk 2
3. ...

### Fix Priority

1. CRITICAL — fix immediately
2. HIGH — fix before production
3. MEDIUM — technical debt
4. LOW — nice to have

---

# Important Auditor Constraints

## Do NOT Flag As Issues

- Simple architecture
- Small number of abstraction layers
- Absence of enterprise patterns
- "Simple" solutions that work and are readable

## Flag As Issues

- Hard to maintain (hard to understand, modify)
- Implicit logic (hidden behavior, side effects)
- Insecurity (security vulnerabilities)
- Mixed responsibilities (business logic in routes)
- Unstable processing (data loss, corruption)
- Weak access control (unauthorized access)
- Poor error handling (swallowed exceptions)
- `print()` instead of logging
- Missing `StrEnum` where appropriate
- Hardcoded strings instead of enum values
- Missing type hints
- Raw SQL via string interpolation

## Primary Criterion

The system must be:

- Understandable (readable code, clear intent)
- Resilient (error handling, transactions, cleanup)
- Secure (auth, access control, validation)
- Easily maintainable (modular, tested, typed)
- Specification-compliant (`docs/SPEC.md` + all `docs/**/*.md`)

## mkobi-Specific Requirements

- Package name: `mkobi`
- StrEnum for all 17 constant classes (NOT dict/list)
- Pydantic models in `src/mkobi/models/`
- Logging via `logger = logging.getLogger(__name__)`
- Type hints on all functions
- Clean Architecture (layer separation)
- FSD for frontend
- Polars (NOT pandas)
- PostgreSQL + JSONB for aggregated data
- Comments and logs MUST be in English (NOT Russian)
