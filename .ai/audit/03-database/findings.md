# Phase 03 Audit Findings — Database Architecture

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### DB-001: Broken Trigger in Initial Migration for Non-Existent Column

| Field | Value |
|-------|-------|
| **ID** | DB-001 |
| **Severity** | CRITICAL |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | alembic/versions/7130ecb0388c_true_initial_migration.py |
| **Classification** | mandatory |

**Description:** The initial migration `7130ecb0388c_true_initial_migration.py` creates a trigger `update_graphs_updated_at` on the `graphs` table (lines 255-279) that attempts to set an `updated_at` column on every UPDATE operation. However, the `graphs` table definition (lines 91-102) does not include an `updated_at` column. This trigger would cause runtime errors for any UPDATE on the graphs table. While a subsequent migration `ffd23f1f7e2b_drop_broken_update_graphs_trigger.py` drops this trigger, the initial migration remains incorrect, creating an inconsistency in the migration history and potentially causing issues during database recreation from scratch.

**Evidence:**
- `alembic/versions/7130ecb0388c_true_initial_migration.py` lines 255-263: Creates trigger on graphs table
- `alembic/versions/7130ecb0388c_true_initial_migration.py` lines 91-102: graphs table definition - no `updated_at` column
- `alembic/versions/ffd23f1f7e2b_drop_broken_update_graphs_trigger.py` line 26: DROP TRIGGER IF EXISTS `update_graphs_updated_at` ON graphs - acknowledges the broken trigger exists

**Recommendation:** Remove the trigger creation code from the initial migration (lines 255-279) since the `graphs` table does not have an `updated_at` column and likely doesn't need one (no UPDATE operations are expected based on the schema design). This ensures the migration chain is clean and idempotent.

---

### DB-002: Missing GIN Index on `aggregated_data.metrics` Column

| Field | Value |
|-------|-------|
| **ID** | DB-002 |
| **Severity** | HIGH |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/db/models/aggregated_data.py, alembic/versions/7130ecb0388c_true_initial_migration.py |
| **Classification** | advisory |

**Description:** The `aggregated_data` table has a GIN index on the `dims` column (line 162 in migration, line 53 in model) to optimize JSONB containment queries. However, there is no corresponding GIN index on the `metrics` column. If API endpoints ever filter on metrics data (e.g., finding records where a specific metric exceeds a threshold), queries would require full table scans. The repository code in `aggregated_data_repo.py` shows filter operations on `dims` (line 161), but the system architecture should support symmetric querying on both dimension and metric data for flexibility.

**Evidence:**
- `alembic/versions/7130ecb0388c_true_initial_migration.py` line 162: GIN index only on `dims`
- `src/mkobi/db/models/aggregated_data.py` line 53: GIN index only on `dims`
- `docs/09-database/indexes.md` lines 82-84: Documents only `dims` GIN index, mentions it is "critical for filter application"

**Recommendation:** Consider adding a GIN index on the `metrics` column if there's any likelihood of filtering on metric values: `CREATE INDEX IF NOT EXISTS idx_aggregated_data_metrics_gin ON aggregated_data USING GIN (metrics);`

---

### DB-003: Inconsistent Database Role Usage in Test Configuration

| Field | Value |
|-------|-------|
| **ID** | DB-003 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | docker/docker-compose.test.yml, docker/docker-compose.yml |
| **Classification** | advisory |

**Description:** In `docker-compose.test.yml`, the `test-app` service connects to the database using `DATABASE__USER: postgres` (line 90), connecting as the superuser role. However, in production `docker-compose.yml`, the `app` service correctly uses `DATABASE__USER: mkobi_app` (line 84) to connect with limited privileges. This inconsistency means tests don't accurately reflect production security posture - they run with superuser privileges that bypass the row-level security and privilege restrictions that exist in production. This could allow tests to pass while production fails due to permission constraints.

**Evidence:**
- `docker/docker-compose.test.yml` line 90: `DATABASE__USER: postgres` - uses superuser
- `docker/docker-compose.yml` line 84: `DATABASE__USER: mkobi_app` - uses application role
- `docker/init-scripts/01-create-app-role.sh`: Creates `mkobi_app` role with limited privileges (`SELECT, INSERT, UPDATE, DELETE`)

**Recommendation:** Update `docker-compose.test.yml` to use `mkobi_app` role for the `test-app` service: `DATABASE__USER: mkobi_app` and `DATABASE__PASSWORD: ${MKOBI_APP_PASSWORD:-test_app_password}`. This ensures tests run with the same permissions as production.

---

### DB-004: Redundant Index on `aggregated_data` Table

| Field | Value |
|-------|-------|
| **ID** | DB-004 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | alembic/versions/7130ecb0388c_true_initial_migration.py, src/mkobi/db/models/aggregated_data.py |
| **Classification** | advisory |

**Description:** The `aggregated_data` table has both a composite index `idx_aggregated_data_dashboard_graph` on `(dashboard_id, graph_id)` (line 160 in migration, line 52 in model) and separate individual indexes on `idx_aggregated_data_dashboard_id` and `idx_aggregated_data_graph_id`. Since the composite index on `(dashboard_id, graph_id)` can already satisfy queries filtering on `dashboard_id` alone, the individual `idx_aggregated_data_dashboard_id` index is redundant and wastes storage space while adding overhead to INSERT/UPDATE/DELETE operations.

**Evidence:**
- `alembic/versions/7130ecb0388c_true_initial_migration.py` line 160-161: Composite index on `(dashboard_id, graph_id)`
- `alembic/versions/7130ecb0388c_true_initial_migration.py` line 160-161: Individual index on `dashboard_id`
- `docs/09-database/indexes.md` line 6: Documents 7 core indexes, but doesn't account for redundancy

**Recommendation:** Remove the redundant `idx_aggregated_data_dashboard_id` index since `idx_aggregated_data_dashboard_graph` on `(dashboard_id, graph_id)` already covers queries filtering on `dashboard_id` alone. Keep the individual `graph_id` index as queries may filter only by graph_id.

---

### DB-005: Migration Chain Has Repair Migration Instead of Fixing Root Cause

| Field | Value |
|-------|-------|
| **ID** | DB-005 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | alembic/versions/ffd23f1f7e2b_drop_broken_update_graphs_trigger.py, alembic/versions/7130ecb0388c_true_initial_migration.py |
| **Classification** | advisory |

**Description:** The codebase contains a "repair migration" (`ffd23f1f7e2b_drop_broken_update_graphs_trigger.py`) that drops a broken trigger created by the initial migration. While this fixes the issue going forward, it represents technical debt - the migration history should be clean. The correct approach is to fix the initial migration so a fresh database created at that revision doesn't have the bug. This also creates confusion about which migration introduces the trigger and which removes it.

**Evidence:**
- `alembic/versions/ffd23f1f7e2b_drop_broken_update_graphs_trigger.py`: Migration exists solely to drop the incorrectly-created trigger
- `alembic/versions/7130ecb0388c_true_initial_migration.py`: Original migration creates the broken trigger
- Git history would show these as separate changes rather than fixing the root cause

**Recommendation:** Consolidate the trigger fix into the initial migration. Either remove the trigger creation entirely from the initial migration, or add the `updated_at` column to the `graphs` table with its trigger. The repair migration can then be removed.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 1 |
| HIGH | 1 |
| MEDIUM | 2 |
| LOW | 0 |

## Mandatory Fixes

- DB-001: Broken Trigger in Initial Migration for Non-Existent Column — Remove trigger creation for non-existent `updated_at` column on `graphs` table from the initial migration.

## Advisory Recommendations

- DB-002: Missing GIN Index on `aggregated_data.metrics` Column — Add GIN index if metrics filtering is anticipated.
- DB-003: Inconsistent Database Role Usage in Test Configuration — Update test compose to use `mkobi_app` role.
- DB-004: Redundant Index on `aggregated_data` Table — Remove redundant `idx_aggregated_data_dashboard_id` index.
- DB-005: Migration Chain Has Repair Migration Instead of Fixing Root Cause — Fix initial migration to avoid needing repair migration.