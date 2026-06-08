---
name: implement-multiple-tasks
description: Execute semantic development tasks safely and incrementally using implementor subagents with validation and completion control
agent: implementor-orchestrator
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
Execute implementation tasks through an orchestrator + implementor workflow.

The orchestrator manages the loop. Each implementor subagent handles one task.
Orchestrator reviews diffs and commits. One task = one commit on the current branch.
</objective>

<process>

## Step 0 — Ensure Docker Environment is Running

Start Docker services in **development or test mode** (never production). Follow `docs/11-guides/docker.md`. Confirm containers are `running` or `healthy`. If startup fails, document why and skip dependent steps.

## 1. Ask User For Execution Limit

Ask: "How many tasks should be implemented in this run?"

- WAIT for explicit response. Accept only positive integer. Store as `{MAX_TASKS}`.
- Initialize `{COMPLETED_TASKS} = 0`.

## 2. Prepare Execution Loop

- Read execution order: `C:\py_dev\mkobi\.ai\tasks\todo\order.yaml`.
- List files in `C:\py_dev\mkobi\.ai\tasks\todo\*`.
- Select up to `{MAX_TASKS}` files as `{TASKS_FILES_TO_IMPLEMENT}`, preserving execution order.

## 3. Load Shared Project Context

Read once, summarize, pass to every subagent:

- `C:\py_dev\mkobi\.ai\context\commands.md`
- `AGENTS.md`
- `C:\py_dev\mkobi\docs\SPEC.md`
- `C:\py_dev\mkobi\docs\11-guides\docker.md`

Summarize into `{MAIN_CONTEXT}`: architecture, conventions, patterns, boundaries.

## 4. Task Execution Loop

For each task file in `{TASKS_FILES_TO_IMPLEMENT}` (one at a time):

### 4.1 Select Implementor Model

Look up `{task_implementor_model}` from `C:\py_dev\mkobi\.ai\models\lookup_table.md`.

### 4.2 Spawn Implementor Subagent

Only 1 subagent at a time. Never parallel.

```
Task(
  prompt="First, read C:\py_dev\mkobi\.kilo\agents\implementor-subagent.md for your role and instructions.\n\n" + {subagent_prompt},
  subagent_type="general",
  model="{task_implementor_model}",
  description="Implement task {TASK_FILE_NAME}"
)
```

Where `{subagent_prompt}` is:

```
## Task File
{TASK_FILE_ABS_PATH}

## Project Context
{MAIN_CONTEXT}

## What To Do
1. Read the task file. Understand scope, affected files, acceptance criteria.
2. Validate preconditions: semantic targets exist, depends_on tasks are done.
   If already implemented: rename to *_DONE.yaml, move to done/, return IMPLEMENTATION_COMPLETE.
3. Implement: edit only required files. Follow existing patterns.
4. Validate:
   - Python: uv run ruff check <files>, uv run mypy <files>, uv run pytest <paths>
   - Frontend: npm run build, npm run lint, npm run test
   Fix only issues caused by your changes.
   -If tests conflict with architecture:
    -- update tests
    -OR
    -- remove obsolete tests
   -Do NOT degrade architecture for outdated tests.

5. Verify: git diff HEAD --stat —  Check only that your changes applied correctly and ignore other changes. If you see changes in files not related to the task it is normal - other agents are doing their task in parallel.

6. Finalize: rename task file to *_DONE.yaml, move to C:\py_dev\mkobi\.ai\tasks\done/.

## Output
Return ## IMPLEMENTATION_COMPLETE or ## IMPLEMENTATION_BLOCKED.
Include: summary, files modified, validation results, problems found.
```

### 4.3 Handle Subagent Return

```powershell
git diff HEAD --stat
```

Focus on files the task requires. Ignore changes from other agents or the user.


**If task-related changes look good:**
```powershell
git add <task-related files only>
git commit -m "{type}({scope}): {description}" -m "Task: {TASK_FILE_NAME}"
```
**If task-related changes look wrong and you are 100% sure that the agent you spawned broke something or did wrong.** Only in that case you can ran `git restore <specific task-related files>`
Be sure that you do not touch files not related to the current task - this could be changes done by other agents. 
And re-spawn implementor with error details.

Rules:
- Always `git add <specific files>` — NEVER `git add -A` or `git add .`
- Only stage files the task requires.

### 4.5 Validate Task Finalization

Verify:
- Task file renamed to `*_DONE.yaml`
- Task file moved to `C:\py_dev\mkobi\.ai\tasks\done\`
- Task file absent from `C:\py_dev\mkobi\.ai\tasks\todo\`

If ANY check fails:
1. Display `TASK FINALIZATION INVALID`.
2. Spawn new subagent with failure details. Request completion fix ONLY.
3. Do NOT continue until fixed.

### 4.6 Update Progress

- Increment `{COMPLETED_TASKS}`.
- Display `TASK COMPLETED SUCCESSFULLY`.

### 4.7 Continue or Stop

If `{COMPLETED_TASKS} >= {MAX_TASKS}`: STOP.

Otherwise: next task, spawn fresh subagent. Never reuse previous context.

</process>

<output>

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMPLEMENTATION RUN COMPLETE ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tasks completed: {COMPLETED_TASKS}/{MAX_TASKS}

Completed tasks:
- {TASK_NAME}

Validation:
- task finalization verified
- done/ migration verified
- git commit created per task by orchestrator

Status:
✓ Architecture preserved
✓ Tests validated
✓ Lint/type checks validated
```

</output>

<success_criteria>

* [ ] User execution limit requested
* [ ] Shared context loaded once, passed to every subagent
* [ ] One fresh subagent per task, sequential
* [ ] Orchestrator reviews diffs and commits (not subagent)
* [ ] git add <specific files> only (never add -A / add .)
* [ ] git restore only <specific files> with user confirmation
* [ ] Task renamed to *_DONE.yaml, moved to done/
* [ ] One conventional commit per task by orchestrator
* [ ] Failed finalization triggers corrective subagent
* [ ] Execution stops at user-defined limit

</success_criteria>
