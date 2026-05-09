TASK: Fix database test deadlock issues

FILE: tests/conftest.py

GOAL: Fix database deadlocks during test setup/teardown

IMPLEMENT:

* Fix TRUNCATE TABLE statements causing deadlocks
* Use safer table cleanup strategy (drop/create or DELETE with proper ordering)
* Ensure test transactions are properly isolated

LOGIC:

1. Replace CASCADE TRUNCATE with ordered DELETE statements
2. Disable foreign key checks during cleanup if needed
3. Use savepoint-based transactions for better isolation
4. Ensure async test fixtures properly handle cleanup

CONSTRAINTS:

* Must work with PostgreSQL asyncpg driver
* Must not affect production database
* Tests should run in parallel without deadlocks

DONE:

* [ ] Deadlock errors eliminated in test runs
* [ ] All test fixtures properly clean up
* [ ] Tests can run in parallel
* [ ] Test execution time is reasonable
