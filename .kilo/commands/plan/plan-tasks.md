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

## Step 1 Preparation List files only (do not read contents): 
- `C:\py_dev\mkobi\.ai\audit\validated\**` 
- `C:\py_dev\mkobi\.ai\plans\**`

---
## Step 2 User Selection (Mandatory) 
Display discovered files. 
Ask the user to select: 
- one file 
- multiple files 
- ALL files 
Do not continue until a selection is provided. If the user selects ALL, include all discovered files.

---
## Step 3 — Study selected files.

Use ONLY:

- validated findings
- safety validation results
- rollout constraints
- semantic stability analysis

Ignore:

- rejected findings
- stale findings
- unsafe recommendations

Conflict resolution:

- prefer safety constraints
- prefer higher-confidence findings
- surface conflicts in task metadata
- never merge conflicting recommendations into a single task

---

## Step 4 — Load Structural & Semantic Context

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

## Step 5 — Build Dependency-Aware Execution Graph
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
- maximize survivability
- maximize safe parallel execution
- preserve architectural boundaries

Do not split work unless:
- dependency isolation improves
- risk containment improves
- parallel execution improves

Avoid:
- broad rewrites
- unstable task boundaries
- tightly coupled rollout phases
- fragile sequencing assumptions

Use:
- explicit depends_on
- semantic anchors
- symbol paths
- dependency graph analysis

---

## Step 6 — Define Semantic Targets

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

## Step 7 — Generate Semantic Task Specifications

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

Acceptance criteria must be:
- objective
- testable
- binary pass/fail

Tasks with no dependencies must explicitly contain:

```yaml
depends_on: []
```

---

## Step 8 — Insert Verification Tasks


### Simple Tasks

Criteria:

* single function
* trivial implementation
* low risk

Rules:

* no dedicated verification task
* verification is inline
* implementation task completes only after tests pass

### Multi-Stage Tasks

Criteria:

* cross-module
* medium or high risk
* multi-step rollout

Rules:

* create one verification task at the end of the stage
* verification task depends on all implementation tasks in the stage

Verification task requirements:

```yaml
type: verification
verifies:
  - TASK_XXX
verification_steps:
  - build
  - test
  - smoke_check
pass_criteria:
failure_action:
  return task to rework
```
---

## Step 9— Generate Execution Ordering

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

## Step 11 — Save Tasks

Directory:
* `C:\py_dev\mkobi\.ai\tasks\todo\`

Before creating:
* check existing tasks
* merge/update instead of duplicating
* preserve dependency integrity
* preserve rollout ordering consistency

Duplicate detection:
A task is considered duplicate if:
* objective matches
* primary symbol targets overlap
* intended change is semantically equivalent

Naming:

```text
TASK_<XXX>_<task_id>_<short_name>.yaml
```

Where:
* XXX = exact rollout execution position
* numbering must preserve sortable execution order

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