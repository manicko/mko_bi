---
id: admin-api
domain: admin
tags:
  - user-management
  - registration-requests
  - processing-logs
  - admin-panel
  - roles
  - approval-flow
related:
  - auth-api
  - dashboards-api
  - processing-api
  - schema-access
  - security-overview
---

# Admin API

## Overview

The admin API provides endpoints for user management, registration request processing, and system monitoring. All admin endpoints require the `admin` role unless otherwise specified.

**Base path:** `/api/v1`

---

## User Management Endpoints

These endpoints allow admins to manage user accounts. Some endpoints are also accessible to non-admin users for self-management.

### 1. List All Users

Retrieve a list of all registered users. Admin only.

| Attribute      | Value                          |
| -------------- | ------------------------------ |
| **Method**     | `GET`                          |
| **Path**       | `/api/v1/users`                |
| **Auth level** | Admin                          |

**Response** (`200 OK`):

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "admin@example.com",
    "role": "admin",
    "is_active": true,
    "created_at": "2026-04-24T16:02:46+03:00"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "email": "editor@example.com",
    "role": "editor",
    "is_active": true,
    "created_at": "2026-04-25T10:00:00+03:00"
  }
]
```

---

### 2. Get User Detail

Retrieve a single user by ID. Accessible to the user themselves or to admins.

| Attribute      | Value                          |
| -------------- | ------------------------------ |
| **Method**     | `GET`                          |
| **Path**       | `/api/v1/users/:id`            |
| **Auth level** | Self or Admin                  |

**Path parameters:**

| Parameter | Type   | Description        |
| --------- | ------ | ------------------ |
| `id`      | UUID   | User ID            |

**Response** (`200 OK`):

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "admin@example.com",
  "role": "admin",
  "is_active": true,
  "created_at": "2026-04-24T16:02:46+03:00"
}
```

**Error responses:**

| Status | Condition                    | Detail                       |
| ------ | ---------------------------- | ---------------------------- |
| `403`  | Caller is not self or admin  | Forbidden                    |
| `404`  | User not found               | `User not found`             |

---

### 3. Create User

Directly create a new user account with a specified role. Admin only. This endpoint accepts a JSON request body (Pydantic `UserCreateRequest`).

| Attribute      | Value                          |
| -------------- | ------------------------------ |
| **Method**     | `POST`                         |
| **Path**       | `/api/v1/users`                |
| **Auth level** | Admin                          |

**Request body:**

```json
{
  "email": "newuser@example.com",
  "password": "initial_password123",
  "role": "editor"
}
```

**Response** (`201 Created`): User detail object.

**Error responses:**

| Status | Condition                    | Detail                       |
| ------ | ---------------------------- | ---------------------------- |
| `403`  | Caller is not admin          | Forbidden                    |
| `422`  | Duplicate email              | Validation error             |
| `422`  | Invalid role value           | Validation error             |

---

### 4. Update User Role (via /users)

Change the role of an existing user. Admin only. This endpoint accepts a JSON request body (Pydantic `UserUpdateRequest`).

| Attribute      | Value                          |
| -------------- | ------------------------------ |
| **Method**     | `PATCH`                        |
| **Path**       | `/api/v1/users/{user_id}/role` |
| **Auth level** | Admin                          |

**Path parameters:**

| Parameter  | Type   | Description        |
| ---------- | ------ | ------------------ |
| `user_id`  | UUID   | User ID            |

**Request body:**

```json
{
  "role": "editor"
}
```

**Response** (`200 OK`): Updated user detail object.

**Error responses:**

| Status | Condition                    | Detail                       |
| ------ | ---------------------------- | ---------------------------- |
| `404`  | User not found               | `User not found`             |
| `422`  | Invalid role value           | Validation error             |

**Valid roles:** `admin`, `editor`, `viewer` (defined by `UserRole` StrEnum)

---

### 5. Delete User

Delete a user account. Admin only.

| Attribute      | Value                          |
| -------------- | ------------------------------ |
| **Method**     | `DELETE`                       |
| **Path**       | `/api/v1/users/:id`            |
| **Auth level** | Admin                          |

**Path parameters:**

| Parameter | Type   | Description        |
| --------- | ------ | ------------------ |
| `id`      | UUID   | User ID            |

**Response** (`204 No Content`)

**Error responses:**

| Status | Condition                    | Detail                       |
| ------ | ---------------------------- | ---------------------------- |
| `403`  | Caller is not admin          | Forbidden                    |
| `404`  | User not found               | `User not found`             |

---

### 6. Delete Own Account (Self-Deletion)

Allow a non-admin user to delete their own account.

| Attribute      | Value                          |
| -------------- | ------------------------------ |
| **Method**     | `DELETE`                       |
| **Path**       | `/api/v1/users/me`             |
| **Auth level** | Any authenticated user (non-admin only) |

**Response** (`204 No Content`)

**Error responses:**

| Status | Condition                    | Detail                       |
| ------ | ---------------------------- | ---------------------------- |
| `403`  | Caller is admin              | Admins cannot self-delete    |

---

## Admin-Only Endpoints

These endpoints are exclusively available under the `/api/v1/admin` path and require the `admin` role.

### 7. Admin: List Users

Admin-specific user listing (alternative to `/api/v1/users`).

| Attribute      | Value                          |
| -------------- | ------------------------------ |
| **Method**     | `GET`                          |
| **Path**       | `/api/v1/admin/users`          |
| **Auth level** | Admin                          |

**Response** (`200 OK`): Same format as [List All Users](#1-list-all-users).

---

### 8. Admin: Update User Role

Admin-specific role update (alternative to `/api/v1/users/:id/role`).

| Attribute      | Value                          |
| -------------- | ------------------------------ |
| **Method**     | `PATCH`                        |
| **Path**       | `/api/v1/admin/users/:id/role` |
| **Auth level** | Admin                          |

**Request body:**

```json
{
  "role": "viewer"
}
```

**Response** (`200 OK`): Updated user detail object.

---

### 9. Admin: Delete User

Admin-specific user deletion (alternative to `/api/v1/users/:id`).

| Attribute      | Value                          |
| -------------- | ------------------------------ |
| **Method**     | `DELETE`                       |
| **Path**       | `/api/v1/admin/users/:id`      |
| **Auth level** | Admin                          |

**Response** (`204 No Content`)

---

### 10. List Registration Requests

Retrieve all registration requests, optionally filtered by status.

| Attribute      | Value                          |
| -------------- | ------------------------------ |
| **Method**     | `GET`                          |
| **Path**       | `/api/v1/admin/registration-requests` |
| **Auth level** | Admin                          |

**Query parameters:**

| Parameter | Type   | Required | Description                                |
| --------- | ------ | -------- | ------------------------------------------ |
| `status`  | string | No       | Filter by status: `pending`, `approved`, `rejected` |

**Response** (`200 OK`):

```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "email": "applicant@example.com",
    "status": "pending",
    "requested_by_ip": "192.168.1.1",
    "reviewed_by": null,
    "reviewed_at": null,
    "created_at": "2026-05-18T10:00:00Z"
  }
]
```

---

### 11. Approve Registration Request

Approve a pending registration request. Creates a new user account with a randomly generated temporary password.

| Attribute      | Value                          |
| -------------- | ------------------------------ |
| **Method**     | `POST`                         |
| **Path**       | `/api/v1/admin/registration-requests/:id/approve` |
| **Auth level** | Admin                          |

**Path parameters:**

| Parameter | Type   | Description              |
| --------- | ------ | ------------------------ |
| `id`      | UUID   | Registration request ID  |

**Response** (`200 OK`):

```json
{
  "message": "Registration approved",
  "user_id": "880e8400-e29b-41d4-a716-446655440003",
  "temp_password": "xK9mP2nQ5rT8vW1y"
}
```

**Error responses:**

| Status | Condition                    | Detail                       |
| ------ | ---------------------------- | ---------------------------- |
| `403`  | Caller is not admin          | Forbidden                    |
| `404`  | Request not found            | `Registration request not found` |
| `409`  | Request already processed    | `Request is not pending`     |

**Side effects:**
- Creates a new user in the `users` table with the email from the request
- Sets the user's password to a cryptographically random temporary password
- Updates the `registration_requests` record: status → `approved`, `reviewed_by` → admin user ID, `reviewed_at` → current timestamp

> **Security Note:** The `temp_password` is returned in **plaintext JSON**. Ensure the following:
> - HTTPS is enforced in production — never transmit temp passwords over plain HTTP.
> - The temp password is **one-time use** — the user should be forced to change it on first login.
> - **Never log** the `temp_password` in application logs or audit trails.
> - The admin should communicate the temp password to the new user through a **secure out-of-band channel** (e.g., in person, encrypted messaging), not via the same email used for registration.

---

### 12. Reject Registration Request

Reject a pending registration request.

| Attribute      | Value                          |
| -------------- | ------------------------------ |
| **Method**     | `POST`                         |
| **Path**       | `/api/v1/admin/registration-requests/:id/reject` |
| **Auth level** | Admin                          |

**Path parameters:**

| Parameter | Type   | Description              |
| --------- | ------ | ------------------------ |
| `id`      | UUID   | Registration request ID  |

**Response** (`200 OK`):

```json
{
  "message": "Registration rejected"
}
```

**Error responses:**

| Status | Condition                    | Detail                       |
| ------ | ---------------------------- | ---------------------------- |
| `403`  | Caller is not admin          | Forbidden                    |
| `404`  | Request not found            | `Registration request not found` |
| `409`  | Request already processed    | `Request is not pending`     |

**Side effects:**
- Updates the `registration_requests` record: status → `rejected`, `reviewed_by` → admin user ID, `reviewed_at` → current timestamp

---

### 13. List Processing Logs

Retrieve processing logs with filtering and pagination. Admin only.

| Attribute      | Value                          |
| -------------- | ------------------------------ |
| **Method**     | `GET`                          |
| **Path**       | `/api/v1/admin/logs`           |
| **Auth level** | Admin                          |

**Query parameters:**

| Parameter      | Type      | Required | Description                                |
| -------------- | --------- | -------- | ------------------------------------------ |
| `status`       | string    | No       | Filter by status: `started`, `uploaded`, `processing`, `success`, `failed`, `completed` |
| `dashboard_id` | UUID      | No       | Filter by dashboard                        |
| `date_from`    | datetime  | No       | Filter logs with started_at >= this date    |
| `date_to`      | datetime  | No       | Filter logs with started_at <= this date    |
| `skip`         | integer   | No       | Number of records to skip (default: 0)     |
| `limit`        | integer   | No       | Maximum records to return (default: 100)  |

**Response** (`200 OK`):

```json
[
  {
    "id": "990e8400-e29b-41d4-a716-446655440004",
    "dashboard_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "success",
    "message": "Processing completed successfully",
    "started_at": "2026-05-18T12:00:00Z",
    "finished_at": "2026-05-18T12:01:30Z"
  }
]
```

---

### 14. Get Single Processing Log

Retrieve a single processing log entry by ID. Admin only.

| Attribute      | Value                          |
| -------------- | ------------------------------ |
| **Method**     | `GET`                          |
| **Path**       | `/api/v1/admin/logs/:log_id`   |
| **Auth level** | Admin                          |

**Path parameters:**

| Parameter | Type   | Description        |
| --------- | ------ | ------------------ |
| `log_id`  | UUID   | Processing log ID  |

**Response** (`200 OK`): Single processing log object.

---

## Registration Approval Flow

The registration approval flow is a multi-step process that bridges the authentication system and the admin panel.

```
Browser (User)        FastAPI              Database
  │                     │                     │
  │  POST /auth/        │                     │
  │  register-request   │                     │
  │  { email }          │                     │
  │────────────────────►│                     │
  │                     │  INSERT             │
  │                     │  registration_      │
  │                     │  requests           │
  │                     │────────────────────►│
  │                     │  (status=pending)   │
  │                     │◄────────────────────│
  │  201 Created        │                     │
  │  { message, id }    │                     │
  │◄────────────────────│                     │
  │                     │                     │
  │  ... Admin reviews request in panel ...   │
  │                     │                     │
  │  Browser (Admin)    │                     │
  │  POST /admin/       │                     │
  │  registration-      │                     │
  │  requests/:id/      │                     │
  │  approve            │                     │
  │────────────────────►│                     │
  │                     │                     │
  │                     │  Generate temp      │
  │                     │  password           │
  │                     │  (secrets.token_    │
  │                     │   urlsafe(16))      │
  │                     │                     │
  │                     │  INSERT users       │
  │                     │────────────────────►│
  │                     │  (bcrypt hash of    │
  │                     │   temp_password)    │
  │                     │◄────────────────────│
  │                     │                     │
  │                     │  UPDATE             │
  │                     │  registration_      │
  │                     │  requests           │
  │                     │────────────────────►│
  │                     │  (status=approved,  │
  │                     │   reviewed_by,      │
  │                     │   reviewed_at)      │
  │                     │◄────────────────────│
  │                     │                     │
  │  200 OK             │                     │
  │  { message,         │                     │
  │    user_id,         │                     │
  │    temp_password }  │                     │
  │◄────────────────────│                     │
  │                     │                     │
  │  Admin communicates │                     │
  │  temp_password to   │                     │
  │  new user           │                     │
```

### Temporary Password Generation

When a registration request is approved, the system generates a cryptographically random temporary password using `secrets.token_urlsafe(16)`. This password:

- Is generated using a cryptographically secure random number generator
- Is returned in the `temp_password` field of the approval response
- Is stored as a bcrypt hash in the `users` table (never in plaintext)
- Must be communicated to the new user by the admin through an available channel
- Should be changed by the user upon first login

---

## Admin Panel UI Pages

The admin panel is accessible at the `/admin` route and provides the following sections:

### User Management (`/admin`)

Displays a table of all users with the ability to change roles and delete users.

**Key operations:**
- View all users (email, role, active status, creation date)
- Change user role via dropdown (calls `PATCH /api/v1/admin/users/:id/role`)
- Delete a user (calls `DELETE /api/v1/admin/users/:id`)

**Related API endpoints:**
- `GET /api/v1/admin/users` — List all users
- `PATCH /api/v1/admin/users/:id/role` — Update role (body: `{"role": "editor"}`)
- `DELETE /api/v1/admin/users/:id` — Delete user

### Registration Requests (`/admin`)

Displays pending registration requests with approve/reject actions.

**Key operations:**
- View pending requests (email, IP, date submitted)
- Approve a request (calls `POST /api/v1/admin/registration-requests/:id/approve`)
- Reject a request (calls `POST /api/v1/admin/registration-requests/:id/reject`)
- View approved/rejected requests (filtered by status)

**Related API endpoints:**
- `GET /api/v1/admin/registration-requests` — List requests
- `POST /api/v1/admin/registration-requests/:id/approve` — Approve
- `POST /api/v1/admin/registration-requests/:id/reject` — Reject

### Dashboard Management (`/admin`)

Provides CRUD operations for dashboards, layouts, graphs, and filters.

**Related documentation:** [Dashboards API](../02-dashboards/dashboards-api.md)

### Log Viewer (`/admin`)

Displays processing logs with filtering and pagination.

**Key operations:**
- View processing logs (status, dashboard, timestamps)
- Filter by status (`started`, `uploaded`, `processing`, `success`, `failed`, `completed`)
- Filter by dashboard
- Filter by date range (`date_from`, `date_to`)
- Paginated navigation

**Related API endpoints:**
- `GET /api/v1/admin/logs` — List logs with filters (supports `status`, `dashboard_id`, `date_from`, `date_to`, `skip`, `limit`)
- `GET /api/v1/admin/logs/:log_id` — Get single log entry

### Dashboard Access Management (`/admin`)

Provides endpoints for managing user access to dashboards.

**Related API endpoints:**
- `POST /api/v1/dashboards/{id}/access` — Grant access
- `GET /api/v1/dashboards/{id}/access` — List access records
- `DELETE /api/v1/dashboards/{id}/access/{user_id}` — Revoke access

### Dashboard-Filter Binding (`/admin`)

Provides endpoints for binding filters to dashboards.

**Related API endpoints:**
- `POST /api/v1/dashboards/{id}/filters?filter_id=:id` — Bind filter
- `DELETE /api/v1/dashboards/{id}/filters/{filter_id}` — Unbind filter
- `GET /api/v1/dashboards/{id}/filters` — List bound filters

---

## Role & Permission Summary

| Role       | User CRUD | Registration Mgmt | Processing Logs | Dashboard CRUD |
| ---------- | --------- | ----------------- | --------------- | -------------- |
| `admin`    | Full      | Full              | Full            | Full           |
| `editor`   | None      | None              | None            | None           |
| `viewer`   | None      | None              | None            | None           |

All admin API endpoints enforce role-based access control. Requests without the `admin` role receive a `403 Forbidden` response.

---

## Cross-References

- [Authentication API](../01-auth/auth-api.md) — JWT auth, registration request submission, password change
- [Dashboards API](../02-dashboards/dashboards-api.md) — Dashboard, graph, and filter CRUD
- [Processing API](../03-processing/processing-api.md) — Processing logs, upload, and data endpoints
- [Database Schema](../09-database/schema-core.md) — `users`, `registration_requests`, `processing_logs` table definitions
- [Security Overview](../08-security/) — Rate limiting, credential enforcement, CORS
- [Access Control](../08-security/access-control.md) — Role-based access control and enforcement points
- [Database Enums](../09-database/enums.md) — `UserRole`, `RegistrationStatus` StrEnum definitions
