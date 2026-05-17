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


## Step 1 — Study  Task Goals

Take the first task-file by execution order from:
- `C:\py_dev\mkobi\.ai\tasks\todo`


## Step 2 — Preparation

Before implementation study:
- IMPORTANT: `C:\py_dev\mkobi\.ai\context\commands.md`
- Semantic structure: `C:\py_dev\mkobi\.ai\structure\*`
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


## Step 3 — Task Validation

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

## Step 4 — Implement Task

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

## Step 5 — Validate Code Quality

Run ruff and mypy checks on affected code.
Fix only issues directly related to the task.

---

## Step 6 — Validate Tests

Run relevant tests.
If tests conflict with current architecture → update or remove tests.
Do not degrade architecture to satisfy outdated tests.

---

## Step 7 — Completion
- Mark task file name as done (`*_DONE.yaml`)
- Move file to `C:\py_dev\mkobi\.ai\tasks\done`
- Ensure the file is no more presented in `C:\py_dev\mkobi\.ai\tasks\todo`

---

## Step 8 — If unrelated problems are discovered

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
# Expected Result

Result must include:
- completed task implementation
- validated code changes
- passing relevant tests
- passing relevant lint/type checks
- preserved architecture consistency
- Mark task file name as done (`*_DONE.yaml`)
- Ensure file task in `C:\py_dev\mkobi\.ai\tasks\done`
- Ensure the file is no more presented in `C:\py_dev\mkobi\.ai\tasks\todo`

Result must NOT include:
- unrelated refactors
- speculative architecture changes
- broad rewrites
- undocumented behavior changes

