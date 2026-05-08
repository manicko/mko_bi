---
### TASK: Fix UserRead model password_hash access in auth_service

FILE: src/mkobi/services/auth_service.py, src/mkobi/models/user.py

GOAL: Fix AttributeError when accessing password_hash on UserRead model

ERROR:
```
AttributeError: 'UserRead' object has no attribute 'password_hash'
```

ISSUE:
In `src/mkobi/services/auth_service.py:190`, the code tries to access `user_obj.password_hash` where `user_obj` is a `UserRead` object. However, `UserRead` model doesn't expose `password_hash` (which is correct for security reasons).

The issue is that the service is using the wrong model/schema to access the password hash for verification.

IMPLEMENT:
* Fix auth_service.py to use the database model (User) instead of UserRead schema when verifying passwords
* Or use a separate method/repository query that returns the password hash

LOGIC:
1. In `auth_service.py`, modify `login_user` method to fetch user from database directly (not through UserRead schema)
2. Use `UserRepository.get_by_email()` which should return the database model with `password_hash`
3. Verify password using the hash from database model

DONE:
* [ ] auth_service.py uses correct model for password verification
* [ ] Login tests pass
* [ ] UserRead model doesn't expose password_hash (security)

REFERENCE:
* `src/mkobi/services/auth_service.py:190`
* `src/mkobi/models/user.py` - UserRead model
* `tests/test_auth.py::TestLogin`
---

### TASK: Add delete method to RegistrationRequestRepository

FILE: src/mkobi/db/repositories/registration_request_repo.py

GOAL: Add missing delete method to RegistrationRequestRepository

ERROR:
```
AttributeError: 'RegistrationRequestRepository' object has no attribute 'delete'
```

ISSUE:
The `RegistrationRequestRepository` class is missing a `delete` method, but tests expect it to exist.

IMPLEMENT:
* Add `delete` method to RegistrationRequestRepository
* Method should delete a registration request by ID

LOGIC:
1. Add async `delete` method that takes `id` and `db` session
2. Use SQLAlchemy delete query
3. Return True if deleted, False if not found

DONE:
* [ ] delete method added to RegistrationRequestRepository
* [ ] Tests pass

REFERENCE:
* `src/mkobi/db/repositories/registration_request_repo.py`
* `tests/test_auth.py::TestRegisterRequest`
---
