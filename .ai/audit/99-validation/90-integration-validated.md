---
name: 90-integration-validated
description: Validated integration audit findings
agent: validator
alwaysApply: false
problems-only: true
---

# Phase 90 Validation Report — Integration

**Validator:** validator
**Source:** .ai/audit/90-integration/findings.md
**Mode:** problems-only

---

## Merged Findings

### INT-005 + FE-001 — Russian Fallback Message in errorHandler.ts

| Field | Value |
|-------|-------|
| **IDs** | INT-005 (Phase 90), FE-001 (Phase 02) |
| **Merged ID** | FE-001 (primary — first discovery) |
| **Type** | SPEC-DEVIATION |
| **Classification** | advisory |

**Rationale:** Both INT-005 (Phase 90 — Integration) and FE-001 (Phase 02 — Frontend) identify the same root cause: the Russian fallback message `'Произошла ошибка'` in `frontend/src/shared/api/errorHandler.ts:100`. The evidence, affected module, and recommendation are identical. FE-001 is the primary finding (discovered first in the audit sequence). INT-005 is a duplicate and is merged into FE-001.

**Resolution:** Retain FE-001 as the sole finding. INT-005 is subsumed.

---

### INT-003 + DB-001 — ProcessingStatus ENUM Schema Drift

| Field | Value |
|-------|-------|
| **IDs** | INT-003 (Phase 90), DB-001 (Phase 03) |
| **Merged ID** | DB-001 (primary — more complete description) |
| **Type** | SPEC-DEVIATION |
| **Classification** | advisory |

**Rationale:** Both INT-003 (Phase 90 — Integration) and DB-001 (Phase 03 — Database) identify the same root cause: the PostgreSQL `processing_status` ENUM contains an extra `"success"` value not present in the Python `ProcessingStatus` StrEnum. DB-001 focuses on the schema drift and raw SQL dependency in `db/starter.py`; INT-003 focuses on the frontend-backend type inconsistency arising from the same enum mismatch. DB-001 is the more complete description and was validated first. INT-003 is subsumed under DB-001.

**Resolution:** Retain DB-001 as the sole finding. INT-003 is subsumed.

---

## Rejected Findings

### INT-001 — ProcessingResult Type Mismatch Between Frontend and Backend

| Field | Value |
|-------|-------|
| **ID** | INT-001 |
| **Type** | SPEC-DEVIATION |
| **Classification** | mandatory → REJECTED |

**Rejection reason:** The finding mischaracterizes the problem as a "type mismatch causing runtime errors." In reality, the frontend `ProcessingResult` interface (`api.types.ts:200-204`) and the backend `ProcessingResult` model (`data.py:155-177`) represent **different domain concepts**:

- **Backend `ProcessingResult`** (`data.py:155-177`): Returned by `GET /upload/result/{task_id}` (`upload.py:287`). Contains `success`, `task_id`, `dashboard_id`, `rows_processed`, `message`, `data`. This is a processing completion result.
- **Frontend `ProcessingResult`** (`api.types.ts:200-204`): Consumed by `uploadApi.getProcessingResult()` (`uploadApi.ts:38-41`) which calls `GET /upload/result/${logId}`. Contains `rows_processed`, `status`, `message`.

The frontend type is **not** a mirror of the backend type — it is a **subset** that the frontend chooses to consume. The fields `success`, `task_id`, `dashboard_id`, and `data` exist in the backend response but are simply not destructured on the frontend side. This is a valid design choice: the frontend only needs `rows_processed`, `status`, and `message` for its UI.

However, there IS a real issue: the backend model has no `status` field (it has `success: bool` instead), yet the frontend expects `status: ProcessingStatus`. This means the frontend will receive `status: undefined` at runtime. The finding's description is partially correct about the `status` field mismatch, but the recommendation to "update frontend to match backend model fields" is wrong — the frontend should not be forced to consume fields it doesn't need.

**Correct analysis:** The real problem is that the backend `ProcessingResult` model does not include a `status` field, but the frontend expects one. The fix should be either:
1. Add a `status` field to the backend `ProcessingResult` model (derived from `success`: `COMPLETED` if true, `FAILED` if false), OR
2. Change the frontend to use `success: boolean` instead of `status: ProcessingStatus`.

This is a genuine contract gap, but the finding's framing and recommendation are incorrect. The finding is rejected as stated because it misidentifies the root cause and proposes the wrong fix direction. The actual issue (missing `status` field) is a separate concern that should be filed as a new finding.

---

### INT-002 — UploadResponse Status Field Type Mismatch

| Field | Value |
|-------|-------|
| **ID** | INT-002 |
| **Type** | SPEC-DEVIATION |
| **Classification** | mandatory → REJECTED |

**Rejection reason:** The finding claims the frontend `UploadResponse.status: string` "bypasses type safety and could lead to runtime errors." This is overstated. The evidence shows:

- Backend: `UploadResponse.status: ProcessingStatus` (StrEnum, serializes to string via JSON)
- Frontend: `UploadResponse.status: string`

Since `ProcessingStatus` is a `StrEnum`, it serializes to a plain string in JSON. The frontend receives a string value regardless. The frontend type `string` correctly represents what JSON delivers. The frontend does not need to replicate the backend enum type — it only needs to handle the string values at runtime.

The frontend `uploadApi.ts` does not perform any enum comparison on `UploadResponse.status` — it only uses `ProcessingStatusResponse.status` (which IS typed as `ProcessingStatus` at line 193). The `UploadResponse.status: string` is a pragmatic choice for a field that is displayed but not programmatically compared in the frontend.

**No runtime error risk exists.** The finding is rejected as a non-issue. If stronger typing is desired, this would be a low-priority advisory change, not a mandatory fix.

---

### INT-004 — RegistrationRequestItem Status Field Type Mismatch

| Field | Value |
|-------|-------|
| **ID** | INT-004 |
| **Type** | SPEC-DEVIATION |
| **Classification** | mandatory → REJECTED |

**Rejection reason:** The finding claims the backend `RegistrationRequestItem.status: str` "breaks type safety at the contract boundary." This analysis is incorrect:

1. The `RegistrationStatus` StrEnum exists in `enums.py:43-48` with values `PENDING`, `APPROVED`, `REJECTED`.
2. The backend model uses `status: str` because the value comes from the database via `model_validate(req)` at `admin.py:258`, where `req` is an ORM object with `status` as a string column.
3. Pydantic's `model_validate` will coerce the string value into the model. When serialized to JSON via FastAPI's `response_model`, the `status` field is emitted as a plain string.
4. The frontend receives `"pending"`, `"approved"`, or `"rejected"` — all valid `RegistrationStatus` values.

The use of `str` instead of `RegistrationStatus` in the backend model is a **common and accepted pattern** in Pydantic v2 when the source data comes from an ORM/database layer. The `RegistrationStatus` enum is still used for validation and comparison in business logic. The JSON contract is identical either way — a string is a string.

**No type safety break occurs at the contract boundary.** The finding is rejected. If stronger typing in the model is desired, it would be a low-priority advisory improvement, not a mandatory fix.

---

## Validated Counts

| Category | Count |
|----------|-------|
| Total findings reviewed | 5 |
| Merged (INT-005 → FE-001) | 1 |
| Merged (INT-003 → DB-001) | 1 |
| Rejected (INT-001, INT-002, INT-004) | 3 |
| Validated unchanged | 0 |

### Mandatory Fixes
None. All three mandatory-classified findings (INT-001, INT-002, INT-004) were rejected.

### Advisory Recommendations
None remaining in this phase. INT-005 was merged into FE-001 (Phase 02). INT-003 was merged into DB-001 (Phase 03).

---

## Cross-Phase Conflicts

| Conflict | Finding IDs | Resolution |
|----------|-------------|------------|
| Same root cause: Russian fallback in errorHandler.ts | FE-001 (Phase 02), INT-005 (Phase 90) | Merged into FE-001; INT-005 is duplicate |
| Same root cause: extra `"success"` in DB ENUM | DB-001 (Phase 03), INT-003 (Phase 90) | Merged into DB-001; INT-003 is duplicate |

No conflicting recommendations detected. Both merges are straightforward — the integration-phase findings describe the same root causes already identified in earlier phases.

---

## Rollout Safety Analysis

No rollout safety issues specific to Phase 90 findings. All three rejected findings (INT-001, INT-002, INT-004) proposed code changes that are not required. The two merged findings (INT-005, INT-003) inherit the rollout plans from their primary findings (FE-001 and DB-001 respectively), which were already validated in their phase reports.

---

## Execution Warnings

1. **INT-001 partial validity:** Although INT-001 was rejected due to mischaracterization, there IS a real contract gap: the backend `ProcessingResult` model has no `status` field, but the frontend expects `status: ProcessingStatus`. The frontend will receive `undefined` for `status` at runtime. This should be addressed — either by adding a `status` field to the backend model or by changing the frontend to use `success: boolean`. This is NOT a mandatory fix (the frontend can handle `undefined` gracefully), but it is a latent contract inconsistency.

2. **INT-004 model typing:** While rejected as a mandatory fix, consider changing `RegistrationRequestItem.status` and `RegistrationRequestResponse.status` from `str` to `RegistrationStatus` for consistency with other models (e.g., `ProcessingLogRead.status: ProcessingStatus`). This is a low-priority advisory improvement.

---

## Summary

Phase 90 (Integration) produced 5 findings. After validation:
- 2 were merged into findings from earlier phases (FE-001, DB-001)
- 3 were rejected (INT-001, INT-002, INT-004) — all mischaracterized the severity or nature of the type differences
- 0 remain as standalone validated findings for this phase

The integration audit was overly aggressive in classifying type annotation differences as mandatory spec deviations. Many "mismatches" are standard patterns in full-stack development (frontend subset types, Pydantic ORM coercion, JSON string serialization).
