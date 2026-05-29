# Phase 09 Validated Findings — Integration

**Validator:** validator agent
**Source:** .ai/audit/90-integration/findings.md
**Status:** complete

---

## Rejected Findings

### INT-002: UploadResponse ID field naming inconsistency — REJECTED

**Rejection reason:** The finding's description is factually incorrect. The backend upload route (`upload.py:184-187`) returns `processing_log_id: result.task_id`, which **matches** the frontend `UploadResponse.processing_log_id` field. The frontend type (`api.types.ts:59-68`) actually has **both** `task_id` (line 60) and `processing_log_id` (line 67), so the route response maps correctly.

The real issue is that the frontend type redundantly declares both `task_id` and `processing_log_id` as separate fields when they represent the same value. This is a minor type redundancy, not a schema mismatch. The finding misidentifies the problem as a naming conflict where none exists at runtime.

**Corrective note:** If a future finding addresses this, it should target the redundant field declaration in the frontend type, not a "naming inconsistency."

---

## Reclassified Findings

### INT-004: Token refresh API response type naming — RECLASSIFIED

- **Original type:** SPEC-DEVIATION
- **New type:** DOC-UPDATE
- **Rationale:** The finding itself states "the implementation is correct but the type naming could be more descriptive." There is no schema mismatch, no runtime error, and no deviation from any specification. The `Token` type (`api.types.ts:34-37`) accurately describes the response shape `{access_token, token_type}`. Renaming it to `RefreshTokenResponse` is a cosmetic change with zero functional impact. This is not a spec deviation — it is a documentation/naming preference. Reclassified as DOC-UPDATE only if the team wants to improve type naming clarity in docs.

---

## Validated Findings (Passed — Not Restated)

The following findings passed validation unchanged. They are not restated per `problems-only: true` output mode:

- **INT-001** — ProcessingStatusResponse schema mismatch (SPEC-DEVIATION, advisory) — Confirmed: frontend missing `task_id`, `filename`, `dashboard_id`, `progress`; field name `finished_at` vs `completed_at`.
- **INT-003** — Frontend DashboardConfig incompatible with backend (SPEC-DEVIATION, mandatory) — Confirmed: fundamentally different structures causing UI rendering failures.
- **INT-005** — Concurrent 401 timeout handling (RUNTIME-ERROR, advisory) — Confirmed: functional but could be more robust; low priority.
- **INT-006** — AggregatedDataResponse shape mismatch (SPEC-DEVIATION, mandatory) — Confirmed: backend missing `type` and `name` fields; `graph.name` renders as undefined.
- **INT-007** — AccessGrant vs GrantAccessRequest field mismatch (SPEC-DEVIATION, mandatory) — Confirmed: `permission` vs `permission_level` causes 422 or silent default to "view".

---

## Cross-Phase Conflicts

**None.** No validated findings from phases 01-08 address the same API contract structures (DashboardConfig, ProcessingStatusResponse, AggregatedDataResponse, AccessGrant, UploadResponse). No conflicting recommendations detected.

---

## Rollout Safety Analysis

All validated findings (INT-001, INT-003, INT-005, INT-006, INT-007) are **independent** fixes targeting frontend type definitions or backend model/response shapes. There are no circular dependencies between findings.

**Safe execution order:**
1. Fix backend response shapes first (INT-006: add `type`/`name` to aggregated data response; INT-001: align field names)
2. Fix frontend types to match (INT-001, INT-003, INT-006, INT-007)
3. INT-005 (timeout handling) can be done at any time — it is purely additive

**Semantic targeting stability:** All anchors are stable — Pydantic model class definitions, TypeScript interface declarations, and FastAPI route return statements. None are line-number-dependent.

---

## Validated Counts

| Category | Count |
|----------|-------|
| **Mandatory fixes** | 3 (INT-003, INT-006, INT-007) |
| **Advisory recommendations** | 2 (INT-001, INT-005) |
| **Rejected** | 1 (INT-002) |
| **Reclassified** | 1 (INT-004: SPEC-DEVIATION → DOC-UPDATE) |
| **Cross-phase conflicts** | 0 |
