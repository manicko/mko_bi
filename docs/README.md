# mkobi BI Dashboard — Documentation

## Overview

This directory contains the full project documentation for the mkobi BI Dashboard — a web application for uploading CSV data files, processing them with Polars, storing aggregated results in PostgreSQL, and visualizing data through configurable dashboards with role-based access control.

**Technology stack:** FastAPI, React 18+, PostgreSQL, Polars, SQLAlchemy 2.0 (async), JWT + bcrypt.

---

## Domain Index

| # | Domain | Path | Description |
|---|--------|------|-------------|
| 00 | **Overview** | [`00-overview/`](./00-overview/) | Project overview, architecture summary, and data flow |
| 01 | **Auth** | [`01-auth/`](./01-auth/) | Authentication and authorization API (JWT, registration, login) |
| 02 | **Dashboards** | [`02-dashboards/`](./02-dashboards/) | Dashboard CRUD API and management |
| 03 | **Processing** | [`03-processing/`](./03-processing/) | CSV upload, Polars processing pipeline, task queue |
| 04 | **Admin** | [`04-admin/`](./04-admin/) | Admin API for user and dashboard management |
| 05 | **Health** | [`05-health/`](./05-health/) | Health check and monitoring endpoints |
| 06 | **Backend** | [`06-backend/`](./06-backend/) | Backend architecture, configuration, logging, and testing |
| 07 | **Frontend** | [`07-frontend/`](./07-frontend/) | Frontend architecture (FSD), pages, auth flow, upload UI |
| 08 | **Security** | [`08-security/`](./08-security/) | Access control, permissions, and security overview |
| 09 | **Database** | [`09-database/`](./09-database/) | Database schemas, enums, indexes, and access patterns |
| 10 | **Deployment** | [`10-deployment/`](./10-deployment/) | Docker deployment and environment configuration |
| 90 | **ADR** | [`90-adr/`](./90-adr/) | Architecture Decision Records |
| 99 | **Reference** | [`99-reference/`](./99-reference/) | Supplementary reference materials |

### Files in this directory (root level)

| File | Description |
|------|-------------|
| [`SPEC.md`](./SPEC.md) | Full project specification (technology stack, architecture, data flow) |
| [`run-guide.md`](./99-reference/run-guide.md) | Application setup and launch instructions |
| [`docker.md`](./11-guides/docker.md) | Docker-specific documentation |
| [`swagger.md`](./99-reference/swagger.md) | Swagger/OpenAPI documentation guide |
| [`task-queue-migration.md`](./11-guides/task-queue-migration.md) | Task queue migration guide |

---

## Reading Guide

### New to the project?
Start here:
1. [`00-overview/overview.md`](./00-overview/overview.md) — project purpose and architecture
2. [`00-overview/data-flow.md`](./00-overview/data-flow.md) — how data moves through the system
3. [`06-backend/architecture.md`](./06-backend/architecture.md) — backend Clean Architecture
4. [`07-frontend/architecture.md`](./07-frontend/architecture.md) — frontend Feature-Sliced Design

### Setting up locally?
1. [`run-guide.md`](./99-reference/run-guide.md) — local setup instructions
2. [`10-deployment/deployment.md`](./10-deployment/deployment.md) — Docker deployment
3. [`06-backend/configuration.md`](./06-backend/configuration.md) — backend configuration

### Working on API endpoints?
- Auth endpoints → [`01-auth/auth-api.md`](./01-auth/auth-api.md)
- Dashboard endpoints → [`02-dashboards/dashboards-api.md`](./02-dashboards/dashboards-api.md)
- Processing endpoints → [`03-processing/processing-api.md`](./03-processing/processing-api.md)
- Admin endpoints → [`04-admin/admin-api.md`](./04-admin/admin-api.md)
- Health endpoints → [`05-health/health-api.md`](./05-health/health-api.md)

### Working on data processing?
1. [`03-processing/processing-api.md`](./03-processing/processing-api.md) — upload and processing API
2. [`03-processing/task-queue.md`](./03-processing/task-queue.md) — background task queue
3. [`09-database/schema-processing.md`](./09-database/schema-processing.md) — processing-related DB schemas

### Working on the frontend?
1. [`07-frontend/fsd-structure.md`](./07-frontend/fsd-structure.md) — Feature-Sliced Design structure
2. [`07-frontend/pages.md`](./07-frontend/pages.md) — page components and routing
3. [`07-frontend/auth-flow.md`](./07-frontend/auth-flow.md) — authentication flow on the frontend
4. [`07-frontend/upload-ui.md`](./07-frontend/upload-ui.md) — file upload UI

### Working on security?
1. [`08-security/security-overview.md`](./08-security/security-overview.md) — security model
2. [`08-security/access-control.md`](./08-security/access-control.md) — permissions and access control
3. [`07-frontend/frontend-security.md`](./07-frontend/frontend-security.md) — frontend security considerations

### Working on the database?
1. [`09-database/schema-core.md`](./09-database/schema-core.md) — core schemas (users, dashboards)
2. [`09-database/schema-access.md`](./09-database/schema-access.md) — access control schemas
3. [`09-database/enums.md`](./09-database/enums.md) — database enums
4. [`09-database/indexes.md`](./09-database/indexes.md) — index definitions

---

## Document Conventions

- **File format:** All documents are Markdown (`.md`).
- **Language:** All documentation is written in English.
- **Structure:** Each domain folder groups related documentation by topic.
- **Cross-references:** Use relative paths when linking between documents (e.g., `../06-backend/architecture.md`).
- **Diagrams:** Mermaid syntax is used for diagrams where applicable.
- **Code examples:** All code snippets use fenced code blocks with language tags.
- **Line length:** Soft-wrapped at ~120 characters for readability.
