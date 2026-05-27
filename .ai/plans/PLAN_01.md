# PLAN_01 — LLM Audit System Redesign

## Meta

| Field | Value |
|------|-------|
| **Phase** | 01 — LLM Audit System Redesign |
| **Goal** | Transform monolithic single-agent audit into multi-agent orchestration system |
| **Waves** | 3 (Foundation → Silo Templates → Verification) |
| **Tasks** | 14 |
| **Risk** | Low (all changes are documentation/agent infrastructure, no production code) |

---

## must_haves

- [ ] `audit-findings.md` template with mandatory fields: id, title, type, severity, description, evidence, affected_modules, recommendation
- [ ] `audit-final-report.md` template with merge strategy for combining 9 phase findings
- [ ] `audit-executor.md` agent role — generic parameterized executor, no domain specialization
- [ ] `audit-orchestrator.md` agent role — pipeline coordinator (no deep analysis)
- [ ] `09-audit-integration.md` phase template — cross-cutting integration audit covering API contract, auth flow, data flow, DB alignment, type alignment, Docker wiring
- [ ] All 8 silo phase templates created (01-08), each with relevant file paths from structure maps
- [ ] All 9 phase templates base-layer context: project purpose, directory structure, verification commands, docker paths, doc index
- [ ] All 9 phase templates extract domain knowledge from existing audit commands
- [ ] `auditor.md` deprecated status documented in new agents
- [ ] `validator.md` unchanged (referenced, not modified)

---

## Wave 1 — Foundation (Sequential)

> All tasks in Wave 1 are sequential. Each depends on the previous.

---

### T01 — Create `audit-findings.md` Template

```xml
<task id="T01" wave="1" depends_on="" files_modified="true" autonomous="true">
  <action>
    Create the structured findings template used by every phase's executor agent.
  </action>
  <frontmatter>
    wave: 1
    depends_on: none
    files_modified:
      - .kilo/commands/audit/templates/audit-findings.md
    autonomous: true
  </frontmatter>
  <details>
    Create file: `.kilo/commands/audit/templates/audit-findings.md`

    This template defines the structured format for audit findings produced by each phase executor.
    Every phase writes findings to `.ai/audit/{phase-name}/findings.md` using this format.

    **Mandatory fields per finding:**

    | Field | Type | Description |
    |-------|------|-------------|
    | `id` | string | Unique identifier within phase (e.g., `BE-001`, `FE-003`) |
    | `title` | string | Human-readable one-line summary |
    | `type` | enum | `[SPEC-DEVIATION]`, `[BEST-PRACTICE]`, `[DOC-UPDATE]`, `[RUNTIME-ERROR]` |
    | `severity` | enum | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
    | `description` | string | Detailed problem description with context |
    | `evidence` | string | File paths, line references, log excerpts, code snippets |
    | `affected_modules` | list | Affected module paths (e.g., `src/mkobi/api/routes/`, `frontend/src/features/auth/`) |
    | `recommendation` | string | Concrete fix direction: what to change and why |
    | `classification` | enum | `mandatory` (security, data loss, correctness) or `advisory` (improvement, refactoring) |

    **Template structure:**

    ```markdown
    # Phase N Audit Findings — {Phase Name}

    **Executor:** audit-executor
    **Template:** {phase-template-file}
    **Status:** {pending|in-progress|complete}
    **Validated:** {yes|no}

    ---

    ## Findings

    ### {ID}: {Title}

    | Field | Value |
    |-------|-------|
    | **ID** | {id} |
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
    ## Advisory Recommendations
    ## Doc Updates Needed
    ```

    **Acceptance criteria:**
    - Template has all 9 mandatory fields defined
    - Template includes Summary section with severity counts
    - Template separates mandatory fixes, advisory recommendations, and doc updates
    - Template is copy-ready (executor fills in the blanks)
  </details>
  <validation>
    - File exists at `.kilo/commands/audit/templates/audit-findings.md`
    - Contains all 9 mandatory fields
    - Contains Summary section with severity table
    - Contains 3 classification sections (mandatory, advisory, doc updates)
  </validation>
</task>
```

---

### T02 — Create `audit-final-report.md` Template

```xml
<task id="T02" wave="1" depends_on="T01" files_modified="true" autonomous="true">
  <action>
    Create the final report template used by the orchestrator to merge all phase findings.
  </action>
  <frontmatter>
    wave: 1
    depends_on: T01
    files_modified:
      - .kilo/commands/audit/templates/audit-final-report.md
    autonomous: true
  </frontmatter>
  <details>
    Create file: `.kilo/commands/audit/templates/audit-final-report.md`

    This template defines the structured format for the final merged audit report.
    The orchestrator uses this to combine all validated phase findings into one deliverable.

    **Report structure:**

    ```markdown
    # Audit Report — mkobi BI Dashboard

    **Generated:** {date}
    **Phases Completed:** 9/9
    **Validated Findings:** {N} total

    ---

    ## 1. Executive Summary

    - **Overall Quality Score:** {1-10}
    - **Critical Findings:** {count}
    - **Production Readiness:** {READY | PARTIALLY_READY | NOT_READY}

    Brief paragraph summarizing system quality, main risks, readiness level.

    ---

    ## 2. Architecture Summary

    ### Backend (Clean Architecture)
    Strengths, weaknesses, maintainability assessment.

    ### Frontend (Feature-Sliced Design)
    Strengths, weaknesses, maintainability assessment.

    ---

    ## 3. Findings by Phase

    ### Phase 1: Backend Architecture
    [Findings from audit-backend/findings.md]

    ### Phase 2: Frontend Architecture
    [Findings from audit-frontend/findings.md]

    ... (all 9 phases)

    ---

    ## 4. Findings by Severity

    ### CRITICAL (must fix immediately)
    [All CRITICAL findings across all phases]

    ### HIGH (fix before production)
    [All HIGH findings across all phases]

    ### MEDIUM (technical debt)
    [All MEDIUM findings across all phases]

    ### LOW (nice to have)
    [All LOW findings across all phases]

    ---

    ## 5. Cross-Cutting Concerns (from Phase 9: Integration)

    [Integration-specific findings: API contract, auth flow, data flow, DB alignment, type alignment, Docker wiring]

    ---

    ## 6. Fix Priority

    Numbered list: 1. CRITICAL, 2. HIGH, 3. MEDIUM, 4. LOW

     ```
    **Acceptance criteria:**
    - Template has: Executive Summary, Architecture Summary, Findings by Phase, Findings by Severity, Cross-Cutting, Fix Priority
    - Includes scoring area (1-10 per section)
    - Merge strategy documented (orchestrator pulls from per-phase findings files)
  </details>
  <validation>
    - File exists at `.kilo/commands/audit/templates/audit-final-report.md`
    - Contains all 6 sections
    - References per-phase findings files as source
    - Includes scoring and readiness assessment
  </validation>
</task>
```

---

### T03 — Create `audit-executor.md` Agent Role

```xml
<task id="T03" wave="1" depends_on="T02" files_modified="true" autonomous="true">
  <action>
    Create the generic parameterized executor agent role.
  </action>
  <frontmatter>
    wave: 1
    depends_on: T02
    files_modified:
      - .kilo/agents/audit-executor.md
    autonomous: true
  </frontmatter>
  <details>
    Create file: `.kilo/agents/audit-executor.md`

    This is the **single generic executor role**. It is parameterized by the phase template supplied at invocation.
    No domain specialization — the same executor audits backend, frontend, database, etc.

    **Agent definition structure (YAML frontmatter):**

    ```yaml
    ---
    description: Generic parameterized audit executor agent. Executes one audit phase by reading the phase template, loading relevant files, performing analysis, and writing structured findings.
    mode: all
    color: "#8B5CF6"
    steps: 150

    permission:
      read: allow
      grep: allow
      glob: allow
      todoread: allow
      websearch: allow
      webfetch: allow

      edit:
        "*.md": allow
        "*.yaml": allow
        "*.yml": allow
        "*": deny

      bash:
        "pytest*": allow
        "ruff*": allow
        "mypy*": allow
        "alembic*": allow
        "docker compose*": allow
        "docker ps*": allow
        "docker logs*": allow
        "curl*": allow
        "psql*": allow
        "redis-cli*": allow
        "*": deny
    ---
    ```

    **Agent instructions (body):**

    The executor must be defined as:

    1. **Role:** Generic parameterized executor. Receives a phase template path as parameter.
    2. **Process:**
       a. Read the phase template to get the audit checklist and scope.
       b. For each file path listed in the phase template, read the file.
       c. For each checklist item, verify against the actual code.
       d. Use `websearch` to verify current best practices when the template asks.
       e. Write findings to `.ai/audit/{phase-name}/findings.md` using the `audit-findings.md` template.
    3. **Constraints:**
       - Do NOT modify production code.
       - Do NOT make implementation changes.
       - Analysis only — produce findings, not fixes.
       - Use structured findings format (from audit-findings.md template).
       - Classify each finding as mandatory or advisory.
       - Use StrEnum severity levels: CRITICAL, HIGH, MEDIUM, LOW.
    4. **Reference to existing auditor.md:** The executor inherits the analytical mindset from the existing auditor role but operates within a constrained, parameterized scope. Read `.kilo/agents/auditor.md` for the baseline audit philosophy (spec-first, evidence-driven, forward-looking).

    **Acceptance criteria:**
    - Agent file exists with correct YAML frontmatter
    - Permissions scoped to read + grep + glob + edit *.md only
    - Bash permissions scoped to audit execution needs
    - Instructions reference the findings template
    - No domain specialization — generic and parameterized
    - Reference to existing `auditor.md` for audit philosophy baseline
  </details>
  <validation>
    - File exists at `.kilo/agents/audit-executor.md`
    - YAML frontmatter has all required fields (description, mode, color, steps, permission)
    - Body contains the 4-point process definition
    - References `audit-findings.md` template
    - Generic (no domain-specific instructions hardcoded)
  </validation>
</task>
```

---

### T04 — Create `audit-orchestrator.md` Agent Role

```xml
<task id="T04" wave="1" depends_on="T03" files_modified="true" autonomous="true">
  <action>
    Create the pipeline orchestrator agent role.
  </action>
  <frontmatter>
    wave: 1
    depends_on: T03
    files_modified:
      - .kilo/agents/audit-orchestrator.md
    autonomous: true
  </frontmatter>
  <details>
    Create file: `.kilo/agents/audit-orchestrator.md`

    The orchestrator coordinates the multi-agent pipeline. It does NOT perform deep analysis itself.

    **Agent definition structure (YAML frontmatter):**

    ```yaml
    ---
    description: Multi-agent audit pipeline orchestrator. Coordinates 9-phase audit by preparing context packages, delegating to parameterized executor agents, triggering validation, managing retry, and merging validated findings into final report.
    mode: all
    color: "#F59E0B"
    steps: 80

    permission:
      read: allow
      grep: allow
      glob: allow
      todoread: allow

      edit:
        "*.md": allow
        "*.yaml": allow
        "*.yml": allow
        "*": deny

      bash:
        "*": deny
    ---
    ```

    **Orchestrator instructions (body):**

    Define the orchestrator as:

    1. **Role:** Pipeline coordinator — context curator, delegator, validator-trigger, merger.
    2. **What the orchestrator does NOT do:** Deep code analysis. That's the executor's job.
    3. **Process:**

       **Phase A — Context Gathering (once):**
       a. Read `.ai/structure/map.md` for directory structure.
       b. Read `.ai/context/commands.md` for verification commands.
       c. Read `docs/SPEC.md` for project purpose and tech stack.
       d. Read `docs/README_DOCKER.md` for Docker service paths.
       e. Build the **Base Layer** context package (same for all phases).

       **Phase B — Pipeline Execution (per phase):**
       a. For each silo phase 1-8 (in order):
          - Read the phase template to get domain-specific file paths.
          - Prepare the **Phase-Specific Layer** context (file paths only, NOT contents).
          - Delegate to executor: "audit-executor with template `.kilo/commands/audit/phases/NN-audit-X.md`".
          - Executor writes findings to `.ai/audit/{phase-name}/findings.md`.
          - Trigger validator on the findings file.
          - If validation rejects most findings: retry once with adjusted scope.
          - If retry also fails: escalate to user with detailed report.
          - Clean rejected findings from the file.
          - Begin Phase N+1 audit in parallel with Phase N validation.

       b. After all 8 silo phases complete:
          - Collect all validated findings files.
          - Delegate Phase 9 (Integration) with ALL silo findings as context.
          - Trigger validator on integration findings.
          - Merge all 9 sets of validated findings using `audit-final-report.md` template.
          - Write final report to `.ai/audit/final-report.md`.

    4. **Context Package Format:**

       Each context package must contain:
       - **Base Layer:** project purpose, directory structure, verification commands, Docker paths, doc index
       - **Phase-Specific Layer:** relevant file paths from structure maps + relevant docs
       - No file contents — only paths. Sub-agents read files themselves.

    5. **Validation & Retry Rules:**
       - Max 1 retry per phase (2 total attempts).
       - On second failure: escalate to user with structured failure report.
       - Rejected findings are cleaned from findings file before merge.

    6. **Parallel Execution:**
       - While Phase N is being validated, Phase N+1 executor runs.
       - This overlap is the primary latency optimization.

    7. **Reference to existing agents:**
       - `.kilo/agents/auditor.md` — DEPRECATED. Logic distributed to executor + phase templates.
       - `.kilo/agents/validator.md` — UNCHANGED. Reused as-is for validation.

    **Acceptance criteria:**
    - Agent file exists with correct YAML frontmatter.
    - Permissions are **read-only** (no bash, no production edits) — orchestrator only coordinates.
    - Instructions define all 6 process stages: Context Gathering, Pipeline Execution, Parallel Execution, Validation, Retry, Merge.
    - Context package format documented (Base Layer + Phase-Specific Layer, paths only).
    - Retry budget defined (max 1 retry + escalation).
    - Explicit statement: orchestrator does NOT perform deep analysis.
    - Explicit deprecation note for `auditor.md`.
    - Explicit note that `validator.md` is reused unchanged.
  </details>
  <validation>
    - File exists at `.kilo/agents/audit-orchestrator.md`
    - YAML frontmatter has read-only permissions (no bash access)
    - Body contains all pipeline stages
    - References both deprecated `auditor.md` and existing `validator.md`
    - Retry logic defined with escalation path
  </validation>
</task>
```

---

### T05 — Create `09-audit-integration.md` Phase Template

```xml
<task id="T05" wave="1" depends_on="T04" files_modified="true" autonomous="true">
  <action>
    Create the cross-cutting integration audit phase template (Phase 9).
  </action>
  <frontmatter>
    wave: 1
    depends_on: T04
    files_modified:
      - .kilo/commands/audit/phases/09-audit-integration.md
    autonomous: true
  </frontmatter>
  <details>
    Create file: `.kilo/commands/audit/phases/09-audit-integration.md`

    This is the ONLY new phase template not extracted from existing audit commands.
    It covers cross-cutting concerns across all 8 silo phases.

    **Phase template structure (YAML frontmatter + body):**

    YAML frontmatter:
    ```yaml
    ---
    name: audit-integration
    description: Cross-cutting integration audit covering API contract consistency, auth flow end-to-end, data flow end-to-end, database-backend alignment, frontend-backend type alignment, Docker service wiring
    agent: audit-executor
    alwaysApply: false
    ---
    ```

    Body must contain these **6 audit dimensions**, each with specific checklists:

    **Dimension 1 — API Contract Consistency:**
    - Frontend API client calls match backend route definitions.
    - Check `.ai/structure/front/ts_anchors.yaml` for API call patterns against `src/mkobi/api/routes/` route definitions.
    - Verify path parameters, query parameters, request body shapes match.
    - Files: `frontend/src/features/*/api/*.ts`, `src/mkobi/api/routes/*.py`

    **Dimension 2 — Auth Flow End-to-End:**
    - Frontend attaches JWT tokens correctly (axios interceptors).
    - Backend validates tokens (dependencies in `deps.py`).
    - Token refresh flow works end-to-end.
    - Session/cookie handling secure (Secure flag, SameSite).
    - Files: `frontend/src/shared/api/axiosInstance.ts`, `src/mkobi/core/security.py`, `src/mkobi/api/routes/auth.py`

    **Dimension 3 — Data Flow End-to-End (Upload → Process → Store → Retrieve → Render):**
    - Upload endpoint receives file correctly.
    - Processing pipeline (Polars) produces correct aggregates.
    - Storage manager writes correct JSONB to PostgreSQL.
    - Data retrieval endpoint returns correct shape.
    - Frontend renders data correctly (Plotly charts).
    - Files: `src/mkobi/data/loaders/`, `src/mkobi/data/processing/`, `src/mkobi/data/storage/`, `src/mkobi/api/routes/data.py`, `frontend/src/features/dashboards/ui/charts/`

    **Dimension 4 — Database ↔ Backend Alignment:**
    - SQLAlchemy models match Alembic migration schema.
    - File: `src/mkobi/db/models/*.py` vs `alembic/versions/*.py`
    - Check for schema drift.

    **Dimension 5 — Frontend ↔ Backend Type Alignment:**
    - TypeScript types match Pydantic response models.
    - File: `frontend/src/shared/types/api.types.ts` vs `src/mkobi/models/*.py`
    - Check response shapes, field names, nullable types.

    **Dimension 6 — Docker Service Wiring:**
    - Services communicate via Docker network.
    - Environment variables flow correctly between services.
    - Health checks reference correct inter-service endpoints.
    - Files: `docker/docker-compose.yml`, `docker/docker-compose.override.yml`, `Dockerfile`

    **Report format:** Same as audit-findings.md template (T01). Findings prefixed with `INT-` prefix.

    **Input dependency:** This phase receives ALL 8 silo-phase validated findings as additional context.

    **Acceptance criteria:**
    - File exists at `.kilo/commands/audit/phases/09-audit-integration.md`
    - Contains all 6 integration dimensions
    - Each dimension has specific file paths from structure maps
    - Includes dimension-specific checklists
    - Notes that this phase runs AFTER all 8 silos complete
    - Uses `INT-` prefix for finding IDs
    - References validated silo findings as input
  </details>
  <validation>
    - File exists with correct YAML frontmatter
    - All 6 dimensions covered with specific file lists
    - Dependencies on other phases documented
    - Finding ID prefix `INT-` specified
  </validation>
</task>
```

---

## Wave 2 — Silo Phase Templates (Parallel)

> All Wave 2 tasks depend on Wave 1 completion (T01-T05).
> All Wave 2 tasks are independent of each other and can execute in parallel.

---

### T06 — Create `01-audit-backend.md` Phase Template

```xml
<task id="T06" wave="2" depends_on="T05" files_modified="true" autonomous="true">
  <action>
    Create the backend architecture audit phase template.
    Extract content from: audit-project-detailed.md blocks 1-3, 7.
  </action>
  <frontmatter>
    wave: 2
    depends_on: T05
    files_modified:
      - .kilo/commands/audit/phases/01-audit-backend.md
    autonomous: true
  </frontmatter>
  <details>
    Create file: `.kilo/commands/audit/phases/01-audit-backend.md`

    Source: Extract and adapt from `.kilo/commands/audit/project/audit-project-detailed.md`

    **Extract blocks:**
    - BLOCK 1 — Project Structure & Architecture (1.1 Backend Structure only)
    - BLOCK 2 — Backend API Layer (2.1 Auth, 2.2 Dashboard, 2.3 Data & Upload, 2.4 Admin, 2.5 Health, 2.6 Other)
    - BLOCK 3 — Access Control & Security (3.1-3.8, scoped to backend)
    - BLOCK 7 — Code Quality Backend (7.1 Typing, 7.2 Pydantic, 7.3 StrEnum, 7.4 Readability, 7.5 Logging Language, 7.6 Error Handling, 7.7 Async, 7.8 Logging)

    **Phase template structure:**

    YAML frontmatter:
    ```yaml
    ---
    name: audit-backend
    description: Backend architecture audit covering Clean Architecture compliance, API layer correctness, access control, code quality (typing, Pydantic, StrEnum, async, logging)
    agent: audit-executor
    alwaysApply: false
    ---
    ```

    Body structure:

    1. **Base Layer Context** (auto-included by orchestrator):
       - Project: mkobi BI Dashboard (FastAPI + React + PostgreSQL)
       - Structure: `.ai/structure/map.md`
       - Commands: `.ai/context/commands.md`
       - SPEC: `docs/SPEC.md`

    2. **Phase-Specific File Paths** (orchestrator provides these, executor reads them):
       - `src/mkobi/api/routes/*.py`
       - `src/mkobi/services/*.py`
       - `src/mkobi/db/repositories/*.py`
       - `src/mkobi/db/models/*.py`
       - `src/mkobi/models/*.py`
       - `src/mkobi/models/enums.py`
       - `src/mkobi/core/*.py`
       - `src/mkobi/data/loaders/*.py`
       - `src/mkobi/data/processing/*.py`
       - `src/mkobi/data/storage/*.py`
       - `src/mkobi/config.py`
       - `src/mkobi/interfaces/*.py`
       - `src/mkobi/workers/*.py`

    3. **Checklist** (adapted from source blocks, condensed):
       - [ ] Backend Clean Architecture: layer separation, no business logic in routes, DI via `deps.py`
       - [ ] API endpoints: all routes correct, Pydantic models, HTTPException errors, no `print()`
       - [ ] Auth: JWT (algorithm set, expiration, bcrypt, rate limiting)
       - [ ] Dashboard access: `dashboard_access`, admin bypass, 403/404 dual-signal
       - [ ] Upload: MIME validation, size limit, temp file cleanup, path traversal protection
       - [ ] Admin: role enforcement, registration flow, no sensitive data leakage
       - [ ] Health: `/health`, `/health/detailed`, `/` all functional
       - [ ] Processing pipeline: Polars only (no pandas), full recalc, cleanup
       - [ ] StrEnum: all used, no string literals for role/status/type checks
       - [ ] Code quality: type hints, Pydantic models, async correctness, no `print()`, English comments/logs
       - [ ] SQL safety: parameterized queries, no raw f-string SQL
       - [ ] Temp file cleanup: `platformdirs`, `finally` blocks

    4. **Report format:** Same as audit-findings.md (T01). Findings prefixed with `BE-` prefix.

    **Acceptance criteria:**
    - File exists and has valid YAML frontmatter
    - Content extracted from source blocks 1, 2, 3, 7 only (no frontend/code quality frontend sections)
    - Contains phase-specific file paths for backend
    - Contains condensed checklist covering all backend concerns
    - Uses `BE-` finding ID prefix
  </details>
  <validation>
    - File exists at `.kilo/commands/audit/phases/01-audit-backend.md`
    - Extracted ONLY from blocks 1-3, 7 (not frontend blocks)
    - Contains backend-specific file paths
    - Condensed checklist present
  </validation>
</task>
```

---

### T07 — Create `02-audit-frontend.md` Phase Template

```xml
<task id="T07" wave="2" depends_on="T05" files_modified="true" autonomous="true">
  <action>
    Create the frontend architecture audit phase template.
    Extract content from: audit-project-detailed.md blocks 1.2, 6, 8.
  </action>
  <frontmatter>
    wave: 2
    depends_on: T05
    files_modified:
      - .kilo/commands/audit/phases/02-audit-frontend.md
    autonomous: true
  </frontmatter>
  <details>
    Create file: `.kilo/commands/audit/phases/02-audit-frontend.md`

    Source: Extract and adapt from `.kilo/commands/audit/project/audit-project-detailed.md`

    **Extract blocks:**
    - BLOCK 1.2 — Frontend Structure (from Project Structure & Architecture)
    - BLOCK 6 — Frontend (React SPA): full section (6.1-6.7)
    - BLOCK 8 — Code Quality Frontend (8.1 TypeScript, 8.2 React Best Practices, 8.3 Code Style)

    **Phase template structure:**

    YAML frontmatter:
    ```yaml
    ---
    name: audit-frontend
    description: Frontend architecture audit covering Feature-Sliced Design compliance, React SPA correctness, type safety, API integration, code quality
    agent: audit-executor
    alwaysApply: false
    ---
    ```

    Body structure:

    1. **Base Layer Context** (same as all phases)

    2. **Phase-Specific File Paths:**
       - `frontend/src/app/*.tsx`
       - `frontend/src/features/auth/**/*`
       - `frontend/src/features/dashboards/**/*`
       - `frontend/src/features/upload/**/*`
       - `frontend/src/features/users/**/*`
       - `frontend/src/features/admin/**/*`
       - `frontend/src/shared/api/*.ts`
       - `frontend/src/shared/components/*.tsx`
       - `frontend/src/shared/types/*.ts`

     3. **Checklist:**
       - [ ] FSD compliance: `app/`, `features/`, `shared/` structure correct
       - [ ] Feature structure: `ui/`, `api/`, `model/`, `types/` per feature
       - [ ] Routes: all paths from spec implemented, correct access control per route
       - [ ] Type safety: TypeScript strict, no `any`, Zod schemas, correct API types
       - [ ] API integration: axiosInstance, JWT interceptors, 401 handling, TanStack Query
       - [ ] Pages: Login, Register, DashboardList, DashboardView, Upload, Admin, Profile all implemented
       - [ ] Charts: Plotly.js React, bar/line/pie/table, config-driven
       - [ ] State: TanStack Query (no Redux/Zustand), React Hook Form + Zod
       - [ ] Security: JWT in memory/sessionStorage (not localStorage), ProtectedRoute, RoleBasedAccess
       - [ ] UI components: no business logic in components, props interfaces
       - [ ] Code quality: functional components, hooks usage, no `console.log`, English comments

    4. **Report format:** Same as audit-findings.md. Findings prefixed with `FE-` prefix.

    **Acceptance criteria:**
    - File exists with valid YAML frontmatter
    - Content extracted from blocks 4(FSD), 6(Full Frontend), 8(Code Quality Frontend)
    - Phase-specific frontend file paths included
    - Condensed checklist covering FSD, React, TypeScript, API integration
    - Uses `FE-` finding ID prefix
  </details>
  <validation>
    - File exists at `.kilo/commands/audit/phases/02-audit-frontend.md`
    - Extracted ONLY from frontend-related blocks
    - Contains frontend-specific file paths
  </validation>
</task>
```

---

### T08 — Create `03-audit-database.md` Phase Template

```xml
<task id="T08" wave="2" depends_on="T05" files_modified="true" autonomous="true">
  <action>
    Create the database audit phase template.
    Extract content from: audit-db-structure.md.
  </action>
  <frontmatter>
    wave: 2
    depends_on: T05
    files_modified:
      - .kilo/commands/audit/phases/03-audit-database.md
    autonomous: true
  </frontmatter>
  <details>
    Create file: `.kilo/commands/audit/phases/03-audit-database.md`

    Source: Extract and adapt from `.kilo/commands/audit/db/audit-db-structure.md`

    **Phase template structure:**

    YAML frontmatter:
    ```yaml
    ---
    name: audit-database
    description: Database architecture audit covering schema compliance, indexes, migrations, JSONB usage, test isolation, async compatibility, scalability risks
    agent: audit-executor
    alwaysApply: false
    ---
    ```

    Body structure:

    1. **Base Layer Context** (same as all phases)

    2. **Phase-Specific File Paths:**
       - `alembic/versions/*.py`
       - `src/mkobi/db/models/*.py`
       - `src/mkobi/db/repositories/*.py`
       - `src/mkobi/db/starter.py`
       - `docker/docker-compose.yml`
       - `.env`, `.env.example`

    3. **Checklist (adapted from audit-db-structure.md):**
       - [ ] Schema compliance: all 10 tables match spec, correct types, constraints, CASCADE/SET NULL
       - [ ] UUID strategy: UUID for entities, BIGSERIAL for `aggregated_data`
       - [ ] JSONB usage: `dims` + `metrics` in `aggregated_data`, GIN index, dims key sorted
       - [ ] Indexes: all 7 core indexes + additional indexes present
       - [ ] Migrations: chain intact, reproducible, no broken revisions, ENUM `checkfirst=True`
       - [ ] Roles & permissions: least privilege, no superuser for application
       - [ ] Test isolation: `bidb_test` separate, SAVEPOINT rollback, NullPool
       - [ ] Async compatibility: asyncpg driver, no sync in async context
       - [ ] Scalability: archival strategy for `processing_logs`, growth risks identified
       - [ ] Schema drift: ORM vs Alembic vs real DB consistent

    4. **Report format:** Same as audit-findings.md. Findings prefixed with `DB-` prefix.

    **Acceptance criteria:**
    - File exists with valid YAML frontmatter
    - Content extracted from audit-db-structure.md only
    - Contains database-specific file paths
    - Condensed checklist covering schema, migrations, indexes, JSONB, isolation, scalability
    - Uses `DB-` finding ID prefix
  </details>
  <validation>
    - File exists at `.kilo/commands/audit/phases/03-audit-database.md`
    - Source is audit-db-structure.md
    - Database-specific file paths included
  </validation>
</task>
```

---

### T09 — Create `04-audit-security.md` Phase Template

```xml
<task id="T09" wave="2" depends_on="T05" files_modified="true" autonomous="true">
  <action>
    Create the security audit phase template.
    Extract content from: audit-project-detailed.md blocks 3, 7.3, 8.1.
  </action>
  <frontmatter>
    wave: 2
    depends_on: T05
    files_modified:
      - .kilo/commands/audit/phases/04-audit-security.md
    autonomous: true
  </frontmatter>
  <details>
    Create file: `.kilo/commands/audit/phases/04-audit-security.md`

    Source: Extract and adapt from `.kilo/commands/audit/project/audit-project-detailed.md`

    **Extract blocks:**
    - BLOCK 3 — Access Control & Security (3.1-3.7)
    - BLOCK 7.3 — Enum Usage (StrEnum)
    - BLOCK 8.1 — Frontend Security aspects (from Frontend Code Quality)

    **Phase template structure:**

    YAML frontmatter:
    ```yaml
    ---
    name: audit-security
    description: Security audit covering authentication, access control, JWT, password security, upload safety, SQL safety, secrets/config, rate limiting, email domain blocklist, StrEnum enforcement
    agent: audit-executor
    alwaysApply: false
    ---
    ```

    Body structure:

    1. **Base Layer Context** (same as all phases)

    2. **Phase-Specific File Paths:**
       - `src/mkobi/core/security.py`
       - `src/mkobi/core/permissions.py`
       - `src/mkobi/api/routes/auth.py`
       - `src/mkobi/api/routes/upload.py`
       - `src/mkobi/api/deps.py`
       - `src/mkobi/config.py`
       - `src/mkobi/models/enums.py`
       - `frontend/src/shared/api/axiosInstance.ts`
       - `frontend/src/shared/components/ProtectedRoute.tsx`
       - `frontend/src/shared/components/RoleBasedAccess.tsx`

    3. **Checklist:**
       - [ ] JWT: algorithm explicitly set, expiration, invalid/missing token handling, secret in env
       - [ ] Passwords: bcrypt (not md5/SHA/plaintext), `secrets.token_urlsafe(16)` for temp passwords, no password logging
       - [ ] Dashboard access: checked on every request, admin bypass, 403/404 dual-signal
       - [ ] Roles: `UserRole` StrEnum used (not string literals)
       - [ ] Permissions: `DashboardPermission` StrEnum used
       - [ ] Upload: MIME-type, extension, encoding, size, path traversal, temp cleanup, rate limiting
       - [ ] SQL: parameterized queries, no f-string SQL
       - [ ] Secrets: no hardcoded, env-based, Docker secrets `_FILE` support, production enforcement
       - [ ] Rate limiting: Redis sliding window, fail-open/closed, protected endpoints
       - [ ] Email domain blocklist: backend Pydantic + frontend Zod validation
       - [ ] StrEnum: all 17 classes present, no string literal comparisons
       - [ ] Frontend security: JWT not in localStorage, ProtectedRoute, RoleBasedAccess

    4. **Report format:** Same as audit-findings.md. Findings prefixed with `SEC-` prefix.

    **Acceptance criteria:**
    - File exists with valid YAML frontmatter
    - Content covers all security dimensions (JWT, access, upload, secrets, SQL, rate limiting, StrEnum)
    - Contains security-specific file paths
    - Uses `SEC-` finding ID prefix
  </details>
  <validation>
    - File exists at `.kilo/commands/audit/phases/04-audit-security.md`
    - Covers all security areas from source blocks
    - Security-specific file paths included
  </validation>
</task>
```

---

### T10 — Create `05-audit-docker.md` Phase Template

```xml
<task id="T10" wave="2" depends_on="T05" files_modified="true" autonomous="true">
  <action>
    Create the Docker and runtime audit phase template.
    Extract content from: audit-docker.md.
  </action>
  <frontmatter>
    wave: 2
    depends_on: T05
    files_modified:
      - .kilo/commands/audit/phases/05-audit-docker.md
    autonomous: true
  </frontmatter>
  <details>
    Create file: `.kilo/commands/audit/phases/05-audit-docker.md`

    Source: Extract and adapt from `.kilo/commands/audit/docker/audit-docker.md`

    **Phase template structure:**

    YAML frontmatter:
    ```yaml
    ---
    name: audit-docker
    description: Docker and runtime environment audit covering Dockerfile, docker-compose, container health, security, persistence, production readiness, runtime verification
    agent: audit-executor
    alwaysApply: false
    ---
    ```

    Body structure:

    1. **Base Layer Context** (same as all phases)

    2. **Phase-Specific File Paths:**
       - `docker/Dockerfile`
       - `docker/docker-compose.yml`
       - `docker/docker-compose.override.yml`
       - `docker/docker-compose.test.yml`
       - `docker/.dockerignore`
       - `.env`

    3. **Checklist (adapted from audit-docker.md):**
       - [ ] Dockerfile: multi-stage (base/dev/test/prod/prod-slim), pinned base images, no secrets baked, non-root user
       - [ ] uv.lock: pinned dependencies, no floating versions
       - [ ] Docker compose: service separation (app/db/redis), volumes, restart policies, networking
       - [ ] Environment variables: correct names, production enforcement (`${VAR:?...}`), no hardcoded secrets
       - [ ] Health checks: db (`pg_isready`), app (HTTP `/health`), configured intervals/retries
       - [ ] Persistence: `postgres_data`, `app_data` volumes, stale temp file cleanup on startup
       - [ ] Security: non-root container, `.env` not in image, no secrets baked
       - [ ] Production readiness: structured logging, debug disabled, CORS configured, `AUTO_MIGRATE`
       - [ ] Frontend service: correct startup, responds on port 5173, proxy to backend works

    4. **Runtime Verification Steps** (condensed from audit-docker.md Step 1):
       - `docker compose up -d` → check all containers running/healthy
       - Check logs for ERROR/FATAL per service
       - Test inter-service connectivity (app→db, frontend→app)
       - Verify health endpoint responds

    5. **Report format:** Same as audit-findings.md. Findings prefixed with `DKR-` prefix.

    **Acceptance criteria:**
    - File exists with valid YAML frontmatter
    - Content extracted from audit-docker.md
    - Condensed checklist covering Dockerfile, compose, health, security, runtime verification
    - Includes runtime verification steps
    - Uses `DKR-` finding ID prefix
  </details>
  <validation>
    - File exists at `.kilo/commands/audit/phases/05-audit-docker.md`
    - Source is audit-docker.md
    - Runtime verification steps included
  </validation>
</task>
```

---

### T11 — Create `06-audit-tests.md` Phase Template

```xml
<task id="T11" wave="2" depends_on="T05" files_modified="true" autonomous="true">
  <action>
    Create the tests audit phase template.
    Extract content from: audit-tests-full.md.
  </action>
  <frontmatter>
    wave: 2
    depends_on: T05
    files_modified:
      - .kilo/commands/audit/phases/06-audit-tests.md
    autonomous: true
  </frontmatter>
  <details>
    Create file: `.kilo/commands/audit/phases/06-audit-tests.md`

    Source: Extract and adapt from `.kilo/commands/audit/tests/audit-tests-full.md`

    **Phase template structure:**

    YAML frontmatter:
    ```yaml
    ---
    name: audit-tests
    description: Test quality audit covering coverage gaps, anti-patterns (overmocking, contract mismatch, tautological tests), pytest standards, test database isolation, missing critical path coverage
    agent: audit-executor
    alwaysApply: false
    ---
    ```

    Body structure:

    1. **Base Layer Context** (same as all phases)

    2. **Phase-Specific File Paths:**
       - `tests/**/*.py`
       - `tests/conftest.py`
       - `docs/06-backend/testing.md`

    3. **Checklist (condensed from audit-tests-full.md):**

       **Anti-patterns to flag:**
       - [ ] Architecture mismatch: sync in async tests, deprecated methods, `pandas` instead of `polars`
       - [ ] Overmocking: mock replaces all logic, assertions on mock values not real results
       - [ ] Tautological: `assert True`, no assert, trivial checks
       - [ ] Wrong abstraction: testing private methods, SQL internals, call order
       - [ ] Fragile: depends on execution order, shared mutable state, no `pytest.mark.asyncio`

       **Coverage areas:**
       - [ ] Auth: login (`TokenWithUser`), refresh, roles, admin bypass, 403/404 dual-signal
       - [ ] API: all endpoints (success + error cases)
       - [ ] Processing: CSV loading (Polars), transformations, aggregations, formula parser, JSONB normalization
       - [ ] Repositories: CRUD, JSONB queries, UPSERT
       - [ ] Config: loading, production enforcement
       - [ ] Task queue: enqueue, status tracking, background worker
       - [ ] Pydantic models: all request/response models, validators, StrEnum

       **Infrastructure:**
       - [ ] pytest standards: `pytest.mark.asyncio`, fixtures in conftest, no `unittest.TestCase`
       - [ ] Test database: separate `bidb_test`, SAVEPOINT rollback, NullPool
       - [ ] Fixture structure matches `docs/06-backend/testing.md`

    4. **Report format:** Same as audit-findings.md. Findings prefixed with `TST-` prefix.

    **Acceptance criteria:**
    - File exists with valid YAML frontmatter
    - Content extracted from audit-tests-full.md
    - Anti-patterns + coverage areas + infrastructure checklist included
    - Uses `TST-` finding ID prefix
  </details>
  <validation>
    - File exists at `.kilo/commands/audit/phases/06-audit-tests.md`
    - Source is audit-tests-full.md
    - Anti-patterns and coverage areas covered
  </validation>
</task>
```

---

### T12 — Create `07-audit-data-processing.md` Phase Template

```xml
<task id="T12" wave="2" depends_on="T05" files_modified="true" autonomous="true">
  <action>
    Create the data processing audit phase template.
    Extract content from: audit-project-detailed.md blocks 4, 5, 9.
  </action>
  <frontmatter>
    wave: 2
    depends_on: T05
    files_modified:
      - .kilo/commands/audit/phases/07-audit-data-processing.md
    autonomous: true
  </frontmatter>
  <details>
    Create file: `.kilo/commands/audit/phases/07-audit-data-processing.md`

    Source: Extract and adapt from `.kilo/commands/audit/project/audit-project-detailed.md`

    **Extract blocks:**
    - BLOCK 4 — Data Processing (Polars)
    - BLOCK 5 — PostgreSQL Layer (storage-specific aspects)
    - BLOCK 9 — Task Queue & Background Processing

    **Phase template structure:**

    YAML frontmatter:
    ```yaml
    ---
    name: audit-data-processing
    description: Data processing audit covering Polars pipeline, loaders, transformations, aggregations, formula parser, storage, task queue, background worker, resource cleanup
    agent: audit-executor
    alwaysApply: false
    ---
    ```

    Body structure:

    1. **Base Layer Context** (same as all phases)

    2. **Phase-Specific File Paths:**
       - `src/mkobi/data/loaders/loader.py`
       - `src/mkobi/data/loaders/validator.py`
       - `src/mkobi/data/processing/transformations.py`
       - `src/mkobi/data/processing/registry.py`
       - `src/mkobi/data/storage/manager.py`
       - `src/mkobi/core/task_queue.py`
       - `src/mkobi/workers/data_worker.py`
       - `src/mkobi/services/file_processing.py`

    3. **Checklist:**
       - [ ] Polars only: no `import pandas`, all transformations via Polars
       - [ ] Loaders: CSV/CSV.gz support, schema validation, error handling for corrupted files
       - [ ] Transformations: group_by, YoY (absolute/percent), shares, custom metrics
       - [ ] Formula parser: supports `+`, `-`, `*`, `/`, clear errors for invalid formulas
       - [ ] Storage: JSONB write, dims key sorted recursively, UPSERT determinism
       - [ ] Pipeline: upload → parse → transform → aggregate → save → cleanup
       - [ ] Resource cleanup: `platformdirs`, `finally` blocks, success + failure cleanup
       - [ ] Transaction handling: atomic processing, rollback on failure
       - [ ] Task queue: `asyncio.Queue`, lifecycle tracking (`STARTED` → `PROCESSING` → `SUCCESS`/`FAILED`)
       - [ ] Background worker: full pipeline in worker, processing log updates at each stage

    4. **Report format:** Same as audit-findings.md. Findings prefixed with `DP-` prefix.

    **Acceptance criteria:**
    - File exists with valid YAML frontmatter
    - Content extracted from blocks 4, 5, 9
    - Covers full data pipeline from upload to storage
    - Covers task queue and background worker
    - Uses `DP-` finding ID prefix
  </details>
  <validation>
    - File exists at `.kilo/commands/audit/phases/07-audit-data-processing.md`
    - Source blocks 4, 5, 9
    - Pipeline stages checklist complete
  </validation>
</task>
```

---

### T13 — Create `08-audit-deployment-config.md` Phase Template

```xml
<task id="T13" wave="2" depends_on="T05" files_modified="true" autonomous="true">
  <action>
    Create the deployment and config audit phase template.
    Extract content from: audit-project-detailed.md blocks 10, 11.
  </action>
  <frontmatter>
    wave: 2
    depends_on: T05
    files_modified:
      - .kilo/commands/audit/phases/08-audit-deployment-config.md
    autonomous: true
  </frontmatter>
  <details>
    Create file: `.kilo/commands/audit/phases/08-audit-deployment-config.md`

    Source: Extract and adapt from `.kilo/commands/audit/project/audit-project-detailed.md`

    **Extract blocks:**
    - BLOCK 10 — Performance & Stability
    - BLOCK 11 — Configuration & Deployment
    - (Condense BLOCK 12 — No Overengineering Check into checklist intro)

    **Phase template structure:**

    YAML frontmatter:
    ```yaml
    ---
    name: audit-deployment-config
    description: Deployment and configuration audit covering config management, startup lifecycle, deployment options, performance, stability, no-overengineering check
    agent: audit-executor
    alwaysApply: false
    ---
    ```

    Body structure:

    1. **Base Layer Context** (same as all phases)

    2. **Phase-Specific File Paths:**
       - `src/mkobi/config.py`
       - `src/mkobi/settings/app.yaml`
       - `src/mkobi/db/starter.py`
       - `src/mkobi/app.py`
       - `docker/Dockerfile`
       - `docker/docker-compose.yml`
       - `docker/docker-compose.override.yml`
       - `.env`, `.env.example`

    3. **Checklist:**
       - [ ] Config: Pydantic-settings, priority chain (env > Docker secrets > .env > app.yaml > defaults)
       - [ ] Docker secrets: `_FILE` suffix support, `.env` for dev only
       - [ ] Startup lifecycle: DB check → schema check → migrations → admin user creation → stale file cleanup → ready
       - [ ] Production credential enforcement: refuses to start with default `admin`/`admin`
       - [ ] Deployment options: dev (React dev + FastAPI), prod (static files via FastAPI or Nginx)
       - [ ] Performance: JSONB GIN index, connection pooling, N+1 checks, rate limiting
       - [ ] Stability: error isolation, timeout handling, CORS
       - [ ] No overengineering: no Redux/Zustand, no unnecessary abstractions, TanStack Query sufficient

    4. **Report format:** Same as audit-findings.md. Findings prefixed with `DC-` prefix.

    **Acceptance criteria:**
    - File exists with valid YAML frontmatter
    - Content extracted from blocks 10, 11 (plus 12 as condensed note)
    - Covers config, startup, deployment, performance, stability
    - Uses `DC-` finding ID prefix
  </details>
  <validation>
    - File exists at `.kilo/commands/audit/phases/08-audit-deployment-config.md`
    - Source blocks 10, 11
    - Config and deployment checklist complete
  </validation>
</task>
```

---

## Wave 3 — Verification

### T14 — Verify All Files Created Correctly

```xml
<task id="T14" wave="3" depends_on="T06,T07,T08,T09,T10,T11,T12,T13" files_modified="false" autonomous="true">
  <action>
    Verify all files from Waves 1 and 2 exist, have correct structure, and are internally consistent.
  </action>
  <frontmatter>
    wave: 3
    depends_on: T06, T07, T08, T09, T10, T11, T12, T13
    files_modified: false
    autonomous: true
  </frontmatter>
  <details>
    Verification checklist — run through every file created in this plan:

    **Template files (2):**
    - [ ] `.kilo/commands/audit/templates/audit-findings.md` — has all 9 mandatory fields + Summary + 3 classification sections
    - [ ] `.kilo/commands/audit/templates/audit-final-report.md` — has all 6 sections + scoring + merge strategy

    **Agent files (2):**
    - [ ] `.kilo/agents/audit-executor.md` — YAML frontmatter complete, permissions scoped, generic (no domain specialization), references findings template
    - [ ] `.kilo/agents/audit-orchestrator.md` — YAML frontmatter complete, read-only permissions, pipeline stages defined, retry logic, deprecation note for auditor.md

    **Phase templates (9):**
    | # | File | Finding Prefix | Source |
    |---|------|---------------|--------|
    | 1 | `01-audit-backend.md` | `BE-` | blocks 1,2,3,7 |
    | 2 | `02-audit-frontend.md` | `FE-` | blocks 1.2,6,8 |
    | 3 | `03-audit-database.md` | `DB-` | audit-db-structure.md |
    | 4 | `04-audit-security.md` | `SEC-` | blocks 3,7.3,8.1 |
    | 5 | `05-audit-docker.md` | `DKR-` | audit-docker.md |
    | 6 | `06-audit-tests.md` | `TST-` | audit-tests-full.md |
    | 7 | `07-audit-data-processing.md` | `DP-` | blocks 4,5,9 |
    | 8 | `08-audit-deployment-config.md` | `DC-` | blocks 10,11 |
    | 9 | `09-audit-integration.md` | `INT-` | newly created (cross-cutting) |

    **Cross-consistency checks:**
    - [ ] All 9 phase template filenames follow `NN-audit-X.md` naming convention (zero-padded)
    - [ ] All 9 phase templates have consistent YAML frontmatter format (name, description, agent, alwaysApply)
    - [ ] All 9 phase templates contain both Base Layer context reference AND Phase-Specific file paths
    - [ ] All 9 phase templates specify the audit-executor agent
    - [ ] All 9 phase templates use unique finding ID prefixes (no duplicates)
    - [ ] All 9 phase templates reference the audit-findings.md template for report format
    - [ ] `09-audit-integration.md` explicitly states it depends on all 8 silo phase findings
    - [ ] `audit-orchestrator.md` references all 9 phase templates by filename
    - [ ] Phase template numbering matches the locked decision: 01=Backend, 02=Frontend, 03=Database, 04=Security, 05=Docker, 06=Tests, 07=Data Processing, 08=Deployment/Config, 09=Integration

    **File count verification:**
    - 2 templates + 2 agents + 9 phases = 13 new/updated files total
  </details>
  <validation>
    - All 13 files exist
    - All YAML frontmatter blocks are valid
    - All finding ID prefixes are unique
    - All phase templates reference correct source audit commands
    - orchestrator.md references executor.md and validator.md
    - No production code was modified
  </validation>
</task>
```

---

## Dependency Graph

```
T01 (findings template)
 └─> T02 (report template)
      └─> T03 (executor agent)
           └─> T04 (orchestrator agent)
                └─> T05 (integration phase)
                     ├─> T06 (backend phase) ─┐
                     ├─> T07 (frontend phase) ─┤
                     ├─> T08 (database phase) ─┤
                     ├─> T09 (security phase) ─┤---> T14 (verification)
                     ├─> T10 (docker phase)    ─┤
                     ├─> T11 (tests phase)     ─┤
                     ├─> T12 (data proc phase) ─┘
                     └─> T13 (deploy/config phase)
```

---

## Rollout Ordering

| Order | Task | Wave | Notes |
|-------|------|------|-------|
| 1 | T01 | 1 | Findings template — prerequisite for everything |
| 2 | T02 | 1 | Report template — needed by orchestrator |
| 3 | T03 | 1 | Executor agent — needed by all phases |
| 4 | T04 | 1 | Orchestrator agent — needed to understand pipeline flow |
| 5 | T05 | 1 | Integration phase — defined first so silos know they feed into it |
| 6-13 | T06-T13 | 2 | All silo phases — independent, parallel execution |
| 14 | T14 | 3 | Final verification — depends on all above |

---

## Files Created/Modified

### New files (13):

| # | File Path |
|---|-----------|
| 1 | `.kilo/commands/audit/templates/audit-findings.md` |
| 2 | `.kilo/commands/audit/templates/audit-final-report.md` |
| 3 | `.kilo/agents/audit-executor.md` |
| 4 | `.kilo/agents/audit-orchestrator.md` |
| 5 | `.kilo/commands/audit/phases/01-audit-backend.md` |
| 6 | `.kilo/commands/audit/phases/02-audit-frontend.md` |
| 7 | `.kilo/commands/audit/phases/03-audit-database.md` |
| 8 | `.kilo/commands/audit/phases/04-audit-security.md` |
| 9 | `.kilo/commands/audit/phases/05-audit-docker.md` |
| 10 | `.kilo/commands/audit/phases/06-audit-tests.md` |
| 11 | `.kilo/commands/audit/phases/07-audit-data-processing.md` |
| 12 | `.kilo/commands/audit/phases/08-audit-deployment-config.md` |
| 13 | `.kilo/commands/audit/phases/09-audit-integration.md` |

### Existing files referenced (not modified):
- `.kilo/agents/validator.md` — reused unchanged
- `.kilo/agents/auditor.md` — deprecated, kept for reference
- `.kilo/commands/audit/project/audit-project-detailed.md` — source for T06, T07, T09, T12, T13
- `.kilo/commands/audit/db/audit-db-structure.md` — source for T08
- `.kilo/commands/audit/docker/audit-docker.md` — source for T10
- `.kilo/commands/audit/tests/audit-tests-full.md` — source for T11
- `.ai/structure/map.md` — structure context for orchestrator
- `.ai/context/commands.md` — verification commands for orchestrator
- `docs/SPEC.md` — project purpose for orchestrator

---

## Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| Phase template content divergence from source audit commands | Low | Each task explicitly lists source blocks to extract |
| Overlapping checklist items between phases | Low | Cross-cutting items explicitly assigned to Phase 9 (Integration) |
| Orchestrator permissions too permissive | Low | T04 explicitly defines read-only permissions |
| Findings format inconsistency across phases | Low | T01 defines one template used by all phases |
| Missing file paths in phase-specific context | Low | Each task lists specific file paths from structure maps |
| No production code modified | None | All changes are documentation/infrastructure only |
