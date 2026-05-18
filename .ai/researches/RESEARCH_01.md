# 01 Phase 1: Authorization - Research

**Researched:** 2026-05-18
**Domain:** Authorization, Access Control, Registration Flow, Profile Management (FastAPI + React)
**Confidence:** HIGH

## Summary

The codebase has substantial auth infrastructure already implemented: JWT login/logout, registration request flow with admin approval, change password, role-based route guards, dashboard access control (view/edit/admin), and a complete frontend with React Router + TanStack Query + Material UI. However, there are specific gaps between the current implementation and the locked decisions in DECISION_01.md that must be addressed.

**Primary recommendation:** Focus on 7 specific modifications: (1) admin bypass for dashboard listing, (2) registration request duplicate-handling with status-specific messages, (3) blacklisted domain error message wording, (4) login response missing user data, (5) profile page missing display name, (6) header navigation restructuring, and (7) 403 handling for direct dashboard URL access.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | >=0.110.0 | Backend API | Existing, async, Pydantic integration |
| React 18+ | 18.x | Frontend SPA | Existing, FSD architecture |
| Material UI | v5 | UI components | Existing, used throughout |
| TanStack Query | v5 | Server state | Existing, handles caching |
| React Hook Form + Zod | - | Form validation | Existing, type-safe |
| Axios | - | HTTP client | Existing, interceptors for JWT |
| python-jose | >=3.3.0 | JWT encode/decode | Existing |
| bcrypt | >=5.0.0 | Password hashing | Existing |
| SQLAlchemy 2.0 | >=2.0.29 | Async ORM | Existing |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|--------------|
| react-hot-toast | - | Notifications | Existing, used for success/errors |
| react-router-dom | v6 | Routing | Existing, ProtectedRoute pattern |

**Installation:** No new packages needed. All required libraries are already in `pyproject.toml` and `package.json`.

## Architecture Patterns

### Recommended Project Structure (existing, no changes needed)
```
src/mkobi/
├── api/routes/
│   ├── auth.py          # Login, register-request, change-password, /me
│   ├── admin.py         # User management, registration approval/rejection
│   ├── dashboards.py    # Dashboard CRUD + access management
│   └── users.py         # DELETE /users/me (self-deletion)
├── core/
│   ├── permissions.py   # check_dashboard_access, role hierarchy
│   └── security.py      # JWT create/decode, bcrypt, rate limiter
├── services/
│   ├── auth_service.py  # register_request, login, change_password
│   └── dashboard_service.py  # get_user_dashboards, grant/revoke access
├── models/
│   ├── auth.py          # Pydantic models for auth endpoints
│   ├── user.py          # UserRead, UserCreate, etc.
│   ├── enums.py         # UserRole, RegistrationStatus, DashboardPermission
│   └── dashboard.py     # DashboardRead, DashboardCreate, etc.
└── db/
    ├── models/          # SQLAlchemy models (User, RegistrationRequest, etc.)
    └── repositories/    # DashboardRepository, RegistrationRequestRepository, etc.

frontend/src/
├── features/auth/
│   ├── api/authApi.ts       # login, registerRequest, getProfile
│   ├── model/useAuth.ts     # Auth state management
│   ├── model/authToken.ts   # Token storage (memory/sessionStorage)
│   └── ui/LoginForm.tsx, RegisterForm.tsx
├── features/users/
│   ├── api/userApi.ts       # getProfile, deleteAccount, changePassword
│   └── ui/UserProfile.tsx, ChangePasswordPage.tsx
├── features/dashboards/ui/DashboardList.tsx
├── shared/
│   ├── api/axiosInstance.ts  # Axios with JWT interceptors
│   ├── components/ProtectedRoute.tsx
│   ├── components/RoleBasedAccess.tsx
│   ├── components/Layout/Header.tsx, AppLayout.tsx, Sidebar.tsx
│   └── types/api.types.ts, formSchemas.ts, enums.ts
└── app/routes.tsx, providers.tsx
```

### Pattern 1: Admin Bypass for Dashboard Access

**What:** Admins should see ALL dashboards without needing explicit `dashboard_access` rows.
**Current state:** `DashboardRepository.get_by_user()` JOINs with `dashboard_access` table, so admins only see dashboards they have explicit access entries for.
**Required change:** Modify `get_by_user()` to check if the user is admin first. If admin, return all dashboards via `get_all()`. Otherwise, filter by `dashboard_access` as currently done.

```python
# In DashboardRepository.get_by_user():
# 1. Get user from DB to check role
# 2. If user.role == UserRole.ADMIN, return await self.get_all(db)
# 3. Otherwise, existing JOIN query
```

**Confidence:** HIGH - This is a straightforward repository modification.

### Pattern 2: Registration Request Duplicate Handling

**What:** When a user submits a registration request, the system must check for existing requests and return status-specific error messages.
**Current state:** `AuthService.register_request()` checks for existing request and raises `ValueError("Registration request with email '{email}' already exists")` — a single generic message regardless of status.
**Required changes:**
- If existing request is `pending` or `approved` → `"A request for this email already exists"`
- If existing request is `rejected` → `"Your request was rejected. Contact an administrator for more information."`
- The check must happen BEFORE the blocked domain check (per DECISION_01.md: rejected users should see rejection message, not domain block)

```python
# In AuthService.register_request():
existing = await self.reg_request_repo.get_by_email(email, db)
if existing is not None:
    if existing.status in (RegistrationStatus.PENDING, RegistrationStatus.APPROVED):
        raise ValueError("A request for this email already exists")
    elif existing.status == RegistrationStatus.REJECTED:
        raise ValueError("Your request was rejected. Contact an administrator for more information.")
```

**Confidence:** HIGH - Simple conditional logic change in existing code.

### Pattern 3: Blacklisted Email Domain Error

**What:** When a user registers with a blocked domain, the error message must be explicit.
**Current state:** `AuthService.register_request()` raises `ValueError("Registration with email domain '{email_domain}' is not allowed")`.
**Required change:** Change message to `"This email domain is not allowed for registration"` (exact wording from DECISION_01.md).

**Confidence:** HIGH - Single string change.

### Pattern 4: Login Response Missing User Data

**What:** The frontend `useAuth.login()` expects `response.user` after login, but the backend `/auth/login` endpoint returns only `{access_token, token_type}` (the `Token` model).
**Current state:** Backend returns `Token(access_token=..., token_type="bearrer")`. Frontend `AuthResponse` type expects `{access_token, token_type, user: UserProfile}`. The `user` field is `undefined` after login.
**Required change:** Either:
- (Option A) Modify the login endpoint to return `AuthResponse` with user data embedded (requires DB query for user)
- (Option B) Have the frontend call `/auth/me` separately after login to get user data

**Recommendation:** Option A is better UX (one fewer round-trip). Modify the login endpoint to return user data alongside the token.

```python
# In auth.py login endpoint:
token_data = await auth_service.login_user(email, password)
# Also fetch user and include in response
user = await auth_service.get_user_by_id(token_data["user_id"])
return {"access_token": token_data["access_token"], "token_type": "bearer", "user": user}
```

**Confidence:** HIGH - Well-understood pattern, just needs alignment between frontend expectation and backend response.

### Pattern 5: Profile Page Display Name

**What:** The profile page must show a read-only "Display name" field derived from the email prefix (before @).
**Current state:** `UserProfile.tsx` shows email and role but NOT display name. The `UserRead` Pydantic model and `User` DB model do not have a `display_name` field.
**Required changes:**
- Add a `display_name` property or field that extracts the prefix from email (e.g., `"user@example.com"` → `"user"`)
- This can be a computed property on `UserRead` (no DB migration needed): `display_name: str` derived from `email.split('@')[0]`
- Add the display name field to the profile page UI (read-only, between email and role)

```python
# In models/user.py - UserRead:
class UserRead(UserBase):
    id: UUID
    created_at: datetime
    display_name: str = ""  # Can be computed property
    
    @model_validator(mode='after')
    def set_display_name(self):
        if not self.display_name:
            self.display_name = self.email.split('@')[0]
        return self
```

**Confidence:** HIGH - Simple computed field, no DB changes needed.

### Pattern 6: Header Navigation Restructuring

**What:** DECISION_01.md specifies: narrow top navigation bar on all pages except login; navigation buttons right-to-left; rightmost button is "Profile" (no dropdown).
**Current state:** `Header.tsx` shows email text, then Profile button, Admin button (conditional), and Logout button. Login and Register pages are rendered inside `AppLayout` (which includes Header).
**Required changes:**
- Remove Login and Register routes from inside `AppLayout` — they should render WITHOUT the Header
- Restructure Header: rightmost = "Profile", then other nav buttons to the left
- Remove email display from header (email shown only on Profile page)
- Remove the dropdown pattern (current Header already has flat buttons, which is correct)

```tsx
// In routes.tsx - move login/register OUTSIDE AppLayout:
<Route path="/login" element={<LoginForm />} />
<Route path="/register" element={<RegisterForm />} />
<Route element={<AppLayout />}>
  {/* All protected routes */}
</Route>
```

**Confidence:** HIGH - Simple routing restructure.

### Pattern 7: 403 Handling for Direct Dashboard URL Access

**What:** When a non-admin user accesses a dashboard URL directly without access, they should see 403 "Access denied" (revealing the dashboard exists).
**Current state:** `DashboardService.get_dashboard()` returns `None` when access is denied, and the endpoint returns 404 "Dashboard not found". The `check_dashboard_access()` function in `permissions.py` properly checks access but the dashboard endpoint uses `require_viewer_role` dependency which only checks global role, not dashboard-level access.
**Required changes:**
- The `GET /dashboards/{dashboard_id}` endpoint needs to distinguish between "dashboard doesn't exist" (404) and "user has no access" (403)
- Currently it returns 404 for both cases
- Modify the endpoint to return 403 "Access denied" when the dashboard exists but user has no access

```python
# In dashboards.py get_dashboard_endpoint:
dashboard = await dashboard_service.get_dashboard(dashboard_id, user_id=current_user.id, db=db)
if dashboard is None:
    # Check if dashboard exists at all (without access check)
    exists = await dashboard_service.dashboard_repo.get(dashboard_id, db)
    if exists:
        raise HTTPException(status_code=403, detail="Access denied")
    raise HTTPException(status_code=404, detail="Dashboard not found")
```

**Confidence:** MEDIUM - Requires careful implementation to avoid information leakage for truly non-existent dashboards.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JWT authentication | Custom token logic | python-jose + bcrypt | Existing, battle-tested |
| Password hashing | Custom hashing | bcrypt (existing) | Industry standard, timing-safe |
| Route protection | Custom middleware | ProtectedRoute component (existing) | React Router pattern |
| Role-based UI | Custom role checks | RoleBasedAccess component (existing) | Already implemented |
| Form validation | Manual validation | Zod schemas (existing) | Type-safe, declarative |
| API error handling | Custom interceptors | Axios interceptors (existing) | Already handles 401 |
| Token storage | localStorage | Memory/sessionStorage (existing authToken.ts) | XSS-resistant |

## Common Pitfalls

### Pitfall 1: Admin Bypass Not Applied Consistently

**What goes wrong:** Admin bypass is added to `get_user_dashboards` but not to `get_dashboard` (single dashboard access), so admins can't access individual dashboards they don't have explicit access entries for.
**Why it happens:** Two different code paths for listing vs. single access.
**How to apply:** Both `DashboardRepository.get_by_user()` AND `DashboardService.get_dashboard()` need admin bypass logic.
**Warning signs:** Admin sees dashboard list but gets 404 when clicking on a dashboard they didn't create.

### Pitfall 2: Registration Status Check Order

**What goes wrong:** Blocked domain check runs BEFORE duplicate registration check, so a rejected user with a blocked domain sees the wrong error message.
**Why it happens:** Current code checks blocked domain before checking existing registration.
**How to fix:** Check existing registration request FIRST, then blocked domain, then existing user.
**Warning signs:** Rejected users with blocked domain emails see "domain not allowed" instead of "request was rejected".

### Pitfall 3: Login Response /auth/me Race Condition

**What goes wrong:** If the frontend relies on a separate `/auth/me` call after login, there's a brief window where `user` is null, causing redirect to login page.
**Why it happens:** Token is set but profile hasn't loaded yet.
**How to fix:** Include user data in the login response (Option A above), eliminating the race condition.
**Warning signs:** Flash of login page after successful login, or ProtectedRoute redirecting immediately after login.

### Pitfall 4: Header Shown on Login/Register Pages

**What goes wrong:** Moving login/register outside AppLayout means they lose the Header, but the current routes.tsx has them inside.
**Why it happens:** AppLayout wraps all routes including login/register.
**How to fix:** Restructure routes so login/register are sibling routes to AppLayout, not children.
**Warning signs:** Header with "Profile" button visible on login page.

### Pitfall 5: 403 vs 404 Information Leakage

**What goes wrong:** Returning 403 for "no access" and 404 for "not found" reveals whether a dashboard exists.
**Why it happens:** DECISION_01.md explicitly requires 403 "Access denied" which reveals existence.
**How to fix:** This is intentional per the spec. The 403 response is the desired behavior.
**Warning signs:** N/A — this is by design per DECISION_01.md.

## Code Examples

### Admin Bypass in Repository (Pattern 1)

```python
# In DashboardRepository.get_by_user():
async def get_by_user(self, user_id: UUID, db: AsyncSession) -> list[Dashboard]:
    # Check if user is admin
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user and user.role == UserRole.ADMIN:
        return await self.get_all(db)
    
    # Existing JOIN query for non-admin users
    result = await db.execute(
        select(Dashboard)
        .join(DashboardAccess)
        .where(DashboardAccess.user_id == user_id)
    )
    return list(result.scalars().all())
```

### Registration Duplicate Handling (Pattern 2)

```python
# In AuthService.register_request():
existing_request = await self.reg_request_repo.get_by_email(email, db)
if existing_request is not None:
    if existing_request.status in (RegistrationStatus.PENDING, RegistrationStatus.APPROVED):
        raise ValueError("A request for this email already exists")
    elif existing_request.status == RegistrationStatus.REJECTED:
        raise ValueError("Your request was rejected. Contact an administrator for more information.")
```

### Login Endpoint with User Data (Pattern 4)

```python
# In auth.py login endpoint:
token_data = await auth_service.login_user(email, password)
# Fetch user for response
from mkobi.db.repositories.user_repo import UserRepository
user_repo = UserRepository()
user = await user_repo.get_by_email(email=email, db=db)
return {
    "access_token": token_data["access_token"],
    "token_type": "bearer",
    "user": UserRead.model_validate(user)
}
```

### Display Name on Profile (Pattern 5)

```python
# In models/user.py:
class UserRead(UserBase):
    id: UUID
    created_at: datetime
    display_name: str = ""
    
    @model_validator(mode='after')
    def set_display_name(self):
        if not self.display_name and self.email:
            self.display_name = self.email.split('@')[0]
        return self
```

### Route Restructure for Login/Register (Pattern 6)

```tsx
// In app/routes.tsx:
export function AppRoutes() {
  return (
    <Routes>
      {/* Public routes WITHOUT header */}
      <Route path="/login" element={<LoginForm />} />
      <Route path="/register" element={<RegisterForm />} />
      
      {/* Protected routes WITH header */}
      <Route element={<AppLayout />}>
        <Route path="/dashboards" element={<ProtectedRoute><DashboardList /></ProtectedRoute>} />
        {/* ... other protected routes ... */}
      </Route>
    </Routes>
  )
}
```

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|-----------------|--------|
| Single error for all duplicate registration attempts | Status-specific messages (pending/approved vs rejected) | Better UX, clearer communication |
| Admin needs explicit dashboard_access rows | Admin bypass — sees all dashboards | Simplified admin experience |
| Login returns only token | Login returns token + user data | Fewer API calls, no race condition |
| Header on all pages | Header only on authenticated pages | Cleaner login/register UX |
| 404 for both "not found" and "no access" | 403 for "no access", 404 for "not found" | Proper HTTP semantics per spec |

## Open Questions

1. **Should the login endpoint return user data or should frontend call /auth/me separately?**
   - What we know: Frontend expects `user` in login response. Backend doesn't provide it.
   - What's unclear: Whether the team prefers one round-trip (modify login) or two (keep separate calls).
   - Recommendation: Modify login endpoint to include user data. This eliminates a race condition and is consistent with the frontend's existing `AuthResponse` type.

2. **Should `display_name` be a DB field or computed?**
   - What we know: DECISION_01.md says "email prefix before @" — no separate name field.
   - What's unclear: Whether to store in DB or compute on-the-fly.
   - Recommendation: Compute from email (no DB migration needed). Add as a property on `UserRead`.

3. **Does the admin bypass apply to dashboard detail endpoint too?**
   - What we know: DECISION_01.md says "admins see and can do everything on all dashboards."
   - What's unclear: Whether `GET /dashboards/{id}` also needs admin bypass or just the list endpoint.
   - Recommendation: Yes, apply to both list AND detail endpoints. Admin should access any dashboard directly.

## Sources

### Primary (HIGH confidence)
- `src/mkobi/api/routes/auth.py` — Existing auth endpoints (login, register-request, change-password, /me)
- `src/mkobi/api/routes/admin.py` — Admin endpoints (approve/reject registration)
- `src/mkobi/api/routes/dashboards.py` — Dashboard CRUD with access control
- `src/mkobi/api/routes/users.py` — DELETE /users/me endpoint
- `src/mkobi/api/deps.py` — DI, auth dependencies, role checks
- `src/mkobi/core/permissions.py` — check_dashboard_access, role hierarchy
- `src/mkobi/services/auth_service.py` — register_request with duplicate check
- `src/mkobi/services/dashboard_service.py` — get_user_dashboards, get_dashboard
- `src/mkobi/db/repositories/dashboard_repo.py` — get_by_user (needs admin bypass)
- `src/mkobi/db/repositories/registration_request_repo.py` — get_by_email returns status
- `src/mkobi/models/enums.py` — UserRole, RegistrationStatus, DashboardPermission
- `src/mkobi/models/user.py` — UserRead (missing display_name)
- `src/mkobi/models/auth.py` — Token, ChangePasswordRequest
- `src/mkobi/config.py` — EmailSettings.blocked_domains
- `frontend/src/features/auth/model/useAuth.ts` — login expects user in response
- `frontend/src/features/auth/api/authApi.ts` — login returns AuthResponse with user
- `frontend/src/features/auth/model/authToken.ts` — Token storage
- `frontend/src/shared/api/axiosInstance.ts` — Axios interceptors
- `frontend/src/shared/components/ProtectedRoute.tsx` — Route protection
- `frontend/src/shared/components/Layout/Header.tsx` — Current header (needs restructure)
- `frontend/src/app/routes.tsx` — Route structure (login/register inside AppLayout)
- `frontend/src/features/users/ui/UserProfile.tsx` — Profile page (missing display_name)
- `frontend/src/features/dashboards/ui/DashboardList.tsx` — Already shows empty state message
- `docs/SPEC.md` — Full API specification

### Secondary (HIGH confidence)
- `src/mkobi/db/models/user.py` — User DB model (no display_name field, has email)
- `src/mkobi/db/models/registration_request.py` — RegistrationRequest model with status field
- `frontend/src/shared/types/api.types.ts` — AuthResponse type (expects user field)
- `frontend/src/shared/types/formSchemas.ts` — Zod schemas with blocked domain check

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — All libraries already in use, no new dependencies needed
- Architecture: HIGH — Existing patterns well-established, modifications are targeted
- Pitfalls: HIGH — Identified from direct code inspection, not speculation
- Registration flow changes: HIGH — Simple conditional logic modifications
- Admin bypass: HIGH — Straightforward repository pattern modification
- Frontend changes: HIGH — Existing components need minor additions, not rewrites

**Research date:** 2026-05-18
**Valid until:** 30 days (stable codebase, no major refactoring expected)
