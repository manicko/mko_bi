# Research: Phase 01 — Secure Temp Password Delivery

**Date:** 2026-06-01
**Phase:** 01
**Scope:** Eliminate plaintext temporary passwords from API responses; implement one-time Redis-backed retrieval pattern.

---

## 1. Current State Analysis

### 1.1 Endpoints Returning Plaintext Passwords

**`POST /api/v1/admin/registration-requests/{id}/approve`** (`src/mkobi/api/routes/admin.py:208-268`)
- Returns `{"message": "...", "user_id": "...", "temp_password": "<plaintext>"}` (line 255-259)
- This is the critical endpoint that leaks passwords to response logs, browser history, and proxy caches.

**`POST /api/v1/admin/users/{id}/reset-password`** (`src/mkobi/api/routes/admin.py:127-170`)
- Delegates to `auth_service.reset_password_admin()` (line 146)
- `AuthService.reset_password_admin()` (`src/mkobi/services/auth_service.py:527-581`) returns `{"message": "...", "user_id": "...", "temp_password": "<plaintext>"}` (line 577-581)
- The admin route returns `result` directly, so the plaintext password flows through to the HTTP response.

### 1.2 Password Generation

`AuthService._generate_temp_password()` (`auth_service.py:508-525`):
- Uses `secrets.choice()` (cryptographically secure)
- Generates 16-char alphanumeric string
- Validates at least one letter + one digit
- Calls `validate_password_or_raise()` before use

### 1.3 Existing Redis Infrastructure

**Client:** `src/mkobi/core/redis_client.py`
- `get_redis_client()` — synchronous `redis.Redis` (used by RateLimiter)
- `get_async_redis_client()` — async `aioredis.Redis` (used by AsyncRateLimiter)
- Both use `decode_responses=True`
- Config comes from `Settings.redis` (host, port, db, password)

**Already used for:** Rate limiting (fail-open/fail-closed pattern in `core/security.py:47-111`)

**Configuration:** `Settings.redis` section in `config.py:133-140` with defaults host=localhost, port=6379, db=0.

### 1.4 Existing Frontend Pattern for Password Display

**`ResetPasswordResultDialog`** (`frontend/src/features/admin/ui/ResetPasswordResultDialog.tsx`):
- Receives `tempPassword` and `userEmail` as props
- Shows password in a read-only TextField with copy-to-clipboard button
- Used in `UserManagement.tsx` (line 206-211)
- The flow: `resetUserPassword()` mutation → on success, `setResetResult({tempPassword: data.temp_password, ...})` → dialog shows password

**`RegistrationRequests.tsx`** (`frontend/src/features/admin/ui/RegistrationRequests.tsx`):
- `approveMutation` calls `approveRequest()` then shows toast "Request approved successfully"
- No password handling — no result dialog shown after approval

### 1.5 Current API Types (adminApi.ts)

```typescript
// resetUserPassword returns { temp_password: string } — this must change
export async function resetUserPassword(userId: string): Promise<{
  message: string; user_id: string; temp_password: string
}>

// approveRequest currently returns Promise<void> — this must change
export async function approveRequest(requestId: string): Promise<void>
```

---

## 2. Requirements Summary (from DECISION_01.md)

### Locked Decisions

1. **Remove `temp_password` from all response bodies** — approval and reset endpoints must NOT return `temp_password` anywhere in JSON response.
2. **Response returns:** `message`, `user_id`, `retrieval_token` (random UUID).
3. **New endpoint:** `GET /api/v1/admin/temp-passwords/{retrieval_token}` — admin-only, returns password once, then deletes from Redis.
4. **Redis storage:** Key = retrieval token, Value = temp password, TTL = configurable (default 24h).
5. **Single-use:** On GET, return password and immediately delete the key from Redis.
6. **Admin role required** on both retrieval and approval/reset endpoints.
7. **No mail/SMTP** — out-of-band delivery only.
8. **`force_password_change` unchanged** — existing behavior preserved.

### Suggested Ideas

- Admin UI: After approval, show "Show Password" button that calls retrieval endpoint, displays in a `ResetPasswordResultDialog`-style modal with copy-to-clipboard.
- Retrieval approach is an abstraction layer — if email is added later, same Redis store serves as delivery queue.

### Out of Scope (Deferred)

- Retrieval audit trail
- Email delivery
- End-user self-service password setup

---

## 3. Implementation Architecture

### 3.1 Backend Changes

#### 3.1.1 New Utility: `TempPasswordStore`

Create `src/mkobi/core/temp_password_store.py`:

```python
class TempPasswordStore:
    """Manages temporary password storage in Redis for one-time retrieval.
    
    Uses Redis key pattern: "temp_pwd:{retrieval_token}"
    TTL defaults to 24 hours (configurable via settings).
    """
    
    def __init__(self, redis_client: aioredis.Redis, ttl_seconds: int = 86400) -> None:
        ...
    
    async def store(self, token: str, password: str) -> None:
        """Store password with TTL. Key = f"temp_pwd:{token}"."""
        ...
    
    async def retrieve(self, token: str) -> str | None:
        """Retrieve and delete password. Returns None if not found or expired."""
        ...
```

**Key design decisions:**
- Use `aioredis.Redis` (async) to match the async route handlers
- Key pattern: `temp_pwd:{retrieval`token}` for easy Redis scanning/debugging
- `retrieve()` must be atomic: GET + DELETE in a single operation. Use `GETDEL` command (Redis 6.2+) or Lua script / pipeline for older versions.
  - Since `redis` package is already in dependencies and Redis version is not specified, use pipeline approach for compatibility:
    ```
    MULTI
    GET temp_pwd:{token}
    DEL temp_pwd:{token}
    EXEC
    ```
- TTL default: 86400 seconds (24 hours). Should be configurable via `Settings` — add `TEMP_PASSWORD_TTL_SECONDS` environment variable with default 86400.

#### 3.1.2 Settings Change

Add to `Settings` in `config.py`:
- `temp_password_ttl_seconds: int = Field(default=86400, alias="TEMP_PASSWORD_TTL_SECONDS")` — with a reasonable range validator.

#### 3.1.3 AuthService Modification

**Method:** `reset_password_admin()` (`auth_service.py:527-581`)
- **After** generating the password and saving the hash to the DB, store the plaintext password in Redis via `TempPasswordStore`.
- **Instead of** returning `temp_password` in the dict, return `retrieval_token` (a new `uuid4()`).
- Signature change: Return dict becomes `{"message": "...", "user_id": "...", "retrieval_token": "..."}`.

**No change to `_generate_temp_password()` or `create_user()` logic.**

#### 3.1.4 Admin Route: `approve_registration_request_admin_endpoint`

**File:** `api/routes/admin.py:208-268`
- After user creation, generate a `retrieval_token = str(uuid4())`.
- Store temp password in Redis via `TempPasswordStore` (need to inject it or use AuthService).
- Return `{"message": "...", "user_id": "...", "retrieval_token": "..."}` — **no `temp_password`**.

**Design choice for Redis injection in approval route:** The approval route does NOT go through `AuthService` for the password generation — it calls `auth_service._generate_temp_password()` directly. So the `TempPasswordStore` should be used directly in the route, OR we refactor to pass the store through AuthService. Best approach: inject `TempPasswordStore` into the route handler (via DI pattern, similar to how `AsyncRateLimiter` is used in AuthService) and store the password right there.

Actually, cleaner approach: modify `AuthService` to accept a `TempPasswordStore` and have it store the password during `reset_password_admin()` AND have the approval route also use `AuthService` for the full flow. But the approval route has custom logic (fetching registration request, setting status, etc.) that shouldn't be in AuthService.

**Cleanest approach:** The route handler generates the password, creates the user, then stores in Redis. We can inject `TempPasswordStore` as a dependency or instantiate it inline.

#### 3.1.5 New Route: `GET /api/v1/admin/temp-passwords/{retrieval_token}`

**File:** `api/routes/admin.py`
- Add `require_admin_role` dependency.
- Use `TempPasswordStore.retrieve(token)`.
- Return `{"temp_password": "<value>"}` if found.
- Return 404 if not found (expired or never existed).
- Use `NotFoundException` from `utils/exceptions.py` for consistent error format.

#### 3.1.6 Dependency Injection

Add to `api/deps.py`:
```python
from mkobi.core.temp_password_store import TempPasswordStore

def get_temp_password_store() -> TempPasswordStore:
    config = get_config()
    redis_client = get_async_redis_client()
    return TempPasswordStore(redis_client, ttl_seconds=config.temp_password_ttl_seconds)
```

### 3.2 Frontend Changes

#### 3.2.1 adminApi.ts — Updated Type Signatures

```typescript
// resetUserPassword: temp_password → retrieval_token
export async function resetUserPassword(userId: string): Promise<{
  message: string; user_id: string; retrieval_token: string
}>

// approveRequest: returns retrieval_token instead of void
export async function approveRequest(requestId: string): Promise<{
  message: string; user_id: string; retrieval_token: string
}>

// NEW: retrieveTempPassword
export async function retrieveTempPassword(retrievalToken: string): Promise<{
  temp_password: string
}>
```

#### 3.2.2 UserManagement.tsx — Refactor Reset Flow

- `resetPasswordMutation` success handler: instead of showing the temp_password directly, store `retrieval_token` and trigger a "Show Password" dialog.
- Add a new state: `pendingRetrievalToken: string | null` — set when reset succeeds.
- Show a new "Show Password" dialog/button that:
  1. Calls `retrieveTempPassword(token)` API
  2. On success, shows the `ResetPasswordResultDialog` with the password
  3. On failure (404), shows toast "Password expired or already retrieved"

**Pattern follows:** The existing `ResetPasswordResultDialog` component already exists and can be reused. We just need to add a "confirmation → retrieve → show" flow instead of "show directly from response."

#### 3.2.3 RegistrationRequests.tsx — Add Password Retrieval After Approval

- `approveMutation` success handler: instead of just showing a toast, store the `retrieval_token` and show a `TempPasswordRetrievalDialog` (or reuse the existing pattern).
- Add a "Show Password" dialog step after approval, same as UserManagement.
- Reuse `ResetPasswordResultDialog` for showing the password — it takes `tempPassword` and `userEmail`.

### 3.3 Pydantic Models

No new backend Pydantic models needed — the existing response dicts are inline. The `retrieval_token` is just a string field in the response dict.

---

## 4. Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| Redis unavailable when storing password | Medium | Log error but don't fail the approval — user can be re-approved. Consider adding a warning in the response. |
| Redis unavailable when retrieving password | Low | Return 503 with `error_code: "SERVICE_UNAVAILABLE"` — admin can retry later if password hasn't expired. |
| TOCTOU race on GET+DEL | Low | Use Redis pipeline (MULTI/EXEC) for atomic read-and-delete. |
| Token collision | Negligible | UUID4 provides 2^122 bits of entropy. |
| Clock skew on TTL | Low | Redis handles TTL internally; no application clock dependency. |
| Approval succeeds but Redis store fails | Medium | Should the entire approval be rolled back? No — because the password is already hashed and saved. Better to return a warning and let admin re-approve if needed. |

---

## 5. Test Strategy

### Backend Tests (pytest)
1. `TempPasswordStore` unit tests:
   - Store then retrieve returns password
   - Second retrieve returns None (single-use)
   - Expired token returns None
   - Redis unavailable on store raises appropriate error
   - Redis unavailable on retrieve returns None/raises

2. Route tests:
   - `POST /admin/registration-requests/{id}/approve` returns `retrieval_token` (not `temp_password`)
   - `POST /admin/users/{id}/reset-password` returns `retrieval_token` (not `temp_password`)
   - `GET /admin/temp-passwords/{valid_token}` returns `temp_password`
   - `GET /admin/temp-passwords/{invalid_token}` returns 404
   - `GET /admin/temp-passwords/{already_used_token}` returns 404
   - Non-admin cannot access retrieval endpoint (403)
   - Expired token returns 404

### Frontend Tests
1. `adminApi.ts` type changes compile
2. `UserManagement.tsx`: reset flow shows "Show Password" dialog, retrieves, shows password
3. `RegistrationRequests.tsx`: approve flow shows password retrieval dialog

---

## 6. File Inventory

### Files to Create
1. `src/mkobi/core/temp_password_store.py` — Redis-backed temp password storage
2. `tests/core/test_temp_password_store.py` — unit tests for TempPasswordStore
3. `tests/api/test_temp_password_retrieval.py` — integration tests for new endpoint

### Files to Modify
1. `src/mkobi/config.py` — add `temp_password_ttl_seconds` setting
2. `src/mkobi/services/auth_service.py` — `reset_password_admin()` to store in Redis and return `retrieval_token`
3. `src/mkobi/api/routes/admin.py` — modify approve/reset endpoints, add retrieval endpoint
4. `src/mkobi/api/deps.py` — add `get_temp_password_store` DI factory
5. `src/mkobi/interfaces/service_interfaces.py` — update `reset_password_admin` return type annotation
6. `frontend/src/features/admin/api/adminApi.ts` — update type signatures, add `retrieveTempPassword`
7. `frontend/src/features/admin/ui/UserManagement.tsx` — refactor reset flow to use retrieval token
8. `frontend/src/features/admin/ui/RegistrationRequests.tsx` — add password retrieval after approval

### Files NOT to Modify (out of scope)
- `src/mkobi/models/user.py` — no model changes needed
- `src/mkobi/models/enums.py` — no new enums needed
- `src/mkobi/core/security.py` — no changes to password generation/hashing
- `src/mkobi/db/` — no DB schema changes
- `alembic/` — no migrations needed
- `ResetPasswordResultDialog.tsx` — reusable as-is

---

## 7. Rollout Order

1. **Backend: `TempPasswordStore`** — foundation, no dependencies on other changes
2. **Backend: Settings + DI** — config and dependency injection
3. **Backend: AuthService `reset_password_admin`** — store in Redis, return token
4. **Backend: Admin route approve endpoint** — store in Redis, return token
5. **Backend: New retrieval endpoint** — `GET /admin/temp-passwords/{token}`
6. **Frontend: API layer** — update types, add `retrieveTempPassword`
7. **Frontend: UserManagement** — refactor reset flow
8. **Frontend: RegistrationRequests** — add password retrieval after approval
9. **Tests** — backend unit + integration, frontend component tests

---

## 8. Open Questions

1. **Should the approval endpoint rollback if Redis store fails?** Recommendation: No. The user is already created with a hashed password. The admin can re-approve (which generates a new password). Log a warning.

2. **Should we add a `TEMP_PASSWORD_TTL_SECONDS` config or hardcode 24h?** Recommendation: Add config with 24h default. This follows the existing pattern (e.g., `STALE_PROCESSING_TIMEOUT_MINUTES`).

3. **Should the retrieval endpoint return the password in the body or as a header?** Recommendation: JSON body `{"temp_password": "..."}`. Consistent with existing API patterns. The password is already in transit over HTTPS.

4. **Do we need to handle the case where Redis is down during `store()`?** Recommendation: Catch the exception, log it as an error, and still return success to the admin (the user was created). The admin can re-approve if needed. This follows the fail-open pattern used by the rate limiter.
