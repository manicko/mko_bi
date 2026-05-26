# Problem 3: No Redirect from /login on Port 5173 (Frontend Dev Server)

## Severity
High

## Labels
[BUG]

## Summary
When accessing `http://localhost:5173/` (Vite dev server), the page should redirect to `/login` for unauthenticated users, but it does not. The user stays on the root path and sees the error page or a blank state.

## Evidence
- `docker-compose.override.yml`: Frontend runs Vite dev server on port 5173 with hot reload
- User report: `http://localhost:5173/` — no redirect to login page despite documentation stating it should happen
- `frontend/src/app/routes.tsx` line 64: `<Route path="/" element={<Navigate to="/dashboards" replace />} />` — the root path redirects to `/dashboards`, NOT to `/login`
- `DashboardList` is wrapped in `ProtectedRoute`, which checks for `accessToken` and `isLoading`

## Root Cause Analysis

The route structure has a redirect chain issue:

1. User visits `http://localhost:5173/`
2. The root route `<Navigate to="/dashboards" replace />` fires immediately
3. This redirects to `/dashboards`
4. `/dashboards` is wrapped in `<ProtectedRoute>` which checks `accessToken` and `isLoading`

The `ProtectedRoute` component (`ProtectedRoute.tsx`) logic:
```typescript
if (isLoading) { return <CircularProgress /> }  // Show loading spinner
if (!accessToken) { return <Navigate to="/login" ... /> }  // Redirect to login
return <>{children}</>
```

The `useAuth` hook on mount (when no token in sessionStorage in dev mode):
1. Token is `null` (fetched via `getToken()`)
2. Attempts silent refresh via `apiRefreshToken()` 
3. The refresh call goes to `http://localhost:5173/api/v1/auth/refresh` → Vite proxy → `http://app:8000/api/v1/auth/refresh`
4. The refresh fails (HTTP 401: "No refresh token in cookies") because user has never logged in before
5. `catch` block runs: `removeToken()`, `setUser(null)`, `setIsLoading(false)`
6. Now `ProtectedRoute` sees `isLoading=false` and `accessToken=null` → should redirect to `/login`

BUT — there's a timing issue. During the `useEffect` in `useAuth`, the `isLoading` state starts as `true`. The `ProtectedRoute` sees `isLoading=true` and renders `<CircularProgress />`. While this happens:

- The axios interceptor in `axiosInstance.ts` intercepts the 401 from the refresh call
- Since `isRefreshing` logic is engaged, but the refresh ITSELF returned 401, the catch block in the interceptor runs: `removeToken()`, `toast.error('Session expired...')`, `window.location.href = '/login'`

The `window.location.href = '/login'` redirect should work. But if there's a JavaScript error during this flow (e.g., the `ErrorBoundary` catching a render error from a component mounted by React Router before the redirect completes), the user sees the error page instead.

Additionally, the `/` route redirects to `/dashboards` via `<Navigate>`. While the `ErrorBoundary` wraps this at the `AppLayout` level:
```tsx
<Route element={<AppLayout />}>
  <Route element={<ErrorBoundary />}>
    ...protected routes...
    <Route path="/" element={<Navigate to="/dashboards" replace />} />
  </Route>
```

The `AppLayout` renders `Header` which uses `useAuth()`. If the auth state is in a transitional state during the initial load, and any component tries to render with an unexpected state, it throws.

## Impact
- Users accessing `http://localhost:5173/` do not see the login page
- Instead they see either the ErrorBoundary's "Something went wrong" page or an infinite loading spinner
- **This completely blocks the login flow in dev mode**

## Affected Modules
- `frontend/src/app/routes.tsx` — root path redirects to /dashboards instead of /login
- `frontend/src/shared/components/ProtectedRoute.tsx` — loading state handling
- `frontend/src/shared/api/axiosInstance.ts` — 401 interceptor with `window.location.href` redirect
- `frontend/src/features/auth/model/useAuth.ts` — silent refresh logic

## Suggested Direction

**Immediate fix:** Change the root route in `routes.tsx` to redirect to `/login` instead of `/dashboards`:
```tsx
<Route path="/" element={<Navigate to="/login" replace />} />
```
This is cleaner UX — unauthenticated users land on the login page directly. Authenticated users who manually navigate to `/` will need to go through ProtectedRoute anyway, but typically they'd bookmark `/dashboards`.

**Secondary fix:** In `ProtectedRoute.tsx`, ensure that the loading spinner is shown consistently during the entire auth initialization, and that no child components attempt to render or make API calls until `isLoading` is definitively `false` and `accessToken` is either set or confirmed absent.

Effort: Trivial (1 line change for the immediate fix)

Priority: High — blocks the primary user flow in development
