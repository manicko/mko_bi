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

**Date:** 2026-06-08
**Author:** Research conducted per TASK_049
**Reference:** FE-006 (audit finding)