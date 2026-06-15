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
- DO NOT write line numbers this is misleading. Write semantic anchors (modules functions, classes and etc) 
- Prefer incremental evolution
- Prefer stable semantic targeting
- Avoid broad rewrites
- Avoid line-based assumptions

---

# Workflow

## Step 1 Preparation List files only (do not read contents): 
- `C:\py_dev\mkobi\.ai\audit\C:\py_dev\mkobi\.ai\audit\99-validation\**` 
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

IMPORTANT Never use:
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

## Step 7.5 — Assess Risky Tasks and Insert Research Gates

For every task, evaluate whether it is **potentially disruptive** — i.e., capable of
breaking existing system behavior, disrupting tests, or causing regressions in
production workflows.

A task is considered **risky** if any of the following apply:
- It modifies configuration files that affect multiple services (Docker Compose, nginx, CI/CD)
- It changes test infrastructure (conftest.py, test fixtures, test compose)
- It removes or renames code that may have hidden consumers (exports, shared components)
- It modifies database schema, migrations, or connection settings
- It changes build, deployment, or startup behavior
- The planner cannot confidently determine all downstream impacts from static analysis

### Rules for Risky Tasks

1. **Mark the risky task as blocked** by adding to its YAML:
   ```yaml
   status: blocked
   blocked_by: TASK_XXX_research_<topic>
   ```

2. **Create a prerequisite research task** with:
   ```yaml
   id: TASK_XXX_research_<topic>
   type: research
   status: pending
   depends_on: []
   ```

3. The research task must:
   - Identify all code, docs, configs, and workflows that depend on the affected component
   - Assess the actual impact of the proposed change
   - Evaluate alternatives that achieve the same goal with less risk
   - Produce a clear **go / no-go / go-with-changes** recommendation with documented rationale
   - Document findings in a plan file (e.g., `C:\py_dev\mkobi\.ai\plans\PLAN_NN.md`)

4. The blocked implementation task depends on the research task:
   ```yaml
   depends_on:
     - TASK_XXX_research_<topic>
   ```

5. **Execution rule**: The implementation task must NOT be executed until the
   research task is complete and recommends "go" or "go-with-changes".
   If the research recommends "no-go", the implementation task must be cancelled.

### Examples from this planning session

- `TASK_056_remove_test_ports_exposure` — blocked by `TASK_055_assess_test_ports_removal_impact`
  because removing test ports could break native test execution, CI/CD, and developer workflows.

- `TASK_049_research_placeholder_page_usage` — research task created instead of
  deletion because the component's intended purpose was unclear and it had integration
  potential (shared component export).

- `TASK_050_research_access_denied_usage` — research task created instead of
  deletion because the component could be valuable as a RoleBasedAccess fallback.

---

## Step 8 — Insert Test Tasks

For every feature, first decide whether it requires testing. Do not create tests for trivial code, simple data mappings, or implementation details.

When tests are needed, set task to build tests that:
- Validate real user-visible or business-critical behavior.
- Exercise complete workflows and interactions between components.
- Detect regressions that would matter in production.
- Cover realistic edge cases and failure modes.
- Remain valid after internal refactoring.

---


## Step 9 — Insert Verification Tasks

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


## Step 10 — Generate Execution Ordering

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