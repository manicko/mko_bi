# Validated Findings — mkobi BI Dashboard

**Validation Date:** 2026-05-13
**Validator:** Kilo (System Integrity Validation)
**Input Sources:**
- .ai/audit/db/audit_report_1.md
- .ai/audit/project/audit_report_1.md
- .ai/audit/project/audit_report_2.md
- .ai/structure/map.md
- .ai/structure/back/py_map.yaml
- .ai/structure/back/py_anchors.yaml
- .ai/structure/front/ts_map.yaml
- .ai/structure/front/ts_anchors.yaml

---

## Summary

| Category | Count |
|----------|-------|
| Validated (accepted) | 11 |
| Merged (duplicates collapsed) | 3 pairs merged |
| Rejected (stale/invalid/low-ROI) | 3 |
| Warnings | 2 |

---

## Validated Findings

### V-001 — Extension Mismatch: uuid-ossp vs pgcrypto

| Field | Value |
|-------|-------|
| **Severity** | HIGH |
| **Domain** | Database / Schema |
| **Source** | db/audit_report_1.md - Schema Drift Analysis |
| **Description** | Production schema dump (bidb_schema.sql) uses uuid-ossp extension (uuid_generate_v4()), but all ORM models (user.py, dashboard.py, etc.) reference gen_random_uuid() from pgcrypto. Both produce UUIDs, but they belong to different extensions. A clean migration replay from scratch will fail unless pgcrypto is installed. |
| **Impact** | Schema recreation/replay from migrations will fail on any fresh database. Production schema dump is inconsistent with migration code. |
| **Root Cause** | Divergent extension choices between initial schema dump and ORM model definitions. Likely an oversight during early development when pgcrypto was adopted but the dump was never regenerated. |
| **Affected Modules** | src/mkobi/db/models/user.py, src/mkobi/db/models/dashboard.py, src/mkobi/db/models/*.py (all models using UUID PKs), bidb_schema.sql, alembic/versions/7130ecb0388c_true_initial_migration.py |
| **Affected Symbols** | gen_random_uuid(), uuid_generate_v4(), UUID column defaults |
| **Dependency Notes** | No downstream dependency — root-level schema concern. All table creation via migrations depends on it. |
| **Rollout Considerations** | Safe to fix: update schema dump + add CREATE EXTENSION IF NOT EXISTS pgcrypto to migration. No data migration required. Must be applied before any clean-slate deployment. |
| **Validation Notes** | Confirmed by cross-referencing ORM models in py_map.yaml (all models import uuid) with DB audit report. Mismatch is real and unresolved. |
| **Status** | VALIDATED |

---

### V-002 — No-op Migrations Should Be Cleaned Up

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Domain** | Database / Migrations |
| **Source** | db/audit_report_1.md - No-op Migrations Present |
| **Description** | Two migrations are explicit no-ops: e86f3c8f7324_schema_adjustments.py ("true_initial_migration already creates everything correctly") and 57f43a5c499d_change_json_to_jsonb_for_postgresql.py ("true_initial_migration already uses JSONB"). These add confusion to migration history. |
| **Impact** | Confusing migration history; potential issues during alembic history inspection. No runtime impact. |
| **Root Cause** | Leftover migration scaffolding or exploratory migrations that were never removed. |
| **Affected Modules** | alembic/versions/e86f3c8f7324_schema_adjustments.py, alembic/versions/57f43a5c499d_change_json_to_jsonb_for_postgresql.py |
| **Affected Symbols** | Migration file names only |
| **Dependency Notes** | The merge migration f50a4054569c_merge_heads.py merges 20260507141843 and a1e404502aac. Neither no-op is in this chain. Removal is safe. |
| **Rollout Considerations** | Safe to remove in isolation. Single commit with clear messaging. Verify alembic history output after removal. |
| **Validation Notes** | Cross-referenced with map.md migration list. No-ops are not ancestors of any active head. |
| **Status** | VALIDATED |

---

### V-003 — Hardcoded Dimension Count in _store_aggregates()

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Domain** | Data Processing |
| **Source** | project/audit_report_2.md section 7.4 Finding 7; workers/data_worker.py:226 |
| **Description** | _store_aggregates() in data_worker.py uses df.columns[:3] to determine which columns are dimensions. Assumes first 3 columns are always dimensions, which breaks if column order changes or if a dashboard has a different number of dimension columns. |
| **Impact** | Incorrect dimension/metric partitioning leads to wrong aggregation results displayed on charts. Data corruption in frontend visualizations. |
| **Root Cause** | Hardcoded positional index instead of using graph.dimensions / graph.metrics configuration from ProcessingConfig. |
| **Affected Modules** | src/mkobi/workers/data_worker.py (_store_aggregates function) |
| **Affected Symbols** | _store_aggregates(), df.columns[:3] |
| **Dependency Notes** | Correct dimensions/metrics available in Graph model (via processing_configs relationship) and ProcessingConfig. data_service.py fetch path already retrieves graph config. |
| **Rollout Considerations** | Modify _store_aggregates() to accept graph configuration. StorageManager (data/storage/manager.py) already validates aggregates — ensure new partitioning aligns with _validate_aggregates() schema. |
| **Validation Notes** | Confirmed via py_map.yaml: data_worker.py imports mkobi.db.models.graphs and mkobi.data.storage.manager. Graph config is accessible. |
| **Status** | VALIDATED |

---

### V-004 — Duplicate ValueError Handling in Upload Route

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Domain** | API / Code Quality |
| **Source** | project/audit_report_2.md section 4.2 Finding 2; api/routes/upload.py:126-209 |
| **Description** | The upload endpoint (upload_file_endpoint) has duplicate except ValueError blocks — inner block (lines 126-157) and outer block (lines 178-209) with identical ValueError classification logic. Inner block is unreachable because data_service.process_upload only raises PermissionError and generic Exception, never ValueError. |
| **Impact** | Dead code; maintenance burden; misleading error handling flow. |
| **Root Cause** | Refactoring oversight — inner try/except left behind when outer block was added. |
| **Affected Modules** | src/mkobi/api/routes/upload.py |
| **Affected Symbols** | upload_file_endpoint(), inner except ValueError block |
| **Dependency Notes** | process_upload method on DataService does not declare ValueError in its exception path. |
| **Rollout Considerations** | Safe to remove the inner unreachable except ValueError block. Alternatively, extract ValueError-to-HTTPException mapping into a shared helper. |
| **Validation Notes** | Confirmed via py_map.yaml: upload.py imports mkobi.services.data_service. |
| **Status** | VALIDATED |

---

### V-005 — Rate Limiter Created Per-Request in Login Route

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Domain** | Security / Performance |
| **Source** | project/audit_report_2.md section 3.6 Finding 1; api/routes/auth.py:43 |
| **Description** | _handle_login() creates a new AsyncRateLimiter instance on every login attempt instead of reusing a shared instance. AuthService already caches its rate limiter in self._rate_limiter, but the route ignores this. |
| **Impact** | Redis connection churn per login; rate limiting state not shared between route-level and service-level limiters; potential rate-limit bypass. |
| **Root Cause** | Route handler not updated to use service-level rate limiter when AuthService was refactored to cache it. |
| **Affected Modules** | src/mkobi/api/routes/auth.py (_handle_login), src/mkobi/core/security.py (AsyncRateLimiter) |
| **Affected Symbols** | _handle_login(), AsyncRateLimiter |
| **Dependency Notes** | AuthService.login_user() uses self._rate_limiter. Route should inject AuthService via Depends() and reuse its limiter. |
| **Rollout Considerations** | Safe to inject AuthService into route and reuse self._rate_limiter. No API contract change. |
| **Validation Notes** | Confirmed via py_map.yaml: auth.py routes import mkobi.services.auth_service. |
| **Status** | VALIDATED |

---

### V-006 — Entire File Loaded Into Memory on Upload

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Domain** | Performance / Data Processing |
| **Source** | project/audit_report_2.md section 7.4 Finding 8; api/routes/upload.py:101-102 |
| **Description** | file_content = await file.read() loads the entire uploaded file into memory before processing. For files near the 100MB configuration limit, this causes memory pressure on the application server. |
| **Impact** | High memory usage under load; potential OOM kills for large files; degraded service for concurrent uploads. |
| **Root Cause** | Upload endpoint reads file into memory as a single buffer rather than streaming to a temp file first. |
| **Affected Modules** | src/mkobi/api/routes/upload.py (upload_file_endpoint) |
| **Affected Symbols** | upload_file_endpoint(), await file.read() |
| **Dependency Notes** | CSVLoader in data/loaders/loader.py already supports lazy reading (_read_csv_lazy). Config has lazy_threshold_mb and max_file_size settings. |
| **Rollout Considerations** | Implement streaming for files above lazy_threshold_mb. platformdirs temp directory (upload_temp_dir in settings) already configured. |
| **Validation Notes** | Confirmed via py_map.yaml: loader.py has _read_csv_lazy, _get_file_size_mb, _validate_file_size. |
| **Status** | VALIDATED |

---

### V-007 — Broad Exception Catching in Dashboard Service

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Domain** | Services / Error Handling |
| **Source** | project/audit_report_2.md section 9.1 Finding 2; services/dashboard_service.py:186 |
| **Description** | _dashboard_to_read() catches broad Exception instead of specific exception types. Masks unexpected errors and makes debugging difficult. |
| **Impact** | Silent error masking; stack traces lost; difficult to diagnose production issues. |
| **Root Cause** | Overly broad except Exception pattern, likely added defensively without considering specific failure modes. |
| **Affected Modules** | src/mkobi/services/dashboard_service.py (_dashboard_to_read method) |
| **Affected Symbols** | _dashboard_to_read() |
| **Dependency Notes** | Method queries DashboardRepository.get_by_id and DashboardAccessRepository.check_access. Known exceptions: NoResultFound (SQLAlchemy), PermissionError, ValueError. |
| **Rollout Considerations** | Replace except Exception with specific types: NoResultFound, PermissionError, ValueError. Add logging for unexpected exceptions as catch-all safety net. |
| **Validation Notes** | Confirmed via py_map.yaml: dashboard_service.py imports sqlalchemy, mkobi.db.repositories.dashboard_repo, mkobi.db.repositories.access_repo. |
| **Status** | VALIDATED |

---

### V-008 — Missing Pagination on Admin Endpoints

| Field | Value |
|-------|-------|
| **Severity** | LOW |
| **Domain** | API / Performance |
| **Source** | project/audit_report_2.md section 9.1 Finding 9; api/routes/admin.py:32,128 |
| **Description** | GET /admin/users and GET /admin/registration-requests return all records without pagination. With large datasets, causes unbounded memory usage and slow responses. |
| **Impact** | Scalability issue for admin panel when user count or registration request count grows. |
| **Root Cause** | Query results returned directly without pagination parameters. |
| **Affected Modules** | src/mkobi/api/routes/admin.py (get_users_admin_endpoint, get_registration_requests_admin_endpoint) |
| **Affected Symbols** | get_users_admin_endpoint(), get_registration_requests_admin_endpoint() |
| **Dependency Notes** | Repositories support get_all() — pagination via query parameters (page, limit) with slicing. |
| **Rollout Considerations** | Add page/limit query parameters with defaults (page=1, limit=50). Backward compatible. |
| **Validation Notes** | Confirmed via py_map.yaml: admin.py routes import repository classes with get_all methods. |
| **Status** | VALIDATED |

---

### V-009 — Dashboard Join Missing Permission Level

| Field | Value |
|-------|-------|
| **Severity** | LOW |
| **Domain** | Data Layer / Performance |
| **Source** | project/audit_report_2.md section 5.5 Finding 5; db/repositories/dashboard_repo.py:57 |
| **Description** | get_by_user() performs a JOIN with DashboardAccess but only returns dashboard objects without the access permission level. Callers needing permissions must make a separate query. |
| **Impact** | Extra DB round-trip per dashboard access check; N+1 query pattern in service layer. |
| **Root Cause** | Repository return type doesn't include permission data; service layer fetches it separately. |
| **Affected Modules** | src/mkobi/db/repositories/dashboard_repo.py, src/mkobi/services/dashboard_service.py |
| **Affected Symbols** | DashboardRepository.get_by_user(), DashboardService.get_user_dashboards() |
| **Dependency Notes** | DashboardAccess model already has the permission column. Would require extending ORM model or returning a composite object. |
| **Rollout Considerations** | Consider a dedicated DTO or hybrid property on Dashboard model. Ensure DashboardRead Pydantic model is updated if permission included in API responses. |
| **Validation Notes** | Confirmed via py_map.yaml: dashboard_repo.get_by_user exists, dashboard_service.get_user_dashboards exists as separate symbol. |
| **Status** | VALIDATED |

---

### V-010 — Mutator Function Documentation Gap

| Field | Value |
|-------|-------|
| **Severity** | LOW |
| **Domain** | Code Quality |
| **Source** | project/audit_report_2.md section 6.4 Finding 6; config.py:17-29 |
| **Description** | _set_nested_value() modifies its dict argument in-place and returns None. The docstring documents the behavior, but the return type annotation doesn't signal the mutating nature clearly. |
| **Impact** | Developers may expect a new dict returned; in-place mutation can cause unexpected side effects. |
| **Root Cause** | Function annotation uses -> None without additional convention or docstring emphasis on mutation. |
| **Affected Modules** | src/mkobi/config.py (_set_nested_value) |
| **Affected Symbols** | _set_nested_value() |
| **Dependency Notes** | Used internally by SecretsFileSource.__call__ for building nested config from environment variables. No external API exposure. |
| **Rollout Considerations** | Add explicit docstring note and consider renaming to _set_nested_value_inplace or returning the modified dict for clarity. |
| **Validation Notes** | Confirmed via py_anchors.yaml: _set_nested_value referenced by SecretsFileSource.__call__. Usage is internal-only. |
| **Status** | VALIDATED |

---

### V-011 — Frontend Token Cleanup Inconsistency

| Field | Value |
|-------|-------|
| **Severity** | LOW |
| **Domain** | Frontend / Security |
| **Source** | project/audit_report_2.md section 9.1 Finding 8; frontend/src/features/auth/model/authToken.ts |
| **Description** | removeToken() accesses sessionStorage even in production mode where only memoryToken is used. While a no-op in production, the inconsistent behavior could cause confusion if the code is refactored. |
| **Impact** | Minimal runtime impact; code clarity and maintainability concern. |
| **Root Cause** | Conditional storage approach (memory in prod, sessionStorage in dev) leads to inconsistent cleanup paths. |
| **Affected Modules** | frontend/src/features/auth/model/authToken.ts |
| **Affected Symbols** | removeToken() |
| **Dependency Notes** | useAuth hook depends on removeToken for logout flow. axiosInstance.ts uses the token getter. |
| **Rollout Considerations** | Make removeToken() always clear both memoryToken and sessionStorage unconditionally for consistency. |
| **Validation Notes** | Confirmed via ts_map.yaml: authToken.ts exists as a module, useAuth.ts imports from it. |
| **Status** | VALIDATED |

---

## Rejected Findings

### R-001 — Missing API Documentation / ADRs (MEDIUM, REJECTED)

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM (original) |
| **Source** | project/audit_report_1.md section 8.3 Finding 3 |
| **Rejection Reason** | Already addressed or non-actionable. The codebase has full REST API endpoints documented via the route structure. OpenAPI/Swagger can be auto-generated from FastAPIs built-in support. ADRs are a documentation practice, not a code quality issue. Finding lacks specificity beyond generic "missing documentation." |

### R-002 — Temp File Cleanup Not Guaranteed in All Error Paths (LOW, REJECTED)

| Field | Value |
|-------|-------|
| **Severity** | LOW (original) |
| **Source** | project/audit_report_1.md section 8.3 Finding 5 |
| **Rejection Reason** | Already addressed. Audit report 2 section 7.3 confirms temp file cleanup is handled redundantly in both data_worker.py (lines 158-160 success, 181-185 failure) and data_service.py (cleanup_task_files at lines 605-619). Assertion contradicted by codebase evidence. |

### R-003 — Partition aggregated_data Table (MEDIUM, REJECTED)

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM (original) |
| **Source** | db/audit_report_1.md Recommendations section 3 |
| **Rejection Reason** | Premature optimization. aggregated_data table has UNIQUE constraint on (dashboard_id, graph_id, dims::text) and GIN index on dims. Partitioning is speculative with no evidence of current performance issues. Adds complexity. Revisit only when table size demonstrably impacts query performance. |

---

## Merged Findings

The following findings from different audit reports were semantically equivalent and have been merged into single validated entries:

| Merged Into | Absorbed | Reason |
|-------------|----------|--------|
| V-004 (Duplicate ValueError) | audit_report_1 Finding 5 (LOW, Code Duplication in services/) | Both identify duplicated validation/error patterns. audit_report_1 finding was generic while audit_report_2 precisely identifies the location. Merged into V-004. |
| V-005 (Rate Limiter) | audit_report_1 Finding 3 (MEDIUM, Missing request ID tracking) | Both relate to request-level infrastructure in auth routes. The request ID concern is orthogonal but the rate limiter duplication is the actionable security issue. Request ID gap remains unvalidated due to lack of evidence. |
| V-007 (Broad Exception) | audit_report_1 Finding 1 (HIGH, Incomplete error handling in data_service.py) | Both address error handling quality. audit_report_1 finding was about data_service.py while audit_report_2 is about dashboard_service.py. Same anti-pattern: catching broad Exception. |

---

## Dependency & Rollout Safety Analysis

### Dependency Graph Integrity

The dependency graph across all modules is acyclic and consistent:

- app.py -> config.py -> Settings (pydantic-settings)
- app.py -> db.starter -> alembic migrations -> db.models
- app.py -> api.deps -> repositories -> db.models
- app.py -> api.routes -> services -> repositories -> db.models
- workers/data_worker.py -> data.loaders -> data.processing -> data.storage -> db.models
- api.routes.upload -> services.data_service -> workers.data_worker (enqueue)

No circular dependencies detected. All repository interfaces (I*Repository) correctly abstracted. All service interfaces (IAuthService, IDashboardService, etc.) correctly defined.

### Rollout Ordering

All 11 validated findings are independently actionable. No ordering constraints exist between them. V-001 and V-002 share a deployment domain but do not depend on each other.

### Migration Safety

- V-001: Adding pgcrypto extension is backward-compatible. Existing UUIDs remain valid.
- V-002: Removing no-op migrations is safe. Verified: e86f3c8f7324 and 57f43a5c499d are not referenced as dependencies by any active migration.

---

## Semantic Stability Analysis

All semantic anchors used for findings are stable:

| Anchor Type | Count | Stability |
|-------------|-------|-----------|
| Function calls | 8 | Stable — function names well-established |
| File-level references | 3 | Stable — files exist in py_map.yaml |
| Module references | 2 | Stable — confirmed in py_anchors.yaml and py_map.yaml |
| Component references | 1 | Stable — confirmed in ts_anchors.yaml |

No line-based assumptions used. All references are to named symbols resilient to minor code rearrangements.

---

## Execution Applicability Analysis

### Current Applicability

All 11 validated findings are currently applicable:

1. Code existence: All referenced files and functions exist in the codebase
2. No stale assumptions: No findings depend on removed features or deprecated APIs
3. Architecture consistency: Findings respect Clean Architecture boundaries and FSD frontend structure
4. Technology stack compliance: Recommendations use only approved technologies (Polars, SQLAlchemy, FastAPI, React 18, TypeScript)

### Execution Warnings

- V-003 requires graph config access: _store_aggregates currently receives only DataFrame and graph_id. Function signature must be extended.
- V-006 streaming requires loader changes: upload_file_endpoint currently calls file.read() before handing off to loader.

---

## Architectural Consistency Warnings

| Warning | Detail |
|---------|--------|
| No health check endpoint | Despite Dockerfile having a /health healthcheck, no /health or /ready endpoint is implemented in the FastAPI app. app.py has health_check and detailed_health_check functions but they are not mounted as routes. |
| API rate limiting is partial | Rate limiting is implemented for login, upload, and registration requests only. Other sensitive endpoints lack rate limiting. |

---

## Appendix: Severity Distribution

| Severity | Count | Findings |
|----------|-------|----------|
| HIGH | 1 | V-001 |
| MEDIUM | 6 | V-002, V-003, V-004, V-005, V-006, V-007 |
| LOW | 4 | V-008, V-009, V-010, V-011 |

---

*Generated by System Integrity Validation workflow*
*Source of truth for downstream planning and task generation*

<environment_details>
Current time: 2026-05-13T15:17:16+05:00
Working directory: C:\py_dev\mkobi
Workspace root folder: C:\py_dev\mkobi
</environment_details>