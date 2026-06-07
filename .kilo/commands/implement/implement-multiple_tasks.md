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

## Step 0 — Ensure Docker Environment is Running

Start Docker services in **development or test mode** (never production) before executing tests, lint, or type checks. Follow the setup instructions in `docs/11-guides/docker.md`. Confirm all required containers are in `running` or `healthy` state before proceeding. If the environment cannot be started, document why and skip dependent steps.

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

## ⛔ GIT RULES — FORBIDDEN FOREVER (planner + all subagents)

**These git commands are ALWAYS forbidden. No exceptions. Ever.**

```
git reset
git checkout
git clean
git stash
git rebase
git push --force / git push -f
git branch -D
git tag -d
git commit --amend
git revert
git mv
git rm
git cherry-pick
```

**If you need to undo something — just edit the files and commit a fix. Never use git to "go back".**

**If you absolutely must use a forbidden command — ask the user first via `question` tool. WAIT for "yes".**

Task files are moved with PowerShell only: `Rename-Item`, `Move-Item`. Never `git mv`/`git rm`.

---

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
- C:\py_dev\mkobi\docs\11-guides\docker.md


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

IMPORTANT: Only 1 subagent allowed simultaneously. Do not parallel more than 1 agents.

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

## ⛔ GIT RULES — FORBIDDEN FOREVER

**Never use these git commands. No exceptions.**
```
git reset / git checkout / git clean / git stash / git rebase
git push --force / git branch -D / git commit --amend / git revert
git mv / git rm / git cherry-pick
```
**Need to undo? Edit files and commit a fix. Never "go back" with git.**
**Must use a forbidden command? Ask user first via `question`. WAIT for "yes".**
Task files: PowerShell `Rename-Item` / `Move-Item` only. Never `git mv`/`git rm`.

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

## 5. Finalize Task

REQUIRED:

1. Rename  {TASK_FILE_ABS_PATH} to `*_DONE.yaml`
2. Move task file to:`C:\py_dev\mkobi\.ai\tasks\done`
3. Verify  {TASK_FILE_ABS_PATH} absent from`C:\py_dev\mkobi\.ai\tasks\todo`
4. Verify ALL completion conditions
5. Commit changes:
   - `git add -A`
   - Determine commit type from task content: `feat` (new feature), `fix` (bug fix), `refactor` (restructure), `test` (tests only), `chore` (other)
   - Determine scope from affected module (e.g. `auth`, `api`, `frontend`, `db`)
   - `git commit -m "{type}({scope}): {short_description}" -m "Task: {TASK_FILE_NAME}"`

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
* [ ] Git commit created per task (conventional commit format)
* [ ] Failed finalization triggers corrective implementor
* [ ] No context leakage between tasks
* [ ] Execution stops at user-defined limit

</success_criteria>

```

