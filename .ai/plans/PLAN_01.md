# PLAN_01 — Modular Spec + Minimal AI Metadata

**Phase:** 01 — Documentation Restructuring
**Status:** Ready for execution
**Created:** 2026-05-18
**Source:** `docs/SPEC.md` (1069 lines) + 4 standalone docs
**Target:** ~30 markdown files across 12 domain folders with YAML frontmatter

---

## Dependency Graph

```
Wave 1 (Preparation)
  ├── T1.1 Create folder structure
  ├── T1.2 Extract inventory from SPEC.md
  ├── T1.3 Build migration map
  └── T1.4 Create high-risk section checklist
        │
        ▼
Wave 2 (Core API domains) ── depends_on: Wave 1
  ├── T2.1 Create 00-overview/ files
  ├── T2.2 Create 01-auth/auth-api.md
  ├── T2.3 Create 02-dashboards/dashboards-api.md
  └── T2.4 Create 03-processing/ files
        │
        ▼
Wave 3 (Extended domains) ── depends_on: Wave 1
  ├── T3.1 Create 04-admin/admin-api.md
  ├── T3.2 Create 05-health/health-api.md
  ├── T3.3 Create 06-backend/ files
  ├── T3.4 Create 07-frontend/ files
  ├── T3.5 Create 08-security/ files
  ├── T3.6 Create 09-database/ files
  └── T3.7 Create 10-deployment/deployment.md
        │
        ▼
Wave 4 (SPEC.md conversion + README) ── depends_on: Wave 2, Wave 3
  ├── T4.1 Convert SPEC.md to system overview
  └── T4.2 Create docs/README.md root index
        │
        ▼
Wave 5 (Cross-linking + frontmatter) ── depends_on: Wave 4
  ├── T5.1 Add YAML frontmatter to all created files
  ├── T5.2 Add cross-links between domain files
  └── T5.3 Integrate standalone docs into 99-reference/
        │
        ▼
Wave 6 (Validation + cleanup) ── depends_on: Wave 5
  ├── T6.1 Reconciliation pass (no content loss)
  ├── T6.2 Frontmatter consistency check
  └── T6.3 Final structure verification
```

**Parallel execution:** Wave 2 and Wave 3 can run in parallel (both depend only on Wave 1). All other waves are sequential.

**Total tasks:** 22
**Estimated output files:** ~30 .md files + 1 README.md + modified SPEC.md

---

## Wave 1: Preparation

**Goal:** Create folder structure, extract complete inventory from SPEC.md, build section-to-file migration map, and create high-risk section checklist.
**Dependencies:** None (first wave)

---

### T1.1 — Create Folder Structure

**Action:** Create all target directories for the modular docs system.

**Files to create (directories):**
```
docs/00-overview/
docs/01-auth/
docs/02-dashboards/
docs/03-processing/
docs/04-admin/
docs/05-health/
docs/06-backend/
docs/07-frontend/
docs/08-security/
docs/09-database/
docs/10-deployment/
docs/90-adr/
docs/99-reference/
```

**Acceptance criteria:**
- All 13 directories exist under `docs/`
- Numbered folders use two-digit prefix (00-, 01-, … 10-, 90-, 99-)
- No files created yet — structure only

---

### T1.2 — Extract Inventory from SPEC.md

**Action:** Parse `docs/SPEC.md` and produce a complete inventory of all content elements.

**Output:** A working checklist (can be a temporary markdown file at `.ai/tmp/inventory_01.md`) listing:

| Item | Details |
|------|---------|
| All `##` sections | Section number, title, line range, line count |
| All `###` subsections | Parent section, title, line range |
| All SQL blocks | Which table(s) they define, line range |
| All code blocks | Language (python, yaml, json, bash), line range |
| All enums | Section 22 — list of all StrEnum classes |
| All API endpoints | Section 14 — method, path, auth level |
| All high-risk sections | The 7 sections from DECISION_01.md |
| All Russian-language sections | Sections with Russian text (sections 1-18 primarily) |
| All standalone doc references | Links to SWAGGER_README.md, RUN.md, TASK_QUEUE_MIGRATION.md |

**Acceptance criteria:**
- Every `##` section in SPEC.md is catalogued
- All 7 high-risk sections are flagged
- All SQL DDL blocks are identified with their table names
- All 19 StrEnum classes from section 22 are listed
- All ~30 API endpoints from section 14 are listed with method + path + auth
- Russian-language sections are identified for translation during migration

---

### T1.3 — Build Migration Map

**Action:** Map each SPEC.md section/subsection to its target file in the new structure.

**Output:** A mapping document (at `.ai/tmp/migration_map_01.md`) with format:

```
## SPEC.md → Target File Mapping

### Section 1. Purpose → docs/00-overview/overview.md
  - Content: System purpose description
  - Action: Translate Russian → English, rewrite as Purpose section

### Section 2. Stack → docs/00-overview/overview.md
  - Content: Technology stack list
  - Action: Include in overview as "Technology Stack" subsection

### Section 3. Core Entities → docs/00-overview/overview.md
  - Content: User, Dashboard, Access, Data entities
  - Action: Summarize in overview, cross-link to schema files

### Section 4. Roles & Permissions → docs/00-overview/overview.md
  - Content: Admin, Editor, Viewer roles
  - Action: Include in overview, cross-link to access-control.md

### Section 5. Authentication → docs/01-auth/auth-api.md
  - Content: Login flow, bcrypt, JWT
  - Action: Transfer to auth-api.md Main Concepts

### Section 6. Security → docs/08-security/security-overview.md
  - Content: Rate limiting, MIME checks, SQL injection prevention, etc.
  - Action: Transfer to security-overview.md

### Section 6.1 Configuration → docs/06-backend/configuration.md
  - Content: Config sources, secrets management, env vars
  - Action: Transfer to configuration.md

### Section 6.2 Rate Limiter Failure → docs/08-security/security-overview.md
  - Content: Fail-open/fail-closed behavior [HIGH-RISK]
  - Action: Transfer to security-overview.md under Edge Cases

### Section 6.3 Production Credentials → docs/06-backend/configuration.md
  - Content: Default credential rejection in production [HIGH-RISK]
  - Action: Transfer to configuration.md under Constraints

### Section 7. Data Flow → docs/00-overview/data-flow.md
  - Content: Upload → Parse → Transform → Aggregate → Save → Display
  - Action: Transfer to data-flow.md, expand with step details

### Section 8. Data Upload → docs/03-processing/processing-api.md
  - Content: CSV/CSV.gz format, encoding, temp file lifecycle
  - Action: Transfer to processing-api.md under Upload subsection

### Section 9. Data Processing → docs/03-processing/processing-api.md
  - Content: Processing trigger, pipeline, aggregation types
  - Action: Transfer to processing-api.md

### Section 9.1 Formula Parser → docs/03-processing/processing-api.md
  - Content: Custom metrics formula parser limitations [HIGH-RISK]
  - Action: Transfer to processing-api.md under Edge Cases

### Section 10. Data Storage → docs/09-database/schema-processing.md
  - Content: Aggregated data storage approach, JSONB structure
  - Action: Transfer to schema-processing.md as context for aggregated_data

### Section 11. Background Processing → docs/03-processing/processing-api.md
  - Content: Async task queue, processing_logs, status tracking
  - Action: Transfer to processing-api.md

### Section 11.1 Task Ownership → docs/03-processing/processing-api.md
  - Content: Cross-dashboard task validation
  - Action: Transfer to processing-api.md under Constraints

### Section 11.2 Task Queue Migration → docs/03-processing/task-queue.md
  - Content: MVP limitations, Redis/RQ migration plan [HIGH-RISK]
  - Action: Content already in TASK_QUEUE_MIGRATION.md — integrate into task-queue.md

### Section 12. Dashboards → docs/02-dashboards/dashboards-api.md
  - Content: Config-driven dashboards, graph types, features
  - Action: Transfer to dashboards-api.md

### Section 13. Filters → docs/02-dashboards/dashboards-api.md
  - Content: Global filters (year, category, brand), backend implementation
  - Action: Transfer to dashboards-api.md under Filters subsection

### Section 14. API Responsibilities → Split by domain:
  - 14.1 Auth → docs/01-auth/auth-api.md
  - 14.2-14.6 Dashboards/Layouts/Graphs/Filters/Processing → docs/02-dashboards/dashboards-api.md + docs/03-processing/processing-api.md
  - 14.7 Data → docs/03-processing/processing-api.md
  - 14.8 Users → docs/04-admin/admin-api.md
  - 14.9 Admin → docs/04-admin/admin-api.md
  - 14.10 Health → docs/05-health/health-api.md

### Section 15. Access Control → docs/08-security/access-control.md
  - Content: Per-request access check, user-dashboard filtering
  - Action: Transfer to access-control.md

### Section 15.1 Dashboard Access Enforcement → docs/08-security/access-control.md
  - Content: Specific endpoints with access validation [HIGH-RISK]
  - Action: Transfer to access-control.md under Constraints

### Section 16. Database Schema → docs/09-database/ (split by concern):
  - 16.1 Core Tables → schema-core.md (users, layouts, dashboards, graphs, filters)
  - 16.1 Core Tables (cont.) → schema-processing.md (aggregated_data, processing_logs, processing_configs)
  - 16.1 Core Tables (cont.) → schema-access.md (dashboard_access, registration_requests, dashboard_filters)
  - 16.2 Indexes → indexes.md
  - 16.3 Data Principles → schema-core.md (as design rationale)

### Section 17. Frontend Architecture → docs/07-frontend/:
  - 17.1-17.3 → architecture.md (Clean Architecture + FSD, key principles)
  - 17.3 Project Structure → fsd-structure.md (folder tree, feature layout)

### Section 18. UI Pages → docs/07-frontend/pages.md
  - Content: All 8 pages (Login, Register, Dashboard List, Dashboard View, Profile, Change Password, Admin, Upload)
  - Action: Transfer all 8 subsections to pages.md

### Section 19. Architecture (React + FastAPI) → docs/06-backend/architecture.md
  - Content: System architecture, stateless design, request flow
  - Action: Transfer to architecture.md

### Section 19.5 Application Startup → docs/06-backend/architecture.md
  - Content: DatabaseStarter, admin creation, temp file cleanup, test DB [HIGH-RISK]
  - Action: Transfer to architecture.md under Application Lifecycle

### Section 20. Logging → docs/06-backend/logging.md
  - Content: Logged events, levels, English language requirement
  - Action: Transfer to logging.md

### Section 20.1 Code Comments → docs/06-backend/logging.md
  - Content: English-only code comments requirement
  - Action: Append to logging.md as Code Standards subsection

### Section 21. Testing → docs/06-backend/testing.md
  - Content: pytest, coverage areas (API, processing, auth)
  - Action: Transfer to testing.md

### Section 22. Enums → docs/09-database/enums.md
  - Content: All 19 StrEnum classes with their values
  - Action: Transfer to enums.md with formatting

### Section 23. Frontend Security → docs/07-frontend/frontend-security.md
  - Content: JWT handling, file upload security, role-based access, email validation, CORS
  - Action: Transfer to frontend-security.md

### Section 23.5 CORS → docs/07-frontend/frontend-security.md
  - Content: CORS configuration, production validation [HIGH-RISK]
  - Action: Transfer to frontend-security.md under CORS Configuration

### Section 24. Deployment → docs/10-deployment/deployment.md
  - Content: Dev setup, production variants (A/B), no-overengineering, Dash migration
  - Action: Transfer to deployment.md
```

**Acceptance criteria:**
- Every `##` section from SPEC.md has a mapped target file
- All 7 high-risk sections have explicit target locations
- No section is left unmapped
- Standalone docs (TASK_QUEUE_MIGRATION.md, SWAGGER_README.md, RUN.md) are mapped to 99-reference/

---

### T1.4 — Create High-Risk Section Checklist

**Action:** Create a verification checklist for the 7 high-risk sections that must not be lost during migration.

**Output:** Checklist at `.ai/tmp/high_risk_checklist_01.md`:

```
## High-Risk Section Verification Checklist

| # | Section | Target File | Status |
|---|---------|-------------|--------|
| 1 | 6.2 Rate Limiter Failure Behavior | docs/08-security/security-overview.md | ☐ |
| 2 | 6.3 Production Credential Enforcement | docs/06-backend/configuration.md | ☐ |
| 3 | 9.1 Formula Parser limitations | docs/03-processing/processing-api.md | ☐ |
| 4 | 11.2 Task Queue Migration | docs/03-processing/task-queue.md | ☐ |
| 5 | 15.1 Dashboard Access Enforcement | docs/08-security/access-control.md | ☐ |
| 6 | 19.5 Application Startup Behavior | docs/06-backend/architecture.md | ☐ |
| 7 | 23.5 CORS validation behavior | docs/07-frontend/frontend-security.md | ☐ |
```

**Acceptance criteria:**
- All 7 high-risk sections listed with exact target file paths
- Checklist will be used in Wave 6 (T6.1) to verify no content loss

---

## Wave 2: Core API Domain Migration

**Goal:** Transfer content from SPEC.md into the overview, auth, dashboards, and processing domain files.
**Dependencies:** Wave 1 (T1.3 migration map)

---

### T2.1 — Create 00-overview/ Files

**Files to create:**
- `docs/00-overview/overview.md`
- `docs/00-overview/data-flow.md`

**`overview.md` content (from SPEC.md):**
- Section 1: Purpose → `## Purpose` (translate Russian → English)
- Section 2: Stack → `## Technology Stack`
- Section 3: Core Entities → `## Core Entities` (User, Dashboard, Access, Data — summary level)
- Section 4: Roles & Permissions → `## Roles & Permissions` (Admin, Editor, Viewer)
- Section 14: API Responsibilities (summary) → `## API Overview` (brief summary per domain with cross-links)

**`data-flow.md` content (from SPEC.md):**
- Section 7: Data Flow → `## Main Data Flow` (upload → parse → transform → aggregate → save → display)
- Section 8: Data Upload → `## Upload Flow` (as part of the data flow context)
- Section 10: Data Storage → `## Storage Model` (aggregated-only, JSONB approach)

**Acceptance criteria:**
- `overview.md` contains Purpose, Technology Stack, Core Entities, Roles, API Overview
- `data-flow.md` contains the complete end-to-end data flow
- All Russian text translated to English
- Cross-links added to domain-specific files (e.g., "See [auth-api.md](01-auth/auth-api.md) for authentication details")
- No YAML frontmatter yet (added in Wave 5)

---

### T2.2 — Create docs/01-auth/auth-api.md

**File to create:** `docs/01-auth/auth-api.md`

**Content (from SPEC.md):**
- Section 5: Authentication → `## Purpose` + `## Main Concepts` (login flow, bcrypt, JWT)
- Section 14.1: Auth Endpoints → `## Endpoints` (all 7 auth endpoints with method, path, request/response)
- Section 18.1: Login Page → `## Login Page` (UI reference)
- Section 18.2: Registration Page → `## Registration Page` (UI reference)
- Section 18.6: Change Password Page → `## Change Password` (endpoint + UI reference)

**Structure:**
```markdown
# Authentication API

## Purpose
...

## Main Concepts
- Login: email + password → bcrypt hash → JWT
- All API endpoints protected by JWT

## Endpoints
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /api/v1/auth/login | Public | Login, returns {access_token, user} |
| ... | ... | ... | ... |

## Flows
### Login Flow
1. User submits email + password
2. Server validates against users table (bcrypt)
3. Server returns JWT access_token
4. Client stores token in memory (prod) or sessionStorage (dev)

### Registration Flow
1. User submits email to /register-request
2. Admin approves via /admin/registration-requests/:id/approve
3. System generates temp password via secrets.token_urlsafe(16)

## Constraints
- Login and registration-request endpoints are rate-limited (Redis-based)
- Email domain blocklist checked during registration
- JWT required for all non-auth endpoints

## Edge Cases
- Rate limiter fail-open/fail-closed behavior (see security-overview.md)

## Related Docs
- security-overview.md — Rate limiting details
- auth-flow.md — Frontend JWT handling
- access-control.md — Role-based access enforcement
```

**Acceptance criteria:**
- All 7 auth endpoints documented with method, path, auth level, description
- Login and registration flows described step-by-step
- Cross-links to security-overview.md, auth-flow.md, access-control.md
- Russian text translated to English

---

### T2.3 — Create docs/02-dashboards/dashboards-api.md

**File to create:** `docs/02-dashboards/dashboards-api.md`

**Content (from SPEC.md):**
- Section 12: Dashboards → `## Main Concepts` (config-driven, graph types, features)
- Section 13: Filters → `## Filters` (global filters, backend implementation)
- Section 14.2: Dashboard Endpoints → `## Dashboard Endpoints`
- Section 14.3: Layout Endpoints → `## Layout Endpoints`
- Section 14.4: Graph Endpoints → `## Graph Endpoints`
- Section 14.5: Filter Endpoints → `## Filter Endpoints`
- Section 14.6: Processing Config Endpoints → `## Processing Config Endpoints`
- Section 18.3: Dashboard List Page → `## Dashboard List Page`
- Section 18.4: Dashboard View Page → `## Dashboard View Page`

**Acceptance criteria:**
- All CRUD endpoints for dashboards, layouts, graphs, filters documented
- Graph types (bar, line, pie, table) and features (multi-axis, YoY) described
- Filter types and backend implementation approach described
- UI page references included for frontend context
- Cross-links to schema-core.md, access-control.md

---

### T2.4 — Create docs/03-processing/ Files

**Files to create:**
- `docs/03-processing/processing-api.md`
- `docs/03-processing/task-queue.md`

**`processing-api.md` content (from SPEC.md):**
- Section 8: Data Upload → `## Upload` (CSV/CSV.gz, UTF-8, temp file lifecycle)
- Section 9: Data Processing → `## Processing Pipeline` (trigger, pipeline steps, aggregation types)
- Section 9.1: Formula Parser → `## Custom Metrics` + `## Edge Cases` (parser limitations) [HIGH-RISK]
- Section 11: Background Processing → `## Background Processing` (async queue, processing_logs)
- Section 11.1: Task Ownership → `## Constraints` (cross-dashboard validation)
- Section 14.7: Data Endpoints → `## Endpoints` (aggregated data, upload, process trigger, status, result)
- Section 18.8: Data Upload Page → `## Upload Page` (UI reference)

**`task-queue.md` content:**
- Integrate content from `docs/TASK_QUEUE_MIGRATION.md` (current state, limitations, target architecture, migration steps)
- Section 11.2: Task Queue Migration reference → link to this file [HIGH-RISK]

**Acceptance criteria:**
- `processing-api.md` covers upload, processing pipeline, background processing, and all data endpoints
- Formula parser limitations documented under Edge Cases
- Task ownership validation documented under Constraints
- `task-queue.md` contains complete migration plan from TASK_QUEUE_MIGRATION.md
- Cross-links between processing-api.md and task-queue.md

---

## Wave 3: Extended Domain Migration

**Goal:** Transfer content from SPEC.md into admin, health, backend, frontend, security, database, and deployment domain files.
**Dependencies:** Wave 1 (T1.3 migration map)
**Can run in parallel with:** Wave 2

---

### T3.1 — Create docs/04-admin/admin-api.md

**File to create:** `docs/04-admin/admin-api.md`

**Content (from SPEC.md):**
- Section 14.8: User Endpoints → `## User Management Endpoints`
- Section 14.9: Admin Endpoints → `## Admin Endpoints` (users, registration requests, logs)
- Section 18.7: Admin Panel → `## Admin Panel Pages` (User Management, Registration Requests, Dashboard Management, Log Viewer)

**Acceptance criteria:**
- All user management and admin endpoints documented
- Registration approval flow with temp_password generation described
- Admin panel UI pages referenced
- Cross-links to auth-api.md, access-control.md

---

### T3.2 — Create docs/05-health/health-api.md

**File to create:** `docs/05-health/health-api.md`

**Content (from SPEC.md):**
- Section 14.10: Health Endpoints → `## Endpoints` (basic + detailed health checks)

**Acceptance criteria:**
- Both health endpoints documented with response format
- DB connectivity check described
- Cross-links to architecture.md

---

### T3.3 — Create docs/06-backend/ Files

**Files to create:**
- `docs/06-backend/architecture.md`
- `docs/06-backend/configuration.md`
- `docs/06-backend/logging.md`
- `docs/06-backend/testing.md`

**`architecture.md` content (from SPEC.md):**
- Section 17.1-17.3: Frontend Architecture principles → adapted for backend context
- Section 19: Architecture (React + FastAPI) → `## System Architecture` (general architecture, stateless design, request flow)
- Section 19.4: Stateless Architecture → `## Stateless Design`
- Section 19.5: Application Startup → `## Application Lifecycle` (DatabaseStarter, admin creation, temp cleanup, test DB) [HIGH-RISK]

**`configuration.md` content (from SPEC.md):**
- Section 6.1: Configuration & Secrets Management → `## Configuration Sources` (priority chain, env vars, Docker secrets, .env, YAML)
- Section 6.3: Production Credential Enforcement → `## Production Requirements` (default credential rejection) [HIGH-RISK]
- Section 24.3: No Overengineering → `## Design Principles`

**`logging.md` content (from SPEC.md):**
- Section 20: Logging → `## Logging Standards` (logged events, levels)
- Section 20.1: Code Comments → `## Code Comment Standards` (English-only requirement)

**`testing.md` content (from SPEC.md):**
- Section 21: Testing → `## Testing Strategy` (pytest, coverage areas: API, processing, auth)

**Acceptance criteria:**
- `architecture.md` covers system architecture, stateless design, and complete application startup lifecycle
- `configuration.md` covers config source priority, secrets management, and production credential enforcement
- `logging.md` covers logging standards and English-only code comment requirement
- `testing.md` covers pytest strategy and coverage areas
- All Russian text translated to English

---

### T3.4 — Create docs/07-frontend/ Files

**Files to create:**
- `docs/07-frontend/architecture.md`
- `docs/07-frontend/fsd-structure.md`
- `docs/07-frontend/pages.md`
- `docs/07-frontend/auth-flow.md`
- `docs/07-frontend/upload-ui.md`
- `docs/07-frontend/frontend-security.md`

**`architecture.md` content (from SPEC.md):**
- Section 17.1-17.3: Frontend Architecture → `## Architecture` (Clean Architecture + FSD, key principles, separation of concerns)

**`fsd-structure.md` content (from SPEC.md):**
- Section 17.3: Project Structure → `## Project Structure` (complete folder tree with explanations)

**`pages.md` content (from SPEC.md):**
- Section 18.1: Login Page → `## Login Page`
- Section 18.2: Registration Page → `## Registration Page`
- Section 18.3: Dashboard List Page → `## Dashboard List Page`
- Section 18.4: Dashboard View Page → `## Dashboard View Page`
- Section 18.5: User Profile Page → `## User Profile Page`
- Section 18.6: Change Password Page → `## Change Password Page`
- Section 18.7: Admin Panel → `## Admin Panel`
- Section 18.8: Data Upload Page → `## Data Upload Page`

**`auth-flow.md` content (from SPEC.md):**
- Section 23.1: JWT Handling → `## JWT Handling` (storage: memory vs sessionStorage, interceptors)
- Section 23.3: Role-Based Access → `## Role-Based Access` (ProtectedRoute, RoleBasedAccess)
- Section 23.4: Email Validation → `## Email Validation` (Zod + Pydantic, domain blacklist)

**`upload-ui.md` content (from SPEC.md):**
- Section 23.2: File Upload → `## Upload Security` (rate limiting, file size, MIME validation)
- Section 18.8: Data Upload Page → `## Upload Page UI` (mode toggle, dropzone, progress)

**`frontend-security.md` content (from SPEC.md):**
- Section 23: Frontend Security → `## Security Measures`
- Section 23.5: CORS Configuration → `## CORS Configuration` (explicit methods/headers, production validation) [HIGH-RISK]

**Acceptance criteria:**
- All 8 UI pages documented in `pages.md` with their API endpoints and UI elements
- FSD structure clearly documented with folder tree
- Frontend auth flow covers JWT storage, role-based access, email validation
- Frontend security covers CORS, file upload security, JWT handling
- Cross-links to auth-api.md, processing-api.md, security-overview.md

---

### T3.5 — Create docs/08-security/ Files

**Files to create:**
- `docs/08-security/security-overview.md`
- `docs/08-security/access-control.md`

**`security-overview.md` content (from SPEC.md):**
- Section 6: Security & Limitations → `## Security Measures` (rate limiting, file size, MIME checks, SQL injection prevention, temp file cleanup, email domain blocklist)
- Section 6.2: Rate Limiter Failure Behavior → `## Failure Modes` (fail-open/fail-closed, RATE_LIMITER_FAIL_CLOSED env var) [HIGH-RISK]

**`access-control.md` content (from SPEC.md):**
- Section 15: Access Control → `## Access Control Model` (per-request check, user-dashboard filtering)
- Section 15.1: Dashboard Access Enforcement → `## Enforcement Points` (specific endpoints, check_dashboard_access function) [HIGH-RISK]

**Acceptance criteria:**
- `security-overview.md` covers all security constraints from section 6
- Rate limiter failure behavior documented with both modes
- `access-control.md` covers access control model and specific enforcement points
- Cross-links to auth-api.md, configuration.md, frontend-security.md

---

### T3.6 — Create docs/09-database/ Files

**Files to create:**
- `docs/09-database/schema-core.md`
- `docs/09-database/schema-processing.md`
- `docs/09-database/schema-access.md`
- `docs/09-database/indexes.md`
- `docs/09-database/enums.md`

**`schema-core.md` content (from SPEC.md):**
- Section 16.1: Core Tables → `users`, `layouts`, `dashboards`, `graphs`, `filters` tables (full DDL)
- Section 16.3: Data Principles → `## Design Principles` (flexibility, performance, security, scalability)

**`schema-processing.md` content (from SPEC.md):**
- Section 16.1: Core Tables → `aggregated_data`, `processing_logs`, `processing_configs` tables (full DDL)
- Section 10: Data Storage → context about aggregated-only storage approach

**`schema-access.md` content (from SPEC.md):**
- Section 16.1: Core Tables → `dashboard_access`, `registration_requests`, `dashboard_filters` tables (full DDL)

**`indexes.md` content (from SPEC.md):**
- Section 16.2: Indexes → all 7 CREATE INDEX statements with explanations

**`enums.md` content (from SPEC.md):**
- Section 22: Enums → all 19 StrEnum classes formatted as a reference table

**Acceptance criteria:**
- All 10 tables have complete DDL in the correct schema file
- All 7 indexes documented in indexes.md
- All 19 StrEnum classes documented in enums.md with their values
- JSONB normalization note included in schema-processing.md (aggregated_data.dims)
- Cross-links between schema files and API files

---

### T3.7 — Create docs/10-deployment/deployment.md

**File to create:** `docs/10-deployment/deployment.md`

**Content (from SPEC.md):**
- Section 24.1: Development → `## Development Setup` (React dev server + FastAPI, hot reload, .env)
- Section 24.2: Production → `## Production Deployment` (Option A: FastAPI serves static files, Option B: Nginx proxy)
- Section 24.3: No Overengineering → `## Design Principles`
- Section 24.4: Migration from Dash → `## Dash Migration` (fallback or full replacement)
- Content from `docs/README_DOCKER.md` → `## Docker Deployment` (multi-stage builds, compose, health checks)

**Acceptance criteria:**
- Development and production deployment options documented
- Docker deployment integrated from README_DOCKER.md
- Design principles (no overengineering) included
- Dash migration path documented
- Cross-links to configuration.md, architecture.md

---

## Wave 4: SPEC.md Conversion + README Creation

**Goal:** Convert SPEC.md from monolithic spec to system overview/documentation index. Create root README.md for navigation.
**Dependencies:** Wave 2, Wave 3 (all domain files must exist first)

---

### T4.1 — Convert SPEC.md to System Overview

**File to modify:** `docs/SPEC.md`

**Action:** Rewrite SPEC.md to serve as the high-level entry point. Keep it as "what the system is" while README.md becomes "how docs are organized."

**New SPEC.md structure:**
```markdown
# BI Dashboard System — Overview

## Purpose
[2-3 paragraph system summary: what it does, key capabilities]

## Technology Stack
[Concise stack list — backend, frontend, data, auth, tools]

## Architecture Summary
[High-level architecture diagram/description: React SPA ↔ FastAPI ↔ PostgreSQL]

## Main Data Flow
[End-to-end flow: Upload → Process → Store → Display]

## Documentation Structure
[Links to all domain folders with 1-line descriptions]
- [00-overview/](00-overview/) — System overview and data flow
- [01-auth/](01-auth/) — Authentication API
- [02-dashboards/](02-dashboards/) — Dashboards, layouts, graphs, filters API
- [03-processing/](03-processing/) — Data upload, processing, task queue
- [04-admin/](04-admin/) — Admin API
- [05-health/](05-health/) — Health check endpoints
- [06-backend/](06-backend/) — Backend architecture, config, logging, testing
- [07-frontend/](07-frontend/) — Frontend architecture, pages, security
- [08-security/](08-security/) — Security overview and access control
- [09-database/](09-database/) — Database schema, indexes, enums
- [10-deployment/](10-deployment/) — Deployment guide
- [90-adr/](90-adr/) — Architecture decision records
- [99-reference/](99-reference/) — Reference docs (Swagger, run guide)

## Key Design Decisions
[Links to ADRs and important constraints]

## Version History
- 2.2 (2026-05-16) — Updated with implemented features
- [Previous versions preserved]
```

**Acceptance criteria:**
- SPEC.md is no longer a monolithic spec but a system overview + doc index
- All domain folders are linked with descriptions
- Original author/date/version info preserved
- No content deleted — all details live in domain files now
- File is ~100-200 lines (down from 1069)

---

### T4.2 — Create docs/README.md

**File to create:** `docs/README.md`

**Action:** Create the root navigation index for the documentation system.

**Content:**
```markdown
# mkobi BI Dashboard — Documentation

## How This Documentation Is Organized

This documentation is structured by **domain** and **retrieval intent**. Each file
covers one coherent topic that can be loaded into context independently.

### Active System Domains (00–10)

| Folder | Domain | Description |
|--------|--------|-------------|
| [00-overview/](00-overview/) | Overview | System purpose, stack, data flow |
| [01-auth/](01-auth/) | Authentication | Auth endpoints, JWT, registration |
| [02-dashboards/](02-dashboards/) | Dashboards | Dashboard, layout, graph, filter CRUD |
| [03-processing/](03-processing/) | Processing | Upload, processing pipeline, task queue |
| [04-admin/](04-admin/) | Admin | User management, registration requests, logs |
| [05-health/](05-health/) | Health | Health check endpoints |
| [06-backend/](06-backend/) | Backend | Architecture, config, logging, testing |
| [07-frontend/](07-frontend/) | Frontend | React SPA, FSD, pages, security |
| [08-security/](08-security/) | Security | Rate limiting, access control |
| [09-database/](09-database/) | Database | Schema, indexes, enums |
| [10-deployment/](10-deployment/) | Deployment | Dev setup, production, Docker |

### Reference (90–99)

| Folder | Domain | Description |
|--------|--------|-------------|
| [90-adr/](90-adr/) | ADRs | Architecture decision records |
| [99-reference/](99-reference/) | Reference | Swagger guide, run guide |

### Reading Guide

- **New to the system?** Start with [SPEC.md](SPEC.md) for the overview,
  then [00-overview/](00-overview/) for details.
- **Building a feature?** Go directly to the relevant domain folder.
- **Debugging?** Check [08-security/](08-security/) for constraints and
  [06-backend/](06-backend/) for logging/config.
- **Deploying?** See [10-deployment/](10-deployment/).

### Document Conventions

- Each file has YAML frontmatter with `id`, `domain`, `tags`, `related`
- Required sections: `## Purpose`, `## Main Concepts`
- Recommended sections: `## Flows`, `## Constraints`, `## Edge Cases`, `## Related Docs`
- Cross-links use relative paths: `[text](folder/file.md)`
```

**Acceptance criteria:**
- README.md provides clear navigation for all 12 domain folders
- Reading guide helps users find the right doc quickly
- Document conventions are explained
- All links are valid relative paths

---

## Wave 5: Cross-Linking + Frontmatter Addition

**Goal:** Add YAML frontmatter to all created files, add cross-links between domain files, and integrate standalone docs into 99-reference/.
**Dependencies:** Wave 4 (SPEC.md converted, README.md created)

---

### T5.1 — Add YAML Frontmatter to All Created Files

**Action:** Add consistent YAML frontmatter to every `.md` file created in Waves 2-4.

**Frontmatter template applied to each file:**
```yaml
---
id: {kebab-case-id}
domain: {domain-name}
tags:
  - {tag1}
  - {tag2}
related:
  - {related-doc-id-1}
  - {related-doc-id-2}
---
```

**Domain values (fixed taxonomy, 12 values):**
`overview`, `auth`, `dashboards`, `processing`, `admin`, `health`, `backend`, `frontend`, `security`, `database`, `deployment`, `reference`

**Files requiring frontmatter (complete list):**
| File | id | domain |
|------|----|--------|
| `00-overview/overview.md` | `system-overview` | `overview` |
| `00-overview/data-flow.md` | `data-flow` | `overview` |
| `01-auth/auth-api.md` | `auth-api` | `auth` |
| `02-dashboards/dashboards-api.md` | `dashboards-api` | `dashboards` |
| `03-processing/processing-api.md` | `processing-api` | `processing` |
| `03-processing/task-queue.md` | `task-queue` | `processing` |
| `04-admin/admin-api.md` | `admin-api` | `admin` |
| `05-health/health-api.md` | `health-api` | `health` |
| `06-backend/architecture.md` | `backend-architecture` | `backend` |
| `06-backend/configuration.md` | `configuration` | `backend` |
| `06-backend/logging.md` | `logging` | `backend` |
| `06-backend/testing.md` | `testing` | `backend` |
| `07-frontend/architecture.md` | `frontend-architecture` | `frontend` |
| `07-frontend/fsd-structure.md` | `fsd-structure` | `frontend` |
| `07-frontend/pages.md` | `ui-pages` | `frontend` |
| `07-frontend/auth-flow.md` | `frontend-auth-flow` | `frontend` |
| `07-frontend/upload-ui.md` | `upload-ui` | `frontend` |
| `07-frontend/frontend-security.md` | `frontend-security` | `frontend` |
| `08-security/security-overview.md` | `security-overview` | `security` |
| `08-security/access-control.md` | `access-control` | `security` |
| `09-database/schema-core.md` | `schema-core` | `database` |
| `09-database/schema-processing.md` | `schema-processing` | `database` |
| `09-database/schema-access.md` | `schema-access` | `database` |
| `09-database/indexes.md` | `indexes` | `database` |
| `09-database/enums.md` | `enums` | `database` |
| `10-deployment/deployment.md` | `deployment` | `deployment` |
| `99-reference/swagger.md` | `swagger-guide` | `reference` |
| `99-reference/run-guide.md` | `run-guide` | `reference` |

**Acceptance criteria:**
- All 28 files have valid YAML frontmatter
- `id` matches filename (kebab-case, no `.md`)
- `domain` is one of the 12 fixed values
- `tags` has 3-8 relevant tags per file
- `related` has 3-5 co-retrieved doc IDs (no self-references)
- No frontmatter on SPEC.md or README.md (these are navigation files)

---

### T5.2 — Add Cross-Links Between Domain Files

**Action:** Add inline cross-links within each file's `## Related Docs` section and within body content where concepts reference other domains.

**Key cross-link pairs (minimum):**
- `auth-api.md` ↔ `auth-flow.md` (backend auth ↔ frontend auth)
- `auth-api.md` ↔ `security-overview.md` (rate limiting)
- `dashboards-api.md` ↔ `schema-core.md` (endpoints ↔ DDL)
- `dashboards-api.md` ↔ `access-control.md` (endpoints ↔ enforcement)
- `processing-api.md` ↔ `task-queue.md` (processing ↔ queue migration)
- `processing-api.md` ↔ `schema-processing.md` (processing ↔ data storage)
- `architecture.md` ↔ `configuration.md` (startup ↔ config)
- `frontend-security.md` ↔ `security-overview.md` (CORS ↔ rate limiting)
- `deployment.md` ↔ `configuration.md` (deployment ↔ config)
- `pages.md` ↔ `auth-flow.md` (UI pages ↔ auth flow)
- `pages.md` ↔ `upload-ui.md` (UI pages ↔ upload UI)

**Acceptance criteria:**
- Every file has a `## Related Docs` section with 3-5 cross-links
- Body content references use relative paths: `[text](folder/file.md)`
- No broken internal links (all targets exist)
- Cross-links are bidirectional (if A links to B, B links to A)

---

### T5.3 — Integrate Standalone Docs into 99-reference/

**Files to create:**
- `docs/99-reference/swagger.md`
- `docs/99-reference/run-guide.md`

**Action:**
1. Copy content from `docs/SWAGGER_README.md` → `99-reference/swagger.md`
2. Copy content from `docs/RUN.md` → `99-reference/run-guide.md`
3. Add a note at the top of each original file pointing to the new location

**Note format for original files:**
```markdown
> **Note:** This document has been migrated to the new modular documentation
> structure. See [99-reference/swagger.md](../99-reference/swagger.md) for the
> current version. This file is kept for backward compatibility.
```

**Acceptance criteria:**
- `99-reference/swagger.md` contains all content from SWAGGER_README.md
- `99-reference/run-guide.md` contains all content from RUN.md (translated to English)
- Original files have deprecation notes at the top
- TASK_QUEUE_MIGRATION.md content is integrated into `03-processing/task-queue.md` (done in T2.4)
- STRUCT.md is NOT migrated (it's a generated artifact, not a spec)

---

## Wave 6: Validation + Cleanup

**Goal:** Verify no content was lost, frontmatter is consistent, structure is correct, and all cross-links are valid.
**Dependencies:** Wave 5 (all files created and linked)

---

### T6.1 — Reconciliation Pass (No Content Loss)

**Action:** Verify that all 7 high-risk sections and all major content from SPEC.md exists in the new structure.

**Verification steps:**
1. Check each item from the high-risk checklist (T1.4):
   - `6.2 Rate Limiter Failure Behavior` → present in `security-overview.md`
   - `6.3 Production Credential Enforcement` → present in `configuration.md`
   - `9.1 Formula Parser limitations` → present in `processing-api.md`
   - `11.2 Task Queue Migration` → present in `task-queue.md`
   - `15.1 Dashboard Access Enforcement` → present in `access-control.md`
   - `19.5 Application Startup Behavior` → present in `architecture.md`
   - `23.5 CORS validation behavior` → present in `frontend-security.md`

2. Verify all 10 database tables have DDL in schema files
3. Verify all 19 StrEnum classes are in enums.md
4. Verify all ~30 API endpoints are documented in the correct domain files
5. Verify all 8 UI pages are documented in pages.md
6. Verify no `_UNASSIGNED_*` or temporary files remain

**Acceptance criteria:**
- All 7 high-risk sections verified present in target files
- All 10 tables, 7 indexes, 19 enums accounted for
- All API endpoints documented
- No temporary/unassigned files remain
- No content silently dropped

---

### T6.2 — Frontmatter Consistency Check

**Action:** Validate YAML frontmatter across all 28 files.

**Checks:**
- All files have `id` field (kebab-case, matches filename)
- All files have `domain` field (one of 12 fixed values)
- All `domain` values match the folder name
- All files have `tags` array (3-8 items)
- All files have `related` array (3-5 items, valid doc IDs)
- No frontmatter on SPEC.md or README.md
- No N/A filler in any file (empty sections omitted)

**Acceptance criteria:**
- All 28 files pass frontmatter validation
- No inconsistent field names or formats
- All `related` IDs reference existing files

---

### T6.3 — Final Structure Verification

**Action:** Verify the complete documentation structure matches the target from DECISION_01.md.

**Checks:**
```
docs/
├── README.md                    ✓ exists, valid navigation
├── SPEC.md                      ✓ converted to overview/index
├── 00-overview/
│   ├── overview.md              ✓ frontmatter ✓
│   └── data-flow.md             ✓ frontmatter ✓
├── 01-auth/
│   └── auth-api.md              ✓ frontmatter ✓
├── 02-dashboards/
│   └── dashboards-api.md        ✓ frontmatter ✓
├── 03-processing/
│   ├── processing-api.md        ✓ frontmatter ✓
│   └── task-queue.md            ✓ frontmatter ✓
├── 04-admin/
│   └── admin-api.md             ✓ frontmatter ✓
├── 05-health/
│   └── health-api.md            ✓ frontmatter ✓
├── 06-backend/
│   ├── architecture.md          ✓ frontmatter ✓
│   ├── configuration.md         ✓ frontmatter ✓
│   ├── logging.md               ✓ frontmatter ✓
│   └── testing.md               ✓ frontmatter ✓
├── 07-frontend/
│   ├── architecture.md          ✓ frontmatter ✓
│   ├── fsd-structure.md         ✓ frontmatter ✓
│   ├── pages.md                 ✓ frontmatter ✓
│   ├── auth-flow.md             ✓ frontmatter ✓
│   ├── upload-ui.md             ✓ frontmatter ✓
│   └── frontend-security.md     ✓ frontmatter ✓
├── 08-security/
│   ├── security-overview.md     ✓ frontmatter ✓
│   └── access-control.md        ✓ frontmatter ✓
├── 09-database/
│   ├── schema-core.md           ✓ frontmatter ✓
│   ├── schema-processing.md     ✓ frontmatter ✓
│   ├── schema-access.md         ✓ frontmatter ✓
│   ├── indexes.md               ✓ frontmatter ✓
│   └── enums.md                 ✓ frontmatter ✓
├── 10-deployment/
│   └── deployment.md            ✓ frontmatter ✓
├── 90-adr/
│   └── (empty — future ADRs)
└── 99-reference/
    ├── swagger.md               ✓ frontmatter ✓
    └── run-guide.md             ✓ frontmatter ✓
```

**Acceptance criteria:**
- All 28 .md files exist in correct locations
- Folder numbering follows convention (two-digit prefixes)
- File naming is kebab-case
- No files outside the target structure
- 90-adr/ is empty but exists for future use
- Total file count: 28 domain files + README.md + SPEC.md = 30 files

---

## Summary

| Wave | Tasks | Files Created | Dependencies |
|------|-------|---------------|--------------|
| Wave 1: Preparation | 4 | 0 (3 temp working files) | None |
| Wave 2: Core API Domains | 4 | 6 files | Wave 1 |
| Wave 3: Extended Domains | 7 | 20 files | Wave 1 |
| Wave 4: SPEC.md + README | 2 | 1 file (README), 1 modified (SPEC.md) | Wave 2 + Wave 3 |
| Wave 5: Cross-links + Frontmatter | 3 | 2 files (reference), 28 files updated | Wave 4 |
| Wave 6: Validation | 3 | 0 (validation only) | Wave 5 |
| **Total** | **22 tasks** | **~30 final .md files** | **Sequential waves** |

**Parallel execution:** Wave 2 and Wave 3 can execute concurrently.

**Risk mitigation:**
- High-risk sections tracked via checklist (T1.4) and verified in T6.1
- No silent dropping — unclear items go to temporary docs
- Migration map (T1.3) is the source of truth for content placement
- Reconciliation pass (T6.1) catches any lost content before completion
