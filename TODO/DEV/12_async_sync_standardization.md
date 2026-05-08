---
## DATA PROCESSING
---

### TASK: Standardize Async/Sync Patterns

FILE: src/mkobi/services/*.py, src/mkobi/db/repositories/*.py, src/mkobi/api/routes/*.py

GOAL: Ensure consistent async patterns throughout codebase

IMPLEMENT:

* Verify all database operations use async SQLAlchemy
* Check no sync SQLAlchemy in async endpoints
* Ensure all service methods are async (matching interface)
* Fix any blocking calls in async context:
  - time.sleep() → asyncio.sleep()
  - sync file I/O → async file I/O
  - sync HTTP calls → async HTTP calls

LOGIC:

1. Run `uv run mypy .` to find async-related errors
2. Check all repository methods are async:
   - Should use `async def` and `await` for DB calls
3. Check all service methods match IService interfaces
4. Check API routes properly await service calls
5. Search for blocking calls:
   - `grep -r "time.sleep" src/mkobi/`
   - `grep -r "requests." src/mkobi/` (should use httpx or aiohttp)
6. Replace with async equivalents
7. Test: `uv run pytest tests/` passes

DONE:

* [ ] All repositories use async SQLAlchemy
* [ ] All services methods are async
* [ ] No sync DB calls in async context
* [ ] No blocking I/O in async code
* [ ] MyPy async errors resolved
* [ ] All tests pass

---

### TASK: Fix Data Processing Pipeline

FILE: src/mkobi/data/processing/registry.py, src/mkobi/data/processing/transformations.py, src/mkobi/data/storage/manager.py

GOAL: Ensure data processing pipeline is correct and efficient

IMPLEMENT:

* Verify pipeline stages are explicit:
  1. Upload → temp file
  2. Parse (CSV/CSV.gz using Polars)
  3. Transform (apply config)
  4. Aggregate (groupby, YoY, shares)
  5. Save to PostgreSQL (JSONB)
* Check Polars usage (not pandas):
  - `import polars as pl` (not `import pandas as pd`)
* Verify error handling at each stage
* Ensure temp file cleanup (platformdirs, finally block)
* Check memory efficiency for large files

LOGIC:

1. Review registry.py for pipeline flow
2. Verify transformations.py has all required aggregations:
   - groupby
   - YoY calculations
   - Shares calculations
   - Custom metrics
3. Check storage/manager.py for proper JSONB serialization
4. Verify temp file cleanup in finally block
5. Test with sample CSV and CSV.gz files
6. Test error handling (corrupted CSV, missing columns)

DONE:

* [ ] Pipeline stages explicit and correct
* [ ] Polars used (not pandas)
* [ ] All aggregation types implemented
* [ ] Error handling at each stage
* [ ] Temp files cleaned up
* [ ] Memory-efficient for large files
* [ ] Tests pass: `uv run pytest tests/test_data_processing.py`

---
