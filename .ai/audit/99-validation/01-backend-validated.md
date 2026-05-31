---
name: 01-backend-validated
description: Backend Audit Validation Report
status: complete
phase: 01-backend
---

# Phase 01 Backend — Validation Report

**Validator:** validator agent  
**Source findings:** .ai/audit/01-backend/findings.md  
**Scope:** Backend Architecture (8 findings)  
**Mode:** problems-only

---

## Rejected Findings

### BE-002: Unnecessary Rate Limiter in Process endpoint
- **Original type:** BEST-PRACTICE
- **Original severity:** HIGH
- **Rejection reason (OVERENGINEERING / WRONG TARGET):** The `/upload/{dashboard_id}/process` endpoint (lines 220-271 in `upload.py`) does NOT apply rate limiting. The rate limiter at lines 122-138 is only applied in the `upload_file_endpoint` (the `POST /{dashboard_id}` endpoint). The finding incorrectly references the process endpoint when rate limiting is actually applied to the upload endpoint. The finding is based on a wrong premise.

### BE-006: DataService rate limiter initialized but never used
- **Original type:** BEST-PRACTICE
- **Original severity:** MEDIUM
- **Rejection reason (DUPLICATE OF BE-001):** This finding addresses the same `_upload_rate_limiter` field in `DataService.__init__` as BE-001. BE-001 identifies the critical issue (sync `RateLimiter` in async context); BE-006 only notes it's unused. Fixing BE-001 (replacing with `AsyncRateLimiter` or removing it) inherently resolves BE-006. Keeping both would produce redundant work and conflicting fix strategies. Superseded by BE-001.

### BE-007: Missing explicit transaction rollback on error in process_upload_with_session
- **Original type:** SPEC-DEVIATION
- **Original severity:** MEDIUM
- **Rejection reason (STALE / INACCURATE):** The finding claims there is "no explicit rollback" in `process_upload_with_session`. However, the function uses a caller-provided `AsyncSession` — the session lifecycle is managed by the caller (FastAPI dependency injection provides the session and handles cleanup). The function performs `db.flush()` before the file move and `db.commit()` after. If an error occurs after `file_path.replace()` (line 171), the file move is the side-effect that is not transactional — but this is a file system operation, not a database one. The file system state inconsistency is a real but very narrow edge case (file moved but DB commit failed would leave an orphan file). The DB session does not need explicit `rollback()` here — the caller's session management handles that. The finding is technically overstated.

---

## Merged Findings

### BE-001 + BE-006 → BE-001
- **BE-001:** Sync RateLimiter in async DataService breaks event loop (CRITICAL)
- **BE-006:** DataService rate limiter initialized but never used (MEDIUM)
- **Merge rationale:** Both findings target the same `_upload_rate_limiter` field in `data_service.py:54-71`. BE-001 correctly identifies the critical async violation. BE-006 only observes the rate limiter is unused — a lesser observation subsumed by the root cause. The fix for BE-001 (either replace with `AsyncRateLimiter` + async Redis client, or remove the unused rate limiter entirely) resolves both concerns simultaneously.
- **Retained as:** BE-001 (CRITICAL, SPEC-DEVIATION, mandatory)

---

## Reclassified Findings

### BE-008: Exception handlers in app.py don't use standard error format
- **Original type:** SPEC-DEVIATION
- **Reclassified type:** BEST-PRACTICE
- **Rationale:** The finding states that HTTP exception handlers lack the `error_code` field that `AppException` provides. Inspection confirms:
  - `app.py:250-256` — `StarletteHTTPException` handler returns `{detail, status_code}` — no `error_code`
  - `app.py:258-270` — `RequestValidationError` handler returns `{detail, errors, status_code}` — no `error_code`
  - `app.py:272-284` — `Pydantic ValidationError` handler returns `{detail, errors, status_code}` — no `error_code`
  
  Meanwhile, `utils/exceptions.py:102-109` shows `AppException` handler returns `{status_code, detail, error_code}` — BUT this handler is registered via `add_exception_handlers()` which is **never called** in `create_app()`. The `AppException` handler is dead code.
  
  This is not a SPEC-DEVIATION (the project spec does not mandate a uniform error format). It is a BEST-PRACTICE concern about API response consistency. Additionally, the custom `AppException` handler at `utils/exceptions.py` is registered but never wired in, which is itself a separate architectural integrity issue that the audit did not catch.

---

## Cross-Phase Conflicts

No cross-phase conflicts detected. Only Phase 01 (backend) audit findings exist.

---

## Rollout Safety Issues

### BE-001 and BE-003 have interaction risk
- **Finding pair:** BE-001 (RateLimiter fix) and BE-003 (ProcessingStatus enum consolidation)
- **Risk:** BE-001 recommends either replacing `RateLimiter` with `AsyncRateLimiter` or removing the dead code. Both options are safe isolation-wise. However, if the fix for BE-001 chooses removal (simpler), it also fixes BE-006 merged concern. These are independent of BE-003.
- **Recommendation:** Execute BE-003 (enum consolidation) independently. Execute BE-001 (rate limiter fix) independently. No ordering dependency.

### BE-005 requires graph repository changes that could conflict with dashboard-scoped graph endpoints
- **Finding:** BE-005 — Global graph endpoints lack dashboard access verification
- **Risk:** The fix requires adding `check_dashboard_access` to 3 endpoints in `graphs.py` (`GET /`, `GET /{graph_id}`, `PUT /{graph_id}`). The `POST /` endpoint already has `require_admin_role` but no dashboard access check (it receives `dashboard_id` in the request body). The existing `dashboards_graphs.py` uses `require_dashboard_read_access` which extracts `dashboard_id` from the path. For global graph endpoints, the `dashboard_id` is not in the path — it must be fetched from the graph record first. This adds a DB query before the access check. Semantic targets are stable (function definitions are unique).
- **Recommendation:** Rollout safe. Add a fetch-then-check pattern: fetch graph by ID, extract `dashboard_id`, then call `check_dashboard_access`.

---

## Validated Counts

| Category | Count |
|----------|-------|
| **Total findings** | 8 |
| **Rejected** | 3 (BE-002, BE-006, BE-007) |
| **Merged** | 1 pair (BE-006 into BE-001) |
| **Reclassified** | 1 (BE-008: SPEC-DEVIATION → BEST-PRACTICE) |
| **Validated as-is** | 5 (BE-001, BE-003, BE-004, BE-005, BE-008 reclassified) |
| **Mandatory fixes (post-validation)** | 2 (BE-001, BE-005) |
| **Advisory recommendations (post-validation)** | 3 (BE-003, BE-004, BE-008) |

### Mandatory fixes
- **BE-001:** Sync RateLimiter in async DataService breaks event loop — SPEC-DEVIATION
- **BE-005:** Global graph endpoints lack dashboard access verification — SPEC-DEVIATION

### Advisory recommendations
- **BE-003:** ProcessingStatus enum has redundant SUCCESS and COMPLETED values — SPEC-DEVIATION
- **BE-004:** In-memory TaskQueue not integrated with background workers — SPEC-DEVIATION
- **BE-008:** Exception handlers in app.py don't use standard error format — BEST-PRACTICE (reclassified)
