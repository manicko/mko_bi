---
id: auth-api
domain: auth
tags:
  - authentication
  - jwt
  - login
  - registration
  - rate-limiting
  - password
  - security
related:
  - security-overview
  - access-control
  - admin-api
  - frontend-auth-flow
---

# Authentication API

## Overview

The authentication API provides endpoints for user login, registration, token management, and password changes. All endpoints are part of the `/api/v1/auth` route group.

**Authentication method:** JWT (JSON Web Token) with bcrypt password hashing. See [Frontend Auth Flow](../07-frontend/auth-flow.md) for token storage strategy and login flow details.

**Base path:** `/api/v1/auth`

---

## Endpoints

### 1. Login

Authenticate a user by email and password.

| Attribute      | Value                                      |
| -------------- | ------------------------------------------ |
| **Method**     | `POST`                                     |
| **Path**       | `/api/v1/auth/login`                       |
| **Auth level** | Public                                     |
| **Rate limit** | 5 attempts per 5 minutes per IP            |

**Request body:**

```json
{
  "email": "user@example.com",
  "password": "secure_password123"
}
```

**Response** (`200 OK`):

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "role": "viewer",
    "display_name": "user",
    "created_at": "2026-04-24T16:02:46+03:00"
  }
}
```

> The login response now includes the full user profile (`TokenWithUser` model), eliminating the need for a separate `/auth/me` call after login. The `display_name` field is computed from the email prefix (text before `@`).

**Error responses:**

| Status | Condition            | Detail                       |
| ------ | -------------------- | ---------------------------- |
| `401`  | Invalid credentials  | `Invalid credentials`        |
| `429`  | Rate limit exceeded  | `Too many login attempts...` |

---

### 2. Login (OAuth2 Form)

Authenticate a user via OAuth2 password flow (form-encoded).

| Attribute      | Value                                      |
| -------------- | ------------------------------------------ |
| **Method**     | `POST`                                     |
| **Path**       | `/api/v1/auth/login/form`                  |
| **Auth level** | Public                                     |
| **Rate limit** | 5 attempts per 5 minutes per IP            |

**Request:** `application/x-www-form-urlencoded` with `username` (email) and `password` fields.

**Response** (`200 OK`): Same as [Login](#1-login), including the `user` field.

---

### 3. Registration Request

Submit a registration request for a new account. The request must be approved by an admin before the user can log in.

| Attribute      | Value                                      |
| -------------- | ------------------------------------------ |
| **Method**     | `POST`                                     |
| **Path**       | `/api/v1/auth/register-request`            |
| **Auth level** | Public                                     |
| **Rate limit** | 3 attempts per hour per IP/email           |

**Request body:**

```json
{
  "email": "user@example.com"
}
```

**Response** (`201 Created`):

```json
{
  "message": "Request submitted",
  "id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error responses:**

| Status | Condition                        | Detail                                  |
| ------ | -------------------------------- | --------------------------------------- |
| `422`  | Email already registered         | Validation error message                |
| `422`  | Email domain blocklisted         | Validation error message                |
| `429`  | Rate limit exceeded              | `Too many registration requests...`     |

**Side effects:**
- Creates a row in the `registration_requests` table with status `pending`
- Records the requester's IP address (`requested_by_ip`)

---

### 4. Register (Admin Only)

Directly create a new user account. Requires admin role. This endpoint is deprecated for public use — public users should use `/auth/register-request` instead.

| Attribute      | Value                                      |
| -------------- | ------------------------------------------ |
| **Method**     | `POST`                                     |
| **Path**       | `/api/v1/auth/register`                    |
| **Auth level** | Admin                                      |

**Request body:**

```json
{
  "email": "user@example.com",
  "password": "secure_password123",
  "role": "viewer"
}
```

**Response** (`201 Created`):

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error responses:**

| Status | Condition                    | Detail                       |
| ------ | ---------------------------- | ---------------------------- |
| `403`  | Caller is not admin          | Forbidden                    |
| `422`  | Validation error             | Error message                |
| `500`  | Registration/token error     | `Registration error`         |

---

### 5. Refresh Token

Refresh an expired or soon-to-expire JWT access token.

| Attribute      | Value                                      |
| -------------- | ------------------------------------------ |
| **Method**     | `POST`                                     |
| **Path**       | `/api/v1/auth/refresh`                     |
| **Auth level** | Public (requires valid refresh token)      |

**Request body:**

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (`200 OK`):

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error responses:**

| Status | Condition                    | Detail                       |
| ------ | ---------------------------- | ---------------------------- |
| `401`  | Invalid or expired token     | `Invalid token`              |
| `401`  | User no longer exists        | `User not found`             |
| `500`  | Token creation error         | `Token creation error`       |

**Behavior:**
- Verifies the refresh token payload (user_id, email, role)
- Checks that the user still exists in the database
- Issues a new access token with fresh expiration

---

### 6. Get Current User

Retrieve the currently authenticated user's profile.

> **Note:** This endpoint is retained for backward compatibility. The preferred approach is to use the `user` field returned directly in the login response, which avoids an extra round-trip.

| Attribute      | Value                                      |
| -------------- | ------------------------------------------ |
| **Method**     | `GET`                                      |
| **Path**       | `/api/v1/auth/me`                          |
| **Auth level** | Any authenticated user                     |

**Request:** Requires `Authorization: Bearer <token>` header.

**Response** (`200 OK`):

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "role": "viewer",
  "display_name": "user",
  "created_at": "2026-04-24T16:02:46+03:00"
}
```

**Error responses:**

| Status | Condition                    | Detail                       |
| ------ | ---------------------------- | ---------------------------- |
| `401`  | Invalid or missing token     | Unauthorized                 |

---

### 7. Change Password

Change the current user's password.

| Attribute      | Value                                      |
| -------------- | ------------------------------------------ |
| **Method**     | `POST`                                     |
| **Path**       | `/api/v1/auth/change-password`             |
| **Auth level** | Any authenticated user                     |

**Request body:**

```json
{
  "current_password": "old_password123",
  "new_password": "new_secure_password456",
  "confirm_password": "new_secure_password456"
}
```

**Response** (`200 OK`):

```json
{
  "message": "Password changed successfully"
}
```

**Error responses:**

| Status | Condition                              | Detail                                   |
| ------ | -------------------------------------- | ---------------------------------------- |
| `400`  | Confirmation mismatch                  | `New password and confirmation do not match` |
| `401`  | Current password incorrect             | Error message                            |
| `500`  | Server error                           | `Password change error`                  |

**Notes:**
- The user remains logged in after a password change (token is not invalidated)
- New password must be at least 8 characters (enforced by frontend via Zod)

---

## Login Flow

```
Browser                          FastAPI
  │                                │
  │  POST /api/v1/auth/login       │
  │  { email, password }           │
  │ ──────────────────────────────►│
  │                                │ ┌─────────────────────┐
  │                                │ │ Rate limit check     │
  │                                │ │ (5 attempts / 5 min) │
  │                                │ └─────────┬───────────┘
  │                                │           │
  │                                │ ┌─────────▼───────────┐
  │                                │ │ Verify email exists  │
  │                                │ │ Check bcrypt hash    │
  │                                │ └─────────┬───────────┘
  │                                │           │
  │                                │ ┌─────────▼───────────┐
  │                                │ │ Create JWT token     │
  │                                │ │ {user_id, email,     │
  │                                │ │  role, exp}          │
  │                                │ └─────────┬───────────┘
  │                                │           │
  │  200 OK                        │           │
  │  { access_token, token_type }  │           │
  │ ◄──────────────────────────────│           │
  │                                │
  │  Store token in memory         │
  │  Redirect to /dashboards       │
```

1. User submits email and password via the login form (`/login` page)
2. Server applies rate limiting (5 attempts per 5-minute window per IP)
3. Server looks up user by email and verifies the bcrypt password hash
4. On success, server creates a JWT access token containing `user_id`, `email`, and `role`
5. Server returns `TokenWithUser` — the token plus the full user profile (including computed `display_name`)
6. Client stores the token and sets user state immediately (no separate `/me` call needed)
7. Client redirects to the dashboard list page

---

## Registration Flow

```
Browser              FastAPI              Database
  │                    │                    │
  │  POST /register-   │                    │
  │  request { email } │                    │
  │ ──────────────────►│                    │
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
  │ ◄──────────────────│                    │
  │                    │                    │
  │  User waits for    │                    │
  │  admin approval    │                    │
  │                    │                    │
  │         Admin Panel│                    │
  │         POST /admin/registration-       │
  │         requests/:id/approve            │
  │                    │───────────────────►│
  │                    │  Create user       │
  │                    │  Update request    │
  │                    │  (status=approved) │
  │                    │◄───────────────────│
  │                    │                    │
  │  Admin receives    │                    │
  │  temp_password     │                    │
  │  via response      │                    │
```

1. User submits their email on the registration page (`/register`)
2. Server applies rate limiting (3 requests per hour per IP/email)
3. Server validates the email format and checks against the domain blocklist
4. Server creates a `registration_requests` record with status `pending`
5. Admin reviews pending requests via the admin panel (`/admin`)
6. Admin approves the request — a user account is created with a random temporary password
7. Admin communicates the temporary password to the new user
8. New user logs in and changes their password

---

## Security Constraints

- **Password hashing:** bcrypt (never stored in plaintext)
- **JWT:** Signed tokens with expiration; payload contains `user_id`, `email`, `role`
- **Rate limiting:** Redis-based; fail-open by default, configurable to fail-closed
- **Email blocklist:** Configurable domain blocklist for registration requests
- **CORS:** Explicit allowed methods and headers (no wildcards in production)
- **Production credentials:** Default credentials (`admin`/`admin`) are rejected in production

---

## Cross-References

- [Security Overview](../08-security/) — CORS, rate limiting, credential enforcement
- [Auth & Access Control](./) — Authorization flows and role-based access
- [Access Control](./) — Dashboard-level permission enforcement
- [API Responsibilities](../SPEC.md#14-api-responsibilities-fastapi) — Full API endpoint listing
- [Frontend Auth Flow](../07-frontend/auth-flow.md) — JWT handling, login/registration flows, role-based UI
- [Access Control](../08-security/access-control.md) — Dashboard-level permission model and enforcement points
- [Admin API](../04-admin/admin-api.md) — User management and registration approval
