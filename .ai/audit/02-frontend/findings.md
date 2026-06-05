---
name: 02-frontend-findings
description: Frontend architecture audit findings
agent: audit-executor
alwaysApply: false
---

# Phase 02 Audit Findings — Frontend Architecture

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### FE-001: Russian Language in Production Error Handler

| Field | Value |
|-------|-------|
| **ID** | FE-001 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | frontend/src/shared/api/errorHandler.ts |
| **Classification** | advisory |

**Description:** The error handler contains a hardcoded Russian fallback message ("Произошла ошибка") in production code, violating the project rule that all code, logs, and error messages must be in English. This creates inconsistency and may cause issues if the application needs to be localized or monitored by English-speaking operators.

**Evidence:** `frontend/src/shared/api/errorHandler.ts:97-101`
```typescript
// Generic fallback with Russian message as specified
return {
  code: ErrorCode.INTERNAL_ERROR,
  message: 'Произошла ошибка',
}
```

**Recommendation:** Replace the Russian fallback message with English ("An error occurred") to comply with project standards. The error message localization layer in `errorMessages.ts` can still provide Russian messages to users, but the core error extraction should return English strings.

---

### FE-002: Russian Language in Shared Error Messages

| Field | Value |
|-------|-------|
| **ID** | FE-002 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | frontend/src/shared/api/errorMessages.ts |
| **Classification** | advisory |

**Description:** The shared error message map contains only Russian messages, violating the project rule that all code and messages must be in English. This creates maintenance issues and contradicts the project's multilingual architecture expectations.

**Evidence:** `frontend/src/shared/api/errorMessages.ts:13-53` - Contains messages like "Внутренняя ошибка сервера", "Ошибка аутентификации", "Доступ запрещён", etc.

**Recommendation:** Use English error messages in the shared error message map. Localization can be implemented through a proper i18n system that maps English error codes to user-facing localized strings.

---

### FE-003: Lint Errors in ChartRenderer Component

| Field | Value |
|-------|-------|
| **ID** | FE-003 |
| **Severity** | MEDIUM |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | frontend/src/features/dashboards/ui/charts/ChartRenderer.tsx |
| **Classification** | mandatory |

**Description:** The ChartRenderer component has 4 lint errors that indicate potential runtime issues: unnecessary type assertions and unsafe string conversions. The `@typescript-eslint/no-base-to-string` errors indicate values could become "[object Object]" when converted to strings, which would corrupt chart data display.

**Evidence:** Lint output from `npm run lint`:
- Line 20:12 - Unnecessary type assertion `as Data[]`
- Line 36:12 - Unnecessary type assertion (contextually unnecessary cast)
- Line 43:28 - `'row[colorCol] ?? 'unknown'' will use Object's default stringification format '[object Object]'` when stringified
- Line 44:72 - `'row[xCol]' will use Object's default stringification format '[object Object]'` when stringified

**Recommendation:** 
1. Remove unnecessary type assertions on lines 20 and 36
2. Add proper type checking before string conversion for `row[xCol]` and `row[colorCol]` values to prevent "[object Object]" display in charts

---

### FE-004: Unused Chart Components in Codebase

| Field | Value |
|-------|-------|
| **ID** | FE-004 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | frontend/src/features/dashboards/ui/charts/BarChart.tsx, LineChart.tsx, PieChart.tsx, TableChart.tsx |
| **Classification** | advisory |

**Description:** Four chart component files exist (BarChart, LineChart, PieChart, TableChart) but are never imported anywhere in the application. The application uses `ChartRenderer` which internally uses `PlotlyChart` directly. This is dead code that increases bundle size and maintenance burden.

**Evidence:** 
- `frontend/src/features/dashboards/ui/charts/BarChart.tsx` - exported but never imported
- `frontend/src/features/dashboards/ui/charts/LineChart.tsx` - exported but never imported  
- `frontend/src/features/dashboards/ui/charts/PieChart.tsx` - exported but never imported
- `frontend/src/features/dashboards/ui/charts/TableChart.tsx` - exported but never imported

Grep search for imports of these components returns no matches outside their own definition files.

**Recommendation:** Remove unused chart components or integrate them into the rendering pipeline if they were intended for future use.

---

### FE-005: Hardcoded Status String Instead of Enum

| Field | Value |
|-------|-------|
| **ID** | FE-005 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | frontend/src/features/upload/api/uploadApi.ts |
| **Classification** | mandatory |

**Description:** The upload API hook uses a hardcoded string 'completed' instead of the `ProcessingStatus.COMPLETED` enum value for status comparison, violating the project rule that all constants must use StrEnum/enum types.

**Evidence:** `frontend/src/features/upload/api/uploadApi.ts:53`
```typescript
if (data?.status === 'completed' || data?.status === 'failed') {
```

**Recommendation:** Replace hardcoded strings with enum values:
```typescript
if (data?.status === ProcessingStatus.COMPLETED || data?.status === ProcessingStatus.FAILED) {
```

---

### FE-006: Any Type Usage in PlotlyComponent Wrapper

| Field | Value |
|-------|-------|
| **ID** | FE-006 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | frontend/src/shared/components/PlotlyComponent.tsx |
| **Classification** | advisory |

**Description:** The PlotlyComponent wrapper uses `any` type to work around CJS/ESM interop issues with react-plotly.js, violating the project rule of strict TypeScript with no `any` types. This is currently suppressed via eslint-disable directives.

**Evidence:** `frontend/src/shared/components/PlotlyComponent.tsx:19-24`
```typescript
/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access */
const raw = PlotlyDefault as any
const PlotComponent: ComponentType<PlotlyChartProps> =
  (typeof raw?.default === 'function' ? raw.default : null) ??
  (typeof raw === 'function' ? raw : null)
/* eslint-enable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access */
```

**Recommendation:** Investigate alternative approaches such as using TypeScript's `unknown` type with proper type guards, or consider if the eslint-disable approach is acceptable for this specific CJS/ESM compatibility shim. Document the rationale if suppression is retained.

---

### FE-007: Missing Form Field Labels for Accessibility

| Field | Value |
|-------|-------|
| **ID** | FE-007 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | frontend/src/features/auth/ui/LoginForm.tsx, RegisterForm.tsx |
| **Classification** | advisory |

**Description:** Form fields in LoginForm and RegisterForm use MUI TextField components but do not have explicit `htmlFor` label associations, which is required for proper accessibility (screen readers). While MUI's TextField has internal label handling, explicit associations are recommended for WCAG compliance.

**Evidence:** `frontend/src/features/auth/ui/LoginForm.tsx:71-88`
```tsx
<TextField
  label="Email"
  fullWidth
  margin="normal"
  {...register('email')}
  error={!!errors.email}
  helperText={errors.email?.message}
/>
```

**Recommendation:** Add explicit `inputProps={{ 'aria-label': 'Email' }}` or use `InputLabel` with `htmlFor` to ensure proper accessibility for screen readers.

---

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 3 |
| LOW | 4 |

## Mandatory Fixes

- FE-003: Lint errors in ChartRenderer component (potential runtime data corruption)
- FE-005: Hardcoded status string instead of enum in uploadApi.ts

## Advisory Recommendations

- FE-001: Russian language in production error handler
- FE-002: Russian language in shared error messages  
- FE-004: Unused chart components in codebase
- FE-006: Any type usage in PlotlyComponent wrapper
- FE-007: Missing form field labels for accessibility