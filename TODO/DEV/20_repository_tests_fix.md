---
### TASK: Fix repository test instantiation

FILE: tests/test_repositories.py

GOAL: Fix TypeError in repository tests where Repository classes are called without instantiation.

ISSUE DESCRIPTION:
Tests are calling Repository methods as static/class methods, but they require instance instantiation first:
```
TypeError: UserRepository.create() missing 1 required positional argument: 'self'
TypeError: DashboardRepository.create() missing 1 required positional argument: 'self'
```

LOGIC:
Repository classes in `src/mkobi/db/repositories/` likely require instantiation before calling methods, or the test is calling them incorrectly.

IMPACT:
- All repository tests fail
- Cannot verify repository functionality

FILES TO FIX:
- `tests/test_repositories.py` - Fix test code to properly instantiate repositories or call methods

IMPLEMENTATION:
1. Check if repositories need instantiation (have `self` parameter)
2. Fix tests to either:
   - Instantiate repositories before calling methods, or
   - Make methods static/class methods if appropriate

TESTING:
- [ ] Repository tests pass

PRIORITY: Medium (testing infrastructure)
