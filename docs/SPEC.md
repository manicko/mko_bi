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

---

## Version History

| Version | Date       | Description                              |
| ------- | ---------- | ---------------------------------------- |
| 2.2     | 2026-05-16 | Updated with implemented features        |
| 2.3     | 2026-05-19 | Added login user-in-response, admin bypass, 403/404 dual-signal, display_name |
| 2.4     | 2026-05-19 | Upload modal (no page nav), top nav Header, DataGrid tables, ConfirmDialog pattern, toast notifications, short UUID display, Zod v4 migration, admin tab state preservation |
| 2.5     | 2026-05-19 | Dashboard-filter binding API, dashboard access management endpoints, dashboard-scoped graph endpoints, file processing service, background data worker, processing log date filtering |

---

**Author:** Senior Python Architect
**Date:** 2026-05-19
**Version:** 2.5
