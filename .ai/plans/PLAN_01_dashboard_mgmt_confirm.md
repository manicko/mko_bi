---
wave: 2
depends_on:
  - PLAN_01_confirm_dialog.md
  - PLAN_01_short_uuid.md
files_modified:
  - frontend/src/features/admin/ui/DashboardManagement.tsx
autonomous: true
---

# Plan 01.8: Admin Dashboard Management — Confirm Dialog + Short UUID

## Goal
Upgrade `DashboardManagement.tsx` to use `ConfirmDialog` instead of `window.confirm` for delete, display short UUIDs, and update pagination defaults.

## must_haves
- [ ] `ConfirmDialog` replaces `window.confirm` for delete action
- [ ] Delete button in ConfirmDialog disabled during request (`loading={deleteMutation.isPending}`)
- [ ] ID column displays short UUID using `shortUuid` utility
- [ ] Default page size: 25
- [ ] Toast notifications via `react-hot-toast` instead of Snackbar
- [ ] Removed Snackbar/Alert state and imports

## Tasks

### Task 1: Replace window.confirm with ConfirmDialog
In `frontend/src/features/admin/ui/DashboardManagement.tsx`:
- Import `ConfirmDialog` from `'../../../shared/components/ConfirmDialog'`
- Add state: `const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)`
- Add state: `const [dashboardToDelete, setDashboardToDelete] = useState<DashboardAdmin | null>(null)`
- Replace `handleDelete` function: instead of `if (confirm(...)) { deleteMutation.mutate(...) }`, set `setDashboardToDelete(dashboard)` and `setDeleteDialogOpen(true)`
- Render `<ConfirmDialog>` with `loading={deleteMutation.isPending}` and `onConfirm` calling `deleteMutation.mutate(dashboardToDelete.id)` then closing dialog

### Task 2: Add short UUID to ID column
Add an ID column to the columns array:
```tsx
{
  field: 'id',
  headerName: 'ID',
  width: 120,
  valueGetter: (value: string) => shortUuid(value),
},
```
Import `shortUuid` from `'../../../shared/utils/shortUuid'`.

### Task 3: Replace Snackbar with toast
Remove `Snackbar`, `Alert` imports and state. Replace `setSnackbar(...)` calls with `toast.success(...)` / `toast.error(...)` from `react-hot-toast`.

### Task 4: Update pagination defaults
Change `initialState` to use `pageSize: 25` instead of `pageSize: 10`.

## Validation
- Verify ConfirmDialog appears for delete instead of browser confirm
- Verify Delete button is disabled during request
- Verify short UUID displayed in ID column
- Verify toasts appear instead of Snackbar

## Acceptance Criteria
- [ ] ConfirmDialog for delete
- [ ] Short UUID in ID column
- [ ] No Snackbar/Alert usage
- [ ] Default page size 25
