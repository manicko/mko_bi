---
wave: 2
depends_on:
  - PLAN_01_confirm_dialog.md
  - PLAN_01_short_uuid.md
files_modified:
  - frontend/src/features/admin/ui/UserManagement.tsx
autonomous: true
---

# Plan 01.7: Admin User Management — Inline Editing + Confirm Dialog

## Goal
Upgrade `UserManagement.tsx` with DataGrid inline editing (role column as dropdown with `singleSelect`), per-row parallel save with revert-on-error, row highlight during save, and replace `window.confirm` with the `ConfirmDialog` component.

## must_haves
- [ ] Role column uses `editable: true`, `type: 'singleSelect'`, `valueOptions: ['admin', 'editor', 'viewer']`
- [ ] `processRowUpdate` handles save: returns `updatedRow` on success, `originalRow` on error (revert)
- [ ] Row highlight (yellow background) during save via `getRowClassName` + `useState<Set<string>>`
- [ ] Parallel saves: each row saves independently, no blocking
- [ ] Dropdown closes immediately after selection, save triggers right away
- [ ] `ConfirmDialog` replaces `window.confirm` for delete action
- [ ] `shortUuid` used for ID display where applicable
- [ ] Toast notifications via `react-hot-toast` instead of Snackbar
- [ ] Removed Snackbar/Alert state and imports

## Tasks

### Task 1: Add inline editing to role column
In `frontend/src/features/admin/ui/UserManagement.tsx`, update the `role` column definition:
```tsx
{
  field: 'role',
  headerName: 'Role',
  width: 130,
  editable: true,
  type: 'singleSelect',
  valueOptions: ['admin', 'editor', 'viewer'],
}
```

### Task 2: Implement processRowUpdate with row highlight
Add state for tracking saving rows:
```tsx
const [savingRows, setSavingRows] = useState<Set<string>>(new Set())
```

Implement `processRowUpdate`:
```tsx
const processRowUpdate = useCallback(async (updatedRow, originalRow, { rowId }) => {
  setSavingRows((prev) => new Set(prev).add(rowId as string))
  try {
    await changeUserRole(updatedRow.id, updatedRow.role)
    toast.success('User updated')
    return updatedRow
  } catch (error) {
    const msg = error instanceof Error ? error.message : 'Save failed'
    toast.error(msg)
    return originalRow
  } finally {
    setSavingRows((prev) => {
      const next = new Set(prev)
      next.delete(rowId as string)
      return next
    })
  }
}, [])
```

Add to DataGrid props:
```tsx
processRowUpdate={processRowUpdate}
onProcessRowUpdateError={(error) => toast.error(error.message)}
getRowClassName={(params) =>
  savingRows.has(params.id as string) ? 'row-saving' : ''
}
sx={{
  '& .row-saving': { backgroundColor: 'rgba(255, 235, 59, 0.3)' },
}}
```

### Task 3: Remove old Dialog-based role editing code
Remove the old role change Dialog and all associated state/handler:
- Remove the `<Dialog>` element used for role change confirmation
- Remove state variables: `roleDialogOpen`, `selectedUser`, `newRole`
- Remove the `handleRoleChange` function that opens the dialog
- Remove any unused imports related to the old Dialog (e.g., `Dialog`, `DialogTitle`, `DialogContent`, `DialogActions`, `TextField`, `Select`, `MenuItem`, `InputLabel`, `FormControl` — only if not used elsewhere)
- Remove the old role change handler function

### Task 4: Replace window.confirm with ConfirmDialog
Replace the inline `confirm()` calls for delete with `ConfirmDialog` component:
- Import `ConfirmDialog` from `'../../../shared/components/ConfirmDialog'`
- Add state: `const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)`
- Add state: `const [userToDelete, setUserToDelete] = useState<AdminUser | null>(null)`
- Replace `if (confirm(...)) { deleteMutation.mutate(user.id) }` with setting state to open dialog
- Render `<ConfirmDialog>` with `loading={deleteMutation.isPending}`

### Task 5: Replace Snackbar with toast
Remove `Snackbar`, `Alert` imports and state. Replace `setSnackbar(...)` calls with `toast.success(...)` / `toast.error(...)` from `react-hot-toast`.

### Task 6: Update pagination defaults
Change `initialState` to use `pageSize: 25` instead of `pageSize: 10`.

## Validation
- Verify role dropdown appears inline in the table
- Verify selecting a role triggers save immediately
- Verify row turns yellow during save
- Verify on server error, cell reverts to original value
- Verify ConfirmDialog appears for delete instead of browser confirm
- Verify toasts appear instead of Snackbar

## Acceptance Criteria
- [ ] Inline editing works on role column
- [ ] Row highlight during save
- [ ] Revert on error
- [ ] ConfirmDialog for delete
- [ ] No Snackbar/Alert usage
- [ ] Default page size 25
