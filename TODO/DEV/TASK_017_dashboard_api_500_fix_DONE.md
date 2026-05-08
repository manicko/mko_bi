---
### TASK: Fix Dashboard API 500 Internal Server Error

FILE: src/mkobi/api/routes/dashboards.py, src/mkobi/services/dashboard_service.py

GOAL: Fix 500 Internal Server Error on Dashboard API endpoints

ERROR:
```
assert 500 == 200
assert 500 == 201
```

ISSUE:
Multiple Dashboard API endpoints return 500 Internal Server Error:
- GET /dashboards/my
- GET /dashboards/{id}
- POST /dashboards/
- PUT /dashboards/{id}

This indicates unhandled exceptions in the dashboard service or repository layer.

IMPLEMENT:
* Debug and fix the cause of 500 errors in dashboard endpoints
* Check dashboard service and repository for bugs
* Ensure proper error handling

LOGIC:
1. Check FastAPI logs for the actual exception causing 500
2. Fix the root cause in dashboard service or repository
3. Add proper error handling with meaningful error messages
4. Verify all dashboard API tests pass

DONE:
* [ ] Root cause of 500 error identified
* [ ] Dashboard service/repository fixed
* [ ] All dashboard API tests pass

REFERENCE:
* `src/mkobi/api/routes/dashboards.py`
* `src/mkobi/services/dashboard_service.py`
* `src/mkobi/db/repositories/dashboard_repo.py`
* `tests/test_dashboards_api.py`
---
