---
name: 07-data-processing
description: Data processing audit covering Polars pipeline, loaders, transformations, aggregations, formula parser, storage, task queue, background worker, resource cleanup
agent: audit-executor
alwaysApply: false
---

# Phase 07 Audit â€” Data Processing

**Executor:** audit-executor
**Status:** {pending|in-progress|complete}
**Validated:** {yes|no}

**IMPORTANT:** Base layer context is auto-included by orchestrator  (SKIP if you already have it):
- Project: mkobi BI Dashboard (FastAPI + React + PostgreSQL)
- Structure: `.ai/structure/map.md`
- Commands: `.ai/context/commands.md`
- SPEC: `docs/SPEC.md`

---

## Phase-Specific File Paths

- `src/mkobi/data/loaders/loader.py`
- `src/mkobi/data/loaders/validator.py`
- `src/mkobi/data/processing/transformations.py`
- `src/mkobi/data/processing/registry.py`
- `src/mkobi/data/storage/manager.py`
- `src/mkobi/core/task_queue.py`
- `src/mkobi/workers/data_worker.py`
- `src/mkobi/services/file_processing.py`

---

## Audit Checklist

### 7.1 Data Loaders

Verify `src/mkobi/data/loaders/loader.py`:

| Check | Status | Evidence |
|-------|--------|----------|
| Polars used (`import polars as pl`) | | |
| pandas NOT used (`import pandas as pd` forbidden) | | |
| CSV reading (`read_csv`) | | |
| CSV.gz reading (gzip decompression) | | |
| Schema validation (`validator.py`) | | |
| Error handling (corrupted CSV, invalid schema, missing columns, empty files) | | |

---

### 7.2 Transformations

Verify `src/mkobi/data/processing/transformations.py`:

#### Aggregations

| Check | Status | Evidence |
|-------|--------|----------|
| GroupBy (Polars `group_by`) | | |
| YoY with modes: `absolute`, `percent` | | |
| Shares (ratio computations) | | |
| Custom metrics (configurable via formula parser) | | |

#### Formula Parser

| Check | Status | Evidence |
|-------|--------|----------|
| Supports: `revenue - cost`, `profit / revenue * 100` | | |
| Operators: `+`, `-`, `*`, `/` | | |
| Limitations documented (no parentheses, no numeric literals, no special chars in column names) | | |
| Invalid formulas produce clear errors with position and nature | | |

#### Pipeline Correctness

| Check | Status | Evidence |
|-------|--------|----------|
| Parsing (CSV â†’ Polars DataFrame) | | |
| Transformations (per dashboard config) | | |
| Aggregations (grouping, metrics) | | |
| Full recalculation on each upload (not incremental) | | |

---

### 7.3 Storage

Verify `src/mkobi/data/storage/manager.py`:

| Check | Status | Evidence |
|-------|--------|----------|
| Save to PostgreSQL (`aggregated_data` table) | | |
| JSONB usage for `dims` and `metrics` | | |
| Correct serialization | | |
| DB transaction handling (atomic processing, rollback on failure) | | |
| `dims` keys sorted recursively before writes (UPSERT determinism) | | |
| Unique index on `(dashboard_id, graph_id, dims::text)` for conflict detection | | |

---

### 7.4 Resource Handling

| Check | Status | Evidence |
|-------|--------|----------|
| Temp files cleanup via `platformdirs` (success and failure) | | |
| DB transaction handling (commit/rollback) | | |
| Memory-efficient processing (Polars lazy evaluation where applicable) | | |
| Errors handled and logged | | |

---

### 7.5 Task Queue & Background Processing

Verify `src/mkobi/core/task_queue.py`:

| Check | Status | Evidence |
|-------|--------|----------|
| `TaskQueue` class with `asyncio.Queue` | | |
| `default_queue` singleton | | |
| `enqueue_job()` compatibility wrapper | | |
| `get_task_queue()` returns singleton | | |
| Task lifecycle: `STARTED` â†’ `PROCESSING` â†’ `SUCCESS`/`FAILED` | | |
| Status/result/error tracking in memory dicts | | |

Verify `src/mkobi/workers/data_worker.py`:

| Check | Status | Evidence |
|-------|--------|----------|
| `process_csv_background()` â€” async entry point | | |
| `process_csv_background_sync()` â€” sync wrapper for RQ compatibility | | |
| Full pipeline: parse â†’ transform â†’ aggregate â†’ save â†’ cleanup | | |
| Processing log updates at each stage | | |

Verify migration path in `docs/03-processing/task-queue.py`:

| Check | Status | Evidence |
|-------|--------|----------|
| `process_csv_background_sync` prepared for RQ | | |
| Dual-mode operation support (`USE_REDIS_QUEUE` env var) | | |
| Rollback plan documented | | |

---

## Findings

### DP-{NN}: {Title}

| Field | Value |
|-------|-------|
| **ID** | DP-{NN} |
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

## Template Field Reference

### Mandatory Fields Per Finding

| Field | Type | Values/Format |
|-------|------|---------------|
| `id` | string | Unique identifier with `DP-` prefix (e.g., `DP-001`, `DP-002`) |
| `title` | string | Human-readable one-line summary |
| `type` | enum | `SPEC-DEVIATION`, `BEST-PRACTICE`, `DOC-UPDATE`, `RUNTIME-ERROR` |
| `severity` | enum | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `description` | string | Detailed problem description with context |
| `evidence` | string | File paths, line references, log excerpts, code snippets |
| `affected_modules` | list | Affected module paths |
| `recommendation` | string | Concrete fix direction: what to change and why |
| `classification` | enum | `mandatory` (security, data loss, correctness) or `advisory` (improvement, refactoring) |

### Classification Guide

- **mandatory**: Security vulnerabilities, data loss risks, correctness issues, spec deviations requiring immediate fix
- **advisory**: Code quality improvements, refactoring suggestions, best practice enhancements

---

**Report Format:** See `.ai/audit/templates/audit-findings.md` for full template.