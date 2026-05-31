---
name: 02-frontend-validated
description: Frontend Audit Validation Report
status: complete
phase: 02-frontend
---

# Phase 02 Frontend — Validation Report

**Validator:** validator agent
**Source findings:** `.ai/audit/02-frontend/findings.md`
**Scope:** Frontend Architecture (6 findings)
**Mode:** problems-only

---

## Rejected Findings

### FE-001: API Contract Mismatch - Missing graph_id Query Parameter
- **Original type:** RUNTIME-ERROR
- **Original severity:** CRITICAL
- **Rejection reason (INACCURATE / MISDIAGNOSED):** The finding is partially correct in identifying a contract mismatch, but mischaracterizes the backend's behavior and proposes an incorrect fix.

  **Evidence from current codebase:**
  - Backend `data.py:49`: `graph_id: UUID = Query(..., description="Graph ID")` — this is a required query parameter.
  - Backend `data.py:142-151`: The endpoint returns `{"graphs": [...], ...}` — a `{graphs: [...]}` envelope with a single graph per the required `graph_id`.
  - Frontend `api.types.ts:134-137`: `AggregatedDataRequest` only has `dashboard_id` + `filters`, missing `graph_id`.
  - Frontend `DashboardView.tsx:138-149`: Iterates `aggregatedData.graphs` array.
  - Frontend `dashboardApi.ts:63-64`: `useAggregatedData` calls `getAggregatedData({ dashboard_id, filters })` without `graph_id`.

  **The finding's claim is correct:** the frontend will indeed get HTTP 422 because `graph_id` is required. However, the finding's recommendation is wrong. It states "DashboardView needs to iterate over graphs and fetch data for each" — but the backend endpoint returns only ONE graph per call (it filters by `graph_id`). The endpoint's docstring says "Returns data for all dashboard charts" but the implementation returns only the single `graph_id` requested. The real problem is an architectural mismatch:

  - Either the backend should provide a `/data/aggregated` endpoint that accepts `dashboard_id` alone and returns ALL graphs, OR
  - The frontend must iterate over dashboard graphs and make one call per `graph_id`.

  The finding proposes the latter (frontend iterates per `graph_id`), but does not acknowledge that the backend's docstring/description contradicts its own implementation. The fix target is ambiguous — both sides of the contract are wrong. The finding oversimplifies by blaming the frontend alone.

  **Verdict: REJECTED as stated.** The issue is a cross-cutting API contract design problem, not a frontend-only bug. Recommendation: Replan as a combined backend+frontend task to either (a) add a `dashboard_id`-only aggregated endpoint that returns all graphs, or (b) update the frontend to fetch per-graph with `graph_id`. The current finding's recommendation is speculative about which side should change.

---

## Merged Findings

No findings merge candidates. All 6 findings address distinct issues.

---

## Reclassified Findings

No reclassifications. All type labels are appropriate for the issues identified (after accounting for FE-001 rejection).

---

## Cross-Phase Conflicts

### FE-001 vs. Backend Phase (data.py design conflict)
- **Conflict:** FE-001 identifies that the `/data/aggregated` backend endpoint requires `graph_id` but the frontend doesn't send it. However, the endpoint's own description (`data.py:41`) says "Returns data for all dashboard charts with applied filters" yet it requires a specific `graph_id`. This is a backend-side documentation/contract inconsistency that the backend audit (Phase 01) did not catch.
- **Note:** Phase 01 findings do not reference `data.py` at all — the data route was not audited for parameter semantics. This is a gap in Phase 01 coverage, not a direct conflict.
- **Resolution:** Regardless of FE-001's rejection, the backend `data.py:41` docstring should be corrected to reflect that the endpoint returns data for ONE graph (the specified `graph_id`), not "all dashboard charts." This is a DOC-UPDATE advisory item for the backend phase.

---

## Rollout Safety Issues

### FE-004 (Hardcoded Layout UUIDs) — Low risk, isolated change
- If replaced with a dynamic `/layouts` endpoint, this requires a backend API addition + frontend change. The two changes are coupled and must be rolled out together or with backward-compatible fallback.
- **Risk:** MEDIUM. Adding a new backend endpoint is a safe isolated change, but the frontend must handle the case where the endpoint does not exist yet (graceful degradation).
- **Recommendation:** Roll out the backend `/layouts` endpoint first, then update the frontend. Do not bundle into a single atomic deploy.

### FE-005 (Accessibility attributes) — Zero risk, trivially isolated
- Purely a frontend template change. No API changes, no side effects.
- **Recommendation:** Can be rolled out independently at any time.

### FE-002 (Unused getFilter) and FE-003 (Unused chart exports) — Zero risk
- Both are dead-code cleanup. Removing unused exports/functions has zero runtime risk.
- **Caveat for FE-003:** Exported names `BarChart`, `LineChart`, `PieChart`, `TableChart` are exported from `charts/index.ts`. While no internal code imports them, removing exports could break external consumers if any exist outside the search scope. Safe to remove but verify no dynamic imports reference them.

---

## Validated Counts

| Category | Count |
|----------|-------|
| **Total findings** | 6 |
| **Rejected** | 1 (FE-001) |
| **Merged** | 0 |
| **Reclassified** | 0 |
| **Validated as-is** | 5 (FE-002, FE-003, FE-004, FE-005, FE-006) |
| **Mandatory fixes (post-validation)** | 1 (FE-006) |
| **Advisory recommendations (post-validation)** | 4 (FE-002, FE-003, FE-004, FE-005) |

### Mandatory fixes
- **FE-006:** API Contract Mismatch - Missing dashboard_id in grantDashboardAccess Body — RUNTIME-ERROR
  - Verified: `GrantAccessRequest` (line 220-223 of `api.types.ts`) has only `user_id` + `permission`. Backend `AccessGrant` model (`access.py:25-30`) requires `dashboard_id` as a mandatory field. The backend route (`dashboards_access.py:72-81`) explicitly checks body `dashboard_id` against path `dashboard_id`. The frontend will get HTTP 422. Fix is clear and isolated: add `dashboard_id` to the request body in `adminApi.ts:83-85`.

### Advisory recommendations
- **FE-002:** Unused getFilter API Function — BEST-PRACTICE
  - Verified: `getFilter` is defined at `dashboardApi.ts:32-35` but zero usages found across all `.ts`/`.tsx` files. Safe to remove.
- **FE-003:** Unused Chart Component Exports — BEST-PRACTICE
  - Verified: `BarChart`, `LineChart`, `PieChart`, `TableChart` exported from `charts/index.ts:2-4` but zero imports found in any `.ts`/`.tsx` file. `PlotlyChart` is the only chart component used.
- **FE-004:** Hardcoded Layout UUID Mapping in Admin API — SPEC-DEVIATION
  - Verified: `adminApi.ts:48-53` hardcodes three UUIDs that must match seed data. Fragile coupling, but functional as long as seeds are stable. Dynamic lookup is architecturally cleaner.
- **FE-005:** Missing Accessibility Attributes in TableChart — BEST-PRACTICE
  - Verified: `TableChart.tsx:33-54` uses plain `<table>` without `scope="col"`, `<caption>`, or ARIA labels. Standard accessibility improvement.
