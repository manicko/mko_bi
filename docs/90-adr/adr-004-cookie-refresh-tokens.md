---
id: adr-004-cookie-refresh-tokens
domain: adr
tags:
  - authentication
  - security
  - cookies
  - refresh-tokens
  - jwt
  - xss-mitigation
related:
  - auth-api
  - security-overview
  - frontend-auth-flow
  - frontend-security
---

# ADR-004: Cookie-Based Refresh Tokens

## Status

Accepted

## Date

2026-05-23

## Context

The original authentication flow passed refresh tokens in the request body (`POST /auth/refresh` with `{ "refresh_token": "..." }`). This approach has a critical security limitation: the refresh token must be accessible to JavaScript, which means it cannot be stored in an httpOnly cookie. Storing it in `localStorage` or a JavaScript variable makes it vulnerable to exfiltration via XSS attacks.

Additionally, there was no dedicated logout endpoint — the frontend simply discarded tokens locally without invalidating the server-side session.

## Decision

Switch to a **cookie-based refresh token** architecture:

### Key Changes

1. **Refresh token in httpOnly cookie:** The refresh token is stored in an httpOnly cookie (`mkobi_refresh_token`) with `Secure`, `HttpOnly`, and `SameSite=Strict` attributes. JavaScript cannot access this cookie, making it resistant to XSS-based token theft.

2. **Reduced access token lifetime:** Access token expiration was reduced from 30 minutes to 15 minutes, limiting the window of opportunity if an access token is compromised.

3. **Dedicated logout endpoint:** `POST /auth/logout` clears the refresh token cookie on the server side, ensuring proper session termination.

4. **Frontend silent refresh:** The frontend automatically attempts a silent token refresh on app initialization using the httpOnly cookie, keeping users logged in across page refreshes.

5. **Request queue for concurrent 401s:** The axios interceptor queues failed requests during token refresh to prevent race conditions.

### Cookie Attributes

| Attribute | Value | Purpose |
| --- | --- | --- |
| `HttpOnly` | `true` | Prevents JS access (XSS protection) |
| `Secure` | `true` | HTTPS-only (MITM protection) |
| `SameSite` | `Strict` | No cross-site sending (CSRF protection) |
| `Max-Age` | `604800` (7 days) | Refresh token lifetime |

### Trade-offs

| Aspect | Before | After |
| --- | --- | --- |
| Refresh token storage | Request body (JS-accessible) | httpOnly cookie (JS-inaccessible) |
| XSS token theft risk | High — any XSS can steal refresh token | Low — cookie is inaccessible to JS |
| Access token lifetime | 30 minutes | 15 minutes |
| CSRF risk | No cookies used for auth | Mitigated by `SameSite=Strict` |
| Logout | Client-side only | Server-side cookie clearing |
| Session continuity | Lost on page refresh | Silent refresh preserves session |
| Complexity | Simple body-based flow | Requires cookie-aware interceptor logic |

### Why Not Other Alternatives?

- **localStorage/sessionStorage:** Vulnerable to XSS token exfiltration. The primary motivation for httpOnly cookies is to eliminate this attack vector.
- **Short-lived access tokens only (no refresh):** Would require users to re-authenticate every 15 minutes, unacceptable UX.
- **Token rotation with body-based refresh:** Still exposes the refresh token to JavaScript. Cookie approach provides the same rotation benefits with better security.
- **Backend sessions (stateful):** Violates the stateless JWT architecture principle and complicates horizontal scaling.

## Consequences

- **Positive:** Significantly reduces the impact of XSS attacks on authentication
- **Positive:** Proper server-side session termination via logout
- **Positive:** Seamless session continuity across page refreshes
- **Positive:** Short-lived access tokens limit exposure window
- **Neutral:** CSRF risk is mitigated by `SameSite=Strict` but requires proper CORS configuration
- **Neutral:** Slightly more complex frontend interceptor logic (request queue, silent refresh)
- **Negative:** Requires `withCredentials: true` on all API calls, which means CORS must be properly configured with explicit origins (no wildcards)

## Related

- [Authentication API](../01-auth/auth-api.md) — Login, refresh, and logout endpoint specifications
- [Security Overview](../08-security/security-overview.md) — Cookie security details
- [Frontend Auth Flow](../07-frontend/auth-flow.md) — Silent refresh and logout flow
- [Frontend Security](../07-frontend/frontend-security.md) — Cookie-based refresh implementation
