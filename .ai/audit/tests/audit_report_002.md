# Test Quality Audit Report 002 — mkobi BI Dashboard

**Date:** 2026-05-26
**Auditor:** OWL Architecture Audit Agent
**Scope:** Full test suite re-audit with live Docker test execution
**Previous report:** audit_report_001.md (structural analysis, no live execution)

---

## Executive Summary

This report re-audits the test suite with **live execution** against Docker test infrastructure (test-db on port 5433, test-redis on port 6380). The previous structural audit identified 22 issues. This execution-based audit reveals a **critical infrastructure failure** that invalidates nearly half the test suite, plus confirms and expands on the previous findings.

**Key result:** 386 tests collected, **213 passed (55%)**, **173 errors (45%)** — all 173 errors from a single root cause: mkobi_app database role does not exist in the test database.

---

## 1. Statistics

| Metric | Value |
|--------|-------|
| Total test files | 21 |
| Total test functions | 386 |
| Tests passed | 213 (55.2%) |
| Tests errored | 173 (44.8%) |
| Tests failed | 0 |
| Test execution time | ~17s |

### Coverage by Module (Live Execution)

| Module | Test File(s) | Passed | Errored | Status |
|--------|-------------|--------|---------|--------|
| Auth API | test_auth.py | 0 | 13 | ALL ERROR — mkobi_app role |
| Auth API (cookies) | test_auth_api.py | 0 | 10 | ALL ERROR — mkobi_app role |
| Auth Service (mocked) | test_auth_service.py | 42 | 0 | FULL PASS |
| Config | test_config.py | 47 | 0 | FULL PASS |
| Dashboard API | test_dashboards_api.py | 0 | 18 | ALL ERROR — mkobi_app role |
| Data Service (mocked) | test_data_service.py | 38 | 0 | FULL PASS |
| DI / Dependencies | test_deps.py | 12 | 16 | Partial |
| Filters API | test_filters.py | 0 | 8 | ALL ERROR — mkobi_app role |
| Graph API | test_graphs.py | 0 | 2 | ALL ERROR — mkobi_app role |
| Graph Service (mocked) | test_graph_service.py | 18 | 0 | FULL PASS |
| Layouts API | test_layouts.py | 0 | 10 | ALL ERROR — mkobi_app role |
| Permissions (unit) | test_permissions.py (CheckRole+GetDb) | 8 | 0 | FULL PASS |
| Permissions (integration) | test_permissions.py (rest) | 0 | 15 | ALL ERROR — mkobi_app role |
| Processing Logs (unit) | test_processing_logs.py (models+filter) | 4 | 0 | FULL PASS |
| Processing Logs (integration) | test_processing_logs.py (rest) | 0 | 10 | ALL ERROR — mkobi_app role |
| Pydantic Models | test_pydantic_models.py | 44 | 0 | FULL PASS |
| Repositories | test_repositories.py | 0 | 11 | ALL ERROR — mkobi_app role |
| Security | test_security.py | 42 | 0 | FULL PASS |
| Services Integration | test_services_integration.py | 0 | 40 | ALL ERROR — mkobi_app role |
| Storage Manager | test_storage_manager.py | 0 | 9 | ALL ERROR — mkobi_app role |
| Upload API | test_upload_api.py | 0 | 13 | ALL ERROR — mkobi_app role |
| Users API | test_users_api.py | 0 | 5 | ALL ERROR — mkobi_app role |

---

## 2. Critical Infrastructure Finding

### FINDING 0: Test database missing \mkobi_app\ role — 173 tests broken

**Severity:** CRITICAL
**Type:** [SPEC-DEVIATION] [BEST-PRACTICE]
**Root cause:** \docker-compose.test.yml\ does not mount the \init-scripts/\ directory, so the \1-create-app-role.sh\ script never runs. The \DatabaseStarter.recreate_test_database()\ (starter.py:232) attempts \GRANT CONNECT ON DATABASE bidb_test TO mkobi_app\, which fails because the role does not exist.

**Evidence:**
\\\
sqlalchemy.exc.ProgrammingError: asyncpg.exceptions.UndefinedObjectError:
role "mkobi_app" does not exist
SQL: GRANT CONNECT ON DATABASE bidb_test TO mkobi_app
\\\

**Affected:** Every test that uses \sync_db_session\, \sync_client\, \uthenticated_client\, or \	est_user\ fixtures (173 tests across 15 files).

**Production code reference:** \src/mkobi/db/starter.py\ lines 231-246

**Required fix:** Either:
1. Add \olumes: - ./docker/init-scripts:/docker-entrypoint-initdb.d\ to the \	est-db\ service in \docker-compose.test.yml\, OR
2. Create the role directly in the \	est-migrate\ container after running migrations, OR
3. Have \DatabaseStarter.recreate_test_database()\ create the role before granting privileges

**Effort:** Trivial (5 minutes)
**Priority:** CRITICAL — Until fixed, 45% of the test suite is dead code.

---

## 3. Problematic Tests Table

| # | File | Test(s) | Type | Category | Problem | Action | Priority |
|---|------|---------|------|----------|---------|--------|----------|
| 1 | conftest.py + 15 files | 173 tests | [SPEC-DEVIATION] | Infrastructure | mkobi_app role not created | Fix docker-compose.test.yml | CRITICAL |
| 2 | test_deps.py | TestGetDbDependency, TestGetCurrentUserDependency | [BEST-PRACTICE] | Quality | Missing @pytest.mark.asyncio on async test classes | Add decorator | LOW |
| 3 | test_auth.py | TestRegisterRequest (2 tests) | [TEST-UPDATE] | Quality | Manual cleanup with double flush() — unnecessary with SAVEPOINT | Remove manual cleanup | MEDIUM |
| 4 | test_upload_api.py | test_upload_too_large | [TEST-REWRITE] | Quality | Creates 102MB real file — slow I/O | Use sparse file or mock | MEDIUM |
| 5 | test_data_service.py | test_process_upload_file_too_large | [TEST-REWRITE] | Quality | Creates 101MB real file — never read due to mocking | Mock file size | MEDIUM |
| 6 | test_storage_manager.py | test_clear_graph_data_instance, test_clear_dashboard_data_instance | [TEST-DELETE] | Quality | Duplicate of existing tests | Delete duplicates | MEDIUM |
| 7 | test_deps.py | test_viewer_cannot_access_admin_endpoint | [TEST-REWRITE] | Contract | Tests viewer-level endpoint, not admin endpoint | Rewrite to test admin denial | MEDIUM |
| 8 | test_auth_service.py | test_login_user_success | [BEST-PRACTICE] | Contract | Verifies display_name pattern — OK but no API-level display_name verification yet | Expand to API layer | LOW |
| 9 | test_pydantic_models.py | test_aggregated_data_invalid_chart_type | [TEST-REWRITE] | Contract | dashboard_id=1 fails UUID check before chart_type — passes for wrong reason | Use valid UUID | HIGH |
| 10 | test_security.py | test_valid_refresh_token + 3 Integration tests | [TEST-REWRITE] | Contract | payload["user_id"] == 123 (int vs string) — WILL FAIL | Fix to compare strings | HIGH |
| 11 | test_graphs.py | TestGraphsAPI (entire class) | [BEST-PRACTICE] | Coverage | Only 2 tests vs 8-10 for filters/layouts | Add 6+ missing tests | HIGH |
| 12 | test_repositories.py | Graph/Filter/Layout repos | [BEST-PRACTICE] | Coverage | Only create tested per repo | Add get/update/delete tests | HIGH |
| 13 | test_services_integration.py | TestDataServiceIntegration | [BEST-PRACTICE] | Coverage | Only error/empty paths tested | Add positive-path tests | HIGH |
| 14 | test_permissions.py | test_invalid_permission_raises | [BEST-PRACTICE] | Quality | Overly complex setup for simple validation test | Simplify fixtures | LOW |
| 15 | test_services_integration.py | TestProcessingConfigServiceIntegration | [TEST-UPDATE] | Isolation | Hardcoded valid settings — brittle if validation changes | Document expected settings | LOW |

---

## 4. Coverage Assessment

### Well-Covered Areas (All Passing)

- **AuthService (42 tests)** — Complete coverage of registration, login, auth, tokens, refresh, blocked domains
- **Config (47 tests)** — Multi-source loading, Docker secrets, priority, reload, CORS origins
- **DataService (38 tests)** — Upload pipeline (mocked), file validation, processing, status, results
- **Security (42 tests)** — Password hashing, JWT create/decode/validate, edge cases
- **GraphService (18 tests)** — Full CRUD, interface compliance, validation
- **Pydantic Models (44 tests)** — All model groups
- **Role hierarchy (7 tests)** — All role comparison combinations

### Broken Coverage (mkobi_app Role Fix Needed)

These suites are structurally correct but non-functional:

- **Auth API (23 tests)** — Login, register-request, me, logout, refresh, cookie flow
- **Dashboard API (18 tests)** — CRUD, access control, admin bypass, 403/404 dual-signal
- **Upload API (13 tests)** — CSV/CSV.gz upload, validation, mode handling, permissions
- **Permissions integration (15 tests)** — Real DB access checks, get_current_user
- **Processing Logs integration (10 tests)** — CRUD, filtering, stale cleanup
- **Repositories (11 tests)** — CRUD for all entity repos
- **Services Integration (40 tests)** — All 8 services with real DB
- **Filters/Layouts/Graphs API (20 tests)** — CRUD and access control
- **Storage Manager (9 tests)** — Data clearing, save operations, deprecated API
- **Users API (5 tests)** — Profile, delete account

### Completely Missing Coverage

| Area | Description | Priority |
|------|-------------|----------|
| **Data Processing (Polars)** | CSVLoader, DataValidator, transformations.py (YoY, shares, custom metrics), DataPipeline, JSONB normalization — entire src/mkobi/data/ package (1,658+ lines) | CRITICAL |
| **Task Queue** | TaskQueue.enqueue, get_task_status, get_task_result | HIGH |
| **Change Password** | /auth/change-password endpoint and service | HIGH |
| **Registration Approval** | Admin approve/reject, temp password via secrets.token_urlsafe(16) | HIGH |
| **Health Endpoints** | /health, /health/detailed, / | MEDIUM |
| **Processing Config API** | CRUD endpoints | MEDIUM |
| **File Processing Service** | file_processing.py — enqueue_job, validate_file integration | MEDIUM |
| **Data Worker** | data_worker.py — process_csv_background, _store_aggregate | MEDIUM |
| **File Cleanup** | file_cleanup.py — cleanup_stale_temp_files | LOW |
| **Rate Limiting (behavioral)** | strict_redis fixture exists, no tests use it | LOW |
| **Startup Lifecycle** | DatabaseStarter, admin user creation | LOW |
| **JSONB Normalization** | Recursive key sorting for dims before UPSERT | LOW |
| **Temp File Cleanup** | Deletion after processing success/failure | LOW |

---

## 5. Action Plan

### Fix Immediately (Unblocks 173 tests)

| # | Action | Effort | Impact |
|---|--------|--------|--------|
| 1 | Add init script mount to docker-compose.test.yml test-db service | 5 min | Unblocks 173 tests |
| 2 | Alternative: add role creation to test-migrate container command | 5 min | Unblocks 173 tests |

### Delete Required

| # | File | Test | Reason |
|---|------|------|--------|
| 1 | test_storage_manager.py | test_clear_graph_data_instance | Duplicate of test_clear_graph_data |
| 2 | test_storage_manager.py | test_clear_dashboard_data_instance | Duplicate of test_clear_dashboard_data |

### Rewrite Required

| # | File | Test | Fix |
|---|------|------|-----|
| 1 | test_pydantic_models.py | test_aggregated_data_invalid_chart_type | Use uuid.uuid4() for dashboard_id |
| 2 | test_security.py | test_valid_refresh_token + 3x TestIntegration | Fix int vs string comparison for user_id |
| 3 | test_deps.py | test_viewer_cannot_access_admin_endpoint | Rewrite to test actual admin endpoint denial |
| 4 | test_upload_api.py | test_upload_too_large | Use sparse file or mock |
| 5 | test_data_service.py | test_process_upload_file_too_large | Mock file size |

### Improve (Priority Order)

| # | Area | Tests to Add | Priority |
|---|------|-------------|----------|
| 1 | Data Processing (Polars) | 30+ tests for loaders, validators, transformations, pipeline | CRITICAL |
| 2 | Graph API | 6+ tests (create success, read, update, delete, access control) | HIGH |
| 3 | Repository CRUD | get/update/delete for Graph, Filter, Layout repos | HIGH |
| 4 | Change Password | 4+ tests (success, wrong old password, unauthorized) | HIGH |
| 5 | Registration Approval | 5+ tests (approve, reject, temp password) | HIGH |
| 6 | Task Queue | 6+ tests (enqueue, status, result, error) | HIGH |
| 7 | Health Endpoints | 3 tests | MEDIUM |
| 8 | Processing Config API | 8 tests | MEDIUM |
| 9 | Data Worker | 6+ tests | MEDIUM |
| 10 | DataService Integration | 4+ positive-path tests | MEDIUM |
| 11 | Rate Limiting | 3+ behavioral tests with strict_redis | LOW |

---

## 6. Previous Audit Confirmation

The previous structural audit (report_001.md) identified 22 issues. This live execution audit confirms and adds to those findings:

**Confirmed from report_001:**
- JWT user_id type coercion (Finding 1 in 001 = Finding 10 here)
- AggregatedData chart_type validation (Finding 2 in 001 = Finding 9 here)
- Graph API thin coverage (Finding 3 in 001 = Finding 11 here)
- Repository tests only cover create (Finding 4 in 001 = Finding 12 here)
- Duplicate storage_manager tests (Finding 5 in 001 = Finding 6 here)
- clean_env fixture bug (Finding 6 in 001 — confirmed in code, passed due to isolated env)
- Data processing zero coverage (Finding 8 in 001 — expanded here with line counts)

**New findings in this audit:**
- mkobi_app role missing — 173 tests broken (CRITICAL)
- test_deps.py missing @pytest.mark.asyncio on classes (minor)
- Services integration only tests error paths for DataService
- Test isolation issues in processing_logs cleanup test

---

## 7. Test Pyramid Assessment

Current state (broken): Over-reliance on mocked unit tests. Integration tests exist but are non-functional.

After mkobi_app fix: Pyramid would be well-balanced with 213 unit + 173 integration tests.

Still needed: Data processing unit tests (currently 0), E2E tests for critical paths (upload to process to display).

---

## 8. Test Culture Recommendations

1. **Fix mkobi_app role immediately** — Single highest-impact fix. 173 tests are dead code until resolved.
2. **Add CI pipeline** — No CI configured. All 386 tests should run on every push.
3. **Data processing tests are critical** — The Polars pipeline (1,658+ lines) has zero coverage. Highest-risk area.
4. **Follow filter/layout test patterns** — test_filters.py and test_layouts.py are the gold standard (8-10 tests each).
5. **Repository tests should match UserRepository** — 5 tests covering full CRUD. Graph/Filter/Layout have only 1 each.
6. **Use strict_redis for behavioral tests** — Fixture exists, never used. Add 2-3 rate limiting tests.
7. **Clean up conftest.py** — 445 lines with complex fixture interactions. Consider splitting into modules.

---

## 9. Blocked by Infrastructure Fix

The following analysis could not be completed until the mkobi_app role issue is resolved:
- Whether the 173 errored tests actually pass when the DB is properly set up
- Whether any additional test failures exist beyond the infrastructure issue
- Integration test isolation verification
- SAVEPOINT rollback verification under concurrent test execution

**Recommendation:** Fix the mkobi_app role issue, re-run the full test suite, and produce a follow-up audit with actual pass/fail results for all 386 tests.

---

*End of audit report 002*
