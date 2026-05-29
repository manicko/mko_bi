---
name: 06-tests
description: Test quality audit covering coverage gaps, anti-patterns, and test isolation
agent: audit-executor
alwaysApply: false
---

# Phase 06 Audit — Test Quality

**Executor:** audit-executor
**Status:** {pending|in-progress|complete}
**Validated:** {yes|no}

---

## Discovery Stage

Before performing audit checks, discover the project's testing architecture:

1. **Test Framework Discovery**
   - Identify test runner (pytest, jest, etc.)
   - Map test organization (unit, integration, e2e)
   - Discover test database setup and isolation strategy
   - Find fixture patterns and shared test utilities

2. **Coverage Discovery**
   - Identify critical user flows
   - Map business logic test coverage
   - Discover authentication/authorization test patterns
   - Find data processing test coverage

3. **Test Patterns Discovery**
   - Identify common test anti-patterns in the codebase
   - Map mocking strategies
   - Discover assertion patterns
   - Find async/sync test handling

4. **Quality Discovery**
   - Identify tautological tests
   - Map coverage gaps in critical paths
   - Discover test brittleness indicators
   - Find test performance characteristics

---

## Audit Dimensions

### 1. Test Anti-Patterns

Flag problematic testing patterns:

| Check | Status | Evidence |
|-------|--------|----------|
| Tests don't mock entire dependency tree | | |
| Assertions verify actual outcomes, not mock calls | | |
| No tautological tests (`assert True`, no assert) | | |
| Tests focus on behavior, not implementation details | | |
| No shared mutable state between tests | | |
| Tests don't depend on execution order | | |
| Async tests properly marked and configured | | |

---

### 2. Critical Path Coverage

Verify essential flows are tested:

| Check | Status | Evidence |
|-------|--------|----------|
| Authentication flow has success and failure tests | | |
| Authorization boundaries tested for different roles | | |
| File upload and processing flows tested | | |
| Data transformation and aggregation tested | | |
| Error handling paths tested | | |
| Input validation rejection cases tested | | |
| External service integration tested (or safely skipped) | | |

---

### 3. Test Isolation

Verify tests don't interfere with each other:

| Check | Status | Evidence |
|-------|--------|----------|
| Each test runs in isolated transaction | | |
| Test database separate from dev/prod | | |
| Fixtures properly scoped (function/module/session) | | |
| No test data leakage between runs | | |
| Cleanup occurs even on test failure | | |

---

### 4. Type Safety in Tests

Verify test code follows type discipline:

| Check | Status | Evidence |
|-------|--------|----------|
| Test configuration properly typed | | |
| No `any` types in test assertions | | |
| Response types match API contracts | | |

---

## Report Output

Write findings to: `.ai/audit/06-tests/findings.md` using template `.ai/audit/templates/audit-findings.md`.

Use prefix `TST-` for finding IDs.