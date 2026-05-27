---
name: audit-findings
description: Runtime error findings for reported bugs — Dashboard Management create, Registration Requests DataGrid, and Session/Auth routing
agent: auditor
alwaysApply: false
---

# Runtime Bug Analysis — Dashboard Management, Registration Requests, Session Routing

**Executor:** auditor
**Template:** audit-findings.md
**Status:** complete
**Validated:** yes

---

## Findings

### BUG-001: Dashboard Create — Layout Field Ignored, Silently Creates Dashboard Without Layout

| Field | Value |
|-------|-------|
| **ID** | BUG-001 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/features/admin/ui/DashboardManagement.tsx`, `frontend/src/features/admin/api/adminApi.ts`, `src/mkobi/models/dashboard.py`, `src/mkobi/api/routes/dashboards_crud.py` |
| **Classification** | mandatory |

**Description:**
When an admin creates a dashboard through the frontend form at `/admin` → Dashboard Management → Create Dashboard, the user selects a Layout (single-column / two-columns / grid) from a dropdown. The "Create" button fires a `createDashboard` mutation. The frontend sends the layout value as part of the request payload, but the backend **silently drops it** because the frontend and backend data models are fundamentally mismatched.

**Root Cause — Frontend sends `layout` as a string enum, backend expects `layout_id` as a UUID:**

1. **Frontend type definition** (`frontend/src/shared/types/api.types.ts:223`):
   ```typescript
   export interface CreateDashboardRequest {
     name: string
     description?: string
     layout?: 'single-column' | 'two-columns' | 'grid'
   }
   ```
   The `layout` field is a human-readable string enum.

2. **Frontend API call** (`frontend/src/features/admin/api/adminApi.ts:54-61`):
   ```typescript
   export async function createDashboard(data: CreateDashboardRequest) {
     const payload: Record<string, unknown> = { name: data.name }
     if (data.description) { payload.description = data.description }
     // NOTE: data.layout is NEVER added to the payload
     const response = await axiosInstance.post('/dashboards', payload)
   }
   ```
   Critically, the `layout` field from `CreateDashboardRequest` is **never included** in the API payload. It is silently dropped even before reaching the backend.

3. **Frontend handleCreate** (`frontend/src/features/admin/ui/DashboardManagement.tsx:79-85`):
   ```typescript
   const handleCreate = () => {
     createMutation.mutate({
       name: formData.name,
       description: formData.description,
       layout: formData.layout || undefined,  // layout is passed to mutation but dropped in adminApi.ts
     })
   }
   ```

4. **Backend model** (`src/mkobi/models/dashboard.py:50-56`):
   ```python
   class DashboardCreate(BaseModel):
       name: str
       description: str | None = None
       config: DashboardConfig = DashboardConfig(graph_types=[GraphType.BAR])
       layout_id: UUID | None = None
   ```
   The backend expects `layout_id: UUID`, not `layout: string`. Even if the frontend sent the layout string, Pydantic v2 (with default `extra='ignore'`) would silently drop it since there is no `layout` field in the model.

**Result:** Every dashboard created via the admin form has `layout_id = NULL` and uses a default empty config with only `graph_types: ["bar"]`. The "two-columns" layout is never persisted, so when the user navigates to view the dashboard, there is no matching layout to render — resulting in the reported "Request failed with status code 404" if the frontend attempts to fetch a layout by the string name "two-columns" as if it were a resource.

**Evidence:**
- `DashboardManagement.tsx:31` — State includes `layout: 'single-column' | 'two-columns' | 'grid' | ''`
- `DashboardManagement.tsx:83` — `layout: formData.layout || undefined` passed to mutation
- `adminApi.ts:54-61` — Payload built without `layout`; only `name` and `description` are included
- `dashboard.py:56` — Backend model has `layout_id: UUID`, no `layout` string field
- No enum or lookup table exists on the backend for layout names like `"two-columns"`, `"single-column"`, `"grid"`

**Recommendation:**
Two possible approaches:
1. **Quick fix:** Pre-create layout records in the database with known UUIDs and map the frontend layout string to a `layout_id` UUID in `adminApi.ts` before sending to the backend.
2. **Proper fix:** Create a `POST /api/v1/layouts` endpoint and a `layouts` seed/migration. Store the mapping between layout names and UUIDs in a seed table. The frontend should resolve the layout name to a UUID before calling `POST /dashboards`. This requires a new `layouts` concept currently missing from the backend entirely.

---

### BUG-002: Registration Requests — DataGrid `getActions` Missing Causes Runtime Crash

| Field | Value |
|-------|-------|
| **ID** | BUG-002 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `frontend/src/features/admin/ui/RegistrationRequests.tsx` |
| **Classification** | mandatory |

**Description:**
The Registration Requests tab (`/admin` → Registration Requests) crashes with the error:
> "MUI X: Missing the `getActions` property in the `GridColDef`."

This error occurs in the browser console and renders the entire tab non-functional, showing "Something went wrong" to the user.

**Root Cause:**
MUI X DataGrid v9 (`@mui/x-data-grid: ^9.0.4`) requires that columns with `type: 'actions'` define a `getActions` callback property. The current code in `RegistrationRequests.tsx` defines the actions column incorrectly:

**Current broken code** (`RegistrationRequests.tsx:12-26`):
```typescript
const columns: GridColDef[] = [
  { field: 'email', headerName: 'Email', width: 250 },
  { field: 'status', headerName: 'Status', width: 130, renderCell: ... },
  { field: 'created_at', headerName: 'Created', width: 180 },
  { field: 'actions', headerName: 'Actions', type: 'actions', width: 150 },
  // ❌ Missing getActions callback
]
```

Instead of using `getActions`, the code attempts to inject action buttons by adding an `actions` property directly to each **row** (`RegistrationRequests.tsx:70-95`):
```typescript
const rows = requests.map((req) => ({
  id: req.id,
  email: req.email,
  status: req.status,
  created_at: new Date(req.created_at).toLocaleString(),
  actions: (
    <>
      {req.status === 'pending' && (
        <>
          <GridActionsCellItem icon={<ApproveIcon />} label="Approve" onClick={...} />
          <GridActionsCellItem icon={<RejectIcon />} label="Reject" onClick={...} />
        </>
      )}
    </>
  ),
}))
```

This approach is incompatible with MUI X DataGrid v9. The `type: 'actions'` column expects the grid to call `getActions(params)` to retrieve the action components. Without it, the grid's internal `GridActionsCellWrapper` crashes.

**Contrast with working pattern** (`DashboardManagement.tsx:131-162`):
The `DashboardManagement` component correctly uses `renderCell` (not `type: 'actions'`) for its actions column:
```typescript
{
  field: 'actions',
  headerName: 'Actions',
  width: 200,
  sortable: false,
  filterable: false,
  renderCell: ({ row }: GridRenderCellParams<DashboardAdmin>) => (
    <>
      <GridActionsCellItem icon={<EditIcon />} label="Edit" onClick={...} />
      ...
    </>
  ),
}
```

**Evidence:**
- `RegistrationRequests.tsx:25` — Column defined with `type: 'actions'` but no `getActions`
- `RegistrationRequests.tsx:70-95` — Actions injected into rows instead of column definition
- `DashboardManagement.tsx:131-162` — Working pattern using `renderCell` instead of `type: 'actions'`
- `@mui/x-data-grid: ^9.0.4` in `frontend/package.json`
- MUI type definition at `node_modules/@mui/x-data-grid/models/colDef/gridColDef.d.ts:275` confirms `getActions` is required on `GridActionsColDef`

**Recommendation:**
Either:
1. **Preferred:** Replace `type: 'actions'` with `renderCell` (matching the pattern in `DashboardManagement.tsx`), which avoids the `getActions` requirement entirely.
2. **Alternative:** Add a `getActions` callback to the column definition and remove the `actions` property from the row mapping.

---

### BUG-003: Session/Auth Routing — Root `/` Always Redirects to Login, Even for Authenticated Users

| Field | Value |
|-------|-------|
| **ID** | BUG-003 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/app/routes.tsx`, `frontend/src/shared/components/ProtectedRoute.tsx` |
| **Classification** | mandatory |

**Description:**
According to the system specification:
- If a user is **not logged in**, navigating to any page (including `/`) should redirect to `/login`.
- If a user **is logged in** (session alive), navigating to `/` should redirect to `/dashboards`.

The current implementation unconditionally redirects `/` to `/login` regardless of authentication state. This means authenticated users who navigate to `http://localhost:5173/` are sent to the login page instead of their dashboards.

**Root Cause:**
The route definition at `frontend/src/app/routes.tsx:117`:
```typescript
<Route path="/" element={<Navigate to="/login" replace />} />
```

This is an **unconditional** redirect. It sits inside `<AppLayout>` and `<ErrorBoundary>` but **outside** any `<ProtectedRoute>` wrapper, so it has no access to authentication state.

The redirect logic is handled by two separate, disconnected mechanisms:
1. **Root route** (`routes.tsx:117`): Always sends to `/login`.
2. **`ProtectedRoute`** (`ProtectedRoute.tsx:9-25`): Wraps protected routes (like `/dashboards`, `/admin`) and redirects unauthenticated users to `/login` with `state={{ from: location }}`.

**Expected behavior flow:**
1. User navigates to `/`
2. System checks if user has a valid session (via `useAuth` → `getToken()` or silent refresh)
3. If authenticated → redirect to `/dashboards`
4. If not authenticated → redirect to `/login`

**Evidence:**
- `routes.tsx:117` — `<Route path="/" element={<Navigate to="/login" replace />} />` is unconditional
- `routes.tsx:63-120` — All protected routes are wrapped in `<ProtectedRoute>` inside `<AppLayout>`, but the `/` route is not
- `ProtectedRoute.tsx:9-25` — Checks `accessToken` from `useAuth()` but is never invoked for the `/` route
- `useAuth.ts:53-87` — Silent refresh on mount checks for token and attempts refresh, providing auth state
- SPEC.md Session management expectations (lines 152-155): "Cookie-based refresh token flow", "frontend silent refresh on request", "ProtectedRoute loading state during refresh"

**Recommendation:**
Replace the unconditional redirect at `routes.tsx:117` with an auth-aware redirect that checks authentication state. The component should:
1. Show a loading spinner while the silent refresh/auth check is in progress
2. Redirect to `/dashboards` if the user is authenticated
3. Redirect to `/login` if the user is not authenticated

This requires creating a small `RootRedirect` component that uses `useAuth()` (similar to `ProtectedRoute`) or integrating the `/` route into the `<ProtectedRoute>` + auth-check pattern. The loading state is critical to prevent a flash of the login page for authenticated users (as described in the spec: "ProtectedRoute loading state during refresh").

---

### BUG-003b: Authenticated Users Not Redirected Away from /login

| Field | Value |
|-------|-------|
| **ID** | BUG-003b |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/auth/ui/LoginForm.tsx`, `frontend/src/app/routes.tsx` |
| **Classification** | advisory |

**Description:**
If an authenticated user navigates directly to `/login`, they see the login form instead of being redirected to `/dashboards`. This is a minor UX issue — authenticated users should not need to see the login page.

**Root Cause:**
The `LoginForm` component (`LoginForm.tsx`) does not check the current authentication state on mount. It has no logic like:
```typescript
if (accessToken) return <Navigate to="/dashboards" />
```

**Evidence:**
- `LoginForm.tsx:9-46` — No auth state check on mount; renders the form unconditionally
- `routes.tsx:47-54` — `/login` route is at the top level, outside any `<ProtectedRoute>`

**Recommendation:**
Add an auth check at the top of `LoginForm` that redirects authenticated users to `/dashboards`. Alternatively, `LoginForm` could accept `accessToken` as a prop from a route wrapper that performs the check.

---

### BUG-003c: `isLoading` Race Condition in Root Route Handling

| Field | Value |
|-------|-------|
| **ID** | BUG-003c |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/app/routes.tsx`, `frontend/src/features/auth/model/useAuth.ts` |
| **Classification** | advisory |

**Description:**
The `useAuth` hook initializes `isLoading` to `true` (`useAuth.ts:8`). When the root route unconditionally redirects to `/login` before `useAuth` completes its silent refresh, an authenticated user with an expired access token but a valid refresh cookie will:

1. Hit `/` → immediately redirected to `/login`
2. `LoginForm` mounts → `useAuth` runs → attempts silent refresh → succeeds
3. User is now authenticated but sees the login form (or is redirected if BUG-003b is fixed)

This is a race condition between the route guard and the auth initialization. The fix for BUG-003 (making the root route auth-aware) will also resolve this issue, as the root component should wait for `isLoading` to become `false` before deciding where to redirect.

**Evidence:**
- `useAuth.ts:8` — `const [isLoading, setIsLoading] = useState(true)`
- `useAuth.ts:53-87` — `useEffect` runs silent refresh asynchronously; `isLoading` stays `true` until complete
- `routes.tsx:117` — Redirect happens synchronously before any async auth check

**Recommendation:**
Resolved by fixing BUG-003. The root redirect component must await the `isLoading` state before making a routing decision.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 3 |
| MEDIUM | 2 |
| LOW | 0 |

## Mandatory Fixes

| ID | Issue | File | Effort |
|----|-------|------|--------|
| BUG-001 | Layout field not sent to backend; frontend-backend model mismatch for `layout` vs `layout_id` | `DashboardManagement.tsx`, `adminApi.ts`, `dashboard.py` | medium — requires either a mapping layer or a new layouts concept on the backend |
| BUG-002 | DataGrid `getActions` missing on `type: 'actions'` column crashes Registration Requests tab | `RegistrationRequests.tsx` | small — replace `type: 'actions'` with `renderCell` pattern (matching DashboardManagement) |
| BUG-003 | Root `/` unconditionally redirects to `/login` instead of checking auth state | `routes.tsx` | small — create auth-aware root redirect component |

## Advisory Recommendations

| ID | Issue | File | Effort |
|----|-------|------|--------|
| BUG-003b | Authenticated users can still access `/login` | `LoginForm.tsx` | trivial — add auth check at top of component |
| BUG-003c | Race condition between route redirect and async auth initialization | `routes.tsx`, `useAuth.ts` | resolved by BUG-003 fix |

## Doc Updates Needed

| ID | Doc | Update |
|----|-----|--------|
| BUG-001 | `docs/02-dashboards/` | Document that layout must be resolved to a `layout_id` UUID before dashboard creation. If layouts don't exist as a backend concept yet, document this as a known gap. |
| BUG-003 | `docs/01-auth/` | Update auth flow description to reflect: root `/` should redirect to `/dashboards` for authenticated users and to `/login` for unauthenticated users, with a loading state during silent refresh. |

---

## Additional Observations (Non-Bug)

### A-001: `description` field max length not enforced on backend

**Severity:** LOW | **Type:** BEST-PRACTICE

The frontend caps `description` at 200 characters (`DashboardManagement.tsx:216`), but the backend `DashboardCreate` model (`dashboard.py:54`) has no `max_length` constraint on the `description` field. A direct API call could send an arbitrarily long description.

**Recommendation:** Add `max_length=200` (or a `StringConstraints(max_length=200)`) to `DashboardCreate.description` and `DashboardUpdate.description` for defense-in-depth.
