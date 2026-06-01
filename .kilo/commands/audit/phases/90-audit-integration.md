---
name: 09-integration
description: Cross-cutting integration audit covering API contract consistency, auth flow, data flow, and type alignment
agent: audit-executor
alwaysApply: false
problems-only: true
---

# Phase 09 Audit — Integration

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

Before performing audit checks, discover the project's integration architecture:

1. **API Contract Discovery** — Identify API entry points and response formats, map frontend API client patterns, discover versioning strategy, find contract validation approach.
2. **Auth Flow Discovery** — Identify token lifecycle, map frontend authentication state, discover backend token validation points, find auth error handling patterns.
3. **Data Flow Discovery** — Trace data from source to output, map serialization formats, discover error propagation across layers, find data transformation boundaries.
4. **Type Alignment Discovery** — Identify shared type definitions, map backend response types to frontend types, discover type validation at boundaries.

---

## Mandatory Runtime Verification

**Before evaluating any checklist item, you MUST complete these steps. Use the commands provided in the project's commands file. Skip only if a step is impossible — document why.**

### Step R1 — Full Route-by-Route Contract Comparison

Extract ALL routes from the backend and ALL API calls from the frontend:

- Create a complete mapping: `Backend Route → Frontend Call → Match/Mismatch`.
- For mismatches: document the exact path, HTTP method, request shape, and response shape differences.
- Every mismatch is a finding — it will cause a runtime error for users.

### Step R2 — Auth Flow End-to-End Verification

Read the complete authentication flow from both sides:

1. Frontend: token acquisition → storage → attachment to requests → refresh on expiry → logout.
2. Backend: token validation → permission check → token expiry enforcement → revocation.

- For each step, verify both sides agree. If the frontend sends `Authorization: Bearer` but the backend expects `X-Token`, that is CRITICAL.
- If tokens can expire without the frontend handling it, that is a finding.
- If logout doesn't invalidate tokens on the backend, that is a security finding.

### Step R3 — Data Flow End-to-End Trace

Pick the primary data flow (file upload → processing → aggregation → display) and trace it completely:

- Start at the upload handler, follow through parsing, transformation, aggregation, storage, retrieval, and rendering.
- At each boundary (frontend→backend, backend→database, database→backend, backend→frontend), verify data shapes match.
- Any shape mismatch is a finding.

### Step R4 — Schema Alignment Verification

- Compare ORM models against database schema (columns, types, constraints).
- Compare backend response types against ORM models.
- Compare frontend types against backend response types.
- Any drift (column exists in model but not DB, response field exists in backend but not in frontend type, etc.) is a finding.

### Step R5 — Environment Variable Consistency

Check that configuration is consistent across services:

- Do all services agree on database connection strings?
- Do all services agree on the backend URL?
- Are there any hardcoded URLs that should be configurable?
- Are there development-only values in production configuration?

### Step R6 — Error Propagation Verification

For each layer, verify that errors are correctly propagated:

- Backend catches errors and returns appropriate HTTP status + body.
- Frontend catches HTTP errors and displays meaningful messages to users.
- No unhandled errors crash the frontend or return raw stack traces to users.
- Database errors are caught and don't propagate as unhandled 500s with internal details.

---

## Audit Scope

API contract consistency, auth flow, data flow, schema alignment, cross-cutting invariants.

---

## Audit Dimensions

### 1. API Contract Consistency

| Check | Description |
|-------|-------------|
| Frontend API calls match backend endpoint definitions | Path, method, request shape. |
| Request/response shapes align between client and server | No missing or extra fields. |
| Error responses handled consistently | Consistent error format. |
| Path/query parameters match across contract | Same names, same types. |

**Evidence required:** Step R1 route-by-route comparison. Every mismatch is a finding.

### 2. Auth Flow End-to-End

| Check | Description |
|-------|-------------|
| Tokens attached to requests correctly | Same header name, same format. |
| Tokens validated at backend entry points | Every protected route validates. |
| Token refresh flow works across restarts | Refresh is handled. |
| Unauthenticated requests return 401 | Correct status code. |
| Session termination handled | Logout invalidates tokens. |

**Evidence required:** Step R2 auth flow analysis. Read both frontend and backend auth code.

### 3. Data Flow End-to-End

| Check | Description |
|-------|-------------|
| Data ingestion validates input at boundary | Upload is validated. |
| Processing transforms data correctly | Transformations are correct. |
| Storage writes data in expected format | DB schema matches data shape. |
| Retrieval returns data with correct shape | Response matches frontend expectations. |
| UI renders data without crashes | No rendering errors. |
| Error states propagate to UI | Users see error messages. |

**Evidence required:** Step R3 end-to-end trace. Step R6 error propagation analysis.

### 4. Schema Alignment

| Check | Description |
|-------|-------------|
| ORM models match database schema | No drift. |
| Database schema matches migrations | Migrations are up to date. |
| Backend response types match ORM models | Types are consistent. |
| Frontend types match backend responses | No type mismatches. |
| No schema drift detected | Everything is aligned. |

**Evidence required:** Step R4 schema comparison. Document every drift with file:line.

### 5. Cross-Cutting Invariants

| Check | Description |
|-------|-------------|
| Configuration flows correctly between services | Consistent config. |
| Environment variables consistent across services | Same values where needed. |
| Health check endpoints return consistent format | Standard health format. |
| Error handling consistent across layers | Same error patterns. |
| Logging context preserved across async boundaries | Traceable logs. |

**Evidence required:** Step R5 environment consistency. Read error handling code across layers.

---

## Report Output

Write findings to: `.ai/audit/90-integration/findings.md` using template `.ai/audit/templates/audit-findings.md`.

Use prefix `INT-` for finding IDs.

**`problems-only: true` rules:**
- The report contains **only findings** — real problems discovered during investigation.
- Do NOT include sections, dimensions, or checklist rows where everything is correct.
- If after completing all Runtime Verification steps and all Audit Dimensions, no problems were found, write a single line: `No problems found in this phase.`
- Every finding MUST include:
  1. **Runtime evidence** — route comparison table, schema drift proof, auth flow mismatch, error propagation failure.
  2. **Not just:** "violates invariant X" — show the exact endpoint, the exact field, the exact type mismatch, and the exact user-facing failure.
