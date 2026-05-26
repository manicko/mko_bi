# Problem 2: Root Path (http://localhost:8000/) Shows "Something went wrong" Error Page

## Severity
High

## Labels
[BEST-PRACTICE]

## Summary
When accessing `http://localhost:8000/` (backend directly), the server returns HTTP 200 and serves the React SPA `index.html`, but the React app immediately hits a runtime error that triggers the ErrorBoundary, displaying "Something went wrong / An unexpected error occurred."

## Evidence
- `curl http://localhost:8000/` returns HTTP 200 with valid `index.html` containing `<script type="module" crossorigin src="/assets/index-DW1oWDTg.js">`
- User report: Page shows "Something went wrong / An unexpected error occurred."
- This means the React app mounts, starts executing, and one of its components throws during the initial render — hitting the `ErrorBoundary`.

## Root Cause Analysis

The SPA is served correctly from the backend's `frontend/dist`. The issue is that **the app is running in dev mode via Vite (port 5173), not via the backend-served static files (port 8000)**. When a user accesses port 8000, the React bundle from the Docker `frontend/dist` is loaded. This is a **production build** that expects:
1. Cookie-based auth with `secure` cookies (HTTPS only)
2. Access Token stored in memory only (`USE_MEMORY_STORAGE = true` in production builds — see `frontend/src/features/auth/model/authToken.ts` line 25)

The production build has `cookie_secure=True` by default. Over plain HTTP (localhost), the browser **refuses to set the `secure` cookie**, so login silently fails — the refresh token cookie never gets set.

When the `useAuth` hook runs:
1. No token in memory (production mode, memory-only storage)
2. Silent refresh fails (no cookie, or cookie is rejected by browser over HTTP)
3. `isLoading` becomes `false`, `user` is `null`
4. `ProtectedRoute` redirects to `/login`
5. The login page should render fine, but if there's **another component** (like `AppLayout` or `Header`) that renders before the redirect and tries to call an API, the axios interceptor hits a 401, attempts refresh (fails), and the error propagates to ErrorBoundary.

The error page text confirms this: in production mode, the `ErrorPage` variant "500" shows "An unexpected error occurred. Please try again later." (without debug details), which is exactly what the user sees.

## Impact
- **Direct access to port 8000 is broken in dev mode** — users see the error page instead of the login page
- In production (HTTPS), this would work correctly because `secure` cookies are accepted
- Confusing for developers who expect the backend to serve the SPA in dev mode

## Affected Modules
- `frontend/src/features/auth/model/useAuth.ts` — silent refresh fails over HTTP
- `frontend/src/features/auth/model/authToken.ts` — `USE_MEMORY_STORAGE = true` in prod builds
- `src/mkobi/core/security.py` — `set_secure_cookie` uses `cookie_secure=True` by default
- `src/mkobi/config.py` — `AppSettings.cookie_secure=True` (default)
- `frontend/src/shared/components/ErrorBoundary.tsx` — catches the error

## Suggested Direction
Several options (pick one):

**Option A (Recommended for dev mode):** Add `APP__COOKIE_SECURE=false` environment variable to `docker-compose.override.yml` so that the cookie's `secure` flag is disabled during development over HTTP. This matches the dev environment setup.

**Option B:** Document that port 8000 in dev mode is **not** the intended entry point. The intended flow is: frontend at port 5173 → proxies `/api` to backend at 8000. Accessing 8000 directly should show an informational message, not the SPA.

**Option C:** Add logic to `useAuth.ts` to catch the initial error more gracefully, e.g., if the refresh fails and the user has no token, set `isLoading = false` and `user = null` without letting the error propagate to the ErrorBoundary. Add an error state check before the `getProfile` call.

Effort: Small (Option A is trivial, ~1 line in docker-compose.override.yml)

Priority: Recommended — this directly affects developer experience and understanding of the system
