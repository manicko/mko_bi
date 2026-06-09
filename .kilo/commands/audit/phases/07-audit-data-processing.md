---
name: 07-data-processing
description: Data processing audit covering pipeline correctness, resource management, and data integrity
agent: auditor
alwaysApply: false
problems-only: true
---

# Phase 07 Audit — Data Processing Pipeline

## Output Mode

`problems-only: true` — **only problems, bugs, and deviations are documented.**

- **Do NOT** write sections that say "X is correct" or "no issues found in Y".
- **Do NOT** include checklist rows where the check passes — omit them entirely.
- If a dimension has zero findings after investigation, **omit the dimension entirely**.
- Every finding must be actionable: it describes a real problem, its evidence (code/logs/output), and its impact.
- If `problems-only: false` were set, you would produce a full report with compliance statements. But it is `true`, so the report is exclusively findings.

---

## Discovery Stage

Before performing audit checks, discover the project's data processing architecture:

1. **Pipeline Discovery** — Identify data ingestion entry points, map processing stages (validate → parse → transform → aggregate → store), discover configuration-driven vs hardcoded processing.
2. **Resource Discovery** — Identify temporary file storage locations, map resource cleanup mechanisms, discover memory management approach, find transaction boundaries.
3. **Data Flow Discovery** — Identify source data formats and validation, map transformation rules and business logic, discover aggregation patterns and output formats, find error handling and recovery points.
4. **Background Processing Discovery** — Identify task queue implementation, map task lifecycle and status tracking, discover worker isolation, find task failure and retry handling.

---

## Mandatory Runtime Verification

**Before evaluating any checklist item, you MUST complete these steps. Use the commands provided in the project's commands file. Skip only if a step is impossible — document why.**

### Step R1 — Trace the Full Data Pipeline in Code

Read the entire data processing flow from entry point to storage:

- Identify the upload/ingestion handler.
- Follow the call chain through parse, transform, aggregate, and store.
- At each stage, note: input format, output format, error handling, resource allocation, resource cleanup.
- If any stage is missing error handling, that is a finding.

### Step R2 — Verify Resource Cleanup

Search the processing code for temporary file creation:

- For each temp file creation, verify there is a corresponding cleanup (`try/finally`, context manager, or signal handler).
- If cleanup is missing on any code path (including error paths), that is a finding.
- Verify cleanup runs even when processing fails mid-pipeline.

### Step R3 — Verify Transactional Boundaries

Read the storage/aggregation code:

- Identify all database write operations in the pipeline.
- Verify they are wrapped in a single transaction.
- If writes can be partially committed (e.g., commit after each table), that is a CRITICAL finding.
- Verify rollback happens on any failure.

### Step R4 — Determine Processing Determinism

Read the aggregation logic:

- Identify any use of: random values, current timestamp, unordered collections (sets, dicts before Python 3.7), or race conditions.
- If any non-deterministic element exists in aggregation, identical inputs may produce different outputs. Finding.
- Identify any floating-point arithmetic that could cause precision drift.

### Step R5 — Verify Recalculation Completeness

Find where data is replaced after a new upload:

- Verify ALL aggregated metrics are recalculated from the new data.
- If any metric is incrementally updated (rather than fully recalculated), that is a data drift risk. Finding.
- Verify no stale data remains after processing.

### Step R6 — Test Error Paths with Invalid Input

Review the validation code for uploaded data:

- Identify what happens when: required columns are missing, data types are wrong, file is empty, file is malformed, file exceeds size limits.
- For each error scenario, verify: the error is caught, a meaningful error is returned to the user, no partial data is stored, temp files are cleaned up.
- Any unhandled error path is a CRITICAL finding (processing crash = potential data corruption).

---

## Audit Scope

Pipeline correctness, resource management, atomicity/consistency, configuration-driven processing, background task safety.

---

## Audit Dimensions

### 1. Pipeline Correctness

| Check | Description |
|-------|-------------|
| Input validation at pipeline entry | Every upload is validated before processing. |
| Data parsed into structured format | Parsing handles all expected formats. |
| Transformations match configuration | Processing rules are applied correctly. |
| Aggregations produce deterministic results | Same input always produces same output. |
| Output stored atomically | All-or-nothing storage. |
| Pipeline fails fast on invalid data | No partial processing of invalid input. |

**Evidence required:** Step R1 end-to-end trace. Step R4 determinism analysis. Step R6 error path verification.

### 2. Resource Management

| Check | Description |
|-------|-------------|
| Temporary files cleaned up on success | No orphaned temp files. |
| Temporary files cleaned up on failure | Error paths clean up resources. |
| Memory usage bounded for large inputs | No unbounded memory growth. |
| Database connections properly managed | No connection leaks. |
| No resource leaks in async context | Async processing doesn't leak resources. |

**Evidence required:** Step R2 cleanup analysis. Read the code for memory-efficient processing (streaming vs loading entire file).

### 3. Atomicity & Consistency

| Check | Description |
|-------|-------------|
| Processing runs in database transaction | All writes are transactional. |
| Changes rolled back on failure | Failed processing doesn't leave partial data. |
| Partial results never visible on error | Users never see inconsistent state. |
| UPSERT operations are idempotents | Re-processing produces the same result. |

**Evidence required:** Step R3 transaction analysis. Read the UPSERT/logic code for idempotency verification.

### 4. Configuration-Driven Processing

| Check | Description |
|-------|-------------|
| Processing rules configurable | Rules come from config, not code. |
| Invalid configurations handled gracefully | Bad config produces clear errors. |
| Formula/metric definitions validated | Metrics are validated before use. |
| Processing params not hardcoded | No magic numbers in processing logic. |

**Evidence required:** Read the configuration and validation code. If processing logic has hardcoded values, that is a finding.

### 5. Background Task Safety

| Check | Description |
|-------|-------------|
| Task state transitions complete | STARTED → PROCESSING → SUCCESS/FAILED. |
| Task status/results retrievable | Users can check task outcome. |
| Long-running tasks don't block event loop | Processing is offloaded correctly. |
| Task failures logged with context | Failed tasks have diagnostic info. |

**Evidence required:** Read the background task implementation. Verify state machine completeness. Check failure logging.

---

## Report Output

Write findings to: `.ai/audit/07-data-processing/findings.md` using template `.ai/audit/templates/audit-findings.md`.

Use prefix `DP-` for finding IDs.

**`problems-only: true` rules:**
- The report contains **only findings** — real problems discovered during investigation.
- Do NOT include sections, dimensions, or checklist rows where everything is correct.
- If after completing all Runtime Verification steps and all Audit Dimensions, no problems were found, write a single line: `No problems found in this phase.`
- Every finding MUST include:
  1. **Runtime evidence** — code trace (file:line), missing error handler, missing cleanup, transaction boundary violation.
  2. **Not just:** "violates invariant X" — show the exact code path that breaks and the exact data consequence (corruption, leak, inconsistency).
