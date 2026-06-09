---
name: 02-frontend
description: Frontend architecture audit covering component isolation, state management, type safety, security boundaries, and runtime behavior
agent: auditor
alwaysApply: false
problems-only: true
---

# Phase 02 Audit — Frontend Architecture

## Output Mode

`problems-only: true` — **only problems, bugs, and deviations are documented.**

- **Do NOT** write sections that say "X is correct" or "no issues found in Y".
- **Do NOT** include checklist rows where the check passes — omit them entirely.
- If a dimension has zero findings after investigation, **omit the dimension entirely**.
- Every finding must be actionable: it describes a real problem, its evidence (code/logs/output), and its impact.
- If `problems-only: false` were set, you would produce a full report with compliance statements. But it is `true`, so the report is exclusively findings.

---

## Discovery Stage

Before performing audit checks, discover the project's architectural reality:

1. **Architecture Discovery** — Identify the primary architectural pattern, map layer boundaries, identify feature modules and responsibilities, locate trust boundaries.
2. **Component Structure Discovery** — UI layer, state layer, API layer, shared/utilities.
3. **Critical Flows Discovery** — Auth flow, data loading/rendering, user interaction cycle, error handling paths.
4. **Runtime Model** — Client-side routing structure, state management approach, async handling, resource lifecycle.

---

## Mandatory Runtime Verification

**Before evaluating any checklist item, you MUST complete these steps. Use the commands provided in the project's commands file. Skip only if a step is impossible — document why.**

### Step R0 — Ensure Docker Environment is Running

Start Docker services in **development or test mode** (never production) before building or testing the frontend. Follow the setup instructions in `docs/11-guides/docker.md`. Confirm all required containers are in `running` or `healthy` state before proceeding. If the environment cannot be started, document why and skip dependent steps.

### Step R1 — Dependency Install and Build Verification

Install dependencies and run the production build.

- **Record exit codes.** A build failure is CRITICAL — the frontend does not work.
- If the build produces warnings, capture them. Warnings about missing types, deprecated APIs, or unused variables are evidence.
- If dependency install fails due to conflicts, that is a finding (dependency hygiene).

### Step R2 — TypeScript Compilation Check

Run the TypeScript compiler in no-emit mode.

- Record all TypeScript errors. Each error is a type-safety finding with file:line.
- Check `tsconfig.json`: verify `strict: true` and other strict flags. If strict mode is off, that is a finding.

### Step R3 — Lint Verification

Run the project's configured linter.

- Record all errors and warnings. Each error is evidence.
- If no linter is configured, that is itself a finding (missing quality gate).

### Step R4 — Frontend Test Execution

Run the project's frontend test suite.

- Record pass/fail counts, skipped tests, and failure output.
- Any failing test is a real bug — create a finding for each failure.
- If tests don't exist at all for critical features, that is a coverage gap finding.

### Step R5 — Dead/Unused Code Search

Identify components, pages, and API clients that exist in the codebase but are never rendered:

- Find all page/route components. Check which are registered in the router config.
- Components imported nowhere = dead code **only after Step R5-CROSSCHECK**.
- API client functions called nowhere = dead endpoints or dead client code.
- Routes in the router with no corresponding backend endpoint = broken navigation.

For each finding, provide file path, line number, and evidence of non-use.

#### Step R5-CROSSCHECK — Verify "Dead" Code Against Specification

**Before filing any "dead code" finding, you MUST cross-reference the item against the specification:**

1. Read `docs/SPEC.md` and applicable docs under `docs/07-frontend/`, `docs/02-dashboards/`, `docs/03-processing/`.
2. Check `src/mkobi/models/enums.py` for enum values (e.g., `GraphType`, `FilterType`) that define required features.
3. Check `src/mkobi/models/` for Pydantic models that reference the component type (e.g., `DashboardConfig.graph_types`).
4. For each "dead" component, answer: **Is this component type listed in the specification as a supported feature?**

**Decision logic:**
- **If the spec requires it but the component exists and is unwired** → This is NOT dead code. File as `[SPEC-DEVIATION]`: "Component X implements spec-required feature Y but is never imported/rendered — the feature is missing from the UI."
- **If the spec requires it and no component exists at all** → File as `[SPEC-DEVIATION]`: "Feature Y is specified but has no frontend implementation."
- **Only if the spec does NOT mention the feature AND the component is unwired** → File as dead code.

**Flagging rule:** If you find unwired components whose types match enum values in `GraphType`, `FilterType`, or similar spec enums, this is a **missing implementation finding**, not a dead code finding.

### Step R6 — API Contract Alignment

Extract all backend API routes and all frontend API calls:

- For each route the frontend calls, verify it exists on the backend (path + method match).
- For each route the backend exposes, verify it is called by the frontend (or document it as unused).
- Mismatches are CRITICAL findings — they will cause runtime errors for users.

---

## Audit Scope

Component architecture, state management, rendering correctness, client security, type safety, accessibility.

---

## Audit Dimensions

### 1. Component Architecture Invariants

| Check | Description |
|-------|-------------|
| UI components contain rendering logic only | Business logic should not live inside presentational components. |
| Business logic is extracted from components | Hooks, services, or utilities should own business rules. |
| State management is centralized or colocated with features | No ad-hoc state scattered across unrelated components. |
| No duplicated API calls or data fetching patterns | Single source of truth for each data fetch. |
| No hardcoded URLs or endpoints in components | All endpoints should come from a shared API client module. |
| Layer boundaries preserved | No cross-layer leakage (e.g. API layer importing from UI layer). |

**Evidence required:** Reference specific file:line. Use build/lint/test output from Steps R1-R4 as supporting evidence. Dead code from Step R5 feeds this section.

### 2. State Consistency

| Check | Description |
|-------|-------------|
| Server state managed through query library | No manual fetch for server data. |
| Form state managed through form library with validation | Forms have schema-driven validation. |
| Local state changes are predictable and traceable | No hidden state mutations. |
| No excessive global state | Only truly global data lives globally. |
| State updates trigger re-renders correctly | No stale UI after state changes. |
| No stale closures or race conditions | Async state access is safe. |

**Evidence required:** Read the actual query/form setup code. TypeScript errors from Step R2 related to state types are evidence.

### 3. Rendering Correctness

| Check | Description |
|-------|-------------|
| Chart rendering handles missing/null data gracefully | No crashes on empty datasets. |
| Config-driven rendering (data shapes define UI) | UI is driven by data, not hardcoded. |
| Invalid configurations produce safe fallback UI | Degraded UI, not broken UI. |
| No rendering crashes from malformed data | Error boundaries or safe defaults exist. |
| Loading states for async operations | Users see feedback during fetches. |
| Error states for failed operations | Users see meaningful error messages. |

**Evidence required:** Read chart/rendering components and trace what happens when data is `null`, `undefined`, or empty. If no loading state exists for a data-fetching component, show the file:line.

### 4. Client Security Boundaries

| Check | Description |
|-------|-------------|
| Tokens stored securely | Not in localStorage (XSS-vulnerable). |
| HTTP interceptors attach credentials to requests | All authenticated requests carry the token. |
| Protected routes block unauthorized access | Router-level auth guards exist. |
| Role-based UI elements are UX-only | backend enforcement is the real security. |
| Input validation on client matches backend requirements | Redundant but consistent validation. |
| No sensitive data logged to browser console | No `console.log` with tokens, passwords, PII. |

**Evidence required:** Read the actual token storage code. Check the interceptor for completeness. Search for `console.log` in production code.

### 5. Type Safety & Validation

| Check | Description |
|-------|-------------|
| TypeScript strict mode enabled (no `any`) | `strict: true` in tsconfig. |
| Types defined for all API responses | No untyped fetch results. |
| Types defined for component props | All props are explicitly typed. |
| Form schemas validate input correctly | Zod/Yup schemas cover all form fields. |
| No type mismatches between API and frontend | Frontend types match backend responses. |

**Evidence required:** Step R2 (tsc) output is primary evidence. Count `any` types. Step R6 (API contract alignment) feeds the mismatch check.

### 6. Accessibility

| Check | Description |
|-------|-------------|
| Interactive elements have proper ARIA attributes | `aria-label`, `aria-describedby`, etc. |
| Keyboard navigation supported | Tab order, Enter/Space activation. |
| Color contrast meets WCAG standards | Text is readable against backgrounds. |
| Form fields have associated labels | `<label htmlFor>` or `aria-labelledby`. |
| Error messages accessible to screen readers | Live regions for dynamic errors. |

**Evidence required:** Read component markup. If using an accessibility lint plugin, include its output (Step R3).

---

## Report Output

Write findings to: `.ai/audit/02-frontend/findings.md` using template `.ai/audit/templates/audit-findings.md`.

Use prefix `FE-` for finding IDs.

**`problems-only: true` rules:**
- The report contains **only findings** — real problems discovered during investigation.
- Do NOT include sections, dimensions, or checklist rows where everything is correct.
- If after completing all Runtime Verification steps and all Audit Dimensions, no problems were found, write a single line: `No problems found in this phase.`
- Every finding MUST include:
  1. **Runtime evidence** — build errors, TS compilation failures, lint errors, test failures, dead code proof, or API contract mismatches.
  2. **Not just:** "violates invariant X" — show the exact code (file:line), the exact error, and the exact user-facing consequence.
