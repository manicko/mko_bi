---
name: 06-tests
description: Test quality audit covering coverage gaps, anti-patterns (overmocking, contract mismatch, tautological tests), pytest standards, test database isolation, missing critical path coverage
agent: audit-executor
alwaysApply: false
---

# Phase 06 Audit â€” Test Quality

**Executor:** audit-executor
**Status:** {pending|in-progress|complete}
**Validated:** {yes|no}

**IMPORTANT:** Base layer context is auto-included by orchestrator:
- Project: mkobi BI Dashboard (FastAPI + React + PostgreSQL)
- Structure: `.ai/structure/map.md`
- Commands: `.ai/context/commands.md`
- SPEC: `docs/SPEC.md`

---

## Phase-Specific File Paths

- `tests/**/*.py`
- `tests/conftest.py`
- `docs/06-backend/testing.md`

---

## Checklist

### Anti-patterns to Flag

| Check | Status | Evidence |
|-------|--------|----------|
| Architecture mismatch: sync in async tests, deprecated methods, `pandas` instead of `polars` | | |
| Overmocking: mock replaces all logic, assertions on mock values not real results | | |
| Tautological: `assert True`, no assert, trivial checks | | |
| Wrong abstraction: testing private methods, SQL internals, call order | | |
| Fragile: depends on execution order, shared mutable state, no `pytest.mark.asyncio` | | |

### Coverage Areas

| Check | Status | Evidence |
|-------|--------|----------|
| Auth: login (`TokenWithUser`), refresh, roles, admin bypass, 403/404 dual-signal | | |
| API: all endpoints (success + error cases) | | |
| Processing: CSV loading (Polars), transformations, aggregations, formula parser, JSONB normalization | | |
| Repositories: CRUD, JSONB queries, UPSERT | | |
| Config: loading, production enforcement | | |
| Task queue: enqueue, status tracking, background worker | | |
| Pydantic models: all request/response models, validators, StrEnum | | |

### Infrastructure

| Check | Status | Evidence |
|-------|--------|----------|
| pytest standards: `pytest.mark.asyncio`, fixtures in conftest, no `unittest.TestCase` | | |
| Test database: separate `bidb_test`, SAVEPOINT rollback, NullPool | | |
| Fixture structure matches `docs/06-backend/testing.md` | | |

---

## Findings

### TST-{NN}: {Title}

| Field | Value |
|-------|-------|
| **ID** | TST-{NN} |
| **Severity** | {severity} |
| **Type** | {type} |
| **Affected Modules** | {modules} |
| **Classification** | {mandatory|advisory} |

**Description:** {description}

**Evidence:** {evidence}

**Recommendation:** {recommendation}

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |

## Mandatory Fixes

{List all findings classified as mandatory}

## Advisory Recommendations

{List all findings classified as advisory}

## Doc Updates Needed

{List all findings classified as DOC-UPDATE type}

---

## Report Format

Create file: `.ai/audit/tests/audit_report_<number>.md` (next available number)

See `.ai/audit/templates/audit-findings.md` for full template.