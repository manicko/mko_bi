---
### TASK: Add delete method to RegistrationRequestRepository
FILE: src/mkobi/db/repositories/registration_request_repo.py
GOAL: Fix `AttributeError: 'RegistrationRequestRepository' object has no attribute 'delete'`
IMPLEMENT:
* Add `delete()` method to `RegistrationRequestRepository` class
* Method should delete by ID and return boolean (True if deleted, False if not found)
* Follow the pattern of other repository `delete()` methods
LOGIC:
1. Check `src/mkobi/db/repositories/registration_request_repo.py` for existing methods
2. Add `async def delete(self, id: UUID, db: AsyncSession) -> bool:` method
3. Follow the pattern from `dashboard_repo.py` or `user_repo.py`
4. Verify method works by running failing tests
DONE:
* [ ] Method implemented
* [ ] `uv run pytest tests/test_auth.py::TestRegisterRequest -v` passes
---
