---
name: 07-data-processing
description: Data processing audit covering pipeline correctness, resource management, and data integrity
agent: audit-executor
alwaysApply: false
---

# Phase 07 Audit — Data Processing Pipeline

**Executor:** audit-executor
**Status:** {pending|in-progress|complete}
**Validated:** {yes|no}

---

## Discovery Stage

Before performing audit checks, discover the project's data processing architecture:

1. **Pipeline Discovery**
   - Identify data ingestion entry points (file upload, API, message queues)
   - Map processing stages (parse → transform → aggregate → store)
   - Discover configuration-driven vs hardcoded processing
   - Locate batch vs streaming processing patterns

2. **Resource Discovery**
   - Identify temporary file storage locations
   - Map resource cleanup mechanisms
   - Discover memory management approach
   - Find transaction boundaries in processing

3. **Data Flow Discovery**
   - Identify source data formats and validation
   - Map transformation rules and business logic
   - Discover aggregation patterns and output formats
   - Find error handling and recovery points

4. **Background Processing Discovery**
   - Identify task queue implementation
   - Map task lifecycle and status tracking
   - Discover worker isolation and scaling
   - Find task failure and retry handling

---

## Audit Dimensions

### 1. Pipeline Correctness

Verify data flows correctly through the pipeline:

| Check | Status | Evidence |
|-------|--------|----------|
| Input validation at pipeline entry | | |
| Data parsed into structured format | | |
| Transformations match configuration | | |
| Aggregations produce deterministic results | | |
| Output stored atomically | | |
| Pipeline fails fast on invalid data | | |

---

### 2. Resource Management

Verify resources are cleaned up:

| Check | Status | Evidence |
|-------|--------|----------|
| Temporary files cleaned up on success | | |
| Temporary files cleaned up on failure | | |
| Memory usage bounded for large inputs | | |
| Database connections properly managed | | |
| No resource leaks in async context | | |

---

### 3. Atomicity & Consistency

Verify data integrity during processing:

| Check | Status | Evidence |
|-------|--------|----------|
| Processing runs in database transaction | | |
| Changes rolled back on failure | | |
| Partial results never visible on error | | |
| UPSERT operations are idempotent | | |

---

### 4. Configuration-Driven Processing

Verify flexibility and maintainability:

| Check | Status | Evidence |
|-------|--------|----------|
| Processing rules configurable | | |
| Invalid configurations handled gracefully | | |
| Formula/metric definitions validated | | |
| Processing params not hardcoded | | |

---

### 5. Background Task Safety

Verify async/background processing is robust:

| Check | Status | Evidence |
|-------|--------|----------|
| Task state transitions complete (STARTED → PROCESSING → SUCCESS/FAILED) | | |
| Task status/results retrievable | | |
| Long-running tasks don't block event loop | | |
| Task failures logged with context | | |

---

## Report Output

Write findings to: `.ai/audit/07-data-processing/findings.md` using template `.ai/audit/templates/audit-findings.md`.

Use prefix `DP-` for finding IDs.