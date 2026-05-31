---
name: audit-multi-phase
description: Execute full multi-agent audit pipeline using orchestrator coordination, executor subagents, and validator subagents with retry logic
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
Execute the complete multi-agent audit pipeline: prepare context, execute all phases with executors, validate findings, and merge into final report.

</objective>

<process>

## 1. Gather Base Layer Context (once)

Read `.ai/structure/map.md` for directory structure.
Read `.ai/context/commands.md` for verification commands.
Read `AGENTS.md` for project guidelines.
List documentation structure from `docs/` folder.


Set variables:
- `{BASE_CONTEXT}` = summary of the above files
- `{REPORT_TEMPLATE_PATH}` = `.ai/audit/templates/audit-findings.md`
- `{TASK_FILES}` = list of files in `.kilo/commands/audit/phases/`
- {AUDIT-EXECUTOR} - model from `C:\py_dev\mkobi\.ai\models\lookup_table.md`
- {VALIDATOR} -  model from `C:\py_dev\mkobi\.ai\models\lookup_table.md`

# 1.1 DO NOT
- Read executor role or executor tasks and templates, just provide links
- Read production code, full documentation content


## 2. Execute Phase Loop 

For each phase file in `{TASK_FILES}` (sorted by phase number) follow steps 2.1-2.6:

IMPORTANT: 
- do not read task files or findings templates just pass file paths to agent to read them 
- Max allowed parallel subagents = 2 

<phase_loop>

### 2.1 Extract Phase Metadata
- `{TASK_PATH}` = full path to phase file
- `{PHASE_NUMBER}`, `{PHASE_NAME}` = parsed from filename `NN-audit-name.md`
- `{OUTPUT_PATH}` = `.ai/audit/{PHASE_NUMBER}-{PHASE_NAME}/findings.md`

### 2.2 Launch Executor
```
Task(
  prompt="Read .kilo/agents/audit-executor.md for your role.\n"
       + "Read and execute phase task: {TASK_PATH}\n"
       + "Report template: {REPORT_TEMPLATE_PATH}\n"
       + "Write findings to: {OUTPUT_PATH}\n"
       + "Base context: {BASE_CONTEXT}\n"
       + "problems_only = TRUE\n",

  agent="audit-executor",
  mode = "subagent",
  model = "{AUDIT-EXECUTOR}",
  description="Execute audit phase {PHASE_NUMBER} - {PHASE_NAME}"
)
```


### 2.3 Verify Executor Output
Check that `{OUTPUT_PATH}` exists and is not empty.
If missing or empty: retry once, then escalate on second failure.

### 2.4 Launch Validator (skip for Phase 99)
```
Task(
  prompt="Read .kilo/agents/validator.md for your role.\n"
       + "Read validation task: .kilo/commands/audit/phases/99-audit-validate.md\n"
       + "Validate findings at: {OUTPUT_PATH}\n"
       + "Write validation report to: {PHASE_NUMBER}-{PHASE_NAME}-validated-findings.md\n"
       + "Base context: {BASE_CONTEXT}\n"
       + "problems_only = TRUE\n",

  agent = "validator",
  mode = "subagent",
  model = "{VALIDATOR}",
  description="Validate phase {PHASE_NUMBER} - {PHASE_NAME}",
)
```

### 2.5 Verify Validation Output
Check that `.ai/audit/99-validation/{PHASE_NUMBER}-{PHASE_NAME}-validated.md` exists.
If missing or empty: retry once, then escalate on second failure.

</phase_loop>

## 3. Merge Final Report

Use template `.kilo/commands/audit/templates/audit-final-report.md`.
Merge all validated findings from `.ai/audit/99-validation/` into `.ai/audit/final-report.md`.

</process>

<output>

```
AUDIT COMPLETE

Phases completed: {N}/{N}
Validated findings: {N} total
Final report: .ai/audit/validated/final-report.md

By severity:
- CRITICAL: {n}
- HIGH: {n}
- MEDIUM: {n}
- LOW: {n}
```

</output>

<retry_rules>
- Max 1 retry per phase (2 total attempts maximum)
- On second failure: escalate to user with structured failure report (phase number, error, missing outputs)
- Rejected findings cleaned from file before merge
</retry_rules>