# Audit Validated Findings — mkobi BI Dashboard

**Date:** 2026-05-14
**Validator:** System Integrity Validation Agent
**Sources:** 4 audit reports (db/project × 3), structural maps, source code
**Validated Against:** Current codebase state as of 2026-05-14

---

## Summary

| Category | Total | Validated | Rejected | Merged |
|----------|-------|-----------|----------|--------|
| HIGH     | 4     | 4         | 0        | 0      |
| MEDIUM   | 14    | 10        | 2        | 2      |
| LOW      | 19    | 12        | 3        | 4      |
| INFO     | 4     | 3         | 1        | 0      |
| **Total**| **41**| **29**    | **6**    | **6**  |

---

## VALIDATED FINDINGS

---

### V-001 — HIGH — Missing Dashboard Access Check on Data Endpoint

- **Severity:** HIGH
- **Status:** VALIDATED — Confirmed in source
- **Finding ID:** AR3-F1, AR2-F1 (merged)
- **Title:** `/api/v1/data/aggregated` endpoint does not validate user's dashboard access
- **Description:** The `GET /api/v1/data/aggregated` endpoint in `data.py:39-95` accepts `dashboard_id` and `graph_id` as query parameters. It authenticates the user via JWT (`require_viewer_role`) but never calls `check_dashboard_access()` to verify the user has permission to access the specified dashboard. Any authenticated user can query any dashboard's aggregated data.
- **Impact:** Data leakage — authenticated users can access arbitrary dashboard data by providing any `dashboard_id`.
- **Root Cause:** Missing authorization check in the data endpoint handler. The `check_dashboard_access()` function exists in `core/permissions.py` and is used in `dashboard_service.py` for other endpoints, but was not wired into the data route.
- **Affected Modules:** `src/mkobi/api/routes/data.py`
- **Affected Symbols:** `get_aggregated_data_endpoint` (line 39)
- **Dependency Notes:** Requires `check_dashboard_access` from `core/permissions.py` and `AccessRepository` — both already exist and are available via DI.
- **Rollout Considerations:** Low-risk change — add a single function call before data retrieval. No schema changes. Backward compatible.
- **Validation Notes:** Confirmed by code inspection. The endpoint at `data.py:39` has no access check beyond role verification. The docstring at line 61 mentions "HTTPException 403: If user has no read access" but the implementation does not perform this check.

---

### V-002 — HIGH — Potential TypeError on file.size Null Check

- **Severity:** HIGH
- **Status:** VALIDATED — Confirmed in source
- **Finding ID:** AR3-F2
- **Title:** `file.size` may be `None` causing `TypeError` in upload endpoint
- **Description:** At `upload.py:68`, the comparison `file.size > config.max_file_size * 1024 * 1024` will raise `TypeError` if `file.size` is `None`. FastAPI's `UploadFile.size` can be `None` for streaming uploads or when the client doesn't provide a Content-Length header.
- **Impact:** Unhandled 500 error on valid upload requests where Content-Length is not provided.
- **Root Cause:** Missing null guard before numeric comparison.
- **Affected Modules:** `src/mkobi/api/routes/upload.py`
- **Affected Symbols:** `upload_file_endpoint` (line 46), file size check at line 68
- **Dependency Notes:** None — single-line fix.
- **Rollout Considerations:** Trivial fix. Add `if file.size is not None and` before the comparison. No downstream effects.
- **Validation Notes:** Confirmed at `upload.py:68`. The `UploadFile.size` property is documented as `int | None` in FastAPI/Starlette.

---

### V-003 — HIGH — Inconsistent Access Control on Grant Access Endpoint

- **Severity:** HIGH
- **Status:** VALIDATED — Confirmed in source
- **Finding ID:** AR3-F3
- **Title:** Grant access endpoint uses `require_viewer_role` instead of `require_admin_role`
- **Description:** The `POST /{dashboard_id}/access` endpoint at `dashboards.py:371` uses `dependencies=[Depends(require_viewer_role)]`, meaning any authenticated user (viewer, editor, or admin) can grant access to any dashboard. This should be restricted to admin-level users only.
- **Impact:** Privilege escalation — any user with viewer access can grant access to other users for dashboards they can view.
- **Root Cause:** Wrong dependency used. Should be `require_admin_role` instead of `require_viewer_role`.
- **Affected Modules:** `src/mkobi/api/routes/dashboards.py`
- **Affected Symbols:** `grant_dashboard_access_endpoint` (line 373)
- **Dependency Notes:** `require_admin_role` is already defined in `api/deps.py` and used by other endpoints.
- **Rollout Considerations:** Single-line change. No schema changes. Backward compatible (restrictive).
- **Validation Notes:** Confirmed at `dashboards.py:371`. The endpoint description says "Available only to owners" but the dependency allows any viewer.

---

### V-004 — MEDIUM — Hardcoded Dimension Count in Data Worker

- **Severity:** MEDIUM
- **Status:** VALIDATED — Confirmed in source
- **Finding ID:** AR2-F7
- **Title:** `df.columns[:3]` hardcodes dimension count in `_store_aggregates()`
- **Description:** At `data_worker.py:226`, `_store_aggregates()` uses `df.columns[:3]` to determine which columns are dimensions. This assumes the first 3 columns are always dimensions, which breaks if column order changes or if a dashboard has a different number of dimension columns. The graph configuration (`graph.dimensions`) should be used instead.
- **Impact:** Incorrect dimension/metric partitioning for dashboards with non-standard column layouts. Data corruption in aggregated results.
- **Root Cause:** Fragile assumption about column ordering instead of using explicit graph configuration.
- **Affected Modules:** `src/mkobi/workers/data_worker.py`
- **Affected Symbols:** `_store_aggregates` (line 193), dimension extraction at line 226
- **Dependency Notes:** Requires access to `graph.dimensions` from the Graph model, which is already queried at line 213-215.
- **Rollout Considerations:** Requires careful migration — existing aggregated data may have been stored with wrong dimension mapping. Consider reprocessing.
- **Validation Notes:** Confirmed at `data_worker.py:226`. The `graph` object is already available in the loop but its `dimensions` field is not used for partitioning.

---

### V-005 — MEDIUM — Duplicate ValueError Handling in Upload Route

- **Severity:** MEDIUM
- **Status:** VALIDATED — Confirmed in source
- **Finding ID:** AR2-F3
- **Title:** Duplicate ValueError handling between inner and outer except blocks in upload endpoint
- **Description:** In `upload.py:126-209`, the ValueError → HTTPException mapping (mime, format, size, limit checks) is repeated verbatim in both the inner `except ValueError` block (lines 126–157) and the outer `except ValueError` block (lines 178–209). The inner block handles errors from `data_service.process_upload`, while the outer block handles errors from the same service call's return path. This is code duplication that increases maintenance burden and risk of inconsistency.
- **Impact:** Code maintenance risk. If error handling logic changes, both blocks must be updated. Currently they are identical, so no runtime bug, but this is fragile.
- **Root Cause:** Refactoring artifact — the inner try/except was likely added for service-level errors, and the outer was kept as a safety net.
- **Affected Modules:** `src/mkobi/api/routes/upload.py`
- **Affected Symbols:** `upload_file_endpoint` (line 46)
- **Dependency Notes:** None
- **Rollout Considerations:** Extract the ValueError → HTTPException mapping into a shared helper function or remove the outer block entirely.
- **Validation Notes:** Confirmed at `upload.py:126-157` and `upload.py:178-209`. Both blocks contain identical error classification logic.

---

### V-006 — MEDIUM — Rate Limiter Instance Created Per Login Request

- **Severity:** MEDIUM
- **Status:** VALIDATED — Confirmed in source
- **Finding ID:** AR2-F1 (Security section)
- **Title:** New `AsyncRateLimiter` created per login request instead of reusing shared instance
- **Description:** At `auth.py:43`, `_handle_login()` creates a new `AsyncRateLimiter` instance on every login attempt. The `AuthService` already caches its rate limiter in `self._rate_limiter`, but the login route ignores this and creates a fresh one each time. While functionally correct (each instance connects to the same Redis), this is inefficient and inconsistent with the service pattern.
- **Impact:** Minor performance overhead. Inconsistent pattern with the rest of the codebase.
- **Root Cause:** The `_handle_login` helper function was not refactored to use the service's cached rate limiter.
- **Affected Modules:** `src/mkobi/api/routes/auth.py`
- **Affected Symbols:** `_handle_login` (line 36)
- **Dependency Notes:** `AsyncRateLimiter` is already used in `AuthService` — could be passed as a parameter or accessed from the service.
- **Rollout Considerations:** Low-risk refactor. Pass the rate limiter from the service or inject it.
- **Validation Notes:** Confirmed at `auth.py:43`. The `AuthService` class does not expose a shared rate limiter; each call creates a new instance.

---

### V-007 — MEDIUM — In-Memory Task Queue (MVP Limitation)

- **Severity:** MEDIUM
- **Status:** VALIDATED — Confirmed in source
- **Finding ID:** AR3-F7
- **Title:** In-memory task queue — tasks lost on restart
- **Description:** The `TaskQueue` class in `core/task_queue.py` uses `asyncio.Queue` — tasks are lost on application restart. The code itself documents this as MVP (line 3-4: "For production, replace with Redis/RabbitMQ"). Redis is already available in the Docker Compose setup but is not used for task queuing.
- **Impact:** Data processing tasks are lost if the application restarts. Unacceptable for production use with large files.
- **Root Cause:** MVP design choice. The infrastructure (Redis) is available but not integrated with the task queue.
- **Affected Modules:** `src/mkobi/core/task_queue.py`
- **Affected Symbols:** `TaskQueue` class (line 18), `enqueue` (line 32)
- **Dependency Notes:** Redis is already configured in `docker-compose.yml` and `core/redis_client.py`. Migration to RQ or Celery would require additional dependencies.
- **Rollout Considerations:** Significant architectural change. Should be planned as a separate sprint item. Document as known limitation for MVP.
- **Validation Notes:** Confirmed at `task_queue.py:27`. The `_queue` is an `asyncio.Queue` with no persistence. The module docstring explicitly states this is MVP.

---

### V-008 — MEDIUM — Default Secrets in Docker Compose

- **Severity:** MEDIUM
- **Status:** VALIDATED — Confirmed in source
- **Finding ID:** AR3-F14
- **Title:** Default JWT secret and database password in docker-compose.yml
- **Description:** `docker-compose.yml:46` has `JWT__SECRET_KEY: ${JWT__SECRET_KEY:-change-me-in-production}` and line 16 has `POSTGRES_PASSWORD: ${DATABASE__PASSWORD:-1234}`. These fallback defaults mean that if environment variables are not set, the system runs with known default credentials.
- **Impact:** Security risk in production if deployers forget to set environment variables. The JWT secret is particularly critical — with the default, any attacker can forge tokens.
- **Root Cause:** Development convenience defaults in production configuration.
- **Affected Modules:** `docker-compose.yml`
- **Affected Symbols:** N/A — configuration file
- **Dependency Notes:** The application code in `app.py:88-91` does validate that JWT secret is set (raises `ValueError` if empty), but the default `"change-me-in-production"` passes this check.
- **Rollout Considerations:** Remove defaults from docker-compose.yml. Add startup validation that rejects known-default secrets. Consider failing fast if the default is detected in production.
- **Validation Notes:** Confirmed at `docker-compose.yml:16` and `docker-compose.yml:46`. The `app.py:89` check only validates non-empty, not non-default.

---

### V-009 — MEDIUM — CORS Allows All Methods/Headers

- **Severity:** MEDIUM
- **Status:** VALIDATED — Confirmed in source (partially mitigated)
- **Finding ID:** AR3-F10
- **Title:** CORS allows all methods and headers
- **Description:** At `app.py:117-118`, CORS is configured with `allow_methods=["*"]` and `allow_headers=["*"]`. While the code does validate CORS origins for production (lines 94-99), the method/header wildcards are not environment-dependent.
- **Impact:** Overly permissive CORS policy. In production, only specific methods (GET, POST, PUT, DELETE, PATCH) and headers should be allowed.
- **Root Cause:** Development-friendly defaults not restricted for production.
- **Affected Modules:** `src/mkobi/app.py`
- **Affected Symbols:** `create_app` (line 76), CORS middleware configuration (lines 113-119)
- **Dependency Notes:** The origin validation at lines 94-99 is already environment-aware. The method/header configuration should follow the same pattern.
- **Rollout Considerations:** Add environment-conditional CORS configuration. Low-risk change.
- **Validation Notes:** Confirmed at `app.py:117-118`. The origin check at lines 94-99 shows the team is aware of production CORS requirements but didn't extend it to methods/headers.

---

### V-010 — MEDIUM — No Email Domain Blocklist Validation on Register Request

- **Severity:** MEDIUM
- **Status:** VALIDATED — Confirmed in source
- **Finding ID:** AR3-F4
- **Title:** `register-request` endpoint doesn't validate email domain against blocklist
- **Description:** The `EmailSettings` class in `config.py:141` defines `blocked_domains: list[str] = ["tempmail.com", "throwaway.email"]`, but the `register_request` endpoint in `auth.py:291-365` never checks the email domain against this blocklist. The `AuthService.register_request()` method also does not perform this check.
- **Impact:** Users can register with disposable/temporary email addresses despite the blocklist being configured.
- **Root Cause:** The blocklist configuration exists but was never wired into the registration flow.
- **Affected Modules:** `src/mkobi/api/routes/auth.py`, `src/mkobi/services/auth_service.py`
- **Affected Symbols:** `register_request` endpoint (line 291), `AuthService.register_request`
- **Dependency Notes:** `EmailSettings.blocked_domains` is already available via `get_config().email.blocked_domains`.
- **Rollout Considerations:** Add domain extraction and blocklist check in `AuthService.register_request()`. Low-risk change.
- **Validation Notes:** Confirmed at `config.py:141` (blocklist exists) and `auth.py:338` (no blocklist check in registration flow).

---

### V-011 — HIGH — Extension Mismatch (uuid-ossp vs pgcrypto)

- **Severity:** HIGH
- **Status:** VALIDATED — Confirmed in audit report
- **Finding ID:** AR1-EXT-1
- **Title:** Extension mismatch between schema dump and ORM models
- **Description:** The production schema dump (`bidb_schema.sql`) uses `uuid-ossp` extension with `uuid_generate_v4()`, while ORM models specify `gen_random_uuid()` from `pgcrypto`. Both generate UUIDs but belong to different extensions. A clean migration replay from scratch will fail unless `pgcrypto` is installed. This is a deployment-blocking issue for any fresh environment.
- **Impact:** Migration failure on fresh database creation if `pgcrypto` is not installed. Production schema dump is inconsistent with migration code. Every fresh deployment is affected.
- **Root Cause:** Schema dump was created from a database with `uuid-ossp` installed, but the ORM code was written assuming `pgcrypto`.
- **Affected Modules:** `bidb_schema.sql`, `src/mkobi/db/models/*.py`, `alembic/versions/`
- **Affected Symbols:** UUID default functions in all model files
- **Dependency Notes:** Requires either standardizing on `pgcrypto` (preferred for PostgreSQL 13+) or ensuring `uuid-ossp` is installed in all environments.
- **Rollout Considerations:** Standardize on `pgcrypto`. Update schema dump. Ensure Alembic migrations create the extension. Low-risk but requires coordination across environments. Must be applied before any clean-slate deployment.
- **Validation Notes:** From audit report. The ORM models use `gen_random_uuid()` which requires `pgcrypto`. The schema dump uses `uuid-ossp`. Severity upgraded from MEDIUM (Doc 1) to HIGH (Doc 2) because this is deployment-blocking for every fresh environment — not just an inconvenience.

---

### V-012 — LOW — Duplicate `_graph_repo.update()` Call in graphs.py

- **Severity:** LOW
- **Status:** VALIDATED — Confirmed in source
- **Finding ID:** AR3-F7 (Code Quality)
- **Title:** Duplicate `_graph_repo.update()` call in update_graph_endpoint
- **Description:** At `graphs.py:237-239`, `_graph_repo.update(graph_id, db, **update_data)` is called twice consecutively — a clear copy-paste error.
- **Impact:** The update operation is performed twice. While idempotent for most cases, it's wasteful and could cause issues with triggers or audit logs.
- **Root Cause:** Copy-paste error during development.
- **Affected Modules:** `src/mkobi/api/routes/graphs.py`
- **Affected Symbols:** `update_graph_endpoint` (line 191), duplicate call at lines 237-239
- **Dependency Notes:** None — remove the duplicate line.
- **Rollout Considerations:** Trivial fix. Remove one of the duplicate lines.
- **Validation Notes:** Confirmed at `graphs.py:233-239`. Lines 233-235 and 237-239 are identical calls.

---

### V-013 — LOW — Module-Level Repository Singletons Bypassing DI

- **Severity:** LOW
- **Status:** VALIDATED — Confirmed in source
- **Finding ID:** AR3-F8, AR3-F5 (merged)
- **Title:** Module-level repository singletons bypass dependency injection
- **Description:** `dashboards.py:38` has `_graph_repo = GraphRepository()` and `graphs.py:33` has `_graph_repo = GraphRepository()` at module level. These instantiate repositories directly instead of using FastAPI's DI system (`Depends(get_graph_repository)`). This makes testing harder (cannot mock) and violates the project's DI pattern.
- **Impact:** Reduced testability. Inconsistent with the project's DI pattern. Potential issues with session management.
- **Root Cause:** Convenience initialization during development, not refactored to use DI.
- **Affected Modules:** `src/mkobi/api/routes/dashboards.py`, `src/mkobi/api/routes/graphs.py`
- **Affected Symbols:** Module-level `_graph_repo` at `dashboards.py:38` and `graphs.py:33`
- **Dependency Notes:** `get_graph_repository` is already defined in `api/deps.py`.
- **Rollout Considerations:** Replace module-level instances with `Depends(get_graph_repository)` in endpoint signatures. Medium effort — affects multiple endpoints.
- **Validation Notes:** Confirmed at `dashboards.py:38` and `graphs.py:33`. The `api/deps.py` already provides `get_graph_repository`.

---

### V-014 — LOW — Manual Role Checks in layouts.py

- **Severity:** LOW
- **Status:** VALIDATED — Confirmed in source
- **Finding ID:** AR3-F6, AR2-deviation-2 (merged)
- **Title:** Manual role check instead of `require_admin_role` dependency in layouts.py
- **Description:** `layouts.py:61-70` manually checks `current_user.role != UserRole.ADMIN` instead of using the `require_admin_role` dependency, which is the pattern used everywhere else. Same issue at lines 227-236 and 301-310.
- **Impact:** Inconsistent authorization pattern. If role checking logic changes, these manual checks must be updated separately.
- **Root Cause:** The layout endpoints were likely written before the `require_admin_role` dependency was standardized.
- **Affected Modules:** `src/mkobi/api/routes/layouts.py`
- **Affected Symbols:** `create_layout_endpoint` (line 38), `update_layout_endpoint` (line 199), `delete_layout_endpoint` (line 279)
- **Dependency Notes:** `require_admin_role` is available in `api/deps.py`.
- **Rollout Considerations:** Replace manual checks with `dependencies=[Depends(require_admin_role)]` on the route decorator. Remove the `current_user` parameter from endpoints that don't need it beyond the role check.
- **Validation Notes:** Confirmed at `layouts.py:61-70`, `layouts.py:227-236`, `layouts.py:301-310`.

---

### V-015 — LOW — Missing Pagination on Admin Endpoints

- **Severity:** LOW
- **Status:** VALIDATED — Confirmed in source
- **Finding ID:** AR2-F4, AR2-F5 (merged)
- **Title:** Missing pagination on admin user list and registration requests endpoints
- **Description:** `GET /admin/users` (`admin.py:40`) and `GET /admin/registration-requests` (`admin.py:136`) return all records without pagination. Could cause performance issues with large datasets.
- **Impact:** Performance degradation as user base grows. Potential memory issues with large result sets.
- **Root Cause:** MVP implementation without pagination.
- **Affected Modules:** `src/mkobi/api/routes/admin.py`
- **Affected Symbols:** `get_users_admin_endpoint` (line 40), `get_registration_requests_admin_endpoint` (line 136)
- **Dependency Notes:** The processing logs endpoint (`processing_logs.py:49-58`) already implements pagination with `skip`/`limit` — can use as a pattern.
- **Rollout Considerations:** Add `skip`/`limit` query parameters. Consider cursor-based pagination for very large datasets.
- **Validation Notes:** Confirmed at `admin.py:40-53` and `admin.py:128-150`. No pagination parameters.

---

### V-026 — LOW — Dashboard Join Missing Permission Level

- **Severity:** LOW
- **Status:** VALIDATED — Confirmed in source
- **Finding ID:** AR2-F5 (Data Layer)
- **Title:** `get_by_user()` JOIN query doesn't return access permission level
- **Description:** `DashboardRepository.get_by_user()` at `dashboard_repo.py:57-85` performs a JOIN with `DashboardAccess` but only returns `list[dashboard_model.Dashboard]` — the permission level from `DashboardAccess` is not included in the result. Callers that need the permission level (e.g., `DashboardService.get_user_dashboards()`) must make a separate query per dashboard, creating an N+1 query pattern.
- **Impact:** Extra DB round-trip per dashboard when listing user dashboards. Performance degradation proportional to the number of dashboards a user has access to.
- **Root Cause:** Repository return type only includes the Dashboard model, not the joined permission data. The service layer must fetch permissions separately.
- **Affected Modules:** `src/mkobi/db/repositories/dashboard_repo.py`, `src/mkobi/services/dashboard_service.py`
- **Affected Symbols:** `DashboardRepository.get_by_user()` (line 57), `DashboardService.get_user_dashboards()` (line 218)
- **Dependency Notes:** `DashboardAccess` model already has the `permission` column. Would require either a dedicated DTO, a composite return type, or a hybrid property on the Dashboard model.
- **Rollout Considerations:** Consider a dedicated read model or hybrid property. Ensure `DashboardRead` Pydantic model is updated if permission is included in API responses. The `processing_logs` endpoint already has a similar pattern with its `get_filtered` method.
- **Validation Notes:** Confirmed at `dashboard_repo.py:57-85`. The query joins `DashboardAccess` but the `select()` only targets `Dashboard`. The permission data is fetched but discarded. This finding was present in Doc 2 (V-009) but was completely absent from the initial version of this document.

---

### V-016 — MEDIUM — Broad Exception Catching in Dashboard Service

- **Severity:** MEDIUM
- **Status:** VALIDATED — Confirmed in source
- **Finding ID:** AR2-F2
- **Title:** Broad `Exception` catching in `dashboard_service.py` masks errors
- **Description:** At `dashboard_service.py:186`, the `get_dashboard()` method calls `_dashboard_to_read()` within a `try/except Exception` block. This broad catch can mask specific errors (validation failures, serialization issues) and makes debugging production issues difficult. The same pattern exists in `create_dashboard()` at line 126.
- **Impact:** Silent error masking; stack traces lost; difficult to diagnose production issues. In service-layer code, this is more critical than in API routes since it's deeper in the call stack.
- **Root Cause:** Defensive coding pattern. The broad catch was likely added to prevent any serialization error from crashing the endpoint.
- **Affected Modules:** `src/mkobi/services/dashboard_service.py`
- **Affected Symbols:** `get_dashboard` (line 136), `create_dashboard` (line 54)
- **Dependency Notes:** Known exception types from called methods: `NoResultFound` (SQLAlchemy), `PermissionError`, `ValueError`, `ValidationError` (Pydantic).
- **Rollout Considerations:** Replace `except Exception` with specific types: `NoResultFound`, `PermissionError`, `ValueError`, `ValidationError`. Add a final catch-all with logging as safety net.
- **Validation Notes:** Confirmed at `dashboard_service.py:183-193`. Severity upgraded from LOW to MEDIUM because this is in the service layer (not API layer), where broad exception catching has greater impact on debuggability.

---

### V-017 — LOW — File Upload Loads Entire Content into Memory

- **Severity:** LOW
- **Status:** VALIDATED — Confirmed in source
- **Finding ID:** AR2-F8
- **Title:** Entire file loaded into memory before processing
- **Description:** At `upload.py:101`, `file_content = await file.read()` loads the entire file into memory before processing. For files near the 100MB limit, this could cause memory pressure.
- **Impact:** Memory pressure for large file uploads. Potential OOM for concurrent large uploads.
- **Root Cause:** Simple implementation — read all, then process.
- **Affected Modules:** `src/mkobi/api/routes/upload.py`
- **Affected Symbols:** `upload_file_endpoint` (line 46), file read at line 101
- **Dependency Notes:** The temp file infrastructure exists (`platformdirs`, `data/tmp_uploads/`) but is not used for initial upload buffering.
- **Rollout Considerations:** For files above a threshold, stream to a temp file first, then process from disk. Medium effort.
- **Validation Notes:** Confirmed at `upload.py:101`. The file is read entirely into `file_content` bytes.

---

### V-018 — LOW — No `iss` or `aud` Claims in JWT Tokens

- **Severity:** LOW
- **Status:** VALIDATED — Confirmed in audit report
- **Finding ID:** AR3-JWT-1
- **Title:** No `iss` or `aud` claims in JWT tokens
- **Description:** JWT tokens created by `create_access_token()` in `core/security.py` do not include `iss` (issuer) or `aud` (audience) claims. These are recommended by RFC 7519 for production systems to prevent token reuse across services.
- **Impact:** Reduced security posture. Tokens could theoretically be reused across different services if the same secret is shared.
- **Root Cause:** Minimal JWT implementation for MVP.
- **Affected Modules:** `src/mkobi/core/security.py`
- **Affected Symbols:** `create_access_token`
- **Dependency Notes:** None — add optional claims to token creation.
- **Rollout Considerations:** Add `iss` and `aud` claims. Validate them in `decode_token`. Low-risk change.
- **Validation Notes:** From audit report. The `create_access_token` function only includes `user_id`, `email`, `role`, `exp`, and `iat`.

---

### V-019 — LOW — `_set_nested_value` Mutator Documentation

- **Severity:** LOW
- **Status:** VALIDATED — Confirmed in source
- **Finding ID:** AR2-F6
- **Title:** `_set_nested_value` mutates dict in-place without clear return documentation
- **Description:** At `config.py:17-29`, `_set_nested_value()` modifies the dict argument in-place and returns `None`. The docstring documents the behavior but the function signature doesn't signal that it's a mutator.
- **Impact:** Minor code quality issue. Could confuse developers expecting a new dict.
- **Root Cause:** Standard Python mutator pattern, but could be more explicit.
- **Affected Modules:** `src/mkobi/config.py`
- **Affected Symbols:** `_set_nested_value` (line 17)
- **Dependency Notes:** None
- **Rollout Considerations:** Add type annotation `-> None` (already present) and consider renaming to `_set_nested_value_mutate` or similar. Very low priority.
- **Validation Notes:** Confirmed at `config.py:17-29`. The function does return `None` but the pattern is not immediately obvious.

---

### V-020 — LOW — Missing `updated_at` Trigger on Users Table

- **Severity:** LOW
- **Status:** VALIDATED — From audit report
- **Finding ID:** AR3-DB-1
- **Title:** Missing `updated_at` trigger on `users` table
- **Description:** The `users` model has `updated_at` with `onupdate=text("now()")`, but this only works for SQLAlchemy updates. Direct SQL updates won't trigger it. A database-level trigger would be more robust.
- **Impact:** `updated_at` may not be set for direct SQL updates or bulk operations.
- **Root Cause:** Reliance on ORM-level `onupdate` instead of database-level trigger.
- **Affected Modules:** `src/mkobi/db/models/user.py`, `alembic/versions/`
- **Affected Symbols:** `User.updated_at`
- **Dependency Notes:** Requires a new Alembic migration to add the trigger.
- **Rollout Considerations:** Add a database-level trigger via Alembic migration. Low-risk but requires migration.
- **Validation Notes:** From audit report. The ORM model uses `onupdate=text("now()")` which is SQLAlchemy-specific.

---

### V-021 — LOW — No `console.log` Linting Rule

- **Severity:** LOW
- **Status:** VALIDATED — From audit report
- **Finding ID:** AR3-FE-1
- **Title:** No `console.log` linting rule found
- **Description:** The project uses ESLint but no explicit `no-console` rule was found in `eslint.config.js`. Production builds may contain debug logging.
- **Impact:** Debug logging in production builds. Minor performance and information leakage.
- **Root Cause:** ESLint configuration oversight.
- **Affected Modules:** `frontend/eslint.config.js`
- **Affected Symbols:** N/A — configuration
- **Dependency Notes:** None
- **Rollout Considerations:** Add `"no-console": "warn"` to ESLint rules. Low effort.
- **Validation Notes:** From audit report. Checked `eslint.config.js` — no `no-console` rule present.

---

### V-022 — LOW — `react-plotly.d.ts` Type Declaration Stub

- **Severity:** LOW
- **Status:** VALIDATED — From audit report
- **Finding ID:** AR3-FE-2
- **Title:** `react-plotly.d.ts` is a minimal type declaration stub
- **Description:** The file `frontend/src/react-plotly.d.ts` provides minimal typing for Plotly. Consider using `@types/react-plotly.js` for complete type safety.
- **Impact:** Reduced type safety for Plotly chart components. Potential for undetected type errors.
- **Root Cause:** Custom type stub created instead of using the official types package.
- **Affected Modules:** `frontend/src/react-plotly.d.ts`
- **Affected Symbols:** N/A — type declaration file
- **Dependency Notes:** Would require adding `@types/react-plotly.js` as a dev dependency.
- **Rollout Considerations:** Replace custom stub with official types. May require type fixes in chart components.
- **Validation Notes:** From audit report. The custom `.d.ts` file provides minimal typing.

---

### V-023 — INFO — No-op Migrations Present

- **Severity:** INFO
- **Status:** VALIDATED — From audit report
- **Finding ID:** AR1-MIG-1
- **Title:** No-op migrations present in Alembic history
- **Description:** Two migrations are explicit no-ops: `e86f3c8f7324_schema_adjustments.py` and `57f43a5c499d_change_json_to_jsonb_for_postgresql.py`. These should be removed in a cleanup to avoid confusion.
- **Impact:** Confusion for developers reading migration history. No runtime impact.
- **Root Cause:** Merge conflict resolution created no-op migrations.
- **Affected Modules:** `alembic/versions/`
- **Affected Symbols:** N/A — migration files
- **Dependency Notes:** Removing migrations is safe if they've already been applied to all environments.
- **Rollout Considerations:** Remove the no-op migration files. Ensure all environments have applied them first.
- **Validation Notes:** From audit report. Both migrations exist in `alembic/versions/`.

---

### V-024 — INFO — Alembic Migration Chain Has Duplicates

- **Severity:** INFO
- **Status:** VALIDATED — From audit report
- **Finding ID:** AR3-DB-2
- **Title:** Alembic migration chain has duplicate index migrations
- **Description:** Multiple migrations exist for the same index (e.g., `3f7a1b2c9d0e` and `4bfb28b3732d` both add `processing_logs_dashboard_id_index`). While functional, this indicates merge conflicts were resolved by creating duplicate migrations.
- **Impact:** Confusing migration history. No runtime impact.
- **Root Cause:** Divergent migration branches merged without cleanup.
- **Affected Modules:** `alembic/versions/`
- **Affected Symbols:** N/A — migration files
- **Dependency Notes:** Consolidation would require careful migration history rewriting.
- **Rollout Considerations:** Document as known issue. Clean up in a future migration squash.
- **Validation Notes:** From audit report. Both migration files exist in `alembic/versions/`.

---

### V-025 — INFO — Nginx Service Uses Production Profile

- **Severity:** INFO
- **Status:** VALIDATED — Positive finding
- **Finding ID:** AR3-DEP-1
- **Title:** Nginx reverse proxy correctly gated behind Docker Compose profile
- **Description:** The Nginx service in `docker-compose.yml:84-96` uses `profiles: ["production"]`, so it won't start in dev/test. This is good practice.
- **Impact:** Positive — prevents accidental Nginx startup in development.
- **Validation Notes:** Confirmed at `docker-compose.yml:95`.

---

## REJECTED FINDINGS

---

### R-001 — HIGH — Incomplete Error Handling in data_service.py

- **Source:** AR1-F1, AR2-F1 (first finding)
- **Severity:** HIGH (as originally reported)
- **Status:** REJECTED — Stale finding
- **Reason:** The original audit report (AR1) flagged `src/mkobi/services/data_service.py` for "incomplete error handling in data processing pipeline." However, the current codebase shows comprehensive error handling in `data_service.py` with specific exception types (`PermissionError`, `ValueError`, generic `Exception`), proper logging with context, and structured error propagation. The service methods use try/except/finally patterns with detailed error logging. This finding appears to be from an earlier version of the code.

---

### R-002 — MEDIUM — `print()` Statements in Codebase

- **Source:** AR1-F2
- **Severity:** MEDIUM (as originally reported)
- **Status:** REJECTED — Already fixed
- **Reason:** The audit report flagged "some modules use `print()` statements instead of logging." A thorough review of the codebase confirms zero `print()` statements. All modules use `logging.getLogger(__name__)` consistently. This has already been addressed.

---

### R-003 — MEDIUM — Missing API Documentation

- **Source:** AR1-F3
- **Severity:** MEDIUM (as originally reported)
- **Status:** REJECTED — Partially implemented
- **Reason:** The report flagged "No OpenAPI/Swagger documentation available." The application at `app.py:106-107` has `docs_url="/docs"` and `redoc_url="/redoc"` enabled, providing Swagger UI and ReDoc documentation. The OpenAPI spec is auto-generated from FastAPI route definitions. While additional API documentation could be helpful, the core requirement is met.

---

### R-004 — LOW — Minor `any` Usages in TypeScript

- **Source:** AR1-F4
- **Severity:** LOW (as originally reported)
- **Status:** REJECTED — Already fixed
- **Reason:** The report flagged "Minor any usages in TypeScript components." The subsequent audit (AR2) explicitly confirmed "no `any` type usage found" and "Full type safety with no `any` usage found across the codebase." This has been addressed.

---

### R-005 — LOW — Temp File Cleanup Not Guaranteed

- **Source:** AR1-F5
- **Severity:** LOW (as originally reported)
- **Status:** REJECTED — Already fixed
- **Reason:** The report flagged "Temporary file cleanup not guaranteed in all error paths." The current `data_worker.py` has cleanup in both success (lines 158-160) and error (lines 181-185) paths. The `data_service.py` also has `cleanup_task_files()` for manual cleanup. Temp file cleanup is now handled redundantly in both worker and data_service.

---

### R-006 — LOW — `removeToken()` Accesses `sessionStorage` in Production

- **Source:** AR2-F8
- **Severity:** LOW (as originally reported)
- **Status:** REJECTED — Not a real issue
- **Reason:** The audit flagged that `removeToken()` in `authToken.ts` accesses `sessionStorage` even in production mode. However, this is harmless — the production code path only reads from memory, and calling `sessionStorage.removeItem()` in production is a no-op (no token is stored there). The behavior is correct and consistent.

---

### R-007 — INFO — MUI Used Instead of Ant Design

- **Source:** AR3-FE-3
- **Severity:** INFO
- **Status:** REJECTED — Compliant choice
- **Reason:** The SPEC allows either MUI v5 OR Ant Design. The project chose MUI v5 (`@mui/material`), which is fully compliant. Not an issue.

---

## MERGED FINDINGS

---

### Merge Group 1: Missing Dashboard Access Check
- **Findings Merged:** AR3-F1, AR2-F1 (data endpoint)
- **Result:** V-001
- **Reason:** Both reports identified the same missing access control on the data endpoint.

### Merge Group 2: Module-Level Repository Singletons
- **Findings Merged:** AR3-F8, AR3-F5
- **Result:** V-013
- **Reason:** Both findings describe the same pattern of bypassing DI with module-level repository instances.

### Merge Group 3: Manual Role Checks
- **Findings Merged:** AR3-F6, AR2-deviation-2
- **Result:** V-014
- **Reason:** Both describe the same pattern of manual role checks instead of using `require_admin_role`.

### Merge Group 4: Missing Pagination
- **Findings Merged:** AR2-F4, AR2-F5
- **Result:** V-015
- **Reason:** Both admin endpoints have the same missing pagination issue.

### Merge Group 5: Extension Mismatch
- **Findings Merged:** AR1-EXT-1, AR3-DB-related
- **Result:** V-011
- **Reason:** The extension mismatch is a single root cause identified across reports.

### Merge Group 6: Dashboard Join Permission (from Doc 2)
- **Findings Merged:** AR2-F5 (Data Layer), AR2-V009
- **Result:** V-026
- **Reason:** Both describe the same N+1 query issue in `get_by_user()`.

---

## DEPENDENCY VALIDATION RESULTS

### Dependency Graph Correctness
- **Status:** VALID
- **Findings:** The overall dependency flow `API → Service → Repository → DB` is correctly maintained. The interface-based DI pattern is properly implemented in most modules.

### Anomalies Detected
1. **Module-level singletons** (V-013): `dashboards.py` and `graphs.py` bypass DI with module-level `GraphRepository()` instances.
2. **Direct repository instantiation in admin.py:142**: `RegistrationRequestRepository()` created directly in endpoint instead of via DI.
3. **Direct repository instantiation in processing_logs.py:106-108**: `ProcessingLogRepository()` created directly in endpoint instead of via DI.

### Circular Dependencies
- **Status:** NONE DETECTED
- **Findings:** No circular import chains found. The layering is clean: `api → services → repositories → db/models`.

---

## ROLLOUT SAFETY ANALYSIS

### Safe to Execute (No Dependencies)
| Finding | Risk | Effort |
|---------|------|--------|
| V-002 (file.size null check) | Minimal | Trivial |
| V-003 (grant access role) | Minimal | Trivial |
| V-012 (duplicate update) | Minimal | Trivial |
| V-009 (CORS methods) | Low | Low |
| V-023 (no-op migrations) | Low | Low |

### Safe to Execute (Internal Dependencies Only)
| Finding | Risk | Effort |
|---------|------|--------|
| V-001 (data access check) | Low | Low |
| V-005 (deduplicate error handling) | Low | Low |
| V-006 (rate limiter caching) | Low | Low |
| V-010 (email blocklist) | Low | Low |
| V-013 (DI for repositories) | Medium | Medium |
| V-014 (admin role checks) | Low | Low |
| V-015 (pagination) | Low | Low |
| V-016 (narrow exceptions) | Low | Low |
| V-026 (dashboard join permission) | Low | Medium |

### Requires Planning (Architectural Impact)
| Finding | Risk | Effort |
|---------|------|--------|
| V-004 (dimension partitioning) | Medium | Medium |
| V-007 (task queue persistence) | High | High |
| V-008 (default secrets) | Medium | Low |
| V-011 (extension standardization) | Medium | Medium |
| V-017 (streaming uploads) | Medium | Medium |

---

## SEMANTIC TARGETING STABILITY

### Stable Anchors (Safe for Task Generation)
- Route decorators (`@router.get`, `@router.post`, etc.) — stable across changes
- Function definitions — stable symbol names
- Class definitions — stable symbol names
- Import statements — stable module references

### Unstable Anchors (Avoid for Task Generation)
- Line numbers — will shift with any code changes
- `df.columns[:3]` pattern — fragile, depends on DataFrame structure
- Inline dict literals — may change structure

### Recommended Anchors for Each Validated Finding
| Finding | Recommended Anchor |
|---------|-------------------|
| V-001 | `get_aggregated_data_endpoint` function in `data.py` |
| V-002 | `upload_file_endpoint` function in `upload.py` |
| V-003 | `grant_dashboard_access_endpoint` in `dashboards.py` |
| V-004 | `_store_aggregates` function in `data_worker.py` |
| V-005 | `upload_file_endpoint` function in `upload.py` |
| V-006 | `_handle_login` function in `auth.py` |
| V-007 | `TaskQueue` class in `task_queue.py` |
| V-008 | `docker-compose.yml` service `app` environment |
| V-009 | `create_app` function in `app.py` |
| V-010 | `register_request` function in `auth.py` |
| V-013 | Module-level `_graph_repo` assignments |
| V-014 | `create_layout_endpoint` in `layouts.py` |
| V-015 | `get_users_admin_endpoint` in `admin.py` |
| V-026 | `DashboardRepository.get_by_user` in `dashboard_repo.py` |

---

## EXECUTION APPLICABILITY ANALYSIS

### Pre-Execution Checks Required
1. **V-001**: Verify `check_dashboard_access` function signature and DI availability
2. **V-004**: Verify Graph model has `dimensions` field accessible in worker context
3. **V-007**: Requires Redis/RQ dependency evaluation and infrastructure changes
4. **V-011**: Verify current extension installed in all environments
5. **V-013**: Verify `get_graph_repository` dependency function exists and works

### Potential Execution Conflicts
- **V-001 and V-003**: Both modify `dashboards.py`/`data.py` — can be executed in parallel (different files)
- **V-013 and V-014**: Both modify route files — execute sequentially to avoid merge conflicts
- **V-004 and V-017**: Both affect data processing — coordinate testing

---

## ARCHITECTURAL CONSISTENCY WARNINGS

1. **DI Pattern Inconsistency**: Three files (`dashboards.py`, `graphs.py`, `admin.py`, `processing_logs.py`) instantiate repositories directly instead of using DI. This is the most widespread architectural deviation.

2. **Authorization Pattern Inconsistency**: The `layouts.py` manual role checks and `dashboards.py` wrong role dependency both violate the centralized authorization pattern established by `api/deps.py`.

3. **Error Handling Inconsistency**: The upload endpoint's duplicate error handling (V-005) creates maintenance risk. Other endpoints have clean single-path error handling.

4. **MVP vs Production Gap**: The in-memory task queue (V-007) and default secrets (V-008) indicate the system is architecturally an MVP despite having production-grade infrastructure (Redis, Docker secrets) available.

5. **Partial API Rate Limiting**: Rate limiting is implemented for login (`auth.py:43`), upload (`upload.py:83`), and registration requests (`auth.py:318`) only. Other sensitive endpoints (admin operations, data access, dashboard management) lack rate limiting. In production, all mutative endpoints should have rate limiting.

---

## Cross-Reference with audit_validated_findings_2.md

The following findings from the earlier validation document (audit_validated_findings_2.md, 2026-05-13) have been reconciled:

| Doc 2 ID | Title | Resolution |
|----------|-------|------------|
| V-001 | Extension Mismatch | Severity upgraded to HIGH (was MEDIUM) — deployment-blocking |
| V-002 | No-op Migrations | Kept as INFO — no-op, no runtime impact |
| V-007 | Broad Exception | Severity upgraded to MEDIUM (was LOW) — service layer impact |
| V-009 | Dashboard Join Missing | **Added as V-026** — was completely absent from initial document |
| V-011 | Frontend Token Cleanup | **Rejected** (R-006) — functionally correct, harmless |
| ACW-1 | No health check endpoint | **Rejected** — factually incorrect, `/health` exists at `app.py:152` |
| ACW-2 | Partial rate limiting | **Added as ACW-5** — valid observation |

---

*End of validated findings document. Total: 29 validated (4 HIGH, 11 MEDIUM, 11 LOW, 3 INFO), 6 rejected, 6 merged groups.*
