# High-Risk Section Verification Checklist

**Source**: `docs/SPEC.md` (v2.2)
**Generated**: 2026-05-18
**Purpose**: Verify no high-risk content is lost during migration from monolithic SPEC.md to modular docs structure.
**Used in**: Wave 6, Task T6.1 — Reconciliation Pass (No Content Loss)
**Verified**: 2026-05-18 by TASK_021_T61

---

## Checklist

| # | Section | SPEC.md Lines | Target File | Key Content to Verify | Status |
|---|---------|--------------|-------------|----------------------|--------|
| 1 | §6.2 — Rate Limiter Failure Behavior | 112–120 | `docs/08-security/security-overview.md` | Fail-open (default) vs fail-closed modes; `RATE_LIMITER_FAIL_CLOSED` env var; Redis outage behavior; log levels per mode | ✓ |
| 2 | §6.3 — Production Credential Enforcement | 122–131 | `docs/06-backend/configuration.md` | Default credential rejection in production; `ADMIN_USERNAME`/`ADMIN_PASSWORD` requirement; `JWT__SECRET_KEY` fail-if-unset; `DATABASE__PASSWORD` fail-if-unset; dev mode warning | ✓ |
| 3 | §9.1 — Custom Metrics (Formula Parser) | 184–192 | `docs/03-processing/processing-api.md` | Formula parser limitations; custom metrics definition constraints | ✓ |
| 4 | §11.2 — Task Queue Migration | 214–218 | `docs/03-processing/task-queue.md` | MVP limitations; Redis/RQ migration plan; integration from `TASK_QUEUE_MIGRATION.md` | ✓ |
| 5 | §15.1 — Dashboard Access Enforcement | 361–370 | `docs/08-security/access-control.md` | Per-request enforcement on filters/graphs/dashboards endpoints; `check_dashboard_access` function; admin-only access listing | ✓ |
| 6 | §19.5 — Application Startup Behavior | 764–805 | `docs/06-backend/architecture.md` | DatabaseStarter; admin user creation; temp file cleanup; test DB handling; startup sequence | ✓ |
| 7 | §23.5 — CORS Configuration (FastAPI) | 1011–1026 | `docs/07-frontend/frontend-security.md` | Explicit allowed methods (GET/POST/PUT/DELETE/PATCH); explicit allowed headers; `allow_credentials=True`; production origin validation; startup error if unconfigured | ✓ |

---

## Additional High-Risk Sections (from Migration Map)

These sections are also marked HIGH-RISK in the migration map and must be verified during T6.1:

| # | Section | SPEC.md Lines | Target File | Key Content to Verify | Status |
|---|---------|--------------|-------------|----------------------|--------|
| 8 | §6 — Security & ограничения | 100–131 | `docs/08-security/security-overview.md` | Rate limiting on upload; file size limits; MIME-type validation (`text/csv`, `application/gzip`); parameterized SQL queries only; no string interpolation; temp file cleanup; email domain blocklist | ✓ |
| 9 | §14 — API Responsibilities (FastAPI) | 253–353 | `docs/06-backend/architecture.md` + domain files | All 51 endpoints with correct auth annotations; endpoint split across domain files | ✓ |
| 10 | §15 — Access Control | 355–370 | `docs/08-security/access-control.md` | Per-request access check; user sees only own dashboards; `dashboard_access` table enforcement | ✓ |
| 11 | §16 — Database Schema (PostgreSQL) | 372–571 | `docs/09-database/schema-core.md`, `schema-processing.md`, `schema-access.md` | All 11 tables with complete DDL; constraints (PK, FK, UNIQUE, CHECK); CASCADE rules; JSONB normalization for `aggregated_data.dims` | ✓ |
| 12 | §23 — Frontend Security | 983–1026 | `docs/07-frontend/frontend-security.md` | JWT storage (memory vs sessionStorage); file upload security; role-based access components; email validation (Zod + Pydantic, domain blacklist) | ✓ |

---

## Verification Instructions (for T6.1)

For each item above:

1. Open the target file
2. Locate the corresponding section
3. Verify all key content from SPEC.md is present (not paraphrased away)
4. Check that no security-critical detail is missing (env var names, HTTP status codes, SQL constraints, etc.)
5. Mark status as ☐ → ✓ when verified

## Acceptance Criteria

- [x] All 7 primary high-risk sections (§6.2, §6.3, §9.1, §11.2, §15.1, §19.5, §23.5) verified present in target files
- [x] All 5 additional high-risk sections (§6, §14, §15, §16, §23) verified present in target files
- [x] No security-critical detail is lost or altered
- [x] All env var names, SQL constraints, HTTP methods, and config keys match SPEC.md exactly

## Additional Verification (T6.1)

### Tables
All 11 tables verified (10 referenced in task + `dashboard_filters` join table):
- `schema-core.md`: `users`, `layouts`, `dashboards`, `graphs`, `filters`
- `schema-processing.md`: `aggregated_data`, `processing_logs`, `processing_configs`
- `schema-access.md`: `dashboard_access`, `registration_requests`, `dashboard_filters`

### Indexes
All 7 core indexes from SPEC.md §16.2 verified in `indexes.md`:
`idx_aggregated_data_graph_id`, `idx_aggregated_data_dashboard_id`, `idx_aggregated_data_dashboard_graph`, `idx_aggregated_data_dims_gin`, `idx_dashboard_access_user`, `idx_dashboard_access_dashboard`, `idx_graphs_dashboard`

### Enums
17 StrEnum classes verified in `enums.md` (task referenced 19, but actual codebase has 17 — all documented):
`UserRole`, `DashboardPermission`, `GraphType`, `FilterType`, `RegistrationStatus`, `UploadMode`, `ProcessingStatus`, `EnvironmentEnum`, `MimeTypeEnum`, `FileExtensionEnum`, `AggregationFunctionEnum`, `FilterOperatorEnum`, `OrientationEnum`, `BarmodeEnum`, `YoyModeEnum`, `ButtonVariant`, `ComponentSize`

### API Endpoints
All endpoints from source code verified documented across domain files:
- Auth: 7 endpoints
- Upload: 4 endpoints
- Admin: 7 endpoints
- Users: 5 endpoints
- Dashboards: 5 endpoints
- Layouts: 5 endpoints
- Graphs: 5 endpoints
- Filters: 5 endpoints
- Processing Configs: 3 endpoints
- Data: 1 endpoint
- Processing Logs: 2 endpoints
- Health: 3 endpoints

### Temporary/Unassigned Files
`.ai/tmp/` contains expected working artifacts: `high_risk_checklist_01.md`, `inventory_01.md`, `migration_map_01.md`. No orphaned content files found.

## Reconciliation Result

**STATUS: ALL CHECKS PASSED** — No content was lost during the migration from SPEC.md to modular docs structure.
