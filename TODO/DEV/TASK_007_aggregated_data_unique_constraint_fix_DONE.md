---
## TASK: Add missing unique constraint to aggregated_data table
---

### PROBLEM

The storage manager uses `ON CONFLICT (dashboard_id, graph_id, dims) DO UPDATE` in INSERT statements, but the database is missing the required unique constraint on these columns.

Error observed:
```
sqlalchemy.exc.ProgrammingError: (sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError) 
<class 'asyncpg.exceptions.InvalidColumnReferenceError'>: 
there is no unique or exclusion constraint matching the ON CONFLICT specification
[SQL: INSERT INTO aggregated_data (dashboard_id, graph_id, dims, metrics) 
VALUES ($1::UUID, $2::UUID, $3::JSONB, $4::JSONB) 
ON CONFLICT (dashboard_id, graph_id, dims) DO UPDATE SET metrics = excluded.metrics]
```

### ROOT CAUSE

The `aggregated_data` table is missing a unique constraint on `(dashboard_id, graph_id, dims)` that is required for the `ON CONFLICT` clause to work.

### FILES TO CHECK

- `src/mkobi/db/models/aggregated_data.py` - Model definition
- `alembic/versions/` - Need new migration to add constraint
- `src/mkobi/data/storage/manager.py` - Storage manager using ON CONFLICT

### SOLUTION

1. Create a new Alembic migration to add unique constraint:
   ```sql
   CREATE UNIQUE INDEX IF NOT EXISTS idx_aggregated_data_dashboard_graph_dims 
   ON aggregated_data (dashboard_id, graph_id, dims);
   ```
   Note: GIN index on dims is already present, but we need a composite unique constraint.

2. Update the model if needed to include the constraint definition.

### VERIFICATION

1. Run `uv run alembic upgrade head`
2. Run `uv run pytest tests/test_storage_manager.py -v`
3. Verify constraint exists: `psql -h localhost -p 5432 -U postgres -d bidb_test -c "\d aggregated_data"`

### PRIORITY

High - blocks all storage manager operations

### STATUS

- [ ] Issue identified
- [ ] Migration created
- [ ] Constraint added
- [ ] Tests pass

---
