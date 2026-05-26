# Audit Report 001 — Runtime Errors Found via Docker Verification

**Date:** 2026-05-26
**Auditor:** OWL (automated runtime verification)
**Scope:** Docker dev environment, frontend rendering, backend startup stability
**Trigger:** Manual investigation after user reported "Something went wrong" on both `http://localhost:8000/` and `http://localhost:5173/`

---

## Executive Summary

Two critical issues were found that prevent the application from being used. Both were **only detectable through runtime verification** — static code analysis and spec compliance checks did not catch them.

**Overall readiness: 2/10** — Application is non-functional for end users.

---

## Findings

### Finding 1 — Frontend Crashes on Load (CRITICAL)

| Field | Value |
|-------|-------|
| **Severity** | CRITICAL |
| **Type** | [RUNTIME] |
| **File** | `frontend/src/app/routes.tsx` |
| **Line** | 26 |
| **Problem** | `<TrailingSlashRedirect />` placed as direct child of `<Routes>` |
| **Error** | `Error: [TrailingSlashRedirect] is not a <Route> component. All component children of <Routes> must be a <Route> or <React.Fragment>` |
| **Impact** | React app crashes on every page load. ErrorBoundary catches it and shows "Something went wrong". Application is completely non-functional. |
| **Affected URLs** | `http://localhost:5173/*` (Vite dev), `http://localhost:8000/*` (built frontend) |
| **Root Cause** | `react-router-dom` v7 strictly validates children of `<Routes>`. Only `<Route>` and `<React.Fragment>` are allowed. `TrailingSlashRedirect` is a plain component. |

**Evidence:**
```
Error: [TrailingSlashRedirect] is not a <Route> component. All component children of <Routes> must be a <Route> or <React.Fragment>
    at invariant (react-router-dom.js:161:79)
    at createRoutesFromChildren (react-router-dom.js:4771:24)
```

**Code at fault (routes.tsx:23-78):**
```tsx
export function AppRoutes() {
  return (
    <Routes>
      <TrailingSlashRedirect />   {/* ← INVALID: not a <Route> */}
      <Route path="/login" element={<LoginForm />} />
      ...
    </Routes>
  )
}
```

**Recommended fix:** Move `TrailingSlashRedirect` inside a layout route or wrap it within each route's `element` prop. For example, inside `AppLayout`:

```tsx
function AppLayoutWrapper() {
  return (
    <>
      <TrailingSlashRedirect />
      <AppLayout />
    </>
  )
}
```

Then use `<Route element={<AppLayoutWrapper />}>` instead of `<Route element={<AppLayout />}>`.

---

### Finding 2 — Backend Restart Loop from Volume Mounts (MEDIUM)

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Type** | [RUNTIME] |
| **File** | `docker/docker-compose.override.yml` |
| **Lines** | 68-72 |
| **Problem** | Mounted `../tests:/app/tests` volume triggers uvicorn `--reload` on every file change |
| **Impact** | Backend restarts every few seconds when test files or `__pycache__` are updated. Causes intermittent 503s, dropped connections, and database connection churn. |
| **Root Cause** | Uvicorn's `--reload` watches the entire working directory. The `tests/` volume mount includes `__pycache__/*.pyc` files that change on every test run or Python process. |

**Evidence (from `docker compose logs app`):**
```
WARNING:  StatReload detected changes in 'tests/test_repositories.py'. Reloading...
{"timestamp": "...", "message": "Shutting down application..."}
{"timestamp": "...", "message": "Database engines disposed"}
Using default admin username in development environment
{"timestamp": "...", "message": "Application initialized successfully"}
WARNING:  StatReload detected changes in 'tests/test_graphs.py'. Reloading...
... (cycle repeats)
```

**Recommended fix:** Either:
1. Exclude `tests/` from the volume mount (remove `- ../tests:/app/tests`), or
2. Add `--reload-exclude tests/` to the uvicorn command, or
3. Set `PYTHONDONTWRITEBYTECODE=1` and exclude `__pycache__` directories.

---

### Finding 3 — Placeholder Page Title (LOW)

| Field | Value |
|-------|-------|
| **Severity** | LOW |
| **Type** | [DOC-UPDATE] |
| **File** | `frontend/index.html` |
| **Line** | 7 |
| **Problem** | `<title>frontend</title>` is a Vite default placeholder |
| **Impact** | Browser tab shows "frontend" instead of the application name. Poor UX. |
| **Recommended fix** | Change to `<title>mkobi BI Dashboard</title>` |

---

### Finding 4 — Built Frontend Served by Backend May Have Stale Assets (LOW)

| Field | Value |
|-------|-------|
| **Severity** | LOW |
| **Type** | [RUNTIME] |
| **File** | Docker image's `/app/frontend/dist/index.html` |
| **Problem** | The Docker image bakes in a specific `index.html` with a hardcoded JS bundle hash (e.g., `index-DW1oWDTg.js`). After rebuilding the host frontend, the hash changes (e.g., `index-DRl1PhTO.js`), but the Docker image's `index.html` still references the old hash. |
| **Impact** | `http://localhost:8000/` may serve an `index.html` that references a non-existent JS bundle if the frontend was rebuilt without rebuilding the Docker image. |
| **Recommended fix** | Ensure the Docker image is rebuilt after frontend changes. Document this dependency in `docs/11-guides/docker.md`. |

---

## Runtime Status Summary

| Service | Status | Notes |
|---------|--------|-------|
| app | running + restarting loop | Restarts triggered by `tests/` volume mount changes |
| db | healthy | PostgreSQL accepting connections |
| redis | healthy | Responds to ping |
| frontend | running | Vite dev server responds on 5173 |

| Endpoint | Status | Notes |
|----------|--------|-------|
| `GET http://localhost:8000/healthy` | 200 OK | `{"status":"healthy","database":"connected"}` |
| `GET http://localhost:8000/` | 200 OK | Serves index.html but JS bundle may be stale |
| `GET http://localhost:8000/docs` | 200 OK | Swagger UI accessible |
| `GET http://localhost:5173/` | 200 OK | Serves index.html with Vite HMR |
| Browser render `http://localhost:8000/` | **CRITICAL** | "Something went wrong" — ErrorBoundary caught crash |
| Browser render `http://localhost:5173/` | **CRITICAL** | "Something went wrong" — ErrorBoundary caught crash |

---

## Fix Priority

1. **CRITICAL — Finding 1:** Fix `TrailingSlashRedirect` placement in `routes.tsx` — blocks all users
2. **MEDIUM — Finding 2:** Fix volume mount reload loop — degrades reliability
3. **LOW — Finding 3:** Update page title in `index.html`
4. **LOW — Finding 4:** Document/rebuild Docker image after frontend changes

---

## Notes on Audit Process

These findings were discovered by running Docker in dev mode and observing:
1. Browser console errors when loading `http://localhost:5173/`
2. Repeated restart messages in `docker compose logs app`
3. Mismatch between container's `index.html` and actual JS bundle hash

**None of these issues would be found by static code analysis alone.** This confirms the need for runtime verification steps in the audit process (see updated `.kilo/agents/auditor.md` and `.kilo/commands/audit/`).
