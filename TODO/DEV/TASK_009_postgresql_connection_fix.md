---
## TASK: Fix PostgreSQL connection for tests
---

### PROBLEM

Tests are failing with `ConnectionRefusedError: [WinError 1225] The remote computer refused the network connection`. The PostgreSQL server is not running or not accessible on localhost:5432.

Error observed:
```
asyncpg.exceptions.ConnectionRefusedError: [WinError 1225] The remote computer refused the network connection
```

### ROOT CAUSE

PostgreSQL server is not running or not configured properly for the test environment.

### FILES TO CHECK

- `tests/conftest.py` - Test database configuration
- `docker-compose.yml` - PostgreSQL service configuration
- Environment variables in conftest.py:
  - DATABASE__HOST: localhost
  - DATABASE__PORT: 5432
  - DATABASE__DBNAME: bidb_test
  - DATABASE__USER: postgres
  - DATABASE__PASSWORD: 1234

### SOLUTION

1. Ensure PostgreSQL server is running on localhost:5432
2. Create test database `bidb_test` if it doesn't exist
3. Apply all migrations to the test database
4. Verify connection settings match the actual PostgreSQL configuration

### VERIFICATION

1. Start PostgreSQL server
2. Run `uv run pytest tests/test_storage_manager.py -v`
3. All tests should pass

### PRIORITY

High - blocks all database-related tests

### STATUS

- [ ] PostgreSQL server running
- [ ] Test database created
- [ ] Migrations applied
- [ ] Tests pass

---
