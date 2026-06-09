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

---

## Findings

### FE-001: Unwired chart components - BarChart and PieChart exist but are never imported or used

| Field | Value |
|-------|-------|
| **ID** | FE-001 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/features/dashboards/ui/charts/BarChart.tsx`, `frontend/src/features/dashboards/ui/charts/PieChart.tsx` |
| **Classification** | advisory |

**Description:** The `BarChart` and `PieChart` components are defined in separate files under `features/dashboards/ui/charts/` but are never imported, exported, or used anywhere in the codebase. The `ChartRenderer` component handles bar, line, pie, and table chart types but only uses `LineChart` and `TableChart` components directly - bar and pie charts are rendered through `PlotlyChart` instead. According to SPEC.md v3.6, "Charts under dashboards feature — Chart components reside in features/dashboards/ui/charts/ as dashboard-specific UI. No standalone features/charts/ module is needed." The bar and pie chart components should either be integrated into ChartRenderer or removed as dead code.

**Evidence:**
- `BarChart.tsx` exists at line 1-28 but no imports found in any `.ts` or `.tsx` files
- `PieChart.tsx` exists at line 1-17 but no imports found in any `.ts` or `.tsx` files
- `ChartRenderer.tsx` line 2-3 imports: `import { PlotlyChart } from './PlotlyChart'`, `import { LineChart } from './LineChart'`, `import { TableChart } from './TableChart'` - no BarChart or PieChart imports
- `charts/index.ts` line 1-2 exports only `PlotlyChart` and `ChartRenderer` - BarChart and PieChart not exported

**Recommendation:** Either integrate BarChart and PieChart into ChartRenderer, or remove them as dead code. If they provide no additional value beyond PlotlyChart, they should be deleted to reduce code bloat.

---

### FE-002: LineChart component lacks null/empty data handling and type safety

| Field | Value |
|-------|-------|
| **ID** | FE-002 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/dashboards/ui/charts/LineChart.tsx` |
| **Classification** | advisory |

**Description:** The `LineChart` component (line 12-27) passes data directly to `PlotlyChart` without handling cases where `data` might be null, undefined, or have empty/missing x/y arrays. This could cause runtime crashes when rendering charts with minimal or no data. Additionally, the `partial<Layout>` type should be `Partial<Layout>` (lowercase 'p').

**Evidence:**
- `LineChart.tsx` line 5: `layout?: Layout` should be `layout?: Partial<Layout>`
- `LineChart.tsx` line 19-24: `chartLayout` uses `title?.text || ''` but no guard for null data
- `ChartRenderer.tsx` line 84-86: `convertToPlotlyData(graph)[0]` called without checking if array is empty for line charts

**Recommendation:** Add null/empty data guard in LineChart component. Change `layout?: Layout` to `layout?: Partial<Layout>` for proper type consistency.

---

### FE-003: Missing ESLint accessibility plugin - no automated accessibility linting

| Field | Value |
|-------|-------|
| **ID** | FE-003 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | Frontend ESLint configuration |
| **Classification** | advisory |

**Description:** The ESLint configuration in `eslint.config.js` does not include an accessibility linting plugin (such as `eslint-plugin-jsx-a11y`). While some components have manual ARIA attributes (e.g., FileDropzone has `aria-label`, `aria-describedby`), there is no automated linting to catch accessibility issues.

**Evidence:**
- `eslint.config.js` line 1-38 includes: `js.configs.recommended`, `tseslint.configs.recommendedTypeChecked`, `reactHooks.configs.flat.recommended`, `reactRefresh.configs.vite` - no `jsx-a11y` plugin

**Recommendation:** Add `eslint-plugin-jsx-a11y` to the ESLint configuration for automated accessibility linting.

---

### FE-004: Missing password strength validation in frontend - allows weak passwords that backend will reject

| Field | Value |
|-------|-------|
| **ID** | FE-004 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/shared/types/formSchemas.ts` |
| **Classification** | advisory |

**Description:** The frontend `changePasswordSchema` (line 54-61) only validates that the password is at least 8 characters and matches confirmation. However, the backend `validate_password_or_raise` function in `src/mkobi/utils/validators.py` (line 183-205) requires: minimum 8 characters, at least one digit, and at least one letter. This mismatch means users can submit passwords that pass frontend validation but are rejected by the backend, resulting in confusing error messages.

**Evidence:**
- `formSchemas.ts` line 56: `z.string().min(8, { error: 'Password must be at least 8 characters' })` - no digit/letter requirements
- `validators.py` line 196-203: Backend checks for digit (`re.search(r"\d", password)`) and letter (`re.search(r"[a-zA-Z]", password)`) - not mirrored in frontend

**Recommendation:** Add frontend validation to match backend password strength requirements (at least one digit and one letter in addition to minimum 8 characters).

---

### FE-005: Build warning about large chunk size for plotly library

| Field | Value |
|-------|-------|
| **ID** | FE-005 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/vite.config.ts` |
| **Classification** | advisory |

**Evidence:**
- `npm run build` output shows: "Some chunks are larger than 500 kB after minification" for `plotly-BxTkdUEp.js` (4.6MB)

**Recommendation:** Consider code-splitting for plotly or increasing `chunkSizeWarningLimit` in vite.config.ts as documentation.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 3 |
| LOW | 2 |

## Advisory Recommendations

- FE-001: Remove or integrate unwired BarChart and PieChart components
- FE-002: Add null/empty data handling to LineChart component and fix type definition
- FE-003: Add eslint-plugin-jsx-a11y for automated accessibility linting
- FE-004: Add password strength validation to match backend requirements
- FE-005: Address large plotly bundle size with code-splitting or configuration adjustment

---