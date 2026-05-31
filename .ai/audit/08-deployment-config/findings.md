# Phase 08 Audit Findings — Configuration & Lifecycle

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### DC-001: Debug mode allowed in production configuration without blocking validation

| Field | Value |
|-------|-------|
| **ID** | DC-001 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/config.py, src/mkobi/app.py |
| **Classification** | advisory |

**Description:** The application allows `debug=True` to be set in production without explicit validation that prevents startup with debug mode enabled. While the spec (SPEC.md line 120) mentions "Production debug mode disabled" as a requirement, there is no validation to reject debug mode in production environment. The `debug` setting defaults to `False` and is passed to FastAPI's debug parameter, but a misconfiguration could allow debug mode in production.

**Evidence:**
- `src/mkobi/config.py` line 244: `debug: bool = False` - defaults to False but no validation against production environment
- `src/mkobi/app.py` line 144-145: `debug=config.debug` passed directly to FastAPI without environment check
- `src/mkobi/config.py` lines 286-310: Admin credential validation exists for production but debug mode has no equivalent check

**Recommendation:** Add validation in `create_app()` to reject `debug=True` when `environment == EnvironmentEnum.PRODUCTION`, similar to the CORS and JWT secret validation already present.

---

### DC-002: Rate limiter uses fail-open mode by default

| Field | Value |
|-------|-------|
| **ID** | DC-002 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | docker/docker-compose.yml, src/mkobi/config.py |
| **Classification** | advisory |

**Description:** The rate limiter defaults to `fail_closed: false` (fail-open mode). When Redis is unavailable, requests are allowed through. According to SPEC.md line 119, this is intentional ("Fail-open rate limiter — When Redis is unavailable, requests are allowed through by default (configurable to fail-closed)"), but this is a security risk in production environments as it allows traffic to bypass rate limiting during Redis outages.

**Evidence:**
- `docker/docker-compose.yml` does not set `RATE_LIMITER_FAIL_CLOSED` environment variable
- `src/mkobi/config.py` line 283: `rate_limiter_fail_closed: bool = Field(default=False, alias="RATE_LIMITER_FAIL_CLOSED")`
- `src/mkobi/services/auth_service.py` line 56-59: Rate limiter is initialized with `fail_closed=config.rate_limiter_fail_closed`
- `src/mkobi/.env.example` line 56 is missing `RATE_LIMITER_FAIL_CLOSED=true` for production guidance

**Recommendation:** Add explicit documentation recommending `RATE_LIMITER_FAIL_CLOSED=true` for production deployments, or set it to `true` by default to prioritize security over availability.

---

### DC-003: Test environment credentials use weak defaults in docker-compose.test.yml

| Field | Value |
|-------|-------|
| **ID** | DC-003 |
| **Severity** | LOW |
| **Type** | BEHAVIORAL-GAP |
| **Affected Modules** | docker/docker-compose.test.yml |
| **Classification** | advisory |

**Description:** The test Docker Compose configuration uses the same weak default passwords as the development environment. While this is intentional for test isolation, the `JWT__SECRET_KEY` defaults to `test_secret_key` which is a predictable value. Test environments should use distinct, non-production-looking credentials to prevent accidental leakage or confusion about which environment is being used.

**Evidence:**
- `docker/docker-compose.test.yml` line 67: `JWT__SECRET_KEY: ${JWT__SECRET_KEY:-test_secret_key}`
- `docker/docker-compose.test.yml` line 70: `ADMIN_PASSWORD: ${ADMIN_PASSWORD:-admin@example.com}`
- These match the dev defaults in `docker-compose.override.yml`

**Recommendation:** Use clearly test-marked defaults like `test_jwt_secret_for_ci_only` or generate random secrets at startup to make test environment credentials obviously non-production.

---

### DC-004: TaskQueue (in-memory) and RQ worker coexistence without clear migration path

| Field | Value |
|-------|-------|
| **ID** | DC-004 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | src/mkobi/core/task_queue.py, docker/docker-compose.yml |
| **Classification** | advisory |

**Description:** The application has two parallel task processing mechanisms: an in-memory `TaskQueue` (`core/task_queue.py`) for MVP and dedicated RQ workers (`rq-worker` service in docker-compose.yml). According to SPEC.md line 121-122, the in-memory queue is the MVP with documented migration path, but both can be active simultaneously without clear indication which is being used. The `enqueue_job` function in `file_processing.py` uses `TaskQueue`, while `data_worker.py` provides both async and sync RQ-compatible interfaces.

**Evidence:**
- `src/mkobi/core/task_queue.py` lines 18-149: Full in-memory TaskQueue implementation
- `docker/docker-compose.yml` lines 126-162: RQ worker service defined but only for `profiles: [production]`
- `src/mkobi/services/file_processing.py` lines 190-197: Uses `enqueue_job` from `TaskQueue`, not RQ

**Recommendation:** Add clear documentation about which queue is used in which environment, or implement a single unified interface that delegates to either TaskQueue (for dev) or RQ (for production) based on a config flag.

---

### DC-005: Database password validation inconsistent across URL properties

| Field | Value |
|-------|-------|
| **ID** | DC-005 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | src/mkobi/config.py |
| **Classification** | mandatory |

**Description:** The `DATABASE_URL` property (lines 398-401) always returns a URL without checking if `database.password` is set. However, `TEST_DATABASE_URL` and `TEST_ADMIN_DATABASE_URL` properties (lines 403-447) return `None` when their passwords are not configured. This inconsistency means the application can start with an invalid database URL that has no password, leading to runtime connection failures.

**Evidence:**
- `src/mkobi/config.py` line 399-401: `DATABASE_URL` property returns `str(self.database.database_url)` unconditionally
- `src/mkobi/config.py` line 406: `if not self.database.password: return None` check exists for test URLs
- `src/mkobi/db/starter.py` line 136-138: Checks `if not main_url: raise DatabaseNotFoundError("Main database URL not configured")` but this check would pass even with an empty password

**Recommendation:** Add validation in `DATABASE_URL` property (or via model validator) to ensure `database.password` is set before returning the URL, preventing startup with incomplete database configuration.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 2 |
| LOW | 2 |

## Mandatory Fixes

- DC-005: Database password validation inconsistent across URL properties

## Advisory Recommendations

- DC-001: Debug mode allowed in production configuration without blocking validation
- DC-002: Rate limiter uses fail-open mode by default
- DC-003: Test environment credentials use weak defaults
- DC-004: TaskQueue and RQ worker coexistence without clear migration path

---

## Template Field Reference

### Mandatory Fields Per Finding

| Field | Type | Values/Format |
|-------|------|---------------|
| `id` | string | Unique identifier within phase (e.g., `BE-001`, `FE-003`) |
| `title` | string | Human-readable one-line summary |
| `type` | enum | `SPEC-DEVIATION`, `BEST-PRACTICE`, `DOC-UPDATE`, `RUNTIME-ERROR` |
| `severity` | enum | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `description` | string | Detailed problem description with context |
| `evidence` | string | File paths, line references, log excerpts, code snippets |
| `affected_modules` | list | Affected module paths (e.g., `src/mkobi/api/routes/`, `frontend/src/features/auth/`) |
| `recommendation` | string | Concrete fix direction: what to change and why |
| `classification` | enum | `mandatory` (security, data loss, correctness) or `advisory` (improvement, refactoring) |

### Classification Guide

- **mandatory**: Security vulnerabilities, data loss risks, correctness issues, spec deviations requiring immediate fix
- **advisory**: Code quality improvements, refactoring suggestions, best practice enhancements