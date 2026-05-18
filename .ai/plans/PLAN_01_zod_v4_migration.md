---
wave: 1
depends_on: []
files_modified:
  - frontend/src/shared/types/formSchemas.ts
autonomous: true
---

# Plan 01.1: Zod v4 Schema Migration

## Goal
Migrate all Zod schemas in `formSchemas.ts` from deprecated v3 syntax to Zod v4 syntax, ensuring form validation works correctly with the installed `zod@4.4.3`.

## must_haves
- [ ] All `z.string().email()` replaced with `z.email()`
- [ ] All `z.string().uuid()` replaced with `z.uuid()`
- [ ] All `{ message: "..." }` replaced with `{ error: "..." }` in `.min()`, `.max()`, `.refine()`
- [ ] All existing type exports (`LoginFormData`, `RegisterFormData`, etc.) preserved
- [ ] No behavioral changes to validation logic

## Tasks

### Task 1: Update login and register schemas
In `frontend/src/shared/types/formSchemas.ts`:
- Line 7: `z.string().email('Invalid email format')` → `z.email({ error: 'Invalid email format' })`
- Line 16-17: `z.string().email('Invalid email format')` → `z.email({ error: 'Invalid email format' })`
- Line 21: `{ message: 'This email domain is not allowed' }` → `{ error: 'This email domain is not allowed' }`

### Task 2: Update password validation messages
In `frontend/src/shared/types/formSchemas.ts`:
- Line 8: `z.string().min(6, 'Password must be at least 6 characters')` → `z.string().min(6, { error: 'Password must be at least 6 characters' })`
- Line 53: `z.string().min(8, 'Password must be at least 8 characters')` → `z.string().min(8, { error: 'Password must be at least 8 characters' })`
- Line 52: `z.string().min(1, 'Current password is required')` → `z.string().min(1, { error: 'Current password is required' })`
- Line 54: `z.string().min(1, 'Password confirmation is required')` → `z.string().min(1, { error: 'Password confirmation is required' })`

### Task 3: Update dashboard schema messages
In `frontend/src/shared/types/formSchemas.ts`:
- Line 28: `z.string().min(1, 'Dashboard name is required').max(100, 'Dashboard name is too long')` → `z.string().min(1, { error: 'Dashboard name is required' }).max(100, { error: 'Dashboard name is too long' })`
- Line 29: `z.string().max(500, 'Description is too long')` → `z.string().max(500, { error: 'Description is too long' })`
- Line 36: same pattern for update schema `.min(1, ...)` and `.max(100, ...)`
- Line 37: `.max(500, ...)`

### Task 4: Update UUID and refine schemas
In `frontend/src/shared/types/formSchemas.ts`:
- Line 44: `z.string().uuid('Invalid user ID')` → `z.uuid({ error: 'Invalid user ID' })`
- Line 55-57: `.refine((data) => data.new_password === data.confirm_password, { message: 'Passwords do not match', path: ['confirm_password'] })` → `{ error: 'Passwords do not match', path: ['confirm_password'] }`

## Validation
- Run `npx tsc --noEmit` in `frontend/` to verify no type errors
- Verify all `z.infer<typeof schema>` types still resolve correctly
- Confirm no remaining `z.string().email()` or `{ message:` patterns in formSchemas.ts

## Acceptance Criteria
- [ ] All schemas use Zod v4 syntax
- [ ] TypeScript compilation passes
- [ ] No deprecated Zod v3 patterns remain
