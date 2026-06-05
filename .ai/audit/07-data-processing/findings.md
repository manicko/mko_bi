# Phase 07 Audit Findings — Data Processing Pipeline

**Executor:** audit-executor  
**Template:** `.ai/audit/templates/audit-findings.md`  
**Status:** complete  
**Validated:** no

---

## Findings

### DP-001: Missing transaction wrapper in `_process_csv_file_async` test mode

| Field | Value |
|-------|-------|
| **ID** | DP-001 |
| **Severity** | CRITICAL |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/workers/data_worker.py` |
| **Classification** | mandatory |

**Description:** When processing runs in test mode (`db_session` is provided), the `_store_aggregates` function performs database operations without an explicit transaction wrapper for the UPSERT operation. The production mode uses `async with session.begin()` (line 459), but the test mode does not. This means that if an error occurs during database operations in test mode, the transaction may not be properly rolled back, potentially leaving partial data in an inconsistent state. Additionally, the `_update_processing_log_status` calls within `_process_csv_file_async` for test mode do not operate within the same transaction context as the storage operations, creating a risk of partial commits.

**Evidence:**
- `src/mkobi/workers/data_worker.py:394-460` - Test mode branch has no `async with session.begin()` wrapper around database operations
- `src/mkobi/workers/data_worker.py:79-87` - Test mode `_update_processing_log_status` commits but without transaction alignment with storage
- `src/mkobi/workers/data_worker.py:458-459` - Production mode correctly uses `async with session.begin()` for atomicity

**Recommendation:** Wrap all database operations in test mode with an explicit transaction context using `async with db_session.begin()` to ensure atomicity. The caller should NOT be responsible for transaction management - the _store_aggregates function should handle its own transaction boundaries or require the caller to provide a transaction context.

---

### DP-002: Incomplete transaction boundary in `_store_aggregates` causes partial commit risk

| Field | Value |
|-------|-------|
| **ID** | DP-002 |
| **Severity** | CRITICAL |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/workers/data_worker.py` |
| **Classification** | mandatory |

**Description:** The `_store_aggregates` function in test mode (lines 394-460) performs database write operations without being wrapped in an explicit transaction. If an exception occurs after some but not all operations complete (e.g., after graphs are fetched but before aggregates are saved, or during filter value saving), the changes will be partially committed. This violates the atomicity requirement for the data processing pipeline. The StorageManager's `save_aggregates` method expects the caller to manage transactions (as noted in the docstring), but `_store_aggregates` does not consistently do this.

**Evidence:**
- `src/mkobi/workers/data_worker.py:394-460` - No transaction wrapper in test mode
- `src/mkobi/data/storage/manager.py:8-11` - Docstring states "Does not manage transactions (commit/rollback is external)"
- The function calls `manager.save_aggregates()` which performs DELETE and INSERT operations that must be atomic

**Recommendation:** Ensure that `_store_aggregates` wraps all database operations in a transaction context. Either: (1) use `async with db_session.begin()` at the start of the test mode branch, or (2) restructure to always rely on the caller for transaction management and document this clearly.

---

### DP-003: Potential race condition in task state transition from PROCESSING to FAILED

| Field | Value |
|-------|-------|
| **ID** | DP-003 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/workers/data_worker.py` |
| **Classification** | mandatory |

**Description:** The `_update_processing_log_status` function in test mode (lines 73-77) only commits when status is COMPLETED or FAILED, but it does not wrap the commit in a try/except that rolls back on failure. If an exception occurs during the status update from PROCESSING to FAILED, the error will be logged and rollback attempted, but there's a risk that the session state could be left in an inconsistent state. Additionally, the status transition from PROCESSING to FAILED doesn't check if the status was already updated by the stale cleanup job, potentially causing incorrect status reporting.

**Evidence:**
- `src/mkobi/workers/data_worker.py:73-77` - Selective commit based on status without full transaction handling
- `src/mkobi/workers/data_worker.py:319-345` - Exception handler calls `_update_processing_log_status` for FAILED status

**Recommendation:** Ensure all status updates use consistent transaction handling. Consider using a single `async with db.begin()` block for the entire `_process_csv_file_async` function to guarantee atomic state transitions.

---

### DP-004: Empty DataFrame handling does not prevent processing continuation

| Field | Value |
|-------|-------|
| **ID** | DP-004 |
| **Severity** | MEDIUM |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/data/loaders/validator.py`, `src/mkobi/services/file_processing.py` |
| **Classification** | mandatory |

**Description:** While `DataValidator.validate()` (line 55-65 in validator.py) correctly detects empty DataFrames and returns `is_valid=False`, this validation is NOT called in the main processing pipeline (`_process_csv_file_async`). The validation happens in `CSVLoader.load_csv()` only when `self.config.required_columns` is empty (line 159-160), which doesn't catch the case of an empty file with valid columns. An empty CSV file with headers would pass through validation and result in a "completed" status with zero data points, which is misleading to users.

**Evidence:**
- `src/mkobi/data/loaders/validator.py:55-65` - Empty DataFrame check exists but is never called in pipeline
- `src/mkobi/workers/data_worker.py:203-208` - CSV loading happens without validation check
- `src/mkobi/services/file_processing.py:196-217` - File validation checks file size and MIME but not DataFrame content validity

**Recommendation:** Add a validation step after CSV loading in `_process_csv_file_async` to check if the DataFrame is empty and raise an appropriate error. Alternatively, call `DataValidator.validate()` in the processing pipeline to ensure proper validation.

---

### DP-005: cleanup_stale_processing_logs test mode lacks commit for status updates

| Field | Value |
|-------|-------|
| **ID** | DP-005 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/workers/data_worker.py` |
| **Classification** | mandatory |

**Description:** The `cleanup_stale_processing_logs` function in test mode (lines 114-128) performs the UPDATE statement to mark stale entries as FAILED but never commits the transaction. The function returns the count of affected rows, but in test mode without an explicit commit, the status changes will not be persisted to the database. This is inconsistent with the production mode which properly uses `async with db.begin()` for transaction handling.

**Evidence:**
- `src/mkobi/workers/data_worker.py:114-128` - Test mode executes UPDATE but has no commit statement
- `src/mkobi/workers/data_worker.py:129-145` - Production mode correctly commits via `async with db.begin()`
- The function returns `count` but in test mode this reflects un-committed changes

**Recommendation:** Either commit the transaction in test mode after the execute(), or restructure to use a consistent transaction pattern across both modes.

---

### DP-006: Graceful handling of missing columns in graphs causes silent data loss

| Field | Value |
|-------|-------|
| **ID** | DP-006 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/services/aggregation_service.py` |
| **Classification** | advisory |

**Description:** When a graph has dimensions or metrics that don't exist in the uploaded CSV, the `aggregate_for_dashboard` method silently skips the graph (line 61-65) without recording any error. This can lead to silent data loss where users believe their data was processed but graphs have no data because column names didn't match. While this is handled gracefully (no crash), it may confuse users.

**Evidence:**
- `src/mkobi/services/aggregation_service.py:61-65` - Graph is skipped with warning but no error recorded
- `src/mkobi/services/aggregation_service.py:85-86` - No return status or metrics about skipped graphs

**Recommendation:** Consider adding skipped graph information to the processing log message or returning a count of skipped graphs so users can be informed about mismatched configurations.

---

### DP-007: Potential unbounded memory usage with lazy CSV loading

| Field | Value |
|-------|-------|
| **ID** | DP-007 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/data/loaders/loader.py` |
| **Classification** | advisory |

**Description:** While `CSVLoader` supports lazy loading via `pl.scan_csv()`, the lazy evaluation is immediately followed by `.collect()` (line 210 in loader.py), which loads the entire dataset into memory. For truly large datasets where memory consumption is a concern, this doesn't provide the intended memory benefit. Additionally, the lazy threshold is hardcoded (10MB) and there's no streaming/chunking option for files that exceed available memory.

**Evidence:**
- `src/mkobi/data/loaders/loader.py:210` - `pl.scan_csv(...).collect()` negates lazy benefits
- `src/mkobi/config.py:188` - `lazy_threshold_mb = 10.0` hardcoded default

**Recommendation:** For files larger than a certain threshold, consider using true streaming during aggregation or implement chunked processing. Currently, the lazy evaluation provides no memory benefit since `.collect()` is called immediately.

---

### DP-008: Unsafe eval() in computed field expressions allows code injection

| Field | Value |
|-------|-------|
| **ID** | DP-008 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/data/processing/filter_transforms.py` |
| **Classification** | mandatory |

**Description:** The `_add_computed_fields` function uses Python's `eval()` to execute user-provided expressions for computed fields (line 100). The expression is evaluated with a restricted namespace (`"{__builtins__: {}}`), but this restriction is insufficient to prevent all code injection attacks. An attacker with control over processing configuration could potentially execute arbitrary code. Additionally, `eval()` on untrusted input is a security best practice violation.

**Evidence:**
- `src/mkobi/data/processing/filter_transforms.py:96-100` - `eval(expr_str.strip(), {"__builtins__": {}}, polars_ns)` without proper sandboxing
- `src/mkobi/data/processing/transformations.py:117-129` - Computed fields can come from user-controlled processing config
- `src/mkobi/models/types.py:175` - `computed_fields: list[dict[str, str]] | None` is user-configurable

**Recommendation:** Replace `eval()` with a safe expression parser (e.g., `asteval`, `simpleeval`, or a custom AST walker) that only allows arithmetic operations. Alternatively, restrict the expression format to a safe DSL that can be validated before execution.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 2 |
| HIGH | 1 |
| MEDIUM | 5 |
| LOW | 0 |

## Mandatory Fixes

- DP-001: Missing transaction wrapper in `_process_csv_file_async` test mode
- DP-002: Incomplete transaction boundary in `_store_aggregates` causes partial commit risk
- DP-003: Potential race condition in task state transition from PROCESSING to FAILED
- DP-004: Empty DataFrame handling does not prevent processing continuation
- DP-005: cleanup_stale_processing_logs test mode lacks commit for status updates
- DP-008: Unsafe eval() in computed field expressions allows code injection

## Advisory Recommendations

- DP-006: Graceful handling of missing columns in graphs causes silent data loss
- DP-007: Potential unbounded memory usage with lazy CSV loading

---

## Pipeline Correctness Evidence Trace

### Step R1 — End-to-end Pipeline Trace
1. **Upload entry:** `src/mkobi/api/routes/upload.py:52-227` - `upload_file_endpoint` streams file in chunks, validates MIME/extension, validates size
2. **Validation:** `src/mkobi/services/file_processing.py:91-159` - `validate_file` checks existence, size, MIME type, extension
3. **Logging:** `src/mkobi/services/file_processing.py:210-231` - Creates processing log with STARTED then UPLOADED status
4. **Background processing:** `src/mkobi/workers/data_worker.py:156-346` - `_process_csv_file_async` loads CSV, applies transformations, stores aggregates
5. **Storage:** `src/mkobi/workers/data_worker.py:348-520` - `_store_aggregates` with StorageManager handles atomic storage

### Step R2 — Resource Cleanup Analysis
- Temp file creation: `src/mkobi/api/routes/upload.py:147-148` - `upload_{uuid}_{filename}`
- Temp file cleanup on upload error: `src/mkobi/api/routes/upload.py:203-208` - finally block removes temp file
- Temp file cleanup on processing success: `src/mkobi/workers/data_worker.py:307-310` - deletes after `_store_aggregates`
- Temp file cleanup on processing error: `src/mkobi/workers/data_worker.py:331-340` - exception handler cleanup
- Stale file cleanup: `src/mkobi/services/file_cleanup.py:39-96` - removes old files by mtime threshold

### Step R3 — Transaction Boundary Analysis
- Production mode: `src/mkobi/workers/data_worker.py:458-459` - `async with session.begin()` wraps all operations
- Test mode: `src/mkobi/workers/data_worker.py:394-460` - NO transaction wrapper found
- Status updates in `_update_processing_log_status`: Lines 73-77 (test) vs 80-87 (production) have inconsistent handling

### Step R4 — Determinism Analysis
- JSON key normalization: `src/mkobi/data/storage/manager.py:33-50` - `_normalize_json_keys` ensures deterministic ordering
- Sorting in aggregations: `src/mkobi/data/processing/aggregate_transforms.py:181, 247` - explicit sorting before YoY calculations
- No random values or timestamps in aggregation logic
- Floating point operations in YoY (line 205) and share (line 248) calculations may have precision drift

### Step R5 — Recalculation Completeness
- OVERWRITE mode: `src/mkobi/data/storage/manager.py:113-134` - deletes old data, then inserts new data
- APPEND mode: `src/mkobi/data/storage/manager.py:136-148` - performs UPSERT without clearing old data
- Both paths process from original DataFrame - full recalculation occurs