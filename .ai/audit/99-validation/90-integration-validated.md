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