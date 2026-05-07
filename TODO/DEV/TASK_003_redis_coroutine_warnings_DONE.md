---
## TASK: Fix Redis coroutine 'get_async_redis_client' never awaited warnings
---

### PROBLEM

Runtime warnings about unawaited coroutines during test execution:

```
RuntimeWarning: coroutine 'get_async_redis_client' was never awaited
```

### ROOT CAUSE

The `get_redis_client` function in `mkobi/core/redis_client.py` appears to be an async function that's being called without `await` in some contexts, or there's a mismatch between sync and async Redis client usage.

### FILES TO CHECK

- `src/mkobi/core/redis_client.py`
- `src/mkobi/services/data_service.py` (line 45: `self._upload_rate_limiter = RateLimiter(get_redis_client())`)

### SOLUTION

1. Check if `get_redis_client()` is async - if so, it needs to be awaited or made sync
2. If the function returns a coroutine, either:
   - Make it a sync function that returns a sync Redis client
   - Properly await it in async contexts
   - Use `asyncio.get_event_loop().run_until_complete()` in sync contexts

### VERIFICATION

1. Run `uv run pytest tests/`
2. Check that RuntimeWarning messages are no longer present

### PRIORITY

Medium - unawaited coroutines can lead to unexpected behavior

### STATUS

- [x] Issue identified
- [x] Fix applied
- [x] Warnings resolved

---
