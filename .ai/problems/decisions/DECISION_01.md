# Phase 1: Auth Token Management - Context

**Gathered:** 2026-05-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement secure authentication token management using in-memory access tokens and httpOnly secure cookie refresh tokens. Users stay logged in across page refreshes without exposing tokens to XSS. Scope: backend token creation/refresh endpoints, frontend silent refresh on initialization, logout cookie clearing.

</domain>

<decisions>
## Implementation Decisions

### Token lifetimes

- Access token: **15 minutes** (short-lived, standard OAuth2 practice for SPAs)
- Refresh token: **7 days** stored in httpOnly cookie (balances security and UX — user stays logged in for a week)
- Rationale: Short access token limits damage window if leaked; 7-day refresh avoids annoying re-logins while still requiring periodic re-auth

### Refresh strategy

- **Silent refresh on app initialization** — when no access token exists in memory but a refresh cookie is present, call `/auth/refresh` transparently
- **No proactive pre-expiry refresh** — only refresh on page load/navigation when access token is missing; keeps logic simple
- **Concurrent request handling** — if multiple API calls fail with 401 simultaneously, queue pending requests and perform a single refresh, then retry all queued requests (standard TanStack Query `onError` retry pattern)
- On 401 from any API call → attempt one refresh → retry original request; if refresh also fails → redirect to login

### Logout & token invalidation

- **Logout clears the httpOnly cookie** (set `max_age=0`) and clears in-memory access token
- **No server-side token blacklist** for this phase — stateless JWT approach is sufficient for the current scale; refresh token rotation is not required yet
- "Logout all devices" is **out of scope** — deferred to a future phase if needed

### Error handling on refresh failure

- **Expired/invalid refresh cookie** → silent redirect to `/login` (no disruptive toast/alert — user simply sees the login page)
- **Network error during refresh** → retry once after 1 second, then redirect to login if still failing
- **No "session expired" toast** — clean redirect avoids confusing users with messages they can't act on
- After successful login post-redirect, user lands on their intended destination (store `location.state.from` in React Router)

### KiloCode's Discretion

- Exact cookie `path` attribute (root `/` is fine)
- Whether to use `zustand`, `context`, or a simple module-level variable for in-memory access token storage
- Exact Axios interceptor vs TanStack Query `onError` implementation for 401 handling
- Refresh token rotation (issuing a new refresh token on each refresh call) — optional enhancement, not required for this phase

</decisions>

<specifics>
## Specific Ideas

- Standard secure cookie attributes: `httponly=True`, `secure=True`, `samesite="strict"`
- Login endpoint returns `TokenWithUser` (token + user profile) to avoid a separate `/me` call — consistent with existing SPEC.md design decision
- Frontend `authToken.ts` module handles in-memory storage and provides `getAccessToken()` / `setAccessToken()` / `clearAccessToken()` helpers
- `authApi.ts` exposes `refreshToken()` function that calls `POST /auth/refresh` with `credentials: 'include'` to send the cookie

</specifics>

<deferred>
## Deferred Ideas

- Refresh token rotation (new refresh token on each use) — future enhancement
- "Logout all devices" / session management — future phase
- Server-side token blacklist/revocation store — future phase if security requirements change
- Remember-me / extended refresh token (30 days) — future phase
- CSRF token for cookie-based auth — evaluate if `samesite="strict"` is sufficient

</deferred>

---

_Phase: 01-auth-token-management_
_Context gathered: 2026-05-22_
