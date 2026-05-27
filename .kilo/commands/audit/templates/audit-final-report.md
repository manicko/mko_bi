---
name: audit-final-report
description: Structured template for final merged audit report combining all phase findings
agent: audit-orchestrator
alwaysApply: false
---

# Audit Report — mkobi BI Dashboard

**Generated:** {date}
**Phases Completed:** 9/9
**Validated Findings:** {N} total

---

## 1. Executive Summary

| Metric | Value |
|--------|-------|
| **Overall Quality Score** | {1-10} |
| **Critical Findings** | {count} |
| **Production Readiness** | {READY \| PARTIALLY_READY \| NOT_READY} |

**Summary:**
{Brief paragraph summarizing system quality, main risks, readiness level.}

---

## 2. Architecture Summary

### Backend (Clean Architecture)

| Assessment Area | Score (1-10) | Notes |
|-----------------|--------------|-------|
| Architecture Boundaries | {score} | {observations} |
| Dependency Direction | {score} | {observations} |
| Layer Separation | {score} | {observations} |
| Maintainability | {score} | {observations} |

**Strengths:**
- {List key strengths}

**Weaknesses:**
- {List key weaknesses}

### Frontend (Feature-Sliced Design)

| Assessment Area | Score (1-10) | Notes |
|-----------------|--------------|-------|
| Feature Modularity | {score} | {observations} |
| Layer Separation | {score} | {observations} |
| Maintainability | {score} | {observations} |
| Consistency | {score} | {observations} |

**Strengths:**
- {List key strengths}

**Weaknesses:**
- {List key weaknesses}

---

## 3. Findings by Phase

### Phase 1: Backend Architecture
[Findings from `.ai/audit/backend-architecture/findings.md`]

### Phase 2: Frontend Architecture
[Findings from `.ai/audit/frontend-architecture/findings.md`]

### Phase 3: Security
[Findings from `.ai/audit/security/findings.md`]

### Phase 4: Data Processing
[Findings from `.ai/audit/data-processing/findings.md`]

### Phase 5: API Endpoints
[Findings from `.ai/audit/api-endpoints/findings.md`]

### Phase 6: Database
[Findings from `.ai/audit/database/findings.md`]

### Phase 7: Configuration
[Findings from `.ai/audit/configuration/findings.md`]

### Phase 8: Testing
[Findings from `.ai/audit/testing/findings.md`]

### Phase 9: Integration
[Findings from `.ai/audit/integration/findings.md`]

---

## 4. Findings by Severity

### CRITICAL (must fix immediately)

| ID | Title | Affected Modules |
|----|-------|----------------|
| {id} | {title} | {modules} |

### HIGH (fix before production)

| ID | Title | Affected Modules |
|----|-------|----------------|
| {id} | {title} | {modules} |

### MEDIUM (technical debt)

| ID | Title | Affected Modules |
|----|-------|----------------|
| {id} | {title} | {modules} |

### LOW (nice to have)

| ID | Title | Affected Modules |
|----|-------|----------------|
| {id} | {title} | {modules} |

---

## 5. Cross-Cutting Concerns (from Phase 9: Integration)

### API Contract Alignment
- {API consistency findings}

### Authentication Flow
- {Auth flow findings across layers}

### Data Flow Consistency
- {Data flow findings}

### Database-Model Alignment
- {DB alignment findings}

### Type Safety Alignment
- {Type alignment findings}

### Docker Deployment Wiring
- {Docker wiring findings}

---

## 6. Fix Priority

1. **CRITICAL** — {count} issues must be fixed before any deployment
2. **HIGH** — {count} issues must be fixed before production release
3. **MEDIUM** — {count} technical debt items to address in next iteration
4. **LOW** — {count} improvements for future enhancement

---

## Merge Strategy

The orchestrator combines findings from all validated phase audits into this final report.

**Source Files:**
- `.ai/audit/backend-architecture/findings.md`
- `.ai/audit/frontend-architecture/findings.md`
- `.ai/audit/security/findings.md`
- `.ai/audit/data-processing/findings.md`
- `.ai/audit/api-endpoints/findings.md`
- `.ai/audit/database/findings.md`
- `.ai/audit/configuration/findings.md`
- `.ai/audit/testing/findings.md`
- `.ai/audit/integration/findings.md`

**Process:**
1. All 9 phase audits must be validated before final report generation
2. Each finding from per-phase files is extracted and categorized
3. Severity counts are tallied across all phases
4. Cross-cutting concerns are consolidated from Phase 9
5. Priority ordering follows: CRITICAL → HIGH → MEDIUM → LOW

---

## Template Field Reference

### Required Fields

| Field | Format | Description |
|-------|--------|-------------|
| `{date}` | ISO date | Report generation timestamp |
| `{N}` | integer | Total validated findings count |
| `{score}` | 1-10 | Assessment score per section |
| `{count}` | integer | Count per severity category |
| `{id}` | string | Finding identifier (e.g., `BE-001`, `FE-003`) |
| `{title}` | string | Finding title |
| `{modules}` | string | Affected module paths |

### Production Readiness Levels

- **READY** — No CRITICAL or HIGH findings, all mandatory fixes complete
- **PARTIALLY_READY** — HIGH findings exist but mitigation is possible
- **NOT_READY** — CRITICAL findings present, immediate fixes required