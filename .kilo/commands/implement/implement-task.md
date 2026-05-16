---
name: implement-task
description: Execute the next semantic development task safely and incrementally following project standards and architecture constraints
agent: implementor
alwaysApply: false
---

# Task Execution Workflow

## Objective

Execute validated semantic development tasks safely while:
- preserving architecture
- following project standards
- maintaining code quality
- minimizing unrelated changes

## Constraints

- DO NOT redesign architecture
- DO NOT change task scope
- DO NOT perform unrelated refactors
- DO NOT introduce speculative abstractions
- Prefer minimal safe implementation
- Follow existing project patterns and conventions

---

# Workflow

## Step 1 — Ask User For Execution Limit

Before starting implementation:

Ask the user:

> "How many tasks should be implemented in this run?"

Rules:
- WAIT for explicit user response before continuing
- Do NOT start analysis or implementation before receiving the answer
- Accept only a positive integer
- Store this value as the maximum number of tasks allowed for the current execution session
- STOP execution immediately after reaching this limit even if more tasks remain

---

## Step 2 — Preparation

Before implementation study:
- IMPORTANT: `C:\py_dev\mkobi\.ai\context\commands.md`
- `AGENTS.md`
- project architecture
- existing module patterns
- coding conventions
- typing conventions
- testing conventions
- dependency boundaries

Understand:
- project stack
- framework usage patterns
- module responsibilities
- existing abstractions
- validation patterns
- logging/error handling patterns

---

## Step 3 — Select and Study Next Task

Take the first task-file by execution order from:
- `C:\py_dev\mkobi\.ai\tasks\todo`

---

## Step 4 — Task Validation

Validate:
- all `depends_on` tasks are completed
- task is still applicable
- semantic targets still exist
- anchors are still stable
- functionality is NOT already implemented
- task assumptions are still valid
- inspect surrounding code and existing patterns

If already implemented:
- mark task as completed
- move task to `done`
- do not reimplement

---

## Step 5 — Implement Task

Implement ONLY:
- approved task scope
- intended semantic changes
- validated modifications

Rules:
- preserve architecture boundaries
- preserve backward compatibility
- preserve dependency integrity
- use semantic targets from task specification
- follow existing project conventions

Avoid:
- unrelated cleanup
- broad rewrites
- hidden side effects
- speculative improvements

---

## Step 6 — Validate Code Quality

Run ruff and mypy checks on affected code.
Fix only issues directly related to the task.

---

## Step 7 — Validate Tests

Run relevant tests.

If tests conflict with current architecture → update or remove tests.

Do not degrade architecture to satisfy outdated tests.

---

## Step 8 — Completion

- Mark task file name as done (`*_DONE.yaml`)
- Move file to `C:\py_dev\mkobi\.ai\tasks\done`
- Ensure the file is no more presented in `C:\py_dev\mkobi\.ai\tasks\todo`
- Update task status and dependency graph

---

## Step 9 — Detect External Problems

If unrelated problems are discovered:

1. Check `C:\py_dev\mkobi\.ai\audit\problems`
2. If matching problem exists extend/update existing problem description if needed

3. If problem does NOT exist create a new detailed problem report

Include:
- description
- affected modules
- risk
- root cause
- architectural impact
- suggested direction

Do NOT fix unrelated problems during current task execution unless:
- they directly block task execution
- they create correctness or safety risks for current task

---

# Execution Loop

After completing a task:

1. Check how many tasks were already completed during the current run
2. If execution limit is reached:
   - STOP immediately
   - provide final summary
   - do NOT continue to next task
3. Otherwise:
   - continue with the next task from `todo`

---

# Expected Result

Result must include:
- completed task implementation
- validated code changes
- passing relevant tests
- passing relevant lint/type checks
- preserved architecture consistency
- updated task status
- documented newly discovered problems
- STOP after reaching the user-defined task limit

Result must NOT include:
- unrelated refactors
- speculative architecture changes
- broad rewrites
- undocumented behavior changes

