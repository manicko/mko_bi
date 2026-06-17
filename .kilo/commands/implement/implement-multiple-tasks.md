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

## 0. Ask User For Execution Limit

Ask: "How many tasks should be implemented in this run?"

- WAIT for explicit response. Accept only positive integer. Store as `{MAX_TASKS}`.
- Initialize `{COMPLETED_TASKS} = 0`.

## 1. Prepare Execution Loop

- Read execution order: `C:\py_dev\mkobi\.ai\tasks\todo\order.yaml`.
- List files in `C:\py_dev\mkobi\.ai\tasks\todo\*`.
- Select up to `{MAX_TASKS}` files as `{TASKS_FILES_TO_IMPLEMENT}`, preserving execution order.


## 2. Load Shared Project Context

Read once, summarize, pass to every subagent:

- `C:\py_dev\mkobi\.ai\context\commands.md`
- `AGENTS.md`
- `C:\py_dev\mkobi\docs\SPEC.md`
- `C:\py_dev\mkobi\docs\11-guides\docker.md`

Summarize into `{MAIN_CONTEXT}`: architecture, conventions, patterns, boundaries.

## 3. — Ensure Docker Environment is Running

Start Docker services in **both development and test modes** (never production). Follow `docs/11-guides/docker.md`. Confirm containers are `running` or `healthy`. If startup fails, document why and skip dependent steps.

## 4. Task Execution Loop

For each task file in `{TASKS_FILES_TO_IMPLEMENT}` (one at a time):

### 4.1 Select Implementor Model

Look up `{task_implementor_model}` from `C:\py_dev\mkobi\.ai\models\lookup_table.md`.

### 4.2  Prepare {subagent_prompt}

<subagent_prompt>

## What To Do
1. Read the task file {TASK_FILE_ABS_PATH}. Understand scope, affected files, acceptance criteria.
2. Validate preconditions: semantic targets exist, depends_on tasks are done.
   If already implemented: rename to *_DONE.yaml, move to done/, return IMPLEMENTATION_COMPLETE.
3. Implement: edit only required files. Follow existing patterns.
4. If found a bug or any problem not relates to the task - don't solve, but create the new file with report to C:\py_dev\mkobi\.ai\audit\00-bug_report\ХХ-report.md
XX - free number.
5. Validate:
   - Python: uv run ruff check <files>, uv run mypy <files>, uv run pytest <paths>
   - Frontend: npm run build, npm run lint, npm run test
   Fix only issues caused by your changes.
   -If tests conflict with architecture:
    -- update tests
    -OR
    -- remove obsolete tests
   -Do NOT degrade architecture for outdated tests.


6. Finalize: rename task file to *_DONE.yaml, move to C:\py_dev\mkobi\.ai\tasks\done/.
If you see changes in files not related to the task it is normal - other agents are doing their task in parallel.

Output:
Return ## IMPLEMENTATION_COMPLETE or ## IMPLEMENTATION_BLOCKED.
Include: summary, files modified, validation results, problems found.

Project Context:
{MAIN_CONTEXT}

Docker:
Should you need to run tests or check frontend Ensure Docker Environment is Running in **development and test modes** (never production) before connecting to the database. Follow the setup instructions in `docs/11-guides/docker.md`.

GIT: Do not execute any Git command that modifies the repository state. You are working on the same files with other agents.

</subagent_prompt>


### 4.3  Spawn Implementor Subagent

Run up to 3 subagent at a time. Start new as soon as any of agents finished. If errors switch to 1 - never parallel.

```
Task(
  prompt="{subagent_prompt}",
  agent="implementor",
  mode = "subagent",
  model="{task_implementor_model}",
  description="Implement task {TASK_FILE_NAME}"
)
```

### 4.4 Handle Subagent Return & Finalization Check

  - if no subagent report or error - restart task

  - if task finished check the agent report:
  - ensure task file moved to `done/*_DONE.yaml` (absent from `todo/`).  
  -  validate related to the task-files changes (ignore file changes not related to the task) 
    ```powershell
    git diff HEAD --stat   
    ```

  - **If checks pass:**
    ```powershell
    git add <task-related files only>
    git commit -m "{type}({scope}): {description}" -m "Task: {TASK_FILE_NAME}"
    ```
    **Rules:**
    - Always `git add <specific files>` — never `-A` or `.`
    - Only stage task-required files.
    **If checks fail:**
    - `git restore <task-related files only>` (only if 100% sure of breakage)
    - Re-spawn implementor with error details
    - Do NOT continue or touch unrelated files

    If you are not sure that task was implemented - rerun agent with the same task. 
    If you are 100% sure that agent damaged/corrupted the file check git history, find damaged file (lost code oe) use  `git restore <damaged_file>` Never restore all files. Only the damaged.

### 4.5 Update Progress

- Increment `{COMPLETED_TASKS}`.
- Display `TASK COMPLETED SUCCESSFULLY`.

### 4.5 Continue or Stop

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
