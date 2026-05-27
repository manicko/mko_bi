---
name: audit-frontend
description: Frontend architecture audit covering Feature-Sliced Design compliance, React SPA correctness, type safety, API integration, code quality
agent: audit-executor
alwaysApply: false
---

# Phase 2 Audit — Frontend Architecture

**Executor:** audit-executor
**Status:** {pending|in-progress|complete}
**Validated:** {yes|no}

**IMPORTANT:** Base layer context is auto-included by orchestrator:
- Project: mkobi BI Dashboard (FastAPI + React + PostgreSQL)
- Structure: `.ai/structure/map.md`
- Commands: `.ai/context/commands.md`
- SPEC: `docs/SPEC.md`

---

## Audit Dimensions

### 1. Frontend Structure (FSD)

Verify Feature-Sliced Design compliance:

| Check | Status | Evidence |
|-------|--------|----------|
| `app/` layer: providers.tsx (QueryClient, Router, Theme), routes.tsx (all routes) | | |
| `features/` layer: auth/, dashboards/, upload/, users/, admin/ | | |
| `shared/` layer: api/, components/, types/ | | |
| Feature structure: **ui/** (React components, UI logic only) | | |
| Feature structure: **api/** (API calls, axios, TanStack Query) | | |
| Feature structure: **model/** (State, hooks like useAuth, useDashboards) | | |
| Feature structure: **types/** (TypeScript types) | | |
| No business logic in components | | |
| No duplicated API calls | | |
| No hardcoded URLs (use axiosInstance) | | |
| No mixed responsibilities between layers | | |

**Files to Audit:**
- `frontend/src/app/*.tsx`
- `frontend/src/features/auth/**/*`
- `frontend/src/features/dashboards/**/*`
- `frontend/src/features/upload/**/*`
- `frontend/src/features/users/**/*`
- `frontend/src/features/admin/**/*`
- `frontend/src/shared/api/*.ts`
- `frontend/src/shared/components/*.tsx`
- `frontend/src/shared/types/*.ts`

---

### 2. Frontend Routes

Verify all routes implemented with correct access control:

| Check | Status | Evidence |
|-------|--------|----------|
| `/login` → LoginForm (Public) | | |
| `/register` → RegisterForm (Public) | | |
| `/dashboards` → DashboardList (Authenticated) | | |
| `/dashboard/:id` → DashboardView (Authenticated) | | |
| `/dashboard/:id/upload` → UploadPage (Admin, Editor) | | |
| `/admin` → AdminPanel (Admin only) | | |
| `/profile` → UserProfile (Authenticated) | | |
| `/profile/change-password` → ChangePasswordPage (Authenticated) | | |
| `*` → NotFound (Public) | | |
| ProtectedRoute works correctly | | |
| RoleBasedAccess works correctly | | |

---

### 3. Type Safety

Verify TypeScript strict mode and Zod schemas:

| Check | Status | Evidence |
|-------|--------|----------|
| TypeScript strict mode used (NO `any`) | | |
| Types for API responses (AuthResponse, DashboardSummary, etc.) | | |
| Types for components (props interfaces) | | |
| Zod schemas for forms (React Hook Form) | | |
| `tsc --noEmit` passes without errors | | |

---

### 4. API Integration

Verify axiosInstance, JWT interceptors, and TanStack Query:

| Check | Status | Evidence |
|-------|--------|----------|
| axiosInstance used (NOT direct axios) | | |
| base URL `/api/v1` configured | | |
| JWT added via request interceptor | | |
| Token expiration checked before attaching | | |
| Response interceptor handles 401 (removes token, toast notification, redirect to `/login`) | | |
| TanStack Query for server state | | |
| Polling for long operations (processing status) | | |
| react-hot-toast for notifications | | |

---

### 5. UI Components

Verify all pages from spec implemented:

| Check | Status | Evidence |
|-------|--------|----------|
| Login Page: fields email/password, email validation, login button, registration link, error display | | |
| Registration Page: email field (Zod validation), domain blocklist check, success message | | |
| Dashboard List Page: list of dashboards, cards with name/description/link | | |
| Dashboard View Page: title, Filters Panel (dynamic), Charts Grid (Plotly.js React), upload button (editor+ only) | | |
| Upload Page: mode toggle (Overwrite/Append), dropzone (react-dropzone), progress bar | | |
| Admin Panel: User Management, Registration Requests, Dashboard Management, Log Viewer | | |
| User Profile Page: email (read-only), role (read-only), display_name, Delete Account button (non-admin), Change Password link | | |

---

### 6. Chart Rendering

Verify Plotly.js React charts config-driven:

| Check | Status | Evidence |
|-------|--------|----------|
| BarChart (Plotly.js React) | | |
| LineChart (Plotly.js React) | | |
| PieChart (Plotly.js React) | | |
| TableChart | | |
| PlotlyChart wrapper | | |
| Supported types: bar, line, pie, table | | |
| Config-driven rendering (from `graph.config` JSONB) | | |
| Invalid config handling | | |
| Missing data handling | | |

---

### 7. State Management

Verify TanStack Query and React Hook Form + Zod:

| Check | Status | Evidence |
|-------|--------|----------|
| TanStack Query for server state (NOT Redux/Zustand) | | |
| React Hook Form for forms | | |
| Zod for form validation | | |
| Local state via `useState`/`useReducer` where appropriate | | |
| No excessive global state | | |

---

### 8. Frontend Security

Verify JWT storage and access control:

| Check | Status | Evidence |
|-------|--------|----------|
| JWT stored in memory (production) or sessionStorage (development) — NOT localStorage | | |
| Axios interceptors add token correctly | | |
| ProtectedRoute component works | | |
| RoleBasedAccess component works | | |
| Email validation (Zod regex + blacklist domains) | | |
| UI-level role checks are for UX only (backend enforces authorization) | | |

---

## Findings

### FE-{NN}: {Title}

| Field | Value |
|-------|-------|
| **ID** | FE-{NN} |
| **Severity** | {severity} |
| **Type** | {type} |
| **Affected Modules** | {modules} |
| **Classification** | {mandatory|advisory} |

**Description:** {description}

**Evidence:** {evidence}

**Recommendation:** {recommendation}

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |

## Mandatory Fixes

{List all findings classified as mandatory}

## Advisory Recommendations

{List all findings classified as advisory}

## Doc Updates Needed

{List all findings classified as DOC-UPDATE type}

---

## Template Field Reference

### Mandatory Fields Per Finding

| Field | Type | Values/Format |
|-------|------|---------------|
| `id` | string | Unique identifier with `FE-` prefix (e.g., `FE-001`, `FE-002`) |
| `title` | string | Human-readable one-line summary |
| `type` | enum | `SPEC-DEVIATION`, `BEST-PRACTICE`, `DOC-UPDATE`, `RUNTIME-ERROR` |
| `severity` | enum | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `description` | string | Detailed problem description with context |
| `evidence` | string | File paths, line references, log excerpts, code snippets |
| `affected_modules` | list | Affected module paths (e.g., `frontend/src/features/auth/`) |
| `recommendation` | string | Concrete fix direction: what to change and why |
| `classification` | enum | `mandatory` (security, data loss, correctness) or `advisory` (improvement, refactoring) |

### Classification Guide

- **mandatory**: Security vulnerabilities, data loss risks, correctness issues, spec deviations requiring immediate fix
- **advisory**: Code quality improvements, refactoring suggestions, best practice enhancements

---

**Report Format:** See `.kilo/commands/audit/templates/audit-findings.md` for full template.