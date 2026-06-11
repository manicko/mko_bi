# Phase 02 Audit Findings — Frontend Architecture

**Executor:** auditor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### FE-001: Dead Code — Unused BarChart and PieChart Components

| Field | Value |
|-------|-------|
| **ID** | FE-001 |
| **Severity** | LOW |
| **Type** | DOC-UPDATE |
| **Affected Modules** | frontend/src/features/dashboards/ui/charts/BarChart.tsx, frontend/src/features/dashboards/ui/charts/PieChart.tsx |
| **Classification** | advisory |

**Description:** `BarChart` and `PieChart` components exist in the codebase but are never imported or used. ChartRenderer.tsx handles bar and pie chart types directly via PlotlyChart without delegating to the dedicated BarChart/PieChart components. These exported functions serve no runtime purpose.

**Evidence:**
- `frontend/src/features/dashboards/ui/charts/BarChart.tsx` - Line 12-27: Exported function `BarChart` exists but never imported anywhere in the codebase
- `frontend/src/features/dashboards/ui/charts/PieChart.tsx` - Line 10-16: Exported function `PieChart` exists but never imported anywhere in the codebase
- `frontend/src/features/dashboards/ui/charts/ChartRenderer.tsx` - Lines 88-90: Bar and pie charts both use `PlotlyChart` directly, not the dedicated components
- Grep search found no imports of `BarChart` or `PieChart` in the source code

**Recommendation:** Either remove the unused BarChart and PieChart components, or document them as future-proof convenience wrappers if there's an intention to use them later. Given the current architecture where ChartRenderer consolidates all chart types through PlotlyChart, removing these components would reduce code surface.

---

### FE-002: Potential Race Condition in 401 Request Queue

| Field | Value |
|-------|-------|
| **ID** | FE-002 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | frontend/src/shared/api/axiosInstance.ts |
| **Classification** | advisory |

**Description:** In the axios response interceptor, when a request fails with 401 and `isRefreshing` is true, the Promise created for the queued request does not return a resolved value. The promise chain resolves with `undefined` (from the executor's implicit return), but the calling code expects a `string` token. This could cause issues when `originalConfig.headers.Authorization` is set to `undefined`.

**Evidence:**
- `frontend/src/shared/api/axiosInstance.ts` - Lines 77-86:
```typescript
if (isRefreshing) {
  return new Promise<string>((resolve, reject) => {
    failedQueue.push({ resolve, reject })
  })
    .then((token) => {
      originalConfig.headers.Authorization = `Bearer ${token}`  // token could be undefined
      return axiosInstance(originalConfig)
    })
```

**Recommendation:** The `failedQueue.push({ resolve, reject })` stores functions expecting `string` and `Error` parameters, but when `processQueue` is called with `null` token on a successful refresh (line 44), `prom.resolve(token!)` passes `null` or `undefined` if the token is falsy. Add null check or ensure the queue only stores functions that handle the token correctly.

---

### FE-003: Missing Loading State for ChartRenderer on Empty Data

| Field | Value |
|-------|-------|
| **ID** | FE-003 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | frontend/src/features/dashboards/ui/charts/ChartRenderer.tsx |
| **Classification** | advisory |

**Description:** `ChartRenderer` does not handle the case where `graph.data` is empty or `undefined`. When data is empty, `convertToPlotlyData` returns an array with a single trace containing empty x and y arrays. This could result in blank charts without any indication to users.

**Evidence:**
- `frontend/src/features/dashboards/ui/charts/ChartRenderer.tsx` - Lines 77-91: No null/undefined check for `graph.data`
- `frontend/src/features/dashboards/ui/DashboardView.tsx` - Line 133-152: Loading state and error state are handled, but ChartRenderer itself doesn't guard against empty data

**Recommendation:** Add a guard in `ChartRenderer` to return a user-friendly message when `graph.data` is empty or undefined, similar to how `TableChart` handles this case (line 26-28).

---

### FE-004: ESLint Warnings in Coverage Directory

| Field | Value |
|-------|-------|
| **ID** | FE-004 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | frontend/coverage/ (generated files) |
| **Classification** | advisory |

**Description:** ESLint is configured to lint the entire project directory but the `coverage/` directory contains generated files that are not source code. These files trigger warnings about unused eslint-disable directives.

**Evidence:**
- `npm run lint` output: 3 warnings from `frontend/coverage/block-navigation.js`, `frontend/coverage/prettify.js`, and `frontend/coverage/sorter.js`
- Current eslint.config.js does not exclude the `coverage/` directory (only excludes `dist/`)

**Recommendation:** Add `coverage/` to the globalIgnores array in `eslint.config.js` to prevent linting generated coverage files.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 1 |
| LOW | 3 |

## Advisory Recommendations

- FE-001: Remove or document unused BarChart and PieChart components
- FE-002: Fix race condition in 401 request queue - ensure token is properly typed
- FE-003: Add empty data handling in ChartRenderer for better UX
- FE-004: Exclude coverage directory from ESLint configuration

---

## Runtime Verification Results

| Check | Result |
|-------|--------|
| TypeScript compilation (tsc -b --noEmit) | ✓ Passed - no errors |
| ESLint | ✓ 3 warnings (generated coverage files) |
| Tests (vitest run) | ✓ 165 tests passed |
| Production build (npm run build) | ✓ Built successfully (4.6MB plotly bundle) |

## API Contract Alignment

The frontend API calls match the backend routes:
- `useMyDashboards()` → `GET /dashboards/my` ✓
- `useDashboard(id)` → `GET /dashboards/{id}` ✓
- `useAggregatedData()` → `GET /data/aggregated` ✓
- `uploadApi.uploadFile()` → `POST /upload/{dashboard_id}` ✓
- `uploadApi.getProcessingStatus()` → `GET /upload/status/{task_id}` ✓
- `uploadApi.getProcessingResult()` → `GET /upload/result/{task_id}` ✓