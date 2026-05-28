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
Execute the full multi-agent audit pipeline.

Before loop prepare general context ->
In a loop  spawn executor of each phase -> retry if needed 
after loop -> spawn validator -> clean rejected findings.

Final step: merge all validated findings into `.ai/audit/final-report.md`.
</objective>

<process>
## 1. Gather Base Layer Context (once)
---------------
Read and summarize `{BASE_CONTEXT}`:
- `.ai/structure/map.md` -- directory structure
- `.ai/context/commands.md` -- verification commands
- `C:\py_dev\mkobi\AGENTS.md`
Get folder structure of documentation:
- C:\py_dev\mkobi\docs

**Do NOT read production code or documentation files.**
------------
{REPORT_TEMPLATE_PATH} : C:\py_dev\mkobi\.ai\audit\templates\audit-findings.md

**Do NOT read**

List file_paths as {TASK_FILES}:
`C:\py_dev\mkobi\.kilo\commands\audit\phases` as 

**Do NOT read just list files**

## 2. Loop through audit + validate phase 

### 2.1 Prepare phase 
For each file from {TASK_FILES} get:
 - file path as {TASK_PATH}
 - {PHASE_NUMBER} and {PHASE_NAME} from file name as {PHASE_NUMBER}-audit-{PHASE_NAME}.md
- {OUTPUT_PATH} as `C:\py_dev\mkobi\.ai\audit\audit\{PHASE_NUMBER}-{PHASE_NAME}\findings.md

### 2.2  Launch executor 

For each {PHASE_NUMBER} != 99 launch executor

```
Task(
  prompt="First, read .kilo/agents/audit-executor.md for your role and instructions {TASK_PATH}.\n\n"
        + "Execute audit phase using template: {REPORT_TEMPLATE_PATH} \n"
        + "Base Layer context: {BASE_CONTEXT}\n"
        + "Write findings to: {OUTPUT_PATH}",
  subagent_type="Audit-executor",
  description="Execute audit phase {PHASE_NUMBER} - {PHASE_NAME}"
)
```

### 2.3 Check file exist at {OUTPUT_PATH} and not empty.
Relaunch agent if task not done.

### 2.3 Validate findings 

Wait for executor to complete before proceeding 
```
Task(
  prompt="First, read `.kilo/agents/validator.md` for your role and instructions `.kilo/commands/audit/phases/99-audit-validate.md` for your task \n\n"
        + "Validate audit findings phase `{PHASE_NUMBER}-{PHASE_NAME}` at path: {OUTPUT_PATH}\n"
         + "Base Layer context: {BASE_CONTEXT}\n",
  subagent_type="Validator",
  description="Validate audit findings phase `{PHASE_NUMBER}-{PHASE_NAME}`"
)
```


As of Phase {PHASE_NUMBER}+1 could launch executor in parallel 
with Phase {PHASE_NUMBER} validation to reduce total latency.
IMPORTANT: Switch to consecutive if network errors or task not done problems.

### 2.3 Check file exist at and not empty.
`.ai/audit/99-validation/{PHASE_NUMBER}-{PHASE_NAME}-validated.md`
Relaunch agent if task not done.

## 3. Merge Final Report

Use `.kilo/commands/audit/templates/audit-final-report.md` for merge strategy.

Merge all validated findings `.ai/audit/99-validation/**` into `.ai/audit/final-report.md`.

</process>

<output>

```
AUDIT COMPLETE

Phases completed: {N}/{N}
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
