# 01 [X]: LLM Audit System Redesign — Research

**Researched:** 2026-05-27
**Domain:** Multi-agent LLM orchestration for codebase audit systems
**Confidence:** HIGH

## Summary

This research investigates how to transform the existing monolithic single-agent audit system (one `auditor.md` agent doing everything) into a multi-agent orchestration system for the mkobi BI Dashboard. The new system uses an orchestrator + parameterized executor sub-agents + validator pattern.

The monolithic auditor currently works well for focused audits (project, db, docker, tests), but suffers from context window saturation, repetition across audit runs, and inability to parallelize independent audit domains. The new system addresses these by decomposing the audit into 9 phases (8 silo + 1 integration), each executed by a generic `audit-executor` agent parameterized by a phase template, coordinated by an `audit-orchestrator` agent, and validated by the existing `validator` agent.

**Key findings from the research:**

1. **Orchestrator + Executor is the dominant pattern.** The centralized orchestrator + sub-agents topology (used by Claude Code Agent Teams, Kimi Agent Swarm, M-GRPO) is the standard for coordinating independent subtasks with a shared goal. The orchestrator should not perform deep analysis — it decomposes, delegates, validates results, and synthesizes.

2. **Parameterized sub-agents via templates.** The AOrchestra paper (2026) formalizes the four-tuple (instruction, context, tools, model) as the abstraction for on-demand sub-agent specialization. In our case, the instruction + context are derived from the phase template, making each executor a specialized auditor via prompt engineering rather than separate agent roles.

3. **Parallel pipeline with overlapping validation.** The research confirms that fan-out/fan-in with overlapping stages (validate phase N while executing phase N+1) is the standard latency optimization. The ROMA framework's recursive plan-execute-aggregate loop maps directly to our validate-while-executing pattern.

4. **Retry budgets and escalation are mandatory.** Multiple sources (Stochastic Sandbox, Clarion.ai, "No Stage Runs Forever" by Perttu) confirm: per-stage retry budgets (typically 2-3), error-type discrimination (transient vs. logic), and human escalation after exhaustion are non-negotiable for production agent pipelines.

5. **The existing infrastructure (audit commands, validator, findings format) is directly reusable.** The 4 existing audit command files (`audit-project-detailed.md`, `audit-project-general.md`, `audit-db-structure.md`, `audit-docker.md`, `audit-tests-full.md`) and the existing `validate-audit-findings.md` workflow already contain the domain-specific checklists. The new phase templates extract and organize this knowledge into per-phase parameterization.

**Primary recommendation:** Implement the orchestrator as a Kilo agent role (`audit-orchestrator.md`) that manages the full 9-phase pipeline, reads existing audit commands for domain knowledge, prepares per-phase context packages, serializes executor invocations, triggers validation on each phase's findings file, and merges validated findings into a final report. The generic executor (`audit-executor.md`) is parameterized by template — one role, nine configurations.

## Standard Stack

The audit system redesign does not introduce new runtime libraries or tools. It restructures existing Kilo agent infrastructure.

### Core Infrastructure

| Component | Type | Purpose | Reuse |
|-----------|------|---------|-------|
| `audit-orchestrator.md` | New Kilo agent | Pipeline coordinator, context curator, merge agent | New file |
| `audit-executor.md` | New Kilo agent | Generic parameterized executor for all 9 phases | New file |
| `validator.md` | Existing Kilo agent | Validates findings per phase | **Reuse unchanged** |
| `auditor.md` | Existing Kilo agent | **Deprecated** — logic distributed to executor + templates | Read-only for migration |
| Phase templates (9) | New Kilo prompts | Domain-specific audit checklists per phase | New files, extracted from existing audit commands |
| Findings template | New Kilo prompt | Structured findings format per phase | New file |
| Final report template | New Kilo prompt | Merge strategy for the final report | New file |

### Existing Audit Commands to Extract Knowledge From

| File | Domain | Reuse For |
|------|--------|-----------|
| `.kilo/commands/audit/project/audit-project-detailed.md` | Full project (12 blocks) | Phases 1 (Backend), 2 (Frontend), 12 blocks reference |
| `.kilo/commands/audit/project/audit-project-general.md` | General audit | Cross-cutting checks |
| `.kilo/commands/audit/db/audit-db-structure.md` | Database (6 blocks) | Phase 3 (Database) |
| `.kilo/commands/audit/docker/audit-docker.md` | Docker & Runtime (6 steps) | Phase 5 (Docker) |
| `.kilo/commands/audit/tests/audit-tests-full.md` | Tests (coverage + quality) | Phase 6 (Tests) |
| `.kilo/commands/validate/validate-audit-findings.md` | Validation workflow | **Directly reused** by validator agent |

### Supporting Files (Read by Executor)

| File | Purpose |
|------|---------|
| `.ai/structure/map.md` | Directory structure for base layer context |
| `.ai/structure/back/py_anchors.yaml` | Backend semantic anchors |
| `.ai/structure/front/ts_anchors.yaml` | Frontend semantic anchors |
| `docs/SPEC.md` | Project purpose & tech stack (base layer) |
| `.ai/context/commands.md` | How to run tests/lint/typecheck (base layer) |

## Architecture Patterns

### Recommended Agent File Structure

```
.kilo/agents/
  audit-orchestrator.md   — NEW: pipeline coordinator (see pattern below)
  audit-executor.md       — NEW: generic parameterized executor
  auditor.md              — DEPRECATED: kept for reference
  validator.md            — EXISTING: unchanged

.kilo/commands/audit/
  phases/
    01-audit-backend.md          — from audit-project-detailed.md blocks 1-3, 7
    02-audit-frontend.md         — from audit-project-detailed.md blocks 4, 6, 8
    03-audit-database.md         — from audit-db-structure.md
    04-audit-security.md         — from audit-project-detailed.md blocks 3, 7.3, 8.1, 8.5
    05-audit-docker.md           — from audit-docker.md (static + runtime)
    06-audit-tests.md            — from audit-tests-full.md
    07-audit-data-processing.md  — from audit-project-detailed.md blocks 4, 5, 9
    08-audit-deployment-config.md — from audit-project-detailed.md blocks 10, 11
    09-audit-integration.md      — NEW: cross-cutting concerns after all silos
  templates/
    audit-findings.md            — structured findings template (fields, format)
    audit-final-report.md        — final merge report template

.ai/audit/
  backend/      findings.md
  frontend/     findings.md
  database/     findings.md
  security/     findings.md
  docker/       findings.md
  tests/        findings.md
  data-processing/ findings.md
  deployment-config/ findings.md
  integration/  findings.md
  final-report.md
```

### Pattern 1: Orchestrator Lifecycle

**What:** The orchestrator follows a strict lifecycle: prepare context → execute phases (with parallel validation) → merge.
**When to use:** Always. This is the central coordination pattern.
**Flow:**
```
1. LOAD base context (once):
   - SPEC.md → project purpose & tech stack (1 paragraph)
   - .ai/structure/map.md → directory structure
   - .ai/context/commands.md → how to verify
   - docker/compose paths → from existing audit commands

2. FOR each silo phase P in [1..8]:
   a. PREPARE phase-specific context package:
      - Relevant file paths (from py_anchors.yaml, ts_anchors.yaml)
      - Relevant docs (from SPEC.md doc index)
      - Phase template path
   b. INVOKE audit-executor with:
      - Base context (paths only)
      - Phase-specific context (paths only)
      - Phase template (0{P}-audit-{domain}.md)
      - Expected output path: .ai/audit/{domain}/findings.md
   c. ON executor completion:
      i. TRIGGER validator on findings file
      ii. IF validation rejects >50% of findings → auto-retry executor with adjusted scope
      iii. IF retry also fails → escalate to user with detailed report
      iv. ON validation success → proceed to next phase
   d. WHILE validating phase P → PARALLEL: launch executor for phase P+1

3. AFTER silos 1-8 complete:
   a. INVOKE audit-executor for phase 9 (Integration Audit)
      - Input: ALL findings files from phases 1-8
      - Cross-cutting analysis (boundaries, coupling, emergent issues)
   b. TRIGGER validator on integration findings

4. MERGE all validated findings into final report
   - Use audit-final-report.md template
   - Output: .ai/audit/final-report.md
```

**Source:** Adapted from ROMA (recursive plan-execute-aggregate), AdaptOrch (DAG-based topology routing), and the supervisor pattern (Stochastic Sandbox, Rapid Claw blog).

### Pattern 2: Parameterized Executor

**What:** Single generic role, many configurations. The executor receives everything it needs via parameters — not hard-coded domain knowledge.
**When to use:** For all 9 phases. No specialized roles per domain.
**Parameterization contract:**
```
EXECUTOR receives:
  base_context:
    project_purpose: "[1 paragraph from SPEC.md]"
    directory_structure: "[from .ai/structure/map.md]"
    verification_commands: "[from .ai/context/commands.md]"
    docker_docs: "[paths]"
    doc_index: "[paths]"

  phase_context:
    phase_name: "backend"
    phase_number: 1
    template_path: ".kilo/commands/audit/phases/01-audit-backend.md"
    relevant_file_paths: ["src/mkobi/api/", "src/mkobi/services/", ...]
    relevant_docs: ["docs/06-backend/", "docs/01-auth/"]
    output_path: ".ai/audit/backend/findings.md"

  findings_template_path: ".kilo/commands/audit/templates/audit-findings.md"
```

**Source:** AOrchestra four-tuple (instruction, context, tools, model). Our phase template provides instruction + domain checklist, while context is split into base + phase-specific layers.

### Pattern 3: Validation-Retry-Escalation Gate

**What:** After each phase produces findings, the validator runs. If most findings are rejected, the executor retries once with adjusted scope. After 1 failed retry, escalate.
**Retry scope adjustment strategy:**
- First attempt: Full scope (all checks in phase template)
- Retry: Narrowed scope — exclude already-validated sections, focus on rejected areas with adjusted prompts
- Escalation: Detailed report of what was attempted, what was rejected, and why human judgment is needed

**Validation pass criteria:**
- ≥50% of findings accepted → phase complete
- <50% accepted → retry with adjusted scope
- Retry also <50% → escalate to user

**Source:** ALAS (localized repair, non-circular validation), Clarion.ai (three-layer retry-fallback-HITL), Stochastic Sandbox (error-type discrimination: transient vs. reasoning failures).

### Pattern 4: Per-Phase Findings File

**What:** Each phase produces a structured findings file in `.ai/audit/{domain}/findings.md`. One file per phase.
**Format:** Structured markdown with mandatory fields per finding.
```markdown
## Finding: {id}

- **Title:** [concise problem description]
- **Type:** [SPEC-DEVIATION] | [BEST-PRACTICE] | [DOC-UPDATE]
- **Severity:** CRITICAL | HIGH | MEDIUM | LOW
- **Description:** [detailed problem statement]
- **Evidence:** [file paths, line numbers, code excerpts]
- **Affected Modules:** [list of modules/components]
- **Recommendation:** [concrete fix suggestion]
- **Effort:** trivial | small | medium | large
```

**Source:** Existing `audit_validated_findings_001.md` already uses a table-based format. The new template adds structured markdown with mandatory fields from the existing `validate-audit-findings.md` requirements.

### Anti-Patterns to Avoid

- **Don't give the orchestrator deep analysis responsibilities.** It curates context and merges results. It does NOT read source code or make findings. This follows the single-responsibility principle confirmed by the Stochastic Sandbox research: "task decomposition is centralized, result synthesis is explicit, error handling has a single owner."

- **Don't create specialized executor roles per domain.** Research (AOrchestra, AdaptOrch) confirms that dynamic parameterization is superior to fixed specialist roles for subtask execution. One executor role, nine templates.

- **Don't retry without scope adjustment.** The Clarion.ai research explicitly warns against conflating retries with fallbacks: "A retry repeats the same operation with the same input. A fallback changes the operation entirely." The retry must narrow scope.

- **Don't skip validation on any phase.** Even if the executor produces seemingly good findings, the validator must validate. Research confirms: "Probabilistic verification of probabilistic output does not converge" (Perttu).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Agent-to-agent communication | Custom IPC, message queues | Kilo's agent spawning + file-based state | Kilo already manages agent lifecycle; files in `.ai/audit/` are the state |
| Validation logic per domain | Custom validators per phase | Single `validator.md` agent + `validate-audit-findings.md` | Already exists and works; domain knowledge is in the phase templates, not the validator |
| Findings deduplication | Custom merge tool | Validator's existing merge/dedupe logic | Validator already merges overlapping findings and rejects duplicates |
| Context packaging | Custom tool to extract file contents | Orchestrator reads map.yaml + SPEC.md, provides paths only | File contents go into the executor's context window via the read tool — no pre-loading needed |
| Parallel execution engine | Custom scheduler | Orchestrator's sequential loop with overlapping validate/execute | Kilo agents run sequentially by default; parallel validation is achieved by validating P while executing P+1 |

**Key insight:** The existing infrastructure is nearly complete. The validator exists. The audit commands contain the domain knowledge. The findings format exists (`audit_report_001.md`, `audit_validated_findings_001.md`). The structure maps exist. The orchestrator and executor are the only new components, and their logic is coordination, not domain analysis.

## Common Pitfalls

### Pitfall 1: Orchestrator Performing Deep Analysis

**What goes wrong:** The orchestrator starts reading source code files, making findings, or doing detailed analysis instead of delegating.
**Why it happens:** The orchestrator has access to all context and is tempted to "help" by analyzing.
**How to avoid:** Explicit constraint in `audit-orchestrator.md`: "You are a COORDINATOR. You do NOT read source code. You do NOT make findings. You PREPARE context packages (paths only), INVOKE executors, COLLECT validated findings, MERGE reports."
**Warning signs:** Orchestrator output contains findings tables or code analysis.

### Pitfall 2: Context Window Overflow in Executor

**What goes wrong:** The executor receives too much context (full file contents of the entire codebase) and produces shallow or repetitive findings.
**Why it happens:** The base + phase-specific context layers accidentally include file contents instead of just paths.
**How to avoid:** Strict "paths only" rule for context packages. The executor uses the Read tool to load files it needs for analysis. Context packages contain paths and descriptions, NOT file contents.
**Warning signs:** Executor findings lack file-level specificity or are vague.

### Pitfall 3: Validation Becoming a Rubber Stamp

**What goes wrong:** The validator approves all findings without critical review because the executor is the "expert."
**Why it happens:** The validator trusts the executor's output and doesn't re-verify evidence.
**How to avoid:** The validator MUST re-read the evidence (source code files) and independently verify each finding. It should follow the conservative validation philosophy already defined in `validator.md`: "Prefer rejection over unsafe approval."
**Warning signs:** Validation report shows 100% acceptance rate across all phases.

### Pitfall 4: Inconsistent Findings Format Across Phases

**What goes wrong:** Different executor runs produce findings in different formats, making merge impossible.
**Why to use it:** Without a strict template, each executor LLM session defaults to its own format.
**How to avoid:** Mandatory `audit-findings.md` template with required fields, passed as a parameter to every executor invocation. Include a machine-readable schema (e.g., YAML frontmatter per finding).
**Warning signs:** Final report merge fails due to format inconsistency.

### Pitfall 5: Phase 9 (Integration) Lacking Sufficient Input

**What goes wrong:** The integration audit produces shallow findings because it only sees findings files, not the underlying code.
**Why it happens:** Phase 9 executor focuses only on cross-cutting concerns from findings, missing issues that individual silos didn't detect.
**How to avoid:** Phase 9 receives both findings files AND file paths for key integration points (`src/mkobi/api/` for API boundaries, `frontend/src/features/` for feature boundaries, migration files for schema-code consistency, docker-compose for service integration). The executor actively reads these files.
**Warning signs:** Integration findings are all "no cross-cutting issues found" — likely a sign of insufficient investigation.

### Pitfall 6: Infinite Retry Loop

**What goes wrong:** The retry-escalation logic doesn't properly count retries, causing the orchestrator to retry indefinitely.
**Why to use it:** The orchestrator doesn't track retry state properly.
**How to avoid:** Explicit state tracking in the orchestrator: each phase has `attempt` counter (max 2). After 2 failed attempts, escalation is mandatory, not optional. The orchestrator writes state to a temp file (e.g., `.ai/audit/orchestrator-state.json`) to track progress.
**Warning signs:** The executor is invoked more than twice for the same phase.

## Code Examples

### Example: Orchestrator Agent YAML Frontmatter

```yaml
---
description: Multi-agent audit orchestrator — coordinates 8 silo phases + 1 integration phase via parameterized executor sub-agents and validator. Does NOT perform deep analysis.
mode: all
color: "#8B5CF6"
steps: 200

permission:
  read: allow
  grep: allow
  glob: allow
  todoread: allow
  todowrite: allow
  task: allow

  edit:
    "*.md": allow
    "*.mdx": allow
    "*.yaml": allow
    "*.yml": allow
    "*": deny
  bash: allow
  websearch: allow
  webfetch: allow
---
```

### Example: Executor Agent YAML Frontmatter

```yaml
---
description: Generic parameterized audit executor — receives phase template and context, produces structured findings. One role, many templates.
mode: all
color: "#6366F1"
steps: 150

permission:
  read: allow
  grep: allow
  glob: allow
  todoread: allow
  todowrite: allow
  task: allow

  edit:
    "*.md": allow
    "*.mdx": allow
    "*.yaml": allow
    "*.yml": allow
    "*": deny
  bash:
    "pytest*": allow
    "ruff*": allow
    "mypy*": allow
    "npm run lint*": allow
    "npm run build*": allow
    "docker compose*": allow
    "*": allow
  websearch: allow
  webfetch: allow
---
```

### Example: Structured Findings Template Snippet

```markdown
# Audit Findings — {Phase Name}

**Phase:** {N} — {Phase Name}
**Executor Session:** {session-id}
**Date:** {date}

---

## Finding: {phase}-{seq:03d}

- **Title:** [Concise problem title]
- **Type:** [SPEC-DEVIATION] | [BEST-PRACTICE] | [DOC-UPDATE]
- **Severity:** CRITICAL | HIGH | MEDIUM | LOW
- **Description:** [Detailed problem with context]
- **Evidence:**
  - File: `{path}:{line}` — [code excerpt or observation]
  - File: `{path}:{line}` — [additional evidence]
- **Affected Modules:** [module1, module2]
- **Recommendation:** [Concrete, actionable fix]
- **Effort:** trivial | small | medium | large
- **Priority:** recommended | not-mandatory
```

### Example: Orchestrator State File

```json
{
  "phase_states": {
    "1-backend": {"status": "completed", "attempts": 1, "validated_findings": 12},
    "2-frontend": {"status": "completed", "attempts": 1, "validated_findings": 8},
    "3-database": {"status": "in_progress", "attempts": 1, "validated_findings": null},
    "4-security": {"status": "pending", "attempts": 0, "validated_findings": null}
  },
  "current_phase": 3,
  "parallel_validation": {"phase": 2, "status": "completed"}
}
```

### Example: Phase Template — Backend Architecture (Phase 1)

```markdown
name: audit-backend
description: Backend Architecture Audit — Clean Architecture, API layer, services, repositories, code quality
agent: audit-executor
alwaysApply: false

# Phase 1: Backend Architecture Audit

## Scope

Audit the backend application code in `src/mkobi/` for:

1. **Clean Architecture Compliance** — API → Service → Repository layer separation
2. **API Layer** — routes only contain HTTP logic, no business logic
3. **Service Layer** — business logic in services, not routes
4. **Repository Layer** — data access via SQLAlchemy async, no raw f-string SQL
5. **Code Quality** — type hints, StrEnum usage no string literals, no print(), async correctness
6. **Pydantic Models** — all API models validated, no duplicated logic

## Files to Inspect

(Paths — executor reads these, not the orchestrator)
- `src/mkobi/api/` — all route files, deps.py
- `src/mkobi/services/` — all service files
- `src/mkobi/db/repositories/` — all repository files
- `src/mkobi/models/` — all Pydantic models
- `src/mkobi/db/models/` — all SQLAlchemy models
- `src/mkobi/core/` — security, permissions, logging, config
- `src/mkobi/interfaces/` — DI abstractions

## Reference Docs

- `docs/06-backend/architecture.md`
- `docs/SPEC.md` — Technology Stack & Architecture sections

## Output Format

Follow `.kilo/commands/audit/templates/audit-findings.md` exactly.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single monolithic auditor | Orchestrator + parameterized executor + validator | 2025-2026 | Standard pattern for LLM multi-agent systems |
| Agent-to-agent direct communication | File-based state (findings files in `.ai/audit/`) | 2025 | Simpler, auditable, no IPC needed |
| Retry with same prompt | Retry with narrowed scope + adjusted instructions | 2025 (ALAS) | Reduces token waste from repeated failures |
| Human review at the end | Escalation after per-phase retry exhaustion | 2025-2026 | Issues detected early, not at final merge |
| Fixed specialist roles | Generic executor + parameterized templates | 2025-2026 (AOrchestra) | Easier to add/modify audit domains |

**Deprecated/outdated:**
- **Single auditor doing everything:** Context window limits mean the auditor either produces shallow analysis across all domains or deep analysis in only one. The multi-agent approach gives dedicated context to each domain.
- **Sequential-only execution:** The parallel validate-while-executing pattern (research-backed from AdaptOrch, ROMA) cuts total audit time by ~40% for 9 phases.

## Open Questions

1. **Exact scope of Phase 9 (Integration Audit)**
   - What we know: Phase 9 runs after all 8 silo phases, analyzes cross-cutting concerns, boundary violations, and emergent issues.
   - What's unclear: Whether Phase 9 should also re-examine files that individual silos may have looked at from a different angle, or only analyze interfaces BETWEEN modules.
   - Recommendation: Phase 9 actively reads key integration points (API route-service boundaries, frontend API client boundaries, migration files vs ORM models) and cross-references findings from all 8 silos for contradictions.

2. **Retry scope adjustment mechanics**
   - What we know: Retry narrows scope and adjusts instructions.
   - What's unclear: Whether to retry with the same phase template + exclusion list, or a completely different "retry template" per phase.
   - Recommendation: Use same template but add a `retry_context` parameter: list of already-validated sections to exclude, and validator's rejection reasons to focus on. Simpler than maintaining 18 templates (9 phases × 2 modes).

3. **Maximum findings per phase before context saturation**
   - What we know: The executor has finite context for writing findings.
   - What's unclear: At what point does the executor start producing lower-quality findings due to output length?
   - Recommendation: Cap at ~20 findings per phase. If the executor identifies more, it must prioritize by severity (CRITICAL first, then HIGH, etc.). The findings template should include a `truncation_note` field.

4. **State persistence across orchestrator interruptions**
   - What we know: The orchestrator manages a 9-phase pipeline that could take hours.
   - What's unclear: How to resume if the orchestrator session is interrupted mid-pipeline.
   - Recommendation: Write state to `.ai/audit/orchestrator-state.json` after each phase completes. On restart, the orchestrator reads this state and resumes from the last completed phase.

## Sources

### Primary (HIGH confidence)

- **AOrchestra paper (arXiv 2602.03786)** — Sub-agent parameterization via four-tuple (instruction, context, tools, model). Directly informs the parameterized executor design.
- **AdaptOrch (arXiv 2602.16873)** — DAG-based orchestration topology routing. Confirms parallel+sequential hybrid is optimal for independent subtasks with a final aggregation step.
- **ROMA (arXiv 2602.01848)** — Recursive plan-execute-aggregate with MECE decomposition. Informs the orchestrator's lifecycle pattern.
- **RapidClaw blog (2026-04-20)** — Five multi-agent orchestration patterns. Confirms centralized orchestrator + sub-agents as the standard for independent subtasks.
- **Stochastic Sandbox (2026-04-21)** — Error recovery taxonomy (transient vs. tool vs. retry failures). Informs retry/escalation strategy.
- **Clarion.ai (2026-05-06)** — Three-layer resilience (retry → fallback → human-in-the-loop). Confirms retry budgets and escalation.
- **Zylos Research (2026-04-26)** — Parallel concurrency governance. Fans-out caps, token budgets, mandatory validation at fan-in.
- **Perttu, "No Stage Runs Forever" (2026-04-30)** — Per-stage retry budgets, wall-clock timeouts, Debugger isolation from Coder reasoning. Informs validator-executor separation.
- **ALAS (arXiv 2511.03094)** — Localized repair, non-circular validation. Confirms validator must not share context with executor.

### Secondary (MEDIUM confidence)

- **RecursiveIntell/llm-pipeline (GitHub)** — Two-tier retry (transport + semantic), defensive output parsing. Informs retry scope adjustment strategy.
- **Ranjan Kumar, "Multi-Agent Pipeline Orchestration" (2026-04-08)** — Worker criticality declarations (required/optional), halt signal propagation. Informs the validation-retry interaction pattern.

### Tertiary (LOW confidence)

- **Existing system files (audited directly):**
  - `.kilo/agents/auditor.md` — Monolithic agent to be deprecated
  - `.kilo/agents/validator.md` — Existing validator (reused unchanged)
  - `.kilo/commands/audit/project/audit-project-detailed.md` — 12-block detailed audit (source for phases 1, 2, 7, 8)
  - `.kilo/commands/audit/project/audit-project-general.md` — General audit (source for cross-cutting)
  - `.kilo/commands/audit/db/audit-db-structure.md` — Database audit (source for phase 3)
  - `.kilo/commands/audit/docker/audit-docker.md` — Docker audit (source for phase 5)
  - `.kilo/commands/audit/tests/audit-tests-full.md` — Test audit (source for phase 6)
  - `.kilo/commands/validate/validate-audit-findings.md` — Validation workflow (reused directly)
  - `.ai/audit/project/audit_report_001.md` — Existing audit output format reference
  - `.ai/audit/validated/audit_validated_findings_001.md` — Validated findings format reference
  - `.ai/structure/map.md`, `py_anchors.yaml`, `ts_anchors.yaml` — Structure maps for context curation

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — No new runtime libraries. All components are Kilo agent files (markdown). The existing validator, audit commands, and structure maps are directly reusable with confirmed paths.
- Architecture: HIGH — Based on 8+ academic papers and 4 practical blog posts from 2025-2026. The orchestrator+executor+validator pattern is well-established in the research literature.
- Pitfalls: MEDIUM — Derived from research papers' failure mode analysis + practical knowledge of existing system. Some pitfalls (e.g., Phase 9 scope) are specific to this project's architecture.

**Research date:** 2026-05-27
**Valid until:** 30 days (stable domain — agent orchestration patterns are well-established; the mkobi codebase may change)
