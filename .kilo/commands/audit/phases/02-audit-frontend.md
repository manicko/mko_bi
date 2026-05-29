---
name: 02-frontend
description: Frontend architecture audit covering component isolation, state management, type safety, security boundaries, and runtime behavior
agent: audit-executor
alwaysApply: false
---

# Phase 02 Audit — Frontend Architecture

**Executor:** audit-executor
**Status:** {pending|in-progress|complete}
**Validated:** {yes|no}

---

## Discovery Stage

Before performing audit checks, discover the project's architectural reality:

1. **Architecture Discovery**
   - Identify the primary architectural pattern (Feature-Sliced Design, modular, component-based)
   - Map layer boundaries: presentation → business logic → data access
   - Identify feature modules and their responsibilities
   - Locate trust boundaries (auth zones, admin-only areas)

2. **Component Structure Discovery**
   - UI layer: presentation components
   - State layer: data fetching and local state management
   - API layer: external communication
   - Shared/utilities: reusable code

3. **Critical Flows Discovery**
   - Authentication flow (token acquisition, storage, refresh)
   - Data loading and rendering flow
   - User interaction → state → API → render cycle
   - Error handling and user feedback paths

4. **Runtime Model**
   - Client-side routing structure
   - State management approach
   - Async operation handling
   - Memory/resource lifecycle

---

## Audit Dimensions

### 1. Component Architecture Invariants

Verify clean component boundaries and separation of concerns:

| Check | Status | Evidence |
|-------|--------|----------|
| UI components contain rendering logic only | | |
| Business logic is extracted from components | | |
| State management is centralized or colocated with features | | |
| No duplicated API calls or data fetching patterns | | |
| No hardcoded URLs or endpoints in components | | |
| Layer boundaries preserved (no cross-layer leakage) | | |

---

### 2. State Consistency

Verify predictable state management:

| Check | Status | Evidence |
|-------|--------|----------|
| Server state managed through query library (TanStack Query or equivalent) | | |
| Form state managed through form library with validation | | |
| Local state changes are predictable and traceable | | |
| No excessive global state | | |
| State updates trigger re-renders correctly | | |
| No stale closures or race conditions in state access | | |

---

### 3. Rendering Correctness

Verify UI reliability and performance:

| Check | Status | Evidence |
|-------|--------|----------|
| Chart rendering handles missing/null data gracefully | | |
| Config-driven rendering (data shapes define UI) | | |
| Invalid configurations produce safe fallback UI | | |
| No rendering crashes from malformed data | | |
| Loading states for async operations | | |
| Error states for failed operations | | |

---

### 4. Client Security Boundaries

Verify frontend security properties:

| Check | Status | Evidence |
|-------|--------|----------|
| Tokens stored securely (memory or httpOnly, not localStorage) | | |
| HTTP interceptors attach credentials to requests | | |
| Protected routes block unauthorized access | | |
| Role-based UI elements are UX-only (backend enforces) | | |
| Input validation on client matches backend requirements | | |
| No sensitive data logged to browser console | | |

---

### 5. Type Safety & Validation

Verify frontend type correctness:

| Check | Status | Evidence |
|-------|--------|----------|
| TypeScript strict mode enabled (no `any`) | | |
| Types defined for all API responses | | |
| Types defined for component props | | |
| Form schemas validate input correctly | | |
| No type mismatches between API and frontend | | |

---

### 6. Accessibility

Verify inclusive UI design:

| Check | Status | Evidence |
|-------|--------|----------|
| Interactive elements have proper ARIA attributes | | |
| Keyboard navigation supported | | |
| Color contrast meets WCAG standards | | |
| Form fields have associated labels | | |
| Error messages accessible to screen readers | | |

---

## Report Output

Write findings to: `.ai/audit/02-frontend/findings.md` using template `.ai/audit/templates/audit-findings.md`.

Use prefix `FE-` for finding IDs.