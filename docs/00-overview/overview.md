---
id: system-overview
domain: overview
tags:
  - architecture
  - technology-stack
  - entities
  - roles
  - permissions
  - api-overview
related:
  - data-flow
  - auth-api
  - dashboards-api
  - backend-architecture
  - security-overview
---

# System Overview

## Purpose

A web application for:

* Uploading CSV and CSV.gz data files into a temporary user directory
* Processing the uploaded data
* Storing aggregated results
* Displaying data in dashboards
* Managing user access control

---

## Technology Stack

| Layer            | Technology                                |
| ---------------- | ----------------------------------------- |
| Backend          | **FastAPI**                               |
| Frontend         | **React 18+ (TypeScript) + Vite**        |
| UI Kit           | **Material UI v5** or **Ant Design**     |
| State Management | **TanStack Query** (React Query)          |
| Forms            | **React Hook Form + Zod**                |
| Charts           | **Plotly.js React**                       |
| File Upload      | **react-dropzone**                        |
| HTTP Client      | **Axios** (with JWT interceptors)         |
| Notifications    | **react-hot-toast**                       |
| Data Processing  | **Polars** (pandas is forbidden)          |
| Storage          | **PostgreSQL**                            |
| Validation       | **Pydantic v2**                           |
| Auth             | **JWT + bcrypt**                          |
| Testing          | **pytest**                                |
| Logging          | **Python logging**                        |
| Env/Deps         | **uv**                                    |
| Temp Files       | **platformdirs**                          |
| ORM              | **SQLAlchemy 2.0 (async)**               |
| Migrations       | **Alembic**                               |
| DB Driver        | **asyncpg**                               |
| Rate Limiting    | **Redis** (async operations)              |

---

## Core Entities

### User

| Field          | Type   | Description                    |
| -------------- | ------ | ------------------------------ |
| id             | UUID   | Primary key                    |
| email          | TEXT   | Unique, not null               |
| password_hash  | TEXT   | Bcrypt hash                    |
| role           | TEXT   | `admin` \| `editor` \| `viewer` |
| is_active      | BOOL   | Account activation flag        |
| force_password_change | BOOL | Forces password change on next login |

> The `UserRead` Pydantic model exposes a computed `display_name` field derived from the email prefix (text before `@`). This field is included in all API responses returning user data (login, profile, user management). The `force_password_change` field is also included in login responses; when `true`, the frontend redirects to the forced password change page.

### Dashboard

| Field       | Type   | Description                          |
| ----------- | ------ | ------------------------------------ |
| id          | UUID   | Primary key                          |
| name        | TEXT   | Unique, not null                     |
| config      | JSONB  | Structure and graph descriptions     |

### Access

| Field        | Type   | Description                     |
| ------------ | ------ | ------------------------------- |
| user_id      | UUID   | References users.id             |
| dashboard_id | UUID   | References dashboards.id        |

### Aggregated Data

| Field        | Type   | Description                                |
| ------------ | ------ | ------------------------------------------ |
| dashboard_id | UUID   | References dashboards.id                   |
| dims         | JSONB  | Dimension values (filter and axis data)    |
| metrics      | JSONB  | Metric values (display data)               |

### Access

| Field        | Type   | Description                     |
| ------------ | ------ | ------------------------------- |
| user_id      | UUID   | References users.id             |
| dashboard_id | UUID   | References dashboards.id        |
| permission   | TEXT   | `view` \| `edit` \| `admin`     |

### Registration Request

| Field           | Type   | Description                     |
| --------------- | ------ | ------------------------------- |
| id              | UUID   | Primary key                     |
| email           | TEXT   | Unique, not null                |
| status          | TEXT   | `pending` \| `approved` \| `rejected` |
| requested_by_ip | INET   | IP address of requester         |
| reviewed_by     | UUID   | Admin who reviewed              |
| reviewed_at     | TIMESTAMPTZ | Review timestamp           |

### Dashboard Filter Value

| Field        | Type   | Description                                   |
| ------------ | ------ | --------------------------------------------- |
| id           | BIGINT | Auto-incrementing primary key                 |
| dashboard_id | UUID   | References dashboards.id (CASCADE on delete)  |
| filter_name  | TEXT   | Filter/dimension name (e.g., "category")      |
| filter_value | TEXT   | Distinct value for the filter (e.g., "Food")  |

> The `dashboard_filter_values` table caches distinct filter values extracted during CSV processing. It supports dynamic filter UI population when a filter's `config.source` is set to `"data"`. Values are rebuilt on each upload. See [Processing Schema](../09-database/schema-processing.md) for the full table definition.

### Dashboard-Filter Binding

| Field        | Type   | Description                     |
| ------------ | ------ | ------------------------------- |
| dashboard_id | UUID   | References dashboards.id        |
| filter_id    | UUID   | References filters.id           |

> See [Database Schema](../09-database/) for full table definitions and indexes.

---

## Roles & Permissions

### Admin

* Full CRUD on dashboards
* Defines data schema, processing logic, and graph configurations
* Manages users
* Grants access permissions

### Editor

* Uploads CSV files
* Triggers data recalculation

### Viewer

* Read-only access

> See [Auth & Access Control](../01-auth/) for detailed authentication and authorization flows.

---

## API Overview

The FastAPI backend exposes the following endpoint groups:

| Group               | Description                                    | Access        |
| ------------------- | ---------------------------------------------- | ------------- |
| Auth                | Login, register-request, change-password, refresh (cookie-based), logout, me | Public/Any    |
| Users               | CRUD operations                                | Admin         |
| Dashboards          | CRUD operations, access management, filter binding | Admin+        |
| Layouts             | CRUD operations                                | Admin         |
| Graphs              | CRUD operations (global + dashboard-scoped)    | Admin         |
| Filters             | CRUD operations                                | Admin         |
| Processing Configs  | Read/Write processing settings                 | Editor+       |
| Upload & Processing | File upload, processing triggers, status, result | Editor+       |
| Aggregated Data     | Retrieve chart data as JSON                    | Viewer+       |
| Admin               | User management, registration requests, logs, temp password retrieval | Admin         |
| Health              | Health checks                                  | Public        |

> See [API Responsibilities](../SPEC.md#14-api-responsibilities-fastapi) in SPEC.md for full endpoint listing.

---

## Related Docs

* [Data Flow](data-flow.md) — End-to-end upload-to-display pipeline
* [Authentication API](../01-auth/auth-api.md) — JWT auth and role definitions
* [Backend Architecture](../06-backend/architecture.md) — Clean Architecture and layer design
* [Security Overview](../08-security/security-overview.md) — Security constraints and measures
* [Deployment](../10-deployment/deployment.md) — Production deployment options
