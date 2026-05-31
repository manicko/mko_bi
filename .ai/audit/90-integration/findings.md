# Phase 09 Audit Findings — Integration

**Executor:** audit-executor  
**Template:** `.ai/audit/templates/audit-findings.md`  
**Status:** complete  
**Validated:** no  

---

## Findings

### INT-001: API Contract Mismatch - `/data/aggregated` Missing Required `graph_id` Parameter

| Field | Value |
|-------|-------|
| **ID** | INT-001 |
| **Severity** | CRITICAL |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/api/routes/data.py`, `frontend/src/features/dashboards/api/dashboardApi.ts` |
| **Classification** | mandatory |

**Description:** The `/data/aggregated` endpoint requires BOTH `dashboard_id` AND `graph_id` query parameters (line 48-49 in data.py), but the frontend `dashboardApi.getAggregatedData` only passes `dashboard_id` and `filters`. The frontend never provides `graph_id`, causing FastAPI to return a 422 Unprocessable Entity error for all aggregated data requests. Additionally, the backend returns data for a single graph (hardcoded single-item array in response), but the frontend `AggregatedDataResponse` type and UI component expect to iterate over multiple graphs. The endpoint description says "Returns data for all dashboard charts" but implementation only handles one graph.

**Evidence:**
- Backend endpoint definition (`src/mkobi/api/routes/data.py:48-49`):
  ```python
  dashboard_id: UUID = Query(..., description="Dashboard ID"),
  graph_id: UUID = Query(..., description="Graph ID"),  # Required - will cause 422 error
  ```
- Backend response (`src/mkobi/api/routes/data.py:142-150`):
  ```python
  return {
      "graphs": [{
          "graph_id": str(graph_id),  # Only ONE graph returned
          "type": graph.type.value,
          "name": graph.name,
          "data": data_points,
      }]
  }
  ```
- Frontend call (`frontend/src/features/dashboards/api/dashboardApi.ts:23-29`):
  ```typescript
  const response = await axiosInstance.get<AggregatedDataResponse>('/data/aggregated', {
    params: { dashboard_id, filters },  // Missing graph_id!
  })
  ```
- Frontend UI (`frontend/src/features/dashboards/ui/DashboardView.tsx:140-148`):
  ```typescript
  aggregatedData?.graphs.map((graph: GraphDataWithConfig) => (  // Expects multiple graphs
    <Paper key={graph.graph_id} ...>
  ))
  ```

**Recommendation:** Redesign the endpoint to either (a) make `graph_id` optional and return all graphs when not provided, or (b) have the frontend fetch graphs first then request data for each graph. The current design will cause 422 errors on the frontend and incomplete data display.

---

### INT-002: ProcessingLog ORM vs Pydantic Model Field Mismatch - `finished_at` vs `completed_at`

| Field | Value |
|-------|-------|
| **ID** | INT-002 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/db/models/processing_logs.py`, `src/mkobi/models/processing_logs.py` |
| **Classification** | mandatory |

**Description:** The ORM model (`src/mkobi/db/models/processing_logs.py:62-65`) uses `finished_at` column name, but the Pydantic response model (`src/mkobi/models/processing_logs.py:81`) uses `completed_at`. Database migrations also use `finished_at` (line 173 in migration). This causes serialization errors when returning processing logs via the `/admin/logs` endpoint.

**Evidence:**
- ORM model field (`src/mkobi/db/models/processing_logs.py:62-65`):
  ```python
  finished_at: Mapped[datetime | None] = mapped_column(
      DateTime(timezone=True), nullable=True,
  )
  ```
- Pydantic model field (`src/mkobi/models/processing_logs.py:81`):
  ```python
  completed_at: datetime | None = None
  ```
- Database migration (`alembic/versions/7130ecb0388c_true_initial_migration.py:173`):
  ```sql
  finished_at TIMESTAMPTZ,
  ```

**Recommendation:** Rename `completed_at` to `finished_at` in the Pydantic model `ProcessingLogRead` to match the ORM model and database schema.

---

### INT-003: Upload Response Field Mismatch - Backend Returns Dictionary but Pydantic Model Expects Structured Response

| Field | Value |
|-------|-------|
| **ID** | INT-003 |
| **Severity** | MEDIUM |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/api/routes/upload.py`, `src/mkobi/models/data.py`, `frontend/src/shared/types/api.types.ts` |
| **Classification** | mandatory |

**Description:** The backend `/upload/{dashboard_id}` endpoint returns a plain dictionary with `message` and `processing_log_id` (lines 184-187 in upload.py), but the Pydantic model `UploadResponse` has fields `task_id`, `filename`, `dashboard_id`, `status`, `message`, `uploaded_at` (lines 59-81 in data.py). The endpoint declares `response_model=dict[str, str | UUID], process_upload_endpoint` (line 58) but the frontend expects the full `UploadResponse` type structure.

**Evidence:**
- Backend returns (`src/mkobi/api/routes/upload.py:184-187`):
  ```python
  return {
      "message": result.message,
      "processing_log_id": result.task_id,
  }
  ```
- Pydantic model (`src/mkobi/models/data.py:59-81`) expects structured response with `task_id`, `filename`, `dashboard_id`, `status`, `message`, `uploaded_at`
- Frontend type (`frontend/src/shared/types/api.types.ts:59-68`) expects `processing_log_id` field

**Recommendation:** Either update the response to return the full `UploadResponse` model, or update the Pydantic model to match the actual response. The frontend type `processing_log_id` is a convenience field that maps to `task_id` in the backend.

---

### INT-004: Unused Endpoint `/upload/{dashboard_id}/process` Without Clear Integration

| Field | Value |
|-------|-------|
| **ID** | INT-004 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/api/routes/upload.py` |
| **Classification** | mandatory |

**Description:** The backend has a `/upload/{dashboard_id}/process` endpoint (lines 213-271 in upload.py) that is never called by the frontend. Processing is auto-triggered during upload via `enqueue_job` in `process_upload_with_session` (lines 187-197 in file_processing.py). This endpoint exists but serves no purpose in the current integration flow.

**Evidence:**
- Frontend upload flow (`frontend/src/features/upload/api/uploadApi.ts`) has `uploadFile`, `getProcessingStatus`, `getProcessingResult` but no `processFile` function
- Backend `/upload/{dashboard_id}/process` endpoint (`src/mkobi/api/routes/upload.py:213-271`) exists but is unused
- Auto-trigger in upload (`src/mkobi/services/file_processing.py:187-197`) happens during `process_upload_with_session`

**Recommendation:** Remove the unused `/upload/{dashboard_id}/process` endpoint or document its purpose for manual re-processing scenarios.

---

### INT-005: User Creation Endpoint URL Path Consistency

| Field | Value |
|-------|-------|
| **ID** | INT-005 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/api/routes/users.py`, `frontend/src/features/admin/api/adminApi.ts` |
| **Classification** | advisory |

**Description:** The frontend `createUser` function posts to `/users` (line 21 in adminApi.ts), but the backend route is registered with `prefix="/users"` (line 26 in users.py). FastAPI's `redirect_slashes=False` means this mismatch could cause 404 errors if the redirect behavior changes.

**Evidence:**
- Frontend call (`frontend/src/features/admin/api/adminApi.ts:21`):
  ```typescript
  const response = await axiosInstance.post<AdminUser>('/users', data)
  ```
- Backend route (`src/mkobi/api/routes/users.py:26`): `prefix="/users", tags=["users"], redirect_slashes=False`

**Recommendation:** Update frontend to use `/users/` to match the route definition exactly, avoiding any potential redirect issues.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 1 |
| HIGH | 1 |
| MEDIUM | 2 |
| LOW | 1 |

## Mandatory Fixes

- INT-001: Fix `/data/aggregated` endpoint to either make `graph_id` optional or implement frontend to provide it
- INT-002: Rename `completed_at` to `finished_at` in `ProcessingLogRead` model
- INT-003: Align Upload endpoint response format with Pydantic model or frontend type expectations

## Advisory Recommendations

- INT-004: Remove unused `/upload/{dashboard_id}/process` endpoint
- INT-005: Align URL paths for consistency

---