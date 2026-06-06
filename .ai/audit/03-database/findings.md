# Phase 03 Audit Findings — Database Architecture

**Executor:** audit-executor
**Template:** .kilo/commands/audit/phases/03-audit-database.md
**Status:** complete
**Validated:** no

---

## Findings

### DB-001: Dev Database Not at Latest Migration

| Field | Value |
|-------|-------|
| **ID** | DB-001 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | alembic/, docker-db-1 (bidb) |
| **Classification** | mandatory |

**Description:** The development database (bidb on port 5432) is at migration revision `000000000002`, while the migration chain head is `4479eb53fd4e` (Remove unused 'success' value from processing_status ENUM). The `alembic check` command returns `FAILED: Target database is not up to date.` This means the dev DB still contains the legacy `success` value in the `processing_status` enum type, creating a drift between the ORM model definition and the live schema.

**Evidence:**
- `alembic current` output: `000000000002`
- `alembic heads` output: `4479eb53fd4e (head)`
- `alembic check` output: `FAILED: Target database is not up to date.`
- Dev DB `processing_status` enum values: `started, uploaded, processing, success, failed, completed` (6 values — includes legacy `success`)
- Python model `ProcessingStatus` StrEnum values: `started, uploaded, processing, completed, failed` (5 values — no `success`)
- Migration `4479eb53fd4e` removes `success` from the enum via `ALTER TYPE` rename-and-recreate pattern

**Recommendation:** Apply the pending migration to the dev database: `alembic upgrade head`. For production, ensure deployment pipelines always run migrations to head before starting the application. Consider adding a startup check that validates the DB is at the latest migration revision.

---

### DB-002: Duplicate Index on dashboard_filters Table

| Field | Value |
|-------|-------|
| **ID** | DB-002 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/db/models/filters.py, alembic/versions/000000000000_initial_migration.py |
| **Classification** | advisory |

**Description:** The `dashboard_filters` table has a composite primary key on `(dashboard_id, filter_id)` which implicitly creates a unique index on that column pair. An additional explicit index `idx_dashboard_filters_dashboard_id` is defined on the exact same column combination `(dashboard_id, filter_id)`. This is a duplicate index — the PK index already serves any query that needs to look up by both columns.

**Evidence:**
- From `pg_indexes`: `dashboard_filters_pkey` = `CREATE UNIQUE INDEX ... ON public.dashboard_filters USING btree (dashboard_id, filter_id)`
- From `pg_indexes`: `idx_dashboard_filters_dashboard_id` = `CREATE INDEX ... ON public.dashboard_filters USING btree (dashboard_id, filter_id)`
- Source: `alembic/versions/000000000000_initial_migration.py`, line creating `idx_dashboard_filters_dashboard_id`
- Source: `src/mkobi/db/models/filters.py`, line `Index("idx_dashboard_filters_dashboard_id", "dashboard_id", "filter_id")` inside `dashboard_filters` Table definition

**Recommendation:** Remove the redundant `idx_dashboard_filters_dashboard_id` index from both the ORM model definition (`filters.py`) and a new migration. If queries need to look up dashboards by `filter_id` alone, create an index on `(filter_id)` instead.

---

### DB-003: Row-by-Row Insert in save_filter_values (N+1 Write Pattern)

| Field | Value |
|-------|-------|
| **ID** | DB-003 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/db/repositories/dashboard_filter_values_repo.py |
| **Classification** | advisory |

**Description:** The `DashboardFilterValuesRepository.save_filter_values()` method uses a `for` loop with individual `db.add()` calls to insert filter values one at a time (lines 89-91). This is an N+1 write pattern that issues separate INSERT statements for each value. The project already has a bulk insert pattern in `AggregatedDataRepository.bulk_insert()` which uses `sqlalchemy.insert()` with a list of dictionaries. The filter values method should follow the same pattern for consistency and performance, especially when dashboards have many distinct filter values.

**Evidence:**
- `src/mkobi/db/repositories/dashboard_filter_values_repo.py`, lines 89-91:
  ```python
  for value in values:
      db.add(
          DashboardFilterValue(
              dashboard_id=dashboard_id,
              filter_name=filter_name,
              filter_value=value,
          )
      )
  ```
- Compare with `src/mkobi/db/repositories/aggregated_data_repo.py`, lines 103-110 which uses `insert(aggregated_data_model.AggregatedData), insert_data` for batch insertion.

**Recommendation:** Replace the loop-based `db.add()` with a bulk `insert()` statement using a list of dictionaries, consistent with `aggregated_data_repo.bulk_insert()`.

---

### DB-004: No Archival Strategy for processing_logs Table

| Field | Value |
|-------|-------|
| **ID** | DB-004 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/db/models/processing_logs.py, src/mkobi/db/repositories/processing_log_repo.py |
| **Classification** | advisory |

**Description:** The `processing_logs` table grows monotonically — every file upload and processing attempt creates a new row. There is no TTL, cleanup, or archival mechanism for old processing logs. As the system processes more data, this table will grow unbounded. Unlike `aggregated_data` (which is replaced on each upload via the `clear_old=True` flag in `bulk_insert`), processing logs accumulate indefinitely.

**Evidence:**
- `src/mkobi/db/models/processing_logs.py`: Model has no expiration column or cleanup logic.
- `src/mkobi/db/repositories/processing_log_repo.py`: The `delete()` method exists but is only called explicitly, never automatically.
- No background worker, cron job, or database-level partitioning/TTL for `processing_logs`.
- The `dashboard_id` FK uses `SET NULL` on delete, so orphaned logs (with `dashboard_id=NULL`) can persist even after dashboards are deleted.

**Recommendation:** Implement a retention policy for `processing_logs`: (1) Add a periodic cleanup task that deletes logs older than N days, or (2) Use PostgreSQL table partitioning by `created_at`, or (3) Add a `ttl` column and a DB-level cleanup mechanism. Consider whether orphaned logs (where the dashboard was deleted) should be automatically purged.

---

### DB-005: Unpaginated get_all() Repository Methods Risk Unbounded Memory Usage

| Field | Value |
|-------|-------|
| **ID** | DB-005 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/db/repositories/user_repo.py, src/mkobi/db/repositories/dashboard_repo.py, src/mkobi/db/repositories/graph_repo.py, src/mkobi/db/repositories/filter_repo.py, src/mkobi/db/repositories/access_repo.py, src/mkobi/db/repositories/layout_repo.py, src/mkobi/db/repositories/processing_config_repo.py, src/mkobi/db/repositories/registration_request_repo.py |
| **Classification** | advisory |

**Description:** Multiple repositories implement `get_all()` methods that load all records from a table without pagination or limit. As tables grow (especially `processing_logs`, `aggregated_data`, and `dashboard_filter_values`), these methods will consume unbounded memory and produce increasingly slow queries. The `UserRepository.get_all()` and `DashboardRepository.get_all()` are particularly risky as they are called from API endpoints and could be triggered by any authenticated user.

**Evidence:**
- `src/mkobi/db/repositories/user_repo.py`, line 124: `async def get_all(self, db: AsyncSession) -> list[UserRead]` — `select(user_model.User)` with no limit.
- `src/mkobi/db/repositories/dashboard_repo.py`, line 211: `async def get_all(self, db: AsyncSession)` — `select(dashboard_model.Dashboard)` with no limit.
- `src/mkobi/db/repositories/graph_repo.py`, line 194: similar pattern.
- `src/mkobi/db/repositories/filter_repo.py`, line 163: similar pattern.
- `src/mkobi/db/repositories/processing_log_repo.py`, `get_by_dashboard()` (line 144) has no limit — could return thousands of logs.

**Recommendation:** Add pagination parameters (`offset`/`limit` or keyset pagination) to `get_all()` methods that are exposed via API endpoints. For `processing_logs`, the `get_filtered()` method already supports pagination — ensure `get_by_dashboard()` also uses it or delegates to it.

---

### DB-006: Processing Log Commits Before Background Job Enqueue — No Compensation on Failure

| Field | Value |
|-------|-------|
| **ID** | DB-006 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/services/file_processing.py |
| **Classification** | mandatory |

**Description:** In `process_upload_with_session()`, the processing log status is committed to the database (`await db.commit()` at line 231) before the background job is enqueued (`await enqueue_processing_job()` at line 237). If the job enqueue fails (e.g., task queue unavailable), the processing log remains in `UPLOADED` status with no corresponding background job. There is no compensation logic to roll back the log status or retry the enqueue. This leaves the task permanently stuck — the API will report the task as `UPLOADED` but no processing will ever occur.

**Evidence:**
- `src/mkobi/services/file_processing.py`, lines 219-237:
  ```python
  await log_repo.update_status(
      log_id=log.id,
      status=ProcessingStatus.UPLOADED,
      message=f"File uploaded successfully, awaiting processing. mode={mode}",
      db=db,
  )
  await db.commit()  # ← Commit happens here

  # Move file to final location AFTER successful commit
  final_file_path = upload_dir / f"{log.id}{file_ext}"
  try:
      file_path.replace(final_file_path)
  except Exception:
      logger.error(...)
      raise  # ← File move failure: log committed but job not enqueued

  await enqueue_processing_job(...)  # ← If this fails, log is stuck in UPLOADED
  ```

**Recommendation:** Reorder operations: enqueue the job first, then commit the log. Or: wrap the commit+enqueue in a compensating transaction that sets the log to `FAILED` if enqueue fails after commit. Alternatively, add a health-check/sweeper that detects stuck `UPLOADED` logs (where `started_at` is older than a threshold) and re-enqueues or marks them failed.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 5 |
| LOW | 0 |

## Mandatory Fixes

- **DB-001**: Dev database not at latest migration revision — apply `alembic upgrade head` to synchronize schema with ORM models
- **DB-006**: Processing log commits before background job enqueue — no compensation on enqueue failure, leaving tasks permanently stuck in `UPLOADED` status

## Advisory Recommendations

- **DB-002**: Remove duplicate index `idx_dashboard_filters_dashboard_id` on `dashboard_filters` table (identical to PK index)
- **DB-003**: Replace row-by-row `db.add()` loop in `save_filter_values()` with bulk `insert()` statement
- **DB-004**: Implement archival/retention policy for `processing_logs` table to prevent unbounded growth
- **DB-005**: Add pagination to `get_all()` repository methods exposed via API endpoints

## Doc Updates Needed

(None)
