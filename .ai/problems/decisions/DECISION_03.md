# Phase 3: Admin Dashboard Creation - Context

**Gathered:** 2026-05-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement the "Create Dashboard" functionality in the admin panel. Currently the modal exists but creation fails ("Failed to create") — backend endpoint is likely missing. This phase covers: implementing the backend create-dashboard API, wiring the frontend modal, adding validation, error handling, and post-creation flow.

This is a bug fix + completion of existing UI. New dashboard management features (edit, delete, layout editing) are separate phases.
</domain>

<decisions>
## Implementation Decisions

### Form fields & validation

- **Fields:** Name (required) + Description (required) + Layout type (optional dropdown)
- **Layout dropdown options:** "Single column", "Two columns", "Grid"
- **Name validation:** Required, 3-100 chars, alphanumeric + spaces + hyphens only (no special chars)
- **Name uniqueness:** Not enforced — duplicate names allowed, identification is by ID
- **Description:** Optional field, max 200 chars with character counter displayed
- **Frontend validation:** Use Zod schema in the form, matching the same rules

### Error handling & feedback

- **Error display:** Inline inside the modal, below form fields. Modal stays open on error so user can fix and retry.
- **Error detail level:** Informative — show the actual backend error message (e.g., "Database connection failed", "Permission denied") so the user knows what went wrong
- **Form state on error:** Preserve user input. Keep modal open, show error, user corrects and retries
- **Submit button:** Disabled during request, no spinner — keep it simple
- **Success feedback:** No toast. Modal closes + dashboard list refreshes. That's sufficient confirmation.

### Post-creation flow

- **After success:** Close modal, stay on admin page, refetch dashboard list so the new entry appears immediately
- **No navigation** to the newly created dashboard — user stays in admin panel
- **Single create flow** — no "Create and add another". Modal closes on success. User opens again for next.

### Dashboard defaults

- **Default layout:** Empty dashboard — no graphs, no filters. Admin adds them manually after creation
- **Access:** All admins are editors for all dashboards by default (existing system behavior, no changes needed)
- **No owner concept** in the system — only viewer/editor roles exist

</decisions>

<specifics>
## Specific Ideas

- The create dashboard modal already exists in the frontend with Name + Description fields — the main work is implementing the backend API endpoint and wiring it up
- The "Failed to create" message currently shown is a generic fallback — the real issue is likely a missing or broken backend endpoint
- Layout type dropdown is a new optional field — if backend doesn't support layout yet, it can be stored as a default/ignored value for future use
- Character counter for Description should be visible near the field (e.g., "145/200")

</specifics>

<deferred>
## Deferred Ideas

- Dashboard edit/delete functionality — separate phase
- Dashboard layout editor (drag-and-drop graphs) — separate phase
- Granting viewer access to specific users for a new dashboard — separate phase (access management already exists)
- Pre-populated dashboard templates — future enhancement

</deferred>

---
_Phase: 03-admin-dashboard-creation_
_Context gathered: 2026-05-20_
