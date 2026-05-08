# Master Development Plan - mkobi Project

**Date**: 2026-05-08  
**Based on**: TASK_050_architecture_audit.md, TASK_031_audit_full.md, TASK_037_test_audit.md, TASK_038_docker_audit.md, TASK_001_db_structure_audit.md

---

## Overview

This master plan organizes all audit findings into isolated, sequentially developable blocks. Each block is saved as a separate file in `TODO/DEV/`.

---

## Development Blocks (in recommended order)

| Block # | File | Focus Area | Priority | Dependencies |
|---------|------|-------------|----------|-------------|
| 04 | `04_enum_str_enum_cleanup.md` | Enum/StrEnum consolidation | HIGH | None |
| 05 | `05_mypy_type_errors_fix.md` | MyPy type errors (234 → 0) | HIGH | 04 |
| 06 | `06_test_quality_improvement.md` | Test quality & architecture alignment | HIGH | 05 |
| 07 | `07_ruff_linting_fix.md` | Ruff linting (0 errors) | MEDIUM | None |
| 08 | `08_docker_devops_improvements.md` | Docker & deployment readiness | MEDIUM | None |
| 09 | `09_database_improvements.md` | DB migrations, indexes, reproducibility | HIGH | None |
| 10 | `10_logging_improvements.md` | Standardize logging (English, no print) | MEDIUM | None |
| 11 | `11_frontend_type_safety.md` | TypeScript strict mode, no `any` | HIGH | None |
| 12 | `12_async_sync_standardization.md` | Consistent async patterns | HIGH | 05 |
| 13 | `13_security_improvements.md` | Security audit & fixes | CRITICAL | None |

---

## Block Details

### Block 04: Enum/StrEnum Cleanup
- **Goal**: Single source of truth for all StrEnum definitions
- **Files**: `src/mkobi/models/enums.py`, `src/mkobi/models/user_roles.py`
- **Tasks**: Remove aliases, update 39+ files to import directly from `enums.py`
- **Validation**: `uv run ruff check .`, `uv run mypy .`, `uv run pytest tests/`

### Block 05: MyPy Type Errors Fix
- **Goal**: Reduce MyPy errors from 234 to 0
- **Files**: `src/mkobi/**/*.py`
- **Tasks**: Fix return types, unused type:ignore, UUID vs int, None attributes, enum access
- **Validation**: `uv run mypy .` passes with 0 errors

### Block 06: Test Quality Improvement
- **Goal**: Align tests with current architecture, remove anti-patterns
- **Files**: `tests/*.py`
- **Tasks**: Fix async/sync mismatches, UUID vs int, weak assertions, overmocking
- **Validation**: `uv run pytest tests/` passes, coverage > 80%

### Block 07: Ruff Linting Fix
- **Goal**: Achieve clean ruff check (0 errors)
- **Files**: `tests/test_users_api.py`, `src/mkobi/**/*.py`
- **Tasks**: Fix unused imports, auto-fixable issues
- **Validation**: `uv run ruff check .` passes with 0 errors

### Block 08: Docker & DevOps Improvements
- **Goal**: Production-ready Docker setup
- **Files**: `Dockerfile`, `docker-compose.yml`, `docker-compose.override.yml`
- **Tasks**: Non-root user, no secrets in image, proper config management
- **Validation**: `docker-compose config` passes, container runs correctly

### Block 09: Database Improvements
- **Goal**: Reproducible schema, proper indexes, migration safety
- **Files**: `src/mkobi/db/starter.py`, `alembic/versions/*.py`
- **Tasks**: Migration chain integrity, index creation, foreign keys verification
- **Validation**: `alembic upgrade head` on empty DB works

### Block 10: Logging Improvements
- **Goal**: Standardize logging (English, proper levels, no print())
- **Files**: `src/mkobi/**/*.py`
- **Tasks**: Replace print(), translate Russian logs, add missing log points
- **Validation**: No print() in code, all logs in English

### Block 11: Frontend Type Safety
- **Goal**: TypeScript strict mode, no `any` types
- **Files**: `frontend/src/**/*.ts`, `frontend/src/**/*.tsx`
- **Tasks**: Enable strict mode, add proper interfaces, Zod schemas
- **Validation**: `tsc --noEmit` passes with 0 errors

### Block 12: Async/Sync Standardization
- **Goal**: Consistent async patterns throughout
- **Files**: `src/mkobi/services/*.py`, `src/mkobi/db/repositories/*.py`
- **Tasks**: All async SQLAlchemy, no blocking calls in async context
- **Validation**: `uv run mypy .` async errors resolved

### Block 13: Security Improvements
- **Goal**: Ensure all security best practices
- **Files**: `src/mkobi/core/security.py`, `src/mkobi/api/routes/upload.py`
- **Tasks**: JWT security, password hashing, upload security, SQL safety
- **Validation**: Security tests pass, penetration testing

---

## Questionable Audit Items (Validated & Rejected)

| Audit Item | Source | Issue | Decision | Reason |
|------------|--------|-------|----------|--------|
| Dash components still present | TASK_050 | Claims `dashboards/` dir has Dash code | **REJECTED** | No Dash components found in codebase; React frontend properly in `frontend/` |
| Over-engineering concern | TASK_031 | Claims overengineering | **REJECTED** | Current architecture follows Clean Architecture appropriately |

---

## Execution Strategy

1. **Start with Block 04** (Enum cleanup) - no dependencies
2. **Proceed to Block 05** (MyPy fixes) - depends on 04
3. **Parallel execution possible**:
   - Block 07 (Ruff) - independent
   - Block 08 (Docker) - independent  
   - Block 09 (Database) - independent
   - Block 10 (Logging) - independent
   - Block 11 (Frontend) - independent
   - Block 13 (Security) - independent
4. **Block 06** (Tests) - after 05 (MyPy)
5. **Block 12** (Async) - after 05 (MyPy)

---

## Validation Commands

```bash
# Type checking
uv run mypy .

# Linting
uv run ruff check .

# Tests
uv run pytest tests/

# Frontend type checking
cd frontend && npm run tsc --noEmit

# Docker validation
docker-compose config

# Database migration test
alembic upgrade head
```

---

## Notes

- Each block is isolated and can be developed independently (except where noted)
- Follow TASKS_TEMPLATE.md format for each block
- All comments and logs MUST be in English
- Use StrEnum instead of dict/list for constants
- No overengineering - keep it simple and maintainable
