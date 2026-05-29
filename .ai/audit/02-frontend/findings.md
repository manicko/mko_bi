---
name: 02-frontend-audit
description: Frontend architecture audit findings
agent: audit-executor
alwaysApply: false
---

# Phase 02 Audit Findings — Frontend Architecture

**Executor:** audit-executor
**Template:** .ai/audit/templates/audit-findings.md
**Status:** complete
**Validated:** no

---

## Findings

### FE-001: Potential Circular Import Between Axios Instance and Auth API

| Field | Value |
|-------|-------|
| **ID** | FE-001 |
| **Severity** | HIGH |
| **Type** | SPEC-DEVIATION |
| **Affected Modules** | `frontend/src/shared/api/axiosInstance.ts`, `frontend/src/features/auth/api/authApi.ts`, `frontend/src/features/auth/model/authToken.ts` |
| **Classification** | mandatory |

**Description:** The axiosInstance response interceptor (line 4) imports `refreshToken` from authApi.ts, which in turn imports `axiosInstance` for its API calls. While this currently works because the axiosInstance object is created before authApi functions execute, this circular dependency is fragile and could cause issues during module initialization or hot-reloading in development.

**Evidence:** `frontend/src/shared/api/axiosInstance.ts` line 4: `import { refreshToken } from '../../features/auth/api/authApi'`. `frontend/src/features/auth/api/authApi.ts` line 1: `import { axiosInstance } from '../../../shared/api/axiosInstance'`.

**Recommendation:** Consider extracting the token refresh logic into a separate module that doesn't import the full axiosInstance, or restructure to use dependency injection to break the circular reference.

---

### FE-002: Stale Closure Risk in UploadModal Status Polling

| Field | Value |
|-------|-------|
| **ID** | FE-002 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/upload/ui/UploadModal.tsx` |
| **Classification** | advisory |

**Description:** The `queueMicrotask` usage in UploadModal's useEffect (line 56) defers state updates to avoid setState-in-effect issues, but creates complexity and potential for stale closures. The `onUploadComplete` callback is referenced inside the microtask but not included in the effect's dependency array (line 76), which could lead to stale closure issues if the callback reference changes.

**Evidence:** `frontend/src/features/upload/ui/UploadModal.tsx` lines 49-76. The effect uses `queueMicrotask` to defer state updates, and `onUploadComplete` is called at line 69-71 but not in the dependency array.

**Recommendation:** Remove `queueMicrotask` and handle state updates directly in the effect response, or add `onUploadComplete` to the dependency array. Consider using TanStack Query's mutation callbacks for cleaner async flow handling.

---

### FE-003: Hardcoded Layout UUIDs Create Backend Coupling

| Field | Value |
|-------|-------|
| **ID** | FE-003 |
| **Severity** | LOW |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/admin/api/adminApi.ts` |
| **Classification** | advisory |

**Description:** Dashboard creation API uses hardcoded UUID values for layout mapping (`LAYOUT_NAME_TO_ID` constant, lines 48-53). These UUIDs are described as "must match seeded layout records in DB" which creates tight coupling between frontend and backend database seeding. If these UUIDs change in the backend, the frontend will break silently.

**Evidence:** `frontend/src/features/admin/api/adminApi.ts` lines 48-53:
```typescript
const LAYOUT_NAME_TO_ID: Record<string, string> = {
  'single-column': '00000000-0000-0000-0000-000000000001',
  'two-columns': '00000000-0000-0000-0000-000000000002',
  'grid': '00000000-0000-0000-0000-000000000003',
}
```

**Recommendation:** Consider fetching available layouts from the backend API or having the backend accept layout names directly instead of UUIDs.

---

### FE-004: Missing Accessibility Attributes

| Field | Value |
|-------|-------|
| **ID** | FE-004 |
| **Severity** | MEDIUM |
| **Type** | BEST-PRACTICE |
| **Affected Modules** | `frontend/src/features/upload/ui/FileDropzone.tsx`, `frontend/src/features/upload/ui/UploadModal.tsx` |
| **Classification** | advisory |

**Description:** Several interactive elements lack proper accessibility attributes. The FileDropzone Paper component (lines 75-99) has no ARIA attributes to describe its interactive nature for screen readers. The ToggleButtonGroup for upload mode (AdminPanel) has no aria-label. While TextField components have labels and MUI components provide basic keyboard navigation, additional ARIA attributes would improve accessibility compliance.

**Evidence:** `frontend/src/features/upload/ui/FileDropzone.tsx` - Paper component has no aria attributes. `frontend/src/features/upload/ui/UploadModal.tsx` lines 183-195 - ToggleButtonGroup has no aria-label.

**Recommendation:** Add `aria-label` to interactive elements, use `aria-live` for status updates during upload, and ensure all form controls have proper labeling.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 2 |
| LOW | 1 |

## Mandatory Fixes

- FE-001: Review potential circular import between axiosInstance and authApi modules

## Advisory Recommendations

- FE-002: Refactor stale closure handling in UploadModal status polling
- FE-003: Replace hardcoded layout UUIDs with API-based configuration
- FE-004: Improve accessibility with ARIA attributes and keyboard navigation

## Doc Updates Needed

None