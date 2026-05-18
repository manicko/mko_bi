# Phase 1: Authorization - Context

**Gathered:** 2026-05-18
**Status:** Ready for planning

<domain>
## Phase Boundary

User authentication and role-based access control: email/password login, JWT session management, two-tier role system (global: admin/user; dashboard-level: viewer/editor), registration request/approval flow, and access enforcement on dashboards.
</domain>

<decisions>
## Implementation Decisions

### Access Control Enforcement

- Admin bypass — admins see and can do everything on all dashboards, no explicit `dashboard_access` row needed
- Regular user (non-admin) with no dashboard access → empty list on `/dashboards` with guidance message (e.g., "No dashboards available. Contact an admin to get access.")
- Editor can fully delete a dashboard (cascading to graphs, data, access entries) — product decision only, no code changes at this time
- Unauthorized dashboard access (direct URL) → 403 "Access denied" (reveals the dashboard exists)

### Registration Request Flow

- After submission → simple confirmation message: "Your request has been submitted. An administrator will review it."
- Duplicate registration requests blocked:
  - If pending or approved → "A request for this email already exists"
  - If previously rejected → "Your request was rejected. Contact an administrator for more information." (no resubmission by user; only admin can change status)
- Rejection: no reason field for admin; if user attempts to register again with a rejected email → "Your request was rejected"
- Blacklisted email domain → explicit form error: "This email domain is not allowed for registration"

### Role Display & User Identity

- Display name derived from email prefix (before @) shown **only on Profile page** as read-only field
- Profile page shows global role only (e.g., "Role: user" or "Role: admin") — dashboard-level roles are NOT shown
- Header: narrow top navigation bar present on all pages except login page; navigation buttons right-to-left; rightmost button is "Profile" (no dropdown)
- Profile page (`/profile`) contains:
  - Email (read-only)
  - Display name — email prefix before @ (read-only)
  - Global role (read-only)
  - "Change Password" button → `/profile/change-password`
  - "Delete Account" button (non-admin users only)
  - Link to "My Dashboards" (`/dashboards`)

</decisions>

<specifics>
## Specific Ideas

- No separate "Name" field — email prefix serves as the display name throughout the system
- Dashboard-level delete permission for editors is a product-level decision, not to be implemented in code at this time
- Registration flow is request-based: no self-registration, all accounts require admin approval

</specifics>

<deferred>
## Deferred Ideas

- Email notifications for registration approval/rejection — not in scope for this phase
- Soft delete for dashboards — deferred, may be revisited
- Rejection reason field for admin — deferred, may be added later
- Dashboard-level role display on profile page — deferred to a future phase

</deferred>

---

_Phase: 01-authorization_
_Context gathered: 2026-05-18_
