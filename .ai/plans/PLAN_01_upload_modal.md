---
wave: 3
depends_on:
  - PLAN_01_toast_config.md
files_modified:
  - frontend/src/features/upload/ui/UploadModal.tsx
  - frontend/src/features/upload/ui/UploadPage.tsx
  - frontend/src/features/upload/index.ts
  - frontend/src/features/dashboards/ui/DashboardView.tsx
  - frontend/src/app/routes.tsx
autonomous: true
---

# Plan 01.10: Upload Modal Conversion

## Goal
Convert the upload flow from a separate page (`UploadPage` at `/dashboard/:id/upload`) to a modal dialog (`UploadModal`) opened from the dashboard view page. Remove the upload route and integrate the modal into `DashboardView`.

## must_haves
- [ ] `UploadModal.tsx` created with upload logic extracted from `UploadPage.tsx`
- [ ] Modal opens from an "Upload Data" button on `DashboardView`
- [ ] Modal contains: mode toggle (overwrite/append), FileDropzone, upload progress, processing status polling
- [ ] On processing success: close modal and invalidate dashboard data queries
- [ ] On close: return to dashboard view (no navigation)
- [ ] `/dashboard/:id/upload` route removed from `routes.tsx`
- [ ] `UploadPage.tsx` removed or no longer imported
- [ ] No page reload on upload — only dashboard data refreshes via TanStack Query invalidation

## Tasks

### Task 1: Create UploadModal component
Create file `frontend/src/features/upload/ui/UploadModal.tsx`. Extract the core upload logic from `UploadPage.tsx` and adapt it for modal usage.

The component interface:
```tsx
interface UploadModalProps {
  open: boolean
  dashboardId: string
  onClose: () => void
  onSuccess: () => void
}
```

Key changes from UploadPage:
- Remove `useNavigate` — no navigation needed
- Remove outer `<Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>` wrapper
- Wrap content in `<Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>`
- Use `DialogTitle`, `DialogContent`, `DialogActions` from MUI
- On processing success: call `onSuccess()` then `onClose()` (no `navigate`)
- Keep all upload state management, file handling, progress tracking, and polling logic
- Keep the `FileDropzone` component usage

### Task 2: Update DashboardView to use UploadModal
In `frontend/src/features/dashboards/ui/DashboardView.tsx`:
- Import `UploadModal` from `'../../upload/ui/UploadModal'`
- Add state: `const [uploadModalOpen, setUploadModalOpen] = useState(false)`
- Change the "Upload Data" button's `onClick` from `() => navigate(`/dashboard/${id}/upload`)` to `() => setUploadModalOpen(true)`
- Render `<UploadModal>` at the end of the component:
```tsx
{canEdit && (
  <UploadModal
    open={uploadModalOpen}
    dashboardId={id || ''}
    onClose={() => setUploadModalOpen(false)}
    onSuccess={() => {
      if (id) {
        invalidateAggregatedData(id)
        queryClient.invalidateQueries({ queryKey: ['dashboards', id] })
      }
    }}
  />
)}
```
- Remove `useNavigate` import if no longer used (check if it's still needed for other logic)

### Task 3: Remove upload route from routes.tsx
In `frontend/src/app/routes.tsx`:
- Remove the entire `<Route>` block for `path="/dashboard/:id/upload"` (lines 37-46)
- Remove the `UploadPage` import (line 10)

### Task 4: Update upload feature exports
Update `frontend/src/features/upload/index.ts` to export `UploadModal` instead of `UploadPage`:
```tsx
export { UploadModal } from './ui/UploadModal'
```

### Task 5: Delete UploadPage.tsx
After confirming all upload logic has been extracted to `UploadModal` and the upload route has been removed from `routes.tsx`, delete the now-unused file:
- Delete `frontend/src/features/upload/ui/UploadPage.tsx`
- Verify no remaining imports reference `UploadPage` anywhere in the codebase (grep for `UploadPage` to confirm)

## Validation
- Verify upload modal opens from DashboardView "Upload Data" button
- Verify modal contains mode toggle, dropzone, and upload progress
- Verify file upload and processing works end-to-end
- Verify on success, modal closes and dashboard data refreshes
- Verify `/dashboard/:id/upload` route no longer exists
- Verify no navigation occurs during upload flow

## Acceptance Criteria
- [ ] UploadModal created and functional
- [ ] Upload route removed
- [ ] DashboardView opens upload as modal
- [ ] No page navigation during upload
- [ ] Dashboard data refreshes after successful upload
- [ ] `UploadPage.tsx` deleted and no dead imports remain
