# Phase 4: Registration Request Issues - Context

**Gathered:** 2026-05-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix 3 identified issues with the user registration request flow:
1. No loading/feedback during form submission (user thinks nothing is happening for 2-3 seconds)
2. Form doesn't submit on Enter key
3. After successful submission, admin's registration requests table doesn't show the new request

These are bug fixes to existing functionality. New registration features (email notifications, approval workflow) are separate phases.
</domain>

<decisions>
## Implementation Decisions

### Loading state & feedback during submission

- **Loading indicator:** Disabled button with spinner inside the button — submit button shows `CircularProgress` and text changes to "Sending..." during the request. Simplest and most native React/MUI pattern.
- **Timing:** Show loading state immediately on submit click (optimistic feedback)
- **Form fields:** No need to disable fields — the form redirects to another page after submission, so the page transition handles it naturally

### Form submission mechanics

- **Enter key fix:** Wrap inputs in a `<form>` element with `onSubmit` handler, make the button `type="submit"`. This is the standard HTML/React pattern — Enter key works automatically, no manual keydown listeners needed.
- **Double-submit prevention:** Yes — button is disabled immediately on click, preventing duplicate requests
- **Validation alignment:** Researcher should investigate existing frontend Zod validation and align it with backend validation rules. Ensure both sides enforce the same constraints (email format, field requirements, etc.)

### Admin panel data sync

- **Root cause:** Investigate both the backend save logic AND the frontend data refresh — both could be contributing. The registration request may not be persisted correctly, or the admin page may not refetch data after a new request is created.
- **Refresh strategy:** Auto-refresh on tab switch — when admin navigates to the "Registration Requests" tab, refetch the list using TanStack Query (`invalidateQueries` or `refetchOnMount`). This is the standard pattern already used in the codebase.
- **No notification badge** — keep it simple, admin checks the table manually
- **Empty state:** When zero requests, show a simple "No pending registration requests" message using MUI `DataGrid` `slots.noRowsOverlay` — standard pattern, minimal code

### Post-submission UX

- **Success flow:** Already implemented — redirects to a confirmation page with a success message. No changes needed.
- **Error flow:** Already implemented — redirects to a separate page that displays the error message (e.g., "email already exists"). Keep this existing pattern.

</decisions>

<specifics>
## Specific Ideas

- The 2-3 second delay with no feedback is the core UX issue — adding an immediate loading state on the submit button will make the system feel responsive even if the backend is slow
- The Enter key issue is likely because the form inputs are not wrapped in a `<form>` element or the button is not `type="submit"` — a common oversight
- The admin table not updating could be a TanStack Query caching issue (stale data) or a backend issue (data not being saved) — needs investigation during implementation
- The existing redirect-after-submit pattern is fine and should be kept — it cleanly separates the form from the result

</specifics>

<deferred>
## Deferred Ideas

- Email notification to admin when a new registration request is submitted — separate phase
- Email notification to user when their registration is approved/rejected — separate phase
- Registration request approval/reject workflow in admin panel — separate phase (if not already implemented)
- Rate limiting on registration requests to prevent spam — separate phase

</deferred>

---
_Phase: 04-registration-request-fixes_
_Context gathered: 2026-05-20_
