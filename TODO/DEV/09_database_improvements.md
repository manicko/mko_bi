---
## DATA PROCESSING
---

### TASK: Database Migration & Reproducibility

FILE: src/mkobi/db/starter.py, alembic/versions/*.py, alembic/env.py

GOAL: Ensure database schema is reproducible and migrations are safe

IMPLEMENT:

* Verify migration chain integrity:
  - `alembic upgrade head` works on empty database
  - No broken revisions
  - No circular dependencies
* Check migration safety:
  - No manual SQL changes without migration
  - No non-idempotent migrations
  - No state-dependent migrations
  - No mixing schema/data migrations
* Verify Alembic configuration:
  - Proper async support
  - Correct migration script location
* Check db/starter.py:
  - Proper environment detection (ENV variable)
  - Production: no auto-migrate without explicit flag
  - Test: allows database recreation
  - Idempotent: repeated runs don't fail
  - Proper logging (INFO/ERROR)

LOGIC:

1. Test migration from scratch: drop DB, run `alembic upgrade head`
2. Verify all migrations apply cleanly
3. Check starter.py for production safety
4. Ensure test DB isolation
5. Add migration tests if missing

DONE:

* [ ] `alembic upgrade head` works on empty DB
* [ ] No broken migrations
* [ ] starter.py production-safe
* [ ] Test DB isolation verified
* [ ] Migration audit passes

---

### TASK: Database Index & Performance

FILE: src/mkobi/db/models/*.py, alembic/versions/*.py

GOAL: Ensure proper indexing for performance

IMPLEMENT:

* Verify required indexes exist:
  - `idx_aggregated_data_graph_id`
  - `idx_aggregated_data_dashboard_id`
  - `idx_aggregated_data_dashboard_graph` (composite)
  - `idx_aggregated_data_dims_gin` (GIN for JSONB)
  - `idx_dashboard_access_user`
  - `idx_dashboard_access_dashboard`
  - `idx_graphs_dashboard`
  - `idx_dashboard_filters_dashboard_filter`
* Check index naming consistency
* Verify foreign key constraints
* Check cascade behavior is correct
* Verify JSONB usage is appropriate

LOGIC:

1. Review all alembic migrations for index creation
2. Compare with SPEC.md requirements
3. Add missing indexes
4. Test query performance with EXPLAIN ANALYZE
5. Verify GIN index works for JSONB filtering

DONE:

* [ ] All required indexes present
* [ ] Index naming consistent
* [ ] Foreign keys verified
* [ ] Cascade behavior correct
* [ ] GIN index functional

---
