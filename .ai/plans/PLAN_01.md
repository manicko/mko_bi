# PLAN_01: Phase 01 — Initial Setup & Test Configuration

## Phase Goal
Establish foundational infrastructure: admin user auto-creation on startup, improved test database configuration with SAVEPOINT isolation, conditional frontend sidebar based on auth state, and password change functionality.

## must_haves
- [ ] Admin user auto-created on application startup via `ensure_admin_user()` in `DatabaseStarter.startup()`
- [ ] Admin credentials configurable via `ADMIN_USERNAME` and `ADMIN_PASSWORD` env vars with safe defaults
- [ ] Admin creation is idempotent — safe to run multiple times without errors or credential updates
- [ ] Test database `async_db_session` fixture uses SAVEPOINT pattern (`session.begin_nested()`) for proper rollback
- [ ] `baseline_data` session-scoped fixture exists for loading reference data once per test session
- [ ] `fast` pytest marker registered in `pyproject.toml` for tests using `Base.metadata.create_all()`
- [ ] Frontend `AppLayout.tsx` conditionally renders `<Sidebar />` only when `user` is authenticated
- [ ] Backend `POST /auth/change-password` endpoint exists and requires current password + new password + confirmation
- [ ] `AuthService.change_password()` method verifies current password, validates new password, updates hash
- [ ] Frontend `ChangePasswordPage.tsx` with form (current password, new password, confirm) and Zod validation
- [ ] `UserProfile.tsx` has "Change password" button navigating to `/profile/change-password`
- [ ] After successful password change, user is redirected to profile page with success message, remains logged in
- [ ] Password validation requires minimum 8 characters (updated from current 6)

---

## Wave 1: Foundation (Independent — Parallel Execution)

### Task 1.1: Admin User Auto-Creation (Backend)

```yaml
wave: 1
depends_on: []
files_modified:
  - src/mkobi/config.py
  - src/mkobi/db/starter.py
autonomous: true
```

**Implementation Steps:**

1. **Add admin credentials to `Settings` in `src/mkobi/config.py`:**
   - Add `admin_username: str = "admin"` field to `Settings` class (after `cors_origins`, before `model_config`)
   - Add `admin_password: str = "admin"` field immediately after `admin_username`
   - These use flat env var names `ADMIN_USERNAME` and `ADMIN_PASSWORD` (consistent with existing flat pattern for simple values like `host`, `port`, `debug`)

2. **Add `ensure_admin_user()` to `DatabaseStarter` in `src/mkobi/db/starter.py`:**
   - Add import: `from mkobi.core.security import hash_password` (already imported in starter via config)
   - Add import: `from mkobi.models.enums import UserRole`
   - Add import: `from mkobi.db.repositories.user_repo import UserRepository`
   - Add import: `from sqlalchemy.exc import IntegrityError`
   - Create method `async def ensure_admin_user(self) -> None:` that:
     a. Gets `admin_username` and `admin_password` from `get_config()`
     b. Creates `UserRepository()` instance
     c. Gets main engine via `self._main_engine`
     d. Opens a new session from the main engine
     e. Calls `user_repo.get_by_email(email=admin_username, db=session)` — if exists, logs and returns (idempotent)
     f. If not exists: calls `user_repo.create(db=session, email=admin_username, password_hash=hash_password(admin_password), role=UserRole.ADMIN.value)`
     g. Commits the session
     h. Handles `IntegrityError` with try/except — logs warning and returns (race condition guard)
     i. Uses `session.begin_nested()` (SAVEPOINT) so failure doesn't rollback the outer transaction

3. **Call `ensure_admin_user()` in `startup()`:**
   - Insert `await self.ensure_admin_user()` after the migration block (after `await self._apply_migrations(main_url)`) and before the test database block (`if self._config.env == EnvironmentEnum.TEST`)

**Acceptance Criteria:**
- `ensure_admin_user()` is idempotent — calling twice creates only one admin
- Admin user has role `admin`
- Admin password is properly bcrypt-hashed
- `IntegrityError` is caught and logged without crashing
- Works with env vars `ADMIN_USERNAME` and `ADMIN_PASSWORD`

**Tests to Run:**
- `pytest tests/ -x -v` (existing tests must pass)

---

### Task 1.2: Test Database Configuration Improvements

```yaml
wave: 1
depends_on: []
files_modified:
  - tests/conftest.py
  - pyproject.toml
autonomous: true
```

**Implementation Steps:**

1. **Update `async_db_session` fixture in `tests/conftest.py`:**
   - Replace the current simple rollback pattern with SAVEPOINT pattern:
   ```python
   @pytest.fixture(scope="function")
   async def async_db_session(async_session_maker):
       async with async_session_maker() as session:
           async with session.begin_nested():
               yield session
               # SAVEPOINT is rolled back automatically when the nested block exits
   ```
   - This ensures each test runs in a SAVEPOINT that rolls back automatically, while the outer transaction remains clean

2. **Add `baseline_data` session-scoped fixture in `tests/conftest.py`:**
   - Add after `async_session_maker` fixture:
   ```python
   @pytest.fixture(scope="session")
   async def baseline_data(setup_test_database):
       """Load minimal reference data once per test session."""
       # This fixture is a placeholder for future reference data loading.
       # Currently ensures the test database is properly initialized.
       yield
   ```

3. **Add `fast` marker to `pyproject.toml`:**
   - In `[tool.pytest.ini_options]` under `markers`, add:
   ```toml
   "fast: marks tests that use Base.metadata.create_all() instead of full migrations"
   ```

**Acceptance Criteria:**
- `async_db_session` uses `session.begin_nested()` SAVEPOINT pattern
- `baseline_data` session-scoped fixture exists
- `fast` marker is registered in `pyproject.toml`
- Existing tests continue to pass with new fixture behavior

**Tests to Run:**
- `pytest tests/ -x -v` (existing tests must pass)

---

### Task 1.3: Frontend Sidebar Conditional Rendering

```yaml
wave: 1
depends_on: []
files_modified:
  - frontend/src/shared/components/Layout/AppLayout.tsx
autonomous: true
```

**Implementation Steps:**

1. **Modify `AppLayout.tsx`:**
   - Import `useAuth` from `../../features/auth/model/useAuth`
   - Call `const { user } = useAuth()` inside the component
   - Wrap `<Sidebar />` with conditional: `{user && <Sidebar />}`

**Acceptance Criteria:**
- Sidebar is not rendered when user is not authenticated (login/register pages)
- Sidebar appears when user is authenticated
- No visual regression in authenticated state

**Tests to Run:**
- `cd frontend && npm run typecheck` (if available)
- `cd frontend && npm run lint` (if available)

---

## Wave 2: Password Change (Depends on Wave 1 Backend Foundation)

### Task 2.1: Backend Password Change Endpoint

```yaml
wave: 2
depends_on: [1.1]
files_modified:
  - src/mkobi/models/auth.py
  - src/mkobi/services/auth_service.py
  - src/mkobi/api/routes/auth.py
autonomous: true
```

**Implementation Steps:**

1. **Add `ChangePasswordRequest` model in `src/mkobi/models/auth.py`:**
   - Add after `RefreshRequest` class:
   ```python
   class ChangePasswordRequest(BaseModel):
       """Change password request model."""

       current_password: str
       new_password: str
       confirm_password: str

       model_config = ConfigDict(
           from_attributes=True,
           json_schema_extra={
               "example": {
                   "current_password": "old_password123",
                   "new_password": "new_secure_password456",
                   "confirm_password": "new_secure_password456",
               }
           },
       )
   ```

2. **Add `change_password()` method to `AuthService` in `src/mkobi/services/auth_service.py`:**
   - Add after `register_request()` method:
   ```python
   async def change_password(
       self,
       user_id: UUID,
       current_password: str,
       new_password: str,
       db: AsyncSession | None = None,
   ) -> bool:
       """Change user password.

       Args:
           user_id: User ID.
           current_password: Current password for verification.
           new_password: New password to set.
           db: Optional database session.

       Returns:
           bool: True if password changed successfully.

       Raises:
           ValueError: If current password is invalid or new password is same as current.
       """
       logger.info("Attempting password change", extra={"user_id": str(user_id)})

       if db is None:
           async with get_session() as db:
               return await self.change_password(user_id, current_password, new_password, db)

       user_obj = await self.user_repo.get_by_email_with_hash(email=current_user.email, db=db)
       if user_obj is None:
           logger.warning("User not found for password change", extra={"user_id": str(user_id)})
           raise ValueError("User not found")

       if not verify_password(current_password, user_obj.password_hash):
           logger.warning("Invalid current password", extra={"user_id": str(user_id)})
           raise ValueError("Current password is incorrect")

       if verify_password(new_password, user_obj.password_hash):
           logger.warning("New password same as current", extra={"user_id": str(user_id)})
           raise ValueError("New password must be different from current password")

       new_hash = hash_password(new_password)
       await self.user_repo.update(user_id, db=db, password_hash=new_hash)
       await db.commit()

       logger.info("Password changed successfully", extra={"user_id": str(user_id)})
       return True
   ```

3. **Add `POST /auth/change-password` endpoint in `src/mkobi/api/routes/auth.py`:**
   - Add import: `ChangePasswordRequest` from `mkobi.models.auth`
   - Add import: `get_current_user_dependency` from `mkobi.api.deps`
   - Add after `get_current_user_info` endpoint:
   ```python
   @router.post(
       "/change-password",
       status_code=status.HTTP_200_OK,
       summary="Change password",
       description="Change current user password. Requires current password verification.",
   )
   async def change_password(
       password_data: ChangePasswordRequest,
       current_user: UserRead = Depends(get_current_user_dependency),
       auth_service=Depends(get_auth_service),
   ) -> dict[str, str]:
       """Change password endpoint.

       Requires valid JWT token and current password verification.

       Args:
           password_data: Password change data (current, new, confirm).
           current_user: Currently authenticated user.
           auth_service: Authentication service.

       Returns:
           dict: Success message.

       Raises:
           HTTPException 400: If new password doesn't match confirmation.
           HTTPException 401: If current password is incorrect.
           HTTPException 422: Validation error.
       """
       if password_data.new_password != password_data.confirm_password:
           logger.warning(
               "Password change failed: confirmation mismatch",
               extra={"user_id": str(current_user.id)},
           )
           raise HTTPException(
               status_code=status.HTTP_400_BAD_REQUEST,
               detail="New password and confirmation do not match",
           )

       try:
           await auth_service.change_password(
               user_id=current_user.id,
               current_password=password_data.current_password,
               new_password=password_data.new_password,
           )
       except ValueError as e:
           logger.warning(
               "Password change failed",
               extra={"user_id": str(current_user.id), "error": str(e)},
           )
           raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
               detail=str(e),
           ) from e

       logger.info(
           "Password changed successfully",
           extra={"user_id": str(current_user.id)},
       )
       return {"message": "Password changed successfully"}
   ```

**Acceptance Criteria:**
- `POST /auth/change-password` requires authentication
- Current password must be verified before change
- New password and confirmation must match
- Returns 400 if confirmation mismatch
- Returns 401 if current password is wrong
- Returns 200 with success message on success
- User remains logged in (token not invalidated)

**Tests to Run:**
- `pytest tests/ -x -v` (existing tests must pass)

---

### Task 2.2: Frontend Password Change Page

```yaml
wave: 2
depends_on: [1.3]
files_modified:
  - frontend/src/shared/types/api.types.ts
  - frontend/src/shared/types/formSchemas.ts
  - frontend/src/features/users/api/userApi.ts
  - frontend/src/features/users/ui/ChangePasswordPage.tsx (NEW)
  - frontend/src/features/users/ui/UserProfile.tsx
  - frontend/src/app/routes.tsx
autonomous: true
```

**Implementation Steps:**

1. **Add `ChangePasswordRequest` interface in `frontend/src/shared/types/api.types.ts`:**
   - Add after `GrantAccessRequest` interface:
   ```typescript
   export interface ChangePasswordRequest {
     current_password: string
     new_password: string
     confirm_password: string
   }
   ```

2. **Add `changePasswordSchema` in `frontend/src/shared/types/formSchemas.ts`:**
   - Add after `grantAccessSchema`:
   ```typescript
   // Change password schema
   export const changePasswordSchema = z
     .object({
       current_password: z.string().min(1, 'Current password is required'),
       new_password: z.string().min(8, 'Password must be at least 8 characters'),
       confirm_password: z.string().min(1, 'Password confirmation is required'),
     })
     .refine((data) => data.new_password === data.confirm_password, {
       message: 'Passwords do not match',
       path: ['confirm_password'],
     })

   export type ChangePasswordFormData = z.infer<typeof changePasswordSchema>
   ```

3. **Add `changePassword()` function in `frontend/src/features/users/api/userApi.ts`:**
   - Add after `deleteAccount`:
   ```typescript
   import type { ChangePasswordRequest } from '../../../shared/types/api.types'

   export async function changePassword(data: ChangePasswordRequest): Promise<void> {
     await axiosInstance.post('/auth/change-password', data)
   }
   ```

4. **Create `frontend/src/features/users/ui/ChangePasswordPage.tsx`:**
   - Create new file with:
   ```tsx
   import { useState } from 'react'
   import { useNavigate } from 'react-router-dom'
   import { Box, Typography, TextField, Button, Alert } from '@mui/material'
   import { useForm } from 'react-hook-form'
   import { zodResolver } from '@hookform/resolvers/zod'
   import { changePasswordSchema, type ChangePasswordFormData } from '../../../shared/types/formSchemas'
   import { changePassword } from '../api/userApi'
   import { toast } from 'react-hot-toast'

   export function ChangePasswordPage() {
     const navigate = useNavigate()
     const [error, setError] = useState<string | null>(null)
     const [isSubmitting, setIsSubmitting] = useState(false)

     const {
       register,
       handleSubmit,
       formState: { errors },
     } = useForm<ChangePasswordFormData>({
       resolver: zodResolver(changePasswordSchema),
     })

     const onSubmit = async (data: ChangePasswordFormData) => {
       try {
         setError(null)
         setIsSubmitting(true)
         await changePassword({
           current_password: data.current_password,
           new_password: data.new_password,
           confirm_password: data.confirm_password,
         })
         toast.success('Password changed successfully')
         navigate('/profile')
       } catch (err) {
         const message = err instanceof Error ? err.message : 'Failed to change password'
         setError(message)
         toast.error(message)
       } finally {
         setIsSubmitting(false)
       }
     }

     return (
       <Box sx={{ p: 3, maxWidth: 500 }}>
         <Typography variant="h4" gutterBottom>
           Change Password
         </Typography>

         {error && (
           <Alert severity="error" sx={{ mb: 2 }}>
             {error}
           </Alert>
         )}

         <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
           <TextField
             label="Current Password"
             type="password"
             {...register('current_password')}
             error={!!errors.current_password}
             helperText={errors.current_password?.message}
             fullWidth
           />
           <TextField
             label="New Password"
             type="password"
             {...register('new_password')}
             error={!!errors.new_password}
             helperText={errors.new_password?.message || 'Minimum 8 characters'}
             fullWidth
           />
           <TextField
             label="Confirm New Password"
             type="password"
             {...register('confirm_password')}
             error={!!errors.confirm_password}
             helperText={errors.confirm_password?.message}
             fullWidth
           />
           <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
             <Button
               variant="contained"
               type="submit"
               disabled={isSubmitting}
             >
               {isSubmitting ? 'Changing...' : 'Change Password'}
             </Button>
             <Button
               variant="outlined"
               onClick={() => navigate('/profile')}
               disabled={isSubmitting}
             >
               Cancel
             </Button>
           </Box>
         </Box>
       </Box>
     )
   }
   ```

5. **Update `UserProfile.tsx` to add "Change password" button:**
   - Add import: `ChangePasswordPage` is not needed, just add a button that navigates
   - Add after the role display box (before the delete account section):
   ```tsx
   <Box sx={{ mt: 4 }}>
     <Button
       variant="outlined"
       onClick={() => navigate('/profile/change-password')}
     >
       Change Password
     </Button>
   </Box>
   ```

6. **Add route in `frontend/src/app/routes.tsx`:**
   - Add import: `import { ChangePasswordPage } from '../features/users/ui/ChangePasswordPage'`
   - Add route after the `/profile` route:
   ```tsx
   <Route
     path="/profile/change-password"
     element={
       <ProtectedRoute>
         <ChangePasswordPage />
       </ProtectedRoute>
     }
   />
   ```

**Acceptance:**
- Change password page accessible at `/profile/change-password`
- Form has three fields: current password, new password, confirm password
- Validation: min 8 chars for new password, confirmation must match
- On success: redirects to `/profile` with toast success message
- On error: shows error message on page
- User remains logged in after password change
- "Change password" button visible on profile page

**Tests to Run:**
- `cd frontend && npm run typecheck` (if available)
- `cd frontend && npm run lint` (if available)

---

## Wave 3: Integration & Verification

### Task 3.1: Integration Testing and Verification

```yaml
wave: 3
depends_on: [1.1, 1.2, 1.3, 2.1, 2.2]
files_modified: []
autonomous: true
```

**Implementation Steps:**

1. **Run full backend test suite:**
   - `pytest tests/ -x -v` — all existing tests must pass
   - Verify no regressions from config changes or starter changes

2. **Run frontend typecheck/lint:**
   - `cd frontend && npm run typecheck` (if available)
   - `cd frontend && npm run lint` (if available)

3. **Run ruff and mypy on backend:**
   - `ruff check src/`
   - `mypy src/`

4. **Verify admin creation manually (optional):**
   - Set `ADMIN_USERNAME=testadmin` and `ADMIN_PASSWORD=TestPass123!` in `.env`
   - Start the application
   - Verify admin user is created in database
   - Restart application — verify no duplicate admin created

5. **Verify password change flow:**
   - Login as any user
   - Navigate to profile page
   - Click "Change password"
   - Enter current password, new password, confirmation
   - Verify success message and redirect to profile
   - Verify user can still access protected routes (token still valid)

**Acceptance Criteria:**
- All existing tests pass
- No ruff or mypy errors
- Admin creation works end-to-end
- Password change flow works end-to-end
- Sidebar hidden on login/register pages

**Tests to Run:**
- `pytest tests/ -x -v`
- `ruff check src/`
- `mypy src/`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run lint`

---

## Execution Order Summary

| Wave | Task | Dependencies | Parallelizable |
|------|------|--------------|----------------|
| 1 | 1.1 Admin User Creation | No | Yes |
| 1 | 1.2 Test DB Config | No | Yes |
| 1 | 1.3 Sidebar Conditional | No | Yes |
| 2 | 2.1 Password Endpoint | 1.1 | Yes (with 2.2) |
| 2 | 2.2 Password Page | 1.3 | Yes (with 2.1) |
| 3 | 3.1 Integration Test | 1.1, 1.2, 1.3, 2.1, 2.2 | No |

**Wave 1** can execute all 3 tasks in parallel.
**Wave 2** can execute both tasks in parallel (backend and frontend are independent).
**Wave 3** runs after all Wave 1 and Wave 2 tasks complete.
