TASK: Fix DataService abstract class instantiation

FILE: src/mkobi/services/data_service.py, src/mkobi/api/routes/upload.py

GOAL: Fix "Can't instantiate abstract class DataService without implementation for abstract methods" error causing upload tests to fail.

ISSUE DESCRIPTION:
1. `DataService` inherits from `IDataService` (abstract interface) but does not implement abstract methods:
   - `get_available_dimensions`
   - `get_available_metrics`
2. Upload endpoint tries to instantiate `DataService` directly, causing 500 errors.

IMPACT:
- Upload endpoints return 500 Internal Server Error
- Upload tests fail

FILES TO FIX:
- `src/mkobi/services/data_service.py` - Implement abstract methods or make DataService non-abstract
- `src/mkobi/api/routes/upload.py` - Ensure correct service usage

IMPLEMENTATION:
1. Implement missing abstract methods in DataService:
   ```python
   async def get_available_dimensions(self, dashboard_id: UUID) -> list[str]:
       # Implementation here
       pass

   async def get_available_metrics(self, dashboard_id: UUID) -> list[str]:
       # Implementation here
       pass
   ```
2. Or modify IDataService to remove unnecessary abstract methods if they are not required.

TESTING:
- [ ] Upload tests pass
- [ ] DataService can be instantiated without errors

PRIORITY: High (blocks upload functionality)
