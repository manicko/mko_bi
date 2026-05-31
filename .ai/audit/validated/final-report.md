# Audit Report — mkobi BI Dashboard

**Generated:** 2026-05-31
**Phases Completed:** 9/9
**Validated Findings:** 20 total

---

## 1. Executive Summary

| Metric | Value |
|--------|-------|
| **Overall Quality Score** | 6/10 |
| **Critical Findings** | 1 |
| **Production Readiness** | PARTIALLY_READY |

**Summary:**
The mkobi BI Dashboard demonstrates a well-structured Clean Architecture backend with Feature-Sliced Design frontend. However, critical security vulnerabilities exist in the form of missing access control on graph endpoints (BE-005, SEC-003) and an async correctness issue with RateLimiter blocking the event loop (BE-001). Several API contract mismatches between frontend and backend create runtime failures (FE-006, INT-001). While the codebase follows project specifications and best practices in many areas, the critical findings require immediate attention before production deployment. Test coverage is critically low on the frontend (TST-003), and JWT token revocation is not implemented (SEC-002).

---

## 2. Architecture Summary

### Backend (Clean Architecture)

| Assessment Area | Score (1-10) | Notes |
|-----------------|--------------|-------|
| Architecture Boundaries | 7 | Clean separation but TaskQueue is dead code creating confusion |
| Dependency Direction | 8 | Correct inward direction, though some sync/async mixing |
| Layer Separation | 8 | Clear API/Service/Repository boundaries |
| Maintainability | 7 | Some dead code and inconsistent patterns reduce clarity |

**Strengths:**
- Clean Architecture with clear API/Service/Repository separation
- Async-first design with proper async/await patterns
- Pydantic v2 + StrEnum used consistently for models and constants

**Weaknesses:**
- Dead code in TaskQueue creates false architectural expectations
- RateLimiter sync/async inconsistency in DataService
- Missing access control on global endpoints

### Frontend (Feature-Sliced Design)

| Assessment Area | Score (1-10) | Notes |
|-----------------|--------------|-------|
| Feature Modularity | 6 | Good feature separation but some unused exports |
| Layer Separation | 7 | API/components correctly separated |
| Maintainability | 5 | Very low test coverage (only 3 test files) |
| Consistency | 6 | API contract issues with backend |

**Strengths:**
- Feature-sliced structure with clear module organization
- TanStack Query for data fetching, React Hook Form + Zod for forms

**Weaknesses:**
- Critically low test coverage (3 test files for entire application)
- Multiple unused API functions and component exports
- Hardcoded UUID mapping to database seed values

---

## 3. Findings by Phase

### Phase 1: Backend Architecture (2 mandatory, 3 advisory)

**Mandatory:**
- **BE-001:** Sync RateLimiter in async DataService breaks event loop — CRITICAL
- **BE-005:** Global graph endpoints lack dashboard access verification — MEDIUM

**Advisory:**
- **BE-003:** ProcessingStatus enum has redundant SUCCESS and COMPLETED values — LOW
- **BE-004:** In-memory TaskQueue not integrated with background workers — MEDIUM
- **BE-008:** Exception handlers in app.py don't use standard error format — LOW

### Phase 2: Frontend Architecture (1 mandatory, 4 advisory)

**Rejected:** FE-001 (API contract issue requires coordinated backend+frontend decision)

**Mandatory:**
- **FE-006:** API Contract Mismatch - Missing dashboard_id in grantDashboardAccess Body — CRITICAL

**Advisory:**
- **FE-002:** Unused getFilter API Function — LOW
- **FE-003:** Unused Chart Component Exports — LOW
- **FE-004:** Hardcoded Layout UUID Mapping in Admin API — MEDIUM
- **FE-005:** Missing Accessibility Attributes in TableChart — MEDIUM

### Phase 3: Database (2 mandatory, 1 doc update)

**Mandatory:**
- **DB-001:** Broken Trigger in Initial Migration for Non-Existent Column — CRITICAL (already mitigated)
- **DB-003:** Inconsistent Database Role Usage in Test Configuration — MEDIUM

**Advisory:**
- **DB-002:** Missing GIN Index on aggregated_data.metrics Column — DOC-UPDATE (premature optimization)

### Phase 4: Security (3 mandatory, 3 advisory)

**Mandatory:**
- **SEC-002:** JWT tokens not revoked when users are deactivated — HIGH
- **SEC-003:** Graph endpoints lack dashboard access verification — HIGH
- **SEC-004:** Layout endpoints lack dashboard access verification — HIGH

**Advisory:**
- **SEC-005:** Rate limiting silently disabled during Redis outages — MEDIUM
- **SEC-006:** Missing security headers in the FastAPI application layer — MEDIUM
- **SEC-007:** Upload endpoint missing explicit dashboard existence check — MEDIUM

### Phase 5: Infrastructure & Docker (0 mandatory, 0 advisory)

All 4 findings rejected as overengineered or already mitigated:
- INF-001: Missing explicit networks — default Docker network sufficient
- INF-002: Floating versions — mitigated by lockfile
- INF-005: Development secrets — .env is gitignored
- INF-006: Volume driver — local is default

### Phase 6: Testing (2 mandatory, 5 advisory)

**Mandatory:**
- **TST-002:** Global graph endpoints lack dashboard access verification in tests — HIGH
- **TST-003:** Frontend has critically low test coverage (only 3 test files) — HIGH

**Advisory:**
- **TST-004:** No coverage threshold in frontend vite.config.ts — MEDIUM
- **TST-005:** Tautological mock assertions in tests — LOW
- **TST-006:** Missing refresh token edge case tests — MEDIUM
- **TST-007:** MockRedis has no-op methods — LOW
- **TST-008:** Missing edge case tests for data transformations — MEDIUM

### Phase 7: Data Processing (4 mandatory, 2 advisory)

**Mandatory:**
- **DP-001:** Transaction boundary issue — file move before DB commit — MEDIUM
- **DP-002:** Processing configuration not wired through upload pipeline — HIGH
- **DP-003:** Missing transaction wrapper in test mode for _store_aggregates — MEDIUM
- **DP-004:** In-memory TaskQueue not persistent — MEDIUM

**Advisory:**
- **DP-005:** Floating-point precision in share calculations — LOW
- **DP-006:** Two divergent processing pipelines with inconsistent terminal states — MEDIUM (bigger issue than reported)

### Phase 8: Deployment & Configuration (0 mandatory, 1 advisory)

**Advisory:**
- **DC-005:** Database password validation inconsistency — MEDIUM (reclassified from HIGH)

### Phase 9: Integration (2 mandatory, 2 advisory)

**Mandatory:**
- **INT-001:** /data/aggregated missing graph_id parameter — CRITICAL (requires coordinated fix)
- **INT-003:** Upload response format mismatch — MEDIUM
- **INT-005:** Frontend createUser uses /users without trailing slash — HIGH (reclassified)

**Advisory:**
- **INT-004:** Unused process endpoint — LOW

---

## 4. Findings by Severity

### CRITICAL (must fix immediately)

| ID | Title | Affected Modules |
|----|-------|----------------|
| BE-001 | Sync RateLimiter in async DataService breaks event loop | src/mkobi/services/data_service.py |
| FE-006 | Missing dashboard_id in grantDashboardAccess request body | frontend/src/features/admin/api/adminApi.ts, src/mkobi/api/routes/dashboards_access.py |

### HIGH (fix before production)

| ID | Title | Affected Modules |
|----|-------|----------------|
| SEC-002 | JWT tokens not revoked when users are deactivated | src/mkobi/core/security.py, src/mkobi/api/deps.py |
| SEC-003 | Graph endpoints lack dashboard access verification | src/mkobi/api/routes/graphs.py |
| SEC-004 | Layout endpoints lack dashboard access verification | src/mkobi/api/routes/layouts.py |
| TST-002 | Missing cross-dashboard access tests for graph endpoints | tests/test_graphs.py |
| TST-003 | Critically low frontend test coverage | frontend/src/ (all features) |
| INT-001 | /data/aggregated missing graph_id parameter | frontend/src/features/dashboards/api/dashboardApi.ts, src/mkobi/api/routes/data.py |
| INT-005 | Frontend createUser posts to /users without trailing slash | frontend/src/features/admin/api/adminApi.ts |

### MEDIUM (technical debt)

| ID | Title | Affected Modules |
|----|-------|----------------|
| BE-005 | Global graph endpoints lack dashboard access verification | src/mkobi/api/routes/graphs.py |
| BE-004 | In-memory TaskQueue not integrated with background workers | src/mkobi/core/task_queue.py |
| BE-008 | Exception handlers don't use standard error format | src/mkobi/app.py |
| DB-003 | Inconsistent database role in test configuration | docker-compose.test.yml |
| DC-005 | Database URL password validation inconsistency | src/mkobi/core/config.py |
| DP-001 | Transaction boundary - file move before commit | src/mkobi/services/file_processing.py |
| DP-002 | Processing configuration not wired through pipeline | src/mkobi/services/data_service.py, src/mkobi/services/file_processing.py |
| DP-003 | Missing transaction wrapper in test mode | src/mkobi/data/processing/data_worker.py |
| DP-006 | Two divergent pipelines with different terminal states | src/mkobi/data/processing/, src/mkobi/db/models/processing_logs.py |
| INT-003 | Upload response format mismatch | src/mkobi/api/routes/upload.py |

### LOW (nice to have)

| ID | Title | Affected Modules |
|----|-------|----------------|
| BE-003 | ProcessingStatus enum has redundant SUCCESS/COMPLETED | src/mkobi/models/enums.py |
| FE-002 | Unused getFilter API function | frontend/src/features/dashboards/api/dashboardApi.ts |
| FE-003 | Unused chart component exports | frontend/src/features/dashboards/ui/charts/index.ts |
| FE-004 | Hardcoded layout UUID mapping | frontend/src/features/admin/api/adminApi.ts |
| FE-005 | Missing accessibility attributes in TableChart | frontend/src/features/dashboards/ui/charts/TableChart.tsx |
| TST-005 | Tautological mock assertions | tests/test_upload_api.py |
| TST-007 | MockRedis no-op methods | tests/conftest.py |

---

## 5. Cross-Cutting Concerns

### API Contract Alignment

- **INT-001/FE-001:** The `/data/aggregated` endpoint requires `graph_id` but frontend only sends `dashboard_id`. Backend docstring incorrectly states "all dashboard charts" while implementation returns one graph. Fix requires coordinated decision.
- **INT-003:** Upload endpoint returns `{"message", "processing_log_id"}` but frontend `UploadResponse` expects structured fields. Response model mismatch.
- **INT-005:** Frontend `createUser` posts to `/users` but backend route uses `prefix="/users"` with `redirect_slashes=False`, causing 404.

### Authentication Flow

- **SEC-002:** `is_active` field exists in user model but is never checked during JWT validation, allowing deactivated users to remain authenticated.
- **TST-006:** Refresh token tests only cover happy path; missing tests for expiration, invalid signatures, token rotation, and revocation.

### Data Flow Consistency

- **DP-002:** Processing configuration exists in `processing_configs` table but is never fetched in primary upload→process flow. `DataPipeline` in registry.py uses it, creating divergent code paths.
- **DP-001:** File moved before database commit creates potential for orphaned files on failure.

### Database-Model Alignment

- **DP-006:** Two processing pipelines use different terminal states (`SUCCESS` in data_worker.py, `COMPLETED` in registry.py) with no semantic distinction.

### Type Safety Alignment

- All cross-cutting type issues are in API contracts between frontend and backend, requiring TypeScript/Python alignment.

### Docker Deployment Wiring

- All infra findings rejected; Docker configuration is appropriate for project scale.

---

## 6. Fix Priority

1. **CRITICAL (2):** BE-001, FE-006 — Must fix before any deployment
2. **HIGH (7):** SEC-002, SEC-003, SEC-004, TST-002, TST-003, INT-001, INT-005 — Must fix before production release
3. **MEDIUM (9):** BE-005, BE-004, BE-008, DB-003, DC-005, DP-001, DP-002, DP-003, DP-006, INT-003 — Technical debt for next iteration
4. **LOW (4):** BE-003, FE-002, FE-003, FE-004, FE-005, TST-005, TST-007 — Nice-to-have improvements

---

## 7. Cross-Phase Dependencies

### Fix Ordering Required

**DB-003 must execute BEFORE BE-005:** Tests running with `postgres` superuser bypass privilege checks. Switching to `mkobi_app` role first ensures access control tests properly validate the BE-005 fix.

### Duplicate Issues (Keep Separate)

**TST-002 and SEC-003:** Both address missing dashboard access on graph endpoints — SEC-003 fixes production code, TST-002 adds test coverage. Complementary, not conflicting.

**INT-001 and FE-001:** Merged — same root cause but FE-001 was rejected. INT-001 retained as integration finding.

---

## 8. Source Files

- `.ai/audit/99-validation/01-backend-validated.md`
- `.ai/audit/99-validation/02-frontend-validated.md`
- `.ai/audit/99-validation/03-database-validated.md`
- `.ai/audit/99-validation/04-security-validated.md`
- `.ai/audit/99-validation/05-docker-validated.md`
- `.ai/audit/99-validation/06-tests-validated.md`
- `.ai/audit/99-validation/07-data-processing-validated.md`
- `.ai/audit/99-validation/08-deployment-config-validated.md`
- `.ai/audit/99-validation/90-integration-validated.md`