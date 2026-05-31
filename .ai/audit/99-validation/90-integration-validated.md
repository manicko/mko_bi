# Phase 09 Validation Report — Integration

**Validator:** validator
**Source Findings:** `.ai/audit/90-integration/findings.md`
**Validated:** yes
**Mode:** problems-only

---

## Rejected Findings

### INT-002: ProcessingLog ORM vs Pydantic Model Field Mismatch — `finished_at` vs `completed_at`

| Field | Value |
|-------|-------|
| **ID** | INT-002 |
| **Rejection Reason** | **Stale / Incorrect Evidence** — The finding claims the Pydantic model `ProcessingLogRead` uses `completed_at` while the ORM uses `finished_at`. Actual code inspection shows **both** the ORM model (`src/mkobi/db/models/processing_logs.py:62-65`) and the Pydantic model (`src/mkobi/models/processing_logs.py:81`) use `finished_at`. The field names are already aligned. No serialization mismatch exists for this field. |

---

## Cross-Phase Conflicts / Overlaps

### Merge Candidate: INT-001 ↔ FE-001 — Same Root Cause

| Field | Value |
|-------|-------|
| **Finding IDs** | INT-001 (Phase 09 — Integration), FE-001 (Phase 02 — Frontend) |
| **Root Cause** | `/data/aggregated` endpoint requires `graph_id` as mandatory query parameter, but the frontend `getAggregatedData` only sends `dashboard_id` and `filters`. |
| **Conflict Type** | Duplicate finding across phases. Both describe the same API contract mismatch from different angles (integration vs frontend perspective). |
| **Recommendation** | Merge into a single task. The fix requires coordination: either make `graph_id` optional on the backend and return all graphs, or update the frontend to iterate over dashboard graphs and request data per-graph. INT-001 is the more complete finding (includes backend evidence + frontend evidence + response format mismatch). FE-001 is a subset. |

---

## Validated Counts

| Category | Count |
|----------|-------|
| **Total Findings** | 5 |
| **Rejected** | 1 (INT-002 — incorrect evidence) |
| **Merge Candidates** | 1 pair (INT-001 ↔ FE-001 — same root cause) |
| **Passed Validation Unchanged** | 3 (INT-001, INT-003, INT-004, INT-005 — noting INT-001 overlaps with FE-001) |

### Mandatory Fixes (Validated)

- **INT-001:** `/data/aggregated` missing `graph_id` — backend requires it, frontend doesn't send it → guaranteed 422 error at runtime.
- **INT-003:** Upload endpoint returns `{"message", "processing_log_id"}` dict but `UploadResponse` Pydantic model and frontend type expect `task_id`, `filename`, `dashboard_id`, `status`, `message`, `uploaded_at`. The endpoint declares `response_model=dict[str, str | UUID]` but the service layer actually returns a full `UploadResponse` — the endpoint discards most fields and returns a custom dict instead.

### Advisory Recommendations (Validated)

- **INT-004:** `/upload/{dashboard_id}/process` endpoint exists but has no frontend consumer. Upload auto-triggers processing via `enqueue_job` in `process_upload_with_session`. The process endpoint is dead code unless needed for manual re-processing.
- **INT-005:** Frontend `createUser` posts to `/users` (no trailing slash) while backend registers with `prefix="/users"` and `redirect_slashes=False`. With `redirect_slashes=False`, FastAPI won't redirect `/users` to `/users/`, meaning the POST hits a 404 unless there's a separate route at `/users` without trailing slash. This is a latent bug.

---

## Execution Warnings

1. **INT-001 and INT-003 are tightly coupled** — both involve API contract mismatches between frontend expectations and backend responses. If the fix approach for INT-001 is to change the backend to return all graphs without requiring `graph_id`, this changes the `AggregatedDataResponse` shape. Ensure the frontend `GraphDataWithConfig` type and `DashboardView.tsx` rendering still match the new response format. Coordinated fix required.

2. **INT-005 is a latent runtime bug** — FastAPI with `redirect_slashes=False` will not redirect `/users` to `/users/`. The `createUser` call to `POST /users` will get a 404 because the route is registered at `/users/`. Contrary to the finding's LOW severity classification, this will **definitely fail at runtime** for any admin user creation. Reclassify from advisory/LOW to mandatory/HIGH.

---

## Rollout Safety Notes

- **INT-001 fix** requires coordinated frontend+backend change. Not safe to deploy backend-only or frontend-only intermediate states. Either use a feature flag or deploy both changes together.
- **INT-003 fix** is backend-only (align the response) but must not break the existing frontend `UploadResponse` type which includes `processing_log_id` as a convenience field mapped from `task_id`. The backend currently returns `processing_log_id` as a key — ensure the frontend still receives this field.
- **INT-005 fix** is a single-line frontend URL change (`/users` → `/users/`). Safe to deploy independently.
