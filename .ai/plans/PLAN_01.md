---
phase: 01
title: "Secure Temp Password Delivery"
depends_on: []
risk_level: medium
autonomous: true
files_modified:
  backend:
    - src/mkobi/core/temp_password_store.py       # NEW
    - src/mkobi/config.py                          # MODIFY
    - src/mkobi/services/auth_service.py           # MODIFY
    - src/mkobi/api/routes/admin.py                # MODIFY
    - src/mkobi/api/deps.py                        # MODIFY
    - src/mkobi/interfaces/service_interfaces.py   # MODIFY
  frontend:
    - frontend/src/features/admin/api/adminApi.ts              # MODIFY
    - frontend/src/features/admin/ui/UserManagement.tsx        # MODIFY
    - frontend/src/features/admin/ui/RegistrationRequests.tsx  # MODIFY
  tests:
    - tests/core/test_temp_password_store.py                  # NEW
    - tests/api/test_temp_password_retrieval.py               # NEW
waves:
  - id: 1
    name: "Backend Foundation"
    tasks:
      - TASK_001_backend_temp_password_store
      - TASK_002_backend_settings_di
  - id: 2
    name: "Backend Endpoint Changes"
    tasks:
      - TASK_003_backend_auth_service_reset_password
      - TASK_004_backend_approve_endpoint
      - TASK_005_backend_retrieval_endpoint
  - id: 3
    name: "Frontend Changes"
    tasks:
      - TASK_006_frontend_api_types
      - TASK_007_frontend_user_management
      - TASK_008_frontend_registration_requests
  - id: 4
    name: "Tests & Verification"
    tasks:
      - TASK_009_backend_tests
      - TASK_010_verify_phase_01

must_haves:
  - "No `temp_password` field in any API response body (approve or reset)"
  - "Approve and reset endpoints return `retrieval_token` (UUID string)"
  - "New GET endpoint `GET /api/v1/admin/temp-passwords/{retrieval_token}` returns password once"
  - "Password stored in Redis with TTL (default 24h), deleted after retrieval"
  - "Retrieval endpoint requires admin role"
  - "Admin UI shows password after approval/reset via retrieval flow (not from response)"
  - "force_password_change behavior unchanged"
  - "No SMTP/email service added"
---

# Phase 01: Secure Temp Password Delivery — Plan

## Goal
Eliminate plaintext temporary passwords from HTTP response bodies. Replace with a one-time retrieval pattern using Redis-backed storage.

## Architecture Overview

```
Admin clicks "Approve" / "Reset Password"
    → Backend generates temp password
    → Backend hashes password → saves to DB (force_password_change=True)
    → Backend stores plaintext in Redis (key=token, TTL=24h)
    → Response returns {message, user_id, retrieval_token}
    → Frontend shows "Show Password" button
    → Admin clicks "Show Password"
    → Frontend calls GET /admin/temp-passwords/{token}
    → Backend retrieves + deletes from Redis
    → Frontend shows password in dialog with copy-to-clipboard
```

## Tasks

---

### TASK_001_backend_temp_password_store

**File:** `src/mkobi/core/temp_password_store.py` (NEW)

Create `TempPasswordStore` class:

```python
import logging
from typing import Final

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

_KEY_PREFIX: Final[str] = "temp_pwd:"


class TempPasswordStore:
    """Redis-backed one-time temporary password storage.

    Passwords are stored with a TTL and deleted immediately upon retrieval.
    Uses Redis pipeline for atomic GET+DELETE to prevent TOCTOU races.
    """

    def __init__(self, redis_client: aioredis.Redis, ttl_seconds: int = 86400) -> None:
        self._redis = redis_client
        self._ttl = ttl_seconds

    async def store(self, token: str, password: str) -> None:
        """Store a temporary password under the given token with TTL."""
        key = f"{_KEY_PREFIX}{token}"
        try:
            await self._redis.set(key, password, ex=self._ttl)
            logger.info("Temp password stored for token %s... (TTL=%ds)", token[:8], self._ttl)
        except Exception as exc:
            # Fail-open: log error but don't crash the calling flow
            logger.error("Failed to store temp password in Redis: %s", exc)

    async def retrieve(self, token: str) -> str | None:
        """Retrieve and delete a temporary password. Returns None if not found."""
        key = f"{_KEY_PREFIX}{token}"
        try:
            # Atomic GET+DELETE using pipeline for compatibility
            async with self._redis.pipeline(transaction=True) as pipe:
                pipe.get(key)
                pipe.delete(key)
                results = await pipe.execute()
            password = results[0]
            if password is not None:
                logger.info("Temp password retrieved for token %s...", token[:8])
            else:
                logger.warning("Temp password not found for token %s...", token[:8])
            return password
        except Exception as exc:
            logger.error("Failed to retrieve temp password from Redis: %s", exc)
            return None
```

**Acceptance criteria:**
- Class instantiates with `aioredis.Redis` client and TTL
- `store()` writes to Redis with `temp_pwd:{token}` key and TTL
- `retrieve()` atomically GET+DELETE via pipeline, returns password or None
- `store()` failures are caught and logged (fail-open)
- `retrieve()` failures return None (graceful degradation)

---

### TASK_002_backend_settings_di

**Files:**
- `src/mkobi/config.py` (MODIFY)
- `src/mkobi/api/deps.py` (MODIFY)

**config.py changes:**

Add field to `Settings` class (after the `rate_limiter_fail_closed` field, ~line 283):
```python
temp_password_ttl_seconds: int = Field(default=86400, alias="TEMP_PASSWORD_TTL_SECONDS")
```

Add `@field_validator` to ensure minimum TTL of 60 seconds:
```python
@field_validator("temp_password_ttl_seconds")
@classmethod
def validate_ttl(cls, value: int) -> int:
    if value < 60:
        raise ValueError("TEMP_PASSWORD_TTL_SECONDS must be at least 60 seconds")
    return value
```

Also add `clear_temp_password_store_cache()` — SKIP this. No caching needed for the store.

**deps.py changes:**

Add factory function:
```python
from mkobi.core.temp_password_store import TempPasswordStore
from mkobi.core.redis_client import get_async_redis_client
from mkobi.config import get_config

def get_temp_password_store() -> TempPasswordStore:
    config = get_config()
    return TempPasswordStore(
        redis_client=get_async_redis_client(),
        ttl_seconds=config.temp_password_ttl_seconds,
    )
```

Export in `__all__`.

**Acceptance criteria:**
- `TEMP_PASSWORD_TTL_SECONDS` env var accepted, default 86400
- Values below 60 are rejected
- `get_temp_password_store()` returns properly configured `TempPasswordStore`

---

### TASK_003_backend_auth_service_reset_password

**File:** `src/mkobi/services/auth_service.py` (MODIFY)
**Also:** `src/mkobi/interfaces/service_interfaces.py` (MODIFY)

**`auth_service.py` changes to `reset_password_admin()` (line 527-581):**

1. Add `temp_password_store: TempPasswordStore | None = None` parameter to `__init__()`:
   ```python
   def __init__(
       self,
       user_repo: IUserRepository,
       reg_request_repo: IRegistrationRequestRepository,
       config: Any | None = None,
       temp_password_store: TempPasswordStore | None = None,
   ) -> None:
       ...
       self.temp_password_store = temp_password_store
   ```

2. In `reset_password_admin()`, after generating `temp_password` and before returning:
   - Generate `retrieval_token = str(uuid4())`
   - If `self.temp_password_store` is not None, call `await self.temp_password_store.store(retrieval_token, temp_password)`
   - Return `{"message": "Password reset successfully", "user_id": str(user_id), "retrieval_token": retrieval_token}` — NO `temp_password` key

**`service_interfaces.py` changes:**

Update `IAuthService.__init__()` signature to include `temp_password_store` parameter.

Update `IAuthService.reset_password_admin()` return type: the return dict no longer contains `temp_password`.

**Acceptance criteria:**
- `reset_password_admin()` returns `retrieval_token` instead of `temp_password`
- Password is stored in Redis when `temp_password_store` is provided
- No `temp_password` in any return path
- When `temp_password_store` is None, no Redis call is made (backward compatibility for tests)

---

### TASK_004_backend_approve_endpoint

**File:** `src/mkobi/api/routes/admin.py` (MODIFY)

**Changes to `approve_registration_request_admin_endpoint` (line 208-268):**

1. Add dependency injection: `temp_password_store: TempPasswordStore = Depends(get_temp_password_store)` to the function signature.

2. Import additions:
   ```python
   from uuid import uuid4
   from mkobi.core.temp_password_store import TempPasswordStore
   from mkobi.api.deps import get_temp_password_store
   ```

3. After line 238 (`user = await auth_service.create_user(...)`) and after `force_password_change` update (line 242-244):
   - Generate `retrieval_token = str(uuid4())`
   - Call `await temp_password_store.store(retrieval_token, temp_password)` — using the `temp_password` variable already generated on line 233

4. Change return dict (line 255-259) to:
   ```python
   return {
       "message": "Registration request approved",
       "user_id": str(user.id),
       "retrieval_token": retrieval_token,
   }
   ```
   **NO `temp_password` key.**

**Acceptance criteria:**
- Approve endpoint returns `retrieval_token` (not `temp_password`)
- Password stored in Redis before response
- `force_password_change=True` still set (unchanged)
- DB commit happens after Redis store (non-critical if Redis fails)

---

### TASK_005_backend_retrieval_endpoint

**File:** `src/mkobi/api/routes/admin.py` (MODIFY)

Add new endpoint after the existing registration request endpoints (after line 318):

```python
@router.get(
    "/temp-passwords/{retrieval_token}",
    status_code=status.HTTP_200_OK,
    summary="Retrieve temporary password (admin)",
    description="Returns a one-time temporary password. Admin only. Password is deleted after retrieval.",
    dependencies=[Depends(require_admin_role)],
)
async def retrieve_temp_password_admin_endpoint(
    retrieval_token: str,
    temp_password_store: TempPasswordStore = Depends(get_temp_password_store),
) -> dict[str, str]:
    """Retrieve a temporary password by its retrieval token (one-time, admin only)."""
    logger.info("Admin: retrieving temp password: token=%s...", retrieval_token[:8])
    password = await temp_password_store.retrieve(retrieval_token)
    if password is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Temporary password not found or already retrieved",
        )
    return {"temp_password": password}
```

Import `get_temp_password_store` and `TempPasswordStore` if not already imported.

**Acceptance criteria:**
- HTTP GET endpoint at `/api/v1/admin/temp-passwords/{retrieval_token}`
- Requires admin role (`require_admin_role`)
- Returns `{"temp_password": "<value>"}` on success (HTTP 200)
- Returns HTTP 404 if token not found, expired, or already retrieved
- Password is deleted from Redis upon retrieval (single-use)

---

### TASK_006_frontend_api_types

**File:** `frontend/src/features/admin/api/adminApi.ts` (MODIFY)

1. Change `resetUserPassword` return type:
   ```typescript
   export async function resetUserPassword(userId: string): Promise<{
     message: string
     user_id: string
     retrieval_token: string
   }> {
     const response = await axiosInstance.post<{
       message: string
       user_id: string
       retrieval_token: string
     }>(`/admin/users/${userId}/reset-password`)
     return response.data
   }
   ```

2. Change `approveRequest` to return data instead of `Promise<void>`:
   ```typescript
   export async function approveRequest(requestId: string): Promise<{
     message: string
     user_id: string
     retrieval_token: string
   }> {
     const response = await axiosInstance.post<{
       message: string
       user_id: string
       retrieval_token: string
     }>(`/admin/registration-requests/${requestId}/approve`)
     return response.data
   }
   ```

3. Add new function:
   ```typescript
   export async function retrieveTempPassword(retrievalToken: string): Promise<{
     temp_password: string
   }> {
     const response = await axiosInstance.get<{ temp_password: string }>(
       `/admin/temp-passwords/${retrievalToken}`
     )
     return response.data
   }
   ```

**Acceptance criteria:**
- `resetUserPassword` returns `retrieval_token` (no `temp_password`)
- `approveRequest` returns `{message, user_id, retrieval_token}`
- `retrieveTempPassword` is a new exported function
- TypeScript compilation passes (no type errors)

---

### TASK_007_frontend_user_management

**File:** `frontend/src/features/admin/ui/UserManagement.tsx` (MODIFY)

**Changes:**

1. Add state for pending retrieval token:
   ```typescript
   const [pendingRetrievalToken, setPendingRetrievalToken] = useState<string | null>(null)
   const [showPasswordMode, setShowPasswordMode] = useState(false)
   ```

2. Modify `resetPasswordMutation` success handler (line 61-73):
   ```typescript
   onSuccess: (data, variables) => {
     void queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
     setPendingRetrievalToken(data.retrieval_token)
     setShowPasswordMode(true)
     toast.success('Password reset successfully')
   },
   ```

3. Add a `TempPasswordDialog` component (inline in same file or separate):
   - Shows when `showPasswordMode` is true
   - Has a "Show Password" button that calls `retrieveTempPassword(pendingRetrievalToken)`
   - On success: shows password in a `ResetPasswordResultDialog` (reuse existing component)
   - On 404: shows toast "Password expired or already retrieved"
   - Also shows "Retrieve" then "Copy" pattern matching `ResetPasswordResultDialog`

   Simpler approach: Reuse `ResetPasswordResultDialog` but add a "Retrieve Password" button that triggers the API call first, then shows the password.

4. Add the dialog at the bottom of the component (alongside existing `ResetPasswordResultDialog`):
   ```tsx
   {showPasswordMode && (
     <RetrievePasswordDialog
       open={showPasswordMode}
       retrievalToken={pendingRetrievalToken ?? ''}
       userEmail={/* find user email from users array */}
       onClose={() => {
         setShowPasswordMode(false)
         setPendingRetrievalToken(null)
       }}
     />
   )}
   ```

   Create `RetrievePasswordDialog` component in the same file:
   - Calls `retrieveTempPassword(token)` on mount or on button click
   - Shows loading state while fetching
   - On success, shows `ResetPasswordResultDialog` with the password
   - On error (404), shows error message and close button

**Acceptance criteria:**
- After reset, admin sees a dialog with "Show Password" button
- Clicking "Show Password" calls the retrieval API
- Password is displayed in a dialog with copy-to-clipboard
- If token expired, shows error message
- No `temp_password` is ever read from the reset/approve response

---

### TASK_008_frontend_registration_requests

**File:** `frontend/src/features/admin/ui/RegistrationRequests.tsx` (MODIFY)

**Changes:**

1. Add state:
   ```typescript
   const [pendingRetrievalToken, setPendingRetrievalToken] = useState<string | null>(null)
   const [approvedEmail, setApprovedEmail] = useState<string>('')
   const [showPasswordMode, setShowPasswordMode] = useState(false)
   ```

2. Modify `approveMutation` success handler (line 27-35):
   ```typescript
   onSuccess: (data) => {
     void queryClient.invalidateQueries({ queryKey: ['admin', 'registration-requests'] })
     setPendingRetrievalToken(data.retrieval_token)
     setApprovedEmail(selectedRequest?.email ?? '')
     setShowPasswordMode(true)
     setConfirmDialogOpen(false)
     toast.success('Request approved successfully')
   },
   ```

3. Add `RetrievePasswordDialog` (same component from TASK_007, or import if extracted to shared):
   ```tsx
   {showPasswordMode && (
     <RetrievePasswordDialog
       open={showPasswordMode}
       retrievalToken={pendingRetrievalToken ?? ''}
       userEmail={approvedEmail}
       onClose={() => {
         setShowPasswordMode(false)
         setPendingRetrievalToken(null)
       }}
     />
   )}
   ```

**Acceptance criteria:**
- After approval, admin sees a dialog to retrieve the password
- Same retrieve → show → copy flow as UserManagement
- No `temp_password` read from approve response

---

### TASK_009_backend_tests

**Files:**
- `tests/core/test_temp_password_store.py` (NEW)
- `tests/api/test_temp_password_retrieval.py` (NEW)

**`test_temp_password_store.py` — Unit tests:**

1. `test_store_and_retrieve` — store a password, retrieve it, verify it matches
2. `test_retrieve_single_use` — retrieve twice, second returns None
3. `test_retrieve_nonexistent_token` — returns None
4. `test_store_failure_logged` — mock Redis error, verify exception is caught and logged
5. `test_retrieve_failure_returns_none` — mock Redis error, returns None

**`test_temp_password_retrieval.py` — Integration tests:**

1. `test_approve_returns_retrieval_token` — POST approve, verify response has `retrieval_token`, no `temp_password`
2. `test_reset_returns_retrieval_token` — POST reset, verify response has `retrieval_token`, no `temp_password`
3. `test_retrieve_valid_token` — POST approve → GET temp-passwords/{token}, verify password returned
4. `test_retrieve_single_use` — GET twice, second returns 404
5. `test_retrieve_invalid_token` — GET with random token, returns 404
6. `test_retrieve_requires_admin` — non-admin gets 403
7. `test_retrieve_expired_token` — (use short TTL in test config) wait for expiry, GET returns 404

**Acceptance criteria:**
- All tests pass with `pytest`
- Tests use `fakeredis` or a test Redis instance
- No `temp_password` in any response assertion

---

### TASK_010_verify_phase_01

**Verification task — depends on: TASK_001 through TASK_009**

**Verification steps:**

1. **Build check:** `cd frontend && npm run build` — no TypeScript errors
2. **Lint check:** `ruff check src/` — no lint errors
3. **Type check:** `mypy src/mkobi/` — no type errors
4. **Test check:** `pytest tests/core/test_temp_password_store.py tests/api/test_temp_password_retrieval.py -v` — all pass
5. **Smoke check:** Start the app, call approve endpoint, verify `retrieval_token` in response, call retrieval endpoint, verify password returned
6. **Security check:** Grep entire codebase for `temp_password` in response dicts — only the retrieval endpoint should return it

**Pass criteria:**
- All checks pass
- No `temp_password` in approve or reset endpoint responses
- Retrieval endpoint works end-to-end
- Frontend compiles without errors

**Failure action:** Return relevant implementation task(s) to rework.
