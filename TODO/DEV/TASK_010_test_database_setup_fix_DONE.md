---
### TASK: Fix test database setup

FILE: tests/conftest.py, src/mkobi/db/starter.py

GOAL: Fix missing test database `bidb_test` causing test failures

ERROR:
```
asyncpg.exceptions.InvalidCatalogNameError: database "bidb_test" does not exist
```

ISSUE:
The test database `bidb_test` does not exist, causing all dashboard API tests to fail.
According to SPEC.md section 22 (Database Initialization), the test database should be 
automatically created when `RECREATE_TEST_DB=true` is set. However, the database 
either doesn't exist or the automatic creation is not working properly.

IMPLEMENT:
* Verify `DatabaseStarter.recreate_test_database()` method works correctly
* Ensure test database is created before running tests
* Add proper error handling if test database creation fails
* Verify `RECREATE_TEST_DB=true` is set in test environment (docker-compose.test.yml)

LOGIC:
1. Check if `bidb_test` database exists in PostgreSQL
2. If not, create it using `DatabaseStarter.recreate_test_database()` or SQL
3. Apply Alembic migrations to the test database
4. Verify tests can connect to `bidb_test`

DONE:
* [ ] Test database `bidb_test` exists
* [ ] Tests can connect to test database
* [ ] All dashboard API tests pass
* [ ] Test database setup documented

REFERENCE:
* SPEC.md section 22: Database Initialization
* docker-compose.test.yml: test environment configuration
* src/mkobi/db/starter.py: DatabaseStarter implementation

---
