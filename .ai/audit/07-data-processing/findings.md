# Phase 07 Audit Findings — Data Processing Pipeline

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### DP-001: Enqueue failure silently leaves task permanently stuck at UPLOADED status

| Field | Value |
|-------|-------|
| **ID** | DP-001 |
| **Severity** | CRITICAL |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/services/file_processing.py`, `src/mkobi/core/task_queue.py`, `src/mkobi/workers/data_worker.py` |
| **Classification** | mandatory |

**Description:** When `enqueue_job()` fails (returns `None`), `enqueue_processing_job()` does not check the return value and does not raise an error. The processing log remains at `UPLOADED` status, and no background processing will ever occur. The stale processing cleanup (`cleanup_stale_processing_logs`) only targets entries in `PROCESSING` status — it does not handle `UPLOADED` or `STARTED`. This means the task is permanently stuck with no automatic recovery path.

**Evidence:**
- `src/mkobi/core/task_queue.py:176-180` — `enqueue_job` catches all exceptions and returns `None` on failure:
  ```python
  async def enqueue_job(...) -> str | None:
      try:
          return await default_queue.enqueue(func, *args, **kwargs)
      except Exception as e:
          logger.error("Failed to enqueue job: %s", e)
          return None
  ```
- `src/mkobi/services/file_processing.py:348-354` — return value of `enqueue_job` is ignored:
  ```python
  await enqueue_job(
      process_csv_background,
      file_path_str=file_path,
      ...
  )
  ```
- `src/mkobi/workers/data_worker.py:121-122` — stale cleanup only handles `PROCESSING`:
  ```python
  .where(
      ProcessingLog.status == ProcessingStatus.PROCESSING,
  ```

**Recommendation:** Propagate enqueue failures: check `enqueue_job` return value in `enqueue_processing_job` and raise `AppException(ErrorCode.PROCESSING_FAILED)` if `None`. Additionally, extend `cleanup_stale_processing_logs` to also handle `UPLOADED` entries older than a threshold (the file exists but processing never started).

---

### DP-002: Multi-transaction pipeline allows inconsistent state between aggregates and processing log

| Field | Value |
|-------|-------|
| **ID** | DP-002 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/workers/data_worker.py` |
| **Classification** | mandatory |

**Description:** The background processing pipeline executes three independent database transactions in sequence: (1) update log to PROCESSING, (2) store aggregates, (3) update log to COMPLETED. Each opens its own session with `get_session()` + `session.begin()`. If the aggregate storage (step 2) succeeds but the COMPLETED status update (step 3) fails, the aggregated data is committed to the database while the processing log remains in `PROCESSING` status. The stale cleanup task will eventually mark it `FAILED`, creating a false negative: data exists and is correct, but the user-visible task status says `FAILED`. Conversely, if step 2 partially fails mid-transaction, the rollback is correct (within that single transaction), but the FAILED status update (step 3') is yet another separate transaction that could also fail.

**Evidence:**
- `src/mkobi/workers/data_worker.py:461-463` — `_store_aggregates` production path creates its own transaction:
  ```python
  async with get_session() as session:
      async with session.begin():
  ```
- `src/mkobi/workers/data_worker.py:81-85` — `_update_processing_log_status` production path creates its own transaction:
  ```python
  async with get_session() as db:
      async with db.begin():
  ```
- `src/mkobi/workers/data_worker.py:299-308` — after `_store_aggregates`, another separate `_update_processing_log_status` call for COMPLETED status.

**Recommendation:** Wrap the entire processing pipeline (aggregate storage + final status update) in a single database transaction. Use a session context at the `process_csv_background` level and pass it through to `_store_aggregates` and `_update_processing_log_status`, committing only after both succeed. This ensures atomicity: either both changes persist or neither does.

---

### DP-003: In-memory task queue loses all pending jobs on server restart

| Field | Value |
|-------|-------|
| **ID** | DP-003 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/core/task_queue.py` |
| **Classification** | mandatory |

**Description:** The `TaskQueue` implementation uses `asyncio.Queue` for in-memory storage. All pending tasks, statuses, results, and errors are lost when the server process restarts or crashes. The code acknowledges this ("MVP: Uses in-memory queue (non-persistent, tasks lost on restart)"), but the processing log entries in the database remain in `UPLOADED` or `PROCESSING` status forever (no automatic retry, no recovery mechanism). Combined with DP-001 (stale cleanup only targets `PROCESSING`), tasks in `UPLOADED` status after a restart are permanently orphaned.

**Evidence:**
- `src/mkobi/core/task_queue.py:27-29` — in-memory storage:
  ```python
  self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
  self._statuses: dict[str, ProcessingStatus] = {}
  self._results: dict[str, Any] = {}
  self._errors: dict[str, str | None] = {}
  ```
- `src/mkobi/core/task_queue.py:143-154` — shutdown only warns, does not persist:
  ```python
  async def shutdown(self) -> None:
      """Log warning for pending tasks on shutdown."""
      pending = self._queue.qsize()
      if pending > 0:
          logger.warning(
              "TaskQueue shutting down with %d pending tasks. "
              "These will be lost. Consider using Redis/RQ for persistence.",
  ```

**Recommendation:** Extend `cleanup_stale_processing_logs` to also handle `UPLOADED` status entries older than a threshold (e.g., 30 minutes), marking them as `FAILED` with message "Job never started - possibly lost on server restart". Additionally, for each such entry, check if the source file still exists in the upload temp directory and re-enqueue the job if found.

---

### DP-004: _store_aggregates test-mode path bypasses transaction boundary

| Field | Value |
|-------|-------|
| **ID** | DP-004 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/workers/data_worker.py` |
| **Classification** | advisory |

**Description:** In production mode, `_store_aggregates` wraps all operations in `async with session.begin()`, ensuring atomicity. In test mode (`db_session is not None`), the function executes database operations directly on the provided session without any transaction context. The comment says "Caller manages the transaction (SAVEPOINT pattern)", but the caller `_process_csv_file_async` does not establish a transaction either when `db_session` is provided. This means test-mode writes can be partially committed if an operation fails mid-sequence (e.g., after `save_aggregates` but before `save_filter_values`).

**Evidence:**
- `src/mkobi/workers/data_worker.py:397-459` — test mode path has no `session.begin()`:
  ```python
  if db_session is not None:
      # Test mode - use provided session without creating nested transaction.
      # Caller manages the transaction (SAVEPOINT pattern in async_db_session fixture).
      result = await db_session.execute(...)
  ```
- `src/mkobi/workers/data_worker.py:449-459` — filter value saves follow after main aggregate save with no error boundary between them.

**Recommendation:** Wrap the test-mode path in a SAVEPOINT using `async with db_session.begin_nested():` to ensure all operations within `_store_aggregates` are atomic even in test mode. This matches the production behavior and prevents partial writes in test scenarios.

---

### DP-005: AggregationService hardcodes "sum" as the only aggregation function

| Field | Value |
|-------|-------|
| **ID** | DP-005 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/services/aggregation_service.py` |
| **Classification** | advisory |

**Description:** `AggregationService.aggregate_for_dashboard` hardcodes `pl.col(m).sum()` as the only aggregation expression for all metrics (line 68). The `metric_agg` parameter exists but is unused — it accepts a string but never applies it. This means the per-chart aggregation step in the background worker always sums all metrics, ignoring other aggregation functions (mean, count, min, max, median, etc.) that are supported by `AggregationFunctionEnum` and the processing config pipeline. If a graph config specifies `mean` or `count` as the desired aggregation, it will be silently ignored during the dashboard-level aggregation in `_store_aggregates`.

**Evidence:**
- `src/mkobi/services/aggregation_service.py:68` — hardcoded sum:
  ```python
  agg_exprs = [pl.col(m).sum().alias(f"{m}_sum") for m in metric_cols]
  ```
- `src/mkobi/services/aggregation_service.py:34` — `metric_agg` parameter is accepted but never used:
  ```python
  async def aggregate_for_dashboard(
      self, ..., metric_agg: str = "sum",
  ) -> list[dict[str, Any]]:
  ```

**Recommendation:** Map the `metric_agg` parameter to the appropriate `AggregationFunctionEnum` and use `AGG_FUNC_MAP` from `aggregate_transforms.py` to build the correct aggregation expressions. Alternatively, read the preferred aggregation function from each graph's configuration (e.g., `graph.config.agg_function`) if per-graph aggregation is needed.

---

### DP-006: Formula parser lacks operator precedence and parentheses support

| Field | Value |
|-------|-------|
| **ID** | DP-006 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/data/processing/formula_parser.py` |
| **Classification** | advisory |

**Description:** The formula parser (`_parse_formula`) evaluates all operations strictly left-to-right with no operator precedence. The code documents this as a known limitation (lines 68-72). This means `a + b * c` evaluates as `(a + b) * c` instead of the standard `a + (b * c)`. Users defining computed fields with mixed operators will get silently incorrect results. There is also no support for parentheses, making complex expressions impossible without pre-computing intermediate fields.

**Evidence:**
- `src/mkobi/data/processing/formula_parser.py:62-72` — documented limitation:
  ```python
  # Known limitations
  # -----------------
  # - **No parentheses** – ``(a + b) * c`` will not group as expected.
  # - **No operator precedence** – all operations evaluate strictly
  #   left-to-right (e.g. ``"a + b * c"`` means ``(a + b) * c``, not
  #   ``a + (b * c)``).
  ```
- `src/mkobi/data/processing/formula_parser.py:139-158` — left-to-right evaluation loop with no precedence handling.

**Recommendation:** Implement standard arithmetic operator precedence (multiplication/division before addition/subtraction) and add parentheses support. This can be done with a simple recursive-descent parser or the Shunting-yard algorithm. Until fixed, document this limitation prominently in the processing configuration UI so users aren't surprised by incorrect computed fields.

---

### DP-007: DataValidator is never invoked in the main upload→process pipeline

| Field | Value |
|-------|-------|
| **ID** | DP-007 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/data/loaders/validator.py`, `src/mkobi/workers/data_worker.py` |
| **Classification** | advisory |

**Description:** A `DataValidator` class exists with comprehensive validation (empty check, required columns, type checking, data quality, duplicates), but it is never called in the main data processing pipeline (`data_worker._process_csv_file_async`). Validation currently relies on `CSVLoader._validate_required_columns` (which only checks column names) and `file_processing.validate_file` (which checks MIME type, extension, and size). This means the rich data quality checks (null values, empty strings, duplicates, type mismatches) are unavailable unless the caller explicitly constructs and invokes a `DataValidator`, which the background worker does not do.

**Evidence:**
- `src/mkobi/data/loaders/validator.py:37-103` — `DataValidator.validate()` performs comprehensive checks but is never called from `data_worker.py` or `file_processing.py`.
- `src/mkobi/workers/data_worker.py:206-209` — only `CSVLoader.load_csv()` is called, which only validates required columns if `config.required_columns` is set:
  ```python
  loader = CSVLoader()
  df = await asyncio.to_thread(
      loader.load_csv, file_path, csv_parse_config if csv_parse_config else None
  )
  ```

**Recommendation:** After loading the CSV in `_process_csv_file_async`, construct a `DataValidator` with the processing config's column metadata and invoke `validate()`. If `result.is_valid` is `False`, raise an error and mark the task as `FAILED` with the validation errors. Log warnings for validation warnings. This prevents malformed data from reaching the aggregation step.

---

### DP-008: Task state machine has unreachable and unhandled transitions

| Field | Value |
|-------|-------|
| **ID** | DP-008 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/workers/data_worker.py`, `src/mkobi/models/enums.py` |
| **Classification** | mandatory |

**Description:** The `ProcessingStatus` enum defines five states: `STARTED`, `UPLOADED`, `PROCESSING`, `COMPLETED`, `FAILED`. The expected state machine is: `STARTED → UPLOADED → PROCESSING → COMPLETED|FAILED`. However:
1. The `STARTED` → `UPLOADED` transition happens in `file_processing.py:214→227`, but `STARTED` is never visible to users (immediately overwritten by `UPLOADED` within the same request).
2. The stale cleanup only rescues `PROCESSING` → `FAILED`. Entries stuck at `STARTED` or `UPLOADED` are never recovered.
3. There is no validation that status transitions follow the expected sequence. Any status can be written at any time.
4. The `trigger_processing` method in `data_service.py:281` transitions directly from any status to `PROCESSING` without checking current status, allowing invalid transitions like `COMPLETED → PROCESSING`.

**Evidence:**
- `src/mkobi/workers/data_worker.py:121-122` — only `PROCESSING` is cleaned up:
  ```python
  .where(
      ProcessingLog.status == ProcessingStatus.PROCESSING,
  ```
- `src/mkobi/services/data_service.py:279-284` — `trigger_processing` does not validate current status before transitioning:
  ```python
  log = await get_and_validate_processing_log(...)
  file_path = find_task_file(task_id)
  await self.log_repo.update_status(
      log_id=task_id, status=ProcessingStatus.PROCESSING,
  ```
- `src/mkobi/models/enums.py:58-65` — `ProcessingStatus` enum defines all 5 states with no transition validation.

**Recommendation:** (1) Extend `cleanup_stale_processing_logs` to handle both `UPLOADED` and `PROCESSING` statuses. (2) Add a `_validate_transition(current, new)` function that checks the valid state machine before any status update. (3) In `trigger_processing`, verify that the current status allows re-processing (e.g., only `UPLOADED` or `FAILED`).

---

### DP-009: File move to final location after commit creates orphaned file if enqueue fails

| Field | Value |
|-------|-------|
| **ID** | DP-009 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/services/file_processing.py` |
| **Classification** | advisory |

**Description:** In `process_upload_with_session`, the file is moved from temp to final location (line 236: `file_path.replace(final_file_path)`) AFTER the database commit (line 231) but BEFORE the job is enqueued (line 251). If enqueue fails, the file sits at the final location (`upload_dir / f"{log.id}{file_ext}"`) with no processing ever happening. The stale temp file cleanup (`cleanup_stale_temp_files`) WILL eventually delete it (since it's in the upload temp dir), but only after `stale_file_threshold_hours` (default 24h). Meanwhile, a manual re-process attempt via `trigger_processing` would work (the file is findable by task ID), but users have no way to know the task is stuck unless they poll the status endpoint.

**Evidence:**
- `src/mkobi/services/file_processing.py:233-243` — file move after commit, before enqueue:
  ```python
  await db.commit()
  # Move file to final location with log ID as filename AFTER successful commit
  final_file_path = upload_dir / f"{log.id}{file_ext}"
  try:
      file_path.replace(final_file_path)
  except Exception:
      logger.error("Failed to move file to final path after commit, log_id=%s", ...)
      raise
  ```
- `src/mkobi/services/file_processing.py:251-257` — enqueue after move with no error handling:
  ```python
  await enqueue_processing_job(...)
  ```

**Recommendation:** If `enqueue_processing_job` fails (per DP-001 fix), catch the error, delete the final file (since it won't be processed), and re-raise. Alternatively, enqueue the job BEFORE moving the file, and move it as the first step of the background worker.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 1 |
| HIGH | 2 |
| MEDIUM | 6 |
| LOW | 0 |

## Mandatory Fixes

- **DP-001** (CRITICAL): Enqueue failure silently leaves task permanently stuck at UPLOADED status. Failed enqueue must propagate as an error; stale cleanup must handle UPLOADED status.
- **DP-002** (HIGH): Multi-transaction pipeline allows inconsistent state between aggregates and processing log. Wrap aggregate storage and final status update in a single transaction.
- **DP-003** (HIGH): In-memory task queue loses all pending jobs on server restart. Extend stale cleanup to recover UPLOADED entries; consider re-enqueueing jobs whose source files still exist.
- **DP-008** (MEDIUM): Task state machine has unreachable and unhandled transitions. Add transition validation and extend stale cleanup to cover UPLOADED status.

## Advisory Recommendations

- **DP-004**: _store_aggregates test-mode path bypasses transaction boundary. Use SAVEPOINT for test mode atomicity.
- **DP-005**: AggregationService hardcodes "sum" as the only aggregation function despite supporting enum. Map metric_agg parameter to actual aggregation expressions.
- **DP-006**: Formula parser lacks operator precedence and parentheses support. Implement standard arithmetic precedence or document limitation prominently in UI.
- **DP-007**: DataValidator is never invoked in the main upload→process pipeline. Integrate data quality validation into the background worker after loading CSV.
- **DP-009**: File move to final location after commit creates orphaned file if enqueue fails. Coordinate file lifecycle with enqueue success/failure.

## Doc Updates Needed

None.

---
