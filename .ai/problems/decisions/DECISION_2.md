<domain>
## Phase Boundary

Resolve URL normalization for dashboard routes. The application currently inconsistently handles `dashboards`, `dashboards/`, and dashboard subpaths (e.g. `/dashboards/subpath`). The React Router should normalize to the canonical format without optional trailing slash, matching most browsers and conventions.
</domain>

<decisions>
## Implementation Decisions

### React Router behavior

- All dashboard routes must resolve to format: `/dashboards/:id` and `/dashboards/:id/subpath?`
- Navigation/Route must not match optional trailing slash (i.e. `/dashboards/` AND `/dashboards` are allowed, but `/dashboards/` is the preferred form)
- `useParams` must return dashboard IDs without `/dashboards/` normalization
- Redirect should happen only from `/dashboards/` to `/dashboards` after slash removal, no redirect for existence checks

### API access control

- API endpoints (HTTP) use `dashboard_id` from URL, not including any slashes
- React Router route matching must explicitly strip `/dashboards/` from URLs
- All reference to dashboard ID in frontend/backend must use normalized format

### KiloCode's Discretion

- Exact error messages for non-existent dashboards
- Middleware behavior for 404 vs 403 signals
- Redirect implementation style (single vs separate page)
</decisions>

<specifics>
## Specific Ideas

- Should follow React Router conventions (canonical form is `/dashboards/:id`)
- API and database should use normalized format for dashboard IDs
- Dashboard existence check must avoid leaking existence via 404/403
</specifics>

<deferred>
## Deferred Ideas

- Dashboard-specific error handling
- Accessibility contrast for 404/403 states
- Dashboard layout variations
</deferred>

---

_Phase: 2-url-normalization_
_Context gathered: 2026-05-22_
