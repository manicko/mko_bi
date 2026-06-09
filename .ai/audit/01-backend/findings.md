---
name: backend-findings
description: Backend architecture audit findings
executor: audit-executor
problems-only: true
---

# Phase 01 Audit Findings — Backend Architecture

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### BE-001: Russian (Cyrillic) characters allowed in filter names violates English-only project rule

| Field | Value |
|-------|-------|
| **ID** | BE-001 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/services/filter_service.py` |
| **Classification** | mandatory |

**Description:** The filter name validation regex includes Cyrillic character ranges (`а-яА-Я`), which violates the project's English-only rule. The regex pattern `^[a-zA-Zа-яА-Я0-9\s\-_.]+$` allows Russian letters in filter names, but the project explicitly requires all logs, comments, and validation to use English only (per AGENTS.md and project rules).

**Evidence:** `src/mkobi/services/filter_service.py:299` contains `r'^[a-zA-Zа-яА-Я0-9\s\-_.]+$'` which permits Cyrillic characters.

**Recommendation:** Remove the Cyrillic character range from the regex pattern. Change to `^[a-zA-Z0-9\s\-_.]+$` to only allow Latin letters, matching the project's English-only requirement.

---

### BE-002: Interface methods return `Any` instead of concrete types causing mypy warnings

| Field | Value |
|-------|-------|
| **ID** | BE-002 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/interfaces/repository_interfaces.py`, `src/mkobi/services/processing_log_service.py` |
| **Classification** | mandatory |

**Description:** The `IProcessingLogRepository` interface methods are typed to return `Any` instead of concrete types. This defeats the purpose of type hints and causes mypy `no-any-return` warnings in the service layer. The interface defines `get_by_dashboard`, `get_filtered` returning `list[Any]` (lines 360-370), while the concrete implementation properly returns `list[ProcessingLogRead]`. Additionally, `create_log` and `update_status` return `Any` instead of specific types.

**Evidence:** 
- `src/mkobi/interfaces/repository_interfaces.py:360,369,378,392` declare return types as `list[Any]`, `Any | None`, `Any | None`
- `src/mkobi/services/processing_log_service.py:78,85,217` trigger mypy `no-any-return` errors because they return values from repository methods typed as `Any`
- `pyproject.toml:179-181` suppresses these errors with `ignore_errors = true` for `mkobi.interfaces.*`

**Recommendation:** Update interface method signatures to use concrete return types (`ProcessingLogRead`, `list[ProcessingLogRead]`, etc.) instead of `Any`. This requires importing the Pydantic models into the interfaces module and adjusting any code that relies on the loose typing.

---

### BE-003: Redundant cast statements after interface type fix

| Field | Value |
|-------|-------|
| **ID** | BE-003 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/services/processing_log_service.py` |
| **Classification** | advisory |

**Description:** After the interface is fixed to use concrete types, the `cast(int, count)` statements at lines 242 and 248 become redundant because `delete_old_logs` already returns `int` in the implementation.

**Evidence:** `src/mkobi/services/processing_log_service.py:242,248` contain `return cast(int, count)` which triggers mypy `redundant-cast` warnings.

**Recommendation:** Remove the redundant `cast(int, count)` statements once the interface properly declares the return type as `int`.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 2 |
| LOW | 1 |

## Mandatory Fixes

- BE-001: Remove Cyrillic character range from filter name validation regex
- BE-002: Update interface method signatures to use concrete types instead of `Any`

## Advisory Recommendations

- BE-003: Remove redundant `cast(int, count)` statements after interface type fix

---

## Template Field Reference

### Mandatory Fields Per Finding

| Field | Type | Values/Format |
|-------|------|---------------|
| `id` | string | Unique identifier within phase (e.g., `BE-001`, `BE-003`) |
| `title` | string | Human-readable one-line summary |
| `type` | enum | `SPEC-DEVIATION`, `BEST-PRACTICE`, `DOC-UPDATE`, `RUNTIME-ERROR` |
| `severity` | enum | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `description` | string | Detailed problem description with context |
| `evidence` | string | File paths, line references, log excerpts, code snippets |
| `affected_modules` | list | Affected module paths (e.g., `src/mkobi/api/routes/`, `frontend/src/features/auth/`) |
| `recommendation` | string | Concrete fix direction: what to change and why |
| `classification` | enum | `mandatory` (security, data loss, correctness) or `advisory` (improvement, refactoring) |