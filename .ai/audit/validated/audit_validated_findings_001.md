# Validated Audit Findings — mkobi BI Dashboard

**Date:** 2026-05-20
**Validator:** Kilo (System Integrity Validation Agent)
**Source Audit:** `.ai/audit/problems/implementation_audit_001.md`
**Source Structure:** `.ai/structure/`
**Source Tasks:** `.ai/tasks/done/`

---

## Executive Summary

| Category | Count |
|----------|-------|
| Total findings in source audit | 5 (2 MINOR + 3 INFO) |
| **Validated (confirmed)** | **3** |
| **Rejected (stale/incorrect)** | **1** |
| **Downgraded (less severe than claimed)** | **1** |
| Merged findings | 0 |
| New findings discovered during validation | 0 |

**Overall Assessment:** The source audit is of high quality. 3 of 5 findings are accurate and current. 1 finding (MINOR-001) is **stale** — the described gap has been implemented since the audit was written. 1 finding (INFO-003) is accurate but should be downgraded to a lower priority since the `config` parameter is harmless backward-compatibility code.

---

## Validated Findings

### VALIDATED-001: Service Methods Still Have `db=None` Fallback Pattern

- **Original Ref:** MINOR-002 / V-009 (TASK_036)
- **Severity:** MEDIUM
- **Status:** CONFIRMED — Valid finding
- **Finding ID:** VF-001

**Description:**
All service methods across the codebase retain the `db: AsyncSession | None = None` fallback pattern. When called without a `db` parameter, each service method creates its own session internally, breaking transaction atomicity across multiple service calls.

**Affected Modules:**
- `src/mkobi/services/auth_service.py` — 9 methods with `db=None`
- `src/mkobi/services/data_service.py` — 7 methods with `db=None`
- `src/mkobi/services/dashboard_service.py` — 13 methods with `db=None`
- `src/mkobi/services/layout_service.py` — 5 methods with `db=None`
- `src/mkobi/services/graph_service.py` — 10 methods with `db=None`
- `src/mkobi/services/filter_service.py` — 6 methods with `db=None`
- `src/mkobi/services/processing_config_service.py` — 7 methods with `db=None`
- `src/mkobi/services/processing_log_service.py` — 5 methods with `db=None`

**Affected Symbols:**
- `AuthService.register_user()`, `login_user()`, `get_user_by_id()`, `verify_token()`, `change_password()`, `delete_user()`, `get_user_by_email()`, `check_rate_limit()`, `list_users()`
- `DataService.process_upload()`, `get_aggregated_data()`, `get_processing_status()`, `cancel_processing()`, `retry_processing()`, `get_processing_history()`, `delete_processing_data()`
- `DashboardService.create_dashboard()`, `get_dashboard()`, `list_dashboards()`, `update_dashboard()`, `delete_dashboard()`, `get_dashboard_by_name()`, `get_dashboard_config()`, `update_dashboard_config()`, `get_dashboard_layout()`, `set_dashboard_layout()`, `get_dashboard_graphs()`, `get_dashboard_filters()`, `get_dashboard_users()`
- (And similar patterns in all other service classes)

**Root Cause:**
TASK_036 (transaction boundaries refactoring) is marked as `status: pending` and explicitly deferred. The task itself acknowledges HIGH RISK and recommends deferring until test quality improves. The `db=None` pattern is a deliberate backward-compatibility measure.

**Impact:**
- **Operational:** Low — current code paths always go through FastAPI dependency injection which provides `db`.
- **Architectural:** Medium — the pattern creates implicit coupling between service layer and session management, violating Clean Architecture separation.
- **Maintenance:** Medium — any future caller that invokes service methods without `db` will silently create a new session, potentially breaking transaction atomicity.

**Required Correction:**
This is a systemic refactoring (HIGH RISK per TASK_036's own assessment). Should be deferred until test quality improves. When executed:
1. Remove `db=None` fallback from all service methods
2. Make `db: AsyncSession` mandatory in all service method signatures
3. Update all callers to pass `db`
4. Update tests that call service methods without `db`

**Execution Risk:** HIGH — As noted in TASK_036 itself. Should not be started until test quality is improved.

**Dependency Notes:**
- TASK_036 → TASK_037 (consolidate get_db) — correct sequencing
- No other tasks depend on this change

**Rollout Considerations:**
- Must be done as a single atomic change across all services
- Cannot be incrementally rolled out (changing some services but not others would create inconsistency)
- Requires full test suite rewrite for overmocked service tests
- Recommend: create a comprehensive test harness first, then execute the refactoring

**Validation Notes:**
Confirmed via grep across all 8 service files. 72 occurrences of `db: AsyncSession | None = None` found. The pattern is consistent and pervasive. The finding is accurate and current.

---

### VALIDATED-002: `check_dashboard_access` Still Has `db=None` Fallback

- **Original Ref:** INFO-001 (related to V-009)
- **Severity:** INFORMATIONAL
- **Status:** CONFIRMED — Valid finding, subset of VF-001
- **Finding ID:** VF-002

**Description:**
`check_dashboard_access()` in `permissions.py` retains `db: AsyncSession | None = None` and creates its own session when `db is None`. While the data route now passes `db` correctly (TASK_030), the function signature maintains the fallback for backward compatibility.

**Affected File:** `src/mkobi/core/permissions.py`
**Affected Symbol:** `check_dashboard_access()` at line 204

**Root Cause:**
Same as VF-001. This is part of the systemic `db=None` pattern. The function is a FastAPI dependency used in route handlers, and the fallback exists for any code that might call it directly.

**Impact:**
- **Operational:** None — all current callers pass `db`.
- **Architectural:** Low — the fallback creates a hidden dependency on session management in the `core` layer.

**Required Correction:**
Part of TASK_036 execution. When service methods are refactored, this function should also be updated to require `db` as mandatory.

**Execution Risk:** LOW — but should be done as part of the larger TASK_036 refactoring, not independently.

**Dependency Notes:**
- Dependent on TASK_036 completion
- No circular dependencies

**Rollout Considerations:**
- Should be bundled with TASK_036 rollout
- Independent execution is possible but would be a partial fix

**Validation Notes:**
Confirmed via code inspection. The function at line 204-208 has `db: AsyncSession | None = None`. The finding is accurate and current. This is a subset of VF-001.

---

### VALIDATED-003: `get_db()` Duplication Between `permissions.py` and `deps.py`

- **Original Ref:** INFO-002 / V-026 (TASK_037)
- **Severity:** INFORMATIONAL
- **Status:** CONFIRMED — Valid finding
- **Finding ID:** VF-003

**Description:**
Two nearly identical session-creation functions exist:
- `get_db()` in `src/mkobi/core/permissions.py` (line 94) — async generator yielding `AsyncSession`
- `get_db_dependency()` in `src/mkobi/api/deps.py` (line 91) — async generator yielding `AsyncSession`

Both create a session via `get_session()` context manager and handle cleanup. This is a known architectural debt.

**Affected Modules:**
- `src/mkobi/core/permissions.py` — `get_db()` at line 94
- `src/mkobi/api/deps.py` — `get_db_dependency()` at line 91

**Root Cause:**
TASK_037 is marked as `status: pending` and depends on TASK_036. The duplication exists because `permissions.py` (core layer) was given its own `get_db()` to avoid importing from `api/deps.py` (API layer), preserving dependency direction.

**Impact:**
- **Operational:** None — both functions create sessions identically.
- **Architectural:** Low — code duplication increases maintenance surface. If session creation logic changes, both must be updated.
- **Dependency Direction:** The duplication exists specifically to avoid upward dependency (core importing from api). Consolidating requires careful handling of import direction.

**Required Correction:**
TASK_037: Remove `get_db()` from `permissions.py` and import from `deps.py`. However, this creates a dependency from `core` to `api`, which violates Clean Architecture. The correct approach is to move the shared session factory to a neutral location (e.g., `db/session.py`) and have both modules import from there.

**Execution Risk:** LOW — but the architectural implication (dependency direction) must be considered. The current TASK_037 description suggests importing from `deps.py` into `permissions.py`, which would create a core→api import. This should be revised.

**Dependency Notes:**
- TASK_037 depends on TASK_036 (correctly sequenced to avoid conflicts)
- No circular dependencies

**Rollout Considerations:**
- Safe to execute independently if the dependency direction issue is resolved
- Should be done after TASK_036 to avoid merge conflicts
- Recommended revision: move shared session logic to `db/session.py` instead of cross-importing

**Validation Notes:**
Confirmed via code inspection. Both functions exist and are nearly identical. The finding is accurate and current. **Architectural warning:** The proposed fix in TASK_037 (importing from `deps.py` into `permissions.py`) would violate Clean Architecture dependency direction (core should not import from api). The task should be revised to move the shared logic to a neutral module.

---

## Rejected Findings

### REJECTED-001: Stale Processing Heartbeat Not Wired Into Startup

- **Original Ref:** MINOR-001 / V-013 (TASK_015)
- **Severity:** Claimed MINOR — **REJECTED (stale)**
- **Finding ID:** RF-001

**Original Claim:**
The `cleanup_stale_processing_logs()` function exists in `data_worker.py` but `start_stale_processing_cleanup_task()` is never called from `DatabaseStarter.startup()` or anywhere else.

**Rejection Reason:** **STALE — The functionality has been implemented.**

**Evidence:**
1. `src/mkobi/app.py` line 32: `from mkobi.workers.data_worker import start_stale_processing_cleanup_task`
2. `src/mkobi/app.py` lines 73-79: The `lifespan()` function starts the cleanup task:
   ```python
   cleanup_task = asyncio.create_task(
       start_stale_processing_cleanup_task(
           interval_seconds=config.stale_processing_cleanup_interval_seconds,
           timeout_minutes=config.stale_processing_timeout_minutes,
       )
   )
   ```
3. `src/mkobi/workers/data_worker.py` lines 405-428: The `start_stale_processing_cleanup_task()` function is fully implemented with configurable interval and timeout.
4. `src/mkobi/config.py` lines 251-252: Configuration values `stale_processing_timeout_minutes` (default 30) and `stale_processing_cleanup_interval_seconds` (default 300) exist.

**Root Cause of Staleness:**
The audit finding was written before the implementation was wired into `app.py`. The task file (TASK_015) is marked as `status: pending` but the actual implementation is present and active in the codebase. The task status was not updated to reflect completion.

**Required Action:**
- Update TASK_015 status from `pending` to `done` (the implementation is complete)
- No code changes needed — the feature is already deployed

**Validation Notes:**
The finding was verified against the current codebase and found to be stale. The wiring exists in `app.py` lifespan handler. The cleanup task is started as an `asyncio.create_task()` after `starter.startup()` completes, with proper configuration from `Settings`.

---

## Downgraded Findings

### DOWNGRADED-001: `update_dashboard` Signature Has Unused `config` Parameter

- **Original Ref:** INFO-003 / V-029 (TASK_035)
- **Severity:** Claimed INFORMATIONAL — **DOWNGRADED to NEGLIGIBLE**
- **Finding ID:** DF-001

**Original Claim:**
The `update_dashboard()` method has both `update_data` and `config` parameters. The `config` parameter is for backward compatibility and is merged into the `data` dict. The route only passes `update_data`.

**Downgrade Rationale:**
The `config` parameter is explicitly documented as backward-compatible. It is harmless dead code that:
1. Does not affect runtime behavior (the route doesn't pass it)
2. Does not create security risks
3. Does not violate architectural boundaries
4. May be used by future callers or external integrations

Removing it would be a speculative cleanup with no measurable benefit. The parameter is self-documenting as "backward compatibility" in the docstring.

**Affected File:** `src/mkobi/services/dashboard_service.py`
**Affected Symbol:** `update_dashboard()` at line 261

**Recommendation:** Leave as-is. Do not create a task for this. If TASK_036 (transaction boundaries) is executed, the parameter can be removed as part of that refactoring if desired, but it should not be a standalone task.

**Validation Notes:**
Confirmed via code inspection. The `config` parameter exists at line 265. The finding is technically accurate but the severity is negligible. No action required.

---

## Dependency Validation Results

### Dependency Graph

The audit findings reference two pending tasks that form a dependency chain:

```
TASK_036 (transaction boundaries) → TASK_037 (consolidate get_db)
```

**Validation:**
- **DAG validity:** PASS — No circular dependencies
- **Ordering:** PASS — TASK_037 correctly depends on TASK_036
- **Isolation:** PASS — Each task has a single, well-defined scope
- **Coupling:** LOW — TASK_037 only touches `permissions.py` and `deps.py`, while TASK_036 touches all service files

### Cross-Finding Dependencies

- VF-001 (db=None pattern) and VF-002 (check_dashboard_access db=None) are **semantically identical** root causes. VF-002 is a subset of VF-001.
- VF-003 (get_db duplication) is **architecturally related** to VF-001 — both involve session management patterns.
- All three validated findings should be addressed in a single coordinated effort (TASK_036 + TASK_037).

---

## Rollout Safety Analysis

### Validated Findings Rollout

| Finding | Risk | Rollout Strategy |
|---------|------|-----------------|
| VF-001 (db=None pattern) | HIGH | Atomic change across all services. Requires test harness first. |
| VF-002 (check_dashboard_access) | LOW | Bundle with VF-001. |
| VF-003 (get_db duplication) | LOW | Execute after VF-001. Watch dependency direction. |

### Safe Execution Sequence

1. **Pre-work:** Improve test quality, especially for overmocked service tests
2. **Phase 1:** Execute TASK_036 (remove db=None from all services) — atomic change
3. **Phase 2:** Execute TASK_037 (consolidate get_db) — after TASK_036 stabilizes
4. **Verification:** Run full test suite after each phase

### Rollout Risks

- **VF-001:** HIGH RISK — 72 method signatures across 8 service files must change simultaneously. Any missed caller will break at runtime.
- **VF-003 (revised):** MEDIUM RISK — If TASK_037 is revised to move session logic to a neutral module, the migration must ensure no import cycles are created.

---

## Semantic Stability Analysis

### Anchor Stability for Validated Findings

| Finding | Anchor Type | Stability | Notes |
|---------|------------|-----------|-------|
| VF-001 | Method signatures | STABLE | Service method names are unlikely to change. The `db=None` pattern is easy to target via grep. |
| VF-002 | Function signature | STABLE | `check_dashboard_access` is a well-established FastAPI dependency. |
| VF-003 | Function definitions | STABLE | Both `get_db` and `get_db_dependency` are small, isolated functions. |

### Anchor Stability for Rejected Findings

| Finding | Anchor Type | Stability | Notes |
|---------|------------|-----------|-------|
| RF-001 | N/A (rejected) | N/A | The claimed missing wiring exists. No action needed. |

### Preferred Anchors for Future Execution

For TASK_036 execution, the recommended semantic anchors are:
- **Function signatures** — target the `db=None` parameter in each service method
- **Class boundaries** — each service class is a natural isolation boundary
- **Return statements** — verify that internal session creation logic is removed

---

## Execution Applicability Analysis

### Task Status vs. Codebase Reality

| Task | Task File Status | Codebase Reality | Discrepancy? |
|------|-----------------|-----------------|--------------|
| TASK_015 (stale processing) | `pending` | **IMPLEMENTED** in `app.py` and `data_worker.py` | **YES** — task status not updated |
| TASK_036 (transaction boundaries) | `pending` | Not implemented — `db=None` pattern persists | No — correctly pending |
| TASK_037 (consolidate get_db) | `pending` | Not implemented — duplication persists | No — correctly pending |

**Critical Discrepancy:** TASK_015 is marked as `pending` but the implementation is complete and wired in. This is a documentation/maintenance issue, not a code issue. The task file should be updated to `done` status.

### Execution Readiness

- **VF-001 (TASK_036):** NOT READY — Blocked by test quality improvements. The task itself acknowledges this.
- **VF-002:** NOT READY — Dependent on VF-001.
- **VF-003 (TASK_037):** NOT READY — Dependent on TASK_036. Additionally, the task description should be revised to address the dependency direction concern.

---

## Architectural Consistency Warnings

### ACW-001: Dependency Direction Risk in TASK_037

**Warning:** TASK_037 as currently described proposes importing from `mkobi.api.deps` into `mkobi.core.permissions`. This would create a dependency from the `core` layer to the `api` layer, violating Clean Architecture dependency direction (inner layers should not depend on outer layers).

**Recommendation:** Revise TASK_037 to move the shared session factory to `mkobi.db.session` (which is already imported by both modules) and have both `permissions.py` and `deps.py` import from there.

### ACW-002: Raw SQL in Infrastructure Code

**Warning:** The audit notes (SSW-001, SSW-002) correctly identify that `ensure_admin_user()` and `cleanup_old_logs()` in `starter.py` use raw SQL with hardcoded table/column names. This is acceptable for infrastructure code but creates implicit schema coupling.

**Recommendation:** No immediate action. Document that these functions must be updated if the `users` or `processing_logs` table schemas change.

---

## Final Verdict

### Summary

| Finding ID | Original Ref | Severity | Status | Action |
|------------|-------------|----------|--------|--------|
| VF-001 | MINOR-002 / V-009 | MEDIUM | **VALIDATED** | Execute TASK_036 (blocked by test quality) |
| VF-002 | INFO-001 | INFORMATIONAL | **VALIDATED** | Bundle with VF-001 |
| VF-003 | INFO-002 / V-026 | INFORMATIONAL | **VALIDATED** | Execute TASK_037 (revise for dependency direction) |
| RF-001 | MINOR-001 / V-013 | — | **REJECTED (stale)** | Update TASK_015 status to `done` |
| DF-001 | INFO-003 / V-029 | NEGLIGIBLE | **DOWNGRADED** | No action needed |

### Conditions for Downstream Planning

1. **TASK_015 status must be updated** from `pending` to `done` to reflect the actual implementation state.
2. **TASK_036 remains blocked** until test quality improvements are made. No downstream tasks should depend on it until unblocked.
3. **TASK_037 should be revised** to address the dependency direction concern before execution.
4. **VF-001 and VF-002 should be merged** into a single planning item (TASK_036) since they share the same root cause and solution.
5. **No blocking issues** prevent production deployment. All validated findings are either deferred (VF-001, VF-002, VF-003) or negligible (DF-001).

---

**End of Validated Findings Document**
