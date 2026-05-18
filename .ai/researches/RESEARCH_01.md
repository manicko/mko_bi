# 01 Frontend — BI Dashboard System (React + Plotly) - Research

**Researched:** 2026-05-18
**Domain:** React SPA frontend with MUI, TanStack Query, Plotly, DataGrid inline editing, toast notifications
**Confidence:** HIGH

## Summary

This research covers Phase 01: building a React SPA frontend for a BI dashboard system. The project already has a solid foundation — MUI v9, TanStack Query v5, React Router v7, react-hot-toast v2.6, Zod v4, and @mui/x-data-grid v9 are all installed and partially implemented. The existing code covers auth (login/register), dashboard list/view with Plotly charts, upload page, admin panel with DataGrid tables, and user profile management.

The key technical challenges for this phase are: (1) implementing inline editing in MUI X DataGrid v9 with per-row parallel save, revert-on-error, and row-highlight during save; (2) converting the upload page from a separate route to a modal on the dashboard page; (3) converting the dashboard list from cards to a table format; (4) implementing toast notifications with correct positioning and auto-dismiss; (5) implementing confirm dialogs with dimmer overlay; (6) ensuring Zod v4 schema compatibility since the installed version has breaking changes from v3.

**Primary recommendation:** The existing stack is well-chosen and already installed. Focus on using MUI X DataGrid v9's `processRowUpdate` callback for inline editing (it supports promise-based save with revert), `react-hot-toast`'s `<Toaster>` with per-toast `duration` for notifications, and Zod v4's `z.email()` top-level function instead of deprecated `z.string().email()`. No new libraries are needed.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 19.2.5 | UI framework | Already installed, latest stable |
| TypeScript | 6.0.2 | Type safety | Already installed, strict mode |
| Vite | 8.0.10 | Build tool | Already installed, fast HMR |
| @mui/material | 9.0.0 | UI component library | Already installed, v9 latest |
| @mui/icons-material | 9.0.0 | Icon components | Already installed, pairs with MUI |
| @mui/x-data-grid | 9.0.4 | Data tables with inline editing | Already installed, v9 supports `processRowUpdate` with rowId param |
| @tanstack/react-query | 5.100.9 | Server state management | Already installed, v5 latest |
| react-router-dom | 7.15.0 | Client-side routing | Already installed, v7 latest |
| react-hook-form | 7.75.0 | Form state management | Already installed |
| @hookform/resolvers | 5.2.2 | Zod integration for RHF | Already installed |
| zod | 4.4.3 | Schema validation | Already installed, v4 (has v3→v4 breaking changes) |
| axios | 1.16.0 | HTTP client | Already installed |
| react-plotly.js | 2.6.0 | Plotly chart wrapper | Already installed |
| plotly.js-dist-min | 3.5.1 | Charting library | Already installed |
| react-hot-toast | 2.6.0 | Toast notifications | Already installed, v2.6 supports multiple toasters |
| react-dropzone | 15.0.0 | File drag-and-drop | Already installed |
| @mui/x-date-pickers | 9.0.4 | Date picker components | Already installed, used in LogViewer |
| date-fns | 4.1.0 | Date utility | Already installed, adapter for x-date-pickers |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|--------------|
| @emotion/react | 11.14.0 | CSS-in-JS for MUI | Already installed, required by MUI v9 |
| @emotion/styled | 11.14.1 | Styled components for MUI | Already installed, required by MUI v9 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| @mui/x-data-grid | AG Grid | AG Grid has more features but heavier; MUI X is already installed and integrated with MUI theme |
| react-hot-toast | Notistack (MUI) | Notistack integrates with MUI Snackbar but react-hot-toast is already installed and lighter |
| react-router-dom v7 data mode | Keep BrowserRouter mode | Data mode (createBrowserRouter) adds loaders/actions; not needed since we use TanStack Query for data fetching |
| Zod v4 `z.string().email()` | `z.email()` | v4 deprecates method-form validators; use top-level functions |

**Installation:** All packages are already installed. No `npm install` needed.

## Architecture Patterns

### Recommended Project Structure

The existing FSD structure is correct and should be maintained:

```
frontend/src/
├── app/                    # Providers and routing (DO NOT change to data mode)
│   ├── providers.tsx       # QueryClient, BrowserRouter, ThemeProvider, Toaster
│   └── routes.tsx          # Route definitions using <Routes>/<Route>
├── features/               # Business features
│   ├── auth/               # Login, register, token management
│   │   ├── api/            # authApi.ts
│   │   ├── model/          # useAuth.ts, authToken.ts
│   │   └── ui/             # LoginForm.tsx, RegisterForm.tsx
│   ├── dashboards/         # Dashboard list, view, charts
│   │   ├── api/            # dashboardApi.ts (TanStack Query hooks)
│   │   ├── ui/             # DashboardList.tsx (TABLE, not cards), DashboardView.tsx
│   │   └── ui/charts/      # PlotlyChart.tsx, BarChart.tsx, etc.
│   ├── upload/             # File upload (MODAL, not separate page)
│   │   ├── api/            # uploadApi.ts
│   │   └── ui/             # FileDropzone.tsx, UploadModal.tsx (was UploadPage.tsx)
│   ├── admin/              # Admin panel with tabs
│   │   ├── api/            # adminApi.ts
│   │   └── ui/             # AdminPanel.tsx, UserManagement.tsx, etc.
│   └── users/              # User profile, change password
│       ├── api/            # userApi.ts
│       └── ui/             # UserProfile.tsx, ChangePasswordPage.tsx
├── shared/                 # Reusable code
│   ├── api/                # axiosInstance.ts (interceptors for JWT)
│   ├── components/         # Layout, ProtectedRoute, RoleBasedAccess, ConfirmDialog
│   │   └── Layout/         # AppLayout.tsx, Header.tsx, Sidebar.tsx
│   └── types/              # enums.ts, api.types.ts, formSchemas.ts
└── main.tsx                # Entry point
```

### Pattern 1: DataGrid Inline Editing with Per-Row Parallel Save

**What:** MUI X DataGrid v9 supports inline cell editing with `processRowUpdate` callback. Each row save is independent — the callback returns a Promise, and the grid handles each row's lifecycle separately.

**When to use:** Admin tables (UserManagement, DashboardManagement, RegistrationRequests) where users edit cells inline and each change saves immediately to the server.

**Key API details (verified from MUI X v9 docs):**
- `processRowUpdate(newRow, originalRow, { rowId })` — called when editing stops. Must return the row object (or a Promise resolving to it). If the promise resolves with `originalRow`, the cell reverts. If rejected, the cell stays in edit mode.
- `onProcessRowUpdateError(error)` — called when `processRowUpdate` throws or rejects.
- Column `editable: true` enables editing per column.
- Column `type: 'singleSelect'` with `valueOptions` renders a dropdown inline editor.
- `editMode: 'row'` enables row-level editing (all editable cells in a row simultaneously).
- `rowModesModel` + `onRowModesModelChange` for controlled editing state.

**Example — Inline cell edit with save/revert pattern:**
```tsx
// Source: Context7 /mui/mui-x — editing/persistence.md
<DataGrid
  rows={rows}
  columns={columns}
  editMode="row"
  processRowUpdate={async (updatedRow, originalRow, { rowId }) => {
    try {
      const saved = await apiSaveRow(updatedRow);
      return saved; // Grid updates with saved data
    } catch (error) {
      toast.error(`Save failed: ${error.message}`);
      return originalRow; // Revert cell to previous value, exit edit mode
    }
  }}
  onProcessRowUpdateError={(error) => {
    toast.error(`Save failed: ${error.message}`);
  }}
/>
```

**Row highlight during save:** Track saving state per row ID in a `Set<string>`. Apply a yellow background via `getRowClassName`:
```tsx
const savingRows = useRef(new Set<string>());

// In processRowUpdate:
savingRows.current.add(rowId);
// ... after save completes or fails:
savingRows.current.delete(rowId);

// In DataGrid props:
getRowClassName={(params) => {
  return savingRows.current.has(params.id) ? 'row-saving' : '';
}}
```

**Parallel saves:** Since `processRowUpdate` is called independently for each row edit, and each returns its own Promise, rows save in parallel naturally. No queue or blocking needed.

**Dropdown inline edit (singleSelect):** For role/status dropdowns, use `type: 'singleSelect'` with `valueOptions`. The dropdown closes automatically after selection, and `processRowUpdate` fires immediately:
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

### Pattern 2: Toast Notifications with react-hot-toast

**What:** react-hot-toast v2.6 supports per-toast duration, stacking, and manual dismiss.

**Configuration in providers.tsx:**
```tsx
// Source: Context7 /timolins/react-hot-toast
<Toaster
  position="top-right"
  gutter={8}
  toastOptions={{
    success: { duration: 3000 },
    error: { duration: 5000 },
    style: { background: '#363636', color: '#fff' },
  }}
/>
```

**Per-toast usage:**
```tsx
import { toast } from 'react-hot-toast';

toast.success('Saved!', { duration: 3000 });
toast.error('Save failed', { duration: 5000 });
toast.dismiss(); // Manual dismiss
```

### Pattern 3: Confirm Dialog Pattern

**What:** MUI Dialog with backdrop dimmer for destructive actions (delete user, delete dashboard, etc.).

**Implementation:**
```tsx
function ConfirmDialog({ open, title, message, onConfirm, onCancel, confirmLoading }) {
  return (
    <Dialog open={open} onClose={onCancel}>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent><Typography>{message}</Typography></DialogContent>
      <DialogActions>
        <Button onClick={onCancel}>Cancel</Button>
        <Button onClick={onConfirm} color="error" disabled={confirmLoading}>
          Delete
        </Button>
      </DialogActions>
    </Dialog>
  );
}
```

MUI Dialog already has a backdrop dimmer by default (`Backdrop` component). The `Delete` button is blocked during request via `disabled={confirmLoading}`.

### Pattern 4: Upload as Modal (Not Separate Page)

**What:** The upload flow should open as a modal dialog on the dashboard page, not navigate to a separate route.

**Implementation approach:**
1. Create `UploadModal.tsx` in `features/upload/ui/` — extract the upload logic from `UploadPage.tsx`
2. In `DashboardView.tsx`, add an "Upload" button that opens the modal state
3. Modal contains: mode toggle (overwrite/append), FileDropzone, upload progress, processing status polling
4. On processing success, close modal and invalidate dashboard data queries
5. Remove the `/dashboard/:id/upload` route from routes.tsx

### Pattern 5: Dashboard List as Table

**What:** Convert from Card grid to DataGrid table with ID + Name columns.

**Implementation:**
```tsx
const columns: GridColDef[] = [
  { field: 'id', headerName: 'ID', width: 120,
    valueGetter: (value: string) => value.slice(0, 8) }, // Short UUID
  { field: 'name', headerName: 'Name', width: 300 },
  { field: 'permission', headerName: 'Permission', width: 130 },
];
```

### Pattern 6: Zod v4 Schema Compatibility

**What:** Zod v4 has breaking changes from v3. The project has `zod: ^4.4.3` installed.

**Critical changes:**
- `z.string().email()` is deprecated → use `z.email()` (top-level function)
- `z.string().uuid()` is deprecated → use `z.uuid()`
- `z.string().url()` is deprecated → use `z.url()`
- `message` param → `error` param in validation methods: `z.string().min(5, { error: "Too short" })`
- `z.infer<typeof Schema>` still works for type inference
- `z.object({})` still works
- `.refine()` still works with `{ error: "..." }` instead of `{ message: "..." }`

**Existing code impact:** The current `formSchemas.ts` uses `z.string().email()` and `{ message: '...' }` pattern — these need updating to Zod v4 syntax.

### Pattern 7: Short UUID Display

**What:** Display first 8 characters of UUID for all IDs.

**Implementation:** Use `valueGetter` in DataGrid columns or a utility function:
```tsx
const shortUuid = (id: string) => id.slice(0, 8);
```

### Pattern 8: Table State Preservation on Navigation

**What:** DataGrid pagination/sorting state should be preserved when navigating back.

**Implementation:** Use `paginationModel` + `onPaginationModelChange` with state lifted to the component level. Since React state is preserved when components stay mounted (using `display: none` for hidden tabs), or use `queryParams` for URL-persisted state. For admin tabs, keep tab content mounted but hidden.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Inline table editing | Custom cell editors with useState per cell | MUI X DataGrid `processRowUpdate` | Handles edit mode, focus, keyboard nav, promise-based save/revert |
| Toast notifications | Custom toast component with CSS animations | react-hot-toast | Already installed, handles stacking, auto-dismiss, pause-on-hover |
| File drag-and-drop | Custom drop event handlers | react-dropzone | Already installed, handles drag state, file filtering |
| Form validation | Manual if/else validation | Zod + @hookform/resolvers | Already installed, type-safe, composable |
| Confirm dialogs | Custom modal with backdrop | MUI Dialog | Already installed, has backdrop dimmer, focus trap, Escape handling |
| Date picking | Custom date input | @mui/x-date-pickers + AdapterDateFns | Already installed, accessible, locale-aware |
| Table pagination/sorting | Custom pagination logic | DataGrid built-in paginationModel | Already installed, handles page size, page index |
| JWT token storage | Custom cookie/sessionStorage logic | Existing authToken.ts (memory-first) | Already implemented with production memory-only mode |
| HTTP interceptors | Custom fetch wrapper | axiosInstance with interceptors | Already implemented with JWT injection and 401 handling |
| Route protection | Custom auth checks per route | ProtectedRoute + RoleBasedAccess | Already implemented |

## Common Pitfalls

### Pitfall 1: Zod v4 Breaking Changes in Form Schemas

**What goes wrong:** `z.string().email()` silently stops working or produces deprecation warnings. `{ message: "error" }` in `.min()` / `.max()` / `.refine()` doesn't work in v4.
**Why it happens:** Zod v4 moved string format validators to top-level functions and renamed `message` to `error`.
**How to avoid:** Update all schemas: `z.string().email()` → `z.email()`, `{ message: "x" }` → `{ error: "x" }`.
**Warning signs:** TypeScript deprecation warnings, validation not triggering.

### Pitfall 2: DataGrid processRowUpdate Not Returning Row Object

**What goes wrong:** After editing a cell, the grid shows the old value or enters an inconsistent state.
**Why it happens:** `processRowUpdate` must return the row object (or a Promise resolving to it). If it returns `undefined` or `void`, the grid doesn't know what to display.
**How to avoid:** Always return either `updatedRow` (on success) or `originalRow` (on error/revert) from `processRowUpdate`.
**Warning signs:** Cell shows stale data after edit, or edit mode doesn't exit.

### Pitfall 3: React Router v7 Import Changes

**What goes wrong:** `import { BrowserRouter } from 'react-router-dom'` may not work in v7. v7 merged `react-router` and `react-router-dom`.
**Why it happens:** In v7, DOM-specific exports moved to `react-router/dom`. However, `react-router-dom` still works as a compatibility shim.
**How to avoid:** The current code uses `react-router-dom` which is fine. If upgrading imports, use `react-router` for core APIs and `react-router/dom` for `RouterProvider`/`HydratedRouter`. Keep `BrowserRouter` for now since the app doesn't use data mode.
**Warning signs:** Import errors, "useRoutes must be used within a RouterProvider" warnings.

### Pitfall 4: MUI X DataGrid v9 Pagination Model

**What goes wrong:** Pagination doesn't work or uses wrong defaults.
**Why it happens:** DataGrid v9 uses `paginationModel: { page: 0, pageSize: 100 }` by default (page is 0-indexed). The old `pageSize` prop is deprecated.
**How to avoid:** Use `initialState: { pagination: { paginationModel: { pageSize: 25 } } }` for initial state, or `paginationModel` + `onPaginationModelChange` for controlled state.
**Warning signs:** Table shows 100 rows by default, pagination controls don't respond.

### Pitfall 5: Toast Auto-Dismiss Timing

**What goes wrong:** Success toasts linger too long or error toasts disappear too quickly.
**Why it happens:** Default toast duration is 5000ms for all types.
**How to avoid:** Configure per-type defaults in `<Toaster toastOptions={{ success: { duration: 3000 }, error: { duration: 5000 } }} />`.
**Warning signs:** Toasts visible for wrong duration.

### Pitfall 6: Upload as Page vs Modal Route Conflict

**What goes wrong:** If upload is converted to modal but the `/dashboard/:id/upload` route remains, users can still navigate to a broken page.
**Why it happens:** Route definition not removed when component changes from page to modal.
**How to avoid:** Remove the upload route from `routes.tsx` when converting to modal. The upload button on DashboardView should set local state, not navigate.
**Warning signs:** Direct URL navigation to `/dashboard/:id/upload` shows broken page.

### Pitfall 7: Row Highlight State Stale Reference

**What goes wrong:** Row highlight doesn't clear after save completes.
**Why it happens:** `Set` mutation doesn't trigger re-render unless state is updated.
**How to avoid:** Use `useState` instead of `useRef` for `savingRows`, or call `apiRef.current.forceUpdate()` after modifying the ref.
**Warning signs:** Row stays yellow after save completes.

### Pitfall 8: Parallel Mutation Race Conditions in TanStack Query

**What goes wrong:** Rapid inline edits on the same row cause stale data to overwrite fresh data.
**Why it happens:** If two mutations are in flight for the same row, the first may resolve after the second, overwriting with stale data.
**How to avoid:** Use `onMutate` for optimistic updates with proper rollback. For inline editing, the DataGrid's `processRowUpdate` pattern handles this naturally since each edit starts from the current grid state.
**Warning signs:** Cell value flickers or reverts after rapid edits.

## Code Examples

### Inline Editing with Row Highlight and Revert-on-Error

```tsx
// Source: Context7 /mui/mui-x — editing/persistence.md (adapted)
import { useState, useCallback } from 'react';
import { DataGrid } from '@mui/x-data-grid';
import { toast } from 'react-hot-toast';

function UserTable() {
  const [savingRows, setSavingRows] = useState<Set<string>>(new Set());

  const processRowUpdate = useCallback(async (updatedRow, originalRow, { rowId }) => {
    setSavingRows((prev) => new Set(prev).add(rowId));
    try {
      const saved = await apiSaveUser(updatedRow);
      toast.success('User updated');
      return saved;
    } catch (error) {
      toast.error(`Save failed: ${error.message}`);
      return originalRow; // Revert to original value
    } finally {
      setSavingRows((prev) => {
        const next = new Set(prev);
        next.delete(rowId);
        return next;
      });
    }
  }, []);

  return (
    <DataGrid
      rows={rows}
      columns={columns}
      editMode="row"
      processRowUpdate={processRowUpdate}
      onProcessRowUpdateError={(error) => toast.error(error.message)}
      getRowClassName={(params) =>
        savingRows.has(params.id as string) ? 'row-saving' : ''
      }
      sx={{
        '& .row-saving': { backgroundColor: 'rgba(255, 235, 59, 0.3)' },
      }}
    />
  );
}
```

### Toast Configuration in App Provider

```tsx
// Source: Context7 /timolins/react-hot-toast — toaster.mdx
<Toaster
  position="top-right"
  gutter={8}
  toastOptions={{
    success: { duration: 3000 },
    error: { duration: 5000 },
    style: { background: '#363636', color: '#fff' },
  }}
/>
```

### Zod v4 Schema (Updated from v3)

```typescript
// Source: Context7 /colinhacks/zod — v4/changelog.mdx
import { z } from 'zod';

// Zod v4 — use top-level functions instead of deprecated method forms
export const loginSchema = z.object({
  email: z.email({ error: 'Invalid email format' }),  // NOT z.string().email()
  password: z.string().min(6, { error: 'Password must be at least 6 characters' }),
});

export const registerSchema = z.object({
  email: z.email({ error: 'Invalid email format' })
    .refine((email) => {
      const domain = email.split('@')[1];
      return domain && !['tempmail.com', 'throwawaymail.com'].includes(domain);
    }, { error: 'This email domain is not allowed' }),
});

export const changePasswordSchema = z.object({
  current_password: z.string().min(1, { error: 'Current password is required' }),
  new_password: z.string().min(8, { error: 'Password must be at least 8 characters' }),
  confirm_password: z.string().min(1, { error: 'Password confirmation is required' }),
}).refine((data) => data.new_password === data.confirm_password, {
  error: 'Passwords do not match',
  path: ['confirm_password'],
});
```

### Upload Modal (Extracted from UploadPage)

```tsx
// features/upload/ui/UploadModal.tsx
interface UploadModalProps {
  open: boolean;
  dashboardId: string;
  onClose: () => void;
  onSuccess: () => void;
}

export function UploadModal({ open, dashboardId, onClose, onSuccess }: UploadModalProps) {
  // ... upload logic from UploadPage.tsx ...
  // On processing success:
  // onSuccess(); // Invalidate dashboard queries
  // onClose();   // Close modal
  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      {/* Upload form content */}
    </Dialog>
  );
}
```

### Dashboard List as Table

```tsx
// features/dashboards/ui/DashboardList.tsx — TABLE format (not cards)
const columns: GridColDef[] = [
  {
    field: 'id',
    headerName: 'ID',
    width: 120,
    valueGetter: (value: string) => value.slice(0, 8),
  },
  { field: 'name', headerName: 'Name', width: 300 },
  { field: 'permission', headerName: 'Permission', width: 130 },
];

// In component:
<DataGrid
  rows={dashboards}
  columns={columns}
  loading={isLoading}
  initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
  pageSizeOptions={[10, 25, 50]}
  autoHeight
  slots={{ noRowsOverlay: () => <Box sx={{ p: 2, textAlign: 'center' }}>No data</Box> }}
/>
```

### Confirm Dialog with Loading State

```tsx
// shared/components/ConfirmDialog.tsx
interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

export function ConfirmDialog({ open, title, message, onConfirm, onCancel, loading }: ConfirmDialogProps) {
  return (
    <Dialog open={open} onClose={onCancel}>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent><Typography>{message}</Typography></DialogContent>
      <DialogActions>
        <Button onClick={onCancel}>Cancel</Button>
        <Button onClick={onConfirm} color="error" disabled={loading}>
          Delete
        </Button>
      </DialogActions>
    </Dialog>
  );
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `z.string().email()` | `z.email()` | Zod v4 (2025) | Method-form validators deprecated; top-level functions are the standard |
| `{ message: "error" }` in Zod | `{ error: "error" }` | Zod v4 (2025) | `message` param renamed to `error` |
| `processRowUpdate(newRow, oldRow)` | `processRowUpdate(newRow, oldRow, { rowId })` | MUI X v7+ (2024) | Third param with `rowId` added for identifying which row was edited |
| `DataGrid pageSize={25}` | `initialState: { pagination: { paginationModel: { pageSize: 25 } } }` | MUI X v6+ | Old `pageSize` prop deprecated in favor of `paginationModel` |
| `BrowserRouter` with `<Routes>` | `createBrowserRouter` + `RouterProvider` | React Router v6.4+ | Data mode recommended but NOT needed for this project (using TanStack Query) |
| `react-hot-toast` single toaster | Multiple toasters via `toasterId` | v2.6 (2025) | Not needed for this project; single default toaster is sufficient |
| MUI DataGrid v6/v7 | MUI X DataGrid v9 (2026-04) | v9 released April 2026 | Current installed version; `processRowUpdate` with `rowId` param works |

**Deprecated/outdated:**
- `z.string().email()`, `z.string().uuid()`, `z.string().url()` — use `z.email()`, `z.uuid()`, `z.url()`
- `{ message: "..." }` in Zod validation — use `{ error: "..." }`
- `DataGrid` `pageSize` prop — use `paginationModel` in `initialState`
- `editRowsModel` prop — replaced by `rowModesModel`/`cellModesModel` in MUI X v6+
- `onRowEditCommit` event — replaced by `processRowUpdate` callback

## Open Questions

1. **Zod v4 migration scope:** The existing `formSchemas.ts` uses `z.string().email()` and `{ message: "..." }`. All schemas need updating to Zod v4 syntax. This is a straightforward find-and-replace but must be done before any form validation works correctly.

2. **DataGrid v9 `processRowUpdate` signature:** The installed version is `^9.0.4`. The `processRowUpdate(newRow, originalRow, { rowId })` signature with the third `params` argument was added in v7. Verify the exact v9 API matches the documented signature. Context7 docs confirm v9 uses the 3-argument form.

3. **React Router v7 `react-router-dom` vs `react-router`:** The project has `react-router-dom: ^7.15.0` installed. In v7, `react-router-dom` is a compatibility shim that re-exports from `react-router`. The current imports (`BrowserRouter`, `Routes`, `Route`, `Navigate`, `Link`, `useNavigate`, `useLocation`, `Outlet`) all work from `react-router-dom`. No migration needed unless we want to switch to `react-router` imports.

4. **Upload modal vs page route:** The decision says "Upload opens as a modal on the dashboard page." This means removing the `/dashboard/:id/upload` route and the `UploadPage` component, replacing with a modal triggered from `DashboardView`. The existing `UploadPage.tsx` logic should be reused in the modal.

## Sources

### Primary (HIGH confidence)
- Context7 `/mui/mui-x` — DataGrid editing persistence, `processRowUpdate`, `singleSelect` columns, pagination model
- Context7 `/timolins/react-hot-toast` — Toaster configuration, per-toast duration, stacking, dismiss API
- Context7 `/tanstack/query` — `useMutation`, optimistic updates, `onMutate`/`onError`/`onSettled` lifecycle
- Context7 `/colinhacks/zod` — Zod v4 changelog, top-level validators, `error` param, `refine` with `abort`
- Context7 `/remix-run/react-router` — `createBrowserRouter`, `RouterProvider`, `BrowserRouter`, route state
- Existing codebase — `frontend/src/` all files (verified current implementation state)

### Secondary (MEDIUM confidence)
- Web Search: MUI X DataGrid v9.0 announcement (2026-04-08) — confirmed v9 release and editing improvements
- Web Search: react-hot-toast v2.6.0 release (2025-08-15) — confirmed multiple toasters support
- Web Search: React Router v7.15.0 release (2026-05-05) — confirmed v7 is current, `react-router-dom` compatibility

### Tertiary (LOW confidence)
- Web Search: React Router v6→v7 migration guide — import changes, data mode vs library mode

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified from `package.json`, Context7 confirms APIs
- Architecture: HIGH — patterns verified against existing codebase and Context7 docs
- Pitfalls: HIGH — Zod v4 changes verified from official changelog; DataGrid API verified from Context7
- Code examples: HIGH — adapted from Context7 official documentation

**Research date:** 2026-05-18
**Valid until:** 2026-06-18 (30 days — stable libraries, but MUI X v9 is very new)
