# Task Queue Migration Plan: In-Memory to Redis/RQ

## Current State

The `TaskQueue` class in `src/mkobi/core/task_queue.py` uses `asyncio.Queue` for in-memory task queuing. This is an MVP implementation designed for simplicity and development convenience.

Key characteristics:
- Uses `asyncio.Queue` for task storage (in-memory only)
- Status tracking via dictionaries (`_statuses`, `_results`, `_errors`)
- Global `default_queue` instance for backward compatibility
- `enqueue_job()` function provides compatibility layer for job enqueueing
- `get_task_queue()` returns the default queue instance

```python
# Current implementation pattern
default_queue = TaskQueue()

async def enqueue_job(func, *args, **kwargs) -> str | None:
    return await default_queue.enqueue(func, *args, **kwargs)

def get_task_queue() -> TaskQueue:
    return default_queue
```

## Limitations

### Task Loss on Restart
All queued tasks are stored in memory. Application restart or crash causes complete task loss.

### No Persistence
Task status, results, and errors are not persisted. Historical task data is unavailable after restart.

### No Horizontal Scaling
In-memory queue cannot be shared across multiple application instances. Each instance has isolated queue state.

### No Retry on Crash
If the worker crashes during task execution, the task is lost. No automatic retry mechanism exists.

### No Monitoring/Visibility
Limited ability to inspect queue depth, pending tasks, or worker health.

## Target Architecture (Redis/RQ)

Redis Queue (RQ) provides:
- Persistent task storage in Redis
- Multiple worker processes support
- Built-in retry mechanisms
- Web monitoring UI
- Task timeouts and failure handling

### Components After Migration

1. **Redis**: Message broker for task queue
2. **RQ Queue**: Python library for Redis-backed queuing
3. **RQ Worker**: Separate process that processes queued jobs
4. **Processing Logs**: Integration with existing `processing_logs` table for result tracking

## Migration Steps

### Step 1: Install Dependencies

```bash
uv add redis rq
```

### Step 2: Create Redis Connection Configuration

Create `src/mkobi/core/redis_client.py`:

```python
from redis import Redis

redis_client = Redis(host="localhost", port=6379, db=0)
```

### Step 3: Replace TaskQueue.enqueue

Replace `TaskQueue.enqueue()` method to use RQ:

```python
from rq import Queue

task_queue = Queue(connection=redis_client)

async def enqueue(self, task_func, *args, **kwargs) -> str:
    job = task_queue.enqueue(task_func, *args, **kwargs)
    return job.id
```

### Step 4: Replace TaskQueue.process_next

RQ uses separate worker processes. Create a worker entry point:

```python
# src/mkobi/workers/rq_worker.py
from rq import Worker, Queue, Connection

if __name__ == "__main__":
    with Connection(redis_client):
        worker = Worker(["default"])
        worker.work()
```

### Step 5: Replace Status/Result/Error Methods

Use RQ's job API:

```python
from rq.job import Job

async def get_status(self, task_id: str) -> ProcessingStatus:
    job = Job.fetch(task_id, connection=redis_client)
    return processing_status_from_rq(job.status)

async def get_result(self, task_id: str) -> Any:
    job = Job.fetch(task_id, connection=redis_client)
    return job.result

async def get_error(self, task_id: str) -> str | None:
    job = Job.fetch(task_id, connection=redis_client)
    return str(job.exc_info) if job.exc_info else None
```

### Step 6: Update enqueue_job Compatibility Function

```python
from rq import Queue

task_queue = Queue(connection=redis_client)

async def enqueue_job(func, *args, **kwargs) -> str | None:
    try:
        job = task_queue.enqueue(func, *args, **kwargs)
        return job.id
    except Exception as e:
        logger.error("Failed to enqueue job: %s", e)
        return None
```

### Step 7: Update Worker Code

Background tasks that currently use `default_queue.process_next()` should be replaced with RQ workers running as separate processes:

```bash
# Run RQ worker
uv run python -m mkobi.workers.rq_worker
```

### Step 8: Update Configuration

Add Redis configuration to environment:

```yaml
# settings/app.yaml or environment variables
REDIS_HOST: localhost
REDIS_PORT: 6379
REDIS_DB: 0
```

## Rollback Plan

If Redis/RQ is unavailable or issues arise:

1. Revert code changes to use in-memory `TaskQueue`
2. Restore original `task_queue.py` implementation
3. Restart application with in-memory queue

The original implementation files should be kept in version control for quick rollback.

## Testing Strategy

1. **Unit Tests**: Test RQ integration with mock Redis
2. **Integration Tests**: Verify task execution with real Redis instance
3. **Migration Verification**: Confirm task status/results match expected values
4. **Rollback Testing**: Verify in-memory queue fallback works correctly

## References

- `TaskQueue` class: `src/mkobi/core/task_queue.py`
- enqueue function: `enqueue_job()` in the same file
- Queue getter: `get_task_queue()` in the same file
- Default queue instance: `default_queue` global variable