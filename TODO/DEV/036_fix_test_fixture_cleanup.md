TASK: Fix test fixture cleanup issues

FILE: tests/conftest.py

GOAL: Fix test fixtures that leave ERROR status due to improper cleanup

IMPLEMENT:

* Review all async fixtures for proper cleanup
* Ensure yield fixtures properly handle exceptions
* Add proper teardown logic for database sessions
* Fix fixtures that don't properly close connections

LOGIC:

1. Review conftest.py fixtures that have yield statements
2. Add try/finally blocks to ensure cleanup happens
3. Ensure database sessions are properly closed even on test failure
4. Check for resource leaks (open connections, uncommitted transactions)

ERROR PATTERN:

* Tests show PASSED but then ERROR in fixture cleanup
* Example: `tests/test_dashboards_api.py::TestCreateDashboard::test_create_dashboard_forbidden ERROR`

DONE:

* [ ] All fixture cleanup errors eliminated
* [ ] Proper exception handling in fixtures
* [ ] No resource leaks in test execution
* [ ] All tests show only PASSED or FAILED (no ERROR)
