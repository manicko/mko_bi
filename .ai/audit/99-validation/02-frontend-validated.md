---
name: audit-validate-frontend
description: Validated frontend audit findings report
agent: validator
alwaysApply: false
problems-only: true
---

# Frontend Validation Report

**Source:** `.ai/audit/02-frontend/findings.md`
**Date:** 2026-06-09
**Mode:** problems-only

---

## Rejected Findings

### FE-001: Dead Code — BarChart and PieChart Components Never Used

| Field | Value |
|-------|-------|
| **Original ID** | FE-001 |
| **Original Type** | SPEC-DEVIATION |
| **Reason** | Invalid dead code identification — components are spec-required |

**Evidence:**
- SPEC.md v3.6 line 179: "Charts under dashboards feature — Chart components reside in `features/dashboards/ui/charts/` as dashboard-specific UI."
- `src/mkobi/models/enums.py` lines 25-31: `GraphType` enum explicitly defines `BAR = "bar"` and `PIE = "pie"` as supported chart types
- `frontend/src/shared/types/enums.ts` lines 23-30: Frontend `GraphType` enum mirrors backend with `BAR` and `PIE` values
- `frontend/src/features/dashboards/ui/charts/ChartRenderer.tsx` line 32: `graph.type` values include 'pie', and line 36-38 handles bar-specific orientation
- The ChartRenderer uses PlotlyChart directly for bar/pie charts, which is a valid implementation choice within the spec

**Rationale:** The finding incorrectly treats spec-required chart type components as dead code. `GraphType.BAR` and `GraphType.PIE` are explicitly defined in both backend and frontend enums as valid chart types. The BarChart and PieChart wrapper components are valid implementations that provide specialized rendering options (title, axis labels) consistent with the LineChart pattern. The current ChartRenderer implementation choosing to use PlotlyChart directly is an architectural choice, not a bug.

---

### FE-004: Missing Accessibility Labels for Form Fields in Login/Register

| Field | Value |
|-------|-------|
| **Original ID** | FE-004 |
| **Original Type** | BEST-PRACTICE |
| **Reason** | MUI TextField provides built-in accessibility with labels |

**Evidence:**
- MUI TextField documentation: When a `label` prop is provided, MUI automatically generates proper `id`/`htmlFor` associations and `aria-labelledby` relationships
- `frontend/src/features/auth/ui/LoginForm.tsx` line 71-78: TextField components with `label="Email"` and `label="Password"` props
- `frontend/src/features/auth/ui/RegisterForm.tsx` line 65-72: TextField with `label="Email"` prop

**Rationale:** MUI's TextField component with the `label` prop already provides proper accessibility attributes. Adding explicit `aria-label` would be redundant and violate the "no overengineering" principle. The current implementation is accessible by default through MUI's built-in label association.

---

### FE-005: Inconsistent Date Format Handling in LogViewer

| Field | Value |
|-------|-------|
| **Original ID** | FE-005 |
| **Original Type** | BEST-PRACTICE |
| **Reason** | ISO format is correct for API; display format is separate concern |

**Evidence:**
- `frontend/src/features/admin/ui/LogViewer.tsx` line 104, 111: `date.toISOString()` converts dates to ISO format for API query parameters
- `src/mkobi/api/routes/processing_logs.py` line 47-54: Backend expects `datetime` type for `date_from` and `date_to` query parameters
- SPEC.md v3.7: "Standard user-facing date format is `dd/mm/yyyy`" refers to display format, not API wire format
- DatePicker component output (ISO format) is the correct format for machine-to-machine communication

**Rationale:** The `dd/mm/yyyy` format specified in SPEC.md is for user-facing display, while ISO format (`YYYY-MM-DDTHH:mm:ss.sssZ`) is the standard for API wire format. The current implementation correctly uses ISO format for the date filter parameters sent to the backend. No change needed.

---

## Approved Findings (Mandatory Fixes)

### FE-006: Status Filter Options Mismatch Between Frontend and Backend

| Field | Value |
|-------|-------|
| **ID** | FE-006 |
| **Original Type** | SPEC-DEVIATION |
| **Status** | APPROVED |
| **Classification** | Mandatory Fix |

**Evidence:**
- `frontend/src/features/admin/ui/LogViewer.tsx` line 22: `statusOptions = ['started', 'uploaded', 'processing', 'success', 'failed', 'completed']`
- `src/mkobi/models/enums.py` lines 58-65: `ProcessingStatus` enum only defines: `started`, `uploaded`, `processing`, `completed`, `failed` (no `success`)
- `frontend/src/features/admin/ui/LogViewer.tsx` line 33: Chip rendering logic treats `'success'` as a valid status color variant
- `src/mkobi/api/routes/processing_logs.py` line 43: `status_filter: ProcessingStatus | None` — backend expects enum value, will reject `success`

**Finding:** The frontend includes `"success"` in status options, but this is not a valid `ProcessingStatus` enum value on the backend. The backend will reject this with a validation error, causing filter queries with 'success' to fail. The frontend should use `ProcessingStatus.COMPLETED` for successful terminal states instead.

---

## Cross-Phase Conflicts

None detected.

---

## Rollout Safety Issues

None detected.

---

## Summary

| Category | Count |
|----------|-------|
| Rejected Findings | 3 |
| Approved Mandatory Fixes | 1 (FE-006) |
| Approved Advisory Recommendations | 0 |
| Merged Findings | 0 |
| Cross-Phase Conflicts | 0 |

**Validated Counts per Phase:**
- Mandatory fixes: 1 (FE-006)
- Advisory recommendations: 0 (FE-002, FE-003 were not validated in problems-only mode)

---

## Required Actions

1. **FE-006**: Remove `"success"` from `statusOptions` in `LogViewer.tsx` and use `ProcessingStatus` enum values for consistency with backend. Import and use the shared `ProcessingStatus` type to ensure type safety.