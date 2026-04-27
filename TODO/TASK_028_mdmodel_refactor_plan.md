# Model Refactor Plan (Corrected)

## 0. Executive Summary

**Current Issues:**
- `user_roles.py` mixes user roles, permissions, AND chart enums (SRP violation)
- `data.py` contains 11 model classes across 5 different domains (massive SRP violation)  
- `auth.py` duplicates AccessCheck/AccessGrant already in `access.py`
- High coupling: 13 files import from `user_roles.py`, creating circular dependency risk
- SQLAlchemy models in `db/models/` also depend on `user_roles.py`

**Correction Principles:**
- NO overengineering: models.py + schemas.py per module = unnecessary duplication
- Pydantic models ARE schemas — no need to split
- Consolidate cohesive domains (auth + users = identity)
- Keep enums with their consumers
- Address BOTH Pydantic AND SQLAlchemy models
- Max 4 modules to avoid navigation complexity

## 1. Target Structure

```
src/mko_bi/models/
├── __init__.py                    # Re-export all models
├── user_roles.py                  # UserRoleEnum, PermissionEnum (keep)
├── identity/                      # Auth + Users (cohesive domain)
│   ├── __init__.py
│   └── models.py                  # LoginRequest, User*, Token*, etc.
├── dashboards/                    # Dashboard + Charts (cohesive domain)
│   ├── __init__.py
│   └── models.py                  # Dashboard*, Chart*, GraphTypeEnum*, etc.
└── processing/                    # Data upload + processing pipeline
    ├── __init__.py
    └── models.py                  # DataUpload, Processing*, etc.
```

**Why this structure:**
- 3 modules (down from 6) — simpler navigation
- No schemas.py duplication — models serve as schemas
- `user_roles.py` kept for SQLAlchemy enums (see Step 5)
- Cohesive grouping: identity, dashboards, processing

## 2. Step-by-Step Execution Plan

### Step 1: Create New Module Directories
- Create: `src/mko_bi/models/identity/` with `__init__.py`
- Create: `src/mko_bi/models/dashboards/` with `__init__.py`
- Create: `src/mko_bi/models/processing/` with `__init__.py`

### Step 2: Migrate Identity Models (Auth + Users)
**Source files:** `auth.py`, `user.py`  
**Target:** `src/mko_bi/models/identity/models.py`

**Models to move:**
- From `auth.py`: LoginRequest, RegisterRequest, Token, TokenData, RefreshRequest
- From `user.py`: UserBase, UserCreate, UserRead, UserDB, UserUpdate
- From `auth.py` (DUPLICATES): AccessCheck, AccessGrant → **DEPRECATE**, use `access.py` versions

**Post-migration:**
- `auth.py` → Keep only FastAPI route dependencies (empty of models)
- `user.py` → Keep only SQLAlchemy User model (if separate)
- Update all imports: `from mko_bi.models.identity.models import ...`

**Imports to update:**
- `src/mko_bi/api/routes/auth.py`
- `src/mko_bi/api/routes/users.py`
- `src/mko_bi/services/auth_service.py`
- `src/mko_bi/services/user_service.py`
- `tests/test_pydantic_models.py`

### Step 3: Migrate Dashboard + Chart Models
**Source files:** `dashboard.py`, `data.py` (partial), `user_roles.py` (partial)  
**Target:** `src/mko_bi/models/dashboards/models.py`

**Models to move:**
- From `dashboard.py`: DashboardConfig, DashboardCreate, DashboardRead, DashboardUpdate
- From `data.py`: ChartConfig, ChartData, ChartDataRequest, FilterState
- From `user_roles.py`: GraphTypeEnum, OrientationEnum, BarmodeEnum, YoyModeEnum

**Critical:** Keep UserRoleEnum, PermissionEnum in `user_roles.py` (used by SQLAlchemy models)

**Post-migration:**
- `dashboard.py` → Empty (models moved)
- `data.py` → Remove chart-related models (keep processing models)
- `user_roles.py` → Keep UserRoleEnum, PermissionEnum only
- Update all imports

**Imports to update:**
- `src/mko_bi/api/routes/dashboards.py`
- `src/mko_bi/services/dashboard_service.py`
- `src/mko_bi/dashboards/components/charts/bar.py`
- `src/mko_bi/dashboards/components/charts/line.py`
- `src/mko_bi/dashboards/components/charts/pie.py`
- `src/mko_bi/dashboards/components/charts/table.py`
- `tests/test_pydantic_models.py`

### Step 4: Migrate Data Processing Models
**Source file:** `data.py` (remaining)  
**Target:** `src/mko_bi/models/processing/models.py`

**Models to move:**
- DataUpload, UploadResponse
- ProcessingStatus, ProcessingConfig, ProcessingResult
- LoaderConfig, ValidationResult
- DataFilter
- AggregatedData

**Post-migration:**
- `data.py` → Delete (all models moved)
- Update all imports

**Imports to update:**
- `src/mko_bi/api/routes/upload.py`
- `src/mko_bi/api/routes/data.py`
- `src/mko_bi/services/data_service.py`
- `tests/test_pydantic_models.py`
- `tests/test_data_loader.py`
- `tests/test_data_processing.py`
- `tests/test_data_api.py`
- `tests/test_upload_api.py`

### Step 5: Update SQLAlchemy Model Dependencies
**Critical issue:** `db/models/user.py` and `db/models/access.py` import from `user_roles.py`

**Solution:** Keep `user_roles.py` with UserRoleEnum and PermissionEnum for SQLAlchemy Enum types. These enums are database schema definitions, not just Pydantic schemas.

**File:** `src/mko_bi/models/user_roles.py` — **KEEP** (minimal)
```python
from enum import StrEnum

class UserRoleEnum(StrEnum):  # Used by SQLAlchemy models
    admin = "admin"
    editor = "editor"
    viewer = "viewer"

class PermissionEnum(StrEnum):  # Used by SQLAlchemy models
    view = "view"
    edit = "edit"
    admin = "admin"
```

**Update:** Pydantic models in `identity/models.py` import these from `user_roles.py`
- This is acceptable: domain enums shared between Pydantic and SQLAlchemy

### Step 6: Update Top-Level `__init__.py`
**File:** `src/mko_bi/models/__init__.py`

**Current:** Individual imports from each model file  
**Update:** Re-export from new modules:
```python
from .user_roles import UserRoleEnum, PermissionEnum
from .identity.models import *
from .dashboards.models import *
from .processing.models import *
from . import access  # Keep access.py models
```

### Step 7: Clean Up Deprecated Files
After verifying all imports work:
- Delete or empty: `auth.py` (models removed)
- Delete or empty: `user.py` (models removed, if no SQLAlchemy model)
- Delete or empty: `dashboard.py` (models removed)
- Delete: `data.py` (all models moved)
- **Keep:** `user_roles.py` (with enums only)
- **Keep:** `access.py` (canonical access models)

### Step 8: Verify SQLAlchemy Models
**Files to check:**
- `src/mko_bi/db/models/user.py` — imports UserRoleEnum from `mko_bi.models.user_roles`
- `src/mko_bi/db/models/access.py` — imports PermissionEnum from `mko_bi.models.user_roles`
- `src/mko_bi/db/models/dashboard.py` — check TYPE_CHECKING imports

**Action:** Update any broken imports in `db/models/` to use new paths

## 3. Model Mapping Reference

| Old Location | Model | New Location |
|-------------|-------|-------------|
| `auth.py` | LoginRequest | `identity/models.py` |
| `auth.py` | RegisterRequest | `identity/models.py` |
| `auth.py` | Token | `identity/models.py` |
| `auth.py` | TokenData | `identity/models.py` |
| `auth.py` | RefreshRequest | `identity/models.py` |
| `auth.py` | AccessCheck | **DEPRECATE** → use `access.py` |
| `auth.py` | AccessGrant | **DEPRECATE** → use `access.py` |
| `user.py` | UserBase | `identity/models.py` |
| `user.py` | UserCreate | `identity/models.py` |
| `user.py` | UserRead | `identity/models.py` |
| `user.py` | UserDB | `identity/models.py` |
| `user.py` | UserUpdate | `identity/models.py` |
| `user_roles.py` | UserRoleEnum | `user_roles.py` (keep) |
| `user_roles.py` | PermissionEnum | `user_roles.py` (keep) |
| `dashboard.py` | DashboardConfig | `dashboards/models.py` |
| `dashboard.py` | DashboardCreate | `dashboards/models.py` |
| `dashboard.py` | DashboardRead | `dashboards/models.py` |
| `dashboard.py` | DashboardUpdate | `dashboards/models.py` |
| `user_roles.py` | GraphTypeEnum | `dashboards/models.py` |
| `data.py` | ChartConfig | `dashboards/models.py` |
| `data.py` | ChartData | `dashboards/models.py` |
| `data.py` | ChartDataRequest | `dashboards/models.py` |
| `user_roles.py` | OrientationEnum | `dashboards/models.py` |
| `user_roles.py` | BarmodeEnum | `dashboards/models.py` |
| `user_roles.py` | YoyModeEnum | `dashboards/models.py` |
| `data.py` | FilterState | `dashboards/models.py` |
| `data.py` | DataUpload | `processing/models.py` |
| `data.py` | UploadResponse | `processing/models.py` |
| `data.py` | ProcessingStatus | `processing/models.py` |
| `data.py` | ProcessingConfig | `processing/models.py` |
| `data.py` | ProcessingResult | `processing/models.py` |
| `data.py` | LoaderConfig | `processing/models.py` |
| `data.py` | ValidationResult | `processing/models.py` |
| `data.py` | DataFilter | `processing/models.py` |
| `data.py` | AggregatedData | `processing/models.py` |
| `access.py` | AccessCheck | `access.py` (keep) |
| `access.py` | AccessGrant | `access.py` (keep) |

## 4. Verification Checklist

- [ ] All Pydantic models moved to new modules
- [ ] `user_roles.py` contains only UserRoleEnum, PermissionEnum
- [ ] No `models.py` + `schemas.py` duplication
- [ ] All imports updated in API routes (5 files)
- [ ] All imports updated in services (4 files)
- [ ] All imports updated in dashboard components (4 files)
- [ ] All imports updated in tests (7 test files)
- [ ] SQLAlchemy models in `db/models/` have correct imports
- [ ] `src/mko_bi/models/__init__.py` re-exports correctly
- [ ] Old model files cleaned up
- [ ] No circular dependencies introduced
- [ ] Tests pass (run `pytest tests/test_pydantic_models.py`)

## 5. Constraints & Anti-Patterns Avoided

❌ **NO** `models.py` + `schemas.py` duplication (Pydantic models ARE schemas)  
❌ **NO** 6+ modules (kept to 3 cohesive modules + shared enums)  
❌ **NO** new entity creation (only reorganize existing)  
❌ **NO** business logic changes  
❌ **NO** SQLAlchemy model changes (only import path updates)  
✅ **YES** SRP compliance (each module has single responsibility)  
✅ **YES** Cohesive domains (identity, dashboards, processing)  
✅ **YES** Shared enums kept for DB schema compatibility  

## 6. Expected Outcome

**Before:**
- 6 flat files with mixed responsibilities
- 13 files importing from `user_roles.py` (tight coupling)
- Duplicate access models in `auth.py` and `access.py`
- Chart enums in user roles file
- Processing models mixed with chart models

**After:**
- 3 cohesive modules + 1 shared enum file
- Clear domain boundaries (identity, dashboards, processing)
- Single source of truth for access models (`access.py`)
- Enums colocated with their domain consumers
- SQLAlchemy enums kept separate for DB schema stability
- Simpler navigation, easier maintenance
