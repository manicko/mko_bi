---
name: implement-multiple_tasks
description: Execute semantic development tasks safely and incrementally using implementor subagents with validation and completion control
agent: planner
alwaysApply: false
allowed-tools:
  - read_file
  - write_to_file
  - execute_command
  - list_files
  - search_files
  - new_task
---

<objective>
Execute implementation tasks through an planner + implementor workflow.

> **Prerequisite:** Docker services must be running before executing tests, lint, or type checks. See: `docs/11-guides/docker.md`

The planner:
- manages task iteration
- loads shared project context
- spawns fresh implementor subagents
- validates task completion
- prevents context pollution between tasks

The implementor subagent:
- performs implementation for ONE task only
- validates code quality
- validates tests
- finalizes task state

</objective>

<process>


## 1. Ask User For Execution Limit 

Ask the user:

> "How many tasks should be implemented in this run?"

Rules:
- WAIT for explicit response
- Accept only positive integer
- Store as `{MAX_TASKS}`
- Initialize `{COMPLETED_TASKS} = 0`

IMPORTANT: DON'T PROCEED TO STEP 2 before finishing this step

## 2. Prepare execution loop

- Study execution order: C:\py_dev\mkobi\.ai\tasks\todo\order.yaml
- List files left in:`C:\py_dev\mkobi\.ai\tasks\todo\*`
- Keep {MAX_TASKS} >= {TASKS_FILES_COUNT} or  {TASKS_FILES_COUNT} 
names from the list. {TASKS_FILES_TO_IMPLEMENT} of files PRESERVING execution order.

---

## 2. Load and SUMMARIZE shared Project Context:

- IMPORTANT: `C:\py_dev\mkobi\.ai\context\commands.md`
- `AGENTS.md`
- `C:\py_dev\mkobi\docs\SPEC.md`


Understand:
- architecture
- module boundaries
- coding conventions
- typing conventions
- testing conventions
- dependency boundaries
- framework patterns
- logging/error handling patterns

Store summarized context as:

`{MAIN_CONTEXT}`

This context MUST be passed to EVERY implementor subagent.


---

## 3. Start Task Execution Loop

Take file names from 
{TASKS_FILES_TO_IMPLEMENT} one by one as {TASK_FILE_ABS_PATH}
PRESERVING execution order.

Don't read task files content, just pass file names. 
---
## 3.1 Select implementor model  depending on task from:

{task_implementor_model} = `C:\py_dev\mkobi\.ai\models\lookup_table.md`

## 3.2 Spawn Implementor Subagent

IMPORTANT: Only 2 subagent allowed simultaneously. Do not parallel more than 2 agents.

Display banner:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMPLEMENTING TASK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
◆ Spawning implementor...
```

Spawn fresh implementor subagent with subagent_prompt FILLED:

<subagent_prompt:START>

<implementation_context>

## Current Task File
{TASK_FILE_ABS_PATH}
## Task Content
{MAIN_CONTEXT}

</implementation_context>

<objective>

Study task content from  {TASK_FILE_ABS_PATH}.

Execute ONLY this task safely and completely.

The task is NOT complete until:
- implementation finished
- validations pass
- task renamed to *_DONE.yaml
- task moved to done/
- task removed from todo/

</objective>

<implementation_rules>

Preserve:
- architecture boundaries
- dependency integrity
- backward compatibility
- existing conventions

Avoid:
- unrelated cleanup
- broad rewrites
- speculative improvements
- hidden side effects

</implementation_rules>

<required_workflow>

## 1. Validate Task

Validate:
- depends_on tasks completed
- task still applicable
- semantic targets exist
- functionality not already implemented
- assumptions still valid

If already implemented:
- rename task file to *_DONE.yaml
- move task to done/
- return IMPLEMENTATION_COMPLETE

---

## 2. Implement Task

Implement ONLY approved scope.
Follow existing patterns.

---

## 3. Validate Code Quality

Run checks depending on what was changed:

**Python files** (`*.py`):
- Lint: `uv run ruff check <affected_files_or_dirs>`
- Type check: `uv run mypy <affected_files_or_dirs>`

**TypeScript / React files** (`*.ts`, `*.tsx`):
- Type check: `npm run build` (runs `tsc -b`) — from `frontend/` directory
- Lint: `npm run lint` — from `frontend/` directory

Fix ONLY issues related to current task.

---

## 4. Validate Tests

**Python:** Run `uv run pytest <path>` for relevant test files.
**Frontend:** Run `npm run test` — from `frontend/` directory.

If tests conflict with architecture:
- update tests
OR
- remove obsolete tests

Do NOT degrade architecture for outdated tests.

---

## 5. If unrelated issues discovered:

Create or extend reports:`C:\py_dev\mkobi\.ai\audit\problems\`
If problem does NOT exist create a new detailed problem report

Include:
- description
- affected modules
- risk
- root cause
- architectural impact
- suggested direction

Do NOT fix unrelated problems unless blocking.

---

## 6. Finalize Task

REQUIRED:

1. Rename  {TASK_FILE_ABS_PATH} to `*_DONE.yaml`
2. Move task file to:`C:\py_dev\mkobi\.ai\tasks\done`
3. Verify  {TASK_FILE_ABS_PATH} absent from`C:\py_dev\mkobi\.ai\tasks\todo`
4. Verify ALL completion conditions
5. Unrelated issues reported to C:\py_dev\mkobi\.ai\audit\problems\

</required_workflow>

<expected_output>

Return one of:

- `## IMPLEMENTATION_COMPLETE`
- `## IMPLEMENTATION_BLOCKED`

Include:
- summary
- validations executed
- tests executed
- files modified
- problems discovered

</expected_output>

<subagent_prompt:END>

```
Task(
  prompt="First, read C:\py_dev\mkobi\.kilo\agents\implementor.md for your role and instructions..\n\n" + subagent_prompt,
  subagent_type="implementor",
  model = "{task_implementor_model}"
  description="Implement task  {TASK_FILE_ABS_PATH}"
)
---

## 3.3 Handle Implementor Return

### If `## IMPLEMENTATION_BLOCKED`

Display blocker information.

Offer:

1. Provide guidance
2. Skip task
3. Abort execution

WAIT for user response.

---

### If `## IMPLEMENTATION_COMPLETE`

Proceed to validation.

---

## 3.4  Completion Validation
- task file renamed to *_DONE.yaml
- task file moved to `C:\py_dev\mkobi\.ai\tasks\done`
- task removed from `C:\py_dev\mkobi\.ai\tasks\todo`


---

## 3.5 Handle Validation Failure

If ANY validation fails:

Display:

```text
TASK FINALIZATION INVALID
```

Examples:

* task not renamed
* task not moved
* task still exists in todo
* incomplete validation
* missing tests

Then:

* spawn NEW implementor subagent
* provide failure details
* request completion fix ONLY

Do NOT continue to next task until validation passes.

---

## 4. Update Progress

After successful validation:

Increment:
`{COMPLETED_TASKS}`

Display:

```text
TASK COMPLETED SUCCESSFULLY
```

---

## 5. Continue Loop Or Stop

If:
`{COMPLETED_TASKS} >= {MAX_TASKS}`

STOP execution.

Otherwise:

* continue OUTER LOOP
* select next task
* spawn NEW fresh implementor

IMPORTANT:
Never reuse previous implementor context.

</process>

<output>

Output final summary directly:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMPLEMENTATION RUN COMPLETE ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tasks completed: {COMPLETED_TASKS}/{MAX_TASKS}

Completed tasks:
- {TASK_NAME}
- {TASK_NAME}

Validation:
- task finalization verified
- done/ migration verified
- todo/ cleanup verified

Status:
✓ Architecture preserved
✓ Tests validated
✓ Lint/type checks validated (ruff+mypy for Python, tsc+eslint for TypeScript)
```

</output>

<success_criteria>

* [ ] User execution limit requested before work starts
* [ ] Shared context loaded once by orchestrator
* [ ] Fresh implementor spawned per task
* [ ] Implementor receives MAIN_CONTEXT + TASK_FILE
* [ ] One implementor handles one task only
* [ ] Planner validates task completion independently
* [ ] Task renamed to *_DONE.yaml
* [ ] Task moved to done/
* [ ] Task removed from todo/
* [ ] Failed finalization triggers corrective implementor
* [ ] No context leakage between tasks
* [ ] Execution stops at user-defined limit

</success_criteria>

```

