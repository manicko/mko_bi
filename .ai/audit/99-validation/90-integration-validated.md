# Phase 90 Validation Report — Integration Findings

**Validator:** validator agent
**Source:** `.ai/audit/90-integration/findings.md`
**Status:** complete

---

## Rejected Findings

### REJECTED: INT-001

| Field | Value |
|-------|-------|
| **Original Type** | SPEC-DEVIATION |
| **Reason** | Finding is incorrect — `metric_agg` IS persisted. The field is intentionally stored within the JSONB `settings` column via `_merge_metric_agg_into_settings()` in `ProcessingConfigService` (service:processing_config_service.py:50-54). On read, `_extract_metric_agg_from_settings()` (service:processing_config_service.py:56-71) extracts it back to the response model. This is a documented design pattern where `metric_agg` acts as a virtual field in the API layer while being persisted as part of `settings`. No fix required. |

### REJECTED: INT-003

| Field | Value |
|-------|-------|
| **Original Type** | SPEC-DEVIATION |
| **Reason** | Finding is incorrect — the `AdminUser` frontend type DOES include `force_password_change`. Verified at `frontend:src/shared/types/api.types.ts:219-225`: `force_password_change: boolean` is present. No type misalignment exists between `UserRead` and `AdminUser`. |

### REJECTED: INT-005

| Field | Value |
|-------|-------|
| **Original Type** | SPEC-DEVIATION |
| **Reason** | Finding is incorrect — `dashboard_name` IS properly injected. Both `get_filtered()` and `get_by_id()` in `processing_log_repo.py` (lines 156, 222, 258, 294) use `selectinload(ProcessingLog.dashboard)` to join the dashboard and inject `log_read.dashboard_name = log.dashboard.name if log.dashboard else None`. The service layer correctly handles this injection. No missing integration. |

---

## Validated Mandatory Fixes

### INT-011 — RUNTIME-ERROR (CORRECT)

| Field | Value |
|-------|-------|
| **ID** | INT-011 |
| **Type** | RUNTIME-ERROR |
| **Status** | **CONFIRMED — requires fix** |
| **Severity** | HIGH |

**Evidence:**
- Frontend (`frontend:src/features/dashboards/api/dashboardApi.ts:23-29`): `getAggregatedData()` passes `params: { dashboard_id, graph_id, filters }` to Axios
- Axios serializes object params as query parameters: `?filters[key]=value`
- Backend (`src:mkobi/api/routes/data.py:52`): `filters: str | None = Query(..., description="JSON string with filters")` — expects a JSON string
- Backend (`src:mkobi/api/routes/data.py:107`): `parsed_filters = json.loads(filters)` will throw `JSONDecodeError` on non-string input

**Impact:** Filters will never work correctly. Any attempt to filter data will result in a 400 validation error.

**Recommendation:** Change frontend to stringify filters:
```typescript
params: {
  dashboard_id,
  graph_id,
  filters: filters ? JSON.stringify(filters) : undefined
}
```

---

## Validated Advisory Recommendations

### INT-002 — SPEC-DEVIATION (CONFIRMED)

| Field | Value |
|-------|-------|
| **Status** | **CONFIRMED — advisory** |

`DashboardRead.permission` is injected by the service layer (`dashboard_service.get_dashboard()`). The model cannot be constructed directly from ORM via `model_validate()`. This is a deliberate architectural pattern but lacks documentation.

### INT-004 — SPEC-DEVIATION (CONFIRMED)

| Field | Value |
|-------|-------|
| **Status** | **CONFIRMED — advisory** |

Backend (`src:mkobi/models/data.py:98`): `error_code: str | None = None`
Frontend (`frontend:src/shared/types/api.types.ts:207`): `error_code?: ErrorCode | null`

The frontend type uses `ErrorCode` which is a const object, accepting any string at runtime. This is acceptable but could be tightened for type safety.

### INT-006 — BEST-PRACTICE (CONFIRMED)

| Field | Value |
|-------|-------|
| **Status** | **CONFIRMED — advisory** |

`logout()` frontend returns `void` while backend returns `SuccessResponse` with body. Semantic inconsistency but functional.

### INT-007 — SPEC-DEVIATION (CONFIRMED)

| Field | Value |
|-------|-------|
| **Status** | **CONFIRMED — advisory** |

`register_request` endpoint has no `response_model=RegistrationResponse`. This is a valid contract gap.

### INT-008 — BEST-PRACTICE (CONFIRMED)

| Field | Value |
|-------|-------|
| **Status** | **CONFIRMED — advisory** |

`change_password` endpoint returns raw dict without response model. Consistent pattern issue.

### INT-009 — BEST-PRACTICE (CONFIRMED)

| Field | Value |
|-------|-------|
| **Status** | **CONFIRMED — advisory** |

`reject-request` endpoint has no response model. Advisory.

### INT-010 — SPEC-DEVIATION (CONFIRMED)

| Field | Value |
|-------|-------|
| **Status** | **CONFIRMED — advisory** |

Backend returns `DashboardRead` (full shape) but frontend `updateDashboard()` expects `DashboardAdmin` (partial shape). The frontend receives extra fields it doesn't use in its type. This is a type narrowing issue.

### INT-012 — SPEC-DEVIATION (CONFIRMED)

| Field | Value |
|-------|-------|
| **Status** | **CONFIRMED — advisory** |

Backend `GraphDataResponse.layout: ChartLayoutConfig | None` vs frontend `GraphDataWithConfig.layout?: Layout` from `react-plotly.js`. Different types that may cause runtime issues if passed directly to Plotly.

### INT-013 — BEST-PRACTICE (CONFIRMED)

| Field | Value |
|-------|-------|
| **Status** | **CONFIRMED — advisory** |

Minor null vs undefined semantic mismatch. Backend `str | None` vs frontend `string | undefined`.

### INT-014 — BEST-PRACTICE (CONFIRMED)

| Field | Value |
|-------|-------|
| **Status** | **CONFIRMED — advisory** |

`204 No Content` response is standard, no fix required. Documented correctly.

### INT-015 — SPEC-DEVIATION (CONFIRMED)

| Field | Value |
|-------|-------|
| **Status** | **CONFIRMED — advisory** |

`LayoutRead.created_at: datetime | None = None` while DB column is `nullable=False`. Misleading nullable type.

### INT-016 — SPEC-DEVIATION (CONFIRMED)

| Field | Value |
|-------|-------|
| **Status** | **CONFIRMED — advisory** |

`UserRead.created_at: datetime | None = None` while DB is non-nullable. Same issue as INT-015.

### INT-017 — SPEC-DEVIATION (CONFIRMED)

| Field | Value |
|-------|-------|
| **Status** | **CONFIRMED — advisory** |

`UserRead` missing `updated_at` field that exists in DB. Valid omission if intentional, but undocumented.

### INT-018 — BEST-PRACTICE (CONFIRMED)

| Field | Value |
|-------|-------|
| **Status** | **CONFIRMED — advisory** |

`Dashboard.created_by` stored but not exposed in any read model. Valid if intentional, documented as advisory.

### INT-019 — BEST-PRACTICE (CONFIRMED)

| Field | Value |
|-------|-------|
| **Status** | **CONFIRMED — advisory** |

`refreshToken()` sends misleading empty body `{}`. The backend reads from cookies, not the body. Should be `post<Token>('/auth/refresh')`.

### INT-020 — BEST-PRACTICE (CONFIRMED)

| Field | Value |
|-------|-------|
| **Status** | **CONFIRMED — advisory** |

Two role update endpoints exist:
- `PUT /users/{user_id}` (users.py:184-243)
- `PATCH /admin/users/{user_id}/role` (admin.py:61-96)

Both perform the same operation with same permission check. Frontend uses the admin endpoint. The `/users/{user_id}` endpoint is redundant and creates maintenance overhead.

---

## Cross-Phase Conflicts

None detected — Integration phase findings do not conflict with other audit phases.

---

## Rollout Safety

The validated mandatory fix (INT-011) requires frontend-only changes. No backend modification needed. Low rollout risk:
- Change is isolated to `dashboardApi.ts`
- Backward compatible: if filters is undefined, behavior unchanged
- No database migration required

---

## Summary

| Category | Count |
|----------|-------|
| **Rejected findings** | 3 |
| **Mandatory fixes validated** | 1 |
| **Advisory recommendations validated** | 14 |

Rejected findings (3): INT-001, INT-003, INT-005 — all were based on incorrect code inspection.

---

## Actionable Recommendations

### INT-002 — Document `DashboardRead.permission` Service-Layer Injection Pattern

**Files to change:**
- `src/mkobi/models/dashboard.py` (DashboardRead class docstring)
- `src/mkobi/services/dashboard_service.py` (`_dashboard_to_read` method docstring)

**Change:**

Add a docstring to `DashboardRead` explaining that `permission` is not a DB column — it is injected at runtime by the service layer:

```python
class DashboardRead(BaseModel):
    """Model for reading dashboard data.

    Note:
        The ``permission`` field is NOT a database column. It is injected
        by ``DashboardService._dashboard_to_read()`` based on the requesting
        user's access level (via the ``dashboard_access`` table). This model
        cannot be constructed directly from ORM via ``model_validate()`` without
        providing ``permission`` explicitly.
    """
```

Update `_dashboard_to_read` docstring:

```python
async def _dashboard_to_read(
    self,
    dashboard_obj: dashboard_model.Dashboard,
    db: AsyncSession,
    permission: DashboardPermission | None = None,
) -> DashboardRead:
    """Convert dashboard ORM object to Pydantic DashboardRead model.

    Injects the ``permission`` field from the access control system
    (not from the DB column — dashboards table has no permission column).
    """
```

**Why this approach:** The pattern is deliberate and correct — `permission` is a computed field from the access control layer, not a persisted column. The only risk is future developers attempting `DashboardRead.model_validate(orm_obj)` and wondering why it fails. A docstring is the lightest-weight fix that prevents confusion without changing runtime behavior. Alternatives considered: (1) making `permission` optional with a default — rejected because it would weaken the contract that every dashboard response carries a permission; (2) a separate architecture decision record — overkill for a single-model pattern already established across `DashboardSummary` and `DashboardRead`.

---

### INT-004 — Tighten Frontend `error_code` Type to `ErrorCode` Union

**File to change:**
- `src/mkobi/models/data.py` — `ProcessingStatusResponse.error_code`
- `frontend/src/shared/types/api.types.ts` — `ProcessingStatusResponse.error_code` and `ProcessingLog.error_code`

**Change 1 (backend):** Constrain `error_code` to the `ErrorCode` enum instead of bare `str`:

```python
# In src/mkobi/models/data.py, ProcessingStatusResponse:
from mkobi.models.enums import ErrorCode

error_code: ErrorCode | None = None
```

**Change 2 (frontend):** The frontend type is already `ErrorCode | null`, which is correct. No change needed to `api.types.ts`. However, the `error_code` field should be made required-but-nullable (not optional) to match the backend's `= None` default:

```typescript
// In frontend/src/shared/types/api.types.ts, ProcessingStatusResponse:
error_code: ErrorCode | null  // was: error_code?: ErrorCode | null
```

Same change for `ProcessingLog.error_code`:

```typescript
error_code: ErrorCode | null  // was: error_code?: ErrorCode | null
```

**Why this approach:** The backend uses `str | None` which accepts any string at runtime, including invalid error codes. Tightening to `ErrorCode | None` gives Pydantic validation (rejects unknown codes in tests/docs generation) and makes the OpenAPI schema show the enum values. The frontend already uses the `ErrorCode` union type — the only issue was the `?` (optional) modifier which means `undefined` is also accepted. Making it required-but-nullable (`: ErrorCode | null`) matches the backend contract: the field is always present but may be `null`. Alternatives considered: (1) Using `Literal` types — rejected because the `ErrorCode` const object pattern already provides equivalent type safety with less duplication; (2) Removing the field when null — rejected because explicit null is better for frontend state management than absent keys.

---

### INT-006 — Align Frontend `logout()` Return Type with Backend `SuccessResponse`

**File to change:**
- `frontend/src/features/auth/api/authApi.ts`

**Change:**

```typescript
import type { SuccessResponse } from '../../../shared/types/api.types'

export async function logout(): Promise<SuccessResponse> {
  const response = await axiosInstance.post<SuccessResponse>('/auth/logout')
  return response.data
}
```

Add `SuccessResponse` to `api.types.ts` if not already present (it is already defined in `auth.py` backend model):

```typescript
// Add to frontend/src/shared/types/api.types.ts:
export interface SuccessResponse {
  message: string
}
```

**Why this approach:** The backend already declares `response_model=SuccessResponse` and returns `{"message": "Logged out successfully"}`. The frontend discards this response with `void`. By typing the return as `SuccessResponse`, callers can access the message for toast notifications or logging. This is a pure type-level fix — no runtime behavior changes. Alternatives considered: (1) Changing backend to return 204 No Content — rejected because the message is useful UX feedback and the endpoint already works correctly; (2) Keeping `void` — rejected because it wastes information the backend already sends.

---

### INT-007 — Add `response_model` to `register_request` Endpoint

**File to change:**
- `src/mkobi/api/routes/auth.py`

**Change:**

```python
from mkobi.models.auth import RegistrationRequestResponse

@router.post(
    "/register-request",
    response_model=RegistrationRequestResponse,  # ADD THIS
    status_code=status.HTTP_201_CREATED,
    summary="Registration request",
    description="Creates registration request. Admin must approve the request.",
)
```

Update the return statement to use the model instead of a raw dict:

```python
# Before:
return {"message": "Request submitted", "id": result["id"]}

# After:
return RegistrationRequestResponse(
    id=result["id"],
    email=request_data.email,
    status=RegistrationStatus.PENDING,
)
```

**Why this approach:** The endpoint currently returns a raw dict, which means FastAPI's OpenAPI schema shows the response as `{}` (empty schema) rather than the actual shape. Adding `response_model=RegistrationRequestResponse` documents the contract and enables proper OpenAPI generation. The `RegistrationRequestResponse` model already exists in `mkobi/models/auth.py` and has the correct fields. Alternatives considered: (1) Creating a new response model — rejected because `RegistrationRequestResponse` already exists and matches; (2) Using `response_model=dict` — rejected because it provides no schema documentation.

---

### INT-008 — Add `response_model=SuccessResponse` to `change_password` Endpoint

**File to change:**
- `src/mkobi/api/routes/auth.py`

**Change:**

```python
@router.post(
    "/change-password",
    response_model=SuccessResponse,  # ADD THIS
    status_code=status.HTTP_200_OK,
    summary="Change password",
    description="Change current user password. Requires current password verification.",
)
```

Update the return statement:

```python
# Before:
return {"message": "Password changed successfully"}

# After:
return SuccessResponse(message="Password changed successfully")
```

**Why this approach:** Consistent with the `logout` endpoint which already uses `response_model=SuccessResponse`. The `SuccessResponse` model already exists and is imported in the same file. This ensures the OpenAPI schema accurately reflects the response shape. Alternatives considered: (1) A dedicated `PasswordChangedResponse` — rejected as overengineering for a single-message response; (2) Returning `None` with 204 — rejected because the message is useful for frontend toast notifications.

---

### INT-009 — Add `response_model=SuccessResponse` to `reject-request` Endpoint

**File to change:**
- `src/mkobi/api/routes/admin.py`

**Change:**

```python
@router.post(
    "/registration-requests/{request_id}/reject",
    response_model=SuccessResponse,  # ADD THIS
    status_code=status.HTTP_200_OK,
    summary="Reject registration request (admin)",
    description="Rejects a registration request. Admin only.",
    dependencies=[Depends(require_admin_role)],
)
```

Update the return statement:

```python
# Before:
return {"message": "Registration request rejected"}

# After:
return SuccessResponse(message="Registration request rejected")
```

Add the import if not present:

```python
from mkobi.models.auth import SuccessResponse
```

**Why this approach:** Same rationale as INT-008. The `approve-request` endpoint already returns a structured dict with `message`, `user_id`, and `retrieval_token`. The `reject-request` endpoint should use the same `SuccessResponse` pattern for consistency. This is a pure contract documentation fix.

---

### INT-010 — Narrow `updateDashboard()` Frontend Return Type to `DashboardDetail`

**File to change:**
- `frontend/src/features/admin/api/adminApi.ts`

**Change:**

```typescript
// Before:
export async function updateDashboard(dashboardId: string, data: UpdateDashboardRequest): Promise<DashboardAdmin> {
  const response = await axiosInstance.put<DashboardAdmin>(`/dashboards/${dashboardId}`, data)
  return response.data
}

// After:
export async function updateDashboard(dashboardId: string, data: UpdateDashboardRequest): Promise<DashboardDetail> {
  const response = await axiosInstance.put<DashboardDetail>(`/dashboards/${dashboardId}`, data)
  return response.data
}
```

**Why this approach:** The backend `PUT /dashboards/{dashboard_id}` endpoint declares `response_model=DashboardRead`, which returns the full dashboard shape (id, name, description, config, permission, layout_id, layout, created_at, updated_at). The frontend was typing the response as `DashboardAdmin` (which only has id, name, description, created_at, updated_at — no config, permission, or layout). This means any code relying on `config` or `permission` from the update response would silently get `undefined` at runtime. `DashboardDetail` matches the backend's `DashboardRead` shape exactly. Alternatives considered: (1) Creating a separate `DashboardUpdateResponse` type — rejected because `DashboardDetail` already matches perfectly; (2) Changing the backend to return `DashboardAdmin` — rejected because the update endpoint needs to return the full config so the frontend can refresh its state.

---

### INT-012 — Align Frontend `GraphDataWithConfig.layout` Type with Backend `ChartLayoutConfig`

**File to change:**
- `frontend/src/shared/types/api.types.ts`

**Change:**

Replace the `layout` field in `GraphDataWithConfig` to use a concrete type instead of Plotly's `Layout`:

```typescript
// Before:
import type { Data, Layout } from 'react-plotly.js'

export interface GraphDataWithConfig {
  graph_id: string
  type: GraphType
  name: string
  data: Data[]
  layout?: Layout
  config?: {
    x?: string
    color?: string
    metrics?: string[]
    orientation?: string
    barmode?: string
  }
}

// After:
import type { Data } from 'react-plotly.js'

export interface ChartLayoutConfig {
  title?: string
  xaxis?: {
    title?: string
    label?: string
    range?: number[]
    type?: string
  }
  yaxis?: {
    title?: string
    label?: string
    range?: number[]
    type?: string
  }
  showlegend?: boolean
  height?: number
  width?: number
  template?: string
}

export interface GraphDataWithConfig {
  graph_id: string
  type: GraphType
  name: string
  data: Data[]
  layout?: ChartLayoutConfig
  config?: {
    x?: string
    color?: string
    metrics?: string[]
    orientation?: string
    barmode?: string
  }
}
```

**Why this approach:** The backend sends `ChartLayoutConfig` (a TypedDict with specific fields: title, xaxis, yaxis, showlegend, height, width, template). The frontend was typing this as Plotly's `Layout` class, which is a much larger type with dozens of additional fields. At runtime, the backend only sends the `ChartLayoutConfig` subset, so the Plotly `Layout` type creates false expectations. By defining `ChartLayoutConfig` explicitly, the frontend type matches exactly what the backend sends. The `data` field correctly uses Plotly's `Data[]` since that's what Plotly.js consumes. Alternatives considered: (1) Using `Partial<Layout>` — rejected because it still implies fields that will never arrive; (2) A runtime conversion/mapping layer — rejected as overengineering since the backend's `ChartLayoutConfig` is already a valid Plotly layout subset.

---

### INT-013 — Normalize Null/Undefined Handling with Type Guard Utility

**File to change:**
- `frontend/src/shared/types/api.types.ts` (add type guard)
- Or create a new file: `frontend/src/shared/utils/typeGuards.ts`

**Change:**

Create a utility module for null/normalization:

```typescript
// frontend/src/shared/utils/typeGuards.ts

/**
 * Normalize a backend nullable field to undefined.
 * Backend sends `null` for optional fields; frontend prefers `undefined`.
 */
export function normalizeNullable<T>(value: T | null): T | undefined {
  return value === null ? undefined : value
}

/**
 * Normalize an entire object's nullable fields from null to undefined.
 * Use in API response mapping to align backend null with frontend undefined semantics.
 */
export function normalizeNullFields<T extends Record<string, unknown>>(
  obj: T
): { [K in keyof T]: T[K] extends null | infer U ? U | undefined : T[K] } {
  const result = { ...obj }
  for (const key of Object.keys(result) as Array<keyof T>) {
    if (result[key] === null) {
      result[key] = undefined as T[keyof T]
    }
  }
  return result as { [K in keyof T]: T[K] extends null | infer U ? U | undefined : T[K] }
}
```

Apply normalization in API functions where null/undefined mismatch matters (e.g., `description` fields):

```typescript
// Example in dashboardApi.ts:
export const dashboardApi = {
  getDashboard: async (id: string): Promise<DashboardDetail> => {
    const response = await axiosInstance.get<DashboardDetail>(`/dashboards/${id}`)
    return {
      ...response.data,
      description: normalizeNullable(response.data.description),
      layout: response.data.layout ? normalizeNullFields(response.data.layout) : null,
    }
  },
}
```

**Why this approach:** The null vs undefined mismatch is systemic — every backend `str | None` field serializes as `null` in JSON, but the frontend types use `string | undefined`. Rather than fixing each field individually (fragile, easy to miss), a utility function provides a consistent pattern. The normalization is applied at the API boundary (in API functions), keeping the rest of the codebase clean. Alternatives considered: (1) Changing all frontend types to `| null` — rejected because it would require null-checking throughout the component tree, which is worse than the current undefined-checking pattern; (2) Changing backend to omit null fields — rejected because it changes the API contract and breaks the explicit "field is present but null" semantics; (3) Ignoring the issue — rejected because it causes subtle bugs with `if (field)` checks that treat `null` and `undefined` differently in some edge cases.

---

### INT-015 — Fix `LayoutRead.created_at` Nullable Type to Match DB

**File to change:**
- `src/mkobi/models/layout.py`

**Change:**

```python
# Before:
class LayoutRead(LayoutBase):
    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None

# After:
class LayoutRead(LayoutBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
```

**Why this approach:** The `layouts` table defines `created_at` and `updated_at` as `nullable=False` with `server_default=text("now()")`. These columns are always populated — they can never be null. The `| None = None` type was copy-pasted from a pattern used for actually nullable columns. Removing it tightens the contract: any code constructing a `LayoutRead` must provide these fields, which is correct since the DB always provides them. The OpenAPI schema will show these as required fields, which is accurate. No migration needed — this is a pure model-level fix.

---

### INT-016 — Fix `UserRead.created_at` Nullable Type to Match DB

**File to change:**
- `src/mkobi/models/user.py`

**Change:**

```python
# Before:
class UserRead(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime | None = None
    force_password_change: bool = False

# After:
class UserRead(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime
    force_password_change: bool = False
```

**Why this approach:** Same as INT-015. The `users` table has `created_at` as `nullable=False` with `server_default=text("now()")`. The type should be `datetime`, not `datetime | None`. This is a pure model-level fix with no migration needed.

---

### INT-017 — Add `updated_at` to `UserRead` Model

**File to change:**
- `src/mkobi/models/user.py`

**Change:**

```python
# Before:
class UserRead(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime
    force_password_change: bool = False

# After:
class UserRead(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    force_password_change: bool = False
```

Update the `json_schema_extra` example to include `updated_at`:

```python
model_config = ConfigDict(
    from_attributes=True,
    json_schema_extra={
        "example": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "user@example.com",
            "role": UserRole.VIEWER,
            "created_at": "2026-04-24T16:02:46+03:00",
            "updated_at": "2026-04-24T16:02:46+03:00",
        }
    },
)
```

**Why this approach:** The `users` table has an `updated_at` column (`nullable=False`, `server_default=text("now()")`) but `UserRead` omits it. This means the field is silently dropped when constructing `UserRead` from ORM via `model_validate()`. Since `UserRead` has `from_attributes=True`, SQLAlchemy will provide `updated_at` during validation, but Pydantic will ignore it because the field isn't declared. Adding it to the model exposes it in the API response, which is needed for admin user management (showing when a user was last updated). The `updated_at` field is already present in `UserDB` and the ORM model, so this is purely a Pydantic model addition. No migration needed.

---

### INT-018 — Expose `created_by` in `DashboardRead` Model

**File to change:**
- `src/mkobi/models/dashboard.py`

**Change:**

```python
# Before:
class DashboardRead(BaseModel):
    id: UUID
    name: str
    description: str | None
    config: DashboardConfig
    permission: DashboardPermission
    layout_id: UUID | None = None
    layout: LayoutRead | None = None
    created_at: datetime
    updated_at: datetime

# After:
class DashboardRead(BaseModel):
    id: UUID
    name: str
    description: str | None
    config: DashboardConfig
    permission: DashboardPermission
    layout_id: UUID | None = None
    layout: LayoutRead | None = None
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime
```

Update `_dashboard_to_read` in `dashboard_service.py` to pass `created_by`:

```python
# In the dashboard_dict construction:
dashboard_dict = {
    "id": dashboard_obj.id,
    "name": dashboard_obj.name,
    "description": dashboard_obj.description,
    "config": config,
    "permission": perm_value,
    "layout_id": dashboard_obj.layout_id,
    "created_by": dashboard_obj.created_by,
    "created_at": dashboard_obj.created_at,
    "updated_at": dashboard_obj.updated_at,
}
```

**Why this approach:** The `dashboards` table has a `created_by` column (FK to users) but it's not exposed in any API response. Admin interfaces need this to show who created a dashboard. The ORM model already loads this column (it's a simple `mapped_column`, not a relationship), so there's no performance cost. The field is nullable in the DB (`nullable=True`) to handle dashboards created during seeding/migration, so the Pydantic type is `UUID | None`. No migration needed — the column already exists.

---

### INT-019 — Remove Misleading Empty Body from `refreshToken()` API Call

**File to change:**
- `frontend/src/features/auth/api/authApi.ts`

**Change:**

```typescript
// Before:
export async function refreshToken(): Promise<Token> {
  const response = await axiosInstance.post<Token>('/auth/refresh', {})
  return response.data
}

// After:
export async function refreshToken(): Promise<Token> {
  const response = await axiosInstance.post<Token>('/auth/refresh')
  return response.data
}
```

**Why this approach:** The backend `POST /auth/refresh` endpoint reads the refresh token from an httpOnly cookie (`request.cookies.get(COOKIE_NAME)`), not from the request body. Sending `{}` as the body is misleading — it implies the body is processed, and Axios serializes `{}` as `Content-Type: application/json` with body `{}`, which some backend frameworks may try to parse. Omitting the body argument entirely makes the intent clear: this POST sends no body, the cookie carries the token. The `withCredentials: true` in `axiosInstance` ensures the cookie is sent. This is a one-character fix (removing `, {}`) with no downstream impact.

---

### INT-020 — Deprecate Redundant `PUT /users/{user_id}` Role Update Path

**Files to change:**
- `src/mkobi/api/routes/users.py` (mark endpoint as deprecated)

**Change:**

```python
@router.put(
    "/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Update user role [DEPRECATED]",
    description="Deprecated: Use PATCH /admin/users/{user_id}/role instead. "
                "This endpoint is retained for backward compatibility.",
    dependencies=[Depends(require_admin_role)],
    deprecated=True,  # FastAPI/OpenAPI deprecated flag
)
async def update_user_endpoint(
    user_id: UUID,
    user_data: UserUpdateRequest,
    user_service: UserService = Depends(get_user_service),
    db: AsyncSession = Depends(get_db_dependency),
) -> UserRead:
    """Update user role.

    .. deprecated:: current
        Use :func:`update_user_role_admin_endpoint` (``PATCH /admin/users/{user_id}/role``) instead.
    """
```

**Why this approach:** Both `PUT /users/{user_id}` and `PATCH /admin/users/{user_id}/role` perform the identical operation (update user role, admin-only, same permission check, same service call). The frontend already uses the admin endpoint. Rather than deleting the users.py endpoint (which could break unknown consumers), marking it as `deprecated=True` in FastAPI adds `"deprecated": true` to the OpenAPI schema, which code generators and API documentation tools will surface. The docstring update provides migration guidance. Alternatives considered: (1) Deleting the endpoint — rejected because it could break API consumers that aren't the frontend (scripts, third-party integrations); (2) Adding a redirect — rejected because PUT-to-PATCH redirects are non-standard; (3) Merging into a single endpoint — rejected because it would require choosing one URL pattern over the other, breaking existing consumers.