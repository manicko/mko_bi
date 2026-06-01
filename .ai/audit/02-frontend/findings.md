# Phase 02 Audit Findings — Frontend Architecture

**Executor:** audit-executor
**Template:** .kilo/commands/audit/phases/02-audit-frontend.md
**Status:** complete
**Validated:** no

---

## Findings

### FE-001: `console.error` in production code (UserManagement)

| Field | Value |
|-------|-------|
| **ID** | FE-001 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/admin/ui/UserManagement.tsx` |
| **Classification** | advisory |

**Description:** `console.error('Row update error:', error)` at line 188 logs raw errors to the browser console in all environments. The project rules require all logging to use proper `logger = logging.getLogger(__name__)` on the backend; the frontend equivalent is to avoid `console.*` calls in production and route errors through a proper error-handling mechanism.

**Evidence:** `frontend/src/features/admin/ui/UserManagement.tsx:188` — `console.error('Row update error:', error)`. The ESLint config has no `no-console` rule configured, so this is not caught at lint time.

**Recommendation:** Remove the `console.error` call entirely (the error is already handled by the `onProcessRowUpdateError` callback which shows a toast), or add `// eslint-disable-next-line no-console` if temporary debugging is intended. Add `no-console: "warn"` to `eslint.config.js` to prevent future regressions.

---

### FE-002: setState during render effect in DashboardFilters

| Field | Value |
|-------|-------|
| **ID** | FE-002 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/dashboards/ui/DashboardFilters.tsx` |
| **Classification** | advisory |

**Description:** `DashboardFilters.tsx:36` uses `setState` inside a `useEffect` to sync local state from props, with an explicit `eslint-disable-next-line react-hooks/set-state-in-effect` suppression. This pattern causes an extra render cycle on every prop change and is considered an anti-pattern in React. The same pattern exists in `UploadModal.tsx:60`.

**Evidence:** `frontend/src/features/dashboards/ui/DashboardFilters.tsx:34-38`:
```tsx
useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLocalFilters(values || {})
}, [values])
```

**Recommendation:** Replace the local `useState` + `useEffect` sync pattern with a fully controlled component that reads directly from the `values` prop, or use a `key` prop on the component to reset internal state when the external value identity changes. This eliminates the extra render cycle and the ESLint suppression.

---

### FE-003: Dead/unused chart components (BarChart, LineChart, PieChart, TableChart)

| Field | Value |
|-------|-------|
| **ID** | FE-003 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/dashboards/ui/charts/` |
| **Classification** | advisory |

**Description:** Four chart components (`BarChart`, `LineChart`, `PieChart`, `TableChart`) exist as fully implemented files but are never imported, rendered, or exported from the module's public API. Only `PlotlyChart` is re-exported from `charts/index.ts`. `DashboardView.tsx` renders charts exclusively through `PlotlyChart`, making the other four components dead code.

**Evidence:**
- `frontend/src/features/dashboards/ui/charts/index.ts:1` — only exports `PlotlyChart`
- `frontend/src/features/dashboards/ui/DashboardView.tsx:15` — imports only `PlotlyChart`
- `BarChart.tsx`, `LineChart.tsx`, `PieChart.tsx`, `TableChart.tsx` — have zero imports from any other file in the codebase

**Recommendation:** Either integrate these specialized chart components into the rendering pipeline (e.g., select chart type based on `graph.type` in `DashboardView`) or remove them to reduce bundle size and maintenance surface.

---

### FE-004: Dead code — AccessDenied and PlaceholderPage components

| Field | Value |
|-------|-------|
| **ID** | FE-004 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/shared/components/AccessDenied.tsx`, `frontend/src/shared/components/PlaceholderPage.tsx` |
| **Classification** | advisory |

**Description:** `AccessDenied` is exported from `shared/components/index.ts` but never imported or rendered anywhere in the application. `PlaceholderPage` exists as a standalone component but is never imported. Both are dead code.

**Evidence:**
- `frontend/src/shared/components/index.ts:5` — exports `AccessDenied`
- `frontend/src/shared/components/PlaceholderPage.tsx` — component defined but zero imports found in entire `src/` tree
- No `Navigate` or conditional render references `AccessDenied` in any route or protected route guard

**Recommendation:** Remove both components if they are not part of an immediate roadmap. If `AccessDenied` is planned for future use, add a `TODO` comment with a ticket reference.

---

### FE-005: getToken() called outside React render cycle in dashboardApi hooks

| Field | Value |
|-------|-------|
| **ID** | FE-005 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `frontend/src/features/dashboards/api/dashboardApi.ts` |
| **Classification** | mandatory |

**Description:** `getToken()` is called at the top level of three custom hooks (`useMyDashboards`, `useDashboard`, `useAggregatedData`) to compute the `enabled` option. Because `getToken()` reads from a module-level variable (`authToken.ts:65`), this value is captured at hook definition time, not at render time. If the token changes (e.g., after login or token refresh), the hooks may use a stale `enabled` value — either staying disabled after login or staying enabled after token removal.

**Evidence:** `frontend/src/features/dashboards/api/dashboardApi.ts:33-38`:
```tsx
export function useMyDashboards() {
  const accessToken = getToken()  // captured once on module load
  return useQuery({
    queryKey: ['dashboards', 'my'],
    queryFn: () => dashboardApi.getMyDashboards(),
    enabled: !!accessToken,  // stale if token changes
  })
}
```

**Recommendation:** Use a callback ref or call `getToken()` inside a function that re-evaluates on each render, such as reading the token from `useAuth()` context instead of calling `getToken()` directly. Alternatively, access the token from the auth context which is guaranteed to be fresh on each render.

---

### FE-006: Duplicate getProfile function (authApi vs userApi)

| Field | Value |
|-------|-------|
| **ID** | FE-006 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/auth/api/authApi.ts`, `frontend/src/features/users/api/userApi.ts` |
| **Classification** | advisory |

**Description:** Both `authApi.ts:21` and `userApi.ts:4` define an identical `getProfile()` function that calls `GET /auth/me`. This violates DRY and creates maintenance risk — if the endpoint changes, both functions must be updated.

**Evidence:**
- `frontend/src/features/auth/api/authApi.ts:21-23`: `export async function getProfile(): Promise<UserProfile> { const response = await axiosInstance.get<UserProfile>('/auth/me'); return response.data; }`
- `frontend/src/features/users/api/userApi.ts:4-6`: identical implementation

**Recommendation:** Remove the duplicate from `userApi.ts` and have all consumers import `getProfile` from `authApi.ts`. This follows the auth-domain ownership principle.

---

### FE-007: Missing HTML label associations on form fields

| Field | Value |
|-------|-------|
| **ID** | FE-007 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/auth/ui/LoginForm.tsx`, `frontend/src/features/auth/ui/RegisterForm.tsx`, `frontend/src/features/users/ui/ChangePasswordPage.tsx` |
| **Classification** | advisory |

**Description:** The audit checklist requires that form fields have associated labels via `<label htmlFor>` or `aria-labelledby`. While MUI's `<TextField>` renders a `<label>` element internally, there are no explicit `id`/`htmlFor` pairs set on the form fields. Screen readers rely on these explicit associations for accessibility. The ESLint config also does not include `eslint-plugin-jsx-a11y`, so no accessibility lint rules are enforced.

**Evidence:**
- `frontend/src/features/auth/ui/LoginForm.tsx:72-78`: `<TextField label="Email" {...register('email')}>` — no explicit `id` prop
- `frontend/src/features/users/ui/ChangePasswordPage.tsx:64-72`: same pattern
- ESLint config (`eslint.config.js`) has no `jsx-a11y` plugin; only `react-hooks` and `react-refresh` are configured

**Recommendation:** Add explicit `id` props to all MUI `<TextField>` components (e.g., `id="email"`, `id="password"`) to ensure the generated `<label htmlFor>` attributes match. Alternatively, add `eslint-plugin-jsx-a11y` to the ESLint configuration to catch these issues automatically.

---

### FE-008: Incomplete admin features — Access management and Dashboard filter in LogViewer

| Field | Value |
|-------|-------|
| **ID** | FE-008 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/admin/ui/DashboardManagement.tsx`, `frontend/src/features/admin/ui/LogViewer.tsx` |
| **Classification** | advisory |

**Description:** Two admin UI features are stubbed with `TODO` comments and non-functional interactions:
1. `DashboardManagement.tsx:148-150`: The "Access" button in the dashboard management grid calls `alert('Access management not yet implemented')` instead of opening a proper dialog.
2. `LogViewer.tsx:83`: The dashboard filter dropdown is empty with a `{/* TODO: Load dashboards for filter */}` comment, making the filter non-functional.

**Evidence:**
- `frontend/src/features/admin/ui/DashboardManagement.tsx:148`: `alert('Access management not yet implemented')` — `alert()` blocks the main thread and provides poor UX
- `frontend/src/features/admin/ui/LogViewer.tsx:83`: Empty `<Select>` with no dashboard options loaded

**Recommendation:** These are known incomplete features marked with TODOs. Track them as implementation tasks. For the `alert()` call, replace with a proper toast notification or remove the button until the feature is implemented. For the LogViewer dashboard filter, fetch the dashboard list from the backend.

---

### FE-009: Form validation inconsistency — ChangePassword confirm_password sent to backend

| Field | Value |
|-------|-------|
| **ID** | FE-009 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/features/users/ui/ChangePasswordPage.tsx`, `frontend/src/features/users/api/userApi.ts`, `frontend/src/shared/types/formSchemas.ts` |
| **Classification** | mandatory |

**Description:** The Zod `changePasswordSchema` includes a `confirm_password` field with a `.refine()` check that `new_password === confirm_password` (`formSchemas.ts:58-61`). The `ChangePasswordRequest` interface in `api.types.ts:227-231` also includes `confirm_password`. When submitted, the entire form data including `confirm_password` is sent via `POST /auth/change-password` (`userApi.ts:14`). The backend `ChangePasswordRequest` model (in `mkobi/models/auth.py`) should validate that `new_password === confirm_password` server-side. If the backend does not accept or validate `confirm_password`, the frontend sends an unexpected field; if the backend does not perform the matching check, the server-side validation is inconsistent with the frontend.

**Evidence:**
- `frontend/src/shared/types/formSchemas.ts:54-61`: schema validates `confirm_password` matches `new_password`
- `frontend/src/shared/types/api.types.ts:227-231`: `ChangePasswordRequest` includes `confirm_password`
- `frontend/src/features/users/api/userApi.ts:13-15`: sends the full request body to `/auth/change-password`
- Backend route `auth.py:366`: `change_password` endpoint receives `ChangePasswordRequest` — the backend model must be checked for `confirm_password` field presence

**Recommendation:** Verify that the backend `ChangePasswordRequest` Pydantic model includes `confirm_password` and validates the match. If the backend only expects `current_password` and `new_password`, remove `confirm_password` from `ChangePasswordRequest` and perform the match only on the frontend.

---

### FE-010: Potential API contract mismatch — UploadMode enum in URL params

| Field | Value |
|-------|-------|
| **ID** | FE-010 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/features/upload/api/uploadApi.ts` |
| **Classification** | advisory |

**Description:** `uploadApi.ts:21` passes the upload mode as a URL query parameter `params: { mode }`. The frontend `UploadMode` enum values are `'overwrite'` and `'append'` (from `enums.ts:49-53`). The backend `UploadMode` StrEnum must have matching string values. Mismatched values would cause the backend to receive an invalid enum value, resulting in a 422 error.

**Evidence:**
- `frontend/src/features/upload/api/uploadApi.ts:17-21`: `params: { mode }` sent as query param
- Backend `upload.py:58`: `mode: UploadMode = UploadMode.OVERWRITE` — expects enum value
- Frontend `enums.ts:49-53`: `UploadMode = { OVERWRITE: 'overwrite', APPEND: 'append' }` as const — values are lowercase

**Recommendation:** Verify that the backend `UploadMode` StrEnum values are also lowercase `'overwrite'` and `'append'`. If they differ (e.g., uppercase), add a mapping layer or align the frontend enum to match.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 4 |
| LOW | 5 |

## Mandatory Fixes

- **FE-005** — `getToken()` called outside React render cycle in `dashboardApi.ts` hooks causes stale `enabled` state, potentially breaking query activation after login/logout/token refresh.
- **FE-009** — `confirm_password` field sent to `/auth/change-password` must be validated against the backend `ChangePasswordRequest` model contract; if the backend doesn't accept it, the request will fail or the field will be silently ignored.

## Advisory Recommendations

- **FE-001** — Remove `console.error` from `UserManagement.tsx`
- **FE-002** — Replace sync-state-in-effect pattern in `DashboardFilters` and `UploadModal`
- **FE-003** — Remove unused chart components or integrate them
- **FE-004** — Remove dead `AccessDenied` and `PlaceholderPage` components
- **FE-006** — Deduplicate `getProfile` function (keep only in `authApi.ts`)
- **FE-007** — Add explicit `id` props to form fields for accessibility; add `jsx-a11y` ESLint plugin
- **FE-008** — Complete or gate admin stubs (access management dialog, LogViewer dashboard filter)
- **FE-010** — Verify `UploadMode` enum value alignment between frontend and backend

## Doc Updates Needed

- None identified in this phase.
