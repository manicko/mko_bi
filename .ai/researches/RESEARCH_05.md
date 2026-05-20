# 05 Frontend Error Handling - Research

**Researched:** 2026-05-20
**Domain:** React 19 Error Boundaries, MUI v9 error pages, axios interceptors, client-side error logging
**Confidence:** HIGH

## Summary

This research covers implementing comprehensive frontend error handling for the mkobi BI Dashboard (React 19 + MUI v9). The phase requires: (1) rewriting `NotFound.tsx` from Tailwind to MUI, (2) creating a shared `ErrorPage.tsx` component with two variants (404 and 500), (3) creating an `ErrorBoundary.tsx` class component with two-tier wrapping (route-level and app-level), (4) adding 403 toast handling to the existing axios interceptor, and (5) creating a new backend endpoint `POST /api/v1/client-errors` for production error logging.

**Primary recommendation:** Use a custom class-based Error Boundary (not a library) since the project already uses class components (`ProtectedRoute` pattern) and the React 19 `createRoot` `onUncaughtError`/`onCaughtError` hooks are NOT needed — the Error Boundary's `componentDidCatch` is sufficient for this scope. Use MUI v9 `WarningAmber` icon (already installed via `@mui/icons-material@9.0.0`) with the existing barrel-import style (`import WarningAmber from '@mui/icons-material/WarningAmber'`).

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| react | 19.2.5 | UI framework | Already in use; Error Boundary is built-in |
| @mui/material | 9.0.0 | UI components | Already in use; Box, Container, Typography, Button |
| @mui/icons-material | 9.0.0 | MUI icons | Already installed; WarningAmber icon |
| react-hot-toast | 2.6.0 | Toast notifications | Already in use for 401 and success/error toasts |
| axios | 1.16.0 | HTTP client | Already in use with interceptors |
| react-router-dom | 7.15.0 | Routing | Already in use; `*` route for 404 |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @emotion/react | 11.14.0 | CSS-in-JS for MUI | Already installed as MUI peer dep |
| @emotion/styled | 11.14.1 | CSS-in-JS for MUI | Already installed as MUI peer dep |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom class Error Boundary | `react-error-boundary` library (v6.1.1) | Adds 1 dependency; provides `useErrorBoundary` hook for async errors and `resetKeys`. Not needed since the phase only requires basic Error Boundary + `componentDidCatch` logging. Custom class is simpler and matches existing codebase patterns. |
| React 19 `createRoot` error hooks | `onUncaughtError`/`onCaughtError` in `main.tsx` | These are global error reporting hooks (like Sentry integration), not UI fallbacks. They don't render fallback UI. The Error Boundary handles UI; these hooks are for external monitoring only. Out of scope for this phase. |

**Installation:** No new packages needed. All dependencies are already installed.

## Architecture Patterns

### Recommended Project Structure

```
frontend/src/
├── app/
│   ├── providers.tsx          # Add top-level ErrorBoundary wrapper
│   └── routes.tsx             # Add route-level ErrorBoundary wrappers
├── shared/
│   ├── api/
│   │   └── axiosInstance.ts   # Add 403 toast handling in interceptor
│   └── components/
│       ├── ErrorPage.tsx      # NEW: shared error page component (404 + 500 variants)
│       ├── ErrorBoundary.tsx  # NEW: class-based Error Boundary
│       ├── NotFound.tsx       # REWRITE: Tailwind -> MUI, delegate to ErrorPage
│       └── index.ts           # Add exports for ErrorPage, ErrorBoundary
```

### Pattern 1: Class-Based Error Boundary (React standard)

**What:** A React class component implementing `static getDerivedStateFromError()` and `componentDidCatch()` to catch rendering errors in child components and display fallback UI.

**When to use:** Wrapping route sections and the entire app to prevent blank screens on JS crashes.

**Example:**
```typescript
// Source: https://github.com/reactjs/react.dev/blob/main/src/content/reference/react/Component.md
import { Component, ErrorInfo, ReactNode } from 'react'

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
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
    console.error('[ErrorBoundary]', error, errorInfo.componentStack)
  }

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }
      return null
    }
    return this.props.children
  }
}
```

### Pattern 2: Two-Tier Error Boundary Placement

**What:** Route-level boundaries around logical route groups in `routes.tsx`, plus an app-level boundary wrapping the entire app in `providers.tsx`.

**When to use:** Route-level boundaries isolate crashes to specific sections (e.g., dashboard view crashing doesn't kill the sidebar). The app-level boundary is the ultimate safety net.

**Example:**
```tsx
// In providers.tsx - top-level (app-level) boundary
export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <Toaster ... />
          <ErrorBoundary>
            <AppRoutes />
          </ErrorBoundary>
        </ThemeProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

// In routes.tsx - route-level boundaries around logical groups
export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginForm />} />
      <Route path="/register" element={<RegisterForm />} />
      <Route element={<AppLayout />}>
        <Route element={<ErrorBoundary />}>
          <Route path="/dashboards" element={<ProtectedRoute><DashboardList /></ProtectedRoute>} />
          <Route path="/dashboard/:id" element={<ProtectedRoute><DashboardView /></ProtectedRoute>} />
          ...
        </Route>
      </Route>
    </Routes>
  )
}
```

### Pattern 3: Shared ErrorPage Component with Variants

**What:** A single `ErrorPage.tsx` component that accepts a `variant` prop (`'404'` | `'500'`) and renders the appropriate MUI-styled error page.

**When to use:** Used as the `fallback` prop for `ErrorBoundary` and as the content for the rewritten `NotFound.tsx`.

**Example:**
```tsx
import WarningAmber from '@mui/icons-material/WarningAmber'
import { Box, Container, Typography, Button } from '@mui/material'
import { useAuth } from '../../features/auth'

interface ErrorPageProps {
  variant: '404' | '500'
  error?: Error | null
}

export function ErrorPage({ variant, error }: ErrorPageProps) {
  const { user } = useAuth()
  const isDev = process.env.NODE_ENV === 'development'
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

  // 500 variant
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

### Pattern 4: Axios 403 Toast Handling

**What:** Extend the existing response interceptor in `axiosInstance.ts` to handle 403 responses with a toast notification.

**When to use:** When an API call returns 403 (forbidden), show "Access denied" toast instead of silently failing.

**Example:**
```typescript
// In axiosInstance.ts - add to existing response interceptor
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

### Anti-Patterns to Avoid

- **Using a function component as Error Boundary:** React requires class components for Error Boundaries. There is no hook equivalent. Don't try to use `useEffect` or `useState` to simulate an Error Boundary.
- **Catching errors in the Error Boundary itself:** An Error Boundary cannot catch its own errors. If the fallback UI throws, it will propagate to the next boundary above.
- **Using Error Boundary for async errors:** Error Boundaries only catch errors during rendering, lifecycle methods, and constructors. They do NOT catch errors in `useEffect`, event handlers, or promises. TanStack Query's `refetch` handles API errors.
- **Showing raw errors in production:** Always gate detailed error messages behind `process.env.NODE_ENV === 'development'`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Error Boundary | Custom hook-based error catcher | React class Component with `getDerivedStateFromError` + `componentDidCatch` | React only supports class components for Error Boundaries. Hooks cannot catch render errors. |
| Error logging transport | Custom retry/queue logic | Simple `fetch` POST with `.catch` swallow | Error reporting must never cause secondary failures. Keep it simple: fire-and-forget with a `.catch` that logs to console. |
| MUI icon | Custom SVG or icon font | `@mui/icons-material/WarningAmber` | Already installed, tree-shakeable, standard MUI pattern used throughout codebase. |
| Toast notifications | Custom toast component | `react-hot-toast` | Already in use for 401, success, and error toasts. Consistent UX. |

**Key insight:** The Error Boundary must be a class component — this is a React framework limitation, not a choice. The `react-error-boundary` library wraps this in a nicer API but adds a dependency. Since the project only needs basic Error Boundary + `componentDidCatch` logging, a custom class is simpler.

## Common Pitfalls

### Pitfall 1: Error Boundary Does Not Catch Async/Event Handler Errors

**What goes wrong:** Developers expect Error Boundaries to catch all errors, but they only catch errors during rendering, lifecycle methods, and constructors.

**Why it happens:** React's error boundary mechanism works by catching errors thrown during the render phase. Async code (promises, `setTimeout`, `useEffect`) and event handlers run outside the render phase.

**How to avoid:** For API errors, rely on TanStack Query's built-in error handling with `refetch`. For event handler errors, use standard `try/catch`. For async errors in effects, use TanStack Query's error state.

**Warning signs:** Error Boundary doesn't trigger when an API call fails or when a button click handler throws.

### Pitfall 2: Error in Error Boundary Fallback Propagates Up

**What goes wrong:** If the fallback UI itself throws an error, it propagates to the next Error Boundary above. If there's no parent boundary, the entire app unmounts.

**Why it happens:** Error Boundaries only catch errors in their children, not in themselves.

**How to avoid:** Keep fallback UI simple (static MUI components, no data fetching). The two-tier approach (route-level + app-level) provides redundancy: if the route-level fallback crashes, the app-level boundary catches it.

**Warning signs:** Blank screen even with Error Boundary in place.

### Pitfall 3: Production vs Development Error Display

**What goes wrong:** Showing stack traces and error details in production exposes internal implementation details to users.

**Why it happens:** Developers forget to gate error details behind `process.env.NODE_ENV` checks.

**How to avoid:** Always use `process.env.NODE_ENV === 'development'` to conditionally show error name/message. In production, show generic "Something went wrong" message.

**Warning signs:** Users see technical error messages in production builds.

### Pitfall 4: Error Reporting Endpoint Failure

**What goes wrong:** If the `POST /api/v1/client-errors` endpoint fails or is slow, it could block the Error Boundary's render or cause secondary errors.

**Why it happens:** The `componentDidCatch` method fires synchronously during React's error handling phase.

**How to avoid:** Make the error report a fire-and-forget `fetch` call. Never `await` it. Always `.catch` and swallow errors in the reporter. The error reporting path must never throw.

**Warning signs:** Error Boundary causes additional errors or UI freezes.

### Pitfall 5: MUI Icon Import Style (v9)

**What goes wrong:** Using barrel imports (`import { WarningAmber } from '@mui/icons-material'`) can significantly increase bundle size in MUI v9.

**Why it happens:** Barrel imports pull in the entire icons package.

**How to avoid:** Use default path-based imports: `import WarningAmber from '@mui/icons-material/WarningAmber'`. This matches the existing codebase pattern (see `Header.tsx`, `FileDropzone.tsx`).

**Warning signs:** Large bundle size, slow builds.

### Pitfall 6: React 19 `createRoot` Error Hooks Confusion

**What goes wrong:** React 19 introduced `onUncaughtError`/`onCaughtError` options for `createRoot`, which might seem like alternatives to Error Boundaries.

**Why it happens:** These are new React 19 APIs that are easy to confuse with Error Boundaries.

**How to avoid:** These hooks are for global error **reporting** (like Sentry integration), not for rendering fallback UI. They don't replace Error Boundaries. The current `main.tsx` uses `ReactDOM.createRoot` without these options — that's correct for this phase. Don't add them.

**Warning signs:** Trying to use `onUncaughtError` to render fallback UI (it can't).

## Code Examples

### ErrorBoundary.tsx — Full Implementation

```typescript
// Source: React official docs + verified patterns from react-error-boundary source
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
    if (process.env.NODE_ENV === 'development') {
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

### NotFound.tsx — Rewritten to MUI

```typescript
import { ErrorPage } from './ErrorPage'

export function NotFound() {
  return <ErrorPage variant="404" />
}
```

### routes.tsx — With Error Boundary Wrappers

```typescript
import { Navigate, Route, Routes } from 'react-router-dom'
import { ErrorBoundary } from '../shared/components/ErrorBoundary'
// ... other imports unchanged

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginForm />} />
      <Route path="/register" element={<RegisterForm />} />
      <Route element={<AppLayout />}>
        <Route element={<ErrorBoundary />}>
          <Route path="/dashboards" element={<ProtectedRoute><DashboardList /></ProtectedRoute>} />
          <Route path="/dashboard/:id" element={<ProtectedRoute><DashboardView /></ProtectedRoute>} />
          <Route path="/admin" element={<ProtectedRoute><RoleBasedAccess roles={['admin']}><AdminPanel /></RoleBasedAccess></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute><UserProfile /></ProtectedRoute>} />
          <Route path="/profile/change-password" element={<ProtectedRoute><ChangePasswordPage /></ProtectedRoute>} />
        </Route>
        <Route path="/" element={<Navigate to="/dashboards" replace />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
```

### providers.tsx — With Top-Level Error Boundary

```typescript
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
              success: { duration: 3000 },
              error: { duration: 5000 },
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

### Backend: POST /api/v1/client-errors Endpoint

```python
# In a new file: src/mkobi/api/routes/client_errors.py
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
        payload.error.get('message', 'Unknown'),
        payload.url,
        payload.componentStack,
    )
```

```python
# In src/mkobi/api/routes/__init__.py, add:
from mkobi.api.routes import client_errors
# Add to __all__ list

# In src/mkobi/app.py, add:
application.include_router(routes.client_errors.router, prefix="/api/v1")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|-----------------|--------------|--------|
| `componentWillMount` + `unstable_handleError` (React 15) | `static getDerivedStateFromError` + `componentDidCatch` (React 16+) | React 16 (2017) | Stable Error Boundary API |
| Manual error logging in every component | Centralized `componentDidCatch` in Error Boundary | React 16+ | Single point of error capture |
| `window.onerror` for all errors | Error Boundary for render errors + `window.onerror` for global | React 16+ | Separation of concerns |
| React 18 `createRoot` without error hooks | React 19 `createRoot` with `onUncaughtError`/`onCaughtError` | React 19 (Dec 2024) | Global error reporting hooks (for monitoring services, not UI fallback) |
| `react-error-boundary` v3/v4 | `react-error-boundary` v6 (Jan 2026) | Ongoing | Modern API with `useErrorBoundary` hook for async errors |

**Deprecated/outdated:**
- `unstable_handleError` (React 15): Removed in React 16, replaced by `componentDidCatch`
- `InfoOutline` and 22 other barrel-exported icons without "d" suffix: Removed in MUI v9, use `InfoOutlined` instead. Not affected: `WarningAmber` is a standard icon name.

## Open Questions

1. **Should the Error Boundary support a `reset` mechanism?**
   - What we know: The `react-error-boundary` library provides `resetErrorBoundary()` to retry rendering after an error. The current phase specifies "Reload page" as the primary action for 500 errors, which does a full `window.location.reload()`.
   - What's unclear: Whether a soft reset (clearing error state without full reload) is needed.
   - Recommendation: Use `window.location.reload()` as specified. No soft reset needed for this phase. The Error Boundary's `getDerivedStateFromError` can be extended later with a `resetKey` pattern if needed.

2. **Should the `POST /api/v1/client-errors` endpoint store errors in the database?**
   - What we know: The phase says "POST to a new backend endpoint for monitoring." The backend currently uses PostgreSQL.
   - What's unclear: Whether errors should be persisted to a table or just logged.
   - Recommendation: For this phase, just log the error via `logger.error()`. Database persistence can be added later when the "error analytics dashboard" phase (deferred) is implemented.

3. **Should the route-level Error Boundary wrap ALL routes or just specific ones?**
   - What we know: The phase says "boundary around each route section in `routes.tsx`."
   - What's unclear: Whether `/login` and `/register` (outside `AppLayout`) need boundaries.
   - Recommendation: Wrap the entire `<Route element={<AppLayout />}>` content in a single `<ErrorBoundary />` route wrapper. Login/register are simple forms with low crash risk. The app-level boundary catches anything that escapes.

## Sources

### Primary (HIGH confidence)
- React official docs (Context7 `/reactjs/react.dev`) — Error Boundary class component pattern, `getDerivedStateFromError`, `componentDidCatch`
- MUI official docs (Context7 `/mui/material-ui`) — Icon import patterns, `sx` prop, Typography variants
- react-hot-toast GitHub (Context7 `/timolins/react-hot-toast`) — `toast.error()` API
- React 19 release notes (react.dev/blog/2024/04/25/react-19) — `onUncaughtError`/`onCaughtError` root options
- MUI v9 upgrade guide (next.mui.com) — Icon naming changes, removed exports
- `@mui/icons-material` npm page — v9.0.1 current version, React 19 support

### Secondary (MEDIUM confidence)
- Sentry React docs (docs.sentry.io) — Error Boundary integration patterns, React 19 error hooks
- Paulund blog (paulund.co.uk, 2026-04-08) — Production Error Boundary implementation patterns
- OneUptime blog (oneuptime.com, 2026-02-20) — Monitored Error Boundary with logging
- CodeFixesHub (codefixeshub.com, 2025-08-14) — Error Boundary patterns and pitfalls
- Toolstac (toolstac.com, 2025-08-28) — Production debugging with Error Boundaries

### Tertiary (LOW confidence)
- Epic React by Kent C. Dodds (epicreact.dev, 2025-05-27) — Error Boundary limitations explanation
- LogRocket Blog (blog.logrocket.com, 2024-07-03) — react-error-boundary library usage

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — All versions verified from package.json and npm ls
- Architecture: HIGH — Patterns verified from React official docs (Context7) and existing codebase
- Pitfalls: HIGH — Verified from React official docs, Sentry docs, and multiple 2025/2026 sources
- Backend endpoint: MEDIUM — Pattern follows existing route conventions but new file creation not verified against all backend patterns
- MUI icon imports: HIGH — Verified from existing codebase usage and MUI v9 docs

**Research date:** 2026-05-20
**Valid until:** 2026-06-20 (30 days — stable domain, no major React/MUI releases expected)
