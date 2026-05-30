---
id: client-error-reporting
domain: security
tags:
  - error-reporting
  - client-side
  - logging
  - monitoring
  - react-error-boundary
related:
  - security-overview
  - frontend-security
  - admin-api
---

# Client Error Reporting API

## Overview

The client error reporting API provides a single public endpoint for the React frontend to report runtime errors (e.g., uncaught exceptions, React Error Boundary catches) to the backend for server-side logging. This enables monitoring of frontend issues without requiring a separate logging infrastructure.

**Base path:** `/api/v1/client-errors`

**Auth level:** Public (no authentication required — errors are reported from the user's browser session, which may not have a valid token).

> **Security:** This endpoint intentionally does not require authentication because errors may occur before or independently of the authentication flow. The endpoint accepts error details and logs them server-side — it does not write to the database or return sensitive information.

---

## Endpoints

### 1. Report Client-Side Error

Accepts error details from the frontend for server-side logging.

| Attribute      | Value                                      |
| -------------- | ------------------------------------------ |
| **Method**     | `POST`                                     |
| **Path**       | `/api/v1/client-errors`                    |
| **Auth level** | Public                                     |
| **Rate limit** | None (errors are expected to be rare)      |

**Request body:**

```json
{
  "error": {
    "message": "Cannot read properties of null (reading 'map')",
    "name": "TypeError"
  },
  "componentStack": "in DashboardView\n  in App\n  in Router",
  "url": "/dashboard/550e8400-e29b-41d4-a716-446655440000",
  "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
  "timestamp": "2026-05-29T15:30:00.000Z"
}
```

**Request fields:**

| Field            | Type                  | Required | Description                                      |
| ---------------- | --------------------- | -------- | ------------------------------------------------ |
| `error`          | `object`              | Yes      | Error object with `message` and `name` fields     |
| `componentStack` | `string \| null`      | No       | React component stack trace (from Error Boundary) |
| `url`            | `string`              | Yes      | Page URL where the error occurred                 |
| `userAgent`      | `string`              | Yes      | Browser user agent string                         |
| `timestamp`      | `string` (ISO 8601)   | Yes      | Client-side timestamp of the error                |

**Response** (`204 No Content`)

The endpoint returns an empty response with HTTP 204. No data is persisted to the database.

**Side effects:**
- The error is logged server-side via `logger.error()` with the format: `Client error: {message} | url={url} | componentStack={componentStack}`
- No database write occurs — the error exists only in server logs

---

## Frontend Integration

The React SPA should call this endpoint from:
- **React Error Boundary** `componentDidCatch` — captures render-phase errors in the component tree
- **Global `window.onerror`** — captures uncaught runtime errors
- **Unhandled promise rejections** (`window.onunhandledrejection`)

This provides visibility into frontend issues that would otherwise go unnoticed by backend monitoring.

---

## Cross-References

- [Security Overview](security-overview.md) — Security constraints and measures
- [Frontend Security](../07-frontend/frontend-security.md) — JWT handling, CORS, upload security
- [Admin API](../04-admin/admin-api.md) — Admin monitoring endpoints (server-side logs)
