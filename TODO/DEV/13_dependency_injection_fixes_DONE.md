---
## DEPENDENCY INJECTION FIXES
---

### TASK: Fix Dependency Injection Type Annotations

FILE: `src/mkobi/api/deps.py`

GOAL: Fix FastAPI compatibility issues with interface types in dependency injection

ISSUE DESCRIPTION:

1. **FastAPI cannot process interface types in type annotations**:
    - FastAPI scans type annotations and tries to create Pydantic models from them
    - Interface types like `IUserRepository`, `IUserService` etc. are not valid Pydantic types
    - Error: `fastapi.exceptions.FastAPIError: Invalid args for response field! Hint: check that <class 'mkobi.interfaces.repository_interfaces.IUserRepository'> is a valid Pydantic field type`

2. **Import chain causing failure**:
    - `tests/conftest.py` → `mkobi.main` → `mkobi.app` → `mkobi.api.routes` → `mkobi.api.deps`
    - `deps.py` imports interface types at module level
    - FastAPI scans these during route registration

3. **Affected components**:
    - All route files that use dependency injection
    - Test suite cannot run due to import errors

IMPACT:
- Cannot run tests
- Cannot start the application
- Breaks FastAPI's dependency injection system

FILES TO FIX:
- `src/mkobi/api/deps.py` - Remove interface types from type annotations or use `Annotated` properly
- Possibly `src/mkobi/api/routes/*.py` - Check for similar issues

ROOT CAUSE:
FastAPI's `add_api_route` calls `get_dependant()` which uses `analyze_param()` to process function signatures. When it encounters type annotations with interface types, it tries to create Pydantic fields from them, which fails.

IMPLEMENTATION OPTIONS:

1. **Remove return type annotations from DI functions** (Simplest):
   ```python
   # BEFORE:
   def get_user_repository() -> IUserRepository:
       ...

   # AFTER:
   def get_user_repository():
       """DI factory for user repository."""
       from mkobi.db.repositories.user_repo import UserRepository
       return UserRepository()
   ```

2. **Use `from __future__ import annotations` + string annotations**:
   - Already attempted, but FastAPI still processes some annotations

3. **Use `Annotated` with proper type hints for FastAPI**:
   ```python
   from typing import Annotated
   from mkobi.interfaces import IUserRepository

   def get_user_repository() -> Annotated[IUserRepository, "DI factory"]:
       ...
   ```

4. **Move interface imports inside functions only** (Recommended):
   - Keep interface types for type checking (mypy)
   - Don't expose them at module level where FastAPI scans

RECOMMENDED APPROACH:
- Remove return type annotations from all DI factory functions in `deps.py`
- Keep the interface imports for static type checking
- Use `# type: ignore` or proper mypy configuration if needed

IMPLEMENTATION STEPS:

1. Remove return type annotations from all DI factory functions:
   - `get_user_repository()`
   - `get_dashboard_repository()`
   - `get_access_repository()`
   - `get_aggregated_data_repository()`
   - `get_filter_repository()`
   - `get_processing_config_repository()`
   - `get_processing_log_repository()`
   - `get_graph_repository()`
   - `get_auth_service()`
   - `get_user_service()`
   - `get_dashboard_service()`
   - `get_filter_service()`
   - `get_data_service()`
   - `get_processing_config_service()`
   - `get_processing_log_service()`

2. Verify no type annotations expose interface types to FastAPI

3. Run `uv run ruff check src/mkobi/api/deps.py` to verify syntax

4. Run `uv run mypy src/mkobi/api/deps.py` to verify types still work

5. Run `uv run pytest tests/test_users_api.py -v` to verify tests work

TESTING:
- [ ] All DI functions work without type annotation errors
- [ ] FastAPI app can start without import errors
- [ ] All route tests pass
- [ ] mypy passes with proper type checking

PRIORITY: High (blocking all tests)

SPEC REFERENCE:
- Architecture: Dependency Injection pattern
- Code standards: Type hints, Clean code

EXAMPLE FIX:
```python
# BEFORE:
def get_user_repository() -> IUserRepository:
    """DI factory for user repository."""
    from mkobi.db.repositories.user_repo import UserRepository
    return UserRepository()

# AFTER:
def get_user_repository():
    """DI factory for user repository.

    Returns:
        UserRepository: User repository implementation.
    """
    from mkobi.db.repositories.user_repo import UserRepository
    return UserRepository()
```

NOTES:
- This is a pre-existing issue not related to task 12 (API route fixes)
- The interface types are correctly defined, but FastAPI cannot process them
- Consider using a separate type stubs file (.pyi) for mypy if needed
- Another option: use Protocol classes instead of ABC for interfaces (FastAPI handles them better)
