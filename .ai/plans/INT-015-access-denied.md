# INT-015 Research: AccessDenied Component Usage

## Summary

Research completed on AccessDenied component usage across the frontend codebase.

## Findings

### Current Usage

1. **RoleBasedAccess.tsx (line 2)**: Direct import of AccessDenied as default fallback
   - Used as the default value for the `fallback` prop
   - Critical for role-based access control functionality

2. **shared/components/index.ts (line 5)**: Re-exported for public API
   - Exported from shared components barrel file

3. **No direct imports elsewhere**: AccessDenied is NOT imported directly in any other files
   - No route-specific usage (routes.tsx does not use AccessDenied directly)
   - No feature-level imports

4. **Tests verify the pattern**: RoleBasedAccess.test.tsx confirms AccessDenied is rendered as default fallback

### Component Implementation

AccessDenied.tsx is a simple 37-line component that displays:
- "No access — contact your administrator" text
- Centered box layout with flex centering
- No navigation options or additional UI

### Comparison with Similar Components

- **NotFound.tsx**: Uses ErrorPage with variant="404" - provides navigation button and user guidance
- **ErrorPage.tsx**: Provides full error pages with "Go to Home" buttons and reload functionality

AccessDenied lacks the user-friendly features (navigation, reload) that ErrorPage provides.

## Recommendation

**KEEP STANDALONE** - Safe to delete is NOT recommended.

### Rationale

1. **Functional Purpose**: AccessDenied serves as the default fallback for RoleBasedAccess, which is used in the `/admin` route
2. **Separation of Concerns**: AccessDenied (403) and NotFound (404) are semantically different error types
3. **Extensibility**: AccessDenied could be enhanced with "Contact admin" mailto links, login redirects, or other 403-specific actions
4. **Test Coverage**: Tests verify this specific behavior works correctly

### Suggested Enhancement (Optional)

If AccessDenied is kept standalone, consider adding:
- A link to contact administrator (mailto or /profile)
- Consistency with ErrorPage styling (currently uses inline Box, ErrorPage uses Container)

## Decision

**Do NOT delete `AccessDenied.tsx` or its re-export**. The component provides value as a dedicated 403 access denial UI and is actively used as the default fallback for RoleBasedAccess.