---
name: 01-backend-validated
description: Validated backend architecture audit findings
agent: validator
source: .ai/audit/01-backend/findings.md
status: validated
---

# Phase 01 Validated Findings — Backend Architecture

**Validator:** validator
**Source:** .ai/audit/01-backend/findings.md
**Date:** 2026-05-29

---

## Summary

| Category | Count |
|----------|-------|
| **Total Findings** | 18 |
| **Validated (Accepted)** | 17 |
| **Validated with Corrections** | 1 |
| **Rejected** | 0 |
| **Mandatory Fixes** | 3 |
| **Advisory Recommendations** | 15 |
| **Doc Updates** | 5 |

---

## Validated Findings

---

### BE-001: Clean Architecture Implementation Verified

| Field | Value |
|-------|-------|
| **ID** | BE-001 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/api/`, `src/mkobi/services/`, `src/mkobi/db/repositories/` |
| **Classification** | advisory |
| **Validation Status** | ACCEPTED |

**Description:** The backend correctly implements Clean Architecture with clear layer separation. Route handlers delegate to services, services depend on repository interfaces, and repositories handle database interactions. Dependency flow is inward.

**Verified Against Code:**
- `upload.py`: Route handlers contain only HTTP logic, call `data_service.process_upload()`
- `data_service.py`: Business logic encapsulated, depends on repository interfaces
- `service_interfaces.py`: Full abstract interface contracts (IAuthService, IDataService, etc.)
- `repository_interfaces.py`: Full abstract repository contracts (IAggregatedDataRepository, etc.)

**Dependency Notes:** None — foundational architecture.
**Rollout Considerations:** No action needed.

---

### BE-002: All Constants Represented as StrEnum

| Field | Value |
|-------|-------|
| **ID** | BE-002 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/models/enums.py` |
| **Classification** | advisory |
| **Validation Status** | ACCEPTED |

**Description:** All domain-critical constants use `StrEnum`. 17 enum classes found including `UserRole`, `DashboardPermission`, `GraphType`, `FilterType`, `UploadMode`, `ProcessingStatus`, `MimeTypeEnum`, `FileExtensionEnum`, `AggregationFunctionEnum`, etc.

**Verified Against Code:**
- `enums.py` (lines 9-171): All constants properly typed as `StrEnum`
- No magic string constants found in business logic

**Dependency Notes:** None.
**Rollout Considerations:** No action needed.

---

### BE-003: JWT Authentication with Secure Token Handling

| Field | Value |
|-------|-------|
| **ID** | BE-003 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/core/security.py`, `src/mkobi/api/routes/auth.py` |
| **Classification** | advisory |
| **Validation Status** | ACCEPTED (doc update recommended) |

**Description:** JWT tokens use HS256, access token lifetime is 15 minutes, refresh tokens live 7 days. bcrypt with SALT_ROUNDS=12. Refresh tokens stored in httpOnly cookies with `samesite="strict"`.

**Verified Against Code:**
- `security.py` (lines 211-256): Token creation with proper expiration
- `security.py` (lines 150-208): bcrypt password hashing
- `config.py` (JWTSettings): algorithm, access_token_expire_minutes=15, refresh_token_expire_minutes=10080
- `security.py` (set_secure_cookie, delete_secure_cookie): httpOnly, samesite, configurable secure flag

**Dependency Notes:** None.
**Rollout Considerations:** No code change needed. Doc update recommended.
**Doc Updates Needed:** Document security model assumptions (HTTPS requirement, cookie security, token lifecycle).

---

### BE-004: Rate Limiting Implementation with Fail-Closed Option

| Field | Value |
|-------|-------|
| **ID** | BE-004 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/core/security.py`, `src/mkobi/config.py` |
| **Classification** | advisory |
| **Validation Status** | ACCEPTED |

**Description:** Rate limiting properly implemented with Redis, sync and async variants, fail-closed mode, per-IP keys for login (prevents email enumeration).

**Verified Against Code:**
- `security.py` (lines 46-111): `RateLimiter` and `AsyncRateLimiter` with fail_closed support
- `config.py`: `rate_limiter_fail_closed` setting

**Dependency Notes:** Requires Redis for effective rate limiting.
**Rollout Considerations:** No action needed.

---

### BE-005: Production Credential Validation

| Field | Value |
|-------|-------|
| **ID** | BE-005 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/config.py` |
| **Classification** | mandatory |
| **Validation Status** | ACCEPTED |

**Description:** Application validates admin credentials against weak/common values in production. Refuses to startup with `ValueError` if defaults are detected. Checks against `WEAK_USERNAMES` and `WEAK_PASSWORDS` sets (not just exact "admin"/"admin" string).

**Verified Against Code:**
- `config.py` (lines 17-18): `WEAK_USERNAMES` and `WEAK_PASSWORDS` sets defined
- `config.py` (lines 285-310): `validate_admin_credentials` model validator with production check

**Dependency Notes:** None.
**Rollout Considerations:** No action needed — correct implementation.

---

### BE-006: Temporary File Cleanup on Processing Failure

| Field | Value |
|-------|-------|
| **ID** | BE-006 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/api/routes/upload.py`, `src/mkobi/workers/data_worker.py` |
| **Classification** | advisory |
| **Validation Status** | ACCEPTED |

**Description:** Temporary files cleaned up in both success and failure paths. Upload route cleans up in `finally` block, worker cleans up on success and failure. Uses `platformdirs` for secure temp directory.

**Verified Against Code:**
- `upload.py` (lines 188-193): Cleanup in `finally` block after failed upload
- `data_worker.py`: Cleanup in both `_process_csv_file_async` success path and exception handler

**Dependency Notes:** Cleanup spread across two modules — requires both to be correct.
**Rollout Considerations:** No action needed.

---

### BE-007: CORS Configuration Security in Production

| Field | Value |
|-------|-------|
| **ID** | BE-007 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/app.py` |
| **Classification** | mandatory |
| **Validation Status** | ACCEPTED |

**Description:** Application enforces CORS configuration in production — refuses to start if origins are empty or wildcard (`*`).

**Verified Against Code:**
- `app.py` (lines ~126-138): Validates `cors_origins` in production, raises `ValueError` if empty or contains `*`

**Dependency Notes:** None.
**Rollout Considerations:** No action needed — critical security control verified.

---

### BE-008: Permission Check Bypass for Admin Role

| Field | Value |
|-------|-------|
| **ID** | BE-008 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/core/permissions.py`, `src/mkobi/services/dashboard_service.py` |
| **Classification** | advisory |
| **Validation Status** | ACCEPTED |

**Description:** Admin users have implicit access to all dashboards. Verified in `_check_access_with_session` and `DashboardService.get_dashboard`. Documented in SPEC.md.

**Verified Against Code:**
- `permissions.py`: Admin bypass in `_check_access_with_session` — checks `user.role == UserRole.ADMIN`
- `dashboard_service.py`: Admin bypass in `get_dashboard` — checks `user_role == UserRole.ADMIN`
- SPEC.md: Documents admin bypass and 403/404 dual-signal design

**Dependency Notes:** None.
**Rollout Considerations:** No action needed — intentional design.

---

### BE-009: No Raw SQL or f-string SQL Queries Found

| Field | Value |
|-------|-------|
| **ID** | BE-009 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | Entire backend codebase |
| **Classification** | advisory |
| **Validation Status** | ACCEPTED |

**Description:** All database queries use SQLAlchemy ORM/Core with parameterized queries. No f-string SQL or raw string concatenation found.

**Verified Against Code:**
- Grepped for `f".*SELECT|f".*INSERT|f".*UPDATE|f".*DELETE` — zero matches
- `storage.manager.py`: Uses `insert()`, `delete()`, `select()` with proper parameterization
- `data_worker.py`: Uses `update()`, `select()` with parameterized statements

**Dependency Notes:** None.
**Rollout Considerations:** No action needed.

---

### BE-010: No print() Statements in Code

| Field | Value |
|-------|-------|
| **ID** | BE-010 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | Entire backend codebase |
| **Classification** | advisory |
| **Validation Status** | ACCEPTED |

**Description:** No `print()` statements found in codebase. All logging uses `logging.getLogger(__name__)`.

**Verified Against Code:**
- Grepped for `print(` in `src/mkobi/` — zero matches

**Dependency Notes:** None.
**Rollout Considerations:** No action needed.

---

### BE-011: Transaction Management in Data Processing

| Field | Value |
|-------|-------|
| **ID** | BE-011 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/workers/data_worker.py`, `src/mkobi/data/storage/manager.py` |
| **Classification** | advisory |
| **Validation Status** | ACCEPTED (doc update recommended) |

**Description:** Background worker uses `session.begin()` for explicit transaction control in `_store_aggregates`. `StorageManager` relies on caller to manage transactions — documented in module docstring ("Does not manage transactions (commit/rollback is external)").

**Verified Against Code:**
- `data_worker.py` (production path): `async with session.begin()` wraps all aggregate storage operations
- `storage.manager.py` (module docstring): Explicitly states "Does not manage transactions"

**Dependency Notes:** `StorageManager` depends on caller transaction management.
**Rollout Considerations:** No code change needed. Doc update recommended to formalize caller responsibilities.
**Doc Updates Needed:** Document transaction management expectations for StorageManager callers.

---

### BE-012: All Public Functions Have Type Hints

| Field | Value |
|-------|-------|
| **ID** | BE-012 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/services/`, `src/mkobi/api/routes/` |
| **Classification** | advisory |
| **Validation Status** | ACCEPTED (with correction) |

**Description:** All public functions and methods have type hints. Correction to audit's claim: `Any` return types DO exist in the codebase — specifically in `StorageManager._normalize_json_keys(data: Any) -> Any` (internal) and `TaskQueue.get_result(task_id: str) -> Any` (internal). Interface repositories (`repository_interfaces.py`) also use `Any` in method signatures (e.g., `async def get(...) -> Any | None`), which is inherent to generic repository interfaces and is acceptable. The audit's claim is therefore slightly overstated but directionally correct — no public service/API-facing methods use `Any` as return types.

**Verified Against Code:**
- Service layer methods: All have concrete return types
- Interface methods: Use `Any` due to generic patterns — acceptable design
- Internal helpers: `_normalize_json_keys`, `get_result` use `Any` — acceptable

**Dependency Notes:** None.
**Rollout Considerations:** No action needed. Interface-level `Any` is idiomatic for generic repository patterns.

---

### BE-013: Structured Logging Implemented

| Field | Value |
|-------|-------|
| **ID** | BE-013 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/core/logging_config.py` |
| **Classification** | advisory |
| **Validation Status** | ACCEPTED |

**Description:** JSON structured logging with `JSONFormatter` class, consistent format across modules, configurable via `setup_logging()`.

**Verified Against Code:**
- `logging_config.py` (lines 14-69): `JSONFormatter` with timestamp, level, service, message, module, function
- `JSONFormatter.format`: Handles extra fields from `logger.info("msg", extra={...})`
- `setup_logging()`: Configures hierarchical loggers for all `mkobi.*` subpackages

**Dependency Notes:** None.
**Rollout Considerations:** No action needed.

---

### BE-014: Secret Management via Environment Variables and Docker Secrets

| Field | Value |
|-------|-------|
| **ID** | BE-014 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/config.py` |
| **Classification** | advisory |
| **Validation Status** | ACCEPTED |

**Description:** Secrets via env vars with Docker secrets support (`_FILE` suffix pattern). `SecretsFileSource` reads from `/run/secrets/`. Priority: env vars > Docker secrets > .env > YAML > defaults.

**Verified Against Code:**
- `config.py` (lines 36-70): `SecretsFileSource` for Docker secrets
- `config.py` `settings_customise_sources()`: Explicit 5-level priority chain

**Dependency Notes:** None.
**Rollout Considerations:** No action needed.

---

### BE-015: Input Validation on Multiple Levels

| Field | Value |
|-------|-------|
| **ID** | BE-015 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/api/routes/upload.py`, `src/mkobi/services/file_processing.py`, `src/mkobi/services/auth_service.py` |
| **Classification** | advisory |
| **Validation Status** | ACCEPTED |

**Description:** Multi-layer validation: Pydantic at route level, MIME-type and extension in file processing, business logic in services.

**Verified Against Code:**
- `file_processing.py`: `validate_mime_type`, `validate_file` with size/format checks
- `upload.py`: Additional size pre-check before reading file content
- `auth_service.py`: Email format validation

**Dependency Notes:** None.
**Rollout Considerations:** No action needed.

---

### BE-016: Error Handling Does Not Leak Internal Details

| Field | Value |
|-------|-------|
| **ID** | BE-016 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION → BEST-PRACTICE |
| **Affected Modules** | `src/mkobi/api/routes/upload.py`, all route modules |
| **Classification** | advisory (upgraded to mandatory — see correction) |
| **Validation Status** | ACCEPTED WITH CORRECTION |

**Description:** Most error handlers properly sanitize user-facing messages. However, **several routes leak internal exception details** in their generic exception handlers through `detail=f"...: {str(e)}"` patterns.

**Evidence of Leaks Found:**
- `upload.py` line 209: `detail=f"Error during file upload: {e}"` — passes raw exception to client
- `layouts.py` lines 100, 139, 188, 269, 332: All use `detail=f"...: {str(e)}"` in generic exception handlers
- `processing_logs.py` lines 87, 120: Same pattern
- `dashboards_crud.py` line 198: Same pattern

**Contrast with Correct Patterns (sanitized):**
- `dashboards_crud.py` line 74: `detail="Error getting dashboards"` — generic message, correct
- `upload.py` line 270: `detail="Error starting processing"` — generic message, correct
- `data.py` line 141: `detail="Error getting data"` — generic message, correct

**Correction to Audit Finding:** The finding is partially correct in spirit but overstates the sanitization. The upload route and layout route explicitly leak `str(e)` to clients. The finding should be classified as a **mandatory fix** (MEDIUM severity) rather than advisory, because leaking internal error messages aids attackers in reconnaissance.

**Root Cause:** Inconsistent error handling pattern across route modules. Some use generic messages, others interpolate exception strings.

**Recommendation:** Audit all route modules for `f"...{e}"` and `f"...{str(e)}"` in `detail=` parameters. Replace with generic messages. Log the full exception server-side via `logger.error()`.

**Dependency Notes:** Affects multiple route modules — should be addressed as a single cross-cutting cleanup task.
**Rollout Considerations:** Low risk — only affects error path responses. Can be done as isolated changes per route module.

**Classification: MANDATORY** (upgraded from advisory)

---

### BE-017: Full Aggregation Recalculation on Upload

| Field | Value |
|-------|-------|
| **ID** | BE-017 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/workers/data_worker.py`, `src/mkobi/data/storage/manager.py` |
| **Classification** | advisory |
| **Validation Status** | ACCEPTED |

**Description:** Each upload triggers complete recalculation. OVERWRITE clears old data, APPEND performs upsert. Documented in SPEC.md.

**Verified Against Code:**
- `data_worker.py` `_store_aggregates`: Mode-aware storage
- `storage.manager.py` `save_aggregates`: `clear_old` flag triggers delete before insert
- SPEC.md: Documents full recalculation design

**Dependency Notes:** None.
**Rollout Considerations:** No action needed.

---

### BE-018: In-Memory Task Queue (MVP) with Migration Path

| Field | Value |
|-------|-------|
| **ID** | BE-018 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/core/task_queue.py`, `src/mkobi/workers/data_worker.py` |
| **Classification** | advisory |
| **Validation Status** | ACCEPTED (doc update recommended) |

**Description:** In-memory `TaskQueue` for MVP. Migration path to Redis/RQ documented in SPEC.md and `task-queue-migration.md`. Stale processing cleanup task handles crashed workers.

**Verified Against Code:**
- `task_queue.py`: In-memory `asyncio.Queue`-based implementation
- `data_worker.py`: `start_stale_processing_cleanup_task` for crashed worker recovery
- SPEC.md: Documents migration path

**Dependency Notes:** None.
**Rollout Considerations:** No action needed for MVP.
**Doc Updates Needed:** Ensure migration guide is up-to-date for production deployments.

---

## Merged Findings

**None.** All 18 findings address distinct concerns. No semantic overlap requiring merge.

---

## Dependency Validation Results

| Relationship | Status |
|---|---|
| Security controls (BE-003, BE-004, BE-005, BE-007) | Independent, no circular dependencies |
| Error handling (BE-016) → Input validation (BE-015) | Complementary, not conflicting |
| Transaction management (BE-011) → Data processing (BE-017) | Consistent — both verified correct |
| Architecture (BE-001) → All other findings | Foundational, no conflicts |

**Result:** No circular dependencies, no conflicting recommendations, no unsafe rollout orderings.

---

## Rollout Safety Analysis

All validated findings are either:
1. **No-op advisory** (no code change needed): BE-001, BE-002, BE-004, BE-008, BE-009, BE-010, BE-012, BE-013, BE-014, BE-015, BE-017
2. **Doc-only changes**: BE-003, BE-011, BE-018
3. **Code fix with low risk**: BE-016 (error message sanitization)
4. **Already-implemented mandatory controls**: BE-005, BE-007

**BE-016 is the only finding requiring code changes** (beyond existing mandatory controls). The fix is low-risk — replacing interpolated exception strings with generic messages in error responses. Each route module can be fixed independently.

---

## Task Applicability Status

| Finding | Applicable | Anchors Stable | Safe to Execute |
|---------|-----------|----------------|-----------------|
| BE-001 | Yes — verified | Yes (existing code) | N/A (no action) |
| BE-002 | Yes — verified | Yes | N/A (no action) |
| BE-003 | Yes — verified | Yes | Doc update safe |
| BE-004 | Yes — verified | Yes | N/A (no action) |
| BE-005 | Yes — verified | Yes | N/A (already correct) |
| BE-006 | Yes — verified | Yes | N/A (no action) |
| BE-007 | Yes — verified | Yes | N/A (already correct) |
| BE-008 | Yes — verified | Yes | N/A (no action) |
| BE-009 | Yes — verified | Yes | N/A (no action) |
| BE-010 | Yes — verified | Yes | N/A (no action) |
| BE-011 | Yes — verified | Yes | Doc update safe |
| BE-012 | Yes — verified | Yes | N/A (no action) |
| BE-013 | Yes — verified | Yes | N/A (no action) |
| BE-014 | Yes — verified | Yes | N/A (no action) |
| BE-015 | Yes — verified | Yes | N/A (no action) |
| BE-016 | Yes — verified | **Yes — specific lines identified** | Safe — isolated per-module fixes |
| BE-017 | Yes — verified | Yes | N/A (no action) |
| BE-018 | Yes — verified | Yes | Doc update safe |

---

## Architectural Consistency Warnings

**None.** The architecture is internally consistent. Clean Architecture layers are properly separated. All security controls operate at correct boundaries. Error handling inconsistency (BE-016) is a code-level issue, not an architectural one.

---

## Mandatory Fixes

1. **BE-005** — Production credential validation (HIGH) — already correctly implemented
2. **BE-007** — CORS configuration security in production (HIGH) — already correctly implemented
3. **BE-016** — Error handling leaks internal details in upload route and layout route (MEDIUM) — **upgraded from advisory to mandatory** — fix needed

---

## Advisory Recommendations

1. **BE-001** — Clean Architecture verified — no action needed
2. **BE-002** — StrEnum usage verified — no action needed
3. **BE-004** — Rate limiting verified — no action needed
4. **BE-006** — Temp file cleanup verified — no action needed
5. **BE-008** — Admin bypass verified — no action needed
6. **BE-009** — SQL safety verified — no action needed
7. **BE-010** — No print() verified — no action needed
8. **BE-012** — Type hints verified — no action needed
9. **BE-013** — Structured logging verified — no action needed
10. **BE-014** — Secret management verified — no action needed
11. **BE-015** — Input validation verified — no action needed
12. **BE-017** — Full aggregation recalculation verified — no action needed
13. **BE-018** — In-memory queue verified — migration needed for production

---

## Doc Updates Needed

| Finding | Doc Change |
|---------|-----------|
| BE-003 | Add security model documentation for JWT/cookie implementation (HTTPS requirement, token lifecycle, cookie attributes) |
| BE-011 | Document transaction management expectations for StorageManager callers |
| BE-018 | Ensure Redis/RQ task queue migration guide is up-to-date |
| BE-016 | Document error handling conventions — generic user-facing messages, detailed server-side logging |

---

## Validation Notes

**Verified by direct code inspection.** Each finding was checked against the actual source code at the referenced line numbers and module paths. All evidence citations in the original audit were validated except:

1. **BE-012 correction:** The finding states "No `Any` return types found in public interfaces (only in internal `StorageService`)". This is incorrect — `Any` is used in `repository_interfaces.py` (all repository interfaces), `security.py` (`_get_config`), and `task_queue.py` (`get_result`). Interface-level `Any` is idiomatic and acceptable for generic repository patterns.

2. **BE-016 correction:** The finding states "Error messages in responses are sanitized" but this is inconsistent across the codebase. The upload route and layout route explicitly leak `str(e)` to clients in their generic exception handlers. This finding was upgraded to mandatory.

**Overall assessment:** The audit was thorough and accurate for 17 of 18 findings. The two corrections above do not undermine the audit's validity — one is a minor overstatement (BE-012), and the other identifies an actual issue the audit misclassified as resolved (BE-016).
