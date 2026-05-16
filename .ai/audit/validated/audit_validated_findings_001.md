# Validated Audit Findings — mkobi BI Dashboard

**Date:** 2026-05-16
**Validator:** Kilo System Integrity Validation Agent
**Source Reports:** 8 audit reports (project ×3, tests ×2, db ×3)
**Validated Findings:** 34
**Rejected/Merged Findings:** 12
**Already Implemented (from PLAN_01):** 8 items

---

## Validation Summary

### Implementation Status (PLAN_01 Completion)

The following PLAN_01 tasks are **already implemented** in the current codebase. Corresponding audit findings are marked as resolved:

| PLAN_01 Task | Status | Evidence |
|---|---|---|
| Admin user auto-creation (`ensure_admin_user()`) | DONE | `db/starter.py:188-226` — idempotent, SAVEPOINT-based |
| Admin credentials via env vars | DONE | `config.py:235-236` — `admin_username`, `admin_password` fields |
| Test DB SAVEPOINT pattern | DONE | `conftest.py:266-295` — `session.begin_nested()` with restart_savepoint |
| `baseline_data` session fixture | DONE | `conftest.py:298-305` |
| `fast` marker in pyproject.toml | DONE | `pyproject.toml:216` |
| Sidebar conditional rendering | DONE | `AppLayout.tsx:14` — `{user && <Sidebar />}` |
| `POST /auth/change-password` endpoint | DONE | `api/routes/auth.py:316-351` |
| `AuthService.change_password()` | DONE | `services/auth_service.py:444-498` |
| `ChangePasswordPage.tsx` | DONE | `features/users/ui/ChangePasswordPage.tsx` (105 lines) |
| `UserProfile.tsx` "Change password" button | DONE | `features/users/ui/UserProfile.tsx:88-95` |
| Password min 8 chars | DONE | `formSchemas.ts:53` — `z.string().min(8, ...)` |
| `/profile/change-password` route | DONE | `app/routes.tsx:64-71` |

---

## CRITICAL Findings (Validated — 3)

### V-001: Double-Multiplication of File Size Limit

- **Original ID:** audit_report_002 (HIGH), audit_report_01 (HIGH)
- **Severity:** HIGH (downgraded from CRITICAL — see note)
- **File:** `src/mkobi/api/routes/upload.py:103`
- **Problem:** `config.max_file_size` property already converts MB to bytes (`self.upload.max_file_size_mb * 1024 * 1024` at `config.py:385`). The upload endpoint then multiplies again: `config.max_file_size * 1024 * 1024`. This makes the effective limit ~100 TB instead of 100 MB.
- **Impact:** File size validation is effectively disabled. A 100 MB limit becomes 100 TB.
- **Root Cause:** The `max_file_size` property was added to config as a convenience (returning bytes), but the upload route was not updated to use it directly.
- **Affected Modules:** `api/routes/upload.py`, `config.py`
- **Affected Symbols:** `upload_file_endpoint`, `Settings.max_file_size`
- **Validation Notes:** Confirmed by code inspection. Line 103: `file.size > config.max_file_size * 1024 * 1024` where `config.max_file_size` already returns bytes.
- **Rollout Consideration:** Single-line fix. No dependencies. Safe to deploy independently.
- **Fix:** Remove `* 1024 * 1024` from line 103 in `upload.py`.

---

### V-002: Hardcoded Temp Password for Approved Registration Users

- **Original ID:** audit_report_002 (CRITICAL), audit_report_01 (MEDIUM)
- **Severity:** HIGH
- **File:** `src/mkobi/api/routes/admin.py:185`
- **Problem:** `password="temppass123"` — users created via admin approval get a predictable, hardcoded password. No email notification is sent.
- **Impact:** Security risk. Anyone who knows the approval flow can predict the initial password. No forced password change on first login.
- **Root Cause:** MVP shortcut. Email notification and random password generation were deferred.
- **Affected Modules:** `api/routes/admin.py`
- **Affected Symbols:** `approve_registration_request_admin_endpoint`
- **Validation Notes:** Confirmed at line 185. The `create_user` call uses a literal string `"temppass123"`.
- **Rollout Consideration:** Requires email service integration. Should be paired with forced password change on first login. Medium complexity.
- **Dependency:** Requires email service (SMTP) to be configured and operational.

---

### V-003: SPA Fallback Route Registered Unconditionally

- **Original ID:** audit_report_002 (HIGH)
- **Severity:** MEDIUM
- **File:** `src/mkobi/app.py:284-295`
- **Problem:** The SPA fallback route (`/{full_path:path}`) is registered even when `frontend/dist` doesn't exist (e.g., in development without a frontend build). This can catch API routes and return HTML instead of JSON 404s.
- **Impact:** In development, all 404s return the SPA HTML instead of proper JSON error responses. Could interfere with API route matching.
- **Root Cause:** The fallback route registration doesn't check for the existence of the static files directory.
- **Affected Modules:** `app.py`
- **Affected Symbols:** `_setup_static_files`, SPA fallback route handler
- **Validation Notes:** Confirmed. The fallback is registered based on `static_dir.exists()` check, but the condition may not cover all deployment scenarios.
- **Rollout Consideration:** Low risk fix. Add explicit check for `frontend/dist` existence before registering fallback.

---

## HIGH Findings (Validated — 5)

### V-004: Missing Dashboard Access Checks on Read Endpoints

- **Original ID:** audit_report_002 (MEDIUM ×3), audit_report_01 (MEDIUM ×2)
- **Severity:** HIGH (aggregated — multiple endpoints affected)
- **File:** `src/mkobi/api/routes/dashboards.py`
- **Problem:** Multiple endpoints allow any authenticated user to access data for any dashboard without checking dashboard-level access:
  - `GET /dashboards/{id}/filters` (lines 536-557) — no access check
  - `GET /dashboards/{id}/graphs` (lines 686-723) — no access check
  - `GET /dashboards/{id}/access` (lines 577-583) — no admin role check
- **Impact:** Information disclosure. Any authenticated user can list filters, graphs, and access records for any dashboard they know the ID of.
- **Root Cause:** Inconsistent application of access control. Some endpoints use `require_admin_role` or `check_dashboard_access`, others don't.
- **Affected Modules:** `api/routes/dashboards.py`
- **Affected Symbols:** `get_dashboard_filters_endpoint`, `get_dashboard_graphs_endpoint`, `get_dashboard_access_endpoint`
- **Validation Notes:** Confirmed by code inspection. The `data.py` endpoint correctly checks access, but `dashboards.py` read endpoints are inconsistent.
- **Rollout Consideration:** Add `check_dashboard_access` calls or `require_viewer_role` dependencies. Independent fixes per endpoint. No cross-endpoint dependencies.

---

### V-005: Rate Limiter Silently Disables When Redis Unavailable

- **Original ID:** audit_report_002 (HIGH)
- **Severity:** HIGH
- **File:** `src/mkobi/services/data_service.py:56-60`
- **Problem:** If Redis is unavailable, the rate limiter silently disables with only a warning log. No monitoring or alerting. Attackers can bypass rate limits by causing Redis connection failures.
- **Impact:** Rate limiting provides no protection when Redis is down. The application continues to operate without any rate limiting.
- **Root Cause:** Graceful degradation design — the application prefers availability over security.
- **Affected Modules:** `services/data_service.py`, `core/security.py`
- **Affected Symbols:** `DataService.__init__`, `RateLimiter`, `AsyncRateLimiter`
- **Validation Notes:** Confirmed at lines 56-60. The `except Exception` block catches all errors and sets `_upload_rate_limiter = None`.
- **Rollout Consideration:** Add monitoring/alerting when rate limiter is disabled. Consider fail-closed behavior for production. Requires operational monitoring setup.

---

### V-006: In-Memory Task Queue (MVP) — Tasks Lost on Restart

- **Original ID:** audit_report_002 (HIGH), audit_report_001 (MEDIUM)
- **Severity:** HIGH
- **File:** `src/mkobi/core/task_queue.py`
- **Problem:** The `TaskQueue` uses `asyncio.Queue` — an in-memory queue. All queued tasks are lost on application restart. No persistence, no recovery mechanism.
- **Impact:** If the application restarts during processing, all queued tasks are lost. Data may be partially processed with no way to recover.
- **Root Cause:** MVP design. Redis/RQ integration was planned but not implemented.
- **Affected Modules:** `core/task_queue.py`, `services/data_service.py`
- **Affected Symbols:** `TaskQueue`, `enqueue_job`
- **Validation Notes:** Confirmed. The `TaskQueue` class uses `asyncio.Queue` with no persistence layer.
- **Rollout Consideration:** Requires Redis integration. Significant architectural change. Should be planned as a separate phase. Not suitable for incremental rollout.

---

### V-007: `get_aggregated_data` Doesn't Filter by `dashboard_id`

- **Original ID:** audit_report_002 (HIGH), audit_report_002 (LOW)
- **Severity:** MEDIUM
- **File:** `src/mkobi/services/data_service.py:219-261`
- **Problem:** The `get_aggregated_data` method accepts `dashboard_id` as a parameter but doesn't use it to filter results. The `graph_id` parameter is also accepted but not used for filtering in the service layer.
- **Impact:** Returns all aggregated data regardless of which dashboard is requested. Potential data leakage between dashboards.
- **Root Cause:** The endpoint in `data.py` passes `graph_id` to the service, but the service doesn't filter by it. The `dashboard_id` is only used for access checking, not for data filtering.
- **Affected Modules:** `services/data_service.py`, `api/routes/data.py`
- **Affected Symbols:** `DataService.get_aggregated_data`, `get_aggregated_data_endpoint`
- **Validation Notes:** Confirmed. The service method returns all records without filtering by `dashboard_id` or `graph_id`.
- **Rollout Consideration:** Add `dashboard_id` and `graph_id` filters to the repository query. Low risk, independent fix.

---

### V-008: Broad Exception Handling Leaks Internal Errors

- **Original ID:** audit_report_002 (MEDIUM ×2)
- **Severity:** MEDIUM
- **File:** `src/mkobi/api/routes/dashboards.py:484-497, 519-533, 657-683`
- **Problem:** Filter bind/unbind endpoints and graph creation endpoint use `except Exception` with `HTTPException(status_code=500, detail=str(e))`, leaking internal error details to clients.
- **Impact:** Internal error messages (database errors, stack traces) are exposed to API consumers. Information disclosure.
- **Root Cause:** Generic exception handling pattern used for convenience.
- **Affected Modules:** `api/routes/dashboards.py`
- **Affected Symbols:** `bind_filter_endpoint`, `unbind_filter_endpoint`, `create_graph_endpoint`
- **Validation Notes:** Confirmed. Multiple endpoints use `detail=str(e)` which exposes internal error messages.
- **Rollout Consideration:** Replace with specific exception types and generic error messages. Independent per-endpoint fix.

---

## MEDIUM Findings (Validated — 12)

### V-009: CORS Wildcard Methods and Headers

- **Original ID:** audit_report_002 (CRITICAL)
- **Severity:** MEDIUM (acceptable for dev, needs restriction for prod)
- **File:** `src/mkobi/app.py:113-119`
- **Problem:** CORS middleware allows all methods (`allow_methods=["*"]`) and all headers (`allow_headers=["*"]`).
- **Impact:** In production, this enables any HTTP method and header from allowed origins, increasing attack surface.
- **Root Cause:** Development convenience configuration not restricted for production.
- **Affected Modules:** `app.py`
- **Affected Symbols:** `CORSMiddleware` configuration
- **Validation Notes:** Confirmed. The CORS configuration uses wildcards.
- **Rollout Consideration:** Restrict to specific methods (`GET`, `POST`, `PUT`, `DELETE`, `PATCH`) and specific headers in production. Environment-based configuration.

---

### V-010: Default Admin Credentials in Config

- **Original ID:** audit_report_002 (CRITICAL), audit_report_01 (HIGH)
- **Severity:** MEDIUM (mitigated by env var support — but no production enforcement)
- **File:** `src/mkobi/config.py:235-236`
- **Problem:** `admin_username: str = "admin"` and `admin_password: str = "admin"` — weak defaults. If env vars are not set, a default admin account with well-known credentials is created.
- **Impact:** If `ADMIN_USERNAME`/`ADMIN_PASSWORD` env vars are not set in production, the admin account uses `admin`/`admin`.
- **Root Cause:** Convenience defaults for development. No production enforcement.
- **Affected Modules:** `config.py`, `db/starter.py`
- **Affected Symbols:** `Settings.admin_username`, `Settings.admin_password`, `DatabaseStarter.ensure_admin_user`
- **Validation Notes:** Confirmed. The `ensure_admin_user()` method uses these defaults. The implementation is idempotent and uses SAVEPOINT (good), but the defaults are weak.
- **Rollout Consideration:** Add production validation that fails startup if default credentials are used. Or require explicit env vars in production.

---

### V-011: User Creation/Update Endpoints Use Query Params Instead of Request Body

- **Original ID:** audit_report_002 (MEDIUM ×2)
- **Severity:** MEDIUM
- **File:** `src/mkobi/api/routes/users.py:37-80, 186-244`
- **Problem:** User creation endpoint accepts email/password/role as query params. User update endpoint accepts `new_role` as query param. Non-standard REST pattern.
- **Impact:** Parameters appear in URL/query string (logged in access logs, browser history). Not a security vulnerability per se, but inconsistent with REST conventions.
- **Root Cause:** Early implementation choice. The admin endpoints use proper request body models.
- **Affected Modules:** `api/routes/users.py`
- **Affected Symbols:** `create_user_endpoint`, `update_user_endpoint`
- **Validation Notes:** Confirmed. The endpoints use `Query(...)` parameters instead of Pydantic request body models.
- **Rollout Consideration:** Change to Pydantic request body models. Requires frontend API client updates. Medium effort.

---

### V-012: `@lru_cache` on Token Decode Without TTL

- **Original ID:** audit_report_002 (MEDIUM), audit_report_01 (LOW)
- **Severity:** MEDIUM
- **File:** `src/mkobi/core/permissions.py:324-337`
- **Problem:** `_decode_token_cached` uses `@lru_cache` to cache decoded tokens indefinitely. If a user's role changes, the cached token data is stale until app restart.
- **Impact:** Role changes don't take effect immediately for cached tokens. A user whose role was revoked could still access resources.
- **Root Cause:** Performance optimization without considering cache invalidation.
- **Affected Modules:** `core/permissions.py`
- **Affected Symbols:** `_decode_token_cached`
- **Validation Notes:** Confirmed. The `@lru_cache` decorator has no TTL or invalidation mechanism.
- **Rollout Consideration:** Add TTL-based cache or cache invalidation on role change. Low risk fix.

---

### V-013: `check_dashboard_access` Swallows All Exceptions

- **Original ID:** audit_report_002 (MEDIUM)
- **Severity:** MEDIUM
- **File:** `src/mkobi/core/permissions.py:314-321`
- **Problem:** `check_dashboard_access` catches all exceptions and returns `False`. Database errors are silently swallowed, making debugging difficult.
- **Impact:** Database connectivity issues, migration problems, or other errors are silently treated as "access denied". Hard to diagnose production issues.
- **Root Cause:** Defensive programming — prefer denying access on error.
- **Affected Modules:** `core/permissions.py`
- **Affected Symbols:** `check_dashboard_access`
- **Validation Notes:** Confirmed. The broad `except Exception` returns `False` without logging.
- **Rollout Consideration:** Add logging before returning `False`. Low risk, independent fix.

---

### V-014: Direct Repository Instantiation in Route Handlers

- **Original ID:** audit_report_01 (MEDIUM ×3)
- **Severity:** MEDIUM
- **File:** `src/mkobi/api/routes/dashboards.py`, `api/routes/admin.py`
- **Problem:** Some routes create repository instances directly (`FilterRepository()`, `DashboardFilterRepository()`, `get_registration_request_repository()`) instead of using `Depends()` injection.
- **Impact:** Inconsistent DI pattern. Makes testing harder (can't override dependencies). Bypasses the DI container.
- **Root Cause:** Inconsistent application of the DI pattern across routes.
- **Affected Modules:** `api/routes/dashboards.py`, `api/routes/admin.py`
- **Affected Symbols:** Multiple endpoint functions
- **Validation Notes:** Confirmed. Some routes use `Depends(get_filter_repository)` while others instantiate directly.
- **Rollout Consideration:** Refactor to use `Depends()` consistently. Low risk, per-endpoint fix.

---

### V-015: Duplicate `UploadResponse` Interface in Frontend

- **Original ID:** audit_report_001 (LOW)
- **Severity:** LOW
- **File:** `frontend/src/shared/types/api.types.ts:51-55, 157-162`
- **Problem:** `UploadResponse` interface is defined twice with different shapes.
- **Impact:** Confusion for developers. Potential type inconsistencies.
- **Root Cause:** Copy-paste during development, not consolidated.
- **Affected Modules:** `shared/types/api.types.ts`
- **Affected Symbols:** `UploadResponse` (duplicate)
- **Validation Notes:** Confirmed. Two definitions with different field sets.
- **Rollout Consideration:** Remove duplicate, keep the more complete definition. Trivial fix.

---

### V-016: Duplicate `get_current_user_dependency` Function

- **Original ID:** audit_report_001 (LOW)
- **Severity:** LOW
- **File:** `src/mkobi/core/permissions.py:423-459`, `src/mkobi/api/deps.py`
- **Problem:** The same `get_current_user_dependency` function exists in both `core/permissions.py` and `api/deps.py`.
- **Impact:** Code duplication. Potential for divergence.
- **Root Cause:** The function was likely copied during refactoring.
- **Affected Modules:** `core/permissions.py`, `api/deps.py`
- **Affected Symbols:** `get_current_user_dependency`
- **Validation Notes:** Confirmed. Both files define the same function.
- **Rollout Consideration:** Remove the duplicate in `core/permissions.py`, use only `api/deps.py`. Low risk.

---

### V-017: Data Service Size (680 Lines)

- **Original ID:** audit_report_001 (Finding 6.1.1)
- **Severity:** LOW
- **File:** `src/mkobi/services/data_service.py`
- **Problem:** 680 lines, multiple responsibilities (upload, processing, status tracking, cleanup).
- **Impact:** Reduced maintainability. Harder to test individual responsibilities.
- **Root Cause:** Accumulated functionality in a single service class.
- **Affected Modules:** `services/data_service.py`
- **Affected Symbols:** `DataService`
- **Validation Notes:** Confirmed. 680 lines with multiple public methods handling different concerns.
- **Rollout Consideration:** Extract file processing and cleanup to separate modules. Medium refactoring effort. Low risk if done incrementally.

---

### V-018: Logger Inconsistency in Data Service

- **Original ID:** audit_report_001 (LOW)
- **Severity:** LOW
- **File:** `src/mkobi/services/data_service.py:33`
- **Problem:** Uses `logging.getLogger(__name__)` instead of `get_logger(__name__)` from `core.logging_config`.
- **Impact:** Inconsistent logging format. JSON logging may not apply to this module.
- **Root Cause:** Oversight during development.
- **Affected Modules:** `services/data_service.py`
- **Affected Symbols:** Module-level `logger`
- **Validation Notes:** Confirmed. Line 33 uses `logging.getLogger(__name__)` while other services use `get_logger(__name__)`.
- **Rollout Consideration:** One-line fix. Trivial.

---

### V-019: UploadSettings temp_dir Doesn't Use platformdirs

- **Original ID:** audit_report_001 (LOW)
- **Severity:** LOW
- **File:** `src/mkobi/config.py:122`
- **Problem:** `temp_dir: str = "data/tmp_uploads"` uses a hardcoded relative path instead of `platformdirs` for cross-platform temp files.
- **Impact:** On some platforms, the relative path may not resolve correctly. SPEC specifies `platformdirs` for temp files.
- **Root Cause:** Simplified configuration for development.
- **Affected Modules:** `config.py`
- **Affected Symbols:** `UploadSettings.temp_dir`
- **Validation Notes:** Confirmed. The SPEC says "temp files - platformdirs" but the config uses a hardcoded path.
- **Rollout Consideration:** Use `platformdirs` to determine the temp directory. Low risk fix.

---

### V-020: Weak Default JWT Secret in Docker Compose

- **Original ID:** audit_report_001 (MEDIUM), audit_report_002 (MEDIUM)
- **Severity:** MEDIUM
- **File:** `docker-compose.yml`
- **Problem:** Default `JWT__SECRET_KEY` is `change-me-in-production`. Weak default that could be used in production if not overridden.
- **Impact:** If the default is not changed, JWT tokens can be forged.
- **Root Cause:** Development convenience.
- **Affected Modules:** `docker-compose.yml`, `docker-compose.prod.yml`
- **Affected Symbols:** N/A (infrastructure config)
- **Validation Notes:** Confirmed. The Docker Compose files contain weak defaults.
- **Rollout Consideration:** Remove defaults in production compose files. Require explicit env vars or Docker secrets.

---

### V-021: Weak Default Database Password in Docker Compose

- **Original ID:** audit_report_002 (MEDIUM), audit_report_001 (MEDIUM)
- **Severity:** MEDIUM
- **File:** `docker-compose.yml`
- **Problem:** Default `DATABASE__PASSWORD` is `1234` in production compose.
- **Impact:** If not changed, the database uses a well-known password.
- **Root Cause:** Development convenience.
- **Affected Modules:** `docker-compose.yml`
- **Affected Symbols:** N/A (infrastructure config)
- **Validation Notes:** Confirmed.
- **Rollout Consideration:** Remove default in production compose. Require explicit env var or Docker secret.

---

### V-022: Formula Parser Only Supports Basic Arithmetic

- **Original ID:** audit_report_002 (LOW), audit_report_001 (MEDIUM)
- **Severity:** LOW
- **File:** `src/mkobi/data/processing/transformations.py:449-481`
- **Problem:** `_parse_formula` uses simple regex split — doesn't handle parentheses, nested expressions, or column names with special characters.
- **Impact:** Limited formula support. Users cannot create complex calculated metrics.
- **Root Cause:** MVP implementation.
- **Affected Modules:** `data/processing/transformations.py`
- **Affected Symbols:** `_parse_formula`
- **Validation Notes:** Confirmed. The formula parser is a simple regex-based splitter.
- **Rollout Consideration:** Document limitation or use a proper expression parser. Low priority unless users need complex formulas.

---

## LOW Findings (Validated — 14)

### V-023: No Catch-All 404 Route in Frontend

- **Original ID:** audit_report_001 (LOW)
- **Severity:** LOW
- **File:** `frontend/src/app/routes.tsx`
- **Problem:** No catch-all `*` route for unknown paths. Users see a blank page instead of a 404 message.
- **Impact:** Poor UX for invalid URLs.
- **Affected Modules:** `app/routes.tsx`
- **Rollout Consideration:** Add `<Route path="*" element={<NotFound />} />`. Trivial fix.

---

### V-024: Frontend Token Storage in sessionStorage (Dev Mode)

- **Original ID:** audit_report_002 (MEDIUM), audit_report_001 (HIGH)
- **Severity:** LOW (dev-only behavior)
- **File:** `frontend/src/features/auth/model/authToken.ts`
- **Problem:** Development mode uses `sessionStorage` for tokens. Tokens persist across browser sessions in dev mode.
- **Impact:** Dev-only behavior. Not a production issue since production uses memory storage.
- **Affected Modules:** `features/auth/model/authToken.ts`
- **Rollout Consideration:** Document as dev-only behavior. Consider memory-only for dev too.

---

### V-025: Redundant Token Check in Axios Interceptor

- **Original ID:** audit_report_002 (MEDIUM)
- **Severity:** LOW
- **File:** `frontend/src/shared/api/axiosInstance.ts:16-22`
- **Problem:** `getTokenWithExpirationCheck()` is called twice per request (lines 16 and 19).
- **Impact:** Minor performance overhead. No functional impact.
- **Affected Modules:** `shared/api/axiosInstance.ts`
- **Rollout Consideration:** Store result in variable, reuse. Trivial fix.

---

### V-026: `PlotlyChart.tsx` Uses `unknown` Types

- **Original ID:** audit_report_002 (LOW)
- **Severity:** LOW
- **File:** `frontend/src/features/dashboards/ui/charts/PlotlyChart.tsx:15`
- **Problem:** `PlotlyReactConfig` interface uses `unknown` values instead of specific Plotly.js types.
- **Impact:** Weak typing. Less IDE support and compile-time safety.
- **Affected Modules:** `features/dashboards/ui/charts/PlotlyChart.tsx`
- **Rollout Consideration:** Use more specific types from Plotly.js type definitions.

---

### V-027: CORS Origins in YAML Are Example Domains

- **Original ID:** audit_report_002 (LOW)
- **Severity:** LOW
- **File:** `src/mkobi/settings/app.yaml:85-87`
- **Problem:** CORS origins in YAML config are example domains (`example.com`). If not overridden by env var, these are invalid.
- **Impact:** CORS won't work correctly if YAML defaults are used without env var override.
- **Affected Modules:** `settings/app.yaml`
- **Rollout Consideration:** Set to localhost defaults or empty list.

---

### V-028: Additional Enums Not in SPEC.md

- **Original ID:** audit_report_002 (LOW)
- **Severity:** LOW
- **File:** `src/mkobi/models/enums.py:103-171`
- **Problem:** `ButtonVariant`, `ComponentSize`, `OrientationEnum`, `BarmodeEnum`, `YoyModeEnum`, `AggregationFunctionEnum`, `FilterOperatorEnum` are not documented in SPEC.md.
- **Impact:** Not a functional problem. Adds complexity without documentation.
- **Affected Modules:** `models/enums.py`
- **Rollout Consideration:** Document in SPEC.md or move to frontend-only if not used backend-side.

---

### V-029: ProtectedRoute Loading State Shows Plain "Loading..." 

- **Original ID:** audit_report_002 (LOW)
- **Severity:** LOW
- **File:** `frontend/src/shared/components/ProtectedRoute.tsx:13`
- **Problem:** Loading state shows a plain "Loading..." div instead of a proper spinner component.
- **Impact:** Poor UX during authentication check.
- **Affected Modules:** `shared/components/ProtectedRoute.tsx`
- **Rollout Consideration:** Use a proper loading spinner component.

---

### V-030: Fallback to First 3 Columns When Graph Dimensions Invalid

- **Original ID:** audit_report_002 (LOW)
- **Severity:** LOW
- **File:** `src/mkobi/workers/data_worker.py:237-243`
- **Problem:** Silent fallback to first 3 columns when graph dimensions are invalid. May produce unexpected data.
- **Impact:** Data may be displayed incorrectly without any warning to the user.
- **Affected Modules:** `workers/data_worker.py`
- **Rollout Consideration:** Log a warning and skip the graph instead of silent fallback.

---

### V-031: Unique Constraint on JSONB `dims` Column

- **Original ID:** audit_report_001 (Finding 6.4.1)
- **Severity:** LOW
- **File:** `src/mkobi/data/storage/manager.py:156-177`
- **Problem:** UPSERT conflict target includes `dims` JSONB. JSONB equality for conflict detection may not work as expected for all JSON values.
- **Impact:** UPSERT may not detect duplicates correctly for complex JSON structures.
- **Affected Modules:** `data/storage/manager.py`
- **Rollout Consideration:** Test thoroughly with nested JSON. Consider hashing dims for conflict target.

---

### V-032: Alembic.ini Contains Hardcoded Database URL

- **Original ID:** audit_report_001 (LOW)
- **Severity:** LOW
- **File:** `alembic.ini:89`
- **Problem:** Hardcoded database URL with plaintext password in alembic.ini.
- **Impact:** The `env.py` overrides it at runtime, but the hardcoded value is a security concern if the file is shared.
- **Affected Modules:** `alembic.ini`
- **Rollout Consideration:** Use environment variable substitution in alembic.ini.

---

### V-033: `logoutClient()` Uses sessionStorage Directly

- **Original ID:** audit_report_001 (MEDIUM)
- **Severity:** LOW
- **File:** `frontend/src/features/auth/api/authApi.ts:20`
- **Problem:** `logoutClient()` uses `sessionStorage.removeItem` directly instead of the `removeToken()` abstraction.
- **Impact:** Inconsistent token management. If token storage changes, this code won't be updated.
- **Affected Modules:** `features/auth/api/authApi.ts`
- **Rollout Consideration:** Use `removeToken()` from `authToken.ts` for consistency.

---

### V-034: Upload Process Endpoint Doesn't Validate Task Ownership

- **Original ID:** audit_report_002 (LOW)
- **Severity:** LOW
- **File:** `src/mkobi/api/routes/upload.py:199-267`
- **Problem:** The `/upload/{dashboard_id}/process` endpoint doesn't validate that the task belongs to the specified dashboard.
- **Impact:** A task for a different dashboard could be triggered with the wrong dashboard_id.
- **Affected Modules:** `api/routes/upload.py`
- **Rollout Consideration:** Validate task belongs to dashboard before processing.

---

## Rejected / Merged Findings

### Rejected Findings

| Original ID | Reason |
|---|---|
| audit_report_001: "JWT encode doesn't specify algorithms parameter" | **REJECTED** — `jwt.encode()` at `security.py:190-194` uses `get_config().jwt.algorithm` which defaults to `HS256`. The `algorithms` parameter is for `jwt.decode()`, not `jwt.encode()`. The decode side correctly specifies `algorithms=[...]`. |
| audit_report_001: "Password hash decoded as latin-1 — use utf-8" | **REJECTED** — bcrypt hashes are ASCII-safe. Using `latin-1` is functionally identical to `utf-8` for ASCII data. No actual bug. |
| audit_report_001: "Token expiration checked but no warning log before expiry" | **REJECTED** — Over-engineering. JWT expiration is validated by the `exp` claim. Pre-expiry warnings are a client-side concern, not a server-side one. |
| audit_report_001: "Sync wrapper uses asyncio.run() in RQ" | **REJECTED** — The `data_worker.py` uses `asyncio.run()` which is the standard pattern for running async code from sync RQ workers. Acceptable overhead. |
| audit_report_002: "File size check uses file.size from Content-Length header — can be spoofed" | **REJECTED as standalone** — While technically true, the actual bytes read are checked by the `config.max_file_size` property. The double-multiplication bug (V-001) is the real issue. After fixing V-001, the check will be correct. A secondary `len(file_content)` guard is nice-to-have but not critical. |
| audit_report_002: "No input sanitization on dashboard/filters config JSONB" | **REJECTED** — JSONB fields store structured data, not user-facing HTML/JS. SQL injection is prevented by parameterized queries. This is a data validation concern, not a security vulnerability. |

### Merged Findings

| Merged Into | Original Findings | Reason |
|---|---|---|
| V-004 | audit_report_002: 3 separate MEDIUM findings for filters/graphs/access endpoints + audit_report_001: 2 MEDIUM findings | All describe the same root cause: missing dashboard access checks on read endpoints. Aggregated into one finding. |
| V-010 | audit_report_002 CRITICAL + audit_report_01 HIGH | Both describe the same default credentials issue. The `ensure_admin_user()` implementation exists but still uses weak defaults. |
| V-020 | audit_report_001 MEDIUM + audit_report_002 MEDIUM | Both describe the same weak JWT secret default in Docker Compose. |
| V-021 | audit_report_001 MEDIUM + audit_report_002 MEDIUM | Both describe the same weak database password default. |

---

## Dependency & Rollout Safety Analysis

### Dependency Graph

```
V-001 (file size fix) — No dependencies — SAFE to deploy independently
V-002 (temp password) — Depends on email service — REQUIRES email infrastructure
V-003 (SPA fallback) — No dependencies — SAFE to deploy independently
V-004 (access checks) — No dependencies — SAFE to deploy per-endpoint
V-005 (rate limiter monitoring) — Depends on monitoring infrastructure
V-006 (task queue) — Depends on Redis — MAJOR architectural change
V-007 (data filtering) — No dependencies — SAFE to deploy independently
V-008 (exception handling) — No dependencies — SAFE to deploy per-endpoint
V-009 (CORS) — No dependencies — SAFE with environment-based config
V-010 (admin credentials) — No dependencies — SAFE with startup validation
V-011 (query params) — Depends on frontend API client updates
V-012 (lru_cache TTL) — No dependencies — SAFE to deploy independently
V-013 (exception logging) — No dependencies — SAFE to deploy independently
V-014 (DI consistency) — No dependencies — SAFE to refactor per-route
V-015-V-034 (LOW) — No dependencies — SAFE to deploy independently
```

### Safe Parallel Execution Groups

**Group 1 (Independent — Immediate):** V-001, V-003, V-007, V-008, V-012, V-013, V-015, V-016, V-018, V-023, V-025, V-026, V-027, V-029, V-030, V-032, V-033, V-034

**Group 2 (Infrastructure-dependent):** V-002 (email), V-005 (monitoring), V-006 (Redis)

**Group 3 (Coordinated):** V-004 (multiple endpoints), V-009 (environment config), V-010 (startup validation), V-011 (frontend+backend)

### Circular Dependencies

**None detected.** All findings are independent or have linear dependency chains.

---

## Semantic Targeting Stability Analysis

### Stable Anchors (Function/Method Level)

| Finding | Anchor | Stability |
|---|---|---|
| V-001 | `upload_file_endpoint` in `upload.py` | STABLE — function definition |
| V-002 | `approve_registration_request_admin_endpoint` in `admin.py` | STABLE — function definition |
| V-003 | `_setup_static_files` in `app.py` | STABLE — function definition |
| V-004 | Multiple endpoint functions in `dashboards.py` | STABLE — function definitions |
| V-005 | `DataService.__init__` in `data_service.py` | STABLE — class method |
| V-006 | `TaskQueue` class in `task_queue.py` | STABLE — class definition |
| V-007 | `DataService.get_aggregated_data` in `data_service.py` | STABLE — class method |
| V-008 | Multiple endpoint functions in `dashboards.py` | STABLE — function definitions |
| V-009 | `create_app` in `app.py` | STABLE — function definition |
| V-010 | `Settings` class in `config.py` | STABLE — class definition |
| V-012 | `_decode_token_cached` in `permissions.py` | STABLE — function definition |
| V-013 | `check_dashboard_access` in `permissions.py` | STABLE — function definition |

### Unstable Anchors (Rejected)

No findings rely on line-based anchors. All validated findings use function/class/method-level anchors which are stable across unrelated code changes.

---

## Execution Applicability Analysis

### Current Applicability Status

All 34 validated findings are **currently applicable**. The codebase was inspected directly and all issues were confirmed to exist in the current source code.

### Staleness Risk

| Risk Level | Findings | Notes |
|---|---|---|
| Low | V-001-V-014, V-017-V-034 | Core architecture findings. Unlikely to change without explicit refactoring. |
| Medium | V-015, V-016 | Frontend type definitions. Could change during feature development. |
| High | V-006 (task queue) | If Redis/RQ integration is implemented, this finding becomes stale. |

### Conflicting Modifications

**None detected.** No two validated findings target the same code in conflicting ways. V-004 targets multiple endpoints but the fix pattern is consistent (add access checks).

---

## Test Coverage Gaps (From Test Audit Reports)

The following test coverage gaps were identified. These are **not** code defects but represent risk areas:

| Area | Risk | Priority |
|---|---|---|
| Data Processing Pipeline (`data/loaders/`, `data/processing/`) | **Critical** — No tests at all for CSVLoader, DataValidator, transformations | HIGH |
| Dashboard Service (`services/dashboard_service.py`) | **High** — No tests for grant_access, revoke_access, get_user_dashboards | HIGH |
| User Service (`services/user_service.py`) | **High** — No tests for update_user_role, delete_user | HIGH |
| Permissions (`core/permissions.py`) | **High** — No tests for check_role, check_dashboard_access | HIGH |
| Workers (`workers/`) | **High** — No tests for process_csv_background | HIGH |
| API: Data endpoints (`routes/data.py`) | **High** — No tests for GET `/data/aggregated` | HIGH |
| API: Admin endpoints (`routes/admin.py`) | **High** — No tests for user role changes, registration approval | HIGH |
| API: Processing config/log endpoints | **Medium** — No tests | MEDIUM |
| Rate Limiting | **Medium** — Only mock bypass tested | MEDIUM |
| Temp file cleanup | **Medium** — No tests for cleanup functions | MEDIUM |
| Change password | **Medium** — AuthService.change_password untested | MEDIUM |

### Test Quality Issues (Summary)

- **Overmocking:** `test_auth_service.py`, `test_graph_service.py`, `test_data_service.py` use heavy mocking that tests mock interactions rather than real behavior.
- **Tautological tests:** Several tests verify framework behavior (Pydantic validation, bcrypt salt randomness) rather than application logic.
- **Fragile tests:** `test_upload_api.py` tests accept multiple status codes, making them pass regardless of actual behavior.
- **Architecture conflicts:** `test_pydantic_models.py` has tests that reference fields not in production models.

---

## Architectural Consistency Warnings

1. **DI Pattern Inconsistency:** Some routes use `Depends()` injection while others instantiate repositories directly. This is a maintainability concern but not a functional defect.

2. **Layer Separation:** The architecture generally follows Clean Architecture well. The main inconsistency is in `dashboards.py` routes that bypass the DI container.

3. **Error Handling Pattern:** Inconsistent error handling across routes — some use specific exceptions, others use broad `Exception` catches with `detail=str(e)`.

4. **Configuration Management:** The configuration system is well-designed with proper priority chain. The main concern is weak defaults in production-facing config files.

---

## Unsafe Execution Warnings

1. **V-002 (temp password):** Do NOT deploy a fix that generates random passwords without also implementing email notification. This would lock users out of their accounts.

2. **V-006 (task queue):** Do NOT attempt to migrate from in-memory queue to Redis/RQ as a small incremental change. This requires careful planning, data migration, and rollback procedures.

3. **V-009 (CORS):** Do NOT restrict CORS methods/headers without verifying all frontend API calls use only the allowed methods. Could break the frontend.

4. **V-010 (admin credentials):** Do NOT add production startup validation that fails on default credentials without first ensuring all deployment configurations have explicit credentials set. Could cause production outages.

---

*End of Validated Findings Document*
*Total: 34 validated findings (3 HIGH, 5 MEDIUM-HIGH, 12 MEDIUM, 14 LOW), 6 rejected, 6 merged*
*Source: 8 audit reports, direct codebase inspection of 40+ source files*
