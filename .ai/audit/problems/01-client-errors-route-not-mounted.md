# Problem 1: Client Errors API Route Not Mounted

## Severity
Medium

## Labels
[SPEC-DEVIATION]

## Summary
The `client_errors` router exists in the codebase (defined in `src/mkobi/api/routes/client_errors.py` and exported via `src/mkobi/api/routes/__init__.py`) but is **never mounted** in `src/mkobi/app.py`. This causes all frontend `POST /api/v1/client-errors` requests to return HTTP 404 instead of being processed.

## Evidence
- `app.py` (lines 167-177): Only mounts these routers: `auth`, `users`, `dashboards`, `graphs`, `layouts`, `upload`, `data`, `filters`, `processing_configs`, `processing_logs`, `admin`. The `client_errors` router is absent.
- Docker logs show repeated 404s: `"POST /api/v1/client-errors HTTP/1.1" 404`
- `curl` test from inside the app container confirms: `POST /api/v1/client-errors` → 404
- OpenAPI spec (`/openapi.json`) does not list any `/api/v1/client-errors` path.
- `ErrorBoundary.tsx` (line 40): Calls `fetch('/api/v1/client-errors', ...)` which silently fails with 404, meaning **all client-side React errors are silently swallowed in production mode**.

## Root Cause
When the `client_errors` module was created, it was added to `__init__.py` exports but the corresponding `application.include_router()` call was never added to `app.py`.

## Impact
- In production (`ErrorBoundary.tsx` line 27-29): `reportError()` is called for every unhandled React error, but the POST returns 404, then `.catch(() => {})` silently swallows it. **No client errors are ever reported or logged.**
- The `ErrorPage` still renders (so users see "Something went wrong"), but developers get zero diagnostics about what went wrong.
- The HTTP 404 itself is harmless to the user flow but represents dead code and a broken observability pathway.

## Affected Modules
- `src/mkobi/app.py` — missing `include_router` call
- `src/mkobi/api/routes/client_errors.py` — dead code (never reached)
- `frontend/src/shared/components/ErrorBoundary.tsx` — error reporting silently fails

## Suggested Direction
Add the missing router mount in `app.py` in the section where other routes are registered:
```python
application.include_router(routes.client_errors.router, prefix="/api/v1")
```

Effort: Trivial (1 line)

Priority: Recommended
