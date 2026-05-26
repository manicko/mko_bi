# Problem 4: /dashboards Page Shows Infinite Loading Spinner

## Severity
High

## Labels
[BUG]

## Summary
When accessing `http://localhost:5173/dashboards`, the page shows a permanent loading spinner (CircularProgress) and never renders the dashboard list or redirects to login.

## Evidence
- User report: `http://localhost:5173/dashboards` — "постоянная загрузка - ничего не отображается, просто крутится загрузка" (permanent loading, nothing displays, just a spinner)
- `DashboardList.tsx` line 12: `const { data: dashboards, isLoading, error } = useMyDashboards()`
- `DashboardList.tsx` lines 14-19: When `isLoading` is true, renders `<CircularProgress />`

## Root Cause Analysis

The `useMyDashboards` hook uses TanStack Query's `useQuery` with `queryFn: () => dashboardApi.getMyDashboards()`, which calls `axiosInstance.get('/dashboards/my')`.

The flow when user is not authenticated:

1. `useAuth` hook mounts, no token in sessionStorage (dev mode)
2. `useAuth` attempts silent refresh → fails with 401
3. `useAuth` sets `isLoading = false`, `user = null`
4. `ProtectedRoute` sees `isLoading = false` and `accessToken = null` → should redirect to `/login`

BUT — there's a race condition. The `useQuery` in `DashboardList` fires immediately when the component mounts, BEFORE `ProtectedRoute` has a chance to redirect. The sequence:

1. `ProtectedRoute` renders `<DashboardList />` because `isLoading` is still `true` (auth hasn't finished yet)
2. `DashboardList` calls `useMyDashboards()` → fires `axiosInstance.get('/dashboards/my')`
3. The request has no valid token → returns 401
4. The axios interceptor catches the 401, attempts refresh → fails → `window.location.href = '/login'`
5. BUT `window.location.href` is an async navigation — it doesn't stop JavaScript execution immediately
6. TanStack Query's `retry: 1` (set in `providers.tsx` line 12) kicks in — it retries the failed request
7. The retry also fails with 401, triggering the interceptor again
8. Meanwhile, `useAuth` finishes its own refresh attempt, sets `isLoading = false`
9. `ProtectedRoute` re-renders, sees no token, tries to `<Navigate to="/login" />`
10. But `window.location.href = '/login'` from the interceptor may conflict with React Router's `<Navigate>`

The result: the user sees the `<CircularProgress />` from `DashboardList` because:
- TanStack Query is in a retry loop (the `isLoading` state from `useQuery` stays `true` during retries)
- The `window.location.href` redirect from the axios interceptor may not execute if the interceptor's catch block is reached but the navigation is somehow blocked by React's rendering cycle
- OR: the page does navigate to `/login` but then the same cycle repeats (refresh fails → interceptor fires → redirect → ...)

Additionally, the `useQuery` in `DashboardList` has no `enabled` condition — it fires immediately regardless of auth state. This is a design issue: protected data queries should only fire when the user is authenticated.

## Impact
- Users cannot reach the dashboard list page
- Users cannot reach the login page (if the redirect chain is broken)
- **Complete blocker for the main application flow**

## Affected Modules
- `frontend/src/features/dashboards/api/dashboardApi.ts` — `useMyDashboards` has no `enabled` guard
- `frontend/src/shared/components/ProtectedRoute.tsx` — renders children while `isLoading=true`, allowing queries to fire
- `frontend/src/shared/api/axiosInstance.ts` — 401 interceptor with `window.location.href` redirect
- `frontend/src/features/auth/model/useAuth.ts` — silent refresh race condition
- `frontend/src/app/providers.tsx` — `retry: 1` causes additional failed requests

## Suggested Direction

**Fix 1 (Immediate):** Add `enabled: !!accessToken` to the `useMyDashboards` query so it only fires when the user is authenticated:
```typescript
export function useMyDashboards() {
  const { accessToken } = useAuth()
  return useQuery({
    queryKey: ['dashboards', 'my'],
    queryFn: () => dashboardApi.getMyDashboards(),
    enabled: !!accessToken,
  })
}
```

**Fix 2 (Architectural):** Modify `ProtectedRoute` to NOT render children while `isLoading` is true. Currently it renders children during loading, which allows data queries to fire prematurely:
```typescript
if (isLoading) {
  return <LoadingSpinner />  // Don't render children
}
if (!accessToken) {
  return <Navigate to="/login" ... />
}
return <>{children}</>
```

**Fix 3 (Defensive):** Reduce `retry` to `0` for auth-dependent queries, or configure the axios interceptor to NOT use `window.location.href` (which is unreliable in SPA context) and instead use React Router's `navigate()` for programmatic navigation.

Effort: Small (1-3 lines per fix)

Priority: High — this is the primary user-facing blocker
