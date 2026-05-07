---
## TASK: Fix Dashboard API Validation and Creation
---

### PROBLEM

Dashboard creation API returns 500 error:
```
'config' is an invalid keyword argument for Dashboard
```

The `DashboardCreate` Pydantic model has a `config` field, but the `Dashboard` SQLAlchemy model doesn't have a `config` column. The service is trying to create `Dashboard(**kwargs)` with `config=...`, which causes an error.

### FILES TO CHECK

- `src/mkobi/api/routes/dashboards.py` (create endpoint)
- `src/mkobi/services/dashboard_service.py` (create_dashboard)
- `src/mkobi/db/repositories/dashboard_repo.py` (create method)
- `src/mkobi/models/dashboard.py` (DashboardCreate, Dashboard SQLAlchemy model)

### ROOT CAUSE

The `config` field in `DashboardCreate` needs to be handled separately (probably stored in `dashboard_configs` table or as JSON in the `Dashboard` model).

### SOLUTION

1. Check how `config` should be stored (JSON column in `dashboards` table, or separate table)
2. Update the dashboard creation logic to handle `config` properly
3. Fix the service and repository methods
4. Update tests to match the correct behavior

### VERIFICATION

1. Run `uv run pytest tests/test_dashboards_api.py::TestCreateDashboard -v`
2. Dashboard creation should return 201 with correct data
3. All dashboard API tests should pass

### PRIORITY

Medium - blocks dashboard creation

### STATUS

- [ ] Issue identified
- [ ] Fix applied
- [ ] Tests passing

---
