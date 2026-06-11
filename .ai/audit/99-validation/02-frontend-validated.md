# Phase 02 Audit Findings — Frontend Validation Report

**Validator:** validator  
**Source:** .ai/audit/02-frontend/findings.md  
**Date:** 2026-06-11

---

## Rejected Findings

### FE-001 REJECTED — Dead Code — Unused BarChart and PieChart Components

**Original Type:** DOC-UPDATE  
**Rejection Reason:** The finding invalidates the SPEC. Both `GraphType.BAR` and `GraphType.PIE` are defined in `src/mkobi/models/enums.py` (lines 28-30) and mirrored in `frontend/src/shared/types/enums.ts` (lines 23-28). The SPEC.md explicitly documents supported chart types including `bar`, `line`, `pie`, and `table`. The `fsd-structure.md` (lines 70-74) explicitly lists `BarChart.tsx` and `PieChart.tsx` as expected chart components under `features/dashboards/ui/charts/`.

The components exist as convenience wrappers matching the `GraphType` enum specification. While `ChartRenderer` currently delegates to `PlotlyChart` directly for bar/pie types (lines 88-90), this is an architectural choice that maintains backward compatibility. The presence of these components aligns with the documented chart component placement and does not violate the specification.

**SPEC Reference:**
- `docs/SPEC.md` — GraphType enum with BAR, LINE, PIE, TABLE values
- `docs/07-frontend/fsd-structure.md` — Documents chart components placement under dashboards

**Evidence:**
- `frontend/src/shared/types/enums.ts` — GraphType includes BAR and PIE constants
- `frontend/src/features/dashboards/ui/charts/BarChart.tsx` — Matches GraphType.BAR
- `frontend/src/features/dashboards/ui/charts/PieChart.tsx` — Matches GraphType.PIE
- `frontend/src/features/dashboards/ui/charts/ChartRenderer.tsx` — Bar/pie charts are rendered via plotlyData conversion, maintaining functional compatibility

---

## Validated Findings

### FE-002 VALIDATED — Potential Race Condition in 401 Request Queue

**Type:** BEST-PRACTICE  
**Classification:** advisory  
**Validation Status:** APPROVED (no change)

The finding correctly identifies a type safety concern where `processQueue(null, newToken.access_token)` at line 99 passes a string token, but the QueueItem type at lines 34-37 expects `(token: string) => void`. When `processQueue` is called with `null` on line 104 (error case), the resolve callback is never invoked but the queue items still expect string tokens. The TypeScript non-null assertion at line 44 (`prom.resolve(token!)`) masks this potential issue.

However, the runtime behavior is correct:
- Line 99: `processQueue(null, newToken.access_token)` — token is provided on success
- Line 104: `processQueue(errorToReject, null)` — error is provided, so reject is called (line 41-42)

The type system does not reflect this safety, but the actual code path is sound. This is a valid type safety improvement opportunity.

---

### FE-003 VALIDATED — Missing Loading State for ChartRenderer on Empty Data

**Type:** BEST-PRACTICE  
**Classification:** advisory  
**Validation Status:** APPROVED

The finding identifies a UX gap. `ChartRenderer` does not guard against empty `graph.data` at line 77. While `DashboardView` (line 146-152) shows "No data available for this dashboard" at the list level, individual charts receive empty data arrays without explicit handling. The `convertToPlotlyData` function (lines 11-75) processes empty arrays without validation, potentially producing charts with empty traces.

**Recommendation:** Valid improvement to add user-friendly empty state handling in `ChartRenderer`, similar to `TableChart` (lines 26-28).

---

### FE-004 VALIDATED — ESLint Warnings in Coverage Directory

**Type:** BEST-PRACTICE  
**Classification:** advisory  
**Validation Status:** APPROVED

The `eslint.config.js` at line 9 only excludes `dist` from global ignores. Generated coverage files in `frontend/coverage/` trigger lint warnings about unused `eslint-disable` directives. This is a valid configuration improvement to prevent linting machine-generated code.

---

## Summary

| Status | Count |
|--------|-------|
| REJECTED | 1 (FE-001) |
| VALIDATED (advisory) | 3 (FE-002, FE-003, FE-004) |

---

## Cross-Phase Conflicts

None detected. All validated findings are frontend-specific advisory recommendations with no conflict with backend findings.