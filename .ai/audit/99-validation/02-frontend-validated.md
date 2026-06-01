# Phase 02 Validation Report — Frontend Architecture

**Validator:** audit-validator
**Input:** `.ai/audit/02-frontend/findings.md`
**Date:** 2026-05-31
**Mode:** problems-only

---

## Rejected Findings

### FE-002: setState during render effect in DashboardFilters — REJECTED

**Rejection reason:** The finding mischaracterizes the severity of the pattern. While `setState` inside `useEffect` is indeed an anti-pattern for simple prop-to-state sync, in this specific case the component (`DashboardFilters`) intentionally maintains a **local filter state** that is distinct from the parent's `values` prop. The parent passes `values` as the "committed" filters, while `localFilters` holds "in-progress" filter selections that are only committed when the user clicks "Apply". The `useEffect` sync is needed to reset local state when the parent's value identity changes (e.g., when a different dashboard is loaded or filters are cleared via Reset). This is a valid use case for the pattern (resetting internal state when an external identity changes). Additionally, the `UploadModal.tsx` instance the finding references (`UploadModal.tsx:60`) is a `setFileStates` call in a different `useEffect` that also serves a legitimate purpose (resetting upload state when the modal closes/opens). Neither case is a blind prop-to-state sync that could be replaced with a controlled component. **Rejected**: the pattern is intentionally used for state reset, not naive prop sync.

### FE-007: Missing HTML label associations on form fields — REJECTED

**Rejection reason:** The finding claims MUI `<TextField>` lacks explicit `id`/`htmlFor` associations, implying a11y failures. However, MUI's `<TextField>` component **internally generates** a unique `id` and renders a `<label htmlFor>` that matches the input automatically. The `label` prop on `<TextField>` is rendered as the `<label>` element. This is standard MUI behavior since v5. While adding explicit `ids` would make the associations visible in snapshots and slightly improve a11y debuggability, the current code is **not broken** from an accessibility standpoint — screen readers correctly associate label and input via MUI's internal mechanism. The recommendation to add `eslint-plugin-jsx-a11y` is valid as advisory, but the finding's framing ("missing label associations") overstates the actual problem. **Rejected** as a finding recommending fixes to working code; the `jsx-a11y` plugin suggestion is captured as an advisory note below.

### FE-010: Potential API contract mismatch — UploadMode enum in URL params — REJECTED

**Rejection reason:** The finding speculates a potential mismatch between frontend `UploadMode` enum values and backend `UploadMode` StrEnum values. Evidence has been verified directly: frontend `enums.ts:54` defines `OVERWRITE: 'overwrite'` and `APPEND: 'append'`; backend `models/enums.py:54` defines `OVERWRITE = "overwrite"` and `APPEND = "append"`. The values are **identical**. There is no mismatch, no mapping layer needed, and no risk of 422 errors from enum value misalignment. The finding is **stale** (based on speculation that turned out to be incorrect after verification).

---

## Merged Findings

### FE-003 + FE-004 → Merged as FE-DEAD-CODE (Advisory)

**Original IDs:** FE-003, FE-004
**Merged into:** FE-DEAD-CODE

**Rationale:** Both findings identify dead code — unused components that exist in source files but are never imported, rendered, or exported from any public API. FE-003 covers four chart components (`BarChart`, `LineChart`, `PieChart`, `TableChart`); FE-004 covers `AccessDenied` and `PlaceholderPage`. All six components share the same root cause (dead code that increases bundle size, maintenance surface, and confusion) and the same resolution pathway (remove or integrate). Merging eliminates redundancy.

| Component | Location | Imported? | Notes |
|-----------|----------|-----------|-------|
| `BarChart` | `features/dashboards/ui/charts/BarChart.tsx` | No | Not in `charts/index.ts` exports |
| `LineChart` | `features/dashboards/ui/charts/LineChart.tsx` | No | Not in `charts/index.ts` exports |
| `PieChart` | `features/dashboards/ui/charts/PieChart.tsx` | No | Not in `charts/index.ts` exports |
| `TableChart` | `features/dashboards/ui/charts/TableChart.tsx` | No | Not in `charts/index.ts` exports |
| `AccessDenied` | `shared/components/AccessDenied.tsx` | Exported but never rendered | Exported from `shared/components/index.ts` but no consumer imports it |
| `PlaceholderPage` | `shared/components/PlaceholderPage.tsx` | No | Zero imports in entire `src/` tree |

**Recommendation:** Remove all six components unless they are part of an immediate sprint. If any are planned for near-future use, add a `TODO` comment with a tracking reference.

---

## Reclassified Findings

### FE-001: Reclassified from `advisory` → advisory (no type change, downgraded severity note)

No reclassification of finding type (remains `BEST-PRACTICE`). However, the ESLint `no-console` rule recommendation is separated as a distinct action item since it is a one-time config change independent of the `console.error` removal.

---

## Rollout Safety Analysis

### FE-005 (getToken() outside render cycle)

The `getToken()` calls in `dashboardApi.ts` hooks are **inside** the hook body (lines 33, 42, 55), not at module scope. TanStack Query evaluates the `enabled` option **per render**, and since `getToken()` reads from a module-level `memoryToken` variable (or `sessionStorage` in dev), the value is re-read each time the hook is called. This means:

- In **production** (`USE_MEMORY_STORAGE = true`): `getToken()` reads `memoryToken` in memory — always current for the JS context. The value is `null` after page reload (token lost), so `enabled` correctly stays `false` until login sets a new token and triggers a re-render.
- In **dev** (`USE_MEMORY_STORAGE = false`): `getToken()` reads `sessionStorage` synchronously — always current.

The actual staleness risk is **minimal** because:
1. Token changes always happen through `useAuth` → `setToken()` → state update → re-render.
2. Page reload loses the in-memory token entirely, so `enabled: false` is the correct state.
3. The `enabled` expression `!!accessToken` is re-evaluated on every hook call (render).

However, the **architectural concern** is valid: calling `getToken()` from a standalone module function (`dashboardApi.ts`) rather than from React context couples the data layer to a global module state. The better pattern is to access auth state through `useAuth()` or a query context function. This remains **advisory** — the bug risk in practice is low, but the coupling is suboptimal long-term.

**Rollout risk:** LOW. Fixing this (by passing auth state as a parameter or using context) would be a refactoring with moderate blast radius (3 hooks, plus any future hooks) and should be done as an isolated change.

### FE-009 (ChangePassword confirm_password API contract)

Verified: Backend `ChangePasswordRequest` (`models/auth.py:178-194`) **does** include `confirm_password: str`. The frontend and backend contracts are aligned. The finding's concern was about a potential mismatch — but since both sides include the field, the contract is consistent. The finding passes validation. The recommendation to verify the match server-side is noted: the backend model currently accepts `confirm_password` but **does not validate** `new_password === confirm_password` in the Pydantic model (only `current_password` and `new_password` are non-optional in the service layer). This is a **spec deviation** that should be tracked: either add a `@field_validator` to the backend model or strip `confirm_password` from `ChangePasswordRequest` and handle matching only client-side.

---

## Validated Counts

| Category | Count | Notes |
|----------|-------|-------|
| Total findings | 10 | |
| Rejected | 3 | FE-002, FE-007, FE-010 |
| Merged | 2→1 | FE-003 + FE-004 → FE-DEAD-CODE |
| Reclassified | 0 | No type changes |
| Passed validation (no issues found) | 7 | FE-001, FE-005, FE-006, FE-008, FE-009 (note: see rollout note above), FE-DEAD-CODE (merged) |
| Mandatory | 2 | FE-005, FE-009 |
| Advisory | 5 | FE-001, FE-006, FE-008, FE-DEAD-CODE |

---

## Cross-Phase Conflicts

**None identified.** No findings from Phase 02 conflict with findings from Phase 01 (Backend). FE-009 was cross-checked against the backend `ChangePasswordRequest` model and found to be consistent (both sides define `confirm_password`). FE-010 was cross-checked against `UploadMode` StrEnum and found to be a false positive (values match exactly).

---

## Advisory Notes

1. **FE-001 ESLint addition:** Adding `no-console: "warn"` to `eslint.config.js` is recommended as a one-time config change to prevent future `console.*` regressions.
2. **FE-007 jsx-a11y plugin:** While the label association finding was rejected (MUI handles it), adding `eslint-plugin-jsx-a11y` to ESLint config would provide broader accessibility linting coverage. This is a general improvement, not a fix for a specific broken case.
3. **FE-005 architectural note:** While the current `getToken()` pattern works in practice, replacing it with context-based auth state access in `dashboardApi.ts` hooks would reduce global state coupling and improve testability. Recommended as a future refactoring, not a blocking fix.
