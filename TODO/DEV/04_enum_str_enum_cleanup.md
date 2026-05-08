---
## DATA PROCESSING
---

### TASK: Enum/StrEnum Consolidation

FILE: src/mkobi/models/enums.py, src/mkobi/models/user_roles.py

GOAL: Consolidate all enum definitions to use StrEnum in a single source of truth

IMPLEMENT:

* Remove `user_roles.py` aliases (UserRoleEnum, PermissionEnum, etc.)
* Update all 39+ files to import directly from `enums.py`
* Ensure all enum usage follows `UserRole.ADMIN` pattern (not string literals)

LOGIC:

1. Keep `enums.py` as single source of truth for all StrEnum definitions
2. Remove backward compatibility aliases from `user_roles.py`
3. Update all imports across codebase:
   - `from mkobi.models.user_roles import UserRoleEnum` → `from mkobi.models.enums import UserRole`
   - Same for PermissionEnum, GraphTypeEnum, FilterTypeEnum, ProcessingStatusEnum
4. Run `uv run ruff check .` and `uv run mypy .` to verify

DONE:

* [ ] All enum imports use `enums.py` directly
* [ ] `user_roles.py` removed or contains only deprecated aliases with warnings
* [ ] No enum-related mypy errors
* [ ] All 39+ files updated
* [ ] Tests pass: `uv run pytest tests/`

---

### TASK: YoyModeEnum Attribute Fix

FILE: src/mkobi/models/enums.py, src/mkobi/data/processing/transformations.py

GOAL: Fix YoyModeEnum.percent → YoyModeEnum.PERCENT

IMPLEMENT:

* Fix enum value: `PERCENT = "percent"` (already correct in enums.py)
* Find and fix all usages of `.percent` attribute (should be `.PERCENT`)
* Update any hardcoded "percent" strings to use enum

LOGIC:

1. Search for `YoyModeEnum.percent` or `.percent` in codebase
2. Replace with `YoyModeEnum.PERCENT`
3. Verify no mypy errors related to enum access

DONE:

* [ ] All YoyModeEnum usages use .PERCENT (not .percent)
* [ ] No attr-defined mypy errors for YoyModeEnum
* [ ] Test: `uv run pytest tests/test_yoy_calculation.py`

---
