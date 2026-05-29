---
name: 08-deployment-config-validated
description: Validated deployment & configuration audit findings — safety, consistency, and applicability verified
agent: validator
source: .ai/audit/08-deployment-config/findings.md
status: complete
---

# Phase 08 Validated Findings — Configuration & Lifecycle

**Validator:** validator
**Source:** .ai/audit/08-deployment-config/findings.md
**Validated:** yes

---

## Validation Summary

| Severity | Source | Validated (Confirmed) | Requires Reclassification | Rejected |
|----------|--------|----------------------|--------------------------|----------|
| CRITICAL | 1 | 1 | 1 | 0 |
| MEDIUM   | 7 | 7 | 7 | 0 |
| LOW      | 12 | 12 | 12 | 0 |

**Total findings:** 20 — all confirmed as describing existing correct implementation.
**Issues found:** The entire phase's findings are fundamentally reclassified (see below).

---

## Key Reclassification: Phase 08 Findings Are Not Spec Deviations

### Root Cause Analysis

All 20 findings in Phase 08 share the same structural pattern:

1. They describe an existing code behavior (security check, startup validation, graceful shutdown, etc.).
2. They classify it as `SPEC-DEVIATION` with severity.
3. Their recommendation is either "continue current approach — no changes needed" or a minor documentation suggestion.

**Validator determination:** These are not deviations from the specification. They are confirmations that the specification is correctly implemented. The audit findings document what the system already does correctly, mislabeled as deviations.

This is a systematic classification issue across all 20 findings, not a per-finding error.

---

## Per-Finding Reclassification

### DC-001: Configuration centralized in single module

| Field | Value |
|-------|-------|
| **ID** | DC-001 |
| **Original Type** | SPEC-DEVIATION |
| **Validated Type** | SPEC-DEVIATION (confirmed — architecture is correct) |
| **Severity** | LOW |
| **Classification** | advisory |

**Verdict:** VALIDATED. The configuration module is correctly implemented and matches Clean Architecture. The audit describes correct behavior, not a deviation.

**Recommendation from audit is accurate:** Consider documenting the configuration priority order in the module docstring. This is a valid doc improvement suggestion.

---

### DC-002: Secrets derived from environment variables with multiple source support

| Field | Value |
|-------|-------|
| **ID** | DC-002 |
| **Original Type** | SPEC-DEVIATION |
| **Validated Type** | SPEC-DEVIATION (confirmed — implementation is correct) |
| **Severity** | LOW |
| **Classification** | advisory |

**Verdict:** VALIDATED. The `_FILE` pattern, `SecretsFileSource`, and 5-level priority chain are correctly implemented. Tests at `tests/test_config.py:122-151` confirm Docker secrets work correctly. No changes needed.

**Cross-reference:** BE-014 (Phase 01) covers the same finding from the backend architecture perspective. This is a **cross-phase overlap**, not a conflict — both confirm the same correct implementation.

---

### DC-003: Production refuses insecure defaults for admin credentials

| Field | Value |
|-------|-------|
| **ID** | DC-003 |
| **Original Type** | SPEC-DEVIATION |
| **Validated Type** | SPEC-DEVIATION (confirmed — mandatory control is implemented) |
| **Severity** | CRITICAL |
| **Classification** | mandatory |

**Verdict:** VALIDATED. The weak credential validation at `config.py:285-310` is correctly implemented, uses `WEAK_USERNAMES` and `WEAK_PASSWORDS` constants, and is tested (`tests/test_config.py:316-349`). This is a CRITICAL security control that is properly in place — not a deviation to fix.

**Cross-reference:** BE-005 (Phase 01) covers the same validator. **Cross-phase overlap** with BE-005 — both confirm the same mandatory control exists and works correctly.

---

### DC-004: Configuration validated at startup

| Field | Value |
|-------|-------|
| **ID** | DC-004 |
| **Original Type** | SPEC-DEVIATION |
| **Validated Type** | BEST-PRACTICE (reclassified — identifies a potential improvement) |
| **Severity** | LOW |
| **Classification** | advisory |

**Verdict:** VALIDATED with reclassification. The finding changes character on inspection:

- Most of the finding describes existing correct validation (JWT secret, CORS, admin credentials at `app.py:120-138`).
- The actual recommendation is: "Consider adding explicit validation that database URL is provided (currently returns None if password not set, which could cause unclear errors later)."

**Reclassification to BEST-PRACTICE:** The one actionable item — validating database URL presence to prevent unclear downstream errors — is a legitimate defensive programming improvement. This is not a spec deviation; it is a best-practice addition.

**Evidence:** `DatabaseSettings.database_url` property (`config.py:91-101`) will build a URL with `password=None` if password is not set. No startup validation exists to catch this. The fix is small: add a check in `DatabaseStarter.startup()` or the config validator. Low ROI for the current scale — the error will surface quickly at startup when DB connection fails.

**Semantic stability:** Anchor at `DatabaseStarter.startup()` (`starter.py:131`) — stable lifecycle boundary.

---

### DC-005: No hardcoded values in configuration

| Field | Value |
|-------|-------|
| **ID** | DC-005 |
| **Original Type** | SPEC-DEVIATION |
| **Validated Type** | SPEC-DEVIATION (confirmed — no action needed) |
| **Severity** | LOW |
| **Classification** | advisory |

**Verdict:** VALIDATED. All sensitive values default to `None` or use environment variable references. Docker Compose required-var syntax (`:${VAR:?}`) enforces this at container startup. No hardcoded secrets exist.

---

### DC-006: Dependency check on startup

| Field | Value |
|-------|-------|
| **ID** | DC-006 |
| **Original Type** | SPEC-DEVIATION |
| **Validated Type** | SPEC-DEVIATION (confirmed — implementation is correct) |
| **Severity** | LOW |
| **Classification** | advisory |

**Verdict:** VALIDATED. `check_dependencies()` at `main.py:28-47` correctly imports all 14 required modules and calls `SystemExit(1)` on missing dependencies. This prevents cryptic import errors later. No changes needed.

---

### DC-007: Database connectivity verified before accepting requests

| Field | Value |
|-------|-------|
| **ID** | DC-007 |
| **Original Type** | SPEC-DEVIATION |
| **Validated Type** | SPEC-DEVIATION (confirmed — mandatory control is implemented) |
| **Severity** | MEDIUM |
| **Classification** | mandatory |

**Verdict:** VALIDATED. `_check_db_connection()` at `starter.py:75-111` implements timeout (10s), retry (5 attempts with exponential backoff), and proper error classification (`DatabaseNotFoundError`). This is a critical startup safety control, correctly implemented.

---

### DC-008: Schema existence verified on startup

| Field | Value |
|-------|-------|
| **ID** | DC-008 |
| **Original Type** | SPEC-DEVIATION |
| **Validated Type** | SPEC-DEVIATION (confirmed — mandatory control is implemented) |
| **Severity** | MEDIUM |
| **Classification** | mandatory |

**Verdict:** VALIDATED. `_get_alembic_revision()` at `starter.py:112-130` correctly queries `alembic_version` and raises `SchemaNotFoundError` if no revision is found (`starter.py:155-160`). This prevents the app from starting against an uninitialized database.

---

### DC-009: Migrations run automatically when configured

| Field | Value |
|-------|-------|
| **ID** | DC-009 |
| **Original Type** | SPEC-DEVIATION |
| **Validated Type** | SPEC-DEVIATION (confirmed — feature works correctly) |
| **Severity** | LOW |
| **Classification** | advisory |

**Verdict:** VALIDATED. Auto-migrate via `starter.py:152-153` and Docker Compose migrate service (`docker-compose.yml:40-65`) both work correctly. The dedicated migrate service pattern ensures schema is ready before app starts.

**Cross-reference:** INF-003 (Phase 05) notes migration strategy is Docker Compose-only and lacks Kubernetes/ECS documentation. Complementary, not conflicting.

---

### DC-010: Admin user creation is idempotent

| Field | Value |
|-------|-------|
| **ID** | DC-010 |
| **Original Type** | SPEC-DEVIATION |
| **Validated Type** | SPEC-DEVIATION (confirmed — correct implementation) |
| **Severity** | LOW |
| **Classification** | advisory |

**Verdict:** VALIDATED. `ensure_admin_user()` at `starter.py:300-334` uses `INSERT ... ON CONFLICT (email) DO NOTHING` with proper UUID generation and password hashing. Race-condition safe.

---

### DC-011: Stale temp files cleaned on startup

| Field | Value |
|-------|-------|
| **ID** | DC-011 |
| **Original Type** | SPEC-DEVIATION |
| **Validated Type** | SPEC-DEVIATION (confirmed — correct implementation) |
| **Severity** | LOW |
| **Classification** | advisory |

**Verdict:** VALIDATED. `cleanup_stale_temp_files()` at `starter.py:166-169` calls the service at `file_cleanup.py:39-96` which correctly deletes files older than the configured threshold. No issues.

---

### DC-012: Test database recreated when configured

| Field | Value |
|-------|-------|
| **ID** | DC-012 |
| **Original Type** | SPEC-DEVIATION |
| **Validated Type** | SPEC-DEVIATION (confirmed — correct implementation) |
| **Severity** | LOW |
| **Classification** | advisory |

**Verdict:** VALIDATED. `recreate_test_database()` at `starter.py:180-275` correctly drops and recreates the test database with proper privilege grants. The compose test environment (`docker-compose.test.yml:78-116`) uses `RECREATE_TEST_DB: "true"`.

---

### DC-013: Production debug mode disabled

| Field | Value |
|-------|-------|
| **ID** | DC-013 |
| **Original Type** | SPEC-DEVIATION |
| **Validated Type** | SPEC-DEVIATION (confirmed — mandatory control is implemented) |
| **Severity** | MEDIUM |
| **Classification** | mandatory |

**Verdict:** VALIDATED. `app.py:144-147` correctly sets `debug=config.debug` (defaults to `False`), `docs_url=None` and `redoc_url=None` when `environment == PRODUCTION`. This is a mandatory security control, correctly implemented.

---

### DC-014: Logging level appropriate for production

| Field | Value |
|-------|-------|
| **ID** | DC-014 |
| **Original Type** | SPEC-DEVIATION |
| **Validated Type** | SPEC-DEVIATION (confirmed — correct implementation) |
| **Severity** | LOW |
| **Classification** | advisory |

**Verdict:** VALIDATED. Production YAML config (`app.yaml:53-57`) sets JSON logging with INFO level. `setup_logging()` at `logging_config.py:72-187` correctly configures hierarchical loggers for all `mkobi.*` subpackages, with console + optional rotating file handler.

**Cross-reference:** BE-013 (Phase 01) covers the same logging implementation. **Cross-phase overlap** — both confirm correct structured logging.

---

### DC-015: Production credentials enforced in Docker

| Field | Value |
|-------|-------|
| **ID** | DC-015 |
| **Original Type** | SPEC-DEVIATION |
| **Validated Type** | SPEC-DEVIATION (confirmed — mandatory control is implemented) |
| **Severity** | LOW |
| **Classification** | advisory |

**Verdict:** VALIDATED. Docker Compose production service (`docker-compose.yml:84-95`) uses `${VAR:?error}` required-variable syntax for all sensitive environment variables. This prevents containers from starting without proper credentials.

**Cross-reference:** INF-004 (Phase 05) notes the development `.env` file has weak defaults (complementary — production is correct, development hygiene could improve).

---

### DC-016: CORS origins validated in production

| Field | Value |
|-------|-------|
| **ID** | DC-016 |
| **Original Type** | SPEC-DEVIATION |
| **Validated Type** | SPEC-DEVIATION (confirmed — mandatory control is implemented) |
| **Severity** | MEDIUM |
| **Classification** | mandatory |

**Verdict:** VALIDATED. `app.py:126-138` correctly validates: (1) `cors_origins` is not empty, (2) `"*"` is rejected in production with clear error messages. This is a mandatory security control.

**Cross-reference:** BE-007 (Phase 01) covers the same CORS validation. **Cross-phase overlap** — both confirm the same mandatory control exists.

---

### DC-017: Graceful shutdown with resource cleanup

| Field | Value |
|-------|-------|
| **ID** | DC-017 |
| **Original Type** | SPEC-DEVIATION |
| **Validated Type** | SPEC-DEVIATION (confirmed — correct implementation) |
| **Severity** | MEDIUM |
| **Classification** | mandatory |

**Verdict:** VALIDATED. The lifespan `finally` block (`app.py:93-105`) correctly: (1) cancels the background cleanup task, (2) awaits task cancellation with `CancelledError` handling, (3) calls `starter.shutdown()` to dispose database engines (`starter.py:357-362`). Clean shutdown sequence.

---

### DC-018: Background task termination on shutdown

| Field | Value |
|-------|-------|
| **ID** | DC-018 |
| **Original Type** | SPEC-DEVIATION |
| **Validated Type** | SPEC-DEVIATION (confirmed — correct implementation) |
| **Severity** | MEDIUM |
| **Classification** | mandatory |

**Verdict:** VALIDATED. `app.py:96-103` correctly cancels the cleanup task, handles `asyncio.CancelledError`, and logs the cancellation. The background task at `data_worker.py:485-508` uses `while True` with `asyncio.sleep()` which is properly cancellable.

**Note:** DC-017 and DC-018 describe the same shutdown sequence from slightly different angles. **Merge candidate** — both cover the shutdown `finally` block. However, they emphasize different aspects (overall resource cleanup vs. async task cancellation). They are complementary, not duplicative. No merge needed.

---

### DC-019: Advisory lock for concurrent migrations

| Field | Value |
|-------|-------|
| **ID** | DC-019 |
| **Original Type** | SPEC-DEVIATION |
| **Validated Type** | SPEC-DEVIATION (confirmed — correct implementation) |
| **Severity** | MEDIUM |
| **Classification** | mandatory |

**Verdict:** VALIDATED. `alembic/env.py:110-135` correctly acquires PostgreSQL advisory lock (`pg_advisory_lock(42)`) before migrations and releases it (`pg_advisory_unlock(42)`) in a `finally` block, even on errors. This prevents concurrent schema modifications in multi-instance deployments.

---

### DC-020: Dedicated application database role

| Field | Value |
|-------|-------|
| **ID** | DC-020 |
| **Original Type** | SPEC-DEVIATION |
| **Validated Type** | SPEC-DEVIATION (confirmed — correct implementation) |
| **Severity** | LOW |
| **Classification** | advisory |

**Verdict:** VALIDATED. The `mkobi_app` role is created by `docker/init-scripts/01-create-app-role.sh` with least-privilege grants (CONNECT, SELECT/INSERT/UPDATE/DELETE, USAGE on sequences, plus CREATEDB for test DB). Production app connects as `mkobi_app` (`docker-compose.yml:84`), while admin operations use the `postgres` superuser.

---

## Cross-Phase Conflicts

**No conflicts detected.** Overlapping findings across phases consistently confirm the same correct implementation from different audit angles.

| DC Finding | Overlapping Finding(s) | Relationship |
|------------|----------------------|--------------|
| DC-002 | BE-014 (Phase 01) | Overlap — both confirm correct secret management |
| DC-003 | BE-005 (Phase 01) | Overlap — both confirm weak credential validation |
| DC-014 | BE-013 (Phase 01) | Overlap — both confirm correct structured logging |
| DC-016 | BE-007 (Phase 01) | Overlap — both confirm CORS production validation |
| DC-009 | INF-003 (Phase 05) | Complementary — DC says it works, INF says docs incomplete |
| DC-015 | INF-004 (Phase 05) | Complementary — DC confirms production enforcement, INF notes dev defaults |

---

## Cross-Phase Dependency Validation

**Phase 08 internal dependency graph:**

```
DC-006 (dependency check)
    ↓
DC-007 (DB connectivity) ──depends──→ DC-008 (schema check)
                                          ↓
DC-009 (auto-migrate) ──depends──→ DC-008 (schema must exist first)
                                          ↓
                                    DC-010 (admin user)
                                    DC-011 (temp cleanup)
                                    DC-012 (test DB)

DC-003 (credential validation) ──must run before──→ DC-010 (admin user creation)

DC-017/018 (shutdown) ──cleanup of──→ DC-011/019 startup resources
```

**Analysis:** The startup sequence in `DatabaseStarter.startup()` correctly orders these operations:
1. Check DB connectivity (DC-007)
2. Apply migrations if configured (DC-009)
3. Verify schema exists (DC-008)
4. Ensure admin user (DC-010)
5. Clean temp files (DC-011)
6. Test DB (DC-012)
7. Start background tasks (DC-018)

**DAG validity:** ✅ Valid. No circular dependencies. Correct topological ordering.
**Semantic anchor stability:** ✅ All anchors are lifecycle boundaries (startup/shutdown), module-level classes, or function definitions — stable targets.
**Rollback feasibility:** ✅ All startup operations are either read-only checks or idempotent writes. No unsafe migration paths within this phase.

**Inter-phase dependencies:** None that create circular chains. Phase 08 depends on Phase 01 (backend architecture) and Phase 05 (infrastructure) for context, but does not create backward dependencies.

---

## Rollout Safety Analysis

| Finding | Risk Level | Rollback Feasibility | Coupling |
|---------|-----------|---------------------|----------|
| DC-001 | None (no code change) | N/A | Module-level docs |
| DC-002 | None | N/A | Already correct |
| DC-003 | None | N/A | Already correct |
| DC-004 | Very Low | Revert config check | Isolated to config module |
| DC-005–DC-020 | None | N/A | Already correct |

**Safe parallel execution:** All 20 findings are either already correct implementations or doc-only suggestions. No inter-finding execution ordering required.

---

## Reclassified Findings

### DC-004: Reclassified from SPEC-DEVIATION to BEST-PRACTICE

| Field | Value |
|-------|-------|
| **ID** | DC-004 |
| **Original Type** | SPEC-DEVIATION |
| **Reclassified Type** | BEST-PRACTICE |
| **Rationale** | The actionable recommendation (add explicit database URL validation) is a defensive programming improvement, not a deviation from spec. The rest of the finding describes existing correct validation. |

All other findings retain their `SPEC-DEVIATION` type label but are confirmed as **positive deviations** — the system correctly exceeds or matches the specification.

---

## Mandatory Fixes

### Already-Correct Mandatory Controls (No Action Required)

The following findings were classified as "mandatory" in the source audit. All describe security and reliability controls that are **already correctly implemented**:

| Finding | Description | Status |
|---------|-------------|--------|
| DC-003 | Production refuses insecure defaults for admin credentials | ✅ Implemented — tested at `test_config.py:316-349` |
| DC-007 | Database connectivity verified with retry logic | ✅ Implemented — `starter.py:75-111` |
| DC-008 | Schema existence verified on startup | ✅ Implemented — `starter.py:112-160` |
| DC-013 | Production debug mode disabled | ✅ Implemented — `app.py:144-147` |
| DC-016 | CORS origins validated in production | ✅ Implemented — `app.py:126-138` |
| DC-017 | Graceful shutdown with resource cleanup | ✅ Implemented — `app.py:93-105` |
| DC-018 | Background task termination on shutdown | ✅ Implemented — `app.py:96-103` |
| DC-019 | Advisory lock for concurrent migrations | ✅ Implemented — `alembic/env.py:110-135` |

**None of these require code changes.** They represent the mandatory baseline that the system already meets.

### New Mandatory Items from Validation

**None.** No new mandatory fixes were identified by the validation. All mandatory controls are present and correct.

---

## Advisory Recommendations

### From Source Audit (validated)

| ID | Recommendation | Priority |
|----|---------------|----------|
| DC-001 | Document configuration priority order in module docstring | LOW |
| DC-004 | Add explicit database URL presence validation to prevent unclear downstream errors | LOW |

**Note:** The original audit classified 13 findings as advisory, but 11 of those describe already-correct behavior with no actionable recommendation (their recommendation is "no changes needed"). Only DC-001 and DC-004 provide actionable advisory improvements.

---

## Doc Updates Needed

| Source | Description | Affected File |
|--------|-------------|---------------|
| DC-001 | Document configuration priority order (env > Docker secrets > .env > YAML > defaults) in `config.py` module docstring | `src/mkobi/config.py` |
| DC-004 | Consider documenting why database URL defaults to None and when it is validated | `src/mkobi/config.py` or docs |

---

## Rejected Findings

**None rejected.** All 20 findings describe real, verified behaviors in the codebase. None are stale, duplicate, or incorrect.

However, the audit's framing is misleading: Phase 08 findings read as a checklist of security/lifecycle controls rather than audit findings of problems. The audit confirms the system is well-architected in this domain.

---

## Architectural Consistency Warnings

**None.** The configuration and lifecycle domain is architecturally sound. All Clean Architecture boundaries are respected. The startup/shutdown sequence is correctly ordered. Security controls operate at the right layers.

**Positive observations:**
- Startup sequence correctly fails fast with clear error messages (credential validation, DB connectivity, schema check)
- Shutdown sequence is clean and covers all resources (DB engine disposal, background task cancellation, cancellation error handling)
- Separation of concerns: config (`config.py`), lifecycle (`starter.py`), app factory (`app.py`), entry point (`main.py`)
- No architecture drift detected. All patterns match AGENTS.md and project rules.
