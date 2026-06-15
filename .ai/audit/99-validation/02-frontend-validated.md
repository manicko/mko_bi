# Phase 02 Validation Report — Frontend Architecture

**Validator:** validator
**Source:** `.ai/audit/02-frontend/findings.md`
**Date:** 2026-06-15

---

## Rejected Findings

### FE-001: PlaceholderPage is dead code — REJECTED

| Field | Value |
|-------|-------|
| **ID** | FE-001 |
| **Original Type** | BEST-PRACTICE |
| **Reason** | SPEC-DEVIATION INVALID — Code is spec-compliant |

**Evidence:**
- SPEC.md line 178 explicitly specifies: `PlaceholderPage for route stubs` — provides a standardized "coming soon" UI for routes that exist in navigation but lack full implementation
- SPEC.md line 128 confirms: `Upload as modal dialog` — UploadModal is implemented as embedded in DashboardView (not as separate page)
- SPEC.md line 129: `Dashboard access management` — endpoints exist at `/api/v1/dashboards/{id}/access` (backend implementation verified in `src/mkobi/api/routes/dashboards_access.py`)
- The component has a `@see PLAN_02.md` reference in its docstring (line 20), indicating intentional design
- Component is exported from barrel file and documented in frontend structure docs (`docs/07-frontend/fsd-structure.md` lines 175, 184-190)

**Conclusion:** PlaceholderPage is spec-required infrastructure for future route stubs. The SPEC explicitly defines when and how it should be used (for routes in navigation but not yet implemented). The finding incorrectly classified spec-compliant code as dead code. Not a violation.

### FE-005: Permanently disabled "Access" button — REJECTED

| Field | Value |
|-------|-------|
| **ID** | FE-005 |
| **Original Type** | BEST-PRACTICE |
| **Reason** | SPEC-DEVIATION INVALID — Code is spec-compliant |

**Evidence:**
- SPEC.md line 129: `Dashboard access management — Admins grant, list, and revoke dashboard access via dedicated endpoints`
- Backend endpoints exist and are functional: `POST/GET/DELETE /api/v1/dashboards/{id}/access` (verified in `dashboards_access.py`)
- The disabled button follows the SPEC-provided guidance: "Not for in-page elements (use disabled button + tooltip)"
- This is a UI stub indicating the backend feature exists but frontend integration is incomplete — exactly the pattern described in SPEC

**Conclusion:** The disabled button is intentional UI communication that access management exists as a backend feature. The SPEC explicitly states to use "disabled button + tooltip" for in-page elements when the feature is coming soon. This is correct architectural communication, not dead code or unnecessary clutter.

---

## Validated Findings

All other findings (FE-002 through FE-004, FE-006 through FE-010) remain valid as BEST-PRACTICE advisory recommendations. No cross-phase conflicts identified with BE-001 through BE-004 from the backend audit.

### FE-002: generateShortId() is defined but never called
- **Status:** VALID
- **Evidence:** Function defined in `shortUuid.ts` (line 25-27), grep confirms zero call sites
- **Classification:** Advisory — Low value cleanup opportunity

### FE-003: getProfile() duplicated across authApi and userApi
- **Status:** VALID
- **Evidence:** Identical implementations in both files (authApi.ts:21-23, userApi.ts:4-6), both calling `/auth/me`
- **Classification:** Advisory — Duplication increases maintenance surface

### FE-004: UploadModal eagerly imported — breaks lazy-loading pattern
- **Status:** VALID
- **Evidence:** Static import in DashboardView.tsx:13 vs lazy() pattern in routes.tsx:13-35
- **Classification:** Advisory — Bundle size optimization opportunity

### FE-006: Inconsistent import paths for useAuth
- **Status:** VALID
- **Evidence:** RegisterForm.tsx:4 imports `from '../'`, LoginForm.tsx:7 imports `from '../model/useAuth'`
- **Classification:** Advisory — Stylistic inconsistency

### FE-007: ErrorPage triggers unnecessary useAuth() call
- **Status:** VALID
- **Evidence:** ErrorPage.tsx:12 calls useAuth for unauthenticated users hitting error pages
- **Classification:** Advisory — Unnecessary API calls on error pages

### FE-008: LogViewer Dashboard filter is non-functional (empty dropdown)
- **Status:** VALID
- **Evidence:** LogViewer.tsx:78-85 has `{/* TODO: Load dashboards for filter */}` with empty dropdown
- **Classification:** Advisory — Confusion risk for admin users

### FE-009: UploadModal polling may double-invoke onUploadComplete callback
- **Status:** VALID
- **Evidence:** UploadModal.tsx:74-78 calls callback when status is 'completed', handleClose can fire separately
- **Classification:** Advisory — Potential duplicate API calls

### FE-010: DashboardFilters local state may desync from parent
- **Status:** VALID
- **Evidence:** DashboardFilters.tsx:32-41 uses object reference comparison which could miss external resets
- **Classification:** Advisory — Fragile state management pattern

---

## Cross-Phase Conflicts

None identified. Frontend and backend audits are consistent:
- No conflicting reports on test status (both report passing with minor failures)
- No conflicting reports on authentication coverage
- No conflicting reports on API contract compliance

---

## Rollout Safety Assessment

All validated advisory findings are low-risk:
- FE-002, FE-001 (rejected), FE-005 (rejected): Pure removals/additions with no runtime impact
- FE-003: Import-only change, no logic modification
- FE-004: React lazy() conversion, well-established pattern
- FE-006: Cosmetic import path standardization
- FE-007, FE-008, FE-009, FE-010: All involve internal logic refactoring with no public API changes

---

## Summary

| Finding ID | Status |
|------------|--------|
| FE-001 | REJECTED (spec-compliant) |
| FE-002 | VALIDATED |
| FE-003 | VALIDATED |
| FE-004 | VALIDATED |
| FE-005 | REJECTED (spec-compliant) |
| FE-006 | VALIDATED |
| FE-007 | VALIDATED |
| FE-008 | VALIDATED |
| FE-009 | VALIDATED |
| FE-010 | VALIDATED |

---

## Actionable Recommendations

### FE-002: Remove unused `generateShortId()`

**File:** `frontend/src/shared/utils/shortUuid.ts`

**Change:** Remove lines 20-27 (the `generateShortId` function and its JSDoc):

```typescript
// REMOVE this entire block (lines 20-27):
/**
 * Generates a new short ID by creating a UUID v4 and returning first 8 characters.
 * Uses crypto.randomUUID() for secure random generation.
 * @returns An 8-character short ID
 */
export function generateShortId(): string {
  return crypto.randomUUID().slice(0, SHORT_ID_LENGTH)
}
```

**Rationale:** `generateShortId()` has zero call sites across the entire codebase. The `shortUuid()` function (which truncates existing UUIDs for display) is the actively used export, imported by 3 files. Dead code increases maintenance surface and bundle size for no benefit. If random ID generation is needed in the future, `crypto.randomUUID()` can be called directly at the call site.

---

### FE-003: Consolidate duplicate `getProfile()` into a single source

**File:** `frontend/src/features/users/api/userApi.ts`

**Change:** Remove the local `getProfile` definition and re-export from `authApi`:

```typescript
// REPLACE the entire file content with:
import { axiosInstance } from '../../../shared/api/axiosInstance'
import type { UserProfile, ChangePasswordRequest } from '../../../shared/types/api.types'
import { getProfile } from '../../auth/api/authApi'

// Re-export getProfile from authApi as the single source of truth
export { getProfile }

export async function deleteAccount(): Promise<void> {
  await axiosInstance.delete('/users/me')
}

export async function changePassword(data: ChangePasswordRequest): Promise<void> {
  await axiosInstance.post('/auth/change-password', data)
}
```

**File:** `frontend/src/features/users/index.ts` (barrel file — update if it re-exports `getProfile` from `userApi`)

**Rationale:** Both `authApi.ts:21-23` and `userApi.ts:4-6` contain identical `getProfile()` implementations calling `GET /auth/me`. This violates DRY and creates a maintenance risk — if the endpoint changes, both must be updated. The auth feature owns authentication, so `authApi.ts` should be the single source of truth. The `userApi.ts` version is a leftover from before the auth feature was consolidated.

---

### FE-004: Convert `UploadModal` import to lazy() in DashboardView

**File:** `frontend/src/features/dashboards/ui/DashboardView.tsx`

**Change 1 — Replace the static import (line 13) with a lazy import at the top of the file:**

```typescript
// REPLACE line 13:
import { UploadModal } from '../../upload/ui/UploadModal'

// WITH a lazy import (add near the top, after existing imports):
const UploadModal = lazy(() =>
  import('../../upload/ui/UploadModal').then((module) => ({ default: module.UploadModal as ComponentType })),
)
```

**Change 2 — Add required imports at the top:**

```typescript
// ADD to existing React import (line 1):
import { useCallback, useState, lazy, Suspense } from 'react'

// ADD a new import after line 2:
import type { ComponentType } from 'react'
```

**Change 3 — Wrap the JSX usage in a Suspense boundary (around line 156):**

```typescript
// REPLACE:
<UploadModal
  open={uploadModalOpen}
  onClose={() => setUploadModalOpen(false)}
  dashboardId={id || ''}
  onUploadComplete={() => {
    setUploadModalOpen(false)
    if (id) {
      void invalidateAggregatedData(id)
    }
  }}
/>

// WITH:
<Suspense fallback={null}>
  <UploadModal
    open={uploadModalOpen}
    onClose={() => setUploadModalOpen(false)}
    dashboardId={id || ''}
    onUploadComplete={() => {
      setUploadModalOpen(false)
      if (id) {
        void invalidateAggregatedData(id)
      }
    }}
  />
</Suspense>
```

**Rationale:** The routes file (`routes.tsx:13-35`) lazy-loads all route components including `DashboardView`, but the static `UploadModal` import creates a eager dependency chain: `DashboardView → UploadModal → uploadApi → ...`. This means the upload feature code is loaded on every dashboard view visit, even though the modal is only rendered when `uploadModalOpen === true` (which requires the "Upload Data" button click, itself gated behind `canEdit`). The `fallback={null}` is appropriate because the modal is hidden until explicitly opened — there's no visual flash.

---

### FE-006: Standardize `useAuth` import path in RegisterForm

**File:** `frontend/src/features/auth/ui/RegisterForm.tsx`

**Change:** Replace the barrel import with the direct path:

```typescript
// REPLACE line 4:
import { useAuth } from '../'

// WITH:
import { useAuth } from '../model/useAuth'
```

**Rationale:** `LoginForm.tsx:7` already uses the direct path `'../model/useAuth'`. The barrel import `'../'` works because `features/auth/index.ts` re-exports `useAuth`, but it's an unnecessary indirection that obscures the actual module dependency. The direct path is consistent with `LoginForm.tsx`, `ErrorPage.tsx:4`, and `routes.tsx:10` — all of which import from the explicit `useAuth` module path. This also makes refactoring easier since barrel files can mask circular dependency issues.

---

### FE-007: Remove unnecessary `useAuth()` call from ErrorPage

**File:** `frontend/src/shared/components/ErrorPage.tsx`

**Change 1 — Remove the `useAuth` import and call (lines 4, 12):**

```typescript
// REMOVE line 4:
import { useAuth } from '../../features/auth/model/useAuth'

// REMOVE line 12:
const { user } = useAuth()
```

**Change 2 — Simplify the `goToHome` logic (line 14):**

```typescript
// REPLACE line 14:
const goToHome = user ? '/dashboards' : '/login'

// WITH:
const goToHome = '/login'
```

**Rationale:** `ErrorPage` is rendered for unauthenticated users hitting 404/500 errors (via the `ErrorBoundary` and `NotFound` routes). In this context, the user is never authenticated — if they were, they'd be inside the `ProtectedRoute` wrapper which handles auth. The `useAuth()` call triggers a token refresh attempt and profile fetch on every error page render, causing unnecessary API calls and potential error toasts for users who are already in a broken state. Hardcoding `goToHome = '/login'` is correct because: (1) unauthenticated users should go to login, (2) authenticated users never reach this component through normal flow.

---

### FE-008: Implement dashboard filter dropdown in LogViewer

**File:** `frontend/src/features/admin/ui/LogViewer.tsx`

**Change 1 — Add the `useQuery` import and a dashboard list query (after line 19):**

```typescript
// ADD import (modify line 19):
import { getLogs, getDashboardsAdmin } from '../api/adminApi'
```

**Change 2 — Add a query for dashboards inside the `LogViewer` component (after line 47):**

```typescript
// ADD after line 47 (const [appliedFilters, ...)):
const { data: dashboards = [] } = useQuery({
  queryKey: ['admin', 'dashboards'],
  queryFn: getDashboardsAdmin,
})
```

**Change 3 — Replace the TODO comment with actual dashboard menu items (lines 83-84):**

```typescript
// REPLACE:
<MenuItem value="">All</MenuItem>
{/* TODO: Load dashboards for filter */}

// WITH:
<MenuItem value="">All</MenuItem>
{dashboards.map((dashboard) => (
  <MenuItem key={dashboard.id} value={dashboard.id}>
    {dashboard.name}
  </MenuItem>
))}
```

**Rationale:** `getDashboardsAdmin()` already exists in `adminApi.ts:93-95` and returns `DashboardAdmin[]` with `id` and `name` fields. The `useQuery` hook is already used in this component for `getLogs`. The filter's `onChange` handler (line 81) already sets `dashboard_id` in filters, and `getLogs()` (line 133) already passes `LogFilters` to the backend which supports `dashboard_id` filtering. This is a 3-line implementation that completes an existing feature.

---

### FE-009: Add guard against double-invoke of `onUploadComplete` callback

**File:** `frontend/src/features/upload/ui/UploadModal.tsx`

**Change — Add a ref-based guard to prevent duplicate callback invocation:**

```typescript
// ADD after line 53 (after onUploadCompleteRef declaration):
const hasCompletedRef = useRef(false)

// MODIFY the completion check (around line 74-78):
if (status === 'completed') {
  toast.success('Processing complete!')
  setProcessingFinished(true)
  if (!hasCompletedRef.current) {
    hasCompletedRef.current = true
    onUploadCompleteRef.current?.()
  }
}
```

**Change — Reset the guard in handleClose (after line 194):**

```typescript
// ADD after setProcessingFinished(false) in handleClose (line 194):
hasCompletedRef.current = false
```

**Rationale:** The polling effect (line 60-97) fires every 2 seconds via `useProcessingStatus`. When status becomes `'completed'`, `onUploadCompleteRef.current?.()` is called. However, `handleClose` (line 188-197) can also trigger `onClose()` which may call the same callback from the parent (e.g., `DashboardView` calls `invalidateAggregatedData`). Without a guard, the callback fires once from the polling effect and potentially again from the close handler's state reset chain. The `useRef` guard ensures exactly one invocation per upload cycle, and resetting it in `handleClose` prepares for the next upload session.

---

### FE-010: Fix DashboardFilters state desync with deep comparison

**File:** `frontend/src/features/dashboards/ui/DashboardFilters.tsx`

**Change — Replace the object reference comparison with a deep equality check:**

```typescript
// REPLACE the useEffect (lines 38-41):
useEffect(() => {
  // eslint-disable-next-line react-hooks/set-state-in-effect
  setLocalFilters(values || {})
}, [values])

// WITH:
import { isEqual } from 'lodash-es'  // ADD to imports at top

useEffect(() => {
  // eslint-disable-next-line react-hooks/set-state-in-effect
  setLocalFilters((prev) => {
    const next = values || {}
    return isEqual(prev, next) ? prev : next
  })
}, [values])
```

**Alternative (no new dependency) — Use JSON serialization for comparison:**

```typescript
// REPLACE the useEffect (lines 38-41):
useEffect(() => {
  // eslint-disable-next-line react-hooks/set-state-in-effect
  setLocalFilters(values || {})
}, [values])

// WITH:
useEffect(() => {
  // eslint-disable-next-line react-hooks/set-state-in-effect
  setLocalFilters((prev) => {
    const next = values || {}
    return JSON.stringify(prev) === JSON.stringify(next) ? prev : next
  })
}, [values])
```

**Rationale:** The current `useEffect` dependency on `values` uses object reference comparison. When the parent (`DashboardView`) resets filters via `handleFilterChange({})`, it creates a new empty object each time — which works. But if the parent ever passes the same filter values (e.g., from a cached or memoized source), the reference won't change and `localFilters` won't sync. The functional updater with deep comparison ensures: (1) actual value changes always propagate, (2) identical values don't trigger unnecessary re-renders, (3) external resets are always reflected. The `JSON.stringify` approach avoids adding `lodash-es` as a dependency and is safe here because filter values are plain primitives/arrays (no circular references, dates, or special objects).