# Phase 1: LLM Audit System Redesign — Context

**Gathered:** 2026-05-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Transform the current monolithic single-agent audit into a multi-agent orchestration system. The new system uses an orchestrator agent to coordinate specialized sub-agents, each responsible for one audit phase via parameterized templates. Phases can run independently or as a whole. The goal is deeper audit quality through specialization, not broader shallow coverage.

Out of scope: changing what the system audits (the project itself), adding new audit capabilities beyond the current scope, redesigning the project being audited.

</domain>

<decisions>
## Implementation Decisions

### Orchestrator Role

- Orchestrator = coordination + context curation + merge. Does NOT perform deep analysis itself.
- Gathers system context once, curates per-phase context packages (file paths only, not file contents).
- Delegates each phase to a generic executor sub-agent parameterized by a phase template.
- Manages the pipeline: launches phases, collects validated findings, merges into final report.
- Validation is a separate agent (`validator`), not the orchestrator's responsibility.

### Pipeline Parallelism

- Pipeline pattern: while Phase N is being validated, Phase N+1 runs audit in parallel.
- Orchestrator gathers validated findings as they complete (not waiting for all phases).
- Integration phase (Phase 9) runs after ALL 8 silo phases complete — it needs their full context.

### Validation & Retry

- After each phase completes, the orchestrator triggers the validator on that phase's findings file.
- Validator reads the findings file, validates each finding, writes a validation report.
- On validation rejection of most findings: auto-retry once with adjusted scope based on validation feedback.
- After 1 failed retry: escalate to user with a detailed report including recommendations for tuning the sub-agent role or task template.
- Rejected findings are cleaned from the findings file before merge.

### Sub-Agent Model

- Single generic executor role (`audit-executor`), parameterized by the phase template.
- No specialized roles per domain. One role, many templates.
- Simpler to maintain, consistent behavior across phases.

### Phase Structure — 9 Phases

8 silo phases + 1 cross-cutting integration phase:

| # | Phase | Type |
|---|-------|------|
| 1 | Backend Architecture | Silo |
| 2 | Frontend Architecture | Silo |
| 3 | Database | Silo |
| 4 | Security | Silo |
| 5 | Docker & Runtime | Silo |
| 6 | Tests | Silo |
| 7 | Data Processing | Silo |
| 8 | Deployment & Config | Silo |
| 9 | Integration Audit | Cross-cutting (after all silos) |

Key rationale:
- No standalone "System Analysis" phase — that's the orchestrator's job (context gathering).
- Docker & Runtime separated from Deployment & Config — runtime must actually start containers and check logs.
- Database separated from Backend — 10+ SQLAlchemy models, JSONB schemas, Alembic migrations deserve focused attention.
- Data Processing separated — it's the core business logic (upload → Polars → aggregate → store).
- Integration phase added to catch cross-layer issues (API contract mismatches, auth flow breaks, frontend-backend disconnects) that siloed audits miss.

### Integration Phase Scope

Phase 9 (Integration) verifies cross-layer connections:
- API contract consistency: frontend API client calls match backend route definitions (paths, methods, request/response shapes).
- Auth flow end-to-end: frontend attaches tokens correctly, backend validates, cookie/silent-refresh works.
- Data flow end-to-end: upload → process → store → retrieve → render.
- Database ↔ Backend alignment: SQLAlchemy models match actual DB schema, repository queries return what services expect.
- Frontend ↔ Backend type alignment: TypeScript types match Pydantic response models (OpenAPI contract).
- Docker service wiring: frontend, backend, DB, Redis actually communicate in the Docker network.

### Context Passing — Layered (Paths Only)

Orchestrator prepares two layers. Does NOT load file contents — only provides paths. Sub-agents read files themselves.

**Base Layer (same for all phases):**
- Project purpose & tech stack (1 paragraph from SPEC.md)
- Directory structure map (from `.ai/structure/map.md`)
- Docker/compose paths & commands
- Key config file paths (`settings/app.yaml`, `.env` convention)
- How to run tests/lint/typecheck
- Path to documentation (`docs/` + `.ai/`)

**Phase-Specific Layer (different per phase):**
- Relevant file paths (e.g., Backend → `src/mkobi/api/routes/`, `src/mkobi/services/`, `src/mkobi/models/`, `src/mkobi/db/`)
- Relevant docs (e.g., Backend → `docs/06-backend/`)

### Cross-Phase Findings Isolation

- Silo phases work independently. No findings from completed phases are passed to subsequent silo phases.
- Context isolation ensures no bias between silo phases.
- Only the Integration phase (Phase 9) receives the full picture — all silo findings are available to it.

### Findings Format & Storage

- Structured template per phase (not free-form). Mandatory fields: id, title, type, severity, description, evidence, affected modules, recommendation.
- One findings file per phase. Stored in `.ai/audit/` restructured by phase directories.
- Example structure: `.ai/audit/backend/findings.md`, `.ai/audit/frontend/findings.md`, etc.
- Validator reads one file per phase, writes validation report to `.ai/audit/validated/`.
- Orchestrator merges all validated findings into a final report.

### File Structure

```
.kilo/agents/
  audit-orchestrator.md   — new role
  audit-executor.md       — new role (replaces monolithic auditor for phase execution)
  validator.md            — already exists
  auditor.md              — deprecated (replaced by orchestrator + executor)

.kilo/commands/audit/
  phases/
    01-audit-backend.md
    02-audit-frontend.md
    03-audit-database.md
    04-audit-security.md
    05-audit-docker.md
    06-audit-tests.md
    07-audit-data-processing.md
    08-audit-deployment-config.md
    09-audit-integration.md
  templates/
    audit-findings.md           — structured findings template
    audit-final-report.md       — final merge report template

example after report
.ai/audit/
  backend/
    findings_01.md
  frontend/
    findings_01.md
  database/
    findings_01.md
  security/
    findings_01.md
  docker-runtime/
    findings_01.md
  tests/
    findings_01.md
  data-processing/
    findings_01.md
  deployment-config/
    findings_01.md
  integration/
    findings_01.md
  validated/
    audit_validated_findings_001.md
  final/
    audit_final_report.md
```

### KiloCode's Discretion

- Exact structured findings template fields (as long as id, title, type, severity, description, evidence, affected modules, recommendation are present).
- Phase template internal structure and checklists — the executor role stays generic, templates define the domain specifics.
- Final report merge strategy — orchestrator decides how to deduplicate and organize validated findings into the final document.
- Retry scope adjustment strategy — how to refine the phase template/context after a validation rejection.

</decisions>

<specifics>
## Specific Ideas

- The core problem being solved: current monolithic audit loses depth because context is spread across too many phases in a single agent. The fix is specialization through sub-agents, not adding more checklist items.
- Integration phase is critical — the example given was: dashboard exists in DB, API returns data, frontend has component, but frontend doesn't call the backend, backend doesn't query the DB. Everything looks good in isolation, nothing works together. This is the #1 class of bug the current audit misses.
- Docker & Runtime phase must actually run containers and check logs — static file checks alone are insufficient. The current auditor doesn't do this consistently.
- The validator already exists as a role (`C:\py_dev\mkobi\.kilo\agents\validator.md`) and has a validation command (`C:\py_dev\mkobi\.kilo\commands\validate\validate-audit-findings.md`). These are inputs to this redesign, not things to build from scratch.
- Existing audit templates in `C:\py_dev\mkobi\.kilo\commands\audit/` (project, docker, tests, db) are the basis for the new phase templates — they need restructuring into the new format, not rewriting from scratch.

</specifics>

<deferred>
## Deferred Ideas

- Specialized executor roles per domain (e.g., `backend-auditor`, `security-auditor`) — rejected for now to keep it simple. Can be revisited if the generic executor produces low-quality findings in specific domains.
- Automated fixing of audit findings — out of scope. This redesign is about audit quality, not auto-remediation.
- Continuous/ongoing audit integration (e.g., triggered on every commit) — future capability, not part of this phase.
- Audit of CI/CD pipeline execution (not just config) — would require running actual builds. Deferred to a future infrastructure phase extension.

</deferred>

---

_Phase: 01-llm-audit-redesign_
_Context gathered: 2026-05-27_
