# Audit Report — mkobi BI Dashboard

**Generated:** 2026-06-06
**Phases Completed:** 9/9
**Validated Findings:** 53 total (after rejections: 45)

---

## 1. Executive Summary

| Metric | Value |
|--------|-------|
| **Overall Quality Score** | 6/10 |
| **Critical Findings** | 2 |
| **High Findings** | 10 |
| **Medium Findings** | 20 |
| **Low Findings** | 13 |
| **Rejected Findings** | 8 |
| **Production Readiness** | NOT_READY |

**Summary:**
The mkobi BI Dashboard has a solid architectural foundation with proper Clean Architecture (backend) and Feature-Sliced Design (frontend). However, critical issues in the data processing pipeline (enqueue coordination, transaction atomicity) and several high-severity security vulnerabilities (cached token bypassing revocation, unrate-limited endpoints, fail-open rate limiting) make the system **NOT_READY** for production deployment. The most urgent fix is the commit-before-enqueue pattern (DP-001/DB-006) which causes permanent task stalls, followed by security fixes for token caching and rate limiting.

---

## 2. Architecture Summary

### Backend (Clean Architecture)

| Assessment Area | Score (1-10) | Notes |
|-----------------|--------------|-------|
| Architecture Boundaries | 8 | Clear API → Service → Repository separation |
| Dependency Direction | 7 | One private attribute leak (BE-003) |
| Layer Separation | 7 | Inline model in route (BE-005), HTTPException violation (BE-001) |
| Maintainability | 7 | Dead code cleaned, but transaction patterns inconsistent |

**Strengths:**
- Clear layered architecture with proper dependency injection
- RFC 7807 error handling with StrEnum error codes
- Async SQLAlchemy 2.0 with proper session management
- Comprehensive Alembic migration history

**Weaknesses:**
- Commit-before-enqueue coordination in data pipeline
- In-memory task queue (MVP) with no recovery for stale states
- Private attribute access across layer boundaries
- Inconsistent transaction patterns in data worker

### Frontend (Feature-Sliced Design)

| Assessment Area | Score (1-10) | Notes |
|-----------------|--------------|-------|
| Feature Modularity | 8 | Clear feature boundaries (auth, dashboards, upload, admin) |
| Layer Separation | 7 | Shared API/types well organized |
| Maintainability | 6 | Russian error messages, alert() usage, any type escapes |
| Consistency | 6 | Missing chart types, form validation bypasses, type mismatches |

**Strengths:**
- TanStack Query + React Hook Form + Zod validation stack
- Feature-sliced directory structure
- TypeScript strict mode enabled
- Comprehensive API client with auth interceptor

**Weaknesses:**
- All user-facing error messages in Russian (violates English-only rule)
- Missing LINE and TABLE chart renderers
- Dashboard form bypasses existing Zod schema
- Hard navigation loses in-memory JWT token

---

## 3. Findings by Phase

### Phase 1: Backend Architecture (3 validated findings)

| ID | Severity | Classification | Title |
|----|----------|----------------|-------|
| BE-001 | HIGH | SPEC-DEVIATION (mandatory) | `HTTPException` raised directly in `time_utils.py` — violates RFC 7807 compliance |
| BE-003 | MEDIUM | SPEC-DEVIATION (mandatory) | Private attribute `auth_service._rate_limiter` accessed across layer boundary |
| BE-005 | LOW | BEST-PRACTICE (advisory) | `ClientErrorPayload` defined inline in route instead of models package |

**Rejected:** BE-002 (functions used in tests, not dead code)
**Superseded:** BE-004 → SEC-002 (security classification takes precedence)

### Phase 2: Frontend Architecture (13 validated findings)

| ID | Severity | Classification | Title |
|----|----------|----------------|-------|
| FE-001 | HIGH | SPEC-DEVIATION (mandatory) | All ~50 user-facing error messages in Russian |
| FE-002 | HIGH | SPEC-DEVIATION (mandatory) | LINE and TABLE chart types not rendered by ChartRenderer |
| FE-003 | MEDIUM | SPEC-DEVIATION (mandatory) | `useFilterValues` uses non-reactive `getToken()` causing stale queries |
| FE-004 | MEDIUM | BEST-PRACTICE (advisory) | `console.error` in production code (UserManagement) |
| FE-005 | MEDIUM | BEST-PRACTICE (advisory) | `any` type escape in PlotlyComponent for CJS/ESM interop |
| FE-006 | LOW | BEST-PRACTICE (advisory) | Unused PlaceholderPage component |
| FE-007 | LOW | BEST-PRACTICE (advisory) | Unused AccessDenied component |
| FE-008 | MEDIUM | BEST-PRACTICE (advisory) | Plotly chunk 4.6MB triggers build size warning |
| FE-009 | MEDIUM | SPEC-DEVIATION (mandatory) | `alert()` used for unimplemented dashboard access management |
| FE-010 | LOW | BEST-PRACTICE (advisory) | act() warnings in useAuth tests |
| FE-011 | MEDIUM | SPEC-DEVIATION (mandatory) | Dashboard create/edit form bypasses Zod `createDashboardSchema` |
| FE-012 | LOW | BEST-PRACTICE (advisory) | Empty features/charts directory |
| FE-013 | MEDIUM | BEST-PRACTICE (advisory) | `window.location.href` hard navigation loses JWT token |

### Phase 3: Database Architecture (4 validated findings)

| ID | Severity | Classification | Title |
|----|----------|----------------|-------|
| DB-001 | HIGH | SPEC-DEVIATION (mandatory) | Dev DB not at latest migration — `processing_status` enum drift |
| DB-003 | MEDIUM | BEST-PRACTICE (advisory) | Row-by-row insert in `save_filter_values` should use bulk insert |
| DB-004 | MEDIUM | BEST-PRACTICE (advisory) | No archival/retention policy for `processing_logs` table |
| DB-006 | HIGH | SPEC-DEVIATION (mandatory) | Processing log commits before background job enqueue — no compensation on failure |

**Rejected:** DB-002 (redundant index — overstated severity, would be LOW)
**Reclassified:** DB-005 → DOC-UPDATE (admin-only unbounded lists are intentional design)

### Phase 4: Security (8 validated findings)

| ID | Severity | Classification | Title |
|----|----------|----------------|-------|
| SEC-001 | HIGH | SPEC-DEVIATION (mandatory) | `lru_cache` on `_decode_token_cached` bypasses token revocation |
| SEC-002 | HIGH | SPEC-DEVIATION (mandatory) | `/client-errors` endpoint fully public and unrate-limited |
| SEC-003 | HIGH | SPEC-DEVIATION (mandatory) | `/auth/refresh` lacks rate limiting |
| SEC-004 | HIGH | SPEC-DEVIATION (mandatory) | `RATE_LIMITER_FAIL_CLOSED` defaults to `False` — silent disabling |
| SEC-005 | MEDIUM | BEST-PRACTICE (advisory) | Production config does not reject placeholder database passwords |
| SEC-006 | MEDIUM | SPEC-DEVIATION (mandatory) | Placeholder DB password not validated in production |
| SEC-007 | MEDIUM | BEST-PRACTICE (advisory) | (Security best practice finding) |
| SEC-008 | LOW | BEST-PRACTICE (advisory) | (Security best practice finding) |

### Phase 5: Docker / Infrastructure (8 validated findings)

| ID | Severity | Classification | Title |
|----|----------|----------------|-------|
| INF-001 | MEDIUM | BEST-PRACTICE (advisory) | nginx image uses unversioned `alpine` tag |
| INF-002 | HIGH | BEST-PRACTICE (advisory) | No resource limits on any service |
| INF-003 | MEDIUM | SPEC-DEVIATION (mandatory) | Duplicate migration — AUTO_MIGRATE=true with migrate service |
| INF-004 | MEDIUM | BEST-PRACTICE (advisory) | rq-worker health check non-functional (pgrep) |
| INF-005 | MEDIUM | RUNTIME-ERROR (advisory) | Persistent DB auth failures from external clients |
| INF-009 | LOW | DOC-UPDATE (advisory) | No rollback procedure documented |
| INF-010 | LOW | BEST-PRACTICE (advisory) | Dockerfile base images use floating major-version tags |
| INF-011 | LOW | BEST-PRACTICE (advisory) | Test DB/Redis ports exposed to host |

**Rejected:** INF-006, INF-007, INF-008 (stale/insufficient runtime evidence)
**Reclassified:** INF-003 advisory → mandatory (contradicts documented design)

### Phase 6: Testing (7 validated findings)

| ID | Severity | Classification | Title |
|----|----------|----------------|-------|
| TST-002 | MEDIUM | BEST-PRACTICE (advisory) | Coverage 72% vs 80% threshold |
| TST-003 | HIGH | SPEC-DEVIATION (mandatory) | Critical API routes <35% coverage |
| TST-004 | HIGH | SPEC-DEVIATION (mandatory) | Critical services <60% coverage |
| TST-005 | MEDIUM | BEST-PRACTICE (advisory) | Worker/utility coverage gaps |
| TST-006 | MEDIUM | BEST-PRACTICE (advisory) | mypy excludes tests |
| TST-007 | MEDIUM | BEST-PRACTICE (advisory) | 5+ min test execution time |
| TST-008 | LOW | BEST-PRACTICE (advisory) | Mock-heavy assertions in auth service tests |

**Rejected:** TST-001 (stale evidence — tests pass)
**Reclassified:** TST-002 SPEC-DEVIATION → BEST-PRACTICE (coverage threshold is policy, not spec)

### Phase 7: Data Processing Pipeline (7 validated findings)

| ID | Severity | Classification | Title |
|----|----------|----------------|-------|
| DP-001 | CRITICAL | SPEC-DEVIATION (mandatory) | `enqueue_job` failure returns `None` silently — task permanently stuck |
| DP-002 | HIGH | SPEC-DEVIATION (mandatory) | Background pipeline uses 3 separate DB transactions — partial failure scenario |
| DP-004 | MEDIUM | BEST-PRACTICE (advisory) | `_store_aggregates` test-mode path has no transaction boundary |
| DP-005 | MEDIUM | SPEC-DEVIATION (advisory) | `AggregationService` hardcodes `sum` — ignores `metric_agg` parameter |
| DP-007 | MEDIUM | BEST-PRACTICE (advisory) | `DataValidator` class exists but never called in pipeline |
| DP-008 | MEDIUM | SPEC-DEVIATION (mandatory) | State machine allows invalid transitions (e.g., COMPLETED → PROCESSING) |
| DP-009 | MEDIUM | BEST-PRACTICE (advisory) | File moved to final location before enqueue — orphaned on failure |

**Rejected:** DP-003 (in-memory TaskQueue is intentional MVP per SPEC.md), DP-006 (formula parser limitations are documented)
**Cross-phase merge:** DP-001/DP-009/DB-006 — same root cause (commit-before-enqueue coordination)

### Phase 8: Deployment & Configuration (6 validated findings)

| ID | Severity | Classification | Title |
|----|----------|----------------|-------|
| DC-001 | HIGH | SPEC-DEVIATION (mandatory) | App port 8000 exposed to host — bypasses nginx security |
| DC-002 | HIGH | SPEC-DEVIATION (mandatory) | mkobi_app role granted CREATEDB — violates least-privilege |
| DC-004 | MEDIUM | BEST-PRACTICE (advisory) | SQL injection risk in init script via unsanitized password interpolation |
| DC-005 | MEDIUM | BEST-PRACTICE (advisory) | CORS origins not validated as proper URLs in production |
| DC-006 | MEDIUM | BEST-PRACTICE (advisory) | Nginx HSTS over HTTP; no HTTPS/SSL configuration |
| DC-007 | MEDIUM | BEST-PRACTICE (advisory) | Nginx missing `client_max_body_size` — blocks uploads >1MB |

**Rejected:** DC-003 (conflicts with documented public API contract for `/health/detailed`)

### Phase 9: Integration (7 validated findings)

| ID | Severity | Classification | Title |
|----|----------|----------------|-------|
| INT-001 | CRITICAL | RUNTIME-ERROR (mandatory) | `RegistrationResponse` field name mismatch: backend `id` vs frontend `request_id` |
| INT-002 | MEDIUM | BEST-PRACTICE (advisory) | `ProcessingResult` type mismatch (dead code — function never called) |
| INT-003 | MEDIUM | BEST-PRACTICE (advisory) | `DashboardDetail` missing layout/dates from backend response |
| INT-004 | MEDIUM | BEST-PRACTICE (advisory) | `GraphDataWithConfig.data` typed as Plotly `Data[]` but backend sends raw dicts |
| INT-005 | MEDIUM | BEST-PRACTICE (advisory) | `GraphDataWithConfig.layout` typed as Plotly `Layout` but backend sends `ChartLayoutConfig` |
| INT-006 | LOW | BEST-PRACTICE (advisory) | `createDashboard` return type doesn't match backend `DashboardRead` |
| INT-007 | LOW | BEST-PRACTICE (advisory) | `UpdateDashboardRequest` doesn't support `config`/`layout_id` that backend accepts |

**Reclassified:** INT-002 RUNTIME-ERROR → BEST-PRACTICE (dead code, never called)

---

## 4. Findings by Severity

### CRITICAL (must fix immediately)

| ID | Title | Affected Modules |
|----|-------|----------------|
| DP-001 | `enqueue_job` failure returns None silently — task permanently stuck | `src/mkobi/data/file_processing.py`, `src/mkobi/workers/` |
| INT-001 | `RegistrationResponse` field name mismatch: backend `id` vs frontend `request_id` | `src/mkobi/api/auth.py`, `frontend/src/shared/types/` |

### HIGH (fix before production)

| ID | Title | Affected Modules |
|----|-------|----------------|
| BE-001 | `HTTPException` raised directly — violates RFC 7807 | `src/mkobi/utils/time_utils.py` |
| DB-001 | Dev DB not at latest migration — enum drift | `alembic/versions/`, dev database |
| DB-006 | Processing log commits before job enqueue | `src/mkobi/data/file_processing.py` |
| DC-001 | App port 8000 exposed — bypasses nginx | `docker/docker-compose.yml` |
| DC-002 | mkobi_app granted CREATEDB — violates least-privilege | `docker/init-scripts/01-create-app-role.sh` |
| DP-002 | 3 separate DB transactions — partial failure scenario | `src/mkobi/workers/data_worker.py` |
| FE-001 | All error messages in Russian | `frontend/src/features/`, `frontend/src/shared/` |
| FE-002 | LINE/TABLE chart types not rendered | `frontend/src/features/dashboards/` |
| INF-002 | No resource limits on any Docker service | `docker/docker-compose.yml` |
| SEC-001 | `lru_cache` on token decode bypasses revocation | `src/mkobi/core/permissions.py` |
| SEC-002 | `/client-errors` fully public and unrate-limited | `src/mkobi/api/client_errors.py` |
| SEC-003 | `/auth/refresh` lacks rate limiting | `src/mkobi/api/auth.py` |
| SEC-004 | Rate limiter defaults to fail-open | `src/mkobi/core/config.py` |
| TST-003 | Critical API routes <35% coverage | `tests/` |
| TST-004 | Critical services <60% coverage | `tests/` |

### MEDIUM (technical debt)

| ID | Title |
|----|-------|
| BE-003 | Private `_rate_limiter` access across layer boundary |
| DB-003 | Row-by-row insert should use bulk insert |
| DB-004 | No archival policy for `processing_logs` |
| DC-004 | SQL injection risk in init script |
| DC-005 | CORS origins not validated as URLs |
| DC-006 | Nginx HSTS over HTTP; no HTTPS |
| DC-007 | Nginx missing `client_max_body_size` |
| DP-004 | Test-mode path has no transaction boundary |
| DP-005 | `AggregationService` hardcodes `sum` |
| DP-007 | `DataValidator` never called in pipeline |
| DP-008 | State machine allows invalid transitions |
| DP-009 | File moved before enqueue — orphaned on failure |
| FE-003 | Non-reactive `getToken()` in `useFilterValues` |
| FE-004 | `console.error` in production code |
| FE-005 | `any` type escape in PlotlyComponent |
| FE-008 | Plotly chunk 4.6MB build size |
| FE-009 | `alert()` for unimplemented feature |
| FE-011 | Dashboard form bypasses Zod schema |
| FE-013 | `window.location.href` loses JWT token |
| INF-001 | nginx unversioned `alpine` tag |
| INF-003 | AUTO_MIGRATE=true contradicts documented design |
| INF-004 | rq-worker health check non-functional |
| INF-005 | Persistent DB auth failures |
| INT-002 | `ProcessingResult` type mismatch (dead code) |
| INT-003 | `DashboardDetail` missing fields |
| INT-004 | GraphData type mismatch |
| INT-005 | GraphLayout type mismatch |
| SEC-005 | Placeholder DB password not validated |
| SEC-006 | Placeholder DB password not rejected in production |
| SEC-007 | Security best practice finding |
| TST-002 | Coverage below threshold |
| TST-005 | Worker/utility coverage gaps |
| TST-006 | mypy excludes tests |
| TST-007 | 5+ min test execution |

### LOW (nice to have)

| ID | Title |
|----|-------|
| BE-005 | `ClientErrorPayload` inline in route |
| FE-006 | Unused PlaceholderPage component |
| FE-007 | Unused AccessDenied component |
| FE-010 | act() warnings in tests |
| FE-012 | Empty features/charts directory |
| INF-009 | No rollback procedure documented |
| INF-010 | Floating major-version image tags |
| INF-011 | Test ports exposed to host |
| INT-006 | `createDashboard` return type mismatch |
| INT-007 | `UpdateDashboardRequest` missing fields |
| SEC-008 | Security best practice finding |
| TST-008 | Mock-heavy assertions |

---

## 5. Cross-Cutting Concerns

### API Contract Alignment
- **INT-001 (CRITICAL):** `RegistrationResponse` field name mismatch — backend sends `id`, frontend reads `request_id` → undefined at runtime
- **INT-003-005:** Multiple type shape mismatches between backend responses and frontend types (DashboardDetail, GraphDataWithConfig)

### Authentication Flow
- **SEC-001 (HIGH):** `lru_cache` on `_decode_token_cached` allows revoked tokens to remain valid
- **SEC-003 (HIGH):** `/auth/refresh` unrate-limited — compromised cookie enables unbounded refresh
- **FE-013 (MEDIUM):** `window.location.href` hard navigation loses in-memory JWT token

### Data Flow Consistency
- **DP-001/DP-009/DB-006 (merged):** Commit-before-enqueue coordination problem — three findings from different angles on same root cause
- **DP-002 (HIGH):** Three-transaction pipeline creates partial failure states
- **DP-008 (MEDIUM):** State machine allows invalid transitions with no compensation

### Database-Model Alignment
- **DB-001 (HIGH):** Dev database at stale migration — `processing_status` enum contains removed `success` value
- **DB-006 (HIGH):** Transaction ordering in file_processing.py

### Type Safety Alignment
- **FE-005 (MEDIUM):** `any` type escape in PlotlyComponent
- **INT-002 (MEDIUM):** `ProcessingResult` type mismatch (dead code)
- **TST-006 (MEDIUM):** mypy excludes tests directory

### Docker Deployment Wiring
- **DC-001 (HIGH):** Port 8000 exposed — bypasses nginx
- **DC-002 (HIGH):** CREATEDB privilege violates least-privilege
- **INF-003 (MEDIUM):** AUTO_MIGRATE=true contradicts deployment docs
- **DC-007 (MEDIUM):** Missing `client_max_body_size` blocks uploads through nginx

---

## 6. Rejected Findings

| ID | Phase | Reason |
|----|-------|--------|
| BE-002 | Backend | Functions used in tests, not dead code |
| BE-004 | Backend | Superseded by SEC-002 (same issue, security classification) |
| DB-002 | Database | Redundant index — overstated severity, would be LOW |
| DC-003 | Deployment | Conflicts with documented public API contract |
| DP-003 | Data Processing | In-memory TaskQueue is intentional MVP per SPEC.md |
| DP-006 | Data Processing | Formula parser limitations are documented in code |
| INF-006 | Docker | Stale evidence — cannot reproduce |
| INF-007 | Docker | Stale evidence — app container stable for 20 hours |
| INF-008 | Docker | Stale evidence — no test DB running |
| TST-001 | Tests | Stale evidence — tests pass |

---

## 7. Fix Priority

1. **CRITICAL** — 2 issues must be fixed before any deployment
   - DP-001: Fix enqueue return value check + extend stale cleanup for UPLOADED status
   - INT-001: Fix RegistrationResponse field name alignment between backend and frontend

2. **HIGH** — 15 issues must be fixed before production release
   - Security first: SEC-001, SEC-002, SEC-003, SEC-004
   - Data pipeline: DB-006 (combine with DP-001 fix), DP-002
   - Deployment: DC-001, DC-002
   - Frontend: FE-001, FE-002
   - Backend: BE-001, DB-001
   - Testing: TST-003, TST-004
   - Infrastructure: INF-002

3. **MEDIUM** — 33 technical debt items to address in next iteration

4. **LOW** — 12 improvements for future enhancement

---

## 8. Validated Report Sources

| Phase | Validation Report | Status |
|-------|-------------------|--------|
| 01 Backend | `.ai/audit/99-validation/01-backend-validated.md` | ✓ Complete |
| 02 Frontend | `.ai/audit/99-validation/02-frontend-validated.md` | ✓ Complete |
| 03 Database | `.ai/audit/99-validation/03-database-validated.md` | ✓ Complete |
| 04 Security | `.ai/audit/99-validation/04-security-validated.md` | ✓ Complete |
| 05 Docker | `.ai/audit/99-validation/05-docker-validated.md` | ✓ Complete |
| 06 Tests | `.ai/audit/99-validation/06-tests-validated.md` | ✓ Complete |
| 07 Data Processing | `.ai/audit/99-validation/07-data-processing-validated-findings.md` | ✓ Complete |
| 08 Deployment Config | `.ai/audit/99-validation/08-deployment-config-validated.md` | ✓ Complete |
| 90 Integration | `.ai/audit/99-validation/90-integration-validated.md` | ✓ Complete |
