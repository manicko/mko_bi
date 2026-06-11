---
id: file-cleanup
domain: processing
tags:
  - cleanup
  - temp-files
  - lifecycle
  - crash-recovery
related:
  - task-queue
  - processing-api
  - backend-architecture
---

# Temp File Cleanup Architecture

## Purpose

Temp files are created during CSV upload processing and must be cleaned up to prevent disk space exhaustion. This document describes the dual cleanup mechanisms that ensure no orphaned files remain after crashes or restarts.

## Cleanup Mechanisms

### 1. Startup Cleanup

On application startup, `cleanup_stale_temp_files()` is called in `src/mkobi/db/starter.py:167`. This function:

- Scans the upload temp directory (`config.upload_temp_dir`)
- Deletes all `.csv*` files older than the threshold
- Runs before request handling begins
- Designed to clean up files from previous runs that were never removed

**Code location:** `src/mkobi/services/file_cleanup.py`

```python
deleted_count = cleanup_stale_temp_files()
if deleted_count > 0:
    logger.info("Cleaned up %d orphaned temp files during startup", deleted_count)
```

### 2. Worker Cleanup

During background processing in `src/mkobi/workers/data_worker.py`:

- **Success path (lines 308-310):** Temp file is deleted immediately after successful processing
- **Error path (lines 332-340):** Temp file is deleted even when processing fails, with error logging as fallback

```python
# On success
if file_path.exists():
    await asyncio.to_thread(file_path.unlink)
    logger.info("Temp file deleted: %s", file_path)

# On error
if file_path.exists():
    try:
        await asyncio.to_thread(file_path.unlink)
    except Exception:
        logger.warning("Failed to clean up temp file: %s", file_path, exc_info=True)
```

## Configuration

The cleanup behavior is controlled by environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `STALE_FILE_THRESHOLD_HOURS` | Age threshold in hours before temp files are considered stale | 24 |
| `LOGS_RETENTION_DAYS` | Retention period for processing logs | 30 |
| `STALE_PROCESSING_TIMEOUT_MINUTES` | Timeout for stale PROCESSING entries to be marked FAILED | 30 |
| `STALE_PROCESSING_CLEANUP_INTERVAL_SECONDS` | Interval for cleanup worker runs | 300 |

These are defined in `src/mkobi/config.py`:

```python
stale_file_threshold_hours: int = Field(default=24, alias="STALE_FILE_THRESHOLD_HOURS")
logs_retention_days: int = Field(default=30, alias="LOGS_RETENTION_DAYS")
stale_processing_timeout_minutes: int = Field(default=30, alias="STALE_PROCESSING_TIMEOUT_MINUTES")
stale_processing_cleanup_interval_seconds: int = Field(default=300, alias="STALE_PROCESSING_CLEANUP_INTERVAL_SECONDS")
```

## Crash/Restart Behavior

The dual cleanup mechanism ensures resilience:

1. **Graceful shutdown:** Worker cleanup handles completed or failed processing
2. **Worker crash:** Temp files remain in the upload directory but are caught by startup cleanup
3. **Container restart:** Startup cleanup removes any orphaned files older than the threshold
4. **Partial processing:** Files left by incomplete processing are removed on next startup

The `app_data` volume persists across container restarts, allowing stale files to accumulate. The startup cleanup ensures they are eventually removed without manual intervention.

## Cross-References

- [Processing API](processing-api.md) — Upload endpoint and processing pipeline
- [Task Queue Migration](task-queue.md) — Background processing with RQ worker
- [Backend Architecture](../06-backend/architecture.md) — Clean Architecture and startup lifecycle