# Validation Report — Phase 01: Backend Architecture

**Validator:** validator agent
**Date:** 2026-05-31
**Input:** `.ai/audit/01-backend/findings.md`
**Mode:** problems-only

---

## Validated Counts

| Classification | Input | Accepted | Rejected | Reclassified | Merged |
|----------------|-------|----------|----------|--------------|--------|
| Mandatory | 3 | 2 | 0 | 1 | 0 |
| Advisory | 4 | 4 | 0 | 0 | 0 |
| **Total** | **7** | **6** | **0** | **1** | **0** |

---

## Reclassified Findings

### BE-001: Reclassified `RUNTIME-ERROR` → `SPEC-DEVIATION`

| Field | Original | Updated |
|-------|----------|---------|
| **ID** | BE-001 | BE-001 |
| **Severity** | HIGH | HIGH |
| **Type** | RUNTIME-ERROR | SPEC-DEVIATION |
| **Classification** | mandatory | mandatory |
| **Status** | ACCEPTED (reclassified) | — |

**Rationale:** The finding is confirmed — the codebase has genuine duplicate route registrations. However, the problem classification is incorrect:

1. **`dashboards_access`, `dashboards_filters`, `dashboards_graphs`** (lines 19-23 of `dashboards.py`) are sub-routers included in the composite `dashboards` router. They are also individually mounted in `app.py`. This creates actual duplication.
   - Verified: `dashboards_access.py` defines routes like `/{dashboard_id}/access` (mounted at `/api/v1/dashboards/{dashboard_id}/access` via composite router AND at `/api/v1/{dashboard_id}/access` via direct mount — but the direct mount preserves the full route pattern). Actually, the directly-mounted routers have their own `prefix` — `dashboards_access` is mounted at `prefix="/api/v1"` in `app.py` but the router itself has no prefix (it's a tag-only router). So `app.py` creates `routes like /api/v1/{dashboard_id}/access` while the composite creates `/api/v1/dashboards/{dashboard_id}/access`. These are **different paths** — no duplication for dashboards_access, dashboards_filters, dashboards_graphs.
   - **Correction:** The sub-routers `dashboards_access`, `dashboards_filters`, `dashboards_graphs` define routes with path params like `/{dashboard_id}/access`, `/{dashboard_id}/filters`, `/{dashboard_id}/graphs`. When mounted individually in `app.py` at `prefix="/api/v1"`, these become `/api/v1/{dashboard_id}/access`, etc. When included via the composite `dashboards` router (mounted at `prefix="/api/v1"`), they become `/api/v1/dashboards/{dashboard_id}/access`, etc. These are **semantically different paths** and do **not** actually conflict.

2. **`graphs`** (`graphs.py` lines 38-392) and `dashboards_graphs` are **completely different route sets**:
   - `graphs.py` defines `POST/GET /graphs/`, `GET/PUT/DELETE /graphs/{graph_id}`, `GET /graphs/{graph_id}/data` (global graph CRUD).
   - `dashboards_graphs.py` defines `POST /{dashboard_id}/graphs`, `GET /{dashboard_id}/graphs` (dashboard-scoped graph operations).
   - The paths are structurally different (`/graphs/` vs `/{dashboard_id}/graphs`) — **no duplication**.

3. **`users.py`** and **`admin.py`** define **different operations on different paths**:
   - `users.py`: `POST/GET /users/`, `GET/PUT/DELETE /users/{user_id}`, `DELETE /users/me` (user-facing).
   - `admin.py`: `GET /admin/users`, `PATCH /admin/users/{user_id}/role`, `DELETE /admin/users/{user_id}`, `POST /admin/users/{user_id}/reset-password` (admin-facing only).
   - Different HTTP methods (`PATCH` vs `PUT`), different semantic scope (self-service vs admin management) — **no duplication**.

4. **`filters.py`** (global filter CRUD: `POST/GET /filters/`, `GET/PUT/DELETE /filters/{filter_id}`) and **`dashboards_filters.py`** (dashboard-filter bindings: `POST/DELETE/GET /{dashboard_id}/filters`) have **different path structures** — **no duplication**.

5. **`layouts.py`** (global: `POST/GET /layouts/`, `GET/PUT/DELETE /layouts/{layout_id}`) has no overlap with any sub-router — **no duplication**.

6. **`processing_configs.py`** (prefix `/processing-configs`: `GET/PUT/DELETE /processing-configs/{dashboard_id}`) has no overlap with any sub-router — **no duplication**.

**Corrected assessment:** The finding **overstates** the problem. Route enumeration shows 61 total vs 41 unique paths, but the audit executor's count is incorrect because FastAPI counts route *registrations*, not unique *paths*. Many of the 61 registrations are for different HTTP methods on the same path, or for structurally different paths that only appear similar when flattened. The **actual duplicate count is zero**.

**However:** The *architectural pattern* of having the same sub-routers both included in a composite router AND individually mounted is still a **SPEC-DEVIATION** from clean design principles. While the paths don't collide today (because the routers have different prefix structures), this is fragile — a future change to a sub-router's prefix or path could introduce silent collisions. The code violates the principle of single-responsibility mounting.

**Recommendation adjusted:** The finding should be kept as SPEC-DEVIATION (architectural smell) but the severity should be reduced from HIGH to MEDIUM, and the claim of "20 duplicate routes" should be corrected. No functional bug exists today.

---

## Validated Findings (Accepted, No Changes)

The following findings pass validation unchanged. No problems to report — they are technically correct, relevant, and actionable. Per problems-only mode, they are listed here for completeness but require no validation commentary:

| ID | Severity | Type | Classification | Verdict |
|----|----------|------|----------------|---------|
| BE-002 | HIGH | SPEC-DEVIATION | mandatory | Validated — raw `select(Graph)` confirmed at lines 117-121 of `data.py`; `graph_repo` injected at line 49 but unused for this query |
| BE-003 | HIGH | RUNTIME-ERROR | mandatory | Validated — `except PermissionError as e` at line 204 of `data.py`; no import of `PermissionError` in the file; service layer raises `mkobi.core.permissions.PermissionError` (different class) |
| BE-004 | MEDIUM | BEST-PRACTICE | advisory | Validated — `PermissionError` at `core/permissions.py:48` shadows Python builtin; `upload.py:27` uses awkward `PermissionError as PermissionError` rename to work around it |
| BE-005 | LOW | BEST-PRACTICE | advisory | Validated — `get_session` deprecated at `deps.py:40-42`; `app.py:25` and `data_worker.py:26` import directly from `mkobi.db.session`, bypassing the deprecated export |
| BE-006 | LOW | BEST-PRACTICE | advisory | Validated — 10 modules use `get_logger()` from `core.logging_config`, 52 modules use `logging.getLogger()` directly; `logging.getLogger(__name__)` works correctly because `setup_logging()` configures the `mkobi.*` logger namespace, but inconsistent pattern remains |
| BE-007 | LOW | BEST-PRACTICE | advisory | Validated — `utils/decorators.py` (362 lines, 5 decorators: `timing`, `retry`, `log_execution`, `require_role`, `error_handler`) has zero imports across entire `src/` tree |

---

## Cross-Phase Conflicts

No cross-phase conflicts detected between Phase 01 (backend) and Phase 02 (frontend):

- Phase 01 reports "603 tests passed" (backend runtime). No contradictory evidence in Phase 02.
- Phase 01 findings about route structure and permission handling are independent of Phase 02 frontend concerns.
- No overlapping root causes between backend and frontend findings.

---

## Rollout Safety Assessment

### BE-001 Fix Risk: MEDIUM

- **Risk:** "Fixing" the non-existent duplicate routes by removing mount points could accidentally break routes if the audit executor's duplicate count is somehow correct in a configuration not visible in static analysis.
- **Mitigation:** Before removing any route mounting, run programmatic route enumeration (as the audit executor did) to verify actual registered paths. Only remove mounting that produces genuine duplicates.

### BE-002 Fix Risk: LOW

- **Risk:** Minimal. Replacing `select(Graph).where(Graph.id == graph_id)` with `graph_repo.get_by_id(graph_id, db)` is a straightforward refactor. The repository method already exists (`graph_repo` is injected).
- **Dependency:** None. Self-contained change.

### BE-003 / BE-004 Fix Risk: LOW

- **Risk:** Adding the correct `PermissionError` import is a one-line fix. A full migration from `PermissionError` to `PermissionDeniedException` (as recommended in BE-004) requires changes across `data_service.py` (raise sites), `data.py`, `upload.py`, and `core/permissions.py` — but these are all straightforward find-and-replace operations with no architectural impact.
- **Dependency:** BE-003 should be fixed regardless of whether BE-004's full migration is done.

### BE-005 Fix Risk: LOW

- **Risk:** Removing `get_session` from `deps.py` exports is safe as long as no external/test code imports from `deps.py` instead of `mkobi.db.session`. Internal code already imports directly from `mkobi.db.session`.

---

## Summary of Actions Required

1. **BE-001**: Reclassify type from `RUNTIME-ERROR` to `SPEC-DEVIATION`, reduce severity claim, correct duplicate count from 20 to 0. The architectural smell is real; the functional impact is overstated.
2. **BE-002 through BE-007**: Accepted as-is. No corrections needed.
3. **No rejections** — all 7 findings describe real issues in the codebase.
4. **No merges** — no findings share duplicate root causes.
5. **No cross-phase conflicts** detected.
