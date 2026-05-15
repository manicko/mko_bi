# 01 Phase 1: Initial Setup & Test Configuration - Research

**Researched:** 2026-05-15
**Domain:** FastAPI/React project initialization, admin user creation, test DB setup, frontend auth UI, password change flow
**Confidence:** HIGH

## Summary

This research covers four areas for Phase 1: (1) idempotent admin user creation at application startup, (2) test database configuration with transaction-based isolation, (3) removing dashboard links from auth screens in the frontend, and (4) implementing password change functionality. The codebase already has strong foundations — DatabaseStarter lifespan hook, bcrypt security, AppLayout with Header/Sidebar, and a working auth system — that constrain and guide the implementation approach.

**Primary recommendation:** Add admin creation to the existing `DatabaseStarter.startup()` flow (after migrations, before the app starts serving), use nested transactions (SAVEPOINT) for test data isolation, conditionally render the Sidebar based on auth state in AppLayout, and add a new `/auth/change-password` endpoint with a dedicated frontend route and form.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | >=0.110.0 | Backend framework | Already in use, async-native |
| SQLAlchemy 2.0 | >=2.0.29 | ORM with async support | Already in use, asyncpg driver |
| Alembic | >=1.18.4 | DB migrations | Already in use, manages schema |
| bcrypt | >=5.0.0 | Password hashing | Already in use, SALT_ROUNDS=12 |
| python-jose | >=3.3.0 | JWT handling | Already in use, HS256 |
| pytest | >=9.0.0 | Test framework | Already in use, asyncio_mode=auto |
| pytest-asyncio | >=1.3.0 | Async test support | Already in use, session-scoped event loop |
| React 18 | (frontend) | UI framework | Already in use |
| React Router | (frontend) | Routing | Already in use, routes.tsx |
| TanStack Query | (frontend) | Data fetching | Already in use |
| React Hook Form + Zod | (frontend) | Form validation | Already in use |
| Material UI v5 | (frontend) | UI components | Already in use |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-multipart | >=0.0.26 | Form parsing | Already in use for OAuth2 forms |
| email-validator | >=2.3.0 | Email validation | Already in use in Pydantic models |

**Installation:** No new packages needed. All required libraries are already in `pyproject.toml` and `package.json`.

---

## Architecture Patterns

### 1. Admin User Creation — Startup Hook Pattern

**What:** Insert admin creation logic into the existing `DatabaseStarter.startup()` method, after migrations are applied but before the app yields control.

**Why this approach (not Alembic migration, not CLI):**
- **Not an Alembic migration:** Migrations are for schema changes, not data seeding. A migration that inserts data would run on every `alembic upgrade`, and making it conditional (only if no admin exists) is non-standard in Alembic. Migrations are also harder to make idempotent for data.
- **Not a separate CLI command:** The decision requires admin creation to be automatic and idempotent on every startup. A CLI command would require manual intervention.
- **Startup hook in `DatabaseStarter.startup()`:** This is the right place because: (a) it already runs on every app startup via the lifespan context manager in `app.py:39-73`, (b) it runs after migrations (so the `users` table exists), (c) it has access to the database engine, and (d) it already handles environment-based conditional logic (test DB recreation).

**Where exactly:** In `src/mkobi/db/starter.py`, between the migration step (line 106) and the test DB step (line 109). A new method `ensure_admin_user()` on the `DatabaseStarter` class.

**Implementation sketch:**
```python
async def ensure_admin_user(self) -> None:
    """Create admin user if no admin exists in the system."""
    from mkobi.core.security import hash_password
    from mkobi.db.repositories.user_repo import UserRepository
    from mkobi.models.enums import UserRole
    
    config = get_config()
    admin_username = getattr(config, 'admin_username', 'admin@example.com')
    admin_password = getattr(config, 'admin_password', 'admin123')
    
    async with get_session() as db:
        repo = UserRepository()
        # Check if any admin exists
        all_users = await repo.get_all(db)
        admin_exists = any(u.role == UserRole.ADMIN for u in all_users)
        if admin_exists:
            logger.info("Admin user already exists, skipping creation")
            return
        
        # Create admin
        await repo.create(
            db=db,
            email=admin_username,
            password_hash=hash_password(admin_password),
            role=UserRole.ADMIN,
        )
        await db.commit()
        logger.info("Admin user created: %s", admin_username)
```

**Key files to modify:**
- `src/mkobi/db/starter.py` — Add `ensure_admin_user()` method, call it in `startup()`
- `src/mkobi/config.py` — Add `admin_username` and `admin_password` settings fields (with env var support: `MK_ADMIN_USERNAME`, `MK_ADMIN_PASSWORD`)

**Gotchas:**
- The `get_session()` function requires the async engine to be initialized. In `DatabaseStarter.startup()`, the engine is created at line 73 (`self._main_engine = create_async_engine(main_url)`), so `get_session()` should work. However, `get_session()` uses its own global engine — need to verify it picks up the same engine or use the starter's engine directly.
- The `UserRepository.get_all()` returns `list[UserRead]` which doesn't have `role` as a string — it's a `UserRole` enum. Comparison `u.role == UserRole.ADMIN` works.
- Config settings for admin credentials must have sensible defaults but be overridable via env vars. The existing config pattern uses `pydantic-settings` with `__` delimiter, so `ADMIN__USERNAME` and `ADMIN__PASSWORD` would map to `config.admin.username` and `config.admin.password` if using a nested model, or flat `ADMIN_USERNAME`/`ADMIN_PASSWORD` fields.

### 2. Test Database Configuration — Nested Transaction (SAVEPOINT) Pattern

**Current state:** The `async_db_session` fixture (conftest.py:266-279) creates a session, yields it, then rolls back. This is a simple rollback approach. The `test_user` fixture (conftest.py:319-342) creates a user and commits it, which means the user is visible to the API (which uses a different session/connection via `get_session()`).

**Problem with current approach:** The test creates a user via `async_db_session` and commits it. The API endpoint runs in a different session (via the overridden `get_db_dependency` which yields the same `async_db_session`). So the committed user IS visible. But if tests modify data and roll back, the committed user from `test_user` persists across tests (since it's committed, not rolled back).

**Recommended improvement — SAVEPOINT pattern:**
```python
@pytest.fixture(scope="function")
async def async_db_session(async_session_maker):
    """Fixture with nested transaction (SAVEPOINT) for test isolation."""
    async with async_session_maker() as session:
        async with session.begin_nested():  # Creates SAVEPOINT
            yield session
            # Rollback to SAVEPOINT happens automatically when the nested
            # transaction context exits (even without explicit rollback)
        # The outer transaction remains open for the next test
```

**Why SAVEPOINT is better:**
- Each test runs inside a SAVEPOINT. If the test fails mid-way, only the SAVEPOINT is rolled back, not the entire session.
- The `test_user` fixture can commit its user within the outer transaction, and the SAVEPOINT rollback will undo any subsequent changes.
- This matches the decision requirement: "database transactions with rollback (function-scoped fixture that begins transaction, yields session, then rolls back)."

**Baseline data fixture (session-scoped):**
```python
@pytest.fixture(scope="session")
async def baseline_data(setup_test_database):
    """Load baseline/reference data once per test session.
    
    This runs after migrations but before any tests.
    Loads enum/reference data that tests depend on.
    """
    from mkobi.db.session import get_session
    async with get_session() as db:
        # Reference data that mirrors what production would have
        # e.g., system settings, default configurations
        # Admin user is NOT included here (created per-test via test_user)
        await db.commit()
    yield
```

**Pytest markers for fast vs. full tests:**
- Add a `fast` marker to `pyproject.toml` markers list: `"fast: fast tests using Base.metadata.create_all() instead of full migrations"`
- Tests that need the full Alembic migration behavior use the default `async_db_session` fixture.
- Tests that need maximum speed can use a separate `fast_db_session` fixture that calls `Base.metadata.create_all()`.

**Key files to modify:**
- `tests/conftest.py` — Replace simple rollback with SAVEPOINT pattern, add `baseline_data` fixture, add `fast` marker
- `pyproject.toml` — Add `fast` marker to `[tool.pytest.ini_options] markers`

**Gotchas:**
- `session.begin_nested()` requires the outer transaction to be started. In SQLAlchemy async, this means the session must be in an active transaction. The pattern `async with session.begin_nested()` works when the session itself is used as a context manager (`async with async_session_maker() as session` starts an implicit transaction).
- SAVEPOINT support requires the database to support it (PostgreSQL does).
- The `test_user` fixture currently calls `await async_db_session.commit()`. With SAVEPOINT, this commit will persist the user within the outer transaction, which is correct — the user will be visible to all tests in the session, and individual test modifications will be rolled back to the SAVEPOINT.

### 3. Frontend Dashboard Link Removal — Conditional Rendering in AppLayout

**Current state analysis:**
- `AppLayout` (routes.tsx:16) wraps ALL routes including `/login` and `/register`
- `AppLayout` renders `Header` and `Sidebar` unconditionally (AppLayout.tsx:6-18)
- `Header` (Header.tsx:5-33) already conditionally renders user-specific buttons (`{user && ...}`) but the "MKOBI Dashboard" title text is always visible
- `Sidebar` (Sidebar.tsx:7-38) renders the "Dashboards" link and "Admin Panel" link. The "Admin Panel" is conditionally rendered (`{user?.role === 'admin'}`), but the "Dashboards" link is ALWAYS visible, even on login/register pages

**The problem:** When unauthenticated users visit `/login` or `/register`, they see the Sidebar with a "Dashboards" link. Clicking it would redirect them to `/dashboards`, which is protected by `ProtectedRoute` and would redirect back to `/login`. This is poor UX.

**Recommended approach — Hide Sidebar when unauthenticated:**

The simplest and most correct approach is to conditionally render the entire `Sidebar` based on auth state in `AppLayout.tsx`:

```tsx
export function AppLayout() {
  const { user } = useAuth()
  
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Header />
      <Box sx={{ display: 'flex', flex: 1 }}>
        {user && <Sidebar />}
        <Box component="main" sx={{ flex: 1, p: 3 }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  )
}
```

**Why this approach (not modifying Header or individual links):**
- The Header already conditionally hides user-specific buttons when `user` is null
- The "MKOBI Dashboard" title in Header is a branding element, not a navigation link — it's acceptable to show it on auth pages
- The Sidebar is the only component with actual dashboard navigation links ("Dashboards", "Admin Panel")
- Hiding the entire Sidebar when unauthenticated is cleaner than conditionally hiding individual links
- This matches the decision: "Remove dashboard links from login and registration screens" and "This removal should be conditional based on authentication state"

**Key files to modify:**
- `frontend/src/shared/components/Layout/AppLayout.tsx` — Add conditional rendering of Sidebar based on `user` state

**Gotchas:**
- The `useAuth()` hook is already imported and used in both `Header` and `Sidebar`. `AppLayout` will need to import it.
- When `user` is null (unauthenticated), the Sidebar is hidden and the main content area should take full width. The current `flex: 1` on the main Box should handle this correctly.
- The `isLoading` state from `useAuth()` should be considered — during initial load, `user` is null while the token is being verified. The Sidebar will be hidden during loading, which is correct behavior.

### 4. Password Change Functionality — New Endpoint + Route + Form

**Backend — New endpoint needed:**

A new `POST /auth/change-password` endpoint in `src/mkobi/api/routes/auth.py`:

```python
@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change password",
    description="Change current user's password. Requires current password.",
)
async def change_password(
    current_password: str,
    new_password: str,
    new_password_confirm: str,
    current_user: UserRead = Depends(get_current_user_dependency),
    auth_service=Depends(get_auth_service),
) -> dict[str, str]:
    # 1. Verify current password
    # 2. Check new_password == new_password_confirm
    # 3. Validate new password strength
    # 4. Update password hash
    # 5. Return success (user stays logged in)
```

**Service layer — New method in AuthService or UserService:**

The password change logic should be in `AuthService` (since it involves authentication verification). A new method:

```python
async def change_password(
    self, user_id: UUID, current_password: str, new_password: str, db: AsyncSession | None = None
) -> bool:
    # 1. Get user with password hash
    # 2. Verify current password via verify_password()
    # 3. Hash new password
    # 4. Update user's password_hash
    # 5. Commit
```

**Frontend — New files needed:**
1. `frontend/src/features/users/ui/ChangePasswordPage.tsx` — The password change form page
2. New route in `routes.tsx`: `/profile/change-password` (protected)
3. New API function in `userApi.ts`: `changePassword(currentPassword, newPassword, newPasswordConfirm)`
4. New Zod schema in `formSchemas.ts`: `changePasswordSchema`

**Frontend — Modified files:**
1. `frontend/src/features/users/ui/UserProfile.tsx` — Add "Change password" button that navigates to `/profile/change-password`
2. `frontend/src/app/routes.tsx` — Add the new route

**Zod schema for password change:**
```typescript
export const changePasswordSchema = z.object({
  currentPassword: z.string().min(1, 'Current password is required'),
  newPassword: z.string().min(8, 'Password must be at least 8 characters'),
  newPasswordConfirm: z.string().min(1, 'Password confirmation is required'),
}).refine((data) => data.newPassword === data.newPasswordConfirm, {
  message: 'Passwords do not match',
  path: ['newPasswordConfirm'],
})
```

**Key files to create:**
- `frontend/src/features/users/ui/ChangePasswordPage.tsx`

**Key files to modify:**
- `src/mkobi/api/routes/auth.py` — Add `POST /auth/change-password` endpoint
- `src/mkobi/services/auth_service.py` — Add `change_password()` method
- `src/mkobi/models/auth.py` — Add `ChangePasswordRequest` Pydantic model
- `frontend/src/app/routes.tsx` — Add `/profile/change-password` route
- `frontend/src/features/users/ui/UserProfile.tsx` — Add "Change password" button
- `frontend/src/features/users/api/userApi.ts` — Add `changePassword()` API function
- `frontend/src/shared/types/formSchemas.ts` — Add `changePasswordSchema`
- `frontend/src/shared/types/api.types.ts` — Add `ChangePasswordRequest` interface

**Gotchas:**
- The `AuthService` currently doesn't have a method to update a password. The `UserService` also doesn't have one. The `UserRepository.update()` method accepts `**kwargs`, so passing `password_hash` would work.
- The endpoint should use `get_current_user_dependency` to identify the user (from JWT token), not accept a user ID from the request. This prevents users from changing other users' passwords.
- After password change, the user should remain logged in. Since JWT tokens are stateless, no action is needed — the existing token remains valid.
- Password strength validation: The existing `loginSchema` only requires `min(6)`. The decision says "New password must follow existing validation rules (length, complexity requirements already implemented)." Need to check if there are actual complexity requirements. The current `loginSchema` has `min(6)` and the `registerSchema` only validates email. There's no password complexity validation currently — the decision says it's "already implemented" so the planner should verify this. If not implemented, add basic complexity rules (min 8 chars, at least one uppercase, one lowercase, one digit).
- The `AuthService.register_user` method accepts `role` as a string, but the `change_password` method should work with the authenticated user's ID from the JWT token.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|------------|-------------|-----|
| Password hashing | Custom hash function | `bcrypt` (already in `core/security.py`) | bcrypt handles salt, rounds, timing attacks |
| JWT token creation | Manual JWT | `python-jose` (already in `core/security.py`) | Handles signing, expiration, algorithm |
| Admin existence check | Raw SQL query | `UserRepository.get_all()` + Python filter | Consistent with existing pattern, type-safe |
| Test DB isolation | Manual TRUNCATE/DELETE | SQLAlchemy SAVEPOINT (nested transaction) | Faster, no deadlocks, proper isolation |
| Email validation | Custom regex | Pydantic `EmailStr` | RFC-compliant, already in use |
| Password confirmation | Manual string compare | Zod `.refine()` | Declarative, already pattern in formSchemas |
| Frontend auth state | Custom context/reducer | `useAuth()` hook (already exists) | Already manages user state, token, loading |

---

## Common Pitfalls

### Pitfall 1: Admin Creation Race Condition

**What goes wrong:** If multiple workers start simultaneously (e.g., uvicorn with `--workers 4`), two workers might both check for admin existence at the same time and both create an admin.
**Why it happens:** The check-then-insert pattern is not atomic.
**How to avoid:** Use a database-level constraint or use `INSERT ... ON CONFLICT DO NOTHING` pattern. Alternatively, since the admin email is fixed, attempt to create and handle the unique constraint violation gracefully.
**Warning signs:** Duplicate admin users in the database.

### Pitfall 2: Test SAVEPOINT with Committed Data

**What goes wrong:** If `test_user` commits a user to the database, and a subsequent test modifies that user's data, the SAVEPOINT rollback will undo the modifications but the original committed user remains. If the next test expects a clean slate, it will see the committed user.
**Why it happens:** SAVEPOINT only rolls back to the point of the SAVEPOINT, not the entire transaction.
**How to avoid:** This is actually the desired behavior — the `test_user` fixture creates a user that persists for all tests in the session. Individual test modifications are rolled back. Tests should be written to expect this.

### Pitfall 3: Sidebar Hidden During Auth Loading

**What goes wrong:** When a user visits `/dashboards` directly, `useAuth()` triggers a profile fetch (in `useEffect`). During loading, `user` is null, so the Sidebar is hidden. After loading completes, `user` is set and the Sidebar appears. This causes a layout shift.
**Why it happens:** The `isLoading` state is true during initial token verification.
**How to avoid:** This is acceptable behavior — the layout shift happens once on page load. The alternative (showing the Sidebar and then hiding it if auth fails) would leak navigation structure to unauthenticated users.

### Pitfall 4: Password Change Without Current Password Verification

**What goes wrong:** If the endpoint doesn't require the current password, an attacker with a valid JWT could change the user's password without knowing the current one.
**Why it happens:** The JWT token identifies the user, so it's tempting to skip current password verification.
**How to avoid:** Always require current password verification. The decision explicitly states: "Current password MUST be required for password change."

### Pitfall 5: Password Change Invalidates Session (Unwanted)

**What goes wrong:** Some implementations invalidate all sessions/tokens after password change, forcing re-login.
**Why it happens:** Security best practice for password resets (not password changes).
**How to avoid:** The decision explicitly states: "User should remain logged in after password change (no forced re-login)." Do not invalidate the JWT token.

---

## Code Examples

### Admin Creation in DatabaseStarter

```python
# In src/mkobi/db/starter.py, inside DatabaseStarter class:

async def ensure_admin_user(self) -> None:
    """Idempotent admin user creation.
    
    Creates admin user if no user with admin role exists.
    Safe to call multiple times. Config-driven credentials.
    """
    from mkobi.core.security import hash_password
    from mkobi.db.repositories.user_repo import UserRepository
    from mkobi.db.session import get_session
    from mkobi.models.enums import UserRole
    
    config = get_config()
    admin_email = config.admin_username
    admin_password = config.admin_password
    
    async with get_session() as db:
        repo = UserRepository()
        all_users = await repo.get_all(db)
        admin_exists = any(u.role == UserRole.ADMIN for u in all_users)
        
        if admin_exists:
            logger.info("Admin user already exists, skipping creation")
            return
        
        await repo.create(
            db=db,
            email=admin_email,
            password_hash=hash_password(admin_password),
            role=UserRole.ADMIN,
        )
        await db.commit()
        logger.info("Admin user created successfully: %s", admin_email)
```

### SAVEPOINT Test Fixture

```python
# In tests/conftest.py, replacing the current async_db_session:

@pytest.fixture(scope="function")
async def async_db_session(async_session_maker):
    """Function-scoped fixture with SAVEPOINT for test isolation.
    
    Begins a nested transaction (SAVEPOINT) that is rolled back
    after each test, ensuring clean state without TRUNCATE overhead.
    """
    async with async_session_maker() as session:
        async with session.begin_nested():
            yield session
        # SAVEPOINT rolled back automatically
        # Outer transaction remains for next test
```

### Conditional Sidebar in AppLayout

```tsx
// In frontend/src/shared/components/Layout/AppLayout.tsx:

import { Outlet } from 'react-router-dom'
import { Header } from './Header'
import { Sidebar } from './Sidebar'
import { Box } from '@mui/material'
import { useAuth } from '../../../features/auth/model/useAuth'

export function AppLayout() {
  const { user } = useAuth()

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Header />
      <Box sx={{ display: 'flex', flex: 1 }}>
        {user && <Sidebar />}
        <Box component="main" sx={{ flex: 1, p: 3 }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  )
}
```

### Password Change Endpoint

```python
# In src/mkobi/api/routes/auth.py:

from mkobi.models.auth import ChangePasswordRequest

@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change password",
    description="Change current user's password. Requires current password verification.",
)
async def change_password(
    request_data: ChangePasswordRequest,
    current_user: UserRead = Depends(get_current_user_dependency),
    auth_service=Depends(get_auth_service),
) -> dict[str, str]:
    """Change password endpoint."""
    try:
        success = await auth_service.change_password(
            user_id=current_user.id,
            current_password=request_data.current_password,
            new_password=request_data.new_password,
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
        ) from e
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|-------------|-----------------|--------------|--------|
| Simple session rollback | SAVEPOINT (nested transaction) | SQLAlchemy 1.4+ | Better isolation, no TRUNCATE needed |
| Manual admin creation in migrations | Startup hook with env config | Best practice | Idempotent, configurable, no migration pollution |
| Showing all nav links to unauthenticated users | Conditional rendering based on auth state | UX best practice | Cleaner auth pages, no confusing links |
| Separate password reset via email | In-app password change with current password verification | Product decision | Better UX, no email dependency |

---

## Open Questions

1. **Admin credentials config structure:** Should admin username/password be flat settings (`ADMIN_USERNAME`, `ADMIN_PASSWORD`) or nested under a new `AdminSettings` model (`ADMIN__USERNAME`, `ADMIN__PASSWORD`)? The existing config uses nested models (DatabaseSettings, JWTSettings, etc.), so a nested `AdminSettings` would be consistent. However, flat settings are simpler for just two values.

2. **Password complexity requirements:** The decision says "New password must follow existing validation rules (length, complexity requirements already implemented)." The current `loginSchema` only has `min(6)` and `registerSchema` only validates email. There are NO existing password complexity rules. The planner needs to either: (a) implement basic complexity rules, or (b) clarify that "existing rules" means the login schema's `min(6)`.

3. **Test baseline data content:** The decision says "Baseline data should include enum/reference data (order statuses, user roles, countries, currencies) and minimal system settings." The current system doesn't have order statuses, countries, or currencies. The only reference data is the PostgreSQL enum types (user_role, dashboard_permission_level, etc.) which are created by Alembic migrations. Need to clarify what "baseline data" actually means for this system — possibly it's just the enum types (already handled by migrations) and no additional seed data is needed.

4. **Admin user for test environment:** The decision says "Admin user should NOT be included in baseline data - created dynamically in tests." The `test_user` fixture already creates an admin user per-test. But if admin creation is added to `DatabaseStarter.startup()`, the test database recreation (which calls `recreate_test_database()`) would also trigger admin creation. Need to ensure the admin creation in `startup()` is skipped during test DB recreation, or that the test `test_user` fixture overrides/removes the admin created by startup.

---

## Sources

### Primary (HIGH confidence)
- **Codebase analysis** — All findings are based on direct reading of the actual source files in the project
- `src/mkobi/db/starter.py` — DatabaseStarter class, startup flow, migration application
- `src/mkobi/app.py` — lifespan hook, DatabaseStarterConfig usage
- `src/mkobi/config.py` — Settings class, env var patterns, pydantic-settings configuration
- `src/mkobi/core/security.py` — hash_password, verify_password, create_access_token, decode_token
- `src/mkobi/services/auth_service.py` — AuthService class, register_user, login_user, authenticate_user
- `src/mkobi/services/user_service.py` — UserService class, CRUD operations
- `src/mkobi/api/routes/auth.py` — Auth endpoints, login, register, refresh, me, register-request
- `src/mkobi/api/routes/users.py` — User CRUD endpoints
- `src/mkobi/api/deps.py` — DI dependencies, get_current_user_dependency, require_admin_role
- `src/mkobi/models/enums.py` — UserRole, DashboardPermission, and other StrEnum classes
- `src/mkobi/models/auth.py` — LoginRequest, RegisterRequest, Token, RefreshRequest
- `src/mkobi/models/user.py` — UserRead, UserCreate, UserDB, UserUpdate
- `src/mkobi/db/models/user.py` — SQLAlchemy User model
- `src/mkobi/db/session.py` — get_session, get_async_engine, init_db
- `src/mkobi/db/repositories/user_repo.py` — UserRepository with CRUD methods
- `tests/conftest.py` — Test fixtures, MockRedis, async_db_session, test_user, auth_headers
- `frontend/src/app/routes.tsx` — React Router routes, AppLayout wrapper
- `frontend/src/shared/components/Layout/AppLayout.tsx` — AppLayout with Header and Sidebar
- `frontend/src/shared/components/Layout/Header.tsx` — Header with conditional user buttons
- `frontend/src/shared/components/Layout/Sidebar.tsx` — Sidebar with dashboard links
- `frontend/src/features/auth/ui/LoginForm.tsx` — Login form
- `frontend/src/features/auth/ui/RegisterForm.tsx` — Registration form
- `frontend/src/features/users/ui/UserProfile.tsx` — User profile page (no password change)
- `frontend/src/features/auth/model/useAuth.ts` — Auth hook
- `frontend/src/features/auth/api/authApi.ts` — Auth API functions
- `frontend/src/features/users/api/userApi.ts` — User API functions
- `frontend/src/shared/types/formSchemas.ts` — Zod schemas
- `frontend/src/shared/types/api.types.ts` — TypeScript interfaces
- `frontend/src/shared/types/enums.ts` — Frontend enum types
- `frontend/src/shared/api/axiosInstance.ts` — Axios instance with interceptors
- `alembic/env.py` — Alembic migration environment
- `alembic/versions/7130ecb0388c_true_initial_migration.py` — Initial migration pattern
- `pyproject.toml` — pytest config, markers, dependencies

### Secondary (MEDIUM confidence)
- **SQLAlchemy 2.0 docs** — Nested transactions (SAVEPOINT) pattern via `session.begin_nested()` (based on training data, consistent with SQLAlchemy 2.0 async patterns)
- **FastAPI docs** — Lifespan context manager pattern (based on training data, consistent with FastAPI >=0.110)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — All libraries are already in use in the project, versions from pyproject.toml
- Architecture patterns: HIGH — All patterns derived from direct codebase analysis, no external assumptions needed
- Pitfalls: MEDIUM — Based on common patterns and codebase-specific analysis; some pitfalls (like race conditions) are theoretical and may not manifest in single-worker deployments

**Research date:** 2026-05-15
**Valid until:** 2026-06-15 (30 days — stable tech stack, no major version changes expected)
