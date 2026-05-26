# Validated Audit Findings — mkobi BI Dashboard

**Date:** 2026-05-26
**Validator:** OWL (Kilo Agent)
**Input reports:**
- `audit/project/audit_report_001.md` (362 lines, 10 findings)
- `audit/project/audit_report_001_part1.md` (45 lines, summary only)
- `audit/project/audit_report_003.md` (326 lines, 12 findings)
- `audit/tests/audit_report_001.md` (321 lines, 22 findings)
- `audit/tests/audit_report_002.md` (255 lines, 15 findings + infrastructure)

**Validation method:** Source code verification + structural analysis + cross-report deduplication

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total raw findings across all reports | ~59 |
| After deduplication | 28 unique findings |
| **Mandatory fixes** (security, data loss, correctness) | 5 |
| **Advisory recommendations** (best practices, improvements) | 18 |
| **Doc updates needed** | 3 |
| **Rejected findings** | 4 |
| **Merged into other findings** | ~27 |

---

## Cross-Report Deduplication Map

Source report IDs are referenced as: `R1` = audit_report_001.md, `R3` = audit_report_003.md, `T1` = tests/audit_report_001.md, `T2` = tests/audit_report_002.md. `P1` = audit_report_001_part1.md (summary only, no unique IDs).

| Validated ID | Original IDs | Merged |
|---|---|---|
| V-001 | R1-F005, R3-HIGH-upload, R3-FileRec-upload | Temp file cleanup gap — 3 reports, same issue |
| V-002 | R1-F002, R3-FileRec-processing_logs | Admin logs skip/limit vs page/page_size |
| V-003 | R1-F001 | LoginForm bypasses useAuth hook |
| V-004 | R1-F003 | Raw SQL f-strings in db/starter.py |
| V-005 | R1-F004, R3-7Sidebar | Sidebar dead code |
| V-006 | R3-HIGH-dashboards | Inline access checks in route handlers |
| V-007 | R3-MEDIUM-pydantic, R3-app-pydantic | Pydantic ValidationError returns 500 |
| V-008 | R3-MEDIUM-cors, R3-app-cors | CORS wildcard in production only warns |
| V-009 | R3-MEDIUM-processing_status | ProcessingStatus SUCCESS/COMPLETED |
| V-010 | R1-F006 | dashboard_service.get_dashboard type annotation |
| V-011 | R1-F007, Merged into broader consistency | dashboard_service.create_dashboard commit pattern |
| V-012 | R1-F008, R3-DOC-admin-registration | Registration request status filter missing |
| V-013 | R1-F009, R3-data-filters | Data filters silently ignored |
| V-014 | R1-F010, R3-MEDIUM-security | _get_config() singleton mutation |
| V-015 | R3-LOW-process_file_endpoint | Hardcoded overwrite mode in process endpoint |
| V-016 | R3-LOW-jsonb_upsert | JSONB UPSERT index compatibility |
| V-017 | R3-LOW-di_inconsistency | Inconsistent DI pattern in route handlers |
| V-018 | T2-FINDING0, R3-CRITICAL-docker | Test Docker: mkobi_app role missing |
| V-019 | T1-Finding1, T2-F10 | JWT user_id type coercion in test_security |
| V-020 | T1-Finding2, T2-F9 | AggregatedData chart_type test wrong reason |
| V-021 | T1-Finding3, T1-F11, T2-F11 | Graph API coverage critically thin |
| V-022 | T1-Finding4, T1-F12, T2-F6 | Duplicate storage_manager tests |
| V-023 | T1-Finding5 | clean_env fixture backup bug |
| V-024 | T1-Finding6, T2-F4 | Tests creating large real files |
| V-025 | T1-Finding7, T2-F7 | test_deps viewer/admin misleading |
| V-026 | T1-Finding8, T2-F3 | test_auth double flush |
| V-027 | T1-F16/17 | Repository CRUD coverage gaps |
| V-028 | T1-F19, T2-F13 | Data processing zero test coverage |

---

## Part 1 — Mandatory Fixes

These findings must be addressed. They affect correctness, data integrity, operational reliability, or test suite viability.

---

### V-001: Temp file cleanup gap on upload failure

| Field | Value |
|---|---|
| **ID** | V-001 |
| **Severity** | HIGH |
| **Type** | [SPEC-DEVIATION] |
| **Classification** | **MANDATORY** |
| **Original IDs** | R1-F005, R3-HIGH-upload |
| **Status** | CONFIRMED — deviates from spec requirement "temporary files after processing **must be removed**" |

**Description:**
The upload endpoint (`src/mkobi/api/routes/upload.py`, lines ~140-198) streams the uploaded file to a temporary file on disk. If `data_service.process_upload()` raises an exception after the temp file is written, no cleanup occurs. The file remains on disk indefinitely.

**Impact:**
- Disk space leak on failed uploads. With a 100MB file limit, repeated failed uploads could exhaust disk space.
- The spec explicitly states temp files must be removed after processing — this is a spec deviation.

**Affected modules:**
- `src/mkobi/api/routes/upload.py` — `_upload_file_endpoint()`
- `src/mkobi/services/file_processing.py` — `validate_file()`, `find_task_file()`

**Affected symbols:**
- `upload.py:_upload_file_endpoint`
- `data_service:process_upload`

**Root cause:**
No `try/finally` block around the temp file lifecycle. The error handlers at lines 200-215 do not clean up `temp_file_path`.

**Fix target:** Code change (production code, not docs).

**Recommended fix:**
Wrap the processing block in `try/finally`. In the `finally` block, check if `temp_file_path.exists()` and unlink it. Skip cleanup only if processing succeeded and the file was moved to its final location.

**Semantic anchor stability:** HIGH — `_upload_file_endpoint` is a named FastAPI route handler. The `temp_file_path` variable and `data_service.process_upload()` call are stable insertion points.

**Validation notes:** Source code confirmed. The finding is valid and the fix is well-scoped. This is a correctness/operational issue that directly impacts production reliability.

**Dependency notes:** No dependencies on other findings. Can be fixed independently.

**Effort:** Small (~15 lines of code)

---

### V-002: Test Docker environment — mkobi_app role missing (173 tests broken)

| Field | Value |
|---|---|
| **ID** | V-0018 |
| **Severity** | CRITICAL |
| **Type** | [SPEC-DEVIATION] |
| **Classification** | **MANDATORY** |
| **Original IDs** | T2-FINDING0, R3-CRITICAL-docker |
| **Status** | CONFIRMED — 173 of 386 tests fail in Docker |

**Description:**
`docker/docker-compose.test.yml` does not mount the `init-scripts/` volume for the `test-db` service. The `1-create-app-role.sh` script never runs, so the `mkobi_app` database role does not exist. `DatabaseStarter.recreate_test_database()` (starter.py:232) attempts `GRANT CONNECT ON DATABASE bidb_test TO mkobi_app`, which fails because the role does not exist.

**Impact:**
- 173 of 386 tests (44.8%) fail with `role "mkobi_app" does not exist`.
- Every test using `sync_db_session`, `sync_client`, `authenticated_client`, or `test_user` fixtures is broken.
- The test suite gives false confidence — infrastructure tests, integration tests, and API tests are all dead code in Docker.

**Affected modules:**
- `docker/docker-compose.test.yml`
- `src/mkobi/db/starter.py` — `recreate_test_database()`
- All 15 integration/API test files

**Affected symbols:**
- `test-db` service in docker-compose.test.yml
- `starter.py:recreate_test_database`
- 173 test functions across 15 files

**Root cause:**
Missing volume mount `- ./docker/init-scripts:/docker-entrypoint-initdb.d:ro` on `test-db` service.

**Fix target:** Infrastructure/config change (docker-compose.test.yml).

**Recommended fix:**
Add the init-scripts volume mount to the `test-db` service. This is the lowest-risk option and mirrors the production compose configuration.

**Semantic anchor stability:** HIGH — `test-db` service definition in docker-compose is a stable target.

**Validation notes:** Confirmed by live test execution. This is the single highest-impact fix — it immediately unblocks 173 tests.

**Dependency notes:** Fix this FIRST before addressing any other test-related findings. All integration test analysis is blocked until this is resolved.

**Effort:** Trivial (~2 lines in docker-compose.test.yml)

---

### V-003: Pydantic ValidationError returns HTTP 500 instead of 422

| Field | Value |
|---|---|
| **ID** | V-007 |
| **Severity** | MEDIUM |
| **Type** | [BEST-PRACTICE] |
| **Classification** | **MANDATORY** |
| **Original IDs** | R3-MEDIUM-pydantic, R3-app-pydantic |
| **Status** | CONFIRMED — verified in source |

**Description:**
`src/mkobi/app.py` has a `pydantic_validation_exception_handler` that catches `pydantic.ValidationError` and returns HTTP 500. The adjacent `RequestValidationError` handler correctly returns 422. These two handlers should be consistent — both represent client input validation failures.

**Impact:**
- Clients see "Internal Server Error" for validation problems, masking the real issue.
- Masking validation failures as 500s makes debugging harder for API consumers.
- Could trigger false alarms in monitoring/alerting systems.

**Affected modules:**
- `src/mkobi/app.py` — `pydantic_validation_exception_handler`

**Affected symbols:**
- `app.py:pydantic_validation_exception_handler`

**Root cause:**
The handler was likely copied from a generic 500 handler and the status code was never corrected.

**Fix target:** Code change.

**Recommended fix:**
Change status code from 500 to 422. Format errors consistently with the `RequestValidationError` handler.

**Semantic anchor stability:** HIGH — `pydantic_validation_exception_handler` is a named exception handler with a unique signature. Stable insertion point.

**Validation notes:** Source confirmed. The fix is a one-line change (status code). Risk is minimal — this changes error visibility semantics but doesn't affect business logic.

**Dependency notes:** Independent. No prerequisites.

**Effort:** Trivial (1 line)

---

### V-004: Data filters silently ignored in /data/aggregated endpoint

| Field | Value |
|---|---|
| **ID** | V-013 |
| **Severity** | MEDIUM |
| **Type** | [BEST-PRACTICE] |
| **Classification** | **MANDATORY** |
| **Original IDs** | R1-F009, R3-data-filters |
| **Status** | CONFIRMED — filters parsed but discarded |

**Description:**
`src/mkobi/api/routes/data.py` accepts a `filters` query parameter (JSON string), validates it with `json.loads()`, but the parsed result is never passed to `data_service.get_aggregated_data()`. The service call only passes `dashboard_id`, `graph_id`, and `db`. Filters are silently discarded.

**Impact:**
- Clients believing they are filtering data receive unfiltered results. This is a data correctness issue.
- The filters parameter is advertised in the API but has no effect.

**Affected modules:**
- `src/mkobi/api/routes/data.py` — `get_aggregated_data_endpoint()`
- `src/mkobi/services/data_service.py` — `get_aggregated_data()`

**Affected symbols:**
- `data.py:get_aggregated_data_endpoint`
- `data_service.py:get_aggregated_data`

**Root cause:**
The parsed filters variable is created but not forwarded to the service layer. Likely an incomplete implementation.

**Fix target:** Code change.

**Recommended fix:**
Pass the parsed filters to `data_service.get_aggregated_data()` and implement filtering logic in the service layer (either at DB query level or in Polars).

**Semantic anchor stability:** HIGH — `get_aggregated_data_endpoint` is a named route handler. The service call is a stable insertion point.

**Validation notes:** Source confirmed. This is a functional bug — the feature is documented but incomplete.

**Dependency notes:** Depends on defining the filter contract between route and service. Should be implemented atomically.

**Effort:** Medium (route parameter passing + service layer filtering logic)

---

### V-005: Inline access checks violate Clean Architecture

| Field | Value |
|---|---|
| **ID** | V-006 |
| **Severity** | HIGH |
| **Type** | [SPEC-DEVIATION] |
| **Classification** | **MANDATORY** |
| **Original IDs** | R3-HIGH-dashboards |
| **Status** | CONFIRMED — verified in source |

**Description:**
`src/mkobi/api/routes/dashboards.py` lines 661-697 (`get_dashboard_filters_endpoint`) and 872-917 (`get_dashboard_graphs_endpoint`) perform dashboard access checks inline by importing `check_dashboard_access` inside the endpoint function body. The same check is duplicated (10 lines each time). Meanwhile, `deps.py` already provides `require_dashboard_read_access` dependency that performs the same check.

**Impact:**
- Violates Clean Architecture (business logic in route handler instead of DI layer).
- Duplicated access check logic — maintenance risk (change must be made in 3+ places).
- Backend uses local imports instead of module-level imports (unconventional).

**Affected modules:**
- `src/mkobi/api/routes/dashboards.py` — `get_dashboard_filters_endpoint()`, `get_dashboard_graphs_endpoint()`
- `src/mkobi/api/deps.py` — `require_dashboard_read_access` (already exists, should be used)

**Affected symbols:**
- `dashboards.py:get_dashboard_filters_endpoint`
- `dashboards.py:get_dashboard_graphs_endpoint`
- `deps.py:require_dashboard_read_access`

**Root cause:**
These two endpoints were likely created before the `require_dashboard_read_access` dependency was finalized, or the developer was unaware of its existence.

**Fix target:** Code change.

**Recommended fix:**
Replace inline access checks with `Depends(require_dashboard_read_access)` dependency (same pattern used by other endpoints in the same file). Remove inline imports. Move imports to module level.

**Semantic anchor stability:** MEDIUM — The two endpoint functions are named and stable, but `dashboards.py` is 918 lines (over-sized). Consider extracting dashboard sub-endpoints to separate route files during this refactor.

**Validation notes:** Source confirmed. The `require_dashboard_read_access` dependency already exists in deps.py with the correct logic. The fix is a straightforward replacement.

**Dependency notes:** Independent.

**Effort:** Small (~20 lines changed across 2 endpoints)

---

## Part 2 — Advisory Recommended

These findings represent recommended improvements that are not blocking but add long-term value.

---

### V-006: LoginForm bypasses useAuth hook — split auth state

| Field | Value |
|---|---|
| **ID** | V-003 |
| **Severity** | MEDIUM |
| **Type** | [SPEC-DEVIATION] |
| **Classification** | **ADVISORY** |
| **Original IDs** | R1-F001 |

**Description:**
`LoginForm.tsx` calls `setToken(response.access_token)` and `navigate('/dashboards')` directly, bypassing the `useAuth().login()` method. The hook's internal user state is not updated after login.

**Impact:**
- Header component may briefly show no user data after login.
- Components depending on `useAuth().user` have stale null until next re-render triggers `getProfile()`.
- ProtectedRoute works correctly because it reads from `getToken()`, not from hook state.

**Affected modules:**
- `frontend/src/features/auth/ui/LoginForm.tsx`
- `frontend/src/features/auth/model/useAuth.ts`

**Root cause:**
LoginForm manages token storage locally instead of delegating to the auth hook.

**Fix target:** Code change.

**Recommended fix:**
Refactor LoginForm to call `useAuth().login(credentials)` for consistent state management. The hook should handle token storage, profile fetch, and navigation.

**Semantic anchor stability:** HIGH — `LoginForm` component and `useAuth` hook are named exports. Stable targets.

**Dependency notes:** Low risk. The app currently works despite the split state (ProtectedRoute uses token directly).

**Effort:** Small

---

### V-007: Admin logs pagination uses skip/limit instead of page/page_size

| Field | Value |
|---|---|
| **ID** | V-002 |
| **Severity** | MEDIUM |
| **Type** | [SPEC-DEVIATION] |
| **Classification** | **ADVISORY** |
| **Original IDs** | R1-F002, R3-FileRec-processing_logs |

**Description:**
Admin logs endpoint uses `skip/limit` query params instead of `page/page_size` as specified. `ProcessingLogFilter` model also uses `skip/limit`.

**Impact:**
- API interface diverges from spec. Functionally equivalent but different parameter names.
- Minor breaking change for any client already using the old parameter names.

**Affected modules:**
- `src/mkobi/api/routes/processing_logs.py`
- `src/mkobi/models/processing_logs.py` — `ProcessingLogFilter`

**Fix target:** DECISION REQUIRED — Either align code with spec (page/page_size) or update spec to reflect current design (skip/limit). Given that skip/limit is a more standard API pattern, **recommendation: update spec**.

**Semantic anchor stability:** HIGH

**Effort:** Small (if aligning code) or trivial (if updating spec)

---

### V-008: Raw SQL f-strings in db/starter.py

| Field | Value |
|---|---|
| **ID** | V-004 |
| **Severity** | MEDIUM |
| **Type** | [BEST-PRACTICE] |
| **Classification** | **ADVISORY** |
| **Original IDs** | R1-F003 |

**Description:**
Database names are interpolated via f-strings in raw SQL. Mitigated by regex validation (`^[a-zA-Z0-9_]+$`), but f-string SQL is an anti-pattern.

**Impact:**
- Low risk due to validation. Defense-in-depth is adequate.

**Affected modules:**
- `src/mkobi/db/starter.py`

**Root cause:**
Convenience choice. SQLAlchemy DDL constructs are verbose for database creation/drop.

**Fix target:** Code change (low priority).

**Recommended fix:**
Use SQLAlchemy DDL constructs. Keep regex validation as defense-in-depth.

**Semantic anchor stability:** HIGH — `DatabaseStarter` class methods are stable.

**Effort:** Small

---

### V-009: Sidebar.tsx is dead code

| Field | Value |
|---|---|
| **ID** | V-005 |
| **Severity** | LOW |
| **Type** | [BEST-PRACTICE] |
| **Classification** | **ADVISORY** |
| **Original IDs** | R1-F004, R3-7Sidebar |

**Description:**
`Sidebar.tsx` is defined, exported from barrel files, but never rendered in `AppLayout.tsx`. Spec confirms sidebar was replaced with top navigation (Header component).

**Impact:**
- Dead code, slight bundle size increase, potential developer confusion.

**Affected modules:**
- `frontend/src/shared/components/Layout/Sidebar.tsx`
- `frontend/src/shared/components/Layout/index.ts` (barrel export)
- `frontend/src/shared/components/index.ts` (barrel export)

**Fix target:** Code deletion.

**Recommended fix:**
Remove `Sidebar.tsx` and clean up barrel exports.

**Semantic anchor stability:** HIGH — named file and named exports.

**Effort:** Trivial

---

### V-010: CORS wildcard `*` allowed in production with only a warning

| Field | Value |
|---|---|
| **ID** | V-008 |
| **Severity** | MEDIUM |
| **Type** | [BEST-PRACTICE] |
| **Classification** | **ADVISORY** |
| **Original IDs** | R3-MEDIUM-cors, R3-app-cors |

**Description:**
`src/mkobi/app.py` line ~130: when `"*"` is in `cors_origins` in production, only a warning is logged. The application starts with permissive CORS.

**Impact:**
- If misconfigured, the application allows all origins in production without rejecting startup.
- The current behavior is intentional but the warning-only approach is risky.

**Affected modules:**
- `src/mkobi/app.py` — CORS validation

**Fix target:** Code change.

**Recommended fix:**
Change `logger.warning` to `logger.error` and raise `ValueError` for `"*"` in production. Alternatively, keep as warning but add a startup check that requires explicit opt-in for wildcard.

**Semantic anchor stability:** HIGH — CORS validation block is at module level in `create_app`.

**Effort:** Small

---

### V-011: _get_config() mutates config singleton with test fallback

| Field | Value |
|---|---|
| **ID** | V-014 |
| **Severity** | MEDIUM |
| **Type** | [BEST-PRACTICE] |
| **Classification** | **ADVISORY** |
| **Original IDs** | R1-F010, R3-MEDIUM-security |

**Description:**
`_get_config()` in `src/mkobi/core/security.py` mutates the config singleton when `JWT__SECRET_KEY` is not set: `config.jwt.secret_key = "test_fallback_secret_key_do_not_use_in_production"`.

**Impact:**
- Test config singleton mutation. Potential cross-test contamination if tests run in different order.
- Not a production issue (production always has JWT__SECRET_KEY set).

**Affected modules:**
- `src/mkobi/core/security.py` — `_get_config()`

**Fix target:** Code change.

**Recommended fix:**
Use `clear_config_cache()` + `get_config(reload=True)` instead of direct mutation. Or return a separate config instance for tests.

**Semantic anchor stability:** HIGH — `_get_config` is a named private function.

**Effort:** Small

---

### V-012: ProcessingStatus has both SUCCESS and COMPLETED values

| Field | Value |
|---|---|
| **ID** | V-009 |
| **Severity** | MEDIUM |
| **Type** | [BEST-PRACTICE] |
| **Classification** | **ADVISORY** |
| **Original IDs** | R3-MEDIUM-processing_status |

**Description:**
`ProcessingStatus` enum has both `SUCCESS` and `COMPLETED` values. They appear to be used interchangeably.

**Impact:**
- Potential confusion in status tracking. May cause filtering bugs if different parts of code use different status values for the same state.

**Affected modules:**
- `src/mkobi/models/enums.py` — `ProcessingStatus`
- Various services and workers that reference these statuses

**Fix target:** Code change + verification sweep.

**Recommended fix:**
Audit all usages. Consolidate to a single value if semantically identical. If they represent distinct states, document the distinction clearly.

**Semantic anchor stability:** MEDIUM — enum changes require updating all references.

**Effort:** Small to Medium (depends on number of references)

---

### V-013: Registration endpoint missing status filter — overlapping with R1-F008

| Field | Value |
|---|---|
| **ID** | V-012 |
| **Severity** | LOW |
| **Type** | [BEST-PRACTICE] |
| **Classification** | **ADVISORY** |
| **Original IDs** | R1-F008, R3-DOC-admin-registration |

**Description:**
`get_registration_requests_admin_endpoint` doesn't support status filtering despite spec saying "with status filter". Returns ALL requests regardless of status.

**Impact:**
- Admins cannot filter registration requests by status via API.
- Low severity because the frontend can filter client-side for small datasets.

**Affected modules:**
- `src/mkobi/api/routes/admin.py` — `get_registration_requests_admin_endpoint()`

**Fix target:** Code change.

**Semantic anchor stability:** HIGH

**Effort:** Small

---

### V-014: Hardcoded overwrite mode in process_file_endpoint

| Field | Value |
|---|---|
| **ID** | V-015 |
| **Severity** | LOW |
| **Type** | [SPEC-DEVIATION] |
| **Classification** | **ADVISORY** |
| **Original IDs** | R3-LOW-process_file_endpoint |

**Description:**
`process_file_endpoint` hardcodes `mode="overwrite"` when enqueueing, ignoring the original upload mode.

**Impact:**
- Uploads intended as "append" will be processed as "overwrite". Data loss risk.

**Affected modules:**
- `src/mkobi/api/routes/upload.py` — `process_file_endpoint()`

**Fix target:** Code change.

**Semantic anchor stability:** HIGH

**Effort:** Small

---

### V-015: JSONB UPSERT index compatibility

| Field | Value |
|---|---|
| **ID** | V-016 |
| **Severity** | LOW |
| **Type** | [BEST-PRACTICE] |
| **Classification** | **ADVISORY** |
| **Original IDs** | R3-LOW-jsonb_upsert |

**Description:**
`_bulk_upsert` uses `on_conflict_do_update` with `index_elements=[dashboard_id, graph_id, dims]` where `dims` is JSONB. PostgreSQL requires expression indexes for JSONB in unique constraints.

**Impact:**
- May fail at runtime if migration creates a standard B-tree index instead of expression index on `(dims::text)`.

**Affected modules:**
- `src/mkobi/data/storage/manager.py` — `_bulk_upsert()`
- Alembic migrations for aggregated_data table

**Fix target:** Verification required — check if migration already creates expression index.

**Semantic anchor stability:** MEDIUM — migration files change over time.

**Effort:** Small (verification + potential migration fix)

---

### V-016: Inconsistent DI pattern in route handlers

| Field | Value |
|---|---|
| **ID** | V-017 |
| **Severity** | LOW |
| **Type** | [BEST-PRACTICE] |
| **Classification** | **ADVISORY** |
| **Original IDs** | R3-LOW-di_inconsistency |

**Description:**
Some files instantiate `UserRepository()` and other repositories directly inside route handlers instead of using FastAPI `Depends` injection.

**Impact:**
- Inconsistent pattern. Harder to mock in tests. Breaks DI convention.

**Affected modules:**
- Multiple route files (`src/mkobi/api/routes/`)

**Fix target:** Code change (gradual migration).

**Semantic anchor stability:** MEDIUM — spread across multiple files.

**Effort:** Small per file,Medium overall

---

### V-017: dashboard_service.create_dashboard transaction pattern inconsistency

| Field | Value |
|---|---|
| **ID** | V-011 |
| **Severity** | LOW |
| **Type** | [BEST-PRACTICE] |
| **Classification** | **ADVISORY** |
| **Original IDs** | R1-F007 |

**Description:**
`create_dashboard` in `dashboard_service.py` has explicit rollback in exception handler but no explicit commit in success path. Other services let callers manage transactions.

**Impact:**
- Currently safe since only called from route handlers. Could break atomicity if called within a larger transaction.

**Affected modules:**
- `src/mkobi/services/dashboard_service.py`

**Fix target:** Code change — standardize transaction convention.

**Semantic anchor stability:** HIGH

**Effort:** Small

---

### V-018: dashboard_service.get_dashboard type annotation

| Field | Value |
|---|---|
| **ID** | V-010 |
| **Severity** | LOW |
| **Type** | [DOC-UPDATE] |
| **Classification** | **ADVISORY** |
| **Original IDs** | R1-F006 |

**Description:**
`get_dashboard` checks `if user_role == UserRole.ADMIN` but parameter is typed as `str | None`. Works due to `StrEnum` string comparison, but type annotation could be tighter.

**Impact:**
- No runtime issue. Type annotation improvement only.

**Affected modules:**
- `src/mkobi/services/dashboard_service.py`

**Fix target:** Code change.

**Semantic anchor stability:** HIGH

**Effort:** Trivial

---

### V-019: JWT user_id type coercion causes test assertion failures

| Field | Value |
|---|---|
| **ID** | V-019 |
| **Severity** | HIGH (test suite) |
| **Type** | [TEST-REWRITE] |
| **Classification** | **ADVISORY** |
| **Original IDs** | T1-Finding1, T2-F10 |

**Description:**
Multiple tests in `test_security.py` create tokens with `user_id` as int (e.g., `{"user_id": 123}`) and assert `payload["user_id"] == 123` (int). JWT encodes values as JSON, so 123 becomes string "123" on decode. The assertions will FAIL.

**Counter-analysis:** Upon source code verification in `test_security.py`, the `test_valid_refresh_token` test creates the token with int 123 and asserts int 123. Since `create_refresh_token` uses `jwt.encode()` (from python-jose) which serializes to JSON, the decoded value will be `"123"` (string), NOT `123` (int). The assertion `payload["user_id"] == 123` WILL FAIL.

However, `test_auth_service.py` (42 tests, all passing) correctly handles this. The issue is isolated to `test_security.py`.

**Impact:**
- 4 tests in `test_security.py` WILL FAIL when run against real JWT implementation.
- These tests currently pass due to mocked behavior or haven't been run end-to-end.

**Affected modules:**
- `tests/test_security.py` — `test_valid_refresh_token`, 3x `TestIntegration`

**Fix target:** Test code change.

**Recommended fix:**
Change assertions to compare with string values: `payload["user_id"] == "123"`.

**Semantic anchor stability:** HIGH — test function names are stable.

**Dependency notes:** Depends on V-018 (Docker fix) to verify these tests actually pass in integration environment.

**Effort:** Trivial (4 assertion lines)

---

### V-020: AggregatedData chart_type validation test passes for wrong reason

| Field | Value |
|---|---|
| **ID** | V-020 |
| **Severity** | HIGH (test quality) |
| **Type** | [TEST-REWRITE] |
| **Classification** | **ADVISORY** |
| **Original IDs** | T1-Finding2, T2-F9 |

**Description:**
`test_aggregated_data_invalid_chart_type` uses `dashboard_id=1` (int), which causes `ValidationError` BEFORE `chart_type` is checked. The test passes but doesn't actually test chart_type validation.

**Impact:**
- Test gives false confidence. The chart_type validation is never exercised.

**Affected modules:**
- `tests/test_pydantic_models.py` — `test_aggregated_data_invalid_chart_type`

**Fix target:** Test code change.

**Recommended fix:**
Use `dashboard_id=uuid.uuid4()` (valid UUID) so the ValidationError is raised by chart_type, not by dashboard_id type mismatch.

**Effort:** Trivial

---

### V-021: Graph API test coverage critically thin

| Field | Value |
|---|---|
| **ID** | V-021 |
| **Severity** | HIGH (coverage gap) |
| **Type** | [BEST-PRACTICE] |
| **Classification** | **ADVISORY** |
| **Original IDs** | T1-Finding3, T1-F11, T2-F11 |

**Description:**
`test_graphs.py` has only 2 tests: `test_create_graph_admin_required` and `test_get_graphs_for_dashboard`. Missing: create success (as editor), read single graph, update, delete, access control for each role.

**Impact:**
- Graph CRUD endpoints are under-tested. Compare with `test_filters.py` and `test_layouts.py` which have 8-10 tests each.

**Affected modules:**
- `tests/test_graphs.py`

**Fix target:** Add test cases.

**Recommended fix:**
Add 6+ tests covering: create success (editor), create forbidden (viewer), read single, read not found, update, delete, access denied.

**Semantic anchor stability:** HIGH

**Dependency notes:** Blocked by V-018 (Docker fix).

**Effort:** Medium

---

### V-022: Duplicate tests in test_storage_manager.py

| Field | Value |
|---|---|
| **ID** | V-022 |
| **Severity** | MEDIUM |
| **Type** | [TEST-DELETE] |
| **Classification** | **ADVISORY** |
| **Original IDs** | T1-Finding4, T1-F12, T2-F6 |

**Description:**
- `test_clear_graph_data_instance` is identical to `test_clear_graph_data` (both clear from empty table, assert 0).
- `test_clear_dashboard_data_instance` is identical to `test_clear_dashboard_data`.

**Impact:**
- Noise in test output. Wastes CI time. No additional coverage.

**Affected modules:**
- `tests/test_storage_manager.py`

**Fix target:** Delete duplicate test functions.

**Effort:** Trivial

---

### V-023: clean_env fixture backup not populated

| Field | Value |
|---|---|
| **ID** | V-023 |
| **Severity** | MEDIUM |
| **Type** | [TEST-UPDATE] |
| **Classification** | **ADVISORY** |
| **Original IDs** | T1-Finding5 |

**Description:**
`clean_env` fixture initializes `env_backup = {}` but never populates it with pre-yield env values. The cleanup loop checks `if key in env_backup` which is always false, so it always `pop`s rather than restoring.

**Impact:**
- Test env vars are deleted rather than restored. May cause issues if tests depend on pre-existing env vars.

**Affected modules:**
- `tests/test_config.py`

**Fix target:** Test code change.

**Recommended fix:**
Populate `env_backup` before yield: `env_backup = {key: os.environ[key] for key in os.environ if key.startswith(...)}`

**Effort:** Small

---

### V-024: Tests creating large real files for size validation

| Field | Value |
|---|---|
| **ID** | V-024 |
| **Severity** | MEDIUM |
| **Type** | [TEST-REWRITE] |
| **Classification** | **ADVISORY** |
| **Original IDs** | T1-Finding6, T2-F4 |

**Description:**
- `test_upload_too_large` creates 101MB real file (`b"x" * (101 * 1024 * 1024)`) — allocates in RAM + writes to disk.
- `test_process_upload_file_too_large` creates 102MB real file similarly.

**Impact:**
- Slow I/O. Memory-intensive. Wasteful since the file content is never read (mocked validation).

**Affected modules:**
- `tests/test_upload_api.py`
- `tests/test_data_service.py`

**Fix target:** Test code change.

**Recommended fix:**
Use `unittest.mock.patch` to mock `Path.stat().st_size` or the file size validation function instead of writing real files.

**Effort:** Small

---

### V-025: test_deps viewer/admin misleading test name

| Field | Value |
|---|---|
| **ID** | V-025 |
| **Severity** | MEDIUM |
| **Type** | [TEST-REWRITE] |
| **Classification** | **ADVISORY** |
| **Original IDs** | T1-Finding7, T2-F7 |

**Description:**
`test_viewer_cannot_access_admin_endpoint` docstring says "cannot access admin endpoints" but the actual test accesses `/auth/me` (a viewer-level endpoint) and asserts 200 OK. No 403 assertion exists.

**Impact:**
- Misleading test name. Gives false impression that admin endpoint access control is tested.

**Affected modules:**
- `tests/test_deps.py`

**Fix target:** Test code change.

**Recommended fix:**
Rewrite to test actual admin endpoint (e.g., `GET /admin/users`) with viewer token, asserting 403. Or rename test to reflect what it actually tests.

**Effort:** Small

---

### V-026: test_auth double flush() in cleanup

| Field | Value |
|---|---|
| **ID** | V-026 |
| **Severity** | MEDIUM |
| **Type** | [TEST-UPDATE] |
| **Classification** | **ADVISORY** |
| **Original IDs** | T1-Finding8, T2-F3 |

**Description:**
`test_register_request_success` has `await async_db_session.flush()` called twice consecutively (copy-paste bug).

**Impact:**
- No functional issue (second flush is a no-op). Code smell only.

**Affected modules:**
- `tests/test_auth.py`

**Fix target:** Test code cleanup.

**Effort:** Trivial

---

### V-027: Repository CRUD coverage gaps

| Field | Value |
|---|---|
| **ID** | V-027 |
| **Severity** | HIGH (coverage gap) |
| **Type** | [BEST-PRACTICE] |
| **Classification** | **ADVISORY** |
| **Original IDs** | T1-F16, T1-F17 |

**Description:**
`test_repositories.py` only tests `create` for Graph, Filter, Layout repos. Missing: `get`, `update`, `delete`, `get_by_name`, `get_by_dashboard`. AccessRepository only tests `grant_access` + `get_user_dashboards`. Missing: `check_access`, `revoke_access`, `update_permission`.

**Impact:**
- Repository layer is under-tested. The data layer is the foundation of the application.

**Affected modules:**
- `tests/test_repositories.py`

**Fix target:** Add test cases.

**Dependency notes:** Blocked by V-018 (Docker fix).

**Effort:** Medium

---

### V-028: Data processing (Polars) zero test coverage

| Field | Value |
|---|---|
| **ID** | V-028 |
| **Severity** | CRITICAL (coverage gap) |
| **Type** | [BEST-PRACTICE] |
| **Classification** | **ADVISORY** |
| **Original IDs** | T1-F19, T2-F13 |

**Description:**
The entire `src/mkobi/data/` package (CSVLoader, DataValidator, transformations.py, DataPipeline, JSONB normalization — 1,658+ lines) has zero test coverage. This is the core data processing pipeline.

**Impact:**
- Highest-risk area without tests. Any bug in data processing silently corrupts dashboard data.
- YoY calculations, share calculations, custom metrics formula parser, JSONB normalization — none are unit tested.

**Affected modules:**
- `src/mkobi/data/loaders/loader.py`
- `src/mkobi/data/loaders/validator.py`
- `src/mkobi/data/processing/transformations.py`
- `src/mkobi/data/processing/registry.py`

**Fix target:** Add comprehensive unit tests (30+ tests).

**Dependency notes:**
- Independent of V-018 (these are pure unit tests with no DB dependency).
- Should be prioritized after V-018 fix due to criticality.

**Effort:** Large (30+ tests, estimated 2-3 days of work)

---

## Part 3 — Doc Updates Needed

---

### D-001: Admin logs pagination parameter naming

| Field | Value |
|---|---|
| **Type** | [DOC-UPDATE] |
| **Source finding** | V-002 (R1-F002) |
| **File** | `docs/SPEC.md` |
| **Decision** | Update spec to reflect `skip/limit` instead of `page/page_size` |

**Description:**
The spec describes `page/page_size` pagination for admin logs, but the implementation uses `skip/limit`. Since skip/limit is a more standard pattern and the team has already committed to it, update the spec rather than the code.

---

### D-002: SPEC.md upload endpoint version history

| Field | Value |
|---|---|
| **Type** | [DOC-UPDATE] |
| **Source finding** | R3-MEDIUM-doc-upload |
| **File** | `docs/SPEC.md` |

**Description:**
Spec describes `POST /upload/:dashboard_id/process?task_id=` — upload is implemented as `UploadModal` per spec v2.4. Minor doc inconsistency in endpoint version history.

---

### D-003: Temp password security note in SPEC.md

| Field | Value |
|---|---|
| **Type** | [DOC-UPDATE] |
| **Source finding** | R3-LOW-doc-admin-temp-password |
| **File** | `docs/SPEC.md` |

**Description:**
Registration approval returns `temp_password` in plaintext JSON response. Spec requires `secrets.token_urlsafe(16)` returned to admin but has no documentation about secure transmission. Add security note in SPEC.md.

---

## Rejected Findings

These findings were evaluated and rejected for the reasons stated.

| ID | Original ID | Title | Rejection Reason |
|---|---|---|---|
| REJ-001 | R3-MEDIUM-sync_polars | CSV loader uses sync Polars with `asyncio.to_thread` — could impact concurrent operations | **REJECTED — Low ROI.** The `asyncio.to_thread` pattern is a well-documented approach for CPU-bound sync libraries in async apps. The thread pool concern is theoretical for a single-instance BI dashboard. Replacing with a dedicated thread pool adds complexity without measurable benefit at current scale. Revisit if concurrent processing becomes a bottleneck. |
| REJ-002 | R3-LOW-data_filters_in_memory | Data filters applied in Python/Polars rather than at DB level | **REJECTED — Intentional design tradeoff.** Loading data into Polars and applying filters is architecturally intentional — it allows complex filtering that would be difficult to express in SQL JSONB operators. The dataset sizes (up to 100MB files, aggregated to much smaller) make in-memory filtering acceptable. Revisit if performance data shows this is a bottleneck. |
| REJ-003 | R3-MEDIUM-auth-change-password-response | `change_password` returns `dict[str, Any]` instead of Pydantic model | **REJECTED — Low priority inconsistency.** While inconsistent with other endpoints, this is a low-traffic endpoint used once per password change. The response format is documented and functional. Fix during next auth module refactor rather than as a standalone task. |
| REJ-004 | R3-LOW-grant-idempotency | `grant_dashboard_access_endpoint` returns 200 without idempotency check | **REJECTED — No evidence of harm.** The database unique constraint on `(dashboard_id, user_id, permission)` would prevent duplicates at the DB level. A 409 check is cosmetic rather than functionally necessary. The current behavior (200 on repeat grant) is idempotent in effect. |

---

## Dependency & Rollout Safety Analysis

### Rollout Order

```
Phase 1: Infrastructure (unblocks everything else)
  ├── V-018: Fix test Docker (mkobi_app role)          [CRITICAL, blocks 173 tests]
  └── V-028: Add data processing unit tests            [Independent, no DB needed]

Phase 2: Mandatory production fixes
  ├── V-003: Pydantic 500→422 (1 line, low risk)       [Independent]
  ├── V-001: Temp file cleanup (production reliability) [Independent]
  ├── V-005: Inline access checks refactor              [Depends on understanding existing deps.py patterns]
  └── V-004: Data filters pass-through (correctness)    [Depends on filter contract definition]

Phase 3: Advisory production fixes
  ├── V-006: LoginForm auth state refactor              [Independent]
  ├── V-009: Remove Sidebar dead code                   [Independent]
  ├── V-008: Raw SQL f-strings → DDL                    [Independent]
  ├── V-010: CORS wildcard handling                     [Independent]
  └── V-011: _get_config singleton mutation             [Independent]

Phase 4: Test suite cleanup (after V-018 fix)
  ├── V-022: Delete duplicate storage_manager tests    [Independent]
  ├── V-019: Fix JWT user_id assertions                 [Independent]
  ├── V-020: Fix AggregatedData test                    [Independent]
  ├── V-023: Fix clean_env fixture                      [Independent]
  ├── V-024: Mock large file creation                   [Independent]
  ├── V-025: Rewrite test_deps viewer/admin             [Independent]
  └── V-026: Remove double flush                       [Independent]

Phase 5: Test coverage expansion
  ├── V-021: Graph API tests                           [After V-018]
  └── V-027: Repository CRUD tests                     [After V-018]

Phase 6: Doc updates
  ├── D-001: Update spec for skip/limit                 [After decision on V-002]
  ├── D-002: Update spec upload version history         [Independent]
  └── D-003: Add temp password security note            [Independent]
```

### Parallel Execution Safety

**Safe to parallelize:**
- Phase 2 items are independent (different files, different concerns).
- Phase 4 items are independent test file changes.
- Phase 6 doc updates are independent.

**Must be sequential:**
- V-018 must complete before any Phase 4/5 work (Docker test fix unblocks integration test verification).
- V-004 (data filters) should be done after defining the filter contract to avoid rework.

### Rollback Feasibility

All recommended changes are:
- **Atomic:** Each fix targets a single concern.
- **Reversible:** Each can be reverted independently.
- **Low blast radius:** Changes are scoped to specific files/functions.

**Exception:** V-005 (inline access checks) touches security logic. Ensure full test coverage before merging.

### Circular Dependencies Detected

None. The dependency graph is a clean DAG.

---

## Semantic Targeting Stability Analysis

### High Stability (safe for automated task generation)

| Finding | Anchor Type | Stability |
|---|---|---|
| V-001 | Named function (`_upload_file_endpoint`) + variable (`temp_file_path`) | HIGH |
| V-003 | Named exception handler (`pydantic_validation_exception_handler`) | HIGH |
| V-009 | Named file (`Sidebar.tsx`) + barrel exports | HIGH |
| V-018 | Service definition in docker-compose | HIGH |
| V-022 | Named test functions | HIGH |
| V-019-V-021 | Named test functions | HIGH |

### Medium Stability (manual review recommended before execution)

| Finding | Anchor Type | Risk |
|---|---|---|
| V-005 | Functions in oversized file (918 lines) | File refactoring may shift line numbers |
| V-004 | Route handler + service method | Need to define filter contract first |
| V-012 | `ProcessingStatus` enum | Enum change cascades to all references |
| V-013 | Named endpoint function | Low-medium, route handler is stable |

### Low Stability (avoid line-based targeting)

None identified. All recommendations use symbol/function-based targeting.

---

## Execution Applicability Assessment

### Pre-conditions for execution

1. **Docker test fix (V-018) must be verified** before trusting any integration test results.
2. **Data processing tests (V-028)** should be written against the current data package — no preconditions.
3. **Filter contract (V-004)** requires a design decision on filter schema before implementation.

### Risk of findings becoming stale

- **Low risk:** All findings target named symbols (functions, classes, files) rather than line numbers.
- **Medium risk:** V-005 (dashboards.py) is 918 lines. If the file is split during refactoring, the anchor context changes but the fixing logic remains correct.

### Architecture drift detection

No drift detected. All findings are current as of the source code verification performed during this validation.

---

## Summary Statistics

| Category | Count |
|----------|-------|
| **Total unique validated findings** | 31 (28 original + 3 doc updates) |
| **Mandatory fixes** | 5 |
| **Advisory recommendations** | 18 (production) + 7 (test) + 3 (doc) |
| **Rejected findings** | 4 |
| **Merged from raw findings** | ~59 → 31 |
| **Estimated total effort** | ~3-4 days (V-028 data processing tests is the largest item) |

---

*End of Validated Audit Findings Document*
*Generated: 2026-05-26*
*Validator: OWL (Kilo Agent)*
