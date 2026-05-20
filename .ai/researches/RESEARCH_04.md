# 04 Registration Request Fixes - Research

**Researched:** 2026-05-20
**Domain:** React/MUI frontend bug fixes — loading states, form submission, data grid refresh
**Confidence:** HIGH

## Summary

This research covers three bug fixes for the registration request flow: (1) adding a loading indicator to the submit button, (2) fixing Enter key form submission, and (3) ensuring the admin registration requests table refreshes when new requests are created.

All three fixes are straightforward and use existing libraries already in the project. The MUI v9 `Button` component has a built-in `loading` prop (since v6.4.0) that renders a `CircularProgress` spinner and disables the button automatically. The Enter key fix requires wrapping inputs in a `<form>` element with `onSubmit` — the current code already uses `handleSubmit(onSubmit)` from react-hook-form but the `Box` wrapper is not a `<form>`. The admin table refresh issue is caused by the `staleTime: 5 * 60 * 1000` default in the QueryClient — the `RegistrationRequests` component uses `useQuery` with the default staleTime, so switching tabs doesn't trigger a refetch if the data is considered fresh.

**Primary recommendation:** All three fixes are low-risk, use existing APIs, and require minimal code changes. No new dependencies needed.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @mui/material | ^9.0.0 | Button with `loading` prop | Already in project; MUI v9 has built-in `loading` since v6.4.0 |
| @mui/x-data-grid | ^9.0.4 | `slots.noRowsOverlay` for empty state | Already in project; standard MUI X pattern |
| @tanstack/react-query | ^5.100.9 | `refetchOnMount: 'always'` for tab switch refresh | Already in project; standard TanStack Query v5 API |
| react-hook-form | ^7.75.0 | `handleSubmit` + `<form>` onSubmit | Already in project; standard RHF pattern |
| zod | ^4.4.3 | `z.email()` for email validation | Already in project; Zod v4 top-level API |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|--------------|
| @hookform/resolvers | ^5.2.2 | `zodResolver` for RHF+Zod integration | Already in project; connects Zod schema to react-hook-form |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| MUI Button `loading` prop | Manual `CircularProgress` + `disabled` state | More code, reinventing what MUI provides natively |
| `refetchOnMount: 'always'` | `invalidateQueries` on tab change in AdminPanel | Requires lifting state; `refetchOnMount` is simpler and more localized |
| `<form>` wrapper | `onKeyDown` listener for Enter key | Non-standard, doesn't handle other form submission methods |

**Installation:** No new packages needed. All fixes use existing dependencies.

## Architecture Patterns

### Current Registration Flow

```
RegisterForm.tsx → useAuth().registerRequest() → authApi.ts (POST /auth/register-request)
                                                         ↓
                                              auth_service.register_request()
                                                         ↓
                                              RegistrationRequestRepository.create()
                                                         ↓
                                              DB INSERT (registration_requests table)
```

### Current Admin Flow

```
AdminPanel.tsx (Tabs) → RegistrationRequests.tsx → useQuery(getRegistrationRequests)
                                                      → GET /admin/registration-requests
                                                      → repo.get_all()
```

### Pattern 1: MUI Button Loading State

**What:** Use MUI v9 `Button` `loading` prop to show spinner and disable button during async operation.
**When to use:** Any button that triggers an async operation with noticeable delay.
**Example:**
```tsx
// Source: https://mui.com/material-ui/api/button/ (MUI v9 API)
<Button
  type="submit"
  variant="contained"
  fullWidth
  loading={isLoading}
  loadingPosition="start"
>
  {isLoading ? 'Sending...' : 'Submit Request'}
</Button>
```
The `loading` prop automatically:
- Shows a `CircularProgress` indicator (default: `<CircularProgress color="inherit" size={16} />`)
- Disables the button
- Sets `aria-disabled` for accessibility
- Can be customized with `loadingIndicator` and `loadingPosition` props

### Pattern 2: Form Enter Key Submission

**What:** Use `<form>` element with `onSubmit={handleSubmit(onSubmit)}` and `type="submit"` button.
**When to use:** Any form that should submit on Enter key press.
**Example:**
```tsx
// Source: react-hook-form standard pattern
<Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ ... }}>
  <TextField {...register('email')} />
  <Button type="submit" loading={isLoading}>
    Submit
  </Button>
</Box>
```
**Note:** The current code already uses `<Box component="form" onSubmit={handleSubmit(onSubmit)}` — this IS a `<form>` element. The Enter key should already work. The issue may be that the `isLoading` state from `useAuth()` is shared with the login flow, causing the button to be disabled when it shouldn't be, or there may be a z-index/focus issue. Investigation needed during implementation.

### Pattern 3: TanStack Query refetchOnMount

**What:** Use `refetchOnMount: 'always'` on a per-query basis to override the global `staleTime` for data that needs to be fresh when the component mounts.
**When to use:** Tab-based UIs where data should refresh when switching tabs.
**Example:**
```tsx
// Source: TanStack Query v5 API
const { data: requests = [], isLoading } = useQuery({
  queryKey: ['admin', 'registration-requests'],
  queryFn: getRegistrationRequests,
  refetchOnMount: 'always',  // Override global staleTime
})
```
**Why this works:** The global `staleTime` is 5 minutes. When the admin switches to the Registration Requests tab, if the data was fetched within the last 5 minutes, TanStack Query considers it fresh and doesn't refetch. Setting `refetchOnMount: 'always'` on this specific query forces a refetch every time the component mounts, ensuring new requests are visible.

### Pattern 4: DataGrid Empty State Overlay

**What:** Use `slots.noRowsOverlay` to show a custom message when the DataGrid has no rows.
**When to use:** Any DataGrid that can have zero rows.
**Example:**
```tsx
// Source: https://mui.com/x/react-data-grid/overlays/ (MUI X v9)
import { Typography } from '@mui/material'

function NoRowsOverlay() {
  return (
    <Typography sx={{ p: 2, textAlign: 'center' }}>
      No pending registration requests
    </Typography>
  )
}

<DataGrid
  slots={{ noRowsOverlay: NoRowsOverlay }}
  // ...other props
/>
```

### Anti-Patterns to Avoid

- **Conditional `loading` prop:** Don't do `<Button {...(isLoading && { loading: true })}>` — this causes Google Translation crashes. Always use `<Button loading={isLoading}>` where `isLoading` is `true | false | null`.
- **Manual Enter key listeners:** Don't add `onKeyDown` handlers for Enter key — use native `<form>` submission instead.
- **Global staleTime reduction:** Don't reduce the global `staleTime` to fix the refresh issue — this would cause unnecessary refetches everywhere. Use per-query `refetchOnMount` instead.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Button loading state | Manual spinner + disabled logic | MUI `Button` `loading` prop | Handles accessibility, positioning, and edge cases natively |
| Form submission | `onKeyDown` for Enter | `<form>` + `onSubmit` | Native browser behavior, works with all input methods |
| Data refresh on tab switch | Custom event bus or state lifting | `refetchOnMount: 'always'` | TanStack Query handles caching, dedup, and race conditions |
| Empty state message | Conditional rendering outside grid | `slots.noRowsOverlay` | Properly positioned within DataGrid, consistent styling |

**Key insight:** All four problems have well-established solutions in the existing libraries. The fixes are about using the right API, not building new abstractions.

## Common Pitfalls

### Pitfall 1: Shared isLoading State in useAuth

**What goes wrong:** The `useAuth` hook has a single `isLoading` state used for both login and registration. When `registerRequest` is called, it doesn't set `isLoading` to true (unlike `login` which does). The `isLoading` state is only set during `getProfile` on mount and during `login`.
**Why it happens:** Looking at the code, `registerRequest` in `useAuth.ts` is:
```ts
const registerRequest = useCallback(async (email: string) => {
  await apiRegisterRequest(email)
}, [])
```
It does NOT set `isLoading = true` before the call. The `isLoading` in `RegisterForm` comes from `useAuth()` but is never set during registration.
**How to fix:** Add local `isSubmitting` state in `RegisterForm` instead of relying on `useAuth().isLoading`. This is cleaner and more localized.
**Warning signs:** Button shows no loading state during submission even though `isLoading` is passed to `disabled`.

### Pitfall 2: Enter Key Not Working Despite `<form>` Wrapper

**What goes wrong:** The current code already uses `<Box component="form" onSubmit={handleSubmit(onSubmit)}`, which renders as a `<form>` element. The `Button` has `type="submit"`. Enter key should work.
**Why it might not work:** If there's only one input field, some browsers may not submit the form on Enter. Or the `disabled={isLoading}` state might be interfering if `isLoading` is stuck.
**How to fix:** Verify the rendered HTML has a `<form>` element. If Enter still doesn't work with a single input, add `onKeyDown` as a fallback — but this is rare in modern browsers.
**Warning signs:** Clicking the button works but pressing Enter does nothing.

### Pitfall 3: Admin Table Not Refreshing Due to staleTime

**What goes wrong:** The global QueryClient has `staleTime: 5 * 60 * 1000` (5 minutes). When admin navigates to Registration Requests tab, if the data was fetched within the last 5 minutes, TanStack Query returns cached data without refetching.
**Why it happens:** The `RegistrationRequests` component uses `useQuery` with the default options. No `refetchOnMount` override.
**How to fix:** Add `refetchOnMount: 'always'` to the `useQuery` options in `RegistrationRequests.tsx`.
**Warning signs:** New request appears after page refresh but not after tab switch.

### Pitfall 4: Zod v4 API Differences

**What goes wrong:** The current code uses `z.email({ error: 'Invalid email format' })` which is the Zod v3 API. In Zod v4, `z.email()` is the correct top-level API.
**Why it happens:** The project has `zod: ^4.4.3` in package.json but the form schemas use the old v3 method-style API.
**How to fix:** Update to `z.email()` with error messages passed differently in v4. Note: The current code may still work if Zod v4 maintains backward compatibility, but it's using deprecated API.
**Warning signs:** TypeScript warnings or deprecation notices during build.

## Code Examples

### Loading State on Submit Button

```tsx
// Source: MUI v9 Button API (https://mui.com/material-ui/api/button/)
import { Button, CircularProgress } from '@mui/material'

// In RegisterForm.tsx - replace the submit button:
const [isSubmitting, setIsSubmitting] = useState(false)

const onSubmit = async (data: RegisterFormData) => {
  try {
    setError(null)
    setIsSubmitting(true)
    await registerRequest(data.email)
    setSuccess(true)
  } catch (error) {
    // ...error handling
  } finally {
    setIsSubmitting(false)
  }
}

// In the JSX:
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

### Form Enter Key Submission (verify existing)

```tsx
// Source: react-hook-form standard pattern
// Current code already has this pattern - verify it works:
<Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ maxWidth: 400, mx: 'auto', mt: 4, p: 3 }}>
  <TextField
    label="Email"
    fullWidth
    margin="normal"
    {...register('email')}
    error={!!errors.email}
    helperText={errors.email?.message}
  />
  <Button type="submit" variant="contained" fullWidth sx={{ mt: 2 }} loading={isSubmitting}>
    {isSubmitting ? 'Sending...' : 'Submit Request'}
  </Button>
</Box>
```

### Admin Table Auto-Refresh on Tab Switch

```tsx
// Source: TanStack Query v5 API
// In RegistrationRequests.tsx - add refetchOnMount:
const { data: requests = [], isLoading } = useQuery({
  queryKey: ['admin', 'registration-requests'],
  queryFn: getRegistrationRequests,
  refetchOnMount: 'always',  // Force refetch when component mounts (tab switch)
})
```

### DataGrid Empty State

```tsx
// Source: MUI X DataGrid overlays (https://mui.com/x/react-data-grid/overlays/)
import { Typography } from '@mui/material'

function NoRegistrationRequestsOverlay() {
  return (
    <Typography sx={{ p: 3, textAlign: 'center', color: 'text.secondary' }}>
      No pending registration requests
    </Typography>
  )
}

// In the DataGrid component:
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

### Zod v4 Email Validation (align frontend with backend)

```typescript
// Source: Zod v4 API (https://zod.dev/v4)
// In formSchemas.ts - update to Zod v4 API:
const BLOCKED_DOMAINS = ['tempmail.com', 'throwawaymail.com']

export const registerSchema = z.object({
  email: z.email('Invalid email format').refine((email) => {
    const domain = email.split('@')[1]
    return domain && !BLOCKED_DOMAINS.includes(domain)
  }, 'This email domain is not allowed'),
})

// Note: Backend uses EmailStr from Pydantic which is more permissive than z.email().
// The backend also checks blocked_domains from config (default: ["tempmail.com", "throwaway.email"]).
// Frontend BLOCKED_DOMAINS should match backend config.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `z.string().email()` | `z.email()` | Zod v4 (2025) | Top-level API, better tree-shaking |
| `LoadingButton` from `@mui/lab` | `Button` with `loading` prop | MUI v6.4.0 (2024) | No extra lab dependency needed |
| `z.email()` with string param | `z.email()` with object param | Zod v4 | Error messages passed as object property |

**Deprecated/outdated:**
- `z.string().email()` — deprecated in Zod v4, use `z.email()` instead
- `LoadingButton` from `@mui/lab` — removed in MUI v6.4.0, use `Button` `loading` prop

## Open Questions

1. **Enter key submission root cause**
   - What we know: The current code already uses `<Box component="form">` with `onSubmit={handleSubmit(onSubmit)}` and `Button type="submit"`. This should work for Enter key.
   - What's unclear: Why Enter key doesn't submit. Could be a browser-specific issue with single-input forms, or the `disabled` state interfering.
   - Recommendation: During implementation, first verify the rendered HTML. If the `<form>` element is present and Enter still doesn't work, investigate focus management or add a temporary `onKeyDown` listener for debugging.

2. **Blocked domains mismatch**
   - What we know: Frontend has `BLOCKED_DOMAINS = ['tempmail.com', 'throwawaymail.com']` in formSchemas.ts. Backend config has `blocked_domains: ["tempmail.com", "throwaway.email"]` in config.py.
   - What's unclear: Is `'throwawaymail.com'` vs `'throwaway.email'` intentional or a bug?
   - Recommendation: Align frontend BLOCKED_DOMAINS with backend config during implementation. This is a separate concern from the three main fixes but should be noted.

3. **isLoading state management**
   - What we know: `useAuth().isLoading` is shared across login, registration, and profile fetch. The `registerRequest` function doesn't set `isLoading = true`.
   - What's unclear: Whether the current `disabled={isLoading}` on the RegisterForm button ever evaluates to `true` during registration.
   - Recommendation: Use local `isSubmitting` state in `RegisterForm` instead of relying on `useAuth().isLoading`. This is cleaner and avoids side effects.

## Sources

### Primary (HIGH confidence)
- MUI v9 Button API — https://mui.com/material-ui/api/button/ — `loading`, `loadingIndicator`, `loadingPosition` props
- MUI X DataGrid Overlays — https://github.com/mui/mui-x/blob/master/docs/data/data-grid/overlays/overlays.md — `slots.noRowsOverlay` pattern
- TanStack Query v5 API — https://github.com/tanstack/query/blob/main/query/packages/query-core/src/queryObserver.ts — `refetchOnMount` behavior with `staleTime`
- Zod v4 API — https://zod.dev/v4 — `z.email()` top-level API, deprecated `z.string().email()`

### Secondary (MEDIUM confidence)
- MUI v6.4.0 LoadingButton migration — https://github.com/mui/material-ui/blob/master/docs/data/material/migration/upgrade-to-v6/upgrade-to-v6.md — LoadingButton → Button `loading` prop
- TanStack Query v5 initial data + staleTime — https://github.com/tanstack/query/blob/main/docs/framework/react/guides/initial-query-data.md — `staleTime` default behavior

### Tertiary (LOW confidence)
- None — all findings verified with official documentation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — All libraries already in project, APIs verified with official docs
- Architecture: HIGH — Patterns verified with Context7 and official documentation
- Pitfalls: MEDIUM — Some findings based on code analysis (shared isLoading, Enter key) that need runtime verification

**Research date:** 2026-05-20
**Valid until:** 30 days (stable APIs — MUI v9, TanStack Query v5, Zod v4 are all stable releases)
