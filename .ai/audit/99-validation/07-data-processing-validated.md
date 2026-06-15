# Phase 07 Data Processing Validation Report

**Validator:** validator  
**Source:** `.ai/audit/07-data-processing/findings.md`  
**Date:** 2026-06-15

---

## Rejected Findings

None — all findings are technically accurate and describe real issues in the codebase.

---

## Merged Findings

None — no findings overlap with other audit phases.

---

## Reclassified Findings

None — all findings retain their original classification.

---

## Cross-Phase Conflicts

**No conflicts detected.** The data processing findings are consistent with other audit phases and do not contradict any findings from backend, security, or integration audits.

---

## Rollout Safety Issues

| Finding ID | Issue | Risk |
|------------|-------|------|
| DP-08 | FAILED status update must use independent session outside rolled-back transaction | MEDIUM — requires careful implementation to avoid creating connection leaks or double-commit scenarios |
| DP-02 | Filter value clear logic change could cause unintended data loss in APPEND mode if not tested | MEDIUM — the fix should be verified with APPEND mode integration tests before deployment |

---

## Validated Mandatory Fixes

| ID | Description | Severity |
|----|-------------|----------|
| **DP-02** | APPEND mode does not clear stale filter values, causing data drift | HIGH |
| **DP-07** | In-memory TaskQueue loses pending tasks on crash; needs mitigation | HIGH |
| **DP-08** | Error path status update rolls back, leaving no failure record | CRITICAL |

### DP-02 Evidence Verification

- `data_worker.py:659-660` (test mode): `if mode == UploadMode.OVERWRITE: await filter_values_repo.clear_dashboard_values(dashboard_id, db_session)`
- `data_worker.py:730-731` (production mode): Identical conditional, APPEND mode excluded
- SPEC.md line 173: "Values are rebuilt on each upload (idempotent overwrite)"

The specification explicitly states values should be rebuilt on each upload, but APPEND mode does not clear old values before saving new ones. This is a valid SPEC-DEVIATION.

### DP-07 Evidence Verification

- `task_queue.py:28-31`: All state structures (`_queue`, `_statuses`, `_results`, `_errors`) are in-memory dicts
- `task_queue.py:144-155`: `shutdown()` only logs warning, tasks are lost
- SPEC.md line 121: Acknowledges "In-memory TaskQueue (MVP) with a documented migration path to Redis/RQ"
- SPEC.md line 144: "Stale processing heartbeat... marks processing logs stuck in PROCESSING state for more than 30 minutes as FAILED"

This is acknowledged MVP behavior per specification. The recommendations (lower timeout, mark UPLOADED as FAILED on startup) are valid mitigations.

### DP-08 Evidence Verification

- `data_worker.py:522-523`: `async with session.begin():` establishes transaction boundary
- `data_worker.py:524-551`: Exception caught inside context, `_update_processing_log_status` called, then `raise` re-raises
- The `session.begin()` context manager catches the re-raised exception and performs ROLLBACK
- This rolls back the FAILED status update along with all other changes in the transaction

This is a critical architectural flaw — the FAILED status update is lost when the main transaction rolls back, leaving processing logs permanently in PROCESSING state until the stale cleanup task runs (up to 30 minutes later).

---

## Validated Advisory Recommendations

| ID | Description |
|----|-------------|
| DP-01 | Remove dead `DataPipeline` class from `registry.py` |
| DP-03 | Tighten `find_task_file` glob pattern to exact match |
| DP-04 | Re-raise exception in `_update_processing_log_status` test mode on SQLAlchemyError |
| DP-05 | Preserve original types in `AggregationService.aggregate_for_dashboard` dims values |
| DP-06 | Move rounding to presentation layer |

---

## Evidence Summary

### DP-01 Dead Code Verification

- `DataPipeline` defined in `registry.py:33-221` with 7 methods
- Grep search confirms only references are the class definition itself and a comment in `processing_log_service.py:51`
- Active processing in `data_worker.py:522-551` correctly wraps operations in `session.begin()`
- `DataPipeline.run()` has no surrounding transaction boundary

### DP-03 Glob Pattern Verification

- `file_processing.py:234`: File stored as `final_file_path = upload_dir / f"{log.id}{file_ext}"` (e.g., `{uuid}.csv.gz`)
- `file_processing.py:295`: `task_files = list(upload_dir.glob(f"*{task_id}*.csv*"))` matches any file containing task_id anywhere in name
- `file_processing.py:300`: Returns `task_files[0]` without multiple-match validation

The glob pattern `*{task_id}*.csv*` is broader than necessary. Recommended fix: `f"{task_id}.csv*"` to match the exact naming convention.

### DP-04 Silent Swallow Verification

- `data_worker.py:226-228`: `except SQLAlchemyError: logger.error(...)` without re-raise
- `data_worker.py:209-223`: Test mode uses caller-managed transaction (SAVEPOINT pattern)
- This could leave processing logs in inconsistent state during tests

### DP-05 String Conversion Verification

- `aggregation_service.py:83`: `dims = {col: str(row[col]) for col in groupby_cols}`
- Polars `to_dicts()` returns native Python types (int, float, str, bool) which JSON serialization handles correctly
- Converting to string causes lexicographic sorting issues for numeric/date dimensions

---

## Validation Outcome

| Category | Count |
|----------|-------|
| **Mandatory fixes validated** | 3 (DP-02, DP-07, DP-08) |
| **Advisory recommendations validated** | 5 (DP-01, DP-03, DP-04, DP-05, DP-06) |
| **Rejected findings** | 0 |
| **Merged findings** | 0 |
| **Cross-phase conflicts** | 0 |

All 8 audit findings are valid. The three mandatory fixes (DP-02, DP-07, DP-08) should be prioritized before production deployment.

---

## Actionable Recommendations

Exact code-level changes for each finding. Each recommendation includes the file path, before/after snippets, and rationale.

---

### DP-01: Remove dead `DataPipeline` class from `registry.py`

**File:** `src/mkobi/data/processing/registry.py`

**Rationale:** `DataPipeline` is never imported or called anywhere in the codebase. The active pipeline lives in `data_worker.py`. Keeping this class creates confusion and risks someone accidentally using it (it lacks transaction safety — each step commits independently via `log_service`).

**Action:** Delete the entire `DataPipeline` class (lines 33–221) and its associated imports (`tenacity`, `cast`, `ConnectionError`, `ProcessingLogRead`, `IProcessingConfigService`, `IProcessingLogService`, `apply_transformations`, `aggregate_data`, `StorageManager`). Keep the module docstring.

**Before:**
```python
"""Data processing pipeline orchestration.

Contains DataPipeline class that manages sequential
data transformation, aggregation, saving and status updates.
"""

import logging
import tenacity
from typing import Any, cast
from uuid import UUID

import polars as pl
from sqlalchemy import ConnectionError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.data.processing.transformations import (
    aggregate_data,
    apply_transformations,
)
from mkobi.data.storage.manager import StorageManager
from mkobi.interfaces.repository_interfaces import IGraphRepository
from mkobi.interfaces.service_interfaces import (
    IProcessingConfigService,
    IProcessingLogService,
)
from mkobi.models.enums import ProcessingStatus, UploadMode
from mkobi.models.processing_logs import ProcessingLogRead

logger = logging.getLogger(__name__)


class DataPipeline:
    """Data processing orchestration.
    ...  # (189 lines of dead code)
    ...
    @tenacity.retry(...)
    async def _save_with_retry(self, ...):
        ...
```

**After:**
```python
"""Data processing pipeline orchestration.

The authoritative pipeline implementation is in
src/mkobi/workers/data_worker.py (_process_csv_file_async).
"""
```

**Also update:** `src/mkobi/services/processing_log_service.py` line 51 — the docstring comment `"Called from DataPipeline at each processing stage."` should be changed to `"Called from data_worker at each processing stage."` since `DataPipeline` no longer exists.

---

### DP-02: APPEND mode doesn't clear stale filter values

**File:** `src/mkobi/workers/data_worker.py`

**Rationale:** SPEC.md states "Values are rebuilt on each upload (idempotent overwrite)." APPEND mode must also clear stale filter values before saving new ones, otherwise phantom filter options persist.

**Location 1 — Test mode path (line ~659):**

**Before:**
```python
            # In OVERWRITE mode, clear all existing filter values first
            # to avoid orphaned values from removed/renamed filters
            if mode == UploadMode.OVERWRITE:
                await filter_values_repo.clear_dashboard_values(dashboard_id, db_session)
```

**After:**
```python
            # Always clear existing filter values before saving new ones
            # to avoid orphaned values from removed/renamed filters
            # (SPEC: "Values are rebuilt on each upload")
            await filter_values_repo.clear_dashboard_values(dashboard_id, db_session)
```

**Location 2 — Production mode path (line ~730):**

**Before:**
```python
                    # In OVERWRITE mode, clear all existing filter values first
                    # to avoid orphaned values from removed/renamed filters
                    if mode == UploadMode.OVERWRITE:
                        await filter_values_repo.clear_dashboard_values(dashboard_id, session)
```

**After:**
```python
                    # Always clear existing filter values before saving new ones
                    # to avoid orphaned values from removed/renamed filters
                    # (SPEC: "Values are rebuilt on each upload")
                    await filter_values_repo.clear_dashboard_values(dashboard_id, session)
```

---

### DP-03: `find_task_file` glob too broad

**File:** `src/mkobi/services/file_processing.py` (line ~295)

**Rationale:** The file is stored as `{log.id}{file_ext}` (e.g., `550e8400-e29b-41d4-a716-446655440000.csv.gz`). The glob `*{task_id}*.csv*` matches any file containing the task_id substring. The exact pattern `{task_id}.csv*` is sufficient and safer.

**Before:**
```python
    task_files = list(upload_dir.glob(f"*{task_id}*.csv*"))

    if not task_files:
        raise ValueError(f"File for task {task_id} not found in temp directory")

    return str(task_files[0])
```

**After:**
```python
    task_files = list(upload_dir.glob(f"{task_id}.csv*"))

    if not task_files:
        raise ValueError(f"File for task {task_id} not found in temp directory")

    if len(task_files) > 1:
        raise ValueError(
            f"Multiple files found for task {task_id}: "
            f"{[f.name for f in task_files]}"
        )

    return str(task_files[0])
```

---

### DP-04: `_update_processing_log_status` silently swallows errors in test mode

**File:** `src/mkobi/workers/data_worker.py` (lines ~226–228)

**Rationale:** When `session is not None` (test mode), a `SQLAlchemyError` during the UPDATE is caught and logged but never re-raised. The caller's SAVEPOINT transaction continues as if the status update succeeded, leaving processing logs in an inconsistent state during tests. Re-raising after logging lets the caller handle the failure properly.

**Before:**
```python
    except SQLAlchemyError as e:
        logger.error("Failed to update processing log status: %s", e)
        # No rollback in test mode - caller (SAVEPOINT) manages transaction
```

**After:**
```python
    except SQLAlchemyError as e:
        logger.error("Failed to update processing log status: %s", e)
        raise
```

**Note:** The production path (line ~233) already creates its own session and is unaffected — the `SQLAlchemyError` there is also swallowed, but since the production path creates an independent session, the swallowed error only affects logging, not the transaction. The same re-raise pattern should be applied there for consistency:

```python
    except SQLAlchemyError as e:
        logger.error("Failed to update processing log status: %s", e)
        raise
```

---

### DP-05: `AggregationService` converts all dims to strings

**File:** `src/mkobi/services/aggregation_service.py` (line 83)

**Rationale:** `str(row[col])` converts native Polars types (int, float, bool, date) to strings. This causes lexicographic sorting for numeric dimensions ("9" > "10") and breaks date ordering. JSON serialization handles native Python types correctly.

**Before:**
```python
            for row in result.to_dicts():
                dims = {col: str(row[col]) for col in groupby_cols}
                metrics = {k: v for k, v in row.items() if k not in groupby_cols}
```

**After:**
```python
            for row in result.to_dicts():
                dims = {
                    col: _coerce_dim_value(row[col])
                    for col in groupby_cols
                }
                metrics = {k: v for k, v in row.items() if k not in groupby_cols}
```

Add the helper function at module level (after imports, before the class):

```python
def _coerce_dim_value(value: Any) -> str | int | float | bool:
    """Convert a Polars value to a JSON-safe native Python type.

    Preserves int, float, and bool as-is for correct sorting in the frontend.
    Converts date/datetime types to ISO format strings since JSON has no
    native date type.

    Args:
        value: Native Python value from Polars to_dicts().

    Returns:
        JSON-safe native Python type.
    """
    if value is None:
        return ""
    if isinstance(value, (int, float, bool)):
        return value
    # Handle datetime.date, datetime.datetime, and Polars date types
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
```

**Rationale for helper:** Using `hasattr(value, "isoformat")` avoids importing Polars types directly and correctly handles `datetime.date`, `datetime.datetime`, and any Polars temporal type that provides `.isoformat()`.

---

### DP-06: `_calculate_yoy` round(4) precision loss

**File:** `src/mkobi/data/processing/aggregate_transforms.py`

**Rationale:** Rounding to 4 decimal places during storage causes precision loss when downstream calculations aggregate YoY values across groups. Store full precision; round only at the presentation layer (frontend or API serialization).

**Location 1 — `_calculate_yoy` (line ~205):**

**Before:**
```python
        .otherwise(((pl.col(value_column) - prev_value_expr) / prev_value_expr * 100).round(4))
        .alias(alias)
```

**After:**
```python
        .otherwise((pl.col(value_column) - prev_value_expr) / prev_value_expr * 100)
        .alias(alias)
```

**Location 2 — `_calculate_share` with group_cols (line ~248):**

**Before:**
```python
            .otherwise(((pl.col(value_column) / pl.col("total") * 100)).round(4))
            .alias(alias)
```

**After:**
```python
            .otherwise((pl.col(value_column) / pl.col("total") * 100))
            .alias(alias)
```

**Location 3 — `_calculate_share` without group_cols (line ~257):**

**Before:**
```python
            result = df.with_columns(((pl.col(value_column) / total * 100).round(4)).alias(alias))
```

**After:**
```python
            result = df.with_columns((pl.col(value_column) / total * 100).alias(alias))
```

**Note:** If any downstream consumer relies on the 4-decimal precision (e.g., tests asserting exact float values), those assertions should be updated to use `pytest.approx` or the rounding should be applied at the API response serialization layer instead.

---

### DP-07: TaskQueue loses tasks on crash — lower timeout + startup check

**File:** `src/mkobi/workers/data_worker.py`

**Rationale:** The stale processing timeout defaults to 30 minutes. During this window, users see a permanently stuck "processing" task. Lowering the timeout and adding a startup check for orphaned UPLOADED logs provides faster failure detection.

**Change 1 — Lower default timeout (line ~28):**

**Before:**
```python
DEFAULT_STALE_PROCESSING_TIMEOUT_MINUTES = 30
```

**After:**
```python
DEFAULT_STALE_PROCESSING_TIMEOUT_MINUTES = 5
```

**Change 2 — Add startup check for orphaned UPLOADED logs.** Add a new function after `cleanup_stale_processing_logs`:

```python
async def mark_orphaned_uploaded_logs_failed(
    session: AsyncSession | None = None,
) -> int:
    """Mark UPLOADED logs with no running worker as FAILED.

    On startup, any log stuck in UPLOADED state means the worker
    crashed between enqueue and processing start. These should be
    marked FAILED immediately rather than waiting for the stale
    PROCESSING timeout.

    Args:
        session: Optional database session. If None, creates a new session.

    Returns:
        int: Number of entries marked as FAILED.
    """
    cutoff = datetime.now(UTC) - timedelta(minutes=1)

    if session is not None:  # Test mode
        stmt = (
            update(ProcessingLog)
            .where(
                ProcessingLog.status == ProcessingStatus.UPLOADED,
                ProcessingLog.started_at < cutoff,
            )
            .values(
                status=ProcessingStatus.FAILED,
                message="Worker restart: orphaned UPLOADED task marked as failed",
                finished_at=datetime.now(UTC),
            )
        )
        result = await session.execute(stmt)
        count = result.rowcount if result.rowcount is not None else 0
    else:  # Production mode
        async with get_session() as db:
            async with db.begin():
                stmt = (
                    update(ProcessingLog)
                    .where(
                        ProcessingLog.status == ProcessingStatus.UPLOADED,
                        ProcessingLog.started_at < cutoff,
                    )
                    .values(
                        status=ProcessingStatus.FAILED,
                        message="Worker restart: orphaned UPLOADED task marked as failed",
                        finished_at=datetime.now(UTC),
                    )
                )
                result = await db.execute(stmt)
                count = result.rowcount if result.rowcount is not None else 0

    if count > 0:
        logger.info(
            "Marked %d orphaned UPLOADED logs as FAILED on startup", count
        )
    return int(count)
```

**Change 3 — Wire into startup.** In the application startup event handler (where `start_stale_processing_cleanup_task` is called), add:

```python
# Mark orphaned UPLOADED logs from crashed workers
await mark_orphaned_uploaded_logs_failed()
```

---

### DP-08: Error path status update rolls back — use independent session

**File:** `src/mkobi/workers/data_worker.py`

**Rationale:** In the production error path, `_update_processing_log_status` is called with `session=session` inside the `async with session.begin()` block. When the exception is re-raised, the context manager rolls back the entire transaction — including the FAILED status update. The fix is to use an independent session for the status update so it commits immediately, outside the rolled-back transaction.

**Location — Production error path (lines ~520–551):**

**Before:**
```python
    else:
        # Production mode - create new session with single transaction
        async with get_session() as session:
            async with session.begin():
                try:
                    return await _run_with_transaction(session)
                except Exception as e:
                    error_msg = str(e)
                    error_code = _map_processing_error_to_code(e)
                    logger.exception("Processing failed: task_id=%s, error=%s, code=%s", task_id, error_msg, error_code)

                    # Clean up temp file on error
                    if file_path.exists():
                        try:
                            await asyncio.to_thread(file_path.unlink)
                        except Exception:
                            logger.warning(
                                "Failed to clean up temp file: %s",
                                file_path,
                                exc_info=True,
                            )

                    # Update status to failed within the same transaction
                    await _update_processing_log_status(
                        task_id=task_id,
                        status=ProcessingStatus.FAILED,
                        message=f"Processing failed: {error_msg}",
                        finished_at=datetime.now(UTC),
                        session=session,
                        error_code=error_code,
                    )
                    raise
```

**After:**
```python
    else:
        # Production mode - create new session with single transaction
        async with get_session() as session:
            async with session.begin():
                try:
                    return await _run_with_transaction(session)
                except Exception as e:
                    error_msg = str(e)
                    error_code = _map_processing_error_to_code(e)
                    logger.exception("Processing failed: task_id=%s, error=%s, code=%s", task_id, error_msg, error_code)

                    # Clean up temp file on error
                    if file_path.exists():
                        try:
                            await asyncio.to_thread(file_path.unlink)
                        except Exception:
                            logger.warning(
                                "Failed to clean up temp file: %s",
                                file_path,
                                exc_info=True,
                            )
                    raise  # Re-raise BEFORE the rollback so the transaction is aborted

        # Update status to FAILED using an INDEPENDENT session outside the
        # rolled-back transaction. This ensures the failure record persists.
        try:
            await _update_processing_log_status(
                task_id=task_id,
                status=ProcessingStatus.FAILED,
                message=f"Processing failed: {error_msg}",
                finished_at=datetime.now(UTC),
                error_code=error_code,
            )
        except Exception as status_err:
            logger.exception(
                "Failed to update processing log status to FAILED: "
                "task_id=%s, error=%s",
                task_id,
                status_err,
            )
```

**Key changes:**
1. The `raise` now happens **inside** the `async with session.begin()` block (before the rollback), preserving the original error propagation behavior.
2. The `_update_processing_log_status` call moves **outside** the transaction block, using a new independent session (the `else` branch of `_update_processing_log_status` creates its own session via `get_session()`).
3. The status update is wrapped in its own try/except so a DB connectivity failure during status update doesn't mask the original processing error.

**Note on variable scope:** `error_msg` and `error_code` are defined inside the `except` block. To make them available after the `async with` block, capture them before the `raise`:

```python
                except Exception as e:
                    error_msg = str(e)
                    error_code = _map_processing_error_to_code(e)
                    logger.exception(...)
                    # ... cleanup ...
                    # Store error info before re-raise
                    _error_msg = error_msg
                    _error_code = error_code
                    raise
            else:
                return  # success path

        # After the async with block, use captured error info
        try:
            await _update_processing_log_status(
                task_id=task_id,
                status=ProcessingStatus.FAILED,
                message=f"Processing failed: {_error_msg}",
                finished_at=datetime.now(UTC),
                error_code=_error_code,
            )
        except Exception as status_err:
            logger.exception(...)
```

However, since Python `except` block variables are accessible after the `try/except` (they are not scoped to the block), the simpler approach works — `error_msg` and `error_code` remain in scope after the `async with` block ends. The final code:

```python
    else:
        # Production mode - create new session with single transaction
        async with get_session() as session:
            async with session.begin():
                try:
                    return await _run_with_transaction(session)
                except Exception as e:
                    error_msg = str(e)
                    error_code = _map_processing_error_to_code(e)
                    logger.exception("Processing failed: task_id=%s, error=%s, code=%s", task_id, error_msg, error_code)

                    if file_path.exists():
                        try:
                            await asyncio.to_thread(file_path.unlink)
                        except Exception:
                            logger.warning(
                                "Failed to clean up temp file: %s",
                                file_path,
                                exc_info=True,
                            )
                    raise

        # Use independent session for status update (outside rolled-back transaction)
        try:
            await _update_processing_log_status(
                task_id=task_id,
                status=ProcessingStatus.FAILED,
                message=f"Processing failed: {error_msg}",
                finished_at=datetime.now(UTC),
                error_code=error_code,
            )
        except Exception as status_err:
            logger.exception(
                "Failed to update processing log status to FAILED: "
                "task_id=%s, error=%s",
                task_id,
                status_err,
            )
```

---

## Implementation Priority

| Priority | Finding | Effort | Risk |
|----------|---------|--------|------|
| **P0** | DP-08: Independent session for FAILED status | Small | CRITICAL — no failure records without this |
| **P1** | DP-02: Clear filter values in APPEND mode | Trivial | HIGH — data drift in production |
| **P1** | DP-07: Lower timeout + orphaned UPLOADED check | Small | HIGH — user-visible stuck tasks |
| **P2** | DP-01: Remove dead DataPipeline | Trivial | MEDIUM — confusion/maintenance debt |
| **P2** | DP-03: Tighten glob pattern | Trivial | MEDIUM — file collision risk |
| **P2** | DP-04: Re-raise in test mode | Trivial | LOW — test reliability |
| **P3** | DP-05: Preserve native dim types | Small | MEDIUM — sorting/ordering bugs |
| **P3** | DP-06: Remove round(4) from storage | Small | LOW — precision loss |