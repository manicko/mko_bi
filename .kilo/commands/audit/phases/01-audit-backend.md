---
name: 01-backend
status: complete
validated: no
executor: auditor
problems-only: true
---

# Phase 01 Audit — Backend Architecture

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

Before performing audit checks, discover the project's architectural reality:

1. **Architecture Discovery** — Identify the primary architectural pattern, map layer boundaries, identify dependency flow direction, locate trust boundaries.
2. **Layer Identification** — Transport/HTTP layer, business logic layer, data access layer, configuration layer.
3. **Critical Flows Discovery** — Auth entry points, data ingestion pipelines, background task paths, error handling flow.
4. **Runtime Model** — Async/sync context, session/connection management, transaction boundaries, resource cleanup.

---

## Mandatory Runtime Verification

**Before evaluating any checklist item, you MUST complete these steps. Use the commands provided in the project's commands file. Skip only if a step is impossible — document why.**

### Step R0 — Ensure Docker Environment is Running

Start Docker services in **development or test mode** (never production) before running tests or linters that depend on the environment. Follow the setup instructions in `docs/11-guides/docker.md`. Confirm all required containers are in `running` or `healthy` state before proceeding. If the environment cannot be started, document why and skip dependent steps.

### Step R1 — Run Linters and Type Checkers

Run the project's configured linter and type checker commands (see commands file).

- Record exit codes and output.
- Any errors or warnings are direct evidence. Include them in findings.
- If tools are not configured, that itself is a finding (missing quality gates).

### Step R2 — Import Verification

Attempt to import the application entry point. Verify no dependency is missing or broken.

- Capture traceback on failure. A broken import is CRITICAL.

### Step R3 — Static Analysis of Dead Code

Search for code that is unreachable, never called, or conditionally impossible:

- Functions/methods defined but never invoked outside tests.
- Branches guarded by conditions that are always true/false.
- Imported modules that are never used (beyond linter detection, check logical dead code).
- Routes defined in routers but not mounted in the app.

Record each instance with file path and line number.

#### Step R3-SPEC — Verify "Dead" Code Against Specification

Read `docs/` and check if the "dead" function/route/feature is documented as a required capability.

**Dead Code Policy:**
- Dead code is ONLY when NOT documented — if code exists but is unused and documentation specifies it should exist, this is future-proofing, not dead code.
- When filing dead code findings, the recommendation should be to investigate purpose, not delete — ask why the code exists before suggesting removal.

### Step R4 — Run Backend Tests

Run the project's test suite (see commands file).

- Record pass/fail counts, skipped tests, and failure output.
- Any failing test is evidence of a real bug — create a finding for each failure.
- If test coverage data is available, note coverage gaps for critical paths.

### Step R5 — Verify API Contract Matches Source

Enumerate all registered routes from the application's route definitions.

- Compare declared routes against the OpenAPI/Swagger spec (if auto-generated) and against the frontend API client.
- Every route not present in the spec or frontend client is a potential dead endpoint or undocumented API.
- Every endpoint called by the frontend but not found in backend routes is a CRITICAL integration bug.

---

## Audit Scope

Transport layer, domain layer, persistence layer, cross-cutting concerns, data processing layer.

---

## Audit Dimensions

### 1. Architectural Integrity

| Invariant | Description |
|----------|-------------|
| Layer Isolation | Transport layer depends only on interface contracts, not on persistence or domain implementation details. |
| Dependency Direction | Dependencies point inward: domain layer does not depend on transport or persistence; persistence layer does not depend on domain. |
| No Business Logic in Transport | Route handlers contain only HTTP-specific logic (validation, serialization, service invocation). |
| Data Access Encapsulation | All database interactions are abstracted behind repository interfaces; no raw SQL in service or transport layers. |
| Dependency Management | Dependencies are centrally managed and injectable, allowing for replacement and testing. |
| Enum Safety | Domain-critical constants are represented as enumerated types to avoid magic strings and ensure type safety. |

**Evidence required per invariant:** At minimum one file:line reference. Include linter/type-checker output if it flagged code in this area.

### 2. API Contract Safety

| Invariant | Description |
|----------|-------------|
| Input Validation | All external inputs are validated at the boundary using strict schema validation. |
| Error Handling | All errors are caught and transformed into appropriate HTTP responses without leaking internal details. |
| Authentication Enforcement | Access to protected endpoints requires valid authentication tokens. |
| Authorization Granularity | Permissions are checked at the resource level, ensuring users can only access allowed resources. |
| Consistent Error Responses | Error responses follow a consistent structure and include actionable information. |
| Secure Token Handling | Authentication tokens are generated with strong algorithms, validated properly, and stored securely. |
| Rate Limiting | Exhaustive rate limiting prevents abuse and protects system availability. |
| Idempotency & Safety | State-modifying operations are idempotent where appropriate and follow HTTP safety guarantees. |

**Evidence required:** Read the validation schemas and error handlers — do not assume they work because they exist. Verify auth middleware/dependency is actually applied to each protected route, not just defined.

### 3. Access Control & Security

| Invariant | Description |
|----------|-------------|
| Defense in Depth | Multiple layers of security (transport, application, data) protect against common vulnerabilities. |
| Secret Management | Secrets are never hardcoded and are managed through secure configuration mechanisms. |
| Password Security | Passwords are hashed using strong, adaptive algorithms and never stored or logged in plaintext. |
| Input Sanitization | All user inputs are sanitized to prevent injection attacks (SQL, path traversal, etc.). |
| Secure Defaults | The system fails securely: missing or invalid configurations result in safe defaults or explicit failure. |
| Audit Trail | Security-relevant events (login, permission changes, data access) are logged for forensic analysis. |
| Configuration Security | Configuration differences between environments do not introduce security weaknesses. |
| Privilege Separation | Administrative functions are isolated and require explicit elevation of privileges. |

### 4. Data Processing Correctness

| Invariant | Description |
|----------|-------------|
| Deterministic Processing | Identical input data always produces identical aggregated outputs, ensuring reproducibility. |
| Full Recalculation | Each data upload triggers a complete recalculation of all aggregated metrics, avoiding incremental drift. |
| Resource Safety | Temporary files are created in secure locations and are guaranteed to be cleaned up after processing. |
| Error Containment | Processing failures are isolated and do not corrupt existing data or leave the system in an inconsistent state. |
| Schema Evolution | The system gracefully handles schema changes in input data through explicit versioning or validation. |
| Performance Scalability | Processing time scales linearly with input size, avoiding quadratic or exponential complexity. |
| Transactional Integrity | Data processing operations are atomic and maintain database consistency through proper transaction management. |

**Evidence required:** Read the actual processing code end-to-end. Trace a file from upload to stored aggregate. Check for `try/finally` or context managers around temp file creation. Verify that transactions wrap multi-step writes.

### 5. Code Quality & Maintainability

| Invariant | Description |
|----------|-------------|
| Type Safety | All public interfaces are explicitly typed, enabling static analysis and reducing runtime errors. |
| Dependency Clarity | Dependencies are explicit and minimal, reducing coupling and simplifying change impact analysis. |
| Consistent Conventions | Naming, formatting, and architectural patterns are consistent across the codebase. |
| Documentation Clarity | Non-obvious logic is documented with clear, English comments and docstrings. |
| Testability | Code is structured to facilitate unit testing, with dependencies injectable and side effects isolated. |
| Async Correctness | Asynchronous code avoids blocking operations and uses proper await semantics. |
| Observability | Structured logging and error tracking provide sufficient diagnostics for production issues. |
| Dependency Hygiene | External dependencies are monitored for security vulnerabilities and kept up to date. |

**Evidence required:** Linter and type-checker output IS the evidence for type safety and conventions. Check for `print()` statements (forbidden per project rules). Search for blocking calls inside `async def` functions.

---

## Report Output

Write findings to: `.ai/audit/01-backend/findings.md` using template `.ai/audit/templates/audit-findings.md`.

Use prefix `BE-` for finding IDs.

**`problems-only: true` rules:**
- The report contains **only findings** — real problems discovered during investigation.
- Do NOT include sections, dimensions, or checklist rows where everything is correct.
- If after completing all Runtime Verification steps and all Audit Dimensions, no problems were found, write a single line: `No problems found in this phase.`
- Every finding MUST include:
  1. **Runtime evidence** — linter output, test failures, import errors, dead code proof (file:line), or tracebacks.
  2. **Not just:** "violates invariant X" — show the exact code that violates it and the exact consequence.
