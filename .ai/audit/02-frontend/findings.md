---
name: audit-findings
description: Structured findings template for audit phase output
agent: audit-executor
alwaysApply: false
---

# Phase 02 Audit Findings — Frontend Architecture

**Executor:** auditor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** yes

---

## Findings

### FE-001: Dead Code — BarChart and PieChart Components Never Used

| Field | Value |
|-------|-------|
| **ID** | FE-001 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/features/dashboards/ui/charts/BarChart.tsx`, `frontend/src/features/dashboards/ui/charts/PieChart.tsx` |
| **Classification** | advisory |

**Description:** `BarChart.tsx` and `PieChart.tsx` components exist in `features/dashboards/ui/charts/` but are never imported or used anywhere in the codebase. According to SPEC.md v3.6, bar and pie chart components should render under `features/dashboards/ui/charts/` (line 178-179). However, the `ChartRenderer` component handles bar and pie charts directly via `PlotlyChart`, bypassing these wrapper components.

**Evidence:**
- `frontend/src/features/dashboards/ui/charts/BarChart.tsx` - 28 lines, exports `BarChart` component, no imports anywhere
- `frontend/src/features/dashboards/ui/charts/PieChart.tsx` - 17 lines, exports `PieChart` component, no imports anywhere
- `frontend/src/features/dashboards/ui/charts/ChartRenderer.tsx` line 88-90 shows bar/pie charts use `PlotlyChart` directly, not the wrapper components

**Recommendation:** Remove `BarChart.tsx` and `PieChart.tsx` files as they are dead code. If dedicated bar/pie chart components were intended, implement them in `ChartRenderer` or document why they should exist separately.

---

### FE-002: Missing Loading State for Filter Values Query

| Field | Value |
|-------|-------|
| **ID** | FE-002 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/dashboards/ui/DashboardFilters.tsx` |
| **Classification** | advisory |

**Description:** In `FilterField` component (line 100-106), the `useFilterValues` hook is called but its loading state is ignored. When filters use `source: 'data'` for dynamic values, users see an empty dropdown while values are being fetched, without any loading indicator.

**Evidence:**
- `frontend/src/features/dashboards/ui/DashboardFilters.tsx` line 102: `const { data: filterValuesData } = useFilterValues(dashboardId, filter.name)` - destructuring only `data`, `isLoading` and `error` states are not used
- Frontend tests pass but don't cover this loading scenario

**Recommendation:** Add loading and error handling for the filter values query. Show a loading spinner or disabled state while fetching dynamic filter values, and provide user feedback on fetch failures.

---

### FE-003: Large Bundle Size Warning — Plotly.js Exceeds 500KB

| Field | Value |
|-------|-------|
| **ID** | FE-003 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/dashboards/ui/charts/PlotlyChart.tsx`, `frontend/src/features/dashboards/ui/charts/ChartRenderer.tsx` |
| **Classification** | advisory |

**Description:** The production build warns that `plotly-BxTkdUEp.js` exceeds 500KB after minification (4,643.95 KB → 1,388.77 KB gzipped). This impacts initial load performance, especially for users who may only need to view tables or dashboards without charts.

**Evidence:**
- Build output: `dist/assets/plotly-BxTkdUEp.js              4,643.95 kB │ gzip: 1,388.77 kB`
- All chart types (bar, line, pie, table) are bundled together regardless of which is used on a page

**Recommendation:** Implement dynamic import/code-splitting for Plotly.js to load chart components only when needed. Use `React.lazy()` with `Suspense` for chart rendering, or consider the build optimization suggestion from Vite's warning about `codeSplitting`.

---

### FE-004: Missing Accessibility Labels for Form Fields in Login/Register

| Field | Value |
|-------|-------|
| **ID** | FE-004 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/auth/ui/LoginForm.tsx`, `frontend/src/features/auth/ui/RegisterForm.tsx` |
| **Classification** | advisory |

**Description:** The `TextField` components for email and password in both `LoginForm.tsx` and `RegisterForm.tsx` lack explicit `aria-label` or `aria-labelledby` attributes beyond the visible label. While MUI's `TextField` provides some accessibility, explicit ARIA attributes improve screen reader compatibility.

**Evidence:**
- `frontend/src/features/auth/ui/LoginForm.tsx` lines 71-87: `TextField` components without explicit ARIA labels
- `frontend/src/features/auth/ui/RegisterForm.tsx` lines 65-72: `TextField` component without explicit ARIA labels

**Recommendation:** Add explicit `aria-label` or `aria-labelledby` attributes to form fields for better accessibility compliance. Consider using MUI's built-in accessibility props or adding additional ARIA attributes.

---

### FE-005: Inconsistent Date Format Handling in LogViewer

| Field | Value |
|-------|-------|
| **ID** | FE-005 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/admin/ui/LogViewer.tsx` |
| **Classification** | advisory |

**Description:** The `LogViewer` component uses `date.toISOString()` for date filtering, but the backend accepts ISO format dates. This works correctly, but the UI DatePicker doesn't enforce the `dd/mm/yyyy` format documented in SPEC.md v3.7 as the standard user-facing date format.

**Evidence:**
- `frontend/src/features/admin/ui/LogViewer.tsx` line 104: `date ? date.toISOString() : undefined` - uses ISO format
- SPEC.md v3.7: "Standard user-facing date format is `dd/mm/yyyy`"

**Recommendation:** Consider configuring the DatePicker to display dates in `dd/mm/yyyy` format to match the documented standard user-facing format, using `AdapterDateFns` with appropriate localization.

---

### FE-006: Status Filter Options Mismatch Between Frontend and Backend

| Field | Value |
|-------|-------|
| **ID** | FE-006 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/features/admin/ui/LogViewer.tsx`, `src/mkobi/models/enums.py` |
| **Classification** | mandatory |

**Description:** The `LogViewer` component defines status filter options as `['started', 'uploaded', 'processing', 'success', 'failed', 'completed']` (line 22), but the backend `ProcessingStatus` enum (SPEC.md v3.0) defines only: `STARTED`, `UPLOADED`, `PROCESSING`, `COMPLETED`, `FAILED`. The frontend includes `"success"` which is not a valid backend status value, and the enum values use lowercase while the backend uses the same lowercase values but the API query parameter expects enum values.

**Evidence:**
- `frontend/src/features/admin/ui/LogViewer.tsx` line 22: `const statusOptions = ['started', 'uploaded', 'processing', 'success', 'failed', 'completed']`
- `src/mkobi/models/enums.py` lines 61-65: Only `started`, `uploaded`, `processing`, `completed`, `failed` are defined
- `frontend/src/features/admin/ui/LogViewer.tsx` line 90: `value={filters.status_filter || ''}` - sends `status_filter` to backend
- Backend `/admin/logs/` endpoint uses `status_filter: ProcessingStatus | None` query parameter (line 43-45 in processing_logs.py)

**Recommendation:** Remove `"success"` from `statusOptions` in LogViewer.tsx since the backend does not have a `success` processing status. The valid terminal success state is `completed`, not `success`. This mismatch causes filter queries with 'success' to return no results, as the backend will not recognize this value. Instead, import and use the `ProcessingStatus` enum from the shared types to ensure consistency with the backend.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 1 |
| LOW | 4 |

## Advisory Recommendations

- FE-001: Remove dead BarChart and PieChart components
- FE-002: Add loading state for filter values in DashboardFilters
- FE-003: Implement code-splitting for Plotly.js bundle
- FE-004: Add explicit ARIA labels to auth form fields
- FE-005: Align date format with documented standard (dd/mm/yyyy)

## Mandatory Fixes

- FE-006: Remove invalid "success" status option from LogViewer status filter (conflicts with backend ProcessingStatus enum)

## Doc Updates Needed

None identified.