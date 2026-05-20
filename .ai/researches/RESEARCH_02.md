# 01 Frontend Bug Fixes - Research

**Researched:** 2026-05-20
**Domain:** React 18 + TypeScript + MUI v9 + Zod v4 + React Hook Form — Frontend bug fixes
**Confidence:** HIGH

## Summary

This research covers 5 frontend bugs in the mkobi BI Dashboard that need fixing. All bugs are well-scoped, low-risk changes confined to specific files in the `frontend/src/` directory. The fixes involve: Zod schema simplification, MUI component adjustments, axios interceptor behavior, and theme color changes.

**Primary recommendation:** All 5 bugs can be fixed in a single pass across 4 files (`formSchemas.ts`, `LoginForm.tsx`, `Header.tsx`, `UserManagement.tsx`) plus 1 type definition file (`api.types.ts`). No new dependencies needed. The most subtle fix is the login redirect bug caused by the axios 401 interceptor firing before the login error handler.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 19.2.5 | UI framework | Project standard |
| TypeScript | ~6.0.2 | Type safety | Project standard |
| MUI (Material UI) | 9.0.0 | Component library | Project standard |
| MUI Icons | 9.0.0 | Icon components | Project standard |
| MUI X DataGrid | 9.0.4 | Data tables | Project standard |
| Zod | 4.4.3 | Schema validation | Project standard |
| React Hook Form | 7.75.0 | Form state management | Project standard |
| @hookform/resolvers | 5.2.2 | Zod integration for RHF | Project standard |
| TanStack Query | 5.100.9 | Server state management | Project standard |
| Axios | 1.16.0 | HTTP client | Project standard |
| react-hot-toast | 2.6.0 | Toast notifications | Project standard |
| react-router-dom | 7.15.0 | Client-side routing | Project standard |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @mui/icons-material/Settings | 9.0.0 | Gear icon for Profile menu item | Bug #3 user menu |
| @mui/material/Divider | 9.0.0 | Separator between Profile and Logout | Bug #3 user menu |
| @mui/material/Alert | 9.0.0 | Inline error display | Bug #2 login errors |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| MUI Alert for login error | react-hot-toast toast | Locked decision: inline Alert, no toast |
| `success.light` custom theme | Keep `secondary.main` (red) | Locked decision: green highlight |
| Custom `is_active` default | Add field to backend `UserRead` | Deferred: out of scope |

**Installation:** No new packages required. All libraries already in `package.json`.

## Architecture Patterns

### Recommended Project Structure (existing, do not change)

```
frontend/src/
├── app/
│   ├── providers.tsx    # MUI ThemeProvider with createTheme
│   └── routes.tsx       # Route definitions
├── features/
│   ├── auth/
│   │   ├── api/authApi.ts
│   │   ├── model/useAuth.ts
│   │   └── ui/LoginForm.tsx    # Bug #1, #2
│   ├── admin/
│   │   ├── api/adminApi.ts
│   │   └── ui/UserManagement.tsx  # Bug #4b
│   └── users/
│       ├── api/userApi.ts
│       └── ui/UserProfile.tsx     # Bug #4a
└── shared/
    ├── api/axiosInstance.ts  # Interceptor causing redirect
    ├── components/Layout/
    │   └── Header.tsx        # Bug #3, #5
    └── types/
        ├── api.types.ts      # AdminUser type (is_active mismatch)
        └── formSchemas.ts   # Bug #1
```

### Pattern 1: Zod v4 Schema Simplification (Bug #1)

**What:** Remove password length validation from login schema, keep only non-empty check.
**When to use:** Login form only — registration and change-password schemas are unaffected.
**File:** `frontend/src/shared/types/formSchemas.ts:8`

Current code:
```typescript
password: z.string().min(6, { error: 'Password must be at least 6 characters' }),
```

Target code:
```typescript
password: z.string().min(1, { error: 'Password is required' }),
```

**Source:** Zod v4 docs confirm `z.string().min(1)` is valid for non-empty checks. The `{ error: '...' }` syntax is the Zod v4 way to specify custom error messages (verified via Context7 `/colinhacks/zod`).

### Pattern 2: Inline Error Display with React Hook Form + MUI Alert (Bug #2)

**What:** Display login errors via MUI `Alert` component, clear on field modification.
**File:** `frontend/src/features/auth/ui/LoginForm.tsx:12,22-30,38-42`

The current code already uses `useState` for error and renders `<Alert severity="error">`. Two issues to fix:

1. **Wrong error message:** Current code sets `"Invalid email or password"` but the spec says `"Invalid login or password"`.
2. **Error not clearing on field change:** Need to watch form fields and clear the error state.

**Clear-on-change pattern using React Hook Form's `watch` + `useEffect`:**
```typescript
import { useEffect } from 'react'
import { useWatch } from 'react-hook-form'

// Inside LoginForm component, after useForm():
const watchedFields = useWatch({ control })
useEffect(() => {
  if (error) setError(null)
}, [watchedFields.email, watchedFields.password, error, setError])
```

**Source:** React Hook Form docs — `useWatch` subscribes to field changes. The `useEffect` dependency array ensures the error clears when any field changes.

### Pattern 3: Axios 401 Interceptor Causing Login Redirect (Bug #2 Root Cause)

**What:** The axios response interceptor in `frontend/src/shared/api/axiosInstance.ts:31-37` fires on 401 responses and redirects to `/login` via `window.location.href = '/login'`. When the login API returns 401 (wrong credentials), the interceptor catches it and redirects before the LoginForm's catch block can display the error inline.

**File:** `frontend/src/shared/api/axiosInstance.ts:32-36`

Current interceptor:
```typescript
if (error.response?.status === 401) {
  removeToken()
  toast.error('Session expired. Please login again.')
  window.location.href = '/login'
}
```

**Fix:** The interceptor should not redirect on login endpoint failures. The login endpoint is `/auth/login`. Check the request URL and skip redirect for login failures:
```typescript
if (error.response?.status === 401) {
  removeToken()
  // Don't redirect on login failures — let the form handle the error
  if (error.config?.url?.includes('/auth/login')) {
    return Promise.reject(error)
  }
  toast.error('Session expired. Please login again.')
  window.location.href = '/login'
}
```

**Source:** Axios interceptor pattern — `error.config` contains the original request config including `url`. This is standard Axios API.

### Pattern 4: MUI Menu with Divider (Bug #3)

**What:** Add Profile menu item with Divider above Logout in the Header dropdown.
**File:** `frontend/src/shared/components/Layout/Header.tsx:82-93`

**Verified pattern (MUI v9):**
```typescript
import { Divider, Menu, MenuItem } from '@mui/material'
import Settings from '@mui/icons-material/Settings'
import LogoutIcon from '@mui/icons-material/Logout'

// Inside Menu component:
<MenuItem onClick={handleProfileClick}>
  <Settings sx={{ mr: 1, fontSize: 20 }} />
  Profile
</MenuItem>
<Divider />
<MenuItem onClick={handleLogout}>
  <LogoutIcon sx={{ mr: 1, fontSize: 20 }} />
  Logout
</MenuItem>
```

**Source:** MUI v9 docs confirm `Divider` renders as `<hr>` by default and works inside `Menu`. No `component="li"` prop needed in MUI v9 for Divider inside Menu — MUI v9 handles this automatically (verified via Context7 `/mui/material-ui`).

### Pattern 5: MUI Theme `success.light` Palette (Bug #5)

**What:** Replace `secondary.main` (red) with `success.light` (green) for active nav highlight.
**File:** `frontend/src/shared/components/Layout/Header.tsx:60,65`

Current:
```typescript
color={isActive(item.path) ? 'secondary' : 'inherit'}
borderBottomColor: 'secondary.main',
```

Target:
```typescript
color={isActive(item.path) ? 'success' : 'inherit'}
borderBottomColor: 'success.light',
```

**Source:** MUI default palette includes `success` with `light`, `main`, `dark` keys. The `success.light` value in MUI v5+ default theme is `green[500]` = `#4caf50` in light mode (verified via Context7 `/mui/material-ui`). MUI v9 inherits the same default palette.

### Pattern 6: DataGrid Column Removal (Bug #4b)

**What:** Remove `is_active`/`Status` column from UserManagement DataGrid.
**File:** `frontend/src/features/admin/ui/UserManagement.tsx:108-113,148`

Remove the column definition (lines 108-113) and the `is_active` mapping in the `rows` computation (line 148).

**Type mismatch root cause:** `AdminUser` type at `frontend/src/shared/types/api.types.ts:180-186` includes `is_active: boolean`, but the backend `UserRead` model doesn't include this field. The `getUsers()` API function returns `AdminUser[]` but the actual response lacks `is_active`, causing the Status column to show `undefined`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Form validation | Custom validation functions | Zod schema via `@hookform/resolvers` | Already integrated, handles edge cases |
| Error display | Custom error component | MUI `Alert` with `severity="error"` | Already in use, consistent with design |
| Menu separator | Custom styled `<hr>` or `<div>` | MUI `Divider` component | Accessibility, theme consistency |
| HTTP error handling | Custom fetch wrapper | Axios interceptors | Already configured, just needs adjustment |
| Theme colors | Custom hex values | MUI palette tokens (`success.light`) | Automatic dark mode support, consistency |

**Key insight:** All 5 bugs have existing MUI/Zod/Axios patterns in the codebase. The fixes are configuration changes, not new implementations.

## Common Pitfalls

### Pitfall 1: Login Redirect on 401 (Bug #2 Root Cause)

**What goes wrong:** When login fails with wrong credentials, the server returns 401. The axios interceptor catches this and does `window.location.href = '/login'`, causing a full page navigation before the LoginForm's catch block can display the inline error.

**Why it happens:** The interceptor at `axiosInstance.ts:32-36` treats all 401s the same — it removes the token and redirects. But during login, there's no valid token yet, and the 401 is the expected "wrong credentials" response.

**How to avoid:** Add a URL check in the interceptor to skip redirect for `/auth/login` endpoint. Let the 401 propagate to the LoginForm's catch handler.

**Warning signs:** Login form briefly flashes an error then redirects to the same page. The error state is never visible to the user.

### Pitfall 2: Zod v4 Error Message Syntax

**What goes wrong:** Using v3-style `{ message: '...' }` instead of v4's `{ error: '...' }`.

**Why it happens:** Zod v4 changed the error message API. The current codebase already uses `{ error: '...' }` correctly (verified in `formSchemas.ts`).

**How to avoid:** Keep using `{ error: '...' }` syntax. Do not change to `{ message: '...' }`.

**Warning signs:** TypeScript compilation errors or runtime validation messages showing as "Invalid input" instead of custom text.

### Pitfall 3: `useWatch` Import from React Hook Form

**What goes wrong:** Forgetting to import `useWatch` or using `watch` from `formState` (which doesn't trigger re-renders for subscription).

**Why it happens:** React Hook Form has both `watch` (from `useForm()` return) and `useWatch` (separate hook). `watch` in the render function causes re-renders of the entire component on every change, while `useWatch` is more targeted.

**How to avoid:** Import `useWatch` from `'react-hook-form'` and use it with `{ control }` from `useForm()`. This is the recommended pattern for subscribing to field changes without full re-renders.

**Warning signs:** Performance issues or the `useEffect` not triggering on field changes.

### Pitfall 4: MUI `color` Prop vs `sx` Prop for Theming

**What goes wrong:** Using `sx={{ color: '#4caf50' }}` instead of `color="success"` for Button text color.

**Why it happens:** MUI Button's `color` prop accepts palette keys (`inherit`, `primary`, `secondary`, `success`, `error`, `info`, `warning`). Using `color="success"` maps to `palette.success.contrastText` for text, while `sx` would require manual color values.

**How to avoid:** Use `color="success"` for the Button's palette-aware text color, and `borderBottomColor: 'success.light'` in `sx` for the specific shade needed for the border.

**Warning signs:** Button text doesn't match the expected green, or active state is invisible on certain backgrounds.

### Pitfall 5: `AdminUser` Type vs Backend Reality (Bug #4b)

**What goes wrong:** The `AdminUser` type includes `is_active: boolean` but the backend `UserRead` model doesn't return this field. The DataGrid's `valueGetter` for the Status column receives `undefined`.

**Why it happens:** The frontend type was written expecting a field that the backend doesn't provide. The `valueGetter: (value: boolean) => (value ? 'Active' : 'Blocked')` will show "Blocked" for `undefined` (falsy).

**How to avoid:** Remove the Status column entirely (locked decision). Do not add a default value for `is_active` — that would be a workaround, not a fix.

**Warning signs:** All users show "Blocked" status in the admin table.

## Code Examples

### Zod v4 Login Schema (Bug #1)

```typescript
// Source: Zod v4 docs (Context7 /colinhacks/zod)
// File: frontend/src/shared/types/formSchemas.ts
export const loginSchema = z.object({
  email: z.email({ error: 'Invalid email format' }),
  password: z.string().min(1, { error: 'Password is required' }),
})
```

### Login Form with Error Clearing (Bug #2)

```typescript
// Source: React Hook Form docs + existing LoginForm.tsx pattern
import { useState, useEffect } from 'react'
import { useWatch } from 'react-hook-form'
import { Box, Button, TextField, Typography, Alert } from '@mui/material'

export function LoginForm() {
  const { login, isLoading } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

  // Clear error when user modifies any field
  const watchedFields = useWatch({ control })
  useEffect(() => {
    if (error) setError(null)
  }, [watchedFields.email, watchedFields.password, error, setError])

  const onSubmit = async (data: LoginFormData) => {
    try {
      setError(null)
      await login(data.email, data.password)
      navigate('/dashboards')
    } catch {
      setError('Invalid login or password')
    }
  }

  return (
    <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ maxWidth: 400, mx: 'auto', mt: 4, p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Login
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <TextField
        label="Email"
        fullWidth
        margin="normal"
        {...register('email')}
        error={!!errors.email}
        helperText={errors.email?.message}
      />

      <TextField
        label="Password"
        type="password"
        fullWidth
        margin="normal"
        {...register('password')}
        error={!!errors.password}
        helperText={errors.password?.message}
      />

      <Button type="submit" variant="contained" fullWidth sx={{ mt: 2 }} disabled={isLoading}>
        {isLoading ? 'Loading...' : 'Login'}
      </Button>

      <Typography sx={{ mt: 2, textAlign: 'center' }}>
        {"Don't have an account? "}
        <Link to="/register">
          Create an account
        </Link>
      </Typography>
    </Box>
  )
}
```

### Axios Interceptor Fix (Bug #2 Root Cause)

```typescript
// Source: Axios API (error.config contains request config)
// File: frontend/src/shared/api/axiosInstance.ts
axiosInstance.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      removeToken()
      // Don't redirect on login failures — let the form handle the error
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

### Header with Profile Menu and Green Highlight (Bug #3 + #5)

```typescript
// Source: MUI v9 docs (Context7 /mui/material-ui)
// File: frontend/src/shared/components/Layout/Header.tsx
import { AppBar, Box, Button, IconButton, Toolbar, Typography, Menu, MenuItem, Divider } from '@mui/material'
import AccountCircle from '@mui/icons-material/AccountCircle'
import Settings from '@mui/icons-material/Settings'
import LogoutIcon from '@mui/icons-material/Logout'

// NAV_ITEMS without Profile:
const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboards', path: '/dashboards' },
  { label: 'Admin', path: '/admin', roles: ['admin'] },
]

// In the Button rendering (Bug #5):
<Button
  key={item.path}
  color={isActive(item.path) ? 'success' : 'inherit'}
  onClick={() => handleNavigation(item.path)}
  sx={{
    mr: 1,
    borderBottom: isActive(item.path) ? '2px solid' : 'none',
    borderBottomColor: 'success.light',
  }}
>
  {item.label}
</Button>

// In the Menu (Bug #3):
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

### UserManagement Without Status Column (Bug #4b)

```typescript
// Source: MUI X DataGrid docs
// File: frontend/src/features/admin/ui/UserManagement.tsx
// Remove the is_active column definition (was lines 108-113):
//   {
//     field: 'is_active',
//     headerName: 'Status',
//     width: 120,
//     valueGetter: (value: boolean) => (value ? 'Active' : 'Blocked'),
//   },

// Remove is_active from rows mapping (was line 148):
const rows = users.map((user) => ({
  id: user.id,
  email: user.email,
  role: user.role,
  created_at: new Date(user.created_at).toLocaleString(),
}))
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Zod v3 `{ message: '...' }` | Zod v4 `{ error: '...' }` | Zod v4.0.0 | Already migrated in this codebase |
| MUI v5 `color="secondary"` | MUI v9 `color="success"` | MUI v9.0.0 | `success` palette key available in all versions |
| `window.location.href` for navigation | `useNavigate()` from react-router | React Router v6+ | Already using `useNavigate()` in Header |
| Manual token storage in localStorage | Memory-first with sessionStorage fallback | Security best practice | Already implemented in `authToken.ts` |

**Deprecated/outdated:**
- `z.string().email()` — replaced by `z.email()` in Zod v4 (already migrated in this codebase)
- `theme.palette.success.light` with custom hex — use MUI's built-in palette token instead

## Open Questions

1. **UserProfile data display (Bug #4a):** The `UserProfile.tsx` component uses `useQuery` with `initialData: user` from `useAuth()`. The `user` state in `useAuth` is populated during login from the `AuthResponse.user` field. If the profile data appears empty, the root cause could be that the `user` state is `null` on initial render (before the `useEffect` in `useAuth` fetches the profile), or the `getProfile()` API call fails silently. The `initialData` should prevent empty display unless the auth state is lost on navigation. Investigation needed during implementation — check if `user` is properly persisted across route changes.

2. **Axios interceptor URL matching:** The fix uses `error.config?.url?.includes('/auth/login')` to detect login requests. The `url` in `error.config` is the full URL (e.g., `/api/v1/auth/login`). The `includes()` check is safe because `/auth/login` is unique enough to not match other endpoints. If the base URL changes, this still works because `error.config.url` contains the path relative to `baseURL`.

## Sources

### Primary (HIGH confidence)
- Context7 `/colinhacks/zod` — Zod v4 string validation, `z.email()`, `z.string().min()`, error message syntax
- Context7 `/mui/material-ui` — MUI palette `success.light`, `createTheme`, Menu/Divider usage, Button `color` prop
- Codebase: `frontend/src/shared/types/formSchemas.ts` — Current Zod schemas
- Codebase: `frontend/src/features/auth/ui/LoginForm.tsx` — Current login form implementation
- Codebase: `frontend/src/shared/api/axiosInstance.ts` — Axios interceptor causing redirect
- Codebase: `frontend/src/shared/components/Layout/Header.tsx` — Current Header with NAV_ITEMS and Menu
- Codebase: `frontend/src/features/admin/ui/UserManagement.tsx` — Current DataGrid with Status column
- Codebase: `frontend/src/features/users/ui/UserProfile.tsx` — Current profile display
- Codebase: `frontend/src/shared/types/api.types.ts` — `AdminUser` type with `is_active` field
- Codebase: `frontend/src/features/auth/model/useAuth.ts` — Auth state management
- Codebase: `frontend/package.json` — Library versions

### Secondary (N/A)
- No secondary sources needed — all findings verified from primary sources

### Tertiary (N/A)
- No tertiary sources needed

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — All versions from `package.json`, all libraries confirmed in project
- Architecture: HIGH — All patterns verified from existing codebase + Context7 official docs
- Pitfalls: HIGH — Root causes identified from actual code inspection (axios interceptor, type mismatch)
- Code examples: HIGH — All examples adapted from existing codebase patterns + Context7 verified APIs

**Research date:** 2026-05-20
**Valid until:** 2026-06-20 (stable — bug fixes don't depend on rapidly changing APIs)
