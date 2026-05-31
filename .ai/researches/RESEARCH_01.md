# 01 Admin User Password Reset - Research

**Researched:** 2026-05-31
**Domain:** Admin password reset flow with force password change — FastAPI backend + React frontend
**Confidence:** HIGH

## Summary

This research covers the implementation of an admin-triggered user password reset feature for the mkobi BI Dashboard system. The phase has two deliverables: (1) a single POST endpoint that atomically generates a temporary password, hashes it, saves it, and returns it to the admin; (2) a force-password-change flow where the user is redirected to change their password on next login.

The backend follows Clean Architecture strictly — new endpoint in `admin.py`, logic in `auth_service.py` (not `user_service.py`, since password operations are owned by AuthService), changes to `User` SQLAlchemy model, Pydantic schemas, and an Alembic migration for the new `force_password_change` column. The frontend follows Feature-Sliced Design — the existing `UserManagement.tsx` gains a "Reset Password" action, the existing `ConfirmDialog` + `useConfirmDialog` pattern is reused for Screen 1, a new "temp password result" dialog is Screen 2, and the existing `ChangePasswordPage` is extended with a "force" mode using a `force` prop/route param.

**Primary recommendation:** Add `POST /api/v1/admin/users/{user_id}/reset-password` endpoint — atomic generate+hash+save, return `{ message, user_id, temp_password }` with HTTP 200. Add `force_password_change` boolean column to `users` table via Alembic migration. Extend `TokenWithUser` response with `must_change_password` field. On frontend, add a "Reset Password" button to each user row in `UserManagement.tsx`, reuse `ConfirmDialog` for the confirmation step, show a new `ResetPasswordResultDialog` with copy-to-clipboard, and extend `ChangePasswordPage` with force mode (disabled cancel, informational banner, clears the flag on success).

## Standard Stack

No new libraries are needed. All required tools already exist in the project:

### Core (existing, no changes)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | current | API framework | Existing project standard |
| SQLAlchemy 2.0 | current | Async ORM | Existing project standard |
| Pydantic v2 | current | Validation models | Existing project standard |
| bcrypt | current | Password hashing (12 rounds) | Used by `hash_password()` in `security.py` |
| secrets | stdlib | Cryptographic random generation | Python standard library, CSPRNG |
| Alembic | current | DB migrations | Existing project standard |
| React 18+ | current | Frontend framework | Existing project standard |
| MUI (Material UI) | current | UI component library | ConfirmDialog, Dialog, Button all from MUI |
| react-hot-toast | current | Toast notifications | Existing project standard, used in UserManagement |
| TanStack Query | current | Server state management | Existing project standard |
| React Hook Form + Zod | current | Form validation | Existing project standard |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `secrets` module for temp password | `random` module | `random` is not cryptographically secure — rejected |
| String-based temp password (8 chars, letters+digits) | `secrets.token_urlsafe(16)` | Locks图案 decided: must pass Pydantic password validation (min 8 chars + letter + digit). Token-based passwordswork but don't match the spec's UX pattern. ANSSI-compliant custom generation chosen instead. |
| New `force_password_change` DB column | Reuse `is_active` flag | Decided: new column. Semantic clarity — `is_active` is for account status, `force_password_change` is for auth flow. No coupling. |
| New `PasswordResetService` extend ` | AuthService. | Password ops already live in `AuthService` (`change_password` method). Adding `reset_password_admin` follows existing pattern. No new service file needed. |

**Installation:** No new packages required.

```bash
# Nothing to add — all dependencies already installed
```

## Architecture Patterns

### Recommended Backend File Changes

```
src/mkobi/
├── api/routes/
│   └── admin.py                    # ADD: POST /users/{user_id}/reset-password endpoint
├── services/
│   └── auth_service.py             # ADD: reset_password_admin() method to AuthService
├── db/
│   ├── models/
│   │   └── user.py                 # ADD: force_password_change column to User model
│   └── repositories/
│       └── user_repo.py            # ADD: update_force_password_change() or use existing update()
├── models/
│   ├── auth.py                     # ADD: must_change_password to TokenWithUser OR add to UserRead
│   └── user.py                     # UPDATE: UserRead to include force_password_change field
├── utils/
│   └── validators.py               # Already has validate_password_or_raise() — reuse
└── interfaces/
    ├── repository_interfaces.py    # ADD: method to IUserRepository (if new query needed)
    └── service_interfaces.py       # ADD: reset_password_admin() to IAuthService

alembic/versions/
└── xxxx_add_force_password_change_to_users.py  # NEW: Alembic migration
```

### Recommended Frontend File Changes

```
frontend/src/
├── features/
│   ├── admin/
│   │   ├── api/
│   │   │   └── adminApi.ts         # ADD: resetUserPassword(userId) function
│   │   └── ui/
│   │       ├── UserManagement.tsx  # ADD: Reset Password button + result dialog integration
│   │       └── ResetPasswordResultDialog.tsx  # NEW: Screen 2 — shows temp password + copy
│   ├── users/
│   │   └── ui/
│   │       └── ChangePasswordPage.tsx  # UPDATE: force mode prop, disabled cancel, banner
│   └── auth/
│       └── model/
│           └── useAuth.ts          # UPDATE: handle must_change_password after login
├── shared/
│   ├── types/
│   │   └── api.types.ts            # UPDATE: UserProfile or AuthResponse with must_change_password
│   │   └── formSchemas.ts          # UPDATE: force mode schema (no current_password needed)
│   └── components/
│       └── ConfirmDialog.tsx       # NO CHANGE — reused as-is for Screen 1
```

### Pattern 1: Atomic Password Reset Endpoint

**What:** Single POST endpoint that generates, hashes, and saves in one operation, then returns the plaintext temp password. Follows the existing approve-registration pattern in `admin.py`.

**When to use:** Always for admin password resets.

**Backend code example (from existing codebase patterns in `admin.py` + `auth_service.py`):**

```python
# In src/mkobi/api/routes/admin.py
import string

@router.post(
    "/users/{user_id}/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset user password (admin)",
    description="Generates a temporary password, sets force_password_change flag. Admin only.",
    dependencies=[Depends(require_admin_role)],
)
async def reset_user_password_admin_endpoint(
    user_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, Any]:
    """Reset user password and return temporary password."""
    logger.info("Admin: resetting password for user: id=%s, admin=%s", user_id, current_user.email)
    try:
        result = await auth_service.reset_password_admin(
            user_id=user_id,
            admin_user_id=current_user.id,
            db=db,
        )
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error resetting user password: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error resetting user password",
        ) from e
```

```python
# In src/mkobi/services/auth_service.py — add method to AuthService class
def _generate_temp_password(self, length: int = 8) -> str:
    """Generate a cryptographically secure 8-char password with letters + digits.
    
    Ensures at least one letter and one digit. Used up to 3 attempts
    to produce a password passing Pydantic validation.
    """
    alphabet = string.ascii_letters + string.digits
    for attempt in range(3):
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        if re.search(r'[a-zA-Z]', password) and re.search(r'\d', password):
            return password
    # Fallback (astronomically unlikely to reach): force letter+digit
    password = secrets.choice(string.ascii_letters) + secrets.choice(string.digits)
    password += ''.join(secrets.choice(alphabet) for _ in range(length - 2))
    return ''.join(random.sample(password, len(password)))  # shuffle


async def reset_password_admin(
    self,
    user_id: UUID,
    admin_user_id: UUID,
    db: AsyncSession,
) -> dict[str, Any] | None:
    """Admin-triggered password reset.
    
    Generates temp password, hashes it, saves to user record,
    sets force_password_change flag.
    
    Returns:
        dict with message, user_id, temp_password on success.
        None if user not found.
        
    Raises:
        ValueError: If admin resets own password (policy: prevent self-reset).
    """
    logger.info("Admin password reset: user_id=%s, admin_id=%s", user_id, admin_user_id)
    
    # Policy: prevent admin from resetting own password
    if user_id == admin_user_id:
        logger.warning("Admin attempted self-password-reset: %s", admin_user_id)
        raise ValueError("Admin cannot reset own password")
    
    user_obj = await self.user_repo.get_with_hash(user_id, db)
    if user_obj is None:
        logger.warning("User not found for password reset: %s", user_id)
        return None
    
    temp_password = self._generate_temp_password()
    password_hash = hash_password(temp_password)
    
    # Atomic update: new hash + force flag
    await self.user_repo.update(
        id=user_id,
        db=db,
        password_hash=password_hash,
        force_password_change=True,
    )
    await db.commit()
    
    logger.info("Password reset successful: user_id=%s", user_id)
    return {
        "message": "Password reset successfully",
        "user_id": str(user_id),
        "temp_password": temp_password,
    }
```

### Pattern 2: Force Password Change on Login

**What:** When `force_password_change` is true on the user record, the login response includes `must_change_password: true`. The frontend intercepts this and redirects to `/profile/change-password?force=true` instead of `/dashboards`.

**Where:**  
- Backend: `auth_service.py` → `login_user()` method already returns `UserRead` in the `TokenWithUser` response. Must add `force_password_change` to `UserRead` or include it in the login response.  
- Frontend: `useAuth.ts` → `login()` callback checks for `must_change_password` and redirects accordingly.

**Backend example (extending existing login response):**

```python
# In auth_service.py — modify login_user() return
# The user_read is built from user_obj; add force_password_change to UserRead Pydantic model
user_read = UserRead.model_validate(user_obj)  # will include force_password_change if added to model
return {
    "access_token": ...,
    "token_type": "bearer",
    "user": user_read,  # user_read.must_change_password maps from force_password_change column
}
```

```python
# In src/mkobi/models/user.py — add field to UserRead
class UserRead(UserBase):
    id: UUID
    created_at: datetime
    force_password_change: bool = False  # NEW FIELD

    @computed_field
    @property
    def must_change_password(self) -> bool:
        """Alias for frontend convenience."""
        return self.force_password_change
```

**Frontend example (extending `useAuth.ts`):**

```typescript
// In useAuth.ts — modify login callback
const login = useCallback(async (email: string, password: string) => {
  setIsLoading(true)
  try {
    const response = await apiLogin(email, password)
    setToken(response.access_token)
    setUser(response.user)
    
    // Force password change redirect
    if (response.user.must_change_password) {
      void navigate('/profile/change-password?force=true')
    } else {
      void navigate('/dashboards')
    }
  } catch (error) {
    removeToken()
    setUser(null)
    throw error
  } finally {
    setIsLoading(false)
  }
}, [])
```

### Pattern 3: ChangePasswordPage Force Mode

**What:** When accessed with `?force=true`, the `ChangePasswordPage` hides/disables Cancel, shows an informational banner, and removes the "Current Password" field (user enters temp password as old password — but the backend `change_password` endpoint still needs `current_password`). Actually, per user decisions: the force flow uses the same standard fields (old + new + confirm), but cancel is disabled and a message is shown.

**Implementation approach:**

```tsx
// ChangePasswordPage.tsx — add force mode
import { useSearchParams } from 'react-router-dom'

export function ChangePasswordPage() {
  const [searchParams] = useSearchParams()
  const isForceMode = searchParams.get('force') === 'true'
  
  // ... existing form setup ...

  const handleCancel = () => {
    if (!isForceMode) {
      void navigate('/profile')
    }
  }

  return (
    <Box sx={{ p: 3, maxWidth: 400, mx: 'auto' }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Change Password
      </Typography>
      
      {isForceMode && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Password change is required. Please set a new password to continue.
        </Alert>
      )}
      
      {/* ... existing form fields unchanged ... */}
      
      <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
        <Button variant="contained" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Changing...' : 'Change Password'}
        </Button>
        <Button
          variant="outlined"
          onClick={handleCancel}
          disabled={isSubmitting || isForceMode}
        >
          Cancel
        </Button>
      </Box>
    </Box>
  )
}
```

**Key detail:** The existing `POST /auth/change-password` endpoint already validates `current_password`. In force mode, the temp password IS the current password. The backend doesn't need changes for this flow — regular password change works. After successful password change, the backend should clear `force_password_change` flag — add this to `auth_service.change_password()`.

```python
# In auth_service.py — change_password() method, after successful change
# Add: clear force_password_change flag
await self.user_repo.update(user_id, db, password_hash=password_hash, force_password_change=False)
```

### Pattern 4: Admin Result Dialog (Screen 2)

**What:** After successful reset, Screen 2 displays the temp password with Copy and Close buttons. Uses `navigator.clipboard.writeText()` + `react-hot-toast` for "Copied" feedback.

```tsx
// New file: frontend/src/features/admin/ui/ResetPasswordResultDialog.tsx
import { useState } from 'react'
import {
  Dialog, DialogTitle, DialogContent, DialogContentText,
  DialogActions, Button, TextField, Box,
} from '@mui/material'
import ContentCopyIcon from '@mui/icons-material/ContentCopy'
import { toast } from 'react-hot-toast'

interface ResetPasswordResultDialogProps {
  open: boolean
  tempPassword: string
  userEmail: string
  onClose: () => void
}

export function ResetPasswordResultDialog({
  open, tempPassword, userEmail, onClose,
}: ResetPasswordResultDialogProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(tempPassword)
      setCopied(true)
      toast.success('Copied')
      setTimeout(() => setCopied(false), 3000)
    } catch {
      toast.error('Failed to copy')
    }
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Password Reset</DialogTitle>
      <DialogContent>
        <DialogContentText sx={{ mb: 2 }}>
          Password for <strong>{userEmail}</strong> has been reset.
          Copy the temporary password and share it securely.
        </DialogContentText>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <TextField
            value={tempPassword}
            fullWidth
            InputProps={{ readOnly: true }}
            size="small"
          />
          <Button
            variant="outlined"
            onClick={handleCopy}
            startIcon={<ContentCopyIcon />}
          >
            {copied ? 'Copied' : 'Copy'}
          </Button>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} variant="contained">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  )
}
```

### Anti-Patterns to Avoid

- **Don't put password reset logic in `user_service.py`** — Password operations (hash, verify, change, reset) all live in `auth_service.py`. UserService handles role/name/email changes.
- **Don't skip the force_password_change flag** — Setting a new password without the flag means the user never has to change the temp password, creating a security gap.
- **Don't use `secrets.token_urlsafe()` for the temp password** — It produces characters like `-_` which may not match the exact pattern specified. Use `secrets.choice()` from `string.ascii_letters + string.digits` for 8-char passwords.
- **Don't log the temp password** — The spec explicitly says never log `temp_password` in application logs. The existing approve-registration endpoint returns it in the response body only (which is acceptable with HTTPS).
- **Don't create a separate Pydantic model for the reset** — No input body is needed (user_id is in the path). The response reuses the `dict[str, Any]` pattern already used by approve/reject registration endpoints.
- **Don't add auth-specific logic to ConfirmDialog** — ConfirmDialog is generic. ResetPasswordResultDialog is a separate component for the temp password display.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Password hashing | Manual hashlib/bcrypt | `hash_password()` from `core/security.py` | Already handles bcrypt with 12 rounds + 72-byte truncation |
| Password validation | Custom regex checks | `validate_password_or_raise()` from `utils/validators.py` | Enforces length + digit + letter requirements consistently |
| Temp password generation | `random.choice()` or custom charset | `secrets.choice()` from `string.ascii_letters + string.digits` | CSPRNG, no bias |
| Confirmation dialog | New custom modal | `ConfirmDialog` + `useConfirmDialog()` hook | Already used for delete in UserManagement |
| Toast notifications | Inline alerts or `window.alert()` | `react-hot-toast` (`toast.success`/`toast.error`) | Already used throughout the codebase |
| DB session management | Manual session creation | `get_db_dedeendency` from FastAPI | Existing pattern ensures proper cleanup |
| Repo query for user+hash | New raw SQL query | `user_repo.get_with_hash()` | Already used by `change_password()` |

**Key insight:** Almost every building block for this feature already exists in the codebase. The `change_password()` method in `AuthService` is a near-template for `reset_password_admin()` — it fetches user with hash, verifies, hashes new, updates, commits. The admin reset flow is simpler: no current password verification needed.

## Common Pitfalls

### Pitfall 1: Forgetting to Clear force_password_change After Password Change

**What goes wrong:** Admin resets user's password, sets `force_password_change=true`, but when the user changes password normally, the flag stays true forever. User gets stuck in a loop.

**Why it happens:** The existing `change_password()` method in `auth_service.py` only updates `password_hash`, doesn't clear the flag.

**How to avoid:** Add `force_password_change=False` to the `update()` call in `change_password()`.

**Warning signs:** Users reporting they can never get past the change-password screen.

### Pitfall 2: Admin Self-Reset Creates Lockout

**What goes wrong:** Admin resets their own password via the UI, gets a temp password in the dialog, but may not copy it quickly. If the session expires, they're locked out with a temp password they may not remember.

**Why it happens:** No guard against self-targeting the reset endpoint.

**How to avoid:** Add a check in `reset_password_admin()`: if `user_id == admin_user_id`, raise `ValueError("Admin cannot reset own password")`. The endpoint should return HTTP 400.

**Warning signs:** If the admin has users in the system and no other admin exists, self-reset is particularly dangerous.

### Pitfall 3: Temp Password Doesn't Meet Validation Requirements

**What goes wrong:** Generated 8-char password is all letters (no digits), so when the user later tries to set it as their "current password" and set a new password, the current password technically passes login but the flow feels wrong. More critically, if `validate_password_or_raise()` is called on the temp password during generation, repeated attempts waste resources.

**Why it happens:** Random selection from `ascii_letters + digits` can produce all-letter or all-digit strings.

**How to avoid:** `_generate_temp_password()` checks for at least one letter and one digit character. Up to 3 re-roll attempts, with a forced fallback on the 3rd. This matches the user decision: "up to 3 generation attempts."

**Warning signs:** Login fails because temp password wasn't properly validated (unlikely but possible).

### Pitfall 4: Race Condition Between Password Change and force_password_change Clear

**What goes wrong:** Two concurrent requests — password reset and password change — could leave the flag in an inconsistent state.

**Why it happens:** `force_password_change` is in the same table as `password_hash`, and SQLAlchemy's `update()` uses optimistic locking by default.

**How to avoid:** The `change_password()` method already does: get user with hash → verify → update hash + force flag → commit. This is a single transaction. Since `get_with_hash` does a SELECT and the update follows in the same session, PostgreSQL's row-level locking handles this. No additional locking needed for this use case.

### Pitfall 5: LoginForm Navigation Override Suppresses Normal Redirect

**What goes wrong:** After login, if `must_change_password` is true but the navigate call fires before the state update completes, the user could briefly see `/dashboards`.

**Why it happens:** React state updates are batched but `navigate` is synchronous.

**How to avoid:** Call `navigate()` directly in the `login()` callback (which already awaits the API call), not in a `useEffect`. The existing `LoginForm.tsx` already navigates after `await login()`. The `useAuth.login()` callback must handle the redirect before returning control.

**Recommendation:** Handle the redirect **inside** `useAuth.login()` rather than in `LoginForm.tsx`. Pass `navigate` to the login function or handle it via an auth state effect.

### Pitfall 6: Alembic Migration For `force_password_change` — Nullable vs Default False

**What goes wrong:** Adding a non-nullable column without a default to an existing table with data will fail.

**Why it happens:** PostgreSQL requires a value for existing rows when adding a `NOT NULL` column without a default.

**How to avoid:** Define the column with `server_default=text("false")` and `nullable=False` in both the SQLAlchemy model AND the Alembic migration. Use `sa.Column('force_password_change', sa.Boolean(), nullable=False, server_default=sa.false())` in the migration.

## Code Examples

### Adding force_password_change to User Model

```python
# Source: Existing pattern from src/mkobi/db/models/user.py
class User(Base):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_role", "role"),)

    # ... existing columns unchanged ...

    # NEW COLUMN — add after is_active
    force_password_change: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
```

### Alembic Migration Skeleton

```python
"""Add force_password_change to users

Revision ID: <generated>
Revises: <previous>
Create Date: 2026-05-31

"""
from alembic import op
import sqlalchemy as sa

revision = '<generated>'
down_revision = '<previous>'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'force_password_change',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column('users', 'force_password_change')
```

### Extending UserRead with force_password_change

```python
# Source: src/mkobi/models/user.py — extend existing UserRead
class UserRead(UserBase):
    id: UUID
    created_at: datetime
    force_password_change: bool = False  # NEW — maps from DB column

    # Existing display_name computed_field stays unchanged

    model_config = ConfigDict(from_attributes=True, ...)
```

### AuthService change_password — Clear Flag

```python
# Source: Modify existing change_password() in auth_service.py
# Change this line (around line 498):
# FROM:
await self.user_repo.update(user_id, db, password_hash=password_hash)
# TO:
await self.user_repo.update(user_id, db, password_hash=password_hash, force_password_change=False)
```

### UserRepo Update with force_password_change

```python
# Source: src/mkobi/db/repositories/user_repo.py — existing update() already supports **kwargs
# The existing update() method uses `for key, value in kwargs.items(): setattr(user_obj, key, value)`
# No changes needed — just pass force_password_change as kwarg
```

### Frontend — Adding Reset Password Action to UserManagement

```tsx
// Source: Extend UserManagement.tsx
import { Key as KeyIcon } from '@mui/icons-material'  // or LockReset

// In the columns array, add to the renderCell of the actions column:
renderCell: ({ row }: GridRenderCellParams<UserRow>) => (
  <>
    <GridActionsCellItem icon={<DeleteIcon />} label="Delete" onClick={() => handleDelete(row)} />
    <GridActionsCellItem icon={<KeyIcon />} label="Reset Password" onClick={() => handleResetPassword(row)} />
  </>
),
```

### Frontend — Reset Password Handler (UserManagement)

```tsx
// Inside UserManagement component:
const [resetResult, setResetResult] = useState<{ tempPassword: string; userEmail: string } | null>(null)

const resetPasswordMutation = useMutation({
  mutationFn: resetUserPassword,
  onSuccess: (data, variables) => {
    const user = users.find((u) => u.id === variables)
    setResetResult({
      tempPassword: data.temp_password,
      userEmail: user?.email ?? '',
    })
    toast.success('Password reset successfully')
  },
  onError: () => {
    toast.error('Failed to reset password')
  },
})

const handleResetPassword = useCallback(
  (user: AdminUser) => {
    confirmDialog.confirm({
      title: 'Reset Password',
      message: `Generate a new temporary password for ${user.email}? The current password will be immediately invalidated.`,
      confirmLabel: 'Confirm',
      onConfirm: () => {
        void resetPasswordMutation.mutateAsync(user.id)
      },
    })
  },
  [confirmDialog, resetPasswordMutation],
)

// Add to JSX at the end:
<ResetPasswordResultDialog
  open={resetResult !== null}
  tempPassword={resetResult?.tempPassword ?? ''}
  userEmail={resetResult?.userEmail ?? ''}
  onClose={() => setResetResult(null)}
/>
```

### Frontend — adminApi.ts Extension

```typescript
// Add to adminApi.ts
export async function resetUserPassword(userId: string): Promise<{
  message: string
  user_id: string
  temp_password: string
}> {
  const response = await axiosInstance.post(`/admin/users/${userId}/reset-password`)
  return response.data
}
```

### Frontend — Silent Refresh Force Redirect

```typescript
// In useAuth.ts — also handle force redirect after silent refresh
// In the useEffect silent refresh block:
void (async () => {
  try {
    const response = await apiRefreshToken()
    setToken(response.access_token)
    const profile = await apiGetProfile()
    setUser(profile)
    if (profile.must_change_password) {
      void navigate('/profile/change-password?force=true')
    }
  } catch {
    removeToken()
    setUser(null)
  } finally {
    setIsLoading(false)
  }
})()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| Return temp password in approve-registration only | Dedicated reset-password endpoint (+ existing approve flow) | This phase | Clean separation of concerns |
| No force password change mechanism | `force_password_change` boolean flag on User model | This phase | Enables mandatory password rotation |
| User must contact admin to reset password | Admin can reset from UserManagement UI | This phase | Self-service admin operation |
| Single-screen destructive confirmation | Two-screen flow: confirm → result with copy | This phase (consistent with existing ConfirmDialog pattern) | Better UX, prevents accidents |
| No self-reset prevention | `admin_user_id == user_id` guard returns 400 | This phase | Prevents admin lockout |

**Deprecated/outdated:** Nothing deprecated in this phase — all additions are additive.

## Open Questions

1. **Should the `approve` registration endpoint also set `force_password_change=true`?**
   - What we know: Currently, the approve-registration endpoint creates a user and returns `temp_password` but doesn't set any force-change flag.
   - What's unclear: Should newly approved users also be forced to change their temp password on first login?
   - Recommendation: Set `force_password_change=True` in the approve-registration endpoint as well (when creating the user). This is a small change in `admin.py` — when calling `auth_service.create_user()`, add the flag. This is LOW effort and improves security consistency.

2. **Should we add rate limiting to the reset-password endpoint?**
   - What we know: The user mentioned "Rate limiting on repeated resets for the same user" as a discretion area.
   - What's unclear: Whether this should use the existing Redis rate limiter pattern or a simple in-memory approach.
   - Recommendation: Add Redis-based rate limiting using the existing `AsyncRateLimiter` pattern: key = `f"password-reset:{user_id}"`, max_attempts=3, ttl=300 (5 minutes). This prevents abuse if an admin account is compromised. Implementation: add check in the endpoint handler before calling the service.

3. **Audit logging: new table or application log?**
   - What we know: User mentioned "Audit logging approach (follow existing logging patterns)" as discretion. Existing pattern uses `logger.info()` for admin actions.
   - What's unclear: Whether security-sensitive events like password resets need persistent audit storage or if application logs suffice.
   - Recommendation: For this phase, follow the existing pattern — `logger.info("Admin password reset", extra={"admin_id": ..., "target_user_id": ...})`. This matches the existing admin action logging in `admin.py`. A dedicated audit table can be added in a future phase if needed. Do NOT create a new audit table now.

4. **Should the reset-password endpoint support reset by email instead of/in addition to user_id?**
   - What we know: Listed in discretion. The existing admin endpoints use `user_id` (UUID) as the path parameter.
   - What's unclear: Whether an email-based lookup (`/admin/users/by-email/{email}/reset-password`) would be useful.
   - Recommendation: Stick with `user_id` only. The admin panel already has the UUID from the listing endpoint. Adding email-based lookup introduces additional attack surface (email enumeration) with no UX benefit since the admin already sees UUIDs in the table.

5. **Should Pydantic validate the temp password?**
   - What we know: The spec says "The generation pattern must pass the same Pydantic validation as regular password changes."
   - What's unclear: Whether the temp password should pass through `validate_password_or_raise()` before hashing, or whether the generation algorithm guarantees it.
   - Recommendation: Call `validate_password_or_raise(temp_password)` in `reset_password_admin()` after generation but before hashing. This is defensive — even if `_generate_temp_password()` guarantees letter+digit, this ensures consistency. If it fails after 3 generation attempts, raise an exception that becomes HTTP 500.

## Sources

### Primary (HIGH confidence)

- **C:\py_dev\mkobi\src\mkobi\api\routes\admin.py** — Existing admin endpoint patterns: `@router.post`, `dependencies=[Depends(require_admin_role)]`, error handling with HTTPException(404/409/500), `db.commit()`/`db.rollback()` patterns
- **C:\py_dev\mkobi\src\mkobi\services\auth_service.py** — AuthService class structure: `__init__` with DI, `change_password()` method (template for reset), `login_user()` return format, `hash_password()`/`verify_password()` usage via security module
- **C:\py_dev\mkobi\src\mkobi\db\models\user.py** — User SQLAlchemy model: column definitions with `mapped_column`, `Boolean`, `server_default`, `text()` patterns
- **C:\py_dev\mkobi\src\mkobi\core\security.py** — `hash_password()` (bcrypt 12 rounds), `verify_password()`, `SALT_ROUNDS: int = 12`, `MAX_PASSWORD_LENGTH: int = 72`
- **C:\py_dev\mkobi\src\mkobi\utils\validators.py** — `validate_password_or_raise()` (min 8 chars + digit + letter) — the same validation that applies to temp passwords
- **C:\py_dev\mkobi\src\mkobi\models\auth.py** — Pydantic auth models: `TokenWithUser` (extends `Token` with `user: UserRead`), `ChangePasswordRequest`, response model patterns
- **C:\py_dev\mkobi\src\mkobi\api\deps.py** — DI patterns: `get_auth_service()`, `get_db_dependency()`, `require_admin_role`, `CurrentUser` alias, `get_user_service()` factory
- **C:\py_dev\mkobi\src\mkobi\interfaces\service_interfaces.py** — `IAuthService` abstract interface (must add `reset_password_admin()` method), `IUserService` interface
- **C:\py_dev\mkobi\src\mkobi\interfaces\repository_interfaces.py** — `IUserRepository` interface (existing `update()` with `**kwargs` supports new field)
- **C:\py_dev\mkobi\src\mkobi\db\repositories\user_repo.py** — `UserRepository.update()` uses `**kwargs` + `hasattr` + `setattr` — already supports arbitrary fields like `force_password_change`
- **C:\py_dev\mkobi\src\mkobi\models\user.py** — `UserRead` Pydantic model (must add `force_password_change: bool = False`)
- **C:\py_dev\mkobi\src\mkobi\models\enums.py** — Existing `StrEnum` patterns (no new enums needed — `force_password_change` is a boolean)
- **C:\py_dev\mkobi\frontend\src\features\admin\ui\UserManagement.tsx** — Existing `ConfirmDialog` integration pattern, `useConfirmDialog()` hook usage, `DataGrid` with `GridActionsCellItem`, toast notifications
- **C:\py_dev\mkobi\frontend\src\shared\components\ConfirmDialog.tsx`** — Reusable dialog: props (`open`, `title`, `message`, `onConfirm`, `onCancel`, `loading`, `confirmLabel`)
- **C:\py_dev\mkobi\frontend\src\shared\hooks\useConfirmDialog.ts`** — Hook API: `confirm()`, `isOpen`, `handleConfirm`, `handleCancel`
- **C:\py_dev\mkobi\frontend\src\features\users\ui\ChangePasswordPage.tsx`** — Existing form with `react-hook-form` + `zod`, `ChangePasswordFormData`, `changePassword()` API call, navigate on success
- **C:\py_dev\mkobi\frontend\src\features\users\api\userApi.ts`** — `changePassword()` POST to `/auth/change-password`
- **C:\py_dev\mkobi\frontend\src\features\admin\api\adminApi.ts`** — Pattern: `getUsers()`, `changeUserRole()`, `deleteUser()` — add `resetUserPassword()` following same pattern
- **C:\py_dev\mkobi\frontend\src\features\auth\model\useAuth.ts`** — `login()` callback with `apiLogin()` → `setToken()` → `setUser()`, silent refresh in `useEffect`, `navigate` import
- **C:\py_dev\mkobi\frontend\src\features\auth\ui\LoginForm.tsx`** — `await login(data.email, data.password)` → `void navigate('/dashboards')` — redirect happens in LoginForm, not useAuth
- **C:\py_dev\mkobi\frontend\src\shared\types\api.types.ts`** — `UserProfile`, `AdminUser`, `AuthResponse` types
- **C:\py_dev\mkobi\frontend\src\shared\types\formSchemas.ts`** — `changePasswordSchema` with zod: `current_password`, `new_password`, `confirm_password` refine check
- **C:\py_dev\mkobi\frontend\src\app\routes.tsx`** — Route structure: `/profile/change-password` with `ProtectedRoute`
- **C:\py_dev\mkobi\frontend\src\shared\components\ProtectedRoute.tsx`** — Redirects to `/login` if no `accessToken`, shows spinner during `isLoading`
- **C:\py_dev\mkobi\frontend\src\shared\api\axiosInstance.ts`** — Base URL `/api/v1`, interceptors for 401/refresh, `withCredentials: true` for cookies
- **C:\py_dev\mkobi\alembic\versions\7130ecb0388c_true_initial_migration.py`** — Migration pattern: `op.execute()` with raw SQL for table creation, `op.add_column`/`op.downgrade()`
- **C:\py_dev\mkobi\alembic\env.py`** — Alembic env: advisory lock pattern, async migration, model imports

### Secondary (MEDIUM confidence)

- **docs\SPEC.md** (v3.0, 2026-05-29) — Architecture decisions: Clean Architecture layers, Cookie-based refresh tokens, Login returns user data pattern, Temp password security note (no logging, HTTPS, one-time use, out-of-band delivery), ConfirmDialog pattern, JWT + bcrypt auth
- **C:\py_dev\mkobi\docs\README_DOCKER.md** — (referenced for context)

### Tertiary (LOW confidence)

- No web-search-only findings — all research derived from codebase analysis and existing patterns.

## Metadata

**Confidence breakdown:**

- Standard stack: **HIGH** — No new libraries needed. All tools are project-standard and verified in existing code.
- Architecture: **HIGH** — All patterns directly observed in codebase: admin endpoint pattern (admin.py), auth service DI (auth_service.py), UserRepo.update() with **kwargs (user_repo.py), ConfirmDialog hook pattern (UserManagement.tsx), useAuth login flow (useAuth.ts), route structure (routes.tsx)
- Pitfalls: **HIGH** — Pitfalls derived from actual codebase behavior (change_password not clearing flag, update() method behavior, existing rate limiter patterns)

**Research date:** 2026-05-31
**Valid until:** 2026-06-30 (stable — core patterns unlikely to change)`