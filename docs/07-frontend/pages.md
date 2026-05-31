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

The application consists of **7 UI pages** (plus a 404 fallback). Authenticated pages are wrapped in `AppLayout` which provides the `Header` top navigation bar. The `/login` and `/register` routes are **outside** `AppLayout` so that the Header is not rendered on authentication pages.

---

## 1. Login Page (`/login`)

**Component:** `features/auth/ui/LoginForm.tsx`
**Access:** Public
**Default landing page** for unauthenticated users (active redirect from other pages, except `/register`).

### UI Elements

| Element | Type | Description |
| --- | --- | --- |
| Email field | `TextField` | Email input with format validation (Zod: `z.email()`) |
| Password field | `TextField` | Password input (`type="password"`) |
| Login button | `Button` | Submits the form; disabled while loading |
| Register link | `Link` | Navigates to `/register` |
| Error alert | `Alert` | Shown on authentication failure |

### API Endpoints

| Action | Method | Endpoint | Request Body |
| --- | --- | --- | --- |
| Login | `POST` | `/api/v1/auth/login` | `{ email, password }` |

**Success response:** `{ access_token, token_type: "bearer", user: { id, email, role, display_name, created_at } }` — token stored in memory (prod) or sessionStorage (dev), user state set immediately, then redirect to `/dashboards`.

**Error responses:** `401` (invalid credentials), `429` (rate limit exceeded).

### Flow

1. User enters email and password.
2. Form is validated via Zod (`loginSchema`).
3. On submit, `POST /api/v1/auth/login` is called.
4. On success: token is stored, user profile (including `display_name`) is set in auth state, redirect to `/dashboards`.
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
| DataGrid table | `DataGrid` | ID (short UUID) + Name + Created columns, sortable |
| Pagination | `DataGrid` | Default 25 rows/page, options: 10, 25, 50 |
| Empty state | `Alert` | Shown when user has no dashboard access |
| Loading spinner | `CircularProgress` | Shown during data fetch |
| Quick filter | `GridToolbar` | Built-in search/filter via DataGrid toolbar |

### API Endpoints

| Action | Method | Endpoint | Response |
| --- | --- | --- | --- |
| List dashboards | `GET` | `/api/v1/dashboards/my` | `DashboardSummary[]` |

### Flow

1. After login, user is redirected to this page.
2. `GET /api/v1/dashboards/my` fetches dashboards the user has access to.
3. Data is displayed in a sortable DataGrid table with short UUID and name columns.
4. Clicking a row navigates to `/dashboard/:id`.
5. If the session expires, the user is redirected to `/login`.

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
| Upload button | `Button` | Visible only for `admin` and `editor` roles; opens `UploadModal` dialog |
| Upload modal | `UploadModal` | Dialog with mode toggle, file dropzone, upload queue, processing status polling |

### API Endpoints

| Action | Method | Endpoint | Query Params |
| --- | --- | --- | --- |
| Get dashboard | `GET` | `/api/v1/dashboards/:id` | — |
| Get aggregated data | `GET` | `/api/v1/data/aggregated` | `dashboard_id`, `graph_id` (optional), `filters` (optional) |
| Upload file | `POST` | `/api/v1/upload/:dashboard_id` | Query: `mode=overwrite\|append`; Body: `multipart/form-data` |
| Check status | `GET` | `/api/v1/upload/status/:task_id` | Polled after upload |

### Flow

1. Page loads with dashboard ID from URL params.
2. Filters panel renders based on dashboard configuration.
3. Charts are fetched and rendered using Plotly.js React.
4. Changing filters triggers new data requests (filtered on the backend).
5. Clicking "Upload Data" opens the `UploadModal` dialog (no page navigation).
6. After successful upload and processing, dashboard data refreshes automatically.

---

## 5. User Profile Page (`/profile`)

**Component:** `features/users/ui/UserProfile.tsx`
**Access:** Authenticated users
**Profile link** is present in the top navigation bar on all authenticated pages.

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

1. Profile data is initialized from the login response via TanStack Query (no extra API call needed).
2. The profile displays email, display_name (computed from email prefix), and global role — all read-only.
3. Non-admin users see a "Delete Account" button.
4. Clicking delete opens a confirmation dialog.
5. On confirmation, `DELETE /api/v1/users/me` is called; on success, user is logged out and redirected to `/login`.

---

## 6. Change Password Page (`/profile/change-password`)

**Component:** `features/users/ui/ChangePasswordPage.tsx`
**Access:** Authenticated users
**Entry point:** Button on the Profile page, or forced redirect from login.

### UI Elements

| Element | Type | Description |
| --- | --- | --- |
| Info Alert | `Alert` | Shown in force mode: "Password change is required. Please set a new password to continue." |
| Current password field | `TextField` | Required; `type="password"` |
| New password field | `TextField` | Minimum 8 characters (validated via Zod) |
| Confirm password field | `TextField` | Must match new password |
| Change Password button | `Button` | Submits the form |
| Cancel button | `Button` | Navigates back to `/profile`; disabled in force mode |
| Error alert | `Alert` | Shown on failure |

### Force Mode

When the URL contains `?force=true`, the page enters **force mode**:
- An informational `Alert` is displayed at the top: "Password change is required. Please set a new password to continue."
- The Cancel button is disabled (user must change password to proceed)
- The form fields and validation remain identical to normal mode

Force mode is triggered automatically when the login response or silent refresh returns `force_password_change: true`. The frontend redirects to `/profile/change-password?force=true` using `window.location.href`.

### API Endpoints

| Action | Method | Endpoint | Request Body |
| --- | --- | --- | --- |
| Change password | `POST` | `/api/v1/auth/change-password` | `{ current_password, new_password, confirm_password }` |

**Success response:** `200` `{ message: "Password changed successfully" }` — redirect to `/profile` with success notification. The `force_password_change` flag is automatically cleared on the backend after a successful change.

**Error responses:** `400` (confirmation mismatch), `401` (current password incorrect).

### Notes

- The user remains logged in after a password change (token is not invalidated).
- Form validation via Zod (`changePasswordSchema`): current password required, new password min 8 chars, confirmation must match.

---

## 7. Admin Panel (`/admin`)

**Component:** `features/admin/ui/AdminPanel.tsx`
**Access:** Admin only (enforced by `RoleBasedAccess` with `roles={['admin']}`)

### UI Elements

The admin panel uses a tabbed interface with 4 sections. Tab state (pagination, sorting) is preserved when switching between tabs by keeping all tab content mounted but hidden (`display: none/block` pattern).

| Tab | Component | Description |
| --- | --- | --- |
| User Management | `UserManagement` | DataGrid with inline role editing (singleSelect dropdown), row highlight during save, ConfirmDialog for delete and reset password, toast notifications, ResetPasswordResultDialog for displaying temp password |
| Registration Requests | `RegistrationRequests` | DataGrid with approve/reject actions via ConfirmDialog with configurable labels ("Approve"/"Reject"), toast notifications |
| Dashboard Management | `DashboardManagement` | DataGrid with short UUID, create/edit dialogs, ConfirmDialog for delete, toast notifications |
| Log Viewer | `LogViewer` | Processing logs with filtering and pagination |

### API Endpoints

| Action | Method | Endpoint |
| --- | --- | --- |
| List users | `GET` | `/api/v1/admin/users` |
| Update user role | `PATCH` | `/api/v1/admin/users/:id/role` |
| Delete user | `DELETE` | `/api/v1/admin/users/:id` |
| Reset user password | `POST` | `/api/v1/admin/users/:id/reset-password` |
| List registration requests | `GET` | `/api/v1/admin/registration-requests` |
| Approve request | `POST` | `/api/v1/admin/registration-requests/:id/approve` |
| Reject request | `POST` | `/api/v1/admin/registration-requests/:id/reject` |
| List processing logs | `GET` | `/api/v1/admin/logs` |
| Get single log | `GET` | `/api/v1/admin/logs/:log_id` |
| Dashboard CRUD | `GET/POST/PUT/DELETE` | `/api/v1/dashboards` |

### User Management Tab — Password Reset Flow

1. Each user row in the `UserManagement` DataGrid includes a "Reset Password" action button (Key icon) alongside the Delete button.
2. Clicking Reset Password opens a `ConfirmDialog` with the message: "Generate a new temporary password for {email}? The current password will be immediately invalidated."
3. On confirmation, `POST /api/v1/admin/users/:id/reset-password` is called.
4. On success, the `ResetPasswordResultDialog` opens, displaying the temporary password in a read-only TextField with a Copy button (uses `navigator.clipboard.writeText` + toast "Copied").
5. The admin copies the temp password and communicates it securely to the user.
6. The user's `force_password_change` flag is set to `True`, so on next login they are forced to change their password.
7. On error, a toast "Failed to reset password" is shown.

### Registration Approval Flow

1. Admin views pending registration requests in a DataGrid table.
2. Approve/reject actions use `ConfirmDialog` with configurable `confirmLabel` ("Approve" / "Reject").
3. On approve: `POST /api/v1/admin/registration-requests/:id/approve` creates a user with a random temporary password.
4. The `temp_password` is returned in the response for the admin to communicate to the new user.
5. On reject: the request status is set to `rejected`.
6. Toast notifications confirm success/failure of actions.

---

## 404 Page

**Component:** `shared/components/NotFound.tsx`
**Access:** Public
**Rendered** for any unmatched route (`*` path).

---

## Cross-References

- [Auth Flow](auth-flow.md) — Detailed authentication and authorization flow
- [Upload UI](upload-ui.md) — Upload modal and file handling details
- [Frontend Security](frontend-security.md) — Security measures for all pages
- [Authentication API](../../01-auth/auth-api.md) — Backend auth endpoint specs
- [Processing API](../../03-processing/processing-api.md) — Upload and data endpoint specs
- [Dashboards API](../../02-dashboards/dashboards-api.md) — Dashboard, graph, and filter CRUD
- [Admin API](../../04-admin/admin-api.md) — Admin panel endpoints
