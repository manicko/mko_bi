# Phase 02 Audit Findings — Frontend Architecture

**Executor:** audit-executor
**Template:** `.ai/audit/templates/audit-findings.md`
**Status:** complete
**Validated:** no

---

## Findings

### FE-001: All user-facing error messages are in Russian, violating project English-only rule

| Field | Value |
|-------|-------|
| **ID** | FE-001 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/shared/api/errorMessages.ts`, `frontend/src/features/auth/model/errorMessages.ts`, `frontend/src/features/dashboards/model/errorMessages.ts`, `frontend/src/features/upload/model/errorMessages.ts`, `frontend/src/features/users/model/errorMessages.ts`, `frontend/src/features/admin/model/errorMessages.ts` |
| **Classification** | mandatory |

**Description:** The AGENTS.md project rule states: "All comments, logs and docstring — **only on English**" and the project rules state: "All comments, logs, docstrings, error messages, and documentation must be in clear English." However, all user-facing error messages displayed via `toast.error()` are written in Russian. This affects every feature module's error messages and the shared fallback map. The `DEFAULT_ERROR_MESSAGE` is `'Произошла ошибка'` and all ~50 mapped error strings are Russian.

**Evidence:**
- `frontend/src/shared/api/errorMessages.ts:15` — `sharedErrorMessages` contains Russian: `'Внутренняя ошибка сервера'`, `'Сервис временно недоступен'`, etc.
- `frontend/src/shared/api/errorMessages.ts:58` — `DEFAULT_ERROR_MESSAGE = 'Произошла ошибка'`
- `frontend/src/features/auth/model/errorMessages.ts:7` — e.g. `'Неверный email или пароль'`
- `frontend/src/features/dashboards/model/errorMessages.ts:6` — e.g. `'Дашборд не найден или был удалён'`
- `frontend/src/features/upload/model/errorMessages.ts:6` — e.g. `'Не удалось загрузить файл. Попробуйте ещё раз.'`
- `frontend/src/features/users/model/errorMessages.ts:6` — e.g. `'Пользователь не найден'`
- `frontend/src/features/admin/model/errorMessages.ts:6` — e.g. `'Недостаточно прав для административной операции'`
- These messages are displayed to users via `toast.error()` in the Axios response interceptor (`axiosInstance.ts:124`) and in mutation error handlers across all feature components.

**Recommendation:** Translate all error message strings to English. Replace `DEFAULT_ERROR_MESSAGE` with `'An error occurred'`. Update each feature's `errorMessages.ts` map with English equivalents. If Russian localization is desired, implement a proper i18n system instead of hardcoding strings.

---

### FE-002: Spec-required chart type components (LineChart, PieChart, TableChart) exist but are never rendered — features missing from UI

| Field | Value |
|-------|-------|
| **ID** | FE-002 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/features/dashboards/ui/charts/LineChart.tsx`, `frontend/src/features/dashboards/ui/charts/PieChart.tsx`, `frontend/src/features/dashboards/ui/charts/TableChart.tsx`, `frontend/src/features/dashboards/ui/charts/BarChart.tsx`, `frontend/src/features/dashboards/ui/charts/ChartRenderer.tsx` |
| **Classification** | mandatory |

**Description:** The backend defines `GraphType` enum with values `bar`, `line`, `pie`, `table` (`src/mkobi/models/enums.py:25-31`). The frontend has corresponding `GraphType` enum and individual chart components `BarChart`, `LineChart`, `PieChart`, and `TableChart`. However, `ChartRenderer` only renders all data through `PlotlyChart` (a generic Plotly wrapper) and never dispatches to the type-specific components. The individual chart components are never imported anywhere except by each other and the index barrel. The `ChartRenderer` does not switch on `graph.type` to render lines, pies, or tables differently — it only handles bar/pie via Plotly's `type` field, meaning line charts lose their line-specific configuration and table charts are rendered as Plotly bar charts (incorrectly).

**Evidence:**
- `frontend/src/features/dashboards/ui/charts/ChartRenderer.tsx:30` — `type: graph.type === 'pie' ? 'pie' : 'bar'` — everything not pie is rendered as bar, including line and table types.
- `frontend/src/shared/types/enums.ts:23-29` — `GraphType = { BAR, LINE, PIE, TABLE }`
- No imports of `LineChart`, `PieChart`, `TableChart`, or `BarChart` found anywhere in the codebase.
- `frontend/src/features/dashboards/ui/charts/index.ts:1-2` — Only exports `PlotlyChart` and `ChartRenderer`, not the individual chart components.

**Recommendation:** Update `ChartRenderer` to dispatch rendering based on `graph.type`:
- `line` → render with Plotly `type: 'scatter'` mode or delegate to `LineChart`
- `pie` → render with Plotly `type: 'pie'` (partially works)
- `table` → delegate to `TableChart` (needs non-Plotly rendering)
- `bar` → render with Plotly `type: 'bar'` (current default)

---

### FE-003: `useFilterValues` hook uses non-reactive `getToken()` instead of `useAuthToken()`, causing stale query enablement

| Field | Value |
|-------|-------|
| **ID** | FE-003 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/dashboards/api/dashboardApi.ts` |
| **Classification** | mandatory |

**Description:** The `useFilterValues` hook (line 87) uses `getToken()` to check if the user is authenticated before enabling the query. All other hooks in the same file (`useMyDashboards`, `useDashboard`, `useAggregatedData`) use the reactive `useAuthToken()` hook. `getToken()` is a synchronous non-reactive read that doesn't subscribe to token changes — if the token changes (login/logout), `useFilterValues` will not re-evaluate its `enabled` condition, potentially leading to queries running without a token or failing to run when a token becomes available.

**Evidence:**
- `frontend/src/features/dashboards/api/dashboardApi.ts:87` — `const accessToken = getToken()` (non-reactive)
- `frontend/src/features/dashboards/api/dashboardApi.ts:45` — `const accessToken = useAuthToken()` (reactive, correct pattern)
- `frontend/src/features/dashboards/api/dashboardApi.ts:54` — `const accessToken = useAuthToken()` (reactive, correct pattern)
- `frontend/src/features/dashboards/api/dashboardApi.ts:67` — `const accessToken = useAuthToken()` (reactive, correct pattern)

**Recommendation:** Replace `getToken()` with `useAuthToken()` in `useFilterValues` on line 87 of `dashboardApi.ts`, consistent with the other hooks in the same file.

---

### FE-004: `console.error` in production code violates no-print rule

| Field | Value |
|-------|-------|
| **ID** | FE-004 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/admin/ui/UserManagement.tsx` |
| **Classification** | advisory |

**Description:** The project rule states "Use proper logging: `logger = logging.getLogger(__name__)`" and forbids `print()` statements. While `console.error` in `ErrorBoundary` is correctly guarded by `import.meta.env.DEV`, the `UserManagement` component has an unguarded `console.error('Row update error:', error)` that runs in production builds.

**Evidence:**
- `frontend/src/features/admin/ui/UserManagement.tsx:254` — `console.error('Row update error:', error)` — not guarded by DEV check
- Compare with `frontend/src/shared/components/ErrorBoundary.tsx:25-29` — `console.error` correctly gated by `import.meta.env.DEV`

**Recommendation:** Replace `console.error` with a proper error reporting mechanism (e.g., the existing client-errors endpoint) or guard with `import.meta.env.DEV`, consistent with the ErrorBoundary pattern.

---

### FE-005: `any` type escape in PlotlyComponent for CJS/ESM interop

| Field | Value |
|-------|-------|
| **ID** | FE-005 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/shared/components/PlotlyComponent.tsx` |
| **Classification** | advisory |

**Description:** `PlotlyComponent.tsx` uses `any` type (`const raw = PlotlyDefault as any`) to work around CJS/ESM interop issues with `react-plotly.js`. The eslint disable comments acknowledge this is intentional, but it creates a type safety gap in the chart rendering path.

**Evidence:**
- `frontend/src/shared/components/PlotlyComponent.tsx:19-24` — `/* eslint-disable @typescript-eslint/no-explicit-any */` and `const raw = PlotlyDefault as any`

**Recommendation:** Create a proper type declaration for the CJS/ESM interop case using module augmentation in the existing `react-plotly.d.ts` file, or create a dedicated wrapper type that narrows the `any` before passing to `PlotComponent`.

---

### FE-006: `PlaceholderPage` component is dead code — never imported or rendered

| Field | Value |
|-------|-------|
| **ID** | FE-006 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/shared/components/PlaceholderPage.tsx` |
| **Classification** | advisory |

**Description:** `PlaceholderPage.tsx` is a component that exists in the shared components directory but is never imported or rendered anywhere in the codebase. The barrel export `shared/components/index.ts` also does not export it. It appears to be a scaffolding leftover.

**Evidence:**
- `frontend/src/shared/components/PlaceholderPage.tsx` — file exists
- No imports of `PlaceholderPage` found anywhere in `frontend/src/`
- `frontend/src/shared/components/index.ts` — does not include `PlaceholderPage`

**Recommendation:** Remove `PlaceholderPage.tsx` if it is not needed by upcoming features, or document its planned use.

---

### FE-007: `AccessDenied` component exported but never imported outside the barrel

| Field | Value |
|-------|-------|
| **ID** | FE-007 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/shared/components/AccessDenied.tsx`, `frontend/src/shared/components/index.ts` |
| **Classification** | advisory |

**Description:** `AccessDenied` is exported from the shared components barrel (`index.ts:5`) but is never imported by any consumer in the codebase. The `RoleBasedAccess` component renders a `fallback={null}` when access is denied, instead of rendering `<AccessDenied />`.

**Evidence:**
- `frontend/src/shared/components/index.ts:5` — `export { AccessDenied } from './AccessDenied'`
- No imports of `AccessDenied` found outside the barrel file
- `frontend/src/shared/components/RoleBasedAccess.tsx:9` — `fallback = null` — the AccessDenied component is not used as the default fallback

**Recommendation:** Either use `AccessDenied` as the default fallback in `RoleBasedAccess` (e.g., `fallback = <AccessDenied />`) or remove the component and its barrel export if not needed.

---

### FE-008: Plotly chunk exceeds 4.6MB — build produces chunk size warning

| Field | Value |
|-------|-------|
| **ID** | FE-008 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/vite.config.ts` |
| **Classification** | advisory |

**Description:** The production build produces a Plotly chunk of 4,643.95 kB (1,388.77 kB gzipped), which triggers Vite's chunk size warning. While the chunk is already manually split, the absolute size is very large and will significantly impact initial load performance for users on slow connections.

**Evidence:**
- Build output: `dist/assets/plotly-BxTkdUEp.js  4,643.95 kB │ gzip: 1,388.77 kB`
- Build warning: `(!) Some chunks are larger than 500 kB after minification.`
- The chunk is already configured in `vite.config.ts:44` via `manualChunks`

**Recommendation:** Consider using `plotly.js-dist-min` (already imported) or a partial Plotly bundle that only includes trace types the app actually uses (bar, scatter, pie). Plotly supports custom bundles via `plotly.js/lib/index-basic` or trace-specific imports.

---

### FE-009: `DashboardManagement` uses `alert()` for unimplemented access management — not production-ready

| Field | Value |
|-------|-------|
| **ID** | FE-009 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/features/admin/ui/DashboardManagement.tsx` |
| **Classification** | mandatory |

**Description:** The "Access" action button in the dashboard management DataGrid calls `alert('Access management not yet implemented')` with a TODO comment. `alert()` is a blocking browser dialog that is not accessible, cannot be styled, and freezes the UI thread. This is a spec deviation because dashboard access management is a core feature described in the specification.

**Evidence:**
- `frontend/src/features/admin/ui/DashboardManagement.tsx:165-168` — `// TODO: Implement access management dialog` and `alert('Access management not yet implemented')`
- Backend endpoint exists: `POST /dashboards/{dashboard_id}/access`, `GET /dashboards/{dashboard_id}/access`, `DELETE /dashboards/{dashboard_id}/access/{user_id}`

**Recommendation:** Replace `alert()` with either a toast notification (`toast.info('Coming soon')`) or implement the access management dialog using the existing `grantDashboardAccess` API function and `GrantAccessRequest` type.

---

### FE-010: `act()` warnings in useAuth tests indicate potential state update timing issues

| Field | Value |
|-------|-------|
| **ID** | FE-010 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/auth/model/__tests__/useAuth.test.tsx` |
| **Classification** | advisory |

**Description:** The `useAuth.test.tsx` test suite produces multiple `act()` warnings: "An update to TestComponent inside a test was not wrapped in act(...)". While all 16 tests pass, these warnings indicate that async state updates (from the `useEffect` initialization and login/logout flows) are not properly awaited in tests, which could mask real race conditions.

**Evidence:**
- Test output stderr: Multiple `An update to TestComponent inside a test was not wrapped in act(...)` warnings across `initialization`, `login`, `logout`, `registerRequest`, and `getProfile` test cases.
- `frontend/src/features/auth/model/__tests__/useAuth.test.tsx` — 16 passing tests with act warnings

**Recommendation:** Wrap async state-triggering interactions in `await act(async () => { ... })` and ensure all promises are flushed before assertions. Consider using `waitFor` from `@testing-library/react` for async state checks.

---

### FE-011: `DashboardManagement` create form bypasses Zod validation schema

| Field | Value |
|-------|-------|
| **ID** | FE-011 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/admin/ui/DashboardManagement.tsx`, `frontend/src/shared/types/formSchemas.ts` |
| **Classification** | mandatory |

**Description:** The project uses React Hook Form + Zod for form validation. A `createDashboardSchema` is defined in `formSchemas.ts` with proper validation (min 3 chars, max 100, regex pattern for name). However, `DashboardManagement` manages its own form state via `useState` and manual `onChange` handlers, completely bypassing both React Hook Form and the Zod schema. This means dashboard names can be submitted with invalid characters, empty names, or names exceeding the length limit — the backend will reject them, but the user gets a poor UX.

**Evidence:**
- `frontend/src/features/admin/ui/DashboardManagement.tsx:35` — `const [formData, setFormData] = useState<{ name: string; ... }>({ name: '', ... })` — manual state
- `frontend/src/features/admin/ui/DashboardManagement.tsx:225` — `onChange={(e) => setFormData({ ...formData, name: e.target.value })}` — no validation
- `frontend/src/shared/types/formSchemas.ts:24-33` — `createDashboardSchema` defines min(3), max(100), regex validation but is never used by `DashboardManagement`

**Recommendation:** Replace the manual `useState` form management in `DashboardManagement`'s create/edit dialogs with `useForm<CreateDashboardFormData>({ resolver: zodResolver(createDashboardSchema) })`, consistent with `LoginForm`, `RegisterForm`, and `ChangePasswordPage`.

---

### FE-012: `features/charts` directory is empty — expected chart feature module structure missing

| Field | Value |
|-------|-------|
| **ID** | FE-012 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/charts/` |
| **Classification** | advisory |

**Description:** The directory `frontend/src/features/charts/` exists but is completely empty. Given the FSD (Feature-Sliced Design) architecture, this appears to be either a planned but unimplemented feature module or an abandoned directory. Chart components currently live under `features/dashboards/ui/charts/`, which mixes the chart feature with the dashboard feature.

**Evidence:**
- `frontend/src/features/charts/` — empty directory (no files)
- All chart components live in `frontend/src/features/dashboards/ui/charts/` instead

**Recommendation:** Either remove the empty `features/charts/` directory, or move chart components there if charts should be an independent feature module per FSD principles.

---

### FE-013: `useAuth` hook triggers `window.location.href` hard navigation instead of React Router navigation

| Field | Value |
|-------|-------|
| **ID** | FE-013 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/auth/model/useAuth.ts` |
| **Classification** | advisory |

**Description:** The `useAuth` hook uses `window.location.href = '/profile/change-password?force=true'` (lines 33, 70, 89) for the force-password-change redirect. This triggers a full page reload, losing all React state (including the just-set token in memory), instead of using React Router's `navigate()` which preserves the SPA context and in-memory state. In production mode (`USE_MEMORY_STORAGE = true`), the memory-stored token is lost on hard navigation, causing the user to be logged out immediately after being forced to change their password.

**Evidence:**
- `frontend/src/features/auth/model/useAuth.ts:33` — `window.location.href = '/profile/change-password?force=true'`
- `frontend/src/features/auth/model/useAuth.ts:70` — `window.location.href = '/profile/change-password?force=true'`
- `frontend/src/features/auth/model/useAuth.ts:89` — `window.location.href = '/profile/change-password?force=true'`
- `frontend/src/features/auth/model/authToken.ts:74` — `const USE_MEMORY_STORAGE = import.meta.env.PROD` — production uses memory-only tokens, lost on hard navigation

**Recommendation:** Use React Router's `navigate('/profile/change-password?force=true')` for SPA navigation. Since `useAuth` is a hook, it can access `useNavigate()` from React Router, or alternatively, the redirect should be handled at the component level (like `LoginForm` already does correctly at line 40).

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 6 |
| LOW | 3 |

## Mandatory Fixes

- **FE-001**: All user-facing error messages in Russian — violates English-only project rule
- **FE-002**: Line, Pie, Table chart types specified by backend but unrendered — ChartRenderer only handles bar/pie via Plotly
- **FE-003**: `useFilterValues` uses non-reactive `getToken()` instead of `useAuthToken()`, causing stale query behavior
- **FE-009**: `alert()` used for unimplemented access management — not accessible, not production-ready
- **FE-011**: Dashboard create/edit form bypasses Zod validation schema

## Advisory Recommendations

- **FE-004**: Replace `console.error` in UserManagement with proper logging or DEV guard
- **FE-005**: Type the Plotly CJS/ESM interop instead of using `any`
- **FE-006**: Remove dead `PlaceholderPage` component
- **FE-007**: Use or remove unused `AccessDenied` component
- **FE-008**: Reduce Plotly bundle size via partial/traces-only import
- **FE-010**: Fix `act()` warnings in useAuth tests
- **FE-012**: Remove empty `features/charts/` directory or populate it
- **FE-013**: Replace `window.location.href` hard navigations with React Router `navigate()`

## Doc Updates Needed

None.

---
