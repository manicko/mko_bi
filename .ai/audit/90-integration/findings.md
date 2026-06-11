# Phase 09 Audit Findings — Integration

**Executor:** auditor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** yes

---

## Findings

### INT-001: Frontend UploadResponse.status Type Uses string Instead of ProcessingStatus Enum

| Field | Value |
|-------|-------|
| **ID** | INT-001 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | frontend/src/shared/types/api.types.ts:91, frontend/src/shared/types/enums.ts:64 |
| **Classification** | advisory |

**Description:** The frontend `UploadResponse.status` is typed as `string` (line 91) but the backend returns `ProcessingStatus` enum. The frontend already has `ProcessingStatus` type defined (line 1 imports it, lines 201 and 288 use it), but `UploadResponse.status` was missed. While FastAPI serializes enums to strings automatically, using the proper enum type improves type safety and ensures compile-time validation.

**Evidence:**
- `frontend/src/shared/types/api.types.ts:91` — `status: string` in UploadResponse
- `frontend/src/shared/types/api.types.ts:201` — `status: ProcessingStatus` in ProcessingStatusResponse (correct)
- `frontend/src/shared/types/api.types.ts:288` — `status: ProcessingStatus` in ProcessingLog (correct)
- `src/mkobi/models/data.py:67` — `status: ProcessingStatus` in UploadResponse
- `src/mkobi/models/enums.py:58-66` — ProcessingStatus enum values: STARTED, UPLOADED, PROCESSING, COMPLETED, FAILED

**Recommendation:** Change frontend `UploadResponse.status` from `string` to `ProcessingStatus` to match backend enum and other frontend interfaces.

---

### INT-002: Frontend Type Could Be More Explicit for RegistrationRequestItem.reviewed_by

| Field | Value |
|-------|-------|
| **ID** | INT-002 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | frontend/src/shared/types/api.types.ts:240, src/mkobi/models/auth.py:68 |
| **Classification** | advisory |

**Description:** Frontend type `RegistrationRequestItem.reviewed_by` is declared as `string` (optional), but backend model field is `UUID | None`. When the backend serializes a UUID object, it becomes a string in JSON. The type is functionally correct but could be more explicit about UUID string format.

**Evidence:**
- `frontend/src/shared/types/api.types.ts:240` — `reviewed_by?: string`
- `src/mkobi/models/auth.py:68` — `reviewed_by: UUID | None = None`

**Recommendation:** No functional change needed. Consider adding JSDoc comment: `// UUID as string` for clarity.

---

### INT-003: Missing Frontend Types for Graph CRUD Operations

| Field | Value |
|-------|-------|
| **ID** | INT-003 |
| **Severity** | LOW |
| **Type** | DOC-UPDATE |
| **Affected Modules** | frontend/src/shared/types/api.types.ts, src/mkobi/models/graph.py |
| **Classification** | advisory |

**Description:** The frontend does not have dedicated types for Graph CRUD operations, even though the backend exposes `/api/v1/graphs/` endpoints. The backend has GraphRead, GraphCreate, and GraphUpdate models but frontend only has GraphDataWithConfig for aggregated data responses.

**Evidence:**
- Backend routes: `GET /api/v1/graphs/`, `POST /api/v1/graphs/`, `GET /api/v1/graphs/{graph_id}`, `PUT /api/v1/graphs/{graph_id}`, `DELETE /api/v1/graphs/{graph_id}`
- No frontend API functions call these endpoints (searched — no `getGraphs`, `createGraph`, etc.)

**Recommendation:** Add GraphRead, GraphCreate, GraphUpdate types to api.types.ts if graph management UI is planned.

---

### INT-004: Frontend adminApi Spreads Redundant dashboard_id in grantDashboardAccess

| Field | Value |
|-------|-------|
| **ID** | INT-004 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | frontend/src/features/admin/api/adminApi.ts:125-130 |
| **Classification** | advisory |

**Description:** The frontend `grantDashboardAccess` function spreads `data` (which includes `dashboard_id: string`) and then explicitly adds `dashboard_id: dashboardId` to the request body. This creates redundant code since `dashboard_id` is already in the spread `GrantAccessRequest` object.

**Evidence:**
- `frontend/src/features/admin/api/adminApi.ts:125-130`:
```typescript
await axiosInstance.post(`/dashboards/${dashboardId}/access`, {
  ...data,
  dashboard_id: dashboardId,
})
```
- `frontend/src/shared/types/api.types.ts:272-276` — `GrantAccessRequest` already has `dashboard_id: string`

**Recommendation:** Remove the redundant `dashboard_id: dashboardId` assignment since `data` already contains it.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 1 |
| LOW | 2 |

## Mandatory Fixes

None identified — all findings are advisory.

## Advisory Recommendations

- INT-001: Update UploadResponse.status type from string to ProcessingStatus
- INT-002: Add documentation comment to reviewed_by field for UUID clarity
- INT-003: Add Graph CRUD types if graph management UI is planned
- INT-004: Remove redundant dashboard_id assignment in grantDashboardAccess

## Doc Updates Needed

- INT-003: Document Graph API endpoints availability in frontend types

---

## Detailed Route-by-Route Comparison

| Backend Route | Frontend Call | Status |
|---------------|---------------|--------|
| `/api/v1/auth/login` | `authApi.ts:login()` POST | ✗ Match |
| `/api/v1/auth/login/form` | Not used | ✗ Unused |
| `/api/v1/auth/register` | Not used (admin only) | ✗ Unused |
| `/api/v1/auth/refresh` | `authApi.ts:refreshToken()` POST | ✗ Match |
| `/api/v1/auth/me` | `authApi.ts:getProfile()` GET | ✗ Match |
| `/api/v1/auth/logout` | `authApi.ts:logout()` POST | ✗ Match |
| `/api/v1/auth/register-request` | `authApi.ts:registerRequest()` POST | ✗ Match |
| `/api/v1/users/` (POST) | `adminApi.ts:createUser()` POST | ✗ Match |
| `/api/v1/users/` (GET) | `adminApi.ts:getUsers()` GET | ✗ Match |
| `/api/v1/users/{user_id}/role` | `adminApi.ts:changeUserRole()` PATCH | ✗ Match |
| `/api/v1/users/{user_id}` | `adminApi.ts:deleteUser()` DELETE | ✗ Match |
| `/api/v1/dashboards/` | `adminApi.ts:getDashboardsAdmin()` GET | ✗ Match |
| `/api/v1/dashboards/` (POST) | `adminApi.ts:createDashboard()` POST | ✗ Match |
| `/api/v1/dashboards/{dashboard_id}` | `adminApi.ts:updateDashboard()`, `deleteDashboard()` | ✗ Match |
| `/api/v1/dashboards/my` | `dashboardApi.ts:getMyDashboards()` GET | ✗ Match |
| `/api/v1/dashboards/{dashboard_id}` | `dashboardApi.ts:getDashboard()` GET | ✗ Match |
| `/api/v1/dashboards/{dashboard_id}/access` | `adminApi.ts:grantDashboardAccess()` POST | ⚠ Redundant field |
| `/api/v1/upload/{dashboard_id}` | `uploadApi.ts:uploadFile()` POST | ✗ Match |
| `/api/v1/upload/status/{task_id}` | `uploadApi.ts:getProcessingStatus()` GET | ✗ Match |
| `/api/v1/data/aggregated` | `dashboardApi.ts:getAggregatedData()` GET | ✗ Match |
| `/api/v1/admin/logs/` | `adminApi.ts:getLogs()` GET | ✗ Match |
| `/api/v1/admin/users/{user_id}/reset-password` | `adminApi.ts:resetUserPassword()` POST | ✗ Match |
| `/api/v1/admin/registration-requests` | `adminApi.ts:getRegistrationRequests()` GET | ✗ Match |
| `/api/v1/admin/registration-requests/{request_id}/approve` | `adminApi.ts:approveRequest()` POST | ✗ Match |
| `/api/v1/admin/registration-requests/{request_id}/reject` | `adminApi.ts:rejectRequest()` POST | ✗ Match |
| `/api/v1/admin/temp-passwords/{retrieval_token}` | `adminApi.ts:retrieveTempPassword()` GET | ✗ Match |
| `/api/v1/layouts` | `adminApi.ts:getLayouts()` GET | ✗ Match |
| `/api/v1/graphs/` | Not called from frontend | ⚠ Unused |

Key: ✗ = Match, ⚠ = Issue, ✓ = No Issue