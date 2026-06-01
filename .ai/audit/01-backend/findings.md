# Phase 01 Audit Findings — Backend Architecture

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Runtime Verification Summary

| Step | Tool | Exit Code | Result |
|------|------|-----------|--------|
| R1 — Linter (ruff) | `uv run ruff check src/mkobi/` | 0 | All checks passed |
| R1 — Type Checker (mypy) | `uv run mypy src/mkobi/` | 0 | Success: no issues found in 105 source files |
| R2 — Import Verification | `from mkobi.main import app` | OK | Import succeeds via factory pattern (`create_app()`) |
| R3 — Dead Code | grep analysis | — | See findings |
| R4 — Tests | `uv run pytest tests/ --tb=short -q` | 0 | **603 passed**, 11 warnings in 266.84s |
| R5 — Route Enumeration | programmatic | — | See findings — 20 duplicate route registrations |

---

## Findings

### BE-001: Duplicate Route Registrations — Overlapping Sub-Routers

| Field | Value |
|-------|-------|
| **ID** | BE-001 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/app.py`, `src/mkobi/api/routes/dashboards.py`, all `dashboards_*.py` sub-modules, `users.py` + `admin.py` |
| **Classification** | mandatory |

**Description:** The application registers **61 total route paths** but only **41 are unique**, meaning **20 routes are duplicated**. This happens because the same logical endpoints are defined in two separate places and both are mounted:

1. **Direct routers** (`users`, `graphs`, `layouts`, `filters`, `processing_configs`, `dashboards`, `dashboards_access`, `dashboards_filters`, `dashboards_graphs`) are all included under `/api/v1` prefix in `app.py` (lines 200–211).
2. **The `dashboards` router** (line 202) is itself a composite that includes `dashboards_crud`, `dashboards_access`, `dashboards_filters`, `dashboards_graphs` as sub-routers (see `dashboards.py` lines 19–23).
3. **`admin.py`** defines `GET /admin/users`, `PATCH /admin/users/{user_id}/role`, `DELETE /admin/users/{user_id}` — overlapping with `users.py` which defines `GET /users/`, `PUT /users/{user_id}`, `DELETE /users/{user_id}`.

FastAPI resolves duplicates by using the **first** registered handler, making the second registration silently dead. The duplicated routes include:
- `POST/GET /api/v1/users/` (2 each), `GET/PUT/DELETE /api/v1/users/{user_id}` (3 each)
- `POST/GET /api/v1/graphs/` (2 each), routes for `/api/v1/graphs/{graph_id}` (3 each)
- `POST/GET /api/v1/layouts` (2 each), individual layout routes (3 each)
- `POST/GET /api/v1/filters/` (2 each), individual filter routes (3 each)
- `POST/GET/DELETE /api/v1/processing-configs/{dashboard_id}` (3 each)
- Multiple dashboard CRUD routes (2–3 registrations each)
- Dashboard access, filters, graphs sub-routes (2 registrations each)

**Evidence:**
- `src/mkobi/app.py` lines 200–211: individual routers mounted with `/api/v1` prefix
- `src/mkobi/api/routes/dashboards.py` lines 19–23: composite router re-includes crud, access, filters, graphs sub-routers
- `src/mkobi/api/routes/users.py` lines 29–337 and `src/mkobi/api/routes/admin.py` lines 32–124: overlapping user management endpoints
- Programmatic route enumeration: 61 total routes, 41 unique, 20 duplicates

**Recommendation:** Eliminate duplicate route registration. Either:
- Remove the direct mounting of `dashboards_access`, `dashboards_filters`, `dashboards_graphs`, `graphs`, `layouts`, `filters`, `processing_configs`, and `users` from `app.py` (if their functionality is fully covered by composite routers or admin routes), OR
- Remove the sub-router inclusion from `dashboards.py` composite router and only mount individually in `app.py`.
- Consolidate user management: keep either `users.py` admin endpoints or `admin.py` admin endpoints, not both.

---

### BE-002: Transport Layer Directly Accesses Database Models (Raw SQL in Route Handler)

| Field | Value |
|-------|-------|
| **ID** | BE-002 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/api/routes/data.py` |
| **Classification** | mandatory |

**Description:** The `data.py` route handler directly imports and uses `sqlalchemy.select`, the raw `Graph` DB model from `mkobi.db.models.graphs`, and executes database queries against the session — bypassing the repository layer entirely. This violates the Clean Architecture requirement that all database interactions be abstracted behind repository interfaces.

Specifically, at lines 17, 28, and 117–121:
```python
from sqlalchemy import select                                    # Line 17
from mkobi.db.models.graphs import Graph                         # Line 28
graph_result = await db.execute(select(Graph).where(Graph.id == graph_id))  # Line 117-121
```

The route already has `graph_repo` injected via DI (line 49) but never uses it for this query.

**Evidence:**
- `src/mkobi/api/routes/data.py` lines 17–28: direct imports of `select` and `Graph` model
- `src/mkobi/api/routes/data.py` lines 117–121: raw SQL execution in transport layer
- `src/mkobi/api/deps.py` line 49: `graph_repo` is injected but unused for the graph lookup

**Recommendation:** Replace the raw `select(Graph)` with ` await graph_repo.get_by_id(graph_id, db)`. Remove the `from sqlalchemy import select` and `from mkobi.db.models.graphs import Graph` imports from the route handler entirely.

---

### BE-003: NameError Risk — `PermissionError` Not Imported in `data.py` Exception Handler

| Field | Value |
|-------|-------|
| **ID** | BE-003 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/api/routes/data.py` |
| **Classification** | mandatory |

**Description:** The `get_aggregated_data_endpoint` route handler in `data.py` has an `except PermissionError as e` clause (line 204) but **`PermissionError` is never imported** in the module. The module's imports include only: `APIRouter`, `AggregatedDataResponse`, `Any`, `AsyncSession`, `CurrentUser`, `DataService`, `Depends`, `Graph`, `GraphDataResponse`, `HTTPException`, `ProcessingResultData`, `Query`, `UUID`, `cast`, `check_dashboard_access`, `get_data_service`, `get_db_dependency`, `get_graph_repository`, `require_viewer_role`, `select`, `status`.

Since `PermissionError` is not imported from `mkobi.core.permissions`, Python will resolve it to the **builtin** `PermissionError` (which is for filesystem OS errors). The service layer (`data_service.py`) raises `mkobi.core.permissions.PermissionError`, which is a **different class**. This means:

1. The `except PermissionError` handler on line 204 will **never catch** the custom `PermissionError` raised by the service.
2. The custom `PermissionError` will propagate up to the generic `except Exception` handler (line 210), returning a **500 Internal Server Error** instead of the intended **403 Forbidden**.
3. If any code path somehow triggers the builtin `PermissionError`, the handler would catch it and return a misleading 403.

**Evidence:**
- `src/mkobi/api/routes/data.py` line 204: `except PermissionError as e:` — no import exists
- `src/mkobi/api/routes/data.py` lines 1–30: full import list, no `PermissionError`
- `src/mkobi/services/data_service.py` lines 131, 275, 321, 349: raises `PermissionError` from `mkobi.core.permissions`
- Confirmed by AST analysis: `PermissionError` not in imported names for `data.py`
- Contrast with `upload.py` line 27: correctly imports `from mkobi.core.permissions import PermissionError as PermissionError`

**Recommendation:** Add `from mkobi.core.permissions import PermissionError` to the imports in `data.py`, or better yet, replace the custom `PermissionError` with `PermissionDeniedException` throughout the codebase (which already has a proper `AppException` base class and is correctly handled by `add_exception_handlers` in `app.py`).

---

### BE-004: `mkobi.core.permissions.PermissionError` Shadows Python Builtin

| Field | Value |
|-------|-------|
| **ID** | BE-004 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/core/permissions.py`, consumers across all routes and services |
| **Classification** | advisory |

**Description:** The custom exception class `PermissionError` in `mkobi.core.permissions` (line 48) has the **same name** as Python's builtin `PermissionError` (a subclass of `OSError` for filesystem permission issues). When imported via `from mkobi.core.permissions import PermissionError`, the builtin is shadowed in that module's namespace. Combined with the missing import in `data.py` (BE-003), this shadowing causes the wrong exception class to be caught.

The project already has a better alternative: `PermissionDeniedException` (in `mkobi.utils.exceptions`), which extends `AppException` and is properly handled by the global exception handler registered in `app.py`.

**Evidence:**
- `src/mkobi/core/permissions.py` line 48: `class PermissionError(Exception):` — shadows builtin
- `src/mkobi/utils/exceptions.py` lines 53–61: `class PermissionDeniedException(AppException):` — project's own, well-integrated exception
- `src/mkobi/services/dashboard_service.py` lines 29, 181: already uses `PermissionDeniedException`
- `src/mkobi/api/routes/dashboards_crud.py` line 256: catches `PermissionDeniedException`
- `src/mkobi/services/data_service.py` line 16: uses `PermissionError` from `core.permissions`

**Recommendation:** Migrate all usages from `mkobi.core.permissions.PermissionError` to `mkobi.utils.exceptions.PermissionDeniedException` and set `error_code="PERMISSION_DENIED"`. Remove or rename the custom `PermissionError` in `core/permissions.py` to avoid shadowing the builtin.

---

### BE-005: `get_session` Exported from `deps.py` as Deprecated But Still Used Internally

| Field | Value |
|-------|-------|
| **ID** | BE-005 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/api/deps.py` |
| **Classification** | advisory |

**Description:** `deps.py` exports `get_session` with an explicit deprecation comment (line 40–41): "DEPRECATED: get_session is kept for backwards compatibility only. External code may import it from here. Remove in v2.0." It re-exports it from `mkobi.db.session` at line 42. However, `app.py` itself (line 25) and `data_worker.py` (line 26) both import `get_session` directly from `mkobi.db.session`, not from `deps.py`. The only consumer of `get_session` from `deps.py` would be external/test code. The deprecation warning suggests removal in v2.0, but it has been carried over without a tracking mechanism.

Additionally, `get_db` (line 90 in `session.py`) and `get_db_dependency` (line 93 in `deps.py`) are semantically identical — both create a session via `get_session()` context manager and yield it. Having two equivalent dependency injection paths creates confusion.

**Evidence:**
- `src/mkobi/api/deps.py` lines 40–42: deprecation comment and re-export
- `src/mkobi/app.py` line 25: `from mkobi.db.session import get_session` (direct, not via deps)
- `src/mkobi/workers/data_worker.py` line 26: direct import from `mkobi.db.session`
- `src/mkobi/db/session.py` lines 90–97: `get_db()` is functionally identical to `get_session()`

**Recommendation:** Remove the `get_session` export from `deps.py` entirely (it has no internal consumers through that path). Consolidate `get_db` and `get_session` into a single function, and standardize on `get_db_dependency` as the sole FastAPI DI entry point.

---

### BE-006: Dual Logging Pattern — `logging.getLogger` vs `get_logger`

| Field | Value |
|-------|-------|
| **ID** | BE-006 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | Multiple files across `api/routes/`, `services/`, `workers/` |
| **Classification** | advisory |

**Description:** The codebase uses two different logger initialization patterns:

1. **`get_logger(__name__)`** — from `mkobi.core.logging_config` (used in: `file_processing.py`, `data_service.py`, `upload.py`, `auth.py`, `data_worker.py`, `file_cleanup.py`, `exceptions.py`, `dashboard_repo.py`, `registration_request_repo.py`, `processing_logs.py`)
2. **`logging.getLogger(__name__)`** — standard library (used in: `users.py`, `admin.py`, `dashboards_crud.py`, `dashboards_access.py`, `dashboards_filters.py`, `dashboards_graphs.py`, `graphs.py`, `layouts.py`, `filters.py`, `processing_configs.py`, `app.py`, `config.py`, `session.py`, etc.)

The `get_logger()` function from `core.logging_config` applies `logging.basicConfig()` which may override or conflict with the structured JSON logging configuration. When both patterns coexist, some loggers may not respect the JSON formatting configured in `app.py`.

**Evidence:**
- `src/mkobi/services/data_service.py` line 15: `from mkobi.core.logging_config import get_logger`
- `src/mkobi/api/routes/users.py` line 8: `logger = logging.getLogger(__name__)`
- `src/mkobi/api/routes/admin.py` line 3: `logger = logging.getLogger(__name__)`
- `src/mkobi/app.py` line 43: `logger = logging.getLogger(__name__)`
- ~10 modules use `get_logger()`, ~15 modules use `logging.getLogger()`

**Recommendation:** Standardize all modules to use `from mkobi.core.logging_config import get_logger` for consistent structured logging. Ensure `get_logger()` is idempotent (doesn't re-apply `basicConfig` on subsequent calls).

---

### BE-007: Dead Code — `utils/decorators.py` Module Never Imported

| Field | Value |
|-------|-------|
| **ID** | BE-007 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/utils/decorators.py` |
| **Classification** | advisory |

**Description:** The entire `decorators.py` module (362 lines) containing decorators for timing, retry, logging, and access control is **never imported** by any other module in the codebase (confirmed via grep across all source files). This is dead code that adds maintenance burden without providing value.

**Evidence:**
- `grep "from mkobi.utils.decorators import" src/mkobi/` — 0 matches
- `grep "from mkobi.utils.decorators" src/mkobi/` — 0 matches

**Recommendation:** Move `decorators.py` to a separate utilities package or remove it. If decorators are needed, they should be integrated and used consistently.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 3 |
| MEDIUM | 1 |
| LOW | 3 |

## Mandatory Fixes

1. **BE-001**: Resolve 20 duplicate route registrations from overlapping sub-router mounting in `app.py` and `dashboards.py`. Choose a single mounting strategy.
2. **BE-002**: Replace raw SQL `select(Graph)` in `data.py` route handler with repository call via `graph_repo.get_by_id()`.
3. **BE-003**: Add `from mkobi.core.permissions import PermissionError` to `data.py` or migrate to `PermissionDeniedException` to fix the 500-error-instead-of-403 bug.

## Advisory Recommendations

4. **BE-004**: Rename/remove `mkobi.core.permissions.PermissionError` to stop shadowing Python's builtin; migrate to `PermissionDeniedException`.
5. **BE-005**: Remove deprecated `get_session` export from `deps.py`; consolidate `get_db`/`get_session`.
6. **BE-006**: Standardize logging to use `get_logger()` from `core.logging_config` everywhere.
7. **BE-007**: Remove or integrate unused `decorators.py` module.

## Doc Updates Needed

- Document the single-router mounting strategy for dashboards sub-routers.
- Clarify the relationship between `users.py` (user-facing) and `admin.py` (admin-facing) user management endpoints to avoid confusion about intentional duplicates vs. accidental ones.
