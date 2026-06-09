---
name: 06-tests
description: Test quality audit covering coverage gaps, anti-patterns, and test isolation
agent: auditor
alwaysApply: false
problems-only: true
---

# Phase 06 Audit — Test Quality

## Output Mode

`problems-only: true` — **only problems, bugs, and deviations are documented.**

- **Do NOT** write sections that say "X is correct" or "no issues found in Y".
- **Do NOT** include checklist rows where the check passes — omit them entirely.
- If a dimension has zero findings after investigation, **omit the dimension entirely**.
- Every finding must be actionable: it describes a real problem, its evidence (code/logs/output), and its impact.
- If `problems-only: false` were set, you would produce a full report with compliance statements. But it is `true`, so the report is exclusively findings.
- If you need to start or stop docker environment to check functional or run test you should run it following the documantation instruction in dev mode BUT you mast return it to the same status as before - running or stopped

---

## Discovery Stage

Before performing audit checks, discover the project's testing architecture:

1. **Test Framework Discovery** — Identify test runner, map test organization (unit, integration, e2e), discover test database setup and isolation strategy, find fixture patterns.
2. **Coverage Discovery** — Identify critical user flows, map business logic test coverage, discover auth/authorization test patterns, find data processing test coverage.
3. **Test Patterns Discovery** — Identify common anti-patterns, map mocking strategies, discover assertion patterns, find async/sync test handling.
4. **Quality Discovery** — Identify tautological tests, map coverage gaps in critical paths, discover test brittleness indicators, find test performance characteristics.

---

## Mandatory Runtime Verification

**Before evaluating any checklist item, you MUST complete these steps. Use the commands provided in the project's commands file. Skip only if a step is impossible — document why.**

### Step R0 — Ensure Docker Environment is Running

Start Docker services in **development or test mode** (never production) before running tests. Follow the setup instructions in `docs/11-guides/docker.md`. Confirm all required containers are in `running` or `healthy` state before proceeding. If the environment cannot be started, document why and skip dependent steps.

### Step R1 — Run the Full Test Suite

Run the project's test suite and capture the complete output.

- Record pass/fail/skip counts.
- Record every failure with its full traceback.
- Record total execution time — excessively slow tests are a finding.
- If the test suite cannot run at all (import errors, config errors), that is CRITICAL.

### Step R2 — Analyze Test Failures

For each failing test from Step R1:

- Read the test code and the code it tests.
- Determine: is the test wrong, or is the production code wrong?
- If the production code is wrong, that is a CRITICAL finding (the bug exists in production).
- If the test is wrong (outdated, incorrect assertion), that is a finding (false sense of security).

### Step R3 — Detect Tautological and No-Op Tests

Search for tests that cannot fail or test nothing:

- Tests with no assertions (only `pass` or no body).
- Tests that assert a literal (`assert True`, `assert 1 == 1`).
- Tests that only call a function without checking the result.
- Tests where the mock is asserted to have been called, but the mock IS the implementation (testing the mock, not the logic).

Each instance is a finding with file:line.

### Step R4 — Verify Test Isolation

Run the test suite multiple times in sequence (or shuffle test order if the runner supports it).

- If tests pass individually but fail in suite: shared state between tests. Finding.
- If test results are non-deterministic: race condition or time-dependent test. Finding.
- Read test fixtures: verify cleanup happens even on test failure (teardown/fixture finalizers).

### Step R5 — Coverage Gap Analysis

If coverage tools are available, run the test suite with coverage.

- Identify critical paths (auth, data processing, file upload, payment) with low or zero coverage.
- For each critical path without tests, create a finding.
- If no coverage tool is configured, that is itself a finding.

### Step R6 — Verify Test Database Isolation

- Read the test database configuration: is it separate from dev/prod?
- Read test setup/teardown: does each test run in a transaction that gets rolled back?
- If tests modify a shared database without rollback, that is a finding.

---

## Audit Scope

Test anti-patterns, critical path coverage, test isolation, type safety in tests.

---

## Audit Dimensions

### 1. Test Anti-Patterns

| Check | Description |
|-------|-------------|
| Tests don't mock entire dependency tree | Only external boundaries are mocked. |
| Assertions verify actual outcomes, not mock calls | Tests behavior, not implementation. |
| No tautological tests | Every test can actually fail. |
| Tests focus on behavior, not implementation details | Refactoring internals doesn't break tests. |
| No shared mutable state between tests | Tests are independent. |
| Tests don't depend on execution order | Any test can run in isolation. |
| Async tests properly marked and configured | Async tests actually await. |

**Evidence required:** Step R3 results for tautological tests. Step R4 for isolation issues. Read test code for mock-heavy tests.

### 2. Critical Path Coverage

| Check | Description |
|-------|-------------|
| Authentication flow has success and failure tests | Login, logout, token refresh are tested. |
| Authorization boundaries tested for different roles | Each role has access control tests. |
| File upload and processing flows tested | Upload, parse, transform, aggregate are tested. |
| Data transformation and aggregation tested | Core business logic is tested. |
| Error handling paths tested | Error cases have tests, not just happy paths. |
| Input validation rejection cases tested | Invalid inputs are tested. |
| External service integration tested (or safely skipped) | Integration points are covered. |

**Evidence required:** Step R5 coverage analysis. Read the test directory structure and map tests to critical paths. Missing tests = findings.

### 3. Test Isolation

| Check | Description |
|-------|-------------|
| Each test runs in isolated transaction | Transaction-per-test pattern. |
| Test database separate from dev/prod | No shared mutable state. |
| Fixtures properly scoped | No fixture leakage between tests. |
| No test data leakage between runs | Clean state for every run. |
| Cleanup occurs even on test failure | Teardown runs on exception. |

**Evidence required:** Step R4 results. Step R6 analysis. Read conftest/fixtures for cleanup patterns.

### 4. Type Safety in Tests

| Check | Description |
|-------|-------------|
| Test configuration properly typed | No untyped test fixtures. |
| No `any` types in test assertions | Test code follows type discipline. |
| Response types match API contracts | Test assertions use correct types. |

**Evidence required:** Run the type checker on test files. Count `any` types in test code.

---

## Report Output

Write findings to: `.ai/audit/06-tests/findings.md` using template `.ai/audit/templates/audit-findings.md`.

Use prefix `TST-` for finding IDs.

**`problems-only: true` rules:**
- The report contains **only findings** — real problems discovered during investigation.
- Do NOT include sections, dimensions, or checklist rows where everything is correct.
- If after completing all Runtime Verification steps and all Audit Dimensions, no problems were found, write a single line: `No problems found in this phase.`
- Every finding MUST include:
  1. **Runtime evidence** — test output, failure tracebacks, coverage reports, file:line of problematic tests.
  2. **Not just:** "test coverage is low" — show exactly which critical path has no tests and what bug could go undetected.
