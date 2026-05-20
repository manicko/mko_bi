# Phase 2: Frontend Bug Fixes - Context

**Gathered:** 2026-05-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix 5 identified frontend bugs in the mkobi BI Dashboard:
1. Remove password length validation from login form
2. Fix login error display (inline instead of redirect)
3. Add Profile to user dropdown menu
4. Fix data display in Profile and Admin pages
5. Change active menu highlight from red to green

These are bug fixes and UX improvements. New capabilities belong in other phases.
</domain>

<decisions>
## Implementation Decisions

### Login Password Validation

- Remove ALL client-side validation from the login form — no length checks, no strength indicators, no format rules beyond email format
- Only check: fields are not empty (prevents sending blank submissions to the server)
- Server-side is the only real validation — does the user exist, does the password match
- The `loginSchema` in `formSchemas.ts` must be updated: remove `password: z.string().min(6, ...)` rule, keep only `z.string().min(1)` or similar non-empty check

### Login Error Display

- Generic error message: "Invalid login or password" (doesn't reveal which field is wrong)
- Display via existing inline `Alert` component (MUI `Alert` with `severity="error"`) — already in the code
- No toast notification, no redirect to a separate page
- Error message clears as soon as the user modifies any field in the form
- The redirect behavior must be investigated and fixed (likely an unhandled promise rejection or axios interceptor issue)

### User Menu Structure (Header Dropdown)

- Two items in the dropdown: Profile + Logout
- Order: Profile on top, Logout below
- Visual separator: MUI `Divider` between the two items
- Profile item uses `Settings` icon (gear icon from MUI icons)
- Logout item keeps the existing `LogoutIcon`
- Remove "Profile" from the top navigation bar `NAV_ITEMS` in `Header.tsx` (it's now in the dropdown only)

### Profile/Admin Data Display

**Profile page (UserProfile.tsx):**
- Read-only display of: Email, Display Name, Role (keep current three fields)
- Keep existing "Change Password" and "Delete Account" buttons
- Root cause of empty data needs investigation during implementation (likely a frontend data-binding issue or backend API response mismatch)

**Admin user table (UserManagement.tsx):**
- Columns: ID, Email, Role, Created (remove Status column)
- Reason: `AdminUser` type expects `is_active` but backend `UserRead` model doesn't include it — type mismatch
- The Status column `valueGetter` references `is_active` which doesn't exist in the API response

### Active Menu Highlight Color

- Replace both text color and border color with `success.light` (from MUI theme)
- Remove red (`secondary.main`) highlighting
- In `Header.tsx`: change `color="secondary"` to `color="success"` and `borderBottomColor: 'secondary.main'` to `borderBottomColor: 'success.light'`
- Note: MUI `Button` with `color="success"` uses `success.main` for text; the border should explicitly use `success.light` via sx prop

</decisions>

<specifics>
## Specific Ideas

- "Password must be more than 6 characters" validation on login is wrong — it was copied from registration. Login should only verify credentials against the database.
- Login error redirect to a separate page is broken UX — should stay on the same page and show the error inline.
- The `Header.tsx` currently has Profile in the top nav bar `NAV_ITEMS` array — it should be removed from there and added to the dropdown menu instead.
- The `loginSchema` currently has `password: z.string().min(6, { error: 'Password must be at least 6 characters' })` — this needs to be relaxed to just a non-empty check.

</specifics>

<deferred>
## Deferred Ideas

- Adding `is_active` field to `UserRead` backend model — this is a new capability (user status tracking), not just a bug fix. Would require backend model change + migration + frontend update.
- Block/Unblock user functionality in admin panel (currently shows "coming soon" toast) — separate phase.
- Editable profile fields — out of scope for this phase.

</deferred>

---

_Phase: 02-frontend-bug-fixes_
_Context gathered: 2026-05-20_
