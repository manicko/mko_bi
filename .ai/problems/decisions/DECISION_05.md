# Phase 5: Frontend Error Handling - Context

**Gathered:** 2026-05-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement comprehensive frontend error handling for the mkobi BI Dashboard. Cover: wrong pages (404), access errors (403), auth errors (401), server errors (500), unexpected JS crashes, and network failures. Show user-friendly MUI-styled error pages instead of blank screens or raw errors.

This phase completes and systematizes error handling. New capabilities (error analytics dashboard, external monitoring integration) are separate phases.
</domain>

<decisions>
## Implementation Decisions

### Error page design (MUI standard)

- **Style:** Standard MUI-styled page — Warning icon (amber triangle) + message + button
- **Icon:** `WarningAmber` from MUI icons, amber color — softer, less alarming
- **Layout:** Centered on page, using MUI `Box`/`Container`/`Typography` components
- **Primary button:** MUI `Button` with `variant="contained"`, text "Go to Home"
- **"Go to Home" behavior:** Navigates to `/dashboards` if authenticated, `/login` if not
- **No secondary actions** — keep it simple, single button
- **Rewrite existing `NotFound.tsx`** from Tailwind CSS to MUI to match this standard

### Error type differentiation

Two distinct error page variants:

**404 (Not Found):**
- Message: "Page not found" + "The page you are looking for does not exist."
- Button: "Go to Home"
- Trigger: unknown routes (existing `*` route in `routes.tsx`)

**500 (Server Error / Unexpected Crash):**
- Message (dev): actual error name + message for debugging
- Message (production): "Something went wrong" + "An unexpected error occurred."
- Button: "Reload page" (primary) + "Go to Home" (secondary link)
- Trigger: React Error Boundary catches JS crashes

### Navigation after error

- **401 (unauthenticated):** Auto-redirect to `/login` immediately — no error page shown. Already implemented in `axiosInstance` interceptor and `ProtectedRoute`. Keep existing behavior.
- **403 (forbidden):** Toast notification "Access denied" via `react-hot-toast` + user stays on current page. No redirect, no error page.
- **500 / network errors during API calls:** Inline error state within the affected component with a "Retry" button (TanStack Query `refetch`). No full-page redirect.
- **Wrong URL in address bar:** Show 404 error page with message + "Go to Home" button
- **No auto-redirect on error pages** — user must explicitly click the button (except 401 which auto-redirects)

### Error boundary scope

- **Two-tier Error Boundary:**
  1. **Route-level** — boundary around each route section in `routes.tsx` so one crash doesn't take down the whole app
  2. **App-level** — top-level boundary wrapping the entire app as ultimate safety net
- **Error content:** Show error name/message in development (`process.env.NODE_ENV === 'development'`), generic "Something went wrong" in production
- **Error logging:** `console.error` in development. In production, POST to a new backend endpoint (`POST /api/v1/client-errors`) with error details (message, component stack) for monitoring
- **"Reload page" button** as primary action (attempts recovery), "Go to Home" as secondary link

### Existing code to update

- `NotFound.tsx` — rewrite from Tailwind to MUI, match new standard
- `routes.tsx` — add Error Boundary wrappers around route groups
- `providers.tsx` — add top-level Error Boundary
- `axiosInstance.ts` — keep existing 401 interceptor, add 403 toast handling
- New files: `ErrorPage.tsx` (shared component), `ErrorBoundary.tsx` (shared component)

</decisions>

<specifics>
## Specific Ideas

- The user explicitly said: "I prefer showing a nice message with a button to go to login, not auto-redirect" — but for 401, auto-redirect is the correct practice and was agreed upon
- The existing `NotFound.tsx` uses Tailwind CSS (`flex`, `text-gray-800`, etc.) — must be rewritten to MUI for consistency
- The existing axios interceptor already handles 401 correctly (remove token → toast → redirect to `/login`)
- No Error Boundary exists currently — this is a new addition
- The "Go to Home" button should be smart: check auth state, go to dashboards or login accordingly
- For 403 during API calls, use existing `react-hot-toast` pattern (already used throughout the codebase)

</specifics>

<deferred>
## Deferred Ideas

- External error monitoring service integration (Sentry, LogRocket) — separate phase
- Error analytics dashboard in admin panel — separate phase
- "Contact support" / "Report issue" link on error pages — can be added later
- Automatic error recovery / retry for transient network errors — future enhancement
- Rate limiting error page (429) — not currently needed

</deferred>

---

_Phase: 05-frontend-error-handling_
_Context gathered: 2026-05-20_
