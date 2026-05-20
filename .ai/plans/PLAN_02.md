---
phase: "01 — Frontend Bug Fixes"
description: "Fix 5 confirmed frontend bugs: login password validation, login error display, user menu Profile item, Profile/Admin data display, active menu highlight color"
autonomous: true
depends_on: []
files_modified:
  - frontend/src/shared/types/formSchemas.ts
  - frontend/src/features/auth/ui/LoginForm.tsx
  - frontend/src/shared/api/axiosInstance.ts
  - frontend/src/shared/components/Layout/Header.tsx
  - frontend/src/features/admin/ui/UserManagement.tsx
  - frontend/src/features/users/ui/UserProfile.tsx
  - frontend/src/shared/types/api.types.ts
waves:
  - id: 1
    tasks: [TASK_01, TASK_02, TASK_03]
    parallel: true
  - id: 2
    tasks: [TASK_04, TASK_05]
    parallel: true
---

# PLAN_01: Frontend Bug Fixes

## must_haves

When this phase is complete, ALL of the following must be true:

1. **Bug #1:** Login form accepts any non-empty password (no minimum length validation). Only requirement: password field is not empty.
2. **Bug #2:** Login with wrong credentials shows inline MUI `Alert` with "Invalid login or password" — no redirect, no toast. Error clears when user modifies any field.
3. **Bug #3:** Header dropdown menu shows: Profile (Settings icon) → Divider → Logout (LogoutIcon). "Profile" is removed from top-level NAV_ITEMS.
4. **Bug #4a:** UserProfile page displays Email, Display Name, Role as read-only fields. "Change Password" and "Delete Account" buttons remain. Data is populated (not blank).
5. **Bug #4b:** UserManagement DataGrid has columns: ID, Email, Role, Created. No Status column. No Block action button.
6. **Bug #5:** Active nav item uses green (`success` palette) instead of red (`secondary`). Button text color and bottom border are green.

---

## Wave 1 (Parallel — Independent Files)

### TASK_01: Remove password length validation from login schema

**File:** `frontend/src/shared/types/formSchemas.ts`
**Symbol:** `loginSchema`
**Semantic anchor:** `z.string().min(6, { error: 'Password must be at least 6 characters' })` on line 8

**Change:**
```typescript
// Before (line 8):
password: z.string().min(6, { error: 'Password must be at least 6 characters' }),

// After:
password: z.string().min(1, { error: 'Password is required' }),
```

**Rationale:** Remove client-side minimum length check on login. Server handles actual validation. Registration and change-password schemas are unaffected.

**Acceptance criteria:**
- `loginSchema` validates that password is a non-empty string (min 1 char)
- `registerSchema`, `changePasswordSchema`, `createDashboardSchema`, `updateDashboardSchema`, `grantAccessSchema` are unchanged
- Zod v4 `{ error: '...' }` syntax preserved

**Validation:**
- Run `npx tsc --noEmit` in `frontend/` — no type errors
- Confirm only `loginSchema` password line changed via `git diff`

---

### TASK_02: Fix login error display (interceptor + form)

**Files:**
- `frontend/src/shared/api/axiosInstance.ts` — interceptor fix
- `frontend/src/features/auth/ui/LoginForm.tsx` — error message + clear-on-change

**Semantic anchors:**
- `axiosInstance.ts` line 32-36: the `if (error.response?.status === 401)` block
- `LoginForm.tsx` line 28: `setError('Invalid email or password')` — wrong message
- `LoginForm.tsx` lines 14-20: `useForm` call — needs `control` export

#### Change 2a: Axios interceptor — skip redirect for login endpoint

File: `frontend/src/shared/api/axiosInstance.ts`, lines 31-37

```typescript
// Before:
axiosInstance.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      removeToken()
      toast.error('Session expired. Please login again.')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// After:
axiosInstance.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      removeToken()
      if (error.config?.url?.includes('/auth/login')) {
        return Promise.reject(error)
      }
      toast.error('Session expired. Please login again.')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
```

**Rationale:** The interceptor fires on ALL 401s including login failures. Login POSTs to `/auth/login` (full URL: `/api/v1/auth/login`). The `includes('/auth/login')` check is safe — no other endpoint contains that path segment. When matched, the 401 propagates to the LoginForm's catch handler instead of redirecting.

#### Change 2b: LoginForm — fix error message + add clear-on-change

File: `frontend/src/features/auth/ui/LoginForm.tsx`

Changes:
1. Add `useEffect` import (line 6): `import { useState, useEffect } from 'react'`
2. Add `useWatch` import (line 1 or 2): `import { useWatch } from 'react-hook-form'`
3. Destructure `control` from `useForm` (around line 14-20):
   ```typescript
   const {
     register,
     handleSubmit,
     control,
     formState: { errors },
   } = useForm<LoginFormData>({
     resolver: zodResolver(loginSchema),
   })
   ```
4. Add `useWatch` + `useEffect` after `useForm` call (before `onSubmit`):
   ```typescript
   const watchedFields = useWatch({ control })
   useEffect(() => {
     if (error) setError(null)
   }, [watchedFields.email, watchedFields.password, error, setError])
   ```
5. Fix error message (line 28):
   ```typescript
   // Before:
   setError('Invalid email or password')
   // After:
   setError('Invalid login or password')
   ```

**Acceptance criteria:**
- Login with wrong credentials: inline Alert shows "Invalid login or password", no redirect, no toast
- Login with correct credentials: navigates to `/dashboards` (unchanged)
- Modifying email or password field clears the error Alert
- 401 on non-login endpoints (e.g., expired token on `/auth/me`): still redirects to `/login` with toast

**Validation:**
- `npx tsc --noEmit` in `frontend/` — no type errors
- Manual test: submit login with wrong credentials → Alert appears, no redirect
- Manual test: type in email field after error → Alert disappears

---

### TASK_03: Remove Status column and Block action from UserManagement

**File:** `frontend/src/features/admin/ui/UserManagement.tsx`
**Semantic anchors:**
- Lines 108-113: `is_active` column definition
- Line 148: `is_active: user.is_active` in rows mapping
- Lines 122-135: Block action button in actions column

**Changes:**

1. Remove the `is_active` column definition (lines 108-113):
   ```typescript
   // DELETE this entire column object:
   {
     field: 'is_active',
     headerName: 'Status',
     width: 120,
     valueGetter: (value: boolean) => (value ? 'Active' : 'Blocked'),
   },
   ```

2. Remove the Block `GridActionsCellItem` (lines 122-135):
   ```typescript
   // DELETE this entire element:
   <GridActionsCellItem
     icon={<BlockIcon />}
     label="Block"
     onClick={() => {
       confirmDialog.confirm({
         title: 'Block User',
         message: `Are you sure you want to block ${row.email}?`,
         confirmLabel: 'Block',
         onConfirm: () => {
           toast('Block functionality coming soon')
         },
       })
     }}
   />
   ```

3. Remove `is_active` from rows mapping (line 148):
   ```typescript
   // Before:
   const rows = users.map((user) => ({
     id: user.id,
     email: user.email,
     role: user.role,
     is_active: user.is_active,
     created_at: new Date(user.created_at).toLocaleString(),
   }))

   // After:
   const rows = users.map((user) => ({
     id: user.id,
     email: user.email,
     role: user.role,
     created_at: new Date(user.created_at).toLocaleString(),
   }))
   ```

4. Remove unused imports if no longer needed: `BlockIcon` from `@mui/icons-material` (line 5). Check that `DeleteIcon` is still used — it is, so only remove `Block` from the import.

**Acceptance criteria:**
- DataGrid columns: ID, Email, Role, Created, Actions (Delete only)
- No Status column in the table
- No Block button in the Actions column
- `BlockIcon` import removed (no unused import warnings)

**Validation:**
- `npx tsc --noEmit` in `frontend/` — no type errors, no unused import errors
- Confirm columns array has 5 entries (id, email, role, created_at, actions) via code review

---

## Wave 2 (Parallel — Independent Files)

### TASK_04: Add Profile to user menu + remove from NAV_ITEMS + fix active highlight color

**File:** `frontend/src/shared/components/Layout/Header.tsx`
**Semantic anchors:**
- Line 1: imports — need to add `Divider`, `Settings`
- Line 5: `LogoutIcon` import — keep, add `Settings`
- Lines 14-18: `NAV_ITEMS` array — remove Profile entry
- Lines 58-69: `Button` rendering — change `secondary` to `success`
- Lines 82-93: `Menu` component — add Profile + Divider

**Changes:**

1. Update imports (lines 1, 5-6):
   ```typescript
   // Before line 1:
   import { AppBar, Box, Button, IconButton, Toolbar, Typography, Menu, MenuItem } from '@mui/material'
   // After:
   import { AppBar, Box, Button, IconButton, Toolbar, Typography, Menu, MenuItem, Divider } from '@mui/material'

   // Before line 6:
   import LogoutIcon from '@mui/icons-material/Logout'
   // After:
   import Settings from '@mui/icons-material/Settings'
   import LogoutIcon from '@mui/icons-material/Logout'
   ```

2. Remove Profile from NAV_ITEMS (lines 14-18):
   ```typescript
   // Before:
   const NAV_ITEMS: NavItem[] = [
     { label: 'Dashboards', path: '/dashboards' },
     { label: 'Admin', path: '/admin', roles: ['admin'] },
     { label: 'Profile', path: '/profile' },
   ]

   // After:
   const NAV_ITEMS: NavItem[] = [
     { label: 'Dashboards', path: '/dashboards' },
     { label: 'Admin', path: '/admin', roles: ['admin'] },
   ]
   ```

3. Fix active highlight color — change `secondary` to `success` (lines 60, 65):
   ```typescript
   // Before:
   color={isActive(item.path) ? 'secondary' : 'inherit'}
   // ...
   borderBottomColor: 'secondary.main',

   // After:
   color={isActive(item.path) ? 'success' : 'inherit'}
   // ...
   borderBottomColor: 'success.light',
   ```

4. Add Profile + Divider to Menu (lines 88-93):
   ```typescript
   // Before:
   <Menu
     anchorEl={anchorEl}
     open={Boolean(anchorEl)}
     onClose={handleMenuClose}
     anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
     transformOrigin={{ vertical: 'top', horizontal: 'right' }}
   >
     <MenuItem onClick={handleLogout}>
       <LogoutIcon sx={{ mr: 1, fontSize: 20 }} />
       Logout
     </MenuItem>
   </Menu>

   // After:
   <Menu
     anchorEl={anchorEl}
     open={Boolean(anchorEl)}
     onClose={handleMenuClose}
     anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
     transformOrigin={{ vertical: 'top', horizontal: 'right' }}
   >
     <MenuItem onClick={() => { handleMenuClose(); void navigate('/profile') }}>
       <Settings sx={{ mr: 1, fontSize: 20 }} />
       Profile
     </MenuItem>
     <Divider />
     <MenuItem onClick={handleLogout}>
       <LogoutIcon sx={{ mr: 1, fontSize: 20 }} />
       Logout
     </MenuItem>
   </Menu>
   ```

**Acceptance criteria:**
- "Profile" is NOT visible as a top-level nav button in the header
- Clicking the account icon opens dropdown with: Profile (gear icon) → horizontal rule → Logout (logout icon)
- Clicking Profile navigates to `/profile`
- Active nav button text is green (`success` palette), bottom border is `success.light`
- Inactive nav buttons remain `inherit` (white on dark AppBar)

**Validation:**
- `npx tsc --noEmit` in `frontend/` — no type errors
- Confirm `NAV_ITEMS` has exactly 2 entries (Dashboards, Admin) via code review
- Confirm `Divider` and `Settings` imports present

---

### TASK_05: Investigate and fix UserProfile data display + remove is_active from AdminUser type

**Files:**
- `frontend/src/features/users/ui/UserProfile.tsx` — Bug #4a investigation
- `frontend/src/shared/types/api.types.ts` — remove `is_active` from `AdminUser`

#### Change 5a: Remove `is_active` from AdminUser type

File: `frontend/src/shared/types/api.types.ts`, lines 180-186

```typescript
// Before:
export interface AdminUser {
  id: string
  email: string
  role: UserRole
  is_active: boolean
  created_at: string
}

// After:
export interface AdminUser {
  id: string
  email: string
  role: UserRole
  created_at: string
}
```

**Rationale:** Backend `UserRead` model does not return `is_active`. The field is always `undefined` at runtime, causing the Status column to show "Blocked" for all users. Removing it from the type prevents future misuse.

#### Change 5b: Investigate UserProfile data display

File: `frontend/src/features/users/ui/UserProfile.tsx`

**Current state analysis:**
- `UserProfile` uses `useQuery({ queryKey: ['profile'], queryFn: getProfile, initialData: user })`
- `user` comes from `useAuth()` which populates it from `AuthResponse.user` during login
- `getProfile()` calls `GET /auth/me` — same endpoint that populates the user state
- The component already displays `profile?.email`, `profile?.display_name`, `profile?.role` in read-only format
- "Change Password" and "Delete Account" buttons already present

**Root cause investigation checklist:**
1. Verify `UserProfile.tsx` already has the correct read-only display structure (it does — lines 70-95)
2. Check if the `user` state from `useAuth()` could be `null` on initial render when navigating directly to `/profile`
3. The `initialData: user` in `useQuery` should prevent blank display — but if `user` is `null`, `initialData` is `null`, and the component renders the loading or error state

**Fix:** The component structure is already correct for Bug #4a. The data display issue (if any) is likely caused by the `user` state being null when the component mounts before `useAuth`'s `useEffect` fetches the profile. However, since the `useEffect` in `useAuth` fetches the profile and sets `user`, and the `useQuery` in `UserProfile` also fetches via `getProfile()`, the data should populate correctly. No structural changes needed to `UserProfile.tsx` — the existing code already satisfies Bug #4a requirements.

**If investigation reveals blank data:** The likely cause is that `initialData: user` is `null` on first render. In that case, the `isLoading` check at line 48 would show "Loading..." until the query resolves. This is acceptable behavior — the data will appear once the query completes.

**Acceptance criteria:**
- `AdminUser` type no longer has `is_active` field
- `UserProfile` displays Email, Display Name, Role as read-only (already correct)
- "Change Password" and "Delete Account" buttons present (already correct)
- No TypeScript errors from removing `is_active` (all references removed in TASK_03)

**Validation:**
- `npx tsc --noEmit` in `frontend/` — no type errors
- Confirm `AdminUser` interface has exactly 4 fields: id, email, role, created_at
- Confirm no remaining references to `is_active` in UserManagement.tsx

---

## Execution Order Summary

| Wave | Task | File(s) | Dependencies |
|------|------|---------|-------------|
| 1 | TASK_01 | `formSchemas.ts` | None |
| 1 | TASK_02 | `axiosInstance.ts`, `LoginForm.tsx` | None |
| 1 | TASK_03 | `UserManagement.tsx` | None |
| 2 | TASK_04 | `Header.tsx` | None |
| 2 | TASK_05 | `UserProfile.tsx`, `api.types.ts` | TASK_03 (must remove `is_active` column before removing from type, or do together) |

**Note:** TASK_05 should run after or simultaneously with TASK_03 since both touch `AdminUser` type usage. If TASK_03 removes `is_active` from the DataGrid first, TASK_05's type removal will compile cleanly. If run in the same wave, order within the wave matters: TASK_03 before TASK_05.

**Revised Wave 1 ordering:** TASK_01, TASK_02, TASK_03 → then TASK_05 depends on TASK_03 completing.

---

## Final Validation (All Tasks Complete)

1. `cd frontend && npx tsc --noEmit` — zero type errors
2. `cd frontend && npx eslint src/` — zero lint errors (if eslint configured)
3. Manual verification checklist:
   - [ ] Login with empty password → Zod validation error "Password is required"
   - [ ] Login with wrong credentials → inline Alert "Invalid login or password", no redirect
   - [ ] Type in field after error → Alert disappears
   - [ ] Header shows Dashboards, Admin nav buttons (no Profile)
   - [ ] Account menu: Profile (gear) → Divider → Logout
   - [ ] Active nav button is green, inactive is white
   - [ ] Admin user table: ID, Email, Role, Created columns only (no Status, no Block)
   - [ ] Profile page shows Email, Display Name, Role with Change Password and Delete Account buttons
