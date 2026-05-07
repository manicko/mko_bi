---
### TASK: Add unique constraint for aggregated_data UPSERT

FILE: src/mkobi/data/storage/manager.py, alembic/versions/

GOAL: Fix "there is no unique or exclusion constraint matching the ON CONFLICT specification" error in storage manager.

ISSUE DESCRIPTION:
The storage manager uses UPSERT (INSERT ... ON CONFLICT) with conflict target `(dashboard_id, graph_id, dims)`, but there is no unique constraint on these columns.

SQL Error:
```
asyncpg.exceptions.InvalidColumnReferenceError: there is no unique or exclusion constraint matching the ON CONFLICT specification
[SQL: INSERT INTO aggregated_data (dashboard_id, graph_id, dims, metrics) 
 VALUES ($1, $2, $3, $4) ON CONFLICT (dashboard_id, graph_id, dims) DO UPDATE SET metrics = excluded.metrics]
```

IMPACT:
- Storage manager tests fail
- Cannot save aggregated data with UPSERT logic

FILES TO FIX:
- Create alembic migration to add unique constraint on `(dashboard_id, graph_id, dims)` in `aggregated_data` table
- Possibly update `src/mkobi/db/models/aggregated_data.py` to define the constraint

IMPLEMENTATION:
1. Create alembic migration:
   ```sql
   CREATE UNIQUE INDEX idx_aggregated_data_upsert 
   ON aggregated_data (dashboard_id, graph_id, (dims::text));
   ```
   Note: `dims` is JSONB, so we need to cast to text for the index.
   Or use a GIN-like approach if needed.

2. Alternative: Use `(dashboard_id, graph_id, md5(dims::text))` as unique constraint.

TESTING:
- [ ] Storage manager tests pass
- [ ] UPSERT works correctly

PRIORITY: High (blocks data storage functionality)
