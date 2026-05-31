---
name: 01-backend
description: Backend Architecture Audit Findings
status: complete
validated: no
---

# Phase 01 Audit Findings — Backend Architecture

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### BE-001: Sync RateLimiter in async DataService breaks event loop

| Field | Value |
|-------|-------|
| **ID** | BE-001 |
| **Severity** | CRITICAL |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/services/data_service.py |
| **Classification** | mandatory |

**Description:** DataService.__init__ (line 54) instantiates and uses the synchronous `RateLimiter` class instead of `AsyncRateLimiter`. This violates async correctness as the synchronous RateLimiter uses blocking redis.Redis calls inside an async context, which will block the event loop and degrade performance under load.

**Evidence:** 
```python
# src/mkobi/services/data_service.py:54
self._upload_rate_limiter = RateLimiter(
    get_redis_client(),
    fail_closed=config.rate_limiter_fail_closed,
)
```
The synchronous RateLimiter uses `self._redis.get()`, `self._redis.pipeline()`, and blocking Redis operations. In an async application, this will block the event loop. The async equivalent `AsyncRateLimiter` exists and is used elsewhere (e.g., upload.py:122).

**Recommendation:** Replace `RateLimiter` with `AsyncRateLimiter` in DataService, passing `get_async_redis_client()` instead of `get_redis_client()`. Or remove the rate limiter from DataService if it's not needed there, since rate limiting is already applied at the route level.

---

### BE-002: Unnecessary Rate Limiter in Process endpoint

| Field | Value |
|-------|-------|
| **ID** | BE-002 |
| **Severity** | HIGH |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/api/routes/upload.py |
| **Classification** | advisory |

**Description:** The `/upload/{dashboard_id}/process` endpoint (line 220-271) applies rate limiting (lines 122-138) but this endpoint is for triggering processing after file upload, not for the critical path of uploads. The permission check already protects this endpoint (EditorUser dependency). Rate limiting here adds complexity without proportional security benefit.

**Evidence:** 
```python
# src/mkobi/api/routes/upload.py:122-138
rate_limiter = AsyncRateLimiter(
    redis_client.get_async_redis_client(),
    fail_closed=config.rate_limiter_fail_closed,
)
if not await rate_limiter.check_rate_limit(
    f"upload:{current_user.id}",
    max_attempts=10,
    ttl=3600,
):
```

**Recommendation:** Consider removing rate limiting from the process endpoint or reducing its scope to avoid unnecessary Redis calls for internal operations.

---

### BE-003: ProcessingStatus enum has redundant SUCCESS and COMPLETED values

| Field | Value |
|-------|-------|
| **ID** | BE-003 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/models/enums.py |
| **Classification** | advisory |

**Description:** `ProcessingStatus` enum defines both `SUCCESS` (line 64) and `COMPLETED` (line 65) which represent the same final successful state. This creates confusion and potential for inconsistent state transitions.

**Evidence:** 
```python
# src/mkobi/models/enums.py:60-66
class ProcessingStatus(StrEnum):
    """Data processing statuses."""
    STARTED = "started"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    SUCCESS = "success"      # Final success state
    FAILED = "failed"
    COMPLETED = "completed"  # Also final success state - redundant
```

**Recommendation:** Consolidate to a single success state. Either keep `SUCCESS` and remove `COMPLETED`, or keep `COMPLETED` and update references. Check all usages in data_worker.py and other modules.

---

### BE-004: In-memory TaskQueue not integrated with background workers

| Field | Value |
|-------|-------|
| **ID** | BE-004 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/core/task_queue.py, src/mkobi/services/file_processing.py |
| **Classification** | advisory |

**Description:** `TaskQueue` class (lines 18-149) provides in-memory task queue using asyncio.Queue but is not actually used for background processing. The `enqueue_job` function (line 125) enqueues tasks but there's no persistent consumer running these tasks. Instead, `process_csv_background_sync` (data_worker.py:456) is called which runs `asyncio.run()` to execute async code synchronously in an RQ worker context.

**Evidence:** 
```python
# src/mkobi/core/task_queue.py:27
self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

# src/mkobi/services/file_processing.py:190-197
await enqueue_job(
    process_csv_background,
    ...
)
# But process_csv_background_sync just runs asyncio.run() for RQ
```

**Recommendation:** Either implement a proper background task consumer that processes the asyncio.Queue, or remove the TaskQueue module as dead code. The current implementation creates a false sense of async job management.

---

### BE-005: Global graph endpoints lack dashboard access verification

| Field | Value |
|-------|-------|
| **ID** | BE-005 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/api/routes/graphs.py |
| **Classification** | mandatory |

**Description:** Global graph endpoints (`GET /graphs/`, `GET /graphs/{graph_id}`, `PUT /graphs/{graph_id}`, `DELETE /graphs/{graph_id}`) in graphs.py only require `CurrentUser` (authenticated user) but do not verify that the user has access to the dashboard that owns the graph. Per the audit checklist for Authorization Granularity, permissions should be checked at the resource level.

**Evidence:** 
```python
# src/mkobi/api/routes/graphs.py:105-108
async def get_graphs_endpoint(
    current_user: CurrentUser,  # Only checks authentication
    db: AsyncSession = Depends(get_db),
) -> list[GraphRead]:
    # No dashboard access check - returns ALL graphs
```

While `dashboards_graphs.py` (line 124) properly checks access with `require_dashboard_read_access`, the global `/graphs` endpoints bypass this check.

**Recommendation:** Add dashboard access verification to graph endpoints. Either require dashboard_id parameter and check access, or fetch the graph's dashboard_id and verify access using `check_dashboard_access`.

---

### BE-006: DataService rate limiter initialized but never used

| Field | Value |
|-------|-------|
| **ID** | BE-006 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/services/data_service.py |
| **Classification** | advisory |

**Description:** DataService.__init__ sets up `_upload_rate_limiter` (lines 54-71) but the `process_upload` method does not call it. Rate limiting in DataService is dead code - it's configured but never enforced.

**Evidence:** 
```python
# src/mkobi/services/data_service.py:54-71
self._upload_rate_limiter = RateLimiter(...)
self._rate_limiter_healthy = True
# ... initialization logging

# But process_upload (line 76) never calls:
# self._upload_rate_limiter.check_rate_limit(...)
```

**Recommendation:** Either remove the unused rate limiter setup from DataService or integrate it into the `process_upload` method.

---

### BE-007: Missing explicit transaction rollback on error in process_upload_with_session

| Field | Value |
|-------|-------|
| **ID** | BE-007 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/services/file_processing.py |
| **Classification** | advisory |

**Description:** The `process_upload_with_session` function (line 114) performs database operations (create log, update status) but if an exception occurs between `db.commit()` (line 185) and the function returning, there's no explicit rollback. The function relies on FastAPI's exception handling which may result in inconsistent state.

**Evidence:** 
```python
# src/mkobi/services/file_processing.py:161-185
log = await log_repo.create_log(...)
await db.flush()
# ... file move ...
await log_repo.update_status(...)
await db.commit()  # Commit happens before potential errors

# If file_path.replace or subsequent operations fail:
# - Log entry exists with UPLOADED status
# - But file may not be in final location
# - No rollback to clean up the log
```

**Recommendation:** Wrap critical operations in try/except with explicit `db.rollback()` or use `async with db.begin()` for implicit transaction management.

---

### BE-008: Exception handlers in app.py don't use standard error format

| Field | Value |
|-------|-------|
| **ID** | BE-008 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/app.py |
| **Classification** | advisory |

**Description:** The HTTP exception handlers in create_app (lines 245-284) return error responses without the `error_code` field that custom `AppException` provides, creating inconsistency in error response format.

**Evidence:** 
```python
# src/mkobi/app.py:250-256
return JSONResponse(
    status_code=exc.status_code,
    content={
        "detail": exc.detail,
        "status_code": exc.status_code,
    },
)
# Missing: "error_code" field
```

**Recommendation:** Align error response format across all handlers to include `error_code` for consistency with custom exceptions.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 1 |
| HIGH | 1 |
| MEDIUM | 3 |
| LOW | 2 |

**Total Findings:** 7

---

## Mandatory Fixes

- BE-001: Sync RateLimiter in async DataService breaks event loop
- BE-005: Global graph endpoints lack dashboard access verification

---

## Advisory Recommendations

- BE-002: Unnecessary Rate Limiter in Process endpoint
- BE-003: ProcessingStatus enum has redundant SUCCESS and COMPLETED values
- BE-004: In-memory TaskQueue not integrated with background workers
- BE-006: DataService rate limiter initialized but never used
- BE-007: Missing explicit transaction rollback on error in process_upload_with_session
- BE-008: Exception handlers in app.py don't use standard error format