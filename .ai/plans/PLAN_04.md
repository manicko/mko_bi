---
phase: "04 — Registration Request Fixes"
description: "Fix 3 issues: (1) no loading/feedback during registration form submission, (2) form doesn't submit on Enter key, (3) admin registration requests table doesn't show new requests after submission"
autonomous: true
depends_on: []
files_modified:
  - frontend/src/features/auth/ui/RegisterForm.tsx
  - frontend/src/features/admin/ui/RegistrationRequests.tsx
  - frontend/src/shared/types/formSchemas.ts
waves:
  - id: 1
    tasks: [TASK_01, TASK_02, TASK_03]
    parallel: false
---

# PLAN_04: Registration Request Fixes

## must_haves

When this phase is complete, ALL of the following must be true:

1. **Loading state:** RegisterForm shows a disabled button with a spinner and "Sending..." text during submission. Button is immediately disabled on click to prevent double-submit.
2. **Enter key submission:** Pressing Enter in the email field submits the registration form.
3. **Admin data refresh:** When the admin switches to the Registration Requests tab, the table always fetches fresh data (no stale cache).
4. **Empty state:** When there are no pending registration requests, the DataGrid shows "No pending registration requests" instead of a blank table.
5. **Blocked domains aligned:** Frontend BLOCKED_DOMAINS matches backend config (`tempmail.com`, `throwaway.email`).
6. **No regressions:** Existing success flow (redirect to confirmation) and error flow (redirect to error page) remain unchanged. Login form unaffected.

---

## Wave 1 (Sequential — TASK_01 and TASK_02 target the same file; TASK_03 is independent but grouped for simplicity)

### TASK_01: Add loading state to RegisterForm

**File:** `frontend/src/features/auth/ui/RegisterForm.tsx`
**Symbol:** `RegisterForm` component
**Semantic anchor:** Lines 9-32 — component function body with `isLoading` from `useAuth()` and `onSubmit` handler. Lines 70-72 — submit button JSX.

**Root cause:** `useAuth().isLoading` is never set to `true` during `registerRequest()` (see `useAuth.ts:35-37` — the function just calls the API without setting loading state). The form needs its own local `isSubmitting` state.

**Changes:**

1. Remove `isLoading` from the `useAuth()` destructuring (line 10):
   ```typescript
   // Before:
   const { registerRequest, isLoading } = useAuth()
   // After:
   const { registerRequest } = useAuth()
   ```

2. Add local `isSubmitting` state alongside existing `error` and `success` states (after line 12):
   ```typescript
   const [isSubmitting, setIsSubmitting] = useState(false)
   ```

3. Update `onSubmit` handler (lines 22-32) to set submitting state:
   ```typescript
   const onSubmit = async (data: RegisterFormData) => {
     try {
       setError(null)
       setIsSubmitting(true)
       await registerRequest(data.email)
       setSuccess(true)
     } catch (error) {
       const axiosError = error as { response?: { data?: { detail?: string } } }
       const errorMessage = axiosError.response?.data?.detail || 'Failed to submit registration request. Please try again.'
       setError(errorMessage)
     } finally {
       setIsSubmitting(false)
     }
   }
   ```

4. Update the submit button (lines 70-72) to use MUI `loading` prop:
   ```tsx
   // Before:
   <Button type="submit" variant="contained" fullWidth sx={{ mt: 2 }} disabled={isLoading}>
     {isLoading ? 'Submitting...' : 'Submit Request'}
   </Button>

   // After:
   <Button
     type="submit"
     variant="contained"
     fullWidth
     sx={{ mt: 2 }}
     loading={isSubmitting}
     loadingPosition="start"
   >
     {isSubmitting ? 'Sending...' : 'Submit Request'}
   </Button>
   ```

**Rationale:** MUI v9 Button has a built-in `loading` prop that shows a CircularProgress spinner and disables the button automatically. Using local `isSubmitting` state instead of the shared `isLoading` from `useAuth` ensures the loading state is scoped to the form submission. The `finally` block ensures `isSubmitting` is reset even on error.

**Acceptance criteria:**
- On submit click: button shows spinner + "Sending..." text, button is disabled
- On success: `setSuccess(true)` triggers the existing success view (unchanged)
- On error: button re-enables, error Alert shown (existing behavior preserved)
- Double-submit prevented: button disabled immediately via `loading` prop
- `isLoading` is no longer destructured from `useAuth` in this file

**Validation:**
- `cd frontend && npx tsc --noEmit` — no type errors
- `cd frontend && npm run lint` — no lint errors

---

### TASK_02: Fix Enter key form submission in RegisterForm

**File:** `frontend/src/features/auth/ui/RegisterForm.tsx`
**Symbol:** `RegisterForm` component
**Semantic anchor:** Line 50 — `<Box component="form" onSubmit={handleSubmit(onSubmit)}` — already a form element. Line 70 — `<Button type="submit"` — already type="submit".

**Root cause investigation:** The current code already uses `<Box component="form" onSubmit={handleSubmit(onSubmit)}` with `<Button type="submit">`. This pattern should work for Enter key submission. The issue may be that MUI `TextField` with `margin="normal"` wraps in a `div` that interferes, or that the `handleSubmit` from `react-hook-form` has an issue with async handlers.

**Changes:**

1. Verify the form element renders correctly. If the `Box component="form"` does not produce a proper `<form>` element, replace it with a native `<form>` element (line 50):
   ```tsx
   // If Box component="form" doesn't render as <form>:
   // Before:
   <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ maxWidth: 400, mx: 'auto', mt: 4, p: 3 }}>
   // After:
   <form onSubmit={handleSubmit(onSubmit)} style={{ maxWidth: 400, margin: '32px auto 0', padding: '24px' }}>
   ```

   And update the closing tag (line 80) from `</Box>` to `</form>`.

   **However**, if `Box component="form"` does render as `<form>` (which it should — MUI Box renders the specified component), then the Enter key issue is likely caused by the async `onSubmit` not properly returning a promise. In that case, no structural change is needed — just ensure the `onSubmit` handler properly returns the promise chain.

2. Ensure `onSubmit` returns the promise (update the handler to return the result):
   ```typescript
   const onSubmit = async (data: RegisterFormData) => {
     try {
       setError(null)
       setIsSubmitting(true)
       await registerRequest(data.email)
       setSuccess(true)
     } catch (error) {
       const axiosError = error as { response?: { data?: { detail?: string } } }
       const errorMessage = axiosError.response?.data?.detail || 'Failed to submit registration request. Please try again.'
       setError(errorMessage)
     } finally {
       setIsSubmitting(false)
     }
   }
   ```
   (This is the same handler from TASK_01 — `react-hook-form`'s `handleSubmit` works with async handlers.)

3. If the issue persists after TASK_01 changes, add `noValidate` to the form element to prevent browser validation interference:
   ```tsx
   <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate sx={{ maxWidth: 400, mx: 'auto', mt: 4, p: 3 }}>
   ```

**Rationale:** The existing code structure is correct for Enter key submission. The most likely root cause is either (a) the `isLoading` state from the old code was causing a re-render that interfered with form submission, or (b) browser-native validation is interfering. TASK_01's removal of `isLoading` may fix it. Adding `noValidate` is a safe fallback.

**Acceptance criteria:**
- Pressing Enter in the email field triggers form submission
- Form validation runs before submission (Zod schema validates email)
- No JavaScript errors in console on Enter key press
- Works in all modern browsers (Chrome, Firefox, Safari)

**Validation:**
- `cd frontend && npx tsc --noEmit` — no type errors
- Manual test: click email field, type email, press Enter → form submits

---

### TASK_03: Fix admin table stale data + add empty state + align blocked domains

**File:** `frontend/src/features/admin/ui/RegistrationRequests.tsx`
**Symbol:** `RegistrationRequests` component
**Semantic anchor:** Lines 35-38 — `useQuery` call for registration requests. Lines 97-108 — `DataGrid` JSX.

**File:** `frontend/src/shared/types/formSchemas.ts`
**Symbol:** `BLOCKED_DOMAINS` constant and `registerSchema`
**Semantic anchor:** Lines 3-18 — `BLOCKED_DOMAINS` array and `registerSchema` definition.

**Root cause for stale data:** The global `QueryClient` in `providers.tsx:12` sets `staleTime: 5 * 60 * 1000` (5 minutes). This means if the admin navigates away from the Registration Requests tab and back within 5 minutes, TanStack Query returns cached data without refetching. The `approveMutation` and `rejectMutation` do call `invalidateQueries` on success, but a newly submitted request from another user/browser won't appear until the stale time expires.

#### Change 3a: Add `refetchOnMount: 'always'` to useQuery

File: `frontend/src/features/admin/ui/RegistrationRequests.tsx`, lines 35-38

```typescript
// Before:
const { data: requests = [], isLoading } = useQuery({
  queryKey: ['admin', 'registration-requests'],
  queryFn: getRegistrationRequests,
})

// After:
const { data: requests = [], isLoading } = useQuery({
  queryKey: ['admin', 'registration-requests'],
  queryFn: getRegistrationRequests,
  refetchOnMount: 'always',
})
```

**Rationale:** `refetchOnMount: 'always'` ensures that when the component mounts (admin switches to the tab), TanStack Query always refetches from the server, bypassing the stale cache. This is the correct pattern for admin data that may be modified by other users.

#### Change 3b: Add empty state overlay to DataGrid

File: `frontend/src/features/admin/ui/RegistrationRequests.tsx`

1. Add `Typography` to MUI imports (line 4):
   ```typescript
   import { Box, Chip, Typography } from '@mui/material'
   ```

2. Add the no-rows overlay component before the `RegistrationRequests` function (after line 10):
   ```typescript
   function NoRegistrationRequestsOverlay() {
     return (
       <Typography sx={{ p: 3, textAlign: 'center', color: 'text.secondary' }}>
         No pending registration requests
       </Typography>
     )
   }
   ```

3. Update the `DataGrid` JSX (lines 97-108) to add `slots`:
   ```tsx
   <DataGrid
     rows={rows}
     columns={columns}
     loading={isLoading}
     autoHeight
     pageSizeOptions={[10, 25, 50]}
     initialState={{
       pagination: { paginationModel: { pageSize: 25 } },
     }}
     slots={{ noRowsOverlay: NoRegistrationRequestsOverlay }}
   />
   ```

**Rationale:** MUI X DataGrid v9 supports `slots.noRowsOverlay` for custom empty state rendering. This provides a clear message when no requests exist instead of showing an empty grid.

#### Change 3c: Align BLOCKED_DOMAINS with backend

File: `frontend/src/shared/types/formSchemas.ts`, line 3

```typescript
// Before:
const BLOCKED_DOMAINS = ['tempmail.com', 'throwawaymail.com']

// After:
const BLOCKED_DOMAINS = ['tempmail.com', 'throwaway.email']
```

**Rationale:** Backend config (`src/mkobi/config.py:151`) uses `['tempmail.com', 'throwaway.email']`. The frontend had `'throwawaymail.com'` which doesn't match. This means the frontend was blocking a domain the backend allows, and wasn't blocking `'throwaway.email'` which the backend blocks.

**Acceptance criteria:**
- Admin table always fetches fresh data when the tab is mounted (no stale cache)
- Empty state shows "No pending registration requests" when the table has no rows
- Frontend BLOCKED_DOMAINS matches backend: `['tempmail.com', 'throwaway.email']`
- `approveMutation` and `rejectMutation` still invalidate queries on success (unchanged)
- Other admin components (UserManagement, DashboardManagement) are unaffected

**Validation:**
- `cd frontend && npx tsc --noEmit` — no type errors
- `cd frontend && npm run lint` — no lint errors
- Manual test: submit a registration request → switch to admin panel → Registration Requests tab shows the new request
- Manual test: with no requests → DataGrid shows "No pending registration requests"

---

## Execution Order Summary

| Wave | Task | File(s) | Dependencies |
|------|------|---------|-------------|
| 1 | TASK_01 | `RegisterForm.tsx` | None |
| 1 | TASK_02 | `RegisterForm.tsx` | None (targets same file as TASK_01 — sequential within file) |
| 1 | TASK_03 | `RegistrationRequests.tsx`, `formSchemas.ts` | None |

**Note:** TASK_01 and TASK_02 both modify `RegisterForm.tsx` and must be executed sequentially (TASK_01 first, then TASK_02). TASK_03 modifies different files and could run independently, but all three are grouped in a single sequential wave to avoid conflicts.

---

## Final Validation (All Tasks Complete)

1. `cd frontend && npx tsc --noEmit` — zero type errors
2. `cd frontend && npm run lint` — zero lint errors
3. Manual verification checklist:
   - [ ] Open registration page → enter email → click Submit → button shows spinner + "Sending..." + disabled
   - [ ] Open registration page → enter email → press Enter → form submits (same loading behavior)
   - [ ] Submit a registration request → login as admin → navigate to Registration Requests tab → new request appears
   - [ ] With no pending requests → DataGrid shows "No pending registration requests"
   - [ ] Frontend blocks `throwaway.email` (not `throwawaymail.com`)
   - [ ] Success flow still works: submit → confirmation page
   - [ ] Error flow still works: submit with server error → error page
