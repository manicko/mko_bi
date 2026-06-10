# Phase 09 Audit Findings — Integration

**Executor:** auditor  
**Template:** .ai/audit/templates/audit-findings.md  
**Status:** complete

---

## Findings

### INT-001: Backend Uses `str` for Registration Status Instead of Enum

| Field | Value |
|-------|-------|
| **ID** | INT-001 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | src/mkobi/models/auth.py, frontend/src/shared/types/api.types.ts |
| **Classification** | advisory |

**Description:** The backend `RegistrationRequestResponse` and `RegistrationRequestItem` models use `status: str` instead of `RegistrationStatus` enum, even though `RegistrationStatus` enum exists in the codebase. This is inconsistent with other models that use proper enums for status fields (e.g., `ProcessingStatus` in `ProcessingLogRead`). The frontend correctly uses `RegistrationStatus` enum type, creating a mismatch where frontend expects a validated enum value but receives a raw string from the backend.

**Evidence:**
- Backend: `src/mkobi/models/auth.py:47` — `status: str` in `RegistrationRequestResponse`
- Backend: `src/mkobi/models/auth.py:66` — `status: str` in `RegistrationRequestItem`
- Frontend: `frontend/src/shared/types/api.types.ts:238` — `status: RegistrationStatus` (expects enum)
- Backend: `src/mkobi/models/processing_logs.py:12` — Uses proper `ProcessingStatus` enum in `ProcessingLogFilter`

**Recommendation:** Update backend models to use `RegistrationStatus` enum for type safety:
```python
class RegistrationRequestResponse(BaseModel):
    status: RegistrationStatus  # Instead of str
```

---

### INT-002: Missing `INVALID_TRANSITION` ErrorCode in Frontend

| Field | Value |
|-------|-------|
| **ID** | INT-002 |
| **Severity** | MEDIUM |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | frontend/src/shared/types/enums.ts, src/mkobi/models/enums.py |
| **Classification** | advisory |

**Description:** The backend `ErrorCode` enum includes `INVALID_TRANSITION = "invalid_transition"` (line 240 in enums.py) but the frontend `ErrorCode` enum (frontend/src/shared/types/enums.ts:119) does not include this value. This creates a gap where frontend error handling cannot properly process this error code - it will fall through to the generic `INTERNAL_ERROR` handler.

**Evidence:**
- Backend: `src/mkobi/models/enums.py:240` — `INVALID_TRANSITION = "invalid_transition"`
- Frontend: `frontend/src/shared/types/enums.ts:119` — Enum ends with `PROCESSING_IN_PROGRESS`, missing `INVALID_TRANSITION`

**Recommendation:** Add `INVALID_TRANSITION` to frontend ErrorCode enum to match backend:
```typescript
export const ErrorCode = {
  // ... existing codes ...
  PROCESSING_IN_PROGRESS: 'PROCESSING_IN_PROGRESS',
  INVALID_TRANSITION: 'INVALID_TRANSITION',
} as const
```

---

### INT-003: Frontend `status_filter` Uses Generic String Instead of Enum

| Field | Value |
|-------|-------|
| **ID** | INT-003 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | frontend/src/shared/types/api.types.ts, src/mkobi/models/processing_logs.py |
| **Classification** | advisory |

**Description:** The frontend `LogFilters` interface declares `status_filter?: string` (line 296) but the backend endpoint expects `ProcessingStatus` enum value (processing_logs.py:43). While FastAPI can parse string values to StrEnum, this loses type safety on the frontend. The frontend should use `ProcessingStatus` enum to match backend expectations and enable compile-time validation.

**Evidence:**
- Frontend: `frontend/src/shared/types/api.types.ts:296` — `status_filter?: string`
- Backend: `src/mkobi/models/processing_logs.py:43` — `status_filter: ProcessingStatus | None = Query(None, ...)`
- ProcessingStatus enum already imported: line 1 of api.types.ts

**Recommendation:** Change to `status_filter?: ProcessingStatus` for type safety consistency.

---

### INT-004: Frontend `ProcessingLog.finished_at` Optional vs Backend Required

| Field | Value |
|-------|-------|
| **ID** | INT-004 |
| **Severity** | LOW |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | frontend/src/shared/types/api.types.ts, src/mkobi/models/processing_logs.py |
| **Classification** | advisory |

**Description:** The frontend `ProcessingLog` interface marks `finished_at` as optional (`?: string`) but the backend `ProcessingLogRead` model defines it as `datetime | None = None`. While this serializes to ISO string in JSON and both handle null/undefined, the type definitions are semantically different. The backend always returns the field (possibly null), while the frontend allows the field to be entirely missing.

**Evidence:**
- Frontend: `frontend/src/shared/types/api.types.ts:291` — `finished_at?: string` (missing field entirely)
- Backend: `src/mkobi/models/processing_logs.py:81` — `finished_at: datetime | None = None` (field present, nullable)
- Frontend `started_at: string | null` (line 290) is correctly aligned with backend

**Recommendation:** Change to `finished_at: string | null` for explicit null handling, or verify that the current behavior works correctly.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 2 |
| LOW | 2 |

## Advisory Recommendations

| ID | Title | Priority |
|----|-------|----------|
| INT-001 | Backend registration models use `str` instead of `RegistrationStatus` enum | recommended |
| INT-002 | Missing `INVALID_TRANSITION` ErrorCode in frontend | recommended |
| INT-003 | Frontend `LogFilters.status_filter` uses generic string instead of `ProcessingStatus` enum | recommended |
| INT-004 | Frontend `ProcessingLog.finished_at` optional vs backend required | recommended |

---

## Verified Alignments (No Issues)

The following were checked and found to be correctly aligned:

- **UserProfile**: Has `force_password_change: boolean` and `display_name: string` (lines 40-47 in api.types.ts)
- **AdminUser**: Has `force_password_change: boolean` (lines 217-223 in api.types.ts)
- **RegistrationResponse**: Correctly matches backend return shape `{message, id}` (lines 152-155 in api.types.ts) matches backend `auth.py:589`
- **Auth flow**: `AuthResponse` includes `user: UserProfile` with correct field types
- **Token refresh**: `Token` interface matches `Token` model

---