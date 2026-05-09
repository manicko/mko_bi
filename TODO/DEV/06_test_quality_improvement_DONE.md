---
## DATA PROCESSING
---

### TASK: Fix Test Architecture Mismatches

FILE: tests/*.py

GOAL: Align tests with current architecture (async/sync, UUID vs int, contracts)

IMPLEMENT:

* Fix sync/async mismatches in tests:
  - Tests calling async functions without await
  - Tests using sync TestClient for async app
  - Missing `@pytest.mark.asyncio` decorators
* Fix UUID vs int usage in tests:
  - Replace `id=1` with `id=uuid.uuid4()`
  - Update fixtures to use UUID
* Fix outdated API contracts in tests
* Remove tests for removed functionality

LOGIC:

1. Search for sync calls to async functions in tests
2. Add `await` and `@pytest.mark.asyncio` where needed
3. Replace all integer IDs with UUID in test fixtures
4. Update test assertions to match current Pydantic models
5. Remove tests that check deleted endpoints or fields
6. Run `uv run pytest tests/` after each fix

DONE:

* [ ] All tests use proper async/sync patterns
* [ ] All test IDs are UUID (not int)
* [ ] Tests match current API contracts
* [ ] Command `uv run pytest tests/` passes
* [ ] No ARCHITECTURE_CONFLICT labeled tests

---

### TASK: Improve Test Quality (Remove Anti-patterns)

FILE: tests/*.py

GOAL: Remove overmocking, weak assertions, and fragile tests

IMPLEMENT:

* Fix overmocking:
  - Replace mocks with real test DB where appropriate
  - Test business logic, not implementation details
* Fix weak assertions:
  - Add meaningful assertions beyond status_code
  - Check database state after operations
  - Check log outputs where relevant
* Fix fragile tests:
  - Remove dependencies on test execution order
  - Remove time/sleep dependencies
  - Make tests fully isolated
* Remove dead tests (no value, no mutation resistance)

LOGIC:

1. Identify tests with excessive mocking (count of patch/mock > 3)
2. Replace with integration tests using test DB
3. Add assertions for:
   - Database state changes
   - Correct business logic execution
   - Proper error handling
4. Run mutation testing conceptually (ask: will test fail if logic changes?)
5. Ensure each test is independent

DONE:

* [ ] Overmocked tests refactored
* [ ] Weak assertions strengthened
* [ ] Fragile tests fixed
* [ ] Dead tests removed
* [ ] Command `uv run pytest tests/ -v` passes

---

### TASK: Add Missing Business Logic Tests

FILE: tests/test_dashboards_api.py, tests/test_data_processing.py, tests/test_filters.py, tests/test_graphs.py

GOAL: Cover edge cases and negative scenarios

IMPLEMENT:

* Add tests for edge cases:
  - Empty data uploads
  - Invalid file types
  - Corrupted CSV files
  - Missing columns in CSV
  - Invalid JSON in config
* Add permission tests:
  - Viewer cannot edit
  - Editor cannot admin
  - User cannot access other's dashboard
* Add error handling tests:
  - Processing failure scenarios
  - Database connection errors
  - File system errors

LOGIC:

1. Review SPEC.md for all business rules
2. Create test cases for each rule
3. Add negative test cases (what should NOT work)
4. Add edge cases (boundary conditions)
5. Run `uv run pytest tests/ --cov=src/mkobi` to check coverage

DONE:

* [ ] Edge cases covered for all major features
* [ ] Permission tests added
* [ ] Error handling tests added
* [ ] Test coverage > 80%
* [ ] All tests pass

---
