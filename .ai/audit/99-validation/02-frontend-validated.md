---
name: 02-frontend-validated
description: Validated frontend audit findings
agent: validator
alwaysApply: false
problems-only: true
---

# Phase 02 Validation Report — Frontend Architecture

**Validator:** validator
**Source:** .ai/audit/02-frontend/findings.md
**Findings reviewed:** 7

---

## Merged Findings

### FE-001 + INT-005 — Russian Fallback Message in errorHandler.ts

| Field | Value |
|-------|-------|
| **IDs** | FE-002-phase: FE-001, INT-phase: INT-005 |
| **Merged ID** | FE-001 (primary — first discovery) |
| **Type** | BEST-PRACTICE |
| **Classification** | advisory |

**Rationale:** Both FE-001 (Phase 02 — Frontend) and INT-005 (Phase 90 — Integration) identify the same root cause: the Russian fallback message `'Произошла ошибка'` in `frontend/src/shared/api/errorHandler.ts:100`. The evidence, affected module, and recommendation are identical. FE-001 is the primary finding (discovered first in the audit sequence). INT-005 should be considered a duplicate and merged into FE-001.

**Resolution:** Retain FE-001 as the sole finding. INT-005 should be marked as duplicate in the integration phase validation.

---

## Reclassified Findings

### FE-002 — Russian Language in Shared Error Messages

| Field | Value |
|-------|-------|
| **ID** | FE-002 |
| **Original Type** | BEST-PRACTICE |
| **Reclassified Type** | DOC-UPDATE |
| **Classification** | advisory |

**Rationale:** The `errorMessages.ts` file is explicitly designed as a user-facing localization layer. Its own JSDoc states "User-facing Russian error message" and the resolution order in `getErrorMessage()` is: feature map → shared map → error.detail → default Russian message. The error *codes* (ErrorCode enum) are in English. The *user-facing display strings* are intentionally Russian — this is a localization design choice, not an accidental violation.

However, the AGENTS.md rule states "All comments, logs, docstrings, error messages — only English." If the project intends to support only Russian-speaking users, the current design is functional but should be documented as an explicit architectural decision. If the project intends to be multilingual, a proper i18n system should replace this approach.

**Reclassification reasoning:** The code is working as designed. The issue is that the design decision (Russian user-facing messages) is not documented. This should be a DOC-UPDATE to either: (a) document Russian as the supported locale with English error codes, or (b) plan migration to a proper i18n framework.

---

## Rejected Findings

### FE-007 — Missing Form Field Labels for Accessibility

| Field | Value |
|-------|-------|
| **ID** | FE-007 |
| **Type** | BEST-PRACTICE |
| **Classification** | advisory → REJECTED |

**Rejection reason:** MUI `TextField` component internally renders a `<label htmlFor>` association via its `InputLabel` sub-component. When `label="Email"` is passed to `TextField`, MUI generates:
```html
<label id="mui-1" for="mui-2">Email</label>
<input id="mui-2" aria-invalid="false" ... />
```
The label-input association is handled automatically by MUI's FormControl context. The finding's claim that "explicit `htmlFor` label associations are required" is incorrect for MUI TextField — the association exists implicitly through MUI's internal implementation.

Adding `aria-label` would be redundant and could cause screen readers to announce duplicate labels. The current implementation follows MUI's recommended pattern for accessible forms.

**Evidence:** MUI TextField source generates `InputLabel` + `Input` with automatic `htmlFor`/`id` binding via `FormControlContext`. No accessibility violation exists.

---

## Validated Counts

| Category | Count |
|----------|-------|
| Total findings reviewed | 7 |
| Merged (FE-001 + INT-005) | 1 merge pair |
| Reclassified (FE-002) | 1 |
| Rejected (FE-007) | 1 |
| Validated unchanged | 4 (FE-003, FE-004, FE-005, FE-006) |

### Mandatory Fixes (validated)
- FE-003: Lint errors in ChartRenderer component — 4 lint errors confirmed by `npm run lint` output
- FE-005: Hardcoded status strings in uploadApi.ts — `'completed'`/`'failed'` should use `ProcessingStatus.COMPLETED`/`ProcessingStatus.FAILED`

### Advisory Recommendations (validated)
- FE-001: Russian fallback message in errorHandler.ts (merged with INT-005)
- FE-004: Unused chart components (BarChart, LineChart, PieChart, TableChart) — zero imports confirmed
- FE-006: `any` type in PlotlyComponent.tsx — CJS/ESM interop shim, documented suppression

### Reclassified
- FE-002: BEST-PRACTICE → DOC-UPDATE (Russian error messages are intentional localization layer)

### Rejected
- FE-007: MUI TextField provides internal label association; no accessibility violation

---

## Cross-Phase Conflicts

| Conflict | Finding IDs | Resolution |
|----------|-------------|------------|
| Same root cause: Russian fallback in errorHandler.ts | FE-001 (Phase 02), INT-005 (Phase 90) | Merge into FE-001; INT-005 is duplicate |

No other cross-phase conflicts detected for Phase 02 findings.

---

## Rollout Safety Notes

- **FE-003** (ChartRenderer lint fixes) and **FE-005** (uploadApi enum) are independent, low-risk changes that can be executed in parallel. No dependency between them.
- **FE-001** (errorHandler Russian → English) is a single-line string change with zero architectural impact.
- **FE-004** (removing unused chart components) is safe to defer — dead code has no runtime impact. Removal can be done at any time without dependency on other findings.
- **FE-006** (PlotlyComponent `any` type) requires investigation of alternative typing approaches. Not urgent — the current eslint-disable is contained and documented. Changing to `unknown` with type guards adds complexity with minimal practical benefit for a stable CJS/ESM shim.
- No circular dependencies or unsafe rollout sequences detected among validated findings.
