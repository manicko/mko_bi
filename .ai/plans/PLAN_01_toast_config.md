---
wave: 1
depends_on: []
files_modified:
  - frontend/src/app/providers.tsx
autonomous: true
---

# Plan 01.2: Toast Notification Configuration

## Goal
Configure react-hot-toast `<Toaster>` in `providers.tsx` with the correct position (top-right), auto-dismiss durations (3s success, 5s errors), stacking, and manual dismiss support per the locked decisions.

## must_haves
- [ ] Toaster positioned at `top-right`
- [ ] Success toasts auto-dismiss after ~3000ms
- [ ] Error toasts auto-dismiss after ~5000ms
- [ ] Multiple toasts stack vertically
- [ ] Manual dismiss (close button) available on all toasts
- [ ] Toaster rendered inside `<ThemeProvider>` but wrapping `<AppRoutes />`

## Tasks

### Task 1: Update Toaster configuration in providers.tsx
In `frontend/src/app/providers.tsx`, replace the current `<Toaster position="top-right" />` (line 29) with:

```tsx
<Toaster
  position="top-right"
  gutter={8}
  toastOptions={{
    success: { duration: 3000 },
    error: { duration: 5000 },
  }}
/>
```

The `gutter={8}` ensures 8px spacing between stacked toasts. The `toastOptions` sets per-type durations. Manual dismiss (close button) is enabled by default in react-hot-toast v2.6.

## Validation
- Verify the Toaster renders at top-right of the screen
- Trigger a `toast.success('test')` and confirm it disappears after ~3s
- Trigger a `toast.error('test')` and confirm it disappears after ~5s
- Trigger multiple toasts and confirm they stack vertically

## Acceptance Criteria
- [ ] Toaster configured with correct position and durations
- [ ] No visual regressions in the app layout
