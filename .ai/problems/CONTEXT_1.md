Архитектура:
access token → в памяти
refresh token → httpOnly secure cookie
при refresh страницы:
фронт вызывает /auth/refresh
сервер читает cookie
выдает новый access token
пользователь остается залогинен

Implementation Plan: Access Token + httpOnly Refresh Token Cookie
This is a standard secure authentication pattern. Here's the complexity breakdown:

Backend Changes (Medium complexity)
src/mkobi/core/security.py - Add refresh token creation:
create_refresh_token() - Longer-lived JWT (7-30 days)
src/mkobi/api/routes/auth.py - Modify login and refresh:
Set httpOnly cookie with refresh token on login
Read refresh token from cookie in /auth/refresh
Add /auth/logout to clear cookie
New endpoint /auth/refresh - Cookie-based:
No body required, reads refresh token from cookie
Returns new access token
Frontend Changes (Low complexity)
frontend/src/features/auth/model/authToken.ts - Modify:
On app initialization, call /auth/refresh when no access token exists
frontend/src/features/auth/api/authApi.ts - Add:
refreshToken() function for silent refresh
Implementation Steps
# Example: Backend cookie setting on login
response = JSONResponse(content={...})
response.set_cookie(
    key="refresh_token",
    value=refresh_token,
    httponly=True,
    secure=True,  # HTTPS only
    samesite="strict",
    max_age=7 * 24 * 60 * 60,  # 7 days
)