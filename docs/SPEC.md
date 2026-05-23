# BI Dashboard System — Overview

## Purpose

A web application for uploading CSV/CSV.gz data files, processing them with Polars, storing aggregated results in PostgreSQL, and visualizing data through configurable dashboards with role-based access control.

---

## Technology Stack

| Layer            | Technology                                |
| ---------------- | ----------------------------------------- |
| Backend          | **FastAPI**                               |
| Frontend         | **React 18+ (TypeScript) + Vite**        |
| State Management | **TanStack Query**                        |
| Forms            | **React Hook Form + Zod**                |
| Charts           | **Plotly.js React**                       |
| Data Processing  | **Polars** (pandas is forbidden)          |
| Storage          | **PostgreSQL + JSONB**                    |
| Validation       | **Pydantic v2**                           |
| Auth             | **JWT + bcrypt**                          |
| ORM              | **SQLAlchemy 2.0 (async) + asyncpg**     |
| Migrations       | **Alembic**                               |
| Rate Limiting    | **Redis**                                 |
| Testing          | **pytest**                                |
| Package Manager  | **uv**                                    |

---

## Architecture

**Backend:** Clean Architecture — strict layered design (API → Service → Repository).

**Frontend:** Feature-Sliced Design (FSD) — React SPA with type-safe API communication.

```
Browser (React SPA)
       ↓ HTTPS/JSON
FastAPI (REST API)
       ↓
Service Layer
       ↓
PostgreSQL
```

Key principles:
- All business logic resides in the backend service layer.
- React is UI-only; no business logic on the frontend.
- Access control is enforced on every API request.
- Stateless backend — JWT tokens carry authentication state.

> See [Backend Architecture](06-backend/architecture.md) and [Frontend Architecture](07-frontend/architecture.md) for details.

---

## Main Data Flow

1. **Upload** — `POST /api/v1/upload/{dashboard_id}` — file saved to temp directory (platformdirs), MIME-type and size validated.
2. **Parse** — Polars reads the file (UTF-8), structure validated against processing config.
3. **Transform** — LoaderConfig transformations applied, custom metrics evaluated.
4. **Aggregate** — GroupBy, YoY, shares, custom metrics — full recalculation.
5. **Save** — Results written to `aggregated_data` table (JSONB `dims` + `metrics`), temp file deleted.
6. **Retrieve** — `GET /api/v1/data/aggregated` — access check, filters applied, JSON response.
7. **Render** — React SPA receives data via TanStack Query, Plotly.js renders charts.

> See [Data Flow](00-overview/data-flow.md) for the complete end-to-end diagram.

---

## Roles & Permissions

| Role    | Capabilities                                          |
| ------- | ----------------------------------------------------- |
| Admin   | Full CRUD on dashboards, users, configs; grants access |
| Editor  | Uploads CSV, triggers data recalculation              |
| Viewer  | Read-only access to assigned dashboards               |

Access is validated on every request via the `dashboard_access` table.

> See [Auth & Access Control](01-auth/) and [Access Control](08-security/access-control.md) for details.

---

## Documentation Index

### Core Overview
- [System Overview](00-overview/overview.md) — Purpose, stack, entities, roles, API summary.
- [Data Flow](00-overview/data-flow.md) — End-to-end upload-to-display pipeline.

### Domain Documentation
- [Auth & Access Control](01-auth/) — Login, registration, JWT, password change, auth endpoints.
- [Dashboards API](02-dashboards/) — Dashboard CRUD, layout, graph, and filter endpoints.
- [Data Processing](03-processing/) — Upload, parse, transform, aggregate pipeline; task queue; custom metrics.
- [Admin API](04-admin/) — User management, registration requests, processing logs.
- [Health Checks](05-health/) — Health and detailed health endpoints.
- [Backend Architecture](06-backend/) — Clean Architecture layers, configuration, logging, testing.
- [Frontend Architecture](07-frontend/) — FSD structure, pages, auth flow, upload UI, frontend security.
- [Security](08-security/) — Rate limiting, CORS, file validation, credential enforcement, access control.
- [Database](09-database/) — Core schema, processing schema, access control tables, indexes, enums.
- [Deployment](10-deployment/) — Development setup, production deployment, Docker, migrations.

### Guides
- [Docker Setup](11-guides/docker.md) — Multi-stage Dockerfile, Docker Compose, quick start.
- [Task Queue Migration](11-guides/task-queue-migration.md) — In-memory `TaskQueue` to Redis/RQ migration plan.

### Reference
- [Swagger UI Guide](99-reference/swagger.md) — Using the interactive API docs at `/docs/`.
- [Run Guide](99-reference/run-guide.md) — Application setup, configuration, and run instructions.

---

## Key Design Decisions

- **JSONB for aggregated data** — Single `aggregated_data` table with JSONB `dims` + `metrics` supports any dashboard without schema migrations.
- **JSONB key normalization** — `dims` keys are sorted recursively before writes to ensure deterministic UPSERT conflict detection.
- **Full recalculation on upload** — Every upload triggers a complete rebuild of all aggregates for the dashboard.
- **StrEnum for all constants** — All fixed values (roles, statuses, types) use `StrEnum` in `src/mkobi/models/enums.py`.
- **Fail-open rate limiter** — When Redis is unavailable, requests are allowed through by default (configurable to fail-closed).
- **Production credential enforcement** — Application refuses to start in production with default credentials.
- **Background task queue** — In-memory `TaskQueue` (MVP) with a documented migration path to Redis/RQ.
- **Login returns user data** — The login endpoint returns `TokenWithUser` (token + user profile) to eliminate the need for a separate `/me` call after authentication.
- **Admin bypass for dashboards** — Users with the `admin` role implicitly see all dashboards without requiring explicit `dashboard_access` entries.
- **403/404 dual-signal for dashboard access** — The system distinguishes "dashboard not found" (HTTP 404) from "dashboard exists but no access" (HTTP 403) to avoid leaking dashboard existence information.
- **`display_name` computed field** — The `UserRead` model exposes a computed `display_name` derived from the email prefix (text before `@`), available in all API responses returning user data.
- **Upload as modal dialog** — File upload is implemented as `UploadModal` embedded in `DashboardView`, not as a separate page. This eliminates page navigation during upload and provides inline progress feedback.
- **Dashboard-filter binding** — Filters are linked to dashboards via the `dashboard_filters` many-to-many join table. Admins bind/unbind filters using `POST/DELETE /api/v1/dashboards/{id}/filters`. Bound filters are listed via `GET /api/v1/dashboards/{id}/filters`.
- **Dashboard access management** — Admins grant, list, and revoke dashboard access via dedicated endpoints: `POST/GET /api/v1/dashboards/{id}/access` and `DELETE /api/v1/dashboards/{id}/access/{user_id}`. This is in addition to the admin panel endpoints.
- **Dashboard-specific graph endpoints** — Graphs can be created and listed via dashboard-scoped endpoints (`POST/GET /api/v1/dashboards/{id}/graphs`) in addition to the global `/api/v1/graphs` endpoints.
- **File processing service** — `file_processing.py` encapsulates validation, upload processing, and task management functions extracted from `DataService` for modularity and testability.
- **Background data worker** — `data_worker.py` provides `process_csv_background` (async) and `process_csv_background_sync` (sync RQ wrapper) for CSV processing in background. The `_store_aggregate` function handles mode-aware (overwrite/append) data persistence.
- **Processing log date filtering** — The `GET /api/v1/admin/logs` endpoint supports `date_from` and `date_to` query parameters for filtering logs by `started_at` range, in addition to `status` and `dashboard_id` filters.
- **Top navigation Header** — The sidebar was replaced with a top navigation bar (`Header`) containing role-based nav items (Dashboards, Admin, Profile), user email display, and an AccountCircle menu for logout.
- **DataGrid tables for admin and dashboard list** — `DashboardList` and all admin panel tabs use MUI `DataGrid` with pagination, sorting, and quick filter instead of card lists or basic tables.
- **ConfirmDialog pattern** — Destructive actions (delete user, delete dashboard, reject registration) use a shared `ConfirmDialog` component with configurable labels, invoked imperatively via the `useConfirmDialog` hook.
- **Toast notifications** — User feedback for success/failure actions uses `react-hot-toast` (top-right, 3s success, 5s error duration) instead of inline alerts.
- **Short UUID display** — UUIDs displayed in tables are truncated to 8 characters via the shared `shortUuid` utility for improved readability.
- **Admin tab state preservation** — The admin panel uses `display: none/block` to hide inactive tabs, preserving pagination and sorting state across tab switches.
- **Zod v4 migration** — Frontend form validation uses Zod v4 API (`z.email()` instead of `z.string().email()`).
- **Per-IP login rate limiting** — Login rate limiter uses per-IP keys (not per-email) to prevent email enumeration attacks. The rate limiter key was changed from `f"login:{email}`" to `f"login:{client_ip}`" to avoid leaking registered email addresses through rate limit side-channels.
- **Migration advisory lock** — `_apply_migrations()` acquires a PostgreSQL advisory lock (`pg_advisory_lock(42)`) before running Alembic migrations, preventing concurrent migrations in multi-instance deployments (K8s replicas, multiple Gunicorn workers).
- **Dedicated database role (least-privilege)** — The application connects using a dedicated `mkobi_app` role with limited privileges (`CONNECT`, `SELECT`, `INSERT`, `UPDATE`, `DELETE`) instead of the superuser `postgres` role. The superuser role is used only for DDL migrations.
- **Migration job pattern** — Production Docker Compose uses a dedicated `migrate` service that runs before the app service starts, with `depends_on: service_completed_successfully` to ensure migrations complete before the application accepts requests.
- **Stale processing heartbeat** — A periodic cleanup task marks processing logs stuck in `PROCESSING` state for more than 30 minutes (configurable) as `FAILED`, providing visibility into crashed workers and preventing indefinite `PROCESSING` states.
- **Upload memory streaming** — File uploads use chunked streaming writes (`aiofiles` with 8KB chunks) instead of reading the entire file into memory, reducing memory pressure for large uploads (up to 100MB).
- **Weak admin credential detection** — `validate_admin_credentials()` checks against a set of known-weak values (`{"admin", "administrator", "root", "test", "user"}` for usernames, `{"password", "123456", "admin", "secret", "test"}` for passwords) instead of only the exact string `"admin"`.
- **Config reload for testing** — `get_config()` supports a `reload=True` parameter and `clear_config_cache()` function, allowing tests to reload configuration without monkeypatching the global singleton.
- **Atomic UPSERT for admin user** — `ensure_admin_user()` uses `INSERT ... ON CONFLICT (email) DO NOTHING` instead of check-then-create, eliminating the TOCTOU race condition on concurrent startup.
- **Sanitized database URL logging** — `_apply_migrations()` logs the database URL with `render_as_string(hide_password=True)` to prevent credential leakage in log files.
- **LRU token cache** — `_token_cache` in permissions.py uses `functools.lru_cache(maxsize=1000)` instead of an unbounded dict, preventing memory leaks in long-running processes.
- **Cookie-based refresh tokens** — Refresh tokens are stored in httpOnly cookies (`mkobi_refresh_token`) instead of the request body, eliminating XSS-based token theft. The access token lifetime was reduced from 30 to 15 minutes; refresh tokens live 7 days. Login sets the cookie, refresh reads from it, logout clears it.
- **POST /auth/logout endpoint** — Dedicated logout endpoint that clears the refresh token cookie. The frontend calls this on logout and then clears the in-memory access token.
- **Frontend silent refresh** — On app initialization, if no access token exists, the frontend attempts a silent refresh using the httpOnly cookie. This keeps users logged in across page refreshes without requiring re-authentication.
- **Request queue for concurrent 401s** — The axios interceptor implements a request queue (`failedQueue`) with an `isRefreshing` flag. When multiple requests fail with 401 simultaneously, only one refresh call is made; all queued requests are retried after the refresh completes.
- **ProtectedRoute loading state** — `ProtectedRoute` shows a loading spinner during silent refresh to prevent flash of login page for valid sessions with expired access tokens.

---

## Version History

| Version | Date       | Description                              |
| ------- | ---------- | ---------------------------------------- |
| 2.2     | 2026-05-16 | Updated with implemented features        |
| 2.3     | 2026-05-19 | Added login user-in-response, admin bypass, 403/404 dual-signal, display_name |
| 2.4     | 2026-05-19 | Upload modal (no page nav), top nav Header, DataGrid tables, ConfirmDialog pattern, toast notifications, short UUID display, Zod v4 migration, admin tab state preservation |
| 2.5     | 2026-05-19 | Dashboard-filter binding API, dashboard access management endpoints, dashboard-scoped graph endpoints, file processing service, background data worker, processing log date filtering |
| 2.6     | 2026-05-20 | Per-IP login rate limiting (email enumeration fix), migration advisory lock, dedicated DB role (least-privilege), migration job compose pattern, stale processing heartbeat, upload memory streaming, weak admin credential detection, config reload for testing, atomic UPSERT admin user, sanitized DB URL logging, LRU token cache |
| 2.7     | 2026-05-23 | Cookie-based refresh token flow: httpOnly refresh cookies (7-day TTL), 15-min access tokens, POST /auth/logout endpoint, frontend silent refresh on mount, request queue for concurrent 401s, ProtectedRoute loading state during refresh |

---

**Author:** Senior Python Architect
**Date:** 2026-05-23
**Version:** 2.7
