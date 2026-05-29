---
name: 03-database-validated
description: Validated database architecture audit findings — safety, consistency, and applicability verified against current codebase
agent: validator
source: .ai/audit/03-database/findings.md
status: validated
date: 2026-05-29
---

# Phase 03 Validated Findings — Database Architecture

**Validator:** validator agent
**Source:** .ai/audit/03-database/findings.md
**Status:** validated

---

## Validation Summary

| Category | Count |
|----------|-------|
| Total findings in source | 22 |
| Validated (approved) | 19 |
| Rejected | 1 |
| Reclassified | 2 |
| Merged | 0 |

### Severity Distribution (Validated)

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 2 |
| LOW | 16 |

### Classification (Validated)

| Classification | Count |
|----------------|-------|
| Mandatory fixes | 1 |
| Advisory recommendations | 18 |

---

## Validated Findings

---

### DB-001: Schema Version Control via Alembic Migrations

| Field | Value |
|-------|-------|
| **ID** | DB-001 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | alembic/versions/, src/mkobi/db/models/ |
| **Classification** | advisory |

**Description:** The project uses Alembic for database migrations with a well-structured version history. There are 5 migration revisions that form a linear chain from the initial migration to the latest update. Each migration includes both upgrade() and downgrade() functions for reversibility.

**Validation:** CONFIRMED — All 5 migration files exist and form a correct linear chain:
- `7130ecb0388c` (initial) → `ffd23f1f7e2b` → `a2153f0f6094` → `e3b7f4a1c2d5` → `bc892fa3b2ae`. Every migration has both `upgrade()` and `downgrade()`. DAG is valid with no branches or circular dependencies.

**Recommendation:** No action needed — this is a confirmed positive practice. No tasks should be generated from this finding.

**Semantics:** Stable. Anchored on migration file structure, unlikely to shift.

---

### DB-002: Idempotent Migration Design with checkfirst Parameter

| Field | Value |
|-------|-------|
| **ID** | DB-002 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | alembic/versions/7130ecb0388c_true_initial_migration.py |
| **Classification** | advisory |

**Description:** The initial migration uses Alembic's proper API with `checkfirst=True` for ENUM types and `IF NOT EXISTS` clauses in SQL statements, making migrations idempotent and safe to re-run.

**Validation:** CONFIRMED — Evidence lines 27-47 verified. All 6 ENUM types use `create(op.get_bind(), checkfirst=True)`. All CREATE TABLE / CREATE INDEX statements use `IF NOT EXISTS`. Idempotency pattern is consistent and correct.

**Recommendation:** No action needed — confirmed positive practice.

---

### DB-003: Advisory Lock for Concurrent Migration Prevention

| Field | Value |
|-------|-------|
| **ID** | DB-003 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | alembic/env.py, src/mkobi/db/starter.py |
| **Classification** | advisory |

**Description:** The migration system uses PostgreSQL advisory locks (`pg_advisory_lock(42)`) to prevent concurrent migrations in multi-instance deployments.

**Validation:** CONFIRMED — `alembic/env.py` lines 112-125 verified. Lock is acquired before `do_run_migrations` and released in a `finally` block with error handling. The pattern is correct and safe. This is also documented in SPEC.md (design decision #141).

**Recommendation:** No action needed — confirmed positive practice with documented rationale.

---

### DB-004: Composite Indexes Covering Query Patterns

| Field | Value |
|-------|-------|
| **ID** | DB-004 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | alembic/versions/a2153f0f6094_add_composite_index_aggregated_data.py, src/mkobi/db/models/aggregated_data.py |
| **Classification** | advisory |

**Description:** Composite indexes exist for the primary data retrieval pattern (dashboard_id + graph_id) on the `aggregated_data` table.

**Validation:** CONFIRMED — Model defines `Index("idx_aggregated_data_dashboard_graph", "dashboard_id", "graph_id")` at line 52. Migration `a2153f0f6094` adds the index. Query patterns in `aggregated_data_repo.py` filter by `(dashboard_id, graph_id)` which matches this index.

**Recommendation:** No action needed — confirmed positive practice.

---

### DB-005: GIN Index for JSONB Field Filtering

| Field | Value |
|-------|-------|
| **ID** | DB-005 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/db/models/aggregated_data.py, alembic/versions/7130ecb0388c_true_initial_migration.py |
| **Classification** | advisory |

**Description:** A GIN (Generalized Inverted Index) exists on the `dims` JSONB column in `aggregated_data`, enabling efficient JSONB containment queries.

**Validation:** CONFIRMED — Model line 53: `Index("idx_aggregated_data_dims_gin", "dims", postgresql_using="gin")`. Initial migration line 162: `CREATE INDEX IF NOT EXISTS idx_aggregated_data_dims_gin ON aggregated_data USING GIN (dims)`. GIN is the correct index type for JSONB containment queries.

**Recommendation:** No action needed — confirmed positive practice.

---

### DB-006: Unique Constraints for Business Keys

| Field | Value |
|-------|-------|
| **ID** | DB-006 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/db/models/user.py, src/mkobi/db/models/dashboard.py, src/mkobi/db/models/graphs.py, src/mkobi/db/models/filters.py |
| **Classification** | advisory |

**Description:** Unique constraints exist on business keys: `users.email`, `dashboards.name`, `graphs(dashboard_id, name)` composite, `filters.name`, and `layouts.name`.

**Validation:** CONFIRMED — All five unique constraints verified at the specified locations. Business key uniqueness is properly enforced at the database level.

**Recommendation:** No action needed — confirmed positive practice.

---

### DB-007: Foreign Key Constraints Enforce Relationships

| Field | Value |
|-------|-------|
| **ID** | DB-007 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/db/models/*.py |
| **Classification** | advisory |

**Description:** Foreign key constraints are properly defined across all entity relationships. CASCADE behavior is intentional: `ON DELETE CASCADE` for dependent child records and `ON DELETE SET NULL` for optional references.

**Validation:** CONFIRMED — All foreign keys and their `ondelete` strategies match the evidence. The CASCADE vs SET NULL choices align with the data model (CASCADE for dependent children like graphs, aggregated_data, access; SET NULL for optional references like layout_id, created_by).

**Recommendation:** No action needed — confirmed positive practice.

---

### DB-008: Not-Null Constraints on Required Fields

| Field | Value |
|-------|-------|
| **ID** | DB-008 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/db/models/*.py |
| **Classification** | advisory |

**Description:** Not-null constraints are properly defined on all required columns including `email`, `password_hash`, `role`, `dashboard_id`, `dims`, and `metrics`.

**Validation:** CONFIRMED — Evidence verified. Required fields have `nullable=False`. JSONB columns `dims` and `metrics` in `aggregated_data` correctly have `nullable=False` with `default=dict`.

**Recommendation:** No action needed — confirmed positive practice.

---

### DB-009: Transaction Management in Background Processing

| Field | Value |
|-------|-------|
| **ID** | DB-009 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/workers/data_worker.py, src/mkobi/data/storage/manager.py |
| **Classification** | advisory |

**Description:** Background processing uses explicit transaction control via `session.begin()` to ensure atomicity.

**Validation:** CONFIRMED — `data_worker.py` lines 353-398 verified: `async with session.begin()` wraps the entire aggregate save operation. StorageManager correctly delegates transaction management to the caller (documented in module docstring: "Does not manage transactions (commit/rollback is external)"). This is a proper separation of concerns.

**Recommendation:** No action needed — confirmed positive practice with proper layer separation.

---

### DB-010: Batch Operations for Large Data Sets

| Field | Value |
|-------|-------|
| **ID** | DB-010 |
| **Severity** | LOW |
**Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/data/storage/manager.py |
| **Classification** | advisory |

**Description:** The StorageManager implements chunked batch operations with `CHUNK_SIZE = 1000` to handle large data sets.

**Validation:** CONFIRMED — `CHUNK_SIZE: int = 1000` at line 56. Both `_bulk_insert` (line 289-307) and `_bulk_upsert` (line 320-350) use chunked iteration: `for i in range(0, len(aggregates), self.CHUNK_SIZE)`.

**Recommendation:** No action needed — confirmed positive practice.

---

### DB-011: UPSERT Support for Aggregated Data

| Field | Value |
|-------|-------|
| **ID** | DB-011 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/data/storage/manager.py, src/mkobi/db/models/aggregated_data.py |
| **Classification** | advisory |

**Description:** The `aggregated_data` table supports UPSERT operations via a unique index on `(dashboard_id, graph_id, dims::text)`, and StorageManager uses `on_conflict_do_update` for APPEND mode. JSONB key normalization ensures deterministic conflict detection.

**Validation:** CONFIRMED — Unique index `uq_aggregated_data_dashboard_graph_dims` exists (model lines 55-61). StorageManager uses `on_conflict_do_update` (lines 179-188, 335-344) with `index_elements=[dashboard_id, graph_id, dims]`. The `_normalize_json_keys()` function recursively sorts dict keys for deterministic serialization. This pattern is sound.

**Note:** The `on_conflict_do_update` uses `index_elements` referencing the ORM column objects, while the actual unique index is on `dims::text` (cast). PostgreSQL resolves this correctly because the unique index covers the same columns. However, the conflict target relies on JSONB equality matching the text-cast uniqueness, which works because `_normalize_json_keys` ensures deterministic serialization. This is architecturally correct but subtle — worth documenting.

**Recommendation:** Consider adding a code comment explaining the relationship between the `index_elements` in on_conflict and the `dims::text` unique index to aid future maintainers.

---

### DB-012: Connection Pooling Configuration

| Field | Value |
|-------|-------|
| **ID** | DB-012 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/db/session.py |
| **Classification** | advisory |

**Description:** Connection pooling is configured with appropriate settings: `pool_size=10`, `max_overflow=20`, `pool_timeout=30`, `pool_pre_ping=True`.

**Validation:** CONFIRMED — Exact values verified at `session.py` lines 33-40. These are reasonable defaults for an async application. `pool_pre_ping=True` correctly handles stale connections.

**Recommendation:** No action needed — confirmed positive practice.

---

### DB-013: Dedicated Database Role with Least-Privilege

| Field | Value |
|-------|-------|
| **ID** | DB-013 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | docker/init-scripts/01-create-app-role.sh, docker/docker-compose.yml |
| **Classification** | advisory |

**Description:** The application uses a dedicated `mkobi_app` database role with limited privileges (CONNECT, SELECT, INSERT, UPDATE, DELETE) instead of the superuser `postgres` role.

**Validation:** CONFIRMED — Init script creates `mkobi_app` role with exactly the claimed privileges, plus `USAGE ON SCHEMA public`, `USAGE ON SEQUENCES`, and `ALTER DEFAULT PRIVILEGES`. Also grants `CREATEDB` for test database recreation. This matches the documented design decision in SPEC.md (#142).

**Recommendation:** No action needed — confirmed positive practice with documented rationale.

---

### DB-014: Separate Test Database with Migration Recreation

| Field | Value |
|-------|-------|
| **ID** | DB-014 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | tests/conftest.py, src/mkobi/db/starter.py |
| **Classification** | advisory |

**Description:** Test environment uses a physically separate test database that is recreated from scratch before test sessions.

**Validation:** CONFIRMED — `DatabaseStarter.recreate_test_database()` (starter.py lines 180-275) drops and recreates the database, then applies migrations. Database name is validated against `^[a-zA-Z0-9_]+$` to prevent SQL injection. SQL identifiers are properly quoted via `identifier_preparer.quote()`. Privileges are correctly granted to `mkobi_app` on the new database.

**Recommendation:** No action needed — confirmed positive practice with proper security hardening.

---

### DB-015: Test Transaction Isolation with SAVEPOINT Pattern

| Field | Value |
|-------|-------|
| **ID** | DB-015 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | tests/conftest.py |
| **Classification** | advisory |

**Description:** Tests use a SAVEPOINT pattern (`session.begin_nested()`) for proper transaction isolation. Each test runs in a nested transaction that is automatically rolled back.

**Validation:** CONFIRMED — `conftest.py` lines 368-385 verified. Uses `after_transaction_end` event listener to restart SAVEPOINT after each commit/rollback, allowing tests to use `commit()` while maintaining isolation. Pattern is correct and well-established in the SQLAlchemy testing ecosystem.

**Recommendation:** No action needed — confirmed positive practice.

---

### DB-016: Processing Logs Archival Strategy

| Field | Value |
|-------|-------|
| **ID** | DB-016 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/db/starter.py |
| **Classification** | advisory |

**Description:** A retention policy exists for processing logs (default 30 days, configurable via `logs_retention_days`). Old successful/failed logs are cleaned up during application startup.

**Validation:** CONFIRMED — `cleanup_old_logs()` at starter.py lines 337-355 uses `DELETE FROM processing_logs WHERE started_at < :cutoff AND status IN ('success', 'failed')`. Cutoff is `datetime.now() - timedelta(days=self._config.logs_retention_days)`. Default is 30 days. No early return when `logs_retention_days <= 0`.

**Recommendation:** No action needed — confirmed positive practice.

---

### DB-017: Type Definitions Match Between Migrations and Models

| Field | Value |
|-------|-------|
| **ID** | DB-017 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/db/models/*.py, alembic/versions/7130ecb0388c_true_initial_migration.py |
| **Classification** | advisory |

**Description:** Type definitions in migrations match entity definitions. ENUM types are defined using Python `StrEnum` classes and correctly mapped via `Enum(..., values_callable=lambda enum: [e.value for e in enum])`.

**Validation:** CONFIRMED — All models use `Enum(SomeStrEnum, name="...", values_callable=lambda enum: [e.value for e in enum])`. Initial migration creates matching PostgreSQL ENUM types with identical value sets. Both upgrade and downgrade paths handle all 6 ENUM types.

**Recommendation:** No action needed — confirmed positive practice.

---

### DB-018: Unbounded Growth Risk in aggregated_data Table

| Field | Value |
|-------|-------|
| **ID** | DB-018 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/db/models/aggregated_data.py, src/mkobi/data/storage/manager.py, src/mkobi/db/starter.py |
| **Classification** | advisory |

**Description:** The `aggregated_data` table has no archival or partitioning strategy. It can grow unbounded as users upload data. No date-based filtering or automatic cleanup exists for aggregated data.

**Validation:** CONFIRMED — The `aggregated_data` table has no `created_at` or `updated_at` timestamp, no partition key, and no cleanup mechanism. The `cleanup_old_logs()` method exists for `processing_logs` (starter.py lines 337-355) but there is no equivalent for `aggregated_data`. The design pattern for `processing_logs` (retention policy + cleanup job) could be replicated, but its absence for `aggregated_data` is a genuine gap.

**Assessment:** As designed, each upload performs a full recalculation (clear_old=True in OVERWRITE mode). In this model, old data for the same dashboard/graph is deleted on each upload, which naturally limits growth per dashboard. However:
1. In APPEND mode, data accumulates without bound.
2. Even in OVERWRITE mode, if the number of dimension combinations grows arbitrarily, the table grows.
3. No monitoring or alerting exists for table size.

The risk is **MEDIUM**, not HIGH, because the primary use case (full recalculation on upload) naturally limits per-dashboard growth. But for long-running production instances with APPEND usage, this is a real concern.

**Dependency notes:** Any archival feature should not conflict with the composite indexes or UPSERT mechanism.

**Rollout considerations:** Adding a `created_at` column to `aggregated_data` requires a migration. Partitioning can be added without downtime using PostgreSQL declarative partitioning, but requires careful migration planning.

**Semantics:** Stable. Anchored on `aggregated_data` table schema and `storage/manager.py`.

---

### DB-019: Missing Composite Index for Filter Queries on aggregated_data

| Field | Value |
|-------|-------|
| **ID** | DB-019 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/db/models/aggregated_data.py, src/mkobi/db/repositories/aggregated_data_repo.py |
| **Classification** | advisory |

**Description:** When filtering aggregated data by both dashboard_id and JSONB dims values, the existing composite index `(dashboard_id, graph_id)` may not be optimal. Queries that filter by `dims` would not benefit from existing indexes.

**Validation:** CONFIRMED — `aggregated_data_repo.py` lines 158-162 show filter queries using `dims[key].astext == str(value)`. The existing indexes are:
- `(dashboard_id, graph_id)` — composite B-tree
- `(dims)` — GIN

Neither covers `(dims)` in combination with `dashboard_id` efficiently for path-based JSONB queries (`dims->>'key' = 'value'`). However, the GIN index on `dims` already handles JSONB containment queries well. The path-based queries (`dims[key].astext`) use a different access pattern than GIN supports, but a B-tree index on `(dashboard_id, dims)` would not help either since `dims` is JSONB.

**Assessment:** The finding correctly identifies a potential performance gap. However, the recommended solution (`(dashboard_id, dims)` B-tree composite index) would NOT actually help for `dims[key].astext` queries. This type of query typically requires an expression index like `CREATE INDEX ON aggregated_data USING GIN (dims jsonb_path_ops)` or a B-tree expression index on specific keys. Without knowing which filter keys are common, a generic composite B-tree on `(dashboard_id, dims)` would be low-value.

**Reclassified:** The finding correctly identifies the performance concern but the recommended solution is technically incorrect. Recommend a targeted approach instead:
1. Monitor slow queries involving `dims` filtering
2. Add expression indexes for commonly filtered keys if needed
3. Consider `jsonb_path_ops` GIN index for containment-style filter queries

**Semantics:** Stable. Anchored on `aggregated_data_repo.py` query code.

---

### DB-020: Manual Schema Changes in Starter Module

| Field | Value |
|-------|-------|
| **ID** | DB-020 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/db/starter.py |
| **Classification** | mandatory |

**Description:** The `DatabaseStarter.ensure_admin_user()` method performs direct SQL INSERT using raw SQL text, which technically bypasses Alembic migration tracking. However, this is application initialization logic (data seeding), not schema modification.

**Validation:** CONFIRMED — `ensure_admin_user()` at starter.py lines 300-334 uses raw SQL `INSERT INTO users ... ON CONFLICT (email) DO NOTHING`. The operation is executed within a transaction (`async with db.begin()`).

**Assessment:** This is intentionally application-level data seeding, not a schema change. The SPEC.md design decision #148 explicitly documents this: "Atomic UPSERT for admin user — `ensure_admin_user()` uses `INSERT ... ON CONFLICT (email) DO NOTHING` instead of check-then-create, eliminating the TOCTOU race condition on concurrent startup." The INSERT targets an existing table (created by migrations) and does not alter schema. This is a defensible pattern for idempotent bootstrap data.

**Severity adjustment:** The finding classifies this as HIGH + mandatory, but the SPEC.md explicitly endorses this pattern as a design decision. The "risk of schema drift" is minimal because:
1. The table structure and constraints are defined in migrations
2. The INSERT only touches `users` table which is well-defined
3. The UPSERT pattern is idempotent and safe for concurrent execution
4. This is called at application startup, not ad-hoc

**Reclassification:** Downgrade advisory only, not mandatory. The pattern is intentional and documented. No migration is needed — the code is correct. However, a DOC-UPDATE to clarify in the code comment that this is intentional bootstrap data seeding (not ad-hoc SQL) would improve maintainability.

**Required action:** Add a code comment or docstring note explaining that this is intentional application initialization logic, explicitly linking to SPEC.md design decision #148. This is a **DOC-UPDATE**, not a code change.

---

### DB-021: Missing updated_at Column on graphs Table

| Field | Value |
|-------|-------|
| **ID** | DB-021 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION → RECLASSIFIED TO DOC-UPDATE |
| **Affected Modules** | src/mkobi/db/models/graphs.py, alembic/versions/ffd23f1f7e2b_drop_broken_update_graphs_trigger.py, docs/09-database/schema-core.md |
| **Classification** | advisory |

**Description:** The initial migration created an `updated_at` trigger for the `graphs` table, but the `Graph` model has no `updated_at` column. Migration `ffd23f1f7e2b` drops the broken trigger.

**Validation:** CONFIRMED — `graphs.py` has no `updated_at` column (only `created_at` at line 83). The broken trigger was dropped by `ffd23f1f7e2b`. Critically, the **database documentation** (`docs/09-database/schema-core.md` lines 157-198) explicitly defines the `graphs` table **without** an `updated_at` column. This is by design.

**Assessment:** This is NOT a spec deviation. The documentation schema definition for `graphs` intentionally omits `updated_at` — it only has `created_at`, unlike `users`, `layouts`, `dashboards`, and `processing_configs` which all have `updated_at`. The initial migration's attempt to create a trigger on a non-existent column was the actual bug, and it was correctly fixed by migration `ffd23f1f7e2b`. The current state is intentional and documented.

**Reclassification:** RECLASSIFIED as DOC-UPDATE. The finding itself is based on a misunderstanding — the initial migration's broken trigger was the deviation, and it has already been corrected. The current codebase is consistent with the documented schema. No code change needed.

**Required action:** None. The codebase is correct. If anything, the audit finding itself should be noted as resolved by the existing migration `ffd23f1f7e2b`.

---

### DB-022: No Check Constraints for Business Rules

| Field | Value |
|-------|-------|
| **ID** | DB-022 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/db/models/*.py |
| **Classification** | advisory |

**Description:** Beyond the email length check, there are no CHECK constraints for business rules such as ensuring `metrics` and `dimensions` lists in graphs are non-empty, or validating JSONB structures.

**Validation:** CONFIRMED — The only CHECK constraint is `users_email_length_check`. No constraints exist for:
- `graphs.dimensions` and `graphs.metrics` being non-empty arrays
- `aggregated_data.dims` having at least one key
- `processing_logs` status transitions

**Assessment:** This is a valid observation. However, the application uses Pydantic validation at the API layer and SQLAlchemy defaults (`default=list`, `default=dict`) at the ORM layer. Adding CHECK constraints for array non-emptiness would require PostgreSQL array operators (`array_length(dimensions, 1) > 0`), which adds complexity. For a BI dashboard system at this scale, the ORM-level validation is likely sufficient.

**Severity justification:** MEDIUM is appropriate. This is a defense-in-depth improvement, not a critical gap. The risk is that direct database access (admin tools, manual SQL) could insert invalid data, but normal application flow is protected by Pydantic + ORM validation.

**Rollout considerations:** Adding CHECK constraints requires a migration. Must be done carefully to avoid locking the table on large datasets. Should be tested against existing data to ensure no violations.

**Semantics:** Stable. Anchored on model definitions.

---

## Rejected Findings

### DB-021: Missing updated_at Trigger for graphs Table — REJECTED

**Reason:** Not a spec deviation. The `graphs` table is intentionally designed without an `updated_at` column, as documented in `docs/09-database/schema-core.md`. The initial migration's broken trigger was a bug that was correctly fixed by migration `ffd23f1f7e2b`. The current state is consistent with the documented schema. The finding was based on the assumption that `graphs` should have `updated_at` like other tables, but the documentation explicitly defines it without one.

**Resolution:** No action required. The codebase is correct as-is.

---

## Merged Findings

None. No findings have overlapping root causes or semantically identical recommendations.

---

## Dependency Validation

### Migration Chain (DAG)

```
7130ecb0388c (initial)
  └── ffd23f1f7e2b (drop broken trigger)
        └── a2153f0f6094 (add composite index)
              └── e3b7f4a1c2d5 (add permission default)
                    └── bc892fa3b2ae (rename index)
```

**Status:** VALID — Linear chain, no circular dependencies, no branches. All `down_revision` pointers are correct.

### Cross-Finding Dependencies

| Finding | Depends On | Type |
|---------|-----------|------|
| DB-018 (unbounded growth) | DB-010 (batch ops), DB-011 (UPSERT) | Informational — growth risk is related to data volume from batch/upsert operations |
| DB-019 (missing index) | DB-004 (composite index), DB-005 (GIN index) | Informational — builds on existing index analysis |
| DB-020 (manual SQL) | DB-001 (migration chain) | Informational — the concern is about bypassing the migration system |
| DB-021 (updated_at) | DB-001 (migration chain), DB-017 (type matching) | Informational — relates to migration/model consistency |
| DB-022 (check constraints) | DB-006 (unique constraints), DB-007 (FK constraints), DB-008 (not-null) | Informational — extends the constraint analysis |

**Status:** No circular dependencies detected. All cross-finding relationships are informational, not execution-ordering dependencies.

---

## Rollout Safety Analysis

### Safe to Implement Independently

- **DB-018** (archival strategy) — Can be implemented as a new feature without affecting existing functionality. Requires a new migration for adding `created_at` column.
- **DB-019** (expression index for dims filtering) — Can be added as a new index without affecting existing queries. Use `CREATE INDEX CONCURRENTLY` to avoid locking.
- **DB-020** (code comment for ensure_admin_user) — Pure documentation change, zero risk.
- **DB-022** (CHECK constraints) — Can be added via migration. Must validate existing data first. Use `NOT VALID` + `VALIDATE CONSTRAINT` pattern for zero-downtime rollout.

### Sequencing Recommendations

1. **DB-020** (DOC-UPDATE) — Can be done immediately, no dependencies.
2. **DB-022** (CHECK constraints) — Should be done before DB-018 to ensure data integrity before adding archival logic.
3. **DB-018** (archival strategy) — Should be done after DB-022. Requires careful migration planning.
4. **DB-019** (expression index) — Can be done at any time, independent of other changes.

### Rollout Risks

- **DB-018:** Adding `created_at` column to a potentially large table requires careful migration strategy (add nullable, backfill, add default).
- **DB-019:** Expression indexes on JSONB may have limited benefit depending on actual query patterns. Recommend monitoring first.
- **DB-022:** CHECK constraints could fail if existing data violates the new constraints. Must audit data before applying.

---

## Architectural Consistency Warnings

1. **No warnings for DB-001 through DB-017.** All confirmed positive practices are architecturally sound and consistent with the documented design.

2. **DB-018 warning:** The `aggregated_data` table uses `BIGSERIAL` (not UUID) as its primary key, which is documented and intentional. Any archival strategy must account for this — the `id` column is not a UUID and cannot be used for cross-table correlation without joins.

3. **DB-019 warning:** The `dims` JSONB column uses a custom `JSONBType` TypeDecorator that falls back to plain JSON for non-PostgreSQL databases. Any expression index on `dims` must be PostgreSQL-specific.

4. **DB-022 warning:** The `graphs.dimensions` and `graphs.metrics` columns are typed as `JSONB` in the database but `list[str]` in the ORM. CHECK constraints on these columns would need to use PostgreSQL JSONB array functions (`jsonb_array_length`), not SQL array functions.

---

## Mandatory Fixes

### DB-020: Clarify ensure_admin_user Intent (DOC-UPDATE)

| Field | Value |
|-------|-------|
| **Severity** | HIGH → LOW (downgraded) |
| **Type** | SPEC-DEVIATION → DOC-UPDATE (reclassified) |
| **Action** | Add code comment/docstring to `ensure_admin_user()` linking to SPEC.md design decision #148 |
| **Risk if not addressed** | Future maintainers may mistake intentional bootstrap seeding for ad-hoc SQL and attempt to "fix" it by moving to migrations, which would be unnecessary complexity |

---

## Advisory Recommendations

### DB-018: Implement Archival/Partitioning Strategy for aggregated_data

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Action** | Add `created_at` column, implement retention policy, consider partitioning for high-volume deployments |
| **Priority** | Medium — important for long-running production instances |

### DB-019: Evaluate Expression Index for JSONB dims Filtering

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Action** | Monitor slow queries on `dims` filtering; add expression index for commonly filtered keys if needed |
| **Priority** | Low-Medium — optimize based on observed query patterns |

### DB-022: Add CHECK Constraints for Business Rules

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Action** | Add CHECK constraints for non-empty dimensions/metrics arrays, valid JSONB structures |
| **Priority** | Low — defense-in-depth improvement, ORM validation is primary guard |

---

## Appendix: Validation Methodology

Each finding was validated by:
1. Reading the exact source files referenced in the evidence
2. Verifying line numbers and code snippets match the claims
3. Cross-referencing with SPEC.md and database documentation
4. Checking migration chain integrity (DAG validation)
5. Assessing architectural consistency with Clean Architecture principles
6. Evaluating rollout safety and dependency ordering

All file paths and line references were confirmed against the current codebase state.
