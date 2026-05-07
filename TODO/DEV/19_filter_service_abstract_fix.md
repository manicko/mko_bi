---
### TASK: Fix FilterService abstract class instantiation

FILE: src/mkobi/services/filter_service.py, src/mkobi/interfaces/service_interfaces.py

GOAL: Fix "Can't instantiate abstract class FilterService without implementation for abstract methods" error causing filter tests to fail.

ISSUE DESCRIPTION:
1. `FilterService` inherits from `IFilterService` (abstract interface) but does not implement abstract methods correctly:
   - `get_all_filters` (method is named `get_filters` in implementation)
   - `get_filter_by_id` (method is named `get_filter` in implementation)
   - `get_filter_by_name` (missing in implementation)
2. Filter endpoints try to use `FilterService` through backward compatibility wrappers, causing 500 errors.

IMPACT:
- Filter endpoints return 500 Internal Server Error
- Filter tests fail

FILES TO FIX:
- `src/mkobi/services/filter_service.py` - Rename methods to match interface, implement missing `get_filter_by_name`
- `src/mkobi/api/routes/filters.py` - Update function calls if method names changed

IMPLEMENTATION:
1. Rename `get_filters` to `get_all_filters`
2. Rename `get_filter` to `get_filter_by_id`
3. Implement `get_filter_by_name` method
4. Update all callers in the routes file

TESTING:
- [ ] Filter tests pass
- [ ] FilterService can be instantiated without errors

PRIORITY: High (blocks filter functionality)
