---
name: audit-findings
description: Phase 02 frontend architecture audit findings
agent: auditor
alwaysApply: false
---

# Phase 02 Audit Findings — Frontend Architecture

**Executor:** auditor
**Template:** .kilo/commands/audit/phases/02-audit-frontend.md
**Status:** complete
**Validated:** no

---

## Runtime Verification Summary

| Step | Result |
|------|--------|
| R1 — Build | PASS — `tsc -b && vite build` succeeded (12820 modules, 20.88s). Warning: plotly.js chunk >500kB. |
| R2 — TypeScript | PASS — `tsc -b --noEmit` zero errors. `strict: true` enabled in tsconfig.app.json. |
| R3 — Lint | PASS — `eslint .` zero errors, zero warnings. |
| R4 — Tests | PASS — 165 tests passed across 12 test files. Coverage: 69.59% statements, 54.96% branches, 65.07% functions, 70.69% lines. |
| R5 — Dead Code | 2 items found: `PlaceholderPage` (exported, never imported), `generateShortId()` (defined, never called). |
| R6 — API Contract | PASS — all frontend API calls have matching backend routes (path + method). No mismatches. |

---

## Findings

### FE-001: PlaceholderPage is dead code — exported but never used

| Field | Value |
|-------|-------|
| **ID** | FE-001 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/shared/components/PlaceholderPage.tsx`, `frontend/src/shared/components/index.ts` |
| **Classification** | advisory |

**Description:** `PlaceholderPage` is exported from the shared components barrel (`index.ts`, line 9) but is never imported or rendered anywhere in the application. No route, feature, or test references it. It is a "planned but not yet implemented" stub that has no active consumers.

**Evidence:**
- `frontend/src/shared/components/index.ts:9` — `export { PlaceholderPage } from './PlaceholderPage'`
- `frontend/src/shared/components/PlaceholderPage.tsx:22` — component definition
- Grep for `PlaceholderPage` across `frontend/src/` returns only the export and definition — zero imports

**Recommendation:** Investigate whether `PlaceholderPage` is planned for a near-future feature. If yes, add a `@see` reference or TODO comment linking to the tracking issue. If not, remove the component and its barrel export to reduce bundle size and maintenance surface.

---

### FE-002: generateShortId() is defined but never called

| Field | Value |
|-------|-------|
| **ID** | FE-002 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/shared/utils/shortUuid.ts` |
| **Classification** | advisory |

**Description:** `generateShortId()` (line 25) is a public function that generates a UUID v4 and returns the first 8 characters. It is never called anywhere in the application. Only `shortUuid()` (which truncates an existing ID) is used.

**Evidence:**
- `frontend/src/shared/utils/shortUuid.ts:25-27` — function definition
- Grep for `generateShortId` across `frontend/src/` returns only the definition — zero call sites

**Recommendation:** Remove `generateShortId()` or document it as a utility reserved for future use. If kept, add a comment explaining why it exists (e.g., "Reserved for future ID generation feature").

---

### FE-003: getProfile() duplicated across authApi and userApi

| Field | Value |
|-------|-------|
| **ID** | FE-003 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/auth/api/authApi.ts`, `frontend/src/features/users/api/userApi.ts` |
| **Classification** | advisory |

**Description:** The `getProfile()` function is defined in both `authApi.ts` (line 21-23) and `userApi.ts` (line 4-6), both making an identical `GET /auth/me` call. `useAuth.ts` imports from `authApi`, while `UserProfile.tsx` imports from `userApi`. This creates two independent API functions for the same endpoint, increasing maintenance surface and risk of divergence.

**Evidence:**
- `frontend/src/features/auth/api/authApi.ts:21-23`:
  ```ts
  export async function getProfile(): Promise<UserProfile> {
    const response = await axiosInstance.get<UserProfile>('/auth/me')
    return response.data
  }
  ```
- `frontend/src/features/users/api/userApi.ts:4-6`:
  ```ts
  export async function getProfile(): Promise<UserProfile> {
    const response = await axiosInstance.get<UserProfile>('/auth/me')
    return response.data
  }
  ```
- `frontend/src/features/users/ui/UserProfile.tsx:5` — imports from `userApi`
- `frontend/src/features/auth/model/useAuth.ts:4` — imports from `authApi`

**Recommendation:** Consolidate `getProfile()` into a single source (e.g., `authApi.ts`) and have `UserProfile.tsx` import from there. Remove the duplicate from `userApi.ts`. This ensures one source of truth for the `/auth/me` endpoint.

---

### FE-004: UploadModal is eagerly imported — breaks lazy-loading pattern

| Field | Value |
|-------|-------|
| **ID** | FE-004 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/dashboards/ui/DashboardView.tsx` |
| **Classification** | advisory |

**Description:** All route-level components in `routes.tsx` use `React.lazy()` for code splitting (LoginForm, RegisterForm, DashboardList, DashboardView, AdminPanel, UserProfile, ChangePasswordPage). However, `DashboardView.tsx` eagerly imports `UploadModal` (line 13) with a static `import` statement, meaning the upload modal code is always loaded even when the user is on a different route.

**Evidence:**
- `frontend/src/features/dashboards/ui/DashboardView.tsx:13`:
  ```ts
  import { UploadModal } from '../../upload/ui/UploadModal'
  ```
- `frontend/src/app/routes.tsx:13-35` — all other route components use `lazy(() => import(...))`
- `UploadModal` depends on `FileDropzone`, `useProcessingStatus`, and multiple MUI components — a non-trivial bundle addition

**Recommendation:** Convert `UploadModal` to a lazy import inside `DashboardView.tsx` using `React.lazy()` and wrap the usage in `<Suspense>` with a fallback. This maintains the code-splitting pattern and reduces initial bundle size for users who never open the upload modal.

---

### FE-005: Permanently disabled "Access" button in DashboardManagement

| Field | Value |
|-------|-------|
| **ID** | FE-005 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/admin/ui/DashboardManagement.tsx` |
| **Classification** | advisory |

**Description:** The dashboard management grid includes a permanently disabled "Access (coming soon)" button (line 187-189) with `disabled` prop and a `title` attribute. This UI element provides no value to admin users and creates visual clutter. The `grantDashboardAccess` API function exists in `adminApi.ts` (line 125-130) but is not wired to any UI.

**Evidence:**
- `frontend/src/features/admin/ui/DashboardManagement.tsx:187-189`:
  ```tsx
  <GridActionsCellItem
    icon={<AccessIcon />}
    label="Access (coming soon)"
    disabled
    title="Access management is not yet implemented"
  />
  ```
- `frontend/src/features/admin/api/adminApi.ts:125-130` — `grantDashboardAccess` function exists but is never called from the frontend

**Recommendation:** Remove the disabled button until the access management feature is implemented. When implemented, wire it to the existing `grantDashboardAccess` API function. This reduces UI clutter and avoids confusing admin users with non-functional controls.

---

### FE-006: Inconsistent import paths for useAuth

| Field | Value |
|-------|-------|
| **ID** | FE-006 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/auth/ui/RegisterForm.tsx`, `frontend/src/features/auth/ui/LoginForm.tsx` |
| **Classification** | advisory |

**Description:** `RegisterForm.tsx` imports `useAuth` from the feature barrel (`from '../'`), while `LoginForm.tsx` imports directly from the module path (`from '../model/useAuth'`). Both files are in the same `ui/` directory and import the same hook. This inconsistency makes it harder to track dependencies and refactoring.

**Evidence:**
- `frontend/src/features/auth/ui/RegisterForm.tsx:4`:
  ```ts
  import { useAuth } from '../'
  ```
- `frontend/src/features/auth/ui/LoginForm.tsx:7`:
  ```ts
  import { useAuth } from '../model/useAuth'
  ```

**Recommendation:** Standardize on direct module imports (`from '../model/useAuth'`) for both files. Direct imports are more explicit, easier to trace, and avoid barrel file indirection. This aligns with the pattern used by all other components in the codebase.

---

### FE-007: ErrorPage triggers unnecessary useAuth() call on 404/500 pages

| Field | Value |
|-------|-------|
| **ID** | FE-007 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/shared/components/ErrorPage.tsx` |
| **Classification** | advisory |

**Description:** `ErrorPage.tsx` calls `useAuth()` (line 12) on every 404 or 500 page render. The `useAuth` hook's `useEffect` (in `useAuth.ts:60-100`) attempts to fetch the user profile via `apiGetProfile()` or `apiRefreshToken()`. For unauthenticated users hitting a 404 page, this causes an unnecessary API call that will fail, potentially triggering error toasts or console errors. The `useAuth` hook is used here only to determine the "Go to Home" link target.

**Evidence:**
- `frontend/src/shared/components/ErrorPage.tsx:12`:
  ```ts
  const { user } = useAuth()
  ```
- `frontend/src/features/auth/model/useAuth.ts:60-100` — useEffect that calls `apiRefreshToken()` or `apiGetProfile()` on mount
- `frontend/src/app/routes.tsx:79` — ErrorBoundary wraps all routes, so ErrorPage renders within the authenticated layout context

**Recommendation:** Replace `useAuth()` in `ErrorPage` with a simpler check: read the token directly from `getToken()` (a synchronous, non-fetching function from `authToken.ts`) to determine the home link target. This avoids unnecessary API calls on error pages for unauthenticated users.

---

### FE-008: LogViewer Dashboard filter is non-functional (empty dropdown)

| Field | Value |
|-------|-------|
| **ID** | FE-008 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/admin/ui/LogViewer.tsx` |
| **Classification** | advisory |

**Description:** The LogViewer includes a "Dashboard" filter dropdown (line 78-85) that is always empty. The code has an explicit `{/* TODO: Load dashboards for filter */}` comment. The dropdown renders but provides no options, making it a non-functional UI element that confuses admin users.

**Evidence:**
- `frontend/src/features/admin/ui/LogViewer.tsx:78-85`:
  ```tsx
  <Select
    value={filters.dashboard_id || ''}
    label="Dashboard"
    onChange={(e) => setFilters({ ...filters, dashboard_id: e.target.value || undefined })}
  >
    <MenuItem value="">All</MenuItem>
    {/* TODO: Load dashboards for filter */}
  </Select>
  ```
- The `getDashboardsAdmin()` function exists in `adminApi.ts` (line 93-96) and could populate this dropdown

**Recommendation:** Either wire the dropdown to `getDashboardsAdmin()` to load available dashboards, or remove the non-functional filter until implementation. A non-functional filter is worse than no filter — it misleads users into thinking filtering is possible.

---

### FE-009: UploadModal polling effect may double-invoke onUploadComplete callback

| Field | Value |
|-------|-------|
| **ID** | FE-009 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/upload/ui/UploadModal.tsx`, `frontend/src/features/dashboards/ui/DashboardView.tsx` |
| **Classification** | advisory |

**Description:** `UploadModal.tsx` has a polling effect (line 60-97) that calls `onUploadCompleteRef.current?.()` when processing status becomes `completed` (line 77). Meanwhile, `DashboardView.tsx` passes an `onUploadComplete` callback (line 160-165) that calls `invalidateAggregatedData(id)`. The `handleClose` function (line 188-197) also calls `onClose()` which triggers the parent's state reset. If both the polling effect and the close handler fire, `invalidateAggregatedData` could be called twice, causing redundant API calls.

**Evidence:**
- `frontend/src/features/upload/ui/UploadModal.tsx:74-78`:
  ```ts
  if (status === 'completed') {
    toast.success('Processing complete!')
    setProcessingFinished(true)
    onUploadCompleteRef.current?.()
  }
  ```
- `frontend/src/features/dashboards/ui/DashboardView.tsx:160-165`:
  ```ts
  onUploadComplete={() => {
    setUploadModalOpen(false)
    if (id) {
      void invalidateAggregatedData(id)
    }
  }}
  ```
- The `processingFinished` state gates the "Close" button text but does not prevent the `onUploadComplete` ref from being called if the polling effect fires after the modal is closed

**Recommendation:** Add a guard (e.g., a `hasCompletedRef` flag) to ensure `onUploadCompleteRef.current?.()` is called exactly once, regardless of whether the polling effect fires before or after the modal closes. This prevents duplicate cache invalidation.

---

### FE-010: DashboardFilters local state may desync from parent

| Field | Value |
|-------|-------|
| **ID** | FE-010 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/dashboards/ui/DashboardFilters.tsx`, `frontend/src/features/dashboards/ui/DashboardView.tsx` |
| **Classification** | advisory |

**Description:** `DashboardFilters` maintains its own `localFilters` state (line 32-34) initialized from the parent's `values` prop. The parent (`DashboardView`) passes `filters` state as the `values` prop. A `useEffect` (line 38-41) syncs `localFilters` when `values` changes. However, `DashboardView` never changes the `values` reference — it only reads `filters` to pass to `useAggregatedData`. If the parent's `filters` state were to reset externally, the child's `localFilters` would not update because the `useEffect` dependency is `[values]` (object reference comparison).

**Evidence:**
- `frontend/src/features/dashboards/ui/DashboardFilters.tsx:32-34`:
  ```ts
  const [localFilters, setLocalFilters] = useState<
    Record<string, string | string[] | number | number[]>
  >(() => values || {})
  ```
- `frontend/src/features/dashboards/ui/DashboardFilters.tsx:38-41`:
  ```ts
  useEffect(() => {
    setLocalFilters(values || {})
  }, [values])
  ```
- `frontend/src/features/dashboards/ui/DashboardView.tsx:22-24` — parent state is `filters`, passed as `values={filters}` (line 108)

**Recommendation:** Consider lifting filter state entirely to the parent (`DashboardView`) and passing it down as a controlled prop, or use a key on `DashboardFilters` to force remount when the dashboard changes. The current pattern works for the current use case but is fragile if the parent ever needs to reset filters programmatically.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 7 |
| LOW | 3 |

## Mandatory Fixes

None — no mandatory findings in this phase.

## Advisory Recommendations

| ID | Severity | Summary |
|----|----------|---------|
| FE-001 | MEDIUM | PlaceholderPage is dead code — exported but never used |
| FE-002 | LOW | generateShortId() is defined but never called |
| FE-003 | MEDIUM | getProfile() duplicated across authApi and userApi |
| FE-004 | MEDIUM | UploadModal eagerly imported — breaks lazy-loading pattern |
| FE-005 | LOW | Permanently disabled "Access" button in DashboardManagement |
| FE-006 | LOW | Inconsistent import paths for useAuth in RegisterForm vs LoginForm |
| FE-007 | MEDIUM | ErrorPage triggers unnecessary useAuth() call on 404/500 pages |
| FE-008 | MEDIUM | LogViewer Dashboard filter is non-functional (empty dropdown) |
| FE-009 | MEDIUM | UploadModal polling may double-invoke onUploadComplete callback |
| FE-010 | MEDIUM | DashboardFilters local state may desync from parent |

## Doc Updates Needed

None — no spec deviations found that require doc updates.
