# Test Quality Audit Report — mkobi BI Dashboard

**Date:** 2026-05-26
**Auditor:** OWL Architecture Audit Agent
**Scope:** Full test suite — 21 test files, ~7,082 lines of test code
**Production code base:** 94 Python source files in src/mkobi/

---

## 1. Statistics

| Metric | Value |
|--------|-------|
| Total test files | 21 |
| Total test lines | ~7,082 |
| Total test functions | ~190+ |
| Tests with @pytest.mark.asyncio | All async unit test classes use it correctly |
| Files with stale .pyc cache (no source) | 6 (	est_yoy_calculation, 	est_share_calculation, 	est_data_processing, 	est_data_loader, 	est_models, 	est_graphs) |

### Recommended Actions Summary

| Action Type | Count |
|-------------|-------|
| [TEST-DELETE] — harmfully wrong or worthless | 3 |
| [TEST-REWRITE] — right intent, wrong implementation | 5 |
| [TEST-UPDATE] — needs minor fixes to match current code | 4 |
| [BEST-PRACTICE] — missing coverage or quality improvement | 9 |
| [DOC-UPDATE] — test reveals spec/docs are wrong | 1 |

### Coverage by Module

| Module | Test File(s) | Coverage Quality |
|--------|-------------|-----------------|
| Auth API | 	est_auth.py, 	est_auth_api.py | Good |
| Auth Service | 	est_auth_service.py | Good |
| Dashboard API | 	est_dashboards_api.py | Good |
| Dashboard Service | 	est_services_integration.py | Good |
| Graph API | 	est_graphs.py | WEAK — only 2 tests |
| Graph Service | 	est_graph_service.py | Good |
| Filter API | 	est_filters.py | Good |
| Filter Service | 	est_services_integration.py | Good |
| Layout API | 	est_layouts.py | Good |
| Layout Service | 	est_services_integration.py | Good |
| Upload API | 	est_upload_api.py | Good |
| Data Service | 	est_data_service.py | Good |
| Data Processing (Polars) | MISSING — no tests | Critical gap |
| Security | 	est_security.py | Good |
| Permissions | 	est_permissions.py | Good |
| Dependencies / DI | 	est_deps.py | Good |
| Repositories | 	est_repositories.py | Partial |
| Processing Logs | 	est_processing_logs.py | Good |
| Pydantic Models | 	est_pydantic_models.py | Good |
| Config | 	est_config.py | Good |
| Users API | 	est_users_api.py | Adequate |
| Storage Manager | 	est_storage_manager.py | Adequate |
| Integration (all services) | 	est_services_integration.py | Good |
| Change Password | MISSING | No tests |
| Registration Approval Flow | MISSING | No tests |
| Health Endpoints | MISSING | No tests |
| Rate Limiting | PARTIAL | Fixture only, no behavioral tests |
| Task Queue | MISSING | No tests |
| JSONB Normalization | MISSING | No tests |
| Temp File Cleanup | MISSING | No tests |

---

## 2. Problematic Tests Table

| # | File | Test | Type | Category | Problem | Action | Priority |
|---|------|------|------|----------|---------|--------|----------|
| 1 | 	est_auth_service.py | 	est_login_user_success | [TEST-UPDATE] | Contract | Mock created_at = datetime.now() (naive dt) but production code constructs UserRead from user data — fragile mock data | Review mock construction | LOW |
| 2 | 	est_auth_service.py | 	est_create_access_token | [TEST-UPDATE] | Quality | Only checks token format, duplicates assertions in TestDecodeToken | Consider merging or removing | LOW |
| 3 | 	est_storage_manager.py | 	est_clear_graph_data_instance | [TEST-DELETE] | Quality | Identical duplicate of 	est_clear_graph_data | Delete duplicate | MEDIUM |
| 4 | 	est_storage_manager.py | 	est_clear_dashboard_data_instance | [TEST-DELETE] | Quality | Identical duplicate of 	est_clear_dashboard_data | Delete duplicate | MEDIUM |
| 5 | 	est_config.py | clean_env fixture | [TEST-UPDATE] | Architecture | Captures env_backup AFTER yield (post-test state), not pre-test state. Restoration is effectively no-op. | Fix backup to capture pre-test state before yield | MEDIUM |
| 6 | 	est_config.py | 	est_aggregated_data_invalid_chart_type | [TEST-REWRITE] | Contract | dashboard_id=1 (int) causes ValidationError BEFORE chart_type is checked. Test passes for wrong reason | Fix to use valid UUID | HIGH |
| 7 | 	est_config.py | TestSettingsFromYaml | [DOC-UPDATE] | Contract | Tests hardcoded to pp.yaml values — tightly coupled | Document coupling | LOW |
| 8 | 	est_upload_api.py | 	est_upload_mode_invalid | [TEST-UPDATE] | Contract | Doesn't grant explicit dashboard access — passes only because admin bypass grants implicit access | Grant explicit access | MEDIUM |
| 9 | 	est_upload_api.py | 	est_upload_too_large | [TEST-REWRITE] | Quality | Creates 101MB real file synchronously — slow and I/O heavy. Access grant after file creation — wrong order | Use sparse file; reorder operations | MEDIUM |
| 10 | 	est_deps.py | 	est_viewer_cannot_access_admin_endpoint | [TEST-REWRITE] | Contract | Name says "admin endpoint" but test only checks viewer CAN access /auth/me (viewer-level). Never tests admin endpoint denial | Rewrite to test actual admin endpoint | MEDIUM |
| 11 | 	est_graphs.py | TestGraphsAPI overall | [BEST-PRACTICE] | Coverage | Only 2 tests (create forbidden + list). Missing: create success, read, update, delete, access control | Add 6+ missing tests | HIGH |
| 12 | 	est_auth.py | 	est_register_request_duplicate cleanup | [TEST-DELETE] | Quality | Double lush() on lines 85-86 is copy-paste bug; cleanup may not work correctly | Fix double flush | MEDIUM |
| 13 | 	est_data_service.py | 	est_process_upload_file_too_large | [TEST-REWRITE] | Quality | Creates 102MB real file — 102 iterations of 1MB writes. Slow and wasteful | Use mock for file size | MEDIUM |
| 14 | 	est_data_service.py | 	est_process_upload_success | [TEST-UPDATE] | Quality | Patches check_dashboard_access but doesn't verify call arguments | Add argument assertion | LOW |
| 15 | 	est_permissions.py | 	est_get_db_closes_session | [TEST-UPDATE] | Quality | Patches close method manually — tests generator protocol, not FastAPI integration | Clarify test intent | LOW |
| 16 | 	est_repositories.py | Graph/Filter/Layout repos | [BEST-PRACTICE] | Coverage | Only create tested. Missing: get, update, delete, get_by_name, get_by_dashboard | Add full CRUD tests | HIGH |
| 17 | 	est_repositories.py | AccessRepository | [BEST-PRACTICE] | Coverage | Only grant_access + get_user_dashboards. Missing: check_access, revoke_access, update_permission | Add missing method tests | HIGH |
| 18 | 	est_processing_logs.py | 	est_cleanup_stale_processing_logs | [TEST-UPDATE] | Contract | Uses raw SQL to bypass ORM. Commit in SAVEPOINT may affect isolation. | Add pre-test cleanup of stale data | MEDIUM |
| 19 | 	est_services_integration.py | DataService integration | [BEST-PRACTICE] | Coverage | Only tests error cases. Missing: successful process_upload, trigger_processing, get_processing_result | Add positive-path tests | HIGH |
| 20 | 	est_pydantic_models.py | 	est_aggregated_data_invalid_chart_type | [TEST-REWRITE] | Contract | dashboard_id=1 fails UUID validation before chart_type is checked. Test passes for wrong reason. | Use valid UUID | HIGH |
| 21 | 	est_security.py | 	est_valid_refresh_token | [TEST-REWRITE] | Contract | payload["user_id"] == 123 compares str "123" to int 123 — WILL FAIL | Fix assertion to compare with string | HIGH |
| 22 | 	est_security.py | 3x TestIntegration user_id assertions | [TEST-REWRITE] | Contract | decoded["user_id"] == N compares string to int — WILL FAIL for N=42, 999, 1 | Fix assertions to compare with string | HIGH |

---

## 3. Coverage Assessment

### Well-Covered Areas

- **Authentication API** — login, register-request, refresh, logout, cookie flow
- **Authorization / RBAC** — role hierarchy, dashboard access, admin bypass
- **Security** — password hashing, JWT creation/decode, refresh token validation
- **Configuration** — multi-source loading, priority, Docker secrets, reload
- **Upload API** — comprehensive edge cases (wrong extension, wrong MIME, too large, empty file, encoding)
- **Processing Logs** — CRUD, filtering, stale cleanup
- **Pydantic Models** — validation across all model groups
- **DI / Dependencies** — all factory functions
- **Service Integration** — all 8 services tested with real DB

### Completely Missing Coverage

- **Data Processing (Polars)** — CSVLoader, DataValidator, transformations, aggregations, custom metrics formula parser, DataPipeline, JSONB normalization
- **Task Queue** — TaskQueue.enqueue, get_task_status, get_task_result
- **Change Password** — /auth/change-password endpoint and service
- **Registration Approval** — admin approve/reject endpoints
- **Health Endpoints** — /health, /health/detailed
- **Admin API** — user management, registration request management, log viewing
- **Processing Config API** — CRUD endpoints
- **Behavioral Rate Limiting** — strict_redis fixture exists but no tests use it
- **Temp File Cleanup** — no tests verifying deletion after processing
- **Startup Lifecycle** — DatabaseStarter, admin user creation, stale file cleanup
- **JSONB UPSERT** — StorageManager.save_aggregates with real data

---

## 4. Key Findings

### Finding 1: JWT user_id type coercion causes 4 test failures

**Severity:** HIGH
**Type:** [TEST-REWRITE]
**Affected:** 	est_security.py

Multiple tests create tokens with user_id as int and assert decoded["user_id"] == <int>. JWT encodes all values as JSON, so 123 becomes string "123" on decode. These assertions WILL FAIL.

`python
# test_security.py line 264
data = {"user_id": 123}  # int
token = create_refresh_token(data)
payload = validate_refresh_token(token)
assert payload["user_id"] == 123  # FAILS: "123" != 123
`

**Fix:** Change assertions to compare with string values ("123", "42", "999", "1").

---

### Finding 2: AggregatedData chart_type validation test passes for wrong reason

**Severity:** HIGH
**Type:** [TEST-REWRITE]
**Affected:** 	est_pydantic_models.py line 294-301

`python
with pytest.raises(ValidationError):
    AggregatedData(
        dashboard_id=1,  # int, not UUID — fails HERE first
        chart_type="invalid",  # never reached
        data=[],
    )
`

dashboard_id=1 is not a valid UUID, so ValidationError is raised before chart_type is validated. The test passes but doesn't test chart_type validation.

**Fix:** Use dashboard_id=uuid.uuid4() or a valid UUID string.

---

### Finding 3: Graph API coverage critically thin

**Severity:** HIGH
**Type:** [BEST-PRACTICE]

Only 2 tests for 5 endpoints. Compare with 	est_filters.py and 	est_layouts.py which have 8-10 tests each.

Missing from 	est_graphs.py:
- Create graph as admin (success)
- Read graph by ID
- Update graph (admin success + viewer forbidden)
- Delete graph (admin success + viewer forbidden)
- Access control (viewer with/without dashboard access)

---

### Finding 4: Repository tests only cover create

**Severity:** HIGH
**Type:** [BEST-PRACTICE]

TestUserRepository has 5 tests (create, get, get_by_email, update, delete) but Graph, Filter, and Layout repos each have only 1 test (create).

---

### Finding 5: Duplicate tests in test_storage_manager.py

**Severity:** MEDIUM
**Type:** [TEST-DELETE]

Two pairs of identical tests:
- 	est_clear_graph_data and 	est_clear_graph_data_instance
- 	est_clear_dashboard_data and 	est_clear_dashboard_data_instance

Each pair tests the same method with the same assertion, just with different instantiation.

---

### Finding 6: clean_env fixture doesn't restore pre-test state

**Severity:** MEDIUM
**Type:** [TEST-UPDATE]

The clean_env fixture in 	est_config.py captures env_backup AFTER yield (post-test), making restoration a no-op. Tests may leak environment state on failure.

---

### Finding 7: 	est_viewer_cannot_access_admin_endpoint doesn't test admin endpoints

**Severity:** MEDIUM
**Type:** [TEST-REWRITE]

The test verifies a viewer can access /auth/me (viewer-level endpoint) but never attempts to access an actual admin endpoint (like POST /dashboards/).

---

### Finding 8: Data processing pipeline has zero test coverage

**Severity:** HIGH
**Type:** [BEST-PRACTICE]

The entire src/mkobi/data/ package (1,658 lines) is untested:
- CSVLoader (494 lines)
- DataValidator (337 lines)
- 	ransformations.py (606 lines) — YoY, shares, custom metrics, formula parser
- egistry.py (221 lines)

Stale .pyc files suggest tests existed before but were deleted.

---

## 5. Action Plan

### Delete Required

| # | File | Test | Reason |
|---|------|------|--------|
| 1 | 	est_storage_manager.py | 	est_clear_graph_data_instance (line 160) | Duplicate |
| 2 | 	est_storage_manager.py | 	est_clear_dashboard_data_instance (line 170) | Duplicate |
| 3 | 	est_auth.py | 	est_register_request_duplicate double flush | Copy-paste bug in cleanup |

### Rewrite Required

| # | File | Test | Fix |
|---|------|------|-----|
| 1 | 	est_security.py | 	est_valid_refresh_token + 3x TestIntegration | Fix int vs string comparison |
| 2 | 	est_pydantic_models.py | 	est_aggregated_data_invalid_chart_type | Use valid UUID for dashboard_id |
| 3 | 	est_deps.py | 	est_viewer_cannot_access_admin_endpoint | Test actual admin endpoint denial |
| 4 | 	est_upload_api.py | 	est_upload_too_large | Use sparse file; reorder operations |
| 5 | 	est_data_service.py | 	est_process_upload_file_too_large | Use mock for file size |

### Improve (Add Missing Coverage)

| # | Area | Priority | Description |
|---|------|----------|-------------|
| 1 | Data Processing | HIGH | Tests for CSVLoader, DataValidator, transformations, DataPipeline |
| 2 | Graph API | HIGH | Add 6+ CRUD and access control tests |
| 3 | Repository CRUD | HIGH | Add get/update/delete for Graph, Filter, Layout repos |
| 4 | Access Repository | HIGH | Add check_access, revoke_access, update_permission tests |
| 5 | Change Password | HIGH | Add endpoint and service tests |
| 6 | Registration Approval | HIGH | Add admin approve/reject tests |
| 7 | Health Endpoints | MEDIUM | Add /health and /health/detailed tests |
| 8 | Admin API | MEDIUM | Add user management, log viewing tests |
| 9 | Processing Config API | MEDIUM | Add API-level CRUD tests |
| 10 | Task Queue | MEDIUM | Add enqueue/status/result tests |
| 11 | Rate Limiting | MEDIUM | Add behavioral tests with strict_redis |
| 12 | DataService Integration | MEDIUM | Add positive-path integration tests |

### Doc Updates

| # | Finding | Action |
|---|---------|--------|
| 1 | 	est_config.py YAML tests coupled to pp.yaml | Document that tests must be updated when YAML changes |

---

## 6. Blocked Refactorings

### 6.1 — check_dashboard_access refactoring blocked by thin repository tests

The access check logic in core/permissions.py and dashboard_service.py has admin bypass. Before refactoring, add tests for check_access, evoke_access, and update_permission in the access repository.

### 6.2 — Data processing refactoring blocked by zero test coverage

The entire src/mkobi/data/ package (1,658 lines) has no tests. Any refactoring is high-risk without a test safety net.

### 6.3 — 403/404 dual-signal not comprehensively tested

The SPEC claims the system distinguishes 404 from 403. Only 2 tests verify this behavior (both in dashboard API). Other endpoints (graphs, filters, layouts, data) have no dual-signal tests.

---

## 7. Test Culture Recommendations

1. **Follow existing patterns** — 	est_filters.py and 	est_layouts.py are excellent examples. Apply the same pattern to 	est_graphs.py.
2. **Repository tests should cover all CRUD** — TestUserRepository is the gold standard (5 tests). Apply to all repos.
3. **Integration tests need positive paths** — 	est_services_integration.py only covers error cases for DataService.
4. **Delete stale .pyc files** — 6 stale cache files remain from deleted test files.
5. **Use strict_redis for rate limiting tests** — Infrastructure exists, no tests use it.
6. **Test data processing formulas** — The formula parser (_parse_formula) is complex and needs dedicated tests.
7. **Add conftest.py documentation** — The file is 445 lines with complex fixture interactions. Add a fixture hierarchy comment.

---

## 8. Test Pyramid Assessment

The pyramid is well-shaped for backend tests. Main gaps: no E2E tests (acceptable), data processing layer has zero coverage (critical), and API layer has uneven coverage (graphs weak, admin missing).

---

*End of audit report*
