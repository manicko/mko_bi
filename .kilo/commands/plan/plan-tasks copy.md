---
name: gen-tasks
description: Analyze audit reports, validate findings, and create isolated development plans without modifying code
agent: planner
alwaysApply: false
---

# Audit Analysis & Development Planning Workflow

## Objective
Analyze audit results, validate recommendations, remove weak or outdated findings, and create a structured development roadmap.

## Constraints
- DO NOT modify source code
- DO NOT apply fixes
- ONLY analyze, validate, and create development plans
- Avoid overengineering
- Follow Clean Architecture, simplicity and maintainability principles

---

# Workflow

## Step 1 — Analyze Audit Results

Study all audit reports in:

* `C:\py_dev\mkobi\.ai\audit\**`

Tasks:

* extract findings, recommendations, and issues
* group findings by domain:
  * Architecture & Boundaries
  * Code Quality & Standards
  * Security & Access Control
  * Data Pipeline
  * API Layer
  * Database & Repositories
  * Typing & Validation
  * Logging & Observability
  * Testing
  * Frontend Architecture (FSD)
  * Configuration & DevOps
* map findings to concrete modules/files
* identify affected symbols and dependency areas

---

## Step 2 — Detect Suspicious Findings

Mark as **suspicious** if:
* appears only in one audit
* contradicts other audits
* introduces unnecessary complexity
* conflicts with "simplicity first"
* outdated or already implemented
* low practical value
* violates current architecture direction

---

## Step 3 — Analyze Project Structure & Dependency Graph

Study file content in:
* `C:\py_dev\mkobi\.ai\structure**`

to get view on project structure and dependencies

Tasks:
* map audit findings to:
  * modules
  * classes
  * functions
  * frontend segments
  
* identify:
  * coupling
  * dependency chains
  * cross-layer violations
  * unstable integration points
* detect reusable semantic anchors
* identify safe insertion/update zones

---

## Step 4 — Validate Findings Against Current Codebase

For every suspicious or high-impact finding:

Validate:
* relevance
* technical correctness
* architectural consistency
* dependency impact
* implementation complexity
* overengineering risks
* current implementation state
* anchor availability
* semantic target stability

Remove anything that:
* duplicates existing behavior
* conflicts with current architecture
* has unstable targeting
* creates excessive coupling
* cannot be safely isolated

---

## Step 5 — Build Dependency-Based Development Graph

Create implementation tasks as:
* isolated
* dependency-aware
* semantically targetable
* independently executable
* minimally coupled

Rules:
* one coherent problem per task
* avoid broad file rewrites
* avoid line-based assumptions
* prefer symbol-level targeting
* minimize overlap between tasks
* tasks must survive unrelated file modifications

Use:
* `depends_on`
* semantic anchors
* symbol paths
* module dependency graph

---

## Step 6 — Create Semantic Task Specifications

Use template:
* `C:\py_dev\mkobi\.ai\tasks\templates\task_template.yaml`

For every task define:
* objective
* affected files
* symbol targets
* semantic anchors
* dependency constraints
* intended changes
* risks
* acceptance criteria
* validation/tests

Targeting rules:
* use semantic anchors instead of line numbers
* target:
  * classes
  * methods
  * functions
  * hooks
  * components
  * stores
  * repositories
* prefer stable insertion points:
  * function calls
  * return statements
  * decorators
  * route definitions
  * lifecycle hooks

Task requirements:
* atomic
* measurable
* implementation-ready
* resilient to unrelated code shifts

---

## Step 7 — Build Task Execution Order

Create task execution order and dependency graph file using:
* `C:\py_dev\mkobi\.ai\tasks\templates\order_template.yaml`

Rules:
* task order in file defines production execution order
* define explicit `depends_on`
* avoid circular dependencies
* maximize parallel execution
* separate infrastructure tasks from feature tasks
* ensure topological execution order

---

## Step 8 — Save Tasks

Save tasks as separate `.yaml` files:

Directory:

* `C:\py_dev\mkobi\TODO\DEV`

Before creating:
* check for existing related tasks
* merge/update instead of duplicating
* preserve dependency integrity

Naming:
* `TASK_<XXX>_<task_id>_<short_name>.yaml`
  whre `XXX` = preserve sortable development order`
---

# Expected Output

Result must include:

* validated audit findings
* dependency-aware development graph
* semantic task specifications
* stable symbol-level targeting
* execution ordering via `depends_on`
* isolated implementation units
* no line-based patching assumptions
* no code changes
* no implementation
