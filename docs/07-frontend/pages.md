---
id: ui-pages
domain: frontend
tags:
  - ui-pages
  - login
  - registration
  - dashboards
  - upload
  - admin-panel
  - profile
related:
  - frontend-architecture
  - auth-flow
  - upload-ui
  - frontend-security
  - auth-api
---

# UI Pages

## Overview

The application consists of **8 UI pages** (plus a 404 fallback). Authenticated pages are wrapped in `AppLayout` which provides the `Header` navigation bar. The `/login` and `/register` routes are **outside** `AppLayout` so that the Header and Sidebar are not rendered on authentication pages.

---

## 1. Login Page (`/login`)

**Component:** `features/auth/ui/LoginForm.tsx`
**Access:** Public
**Default landing page** for unauthenticated users (active redirect from other pages, except `/register`).

### UI Elements

| Element | Type | Description |
| --- | --- | --- |
| Email field | `TextField` | Email input with format validation (Zod: `z.string().email()`) |
| Password field` | `TextField` | Password input (`type="password"`) |
| Login button | `Button` | Submits the form; disabled while loading |
| Register link | `Link` | Navigates to `/register` |
| Error alert | `Alert` | Shown on authentication failure |

### API Endpoints

| Action | Method | Endpoint | Request Body |
| --- | --- | --- | --- |
| Login | `POST` | `/api/v1/auth/login` | `{ email, password }` |

**Success response:** `{ access_token, token_type: "bearer" }` — token stored in memory (prod) or sessionStorage (dev), then redirect to `/dashboards`.

**Error responses:** `401` (invalid credentials), `429` (rate limit exceeded).

### Flow

1. User enters email and password.
2. Form is validated via Zod (`loginSchema`).
3. On submit, `POST /api/v1/auth/login` is called.
4. On success: token is stored, user is redirected to `/dashboards`.
5. On failure: error alert is displayed.

---

## 2. Registration Page (`/register`)

**Component:** `features/auth/ui/RegisterForm.tsx`
**Access:** Public
**Entry point:** Link from the Login page.

### UI Elements

| Element | Type | Description |
| --- | --- | --- |
| Email field | `TextField` | Email input with Zod validation (format + domain blocklist) |
| Submit button | `Button` | Submits the registration request |
| Login link | `Link` | Navigates back to `/login` |
| Success alert | `Alert` | Shown after successful request submission |

### API Endpoints

| Action | Method | Endpoint | Request Body |
| --- | --- | --- | --- |
| Register Request | `POST` | `/api/v1/auth/register-request` | `{ email }` |

**Success response:** `201` `{ message, id }` — request saved in `registration_requests` table with status `pending`.

**Error responses:** `422` (email already registered or domain blocklisted), `429` (rate limit exceeded).

### Flow

1. User enters their email address.
2. Form is validated via Zod (`registerSchema`) — checks format and blocked domains.
3. On submit, `POST /api/v1/auth/register-request` is called.
4. On success: success message is shown with a link back to login.
5. The request awaits admin approval.

---

## 3. Dashboard List Page (`/dashboards`)

**Component:** `features/dashboards/ui/DashboardList.tsx`
**Access:** Authenticated users
**Default redirect** from `/` after successful login.

### UI Elements

| Element | Type | Description |
| --- | --- | --- |
| Dashboard cards | Card list | Each card shows name, description, and "Open" link |
| Profile link | Link | Top-right corner, navigates to `/profile` |

### API Endpoints

| Action | Method | Endpoint | Response |
| --- | --- | --- | --- |
| List dashboards | `GET` | `/api/v1/dashboards/my` | `DashboardSummary[]` |

### Flow

1. After login, user is redirected to this page.
2. `GET /api/v1/dashboards/my` fetches dashboards the user has access to.
3. Each dashboard card links to `/dashboard/:id`.
4. If the session expires, the user is redirected to `/login`.

---

## 4. Dashboard View Page (`/dashboard/:id`)

**Component:** `features/dashboards/ui/DashboardView.tsx`
**Access:** Authenticated users

### UI Elements

| Element | Type | Description |
| --- | --- | --- |
| Dashboard title | `Typography` | Dashboard name header |
| Filters panel | `DashboardFilters` | Dynamic filters (Select/Range/Date) based on dashboard config |
| Charts grid | Chart components | Plotly.js charts (Bar, Line, Pie, Table) arranged in a grid |
| Upload button | `Button` | Visible only for `admin` and `editor` roles; links to `/dashboard/:id/upload` |

### API Endpoints

| Action | Method | Endpoint | Query Params |
| --- | --- | --- | --- |
| Get aggregated data | `GET` | `/api/v1/data/aggregated` | `dashboard_id`, `graph_id` (optional), `filters` (optional) |

### Flow

1. Page loads with dashboard ID from URL params.
2. Filters panel renders based on dashboard configuration.
3. Charts are fetched and rendered using Plotly.js React.
4. Changing filters triggers new data requests (filtered on the backend).

---

## 5. User Profile Page (`/profile`)

**Component:** `features/users/ui/UserProfile.tsx`
**Access:** Authenticated users
**Profile link** is present on all pages except `/login`.

### UI Elements

| Element | Type | Description |
| --- | --- | --- |
| Email display | Read-only text | User's email address |
| Display Name display | Read-only text | User's `display_name` (computed from email prefix) |
| Role display | Read-only text | User's role (`admin`, `editor`, or `viewer`) |
| Change Password button | `Button` | Navigates to `/profile/change-password` |
| Delete Account button | `Button` | Only visible for non-admin users; opens a confirmation dialog |
| Delete confirmation dialog | `Dialog` | Confirms account deletion with "Cancel" and "Delete" options |

### API Endpoints

| Action | Method | Endpoint | Description |
| --- | --- | --- | --- |
| Get profile | `GET` | `/api/v1/auth/me` | Returns current user profile (also available from login response) |
| Delete account | `DELETE` | `/api/v1/users/me` | Self-deletion (non-admin only) |

### Flow

1. Profile data is fetched via `GET /api/v1/auth/me` (initialized with cached user data from the login response via TanStack Query).
2. The profile displays email, display_name (computed from email prefix), and global role — all read-only.
3. Non-admin users see a "Delete Account" button.
4. Clicking delete opens a confirmation dialog.
5. On confirmation, `DELETE /api/v1/users/me` is called; on success, user is logged out and redirected to `/login`.

---

## 6. Change Password Page (`/profile/change-password`)

**Component:** `features/users/ui/ChangePasswordPage.tsx`
**Access:** Authenticated users
**Entry point:** Button on the Profile page.

### UI Elements

| Element | Type | Description |
| --- | --- | --- |
| Current password field | `TextField` | Required; `type="password"` |
| New password field | `TextField` | Minimum 8 characters (validated via Zod) |
| Confirm password field | `TextField` | Must match new password |
| Change Password button | `Button` | Submits the form |
| Cancel button | `Button` | Navigates back to `/profile` |
| Error alert | `Alert` | Shown on failure |

### API Endpoints

| Action | Method | Endpoint | Request Body |
| --- | --- | --- | --- |
| Change password | `POST` | `/api/v1/auth/change-password` | `{ current_password, new_password, confirm_password }` |

**Success response:** `200` `{ message: "Password changed successfully" }` — redirect to `/profile` with success notification.

**Error responses:** `400` (confirmation mismatch), `401` (current password incorrect).

### Notes

- The user remains logged in after a password change (token is not invalidated).
- Form validation via Zod (`changePasswordSchema`): current password required, new password min 8 chars, confirmation must match.

---

## 7. Admin Panel (`/admin`)

**Component:** `features/admin/ui/AdminPanel.tsx`
**Access:** Admin only (enforced by `RoleBasedAccess` with `roles={['admin']}`)

### UI Elements

The admin panel uses a tabbed interface with 4 sections:

| Tab | Component | Description |
| --- | --- | --- |
| User Management | `UserManagement` | Table of users, role changes, user deletion |
| Registration Requests | `RegistrationRequests` | List of pending requests, approve/reject actions |
| Dashboard Management | `DashboardManagement` | CRUD operations for dashboards |
| Log Viewer | `LogViewer` | Processing logs with filtering and pagination |

### API Endpoints

| Action | Method | Endpoint |
| --- | --- | --- |
| List users | `GET` | `/api/v1/admin/users` |
| Update user role | `PATCH` | `/api/v1/admin/users/:id/role` |
| Delete user | `DELETE` | `/api/v1/admin/users/:id` |
| List registration requests | `GET` | `/api/v1/admin/registration-requests` |
| Approve request | `POST` | `/api/v1/admin/registration-requests/:id/approve` |
| Reject request | `POST` | `/api/v1/admin/registration-requests/:id/reject` |
| List processing logs | `GET` | `/api/v1/admin/logs` |
| Get single log | `GET` | `/api/v1/admin/logs/:log_id` |
| Dashboard CRUD | `GET/POST/PUT/DELETE` | `/api/v1/dashboards` |

### Registration Approval Flow

1. Admin views pending registration requests.
2. On approve: `POST /api/v1/admin/registration-requests/:id/approve` creates a user with a random temporary password.
3. The `temp_password` is returned in the response for the admin to communicate to the new user.
4. On reject: the request status is set to `rejected`.

---

## 8. Data Upload Page (`/dashboard/:id/upload`)

**Component:** `features/upload/ui/UploadPage.tsx`
**Access:** Admin and Editor (enforced by `RoleBasedAccess` with `roles={['admin', 'editor']}`)

### UI Elements

| Element | Type | Description |
| --- | --- | --- |
| Mode toggle | `ToggleButtonGroup` | "Overwrite" (reset all data) / "Append" (add new rows) |
| File dropzone | `FileDropzone` | Drag-and-drop area for `.csv` and `.csv.gz` files |
| File list | List | Selected files with remove buttons |
| Upload queue | Paper section | Per-file progress bars and status indicators |
| Start Upload button | `Button` | Begins upload of all selected files |
| Cancel button | `Button` | Returns to dashboard view |
| Success alert | `Alert` | Shown when all files are uploaded and processing starts |

### API Endpoints

| Action | Method | Endpoint | Params |
| --- | --- | --- | --- |
| Upload file | `POST` | `/api/v1/upload/:dashboard_id` | Query: `mode=overwrite\|append`; Body: `multipart/form-data` |
| Check status | `GET` | `/api/v1/upload/status/:task_id` | Polled after upload |
| Get result | `GET` | `/api/v1/upload/result/:task_id` | Final processing result |

### Flow

1. User selects upload mode (overwrite or append).
2. User drags and drops or selects `.csv` / `.csv.gz` files.
3. Files are validated for correct extension and MIME type.
4. On "Start Upload", files are uploaded sequentially.
5. Progress bars show upload progress per file.
6. After upload, processing status is polled via `GET /api/v1/upload/status/:task_id`.
7. On completion (`status === 'completed'` or `'success'`), user is redirected back to the dashboard.

---

## 404 Page

**Component:** `shared/components/NotFound.tsx`
**Access:** Public
**Rendered** for any unmatched route (`*` path).

---

## Cross-References

- [Auth Flow](auth-flow.md) — Detailed authentication and authorization flow
- [Upload UI](upload-ui.md) — Upload security and file handling details
- [Frontend Security](frontend-security.md) — Security measures for all pages
- [Authentication API](../../01-auth/auth-api.md) — Backend auth endpoint specs
- [Processing API](../../03-processing/processing-api.md) — Upload and data endpoint specs
- [Dashboards API](../../02-dashboards/dashboards-api.md) — Dashboard, graph, and filter CRUD
- [Admin API](../../04-admin/admin-api.md) — Admin panel endpoints
