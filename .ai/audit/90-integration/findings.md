# Phase 90 Audit Findings — Integration

**Executor:** auditor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### INT-001: `ProcessingConfigRead` missing `metric_agg` field — backend response shape mismatch

| Field | Value |
|-------|-------|
| **ID** | INT-001 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/models/processing_configs.py`, `src/mkobi/db/models/processing_configs.py` |
| **Classification** | mandatory |

**Description:** The `ProcessingConfigRead` Pydantic model at `src/mkobi/models/processing_configs.py:57-77` inherits from `ProcessingConfigBase` which includes `metric_agg: AggregationFunctionEnum | None`. However, the database model `ProcessingConfig` at `src/mkobi/db/models/processing_configs.py:18-56` has **no `metric_agg` column** — only `dashboard_id`, `settings`, and `updated_at`. This means the `metric_agg` field will always be `None` when reading from the DB, and the `upsert` endpoint at `src/mkobi/api/routes/processing_configs.py:162-167` accepts `metric_agg` from the request but the value is never persisted. The frontend never consumes this field directly, but any consumer of the API expecting `metric_agg` in the response will receive `null` silently.

**Evidence:**
- DB model columns (`src/mkobi/db/models/processing_configs.py:27-43`): only `dashboard_id`, `settings`, `updated_at` — no `metric_agg`
- Pydantic model (`src/mkobi/models/processing_configs.py:12`): `metric_agg: AggregationFunctionEnum | None = None`
- Upsert endpoint (`src/mkobi/api/routes/processing_configs.py:162-167`): accepts `metric_agg` but service layer has no column to persist it

**Recommendation:** Either add a `metric_agg` column to the `processing_configs` table (via Alembic migration) and persist it in the service layer, or remove the field from `ProcessingConfigBase` / `ProcessingConfigRead` to avoid misleading API consumers. The former is the likely intent since the upsert endpoint explicitly handles it.

---

### INT-002: `DashboardRead` missing `permission` field in DB model — relies on service-layer injection

| Field | Value |
|-------|-------|
| **ID** | INT-002 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/models/dashboard.py`, `src/mkobi/db/models/dashboard.py`, `src/mkobi/api/routes/dashboards_crud.py` |
| **Classification** | advisory |

**Description:** The `DashboardRead` Pydantic model at `src/mkobi/models/dashboard.py:92-127` includes a `permission: DashboardPermission` field, but the `Dashboard` ORM model at `src/mkobi/db/models/dashboard.py:32-162` has **no `permission` column**. The `permission` value is injected at the service layer (`DashboardService.get_dashboard()`) based on the user's access level. While this works, it creates a hidden contract: the `DashboardRead` model can only be constructed by the service layer, not directly from an ORM instance via `model_validate()`. If any code attempts `DashboardRead.model_validate(orm_instance)`, it will fail or produce `None` for `permission`. This is a maintenance hazard.

**Evidence:**
- Pydantic model (`src/mkobi/models/dashboard.py:99`): `permission: DashboardPermission`
- ORM model (`src/mkobi/db/models/dashboard.py:32-162`): no `permission` attribute
- CRUD endpoint (`src/mkobi/api/routes/dashboards_crud.py:241`): `dashboard_service.get_dashboard(...)` returns a dict or object with permission injected

**Recommendation:** Document this hidden contract explicitly in the `DashboardRead` docstring, or refactor to use a dedicated response builder that makes the injection explicit. Consider adding a comment at the model definition warning against direct ORM validation.

---

### INT-003: `UserRead` has `force_password_change` but `AdminUser` frontend type does not — type misalignment

| Field | Value |
|-------|-------|
| **ID** | INT-003 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/models/user.py`, `frontend/src/shared/types/api.types.ts` |
| **Classification** | advisory |

**Description:** The backend `UserRead` model at `src/mkobi/models/user.py:42-68` includes `force_password_change: bool = False`. The frontend `UserProfile` type at `frontend/src/shared/types/api.types.ts:40-47` also includes `force_password_change: boolean`. However, the frontend `AdminUser` type at `frontend/src/shared/types/api.types.ts:219-225` is **missing** `force_password_change`. The admin API (`GET /admin/users`) returns `UserRead` objects which include `force_password_change`, but the frontend `AdminUser` type will silently drop this field. If the admin panel needs to display or act on `force_password_change` (e.g., indicating which users need to change passwords), this data is lost.

**Evidence:**
- Backend `UserRead` (`src/mkobi/models/user.py:48`): `force_password_change: bool = False`
- Frontend `UserProfile` (`frontend/src/shared/types/api.types.ts:46`): `force_password_change: boolean`
- Frontend `AdminUser` (`frontend/src/shared/types/api.types.ts:219-225`): missing `force_password_change`
- Admin endpoint (`src/mkobi/api/routes/admin.py:52`): returns `UserRead` objects

**Recommendation:** Add `force_password_change: boolean` to the `AdminUser` frontend type to align with the backend `UserRead` model.

---

### INT-004: `ProcessingStatusResponse.error_code` is `str | null` in backend but `ErrorCode | null` in frontend

| Field | Value |
|-------|-------|
| **ID** | INT-004 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/models/data.py`, `frontend/src/shared/types/api.types.ts` |
| **Classification** | advisory |

**Description:** The backend `ProcessingStatusResponse` model at `src/mkobi/models/data.py:98` declares `error_code: str | None = None`, while the frontend `ProcessingStatusResponse` type at `frontend/src/shared/types/api.types.ts:207` declares `error_code?: ErrorCode | null`. The backend sends a raw string; the frontend expects an enum-typed value. Since `ErrorCode` is a const object (not a TypeScript enum), the frontend will accept any string at runtime — but the type annotation is misleading and won't provide proper type narrowing. If the backend sends an error code string that doesn't match the frontend `ErrorCode` values, the frontend's `mapErrorCode` function in `errorHandler.ts:118-123` will fall back to `INTERNAL_ERROR`, potentially losing the actual error context.

**Evidence:**
- Backend (`src/mkobi/models/data.py:98`): `error_code: str | None = None`
- Frontend (`frontend/src/shared/types/api.types.ts:207`): `error_code?: ErrorCode | null`
- Error handler (`frontend/src/shared/api/errorHandler.ts:118-123`): falls back to `INTERNAL_ERROR` for unknown codes

**Recommendation:** Align the types — either make the frontend type `string | null` to match the backend, or make the backend use `ErrorCode` enum type in the Pydantic model for stronger validation.

---

### INT-005: `ProcessingLogRead` has `dashboard_name` in Pydantic model but not in DB model — service-layer injection required

| Field | Value |
|-------|-------|
| **ID** | INT-005 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/models/processing_logs.py`, `src/mkobi/db/models/processing_logs.py` |
| **Classification** | advisory |

**Description:** The `ProcessingLogRead` Pydantic model at `src/mkobi/models/processing_logs.py:74-99` includes `dashboard_name: str | None = None`, but the `ProcessingLog` ORM model at `src/mkobi/db/models/processing_logs.py:21-90` has **no `dashboard_name` column** — only `dashboard_id`. The `dashboard_name` must be injected by the service layer (e.g., via a join or separate query). The admin logs endpoint at `src/mkobi/api/routes/processing_logs.py:85-88` uses `ProcessingLogService.get_filtered()` which presumably handles this, but the repository-level `get_by_id` at line 113-120 returns the raw ORM model validated via `ProcessingLogRead.model_validate(log)`, which would fail to populate `dashboard_name`.

**Evidence:**
- Pydantic model (`src/mkobi/models/processing_logs.py:79`): `dashboard_name: str | None = None`
- ORM model (`src/mkobi/db/models/processing_logs.py:21-90`): no `dashboard_name` column
- Endpoint (`src/mkobi/api/routes/processing_logs.py:113-120`): `ProcessingLogRead.model_validate(log)` on raw ORM instance

**Recommendation:** Ensure the service layer always injects `dashboard_name` before returning, or make the field optional with a default and document that it requires service-layer population. Consider using a DTO pattern to separate ORM validation from API response construction.

---

### INT-006: `logout` endpoint returns `SuccessResponse` (200) but frontend `logout()` expects `void` — response body silently discarded

| Field | Value |
|-------|-------|
| **ID** | INT-006 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/api/routes/auth.py`, `frontend/src/features/auth/api/authApi.ts` |
| **Classification** | advisory |

**Description:** The backend logout endpoint at `src/mkobi/api/routes/auth.py:393-444` returns `response_model=SuccessResponse` with `status.HTTP_200_OK`, which produces a JSON body `{"message": "Logged out successfully"}`. The frontend `logout()` function at `frontend/src/features/auth/api/authApi.ts:26-28` calls `axiosInstance.post('/auth/logout')` and returns `Promise<void>`, discarding the response body. While this works, it creates an inconsistency: the backend declares a response model but the frontend ignores it. If the backend ever needs to return additional data (e.g., redirect URL, session info), the frontend won't receive it.

**Evidence:**
- Backend (`src/mkobi/api/routes/auth.py:395`): `response_model=SuccessResponse`
- Frontend (`frontend/src/features/auth/api/authApi.ts:26-28`): `Promise<void>`, no return value processing

**Recommendation:** Either change the backend to return `204 No Content` (no body) to match the frontend's `void` expectation, or update the frontend to process the response body. The `204 No Content` approach is more semantically correct for a logout operation.

---

### INT-007: `register-request` endpoint returns `{"message": "...", "id": ...}` but frontend `registerRequest()` expects `RegistrationResponse`

| Field | Value |
|-------|-------|
| **ID** | INT-007 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/api/routes/auth.py`, `frontend/src/features/auth/api/authApi.ts` |
| **Classification** | advisory |

**Description:** The backend `register_request` endpoint at `src/mkobi/api/routes/auth.py:506-591` has no `response_model` declared and returns `{"message": "Request submitted", "id": result["id"]}`. The frontend `registerRequest()` function at `frontend/src/features/auth/api/authApi.ts:17-18` expects `RegistrationResponse` which has `message: string` and `id: string`. While the shapes happen to match, the backend response is not validated against any Pydantic model, meaning the response format is not contractually guaranteed. If the backend changes the response shape, the frontend won't get a type error.

**Evidence:**
- Backend (`src/mkobi/api/routes/auth.py:506-507`): no `response_model`, returns raw dict
- Frontend (`frontend/src/features/auth/api/authApi.ts:17`): `Promise<RegistrationResponse>`

**Recommendation:** Add `response_model=RegistrationResponse` to the backend endpoint to enforce the contract and get automatic validation.

---

### INT-008: `change-password` endpoint returns `dict[str, Any]` — no response model validation

| Field | Value |
|-------|-------|
| **ID** | INT-008 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/api/routes/auth.py`, `frontend/src/features/users/api/userApi.ts` |
| **Classification** | advisory |

**Description:** The backend `change_password` endpoint at `src/mkobi/api/routes/auth.py:447-503` has no `response_model` and returns `{"message": "Password changed successfully"}` as a raw dict. The frontend `changePassword()` function at `frontend/src/features/users/api/userApi.ts:13-14` expects `Promise<void>`. The response body is discarded on the frontend side. This is inconsistent with other similar endpoints (e.g., logout uses `SuccessResponse`).

**Evidence:**
- Backend (`src/mkobi/api/routes/auth.py:447-449`): no `response_model`, returns raw dict
- Frontend (`frontend/src/features/users/api/userApi.ts:13-14`): `Promise<void>`

**Recommendation:** Use `response_model=SuccessResponse` and `status_code=200` for consistency with the logout endpoint, or return `204 No Content` to match the frontend's `void` expectation.

---

### INT-009: `reject-request` endpoint returns `{"message": "..."}` but frontend `rejectRequest()` expects `void`

| Field | Value |
|-------|-------|
| **ID** | INT-009 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/api/routes/admin.py`, `frontend/src/features/admin/api/adminApi.ts` |
| **Classification** | advisory |

**Description:** The backend `reject_registration_request_admin_endpoint` at `src/mkobi/api/routes/admin.py:343-391` returns `{"message": "Registration request rejected"}` with `status.HTTP_200_OK` and no `response_model`. The frontend `rejectRequest()` at `frontend/src/features/admin/api/adminApi.ts:77-79` calls `axiosInstance.post(...)` without a type parameter and expects `Promise<void>`. The response body is silently discarded.

**Evidence:**
- Backend (`src/mkobi/api/routes/admin.py:343-344`): no `response_model`, returns `{"message": "Registration request rejected"}`
- Frontend (`frontend/src/features/admin/api/adminApi.ts:77-79`): `Promise<void>`, no type parameter on `post()`

**Recommendation:** Add `response_model=SuccessResponse` to the backend endpoint for consistency, or return `204 No Content`.

---

### INT-010: `updateDashboard` frontend expects `DashboardAdmin` but backend returns `DashboardRead`

| Field | Value |
|-------|-------|
| **ID** | INT-010 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/api/routes/dashboards_crud.py`, `frontend/src/features/admin/api/adminApi.ts` |
| **Classification** | advisory |

**Description:** The backend `update_dashboard_endpoint` at `src/mkobi/api/routes/dashboards_crud.py:281-374` declares `response_model=DashboardRead` which includes fields like `config`, `permission`, `layout`, `layout_id`, `updated_at`. The frontend `updateDashboard()` function at `frontend/src/features/admin/api/adminApi.ts:116-118` expects `DashboardAdmin` which only has `id`, `name`, `description`, `created_at`, `updated_at` — **no `config`**, **no `permission`**, **no `layout`**. The frontend will receive extra fields it doesn't expect (which TypeScript will ignore at compile time), but more importantly, if the frontend code ever tries to access `config` or `permission` on the returned object, it will be `undefined` at runtime.

**Evidence:**
- Backend (`src/mkobi/api/routes/dashboards_crud.py:283`): `response_model=DashboardRead`
- Frontend (`frontend/src/features/admin/api/adminApi.ts:116-118`): `axiosInstance.put<DashboardAdmin>(...)`
- `DashboardRead` (`src/mkobi/models/dashboard.py:92-127`): has `config`, `permission`, `layout`, `layout_id`
- `DashboardAdmin` (`frontend/src/shared/types/api.types.ts:247-253`): no `config`, no `permission`, no `layout`

**Recommendation:** Either create a dedicated `DashboardUpdateResponse` type on the backend that matches what the admin panel actually needs, or update the frontend to use `DashboardDetail` (which has the full shape including `config`, `permission`, `layout`).

---

### INT-011: `getAggregatedData` frontend passes `filters` as object but backend expects JSON string

| Field | Value |
|-------|-------|
| **ID** | INT-011 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `frontend/src/features/dashboards/api/dashboardApi.ts`, `src/mkobi/api/routes/data.py` |
| **Classification** | mandatory |

**Description:** The frontend `getAggregatedData()` function at `frontend/src/features/dashboards/api/dashboardApi.ts:23-29` passes `params` directly to Axios, which serializes the `filters` object as query parameters (e.g., `?filters[key]=value`). However, the backend endpoint at `src/mkobi/api/routes/data.py:52` expects `filters: str | None = Query(default=None, description="JSON string with filters")` — a **JSON string**, not individual query parameters. The backend then does `json.loads(filters)` at line 107. This means the frontend's `filters` object will never be correctly parsed by the backend. The `json.loads()` call will either fail with a `JSONDecodeError` (returning a 400 error to the user) or receive `None` (if the query param is absent), effectively making filter functionality non-functional.

**Evidence:**
- Frontend (`frontend/src/features/dashboards/api/dashboardApi.ts:23-29`): passes `params: { dashboard_id, graph_id, filters }` — Axios serializes `filters` object as individual query params
- Backend (`src/mkobi/api/routes/data.py:52`): `filters: str | None = Query(...)` — expects a JSON string
- Backend (`src/mkobi/api/routes/data.py:107`): `parsed_filters = json.loads(filters)` — will fail on non-string input

**Recommendation:** The frontend must `JSON.stringify(filters)` before passing it as a query parameter. Change the frontend to: `params: { dashboard_id, graph_id, filters: filters ? JSON.stringify(filters) : undefined }`.

---

### INT-012: `AggregatedDataResponse` backend uses `GraphDataResponse` with `layout` field, but frontend `GraphDataWithConfig` uses `layout` of type `Layout` from react-plotly.js

| Field | Value |
|-------|-------|
| **ID** | INT-012 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/models/data.py`, `frontend/src/shared/types/api.types.ts` |
| **Classification** | advisory |

**Description:** The backend `GraphDataResponse` model at `src/mkobi/models/data.py:425-452` declares `layout: ChartLayoutConfig | None = None` where `ChartLayoutConfig` is a custom Pydantic model. The frontend `GraphDataWithConfig` type at `frontend/src/shared/types/api.types.ts:179-192` declares `layout?: Layout` where `Layout` is imported from `react-plotly.js`. These are completely different types. The backend sends a `ChartLayoutConfig` object, but the frontend expects a Plotly `Layout` object. If the frontend passes the backend's `layout` directly to Plotly, it may not render correctly due to shape differences.

**Evidence:**
- Backend (`src/mkobi/models/data.py:435`): `layout: ChartLayoutConfig | None = None`
- Frontend (`frontend/src/shared/types/api.types.ts:184`): `layout?: Layout` (from react-plotly.js)
- `ChartLayoutConfig` (`src/mkobi/models/types.py`): custom Pydantic model
- `Layout` (react-plotly.js): Plotly's own Layout type

**Recommendation:** Ensure the backend's `ChartLayoutConfig` matches the Plotly `Layout` shape, or add a transformation layer on the frontend to convert between the two types.

---

### INT-013: `ProcessingLog` frontend type has `message?: string` but backend `ProcessingLogRead` has `message: str | None` — null vs undefined semantic mismatch

| Field | Value |
|-------|-------|
| **ID** | INT-013 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/models/processing_logs.py`, `frontend/src/shared/types/api.types.ts` |
| **Classification** | advisory |

**Description:** The backend `ProcessingLogRead` model at `src/mkobi/models/processing_logs.py:81` declares `message: str | None = None` (nullable, will serialize as `null` in JSON). The frontend `ProcessingLog` type at `frontend/src/shared/types/api.types.ts:291` declares `message?: string` (optional, will be `undefined` if absent). When the backend sends `{"message": null}`, the frontend receives `null` but the type says `string | undefined`. This is a minor type safety issue — `null` is not `undefined` in TypeScript, and code checking `if (!message)` will work correctly, but code checking `message === undefined` will not match `null`.

**Evidence:**
- Backend (`src/mkobi/models/processing_logs.py:81`): `message: str | None = None`
- Frontend (`frontend/src/shared/types/api.types.ts:291`): `message?: string`

**Recommendation:** Align the types — either make the frontend type `message?: string | null` or make the backend omit the field when null using `response_model_exclude_none=True` or a custom serializer.

---

### INT-014: `deleteDashboard` frontend expects `void` but backend returns `204 No Content` — Axios may throw on 204

| Field | Value |
|-------|-------|
| **ID** | INT-014 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/api/routes/dashboards_crud.py`, `frontend/src/features/admin/api/adminApi.ts` |
| **Classification** | advisory |

**Description:** The backend `delete_dashboard_endpoint` at `src/mkobi/api/routes/dashboards_crud.py:377-449` returns `status.HTTP_204_NO_CONTENT` with no body. The frontend `deleteDashboard()` at `frontend/src/features/admin/api/adminApi.ts:121-122` calls `axiosInstance.delete(...)` and expects `Promise<void>`. While Axios handles 204 responses correctly (resolving with empty data), the `response.data` will be an empty string `""`, not `undefined`. This is generally fine but can cause issues if the frontend code checks `response.data` for truthiness.

**Evidence:**
- Backend (`src/mkobi/api/routes/dashboards_crud.py:379`): `status_code=status.HTTP_204_NO_CONTENT`
- Frontend (`frontend/src/features/admin/api/adminApi.ts:121-122`): `Promise<void>`

**Recommendation:** No immediate fix needed, but document this behavior. If the frontend ever needs to check the response, it should handle the empty string case.

---

### INT-015: `LayoutRead` backend model has `created_at: datetime | None` and `updated_at: datetime | None` but DB model has them as non-nullable with server defaults

| Field | Value |
|-------|-------|
| **ID** | INT-015 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/models/layout.py`, `src/mkobi/db/models/layout.py` |
| **Classification** | advisory |

**Description:** The backend `LayoutRead` Pydantic model at `src/mkobi/models/layout.py:90-92` declares `created_at: datetime | None = None` and `updated_at: datetime | None = None`, but the ORM model at `src/mkobi/db/models/layout.py:50-60` declares both as `nullable=False` with `server_default=text("now()")`. These fields will never be `null` in practice. The Pydantic model's nullable types are misleading and suggest the fields might be absent, which could cause unnecessary null-checks in consumer code.

**Evidence:**
- Pydantic (`src/mkobi/models/layout.py:90-92`): `created_at: datetime | None = None`, `updated_at: datetime | None = None`
- ORM (`src/mkobi/db/models/layout.py:50-60`): `nullable=False`, `server_default=text("now()")`

**Recommendation:** Change the Pydantic model to `created_at: datetime` and `updated_at: datetime` (non-nullable) to match the DB constraint.

---

### INT-016: `UserRead.created_at` is `datetime | None` in Pydantic but `datetime` (non-nullable) in DB

| Field | Value |
|-------|-------|
| **ID** | INT-016 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/models/user.py`, `src/mkobi/db/models/user.py` |
| **Classification** | advisory |

**Description:** The `UserRead` Pydantic model at `src/mkobi/models/user.py:47` declares `created_at: datetime | None = None`, but the ORM model at `src/mkobi/db/models/user.py:76-80` declares `created_at` as `nullable=False` with `server_default=text("now()")`. The field will never be null. Same issue as INT-015 — misleading nullable type.

**Evidence:**
- Pydantic (`src/mkobi/models/user.py:47`): `created_at: datetime | None = None`
- ORM (`src/mkobi/db/models/user.py:76-80`): `nullable=False`, `server_default=text("now()")`

**Recommendation:** Change to `created_at: datetime` in `UserRead`.

---

### INT-017: `UserRead` missing `updated_at` field — present in DB but not in read model

| Field | Value |
|-------|-------|
| **ID** | INT-017 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/models/user.py`, `src/mkobi/db/models/user.py` |
| **Classification** | advisory |

**Description:** The `User` ORM model at `src/mkobi/db/models/user.py:82-86` has an `updated_at` column (`DateTime(timezone=True), nullable=False, server_default=text("now()")`), but the `UserRead` Pydantic model at `src/mkobi/models/user.py:42-68` does **not** include `updated_at`. Any code that updates a user record will have the `updated_at` timestamp in the DB, but it will never be exposed via the API. If the frontend needs to display "last updated" information for users, this data is unavailable.

**Evidence:**
- ORM (`src/mkobi/db/models/user.py:82-86`): `updated_at: Mapped[datetime] = mapped_column(...)` 
- Pydantic (`src/mkobi/models/user.py:42-68`): no `updated_at` field

**Recommendation:** Add `updated_at: datetime` to `UserRead` if the API should expose this timestamp, or document the intentional omission.

---

### INT-018: `Dashboard.created_by` is `UUID | None` in DB but never exposed in any read model

| Field | Value |
|-------|-------|
| **ID** | INT-018 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/db/models/dashboard.py`, `src/mkobi/models/dashboard.py` |
| **Classification** | advisory |

**Description:** The `Dashboard` ORM model at `src/mkobi/db/models/dashboard.py:68-72` has a `created_by` column (nullable UUID foreign key to users). However, none of the Pydantic read models (`DashboardRead`, `DashboardSummary`, `DashboardAdmin`) include this field. The `created_by` data is stored in the DB but never exposed via the API. If the admin panel needs to show who created a dashboard, this information is unavailable through the API.

**Evidence:**
- ORM (`src/mkobi/db/models/dashboard.py:68-72`): `created_by: Mapped[UUID | None] = mapped_column(...)`
- `DashboardRead` (`src/mkobi/models/dashboard.py:92-127`): no `created_by`
- `DashboardAdmin` (`src/mkobi/models/dashboard.py:168-178`): no `created_by`
- `DashboardSummary` (`src/mkobi/models/dashboard.py:154-165`): no `created_by`

**Recommendation:** Add `created_by` to `DashboardAdmin` if the admin panel needs this information, or document the intentional omission.

---

### INT-019: `refreshToken()` frontend function sends POST to `/auth/refresh` with empty body, but backend reads refresh token from httpOnly cookie — works but the empty body is misleading

| Field | Value |
|-------|-------|
| **ID** | INT-019 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/auth/api/authApi.ts`, `src/mkobi/api/routes/auth.py` |
| **Classification** | advisory |

**Description:** The frontend `refreshToken()` function at `frontend/src/features/auth/api/authApi.ts:11-13` sends `axiosInstance.post<Token>('/auth/refresh', {})` with an empty object body. The backend at `src/mkobi/api/routes/auth.py:263-366` reads the refresh token from `request.cookies.get(COOKIE_NAME)` — it completely ignores the request body. The empty body `{}` is misleading and suggests the function might be sending data that isn't needed. Additionally, the `withCredentials: true` in `axiosInstance.ts:10` is what actually sends the cookie.

**Evidence:**
- Frontend (`frontend/src/features/auth/api/authApi.ts:12`): `post<Token>('/auth/refresh', {})`
- Backend (`src/mkobi/api/routes/auth.py:285`): `refresh_token_value = request.cookies.get(COOKIE_NAME)`
- Axios config (`frontend/src/shared/api/axiosInstance.ts:10`): `withCredentials: true`

**Recommendation:** Change the frontend to `post<Token>('/auth/refresh')` (no body) to make it clear that the refresh token comes from cookies, not the request body.

---

### INT-020: `update_user_role` endpoint on `/users/{user_id}` accepts `UserUpdateRequest` with only `role` field, but the same endpoint pattern on `/admin/users/{user_id}/role` also accepts `UserUpdateRequest` — duplicate functionality with different prefixes

| Field | Value |
|-------|-------|
| **ID** | INT-020 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/api/routes/users.py`, `src/mkobi/api/routes/admin.py` |
| **Classification** | advisory |

**Description:** There are two endpoints for updating a user's role:
1. `PUT /api/v1/users/{user_id}` at `src/mkobi/api/routes/users.py:184-243` — accepts `UserUpdateRequest` (role only), requires admin role
2. `PATCH /api/v1/admin/users/{user_id}/role` at `src/mkobi/api/routes/admin.py:61-96` — accepts `UserUpdateRequest` (role only), requires admin role

Both do the same thing (update user role) with the same input model and same permission check. The frontend `adminApi.ts:27-29` uses the admin endpoint (`/admin/users/${userId}/role`). The `/users/{user_id}` endpoint is redundant and creates maintenance overhead — if the role update logic changes, both endpoints must be updated.

**Evidence:**
- Users endpoint (`src/mkobi/api/routes/users.py:184-243`): `PUT /users/{user_id}` with `UserUpdateRequest`
- Admin endpoint (`src/mkobi/api/routes/admin.py:61-96`): `PATCH /admin/users/{user_id}/role` with `UserUpdateRequest`
- Frontend (`frontend/src/features/admin/api/adminApi.ts:27-29`): uses admin endpoint

**Recommendation:** Remove the `PUT /users/{user_id}` role update functionality or mark it as deprecated, and consolidate all admin user management under `/admin/users/*` endpoints.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 6 |
| LOW | 12 |

## Mandatory Fixes

1. **INT-001** — `ProcessingConfigRead.metric_agg` has no DB column — add column or remove field
2. **INT-011** — `getAggregatedData` frontend passes filters as object, backend expects JSON string — runtime error, filters will never work

## Advisory Recommendations

1. **INT-002** — `DashboardRead.permission` not in DB model — document hidden contract
2. **INT-003** — `AdminUser` frontend type missing `force_password_change`
3. **INT-004** — `ProcessingStatusResponse.error_code` type mismatch (`str` vs `ErrorCode`)
4. **INT-005** — `ProcessingLogRead.dashboard_name` not in DB model — service-layer injection required
5. **INT-006** — `logout` returns body but frontend expects `void`
6. **INT-007** — `register-request` endpoint has no `response_model`
7. **INT-008** — `change-password` endpoint has no `response_model`
8. **INT-009** — `reject-request` returns body but frontend expects `void`
9. **INT-010** — `updateDashboard` frontend expects `DashboardAdmin` but backend returns `DashboardRead`
10. **INT-012** — `GraphDataResponse.layout` type mismatch (backend `ChartLayoutConfig` vs frontend Plotly `Layout`)
11. **INT-013** — `ProcessingLog.message` null vs undefined semantic mismatch
12. **INT-014** — `deleteDashboard` 204 response handling
13. **INT-015** — `LayoutRead` timestamps nullable in Pydantic but not in DB
14. **INT-016** — `UserRead.created_at` nullable in Pydantic but not in DB
15. **INT-017** — `UserRead` missing `updated_at` field
16. **INT-018** — `Dashboard.created_by` never exposed in API
17. **INT-019** — `refreshToken()` sends misleading empty body
18. **INT-020** — Duplicate role update endpoints (`PUT /users/{id}` and `PATCH /admin/users/{id}/role`)

## Doc Updates Needed

- Document that `DashboardRead`, `ProcessingLogRead`, and `ProcessingConfigRead` cannot be constructed directly from ORM instances — they require service-layer injection of computed fields
- Document the `metric_agg` field status in processing configs (planned but not yet persisted)
- Document the `created_by` field omission from dashboard read models
