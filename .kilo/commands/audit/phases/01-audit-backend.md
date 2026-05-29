---
name: 01-backend
description: Backend architecture audit covering architectural integrity, API contract safety, access control, data processing correctness, and code quality
agent: audit-executor
alwaysApply: false
---

# Phase 01 Audit — Backend Architecture

**Executor:** audit-executor
**Status:** {pending|in-progress|complete}
**Validated:** {yes|no}

---

## Discovery Stage

Before performing audit checks, discover the project's architectural reality:

1. **Architecture Discovery**
   - Identify the primary architectural pattern (Clean Architecture, Onion, Hexagonal, etc.)
   - Map layer boundaries: transport/presentation → business logic → data access
   - Identify dependency flow direction
   - Locate trust boundaries and security entry points

2. **Layer Identification**
   - Transport/HTTP layer: where requests enter the system
   - Business logic layer: core application rules and orchestration
   - Data access layer: persistence and external data integrations
   - Configuration layer: settings and environment management

3. **Critical Flows Discovery**
   - Authentication and authorization entry points
   - Data ingestion and processing pipelines
   - Background task execution paths
   - Error handling and logging flow

4. **Runtime Model**
   - Async/sync execution context
   - Session/connection management
   - Transaction boundaries
   - Resource cleanup mechanisms

---

## Audit Scope

- Transport layer (API routing, request/response handling)
- Domain layer (business logic, use cases, services)
- Persistence layer (data access, storage, transactions)
- Cross-cutting concerns (security, logging, configuration, error handling)
- Data processing layer (ingestion, transformation, storage of uploaded data)

---

## Audit Dimensions

### 1. Architectural Integrity

Evaluate whether the system maintains proper separation of concerns and architectural boundaries.

| Invariant | Description |
|----------|-------------|
| Layer Isolation | Transport layer depends only on interface contracts, not on persistence or domain implementation details. |
| Dependency Direction | Dependencies point inward: domain layer does not depend on transport or persistence; persistence layer does not depend on domain. |
| No Business Logic in Transport | Route handlers contain only HTTP-specific logic (validation, serialization, service invocation). |
| Data Access Encapsulation | All database interactions are abstracted behind repository interfaces; no raw SQL in service or transport layers. |
| Dependency Management | Dependencies are centrally managed and injectable, allowing for replacement and testing. |
| Enum Safety | Domain-critical constants are represented as enumerated types to avoid magic strings and ensure type safety. |

### 2. API Contract Safety

Evaluate the safety and correctness of the API interface.

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

### 3. Access Control & Security

Evaluate the effectiveness of security mechanisms and access controls.

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

Evaluate the correctness and reliability of the data processing pipeline.

| Invariant | Description |
|----------|-------------|
| Deterministic Processing | Identical input data always produces identical aggregated outputs, ensuring reproducibility. |
| Full Recalculation | Each data upload triggers a complete recalculation of all aggregated metrics, avoiding incremental drift. |
| Resource Safety | Temporary files are created in secure locations and are guaranteed to be cleaned up after processing. |
| Error Containment | Processing failures are isolated and do not corrupt existing data or leave the system in an inconsistent state. |
| Schema Evolution | The system gracefully handles schema changes in input data through explicit versioning or validation. |
| Performance Scalability | Processing time scales linearly with input size, avoiding quadratic or exponential complexity. |
| Transactional Integrity | Data processing operations are atomic and maintain database consistency through proper transaction management. |

### 5. Code Quality & Maintainability

Evaluate the codebase for maintainability, readability, and adherence to engineering best practices.

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

---

## Report Output

Write findings to: `.ai/audit/01-backend/findings.md` using template `.ai/audit/templates/audit-findings.md`.

Use prefix `BE-` for finding IDs.