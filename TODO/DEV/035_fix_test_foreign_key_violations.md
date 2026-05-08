TASK: Fix foreign key violations in tests

FILE: tests/test_dashboards_api.py

GOAL: Fix foreign key constraint violations in dashboard tests

IMPLEMENT:

* Fix test data setup to create users before creating dashboards
* Ensure created_by field references valid user IDs
* Fix dashboard_access tests to create users before granting access

LOGIC:

1. Review all test fixtures that create dashboards
2. Ensure user is created first and ID is captured
3. Use proper fixture dependencies (user fixture before dashboard fixture)
4. Fix dashboard_access tests to reference valid user IDs

ERRORS OBSERVED:

* `insert or update on table "dashboards" violates foreign key constraint "dashboards_created_by_fkey"`
* `insert or update on table "dashboard_access" violates foreign key constraint "dashboard_access_user_id_fkey"`
* Key (created_by)=(UUID) is not present in table "users"

DONE:

* [ ] All dashboard tests create valid user references
* [ ] Foreign key violations eliminated
* [ ] Test fixtures properly handle dependencies
* [ ] All dashboard API tests pass
