# Task Queue Migration Plan: In-Memory to Redis/RQ

## Current State

The `TaskQueue` class in `src/mkobi/core/task_queue.py` uses `asyncio.Queue` for in-memory task queuing. This is an MVP implementation designed for simplicity during initial development.

### Architecture Overview

```
FastAPI endpoint → enqueue_job() → default_queue (TaskQueue) → process_next() → task func
```

### Key Components

| Component | Location | Role |
|---|---|---|
| `TaskQueue` class | `src/mkobi/core/task_queue.py:18` | In-memory queue with status/result/error tracking |
| `default_queue` | `src/mkobi/core/task_queue.py:122` | Global singleton `TaskQueue` instance |
| `enqueue_job()` | `src/mkobi/core/task_queue.py:125` | Compatibility wrapper around `default_queue.enqueue()` |
| `get_task_queue()` | `src/mkobi/core/task_queue.py:147` | Returns the `default_queue` singleton |

### Internal Storage

```python
self._queue: asyncio.Queue[dict[str, Any]]       # pending tasks
self._statuses: dict[str, ProcessingStatus]        # task_id → status
self._results: dict[str, Any]                     # task_id → result
self._errors: dict[str, str | None]                # task_id → error message
```

### Task Lifecycle

1. `enqueue()` — generates UUID, sets status to `ProcessingStatus.STARTED`, pushes to `asyncio.Queue`
2. `process_next()` — pops from queue, sets status to `ProcessingStatus.PROCESSING`, executes task function
3. On success — status set to `ProcessingStatus.SUCCESS`, result stored in `_results`
4. On failure — status set to `ProcessingStatus.FAILED`, error stored in `_errors`

### Call Sites

`enqueue_job()` is called from `src/mkobi/services/data_service.py` in two places:

- **Line 210** — after file upload, enqueues `process_csv_background` with file path, dashboard ID, task ID, log ID, and mode
- **Line 504** — on manual processing trigger, enqueues the same function with similar parameters

### Worker Code

The actual task function lives in `src/mkobi/workers/data_worker.py`:

- `process_csv_background()` (line 272) — async entry point, called by the in-memory queue
- `process_csv_background_sync()` (line 310) — sync wrapper using `asyncio.run()`, designed for RQ worker compatibility

### MVP Rationale

The in-memory queue was chosen for the MVP to avoid external dependencies (Redis) and keep the deployment simple. The module docstring and inline comments explicitly note this is temporary:

> "For production, replace with Redis/RabbitMQ and integrate with processing_logs."

## Limitations

### 1. Task Loss on Restart

All queued but unprocessed tasks reside in `asyncio.Queue`, which is a pure in-memory data structure. Any application restart, crash, or graceful shutdown causes **complete loss of pending tasks**. Tasks that have not yet been dequeued by `process_next()` are irrecoverably lost.

### 2. No Persistence

Task status (`_statuses`), results (`_results`), and errors (`_errors`) are stored in Python dictionaries in memory. After a restart:

- No historical task data is available
- Clients polling `get_status()` will receive `ProcessingStatus.FAILED` for previously enqueued tasks
- No audit trail exists for completed or failed tasks (beyond the separate `processing_logs` table)

### 3. No Horizontal Scaling

Each application instance has its own isolated `default_queue`. It is impossible to:

- Share a queue across multiple FastAPI workers (e.g., multiple uvicorn workers)
- Run a separate worker process that consumes tasks from the same queue
- Scale workers independently of the API server

### 4. No Retry on Crash

If the application crashes while `process_next()` is executing a task function (between `self._queue.get()` and `self._queue.task_done()`), the task is lost. There is no dead-letter queue, no retry counter, and no mechanism to re-enqueue failed tasks.

### 5. Single-Threaded Processing

`process_next()` processes one task at a time. There is no concurrency control beyond the single async loop. Long-running CSV processing blocks all subsequent tasks.

### 6. No Monitoring or Visibility

There is no way to inspect:

- Queue depth (number of pending tasks)
- Worker health or liveness
- Task throughput or processing times
- Failed task history

## Target Architecture (Redis/RQ)

Redis Queue (RQ) provides a persistent, Redis-backed task queue designed for exactly this use case.

### Architecture After Migration

```
FastAPI endpoint → enqueue_job() → rq.Queue (Redis) → RQ Worker (separate process) → task func
                                                                        ↓
                                                           rq.Job (status/result/error in Redis)
```

### Components

| Component | Technology | Role |
|---|---|---|
| **Redis** | Redis server | Persistent message broker for task queue |
| **rq.Queue** | `rq` Python library | Queue abstraction over Redis lists |
| **rq.Worker** | `rq` CLI or programmatic | Separate process that dequeues and executes jobs |
| **rq.Job** | `rq.job.Job` | Job handle for status, result, and error retrieval |

### ProcessingStatus → RQ Status Mapping

| `ProcessingStatus` (current) | RQ Job Status | Meaning |
|---|---|---|
| `STARTED` | `queued` | Job is in the queue, waiting for a worker |
| `PROCESSING` | `started` | Worker has picked up the job |
| `SUCCESS` | `finished` | Job completed successfully |
| `FAILED` | `failed` | Job raised an exception |
| `UPLOADED` | N/A (application-level) | File uploaded, before enqueue — not an RQ concern |

### Benefits After Migration

- **Persistence**: Tasks survive application restarts
- **Horizontal scaling**: Multiple workers can consume from the same queue
- **Retry**: RQ supports built-in retry with configurable attempts and intervals
- **Monitoring**: RQ provides `rq info`, `rq-dashboard`, and programmatic job inspection
- **Separation of concerns**: Worker processes run independently from the API server

## Migration Steps

### Step 1: Install Dependencies

```bash
uv add redis rq
```

### Step 2: Create Redis Connection Configuration

Create `src/mkobi/core/redis_client.py`:

```python
"""Redis connection configuration."""

import os

from redis import Redis

redis_client = Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=int(os.getenv("REDIS_DB", "0")),
)
```

Add to environment configuration:

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### Step 3: Replace TaskQueue.enqueue

Replace the `enqueue()` method to use RQ instead of `asyncio.Queue`:

```python
from rq import Queue as RQQueue

rq_queue = RQQueue("default", connection=redis_client)

async def enqueue(self, task_func: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
    job = rq_queue.enqueue(task_func, *args, **kwargs)
    return job.id
```

Note: RQ requires task functions to be importable by the worker process. The sync wrapper `process_csv_background_sync` in `src/mkobi/workers/data_worker.py:310` is already prepared for this.

### Step 4: Replace TaskQueue.process_next

RQ uses separate worker processes instead of in-process `process_next()`. Create a worker entry point:

```python
# src/mkobi/workers/rq_worker.py
"""RQ worker entry point."""

from rq import Worker, Queue, Connection

from mkobi.core.redis_client import redis_client

if __name__ == "__main__":
    with Connection(redis_client):
        worker = Worker(["default"])
        worker.work()
```

Run the worker:

```bash
uv run python -m mkobi.workers.rq_worker
```

The `process_next()` method can be removed or kept as a no-op for backward compatibility during the transition period.

### Step 5: Replace Status/Result/Error Methods

Use RQ's `Job.fetch()` API:

```python
from rq.job import Job

async def get_status(self, task_id: str) -> ProcessingStatus:
    try:
        job = Job.fetch(task_id, connection=redis_client)
        rq_status_to_processing_status = {
            "queued": ProcessingStatus.STARTED,
            "started": ProcessingStatus.PROCESSING,
            "finished": ProcessingStatus.SUCCESS,
            "failed": ProcessingStatus.FAILED,
            "deferred": ProcessingStatus.STARTED,
            "scheduled": ProcessingStatus.STARTED,
            "canceled": ProcessingStatus.FAILED,
        }
        return rq_status_to_processing_status.get(job.get_status(), ProcessingStatus.FAILED)
    except Exception:
        logger.warning("Task not found: task_id=%s", task_id)
        return ProcessingStatus.FAILED

async def get_result(self, task_id: str) -> Any:
    try:
        job = Job.fetch(task_id, connection=redis_client)
        return job.result
    except Exception:
        return None

async def get_error(self, task_id: str) -> str | None:
    try:
        job = Job.fetch(task_id, connection=redis_client)
        return str(job.exc_info) if job.exc_info else None
    except Exception:
        return None
```

### Step 6: Update enqueue_job Compatibility Function

Update `enqueue_job()` in `src/mkobi/core/task_queue.py:125` to use RQ:

```python
async def enqueue_job(
    func: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> str | None:
    try:
        job = rq_queue.enqueue(func, *args, **kwargs)
        logger.info("Job enqueued: job_id=%s", job.id)
        return job.id
    except Exception as e:
        logger.error("Failed to enqueue job: %s", e)
        return None
```

### Step 7: Update Call Sites in data_service.py

The call sites in `src/mkobi/services/data_service.py` (lines 210 and 504) call `enqueue_job()` with `process_csv_background` as the task function. Since RQ requires sync-callable functions, these calls should be updated to enqueue `process_csv_background_sync` instead:

```python
# Before (line ~210):
await enqueue_job(
    process_csv_background,  # async function — not compatible with RQ
    ...
)

# After:
enqueue_job(  # no longer needs await — RQ enqueue is sync
    process_csv_background_sync,  # sync wrapper — RQ compatible
    ...
)
```

Note: `enqueue_job()` becomes synchronous after migration since `rq_queue.enqueue()` is a blocking call. The `await` should be removed from all call sites.

### Step 8: Update Docker and Deployment Configuration

Add Redis service to `docker-compose.yml`:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

Add RQ worker service:

```yaml
services:
  rq-worker:
    build: .
    command: uv run python -m mkobi.workers.rq_worker
    depends_on:
      - redis
      - db
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
```

### Step 9: Update get_task_queue

The `get_task_queue()` function at `src/mkobi/core/task_queue.py:147` returns the `default_queue` singleton. After migration, it should return an object that maintains the same interface (enqueue, get_status, get_result, get_error) but delegates to RQ. This preserves backward compatibility for any code that calls `get_task_queue()`.

## Rollback Plan

If Redis/RQ causes issues in production:

1. **Immediate rollback**: Revert `src/mkobi/core/task_queue.py` to the original `asyncio.Queue` implementation (preserved in git history)
2. **Revert call sites**: Restore `await enqueue_job(process_csv_background, ...)` in `data_service.py`
3. **Remove dependencies**: `uv remove redis rq` (optional — harmless to keep installed)
4. **Restart**: Application returns to in-memory queue behavior

### Rollback Feasibility

- The original `TaskQueue` implementation is pure Python with no external dependencies
- The `process_csv_background` async function remains unchanged and works with both queue implementations
- No database schema changes are involved
- Rollback is a simple code revert and restart — no migration scripts needed

### Fallback: Dual-Mode Operation

For zero-downtime migration, consider a dual-mode approach:

```python
# src/mkobi/core/task_queue.py
USE_REDIS = os.getenv("USE_REDIS_QUEUE", "false").lower() == "true"

if USE_REDIS:
    from mkobi.core.redis_client import redis_client
    rq_queue = RQQueue("default", connection=redis_client)
else:
    default_queue = TaskQueue()
```

This allows toggling between in-memory and Redis queues via environment variable without code changes.

## Testing Strategy

### 1. Unit Tests

- Mock `redis.Redis` using `fakeredis` library to test RQ integration without a real Redis server
- Test `enqueue()` returns a valid job ID
- Test `get_status()` correctly maps RQ statuses to `ProcessingStatus` values
- Test `get_result()` and `get_error()` retrieve data from Redis
- Test `enqueue_job()` returns `None` on Redis connection failure

### 2. Integration Tests

- Start a real Redis instance (Docker) in the test environment
- Enqueue a real job and verify it appears in `rq info`
- Start an RQ worker and verify job execution
- Verify task status transitions: `queued` → `started` → `finished`/`failed`
- Verify result and error retrieval after job completion

### 3. Migration Verification

- Run the existing test suite to ensure no regressions in `data_service.py` call sites
- Verify `process_csv_background_sync` produces identical results to `process_csv_background`
- Verify `processing_logs` table is updated correctly after RQ worker execution
- Verify temporary file cleanup works in the RQ worker context

### 4. Rollback Testing

- Verify the application starts correctly with `USE_REDIS_QUEUE=false`
- Verify in-memory queue processes tasks correctly after rollback
- Verify no Redis connection errors appear in logs when Redis is unavailable

### 5. Load Testing

- Enqueue multiple jobs concurrently and verify all are processed
- Verify no task loss during worker restart
- Verify queue depth monitoring works correctly

## References

- `TaskQueue` class: `src/mkobi/core/task_queue.py:18`
- `default_queue` global: `src/mkobi/core/task_queue.py:122`
- `enqueue_job()` function: `src/mkobi/core/task_queue.py:125`
- `get_task_queue()` function: `src/mkobi/core/task_queue.py:147`
- `ProcessingStatus` enum: `src/mkobi/models/enums.py:58`
- `process_csv_background()` (async worker): `src/mkobi/workers/data_worker.py:272`
- `process_csv_background_sync()` (sync RQ wrapper): `src/mkobi/workers/data_worker.py:310`
- Upload call site: `src/mkobi/services/data_service.py:210`
- Manual trigger call site: `src/mkobi/services/data_service.py:504`
- RQ documentation: https://python-rq.org/docs/
