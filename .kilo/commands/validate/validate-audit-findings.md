---
name: validate-audit-findings
description: Validate audit findings, dependency safety, rollout consistency, semantic target stability, and execution applicability without modifying source code
agent: validator
alwaysApply: false
---

# System Integrity Validation Workflow

## Objective

Validate:
- audit findings
- architectural consistency
- dependency graphs
- semantic targeting stability
- rollout safety
- execution applicability

Reject:
- stale findings
- unsafe rollout plans
- unstable semantic targeting
- overengineered recommendations
- invalid execution assumptions

## Constraints

- DO NOT modify source code
- DO NOT generate implementation code
- DO NOT redesign architecture
- DO NOT create speculative refactors
- ONLY validate safety, consistency, applicability, and survivability
- Prefer conservative decisions
- Prefer rejection over unsafe approval

---

# Workflow

## Step 1 — Load Audit Findings

Study:
- `C:\py_dev\mkobi\.ai\audit\**`

Extract:
- findings
- recommendations
- risks
- affected modules
- proposed architectural changes

---

## Step 2 — Load Structural & Semantic Context

Study:
- `C:\py_dev\mkobi\.ai\structure\**`

Including:
- dependency maps
- semantic anchors
- symbol graphs
- module relationships
- execution order files
- existing tasks

Analyze:
- architectural boundaries
- dependency chains
- semantic stability
- integration points
- coupling hotspots

---

## Step 3 — Validate Findings

Validate:
- relevance
- technical correctness
- implementation status
- architectural consistency
- operational value
- maintenance impact
- current applicability

Mark findings as invalid if:
- already implemented
- stale
- duplicate
- low ROI
- architecture-breaking
- operationally unsafe
- overly complex
- conflicting with current direction

Merge:
- duplicated findings
- overlapping root causes
- semantically identical recommendations

---

## Step 4 — Validate Dependency & Rollout Safety

Validate:
- dependency graph correctness
- rollout sequencing
- task isolation
- dependency integrity
- topological ordering
- migration safety
- rollback feasibility
- safe parallel execution

Detect:
- circular dependencies
- hidden dependency chains
- overlapping tasks
- unsafe rollout ordering
- semantic collisions
- broad coupled changes

Reject rollout plans that:
- introduce excessive coupling
- cannot survive unrelated code shifts
- rely on fragile sequencing
- create unsafe migration paths

---

## Step 5 — Validate Semantic Targeting Stability

Validate:
- semantic anchor existence
- anchor uniqueness
- symbol stability
- insertion point safety
- target survivability
- semantic applicability

Reject:
- line-based assumptions
- unstable anchors
- ambiguous targets
- fragile insertion zones

Prefer anchors:
- function calls
- decorators
- route definitions
- lifecycle hooks
- validation boundaries
- transaction boundaries
- return statements

---

## Step 6 — Validate Execution Applicability

Validate:
- task applicability after previous tasks
- dependency drift
- semantic drift
- target validity
- execution ordering consistency
- rollout synchronization

Detect:
- stale tasks
- invalidated assumptions
- dependency desynchronization
- conflicting modifications
- architecture drift

Reject execution if:
- semantic targets became unstable
- dependency graph changed unsafely
- rollout order became invalid
- task assumptions no longer hold

---
## Step 7 — Build Validated Findings Document

New file: `C:\py_dev\mkobi\.ai\audit\validated\audit_validated_findings_<number>.md` with the report (next free number) 

Create a normalized validated findings document that becomes the single source of truth for downstream planning and task generation.

The document must:
- preserve original audit structure
- preserve domain grouping
- preserve severity levels
- preserve architectural context
- preserve dependency context
- preserve affected modules and symbols

The document must exclude:
- rejected findings
- stale findings
- duplicate findings
- unsafe recommendations
- low-value recommendations

For every validated finding include:
- finding id
- title
- severity
- description
- impact
- root cause
- affected modules
- affected symbols
- dependency notes
- rollout considerations
- validation notes

Merge:
- duplicated findings
- overlapping root causes
- semantically equivalent recommendations

Normalize:
- terminology
- severity levels
- architectural naming
- dependency references
- module references

The validated findings document becomes:
- canonical planning input
- source of truth for rollout planning
- source of truth for semantic task generation

---

# Expected Output


Result must include:
- validated findings
- rejected findings
- merged findings
- dependency validation results
- rollout safety analysis
- semantic stability analysis
- execution applicability analysis
- architectural consistency warnings
- unsafe execution warnings

Result must NOT include:
- code changes
- implementation code
- architecture redesign
- speculative refactors


