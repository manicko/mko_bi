# TASK_051: Dependency Injection and Interfaces

## Objective
Improve the codebase by properly implementing Dependency Injection (DI) pattern and ensuring all interfaces are correctly used. Replace remaining dict/list constants with Enums.

## Requirements
- Clean, modular code
- Small functions, decomposition
- Proper architecture with DI
- logging in all modules
- Pydantic models in `src/mko_bi/models`
- Enum (or StrEnum) instead of dict and list in `src/mko_bi/models`
- settings/*.yaml for configuration

## Tasks

### 1. Analyze Current Implementation
- [x] Review existing interfaces in `src/mko_bi/interfaces/`
- [x] Review current DI implementation
- [x] Check Enum usage in `src/mko_bi/models/user_roles.py`

### 2. Fix Mypy Issues
- [ ] Remove `# mypy: ignore-errors` from `repository_interfaces.py`
- [ ] Remove `# mypy: ignore-errors` from `user_roles.py`
- [ ] Remove `# mypy: ignore-errors` from `security.py`
- [ ] Fix type annotations to pass mypy checks

### 3. Enum Replacements
- [ ] Check for dict/list constants that should be Enums
- [ ] Ensure all status fields use `ProcessingStatusEnum`
- [ ] Ensure all role fields use `UserRoleEnum`
- [ ] Ensure all permission fields use `PermissionEnum`
- [ ] Ensure all graph type fields use `GraphTypeEnum`

### 4. Dependency Injection
- [ ] Review current DI pattern
- [ ] Ensure services properly use interfaces
- [ ] Add proper dependency injection for repositories in services
- [ ] Document DI pattern if not documented

### 5. Code Quality
- [ ] Run `uv run ruff check .` and fix issues
- [ ] Run `uv run mypy src/mko_bi` and fix type errors
- [ ] Run tests `uv run pytest tests/`
- [ ] Ensure logging is properly configured in all modules

### 6. Final Steps
- [ ] Verify all changes don't break existing functionality
- [ ] Rename this file to `TASK_051_di_and_interfaces_DONE.md`
