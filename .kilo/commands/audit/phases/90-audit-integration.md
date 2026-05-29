---
name: 09-integration
description: Cross-cutting integration audit covering API contract consistency, auth flow, data flow, and type alignment
agent: audit-executor
alwaysApply: false
---

# Phase 09 Audit — Integration

**Executor:** audit-executor
**Status:** {pending|in-progress|complete}
**Validated:** {yes|no}

---

## Discovery Stage

Before performing audit checks, discover the project's integration architecture:

1. **API Contract Discovery**
   - Identify API entry points and response formats
   - Map frontend API client patterns
   - Discover versioning strategy
   - Find contract validation approach

2. **Auth Flow Discovery**
   - Identify token lifecycle (acquisition, storage, refresh, invalidation)
   - Map frontend authentication state
   - Discover backend token validation points
   - Find auth error handling patterns

3. **Data Flow Discovery**
   - Trace data from source (upload) to output (UI render)
   - Map serialization formats
   - Discover error propagation across layers
   - Find data transformation boundaries

4. **Type Alignment Discovery**
   - Identify shared type definitions
   - Map backend response types to frontend types
   - Discover type validation at boundaries
   - Find type mismatches in contracts

---

## Audit Dimensions

### 1. API Contract Consistency

Verify frontend-backend contract alignment:

| Check | Status | Evidence |
|-------|--------|----------|
| Frontend API calls match backend endpoint definitions | | |
| Request/response shapes align between client and server | | |
| Error responses handled consistently | | |
| Path/query parameters match across contract | | |

---

### 2. Auth Flow End-to-End

Verify authentication across boundaries:

| Check | Status | Evidence |
|-------|--------|----------|
| Tokens attached to requests correctly | | |
| Tokens validated at backend entry points | | |
| Token refresh flow works across restarts | | |
| Unauthenticated requests return 401 | | |
| Session termination handled (logout, token expiry) | | |

---

### 3. Data Flow End-to-End

Verify data integrity across the pipeline:

| Check | Status | Evidence |
|-------|--------|----------|
| Data ingestion validates input at boundary | | |
| Processing transforms data correctly | | |
| Storage writes data in expected format | | |
| Retrieval returns data with correct shape | | |
| UI renders data without crashes | | |
| Error states propagate to UI | | |

---

### 4. Schema Alignment

Verify model consistency across layers:

| Check | Status | Evidence |
|-------|--------|----------|
| ORM models match database schema | | |
| Database schema matches migrations | | |
| Backend response types match ORM models | | |
| Frontend types match backend responses | | |
| No schema drift detected | | |

---

### 5. Cross-Cutting Invariants

Verify consistency across architectural boundaries:

| Check | Status | Evidence |
|-------|--------|----------|
| Configuration flows correctly between services | | |
| Environment variables consistent across services | | |
| Health check endpoints return consistent format | | |
| Error handling consistent across layers | | |
| Logging context preserved across async boundaries | | |

---

## Report Output

Write findings to: `.ai/audit/90-integration/findings.md` using template `.ai/audit/templates/audit-findings.md`.

Use prefix `INT-` for finding IDs.