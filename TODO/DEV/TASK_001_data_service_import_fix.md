---
## TASK: Fix import error in data_service.py
---

### PROBLEM

Tests cannot run due to import error in `src/mkobi/services/data_service.py`:

```
ImportError: cannot import name 'get_redis_client' from 'mkobi.config'
```

### ROOT CAUSE

Line 14 in `data_service.py` incorrectly imports `get_redis_client` from `mkobi.config`:
```python
from mkobi.config import get_config, get_redis_client  # WRONG
```

The function `get_redis_client` does not exist in `mkobi.config`. The correct import is on line 17:
```python
from mkobi.core.redis_client import get_redis_client  # CORRECT
```

### FILES TO FIX

- `src/mkobi/services/data_service.py` (line 14)

### SOLUTION

Remove `get_redis_client` from the import on line 14, since it's already correctly imported on line 17:

```python
# Line 14 - CHANGE FROM:
from mkobi.config import get_config, get_redis_client

# TO:
from mkobi.config import get_config
```

### VERIFICATION

1. Run `uv run ruff check src/mkobi/services/data_service.py`
2. Run `uv run mypy src/mkobi/services/data_service.py`
3. Run `uv run pytest tests/` - tests should load without ImportError

### PRIORITY

High - blocks all tests from running

### STATUS

- [ ] Issue identified
- [ ] Fix applied
- [ ] Tests passing

---
