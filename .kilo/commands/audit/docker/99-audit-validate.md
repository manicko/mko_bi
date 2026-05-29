---
name: audit-validate
description: Validate audit findings, dependency safety, rollout consistency, semantic target stability, and execution applicability without modifying source code
agent: validator
alwaysApply: false
---

# Audit Findings Validation Workflow

## Objective

Validate audit findings:
- `[SPEC-DEVIATION]` — verify the deviation is real and determine whether code or docs should change
- `[BEST-PRACTICE]` — verify feasibility and ROI; reject if overengineered
- `[DOC-UPDATE]` — verify the proposed doc change is accurate

Separate validated findings into:
- **Mandatory fixes** — security, data loss, correctness issues
- **Advisory recommendations** — improvements worth doing but not blocking

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
IMPORTANT provided by user or orchestrator:
 - {FINDINGS_PATH}, {PHASE_NUMBER}, {PHASE_NAME} 
- IF not provided list all findings in `.ai\audit\**`use {PHASE_NUMBER} = next free number in output path and {PHASE_NAME} = TOTAL


Extract:
- findings
- recommendations
- risks
- affected modules
- proposed architectural changes

---

## Step 2 — Load Structural & Semantic Context

PROVIDED BY ORCHESTRATOR 

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

IF NOT PROVIDED, STUDY :`.ai/structure/**`
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
- whether the fix target is correct (code vs docs)

Mark findings as invalid if:
- already implemented
- stale
- duplicate
- low ROI
- architecture-breaking
- operationally unsafe
- overly complex
- conflicting with current direction
- the code choice is actually better than the doc (flip to DOC-UPDATE)

For `[SPEC-DEVIATION]` findings:
- Determine: should code change or docs change?
- If code is better than docs → reclassify as `[DOC-UPDATE]`
- If docs are better than code → keep as spec deviation to fix

For `[BEST-PRACTICE]` findings:
- Verify the recommendation is not overengineered
- Verify ROI is positive for project size
- Reject if it adds complexity without clear maintenance benefit

For `[DOC-UPDATE]` findings:
- Verify the proposed doc change accurately reflects code reality
- Low risk, usually safe to approve

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

New file: `.ai/audit/99-validation/{PHASE_NUMBER}-{PHASE_NAME}-validated.md`
IMPORTANT: if {PHASE_NUMBER}-{PHASE_NAME}-validated.md already exists use next fre {PHASE_NUMBER} to write new file

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
- type: `[SPEC-DEVIATION]` / `[BEST-PRACTICE]` / `[DOC-UPDATE]`
- severity
- description
- impact
- root cause
- affected modules
- affected symbols
- dependency notes
- rollout considerations
- validation notes
- classification: **mandatory** or **advisory**

Separate sections in the output:
1. **Mandatory fixes** — must be addressed (security, data loss, correctness)
2. **Advisory recommendations** — recommended improvements (best practices, doc updates)
3. **Doc updates needed** — documents that should be revised to reflect code reality

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


