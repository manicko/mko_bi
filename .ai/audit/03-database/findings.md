---
name: 03-database
description: Database architecture audit covering migrations, indexing strategy, consistency guarantees, transactional safety, and scalability risks
agent: audit-executor
alwaysApply: false
---

# Phase 03 Audit Findings — Database Architecture

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### DB-001: Schema Version Control via Alembic Migrations

| Field | Value |
|-------|-------|
| **ID** | DB-001 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | alembic/versions/, src/mkobi/db/models/ |
| **Classification** | advisory |

**Description:** The project uses Alembic for database migrations with a well-structured version history. There are 5 migration revisions that form a linear chain from the initial migration to the latest update. Each migration includes both upgrade() and downgrade() functions for reversibility.

**Evidence:**
- `alembic/versions/7130ecb0388c_true_initial_migration.py` (initial migration)
- `alembic/versions/e3b7f4a1c2d5_add_dashboard_access_permission_default.py` (revises: a2153f0f6094)
- `alembic/versions/a2153f0f6094_add_composite_index_aggregated_data.py` (revises: ffd23f1f7e2b)
- `alembic/versions/ffd23f1f7e2b_drop_broken_update_graphs_trigger.py` (revises: 7130ecb0388c)
- `alembic/versions/bc892fa3b2ae_rename_idx_dashboard_filters.py` (revises: e3b7f4a1c2d5)

---

### DB-002: Idempotent Migration Design with checkfirst Parameter

| Field | Value |
|-------|-------|
| **ID** | DB-002 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | alembic/versions/7130ecb0388c_true_initial_migration.py |
| **Classification** | advisory |

**Description:** The initial migration uses Alembic's proper API with `checkfirst=True` for ENUM types and `IF NOT EXISTS` clauses in SQL statements, making migrations idempotent and safe to re-run. This is a good practice for deployment reliability.

**Evidence:** `alembic/versions/7130ecb0388c_true_initial_migration.py` lines 27-47:
```python
user_role_enum.create(op.get_bind(), checkfirst=True)
...
op.execute("CREATE TABLE IF NOT EXISTS users (...")
op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users (email)")
```

---

### DB-003: Advisory Lock for Concurrent Migration Prevention

| Field | Value |
|-------|-------|
| **ID** | DB-003 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | alembic/env.py, src/mkobi/db/starter.py |
| **Classification** | advisory |

**Description:** The migration system uses PostgreSQL advisory locks (`pg_advisory_lock(42)`) to prevent concurrent migrations in multi-instance deployments. This is a critical safeguard for containerized environments where multiple application instances might attempt to migrate simultaneously.

**Evidence:** `alembic/env.py` lines 112-125:
```python
await connection.execute(
    text(f"SELECT pg_advisory_lock({MIGRATION_ADVISORY_LOCK_KEY})")
)
...
await connection.execute(
    text(f"SELECT pg_advisory_unlock({MIGRATION_ADVISORY_LOCK_KEY})")
)
```

---

### DB-004: Composite Indexes Covering Query Patterns

| Field | Value |
|-------|-------|
| **ID** | DB-004 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | alembic/versions/a2153f0f6094_add_composite_index_aggregated_data.py, src/mkobi/db/models/aggregated_data.py |
| **Classification** | advisory |

**Description:** Composite indexes exist for the primary data retrieval pattern (dashboard_id + graph_id) on the `aggregated_data` table, optimizing the most common query pattern for fetching chart data.

**Evidence:** `src/mkobi/db/models/aggregated_data.py` lines 49-62 and `alembic/versions/a2153f0f6094_add_composite_index_aggregated_data.py`:
```python
Index("idx_aggregated_data_dashboard_graph", "dashboard_id", "graph_id"),
```

---

### DB-005: GIN Index for JSONB Field Filtering

| Field | Value |
|-------|-------|
| **ID** | DB-005 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/db/models/aggregated_data.py, alembic/versions/7130ecb0388c_true_initial_migration.py |
| **Classification** | advisory |

**Description:** A GIN (Generalized Inverted Index) exists on the `dims` JSONB column in `aggregated_data`, enabling efficient JSONB containment queries for filter application. This is the optimal index type for JSONB field filtering.

**Evidence:** `src/mkobi/db/models/aggregated_data.py` line 53:
```python
Index("idx_aggregated_data_dims_gin", "dims", postgresql_using="gin"),
```

---

### DB-006: Unique Constraints for Business Keys

| Field | Value |
|-------|-------|
| **ID** | DB-006 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/db/models/user.py, src/mkobi/db/models/dashboard.py, src/mkobi/db/models/graphs.py, src/mkobi/db/models/filters.py |
| **Classification** | advisory |

**Description:** Unique constraints exist on business keys: `users.email`, `dashboards.name`, `graphs(dashboard_id, name)` composite, `filters.name`, and `layouts.name`. This prevents duplicate business entities.

**Evidence:**
- `src/mkobi/db/models/user.py` lines 38-42: `email` with `unique=True`
- `src/mkobi/db/models/dashboard.py` lines 40-44: `name` with `unique=True`
- `src/mkobi/db/models/graphs.py` lines 104-109: `UniqueConstraint("dashboard_id", "name")`
- `src/mkobi/db/models/filters.py` lines 40-44: `name` with `unique=True`

---

### DB-007: Foreign Key Constraints Enforce Relationships

| Field | Value |
|-------|-------|
| **ID** | DB-007 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/db/models/*.py |
| **Classification** | advisory |

**Description:** Foreign key constraints are properly defined across all entity relationships. CASCADE behavior is intentional: `ON DELETE CASCADE` for dependent child records (graphs, aggregated data, access entries) and `ON DELETE SET NULL` for optional references (layout_id, created_by).

**Evidence:**
- `src/mkobi/db/models/dashboard.py` line 58: `ForeignKey("layouts.id", ondelete="SET NULL")`
- `src/mkobi/db/models/dashboard.py` line 64: `ForeignKey("users.id", ondelete="SET NULL")`
- `src/mkobi/db/models/access.py` lines 31-41: `ON DELETE CASCADE` on both user_id and dashboard_id
- `src/mkobi/db/models/aggregated_data.py` lines 73-79: `ON DELETE CASCADE` on dashboard_id and graph_id

---

### DB-008: Not-Null Constraints on Required Fields

| Field | Value |
|-------|-------|
| **ID** | DB-008 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/db/models/*.py |
| **Classification** | advisory |

**Description:** Not-null constraints are properly defined on all required columns. Required fields like `email`, `password_hash`, `role`, `dashboard_id` in related tables, and JSONB fields (`dims`, `metrics`) have `nullable=False`.

**Evidence:**
- `src/mkobi/db/models/user.py` line 40: `nullable=False` on email
- `src/mkobi/db/models/aggregated_data.py` lines 74-81: `nullable=False` on dashboard_id, graph_id, dims, metrics

---

### DB-009: Transaction Management in Background Processing

| Field | Value |
|-------|-------|
| **ID** | DB-009 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/workers/data_worker.py, src/mkobi/data/storage/manager.py |
| **Classification** | advisory |

**Description:** Background processing uses explicit transaction control via `session.begin()` to ensure atomicity. Either all aggregates are saved or none, preventing partial data states on errors.

**Evidence:** `src/mkobi/workers/data_worker.py` lines 353-406:
```python
async with session.begin():
    ...
    processed = await manager.save_aggregates(...)
```

---

### DB-010: Batch Operations for Large Data Sets

| Field | Value |
|-------|-------|
| **ID** | DB-010 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/data/storage/manager.py |
| **Classification** | advisory |

**Description:** The StorageManager implements chunked batch operations with `CHUNK_SIZE = 1000` to handle large data sets without overwhelming memory or causing long-running transactions. This is a scalable approach for bulk inserts.

**Evidence:** `src/mkobi/data/storage/manager.py` lines 56, 289-307:
```python
CHUNK_SIZE: int = 1000
...
for i in range(0, len(aggregates), self.CHUNK_SIZE):
    chunk = aggregates[i : i + self.CHUNK_SIZE]
```

---

### DB-011: UPSERT Support for Aggregated Data

| Field | Value |
|-------|-------|
| **ID** | DB-011 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/data/storage/manager.py, src/mkobi/db/models/aggregated_data.py |
| **Classification** | advisory |

**Description:** The `aggregated_data` table supports UPSERT operations via a unique index on `(dashboard_id, graph_id, dims::text)`, and the StorageManager uses `on_conflict_do_update` for the APPEND mode in data uploads. JSONB key normalization ensures deterministic conflict detection.

**Evidence:** `src/mkobi/db/models/aggregated_data.py` lines 55-61:
```python
Index(
    "uq_aggregated_data_dashboard_graph_dims",
    "dashboard_id",
    "graph_id",
    text("dims::text"),
    unique=True,
),
```
And `src/mkobi/data/storage/manager.py` lines 179-188:
```python
stmt = stmt.on_conflict_do_update(
    index_elements=[...],
    set_={"metrics": stmt.excluded.metrics},
)
```

---

### DB-012: Connection Pooling Configuration

| Field | Value |
|-------|-------|
| **ID** | DB-012 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/db/session.py |
| **Classification** | advisory |

**Description:** Connection pooling is configured with appropriate settings for async operations: `pool_size=10`, `max_overflow=20`, `pool_timeout=30`, and `pool_pre_ping=True` to handle stale connections.

**Evidence:** `src/mkobi/db/session.py` lines 33-40:
```python
_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
)
```

---

### DB-013: Dedicated Database Role with Least-Privilege

| Field | Value |
|-------|-------|
| **ID** | DB-013 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | docker/init-scripts/01-create-app-role.sh, docker/docker-compose.yml |
| **Classification** | advisory |

**Description:** The application uses a dedicated `mkobi_app` database role with limited privileges (CONNECT, SELECT, INSERT, UPDATE, DELETE on public schema) instead of the superuser `postgres` role. This follows the principle of least privilege.

**Evidence:** `docker/init-scripts/01-create-app-role.sh`:
```bash
CREATE ROLE mkobi_app WITH LOGIN PASSWORD '${MKOBI_APP_PASSWORD}';
GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO mkobi_app;
GRANT USAGE ON SCHEMA public TO mkobi_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mkobi_app;
```

---

### DB-014: Separate Test Database with Migration Recreation

| Field | Value |
|-------|-------|
| **ID** | DB-014 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | tests/conftest.py, src/mkobi/db/starter.py |
| **Classification** | advisory |

**Description:** Test environment uses a physically separate test database (`bidb_test`) that is recreated from scratch before test sessions, ensuring isolation from dev/prod data. The `DatabaseStarter.recreate_test_database()` method drops and recreates the test database, then applies migrations.

**Evidence:** `src/mkobi/db/starter.py` lines 180-275:
```python
async def recreate_test_database(self) -> None:
    ...
    # Drop and recreate test database
    await conn.execute(DDL("DROP DATABASE IF EXISTS %(name)s", ...))
    await conn.execute(DDL("CREATE DATABASE %(name)s", ...))
    ...
    # Apply migrations to test database
    await self._apply_migrations(test_url)
```

---

### DB-015: Test Transaction Isolation with SAVEPOINT Pattern

| Field | Value |
|-------|-------|
| **ID** | DB-015 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | tests/conftest.py |
| **Classification** | advisory |

**Description:** Tests use a SAVEPOINT pattern (`session.begin_nested()`) for proper transaction isolation. Each test runs in a nested transaction that is automatically rolled back after completion, ensuring no test data leakage.

**Evidence:** `tests/conftest.py` lines 368-385:
```python
async with async_session_maker() as session:
    @event.listens_for(session.sync_session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        if trans.nested and not trans._parent.nested:
            sess.begin_nested()
    await session.begin_nested()
    try:
        yield session
    finally:
        await session.rollback()
        await session.close()
```

---

### DB-016: Processing Logs Archival Strategy

| Field | Value |
|-------|-------|
| **ID** | DB-016 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/db/starter.py |
| **Classification** | advisory |

**Description:** A retention policy exists for processing logs (default 30 days, configurable via `logs_retention_days`). Old successful/failed logs are periodically cleaned up during application startup.

**Evidence:** `src/mkobi/db/starter.py` lines 337-355:
```python
async def cleanup_old_logs(self) -> None:
    ...
    cutoff_date = datetime.now() - timedelta(days=self._config.logs_retention_days)
    ...
    "DELETE FROM processing_logs "
    "WHERE started_at < :cutoff AND status IN ('success', 'failed')"
```

---

### DB-017: Type Definitions Match Between Migrations and Models

| Field | Value |
|-------|-------|
| **ID** | DB-017 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/db/models/*.py, alembic/versions/7130ecb0388c_true_initial_migration.py |
| **Classification** | advisory |

**Description:** Type definitions in migrations match entity definitions. ENUM types are defined using Python classes (`UserRole`, `DashboardPermission`, etc.) via `StrEnum` and correctly mapped in SQLAlchemy models using `Enum(..., values_callable=lambda enum: [e.value for e in enum])`.

**Evidence:** `src/mkobi/db/models/user.py` lines 49-58 and `alembic/versions/7130ecb0388c_true_initial_migration.py` lines 27-47.

---

### DB-018: Unbounded Growth Risk in aggregated_data Table

| Field | Value |
|-------|-------|
| **ID** | DB-018 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/db/models/aggregated_data.py, src/mkobi/data/storage/manager.py |
| **Classification** | advisory |

**Description:** The `aggregated_data` table has no archival or partitioning strategy. It can grow unbounded as users upload data. For a BI dashboard system with potentially large datasets, this poses a scalability risk. No date-based filtering or automatic cleanup exists for aggregated data.

**Evidence:** The `cleanup_old_logs()` method exists for processing_logs but there is no equivalent `cleanup_old_aggregates()` method. The `aggregated_data` table schema lacks any TTL or archival mechanism.

**Recommendation:** Consider implementing:
1. Time-based partitioning for `aggregated_data` (e.g., by upload date)
2. A cleanup/archival job for old aggregated data
3. Size monitoring alerts for the `aggregated_data` table

---

### DB-019: Missing Composite Index for Filter Queries on aggregated_data

| Field | Value |
|-------|-------|
| **ID** | DB-019 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/db/models/aggregated_data.py, src/mkobi/db/repositories/aggregated_data_repo.py |
| **Classification** | advisory |

**Description:** When filtering aggregated data by both dashboard_id and JSONB dims values, the existing composite index `(dashboard_id, graph_id)` may not be optimal. Queries that filter only by `dims` would need to scan all dashboards. Consider adding a composite index `(dashboard_id, dims)` for filter-heavy query patterns.

**Evidence:** `src/mkobi/db/repositories/aggregated_data_repo.py` lines 158-162 show filter queries on `dims`:
```python
if filters:
    for key, value in filters.items():
        query = query.where(
            aggregated_data_model.AggregatedData.dims[key].astext == str(value)
        )
```

---

### DB-020: Manual Schema Changes in Starter Module

| Field | Value |
|-------|-------|
| **ID** | DB-020 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/db/starter.py |
| **Classification** | mandatory |

**Description:** The `DatabaseStarter.ensure_admin_user()` method performs direct SQL INSERT without using migrations. This is a manual schema change outside the Alembic migration framework. While the operation uses UPSERT to avoid race conditions, this pattern bypasses migration tracking and could lead to schema drift in production environments.

**Evidence:** `src/mkobi/db/starter.py` lines 322-334:
```python
await db.execute(
    text(
        "INSERT INTO users (id, email, password_hash, role, is_active) "
        "VALUES (:id, :email, :password, :role, true) "
        "ON CONFLICT (email) DO NOTHING"
    ),
    ...
)
```

**Recommendation:** Either:
1. Create a migration for admin user seeding, or
2. Use a dedicated seed data management system (e.g., Alembic seed migrations)
3. Document that this is intentional application initialization logic, not schema modification

---

### DB-021: Missing updated_at Trigger for graphs Table

| Field | Value |
|-------|-------|
| **ID** | DB-021 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | alembic/versions/7130ecb0388c_true_initial_migration.py, src/mkobi/db/models/graphs.py |
| **Classification** | advisory |

**Description:** The initial migration created an `updated_at` trigger for the `graphs` table (line 255-266), but the `Graph` model in `graphs.py` does not have an `updated_at` column. This inconsistency was corrected by the `ffd23f1f7e2b_drop_broken_update_graphs_trigger.py` migration which drops the trigger. However, the model should have an `updated_at` column for audit purposes.

**Evidence:** 
- `src/mkobi/db/models/graphs.py` has no `updated_at` column
- `alembic/versions/ffd23f1f7e2b_drop_broken_update_graphs_trigger.py` explicitly drops the trigger

**Recommendation:** Either add `updated_at` column to `graphs` table for audit trail, or document why graphs should not have modification timestamps.

---

### DB-022: No Check Constraints for Business Rules

| Field | Value |
|-------|-------|
| **ID** | DB-022 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/db/models/*.py |
| **Classification** | advisory |

**Description:** Beyond the email length check in the initial migration, there are no CHECK constraints for business rules such as ensuring `metrics` and `dimensions` lists in graphs are non-empty, or validating JSONB structures. This could allow invalid data to be stored.

**Evidence:** The only CHECK constraint is for email length (`users_email_length_check`). No constraints exist for:
- `graphs.dimensions` and `graphs.metrics` being non-empty arrays
- `aggregated_data.dims` having at least one key
- `processing_logs` having valid status transitions

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 3 |
| LOW | 18 |

## Mandatory Fixes

- **DB-020**: Manual schema changes in `DatabaseStarter.ensure_admin_user()` bypass Alembic migration tracking.

## Advisory Recommendations

- **DB-018**: Implement archival/partitioning strategy for `aggregated_data` table to handle unbounded growth.
- **DB-019**: Consider adding composite index `(dashboard_id, dims)` for optimized filter queries.
- **DB-021**: Add `updated_at` column to `graphs` model or document the intentional omission.
- **DB-022**: Add CHECK constraints for business rules (non-empty dimensions/metrics, valid JSONB structures).

---

## Template Field Reference

### Mandatory Fields Per Finding

| Field | Type | Values/Format |
|-------|------|---------------|
| `id` | string | Unique identifier within phase (e.g., `DB-001`, `DB-002`) |
| `title` | string | Human-readable one-line summary |
| `type` | enum | `SPEC-DEVIATION`, `BEST-PRACTICE`, `DOC-UPDATE`, `RUNTIME-ERROR` |
| `severity` | enum | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `description` | string | Detailed problem description with context |
| `evidence` | string | File paths, line references, log excerpts, code snippets |
| `affected_modules` | list | Affected module paths |
| `recommendation` | string | Concrete fix direction: what to change and why |
| `classification` | enum | `mandatory` (security, data loss, correctness) or `advisory` (improvement, refactoring) |

### Classification Guide

- **mandatory**: Security vulnerabilities, data loss risks, correctness issues, spec deviations requiring immediate fix
- **advisory**: Code quality improvements, refactoring suggestions, best practice enhancements