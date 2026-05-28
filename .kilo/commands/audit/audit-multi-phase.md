---
name: audit-multi-phase
description: Execute full 9-phase multi-agent audit pipeline using orchestrator coordination, executor subagents, and validator subagents with retry logic and parallel execution overlap
agent: audit-orchestrator
alwaysApply: false
allowed-tools:
  - read_file
  - write_to_file
  - list_files
  - search_files
  - new_task
---

<objective>
Execute the full 9-phase multi-agent audit pipeline.

The orchestrator coordinates:
- Phase 1-8: Backend, Frontend, Database, Security, Docker, Tests, Data Processing, Deployment/Config
- Phase 9: Integration (cross-cutting, runs after all silo phases)

For each phase: prepare context -> spawn executor -> spawn validator -> retry if needed -> clean rejected findings.

Final step: merge all validated findings into `.ai/audit/final-report.md`.
</objective>

<process>

## 1. Gather Base Layer Context (once)

Read and summarize:
- `.ai/structure/map.md` -- directory structure
- `.ai/context/commands.md` -- verification commands
- `docs/SPEC.md` -- project purpose and tech stack
- `docs/README_DOCKER.md` -- Docker service paths

Store as `{BASE_CONTEXT}`.

## 2. Execute Silo Phases 1-8 (in order)

For each phase from 1 to 8:

### 2.1 Read Phase Template
Read `.kilo/commands/audit/phases/NN-audit-X.md` to get domain-specific file paths and checklist.

### 2.2 Prepare Phase-Specific Context
Extract file paths from the template. Do NOT read file contents -- sub-agents read their own files.

### 2.3 Spawn Executor Subagent

```
Task(
  prompt="First, read .kilo/agents/audit-executor.md for your role and instructions.\n\n"
        + "Execute audit phase using template: .kilo/commands/audit/phases/NN-audit-X.md\n"
        + "Base Layer context: {BASE_CONTEXT}\n"
        + "Phase-Specific file paths: [paths from phase template]\n"
        + "Write findings to: .ai/audit/{phase-name}/findings.md",
  subagent_type="general",
  description="Execute audit phase NN -- {Phase Name}"
)
```

**Wait for executor to complete before proceeding to step 2.4.**

### 2.4 Spawn Validator Subagent

```
Task(
  prompt="First, read .kilo/agents/validator.md for your role and instructions.\n\n"
        + "Validate audit findings at: .ai/audit/{phase-name}/findings.md\n"
        + "Check: all mandatory fields present, severity levels valid, classifications correct.",
  subagent_type="general",
  description="Validate {phase-name} findings"
)
```

### 2.5 Handle Validation Result

**If validation passes:** proceed to next phase.

**If validation rejects findings:**
- Retry once: spawn executor again with adjusted scope based on validator feedback.
- If retry also fails: escalate to user with structured failure report.
- Clean rejected findings from the findings file.

### 2.6 Parallel Execution Overlap

Begin Phase N+1 executor in parallel with Phase N validation to reduce total latency.

## 3. Execute Phase 9 -- Integration (after all silos complete)

Collect all 8 validated findings files as context. Spawn executor with:

```
Task(
  prompt="First, read .kilo/agents/audit-executor.md for your role and instructions.\n\n"
        + "Execute integration audit using template: .kilo/commands/audit/phases/09-audit-integration.md\n"
        + "All silo findings as context: [paths to 8 validated findings files]\n"
        + "Write findings to: .ai/audit/09-integration/findings.md",
  subagent_type="general",
  description="Execute audit phase 09 -- Integration"
)
```

Spawn validator on integration findings.

## 4. Merge Final Report

Read `.kilo/commands/audit/templates/audit-final-report.md` for merge strategy.

Merge all 9 validated findings files into `.ai/audit/final-report.md`.

</process>

<output>

```
AUDIT COMPLETE

Phases completed: 9/9
Validated findings: {N} total
Final report: .ai/audit/final-report.md

By severity:
- CRITICAL: {n}
- HIGH: {n}
- MEDIUM: {n}
- LOW: {n}
```

</output>

<retry_rules>
- Max 1 retry per phase (2 total attempts maximum)
- On second failure: escalate to user with structured failure report
- Rejected findings cleaned from file before merge
</retry_rules>
