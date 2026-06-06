# Phase 09 Audit Findings — Integration

**Executor:** audit-executor
**Template:** .kilo/commands/audit/phases/90-audit-integration.md
**Status:** complete
**Validated:** no

---

## Findings

### INT-001: RegistrationResponse field name mismatch — backend `id` vs frontend `request_id`

| Field | Value |
|-------|-------|
| **ID** | INT-001 |
| **Severity** | CRITICAL |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/api/routes/auth.py`, `frontend/src/shared/types/api.types.ts`, `frontend/src/features/auth/api/authApi.ts` |
| **Classification** | mandatory |

**Description:** The backend `/auth/register-request` endpoint returns `{"message": "Request submitted", "id": result["id"]}` (field name `id`), but the frontend `RegistrationResponse` type declares `request_id: string`. The JSON key sent by the server is `"id"`, while the frontend expects `"request_id"`. Any frontend code reading `response.request_id` will receive `undefined` at runtime.

**Evidence:**
- Backend: `src/mkobi/api/routes/auth.py:566` — `return {"message": "Request submitted", "id": result["id"]}`
- Frontend type: `frontend/src/shared/types/api.types.ts:148-151` — `interface RegistrationResponse { message: string; request_id: string; }`
- Frontend API call: `frontend/src/features/auth/api/authApi.ts:16-18` — `axiosInstance.post<RegistrationResponse>('/auth/register-request', { email })`
- Test mock: `frontend/src/features/auth/model/__tests__/useAuth.test.tsx:266` — `request_id: 'req-123'` (perpetuates the mismatch)

**Recommendation:** Choose one field name and apply consistently. Either:
1. Change backend to return `request_id` instead of `id` (preferred — avoids breaking any frontend that might be reading it), or
2. Change frontend `RegistrationResponse.request_id` to `id`.

---

### INT-002: ProcessingResult type shape mismatch — frontend expects `status`, backend returns `success`

| Field | Value |
|-------|-------|
| **ID** | INT-002 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/models/data.py`, `frontend/src/shared/types/api.types.ts`, `frontend/src/features/upload/api/uploadApi.ts` |
| **Classification** | mandatory |

**Description:** The backend `ProcessingResult` model (used by `GET /upload/result/{task_id}`) has fields: `success: bool`, `task_id: UUID`, `dashboard_id: UUID`, `rows_processed: int`, `message: str`, `data: ProcessingResultData | None`. The frontend `ProcessingResult` type declares only: `rows_processed: number`, `status: ProcessingStatus`, `message?: string`. The frontend has a `status` field that doesn't exist in the backend model, and is missing `success`, `task_id`, `dashboard_id`, and `data` fields. At runtime, the frontend's `status` will be `undefined`, and `rows_processed` may work by coincidence, but the type contract is completely wrong.

**Evidence:**
- Backend model: `src/mkobi/models/data.py:156-178` — `class ProcessingResult(BaseModel): success: bool, task_id: UUID, dashboard_id: UUID, rows_processed: int, message: str, data: ProcessingResultData | None`
- Backend route: `src/mkobi/api/routes/upload.py:286-337` — `response_model=ProcessingResult`
- Frontend type: `frontend/src/shared/types/api.types.ts:200-204` — `interface ProcessingResult { rows_processed: number; status: ProcessingStatus; message?: string; }`
- Frontend API call: `frontend/src/features/upload/api/uploadApi.ts:38-40` — `axiosInstance.get<ProcessingResult>(\`/upload/result/${logId}\`)`

**Recommendation:** Align the frontend `ProcessingResult` type with the backend model. Add `success: boolean`, `task_id: string`, `dashboard_id: string`, and `data` fields. Replace `status` with the correct field or add a mapping if the backend response is transformed elsewhere.

---

### INT-003: DashboardDetail frontend type missing fields returned by backend DashboardRead

| Field | Value |
|-------|-------|
| **ID** | INT-003 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/shared/types/api.types.ts`, `src/mkobi/models/dashboard.py` |
| **Classification** | advisory |

**Description:** The frontend `DashboardDetail` type (used for `GET /dashboards/{id}` response) declares only: `id`, `name`, `description`, `config`, `permission`. The backend `DashboardRead` model additionally returns: `layout_id`, `layout` (full LayoutRead object), `created_at`, `updated_at`. The frontend silently discards these fields. This prevents the UI from displaying layout information, creation dates, or modification timestamps for individual dashboards.

**Evidence:**
- Frontend type: `frontend/src/shared/types/api.types.ts:153-159` — `interface DashboardDetail { id, name, description, config, permission }`
- Backend model: `src/mkobi/models/dashboard.py:92-127` — `class DashboardRead(BaseModel): id, name, description, config, permission, layout_id, layout, created_at, updated_at`
- API call: `frontend/src/features/dashboards/api/dashboardApi.ts:18-19` — `axiosInstance.get<DashboardDetail>(\`/dashboards/${id}\`)`

**Recommendation:** Add `layout_id?: string | null`, `layout?: LayoutRead | null`, `created_at: string`, `updated_at: string` to the frontend `DashboardDetail` interface, or create a client-side type that accurately represents what the server returns.

---

### INT-004: GraphDataWithConfig.data typed as Plotly Data[] but backend sends raw dicts

| Field | Value |
|-------|-------|
| **ID** | INT-004 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/shared/types/api.types.ts`, `src/mkobi/models/data.py`, `src/mkobi/api/routes/data.py` |
| **Classification** | advisory |

**Description:** The `GraphDataWithConfig.data` field is typed as `Data[]` from `react-plotly.js`, which is the Plotly trace format (objects with `x`, `y`, `type`, `mode`, etc.). However, the backend `GraphDataResponse.data` field contains `list[dict[str, int | float | str]]` — flat data point dictionaries like `{"category": "A", "revenue": 1000}`. The backend assembles these from `item["preview"]` arrays in `data.py:144-146,181-183`. The actual runtime data is NOT in Plotly format; it's transformed into Plotly traces on the frontend. The TypeScript type is misleading — it claims the data arrives as Plotly traces when it actually arrives as raw dicts.

**Evidence:**
- Frontend type: `frontend/src/shared/types/api.types.ts:171-184` — `interface GraphDataWithConfig { data: Data[]; layout?: Layout; config?: {...} }`
- Backend type: `src/mkobi/models/data.py:431` — `data: list[dict[str, int | float | str]]`
- Backend route: `src/mkobi/api/routes/data.py:144-146` — `single_data_points.extend(cast(list[dict[str, int | float | str]], item["preview"]))`

**Recommendation:** Change the frontend `GraphDataWithConfig.data` type from `Data[]` (Plotly traces) to `Record<string, unknown>[]` or a more specific type that matches the flat dict format actually sent by the server. Add a separate type for the Plotly-transformed data after client-side transformation.

---

### INT-005: GraphDataWithConfig.layout typed as Plotly Layout but backend sends ChartLayoutConfig

| Field | Value |
|-------|-------|
| **ID** | INT-005 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/shared/types/api.types.ts`, `src/mkobi/models/data.py` |
| **Classification** | advisory |

**Description:** The `GraphDataWithConfig.layout` field is typed as `Layout` from `react-plotly.js` (which has dozens of Plotly-specific properties like `xaxis`, `yaxis`, `annotations`, etc.). The backend `GraphDataResponse.layout` field has type `ChartLayoutConfig | None`, which is a much simpler structure defined in `src/mkobi/models/types.py`. The type mismatch misleads developers into thinking full Plotly layout configuration is received from the server.

**Evidence:**
- Frontend type: `frontend/src/shared/types/api.types.ts:176` — `layout?: Layout` (from `react-plotly.js`)
- Backend type: `src/mkobi/models/data.py:432` — `layout: ChartLayoutConfig | None = None`

**Recommendation:** Replace `Layout` from `react-plotly.js` with a type that matches the actual `ChartLayoutConfig` shape sent by the server, or use `Record<string, unknown>` if the shape is dynamic.

---

### INT-006: createDashboard return type mismatch — frontend expects DashboardAdmin, backend returns DashboardRead

| Field | Value |
|-------|-------|
| **ID** | INT-006 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/admin/api/adminApi.ts`, `src/mkobi/api/routes/dashboards_crud.py` |
| **Classification** | advisory |

**Description:** The `createDashboard` function in adminApi.ts declares return type `Promise<DashboardAdmin>`. However, the backend `POST /dashboards/` endpoint uses `response_model=DashboardRead`, which includes `config`, `permission`, `layout_id`, `layout`, `created_at`, `updated_at` — more fields than `DashboardAdmin` (which only has `id`, `name`, `description`, `created_at`, `updated_at`). The frontend receives extra fields but the type doesn't reflect them. While this doesn't cause runtime errors (TypeScript types are erased), it creates type inaccuracy and the admin panel cannot access `config` or `permission` of the newly-created dashboard without refetching.

**Evidence:**
- Frontend: `frontend/src/features/admin/api/adminApi.ts:105` — `async function createDashboard(data): Promise<DashboardAdmin>`
- Backend: `src/mkobi/api/routes/dashboards_crud.py:82-84` — `response_model=DashboardRead`

**Recommendation:** Either change the frontend `createDashboard` return type to `DashboardDetail` (which has `config` and `permission`), or adjust the backend endpoint to return `DashboardAdmin` if the extra fields aren't needed post-creation.

---

### INT-007: updateDashboard frontend type doesn't support backend config or layout_id updates

| Field | Value |
|-------|-------|
| **ID** | INT-007 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/admin/api/adminApi.ts`, `src/mkobi/models/dashboard.py` |
| **Classification** | advisory |

**Description:** The frontend `UpdateDashboardRequest` type only includes `name?: string` and `description?: string`. The backend `DashboardUpdate` model additionally accepts `config?: DashboardConfig` and `layout_id?: UUID`. The frontend admin panel cannot update dashboard configuration or layout association through the update API call, even though the backend supports it.

**Evidence:**
- Frontend type: `frontend/src/shared/types/api.types.ts:249-252` — `interface UpdateDashboardRequest { name?: string; description?: string; }`
- Backend model: `src/mkobi/models/dashboard.py:130-151` — `class DashboardUpdate: name, description, config, layout_id`

**Recommendation:** If the admin UI needs to update dashboard config or layout, extend `UpdateDashboardRequest` to include `config?: DashboardConfig` and `layout_id?: string`. If this is intentional UX limitation, document it explicitly.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 1 |
| HIGH | 1 |
| MEDIUM | 3 |
| LOW | 2 |

## Mandatory Fixes

- **INT-001**: RegistrationResponse field mismatch (`id` vs `request_id`) — will cause `undefined` at runtime when frontend reads `request_id` from a backend response that sends `id`
- **INT-002**: ProcessingResult type shape mismatch — frontend expects `status: ProcessingStatus` but backend sends `success: bool`; frontend missing `success`, `task_id`, `dashboard_id`, `data` fields

## Advisory Recommendations

- **INT-003**: DashboardDetail missing layout_id, layout, created_at, updated_at from backend DashboardRead
- **INT-004**: GraphDataWithConfig.data incorrectly typed as Plotly `Data[]` — backend sends raw dicts
- **INT-005**: GraphDataWithConfig.layout incorrectly typed as Plotly `Layout` — backend sends ChartLayoutConfig
- **INT-006**: createDashboard return type doesn't match backend response_model
- **INT-007**: UpdateDashboardRequest doesn't support config or layout_id updates that the backend accepts

## Doc Updates Needed

None in this phase.

---
