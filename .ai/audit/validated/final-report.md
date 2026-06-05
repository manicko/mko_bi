# Audit Report — mkobi BI Dashboard

**Generated:** 2026-06-05
**Phases Completed:** 8/8 (Phases 1, 2, 3, 6, 7, 8, 90 + validation)
**Validated Findings:** 18 total (after merges and rejections)

**- Total LOW advisory: 13**

---

## 1. Executive Summary

| Metric | Value |
|--------|-------|
| **Overall Quality Score** | 7/10 |
| **Critical Findings** | 0 |
| **High Findings** | 2 |
| **Production Readiness** | PARTIALLY_READY |

**Summary:** The mkobi BI Dashboard demonstrates solid architectural discipline with Clean Architecture on the backend and Feature-Sliced Design on the frontend. Type safety is generally well-maintained, and the codebase follows project conventions (StrEnum for constants, English-only code, RFC 7807 error format). However, two HIGH-severity security issues were identified: unsafe `eval()` usage in computed field expressions and weak default admin credentials. Additionally, test coverage is critically low (45%), and several test-related issues need addressing. The system can be production-ready once mandatory fixes are implemented.

---

## 2. Architecture Summary

### Backend (Clean Architecture)

| Assessment Area | Score (1-10) | Notes |
|-----------------|--------------|-------|
| Architecture Boundaries | 8 | Clean separation: API → Service → Repository. No layer bleeding detected |
| Dependency Direction | 8 | Dependencies point inward correctly. DI pattern followed |
| Layer Separation | 8 | Transport layer contains HTTP logic only, no business logic leakage |
| Maintainability | 7 | Some test-only transaction handling inconsistencies, but code is well-structured |

**Strengths:**
- RFC 7807 error handling properly implemented via `AppException`
- All constants use `StrEnum` as required
- No `print()` statements or raw SQL f-strings found
- Security measures in place (JWT + bcrypt, rate limiting, MIME detection)

**Weaknesses:**
- Missing Pydantic response model on filter-values endpoint
- Weak admin password default in config
- Unsafe eval() in computed field expressions

### Frontend (Feature-Sliced Design)

| Assessment Area | Score (1-10) | Notes |
|-----------------|--------------|-------|
| Feature Modularity | 8 | Well-organized features with clear boundaries |
| Layer Separation | 7 | Some unnecessary CJS/ESM type assertions, but structure is clean |
| Maintainability | 7 | Dead code (unused chart components) and some any-type usage |
| Consistency | 7 | Russian error messages in some places, English in others |

**Strengths:**
- TanStack Query for server state management
- React Hook Form + Zod for form validation
- Protected routes with role-based access control
- Memory-first token storage for security

**Weaknesses:**
- Lint errors in ChartRenderer (potential data corruption)
- Hardcoded status strings instead of enum values
- Unused chart components (BarChart, LineChart, PieChart, TableChart)
- Russian error fallback messages in English codebase

---

## 3. Validated Findings by Phase

### Phase 1: Backend Architecture
*(Source: `.ai/audit/01-backend/findings.md`)*

| ID | Title | Severity | Classification |
|----|-------|----------|----------------|
| BE-001 | Missing response model on filter values endpoint | MEDIUM | advisory |
| BE-002 | Test failure - JWT secret validation expectation misaligned with .env loading | MEDIUM | **mandatory** |
| BE-003 | Test failure - file extension validation order | LOW | advisory |

### Phase 2: Frontend Architecture
*(Source: `.ai/audit/02-frontend/findings.md`)*

| ID | Title | Severity | Classification |
|----|-------|----------|----------------|
| FE-001 | Russian language in production error handler | MEDIUM | advisory |
| FE-002 | Russian language in shared error messages (intentional, needs doc) | MEDIUM | DOC-UPDATE (reclassified) |
| FE-003 | Lint errors in ChartRenderer component | MEDIUM | **mandatory** |
| FE-004 | Unused chart components in codebase | LOW | advisory |
| FE-005 | Hardcoded status string instead of enum | MEDIUM | **mandatory** |
| FE-006 | Any type usage in PlotlyComponent wrapper | LOW | advisory |
| FE-007 | Missing form field labels | LOW | REJECTED |

### Phase 3: Database
*(Source: `.ai/audit/03-database/findings.md`)*

| ID | Title | Severity | Classification |
|----|-------|----------|----------------|
| DB-001 | ProcessingStatus ENUM schema drift (extra "success" value) | MEDIUM | advisory |

### Phase 6: Testing
*(Source: `.ai/audit/06-tests/findings.md`)*

| ID | Title | Severity | Classification |
|----|-------|----------|----------------|
| TST-001 | Test expects None JWT secret but .env provides default | HIGH | **mandatory** |
| TST-002 | Test assertion mismatch - file extension validation | MEDIUM | BEST-PRACTICE (reclassified) |
| TST-003 | Tautological test - assert True only | MEDIUM | advisory |
| TST-004 | Mock-heavy tests | MEDIUM | REJECTED (overstated) |
| TST-005 | Mock-heavy unit tests in test_auth_service.py | MEDIUM | advisory |
| TST-006 | Frontend tests have act() warnings | MEDIUM | advisory |
| TST-007 | Rate limiter tests lack endpoint integration | LOW | advisory |
| TST-008 | Coverage 45% (critical) | HIGH | advisory |

### Phase 7: Data Processing
*(Source: `.ai/audit/07-data-processing/findings.md`)*

| ID | Title | Severity | Classification |
|----|-------|----------|----------------|
| DP-001 | Missing transaction wrapper in test mode | CRITICAL → MEDIUM | advisory (reclassified) |
| DP-002 | Incomplete transaction boundary (merged into DP-001) | CRITICAL | merged |
| DP-003 | Race condition in task state transition | MEDIUM | REJECTED |
| DP-004 | Empty DataFrame handling | MEDIUM | REJECTED |
| DP-005 | Cleanup function missing commit | MEDIUM | advisory (reclassified) |
| DP-006 | Silent graph skipping on missing columns | MEDIUM | advisory |
| DP-007 | Potential unbounded memory usage | MEDIUM | advisory |
| DP-008 | Unsafe eval() in computed field expressions | HIGH | **mandatory** |

### Phase 8: Deployment & Configuration
*(Source: `.ai/audit/08-deployment-config/findings.md`)*

| ID | Title | Severity | Classification |
|----|-------|----------|----------------|
| DC-001 | Production .env.production template missing values | HIGH → LOW | advisory (reclassified) |
| DC-002 | Admin password default value is weak | MEDIUM | **mandatory** |
| DC-003 | Missing production debug mode validation | MEDIUM | **mandatory** |
| DC-004 | Unauthenticated /health/detailed endpoint | HIGH → LOW | advisory (downgraded) |
| DC-005 | Test compose fallback credentials | LOW | advisory |

### Phase 90: Integration
*(Source: `.ai/audit/90-integration/findings.md`)*

| ID | Title | Severity | Classification |
|----|-------|----------|----------------|
| INT-001 | ProcessingResult type mismatch | HIGH | REJECTED |
| INT-002 | UploadResponse status field mismatch | MEDIUM | REJECTED |
| INT-003 | ProcessingStatus enum inconsistency | MEDIUM | merged into DB-001 |
| INT-004 | RegistrationRequestItem status mismatch | MEDIUM | REJECTED |
| INT-005 | Russian fallback in errorHandler | LOW | merged into FE-001 |

---

## 4. Findings by Severity (Final Validated)

### CRITICAL (must fix immediately)
None after validation. The original CRITICAL findings in Phase 7 were reclassified to MEDIUM as they relate to test-mode transaction handling which is a deliberate design choice.

### HIGH (fix before production)
| ID | Title | Affected Modules |
|----|-------|----------------|
| DP-008 | Unsafe eval() in computed field expressions allows code injection | src/mkobi/data/processing/filter_transforms.py |
| TST-001 | Test expects None JWT secret but .env provides default (test broken) | tests/test_config.py, .env, src/mkobi/config.py |

**Total HIGH: 2 mandatory, 0 advisory**

### MEDIUM (mandatory fixes)
| ID | Title | Affected Modules |
|----|-------|----------------|
| DC-002 | Admin password default value is weak | src/mkobi/config.py |
| DC-003 | Missing production debug mode validation | src/mkobi/config.py, src/mkobi/app.py |
| FE-003 | Lint errors in ChartRenderer component | frontend/src/features/dashboards/ui/charts/ChartRenderer.tsx |
| FE-005 | Hardcoded status strings instead of enum | frontend/src/features/upload/api/uploadApi.ts |
| BE-002 | JWT secret validation test expectation misaligned | tests/test_config.py, .env, src/mkobi/config.py |

**Total MEDIUM mandatory: 5**

### MEDIUM (advisory/reclassified)
| ID | Title | Affected Modules |
|----|-------|----------------|
| TST-008 | Coverage failure - 45% below required 80% | entire codebase |

**Total MEDIUM advisory: 1**

### LOW (advisory/technical debt)
| ID | Title | Affected Modules |
|----|-------|----------------|
| BE-003 | File extension validation order (platform-specific) | tests/test_data_service.py |
| DC-001 | .env.production template inconsistency | docker/.env.production |
| DC-004 | /health/detailed public by design | src/mkobi/app.py |
| DC-005 | Test compose fallback credentials | docker/docker-compose.test.yml |
| DP-001 | Test mode transaction consistency | src/mkobi/workers/data_worker.py |
| DP-005 | Cleanup function transaction handling | src/mkobi/workers/data_worker.py |
| DP-006 | Silent graph skipping feedback | src/mkobi/services/aggregation_service.py |
| DP-007 | Lazy CSV loading memory concern | src/mkobi/data/loaders/loader.py |
| FE-002 | Russian error messages (intentional, doc needed) | frontend/src/shared/api/errorMessages.ts |
| FE-004 | Unused chart components | frontend/src/features/dashboards/ui/charts/ |
| FE-006 | Any type in PlotlyComponent | frontend/src/shared/components/PlotlyComponent.tsx |
| TST-002 | Test assertion mismatch | tests/test_data_service.py |
| TST-003 | Tautological test | tests/core/test_temp_password_store.py |
| TST-005 | Mock-heavy auth service tests | tests/test_auth_service.py |
| TST-006 | Frontend act() warnings | frontend/src/features/auth/model/__tests__/useAuth.test.tsx |
| TST-007 | Rate limiter endpoint tests missing | tests/test_auth.py |

---

## 5. Cross-Cutting Concerns (from Phase 9: Integration)

### API Contract Alignment
- **DB-001 (merged with INT-003):** ProcessingStatus ENUM inconsistency across PostgreSQL, backend, and frontend. The database has `success` value not in Python StrEnum; frontend has deprecated `SUCCESS` alias. All layers should use consistent values: `started`, `uploaded`, `processing`, `completed`, `failed`.

### Authentication Flow
- No critical issues found. JWT + bcrypt implemented correctly. Token storage uses sessionStorage (secure) with memory-first fallback in development only.

### Data Flow Consistency
- Data processing pipeline follows correct flow: Upload → Validate → Parse → Transform → Aggregate → Store. Temp file cleanup verified at multiple points.

### Database-Model Alignment
- ProcessingStatus ENUM drift is the primary concern (DB-001). All other enums are aligned. Foreign key constraints verified present.

### Type Safety Alignment
- Several type mismatches are intentional design choices (frontend subset types, Pydantic ORM coercion). The real issue is missing `status` field in backend `ProcessingResult` model vs frontend expectation.

### Docker Deployment Wiring
- Production compose uses `${VAR:?error}` enforcement correctly. Test compose uses fallback values for CI/CD. One missing placeholder in `.env.production` template.

---

## 6. Fix Priority

1. **HIGH (security/correctness)** — 2 issues must be fixed before production:
   - DP-008: Remove `eval()` from computed field expressions (code injection risk)
   - TST-001: Fix JWT secret test to properly isolate `.env` loading

2. **MEDIUM (mandatory fixes)** — 5 issues requiring attention:
   - DC-002: Change admin password default to obviously-invalid placeholder
   - DC-003: Add production guard against `debug=True`
   - FE-003: Fix lint errors in ChartRenderer (potential data corruption)
   - FE-005: Use ProcessingStatus enum instead of hardcoded strings
   - BE-002: Fix JWT secret test expectation or `.env` isolation

3. **MEDIUM (advisory/coverage)** — 1 issue to improve:
   - TST-008: Address 45% test coverage (critical modules at 0% coverage)

4. **LOW (advisory/technical debt)** — 13 improvements for future enhancement

---

## Merge Strategy

The orchestrator combined findings from all validated phase audits into this final report.

**Source Files:**
- `.ai/audit/01-backend/findings.md`
- `.ai/audit/02-frontend/findings.md`
- `.ai/audit/03-database/findings.md`
- `.ai/audit/06-tests/findings.md`
- `.ai/audit/07-data-processing/findings.md`
- `.ai/audit/08-deployment-config/findings.md`
- `.ai/audit/90-integration/findings.md`

**Merges Applied:**
- INT-005 → FE-001 (same Russian fallback issue)
- INT-003 → DB-001 (same ProcessingStatus enum drift)
- DP-002 → DP-001 (same transaction boundary issue)

**Reclassifications:**
- DC-001: SPEC-DEVIATION → DOC-UPDATE, HIGH → LOW
- DC-004: HIGH → LOW, mandatory → advisory
- DP-001: SPEC-DEVIATION → BEST-PRACTICE
- DP-005: SPEC-DEVIATION → BEST-PRACTICE
- TST-002: RUNTIME-ERROR → BEST-PRACTICE

**Rejected (after validation):**
- FE-007: MUI TextField already provides label association
- INT-001: Mischaracterized the problem (frontend uses subset types)
- INT-002: String type is correct for JSON-serialized StrEnum
- INT-004: Str type in Pydantic model is standard for ORM coercion
- DP-003: Race condition speculative, standard stale-cleanup pattern
- DP-004: Empty file behavior is technically correct
- TST-004: Tests do verify outcome data alongside mock calls