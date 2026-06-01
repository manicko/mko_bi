# Audit Report — mkobi BI Dashboard

**Generated:** 2026-06-01
**Phases Completed:** 9/9
**Validated Findings:** 52 total

---

## 1. Executive Summary

| Metric | Value |
|--------|-------|
| **Overall Quality Score** | 5/10 |
| **Critical Findings** | 4 |
| **Production Readiness** | NOT_READY |

**Summary:**
The mkobi BI Dashboard has a solid architectural foundation with Clean Architecture (backend) and Feature-Sliced Design (frontend) patterns in place. However, the audit uncovered 4 critical findings that must be addressed before any production deployment: 233 backend tests are broken due to Docker port misconfiguration, an orphaned `/process` endpoint with broken route parameters, orphaned filter CRUD endpoints increasing attack surface, and a login flow that bypasses forced password change. Additionally, there are 14 HIGH-severity findings including missing token revocation, weak default secrets, missing resource-level access control, and data processing pipeline vulnerabilities (unbounded file reads, silent exception swallowing, YoY infinity values). The system requires significant remediation before production readiness.

---

## 2. Architecture Summary

### Backend (Clean Architecture)

| Assessment Area | Score (1-10) | Notes |
|-----------------|--------------|-------|
| Architecture Boundaries | 6 | API → Service → Repository pattern mostly followed; `data.py` bypasses repository with raw `select(Graph)` |
| Dependency Direction | 7 | Generally correct; some circular risk with custom `PermissionError` shadowing builtin |
| Layer Separation | 6 | Service layer exists but `data_service.py` lacks defense-in-depth access control |
| Maintainability | 7 | Good type hints, consistent patterns; dead `decorators.py` (362 lines) and dual logging patterns add noise |

**Strengths:**
- Clear API → Service → Repository layering in most modules
- Consistent use of Pydantic v2 models and StrEnum for constants
- Async SQLAlchemy 2.0 with asyncpg throughout
- Proper JWT + bcrypt authentication with rate limiting

**Weaknesses:**
- Dual route mounting pattern (composite + individual) creates fragile architecture
- Custom `PermissionError` shadows Python builtin, causing real bugs
- Dead code (`decorators.py`, unused chart components) increases maintenance surface
- Inconsistent logging patterns (10 modules use `get_logger()`, 52 use `logging.getLogger()`)

### Frontend (Feature-Sliced Design)

| Assessment Area | Score (1-10) | Notes |
|-----------------|--------------|-------|
| Feature Modularity | 7 | Good feature-based organization; some dead components |
| Layer Separation | 7 | Clear separation between features, shared, and app layers |
| Maintainability | 6 | TypeScript strict mode passes; `getToken()` coupling to global state is suboptimal |
| Consistency | 7 | Consistent patterns; minor issues with `console.error` and setState in effects |

**Strengths:**
- Clean Feature-Sliced Design with proper layer boundaries
- TypeScript strict mode with zero `any` types
- Memory-first token storage (XSS-safe in production)
- Protected routes and role-based access guards implemented

**Weaknesses:**
- Only 82 frontend tests across 6 files — critical components (ProtectedRoute, RoleBasedAccess, charts) have zero coverage
- `getToken()` called outside React context couples data layer to global state
- Dead chart components (BarChart, LineChart, PieChart, TableChart) and unused shared components

---

## 3. Findings by Phase

### Phase 1: Backend Architecture

| ID | Severity | Type | Classification | Title |
|----|----------|------|----------------|-------|
| BE-001 | HIGH | SPEC-DEVIATION | mandatory | Dual sub-router mounting pattern (composite + individual) — fragile architecture |
| BE-002 | HIGH | SPEC-DEVIATION | mandatory | `data.py` bypasses repository layer with raw `select(Graph)` |
| BE-003 | HIGH | RUNTIME-ERROR | mandatory | `PermissionError` not imported in `data.py` — 500 instead of 403 |
| BE-004 | MEDIUM | BEST-PRACTICE | advisory | Custom `PermissionError` shadows Python builtin |
| BE-005 | LOW | BEST-PRACTICE | advisory | Deprecated `get_session` export still present |
| BE-006 | LOW | BEST-PRACTICE | advisory | Dual logging pattern across 62 modules |
| BE-007 | LOW | BEST-PRACTICE | advisory | Dead `decorators.py` module (362 lines, 5 decorators) |

### Phase 2: Frontend Architecture

| ID | Severity | Type | Classification | Title |
|----|----------|------|----------------|-------|
| FE-001 | LOW | BEST-PRACTICE | advisory | `console.error` in `UserManagement.tsx` |
| FE-005 | HIGH | RUNTIME-ERROR | mandatory | `getToken()` outside React render cycle — stale `enabled` state |
| FE-006 | LOW | BEST-PRACTICE | advisory | Duplicate `getProfile()` in `authApi.ts` and `userApi.ts` |
| FE-008 | MEDIUM | BEST-PRACTICE | advisory | Incomplete admin features (access management `alert()`, empty LogViewer) |
| FE-009 | MEDIUM | SPEC-DEVIATION | mandatory | `confirm_password` sent to backend but no server-side match validation |
| FE-DEAD-CODE | LOW | BEST-PRACTICE | advisory | 6 dead unused components (4 charts + AccessDenied + PlaceholderPage) |

### Phase 3: Database

| ID | Severity | Type | Classification | Title |
|----|----------|------|----------------|-------|
| DB-01 | HIGH | SPEC-DEVIATION | mandatory | Migration chain has a branch — two independent branches merged with empty upgrade/downgrade |
| DB-02 | HIGH | SPEC-DEVIATION | mandatory | ORM `unique=True` vs raw `CREATE UNIQUE INDEX` — `alembic check` always reports false drift |
| DB-03 | MEDIUM | BEST-PRACTICE | advisory | No index on `dashboards.layout_id` FK column |
| DB-04 | MEDIUM | BEST-PRACTICE | advisory | No index on `dashboards.created_by` FK column |
| DB-05 | MEDIUM | BEST-PRACTICE | advisory | No index on `registration_requests.reviewed_by` FK column |
| DB-06 | MEDIUM | BEST-PRACTICE | advisory | Redundant duplicate index on `dashboard_filters` |
| DB-07 | HIGH | SPEC-DEVIATION | mandatory | `force_password_change` column missing from test database (60 vs 61 columns) |
| DB-08 | MEDIUM | BEST-PRACTICE | advisory | `processing_logs` has 951 sequential scans / 0 index scans |
| DB-09 | MEDIUM | BEST-PRACTICE | advisory | `create_dashboard` has partial-write risk — flush and access grant not atomic |

### Phase 4: Security

| ID | Severity | Type | Classification | Title |
|----|----------|------|----------------|-------|
| SEC-001 | HIGH | BEST-PRACTICE | mandatory | No token revocation — deactivated users can use valid tokens until expiry |
| SEC-002 | HIGH | SPEC-DEVIATION | mandatory | Weak default secrets in `docker/.env` and `docker-compose.override.yml` |
| SEC-003 | HIGH | SPEC-DEVIATION | mandatory | Dashboard update/delete endpoints lack resource-level access control |
| SEC-004 | MEDIUM | SPEC-DEVIATION | mandatory | Plaintext temp passwords returned in HTTP responses |
| SEC-005 | MEDIUM | BEST-PRACTICE | advisory | Missing HSTS and CSP security headers |
| SEC-006 | MEDIUM | BEST-PRACTICE | advisory | JWT secret key has no entropy or strength validation |
| SEC-007 | LOW | BEST-PRACTICE | advisory | Cookie samesite set to "strict" instead of "lax" |
| SEC-008 | LOW | BEST-PRACTICE | advisory | Data service layer missing defense-in-depth access control |

### Phase 5: Docker

| ID | Severity | Type | Classification | Title |
|----|----------|------|----------------|-------|
| INF-01 | MEDIUM | BEST-PRACTICE | advisory | Base images use floating tags (not pinned to SHA256 digest) |
| INF-02 | HIGH | SPEC-DEVIATION | mandatory | `.env` with weak credentials overrides production compose's `${ENV:-production}` default |
| INF-03 | MEDIUM | BEST-PRACTICE | advisory | `rq-worker` and `nginx` services lack health checks |
| INF-04 | LOW | BEST-PRACTICE | advisory | `AUTO_MIGRATE=true` redundant with dedicated `migrate` service |
| INF-05 | MEDIUM | BEST-PRACTICE | advisory | Redis runs with no config file, no auth, dangerous commands enabled |
| INF-06 | MEDIUM | BEST-PRACTICE | advisory | PostgreSQL uses `trust` auth for local connections |
| INF-07 | LOW | BEST-PRACTICE | advisory | Production image is 706MB — `plotly` as backend dependency may be unnecessary |
| INF-08 | LOW | BEST-PRACTICE | advisory | Production compose lacks explicit network configuration |

### Phase 6: Testing

| ID | Severity | Type | Classification | Title |
|----|----------|------|----------------|-------|
| TST-001 | CRITICAL | RUNTIME-ERROR | mandatory | 233/603 backend tests fail — DB port 5432 not exposed to host |
| TST-003 | LOW | BEST-PRACTICE | advisory | `test_upload_api.py.bak` committed alongside real file |
| TST-004 | HIGH | SPEC-DEVIATION | mandatory | Frontend coverage critically sparse — 82 tests/6 files, zero coverage for critical components |
| TST-005 | MEDIUM | BEST-PRACTICE | advisory | `baseline_data` fixture is a no-op placeholder used by zero tests |
| TST-006 | HIGH | SPEC-DEVIATION | mandatory | Test database not isolated — targets dev instance instead of test-db on port 5433 |
| TST-007 | MEDIUM | BEST-PRACTICE | advisory | Auto-mock Redis fixture disables rate limiting in all tests |

### Phase 7: Data Processing

| ID | Severity | Type | Classification | Title |
|----|----------|------|----------------|-------|
| DP-001 | HIGH | RUNTIME-ERROR | mandatory | No cumulative size check during file streaming when `file.size` is None |
| DP-003 | HIGH | RUNTIME-ERROR | mandatory | MIME type validation trusts client `Content-Type` header (spoofable) |
| DP-004 | HIGH | RUNTIME-ERROR | mandatory | `_update_processing_log_status` silently swallows all exceptions |
| DP-005 | MEDIUM | BEST-PRACTICE | advisory | In-memory task queue loses all pending tasks on restart |
| DP-006 | MEDIUM | RUNTIME-ERROR | advisory | No explicit `FileNotFoundError` handling in CSV worker |
| DP-007 | MEDIUM | BEST-PRACTICE | advisory | M×N aggregate storage inflates storage for multi-graph dashboards |
| DP-008 | HIGH | RUNTIME-ERROR | mandatory | YoY calculation produces `inf` values not handled by `fill_nan` |
| DP-009 | MEDIUM | DOC-UPDATE | advisory | APPEND mode semantics undocumented |

### Phase 8: Deployment & Configuration

| ID | Severity | Type | Classification | Title |
|----|----------|------|----------------|-------|
| DC-001 | HIGH | SPEC-DEVIATION | mandatory | `.env` files with weak credentials exist in working tree |
| DC-002 | MEDIUM | SPEC-DEVIATION | advisory | `RATE_LIMITER_FAIL_CLOSED` defaults inconsistent between code and Docker Compose |
| DC-003 | LOW | BEST-PRACTICE | advisory | `DEBUG=false` in development environment |
| DC-005 | MEDIUM | SPEC-DEVIATION | advisory | `CORS_ORIGINS` defaults to localhost in production compose |
| DC-006 | LOW | BEST-PRACTICE | advisory | `rq-worker` in override lacks explicit `AUTO_MIGRATE: "false"` |
| DC-009 | LOW | BEST-PRACTICE | advisory | `JWT__ACCESS_TOKEN_EXPIRE_MINUTES` differs between `.env` (30) and `app.yaml` (15) |
| DC-010 | LOW | BEST-PRACTICE | advisory | `app.yaml` contains development-only `cors_origins` values |

### Phase 9: Integration

| ID | Severity | Type | Classification | Title |
|----|----------|------|----------------|-------|
| INT-001 | CRITICAL | RUNTIME-ERROR | mandatory | `POST /{dashboard_id}/process` orphaned endpoint with broken `task_id` query param |
| INT-002 | CRITICAL | RUNTIME-ERROR | mandatory | `/api/v1/filters` CRUD endpoints orphaned — no frontend consumer |
| INT-004 | LOW | SPEC-DEVIATION | advisory | `change_password` returns raw dict without `response_model` |
| INT-005 | HIGH | RUNTIME-ERROR | mandatory | `ProcessingStatusResponse` field mismatch: `finished_at` vs `completed_at` |
| INT-006 | MEDIUM | SPEC-DEVIATION | advisory | `DashboardSummary.permission` required in frontend but absent from backend |
| INT-008 | MEDIUM | BEST-PRACTICE | advisory | Inconsistent error response formats across endpoints |
| INT-009 | MEDIUM | RUNTIME-ERROR | mandatory | `login` callback doesn't check `force_password_change` |
| INT-010 | LOW | SPEC-DEVIATION | advisory | `CreateDashboardRequest` lacks `config` field |

---

## 4. Findings by Severity

### CRITICAL (must fix immediately)

| ID | Title | Affected Modules |
|----|-------|----------------|
| TST-001 | 233/603 backend tests fail — DB port 5432 not exposed to host | `tests/conftest.py`, `docker/docker-compose.yml` |
| INT-001 | `POST /{dashboard_id}/process` orphaned endpoint with broken `task_id` query param | `src/mkobi/api/routes/upload.py` |
| INT-002 | `/api/v1/filters` CRUD endpoints orphaned — no frontend consumer | `src/mkobi/api/routes/filters.py`, `app.py` |

### HIGH (fix before production)

| ID | Title | Affected Modules |
|----|-------|----------------|
| BE-001 | Dual sub-router mounting pattern — fragile architecture | `src/mkobi/api/app.py`, `src/mkobi/api/routes/dashboards.py` |
| BE-002 | `data.py` bypasses repository layer with raw `select(Graph)` | `src/mkobi/api/routes/data.py` |
| BE-003 | `PermissionError` not imported — 500 instead of 403 | `src/mkobi/api/routes/data.py` |
| FE-005 | `getToken()` outside React render cycle — stale `enabled` state | `frontend/src/features/dashboards/api/dashboardApi.ts` |
| SEC-001 | No token revocation mechanism | `src/mkobi/core/security.py`, `src/mkobi/api/routes/auth.py` |
| SEC-002 | Weak default secrets in Docker configs | `docker/.env`, `docker/docker-compose.override.yml` |
| SEC-003 | Dashboard update/delete lacks resource-level access control | `src/mkobi/api/routes/dashboards_crud.py` |
| INF-02 | `.env` overrides production mode in Docker Compose | `.env`, `docker/docker-compose.yml` |
| TST-004 | Frontend coverage critically sparse (82 tests/6 files) | `frontend/src/` |
| TST-006 | Test database not isolated — targets dev instance | `tests/conftest.py`, `docker/docker-compose.test.yml` |
| DP-001 | No cumulative size check during file streaming | `src/mkobi/api/routes/upload.py` |
| DP-003 | MIME type validation trusts spoofable `Content-Type` header | `src/mkobi/services/file_processing.py` |
| DP-004 | `_update_processing_log_status` silently swallows exceptions | `src/mkobi/services/data_worker.py` |
| DP-008 | YoY calculation produces `inf` values breaking JSON serialization | `src/mkobi/data/aggregate_transforms.py` |
| DC-001 | `.env` files with weak credentials in working tree | `.env` |
| INT-005 | `ProcessingStatusResponse` field mismatch (`finished_at` vs `completed_at`) | `frontend/src/features/dashboards/types.ts`, `src/mkobi/models/processing.py` |

### MEDIUM (technical debt)

| ID | Title | Affected Modules |
|----|-------|----------------|
| BE-004 | Custom `PermissionError` shadows Python builtin | `src/mkobi/core/permissions.py` |
| FE-008 | Incomplete admin features | `frontend/src/features/admin/` |
| FE-009 | `confirm_password` not validated server-side | `src/mkobi/models/auth.py` |
| DB-03 | No index on `dashboards.layout_id` FK | `src/mkobi/db/models/dashboards.py` |
| DB-04 | No index on `dashboards.created_by` FK | `src/mkobi/db/models/dashboards.py` |
| DB-05 | No index on `registration_requests.reviewed_by` FK | `src/mkobi/db/models/registration.py` |
| DB-06 | Redundant duplicate index on `dashboard_filters` | `alembic/versions/` |
| DB-07 | `force_password_change` column missing from test DB | `docker/docker-compose.test.yml` |
| DB-08 | `processing_logs` missing composite index | `src/mkobi/db/models/processing.py` |
| DB-09 | `create_dashboard` partial-write risk | `src/mkobi/services/dashboard_service.py` |
| SEC-004 | Plaintext temp passwords in HTTP responses | `src/mkobi/services/auth_service.py` |
| SEC-005 | Missing HSTS and CSP headers | `src/mkobi/api/app.py`, `docker/nginx.conf` |
| SEC-006 | JWT secret key entropy validation missing | `src/mkobi/core/config.py` |
| INF-01 | Base images use floating tags | `docker/Dockerfile` |
| INF-03 | `rq-worker` and `nginx` lack health checks | `docker/docker-compose.yml` |
| INF-05 | Redis runs without authentication | `docker/docker-compose.yml` |
| INF-06 | PostgreSQL uses `trust` auth | `docker/docker-compose.yml` |
| TST-005 | `baseline_data` fixture is a no-op placeholder | `tests/conftest.py` |
| TST-007 | Auto-mock Redis disables rate limiting in all tests | `tests/conftest.py` |
| DP-005 | In-memory task queue loses tasks on restart | `src/mkobi/workers/data_worker.py` |
| DP-006 | No explicit `FileNotFoundError` in CSV worker | `src/mkobi/workers/data_worker.py` |
| DP-007 | M×N aggregate storage explosion | `src/mkobi/services/manager.py` |
| DP-009 | APPEND mode semantics undocumented | `docs/03-processing/processing-api.md` |
| DC-002 | `RATE_LIMITER_FAIL_CLOSED` default inconsistency | `src/mkobi/core/config.py`, `docker/docker-compose.override.yml` |
| DC-005 | `CORS_ORIGINS` defaults to localhost in production compose | `docker/docker-compose.yml` |
| INT-006 | `DashboardSummary.permission` missing from backend | `src/mkobi/api/routes/dashboards.py` |
| INT-008 | Inconsistent error response formats | `src/mkobi/api/routes/`, `frontend/src/shared/api/axiosInstance.ts` |
| INT-009 | `login` callback doesn't check `force_password_change` | `frontend/src/features/auth/hooks/useAuth.ts` |

### LOW (nice to have)

| ID | Title | Affected Modules |
|----|-------|----------------|
| BE-005 | Deprecated `get_session` export | `src/mkobi/api/deps.py` |
| BE-006 | Dual logging pattern | 62 modules across `src/mkobi/` |
| BE-007 | Dead `decorators.py` module | `src/mkobi/utils/decorators.py` |
| FE-001 | `console.error` in `UserManagement.tsx` | `frontend/src/features/admin/UserManagement.tsx` |
| FE-006 | Duplicate `getProfile()` | `frontend/src/features/auth/api/authApi.ts`, `frontend/src/features/users/api/userApi.ts` |
| FE-DEAD-CODE | 6 dead unused components | `frontend/src/features/dashboards/ui/charts/`, `frontend/src/shared/components/` |
| SEC-007 | Cookie samesite "strict" instead of "lax" | `src/mkobi/core/security.py` |
| SEC-008 | Data service missing defense-in-depth access control | `src/mkobi/services/data_service.py` |
| INF-04 | `AUTO_MIGRATE=true` redundant with migrate service | `docker/docker-compose.yml` |
| INF-07 | Production image 706MB — optimization possible | `docker/Dockerfile` |
| INF-08 | Production compose lacks explicit network config | `docker/docker-compose.yml` |
| TST-003 | `test_upload_api.py.bak` committed | `tests/test_upload_api.py.bak` |
| DC-003 | `DEBUG=false` in development | `docker/docker-compose.override.yml` |
| DC-006 | `rq-worker` lacks explicit `AUTO_MIGRATE: "false"` | `docker/docker-compose.override.yml` |
| DC-009 | JWT expiry mismatch between `.env` and `app.yaml` | `.env`, `app.yaml` |
| DC-010 | `app.yaml` has development CORS origins | `app.yaml` |
| INT-004 | `change_password` returns raw dict | `src/mkobi/api/routes/auth.py` |
| INT-010 | `CreateDashboardRequest` lacks `config` field | `frontend/src/features/admin/api/adminApi.ts` |

---

## 5. Cross-Cutting Concerns (from Phase 9: Integration)

### API Contract Alignment
- `ProcessingStatusResponse` has field name mismatch (`finished_at` vs `completed_at`) and missing fields (`progress`, `task_id`, `filename`, `dashboard_id`)
- `DashboardSummary.permission` required in frontend but not returned by backend
- `change_password` returns raw dict without `response_model`; frontend declares `Promise<void>`
- `CreateDashboardRequest` lacks `config` field that backend already accepts
- Inconsistent error response formats across endpoints; frontend ignores structured error bodies

### Authentication Flow
- No server-side token revocation after logout — refresh tokens remain valid for 7 days
- `login()` callback doesn't check `force_password_change`, allowing bypass of forced password change
- Cookie samesite set to "strict" may break cross-origin navigation

### Data Flow Consistency
- APPEND mode semantics undocumented — aggregates calculated from new file only, not combined dataset
- M×N aggregate storage pattern inflates data for multi-graph dashboards
- YoY `inf` values bypass `fill_nan()` and break JSON serialization

### Database-Model Alignment
- Migration chain has a branch causing `alembic check` false drift
- ORM `unique=True` vs raw `CREATE UNIQUE INDEX` mismatch across 5 tables
- Test database schema out of sync with production (missing `force_password_change` column)

### Type Safety Alignment
- Frontend `getToken()` coupling to global module state instead of React context
- Dead type exports from unused components create confusion

### Docker Deployment Wiring
- `.env` development values override production compose defaults
- Test infrastructure not configured for host-native execution (port exposure, test DB isolation)
- Redis and PostgreSQL lack authentication in container environment

---

## 6. Fix Priority

1. **CRITICAL** — 3 issues must be fixed before any deployment:
   - TST-001: Fix Docker port exposure for test execution
   - INT-001: Remove or fix orphaned `/process` endpoint
   - INT-002: Remove orphaned `/api/v1/filters` endpoints or wire frontend

2. **HIGH** — 16 issues must be fixed before production release:
   - BE-001 through BE-003: Backend architecture and permission handling
   - FE-005: Auth token staleness in data fetching
   - SEC-001 through SEC-003: Token revocation, weak secrets, access control
   - INF-02: Docker production mode override
   - TST-004, TST-006: Test coverage and isolation
   - DP-001, DP-003, DP-004, DP-008: Data processing pipeline vulnerabilities
   - DC-001: Remove `.env` from working tree
   - INT-005: ProcessingStatusResponse type alignment

3. **MEDIUM** — 27 technical debt items to address in next iteration

4. **LOW** — 16 improvements for future enhancement

---

## Merge Strategy

**Source Files:**
- `.ai/audit/01-backend/findings.md` → validated: 7 findings (1 reclassified)
- `.ai/audit/02-frontend/findings.md` → validated: 7 findings (3 rejected, 2 merged→1)
- `.ai/audit/03-database/findings.md` → validated: 9 findings (1 rejected, 1 reclassified)
- `.ai/audit/04-security/findings.md` → validated: 8 findings (1 reclassified)
- `.ai/audit/05-docker/findings.md` → validated: 8 findings (1 reclassified)
- `.ai/audit/06-tests/findings.md` → validated: 6 findings (1 rejected)
- `.ai/audit/07-data-processing/findings.md` → validated: 8 findings (1 rejected, 1 reclassified, 1 merged)
- `.ai/audit/08-deployment-config/findings.md` → validated: 7 findings (3 rejected, 1 reclassified)
- `.ai/audit/90-integration/findings.md` → validated: 8 findings (1 rejected, 1 merged into SEC-001)

**Process:**
1. All 9 phase audits validated before final report generation
2. Each finding extracted and categorized by severity
3. Severity counts tallied across all phases
4. Cross-cutting concerns consolidated from Phase 9
5. Priority ordering: CRITICAL → HIGH → MEDIUM → LOW
6. Rejected findings cleaned from file before merge
