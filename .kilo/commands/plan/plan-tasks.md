---
name: plan-tasks
description: Build dependency-aware rollout plans and generate semantic implementation-ready task specifications using stable symbol-level targeting
agent: planner
alwaysApply: false
---

# Dependency-Aware Refactoring Planning Workflow

## Objective

Transform validated findings into:
- dependency-aware rollout graphs
- isolated implementation tasks
- semantic task specifications
- stable execution ordering

Generate:
- semantic task yaml files
- rollout ordering files
- dependency-safe execution plans

## Constraints

- DO NOT modify source code
- DO NOT implement fixes
- DO NOT redesign architecture
- ONLY plan and generate semantic implementation tasks
- Prefer incremental evolution
- Prefer stable semantic targeting
- Avoid broad rewrites
- Avoid line-based assumptions

---

# Workflow

## Step 1 — Load Validated Findings and plans

Study:
- `C:\py_dev\mkobi\.ai\audit\validated\**` 
- `C:\py_dev\mkobi\.ai\plans\**`

For:
- validated audit findings
- safety validation results
- rollout constraints
- rejected findings
- semantic stability analysis

Use ONLY validated findings.

Ignore:
- rejected findings
- stale findings
- unsafe recommendations

---

## Step 2 — Load Structural & Semantic Context

Study:
- `C:\py_dev\mkobi\.ai\structure\**`

Including:
- dependency graphs
- semantic anchor maps
- symbol graphs
- module relationships
- existing tasks
- execution order files

Analyze:
- dependency chains
- integration boundaries
- coupling zones
- semantic insertion points
- stable modification areas

---

## Step 3 — Build Dependency-Aware Execution Graph

Create:
- isolated implementation blocks
- dependency-aware task DAG
- rollout sequencing
- execution phases
- parallel execution groups

Rules:
- one coherent problem per task
- minimize coupling
- minimize overlap
- maximize task survivability
- maximize safe parallel execution
- preserve architectural boundaries

Avoid:
- broad rewrites
- unstable task boundaries
- tightly coupled rollout phases
- fragile sequencing assumptions

Use:
- explicit `depends_on`
- semantic anchors
- symbol paths
- dependency graph analysis

---

## Step 4 — Define Semantic Targets

For every task define:
- affected files
- symbol targets
- semantic anchors
- insertion/update zones
- dependency constraints

Target:
- classes
- methods
- functions
- hooks
- components
- repositories
- services
- stores
- lifecycle boundaries

Prefer anchors:
- function calls
- return statements
- decorators
- route definitions
- validation blocks
- lifecycle hooks
- transaction boundaries

Never use:
- line numbers
- positional patching
- formatting assumptions

---

## Step 5 — Generate Semantic Task Specifications

Use template:
- `C:\py_dev\mkobi\.ai\tasks\templates\task_template.yaml`

Generate tasks including:
- objective
- affected files
- symbol targets
- semantic anchors
- dependency metadata
- intended changes
- risks
- acceptance criteria
- validation/tests
- rollout metadata

Task requirements:
- atomic
- measurable
- independently executable
- semantically targetable
- resilient to unrelated code shifts

---

## Step 5.5 — Insert Verification Tasks

After EVERY implementation task, insert a verification task.

Pattern:
```
TASK_001_implement_X
TASK_002_verify_X          ← depends_on: TASK_001
TASK_003_implement_Y       ← depends_on: TASK_002
```

Verification task must:
- have `type: verification`
- reference the implementation task via `verifies: TASK_XXX_name`
- define `verification_steps` (build, test, smoke_check)
- define `pass_criteria`
- define `failure_action: return TASK_XXX to rework`
- for infrastructure: run the actual service and confirm it works
- for code: run tests_to_run and confirm they pass

Rules:
- No implementation task may be followed directly by another implementation task
- Verification tasks are mandatory, not optional
- Numbering must stay sequential (implementation N, verification N+1)

---

## Step 6 — Generate Execution Ordering

Use template:
- `C:\py_dev\mkobi\.ai\tasks\templates\order_template.yaml`
- Create\update file:
- `C:\py_dev\mkobi\.ai\tasks\todo\order.yaml

Generate:
- rollout ordering
- dependency graph file
- topological execution order

Rules:
- task order defines execution order
- numbering must match rollout order
- avoid circular dependencies
- maximize safe parallel execution
- preserve dependency integrity

---

## Step 7 — Save Tasks

Save:
- task yaml files
- execution ordering file

Directory:
- `C:\py_dev\.ai\todo\`

Before creating:
- check existing tasks
- merge/update instead of duplicating
- preserve dependency integrity
- preserve rollout ordering consistency

Naming:
- `TASK_<XXX>_<task_id>_<short_name>.yaml`

Where:
- `XXX` = exact rollout execution position
- numbering must preserve sortable execution order

---

# Expected Output

Result must include:
- dependency-aware execution DAG
- rollout ordering
- semantic task specifications
- stable symbol-level targeting
- execution-safe dependency graph
- isolated implementation units
- semantic anchor metadata
- implementation-ready yaml task files

Result must NOT include:
- source code modifications
- implementation code
- speculative architecture redesign
- line-based patch assumptions