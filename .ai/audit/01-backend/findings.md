---
name: 01-backend-findings
description: Backend audit findings for mkobi BI Dashboard
agent: audit-executor
alwaysApply: false
---

# Phase 01 Audit Findings — Backend

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** yes

---

## Findings

### BE-001: Type Error - UUID | None Passed to Repository Delete Method

| Field | Value |
|-------|-------|
| **ID** | BE-001 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/services/processing_log_service.py |
| **Classification** | mandatory |

**Description:** The `ProcessingLogRead.dashboard_id` field is typed as `UUID | None` (line 76 in processing_logs.py), but the `IProcessingLogRepository.delete()` method expects a non-nullable `UUID` parameter (line 397-398 in repository_interfaces.py). This creates a type mismatch at line 135 in processing_log_service.py where `log.dashboard_id` (which could be None) is passed to `delete()`. When `dashboard_id` is None, the delete operation would fail or behave unexpectedly.

**Evidence:** 
- `src/mkobi/services/processing_log_service.py:135` - `await self.log_repo.delete(log.dashboard_id, db)`
- `src/mkobi/models/processing_logs.py:76` - `dashboard_id: UUID | None = None`
- `src/mkobi/interfaces/repository_interfaces.py:397-398` - `async def delete(self, dashboard_id: UUID, db: AsyncSession) -> bool:`

**Recommendation:** Either change `ProcessingLogRead.dashboard_id` to non-nullable `UUID`, or add a null check before calling delete. The spec indicates `dashboard_id` should always exist for processing logs, so making it non-nullable is the correct fix. Add `assert log.dashboard_id is not None` or raise an appropriate error when it's None.

---

### BE-002: Type Error - UUID | None Passed to check_dashboard_access

| Field | Value |
|-------|-------|
| **ID** | BE-002 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/services/data_service.py |
| **Classification** | mandatory |

**Description:** In `data_service.py`, the `log.dashboard_id` field (which is `UUID | None`) is passed to `check_dashboard_access()` which requires a non-nullable `UUID`. This occurs at lines 325 and 353. When `log.dashboard_id` is None, access checks would fail or raise errors.

**Evidence:**
- `src/mkobi/services/data_service.py:325` - `dashboard_id=log.dashboard_id,` (status line)
- `src/mkobi/services/data_service.py:353` - `dashboard_id=log.dashboard_id,` (result line)
- `src/mkobi/core/permissions.py:126-127` - `async def check_dashboard_access(user_id: UUID, dashboard_id: UUID, ...`

**Recommendation:** Add null checks before access verification. If `dashboard_id` is None, the processing log is invalid and should be handled appropriately (log error, raise exception, or return error response).

---

### BE-003: Type Error - UUID | None Passed to Graph Repository

| Field | Value |
|-------|-------|
| **ID** | BE-003 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/services/data_service.py |
| **Classification** | mandatory |

**Description:** At line 364 in `data_service.py`, `log.dashboard_id` (typed as `UUID | None`) is passed to `IGraphRepository.get_by_dashboard_id()` which requires a non-nullable `UUID` parameter (line 279-280 in repository_interfaces.py).

**Evidence:**
- `src/mkobi/services/data_service.py:364` - `graphs = await self.graph_repo.get_by_dashboard_id(log.dashboard_id, db)`
- `src/mkobi/interfaces/repository_interfaces.py:279-280` - `async def get_by_dashboard_id(self, dashboard_id: UUID, db: AsyncSession) -> list[Any]:`

**Recommendation:** Add null check before repository call. If dashboard_id is None, handle it as a validation error.

---

### BE-004: Incompatible Type Assignment in ProcessingConfig Validation

| Field | Value |
|-------|-------|
| **ID** | BE-004 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/workers/data_worker.py |
| **Classification** | advisory |

**Description:** At line 128-129 in `data_worker.py`, the code iterates over `config.metrics` (typed as `list[dict[str, str]] | None`) and uses `metric.items()` treating each item as a dict. However, the type annotation suggests the iteration variable is being treated as if it could be a `CustomMetricConfig` model instance, causing a type mismatch.

**Evidence:**
- `src/mkobi/workers/data_worker.py:127-129` - `for metric in config.metrics: if not all(str(k) and str(v) for k, v in metric.items()):`
- `src/mkobi/models/data.py:127` - `metrics: list[dict[str, str]] | None = None`
- `src/mkobi/models/transformation_configs.py:106-110` - `CustomMetricConfig` has `name: str` and `expr: str` fields

**Recommendation:** The iteration and validation logic is correct for `dict[str, str]`, but the mypy error may stem from how the type is inferred. Consider adding an explicit type annotation or cast to clarify the intent. The current behavior is correct at runtime but the type checker sees an ambiguity.

---

### BE-005: Redundant Cast to int in processing_log_service.py

| Field | Value |
|-------|-------|
| **ID** | BE-005 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/services/processing_log_service.py |
| **Classification** | advisory |

**Description:** Lines 242 and 248 in `processing_log_service.py` contain redundant `cast(int, count)` statements. The `count` variable is already an `int` returned from the repository, making the cast unnecessary.

**Evidence:**
- `src/mkobi/services/processing_log_service.py:241-242` - `count = await self.log_repo.delete_old_logs(cutoff, db); return cast(int, count)`
- `src/mkobi/services/processing_log_service.py:247-248` - `count = await self.log_repo.delete_old_logs(cutoff, session); return cast(int, count)`

**Recommendation:** Remove the redundant `cast(int, count)` statements. These casts add noise without benefit.

---

### BE-006: ErrorCode Not Explicitly Exported from exceptions Module

| Field | Value |
|-------|-------|
| **ID** | BE-006 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/utils/exceptions.py, src/mkobi/workers/data_worker.py |
| **Classification** | advisory |

**Description:** Line 33 in `data_worker.py` imports `ErrorCode` from `mkobi.utils.exceptions`, but `ErrorCode` is not in the module's `__all__` export list. `ErrorCode` is defined in `src/mkobi/models/enums.py`, not in `exceptions.py`. The import works because `exceptions.py` imports `ErrorCode` for its own use (line 27), making it available for re-export. However, this creates a confusing import structure and mypy reports it as "does not explicitly export".

**Evidence:**
- `src/mkobi/workers/data_worker.py:33` - `from mkobi.utils.exceptions import AppException, ErrorCode`
- `src/mkobi/utils/exceptions.py:27` - `from mkobi.models.enums import ErrorCode` (imported but not re-exported in `__all__`)

**Recommendation:** Either add `ErrorCode` to `exceptions.py`'s `__all__` list, or import directly from `mkobi.models.enums` in `data_worker.py`. The latter is cleaner as it makes the import source explicit.

---

### BE-007: Temp Files Not Cleaned Up After Tests

| Field | Value |
|-------|-------|
| **ID** | BE-007 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | tests/conftest.py, src/mkobi/services/file_cleanup.py |
| **Classification** | mandatory |

**Description:** After running all tests, 42+ temp files remain in `data/tmp_uploads/` directory. The SPEC (line 58-62) mandates: "Files deleted from temporary storage after processing". The `setup_temp_dir_fixture` in `conftest.py` cleans up temp files for `test_file_cleanup.py` tests, but other test modules do not clean up their temp files. This violates the spec requirement and could cause disk exhaustion in production if cleanup fails.

**Evidence:**
- Pytest output shows 42+ remaining files in `data/tmp_uploads/` after tests complete
- Key files left: `upload_1e6ee4f2-905d-4a14-ab4b-6ebbe18db441_cleanup_test.csv`, `dc531305-a3c2-453d-bc0d-2766c872efec.csv`
- SPEC.md:02-05: "Temp file deletion after processing is mandatory"

**Recommendation:** Add a session-scoped autouse fixture in `conftest.py` that calls `cleanup_stale_temp_files()` after all tests complete, or ensure each test that creates temp files properly cleans them up. The temp file cleanup should happen in a `pytest_sessionfinish` hook or an autouse fixture.

### BE-008: Returning Any from Function Declared to Return List

| Field | Value |
|-------|-------|
| **ID** | BE-008 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/services/processing_log_service.py |
| **Classification** | advisory |

**Description:** Lines 78, 85, and 217 in `processing_log_service.py` return `Any` type when the function is declared to return `list[ProcessingLogRead]`. The repository methods return `Any` because the repository interfaces use `Any` as return types without explicit type annotations. This violates strict typing requirements.

**Evidence:**
- `src/mkobi/services/processing_log_service.py:78` - `return await self.log_repo.get_by_dashboard(dashboard_id, db)` returns `Any`
- `src/mkobi/services/processing_log_service.py:85` - `return await self.log_repo.get_filtered(filters, db)` returns `Any`
- `src/mkobi/services/processing_log_service.py:217` - `return await self.log_repo.get_filtered(filters, db)` returns `Any`
- `src/mkobi/interfaces/repository_interfaces.py:359-365` - `get_by_dashboard` returns `list[ProcessingLogRead]` but repository implementations return `Any`

**Recommendation:** Add explicit `cast(list[ProcessingLogRead], ...)` to the return statements, or improve repository type annotations to return the correct types.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 1 |
| LOW | 4 |

## Mandatory Fixes

- **BE-001:** Type error in processing_log_service.py - UUID | None passed to delete() method
- **BE-002:** Type error in data_service.py - UUID | None passed to check_dashboard_access()
- **BE-003:** Type error in data_service.py - UUID | None passed to graph repository
- **BE-007:** Temp files not cleaned up after test runs - violates SPEC requirement

## Advisory Recommendations

- **BE-004:** Type inference clarity in data_worker.py metrics validation
- **BE-005:** Remove redundant cast() statements in processing_log_service.py
- **BE-006:** Fix ErrorCode import to use explicit source
- **BE-008:** Explicit return type annotations needed for repository methods (no-any-return)

## Doc Updates Needed

None

---