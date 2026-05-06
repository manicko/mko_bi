# Architecture Audit Report - mkobi Project

**Date**: 2026-05-06  
**Auditor**: Senior Python Architect (Roo)  
**Scope**: Clean Architecture, Separation of Concerns, Modularity, Type Safety

---

## 1. Project Goal Analysis (SPEC.md)

**Status**: ✅ Clear and well-defined

- BI Dashboard System with FastAPI backend, React TypeScript frontend
- Clean Architecture + Feature-Sliced Design for frontend
- Stack: FastAPI, React 18+, Material UI, Plotly.js, PostgreSQL, Pydantic, Polars
- All core entities and API endpoints properly documented

---

## 2. Frontend Folder Location Audit

**Question**: Should `C:\py_dev\mkobi\frontend` be moved to `C:\py_dev\mkobi\src\mkobi\frontend`?

**Finding**: ❌ **NO - Current location is CORRECT**

**Rationale**:
- Frontend is a **separate codebase** (Node.js/React) not part of Python package
- Python package `mkobi` is correctly located in `src/mkobi/`
- SPEC.md section 11.3 shows `frontend/` at project root level
- `app.py` (line 163) references `frontend/dist` for static file serving
- Mixing React code inside Python package would violate Python packaging standards
- The `frontend/` directory follows standard React project structure with `src/`, `public/`, etc.

**Recommendation**: Keep `frontend/` at project root level (`C:\py_dev\mkobi\frontend`)

---

## 3. Pydantic Models Location

**Required**: `C:\py_dev\mkobi\src\mkobi\models`  
**Actual**: ✅ **CORRECT**

**Structure**:
```
src/mkobi/models/
├── __init__.py
├── enums.py          # StrEnum definitions
├── user_roles.py     # Aliases for backwards compatibility
├── auth.py
├── user.py
├── dashboard.py
├── graph.py
├── filters.py
├── data.py
├── processing_configs.py
├── processing_logs.py
├── layout.py
├── style.py
├── transformation_configs.py
└── types.py
```

---

## 4. Enum (StrEnum) Usage Audit

**Status**: ⚠️ **NEEDS IMPROVEMENT**

### Findings:

1. ✅ `src/mkobi/models/enums.py` properly defines StrEnum classes:
   - `UserRole`, `DashboardPermission`, `GraphType`, `FilterType`
   - `RegistrationStatus`, `UploadMode`, `ProcessingStatus`
   - Additional enums: `MimeTypeEnum`, `FileExtensionEnum`, `ButtonVariant`, etc.

2. ⚠️ **Issue**: `src/mkobi/models/user_roles.py` creates aliases for backwards compatibility:
   ```python
   UserRoleEnum = UserRole
   PermissionEnum = DashboardPermission
   GraphTypeEnum = GraphType
   FilterTypeEnum = FilterType
   ProcessingStatusEnum = ProcessingStatus
   ```

3. ⚠️ **Problem**: 39 files import from `user_roles.py` instead of directly from `enums.py`, causing:
   - Duplicate enum references (`UserRole` vs `UserRoleEnum`)
   - Confusion about which to use
   - Inconsistent usage across codebase

### Recommendations:

- **Option A**: Remove `user_roles.py` and update all imports to use `enums.py` directly
- **Option B**: Keep aliases but add deprecation warnings and migrate gradually
- **Option C**: Choose one naming convention (`UserRole` OR `UserRoleEnum`) and stick to it

### Files using Enum aliases (39 results found):
- `core/permissions.py`
- `api/deps.py`
- `services/*.py` (auth_service, dashboard_service, graph_service, etc.)
- `utils/*.py` (decorators, validators)
- `models/auth.py`

---

## 5. Package Naming Compliance

**Required**: `mkobi` (single underscore between `mko` and `bi`)  
**Actual**: ✅ **CORRECT**

**Evidence**:
- `pyproject.toml`: `name = "mkobi"` (line 6)
- Directory: `src/mkobi/` (correct Python package name)
- All imports use `mkobi.*` pattern
- No double underscores or other naming violations found

---

## 6. Clean Architecture & Separation of Concerns

**Status**: ⚠️ **PARTIALLY COMPLIANT**

### Positive Findings:
- ✅ Layered structure: `api/`, `services/`, `db/`, `models/`, `core/`, `interfaces/`
- ✅ Repository pattern in `db/repositories/`
- ✅ Service layer in `services/`
- ✅ Pydantic models for API validation
- ✅ Interface definitions in `interfaces/`

### Concerns:

1. ⚠️ **Dash components still present**: `dashboards/` directory contains Dash-specific code (`dashboards/components/charts/*.py`, `dashboards/implementations/`)
   - SPEC.md indicates migration to React + Plotly.js
   - `dash_app.py` still mounts Dash app at `/dashboards`
   - This creates dual UI framework situation

2. ⚠️ **Mixed sync/async patterns**: Some services use async, others sync (based on mypy errors)

3. ⚠️ **Dict/List usage**: While Enums are defined, some code still uses:
   - `dict[str, Any]` for JSONB fields (acceptable for dynamic data)
   - `list[dict[str, Any]]` for data processing results
   - These are not necessarily violations if the data is truly dynamic

---

## 7. Code Quality (Static Analysis)

### Ruff (Linting)
**Status**: ✅ **MOSTLY CLEAN**

- **Errors**: 1 (unused import in test file)
- **File**: `tests/test_users_api.py:6` - `UserRole` imported but unused
- **Fix**: Remove unused import or use `--fix` flag

### MyPy (Type Checking)
**Status**: ❌ **234 ERRORS - NEEDS ATTENTION**

**Error Categories**:

1. **Return type errors** (most common): `Returning Any from function declared to return "..."`
   - Affects: repositories, services, API routes
   - Root cause: SQLAlchemy query results typed as `Any`

2. **Unused "type: ignore" comments**: 
   - Files: `dashboard_filter_repo.py`, `processing_config_repo.py`, `filter_repo.py`, etc.

3. **Type annotation issues**:
   - `Need type annotation for "prepared"`
   - `Item "None" has no attribute "get"`
   - `Value of type "YoyConfig | None" is not indexable`

4. **Argument type mismatches**:
   - UUID vs int mismatches in API routes
   - `FilterConfigDict` has no attribute `model_dump`

5. **Attr-defined errors**:
   - Module does not explicitly export attributes
   - `YoyModeEnum` has no attribute `percent` (should be `YoyModeEnum.PERCENT`)

**Recommendation**: Address mypy errors systematically, starting with:
1. Fix unused `type: ignore` comments
2. Add proper type annotations for repository return types
3. Fix Enum attribute access (`YoyModeEnum.percent` → `YoyModeEnum.PERCENT`)
4. Resolve UUID vs int type mismatches

---

## 8. Logging

**Status**: ✅ **IMPLEMENTED**

- `core/logging_config.py` for logging setup
- Uses Python's standard `logging` module
- Log files stored in `data/logs/`
- Multiple log levels (INFO, WARNING, ERROR) as specified in SPEC.md

---

## 9. Testing

**Status**: ✅ **PRESENT**

- Test files in `tests/` directory
- Uses `pytest` as specified
- Test coverage for: auth, config, dashboards, data processing, filters, graphs, models, repositories, security, upload API, users API, etc.
- Command: `uv run pytest <path>` ✅

---

## 10. Summary & Recommendations

| Area | Status | Priority |
|------|--------|----------|
| Frontend location | ✅ Correct | - |
| Package naming | ✅ Correct | - |
| Pydantic models location | ✅ Correct | - |
| Enum definitions | ⚠️ Needs cleanup | **HIGH** |
| Clean Architecture | ⚠️ Partial | **MEDIUM** |
| Ruff compliance | ✅ Clean (1 error) | LOW |
| MyPy compliance | ❌ 234 errors | **HIGH** |
| Dash migration | ⚠️ In progress | **MEDIUM** |

### Top 3 Action Items:

1. **Fix Enum usage**: Consolidate to single source of truth (remove `user_roles.py` aliases)
2. **Fix MyPy errors**: 234 type errors need systematic resolution
3. **Complete Dash migration**: Remove or archive `dashboards/` directory if fully migrated to React

---

## 11. Detailed File Structure Analysis

### Current Project Structure:
```
C:\py_dev\mkobi\
├── src/mkobi/           # Python package (✅ Correct)
│   ├── api/             # FastAPI routes
│   ├── models/          # Pydantic models (✅ Correct location)
│   │   ├── enums.py    # StrEnum definitions
│   │   └── user_roles.py  # ⚠️ Aliases (needs cleanup)
│   ├── services/        # Business logic layer
│   ├── db/             # Database layer
│   │   ├── models/     # SQLAlchemy models
│   │   └── repositories/  # Data access layer
│   ├── core/           # Core utilities
│   ├── data/           # Data processing
│   ├── interfaces/     # Interface definitions
│   ├── dashboards/     # ⚠️ Dash components (migration needed)
│   └── workers/        # Background workers
├── frontend/           # React SPA (✅ Correct location at root)
├── tests/              # Test files
├── alembic/            # Database migrations
└── TODO/               # Task tracking
```

---

**Overall Assessment**: The project follows most architectural requirements but has technical debt in type annotations and enum usage consistency. The frontend location is correct and should not be moved.
