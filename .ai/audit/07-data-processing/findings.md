# Phase 07 Audit Findings — Data Processing Pipeline

**Executor:** auditor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### DP-01: `DataPipeline` in `registry.py` is dead code with transaction safety issues

| Field | Value |
|-------|-------|
| **ID** | DP-01 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/data/processing/registry.py` |
| **Classification** | advisory |

**Description:** The `DataPipeline` class in `registry.py` is defined but never imported or executed anywhere in the codebase. The actual processing path goes through `data_worker.py:process_csv_background → _process_csv_file_async`. `DataPipeline` is orphaned code that also has a critical architectural flaw: it receives a `db: AsyncSession` parameter in its `run()` method but never wraps the multi-step processing (transform → aggregate → save) in a single transaction boundary (`session.begin()`). Each step commits/rolls back independently via the injected `log_service`, meaning partial results could be persisted if a later step fails.

**Evidence:**
- `src/mkobi/data/processing/registry.py:67-179` — `DataPipeline.run()` calls `apply_transformations`, `aggregate_data`, `_save_with_retry`, and multiple `log_service.update_processing_log` calls without a surrounding `async with session.begin()` transaction.
- Grep for `DataPipeline` across the entire `src/` tree returns only the class definition itself and a comment in `processing_log_service.py:51` — zero call sites.
- The active pipeline in `src/mkobi/workers/data_worker.py:522-551` correctly wraps everything in `async with session.begin()`.

**Recommendation:** Remove `DataPipeline` from `registry.py` to eliminate dead code and avoid confusion. If it was intended as a refactor target, document that `data_worker.py` is the authoritative implementation. Effort: trivial. Priority: recommended.

---

### DP-02: APPEND mode does not clear stale filter values, causing data drift

| Field | Value |
|-------|-------|
| **ID** | DP-02 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/workers/data_worker.py` |
| **Classification** | mandatory |

**Description:** In `_store_aggregates`, when `mode == UploadMode.APPEND`, the filter values from previous uploads are never cleared — only the `OVERWRITE` branch calls `filter_values_repo.clear_dashboard_values()`. This means that in APPEND mode, filter values from old data (including values that no longer exist in the appended dataset) will persist indefinitely in the `dashboard_filter_values` table. Users will see stale/phantom filter options in the UI that don't correspond to any actual data.

Per SPEC.md: "Values are rebuilt on each upload (idempotent overwrite)." The APPEND mode should either also rebuild filter values from the combined dataset, or the behavior should be explicitly documented as a known limitation.

**Evidence:**
- `src/mkobi/workers/data_worker.py:659-660` — test mode path: `if mode == UploadMode.OVERWRITE: await filter_values_repo.clear_dashboard_values(dashboard_id, db_session)`
- `src/mkobi/workers/data_worker.py:730-731` — production mode path: identical conditional, no APPEND handling
- SPEC.md line 173: "Values are rebuilt on each upload (idempotent overwrite)"

**Recommendation:** In APPEND mode, after saving new filter values, also delete any filter values for the dashboard that are not present in the new dataset. Alternatively, clear and rebuild filter values on every upload regardless of mode. The simplest fix: always clear dashboard filter values before saving new ones, removing the `if mode == UploadMode.OVERWRITE` guard. Effort: small. Priority: mandatory.

---

### DP-03: `find_task_file` uses glob with task_id substring, risking file collision

| Field | Value |
|-------|-------|
| **ID** | DP-03 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/services/file_processing.py` |
| **Classification** | advisory |

**Description:** `find_task_file()` uses `upload_dir.glob(f"*{task_id}*.csv*")` to locate a task's file. Since UUIDs are hex strings, it's theoretically possible (though unlikely) for one UUID to be a substring of another, causing the glob to match multiple files. The function returns `task_files[0]` (arbitrary order), which could return the wrong file. More practically, the glob pattern `*{task_id}*` is broader than necessary — the file was stored as `{task_id}{file_ext}` (e.g., `{uuid}.csv`), so the pattern should be `{task_id}.csv*`.

**Evidence:**
- `src/mkobi/services/file_processing.py:295` — `task_files = list(upload_dir.glob(f"*{task_id}*.csv*"))`
- `src/mkobi/services/file_processing.py:234` — file is stored as `final_file_path = upload_dir / f"{log.id}{file_ext}"` where `file_ext` is `.csv` or `.csv.gz`
- `src/mkobi/services/file_processing.py:300` — returns `task_files[0]` without checking for multiple matches

**Recommendation:** Change the glob to `f"{task_id}.csv*"` to match the exact naming convention used when the file was stored. Add an assertion or error if more than one file matches. Effort: trivial. Priority: recommended.

---

### DP-04: `_update_processing_log_status` in test mode does not rollback on failure

| Field | Value |
|-------|-------|
| **ID** | DP-04 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/workers/data_worker.py` |
| **Classification** | advisory |

**Description:** In `_update_processing_log_status`, when `session is not None` (test mode), the function executes the UPDATE statement but explicitly does NOT commit (by design — the caller manages the transaction). However, if the UPDATE fails with a `SQLAlchemyError`, the function catches it, logs it, and silently swallows the error. The comment says "No rollback in test mode - caller (SAVEPOINT) manages transaction", but the swallowed exception means the caller never knows the status update failed. This could leave processing logs in an inconsistent state during tests, making test assertions unreliable.

**Evidence:**
- `src/mkobi/workers/data_worker.py:214-230` — test mode path: `await session.execute(stmt)` followed by `except SQLAlchemyError: logger.error(...)` with no re-raise
- `src/mkobi/workers/data_worker.py:228` — comment: "No rollback in test mode - caller (SAVEPOINT) manages transaction"

**Recommendation:** Consider re-raising the exception after logging, or at minimum adding a warning-level log that clearly indicates the status update was lost. This makes test debugging easier. Effort: trivial. Priority: recommended.

---

### DP-05: `AggregationService.aggregate_for_dashboard` converts all dimension values to strings, losing type information

| Field | Value |
|-------|-------|
| **ID** | DP-05 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/services/aggregation_service.py` |
| **Classification** | advisory |

**Description:** In `AggregationService.aggregate_for_dashboard()`, all dimension values are cast to `str()` before storing in the `dims` dict: `dims = {col: str(row[col]) for col in groupby_cols}`. This means numeric dimensions (e.g., year=2024), date dimensions, and boolean dimensions all become strings. When these are later stored in JSONB and retrieved for filtering/sorting, numeric sorting becomes lexicographic (e.g., "9" > "10"), and date ordering breaks. The frontend receives all dimension values as strings and must parse them back.

**Evidence:**
- `src/mkobi/services/aggregation_service.py:83` — `dims = {col: str(row[col]) for col in groupby_cols}`
- These dims are stored in JSONB via `src/mkobi/data/storage/manager.py:296` — `"dims": _normalize_json_keys(agg["dims"])`

**Recommendation:** Preserve original types in dims values. Only cast to string when the value is a Polars date/datetime type that doesn't serialize cleanly to JSON. Use `row[col]` directly and let JSON serialization handle native Python types (int, float, str, bool). Effort: small. Priority: recommended.

---

### DP-06: `_calculate_yoy` uses `round(4)` on floating-point results, causing precision loss in aggregations

| Field | Value |
|-------|-------|
| **ID** | DP-06 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/data/processing/aggregate_transforms.py` |
| **Classification** | advisory |

**Description:** Both `_calculate_yoy` and `_calculate_share` apply `.round(4)` to their results. This truncates YoY percentages and share percentages to 4 decimal places. While this is reasonable for display, it means the stored aggregated data has reduced precision. If downstream calculations use these rounded values (e.g., summing YoY across groups), errors compound. The rounding should ideally happen at the presentation layer, not during data processing/storage.

**Evidence:**
- `src/mkobi/data/processing/aggregate_transforms.py:205` — `.round(4)` on YoY calculation
- `src/mkobi/data/processing/aggregate_transforms.py:248` — `.round(4)` on share calculation with group_cols
- `src/mkobi/data/processing/aggregate_transforms.py:257` — `.round(4)` on share calculation without group_cols

**Recommendation:** Store full-precision values in the database. Apply rounding only when formatting for display in the frontend or API response serialization. Effort: small. Priority: recommended.

---

### DP-07: In-memory `TaskQueue` loses all pending tasks on worker crash or restart

| Field | Value |
|-------|-------|
| **ID** | DP-07 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/core/task_queue.py` |
| **Classification** | mandatory |

**Description:** The `TaskQueue` implementation uses `asyncio.Queue` with in-memory `_statuses`, `_results`, and `_errors` dictionaries. If the worker process crashes or is restarted, all enqueued tasks and their statuses are permanently lost. The `processing_logs` row remains in `STARTED` or `UPLOADED` state indefinitely (until the stale cleanup task marks it as FAILED after 30 minutes). During that 30-minute window, users see the task as "in progress" with no way to recover. The SPEC documents this as MVP behavior with a migration path to Redis/RQ, but there is no detection or alerting for lost tasks.

**Evidence:**
- `src/mkobi/core/task_queue.py:28-31` — `self._queue: asyncio.Queue`, `self._statuses: dict`, `self._results: dict`, `self._errors: dict` — all in-memory
- `src/mkobi/core/task_queue.py:144-155` — `shutdown()` only logs a warning about pending tasks
- `src/mkobi/workers/data_worker.py:234-292` — `cleanup_stale_processing_logs` has a 30-minute default timeout
- SPEC.md line 121: "In-memory TaskQueue (MVP) with a documented migration path to Redis/RQ"

**Recommendation:** This is acknowledged MVP behavior. To reduce the impact: (1) lower the stale processing timeout from 30 minutes to 5 minutes for faster failure detection, (2) add a startup check that marks any `UPLOADED` logs (not just `PROCESSING`) as FAILED if no worker has touched them, since `UPLOADED` means "enqueued but not yet started". Effort: small. Priority: mandatory for production use.

---

### DP-08: `_process_csv_file_async` error path updates status but transaction rolls back, leaving no failure record

| Field | Value |
|-------|-------|
| **ID** | DP-08 |
| **Severity** | CRITICAL |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/workers/data_worker.py` |
| **Classification** | mandatory |

**Description:** In the production mode error path of `_process_csv_file_async` (line 520-551), when an exception occurs inside the `async with session.begin()` block, the flow is: (1) exception is caught, (2) `_update_processing_log_status` is called with `session=session` to set status to FAILED, (3) the exception is re-raised. However, because the `session.begin()` context manager catches the re-raised exception and performs a **rollback**, the FAILED status update from step 2 is also rolled back. The processing log is left in whatever state it was before the error — typically `PROCESSING`. The stale cleanup task will eventually mark it as FAILED, but until then, the user sees a permanently stuck "processing" task with no error details.

The same issue exists in the test mode error path (line 492-519) if the caller's SAVEPOINT is rolled back.

**Evidence:**
- `src/mkobi/workers/data_worker.py:520-551` — production error path:
  ```python
  async with get_session() as session:
      async with session.begin():          # <-- transaction boundary
          try:
              return await _run_with_transaction(session)
          except Exception as e:
              # ... update status to FAILED within same session ...
              await _update_processing_log_status(
                  task_id=task_id, status=ProcessingStatus.FAILED, ..., session=session
              )
              raise  # <-- session.begin() catches this and ROLLS BACK
  ```
- `src/mkobi/workers/data_worker.py:218-222` — `_update_processing_log_status` in test mode does NOT commit, relying on the caller's transaction

**Recommendation:** The FAILED status update must use a **separate, independent database session** that commits immediately, outside the rolled-back transaction. Create a new session via `get_session()` inside the except block, use it to update the status to FAILED, commit it, and close it. This ensures the failure record persists even when the main transaction rolls back. Effort: small. Priority: mandatory.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 1 |
| HIGH | 2 |
| MEDIUM | 3 |
| LOW | 2 |

## Mandatory Fixes

1. **DP-02** — APPEND mode does not clear stale filter values, causing data drift
2. **DP-07** — In-memory `TaskQueue` loses all pending tasks on worker crash or restart (MVP limitation, needs mitigation)
3. **DP-08** — `_process_csv_file_async` error path updates status but transaction rolls back, leaving no failure record

## Advisory Recommendations

1. **DP-01** — `DataPipeline` in `registry.py` is dead code with transaction safety issues
2. **DP-03** — `find_task_file` uses glob with task_id substring, risking file collision
3. **DP-04** — `_update_processing_log_status` in test mode does not rollback on failure
4. **DP-05** — `AggregationService.aggregate_for_dashboard` converts all dimension values to strings, losing type information
5. **DP-06** — `_calculate_yoy` uses `round(4)` on floating-point results, causing precision loss in aggregations

## Doc Updates Needed

- SPEC.md should document the APPEND mode behavior for filter values (DP-02) — either as a known limitation or as a bug to fix.
- SPEC.md should document the in-memory TaskQueue limitations and the stale processing timeout behavior (DP-07).
