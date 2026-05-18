# Phase 1: Frontend — BI Dashboard System (React + Plotly)

**Gathered:** 2026-05-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Building a React SPA frontend for a BI dashboard system. Covers: authentication (login/register), dashboard list and view pages with Plotly charts, CSV data upload, user profile management, and admin panel (user management, dashboard management, registration requests, log viewing). All with role-based access control (admin/user global roles, viewer/editor dashboard roles).

Dashboard page layout (chart arrangement, filters panel) is described separately in a later phase.

</domain>

<decisions>
## Implementation Decisions

### Table inline editing

- On server error (network failure, validation error): revert cell to previous value + show error toast
- During save (request in flight): highlight the row with yellow background to indicate "saving..." state
- Dropdown inline edits (user role, status): close immediately after selection, save triggers right away
- Rapid successive edits across rows: each row saves independently in parallel, each with own highlight state — no blocking, no queue
- No page reload on save — only the changed row updates

### Upload flow

- Upload opens as a modal on the dashboard page (not a separate page)
- SPEC.md will be adjusted to match this priority

### Dashboard list presentation

- Table format with ID + Name columns (per CONTEXT_01.md)
- SPEC.md will be adjusted to match this priority

### Toast notifications

- Position: top-right
- Auto-dismiss with short duration (~3 seconds for success, ~5 seconds for errors)
- Multiple toasts stack vertically
- Manual dismiss allowed (close button)

### Access denied UX

- Display message: "No access — contact your administrator"
- No additional actions (no request access button, no redirect)

### Dashboard page layout

- Deferred — will be described in a separate phase

</decisions>

<specifics>
## Specific Ideas

- SaaS admin panel style — modern, minimal, light theme
- Tables: light with row separators, hover highlight, rounded buttons
- Icons only for key actions: add, delete, upload
- Active menu item highlighted in top navigation
- Top nav order (right to left): Profile, Dashboards, Admin (admin only)
- Tables support: pagination (25 rows default), sorting, inline editing, loader spinner inside table
- Empty tables: show header + "No data" text
- Short UUID format for all IDs
- Confirm dialogs: background dimmer, short text, Cancel + Delete buttons; Delete button blocked during request
- Esc closes modals, Enter confirms forms
- Table state (pagination page, sorting) preserved on back navigation

</specifics>

<deferred>
## Deferred Ideas

- Dashboard page layout (chart grid arrangement, filters panel placement) — separate phase
- Registration request flow (user self-registration with admin approval) — mentioned in SPEC.md but not detailed in CONTEXT_01.md, may need clarification
- Log viewer in admin panel — mentioned briefly, details TBD

</deferred>

---

_Phase: 01-frontend-spa_
_Context gathered: 2026-05-18_
