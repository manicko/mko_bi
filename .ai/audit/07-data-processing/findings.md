# Phase 07 Audit Findings — Data Processing Pipeline

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### DP-001: Transactional Processing in Background Workers

| Field | Value |
|-------|-------|
| **ID** | DP-001 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/workers/data_worker.py, src/mkobi/data/storage/manager.py |
| **Classification** | advisory |

**Description:** The background processing in `_process_csv_file_async` uses conditional transaction management. When `db_session` is provided (test mode), transactions are not explicitly managed. In production mode, `session.begin()` is used but the storage operations happen inside this context manager. The update of processing log status via `_update_processing_log_status` happens outside the storage transaction boundary in production mode, creating a potential window where processing could succeed but status updates could fail.

**Evidence:** 
- `src/mkobi/workers/data_worker.py:218-240` — `_store_aggregates` uses `session.begin()` for transactions when no `db_session` is provided
- `src/mkobi/workers/data_worker.py:226` — Storage happens in transaction, but status updates at lines 228-235 and 252-259 happen outside this transaction
- `src/mkobi/data/storage/manager.py:350-353` — Production mode uses `async with session.begin()` correctly

**Recommendation:** Consider wrapping the entire processing workflow (status update to SUCCESS + storage + status update completion) in a single transaction to ensure atomicity across status changes and data persistence. Alternatively, use savepoints or ensure the status update failures are handled gracefully without leaving partial state.

---

### DP-002: Temporary File Cleanup Silently Ignores Exceptions

| Field | Value |
|-------|-------|
| **ID** | DP-002 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/workers/data_worker.py |
| **Classification** | mandatory |

**Description:** The temporary file cleanup on processing failure at lines 262-266 silently swallows exceptions without logging. While the cleanup uses `asyncio.to_thread` correctly, any failure to delete the file (permissions, file locked, etc.) is not logged, making debugging difficult. Additionally, the cleanup in `upload.py` at line 193 uses synchronous `temp_file_path.unlink(missing_ok=True)` in an async context without proper error handling.

**Evidence:** 
- `src/mkobi/workers/data_worker.py:262-266` — Exception is silently caught and ignored: `except Exception: pass`
- `src/mkobi/api/routes/upload.py:193` — Uses synchronous `unlink()` without try/except
- `src/mkobi/workers/data_worker.py:238-240` — Success path correctly uses `await asyncio.to_thread(file_path.unlink)` with logging

**Recommendation:** Add logging for cleanup failures in `data_worker.py` to aid debugging. Wrap the cleanup in `upload.py` with proper error handling and logging. Consider using `asyncio.to_thread` for consistency in async contexts.

---

### DP-003: Upload Endpoint Missing Processing Config Parameter

| Field | Value |
|-------|-------|
| **ID** | DP-003 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/api/routes/upload.py |
| **Classification** | advisory |

**Description:** The `upload_file_endpoint` function signature does not include a `processing_config` parameter, which means users cannot specify transformations, filters, or aggregations at upload time. The spec mentions "Processing rules configurable" and the `ProcessingConfig` model exists to support this, but the endpoint doesn't accept it. Users must use the `/process` endpoint to trigger processing with config.

**Evidence:** 
- `src/mkobi/api/routes/upload.py:51` — Endpoint signature lacks `processing_config` parameter
- `src/mkobi/models/data.py:111-149` — `ProcessingConfig` model is defined with filters, groupby, aggregations, yoy_config, share_config, custom_metrics
- The `process_upload_with_session` function in `file_processing.py` doesn't accept processing config either

**Recommendation:** Add optional `processing_config` parameter to the upload endpoint to allow users to specify transformation rules, filters, and aggregation configurations at upload time. Pass this configuration through to the background processing job.

---

### DP-004: Task Queue Implementation Not Production-Ready

| Field | Value |
|-------|-------|
| **ID** | DP-004 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/core/task_queue.py |
| **Classification** | advisory |

**Description:** The `TaskQueue` implementation is an in-memory queue using `asyncio.Queue` which is not suitable for production. According to the spec ("Background task queue — In-memory TaskQueue (MVP) with a documented migration path to Redis/RQ"), this is intentional for MVP, but the current implementation doesn't properly integrate with the processing_log database for persistence. Task statuses are stored in memory (`self._statuses`) and will be lost on process restart.

**Evidence:** 
- `src/mkobi/core/task_queue.py:18-30` — Uses in-memory dict for status tracking
- `src/mkobi/core/task_queue.py:77-83` — Processing status only updated in memory, not persisted to database during queue processing
- The `process_csv_background` function in `data_worker.py` handles its own status updates via `_update_processing_log_status`

**Recommendation:** The current separation is actually better than having TaskQueue track statuses — the worker handles persistence. However, for production readiness, implement the documented Redis/RQ migration. The in-memory queue is documented as MVP with a migration path.

---

### DP-005: YAML Config Processing Rules Not Integrated

| Field | Value |
|-------|-------|
| **ID** | DP-005 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/data/processing/transformations.py |
| **Classification** | advisory |

**Description:** The `apply_transformations` function validates the config using `TransformationConfig` Pydantic model but only uses the `filters`, `computed_fields`, `rename`, and `dtype` fields. The `ProcessingConfig` model has additional fields (`yoy_config`, `share_config`, `custom_metrics`) that aren't validated here. The main processing flow in `data_worker.py` handles these separately in `calculate_aggregations`.

**Evidence:** 
- `src/mkobi/data/processing/transformations.py:82-89` — Only validates `filters`, `computed_fields`, `rename`, `dtype` via `TransformationConfig`
- `src/mkobi/models/data.py:111-149` — `ProcessingConfig` includes `groupby`, `aggregations`, `yoy_config`, `share_config`, `custom_metrics`
- `src/mkobi/workers/data_worker.py:187-216` — These additional fields are handled via separate code paths

**Recommendation:** Either consolidate config validation into `ProcessingConfig` or ensure `TransformationConfig` properly documents its scope. Consider having a unified config model that validates all processing parameters.

---

### DP-006: Formula Parser Limitations Not Documented in API

| Field | Value |
|-------|-------|
| **ID** | DP-006 |
| **Severity** | MEDIUM |
| **Type** | DOC-UPDATE |
| **Affected Modules** | src/mkobi/data/processing/formula_parser.py |
| **Classification** | advisory |

**Description:** The `_parse_formula` function has known limitations (no parentheses, no operator precedence, specific column name format) that are documented in the function docstring but should be communicated to API users. The `CustomMetricConfig` model allows users to specify formulas but doesn't validate or communicate these constraints to API consumers.

**Evidence:** 
- `src/mkobi/data/processing/formula_parser.py:45-54` — Known limitations documented in docstring
- `src/mkobi/models/transformation_configs.py:106-120` — `CustomMetricConfig` accepts any `expr` string without validation hints

**Recommendation:** Add validation hints or examples to `CustomMetricConfig` docstring, or implement formula validation at the model level to reject invalid formulas early.

---

### DP-007: Processing Log Started_At Timestamp Correctly Set

| Field | Value |
|-------|-------|
| **ID** | DP-007 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/db/repositories/processing_log_repo.py |
| **Classification** | advisory |

**Description:** Upon review, the `started_at` timestamp is correctly set in `create_log` when the log is created with STARTED status. This is semantically correct - the timestamp represents when the upload process was initiated. The original concern was unfounded.

**Evidence:** 
- `src/mkobi/db/repositories/processing_log_repo.py:56` — `started_at` is set to `datetime.now(UTC)` during log creation
- The implementation correctly tracks when the upload was initiated

**Recommendation:** This is correct behavior. No change needed.

---

### DP-008: Stale File Cleanup Uses Modification Time Instead of Processing Log

| Field | Value |
|-------|-------|
| **ID** | DP-008 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/services/file_cleanup.py |
| **Classification** | advisory |

**Description:** The `cleanup_stale_temp_files` function uses file modification time to determine staleness, but doesn't correlate with processing logs. This could lead to premature deletion of files that are still being processed, or retention of files that are orphaned.

**Evidence:** 
- `src/mkobi/services/file_cleanup.py:78-89` — Uses `file_path.stat().st_mtime` to determine age
- `src/mkobi/services/file_cleanup.py:39` — No correlation with processing_log table for validation

**Recommendation:** Either maintain current approach with a larger safety margin, or implement cleanup that queries the processing_log table to find files associated with FAILED or COMPLETED tasks.

---

### DP-009: Processing Log Status Transitions Incomplete

| Field | Value |
|-------|-------|
| **ID** | DP-009 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/models/enums.py |
| **Classification** | advisory |

**Description:** The `ProcessingStatus` enum includes `COMPLETED` as a status value but the workflow only uses `STARTED → UPLOADED → PROCESSING → SUCCESS/FAILED`. The `COMPLETED` status appears unused in the codebase, creating confusion about intended state machine.

**Evidence:** 
- `src/mkobi/models/enums.py:58-66` — Five statuses defined: STARTED, UPLOADED, PROCESSING, SUCCESS, FAILED, COMPLETED
- `src/mkobi/workers/data_worker.py:174-176, 229-232, 253-257` — Only STARTED, PROCESSING, SUCCESS, FAILED are used

**Recommendation:** Either remove the unused `COMPLETED` enum value or document its intended use case. The current implementation correctly uses SUCCESS/FAILED as terminal states.

---

### DP-010: Memory Management for Large Files Uses Lazy Loading Threshold

| Field | Value |
|-------|-------|
| **ID** | DP-010 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/data/loaders/loader.py, src/mkobi/config.py |
| **Classification** | advisory |

**Description:** The CSV loader implements lazy loading for files larger than `lazy_threshold_mb` (default 10MB) which helps bound memory usage. However, the lazy loading implementation calls `.collect()` immediately after `scan_csv`, negating the memory benefits of lazy evaluation during the actual read. The threshold only affects how the file is scanned, not the final memory footprint.

**Evidence:** 
- `src/mkobi/data/loaders/loader.py:134-147` — Lazy threshold checked, but `scan_csv().collect()` still loads entire result into memory
- `src/mkobi/config.py:165` — Default threshold is 10.0 MB

**Recommendation:** For truly large file support, consider streaming the data in chunks or using Polars' streaming capabilities. The current implementation provides early validation but doesn't reduce peak memory for large files.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 4 |
| LOW | 3 |

## Mandatory Fixes

- DP-002: Temporary file cleanup on processing failure silently ignores exceptions without logging, making debugging difficult when cleanup fails.

## Advisory Recommendations

- DP-001: Consider wrapping the entire processing workflow in a single transaction for better atomicity.
- DP-003: Add optional `processing_config` parameter to the upload endpoint.
- DP-004: The in-memory task queue is documented as MVP with migration path to Redis/RQ.
- DP-005: Consolidate config validation between ProcessingConfig and TransformationConfig.
- DP-006: Document formula parser limitations in CustomMetricConfig model.
- DP-008: Consider correlating file cleanup with processing log status.
- DP-009: Remove or document the unused COMPLETED processing status.
- DP-010: Lazy loading threshold doesn't reduce peak memory - consider chunked streaming.

---

## Template Field Reference

### Mandatory Fields Per Finding

| Field | Type | Values/Format |
|-------|------|---------------|
| `id` | string | Unique identifier within phase (e.g., `DP-001`, `DP-002`) |
| `title` | string | Human-readable one-line summary |
| `type` | enum | `SPEC-DEVIATION`, `BEST-PRACTICE`, `DOC-UPDATE`, `RUNTIME-ERROR` |
| `severity` | enum | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `description` | string | Detailed problem description with context |
| `evidence` | string | File paths, line references, log excerpts, code snippets |
| `affected_modules` | list | Affected module paths |
| `recommendation` | string | Concrete fix direction |
| `classification` | enum | `mandatory` or `advisory` |

### Classification Guide

- **mandatory**: Security vulnerabilities, data loss risks, correctness issues
- **advisory**: Code quality improvements, refactoring suggestions, best practice enhancements