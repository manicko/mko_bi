---

### TASK: Fix UUID import in dashboards.py

FILE: src/mkobi/api/routes/dashboards.py

GOAL: Fix NameError: name 'UUID' is not defined

ERROR:
```
  File "/app/src/mkobi/api/routes/dashboards.py", line 185, in <module>
    dashboard_id: UUID,
                  ^^^^
NameError: name 'UUID' is not defined
```

ISSUE:
The `UUID` type from `uuid` module is used as a type hint but not imported in the file.

IMPLEMENT:
* Add import: `from uuid import UUID`
* Verify all UUID type hints are properly imported
* Check for similar import issues in the file

LOGIC:
1. Add missing UUID import at the top of the file
2. Verify the import is used correctly with FastAPI path parameters
3. Test that the dashboard routes work correctly

DONE:
* [ ] UUID import added
* [ ] All UUID type hints work correctly
* [ ] Test dashboard API endpoints

---
