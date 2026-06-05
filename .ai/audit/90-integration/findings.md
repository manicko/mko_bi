# Phase 09 Audit Findings — Integration

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### INT-001: ProcessingResult type mismatch between frontend and backend

| Field | Value |
|-------|-------|
| **ID** | INT-001 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/models/data.py`, `frontend/src/shared/types/api.types.ts` |
| **Classification** | mandatory |

**Description:** Frontend `ProcessingResult` interface expects `status: ProcessingStatus` field, but backend `ProcessingResult` model includes `success: bool` and `data: ProcessingResultData | None` fields that are not defined in the frontend type. The frontend type is missing critical fields that the backend returns, causing runtime errors when the frontend tries to access `status` on a response that doesn't have it or vice versa.

**Evidence:**
- Backend model (`src/mkobi/models/data.py:155-177`):
  ```python
  class ProcessingResult(BaseModel):
      success: bool
      task_id: UUID
      dashboard_id: UUID
      rows_processed: int
      message: str
      data: ProcessingResultData | None = None
  ```
- Frontend type (`frontend/src/shared/api/api.types.ts:200-204`):
  ```typescript
  export interface ProcessingResult {
    rows_processed: number
    status: ProcessingStatus
    message?: string
  }
  ```

**Recommendation:** Update frontend `ProcessingResult` interface to match backend model fields: `success`, `task_id`, `dashboard_id`, `rows_processed`, `message`, and `data`. Alternatively, if the frontend needs a `status` field, the backend should be updated to provide it consistently.

---

### INT-002: UploadResponse status field type mismatch

| Field | Value |
|-------|-------|
| **ID** | INT-002 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/models/data.py`, `frontend/src/shared/types/api.types.ts` |
| **Classification** | mandatory |

**Description:** Frontend `UploadResponse` interface defines `status: string` as a generic string type, but backend model uses `ProcessingStatus` enum. While this may work due to serialization, it bypasses type safety and could lead to runtime errors if invalid status values are used.

**Evidence:**
- Backend model (`src/mkobi/models/data.py:59-81`):
  ```python
  class UploadResponse(BaseModel):
      task_id: UUID
      filename: str
      dashboard_id: UUID
      status: ProcessingStatus  # Enum type
      message: str
      uploaded_at: datetime
  ```
- Frontend type (`frontend/src/shared/api/api.types.ts:83-90`):
  ```typescript
  export interface UploadResponse {
    task_id: string
    filename: string
    dashboard_id: string
    status: string  # Should be ProcessingStatus enum
    message: string
    uploaded_at: string
  }
  ```

**Recommendation:** Change frontend `status` field to use `ProcessingStatus` type instead of `string` to maintain type alignment with backend.

---

### INT-003: ProcessingLogRead status field type inconsistency in enum

| Field | Value |
|-------|-------|
| **ID** | INT-003 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/models/processing_logs.py`, `frontend/src/shared/types/enums.ts`, `alembic/versions/000000000000_initial_migration.py` |
| **Classification** | mandatory |

**Description:** The `ProcessingStatus` enum in the backend (`ProcessingStatus.py:58-65`) defines values: `STARTED`, `UPLOADED`, `PROCESSING`, `COMPLETED`, `FAILED`. However, the database migration (`alembic/versions/000000000000_initial_migration.py:38-47`) includes both `"success"` and `"completed"` in the enum, while frontend (`frontend/src/shared/types/enums.ts`) has a deprecated `SUCCESS` alias that maps to `"completed"`. This creates confusion but may work - however, the frontend `ProcessingLog` interface expects `started_at: string | null` while backend `ProcessingLogRead` has `started_at: datetime | None` which serializes correctly.

**Evidence:**
- Migration enum values (`alembic/versions/000000000000_initial_migration.py:38-47`):
  ```python
  processing_status_enum = ENUM(
      "started",
      "uploaded",
      "processing",
      "success",      # Not in backend ProcessingStatus enum
      "failed",
      "completed",    # Backend has COMPLETED
      name="processing_status",
  )
  ```
- Backend enum (`src/mkobi/models/enums.py:58-65`): No `SUCCESS` value, has `COMPLETED` instead.

**Recommendation:** Remove `"success"` from database migration or ensure all layers consistently use the same enum values. The frontend should remove the deprecated `SUCCESS` alias or align it properly.

---

### INT-004: RegistrationRequestItem status field type mismatch

| Field | Value |
|-------|-------|
| **ID** | INT-004 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `src/mkobi/models/auth.py`, `frontend/src/shared/types/api.types.ts` |
| **Classification** | mandatory |

**Description:** Frontend `RegistrationRequestItem` interface expects `status: RegistrationStatus` (typed enum), but backend model uses `status: str` (untyped string). This breaks type safety at the contract boundary.

**Evidence:**
- Backend model (`src/mkobi/models/auth.py:61-85`):
  ```python
  class RegistrationRequestItem(BaseModel):
      id: UUID
      email: EmailStr
      status: str  # Should be RegistrationStatus enum
      ...
  ```
- Frontend type (`frontend/src/shared/api/api.types.ts:225-233`):
  ```typescript
  export interface RegistrationRequestItem {
    id: string
    email: string
    status: RegistrationStatus  # Enum type
    ...
  }
  ```

**Recommendation:** Change backend `RegistrationRequestItem.status` to use `RegistrationStatus` enum type for proper type alignment.

---

### INT-005: Frontend error handler has Russian fallback message in English codebase

| Field | Value |
|-------|-------|
| **ID** | INT-005 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/shared/api/errorHandler.ts` |
| **Classification** | advisory |

**Description:** The frontend error handler (`errorHandler.ts:97-101`) returns a Russian fallback message `'Произошла ошибка'` when it cannot extract an error, but the codebase convention (per AGENTS.md) requires all comments, logs, and errors to be in English.

**Evidence:**
- `frontend/src/shared/api/errorHandler.ts:97-101`:
  ```typescript
  // Generic fallback with Russian message as specified
  return {
    code: ErrorCode.INTERNAL_ERROR,
    message: 'Произошла ошибка',
  }
  ```

**Recommendation:** Change the fallback message to English `'An error occurred'` or `'Something went wrong'` to comply with the project's language convention.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 3 |
| LOW | 1 |

## Mandatory Fixes

- INT-001: ProcessingResult type mismatch between frontend and backend
- INT-002: UploadResponse status field type mismatch
- INT-003: ProcessingLogRead status field type inconsistency in enum
- INT-004: RegistrationRequestItem status field type mismatch

## Advisory Recommendations

- INT-005: Frontend error handler has Russian fallback message in English codebase

---