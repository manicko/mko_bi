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

### Reference
- [Docker Setup](README_DOCKER.md) — Multi-stage Dockerfile, Docker Compose, quick start.
- [Task Queue Migration](TASK_QUEUE_MIGRATION.md) — In-memory `TaskQueue` to Redis/RQ migration plan.
- [Swagger UI Guide](SWAGGER_README.md) — Using the interactive API docs at `/docs/`.

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

---

## Version History

| Version | Date       | Description                              |
| ------- | ---------- | ---------------------------------------- |
| 2.2     | 2026-05-16 | Updated with implemented features        |
| 2.3     | 2026-05-19 | Added login user-in-response, admin bypass, 403/404 dual-signal, display_name |

---

**Author:** Senior Python Architect
**Date:** 2026-05-19
**Version:** 2.3
