# Migration Map: SPEC.md Sections to Target Files

**Source**: `docs/SPEC.md` (v2.2)
**Generated**: 2026-05-18
**Purpose**: Map every `##` section from SPEC.md to its target file in the modular docs structure.

---

## Legend

- **HIGH-RISK** sections are marked with ⚠️
- Target paths are relative to `docs/`
- `99-reference/` is used for standalone/operational docs

---

## Mapping Table

| # | SPEC.md Section | Target File | Notes |
|---|----------------|-------------|-------|
| 1 | §1 — Purpose | `00-overview/purpose.md` | Russian language; overview of the system |
| 2 | §2 — Stack | `00-overview/stack.md` | Technology stack listing |
| 3 | §3 — Core Entities | `00-overview/entities.md` | User, Dashboard, Access, Data entities |
| 4 | §4 — Roles & Permissions | `01-auth/roles.md` | Russian language; Admin/Editor/Viewer roles |
| 5 | §5 — Authentication | `01-auth/authentication.md` | Login, bcrypt, JWT |
| 6 | §6 — Security & ограничения | `08-security/security-constraints.md` | ⚠️ HIGH-RISK; rate limiting, MIME, SQL injection, temp files, email blocklist |
| 6.1 | §6.1 — Configuration & Secrets Management | `08-security/configuration.md` | Env vars, Docker secrets, pydantic-settings |
| 6.2 | §6.2 — Rate Limiter Failure Behavior | `08-security/rate-limiter.md` | ⚠️ HIGH-RISK; fail-open vs fail-closed |
| 6.3 | §6.3 — Production Credential Enforcement | `08-security/credential-enforcement.md` | ⚠️ HIGH-RISK; default credential rejection |
| 7 | §7 — Data Flow | `00-overview/data-flow.md` | Upload → Parse → Transform → Aggregate → Store → Display |
| 8 | §8 — Data Upload | `03-processing/upload.md` | CSV/CSV.gz format, encoding, lifecycle |
| 9 | §9 — Data Processing | `03-processing/processing.md` | Pipeline: read, transform, aggregate |
| 9.1 | §9.1 — Custom Metrics (Formula Parser) | `03-processing/custom-metrics.md` | Formula parser limitations |
| 10 | §10 — Data Storage | `09-database/storage.md` | Aggregated data, JSONB, shared data |
| 11 | §11 — Background Processing | `03-processing/background.md` | Async task queue, processing_logs |
| 11.1 | §11.1 — Task Ownership Validation | `03-processing/background.md` | Cross-dashboard task prevention (same file as §11) |
| 11.2 | §11.2 — Task Queue Migration | `99-reference/TASK_QUEUE_MIGRATION.md` | Already exists; standalone doc |
| 12 | §12 — Dashboards | `02-dashboards/dashboards.md` | Config-driven, graph types, features |
| 13 | §13 — Filters | `02-dashboards/filters.md` | Global filters, backend implementation |
| 14 | §14 — API Responsibilities (FastAPI) | `06-backend/api-overview.md` | ⚠️ HIGH-RISK; all ~51 endpoints summary |
| 14.1 | §14.1 — Auth Endpoints | `01-auth/api-auth.md` | 7 auth endpoints |
| 14.2 | §14.2 — Dashboard Endpoints | `02-dashboards/api-dashboards.md` | 5 CRUD endpoints |
| 14.3 | §14.3 — Layout Endpoints | `02-dashboards/api-layouts.md` | 5 CRUD endpoints |
| 14.4 | §14.4 — Graph Endpoints | `02-dashboards/api-graphs.md` | 5 CRUD endpoints |
| 14.5 | §14.5 — Filter Endpoints | `02-dashboards/api-filters.md` | 5 CRUD endpoints |
| 14.6 | §14.6 — Processing Config Endpoints | `03-processing/api-processing-configs.md` | 3 endpoints |
| 14.7 | §14.7 — Data Endpoints | `03-processing/api-data.md` | 5 endpoints (aggregated, upload, process, status, result) |
| 14.8 | §14.8 — User Endpoints | `04-admin/api-users.md` | 6 endpoints |
| 14.9 | §14.9 — Admin Endpoints | `04-admin/api-admin.md` | 8 endpoints |
| 14.10 | §14.10 — Health Endpoints | `05-health/health.md` | 2 endpoints |
| 15 | §15 — Access Control | `08-security/access-control.md` | ⚠️ HIGH-RISK; per-request access check |
| 15.1 | §15.1 — Dashboard Access Enforcement | `08-security/access-control.md` | Same file as §15 |
| 16 | §16 — Database Schema (PostgreSQL) | `09-database/schema.md` | ⚠️ HIGH-RISK; DDL for 11 tables |
| 16.1 | §16.1 — Core Tables | `09-database/schema.md` | Same file as §16; all 11 table definitions |
| 16.2 | §16.2 — Indexes | `09-database/indexes.md` | 8 CREATE INDEX statements |
| 16.3 | §16.3 — Data Principles | `09-database/principles.md` | Russian language; flexibility, performance, security, scalability |
| 17 | §17 — Frontend Architecture (React SPA) | `07-frontend/architecture.md` | Clean Architecture + FSD |
| 17.1 | §17.1 — Общая концепция | `07-frontend/architecture.md` | Same file as §17 |
| 17.2 | §17.2 — Ключевые принципы | `07-frontend/architecture.md` | Same file as §17 |
| 17.3 | §17.3 — Project Structure (Frontend) | `07-frontend/project-structure.md` | Directory tree, feature-sliced |
| 18 | §18 — UI Pages (React SPA) | `07-frontend/ui-pages.md` | 8 pages overview |
| 18.1 | §18.1 — Login Page (`/login`) | `07-frontend/ui-pages.md` | Same file as §18 |
| 18.2 | §18.2 — Registration Page (`/register`) | `07-frontend/ui-pages.md` | Same file as §18 |
| 18.3 | §18.3 — Dashboard List Page (`/dashboards`) | `07-frontend/ui-pages.md` | Same file as §18 |
| 18.4 | §18.4 — Dashboard View Page (`/dashboard/:id`) | `07-frontend/ui-pages.md` | Same file as §18 |
| 18.5 | §18.5 — User Profile Page (`/profile`) | `07-frontend/ui-pages.md` | Same file as §18 |
| 18.6 | §18.6 — Change Password Page | `07-frontend/ui-pages.md` | Same file as §18 |
| 18.7 | §18.7 — Admin Panel (`/admin`) | `07-frontend/ui-pages.md` | Same file as §18 |
| 18.8 | §18.8 — Data Upload Page | `07-frontend/ui-pages.md` | Same file as §18 |
| 19 | §19 — Architecture (React + FastAPI) | `06-backend/architecture.md` | Integration architecture |
| 19.1 | §19.1 — Общая архитектура | `06-backend/architecture.md` | Same file as §19 |
| 19.2 | §19.2 — Ключевые принципы | `06-backend/architecture.md` | Same file as §19 |
| 19.3 | §19.3 — Поток работы | `06-backend/architecture.md` | Same file as §19 |
| 19.4 | §19.4 — Stateless Architecture | `06-backend/architecture.md` | Same file as §19 |
| 19.5 | §19.5 — Application Startup Behavior | `06-backend/startup.md` | DatabaseStarter, admin creation, cleanup |
| 20 | §20 — Logging | `06-backend/logging.md` | Log levels, language requirement |
| 20.1 | §20.1 — Code Comments | `06-backend/logging.md` | Same file as §20 |
| 21 | §21 — Testing | `06-backend/testing.md` | pytest, coverage areas |
| 22 | §22 — Enums (StrEnum) | `06-backend/enums.md` | 17 StrEnum class definitions |
| 23 | §23 — Frontend Security | `08-security/frontend-security.md` | ⚠️ HIGH-RISK; JWT, CORS, file upload, roles |
| 23.1 | §23.1 — JWT Handling | `08-security/frontend-security.md` | Same file as §23 |
| 23.2 | §23.2 — File Upload | `08-security/frontend-security.md` | Same file as §23 |
| 23.3 | §23.3 — Role-Based Access | `08-security/frontend-security.md` | Same file as §23 |
| 23.4 | §23.4 — Email Validation (Registration) | `08-security/frontend-security.md` | Same file as §23 |
| 23.5 | §23.5 — CORS Configuration (FastAPI) | `08-security/cors.md` | CORS middleware, explicit methods/headers |
| 24 | §24 — Deployment | `10-deployment/deployment.md` | Dev and production deployment |
| 24.1 | §24.1 — Development | `10-deployment/development.md` | Dev server setup, CORS, hot reload |
| 24.2 | §24.2 — Production | `10-deployment/production.md` | FastAPI static files or Nginx proxy |
| 24.3 | §24.3 — No Overengineering | `10-deployment/no-overengineering.md` | Simplicity principles |
| 24.4 | §24.4 — Миграция с Dash | `10-deployment/dash-migration.md` | Dash fallback or full replacement |

---

## Standalone Docs → `99-reference/`

These documents already exist in `docs/` and are mapped to `99-reference/` as operational/reference docs:

| Document | Target Path | Source Section |
|----------|-------------|----------------|
| `TASK_QUEUE_MIGRATION.md` | `99-reference/TASK_QUEUE_MIGRATION.md` | §11.2 |
| `SWAGGER_README.md` | `99-reference/SWAGGER_README.md` | Operational (not in SPEC) |
| `RUN.md` | `99-reference/RUN.md` | Operational (not in SPEC) |

---

## High-Risk Sections Summary (7 total)

All high-risk sections have explicit target locations:

| # | Section | Target File | Risk Reason |
|---|---------|-------------|-------------|
| 1 | §6 — Security & ограничения | `08-security/security-constraints.md` | Core security constraints |
| 2 | §6.2 — Rate Limiter Failure Behavior | `08-security/rate-limiter.md` | Fail-open vs fail-closed |
| 3 | §6.3 — Production Credential Enforcement | `08-security/credential-enforcement.md` | Default credential rejection |
| 4 | §14 — API Responsibilities (FastAPI) | `06-backend/api-overview.md` | ~51 endpoints, auth requirements |
| 5 | §15 — Access Control | `08-security/access-control.md` | Per-request enforcement |
| 6 | §16 — Database Schema (PostgreSQL) | `09-database/schema.md` | DDL, constraints, CASCADE |
| 7 | §23 — Frontend Security | `08-security/frontend-security.md` | JWT, CORS, file upload, roles |

---

## Target File Inventory

### `00-overview/` (4 files)
- `purpose.md` — §1
- `stack.md` — §2
- `entities.md` — §3
- `data-flow.md` — §7

### `01-auth/` (3 files)
- `roles.md` — §4
- `authentication.md` — §5
- `api-auth.md` — §14.1

### `02-dashboards/` (7 files)
- `dashboards.md` — §12
- `filters.md` — §13
- `api-dashboards.md` — §14.2
- `api-layouts.md` — §14.3
- `api-graphs.md` — §14.4
- `api-filters.md` — §14.5

### `03-processing/` (6 files)
- `upload.md` — §8
- `processing.md` — §9
- `custom-metrics.md` — §9.1
- `background.md` — §11, §11.1
- `api-processing-configs.md` — §14.6
- `api-data.md` — §14.7

### `04-admin/` (2 files)
- `api-users.md` — §14.8
- `api-admin.md` — §14.9

### `05-health/` (1 file)
- `health.md` — §14.10

### `06-backend/` (6 files)
- `api-overview.md` — §14
- `architecture.md` — §19, §19.1, §19.2, §19.3, §19.4
- `startup.md` — §19.5
- `logging.md` — §20, §20.1
- `testing.md` — §21
- `enums.md` — §22

### `07-frontend/` (3 files)
- `architecture.md` — §17, §17.1, §17.2
- `project-structure.md` — §17.3
- `ui-pages.md` — §18, §18.1–18.8

### `08-security/` (7 files)
- `security-constraints.md` — §6
- `configuration.md` — §6.1
- `rate-limiter.md` — §6.2
- `credential-enforcement.md` — §6.3
- `access-control.md` — §15, §15.1
- `frontend-security.md` — §23, §23.1–23.4
- `cors.md` — §23.5

### `09-database/` (3 files)
- `storage.md` — §10
- `schema.md` — §16, §16.1
- `indexes.md` — §16.2
- `principles.md` — §16.3

### `10-deployment/` (4 files)
- `deployment.md` — §24
- `development.md` — §24.1
- `production.md` — §24.2
- `no-overengineering.md` — §24.3
- `dash-migration.md` — §24.4

### `99-reference/` (3 files — already exist)
- `TASK_QUEUE_MIGRATION.md` — §11.2 (already exists at `docs/TASK_QUEUE_MIGRATION.md`)
- `SWAGGER_README.md` — (already exists at `docs/SWAGGER_README.md`)
- `RUN.md` — (already exists at `docs/RUN.md`)

---

## Coverage Verification

- **Total `##` sections in SPEC.md**: 48
- **Sections mapped**: 48 (100%)
- **High-risk sections mapped**: 7/7 (100%)
- **Standalone docs mapped to `99-reference/`**: 3/3 (100%)
- **Unmapped sections**: 0
