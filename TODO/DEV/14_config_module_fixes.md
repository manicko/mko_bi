---
## CONFIG MODULE FIXES
---

### TASK: Fix Configuration Module Issues

FILE: `src/mkobi/config.py`

GOAL: Fix bugs and improve configuration module

ISSUE DESCRIPTION:

1. **Bug in `_set_nested_value` function** (lines 70-71):
   ```python
   def __repr__(self) -> str:
       return "SecretsFileSource()"
   ```
   This method is defined INSIDE the `_set_nested_value` function but at wrong indentation level. It appears to be a method of `SecretsFileSource` that was incorrectly placed.

   **Actual issue**: Looking at the code structure:
   ```python
   def _set_nested_value(data: dict[str, Any], key: str, value: Any) -> None:
       """Set a nested value..."""
       # ... function body ...
       
       def __repr__(self) -> str:  # WRONG: This is inside _set_nested_value
           return "SecretsFileSource()"  # But uses self - it's a method, not function
   ```
   
   This is a BUG - `__repr__` is defined inside a regular function but uses `self`.

2. **Unused imports**:
   - `from pydantic.fields import FieldInfo` (line 12) - used but could check
   - `import redis` (line 5) - used in functions

3. **`get_redis_client` and `get_async_redis_client` are in `config.py`**:
   - Should be in a separate module (e.g., `src/mkobi/core/redis_client.py`)
   - `config.py` should only handle configuration

4. **SecretsFileSource has misplaced `__repr__`**:
   - The `__repr__` method at line 70-71 appears to be inside `_set_nested_value`
   - It should be a method of `SecretsFileSource` class

IMPACT:
- Bug in config module (nested function with `self`)
- Poor separation of concerns
- Hard to maintain

FILES TO FIX:
- `src/mkobi/config.py` - Fix `_set_nested_value` function, move Redis clients
- Create `src/mkobi/core/redis_client.py` - For Redis client factories

IMPLEMENTATION:

1. **Fix `_set_nested_value` function** - Remove the misplaced `__repr__`:
   ```python
   def _set_nested_value(data: dict[str, Any], key: str, value: Any) -> None:
       """Set a nested value in a dict using __ as separator."""
       parts = key.lower().split("__")
       current = data
       for part in parts[:-1]:
           if part not in current:
               current[part] = {}
           current = current[part]
       current[parts[-1]] = value


   # REMOVE the __repr__ from here - it doesn't belong
   ```

2. **Move Redis clients to separate module**:
   ```python
   # src/mkobi/core/redis_client.py
   import redis
   import redis.asyncio as aioredis
   from mkobi.config import get_config


   def get_redis_client() -> redis.Redis:
       config = get_config()
       return redis.Redis(...)


   async def get_async_redis_client() -> aioredis.Redis:
       config = get_config()
       return aioredis.Redis(...)
   ```

3. **Clean up config.py**:
   - Remove Redis client functions
   - Import from new module where needed

EXAMPLE FIX for `config.py`:
```python
# REMOVE these functions from config.py:
# - get_redis_client()
# - get_async_redis_client()

# ADD import where needed:
# from mkobi.core.redis_client import get_redis_client, get_async_redis_client
```

TESTING:
- [ ] Config module imports without errors
- [ ] Redis clients work from new location
- [ ] All existing tests pass
- [ ] Mypy passes

PRIORITY: Medium (bug fix + cleanup)

SPEC REFERENCE:
- Requirements: "Clean Architecture", "Separation of concerns"
SPEC REFERENCE:
- Requirements: "Clean Architecture", "Separation of concerns"

