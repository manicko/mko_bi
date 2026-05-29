# Phase 09 Audit Findings — Integration

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### INT-001: ProcessingStatusResponse schema mismatch between frontend and backend

| Field | Value |
|-------|-------|
| **ID** | INT-001 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/shared/types/api.types.ts`, `src/mkobi/models/data.py` |
| **Classification** | advisory |

**Description:** The frontend `ProcessingStatusResponse` interface (lines 171-176 in `api.types.ts`) references only `status`, `message`, `started_at`, and `finished_at` fields, but the backend `ProcessingStatusResponse` Pydantic model (lines 82-108 in `models/data.py`) returns `task_id`, `filename`, `dashboard_id`, `progress`, `started_at`, and `completed_at` (note: `completed_at` vs `finished_at`). The backend response shape has more fields than frontend expects.

**Evidence:**
- Frontend: `frontend/src/shared/types/api.types.ts` lines 171-176
- Backend: `src/mkobi/models/data.py` lines 82-108 (includes `task_id`, `filename`, `dashboard_id`, `progress` - not in frontend)

**Recommendation:** Update frontend `ProcessingStatusResponse` to match backend response shape. Add `task_id`, `filename`, `dashboard_id`, and `progress` fields. Consider renaming `finished_at` to `completed_at` for consistency with backend.

---

### INT-002: UploadResponse ID field naming inconsistency

| Field | Value |
|-------|-------|
| **ID** | INT-002 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/shared/types/api.types.ts`, `src/mkobi/models/data.py` |
| **Classification** | advisory |

**Description:** Frontend `UploadResponse` has a `processing_log_id` field (line 67 in `api.types.ts`) while the backend uses `task_id` in the `UploadResponse` model (line 60 in `models/data.py`). The route returns `processing_log_id: result.task_id` which creates semantic confusion about what the ID represents.

**Evidence:**
- Frontend: `frontend/src/shared/types/api.types.ts` lines 59-68
- Backend: `src/mkobi/models/data.py` lines 57-79 (has `task_id`, `status`, `message`, `uploaded_at`)
- Backend route: `src/mkobi/api/routes/upload.py` line 186 (returns `processing_log_id: result.task_id`)

**Recommendation:** Use consistent field naming - use `task_id` in both frontend and backend to represent the processing log UUID.

---

### INT-003: Frontend DashboardConfig incompatible with backend DashboardConfig

| Field | Value |
|-------|-------|
| **ID** | INT-003 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/shared/types/api.types.ts`, `src/mkobi/models/dashboard.py` |
| **Classification** | mandatory |

**Description:** The frontend `DashboardConfig` interface (lines 70-75 in `api.types.ts`) has `layout`, `graphs`, `filters`, and `bindings` fields, while the backend `DashboardConfig` model (lines 12-18 in `models/dashboard.py`) has `graph_types`, `filters`, `aggregations`, `charts`, `title`, and `description`. These structures are fundamentally incompatible, which would cause UI rendering issues when dashboard data is fetched.

**Evidence:**
- Frontend: `frontend/src/shared/types/api.types.ts` lines 70-75
- Backend: `src/mkobi/models/dashboard.py` lines 12-18
- ORM model uses `config JSONB` field: `src/mkobi/db/models/dashboard.py` line 51

**Recommendation:** Reconcile `DashboardConfig` structures. The frontend appears to expect a different structure than what the backend provides. Either transform data at the API layer or update frontend types to match backend's `graph_types` and `charts` fields.

---

### INT-004: Token refresh API response type naming

| Field | Value |
|-------|-------|
| **ID** | INT-004 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/features/auth/api/authApi.ts`, `frontend/src/shared/types/api.types.ts` |
| **Classification** | advisory |

**Description:** The frontend `refreshToken` function returns `Promise<Token>` (line 12 in `authApi.ts`) using the `Token` type from `api.types.ts`. The implementation is correct but the type naming could be more descriptive as `RefreshTokenResponse` to distinguish from other token-related types.

**Evidence:**
- Frontend API: `frontend/src/features/auth/api/authApi.ts` line 12
- Frontend types: `frontend/src/shared/types/api.types.ts` lines 34-37

**Recommendation:** Consider renaming `Token` type to `RefreshTokenResponse` for clarity, though this is a minor naming improvement.

---

### INT-005: Concurrent 401 handling missing request timeout in axios interceptor

| Field | Value |
|-------|-------|
| **ID** | INT-005 |
| **Severity** | LOW |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `frontend/src/shared/api/axiosInstance.ts` |
| **Classification** | advisory |

**Description:** The axios interceptor's concurrent 401 handling implementation (lines 30-77 in `axiosInstance.ts`) uses a queue pattern but the Promise resolution flow could be improved. When multiple requests get 401 simultaneously, only one triggers refresh while others queue. The queued requests resolve correctly after `processQueue` is called, but the implementation could benefit from timeout handling.

**Evidence:**
- Frontend interceptor: `frontend/src/shared/api/axiosInstance.ts` lines 30-77

**Recommendation:** Add request timeout handling for queued requests to prevent indefinite waiting if refresh fails. The current implementation is functional but not robust against edge cases.

---

### INT-006: AggregatedDataResponse response shape mismatch

| Field | Value |
|-------|-------|
| **ID** | INT-006 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/shared/types/api.types.ts`, `src/mkobi/api/routes/data.py` |
| **Classification** | mandatory |

**Description:** The frontend `AggregatedDataResponse` interface (lines 156-158 in `api.types.ts`) expects `graphs: GraphDataWithConfig[]` containing `type` and `name` fields, but the backend `/data/aggregated` endpoint (line 119 in `data.py`) returns `{"graphs": [{"graph_id": "...", "data": result}]}` - missing `type` and `name` fields. The frontend DashboardView component (line 140-146) accesses `graph.name` and `graph.type` which won't exist in the response.

**Evidence:**
- Frontend: `frontend/src/shared/types/api.types.ts` lines 156-166
- Backend: `src/mkobi/api/routes/data.py` line 119
- Frontend usage: `frontend/src/features/dashboards/ui/DashboardView.tsx` lines 140-146

**Recommendation:** Either: (1) update backend to return full graph metadata including `type` and `name`, or (2) modify frontend to not require these fields for data display.

---

### INT-007: AccessGrant vs GrantAccessRequest field mismatch

| Field | Value |
|-------|-------|
| **ID** | INT-007 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/shared/types/api.types.ts`, `src/mkobi/models/access.py`, `src/mkobi/api/routes/dashboards_access.py` |
| **Classification** | mandatory |

**Description:** Frontend `GrantAccessRequest` (lines 237-239 in `api.types.ts`) has `user_id` and `permission` fields, but backend `AccessGrant` model (lines 25-40 in `access.py`) uses `permission_level` instead of `permission`. This mismatch will cause the access grant request to fail with 422 validation error.

**Evidence:**
- Frontend: `frontend/src/shared/types/api.types.ts` lines 237-239
- Backend: `src/mkobi/models/access.py` lines 25-40 (`permission_level` vs `permission`)
- Frontend API call: `frontend/src/features/admin/api/adminApi.ts` lines 83-85

**Recommendation:** Either change frontend to send `permission_level` instead of `permission`, or add field alias in backend's `AccessGrant` model.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 2 |
| LOW | 3 |

## Mandatory Fixes

- INT-003: Frontend DashboardConfig incompatible with backend DashboardConfig
- INT-006: AggregatedDataResponse response shape mismatch (missing graph metadata)
- INT-007: AccessGrant vs GrantAccessRequest field mismatch (`permission` vs `permission_level`)

## Advisory Recommendations

- INT-001: ProcessingStatusResponse schema mismatch between frontend and backend
- INT-002: UploadResponse ID field naming inconsistency
- INT-004: Token refresh API response type naming improvement
- INT-005: Add request timeout handling for queued requests in axios interceptor

## Doc Updates Needed

- INT-003: DashboardConfig schema needs unified definition
- INT-006: Aggregated data endpoint response format needs documentation
- INT-007: AccessGrant model field names should be documented for API contract