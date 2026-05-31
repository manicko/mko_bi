# Phase 1: Admin User Password Reset - Context

**Gathered:** 2026-05-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Allow administrators to reset user passwords from the admin panel User Management table. A temporary password is generated server-side, saved to the DB, and displayed to the admin for out-of-band communication to the user. The user is forced to change the password on first login. This feature solves the problem where users approved by admin have no password and cannot log in.
</domain>

<decisions>
## Implementation Decisions

### Password generation

- 8 characters, letters + digits only (e.g., `aB3xK9mP`)
- The generation pattern must pass the same Pydantic validation as regular password changes
- Up to 3 generation attempts on backend failure, then HTTP 500 with a clear message
- Rationale: one-time use temp password, must pass existing validation, admin communicates it out-of-band

### Confirmation dialog behavior (two-screen flow)

**Screen 1 — Confirmation:**
- Standard ConfirmDialog component (existing pattern)
- Buttons: "Confirm" / "Cancel"
- On "Confirm": POST API call, buttons disabled, spinner displayed
- On "Cancel": dialog closes, nothing happens

**Screen 2 — Password display:**
- Shows the `temp_password` from the API response
- "Copy" button — copies to clipboard via `navigator.clipboard`, toast "Copied"
- "Close" button — closes the dialog
- Both buttons remain visible simultaneously

### Force password change flow

- Backend sets `force_password_change=true` flag on the user record during reset
- After login, the auth response includes `must_change_password: true`
- Frontend redirects to `/profile/change-password` with a force mode
- `ChangePasswordPage` in force mode: "Cancel" is disabled/disabled, user sees a message that password change is required
- Standard flow: old (temp) password + new password + confirmation

### KiloCode's Discretion

- API endpoint URL design (within `/api/v1/admin/users/{id}` scope)
- Response format for the reset-password endpoint (must include `temp_password`)
- HTTP status codes for success and error cases (follow existing project patterns)
- Error handling specifics (404 for missing user, behavior for unapproved users, admin-self-reset policy)
- Whether to expose reset by email in addition to user_id
- Rate limiting on repeated resets for the same user
- Audit logging approach (follow existing logging patterns)
- DB schema for `force_password_change` flag (new column vs. existing mechanism)

</decisions>

<specifics>
## Specific Ideas

- No email delivery of the temp password — admin communicates it out-of-band (consistent with existing registration approval flow)
- Copy-to-clipboard UX for the temp password on Screen 2
- Reuse existing `ChangePasswordPage` component in force mode (no duplicate form logic)
- One single `POST` endpoint: atomic generate + hash + save (no separate generate endpoint)

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---
_Phase: 01-admin-password-reset_
_Context gathered: 2026-05-31_
