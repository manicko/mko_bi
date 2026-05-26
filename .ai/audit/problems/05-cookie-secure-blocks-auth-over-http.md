# Problem 5: Cookie `secure` Flag Blocks Auth Over HTTP in Dev Mode

## Severity
Medium

## Labels
[BEST-PRACTICE]

## Summary
The backend sets `secure=True` on the refresh token cookie by default (`AppSettings.cookie_secure=True`). In development mode over plain HTTP (localhost), browsers **refuse to set cookies with the `secure` flag**, which silently breaks the entire auth flow — login appears to succeed but the refresh token is never stored.

## Evidence
- `src/mkobi/config.py` line 148: `cookie_secure: bool = True` (default is `True`)
- `src/mkobi/core/security.py` lines 393-399: `set_secure_cookie` uses `config.app.cookie_secure`
- `docker-compose.override.yml`: No `APP__COOKIE_SECURE` override — uses the default `True`
- `.env` file: No `APP__COOKIE_SECURE` setting
- Browser behavior: Cookies with `secure` flag are rejected when served over `http://` (non-HTTPS)

## Root Cause
The `AppSettings.cookie_secure` defaults to `True`, which is correct for production but breaks development over HTTP. The `docker-compose.override.yml` does not override this setting, so the dev environment uses `secure=True`.

When a user logs in:
1. Backend creates refresh token, calls `set_secure_cookie()` with `secure=True`
2. Browser receives `Set-Cookie: mkobi_refresh_token=...; Secure; HttpOnly; SameSite=Strict`
3. Browser **rejects** the cookie because the connection is HTTP, not HTTPS
4. On next page load, no refresh token cookie exists → silent refresh fails → user appears logged out

## Impact
- Login appears to succeed (access token is returned in the response body and stored in sessionStorage/memory)
- But on page reload, the access token is lost (memory storage in prod, or sessionStorage cleared)
- Silent refresh fails because no cookie exists
- User is redirected to login page again
- **Creates a confusing "I just logged in but now I'm logged out" experience**

## Affected Modules
- `src/mkobi/config.py` — `AppSettings.cookie_secure=True` default
- `src/mkobi/core/security.py` — `set_secure_cookie` and `delete_secure_cookie`
- `docker-compose.override.yml` — missing `APP__COOKIE_SECURE=false`

## Suggested Direction
Add `APP__COOKIE_SECURE=false` to `docker-compose.override.yml` under the `app` service environment:
```yaml
app:
  environment:
    # ... existing vars ...
    APP__COOKIE_SECURE: "false"
```

This ensures development over HTTP works correctly while production (which uses HTTPS) keeps `secure=True`.

Effort: Trivial (1 line)

Priority: Recommended — directly impacts developer experience and auth reliability in dev mode
