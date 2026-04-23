# Task: Data Storage Manager

## Goal
Save aggregated data to PostgreSQL database

## Implementation Details

### Files to Modify
- `src/mko_bi/data/storage/manager.py`

### Functions to Implement

#### get_db_engine() -> create_engine
- **Input**: None (reads from config)
- **Output**: SQLAlchemy engine
- **Logic**: Create and return database engine

#### init_db()
- **Input**: None
- **Output**: None
- **Logic**: Create database tables if they don't exist
- Creates `aggregates` table

#### save_aggregates(dashboard_id: int, df: pl.DataFrame) -> bool
- **Input**: Dashboard ID, aggregated DataFrame
- **Output**: Success boolean
- **Logic**:
  1. Convert DataFrame to dict
  2. Create table if not exists
  3. Upsert data (overwrite if exists)
  4. Use ON CONFLICT for PostgreSQL
  5. Return success

#### get_aggregates(dashboard_id: int) -> Optional[pl.DataFrame]
- **Input**: Dashboard ID
- **Output**: DataFrame or None
- **Logic**:
  1. Query latest aggregates for dashboard
  2. Convert from JSON to DataFrame
  3. Return DataFrame or None

### Database Schema
```sql
CREATE TABLE aggregates (
    id SERIAL PRIMARY KEY,
    dashboard_id INTEGER NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Error Handling
- Handle database connection errors
- Handle data conversion errors
- Handle constraint violations

### Testing
- Test database connection
- Test table creation
- Test data save and retrieve
- Test upsert behavior
- Test with empty DataFrame