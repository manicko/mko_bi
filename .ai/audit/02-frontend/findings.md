---
name: 02-frontend
description: Frontend architecture audit findings
agent: audit-executor
alwaysApply: false

---

# Phase 02 Audit Findings — Frontend Architecture

**Executor:** audit-executor  
**Template:** `.ai/audit/templates/audit-findings.md`  
**Status:** complete  
**Validated:** no  

---

## Findings

### FE-001: API Contract Mismatch - Missing graph_id Query Parameter

| Field | Value |
|-------|-------|
| **ID** | FE-001 |
| **Severity** | CRITICAL |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `frontend/src/features/dashboards/api/dashboardApi.ts`, `src/mkobi/api/routes/data.py` |
| **Classification** | mandatory |

**Description:** The frontend `/data/aggregated` endpoint call is missing the required `graph_id` query parameter, AND expects a different response format than what the backend provides. The backend route at `data.py:48-49` requires both `dashboard_id` AND `graph_id` as mandatory query parameters, returning a single graph's data. However, the frontend `getAggregatedData` function only sends `dashboard_id` and `filters`, and `DashboardView` expects an array of graphs in the response. This API contract mismatch will cause HTTP 422 validation errors at runtime.

**Evidence:**
- Frontend call: `frontend/src/features/dashboards/api/dashboardApi.ts:23-30`:
  ```typescript
  getAggregatedData: async (
    params: AggregatedDataRequest
  ): Promise<AggregatedDataResponse> => {
    const response = await axiosInstance.get<AggregatedDataResponse>('/data/aggregated', {
      params,
    })
  ```
  The `AggregatedDataRequest` interface (in `api.types.ts:134-137`) only includes `dashboard_id` and `filters`, lacking `graph_id`.

- Backend definition: `src/mkobi/api/routes/data.py:48-49`:
  ```python
  dashboard_id: UUID = Query(..., description="Dashboard ID"),
  graph_id: UUID = Query(..., description="Graph ID"),  # Required - will cause 422 error!
  ```

- Frontend expects multiple graphs: `frontend/src/features/dashboards/ui/DashboardView.tsx:138-149`:
  ```typescript
  {aggregatedData?.graphs && aggregatedData.graphs.length > 0 ? (
    <Stack spacing={2}>
      {aggregatedData.graphs.map((graph: GraphDataWithConfig) => (
        <Paper key={graph.graph_id} ...>
          <PlotlyChart data={graph.data} layout={graph.layout} />
        </Paper>
      ))
    </Stack>
  )
  ```
  The frontend iterates over `aggregatedData.graphs` array.

- Backend returns single graph: `src/mkobi/api/routes/data.py:142-150` returns a response with a single-element array containing one graph based on the required `graph_id`.

**Recommendation:** Add `graph_id` to the `AggregatedDataRequest` interface and pass it from the frontend. The DashboardView component needs to iterate over graphs and fetch data for each, matching the backend's expectation that graph_id is a required parameter.

---

### FE-002: Unused getFilter API Function

| Field | Value |
|-------|-------|
| **ID** | FE-002 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/dashboards/api/dashboardApi.ts` |
| **Classification** | advisory |

**Description:** The `dashboardApi.getFilter` function is defined but never called anywhere in the codebase. Search found no usages of `getFilter` in TypeScript files outside its definition.

**Evidence:** `frontend/src/features/dashboards/api/dashboardApi.ts:32-35`:
```typescript
getFilter: async (id: string): Promise<FilterDetail> => {
  const response = await axiosInstance.get<FilterDetail>(`/filters/${id}`)
  return response.data
},
```
No matching calls found in any component or hook.

**Recommendation:** Either remove the unused function or implement its usage. If filters are intended to be fetched dynamically, integrate this API call into the DashboardFilters component.

---

### FE-003: Unused Chart Component Exports

| Field | Value |
|-------|-------|
| **ID** | FE-003 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/dashboards/ui/charts/index.ts`, `frontend/src/features/dashboards/ui/DashboardView.tsx` |
| **Classification** | advisory |

**Description:** `BarChart`, `LineChart`, `PieChart`, and `TableChart` are exported from the charts index but only `PlotlyChart` is actually used in DashboardView. The chart-specific components are never imported or rendered. The DashboardView directly uses `PlotlyChart` with data from `GraphDataWithConfig.type`, bypassing the specialized chart wrappers.

**Evidence:**
- Export: `frontend/src/features/dashboards/ui/charts/index.ts:1-5` exports all chart types
- Usage in DashboardView: `frontend/src/features/dashboards/ui/DashboardView.tsx:146` uses `PlotlyChart` directly
- No imports of `BarChart`, `LineChart`, `PieChart`, or `TableChart` found in any component file

**Recommendation:** Either remove unused chart exports or implement chart type-based rendering in DashboardView:
```typescript
const ChartComponent = getChartByType(graph.type)
<ChartComponent data={graph.data} layout={graph.layout} />
```

---

### FE-004: Hardcoded Layout UUID Mapping in Admin API

| Field | Value |
|-------|-------|
| **ID** | FE-004 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/features/admin/api/adminApi.ts` |
| **Classification** | advisory |

**Description:** Layout name to UUID mapping is hardcoded in the admin API client. This creates tight coupling to specific database seed values and will break if layouts are reseeded with different UUIDs.

**Evidence:** `frontend/src/features/admin/api/adminApi.ts:48-53`:
```typescript
const LAYOUT_NAME_TO_ID: Record<string, string> = {
  'single-column': '00000000-0000-0000-0000-000000000001',
  'two-columns': '00000000-0000-0000-0000-000000000002',
  'grid': '00000000-0000-0000-0000-000000000003',
}
```

**Recommendation:** Create a `/layouts` endpoint to fetch layout options dynamically, or use a configuration service that returns available layouts. This decouples the frontend from database seed values.

---

### FE-005: Missing Accessibility Attributes in TableChart

| Field | Value |
|-------|-------|
| **ID** | FE-005 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/dashboards/ui/charts/TableChart.tsx` |
| **Classification** | advisory |

**Description:** TableChart component uses plain HTML table elements without proper semantic structure or accessibility attributes. Screen readers need table headers with scope attributes and the table should have proper ARIA labels.

**Evidence:** `frontend/src/features/dashboards/ui/charts/TableChart.tsx:30-55`:
```typescript
<table style={{ width: '100%', borderCollapse: 'collapse' }}>
  <thead>
    <tr>
      {displayColumns.map((col) => (
        <th key={col} style={{ ... }}>{col}</th>
      ))}
    </tr>
  </thead>
```
Missing: `scope="col"` on headers, `<caption>` for screen readers, and ARIA attributes.

**Recommendation:** Add accessibility attributes:
```typescript
<table aria-label={title ? `${title} data table` : 'Dashboard data table'}>
  {title && <caption>{title}</caption>}
  <thead>
    <tr>
      {displayColumns.map((col) => (
        <th key={col} scope="col">{col}</th>
      ))}
    </tr>
  </thead>
```

---

### FE-006: API Contract Mismatch - Missing dashboard_id in grantDashboardAccess Body

| Field | Value |
|-------|-------|
| **ID** | FE-006 |
| **Severity** | CRITICAL |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `frontend/src/features/admin/api/adminApi.ts`, `src/mkobi/api/routes/dashboards_access.py` |
| **Classification** | mandatory |

**Description:** The `grantDashboardAccess` frontend function sends `{ user_id, permission }` but the backend `AccessGrant` model requires `{ dashboard_id, user_id, permission }` as mandatory fields. The backend explicitly validates that `dashboard_id` in the body matches the URL path parameter (line 72-81 in `dashboards_access.py`), so the frontend request will fail with HTTP 422 validation error.

**Evidence:**
- Frontend call: `frontend/src/features/admin/api/adminApi.ts:83-85`:
  ```typescript
  export async function grantDashboardAccess(dashboardId: string, data: GrantAccessRequest): Promise<void> {
    await axiosInstance.post(`/dashboards/${dashboardId}/access`, data)
  }
  ```
  The `GrantAccessRequest` interface at `api.types.ts:220-223` only has `user_id` and `permission`, missing `dashboard_id`.

- Backend validation: `src/mkobi/api/routes/dashboards_access.py:71-81`:
  ```python
  # Check that dashboard_id from path matches body
  if str(access_grant.dashboard_id) != str(dashboard_id):
      raise HTTPException(
          status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
          detail="dashboard_id in body doesn't match URL",
      )
  ```
  The backend expects `dashboard_id` in the request body.

**Recommendation:** Add `dashboard_id` to the `GrantAccessRequest` interface and include it in the request body:
```typescript
export async function grantDashboardAccess(dashboardId: string, data: GrantAccessRequest): Promise<void> {
  await axiosInstance.post(`/dashboards/${dashboardId}/access`, {
    ...data,
    dashboard_id: dashboardId,
  })
}
```

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 2 |
| HIGH | 0 |
| MEDIUM | 2 |
| LOW | 2 |

## Mandatory Fixes

- FE-001: API Contract Mismatch - Missing graph_id Query Parameter (CRITICAL)
- FE-006: API Contract Mismatch - Missing dashboard_id in grantDashboardAccess Body (CRITICAL)

## Advisory Recommendations

- FE-004: Hardcoded Layout UUID Mapping in Admin API (MEDIUM)
- FE-005: Missing Accessibility Attributes in TableChart (MEDIUM)
- FE-002: Unused getFilter API Function (LOW)
- FE-003: Unused Chart Component Exports (LOW)

---

## Template Field Reference

### Mandatory Fields Per Finding

| Field | Type | Values/Format |
|-------|------|---------------|
| `id` | string | Unique identifier within phase (e.g., `BE-001`, `FE-003`) |
| `title` | string | Human-readable one-line summary |
| `type` | enum | `SPEC-DEVIATION`, `BEST-PRACTICE`, `DOC-UPDATE`, `RUNTIME-ERROR` |
| `severity` | enum | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `description` | string | Detailed problem description with context |
| `evidence` | string | File paths, line references, log excerpts, code snippets |
| `affected_modules` | list | Affected module paths (e.g., `src/mkobi/api/routes/`, `frontend/src/features/auth/`) |
| `recommendation` | string | Concrete fix direction: what to change and why |
| `classification` | enum | `mandatory` (security, data loss, correctness) or `advisory` (improvement, refactoring) |

### Classification Guide

- **mandatory**: Security vulnerabilities, data loss risks, correctness issues, spec deviations requiring immediate fix
- **advisory**: Code quality improvements, refactoring suggestions, best practice enhancements