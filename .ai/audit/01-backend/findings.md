---
name: 01-backend-findings
description: Backend architecture audit findings
agent: audit-executor
alwaysApply: false
---

# Phase 01 Audit Findings — Backend Architecture

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### BE-001: Clean Architecture Implementation Verified

| Field | Value |
|-------|-------|
| **ID** | BE-001 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/api/, src/mkobi/services/, src/mkobi/db/repositories/ |
| **Classification** | advisory |

**Description:** The backend correctly implements Clean Architecture with a clear layer separation. Transport layer (API routes) depends on service interfaces, service layer depends on repository interfaces, and repositories handle database interactions. No business logic is found in route handlers - they only contain HTTP-specific logic (validation, serialization, service invocation). Dependency flow is inward with domain layer completely isolated from transport concerns.

**Evidence:**
- `src/mkobi/api/routes/upload.py` (lines 51-210): Route handlers delegate to `DataService` for processing
- `src/mkobi/services/data_service.py` (lines 76-151): Business logic encapsulated in service methods
- `src/mkobi/interfaces/service_interfaces.py` and `src/mkobi/interfaces/repository_interfaces.py`: Clear interface contracts
- Route handlers use `EditorUser`, `CurrentUser` dependencies for auth, then invoke services

**Recommendation:** No changes required. The architecture follows Clean Architecture principles correctly.

---

### BE-002: All Constants Represented as StrEnum

| Field | Value |
|-------|-------|
| **ID** | BE-002 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/models/enums.py |
| **Classification** | advisory |

**Description:** All domain-critical constants are represented using `StrEnum` for type safety and to avoid magic strings. This includes `UserRole`, `DashboardPermission`, `GraphType`, `FilterType`, `RegistrationStatus`, `UploadMode`, `ProcessingStatus`, `EnvironmentEnum`, `MimeTypeEnum`, `FileExtensionEnum`, and several UI-related enums.

**Evidence:**
- `src/mkobi/models/enums.py` (lines 9-171): Complete enum definitions using StrEnum
- All enum values have `.value` attribute for serialization
- No magic string constants found in codebase (verified via grep for string literals in business logic)

**Recommendation:** No changes required. Enum usage is correct and consistent.

---

### BE-003: JWT Authentication with Secure Token Handling

| Field | Value |
|-------|-------|
| **ID** | BE-003 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/core/security.py, src/mkobi/api/routes/auth.py |
| **Classification** | advisory |

**Description:** JWT tokens are generated with configurable algorithm (HS256), validated properly with signature and expiration checks, and stored in httpOnly cookies. However, the access token lifetime is configured at 15 minutes (not explicitly documented in code comments) and refresh tokens at 7 days. The security implementation follows best practices but could benefit from explicit documentation of the threat model assumptions (HTTPS required in production).

**Evidence:**
- `src/mkobi/core/security.py` (lines 211-256): `create_access_token` and `create_refresh_token` with proper expiration
- `src/mkobi/core/security.py` (lines 150-208): `hash_password` and `verify_password` using bcrypt with SALT_ROUNDS=12
- `src/mkobi/config.py` (lines 124-130): JWT settings with 15-minute access token and 10080-minute (7 day) refresh token
- `src/mkobi/core/security.py` (lines 375-400): Secure cookies with `httponly=True`, `samesite="strict"`

**Recommendation:** Add documentation comments explaining the security model (HTTPS requirement, cookie security) and consider reducing access token lifetime further for high-security scenarios.

---

### BE-004: Rate Limiting Implementation with Fail-Closed Option

| Field | Value |
|-------|-------|
| **ID** | BE-004 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/core/security.py, src/mkobi/config.py |
| **Classification** | advisory |

**Description:** Rate limiting is properly implemented using Redis with both sync and async variants (`RateLimiter` and `AsyncRateLimiter`). The implementation supports configurable fail-closed mode (reject requests when Redis unavailable) and per-IP rate limiting for login attempts to prevent email enumeration attacks.

**Evidence:**
- `src/mkobi/core/security.py` (lines 46-111): Rate limiter classes with fail-closed support
- `src/mkobi/api/routes/auth.py` (lines 65-76): Per-IP rate limiting for login endpoint
- `src/mkobi/api/routes/auth.py` (lines 468-484): Rate limiting for registration requests
- `src/mkobi/config.py` (line 283): `rate_limiter_fail_closed` configuration option

**Recommendation:** No changes required. Rate limiting is properly implemented.

---

### BE-005: Production Credential Validation

| Field | Value |
|-------|-------|
| **ID** | BE-005 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/config.py |
| **Classification** | mandatory |

**Description:** The application validates that admin credentials are not weak/common values in production. It checks against predefined weak username and password sets and raises `ValueError` preventing startup if defaults are detected. This is a critical security control to prevent unauthorized admin access.

**Evidence:**
- `src/mkobi/config.py` (lines 17-18): `WEAK_USERNAMES` and `WEAK_PASSWORDS` sets defined
- `src/mkobi/config.py` (lines 285-310): `validate_admin_credentials` model validator that enforces strong credentials in production

**Recommendation:** Ensure this validation is tested and documented. The current implementation is correct.

---

### BE-006: Temporary File Cleanup on Processing Failure

| Field | Value |
|-------|-------|
| **ID** | BE-006 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/api/routes/upload.py, src/mkobi/services/file_processing.py |
| **Classification** | advisory |

**Description:** Temporary files are properly cleaned up after successful processing (file is moved to final location) and on processing failure. However, the cleanup logic in the upload route only logs cleanup for failed uploads, while the background worker handles cleanup in both success and failure paths. The upload temp directory uses `platformdirs` for secure location.

**Evidence:**
- `src/mkobi/api/routes/upload.py` (lines 188-193): Cleanup in `finally` block for failed uploads
- `src/mkobi/workers/data_worker.py` (lines 237-240, 262-266): Cleanup on success and failure in background worker

**Recommendation:** Consider adding explicit logging for successful file cleanup in the upload route. Ensure the temp directory has proper permissions.

---

### BE-007: CORS Configuration Security in Production

| Field | Value |
|-------|-------|
| **ID** | BE-007 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/app.py |
| **Classification** | mandatory |

**Description:** The application enforces CORS configuration in production - it refuses to start if CORS origins are not configured or if wildcard (`*`) is used. This prevents accidental exposure of the API to all origins in production.

**Evidence:**
- `src/mkobi/app.py` (lines 126-138): Validation that raises `ValueError` if `cors_origins` is empty or contains `*` in production

**Recommendation:** No changes required. This is a critical security control.

---

### BE-008: Permission Check Bypass for Admin Role

| Field | Value |
|-------|-------|
| **ID** | BE-008 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/core/permissions.py, src/mkobi/api/routes/data.py |
| **Classification** | advisory |

**Description:** Admin users have implicit access to all dashboards without requiring explicit `dashboard_access` entries. This is a design decision documented in SPEC.md (line 123). The check is performed in `_check_access_with_session` and `DashboardService.get_dashboard`.

**Evidence:**
- `src/mkobi/core/permissions.py` (lines 175-184): Admin bypass logic
- `src/mkobi/services/dashboard_service.py` (lines 161-168): Admin bypass in dashboard retrieval

**Recommendation:** No changes required. This design is intentional and properly documented.

---

### BE-009: No Raw SQL or f-string SQL Queries Found

| Field | Value |
|-------|-------|
| **ID** | BE-009 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | Entire backend codebase |
| **Classification** | advisory |

**Description:** All database queries use SQLAlchemy ORM/Core with parameterized queries. No raw SQL or f-string SQL queries were found in the codebase, which prevents SQL injection vulnerabilities.

**Evidence:**
- `src/mkobi/db/repositories/aggregated_data_repo.py`: Uses `select()`, `insert()`, `delete()` with proper parameterization
- `src/mkobi/workers/data_worker.py`: Uses SQLAlchemy Core (`update()`, `select()`) with parameterized statements
- Grep search for f-string SQL patterns returned no results

**Recommendation:** No changes required. SQL safety is properly maintained.

---

### BE-010: No print() Statements in Code

| Field | Value |
|-------|-------|
| **ID** | BE-010 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | Entire backend codebase |
| **Classification** | advisory |

**Description:** No `print()` statements were found in the codebase. All logging uses the proper `logging.getLogger(__name__)` pattern for structured logging.

**Evidence:**
- Grep search for `print(` returned no results

**Recommendation:** No changes required. Logging practices are correct.

---

### BE-011: Transaction Management in Data Processing

| Field | Value |
|-------|-------|
| **ID** | BE-011 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/workers/data_worker.py, src/mkobi/data/storage/manager.py |
| **Classification** | advisory |

**Description:** The background processing worker uses explicit transaction management with `session.begin()` for atomic operations. The `_store_aggregates` function wraps all database operations in a transaction block, ensuring atomicity of aggregate storage.

**Evidence:**
- `src/mkobi/workers/data_worker.py` (lines 351-353): Transaction context manager in production mode
- `src/mkobi/data/storage/manager.py`: No explicit transaction handling - relies on caller to manage transactions

**Recommendation:** Consider adding explicit transaction handling in `StorageManager` methods for better encapsulation, though the current approach is workable with proper caller discipline.

---

### BE-012: All Public Functions Have Type Hints

| Field | Value |
|-------|-------|
| **ID** | BE-012 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/services/, src/mkobi/api/routes/ |
| **Classification** | advisory |

**Description:** All public functions and methods have proper type hints, enabling static analysis and reducing runtime errors.

**Evidence:**
- `src/mkobi/services/data_service.py`: All methods have return type annotations
- `src/mkobi/services/auth_service.py`: All methods have return type annotations
- No `Any` return types found in public interfaces (only in internal `StorageService`)

**Recommendation:** No changes required. Type safety is properly maintained.

---

### BE-013: Structured Logging Implemented

| Field | Value |
|-------|-------|
| **ID** | BE-013 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/core/logging_config.py |
| **Classification** | advisory |

**Description:** The application uses structured JSON logging with consistent format across modules. The `JSONFormatter` class provides customizable structured logging output.

**Evidence:**
- `src/mkobi/core/logging_config.py` (lines 14-69): JSON formatter implementation
- All modules use `logger = logging.getLogger(__name__)` pattern
- Extra fields are passed via `logger.info("msg", extra={"key": "value"})`

**Recommendation:** No changes required. Logging is properly structured.

---

### BE-014: Secret Management via Environment Variables and Docker Secrets

| Field | Value |
|-------|-------|
| **ID** | BE-014 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/config.py |
| **Classification** | advisory |

**Description:** Secrets are managed through environment variables with support for Docker secrets files (via `DATABASE__PASSWORD_FILE` pattern). The `SecretsFileSource` class reads secrets from files in `/run/secrets/` directory.

**Evidence:**
- `src/mkobi/config.py` (lines 36-70): `SecretsFileSource` implementation for Docker secrets
- `src/mkobi/config.py` (lines 342-374): Priority order for settings sources (env vars > secrets > .env > yaml > defaults)

**Recommendation:** No changes required. Secret management follows best practices.

---

### BE-015: Input Validation on Multiple Levels

| Field | Value |
|-------|-------|
| **ID** | BE-015 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/api/routes/upload.py, src/mkobi/services/file_processing.py, src/mkobi/services/auth_service.py |
| **Classification** | advisory |

**Description:** Input validation is performed at multiple layers: FastAPI Pydantic validation at the route level, MIME-type and file extension validation in the upload processing, and business logic validation in services.

**Evidence:**
- `src/mkobi/services/file_processing.py` (lines 22-42): `validate_mime_type` function
- `src/mkobi/services/file_processing.py` (lines 45-112): `validate_file` function with size and format checks
- `src/mkobi/services/auth_service.py` (lines 81-96): Email format validation with regex

**Recommendation:** No changes required. Validation is comprehensive.

---

### BE-016: Error Handling Does Not Leak Internal Details

| Field | Value |
|-------|-------|
| **ID** | BE-016 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/api/routes/upload.py, src/mkobi/api/routes/auth.py |
| **Classification** | advisory |

**Description:** HTTP exception handlers transform internal errors into appropriate HTTP responses without exposing stack traces or internal details. The `/health/detailed` endpoint returns component status but not sensitive information.

**Evidence:**
- `src/mkobi/api/routes/upload.py` (lines 71-101): Error mapping that converts internal errors to appropriate HTTP status codes
- `src/mkobi/app.py` (lines 245-284): Exception handlers for HTTP, validation, and Pydantic errors
- Error messages in responses are sanitized (e.g., "Error getting status" instead of full exception)

**Recommendation:** Consider adding correlation IDs for error tracking while maintaining user-facing error message sanitization.

---

### BE-017: Full Aggregation Recalculation on Upload

| Field | Value |
|-------|-------|
| **ID** | BE-017 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/workers/data_worker.py, src/mkobi/data/storage/manager.py |
| **Classification** | advisory |

**Description:** Each data upload triggers a complete recalculation of all aggregated metrics. The `OVERWRITE` mode clears old data before inserting new aggregates, while `APPEND` mode performs upsert.

**Evidence:**
- `src/mkobi/workers/data_worker.py` (lines 274-406): `_store_aggregates` function handling mode-based storage
- `src/mkobi/data/storage/manager.py` (lines 113-134): `clear_old` flag triggers delete before insert
- SPEC.md (line 116): Mentions full recalculation

**Recommendation:** No changes required. The full recalculation approach ensures data consistency.

---

### BE-018: In-Memory Task Queue (MVP) with Migration Path

| Field | Value |
|-------|-------|
| **ID** | BE-018 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/core/task_queue.py, src/mkobi/workers/data_worker.py |
| **Classification** | advisory |

**Description:** The system uses an in-memory `TaskQueue` for MVP with a documented migration path to Redis/RQ. The background worker has both async and sync variants for compatibility. A stale processing cleanup task handles failed workers.

**Evidence:**
- `src/mkobi/core/task_queue.py` (lines 18-122): In-memory task queue implementation
- `src/mkobi/workers/data_worker.py` (lines 485-508): Stale processing cleanup task
- SPEC.md (line 121): Documents migration path

**Recommendation:** The in-memory queue should be replaced with Redis/RQ for production deployments to ensure task persistence across restarts.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 4 |
| LOW | 11 |

## Mandatory Fixes

- BE-005: Production credential validation (HIGH)
- BE-007: CORS configuration security in production (HIGH)

## Advisory Recommendations

- BE-001: Clean Architecture implementation
- BE-002: StrEnum constants usage
- BE-003: JWT authentication documentation
- BE-004: Rate limiting implementation
- BE-006: Temporary file cleanup logging
- BE-008: Admin permission bypass design
- BE-009: SQL safety
- BE-010: No print() statements
- BE-011: Transaction management in StorageManager
- BE-012: Type hints on public functions
- BE-013: Structured logging
- BE-014: Secret management
- BE-015: Input validation
- BE-016: Error handling sanitization
- BE-017: Full aggregation recalculation
- BE-018: In-memory task queue migration

## Doc Updates Needed

- BE-003: Add security model documentation for JWT/cookie implementation
- BE-011: Document transaction management expectations in StorageManager
- BE-018: Create detailed migration guide for Redis/RQ task queue

---