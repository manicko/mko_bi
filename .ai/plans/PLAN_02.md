# PLAN_02: PlaceholderPage Component Usage Research and Recommendations

## Research Summary

### Current State
- **File:** `frontend/src/shared/components/PlaceholderPage.tsx`
- **Status:** Exists but never imported or rendered anywhere in the codebase
- **Barrel Export:** Not exported from `frontend/src/shared/components/index.ts`
- **Git Origin:** Created in commit 406c777 ("frontend 12-17") as part of frontend foundation scaffolding

### Investigation Findings

#### 1. Intended Purpose
The PlaceholderPage component is a simple stub component that renders:
- A title (via `title` prop)
- Static text "This page will be implemented in a future task."

This follows a common pattern for:
- Stub pages during feature development
- Placeholder routes for planned features
- Consistent "coming soon" UI across the application

#### 2. Current "Coming Soon" Patterns in Codebase

| Location | Pattern | Implementation |
|----------|---------|----------------|
| `DashboardManagement.tsx` | Inline action placeholder | Disabled button with tooltip: `label="Access (coming soon)"`, `disabled`, `tooltip="Access management is not yet implemented"` |
| `LogViewer.tsx` | Unimplemented filter | TODO comment: `{/* TODO: Load dashboards for filter */}` (interactive dropdown remains) |

#### 3. Existing Similar Components

The codebase already has appropriate components for different placeholder scenarios:
- `AccessDenied` - For permission-related access denials
- `NotFound` - For missing routes (404)
- `ErrorPage` - For error states
- `ErrorBoundary` - For component-level errors

### Recommendation: **Keep with Documentation**

**Decision:** Keep the PlaceholderPage component with JSDoc documentation. It provides a standardized pattern for future use.

**Rationale:**
1. The component serves a valid purpose (route-level stub pages)
2. No similar lightweight option exists for full-page placeholders
3. Current inline patterns (disabled + tooltip) are correct for in-page elements, but route-level stubs need a different solution
4. Adding proper documentation will guide future developers on when to use it

### Usage Guidelines

Use PlaceholderPage when:
- A route exists in navigation but the page is not yet implemented
- Developing a new feature and need a stub during development
- Creating a roadmap milestone where routes are defined before implementation

Do NOT use when:
- An action within an existing page is not implemented (use disabled button + tooltip instead)
- A 404 should be shown (use `NotFound` component)
- Permission denial (use `AccessDenied` component)

### Recommended Enhancements

| Enhancement | Priority | Description |
|-------------|----------|-------------|
| Add optional `description` prop | Low | Allow custom description text for more context |
| Add icon prop | Low | Allow customization of the placeholder icon |
| Add estimated date prop | Low | Show "Expected: Q3 2026" for roadmap transparency |
| Export from barrel | Done | Add to `shared/components/index.ts` |

### Routes That Could Benefit (Future)

Currently, all routes in `routes.tsx` have implementations. Future features that may need placeholders:
- `/admin/logs` - Already implemented
- `/audit` - If audit trail feature is added (mentioned in spec)
- `/settings` - If user settings expand beyond profile/change-password

### Implementation Changes

1. Add JSDoc to `PlaceholderPage.tsx` documenting intended usage
2. Export `PlaceholderPage` from `shared/components/index.ts` for discoverability

---

## AccessDenied Component Research (FE-007)

### Current State
- **File:** `frontend/src/shared/components/AccessDenied.tsx`
- **Status:** Exported from barrel but never rendered anywhere (only exported)
- **Git Origin:** Created in commit 3c474dc ("tasks 1905-1") alongside PlaceholderPage

### Investigation Findings

#### 1. Component Analysis
The AccessDenied component renders a centered message: "No access — contact your administrator"
- Uses MUI Box and Typography
- Centered layout with `minHeight: '50vh'`
- Simple, clean design appropriate for permission denial states

#### 2. RoleBasedAccess Integration
**Current State:** `RoleBasedAccess` renders `null` as default fallback (lines 9, 12-13 in RoleBasedAccess.tsx)
- `/admin` route uses RoleBasedAccess without explicit fallback - shows blank page when non-admin accesses it
- This is a poor UX - unauthorized users see empty content instead of clear denial message

**Integration Applied:** Changed default fallback to `<AccessDenied />` for better UX

#### 3. Backend Error Handling
Backend uses two error codes for access denial:
- `PERMISSION_DENIED` - Used in 18 locations across routes (users, upload, layouts, graphs, admin, deps)
- `ACCESS_DENIED` - Used in 6 locations (data routes, dashboards_crud)

Both map to HTTP 403 Forbidden. API responses trigger toast notifications via axiosInstance.ts, but no dedicated page.

#### 4. Dashboard Access Control
DashboardView currently checks `dashboard.permission` for UI-level permissions (edit button visibility only)
- No role-based access at route level
- Dashboard data endpoint (`/data/aggregated`) returns 403 with ACCESS_DENIED when unauthorized

### Recommendation: **Integrate into RoleBasedAccess**

**Decision:** Set AccessDenied as the default fallback for RoleBasedAccess.

**Rationale:**
1. Provides clear feedback when users lack required roles
2. Better UX than rendering nothing (current behavior)
3. Follows the component's intended purpose
4. Consistent with existing error handling patterns (NotFound for 404)

### Usage Guidelines

Use AccessDenied when:
- RoleBasedAccess fallback for role-based authorization failures
- Route-level access denial for admin-only pages
- Inline permission denial in future dashboard access scenarios

Do NOT use when:
- Dashboard not found (use `NotFound`)
- General server errors (use `ErrorPage` with variant="500")
- Component-level errors (use `ErrorBoundary`)

### Implementation Changes Made (per TASK_050)

1. ✅ Added JSDoc to `AccessDenied.tsx` documenting intended usage patterns
2. ✅ Updated `RoleBasedAccess.tsx` to use AccessDenied as default fallback
3. ✅ Documented research findings in PLAN_02.md

---

**Date:** 2026-06-08
**Author:** Research conducted per TASK_049, TASK_050
**Reference:** FE-006, FE-007 (audit findings)