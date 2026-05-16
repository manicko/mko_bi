# Frontend Lint Errors

## Description
6 ESLint errors exist in the frontend codebase that were discovered during integration verification.

## Affected Modules
- `frontend/src/features/dashboards/ui/DashboardFilters.tsx` - 2 errors
- `frontend/src/features/dashboards/ui/DashboardView.tsx` - 1 error
- `frontend/src/features/dashboards/ui/charts/PlotlyChart.tsx` - 1 error
- `frontend/src/features/upload/ui/UploadPage.tsx` - 1 error

## Risk
Low - These are code quality issues, not functional bugs. The application works correctly.

## Root Cause
- `react-hooks/set-state-in-effect`: Calling setState synchronously within useEffect can trigger cascading renders
- `no-case-declarations`: Unexpected lexical declaration in case block (should wrap in braces)
- `@typescript-eslint/no-explicit-any`: Using `any` type instead of proper typing

## Architectural Impact
None - these are frontend code quality issues that don't affect architecture.

## Suggested Direction
1. Fix `DashboardFilters.tsx` and `DashboardView.tsx` by moving setState calls to proper lifecycle or using useLayoutEffect
2. Fix case block declarations by wrapping in braces
3. Replace `any` type in PlotlyChart.tsx with proper typing