---
phase: 01
domain: Admin User Password Reset
depends_on: []
files_modified:
  # Backend
  - src/mkobi/db/models/user.py
  - alembic/versions/
  - src/mkobi/models/user.py
  - src/mkobi/interfaces/service_interfaces.py
  - src/mkobi/services/auth_service.py
  - src/mkobi/api/routes/admin.py
  # Frontend
  - frontend/src/shared/types/api.types.ts
  - frontend/src/features/admin/api/adminApi.ts
  - frontend/src/features/admin/ui/UserManagement.tsx
  - frontend/src/features/admin/ui/ResetPasswordResultDialog.tsx
  - frontend/src/features/users/ui/ChangePasswordPage.tsx
  - frontend/src/features/auth/model/useAuth.ts
  - frontend/src/features/auth/ui/LoginForm.tsx
autonomous: true
coupling: medium
CoT: false
horizontal: false
---

# PLAN_01 — Admin User Password Reset

## Goal

Implement admin-triggered password reset with temporary password generation (Screen 1: confirm, Screen 2: show temp password with copy), force-password-change flow on next login, and `force_password_change` DB flag.

## Dependency DAG

```
Wave 1 (Foundation — Parallel)
├── TASK_001_user_model_force_flag        → DB column
├── TASK_002_alembic_migration             → Migration file
├── TASK_003_pydantic_userread_flag        → Pydantic model
└── TASK_004_iauthservice_interface          → Abstract method

Wave 2 (Backend Service Logic — depends on Wave 1)
├── TASK_005_authservice_reset_password     → reset_password_admin() + _generate_temp_password()
└── TASK_006_authservice_clear_flag         → change_password() clears force_password_change

Wave 3 (Backend API — depends on Wave 2)
├── TASK_007_admin_reset_endpoint           → POST /admin/users/{user_id}/reset-password
└── TASK_008_approve_sets_force_flag        → approve-registration sets force_password_change=True

Wave 4 (Frontend — depends on Wave 1 + Wave 3)
├── TASK_009_adminapi_reset_function        → adminApi.ts: resetUserPassword()
├── TASK_010_apitypes_force_flag            → api.types.ts: add force_password_change + must_change_password
├── TASK_011_reset_result_dialog            → New ResetPasswordResultDialog.tsx (Screen 2)
├── TASK_012_usermanagement_reset_button    → UserManagement.tsx: button + mutation + dialog
├── TASK_013_change_password_force_mode     → ChangePasswordPage.tsx: force mode prop
├── TASK_014_useauth_force_redirect         → useAuth.ts: navigate on must_change_password
└── TASK_015_loginform_force_redirect       → LoginForm.tsx: remove own navigate, use useAuth redirect

Wave 5 (Verification)
└── TASK_016_verify_phase01                 → End-to-end integration check
```

## Execution Order

| Order | Task ID | Short Name | Wave | Depends On |
|-------|---------|------------|------|------------|
| 001 | TASK_001 | user_model_force_flag | 1 | — |
| 002 | TASK_002 | alembic_migration | 1 | — |
| 003 | TASK_003 | pydantic_userread_flag | 1 | — |
| 004 | TASK_004 | iauthservice_interface | 1 | — |
| 005 | TASK_005 | authservice_reset_password | 2 | 001, 003, 004 |
| 006 | TASK_006 | authservice_clear_flag | 2 | 001 |
| 007 | TASK_007 | admin_reset_endpoint | 3 | 005 |
| 008 | TASK_008 | approve_sets_force_flag | 3 | 006 |
| 009 | TASK_009 | adminapi_reset_function | 4 | 003 |
| 010 | TASK_010 | apitypes_force_flag | 4 | 003 |
| 011 | TASK_011 | reset_result_dialog | 4 | — |
| 012 | TASK_012 | usermanagement_reset_button | 4 | 009, 011 |
| 013 | TASK_013 | change_password_force_mode | 4 | — |
| 014 | TASK_014 | useauth_force_redirect | 4 | 010 |
| 015 | TASK_015 | loginform_force_redirect | 4 | 014 |
| 016 | TASK_016 | verify_phase01 | 5 | 007, 008, 012, 013, 014, 015 |

## must_haves

- Admin can trigger password reset for any user (except self) via POST `/api/v1/admin/users/{user_id}/reset-password`
- Response includes `{ message, user_id, temp_password }` with HTTP 200
- Temp password is 8 chars, letters + digits, at least one letter and one digit
- Temp password passes `validate_password_or_raise()` before hashing
- Up to 3 generation attempts → HTTP 500 if all fail
- `force_password_change` boolean column on `users` table (NOT NULL, default false)
- Alembic migration adds the column with `server_default=text("false")`
- `force_password_change=True` set during reset AND during approve-registration
- `force_password_change=False` cleared on successful password change by user
- `UserRead` Pydantic model includes `force_password_change: bool = False`
- Self-reset prevention: admin_user_id == user_id → HTTP 400
- User not found → HTTP 400
- Login response includes `force_password_change` via user object → frontend maps to `must_change_password`
- Frontend: Reset Password button in UserManagement per-row actions (after Delete)
- Screen 1: Reuses existing `ConfirmDialog` with "Confirm" / "Cancel", buttons disabled + spinner on confirm
- Screen 2: New `ResetPasswordResultDialog` showing temp password + Copy button + Close button
- Copy uses `navigator.clipboard.writeText()` + toast "Copied"
- Force mode on ChangePasswordPage: `?force=true` → Cancel disabled/disabled, info banner, same form fields
- useAuth.login() handles force redirect internally (pass navigate, or use state effect)
- LoginForm no longer navigates to `/dashboards` unconditionally
- Silent refresh in useAuth also checks `must_change_password`
- No new libraries needed
- All code/logs/comments in English
- ruff + mypy pass

---

## TASK SPECIFICATIONS

<task>
id: TASK_001_user_model_force_flag

title: Add force_password_change column to User SQLAlchemy model

status: pending

priority: high

depends_on: []

description: >
  Add the `force_password_change` boolean column to the User SQLAlchemy model
  in `src/mkobi/db/models/user.py`. The column must be NOT NULL with
  `default=False` and `server_default=text("false")` to support existing rows.

goals:
  - Add force_password_change column to User model
  - Ensure backward compatibility with existing rows via server_default
  - Follow existing column definition patterns (Boolean, server_default, text())

files:
  - path: src/mkobi/db/models/user.py
    targets:
      - type: class
        name: User
      - type: column
        name: force_password_change
    semantic_anchors:
      insert_after:
        type: column_definition
        name: is_active

changes:
  - action: add_column
    description: >
      Add `force_password_change: Mapped[bool]` column after `is_active`,
      using the same Boolean + server_default pattern as other boolean columns.
    code_hint: |
      force_password_change: Mapped[bool] = mapped_column(
          Boolean,
          nullable=False,
          default=False,
          server_default=text("false"),
      )

acceptance_criteria:
  - Column added after is_active in User model
  - Uses Boolean, nullable=False, default=False, server_default=text("false")
  - ruff passes, mypy passes

tests_to_run:
  - ruff check src/mkobi/db/models/user.py
  - mypy src/mkobi/db/models/user.py

source_reference: C:\py_dev\mkobi\.ai\plans\PLAN_01.md
source_section: Wave 1 — TASK_001
</task>

<task>
id: TASK_002_alembic_migration

title: Create Alembic migration for force_password_change column

status: pending

priority: high

depends_on: []

description: >
  Generate a new Alembic migration file in `alembic/versions/` that adds
  the `force_password_change` column to the `users` table. The migration
  must use `sa.Column` with `server_default=sa.false()` and `nullable=False`.

goals:
  - Create migration file with upgrade (op.add_column) and downgrade (op.drop_column)
  - Follow existing Alembic patterns (revision ID, raw SQL or API usage)
  - Ensure existing rows get default value via server_default

files:
  - path: alembic/versions/
    targets:
      - type: new_file
        name: xxxx_add_force_password_change_to_users.py

changes:
  - action: create_file
    description: >
      New Alembic migration file. Use alembic revision --autogenerate or create manually.
      Must follow the pattern from 7130ecb0388c_true_initial_migration.py.
    code_hint: |
      from alembic import op
      import sqlalchemy as sa

      revision = '<generated>'
      down_revision = '7130ecb0388c'
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

acceptance_criteria:
  - Migration file created in alembic/versions/
  - upgrade() adds column with nullable=False, server_default=sa.false()
  - downgrade() drops the column
  - down_revision points to 7130ecb0388c
  - `alembic upgrade head` runs without error

tests_to_run:
  - cd C:\py_dev\mkobi && alembic upgrade head
  - cd C:\py_dev\mkobi && alembic downgrade -1

source_reference: C:\py_dev\mkobi\.ai\plans\PLAN_01.md
source_section: Wave 1 — TASK_002
</task>

<task>
id: TASK_003_pydantic_userread_flag

title: Add force_password_change to UserRead Pydantic model

status: pending

priority: high

depends_on: []

description: >
  Add `force_password_change: bool = False` to the `UserRead` Pydantic model
  in `src/mkobi/models/user.py`. This ensures the field is exposed in API responses
  (login, get users, get profile, etc.).

goals:
  - Add force_password_change field to UserRead
  - Ensure it serializes from SQLAlchemy model attribute via from_attributes=True
  - Default to False for safety

files:
  - path: src/mkobi/models/user.py
    targets:
      - type: class
        name: UserRead
    semantic_anchors:
      insert_after:
        type: field
        name: created_at

changes:
  - action: add_field
    description: >
      Add `force_password_change: bool = False` field to UserRead class,
      after `created_at` field.
    code_hint: |
      force_password_change: bool = False

acceptance_criteria:
  - Field `force_password_change: bool = False` added to UserRead
  - from_attributes=True already set in model_config (existing)
  - ruff passes, mypy passes

tests_to_run:
  - ruff check src/mkobi/models/user.py
  - mypy src/mkobi/models/user.py

source_reference: C:\py_dev\mkobi\.ai\plans\PLAN_01.md
source_section: Wave 1 — TASK_003
</task>

<task>
id: TASK_004_iauthservice_interface

title: Add reset_password_admin() to IAuthService abstract interface

status: pending

priority: high

depends_on: []

description: >
  Add the `reset_password_admin()` abstract method to the `IAuthService`
  interface in `src/mkobi/interfaces/service_interfaces.py`. This ensures
  the concrete AuthService implements the method.

goals:
  - Add reset_password_admin() abstract method to IAuthService
  - Follow existing pattern: @abc.abstractmethod + pass body
  - Correct type hints matching the implementation signature

files:
  - path: src/mkobi/interfaces/service_interfaces.py
    targets:
      - type: class
        name: IAuthService
    semantic_anchors:
      insert_before:
        type: method
        name: create_access_token

changes:
  - action: add_method
    description: >
      Add `reset_password_admin()` abstract method to IAuthService class,
      before the `create_access_token` method. Uses UUID types for user_id
      and admin_user_id, AsyncSession for db, returns dict[str, Any] | None.
    code_hint: |
      @abc.abstractmethod
      async def reset_password_admin(
          self,
          user_id: UUID,
          admin_user_id: UUID,
          db: AsyncSession,
      ) -> dict[str, Any] | None:
          """Admin-triggered password reset. Generates temp password."""
          pass

acceptance_criteria:
  - Abstract method added before create_access_token in IAuthService
  - Has UUID user_id, UUID admin_user_id, AsyncSession db parameters
  - Returns dict[str, Any] | None
  - ruff passes, mypy passes

tests_to_run:
  - ruff check src/mkobi/interfaces/service_interfaces.py
  - mypy src/mkobi/interfaces/service_interfaces.py

source_reference: C:\py_dev\mkobi\.ai\plans\PLAN_01.md
source_section: Wave 1 — TASK_004
</task>

<task>
id: TASK_005_authservice_reset_password

title: Implement reset_password_admin() and _generate_temp_password() in AuthService

status: pending

priority: high

depends_on:
  - TASK_001_user_model_force_flag
  - TASK_003_pydantic_userread_flag
  - TASK_004_iauthservice_interface

description: >
  Add two methods to `AuthService` in `src/mkobi/services/auth_service.py`:
  (1) `_generate_temp_password()` — private helper that generates an 8-char
  password from ascii_letters + digits, ensuring at least one letter + one digit,
  with up to 3 attempts. (2) `reset_password_admin()` — generates temp password,
  validates it via `validate_password_or_raise()`, hashes it, saves via
  `user_repo.update()` with force_password_change=True, commits, and returns
  `{ message, user_id, temp_password }`. Includes self-reset guard (user_id ==
  admin_user_id raises ValueError).

goals:
  - Add _generate_temp_password() private helper method
  - Add reset_password_admin() method with full business logic
  - Self-reset prevention guard (ValueError)
  - Temp password validation via validate_password_or_raise()
  - Use hash_password() from core.security, NOT raw bcrypt
  - Use user_repo.update() with **kwargs for atomic hash + flag update
  - Call await db.commit() after update
  - Audit log via logger.info() — NEVER log temp_password
  - Return dict[str, Any] with message, user_id (str), temp_password
  - Import string module

files:
  - path: src/mkobi/services/auth_service.py
    targets:
      - type: class
        name: AuthService
      - type: method
        name: _generate_temp_password
      - type: method
        name: reset_password_admin
    semantic_anchors:
      insert_after:
        type: method
        name: reset_password_admin
        # Add after change_password method (before end of class)
      insert_before:
        type: method
        name: create_access_token
    # _generate_temp_password placed right before reset_password_admin

changes:
  - action: add_import
    description: Add `import string` at module level (next to existing `import re`)

  - action: add_method
    description: >
      Add `_generate_temp_password(self, length: int = 8) -> str` private method.
      Uses `secrets.choice(string.ascii_letters + string.digits)` in a loop.
      Checks for at least one letter and one digit. Up to 3 attempts.
      Fallback: force letter + digit + fill remaining, then shuffle.
    code_hint: |
      def _generate_temp_password(self, length: int = 8) -> str:
          """Generate a cryptographically secure 8-char password with letters + digits.

          Ensures at least one letter and one digit. Up to 3 attempts
          to produce a password passing Pydantic validation.
          """
          alphabet = string.ascii_letters + string.digits
          for attempt in range(3):
              password = "".join(secrets.choice(alphabet) for _ in range(length))
              if re.search(r"[a-zA-Z]", password) and re.search(r"\d", password):
                  return password
          # Fallback (astronomically unlikely to reach)
          password = secrets.choice(string.ascii_letters) + secrets.choice(string.digits)
          password += "".join(secrets.choice(alphabet) for _ in range(length - 2))
          # Shuffle to avoid predictable positions
          password_list = list(password)
          secrets.SystemRandom().shuffle(password_list)
          return "".join(password_list)

  - action: add_method
    description: >
      Add `reset_password_admin(self, user_id, admin_user_id, db)` method.
      Guard: if user_id == admin_user_id, raise ValueError("Admin cannot reset own password").
      Fetch user via user_repo.get_with_hash(). If None, return None.
      Generate temp password, validate via validate_password_or_raise(),
      hash via hash_password(), update user with password_hash + force_password_change=True,
      commit, log success (without temp_password), return result dict.
    code_hint: |
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
              ValueError: If admin resets own password.
          """
          logger.info(
              "Admin password reset: user_id=%s, admin_id=%s",
              user_id, admin_user_id,
          )

          if user_id == admin_user_id:
              logger.warning(
                  "Admin attempted self-password-reset: %s", admin_user_id,
              )
              raise ValueError("Admin cannot reset own password")

          user_obj = await self.user_repo.get_with_hash(user_id, db)
          if user_obj is None:
              logger.warning(
                  "User not found for password reset: %s", user_id,
              )
              return None

          temp_password = self._generate_temp_password()
          validate_password_or_raise(temp_password)
          password_hash = hash_password(temp_password)

          await self.user_repo.update(
              user_id, db,
              password_hash=password_hash,
              force_password_change=True,
          )
          await db.commit()

          logger.info(
              "Password reset successful: user_id=%s", user_id,
          )
          return {
              "message": "Password reset successfully",
              "user_id": str(user_id),
              "temp_password": temp_password,
          }

acceptance_criteria:
  - _generate_temp_password() generates 8-char passwords with letters + digits
  - At least one letter and one digit guaranteed
  - Up to 3 generation attempts with fallback
  - reset_password_admin() method implements IAuthService interface
  - Self-reset guard raises ValueError("Admin cannot reset own password")
  - Returns None for non-existent user
  - Validates temp password via validate_password_or_raise()
  - Uses hash_password() (not raw bcrypt)
  - Does NOT log temp_password in any logger call
  - Uses user_repo.update() **kwargs pattern
  - Calls await db.commit() explicitly
  - import string at module level
  - ruff passes, mypy passes

tests_to_run:
  - ruff check src/mkobi/services/auth_service.py
  - mypy src/mkobi/services/auth_service.py

source_reference: C:\py_dev\mkobi\.ai\plans\PLAN_01.md
source_section: Wave 2 — TASK_005
</task>

<task>
id: TASK_006_authservice_clear_flag

title: Modify change_password() to clear force_password_change flag

priority: high

status: pending

depends_on:
  - TASK_001_user_model_force_flag

description: >
  Modify the existing `change_password()` method in `AuthService` to include
  `force_password_change=False` in the `user_repo.update()` call. This ensures
  that after a user successfully changes their password (including in force mode),
  the flag is cleared and they won't be stuck in the force-change loop.

goals:
  - Clear force_password_change flag after successful password change
  - Minimal change: just add force_password_change=False to existing update() call
  - Prevent force-password-change infinite loop (Pitfall 1)

files:
  - path: src/mkobi/services/auth_service.py
    targets:
      - type: method
        name: change_password
    semantic_anchors:
      modify:
        type: function_call
        name: user_repo.update
        # In change_password(), line: await self.user_repo.update(user_id, db, password_hash=password_hash)

changes:
  - action: modify_call
    description: >
      Change the existing `self.user_repo.update()` call in `change_password()`
      from `password_hash=password_hash` to `password_hash=password_hash, force_password_change=False`.
    code_hint: |
      # FROM:
      await self.user_repo.update(user_id, db, password_hash=password_hash)
      # TO:
      await self.user_repo.update(user_id, db, password_hash=password_hash, force_password_change=False)

acceptance_criteria:
  - change_password() update call includes force_password_change=False
  - All other behavior unchanged
  - ruff passes, mypy passes

tests_to_run:
  - ruff check src/mkobi/services/auth_service.py
  - mypy src/mkobi/services/auth_service.py

source_reference: C:\py_dev\mkobi\.ai\plans\PLAN_01.md
source_section: Wave 2 — TASK_006
</task>

<task>
id: TASK_007_admin_reset_endpoint

title: Add POST reset-password endpoint to admin.py

status: pending

priority: high

depends_on:
  - TASK_005_authservice_reset_password

description: >
  Add `POST /users/{user_id}/reset-password` endpoint to the admin router
  in `src/mkobi/api/routes/admin.py`. Follows the existing approve-registration
  pattern: admin-only dependency, try/except with HTTPException 400/404/500,
  delegates to `auth_service.reset_password_admin()`. Returns the service
  result dict directly. Uses `current_user: CurrentUser` for admin_user_id.

goals:
  - New endpoint following existing admin pattern
  - Uses require_admin_role dependency (via dependencies=[Depends(require_admin_role)])
  - Delegates to auth_service.reset_password_admin()
  - Self-reset: ValueError → HTTP 400
  - User not found: returns None → HTTP 400 (or 404 consistently)
  - Generic exception → HTTP 500
  - Audit logging via logger.info()
  - Does NOT add rate limiting (deferred)
  - Does NOT log temp_password

files:
  - path: src/mkobi/api/routes/admin.py
    targets:
      - type: router
        name: router
      - type: endpoint_function
        name: reset_user_password_admin_endpoint
    semantic_anchors:
      insert_after:
        type: endpoint
        name: delete_user_admin_endpoint
      # Add after user management section, before registration requests section

changes:
  - action: add_endpoint
    description: >
      Add `POST /users/{user_id}/reset-password` endpoint. Place it after
      `delete_user_admin_endpoint` and before the `--- Registration Requests ---`
      section marker.
    code_hint: |
      @router.post(
          "/users/{user_id}/reset-password",
          status_code=status.HTTP_200_OK,
          summary="Reset user password (admin)",
          description="Generates a temporary password, sets force_password_change flag.",
          dependencies=[Depends(require_admin_role)],
      )
      async def reset_user_password_admin_endpoint(
          user_id: UUID,
          current_user: CurrentUser,
          db: AsyncSession = Depends(get_db_dependency),
          auth_service: AuthService = Depends(get_auth_service),
      ) -> dict[str, Any]:
          """Reset user password and return temporary password."""
          logger.info(
              "Admin: resetting password for user: id=%s, admin=%s",
              user_id, current_user.email,
          )
          try:
              result = await auth_service.reset_password_admin(
                  user_id=user_id,
                  admin_user_id=current_user.id,
                  db=db,
              )
              if result is None:
                  raise HTTPException(
                      status_code=status.HTTP_400_BAD_REQUEST,
                      detail="User not found",
                  )
              return result
          except ValueError as exc:
              raise HTTPException(
                  status_code=status.HTTP_400_BAD_REQUEST,
                  detail=str(exc),
              ) from exc
          except HTTPException:
              raise
          except Exception as exc:
              await db.rollback()
              logger.error("Error resetting user password: %s", exc)
              raise HTTPException(
                  status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                  detail="Error resetting user password",
              ) from exc

  - action: add_import
    description: >
      Add `from uuid import UUID` is already imported. Verify `string` is
      not needed here (only in auth_service). No new imports required beyond
      what's already in admin.py.

acceptance_criteria:
  - Endpoint responds to POST /api/v1/admin/users/{user_id}/reset-password
  - Requires admin role
  - Delegates to auth_service.reset_password_admin()
  - Returns { message, user_id, temp_password } on success (HTTP 200)
  - Returns HTTP 400 for self-reset or user not found
  - Returns HTTP 500 for unexpected errors
  - Includes await db.rollback() in exception handler
  - Does NOT log temp_password
  - ruff passes, mypy passes

tests_to_run:
  - ruff check src/mkobi/api/routes/admin.py
  - mypy src/mkobi/api/routes/admin.py

source_reference: C:\py_dev\mkobi\.ai\plans\PLAN_01.md
source_section: Wave 3 — TASK_007
</task>

<task>
id: TASK_008_approve_sets_force_flag

title: Set force_password_change=True in approve-registration endpoint

status: pending

priority: high

depends_on:
  - TASK_006_authservice_clear_flag

description: >
  In the `approve_registration_request_admin_endpoint` function in `admin.py`,
  the current code creates a user with a temporary password but does NOT set
  `force_password_change=True`. After `auth_service.create_user()`, immediately
  update the user to set `force_password_change=True`. This ensures newly
  approved users must change their temp password on first login.
  NOTE: This requires AFTER the create_user call, using auth_service.user_repo.update()
  (The auth_service is already injected via Depends(get_auth_service) in the endpoint.)

goals:
  - Newly approved users must change password on first login
  - Minimal change to existing approve-registration flow
  - Uses force_password_change=True via user_repo.update() after create_user

files:
  - path: src/mkobi/api/routes/admin.py
    targets:
      - type: endpoint_function
        name: approve_registration_request_admin_endpoint
    semantic_anchors:
      insert_after:
        type: function_call
        name: auth_service.create_user
      # After `user = await auth_service.create_user(...)` line

changes:
  - action: add_code
    description: >
      After the `user = await auth_service.create_user(...)` call in the
      approve-registration endpoint (around line 189), add a call to set
      force_password_change=True on the newly created user. Use existing
      import patterns — get_user_repository is used elsewhere; we can use
      auth_service.user_repo directly or import UserRepository.
    code_hint: |
      # After line: user = await auth_service.create_user(...)
      # Add before: await repo.update_status(...)
      # Reuse the already-injected auth_service's repository (DI pattern)
      await auth_service.user_repo.update(
          user.id, db,
          force_password_change=True,
      )

acceptance_criteria:
  - After user creation in approve-registration, force_password_change=True is set
  - Uses auth_service.user_repo.update() (no direct UserRepository instantiation)
  - Return dict still includes temp_password
  - No other behavior changes
  - ruff passes, mypy passes

tests_to_run:
  - ruff check src/mkobi/api/routes/admin.py
  - mypy src/mkobi/api/routes/admin.py

source_reference: C:\py_dev\mkobi\.ai\plans\PLAN_01.md
source_section: Wave 3 — TASK_008
</task>

<task>
id: TASK_009_adminapi_reset_function

title: Add resetUserPassword() to adminApi.ts

status: pending

priority: medium

depends_on:
  - TASK_003_pydantic_userread_flag

description: >
  Add `resetUserPassword(userId: string)` function to
  `frontend/src/features/admin/api/adminApi.ts`. Follows the existing pattern
  of `deleteUser()`, `changeUserRole()`, etc. Returns a typed promise with
  `{ message, user_id, temp_password }`.

goals:
  - Add resetUserPassword function following existing adminApi patterns
  - POST to `/admin/users/${userId}/reset-password`
  - Return typed response

files:
  - path: frontend/src/features/admin/api/adminApi.ts
    targets:
      - type: function
        name: resetUserPassword
    semantic_anchors:
      insert_after:
        type: function
        name: deleteUser

changes:
  - action: add_function
    description: >
      Add resetUserPassword function after deleteUser function.
    code_hint: |
      export async function resetUserPassword(userId: string): Promise<{
        message: string
        user_id: string
        temp_password: string
      }> {
        const response = await axiosInstance.post(`/admin/users/${userId}/reset-password`)
        return response.data
      }

acceptance_criteria:
  - Function added after deleteUser
  - POSTs to correct URL
  - Returns typed response
  - TypeScript compiles without error

tests_to_run:
  - cd frontend && npx tsc --noEmit --project tsconfig.json (if available)

source_reference: C:\py_dev\mkobi\.ai\plans\PLAN_01.md
source_section: Wave 4 — TASK_009
</task>

<task>
id: TASK_010_apitypes_force_flag

title: Add force_password_change to api.types.ts

status: pending

priority: medium

depends_on:
  - TASK_003_pydantic_userread_flag

description: >
  Add `force_password_change: boolean` field to the `UserProfile` and `AdminUser`
  interfaces in `frontend/src/shared/types/api.types.ts`. This type is used by
  `useAuth.ts`, `LoginForm.tsx`, and admin components. The field maps from the
  backend's `force_password_change` column. Also add `must_change_password` as
  a convenience alias that the frontend checks.

goals:
  - Add force_password_change: boolean to UserProfile
  - Add force_password_change: boolean to AdminUser
  - Runtime id: both frontend and backend use force_password_change as key name;
    frontend checks `user.force_password_change` directly (no separate
    must_change_password alias needed since the backend sends force_password_change)

files:
  - path: frontend/src/shared/types/api.types.ts
    targets:
      - type: interface
        name: UserProfile
      - type: interface
        name: AdminUser
    semantic_anchors:
      insert_after:
        type: field
        name: created_at
      # In UserProfile and AdminUser, after created_at field

changes:
  - action: add_field
    description: >
      Add `force_password_change: boolean` to both UserProfile and AdminUser
      interfaces, after `created_at` field.
    code_hint: |
      force_password_change: boolean

acceptance_criteria:
  - UserProfile interface includes force_password_change: boolean
  - AdminUser interface includes force_password_change: boolean
  - TypeScript compiles without error

tests_to_run:
  - cd frontend && npx tsc --noEmit

source_reference: C:\py_dev\mkobi\.ai\plans\PLAN_01.md
source_section: Wave 4 — TASK_010
</task>

<task>
id: TASK_011_reset_result_dialog

title: Create ResetPasswordResultDialog component (Screen 2)

status: pending

priority: medium

depends_on: []

description: >
  Create new file `frontend/src/features/admin/ui/ResetPasswordResultDialog.tsx`.
  This is Screen 2 of the password reset flow. Shows the temp password in a
  read-only TextField with a Copy button (navigator.clipboard.writeText + toast "Copied")
  and a Close button. Both buttons visible simultaneously.

goals:
  - New file at frontend/src/features/admin/ui/ResetPasswordResultDialog.tsx
  - Uses MUI Dialog, DialogTitle, DialogContent, DialogActions
  - Read-only TextField for temp password
  - Copy button with navigator.clipboard.writeText + toast.success("Copied")
  - Close button to dismiss
  - Props: open, tempPassword, userEmail, onClose
  - Uses MUI ContentCopy icon

files:
  - path: frontend/src/features/admin/ui/ResetPasswordResultDialog.tsx
    targets:
      - type: new_component
        name: ResetPasswordResultDialog
    semantic_anchors: []

changes:
  - action: create_file
    description: >
      Create ResetPasswordResultDialog component. Full implementation from research.
      Uses useState for copied state, async handleCopy with try/catch,
      Box with display:flex for textfield+button layout.
    code_hint: |
      import { useState } from "react"
      import {
        Dialog, DialogTitle, DialogContent, DialogContentText,
        DialogActions, Button, TextField, Box,
      } from "@mui/material"
      import ContentCopyIcon from "@mui/icons-material/ContentCopy"
      import { toast } from "react-hot-toast"

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
            toast.success("Copied")
            setTimeout(() => setCopied(false), 3000)
          } catch {
            toast.error("Failed to copy")
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
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <TextField
                  value={tempPassword}
                  fullWidth
                  InputProps={{ readOnly: true }}
                  size="small"
                />
                <Button
                  variant="outlined"
                  onClick={() => { void handleCopy() }}
                  startIcon={<ContentCopyIcon />}
                >
                  {copied ? "Copied" : "Copy"}
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

acceptance_criteria:
  - File created at correct path
  - Interface has open, tempPassword, userEmail, onClose props
  - Copy button uses navigator.clipboard.writeText + toast
  - Both Copy and Close buttons visible simultaneously
  - TypeScript compiles without error

tests_to_run:
  - cd frontend && npx tsc --noEmit

source_reference: C:\py_dev\mkobi\.ai\plans\PLAN_01.md
source_section: Wave 4 — TASK_011
</task>

<task>
id: TASK_012_usermanagement_reset_button

title: Add Reset Password button + handler to UserManagement.tsx

status: pending

priority: medium

depends_on:
  - TASK_009_adminapi_reset_function
  - TASK_011_reset_result_dialog

description: >
  Modify `frontend/src/features/admin/ui/UserManagement.tsx` to add:
  (1) Import `Key` icon from `@mui/icons-material` (or LockReset if preferred)
  (2) Import `resetUserPassword` from adminApi
  (3) Import `ResetPasswordResultDialog`
  (4) Add GridActionsCellItem for Reset Password in the actions column renderCell
  (5) Add `resetPasswordMutation` using TanStack useMutation
  (6) Add `handleResetPassword` callback using confirmDialog.confirm()
  (7) Add `resetResult` state (tempPassword + userEmail)
  (8) Add `<ResetPasswordResultDialog>` to JSX output

goals:
  - Reset Password icon button in each row's actions (after Delete)
  - Confirmation dialog via existing ConfirmDialog pattern
  - Mutation calls resetUserPassword API
  - On success: stores result, shows ResetPasswordResultDialog
  - On error: toast error

files:
  - path: frontend/src/features/admin/ui/UserManagement.tsx
    targets:
      - type: component
        name: UserManagement
    semantic_anchors:
      insert_after:
        type: import
        name: Delete as DeleteIcon
      insert_after:
        type: mutation
        name: deleteMutation
      insert_after:
        type: callback
        name: handleDelete
      insert_after:
        type: JSX
        name: ConfirmDialog

changes:
  - action: add_imports
    description: >
      Add imports for Key icon, resetUserPassword function, and ResetPasswordResultDialog.
    code_hint: |
      import { Delete as DeleteIcon, Key as ResetPasswordIcon } from '@mui/icons-material'
      import { resetUserPassword } from '../api/adminApi'
      import { ResetPasswordResultDialog } from './ResetPasswordResultDialog'

  - action: add_state_and_mutations
    description: >
      Add resetResult state and resetPasswordMutation after existing deleteMutation.
    code_hint: |
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

  - action: add_handler
    description: >
      Add handleResetPassword callback after handleDelete.
    code_hint: |
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

  - action: modify_columns
    description: >
      Add GridActionsCellItem for Reset Password in the renderCell of actions column.
    code_hint: |
      renderCell: ({ row }: GridRenderCellParams<UserRow>) => (
        <>
          <GridActionsCellItem icon={<DeleteIcon />} label="Delete" onClick={() => handleDelete(row)} />
          <GridActionsCellItem icon={<ResetPasswordIcon />} label="Reset Password" onClick={() => handleResetPassword(row)} />
        </>
      ),

  - action: add_jsx
    description: >
      Add ResetPasswordResultDialog component at end of return JSX (after ConfirmDialog).
    code_hint: |
      <ResetPasswordResultDialog
        open={resetResult !== null}
        tempPassword={resetResult?.tempPassword ?? ''}
        userEmail={resetResult?.userEmail ?? ''}
        onClose={() => setResetResult(null)}
      />

acceptance_criteria:
  - Reset Password button visible in each user row actions
  - Clicking button opens ConfirmDialog
  - Confirm triggers API call, buttons disabled during loading
  - On success: ResetPasswordResultDialog shows with temp password
  - On error: toast "Failed to reset password"
  - Copy button in result dialog works with clipboard + toast
  - TypeScript compiles without error

tests_to_run:
  - cd frontend && npx tsc --noEmit

source_reference: C:\py_dev\mkobi\.ai\plans\PLAN_01.md
source_section: Wave 4 — TASK_012
</task>

<task>
id: TASK_013_change_password_force_mode

title: Add force mode to ChangePasswordPage.tsx

status: pending

priority: medium

depends_on: []

description: >
  Modify `frontend/src/features/users/ui/ChangePasswordPage.tsx` to support
  force mode via `?force=true` query parameter. In force mode: Cancel button
  is disabled/disabled, informational Alert is shown at top, form fields remain
  the same (current_password + new_password + confirm_password).

goals:
  - Read force param from URL via useSearchParams
  - Show info Alert when in force mode
  - Disable Cancel button in force mode
  - Same form fields and validation regardless of mode
  - Navigate logic unchanged

files:
  - path: frontend/src/features/users/ui/ChangePasswordPage.tsx
    targets:
      - type: component
        name: ChangePasswordPage
    semantic_anchors:
      insert_after:
        type: import
        name: useNavigate
      insert_after:
        type: state
        name: isSubmitting

changes:
  - action: add_import
    description: Add useSearchParams from react-router-dom and Alert from MUI.
    code_hint: |
      import { useSearchParams } from 'react-router-dom'

  - action: add_force_mode_detection
    description: >
      Inside ChangePasswordPage component, add searchParams and isForceMode
      after existing useState calls.
    code_hint: |
      const [searchParams] = useSearchParams()
      const isForceMode = searchParams.get('force') === 'true'

  - action: add_info_alert
    description: >
      Add Alert component after the {error && ...} block and before the form.
    code_hint: |
      {isForceMode && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Password change is required. Please set a new password to continue.
        </Alert>
      )}

  - action: disable_cancel_in_force_mode
    description: >
      Add isForceMode to Cancel button's disabled prop.
    code_hint: |
      disabled={isSubmitting || isForceMode}

acceptance_criteria:
  - ?force=true in URL activates force mode
  - Info Alert shows "Password change is required..."
  - Cancel button disabled in force mode
  - Form fields unchanged (current_password + new_password + confirm_password)
  - Submit works normally regardless of mode
  - TypeScript compiles without error

tests_to_run:
  - cd frontend && npx tsc --noEmit

source_reference: C:\py_dev\mkobi\.ai\plans\PLAN_01.md
source_section: Wave 4 — TASK_013
</task>

<task>
id: TASK_014_useauth_force_redirect

title: Handle force password redirect in useAuth.ts login and silent refresh

status: pending

priority: medium

depends_on:
  - TASK_010_apitypes_force_flag

description: >
  Modify `frontend/src/features/auth/model/useAuth.ts` to handle force password
  redirect. (1) In the `login()` callback: check `response.user.force_password_change`
  after successful API login. If true, navigate to `/profile/change-password?force=true`.
  Otherwise navigate to `/dashboards`. Accept `navigate` as parameter.
  (2) In the silent refresh `useEffect`: if profile has `force_password_change` true,
  navigate to `/profile/change-password?force=true`.

goals:
  - login() returns AuthResponse data to caller instead of handling navigation internally
    OR login() accepts navigate callback
  - If force_password_change: redirect to change-password with force param
  - Silent refresh also checks force_password_change
  - LoginForm no longer handles navigation independently

files:
  - path: frontend/src/features/auth/model/useAuth.ts
    targets:
      - type: function
        name: login
      - type: useEffect
        name: silent_refresh
    semantic_anchors:
      insert_after:
        type: statement
        name: setUser(response.user)
      modify:
        type: useEffect
        name: silent_refresh_block

changes:
  - action: modify_login
    description: >
      Modify the login callback to return the AuthResponse data instead of
      handling navigation. Remove internal navigation from useAuth. The caller
      (LoginForm) will receive the response and navigate based on
      `force_password_change`.
    code_hint: |
      # Change from:
      const login = useCallback(async (email: string, password: string) => {
        setIsLoading(true)
        try {
          const response = await apiLogin(email, password)
          setToken(response.access_token)
          setUser(response.user)
        } catch (error) {
          removeToken()
          setUser(null)
          throw error
        } finally {
          setIsLoading(false)
        }
      }, [])

      # Change to:
      const login = useCallback(async (email: string, password: string) => {
        setIsLoading(true)
        try {
          const response = await apiLogin(email, password)
          setToken(response.access_token)
          setUser(response.user)
          return response
        } catch (error) {
          removeToken()
          setUser(null)
          throw error
        } finally {
          setIsLoading(false)
        }
      }, [])

      # In the silent refresh useEffect, after setUser(profile), add:
      if (profile.force_password_change) {
        window.location.href = '/profile/change-password?force=true'
      }

  - action: modify_silent_refresh
    description: >
      In the silent refresh useEffect (the block starting `if (!token)`),
      after fetching the profile, check if profile.force_password_change is true.
      If so, note that the user should be redirected. Since we can't navigate in
      useEffect without navigate, use a flag approach: check profile data and
      set a state that ProtectedRoute or a wrapper can observe.

      For silent refresh: after `setUser(profile)`, check
      `profile.force_password_change`. If true, use `window.location.href` to
      navigate to `/profile/change-password?force=true` (avoids navigate()
      dependency inside useEffect).

acceptance_criteria:
  - login() returns the AuthResponse (including user data)
  - No navigation logic inside useAuth.login()
  - LoginForm can check response.user.force_password_change
  - Silent refresh checks profile.force_password_change and redirects via window.location.href
  - TypeScript compiles without error

tests_to_run:
  - cd frontend && npx tsc --noEmit

source_reference: C:\py_dev\mkobi\.ai\plans\PLAN_01.md
source_section: Wave 4 — TASK_014
</task>

<task>
id: TASK_015_loginform_force_redirect

title: Update LoginForm.tsx for force redirect based on login response

status: pending

priority: medium

depends_on:
  - TASK_014_useauth_force_redirect

description: >
  Modify `frontend/src/features/auth/ui/LoginForm.tsx` to handle the force
  password change redirect. After `await login(data.email, data.password)`,
  check `response.user.force_password_change`. If true, navigate to
  `/profile/change-password?force=true`. Otherwise navigate to `/dashboards`.
  Since login() now returns the AuthResponse, adjust the call accordingly.
  Keep the existing `void` for the non-force path but change the destination.

goals:
  - After login, check user.force_password_change
  - Redirect to force change-password or dashboards accordingly
  - Minimal change to existing LoginForm logic
  - No useAuth-internal navigation (handled in LoginForm)

files:
  - path: frontend/src/features/auth/ui/LoginForm.tsx
    targets:
      - type: component
        name: LoginForm
    semantic_anchors:
      modify:
        type: statement
        name: await login(data.email, data.password)

changes:
  - action: modify_onSubmit
    description: >
      Change the onSubmit handler to capture the login response and branch
      navigation based on force_password_change.
    code_hint: |
      # FROM:
      await login(data.email, data.password)
      void navigate('/dashboards')

      # TO:
      const response = await login(data.email, data.password)
      if (response.user.force_password_change) {
        void navigate('/profile/change-password?force=true')
      } else {
        void navigate('/dashboards')
      }

acceptance_criteria:
  - LoginForm captures response from login()
  - Branches navigation based on force_password_change
  - Normal users go to /dashboards
  - Force-change users go to /profile/change-password?force=true
  - TypeScript compiles without error

tests_to_run:
  - cd frontend && npx tsc --noEmit

source_reference: C:\py_dev\mkobi\.ai\plans\PLAN_01.md
source_section: Wave 4 — TASK_015
</task>

<task>
id: TASK_016_verify_phase01

title: Verify Phase 01 — Admin Password Reset end-to-end

status: pending

priority: high

type: verification

depends_on:
  - TASK_007_admin_reset_endpoint
  - TASK_008_approve_sets_force_flag
  - TASK_012_usermanagement_reset_button
  - TASK_013_change_password_force_mode
  - TASK_014_useauth_force_redirect
  - TASK_015_loginform_force_redirect

verifies:
  - TASK_007_admin_reset_endpoint
  - TASK_008_approve_sets_force_flag
  - TASK_012_usermanagement_reset_button
  - TASK_013_change_password_force_mode
  - TASK_014_useauth_force_redirect
  - TASK_015_loginform_force_redirect

verification_steps:
  - build: docker compose build
  - test: ruff check src/mkobi/ && mypy src/mkobi/ && cd frontend && npx tsc --noEmit
  - smoke_check: >
      1. Start services: docker compose up -d
      2. Login as admin
      3. Navigate to User Management
      4. Click "Reset Password" for a non-admin user
      5. Verify ConfirmDialog appears with Confirm/Cancel, buttons disabled + spinner on confirm
      6. On success, verify ResetPasswordResultDialog shows temp password, Copy, Close
      7. Copy button copies to clipboard + shows "Copied" toast
      8. Close button dismisses dialog
      9. Login as the reset user with temp password
      10. Verify redirect to /profile/change-password?force=true
      11. Verify Cancel button disabled, info Alert visible
      12. Submit new password successfully
      13. Verify login works and user goes to /dashboards (flag cleared)
      14. Verify admin self-reset returns HTTP 400

pass_criteria:
  - All ruff/mypy checks pass
  - Frontend TypeScript compiles without errors
  - Full manual flow works end-to-end
  - force_password_change flag is set on reset and cleared on password change
  - Self-reset prevention returns appropriate error

failure_action: Return relevant implementation task(s) to rework

rollback_task: >
  Revert alembic migration (alembic downgrade -1),
  revert all modified source files to pre-phase state.

source_reference: C:\py_dev\mkobi\.ai\plans\PLAN_01.md
source_section: Wave 5 — TASK_016
</task>
