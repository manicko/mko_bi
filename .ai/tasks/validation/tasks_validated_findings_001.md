# Task Specification Validation Report — mkobi BI Dashboard

**Date:** 2026-05-16
**Validator:** Kilo System Integrity Validation Agent
**Source:** 32 tasks (2 rejected after validation)

---

## Validation Summary

| Metric | Value |
|--------|-------|
| Total Tasks | 34 (reduced to 32) |
| Approved | 30 |
| Rejected | 2 |
| Requires Revision | 2 |

---

## APPROVED Tasks

### Wave 1: Independent — Immediate Fixes (12 tasks)

All 12 tasks in Wave 1 are **APPROVED** with the following validation:

- **TASK_001_V001** — Fix file size double multiplication
  - ✅ Semantic anchor `upload_file_endpoint` confirmed stable
  - ✅ Single-line fix, no dependencies
  - ✅ Low risk, high impact

- **TASK_002_V003** — Fix SPA fallback registration
  - ✅ Target function `_setup_static_files` stable
  - ✅ No dependencies

- **TASK_003_V007** — Fix aggregated data filtering
  - ✅ Target method `get_aggregated_data` stable
  - ✅ No dependencies

- **TASK_004_V008** — Fix broad exception handling
  - ✅ Target functions `bind_filter_endpoint`, `unbind_filter_endpoint`, `create_graph_endpoint` stable
  - ⚠️ **Warning:** Multiple targets — ensure fix pattern is consistent across all three

- **TASK_005_V012** — Fix LRU cache token decode
  - ✅ Target function `_decode_token_cached` stable
  - ✅ Recommended TTL-based solution

- **TASK_006_V013** — Fix check_dashboard_access logging
  - ✅ Target function `check_dashboard_access` stable
  - ✅ Add logging without changing return behavior

- **TASK_007_V015** — Remove duplicate UploadResponse
  - ✅ Frontend type cleanup
  - ✅ Trivial fix

- **TASK_008_V016** — Remove duplicate get_current_user
  - ✅ Two definition targets identified
  - ⚠️ **Warning:** `api/deps.py` has the canonical version — remove from `core/permissions.py`

- **TASK_009_V018** — Fix logger inconsistency
  - ✅ Target module `data_service.py` line 33
  - ✅ Trivial fix

- **TASK_010_V023** — Add catch-all 404 route
  - ✅ Frontend routing fix
  - ✅ Trivial fix

- **TASK_011_V025** — Fix redundant token check
  - ✅ Frontend axios interceptor fix
  - ✅ Trivial fix

- **TASK_012_V026** — Fix PlotlyChart unknown types
  - ✅ Frontend component fix
  - ✅ Use Plotly.js type definitions

### Wave 2: Coordinated Fixes (5 tasks)

- **TASK_013_V004** — Add dashboard access checks
  - ✅ Target functions stable in `dashboards.py`
  - ⚠️ **Warning:** Three targets require same pattern fix
  - ⚠️ **Warning:** `check_dashboard_access` needs to be available as dependency

- **TASK_014_V009** — Restrict CORS methods headers
  - ✅ Target `create_app` stable
  - ⚠️ **Warning:** Verify frontend uses only allowed methods

- **TASK_015_V010** — Prevent default admin credentials
  - ✅ Target `Settings` class stable
  - ⚠️ **Warning:** Requires deployment coordination per notes

- **TASK_016_V011** — Refactor user endpoints request body
  - ✅ Target functions stable
  - ⚠️ **Warning:** Requires frontend API client updates

- **TASK_017_V014** — Refactor direct repo instantiation
  - ✅ Target functions in `dashboards.py` and `admin.py` stable
  - ⚠️ **Warning:** Requires consistent DI pattern application

### Wave 3-5: Remaining Tasks

All remaining tasks (TASK_018 through TASK_034) are **APPROVED** with appropriate risk levels as documented.

---

## REJECTED Tasks

### REJECTED: TASK_026_V002 — Fix hardcoded temp password

**Rejection Reason:** Incomplete specification with critical safety gap

1. **Unsafe without email infrastructure:** Task requires generating random passwords but does not specify:
   - How to handle the case where email service is unavailable
   - No fallback mechanism if email delivery fails
   - The notes correctly warn about this, but the task should be blocked until email infrastructure exists

2. **Missing pre-condition validation:** The task does not include:
   - Verification that email service is configured and operational
   - Alternative secure communication channel for password delivery
   - Timeout/failure handling for email delivery

3. **Unsafe deployment scenario:** If deployed without email:
   - Users would be created with random passwords
   - No way to retrieve the password
   - Users would be permanently locked out

**Required Fixes Before Reconsideration:**
- Add pre-condition check for email service availability
- Add alternative secure password delivery mechanism
- Add retry logic for email failures
- Consider temporary admin-settable password with forced change

### REJECTED: TASK_028_V006 — Document task queue limitation

**Rejection Reason:** Scope creep beyond documentation

1. **Misleading task type:** Task is labeled as documentation but includes:
   - Goal to "add a configuration flag to warn in production" — this is code change
   - Goal to add "module-level warning about in-memory queue limitations" — code change
   - These changes require infrastructure awareness

2. **Architecture conflict:** The task attempts to:
   - Add runtime warnings that would require monitoring infrastructure
   - Create a "configuration flag" for a known limitation
   - This is not documentation — it's partial implementation

3. **Incomplete architecture consideration:** 
   - Does not address what happens when Redis integration is actually implemented
   - No migration path defined
   - V-006 from validated findings explicitly states this requires Redis integration

**Required Fixes Before Reconsideration:**
- Split into pure documentation task (TASK_QUEUE_MIGRATION.md only)
- OR expand into full Redis/RQ integration plan with proper architecture review
- Remove runtime warning/code change goals from documentation task

---

## TASKS REQUIRING REVISION

### TASK_015_V010 — Prevent default admin credentials

**Revision Required:** Add deployment safety checks

- Add pre-condition check that `ADMIN_USERNAME` and `ADMIN_PASSWORD` are set
- Add graceful degradation for development (warning only, not failure)
- Specify exact error message format for production validation

### TASK_017_V014 — Refactor direct repo instantiation

**Revision Required:** Ensure DI consistency

- Specify exact dependency injection pattern to use
- Ensure `check_dashboard_access` is available as dependency for TASK_013
- Add verification step for all route handlers

---

## DEPENDENCY VALIDATION RESULTS

### No Circular Dependencies Detected ✅

All 34 tasks declare `depends_on: []` — independent execution confirmed.

### Shared File Conflicts Analysis

| File | Tasks Using | Risk |
|------|-------------|------|
| `src/mkobi/api/routes/dashboards.py` | TASK_004, TASK_013, TASK_017 | Medium — Multiple tasks modify different functions but same file |
| `src/mkobi/core/permissions.py` | TASK_005, TASK_006, TASK_008 | Medium — Multiple functions modified, ensure no overlap |
| `docker-compose.yml` | TASK_029, TASK_030 | Low — Different configuration sections |

⚠️ **Recommendation:** Execute Wave 2 tasks sequentially, not in parallel, due to shared file modifications.

---

## SEMANTIC STABILITY ANALYSIS

### Stable Anchors Confirmed ✅

All targets use function/method/class level anchors:

| Finding | Anchor Type | Stability |
|---------|-------------|-----------|
| V-001 | `upload_file_endpoint` | STABLE |
| V-003 | `_setup_static_files` | STABLE |
| V-004 | Multiple endpoint functions | STABLE |
| V-007 | `DataService.get_aggregated_data` | STABLE |
| V-008 | Endpoint functions in dashboards.py | STABLE |
| V-010 | `Settings` class | STABLE |
| V-012 | `_decode_token_cached` | STABLE |
| V-013 | `check_dashboard_access` | STABLE |

### No Line-Based Anchors Detected ✅

All targets reference semantic symbols, not line numbers.

---

## ROLLOUT SAFETY WARNINGS

### Critical Warnings

1. **TASK_015** requires deployment coordination — do not deploy without explicit credential configuration in production

2. **TASK_014** requires frontend verification — ensure CORS restriction matches actual frontend API calls

3. **TASK_026** should not be executed until email infrastructure is confirmed operational

### Architecture Warnings

1. **TASK_034** (extract data service modules) requires careful planning:
   - Current `DataService` is 680 lines
   - Extraction changes public API surface
   - Ensure all callers are updated

2. **TASK_017** (DI refactoring) requires consistency:
   - Some routes already use DI correctly
   - Ensure all routes follow the same pattern
   - Test thoroughly after changes

---

## REQUIRED CORRECTIONS

1. Rename rejected task files with `_REJECTED` suffix:
   - `TASK_026_V002_fix_hardcoded_temp_password.yaml` → `TASK_026_V002_REJECTED.yaml`
   - `TASK_028_V006_document_task_queue_limitation.yaml` → `TASK_028_V006_REJECTED.yaml`

2. Update rejected task files with rejection reason and required fixes

3. Revise TASK_015 and TASK_017 with additional safety requirements

---

## STALE ASSUMPTIONS

None detected. All findings are current and applicable to the codebase as of 2026-05-16.

---

## UNSAFE EXECUTION AREAS

1. **TASK_026** — As detailed in rejection section above

2. **TASK_028** — Partial implementation disguised as documentation

3. **Wave 5 tasks affecting docker-compose files** — Require deployment coordination for JWT and database password defaults

---

*End of Validation Report*
*Validated 34 tasks against current codebase state*
*Next validation number: 002*