---
wave: 3
depends_on: []
files_modified:
  - frontend/src/features/admin/ui/AdminPanel.tsx
autonomous: true
---

# Plan 01.12: Admin Panel — Table State Preservation

## Goal
Ensure admin panel tab state (pagination, sorting) is preserved when switching between tabs by keeping tab content mounted but hidden instead of conditionally rendering.

## must_haves
- [ ] All admin tabs (User Management, Registration Requests, Dashboard Management) stay mounted when switching tabs
- [ ] Hidden tabs use `display: none` to preserve DataGrid state
- [ ] Pagination and sorting state preserved when switching back to a tab
- [ ] No data re-fetching when returning to a previously visited tab (TanStack Query cache handles this)

## Tasks

### Task 1: Update AdminPanel to keep tabs mounted
In `frontend/src/features/admin/ui/AdminPanel.tsx`, replace the conditional rendering pattern:
```tsx
{currentTab === 0 && <UserManagement />}
{currentTab === 1 && <RegistrationRequests />}
{currentTab === 2 && <DashboardManagement />}
```

With a visibility-based pattern:
```tsx
<Box sx={{ display: currentTab === 0 ? 'block' : 'none' }}>
  <UserManagement />
</Box>
<Box sx={{ display: currentTab === 1 ? 'block' : 'none' }}>
  <RegistrationRequests />
</Box>
<Box sx={{ display: currentTab === 2 ? 'block' : 'none' }}>
  <DashboardManagement />
</Box>
```

Import `Box` from `@mui/material` if not already imported.

## Validation
- Verify switching tabs preserves DataGrid pagination state
- Verify sorting state is preserved
- Verify no unnecessary re-renders or data refetches when switching tabs

## Acceptance Criteria
- [ ] All tabs remain mounted
- [ ] Pagination state preserved on tab switch
- [ ] Sorting state preserved on tab switch
