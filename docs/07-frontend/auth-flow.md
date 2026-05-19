---
id: frontend-auth-flow
domain: frontend
tags:
  - jwt
  - token-storage
  - login-flow
  - registration-flow
  - role-based-access
  - email-validation
  - session-expiration
related:
  - frontend-security
  - pages
  - auth-api
  - frontend-architecture
---

# Frontend Auth Flow

## Overview

Authentication in the frontend is handled by the `auth` feature (`features/auth/`). The flow uses JWT tokens issued by the FastAPI backend, with a `useAuth` hook providing auth state to the entire application.

## JWT Token Storage

Token storage behavior differs between production and development environments, controlled by `import.meta.env.PROD` in `features/auth/model/authToken.ts`:

### Production (Memory-Only)

- Tokens are stored in a **module-level JavaScript variable** (`memoryToken`).
- Tokens are never written to `localStorage` or `sessionStorage`.
- **Security benefit:** Not vulnerable to XSS-based token exfiltration via browser storage APIs.
- **Trade-off:** Tokens are lost on full page reload or navigation (user must log in again).

### Development (sessionStorage Fallback)

- Tokens are stored in `sessionStorage` under the key `access_token`.
- **Convenience benefit:** Tokens survive page refreshes and hot-reloads during development.
- **Security trade-off:** `sessionStorage` is accessible to any JavaScript running on the page (XSS risk).
- Tokens are cleared when the tab is closed.

### Token Expiration Check

Every API request triggers an expiration check via `getTokenWithExpirationCheck()`:

1. Decode the JWT payload (base64).
2. Read the `exp` field.
3. If `Date.now() >= exp * 1000`, the token is removed and `null` is returned.
4. The Axios request interceptor then sends the request without a token, resulting in a `401` from the backend.

## Login Flow

```
Browser                          FastAPI
  │                                │
  │  POST /api/v1/auth/login       │
  │  { email, password }           │
  │ ──────────────────────────────►│
  │                                │ ┌──────────────────────┐
  │                                │ │ Rate limit check      │
  │                                │ │ (5 attempts / 5 min)  │
  │                                │ └──────────┬───────────┘
  │                                │            │
  │                                │ ┌──────────▼───────────┐
  │                                │ │ Verify bcrypt hash     │
  │                                │ └──────────┬───────────┘
  │                                │            │
  │                                │ ┌──────────▼───────────┐
  │                                │ │ Create JWT token      │
  │                                │ │ {user_id, email,      │
  │                                │ │  role, exp}           │
  │                                │ └──────────┬───────────┘
  │                                │            │
  │  200 OK                        │            │
  │  { access_token, token_type,    │            │
  │    user: { id, email, role,     │            │
  │      display_name, created_at } │            │
  │  }                              │            │
  │ ◄──────────────────────────────│            │
  │                                │
  │  Store token in memory/storage │
  │  Set user in useAuth state     │
  │  Redirect to /dashboards       │
```

### Steps

1. User submits the login form (`LoginForm.tsx`) with email and password.
2. Form is validated via Zod (`loginSchema`): email format, password min 6 characters.
3. `POST /api/v1/auth/login` is called via Axios.
4. On success (`200`): token is stored, user profile (including `display_name`) is set in `useAuth` state, redirect to `/dashboards`.
5. On failure (`401`/`429`): error alert is displayed.

## Registration Request Flow

```
Browser              FastAPI              Database
  │                    │                    │
  │  POST /auth/       │                    │
  │  register-request  │                    │
  │  { email }         │                    │
  │───────────────────►│                    │
  │                    │  Rate limit check  │
  │                    │  (3/hour per IP)   │
  │                    │                    │
  │                    │  Validate email    │
  │                    │  Check blocklist   │
  │                    │                    │
  │                    │  INSERT            │
  │                    │───────────────────►│
  │                    │  registration_     │
  │                    │  requests          │
  │                    │  (status=pending)  │
  │                    │◄───────────────────│
  │                    │                    │
  │  201 Created       │                    │
  │  { message, id }   │                    │
  │◄───────────────────│                    │
  │                    │                    │
  │  Show success      │                    │
  │  message           │                    │
```

### Steps

1. User submits the registration form (`RegisterForm.tsx`) with email.
2. Form is validated via Zod (`registerSchema`): email format + domain blocklist check.
3. `POST /api/v1/auth/register-request` is called.
4. On success (`201`): success message is displayed.
5. Admin reviews and approves the request via the Admin Panel.
6. On approval, a temporary password is generated and returned to the admin.

## Role-Based Access Control

### Route-Level Protection

Two guard components enforce access control at the route level:

**`ProtectedRoute`** (`shared/components/ProtectedRoute.tsx`):
- Checks if `useAuth().user` is set.
- If not authenticated: redirects to `/login` (preserving the intended destination in `location.state`).
- If loading: shows a `CircularProgress` spinner.

**`RoleBasedAccess`** (`shared/components/RoleBasedAccess.tsx`):
- Checks if `useAuth().user.role` is in the allowed `roles` array.
- If authorized: renders children.
- If unauthorized: renders `fallback` (defaults to `null`).

### Route Access Matrix

| Route | Guard | Allowed Roles |
| --- | --- | --- |
| `/login`, `/register` | None | Public |
| `/dashboards` | `ProtectedRoute` | All authenticated |
| `/dashboard/:id` | `ProtectedRoute` | All authenticated |
| `/admin` | `ProtectedRoute` + `RoleBasedAccess` | `admin` only |
| `/profile` | `ProtectedRoute` | All authenticated |
| `/profile/change-password` | `ProtectedRoute` | All authenticated |

### UI-Level Role Checks

Beyond route guards, individual UI elements are conditionally rendered based on role:

- **Upload button** on Dashboard View: visible only for `admin` and `editor`.
- **Delete Account** button on Profile page: visible only for non-admin users.
- **Admin link** in navigation: visible only for `admin`.

## Email Validation

Email validation is applied on both frontend and backend:

### Frontend (Zod)

```typescript
// Login
email: z.string().email('Invalid email format')

// Registration
email: z.string()
  .email('Invalid email format')
  .refine((email) => {
    const domain = email.split('@')[1]
    return domain && !BLOCKED_DOMAINS.includes(domain)
  }, 'This email domain is not allowed')
```

Blocked domains are defined in `shared/types/formSchemas.ts`: `tempmail.com`, `throwawaymail.com`.

### Backend (Pydantic)

The backend independently validates email format and checks against a configurable domain blocklist. Frontend validation is a UX convenience; backend validation is the security boundary.

## Session Expiration Handling

When a session expires (token expires or is invalidated):

1. The next API call returns `401`.
2. The Axios response interceptor catches the `401`.
3. Token is removed from storage.
4. Error toast is displayed: "Session expired. Please login again."
5. User is redirected to `/login`.

## Cross-References

- [Frontend Security](frontend-security.md) — JWT security, CORS, file upload security
- [Pages](pages.md) — Page-level access control details
- [Authentication API](../../01-auth/auth-api.md) — Backend auth endpoint specifications
- [Frontend Architecture](architecture.md) — HTTP client interceptor details
- [Access Control](../../08-security/access-control.md) — Route guards and permission model
- [Admin API](../../04-admin/admin-api.md) — Registration approval flow
