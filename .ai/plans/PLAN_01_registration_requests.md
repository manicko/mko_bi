---
wave: 2
depends_on:
  - PLAN_01_confirm_dialog.md
files_modified:
  - frontend/src/features/admin/ui/RegistrationRequests.tsx
autonomous: true
---

# Plan 01.9: Admin Registration Requests — Confirm Dialog + Toast

## Goal
Upgrade `RegistrationRequests.tsx` to use `ConfirmDialog` for approve/reject confirmations and toast notifications instead of Snackbar.

## must_haves
- [ ] `ConfirmDialog` replaces the existing inline Dialog for approve/reject actions
- [ ] Delete/confirm button disabled during request (`loading`)
- [ ] ConfirmDialog uses `confirmLabel="Approve"` for approve action and `confirmLabel="Reject"` for reject action
- [ ] Toast notifications via `react-hot-toast` instead of Snackbar
- [ ] Default page size: 25
- [ ] Removed Snackbar/Alert state and imports

## Tasks

### Task 1: Replace inline Dialog with ConfirmDialog
In `frontend/src/features/admin/ui/RegistrationRequests.tsx`:
- The existing code already uses a `Dialog` for confirm — replace it with `ConfirmDialog` from `'../../../shared/components/ConfirmDialog'`
- The `actionType` state determines the title/message: `'Approve'` or `'Reject'`
- Pass `loading={approveMutation.isPending || rejectMutation.isPending}`
- Pass `confirmLabel={actionType}` so the button shows "Approve" or "Reject" instead of "Delete"
- `onConfirm` calls the appropriate mutation based on `actionType`

### Task 2: Replace Snackbar with toast
Remove `Snackbar`, `Alert` imports and state. Replace `setSnackbar(...)` calls with `toast.success(...)` / `toast.error(...)` from `react-hot-toast`.

### Task 3: Update pagination defaults
Change `initialState` to use `pageSize: 25` instead of `pageSize: 10`.

## Validation
- Verify ConfirmDialog appears for approve/reject
- Verify button disabled during request
- Verify toasts appear instead of Snackbar

## Acceptance Criteria
- [ ] ConfirmDialog for approve/reject
- [ ] No Snackbar/Alert usage
- [ ] Default page size 25
