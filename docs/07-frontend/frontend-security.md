---
id: frontend-security
domain: frontend
tags:
  - jwt-security
  - cors
  - file-upload-security
  - role-based-access
  - email-validation
  - xss-prevention
related:
  - auth-flow
  - upload-ui
  - auth-api
  - processing-api
  - security-overview
---

# Frontend Security

## Overview

This document describes the security measures implemented in the React frontend. The frontend works in conjunction with the FastAPI backend to provide defense in depth. All security-critical validation is enforced on the backend; the frontend provides a first layer of UX-level validation.

> **[HIGH-RISK]** CORS configuration is a critical security boundary. Misconfiguration can expose the API to cross-origin attacks.

---

## JWT Handling

### Token Storage Strategy

The frontend uses a dual storage strategy based on the build environment (`import.meta.env.PROD`):

| Environment | Storage | Persistence | XSS Risk |
| --- | --- | --- | --- |
| **Production** | Module-level JS variable (`memoryToken`) | Lost on page reload/navigation | **Low** — not accessible via browser storage APIs |
| **Development** | `sessionStorage` (key: `access_token`) | Survives page refresh; cleared on tab close | **Medium** — accessible to any JS on the page |

**Production behavior:**
- Tokens are held only in a closure variable in `authToken.ts`.
- They are never serialized to disk or browser storage.
- This is the most secure option for a SPA as it mitigates XSS-based token theft.

**Development behavior:**
- Tokens fall back to `sessionStorage` for convenience during local development.
- This mode **MUST NEVER** be used in production builds.

### Token Expiration

The Axios request interceptor checks token expiration before every API request:

1. Decode the JWT payload (base64).
2. Read the `exp` claim.
3. If expired: remove the token, return `null` (request proceeds without auth header).
4. The backend returns `401`, triggering the response interceptor.

### Axios Interceptors

**Request interceptor** (`shared/api/axiosInstance.ts`):
- Calls `getTokenWithExpirationCheck()` before each request.
- If a valid token exists: adds `Authorization: Bearer <token>` header.
- If the token is expired: removes the token, sends request without auth.

**Response interceptor**:
- On `401` responses: removes the token, displays toast error ("Session expired. Please login again."), redirects to `/login`.

### Token Refresh

The backend provides `POST /api/v1/auth/refresh` for token renewal. The current frontend implementation does not use automatic token refresh — users are redirected to login when their session expires.

---

## CORS Configuration [HIGH-RISK]

CORS is configured on the **backend** (FastAPI) with explicit allowed methods and headers. Wildcards are **not** used.

### Backend Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,  # From env var or app.yaml (default: localhost)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)
```

### Security Constraints

- **`allow_origins`** must be explicitly configured in production. The application validates CORS configuration at startup and raises an error if origins are not set in production mode.
- **No wildcard origins** (`*`) in production.
- **`allow_credentials: True`** — cookies/credentials are included in cross-origin requests.
- **Explicit method list:** Only `GET`, `POST`, `PUT`, `DELETE`, `PATCH` are allowed.
- **Explicit header list:** Only `Authorization`, `Content-Type`, `Accept` are allowed.

### Frontend Implications

- The Axios instance is configured with `withCredentials: true` to include cookies in cross-origin requests.
- The base URL is set to `/api/v1` (relative path), so in production (where FastAPI serves the React static files), requests are same-origin and CORS is not a concern.
- In development, the React dev server (port 3000) makes cross-origin requests to FastAPI (port 8000), requiring proper CORS configuration.

---

## File Upload Security

### Client-Side Validation

The `FileDropzone` component performs client-side validation:

1. **MIME type filtering:** `react-dropzone` is configured with `accept: { 'text/csv': ['.csv'], 'application/gzip': ['.gz'], 'application/x-gzip': ['.gz'] }`.
2. **Extension validation:** Additional check ensures filenames end with `.csv` or `.csv.gz`.
3. **User feedback:** Rejected files trigger toast error messages.

### Server-Side Enforcement

> **Important:** Client-side validation is a UX convenience only. The backend is the security boundary.

The backend enforces:

| Constraint | Description |
| --- | --- |
| MIME type validation | Only `text/csv`, `application/gzip`, `application/x-gzip` accepted |
| File size limit | Maximum file size enforced on the backend |
| Rate limiting | Upload endpoints are rate-limited (Redis-based) |
| Temporary file cleanup | Files deleted from temporary storage after processing |
| File extension check | Server validates `.csv` and `.csv.gz` extensions |

### Upload Endpoint Security

- **Authentication:** Requires valid JWT token (editor+ role).
- **Rate limiting:** Applied to all `/api/v1/upload/*` endpoints.
- **Task ownership validation:** The `POST /api/v1/upload/:dashboard_id/process` endpoint validates that the task belongs to the specified dashboard, preventing cross-dashboard task triggering.

---

## Role-Based Access Control

### Route-Level Guards

Two components enforce access control at the route level:

**`ProtectedRoute`** (`shared/components/ProtectedRoute.tsx`):
- Redirects unauthenticated users to `/login`.
- Shows a loading spinner while auth state is being determined.

**`RoleBasedAccess`** (`shared/components/RoleBasedAccess.tsx`):
- Renders children only if the user's role is in the allowed list.
- Renders `fallback` (default: `null`) otherwise.

### Access Matrix

| Route | Required Role |
| --- | --- |
| `/login`, `/register` | Public |
| `/dashboards`, `/dashboard/:id` | Any authenticated |
| `/admin` | `admin` only |
| `/profile`, `/profile/change-password` | Any authenticated |

### UI-Level Enforcement

Individual UI elements are conditionally rendered based on role:
- Upload button: visible only for `admin` and `editor`.
- Delete Account button: visible only for non-admin users.
- Admin link in Header: visible only for `admin`.
- Header shows navigation buttons (Dashboards, Admin, Profile) with user email and an AccountCircle menu for logout. Logout is handled via the Header user menu, not on a separate page.
- Login and Register pages render outside `AppLayout` — no Header on authentication pages.

> **Note:** UI-level role checks are for UX only. The backend enforces authorization on every API request.

---

## Email Validation (Registration)

Email validation is applied on both frontend and backend:

### Frontend (Zod)

```typescript
// Login: format check only
email: z.string().email('Invalid email format')

// Registration: format + domain blocklist
email: z.string()
  .email('Invalid email format')
  .refine((email) => {
    const domain = email.split('@')[1]
    return domain && !BLOCKED_DOMAINS.includes(domain)
  }, 'This email domain is not allowed')
```

Blocked domains are defined in `shared/types/formSchemas.ts`: `tempmail.com`, `throwawaymail.com`.

### Backend (Pydantic)

The backend independently validates email format and checks against a configurable domain blocklist (defined in `app.yaml`). Frontend validation is a UX convenience; backend validation is the security boundary.

---

## Content Security

### No `eval()` or `dangerouslySetInnerHTML`

The codebase does not use `eval()`, `new Function()`, or React's `dangerouslySetInnerHTML`, preventing code injection via user input.

### Dependency Management

Frontend dependencies are managed via `package.json` and should be audited regularly (`npm audit`).

---

## Cross-References

- [Auth Flow](auth-flow.md) — JWT storage, login/registration flows, role-based access
- [Upload UI](upload-ui.md) — File upload validation and security
- [Authentication API](../../01-auth/auth-api.md) — Backend auth endpoint security
- [Processing API](../../03-processing/processing-api.md) — Upload endpoint security constraints
- [Frontend Architecture](architecture.md) — HTTP client and interceptor configuration
- [Security Overview](../../08-security/security-overview.md) — Backend security constraints: rate limiting, CORS, credential enforcement
- [Access Control](../../08-security/access-control.md) — Dashboard-level permission model
