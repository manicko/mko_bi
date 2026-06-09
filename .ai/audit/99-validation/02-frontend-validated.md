---
name: 02-frontend-validated
description: Validated frontend audit findings
agent: validator
---

# Phase 02 Validation Report — Frontend Architecture

**Validator:** validator  
**Source:** `.ai/audit/02-frontend/findings.md`  
**Date:** 2026-06-09

---

## Rejected Findings

### FE-001 — REJECTED

| Field | Value |
|-------|-------|
| **Finding ID** | FE-001 |
| **Original Type** | SPEC-DEVIATION |
| **Original Classification** | advisory |
| **Rejection Reason** | **Spec-required features incorrectly flagged as dead code.** SPEC.md v3.6 (line 178) explicitly states: "Chart components reside in `features/dashboards/ui/charts/` as dashboard-specific UI." The `GraphType` enum in `src/mkobi/models/enums.py` defines `BAR = "bar"` and `PIE = "pie"` as supported chart types. Per the SPEC-DEVIATION rejection rule (audit-validate Step 3-SPEC): "If the component type matches a GraphType value, the finding is invalid as filed." The `BarChart` and `PieChart` components implement spec-required chart types and cannot be classified as dead code regardless of current usage. The proper classification would be a missing integration (if integration was intended) or valid unused code (if these are reserved for future use).

---

### FE-002 — REJECTED

| Field | Value |
|-------|-------|
| **Finding ID** | FE-002 |
| **Original Type** | BEST-PRACTICE |
| **Original Classification** | advisory |
| **Rejection Reason** | **Factual errors in evidence invalidate finding.** (1) Finding claims "LineChart.tsx line 5: `layout?: Layout` should be `layout?: Partial<Layout>`" but LineChart.tsx line 6 has `layout?: Layout` (not line 5), and this same pattern exists in BarChart.tsx and PieChart.tsx - making this a consistent (if not ideal) pattern across all wrapper components, not a LineChart-specific issue. (2) The null/empty data handling concern is invalid because PlotlyComponent.tsx Line 36 already handles this: `const chartData = Array.isArray(data) ? data : [data]`. (3) The `convertToPlotlyData(graph)[0]` access at ChartRenderer.tsx Line 85 is safe because `convertToPlotlyData` always returns at least one element (Line 74 returns `[makeTrace(...)]`). The type inconsistency, while present, is a minor concern that doesn't rise to BEST-PRACTICE severity for an advisory finding.

---

## Validated Findings

### FE-003 — VALID

| Field | Value |
|-------|-------|
| **Finding ID** | FE-003 |
| **Type** | BEST-PRACTICE |
| **Classification** | advisory |
| **Rationale** | `eslint.config.js` confirms no `eslint-plugin-jsx-a11y` present. This is a valid advisory recommendation for automated accessibility linting. No evidence contradicts this finding.

---

### FE-004 — VALID

| Field | Value |
|-------|-------|
| **Finding ID** | FE-004 |
| **Type** | BEST-PRACTICE |
| **Classification** | advisory |
| **Rationale** | Verified mismatch: `formSchemas.ts` line 56 only requires `min(8)` characters, while `validators.py` lines 199-203 require digit (`r"\d"`) and letter (`r"[a-zA-Z]"`) presence. This user experience improvement is valid and worth implementing.

---

### FE-005 — VALID

| Field | Value |
|-------|-------|
| **Finding ID** | FE-005 |
| **Type** | BEST-PRACTICE |
| **Classification** | advisory |
| **Rationale** | `vite.config.ts` already implements `manualChunks` for plotly (Line 44-46), which is the correct mitigation. The warning exists and the recommendation aligns with current build configuration. This is a valid advisory noting the remaining chunk size concern.

---

## Cross-Phase Conflict Analysis

| Finding Pair | Conflict Status |
|--------------|-----------------|
| FE-001 (bar/pie charts) vs BE-001 (Cyrillic) | No conflict - separate domains |
| FE-002 (null handling) vs any backend finding | No conflict - different layers |
| All other findings | No cross-phase conflicts detected |

---

## Validated Counts Summary

| Phase | Rejected | Reclassified | Mandatory | Advisory |
|-------|----------|--------------|-----------|----------|
| 02-frontend | 2 | 0 | 0 | 3 |

---

## Rollout Safety Assessment

No rollout safety issues detected. All validated findings are advisory improvements that:
- Do not introduce coupling between modules
- Do not rely on fragile insertion points  
- Have clear implementation boundaries
- Can be implemented independently

---

## Validation Notes

1. **FE-001 rejection** follows the SPEC-DEVIATION rejection rule: GraphType enum defines BAR and PIE as supported chart types. The presence of BarChart.tsx and PieChart.tsx implementing these types means they cannot be classified as dead code.

2. **FE-002 rejection** is based on factual error in evidence. While type tightening could be considered, the evidence provided incorrectly attributes the null-safety concern to the wrong location.

3. **FE-003, FE-004, FE-005** pass validation as they represent genuine improvement opportunities without factual errors or architectural conflicts.

4. All rejections documented with SPEC reference (v3.6, line 178) and GraphType enum evidence from `src/mkobi/models/enums.py`.