---
## DATA PIPELINE FIXES
---

### TASK: Fix Data Processing Pipeline Issues

FILE: `src/mkobi/data/processing/registry.py`, `src/mkobi/data/processing/transformations.py`

GOAL: Fix issues in ETL pipeline and improve error handling

ISSUE DESCRIPTION:

1. **Pipeline doesn't handle empty DataFrames**:
   - If CSV is empty or all rows filtered out, pipeline may fail
   - Need to check for empty DataFrames before processing

2. **Error handling in pipeline**:
   - `registry.py` line 122: Generic exception catch
   - Should catch specific exceptions and provide better error messages

3. **No retry mechanism** (SPEC.md mentions "retry/failure handling"):
   - If database save fails, no retry
   - If transformation fails, entire pipeline fails

4. **Transformation functions have issues** (from Task 09):
   - Curly quotes in `transformations.py` (lines 127, 129, 135, etc.)
   - Need to fix syntax errors first

5. **No validation of transformation config**:
   - `apply_transformations` doesn't validate config structure
   - Could fail with cryptic Polars errors

IMPACT:
- Pipeline failures in production
- No resilience (no retry)
- Hard to debug errors

FILES TO FIX:
- `src/mkobi/data/processing/registry.py` - Add retry, better error handling
- `src/mkobi/data/processing/transformations.py` - Fix curly quotes, add validation
- `src/mkobi/data/storage/manager.py` - Check for storage errors

IMPLEMENTATION:

1. **Add empty DataFrame check**:
   ```python
   # In DataPipeline.run():
   if df.height == 0:
       logger.warning("Empty DataFrame, skipping processing")
       await update_log_status(
           log_id=log_entry.id,
           status=ProcessingStatus.COMPLETED,
           message="No data to process",
           db=db,
       )
       return log_entry
   ```

2. **Add retry mechanism**:
   ```python
   import tenacity


   @tenacity.retry(
       stop=tenacity.stop_after_attempt(3),
       wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
       retry=tenacity.retry_if_exception_type((SQLAlchemyError, ConnectionError)),
   )
   async def _save_with_retry(self, dashboard_id, aggregates, mode, db):
       await self.storage_manager.save(...)
   ```

3. **Better error handling**:
   ```python
   try:
       transformed_df = apply_transformations(df, config)
   except pl.PolarsError as e:
       logger.error("Polars transformation error: %s", e)
       await update_log_status(
           log_id=log_entry.id,
           status=ProcessingStatus.FAILED,
           message=f"Transformation error: {e}",
           db=db,
       )
       raise ValueError(f"Data transformation failed: {e}")
   ```

4. **Validate transformation config**:
   ```python
   def validate_config(config: dict) -> None:
       """Validate transformation config structure."""
       if not isinstance(config, dict):
           raise ValueError("Config must be a dictionary")
       
       if "filters" in config:
           # Validate filter structure
           pass
       # ... validate other sections
   ```

5. **Fix syntax errors first** (Task 09):
   - Fix curly quotes in `transformations.py`

TESTING:
- [ ] Empty DataFrame handled gracefully
- [ ] Retry mechanism works (simulate DB failure)
- [ ] Specific exceptions caught and logged properly
- [ ] Config validation works
- [ ] All syntax errors fixed

PRIORITY: High (ETL pipeline reliability)

SPEC REFERENCE:
- SPEC.md: "ETL-потоки (загрузку данных, трансформации, очистку, агрегации, retry/failure handling)"
- Requirements: "ETL-jobs", "retry/failure handling"
