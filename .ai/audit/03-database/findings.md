# Phase 03 Audit Findings — Database Architecture

**Executor:** audit-executor
**Template:** `.ai/audit/templates/audit-findings.md`
**Status:** complete
**Validated:** no

---

## Findings

### DB-01: Migration Chain Contains a Branch (Merge Point)

| Field | Value |
|-------|-------|
| **ID** | DB-01 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `alembic/versions/` |
| **Classification** | mandatory |

**Description:** The migration chain has a branch point at revision `ffd23f1f7e2b`, which split into two independent branches (`a2153f0f6094` and `a1b2c3d4e5f6`) that were later merged at `64730d3d3446`. The merge revision `64730d3d3446` has empty `upgrade()` and `downgrade()` — it is a no-op bookmark only. Branching in Alembic migrations is an anti-pattern: it means some environments may have applied one branch but not the other, the `downgrade()` path is ambiguous, and the auto-merge revision provides no safety for environments that were on one branch before the merge was introduced.

**Evidence:**
- `alembic history --verbose` output shows `ffd23f1f7e2b` marked as `(branchpoint)` with `Branches into: a2153f0f6094, a1b2c3d4e5f6`
- `64730d3d3446` is a mergepoint with `down_revision: ("bc892fa3b2ae", "a1b2c3d4e5f6")` and empty upgrade/downgrade bodies
- File: `alembic/versions/64730d3d3446_merge_branches_for_force_password_.py` lines 17-19: `def upgrade() -> None: pass` — no verification or reconciliation logic
- File: `alembic/versions/a1b2c3d4e5f6_add_force_password_change_to_user.py` created 2026-05-31, branched from `ffd23f1f7e2b` independently
- File: `alembic/versions/a2153f0f6094_add_composite_index_aggregated_data.py` created 2026-05-20, also branched from `ffd23f1f7e2b`

**Recommendation:** Keep migration chains strictly linear. When concurrent migrations are being developed, coordinate to use sequential `down_revision` pointers. Never create merge revisions. To fix this existing branch, squash the four migrations (`ffd23f1f7e2b`, `a2153f0f6094`, `e3b7f4a1c2d5`, `a1b2c3d4e5f6`, `bc892fa3b2ae`, `64730d3d3446`) into a single new linear migration after `7130ecb0388c`.

---

### DB-02: ORM Model vs. Database Schema Drift — Unique Constraints vs. Unique Indexes Mismatch

| Field | Value |
|-------|-------|
| **ID** | DB-02 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `src/mkobi/db/models/dashboard.py`, `src/mkobi/db/models/filters.py`, `src/mkobi/db/models/layout.py`, `src/mkobi/db/models/user.py`, `src/mkobi/db/models/graphs.py` |
| **Classification** | mandatory |

**Description:** `alembic check` (drift detection) reports that the ORM model definitions expect `UniqueConstraint` objects (via SQLAlchemy's `unique=True` on `mapped_column`), while the current database schema has standalone `CREATE UNIQUE INDEX` statements. This means:
- `alembic check` always reports drift, making it useless as a CI gate.
- Any future autogenerate migration would replace all unique indexes with `UniqueConstraint` objects, dropping and recreating them — a destructive no-op change that wastes time and risks locks on production tables.

The drift affects 5 tables: `dashboards`, `filters`, `graphs`, `layouts`, `users`.

**Evidence:**
- `uv run alembic check` output:
  - `Detected removed index 'idx_dashboards_name' on 'dashboards'` / `Detected added UniqueConstraint None on '('name',)'`
  - `Detected removed index 'idx_filters_name' on 'filters'` / `Detected added UniqueConstraint None on '('name',)'`
  - `Detected removed index 'idx_graphs_dashboard_name' on 'graphs'` / `Detected added UniqueConstraint 'idx_graphs_dashboard_name' on '('dashboard_id', 'name')'`
  - `Detected removed index 'idx_layouts_name' on 'layouts'` / `Detected added UniqueConstraint None on '('name',)'`
  - `Detected removed index 'idx_users_email' on 'users'` / `Detected added UniqueConstraint None on '('email',)'`
  - `Detected removed index 'idx_users_role' on 'users'` / `Detected added index 'ix_users_role'`
- ORM models declare `unique=True` on columns:
  - `src/mkobi/db/models/dashboard.py:43`: `name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)`
  - `src/mkobi/db/models/filters.py:43`: `name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)`
  - `src/mkobi/db/models/layout.py:40`: `name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)`
  - `src/mkobi/db/models/user.py:40`: `email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)`
  - `src/mkobi/db/models/graphs.py:106`: `UniqueConstraint("dashboard_id", "name", name="idx_graphs_dashboard_name")`
- But the migration creates them via raw SQL: `CREATE UNIQUE INDEX idx_dashboards_name ON dashboards (name)` (file `alembic/versions/7130ecb0388c_true_initial_migration.py:101`)
- In PostgreSQL, `CREATE UNIQUE INDEX` and `UNIQUE CONSTRAINT` are functionally similar but structurally different — SQLAlchemy's autogenerate sees them as different objects.

**Recommendation:** Choose one pattern and make the migration match the ORM. Either: (a) Remove `unique=True` from ORM `mapped_column` calls and keep raw `CREATE UNIQUE INDEX` in migrations, OR (b) Replace the raw SQL `CREATE UNIQUE INDEX` calls in the initial migration with `op.create_index()` / `op.create_unique_constraint()` that aligns with SQLAlchemy's representation. Option (b) is preferred for consistency with the ORM and autogenerate.

---

### DB-03: Missing Index on `dashboards.layout_id` Foreign Key Column

| Field | Value |
|-------|-------|
| **ID** | DB-03 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/db/models/dashboard.py` |
| **Classification** | advisory |

**Description:** The `dashboards` table has a foreign key column `layout_id` referencing `layouts(id)`, but there is no index on this column. Every query that joins `dashboards` with `layouts` (the `DashboardRepository.get_by_user` and `DashboardRepository.get` methods use `selectinload(dashboard.layout)`) must perform a sequential scan on the `layouts` table for each dashboard, or a sequential scan on `dashboards` when filtering by layout. As the `dashboards` table grows, this becomes a significant performance problem.

**Evidence:**
- `psql` query for indexes on `dashboards` returns only `dashboards_pkey` and `idx_dashboards_name` (2 indexes, 0 on `layout_id`)
- `pg_indexes` query filtering `layout_id` returns empty
- ORM relationship: `src/mkobi/db/models/dashboard.py:98-102`: `layout: Mapped[Layout | None] = relationship("Layout", back_populates="dashboards", lazy="selectin")`
- FK constraint exists: `dashboards_layout_id_fkey` on `dashboards.layout_id`
- Repository queries join/load layout frequently: `src/mkobi/db/repositories/dashboard_repo.py:44`, `src/mkobi/db/repositories/dashboard_repo.py:76`

**Recommendation:** Add `idx_dashboards_layout_id` index on `dashboards(layout_id)` via a new Alembic migration. This is a standard best practice for all foreign key columns in PostgreSQL.

---

### DB-04: Missing Index on `dashboards.created_by` Foreign Key Column

| Field | Value |
|-------|-------|
| **ID** | DB-04 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/db/models/dashboard.py` |
| **Classification** | advisory |

**Description:** The `dashboards.created_by` column is a foreign key to `users(id)` with no index. While there are currently no repository queries filtering directly by `created_by`, audit trails and admin dashboards commonly need to find "all dashboards created by user X." Without an index, this requires a full table scan on `dashboards`.

**Evidence:**
- `dashboards_created_by_fkey` constraint exists in the database (from `pg_constraint` query)
- No index on `created_by` visible in `pg_indexes` for the `dashboards` table
- FK definition: `src/mkobi/db/models/dashboard.py:62-65`: `created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)`

**Recommendation:** Add `idx_dashboards_created_by` index on `dashboards(created_by)` via a new Alembic migration.

---

### DB-05: Missing Index on `registration_requests.reviewed_by` Foreign Key Column

| Field | Value |
|-------|-------|
| **ID** | DB-05 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/db/models/registration_request.py` |
| **Classification** | advisory |

**Description:** The `registration_requests.reviewed_by` column has a foreign key to `users(id)` but no index. Admin queries to find "all registration requests reviewed by user X" or to join reviewer data will require full table scans.

**Evidence:**
- `registration_requests_reviewed_by_fkey` constraint exists in `pg_constraint`
- `pg_indexes` for `registration_requests` only shows `pkey` and `email_key` — no index on `reviewed_by`
- FK definition: `src/mkobi/db/models/registration_request.py:65-68`

**Recommendation:** Add `idx_registration_requests_reviewed_by` index on `registration_requests(reviewed_by)`.

---

### DB-06: Redundant Duplicate Index on `dashboard_filters`

| Field | Value |
|-------|-------|
| **ID** | DB-06 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/db/models/filters.py`, `alembic/versions/bc892fa3b2ae_rename_idx_dashboard_filters.py` |
| **Classification** | advisory |

**Description:** The `dashboard_filters` table has two identical indexes on the same `(dashboard_id, filter_id)` columns: the primary key `dashboard_filters_pkey` and the secondary index `idx_dashboard_filters_dashboard_id`. Since the primary key already provides a B-tree index on these exact columns, the secondary index is 100% redundant — it doubles write overhead on every INSERT/DELETE to `dashboard_filters` while providing zero additional read performance.

**Evidence:**
- `pg_indexes` output:
  - `dashboard_filters_pkey | CREATE UNIQUE INDEX dashboard_filters_pkey ON public.dashboard_filters USING btree (dashboard_id, filter_id)`
  - `idx_dashboard_filters_dashboard_id | CREATE INDEX idx_dashboard_filters_dashboard_id ON public.dashboard_filters USING btree (dashboard_id, filter_id)`
- The primary key index already covers all lookups on `(dashboard_id, filter_id)`, individual `dashboard_id` lookups (prefix), and `dashboard_id` range scans
- Migration `bc892fa3b2ae` renamed the index but did not remove the redundancy
- Model definition in `src/mkobi/db/models/filters.py:83-88`: `Table("dashboard_filters", ..., Column("dashboard_id", ..., primary_key=True), Column("filter_id", ..., primary_key=True), Index("idx_dashboard_filters_dashboard_id", "dashboard_id", "filter_id"))`

**Recommendation:** Drop the redundant `idx_dashboard_filters_dashboard_id` index via a new migration. Remove the `Index(...)` declaration from `src/mkobi/db/models/filters.py:88`. The primary key already serves all query patterns.

---

### DB-07: `force_password_change` Column Missing from Test Database

| Field | Value |
|-------|-------|
| **ID** | DB-07 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `tests/conftest.py`, `src/mkobi/db/starter.py`, `src/mkobi/db/models/user.py` |
| **Classification** | mandatory |

**Description:** The production database (`bidb`) has 61 columns across all tables, while the test database (`bidb_test`) has only 60. The `force_password_change` column (added in migration `a1b2c3d4e5f6`) exists in production but is missing from the test database. This means tests do not run against a schema that matches production, and any code path that reads/writes `force_password_change` (e.g., `AuthService.change_password`, `AuthService.reset_password_admin`) will fail in production if it hasn't been caught in tests.

**Evidence:**
- Production DB `information_schema.columns` query returns 61 rows including `force_password_change | boolean | false`
- Test DB `information_schema.columns` query returns 60 rows — no `force_password_change` column
- The `setup_test_database` fixture in `tests/conftest.py:287-309` calls `DatabaseStarter.recreate_test_database()` which should apply all migrations, but the test DB on port 5433 clearly hasn't been recreated since the merge migration was added
- The `down_revision` pointers in the merge create an ambiguity: when the test DB was recreated, it may have only applied one branch (`a2153f0f6094 → bc892fa3b2ae`) but not the other (`a1b2c3d4e5f6`)
- Migration `a1b2c3d4e5f6` is the only migration that adds `force_password_change`

**Recommendation:** Immediately recreate the test database to ensure it matches the latest migration: `docker compose -f docker/docker-compose.test.yml exec test-app alembic upgrade head`. Add CI validation that `alembic check` passes before every test run. The merge in DB-01 likely caused the test DB recreation to miss one branch.

---

### DB-08: `processing_logs` and `registration_requests` Receive High Sequential Scans with No Supporting Indexes for Common Query Patterns

| Field | Value |
|-------|-------|
| **ID** | DB-08 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/db/models/processing_logs.py`, `src/mkobi/db/repositories/processing_log_repo.py` |
| **Classification** | advisory |

**Description:** `processing_logs` has 951 sequential scans — the highest of any table — with 0 index scans. While `idx_processing_logs_dashboard_id` exists, the table is likely queried by `status` (e.g., finding all PROCESSING or FAILED entries) which has no index. The `update_processing_log` worker function queries by primary key, but dashboard-level queries for "show me all processing logs" filter by `dashboard_id` and often additionally by `status`.

**Evidence:**
- `pg_stat_user_tables`: `processing_logs | 951 seq_scan | 0 idx_scan`
- Model has only one non-PK index: `idx_processing_logs_dashboard_id` (file `src/mkobi/db/models/processing_logs.py:67-68`)
- No index on `status` column despite frequent status-based filtering (processing, success, failed)
- `cleanup_stale_processing_logs` in `src/mkobi/workers/data_worker.py:108-111` filters by `status = 'processing' AND started_at < cutoff` — a query that would benefit from a composite index on `(status, started_at)`

**Recommendation:** Add a composite index on `processing_logs(status, started_at)` to support the cleanup worker pattern. Consider adding an index on `(dashboard_id, status)` for dashboard log listing queries.

---

### DB-09: DashboardService.create_dashboard Commits Implicitly with No Explicit Rollback on Access Grant Failure

| Field | Value |
|-------|-------|
| **ID** | DB-09 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/services/dashboard_service.py` |
| **Classification** | mandatory |

**Description:** In `DashboardService.create_dashboard`, the dashboard is created via `self.dashboard_repo.create()` which calls `db.flush()` but does not commit. Then `self.access_repo.grant_access()` is also flushed but not committed. The calling route handler (`dashboards_crud.py:125`) calls `db.commit()`. If the dashboard creation succeeds but the access grant fails, there is no explicit rollback — the dashboard object remains in the session as a pending insert. The route handler's rollback may or may not handle this depending on the session state. This is a partial-write risk: a dashboard could be created without the owner's access record.

**Evidence:**
- `src/mkobi/services/dashboard_service.py:82-117`: `create_dashboard` calls `self.dashboard_repo.create(db=db)` then `self.access_repo.grant_access(db=db, ...)` — both flush-only, no commit/rollback within the service
- `src/mkobi/api/routes/dashboards_crud.py:125`: `await db.commit()` — called after the service, outside the service's control
- The service has explicit rollback code for the outer exception handler (line 123), but the access grant failure path through the route handler does not guarantee atomicity
- Contrast with `AuthService.register_request` (`auth_service.py:437`) which calls `db.commit()` explicitly within the service

**Recommendation:** Either wrap both operations in a single explicit transaction boundary (`async with db.begin():`) within the service, or ensure the route handler's rollback is always called on any exception. The most robust pattern is to have the service manage its own transaction.

---

### DB-10: Storage Service Creates Model Object Outside Transaction, References It After Potential Rollback

| Field | Value |
|-------|-------|
| **ID** | DB-10 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/services/layout_service.py` |
| **Classification** | advisory |

**Description:** In `LayoutService.create_layout`, a `Layout` model object is created and added via the repository at line 63, then `db.commit()` is called at line 64. If commit fails, the exception handler rolls back, but the code then tries to access `layout_obj.id` at line 69 (`LayoutRead.model_validate(layout_obj)`) — which is reachable only if commit succeeds. However, if commit raises an exception after the object was temporarily assigned an ID during flush, the object may be in a detached or invalid state. The pattern is fragile.

**Evidence:**
- `src/mkobi/services/layout_service.py:62-74`: `layout_obj = await self.layout_repo.create(...)` → `await db.commit()` → `LayoutRead.model_validate(layout_obj)` — if commit throws, `layout_obj` could be in an inconsistent state
- The `if layout_obj is None` check at line 66 is unreachable for a normal `create` flow (the repo raises on error rather than returning None)

**Recommendation:** Restructure to use `async with db.begin():` pattern for transaction safety, and only reference the committed object after the transaction context exits successfully.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 3 |
| MEDIUM | 7 |
| LOW | 0 |

## Mandatory Fixes

- **DB-01**: Eliminate migration branch — squash into a single linear migration
- **DB-02**: Align unique constraints between ORM models and migration SQL so `alembic check` passes cleanly
- **DB-07**: Recreate test database to include `force_password_change` column; add CI gate for `alembic check`
- **DB-09**: Wrap `create_dashboard` operations in an explicit transaction boundary to ensure atomicity

## Advisory Recommendations

- **DB-03**: Add index on `dashboards(layout_id)`
- **DB-04**: Add index on `dashboards(created_by)`
- **DB-05**: Add index on `registration_requests(reviewed_by)`
- **DB-06**: Drop redundant `idx_dashboard_filters_dashboard_id` index (PK already covers it)
- **DB-08**: Add composite indexes on `processing_logs(status, started_at)` and `(dashboard_id, status)`
- **DB-10**: Restructure `create_layout` to use `async with db.begin()` transaction pattern

## Doc Updates Needed

None.
