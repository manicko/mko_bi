# Phase 1: Auth Token Management — Research

**Date:** 2026-05-22
**Status:** Complete

---

## 1. Current Auth/Login Flow

### Backend
- `POST /auth/login` accepts `LoginRequest` (email + password)
- Returns `TokenWithUser` (access_token, token_type, user data)
- Rate limiting by IP (`client.host`) to prevent email enumeration
- Access token expiration: 30 minutes (`config.jwt.access_token_expire_minutes`)
- `POST /auth/refresh` endpoint exists but uses `RefreshRequest` body (not cookie-based)

### Frontend
- Auth state in `frontend/src/features/auth/model/useAuth` — Zustand store with `accessToken`
- No cookie handling currently
- No `location.state.from` redirect preservation yet
- Token stored in Zustand (in-memory), lost on page refresh

---

## 2. Backend Changes Needed

### Config
- Add `jwt.refresh_token_expire_minutes` to config (10080 = 7 days)

### `security.py`
- Add `create_refresh_token()` — same JWT logic as `create_access_token()` but with longer expiry
- Use same secret key, different expiry duration

### `auth.py` routes
- **Login (`POST /auth/login`):** After successful auth, set httpOnly cookie with refresh token alongside JSON response
- **Refresh (`POST /auth/refresh`):** Read refresh token from cookie (`request.cookies.get("mkobi_refresh_token")`), validate, issue new access token, optionally set new refresh token cookie
- **Logout (`POST /auth/logout`):** Clear cookie (`response.delete_cookie("mkobi_refresh_token")`)

### Cookie Pattern (FastAPI)
```python
from fastapi.responses import JSONResponse

response = JSONResponse(content=token_data)
response.set_cookie(
    key="mkobi_refresh_token",
    value=refresh_token,
    httponly=True,
    secure=True,
    samesite="strict",
    path="/",
    max_age=7 * 24 * 60 * 60  # 7 days
)
```

### Cookie Reading (FastAPI)
```python
refresh_token = request.cookies.get("mkobi_refresh_token")
```

### Cookie Clearing (FastAPI)
```python
response.delete_cookie(
    key="mkobi_refresh_token",
    path="/",
    httponly=True,
    secure=True,
    samesite="strict",
)
```

---

## 3. Frontend Changes Needed

### In-Memory Token Storage
- Keep existing Zustand `accessToken` pattern — it's already in-memory
- Add `token_expiry` tracking to know when to refresh
- Expose `getAccessToken()`, `setAccessToken()`, `clearAccessToken()` helpers

### Silent Refresh on App Init
- On app mount (or route change), check if access token is missing/expired
- If yes, call `POST /auth/refresh` with `credentials: 'include'` (sends cookie)
- On success: store new access token in Zustand
- On failure: redirect to `/login`

### 401 Handling with Request Queuing
- **Recommended approach:** Axios response interceptor
- On 401: queue the failed request, trigger single `/auth/refresh` call
- After refresh succeeds: retry all queued requests with new token
- After refresh fails: clear state, redirect to `/login`
- Prevent multiple concurrent refresh calls with a `isRefreshing` flag

### Axios Interceptor Pattern
```typescript
let isRefreshing = false;
let failedQueue: Array<{ resolve: Function; reject: Function }> = [];

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status !== 401) return Promise.reject(error);
    const originalRequest = error.config;
    if (originalRequest._retry) return Promise.reject(error);
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then((token) => {
        originalRequest.headers.Authorization = `Bearer ${token}`;
        return api(originalRequest);
      });
    }
    originalRequest._retry = true;
    isRefreshing = true;
    try {
      const { data } = await authApi.refreshToken();
      setAccessToken(data.access_token);
      const token = data.access_token;
      failedQueue.forEach(({ resolve }) => resolve(token));
      failedQueue = [];
      originalRequest.headers.Authorization = `Bearer ${token}`;
      return api(originalRequest);
    } catch (refreshError) {
      failedQueue.forEach(({ reject }) => reject(refreshError));
      failedQueue = [];
      clearAccessToken();
      window.location.href = '/login';
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);
```

### Logout
- Call `POST /auth/logout` (clears cookie server-side)
- Clear in-memory access token (Zustand)
- Redirect to `/login`

### Redirect Preservation
- When redirecting to `/login` due to auth failure, store current path in `location.state.from`
- After successful login, navigate to `location.state.from` or default dashboard

---

## 4. Error Handling

| Scenario | Behavior |
|----------|----------|
| Expired/invalid refresh cookie | Silent redirect to `/login` |
| Network error during refresh | Retry once after 1s, then redirect |
| Refresh returns 401 | Clear state, redirect to `/login` |
| Concurrent 401s | Single refresh, retry all queued |

---

## 5. Security Considerations

- `secure=True` cookie flag: only sent over HTTPS (ensure in production)
- `httponly=True`: prevents XSS access to refresh token
- `samesite="strict"`: prevents CSRF via cross-origin requests
- Short-lived access tokens (15 min) limit damage window
- No server-side token blacklist (stateless JWT, sufficient for current scale)

---

## RESEARCH COMPLETE
