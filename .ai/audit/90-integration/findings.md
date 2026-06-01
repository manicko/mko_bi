# Phase 09 Audit Findings — Integration

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### INT-001: POST /upload/{dashboard_id}/process accepts task_id as query parameter but route has no path parameter for it

| Field | Value |
|-------|-------|
| **ID** | INT-001 |
| **Severity** | CRITICAL |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/api/routes/upload.py`, `frontend/src/features/upload/api/uploadApi.ts` |
| **Classification** | mandatory |

**Description:** The `process_file_endpoint` in the upload router defines the route as `POST /{dashboard_id}/process` but the handler function signature includes `task_id: UUID` as a query parameter. The route decorator does NOT include `/{task_id}` in the path. In FastAPI, this means `task_id` will be interpreted as a query parameter rather than a path parameter. The frontend `uploadApi.ts` calls `POST /upload/{dashboardId}` (not `/upload/{dashboardId}/process`) for uploading, so there is no frontend call to `/process` — but the backend exposes this endpoint and it would fail at runtime if called because `task_id` would be missing from the query string.

**Evidence:**
- Backend route definition: `src/mkobi/api/routes/upload.py:217` — `@router.post("/{dashboard_id}/process", ...)` — no `task_id` path param
- Backend handler signature: `src/mkobi/api/routes/upload.py:224` — `async def process_file_endpoint(task_id: UUID, dashboard_id: UUID, ...)` — `task_id` expected as query param
- Frontend upload call: `frontend/src/features/upload/api/uploadApi.ts:16-17` — `axiosInstance.post<UploadResponse>(\`/upload/${dashboardId}\`, ...)` — calls upload endpoint, not `/process`

**Recommendation:** Either add `task_id` as a path parameter to the route (`/{dashboard_id}/process/{task_id}`) or ensure the frontend actually calls this endpoint correctly with `task_id` as a query parameter. Alternatively, if this endpoint is unused, remove it to reduce attack surface.

---

### INT-002: GET /api/v1/filters — Frontend calls /api/v1/filters but backend registers two filter routers causing a prefix conflict

| Field | Value |
|-------|-------|
| **ID** | INT-002 |
| **Severity** | CRITICAL |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/app.py`, `src/mkobi/api/routes/filters.py`, `src/mkobi/api/routes/dashboards_filters.py` |
| **Classification** | mandatory |

**Description:** The `filters.py` router is registered with `prefix="/api/v1/filters"` in `app.py:208`, but `filters.router` is created in `filters.py:32` with `APIRouter(tags=["filters"])` — NO prefix, meaning its routes render as `GET /api/v1/filters/` (note trailing-slash-free). Meanwhile, `dashboards_filters.py` also creates routes at `/dashboards/{dashboard_id}/filters` and `/dashboards/{dashboard_id}/filters/{filter_id}` which are mounted under the `dashboards` router prefix `/api/v1/dashboards`. There is no actual prefix collision for the global filters endpoints, BUT the filters router has `redirect_slashes=False` (line 32), which means both `/api/v1/filters` and `/api/v1/filters/` would match. This is not the actual problem.

The REAL problem: The frontend `dashboardApi.ts` does not call the filter endpoints at all — no frontend feature calls `GET /api/v1/filters`. The `Filter` type exists in `api.types.ts` (line 53-58) but is never used by any frontend API call. This means the global filters CRUD backend endpoints (`/api/v1/filters`) are completely disconnected from the frontend — an orphaned API surface.

**Evidence:**
- Frontend types defined: `frontend/src/shared/types/api.types.ts:53-58` — `Filter` interface exists
- No frontend API call: `frontend/src/features/` — no file imports or calls `/filters` endpoint
- Backend registers: `src/mkobi/app.py:208` — `application.include_router(routes.filters.router, prefix="/api/v1/filters")`

**Recommendation:** Either implement the frontend filter management UI or remove the orphaned backend endpoints. An unused API surface increases attack surface without value.

---

### INT-003: `/api/v1/layouts` — Frontend calls `/layouts` but adminApi declares `getLayouts()` calling `/layouts` which maps to `/api/v1/layouts`; however LayoutRead response shape has `updated_at` field that backend doesn't return from `create_layout`

| Field | Value |
|-------|-------|
| **ID** | INT-003 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/features/admin/api/adminApi.ts`, `src/mkobi/services/layout_service.py`, `src/mkobi/api/routes/layouts.py` |
| **Classification** | advisory |

**Description:** The `create_layout_endpoint` in `layouts.py:46` returns `LayoutRead` but only calls `layout_service.create_layout()` which creates the ORM model and returns it. The `LayoutRead` model expects `id`, `name`, `definition`, `created_at`, and `updated_at` fields. The `updated_at` field is defined in the `LayoutRead` Pydantic model (`layout.py:92`), and will be populated by SQLAlchemy's `server_default=text("now()")` on creation, so it should work. However, the `updated_at` column is defined in the layout ORM model and needs to be verified. This is a potential issue if `updated_at` is None on creation.

**Evidence:**
- Frontend type: `frontend/src/features/admin/api/adminApi.ts:15-21` — `LayoutRead` interface expects `updated_at: string`
- Backend response model: `src/mkobi/api/routes/layouts.py:35` — `response_model=LayoutRead`
- Backend model: `src/mkobi/models/layout.py:87-92` — `LayoutRead` requires `updated_at: datetime`

**Recommendation:** Verify that the layout ORM model includes `updated_at` column and that it's populated on creation. If not, either add the column or make `updated_at` optional in `LayoutRead`.

---

### INT-004: Password change response format inconsistency — Backend returns `{"message": "..."}` dict, frontend `changePassword` declares `Promise<void>`

| Field | Value |
|-------|-------|
| **ID** | INT-004 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/api/routes/auth.py`, `frontend/src/features/users/api/userApi.ts` |
| **Classification** | advisory |

**Description:** The backend `change_password` endpoint (`auth.py:372-433`) returns `dict[str, Any]` with `{"message": "Password changed successfully"}` and has no `response_model` defined. The frontend `userApi.ts:13-14` declares `changePassword` as `Promise<void>` and ignores the response body. This works at runtime because Axios returns the response but the frontend doesn't read `.data`, but it's an inconsistency — the return type annotation on `changePassword` says `void` when the endpoint actually returns a JSON body.

**Evidence:**
- Backend: `src/mkobi/api/routes/auth.py:433` — `return {"message": "Password changed successfully"}`
- Frontend: `frontend/src/features/users/api/userApi.ts:13-14` — `Promise<void>` and `await axiosInstance.post('/auth/change-password', data)` without reading `.data`

**Recommendation:** Either add a `response_model=SuccessResponse` to the backend endpoint for consistency, or update the frontend type to acknowledge the response. Low severity since it works but violates the project's type-safety principle.

---

### INT-005: Processing status response field mismatch — Backend returns `progress`, `started_at`, `completed_at`; frontend `ProcessingStatusResponse` has `message`, `started_at`, `finished_at` but no `progress`, and uses `finished_at` instead of `completed_at`

| Field | Value |
|-------|-------|
| **ID** | INT-005 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/models/data.py`, `frontend/src/shared/types/api.types.ts`, `frontend/src/features/upload/api/uploadApi.ts` |
| **Classification** | mandatory |

**Description:** The backend `ProcessingStatusResponse` model (`data.py:84-110`) defines fields: `task_id`, `filename`, `dashboard_id`, `status`, `progress` (int), `message`, `started_at`, `completed_at`. The frontend `ProcessingStatusResponse` type (`api.types.ts:154-159`) defines: `status`, `message?`, `started_at?`, `finished_at?` — it uses `finished_at` instead of `completed_at` entirely. This means the frontend will never read the `completed_at` field from backend responses. Additionally, the backend field `progress` is entirely missing from the frontend type, and `filename`/`dashboard_id` are absent too. The frontend `useProcessingStatus` hook polls for status changes and checks `data.status === 'completed'` — which happens to work since `ProcessingStatus.COMPLETED = 'completed'` matches the backend. But `data?.status === 'failed'` also needs to match — backend uses `ProcessingStatus.FAILED = 'failed'` which is correct.

However, the CRITICAL issue is: the frontend checks `data?.status === 'completed'` and `data?.status === 'failed'` to stop polling. The backend returns `status: ProcessingStatus` which is a string enum value. This actually aligns. But the `completed_at` vs `finished_at` naming mismatch means any frontend code trying to display completion time would get `undefined`.

**Evidence:**
- Backend model: `src/mkobi/models/data.py:84-110` — fields: `task_id`, `filename`, `dashboard_id`, `status`, `progress`, `message`, `started_at`, `completed_at`
- Frontend type: `frontend/src/shared/types/api.types.ts:154-159` — fields: `status`, `message?`, `started_at?`, `finished_at?` (WRONG field name)
- Frontend polling: `frontend/src/features/upload/api/uploadApi.ts:53` — checks `data?.status === 'completed'` and `data?.status === 'failed'`

**Recommendation:** Align frontend type with backend: rename `finished_at` to `completed_at`, add missing `progress`, `task_id`, `filename`, `dashboard_id` fields.

---

### INT-006: `DashboardSummary` frontend type missing `config`, `layout`, `layout_id`, `updated_at`; backend `DashboardRead` returns them — but frontend `getMyDashboards` calls `/dashboards/my` which returns `list[DashboardRead]`

| Field | Value |
|-------|-------|
| **ID** | INT-006 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/shared/types/api.types.ts`, `src/mkobi/api/routes/dashboards_crud.py` |
| **Classification** | advisory |

**Description:** The frontend `dashboardApi.getMyDashboards()` calls `GET /dashboards/my` which returns `list[DashboardRead]`. The backend `DashboardRead` model includes `config`, `layout`, `layout_id`, `updated_at` fields. But the frontend `getMyDashboards` returns `DashboardSummary[]` which only has `id`, `name`, `description`, `permission`, `created_at`. The `DashboardSummary` type is more restrictive and lacks `layout`, `layout_id`, `config`, `updated_at`. While this is acceptable for a list view (you don't need full config), the `permission` field in `DashboardSummary` does NOT exist on the backend `DashboardRead` model — the backend doesn't return `permission` in the `DashboardRead` response. The frontend type includes `permission` as a required field but the backend never sends it.

**Evidence:**
- Frontend call: `frontend/src/features/dashboards/api/dashboardApi.ts:13` — `axiosInstance.get<DashboardSummary[]>('/dashboards/my')`
- Backend response: `src/mkobi/api/routes/dashboards_crud.py:153` — `response_model=list[DashboardRead]`
- Backend model: `src/mkobi/models/dashboard.py:92-126` — `DashboardRead` fields: `id`, `name`, `description`, `config`, `layout_id`, `layout`, `created_at`, `updated_at` — NO `permission` field
- Frontend type: `frontend/src/shared/types/api.types.ts:17-23` — `DashboardSummary` requires `permission: DashboardPermission`

**Recommendation:** Either add `permission` to the backend `DashboardRead` response (computed from the user's access), or make `permission` optional in the frontend `DashboardSummary` type.

---

### INT-007: Logout does not invalidate the refresh token on the backend — only deletes the cookie on the client

| Field | Value |
|-------|-------|
| **ID** | INT-007 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/api/routes/auth.py`, `frontend/src/features/auth/api/authApi.ts`, `frontend/src/features/auth/model/useAuth.ts` |
| **Classification** | mandatory |

**Description:** The backend `logout` endpoint (`auth.py:346-363`) only calls `delete_secure_cookie(response, COOKIE_NAME)` which clears the refresh token cookie from the response. The access token is NOT blacklisted or stored server-side (JWT is stateless). However, the refresh token (stored in httpOnly cookie) remains valid until it expires (default 7 days = 10080 minutes). If an attacker obtains the refresh token value before logout, they can continue to use it to get new access tokens until it expires. There is no server-side token revocation mechanism (no Redis blacklist, no token versioning).

**Evidence:**
- Backend logout: `src/mkobi/api/routes/auth.py:362` — only `delete_secure_cookie(response, COOKIE_NAME)` — no token blacklisting
- Refresh token TTL: `src/mkobi/config.py:130` — `refresh_token_expire_minutes: int = 10080` (7 days)
- No blacklist implementation: `src/mkobi/core/security.py` — no token revocation logic
- Frontend logout: `frontend/src/features/auth/model/useAuth.ts:44-52` — calls `apiLogout()` then `logoutClient()` (removes access token from memory/storage)

**Recommendation:** Implement server-side refresh token revocation by storing a token version or jti (JWT ID) in the database or Redis, and checking it during token refresh. On logout, increment the version or add the jti to a blacklist. This is a security gap — stolen refresh tokens remain valid for up to 7 days after logout.

---

### INT-008: Error response format inconsistency across handlers — some return `{detail, status_code, error_code}`, others return `{message}` or raw dict

| Field | Value |
|-------|-------|
| **ID** | INT-008 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/app.py`, `src/mkobi/utils/exceptions.py`, `src/mkobi/api/routes/auth.py`, `src/mkobi/api/routes/upload.py` |
| **Classification** | advisory |

**Description:** The backend has multiple error response formats:
1. HTTP exceptions in routes return `{"detail": "..."}` (raw from FastAPI) — caught by the global HTTP handler which wraps it as `{"detail": ..., "status_code": ..., "error_code": "HTTP_..."}` (`app.py:278-290`)
2. AppException returns `{"status_code": ..., "detail": ..., "error_code": "..."}` (`exceptions.py:103-108`)
3. Validation errors return `{"detail": "Validation error", "errors": [...], ...}` (`app.py:297-305`)
4. `SuccessResponse` returns `{"message": "..."}` — this is a success format, not error
5. `change_password` endpoint returns raw `{"message": "..."}` dict with no standard wrapper
6. `logout` returns `SuccessResponse(message="Logged out successfully")`
7. `register-request` returns raw `{"message": "...", "id": ...}` dict

The frontend `axiosInstance` error handler checks `error.response.status` and shows generic toast messages. It does not parse the error body at all — meaning the structured error codes from the backend are never used by the frontend. Users only see generic "Access denied" or "Session expired" toasts regardless of the actual error.

**Evidence:**
- Error handler: `src/mkobi/app.py:278-290` — wraps HTTP exceptions with `error_code: "HTTP_{status_code}"`
- Frontend error handling: `frontend/src/shared/api/axiosInstance.ts:105-107` — only checks `status === 403` and shows "Access denied"
- No frontend parsing: no code reads `error.response.data.detail` or `error.response.data.error_code`

**Recommendation:** Standardize all error responses to a single format (e.g., `{status_code, detail, error_code}`) across all endpoints. Update the frontend to display the `detail` field from the error response rather than generic messages.

---

### INT-009: Frontend does not handle `force_password_change` flow after login — only handles it after token refresh on page load

| Field | Value |
|-------|-------|
| **ID** | INT-009 |
| **Severity** | MEDIUM |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `frontend/src/features/auth/model/useAuth.ts` |
| **Classification** | mandatory |

**Description:** The `useAuth` hook checks `profile.force_password_change` and redirects to `/profile/change-password?force=true` in two places: after the initial token refresh on page load (line 65) and after fetching profile with an existing token (line 84). However, the `login` callback function (line 24-38) does NOT check `force_password_change` after a successful login. This means that if an admin creates a user with a temporary password and sets `force_password_change=True`, the user can log in and access dashboards without ever being redirected to change their password.

**Evidence:**
- Login handler: `frontend/src/features/auth/model/useAuth.ts:24-38` — sets token and user, returns response, NO force_password_change check
- Token refresh handler: `frontend/src/features/auth/model/useAuth.ts:65` — checks `profile.force_password_change`
- Existing token handler: `frontend/src/features/auth/model/useAuth.ts:84` — checks `profile.force_password_change`
- Backend sets flag: `src/mkobi/api/routes/admin.py:241-244` — `force_password_change=True` when admin approves registration

**Recommendation:** Add a `force_password_change` check in the `login` callback function, redirecting to `/profile/change-password?force=true` before allowing dashboard access.

---

### INT-010: `createDashboard` admin API sends `layout_id` in payload but frontend `CreateDashboardRequest` type doesn't include `config` — layout-only creation may conflict with backend defaults

| Field | Value |
|-------|-------|
| **ID** | INT-010 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/features/admin/api/adminApi.ts`, `frontend/src/shared/types/api.types.ts`, `src/mkobi/api/routes/dashboards_crud.py` |
| **Classification** | advisory |

**Description:** The frontend `CreateDashboardRequest` type (`api.types.ts:204-208`) includes `name`, `description?`, `layout?` but no `config` field. The backend `DashboardCreate` model (`dashboard.py:50-89`) has a default config `DashboardConfig(graph_types=[GraphType.BAR])` if none is provided. However, the `adminApi.createDashboard()` function builds a payload explicitly with only `name`, `description`, and optionally `layout_id` — it never sends `config`. This means all admin-created dashboards get the default config with only `bar` graph type. This is functional but means the admin cannot configure dashboard graph types during creation from the frontend.

**Evidence:**
- Frontend type: `frontend/src/shared/types/api.types.ts:204-208` — `CreateDashboardRequest` has no `config` field
- Frontend API: `frontend/src/features/admin/api/adminApi.ts:87-103` — builds payload without `config`
- Backend default: `src/mkobi/models/dashboard.py:55` — `config: DashboardConfig = DashboardConfig(graph_types=[GraphType.BAR])`

**Recommendation:** Add config field to `CreateDashboardRequest` and pass it through in `createDashboard()`, or accept the limitation and document it. Low severity since defaults work.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 2 |
| HIGH | 3 |
| MEDIUM | 3 |
| LOW | 2 |

## Mandatory Fixes

1. **INT-001** — Fix or remove the orphaned `POST /upload/{dashboard_id}/process` route to eliminate runtime errors and reduce attack surface
2. **INT-002** — Either implement frontend filter management for `/api/v1/filters` or remove the orphaned backend endpoints
3. **INT-005** — Align `ProcessingStatusResponse` frontend type with backend: rename `finished_at` to `completed_at`, add missing fields
4. **INT-007** — Implement server-side refresh token revocation (Redis blacklist or token versioning) to prevent stolen refresh tokens from being used after logout
5. **INT-009** — Add `force_password_change` check in the `login` callback to redirect users with temporary passwords

## Advisory Recommendations

1. **INT-003** — Verify layout model `updated_at` field exists and is populated
2. **INT-004** — Align password change endpoint response format with project standards
3. **INT-006** — Align `DashboardSummary`/`DashboardRead` field mismatch, especially the missing `permission` field
4. **INT-008** — Standardize error response format across all endpoints; update frontend to display backend error details
5. **INT-010** — Consider adding config support to admin dashboard creation

## Doc Updates Needed

- Document the logout/token revocation behavior and its limitations (INT-007)
- Document the intentional separation between `DashboardSummary` (list view) and `DashboardRead` (detail view) response shapes (INT-006)
- Document the error response format standard for all API endpoints (INT-008)
