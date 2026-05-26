# mkobi BI Dashboard — Runtime Problem Audit

**Date:** 2026-05-26
**Environment:** Docker dev mode (`docker-compose.override.yml`)
**Ports:** Frontend Vite dev server `5173`, Backend API `8000`

## Summary

| # | Problem | Severity | Labels | Effort |
|---|---------|----------|--------|--------|
| 01 | Client Errors API route not mounted | Medium | [SPEC-DEVIATION] | Trivial |
| 02 | Root path (`:8000/`) shows "Something went wrong" | High | [BEST-PRACTICE] | Small |
| 03 | No redirect to login on port 5173 | High | [BUG] | Trivial |
| 04 | `/dashboards` infinite loading spinner | High | [BUG] | Small |
| 05 | Cookie `secure` flag blocks auth over HTTP | Medium | [BEST-PRACTICE] | Trivial |

## Key Findings

### Critical Path: Auth Flow is Broken in Dev Mode

Problems **02**, **03**, **04**, and **05** are interconnected and all stem from the same root causes:

1. **Cookie `secure` flag** (Problem 05): In dev mode over HTTP, the browser refuses to set the refresh token cookie because `cookie_secure=True` by default. The `docker-compose.override.yml` does not override this.

2. **Root route redirects to protected path** (Problem 03): The `/` route uses `<Navigate to="/dashboards" />` instead of redirecting to `/login`. This sends unauthenticated users through `ProtectedRoute` → `DashboardList` → premature API calls → 401 interceptor → potential ErrorBoundary catch.

3. **Race condition in auth + data fetching** (Problem 04): `ProtectedRoute` renders children while `isLoading=true`, allowing TanStack Query to fire unauthenticated API calls. The axios interceptor then tries `window.location.href = '/login'` which conflicts with React Router's navigation.

4. **Backend SPA serving broken over HTTP** (Problem 02): Port 8000 serves the production React build, which expects `secure` cookies and uses memory-only token storage. Over HTTP, this creates an impossible auth situation.

### Silently Broken: Error Reporting (Problem 01)

The `client_errors` route is defined but never mounted in `app.py`. All frontend error reports are silently lost (HTTP 404 swallowed by `.catch(() => {})`).

## Recommended Fix Order

1. **Problem 05** — Add `APP__COOKIE_SECURE=false` to dev override (trivial, enables auth)
2. **Problem 03** — Change `/` route to redirect to `/login` (trivial, fixes navigation)
3. **Problem 04** — Add `enabled: !!accessToken` to data queries (small, fixes infinite loading)
4. **Problem 01** — Mount `client_errors` router in `app.py` (trivial, restores error reporting)
5. **Problem 02** — Document or fix `:8000` direct access behavior (informational)
