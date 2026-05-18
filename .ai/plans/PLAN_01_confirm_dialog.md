---
wave: 1
depends_on: []
files_modified:
  - frontend/src/shared/components/ConfirmDialog.tsx
autonomous: true
---

# Plan 01.4: Confirm Dialog Component

## Goal
Create a reusable `ConfirmDialog` component for destructive actions (delete user, delete dashboard, etc.) with backdrop dimmer, short text, Cancel + Delete buttons, and Delete button disabled during request.

## must_haves
- [ ] MUI Dialog with backdrop dimmer (default MUI behavior)
- [ ] Props: `open`, `title`, `message`, `onConfirm`, `onCancel`, `loading?`, `confirmLabel?` (default: "Delete")
- [ ] Cancel button always enabled, calls `onCancel`
- [ ] Confirm button with `color="error"` and `disabled={loading}`, label from `confirmLabel` prop (defaults to "Delete")
- [ ] Short, clear text in DialogContent
- [ ] Esc closes dialog (default MUI Dialog behavior)

## Tasks

### Task 1: Create ConfirmDialog component
Create file `frontend/src/shared/components/ConfirmDialog.tsx`:

```tsx
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography } from '@mui/material'

interface ConfirmDialogProps {
  open: boolean
  title: string
  message: string
  onConfirm: () => void
  onCancel: () => void
  loading?: boolean
  confirmLabel?: string
}

export function ConfirmDialog({ open, title, message, onConfirm, onCancel, loading, confirmLabel = 'Delete' }: ConfirmDialogProps) {
  return (
    <Dialog open={open} onClose={onCancel}>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <Typography>{message}</Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel}>Cancel</Button>
        <Button onClick={onConfirm} color="error" disabled={loading}>
          {confirmLabel}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
```

## Validation
- Verify dialog opens with correct title and message
- Verify Delete button is disabled when `loading={true}`
- Verify Esc closes the dialog
- Verify clicking outside (on backdrop) closes the dialog

## Acceptance Criteria
- [ ] ConfirmDialog component created with all required props including `confirmLabel`
- [ ] Confirm button label defaults to "Delete" and is configurable via `confirmLabel` prop
- [ ] Confirm button disabled during loading state
- [ ] Backdrop dimmer present (MUI default)
