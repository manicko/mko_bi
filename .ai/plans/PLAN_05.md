---
phase: "05 — Frontend Error Handling"
description: "Implement comprehensive frontend error handling: MUI-styled error pages (404/500), two-tier Error Boundary, 403 toast in axios interceptor, backend client-errors endpoint. Rewrite NotFound.tsx from Tailwind to MUI."
autonomous: true
depends_on: []
files_modified:
  - frontend/src/shared/components/ErrorPage.tsx
  - frontend/src/shared/components/ErrorBoundary.tsx
  - frontend/src/shared/components/NotFound.tsx
  - frontend/src/shared/components/index.ts
  - frontend/src/app/routes.tsx
  - frontend/src/app/providers.tsx
  - frontend/src/shared/api/axiosInstance.ts
  - src/mkobi/api/routes/client_errors.py
  - src/mkobi/api/routes/__init__.py
  - src/mkobi/app.py
waves:
  - id: 1
    tasks: [TASK_01, TASK_02]
    parallel: true
  - id: 2
    tasks: [TASK_03, TASK_04]
    parallel: true
  - id: 3
    tasks: [TASK_05, TASK_06]
    parallel: true
  - id: 4
    tasks: [TASK_07]
    parallel: false
---

# PLAN_05: Frontend Error Handling

## must_haves

When this phase is complete, ALL of the following must be true:

1. **404 page (MUI):** Unknown routes show a MUI-styled error page with `WarningAmber` icon, "Page not found" heading, "The page you are looking for does not exist." subtext, and a single "Go to Home" button. No Tailwind CSS classes remain in `NotFound.tsx`.
2. **500 page (Error Boundary):** React Error Boundary catches JS crashes and shows a MUI-styled error page with `WarningAmber` icon. In development: error name + message visible. In production: generic "Something went wrong" + "An unexpected error occurred." Primary button "Reload page", secondary link "Go to Home".
3. **"Go to Home" smart navigation:** On both 404 and 500 pages, "Go to Home" navigates to `/dashboards` if user is authenticated (useAuth().user is non-null), `/login` if not.
4. **Two-tier Error Boundary:** Route-level boundary wraps protected routes in `routes.tsx`. App-level boundary wraps `<AppRoutes />` in `providers.tsx`.
5. **403 toast:** Axios interceptor handles 403 responses with `toast.error('Access denied')`. User stays on current page.
6. **Client error reporting:** In production, `componentDidCatch` POSTs error details to `POST /api/v1/client-errors`. Fire-and-forget (never throws, never blocks render).
7. **Backend endpoint:** New `POST /api/v1/client-errors` endpoint accepts Pydantic model, logs via `logger.error()`. No DB persistence.
8. **401 unchanged:** Existing 401 auto-redirect to `/login` behavior preserved.
9. **No regressions:** Existing error flows (TanStack Query refetch for API errors, ProtectedRoute redirect) remain functional.

---

## Wave 1 (Parallel — independent foundation tasks)

### TASK_01: Create shared ErrorPage component

**File:** `frontend/src/shared/components/ErrorPage.tsx` (NEW)
**Symbol:** `ErrorPage` component
**Semantic anchor:** New file — no existing anchor.

**Changes:**

Create a new shared component that renders MUI-styled error pages for both 404 and 500 variants:

```tsx
import WarningAmber from '@mui/icons-material/WarningAmber'
import { Box, Container, Typography, Button } from '@mui/material'
import { useAuth } from '../../features/auth/model/useAuth'

interface ErrorPageProps {
  variant: '404' | '500'
  error?: Error | null
}

export function ErrorPage({ variant, error }: ErrorPageProps) {
  const { user } = useAuth()
  const isDev = import.meta.env.DEV
  const goToHome = user ? '/dashboards' : '/login'

  if (variant === '404') {
    return (
      <Container maxWidth="sm">
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', textAlign: 'center' }}>
          <WarningAmber sx={{ fontSize: 64, color: 'warning.main', mb: 2 }} />
          <Typography variant="h4" gutterBottom>Page not found</Typography>
          <Typography variant="body1" color="text.secondary">The page you are looking for does not exist.</Typography>
          <Button variant="contained" href={goToHome} sx={{ mt: 3 }}>Go to Home</Button>
        </Box>
      </Container>
    )
  }

  return (
    <Container maxWidth="sm">
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', textAlign: 'center' }}>
        <WarningAmber sx={{ fontSize: 64, color: 'warning.main', mb: 2 }} />
        <Typography variant="h4" gutterBottom>
          {isDev && error ? error.name : 'Something went wrong'}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {isDev && error ? error.message : 'An unexpected error occurred.'}
        </Typography>
        <Button variant="contained" onClick={() => window.location.reload()} sx={{ mt: 3 }}>Reload page</Button>
        <Button variant="text" href={goToHome} sx={{ mt: 1 }}>Go to Home</Button>
      </Box>
    </Container>
  )
}
```

**Rationale:** Single shared component with `variant` prop avoids duplication. Uses `import.meta.env.DEV` (Vite's env flag) to gate detailed errors. `useAuth().user` determines smart "Go to Home" destination. MUI `WarningAmber` icon with `warning.main` color matches the amber triangle design from DECISION_05.md. Path-based icon import matches existing codebase pattern (see `Header.tsx`).

**Acceptance criteria:**
- `ErrorPage variant="404"` renders: WarningAmber icon, "Page not found", subtext, single "Go to Home" button
- `ErrorPage variant="500"` renders: WarningAmber icon, error details (dev) or generic message (prod), "Reload page" button, "Go to Home" link
- "Go to Home" links to `/dashboards` when `user` is non-null, `/login` when null
- No Tailwind CSS — pure MUI `sx` prop styling
- Uses path-based `@mui/icons-material/WarningAmber` import

**Validation:**
- `cd frontend && npx tsc --noEmit` — no type errors

---

### TASK_02: Create backend client-errors endpoint

**File:** `src/mkobi/api/routes/client_errors.py` (NEW)
**Symbol:** `report_client_error` route handler
**Semantic anchor:** New file — no existing anchor.

**File:** `src/mkobi/api/routes/__init__.py`
**Symbol:** Route imports
**Semantic anchor:** Lines 3-14 — existing import block and `__all__` list.

**File:** `src/mkobi/app.py`
**Symbol:** Router registration
**Semantic anchor:** Lines 159-168 — existing `include_router` calls.

**Changes:**

1. Create `src/mkobi/api/routes/client_errors.py`:

```python
"""Client-side error reporting route.

Provides an endpoint for the frontend ErrorBoundary to report
JavaScript errors for monitoring and debugging.
"""

from pydantic import BaseModel

from fastapi import APIRouter

from mkobi.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/client-errors", tags=["client-errors"])


class ClientErrorPayload(BaseModel):
    error: dict
    componentStack: str | None = None
    url: str
    userAgent: str
    timestamp: str


@router.post(
    "",
    status_code=204,
    summary="Report client-side error",
    description="Receives error reports from the frontend ErrorBoundary for monitoring.",
)
async def report_client_error(payload: ClientErrorPayload) -> None:
    """Receive and log a client-side error report."""
    logger.error(
        "Client error: %s | url=%s | componentStack=%s",
        payload.error.get("message", "Unknown"),
        payload.url,
        payload.componentStack,
    )
```

2. Update `src/mkobi/api/routes/__init__.py` — add import and `__all__` entry:

```python
from mkobi.api.routes import (
    auth,
    client_errors,
    users,
    dashboards,
    layouts,
    upload,
    data,
    filters,
    processing_configs,
    processing_logs,
    admin,
)

__all__ = [
    "auth",
    "client_errors",
    "users",
    "dashboards",
    "layouts",
    "upload",
    "data",
    "filters",
    "processing_configs",
    "processing_logs",
    "admin",
]
```

3. Update `src/mkobi/app.py` — add router registration after existing routes (after line 168):

```python
    application.include_router(routes.client_errors.router, prefix="/api/v1")
```

**Rationale:** Pydantic model validates incoming payload. `status_code=204` (No Content) since the frontend doesn't need a response body — fire-and-forget. Uses `get_logger(__name__)` which follows the `mkobi.core.logging_config` pattern. No DB persistence — just logging, as specified in DECISION_05.md and RESEARCH_05.md.

**Acceptance criteria:**
- `POST /api/v1/client-errors` accepts JSON payload with `error`, `componentStack`, `url`, `userAgent`, `timestamp`
- Returns HTTP 204 No Content
- Logs error message via `logger.error()`
- Invalid payload returns 422 (Pydantic validation — automatic)
- No database table or migration needed

**Validation:**
- `cd src/mkobi && python -c "from mkobi.api.routes import client_errors; print('OK')"` — import succeeds
- Backend starts without errors

---

## Wave 2 (Parallel — depends on Wave 1)

### TASK_03: Create ErrorBoundary class component

**File:** `frontend/src/shared/components/ErrorBoundary.tsx` (NEW)
**Symbol:** `ErrorBoundary` class
**Semantic anchor:** New file — depends on `ErrorPage.tsx` from TASK_01.

**Changes:**

Create a class-based Error Boundary that catches render errors and renders the 500 `ErrorPage` fallback:

```tsx
import { Component, ErrorInfo, ReactNode } from 'react'
import { ErrorPage } from './ErrorPage'

interface ErrorBoundaryProps {
  children: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    if (import.meta.env.DEV) {
      console.error('[ErrorBoundary]', error)
      console.error('Component stack:', errorInfo.componentStack)
    } else {
      this.reportError(error, errorInfo.componentStack)
    }
  }

  private reportError(error: Error, componentStack: string | null): void {
    const payload = {
      error: {
        name: error.name,
        message: error.message,
        stack: error.stack,
      },
      componentStack,
      url: window.location.href,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
    }

    fetch('/api/v1/client-errors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).catch(() => {
      // Error reporting must never cause secondary failures
    })
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return <ErrorPage variant="500" error={this.state.error} />
    }
    return this.props.children
  }
}
```

**Rationale:** Class component is required — React has no hook-based Error Boundary. `getDerivedStateFromError` updates state to trigger fallback render. `componentDidCatch` handles logging: `console.error` in dev, fire-and-forget `fetch` POST in production. The `.catch(() => {})` swallows any network failures to prevent secondary errors. Fallback UI is static (no data fetching) to prevent cascading failures.

**Acceptance criteria:**
- Class component with `getDerivedStateFromError` and `componentDidCatch`
- Renders `<ErrorPage variant="500" error={this.state.error} />` when `hasError` is true
- In dev: logs to console via `console.error`
- In production: POSTs to `/api/v1/client-errors` (fire-and-forget, errors swallowed)
- Fallback UI is static — no data fetching, no hooks that could fail

**Validation:**
- `cd frontend && npx tsc --noEmit` — no type errors

---

### TASK_04: Rewrite NotFound.tsx from Tailwind to MUI

**File:** `frontend/src/shared/components/NotFound.tsx`
**Symbol:** `NotFound` component
**Semantic anchor:** Lines 1-16 — entire file. Currently uses Tailwind CSS classes (`flex`, `text-gray-800`, etc.) and raw `<Link>`.

**Changes:**

Replace the entire file content to delegate to `ErrorPage`:

```tsx
import { ErrorPage } from './ErrorPage'

export function NotFound() {
  return <ErrorPage variant="404" />
}
```

**Rationale:** DECISION_05.md explicitly requires rewriting `NotFound.tsx` from Tailwind to MUI. Delegating to `ErrorPage` avoids code duplication and ensures consistent styling. The `*` route in `routes.tsx` (line 63) already renders `<NotFound />`, so no route changes needed.

**Acceptance criteria:**
- No Tailwind CSS classes remain in the file
- Renders the 404 variant of `ErrorPage` (WarningAmber icon, "Page not found", subtext, "Go to Home" button)
- Exported as named export `NotFound`

**Validation:**
- `cd frontend && npx tsc --noEmit` — no type errors
- Grep for `className` in NotFound.tsx — zero matches

---

## Wave 3 (Parallel — depends on Wave 2)

### TASK_05: Add Error Boundary wrappers to routes.tsx

**File:** `frontend/src/app/routes.tsx`
**Symbol:** `AppRoutes` component
**Semantic anchor:** Lines 14-67 — entire function body. Lines 19-64 — `<Route element={<AppLayout />}>` block containing all protected routes.

**Changes:**

1. Add `ErrorBoundary` import (after line 4):
```typescript
import { ErrorBoundary } from '../shared/components/ErrorBoundary'
```

2. Wrap the protected routes inside `<Route element={<AppLayout />}>` with `<ErrorBoundary />`. The `<ErrorBoundary />` should be a sibling wrapper alongside `<ProtectedRoute>` for the route group. Since React Router v7 doesn't support multiple wrapper components on a single `<Route>` directly, use a layout route pattern:

```typescript
export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginForm />} />
      <Route path="/register" element={<RegisterForm />} />
      <Route element={<AppLayout />}>
        <Route element={<ErrorBoundary />}>
          <Route
            path="/dashboards"
            element={
              <ProtectedRoute>
                <DashboardList />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard/:id"
            element={
              <ProtectedRoute>
                <DashboardView />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <ProtectedRoute>
                <RoleBasedAccess roles={['admin']}>
                  <AdminPanel />
                </RoleBasedAccess>
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <UserProfile />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile/change-password"
            element={
              <ProtectedRoute>
                <ChangePasswordPage />
              </ProtectedRoute>
            }
          />
        </Route>
        <Route path="/" element={<Navigate to="/dashboards" replace />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
```

**Rationale:** The `<ErrorBoundary />` is placed as a layout route wrapping all protected routes inside `AppLayout`. This means a crash in any protected route (dashboards, admin, profile) will be caught and show the 500 error page, while the layout (sidebar, header) remains intact. Login/register are outside this boundary — they are simple forms with low crash risk, and the app-level boundary (TASK_07) catches anything that escapes. The `*` route for 404 is outside the ErrorBoundary since 404 is not a crash — it's a routing event.

**Acceptance criteria:**
- `ErrorBoundary` wraps all protected routes (dashboards, admin, profile) as a layout route
- Login and register routes are outside the route-level ErrorBoundary
- 404 route (`*`) remains outside the ErrorBoundary
- All existing route elements and wrappers (ProtectedRoute, RoleBasedAccess) remain unchanged

**Validation:**
- `cd frontend && npx tsc --noEmit` — no type errors

---

### TASK_06: Add 403 toast handling to axios interceptor

**File:** `frontend/src/shared/api/axiosInstance.ts`
**Symbol:** Response interceptor
**Semantic anchor:** Lines 29-39 — the response error interceptor function.

**Changes:**

Add a 403 handler after the existing 401 handler inside the response interceptor:

```typescript
// Response interceptor - handle errors
axiosInstance.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      removeToken()
      toast.error('Session expired. Please login again.')
      window.location.href = '/login'
    }
    if (error.response?.status === 403) {
      toast.error('Access denied')
    }
    return Promise.reject(error)
  }
)
```

**Rationale:** DECISION_05.md specifies 403 should show a toast notification and keep the user on the current page. The 403 handler is placed after 401 so both can fire independently (though 401 redirects, so 403 won't be reached in that case). `toast.error('Access denied')` uses the existing `react-hot-toast` import already in the file. The error is still rejected so TanStack Query's error handling continues to work (inline error states with refetch).

**Acceptance criteria:**
- 403 responses trigger `toast.error('Access denied')`
- User stays on current page (no redirect)
- 401 behavior unchanged (remove token → toast → redirect to `/login`)
- Error is still rejected via `Promise.reject(error)` so TanStack Query handles it
- No new imports needed — `toast` is already imported

**Validation:**
- `cd frontend && npx tsc --noEmit` — no type errors

---

## Wave 4 (Sequential — final integration)

### TASK_07: Add app-level ErrorBoundary to providers.tsx + export new components

**File:** `frontend/src/app/providers.tsx`
**Symbol:** `App` component
**Semantic anchor:** Lines 23-46 — the `App` function return JSX. Line 41 — `<AppRoutes />`.

**File:** `frontend/src/shared/components/index.ts`
**Symbol:** Barrel exports
**Semantic anchor:** Lines 1-8 — existing exports.

**Changes:**

1. Update `providers.tsx` — add `ErrorBoundary` import and wrap `<AppRoutes />`:

```typescript
import { ErrorBoundary } from '../shared/components/ErrorBoundary'
```

Wrap `<AppRoutes />` (line 41):
```tsx
          <ErrorBoundary>
            <AppRoutes />
          </ErrorBoundary>
```

Full updated `providers.tsx`:

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { Toaster } from 'react-hot-toast'
import { AppRoutes } from './routes'
import { ErrorBoundary } from '../shared/components/ErrorBoundary'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5 * 60 * 1000,
    },
  },
})

const theme = createTheme({
  palette: {
    mode: 'light',
  },
})

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <Toaster
            position="top-right"
            gutter={8}
            toastOptions={{
              success: {
                duration: 3000,
              },
              error: {
                duration: 5000,
              },
            }}
          />
          <ErrorBoundary>
            <AppRoutes />
          </ErrorBoundary>
        </ThemeProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
```

2. Update `shared/components/index.ts` — add exports for new components:

```typescript
export { AppLayout } from './Layout/AppLayout'
export { Header } from './Layout/Header'
export { Sidebar } from './Layout/Sidebar'
export { ProtectedRoute } from './ProtectedRoute'
export { RoleBasedAccess } from './RoleBasedAccess'
export { AccessDenied } from './AccessDenied'
export { ConfirmDialog } from './ConfirmDialog'
export { ErrorPage } from './ErrorPage'
export { ErrorBoundary } from './ErrorBoundary'
```

**Rationale:** The app-level ErrorBoundary in `providers.tsx` is the ultimate safety net. If the route-level boundary's fallback UI itself crashes, or if an error occurs outside the route structure (e.g., in the Toaster or ThemeProvider), this top-level boundary catches it. The barrel export in `index.ts` follows the existing pattern and makes imports clean for any future consumers of `ErrorPage` or `ErrorBoundary`.

**Acceptance criteria:**
- `<ErrorBoundary>` wraps `<AppRoutes />` in `providers.tsx`
- `ErrorPage` and `ErrorBoundary` are exported from `shared/components/index.ts`
- All existing exports in `index.ts` remain unchanged
- App renders without errors

**Validation:**
- `cd frontend && npx tsc --noEmit` — no type errors
- `cd frontend && npm run lint` — no lint errors

---

## Execution Order Summary

| Wave | Task | File(s) | Dependencies |
|------|------|---------|-------------|
| 1 | TASK_01 | `ErrorPage.tsx` (new) | None |
| 1 | TASK_02 | `client_errors.py` (new), `__init__.py`, `app.py` | None |
| 2 | TASK_03 | `ErrorBoundary.tsx` (new) | TASK_01 (ErrorPage) |
| 2 | TASK_04 | `NotFound.tsx` | TASK_01 (ErrorPage) |
| 3 | TASK_05 | `routes.tsx` | TASK_03 (ErrorBoundary) |
| 3 | TASK_06 | `axiosInstance.ts` | None |
| 4 | TASK_07 | `providers.tsx`, `index.ts` | TASK_03 (ErrorBoundary), TASK_05 (routes) |

**Wave dependencies:** Wave 1 (TASK_01 + TASK_02) runs first in parallel. Wave 2 (TASK_03 + TASK_04) depends on TASK_01. Wave 3 (TASK_05 + TASK_06) depends on TASK_03. Wave 4 (TASK_07) depends on TASK_03 and TASK_05.

---

## Final Validation (All Tasks Complete)

1. `cd frontend && npx tsc --noEmit` — zero type errors
2. `cd frontend && npm run lint` — zero lint errors
3. Backend starts without errors (`uvicorn mkobi.app:create_app`)
4. Manual verification checklist:
   - [ ] Navigate to `/nonexistent` → 404 page with WarningAmber icon, "Page not found", "Go to Home" button
   - [ ] "Go to Home" navigates to `/dashboards` (authenticated) or `/login` (unauthenticated)
   - [ ] 401 response → auto-redirect to `/login` (existing behavior preserved)
   - [ ] 403 response → "Access denied" toast, user stays on page
   - [ ] `NotFound.tsx` has zero `className` attributes (no Tailwind)
   - [ ] `ErrorPage` and `ErrorBoundary` exported from `shared/components/index.ts`
   - [ ] `POST /api/v1/client-errors` returns 204, logs error
